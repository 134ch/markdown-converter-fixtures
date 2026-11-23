"""Atomic static generator for the 12 v1 markdown converter benchmark fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .atomic import atomic_swap_directory, atomic_write_file
from .fetchers import FetchError, fetch_all_live_data
from .templates import (
    RenderedFixture,
    render_all_fixtures,
    render_root_index,
    render_version_index,
)

EXPECTED_FIXTURE_COUNT = 12


def build_needles_payload(
    fixtures: list[RenderedFixture],
    *,
    base_url: str,
    fixture_version: str,
    generated_at: str,
) -> dict[str, Any]:
    """Build the needles.json manifest aligned with the 12-row experiment harness."""
    clean_base = base_url.rstrip("/")
    entries: list[dict[str, Any]] = []
    for fx in fixtures:
        entries.append(
            {
                "id": fx.id,
                "slug": fx.slug,
                "filename": fx.filename,
                "url": f"{clean_base}/{fixture_version}/{fx.filename}",
                "title": fx.title,
                "defect_section": fx.defect_section,
                "defect_class": fx.defect_class,
                "needle": fx.needle,
                "needle_type": fx.needle_type,
                "required_footnote": fx.required_footnote,
                "question": fx.question,
                "expected_answer": fx.expected_answer,
                "silent_wrong_answer": fx.silent_wrong_answer,
                "needle_context": fx.needle_context,
                "source": fx.source,
                "source_url": fx.source_url,
                "data_as_of": fx.data_as_of,
                "generated_at": generated_at,
            }
        )

    return {
        "fixture_version": fixture_version,
        "base_url": clean_base,
        "generated_at": generated_at,
        "count": len(entries),
        "output_layout": {
            "path_template": "out/{tool}/{slug}_{run}.md",
            "tools": ["firecrawl", "crawl4ai", "jina"],
            "runs_per_tool": 2,
            "llm_prompts_per_run": 3,
        },
        "needles": entries,
    }


def validate_staged_build(staging_dir: Path) -> None:
    """Verify staged HTML pages and needles.json are complete and internally consistent."""
    needles_path = staging_dir / "needles.json"
    if not needles_path.is_file():
        raise RuntimeError("Staging validation failed: missing needles.json")

    payload = json.loads(needles_path.read_text(encoding="utf-8"))
    entries = payload.get("needles")
    if not isinstance(entries, list) or len(entries) != EXPECTED_FIXTURE_COUNT:
        raise RuntimeError(
            f"Staging validation failed: expected {EXPECTED_FIXTURE_COUNT} needles, got {len(entries) if isinstance(entries, list) else type(entries)}"
        )

    valid_types = {"price", "version", "stat", "code"}
    required_keys = {
        "id",
        "slug",
        "filename",
        "url",
        "defect_section",
        "defect_class",
        "needle",
        "needle_type",
        "question",
        "expected_answer",
        "silent_wrong_answer",
        "source",
        "generated_at",
    }
    for entry in entries:
        missing = required_keys - set(entry.keys())
        if missing:
            raise RuntimeError(f"Staging validation failed: missing keys {missing} in {entry}")
        if entry["slug"].endswith(".html"):
            raise RuntimeError(
                f"Staging validation failed: slug {entry['slug']!r} must not include .html extension"
            )
        if entry["needle_type"] not in valid_types:
            raise RuntimeError(
                f"Staging validation failed: invalid needle_type {entry['needle_type']!r}"
            )

        html_path = staging_dir / entry["filename"]
        if not html_path.is_file():
            raise RuntimeError(f"Staging validation failed: missing HTML file {entry['filename']}")

        html_text = html_path.read_text(encoding="utf-8")
        if "<script" in html_text.lower():
            raise RuntimeError(f"Staging validation failed: <script> tag found in {entry['filename']}")
        if "Generated on " not in html_text or ", data as of " not in html_text:
            raise RuntimeError(f"Staging validation failed: missing date stamp in {entry['filename']}")
        if entry["needle"] not in html_text:
            raise RuntimeError(
                f"Staging validation failed: needle {entry['needle']!r} not found in {entry['filename']}"
            )
        if entry.get("required_footnote") and entry["required_footnote"] not in html_text:
            raise RuntimeError(
                f"Staging validation failed: required_footnote {entry['required_footnote']!r} not found in {entry['filename']}"
            )

    if not (staging_dir / "index.html").is_file():
        raise RuntimeError("Staging validation failed: missing v1 index.html")


def generate_site(
    *,
    output_dir: Path,
    fixture_version: str = "v1",
    base_url: str = "https://test.bachwidy.site",
    github_token: str | None = None,
    timeout: int = 15,
    retries: int = 3,
    live_data_override: dict[str, Any] | None = None,
    snapshot_out: Path | None = None,
) -> dict[str, Any]:
    """Fetch live data (unless overridden), stage all files, validate, and swap atomically."""
    # Step 1: Fetch all live upstream data BEFORE modifying anything on disk.
    live_data = (
        live_data_override
        if live_data_override is not None
        else fetch_all_live_data(github_token=github_token, timeout=timeout, retries=retries)
    )

    now_utc = datetime.now(timezone.utc)
    generated_at = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    generated_date = now_utc.strftime("%Y-%m-%d")

    fixtures = render_all_fixtures(
        live_data=live_data,
        generated_date=generated_date,
        fixture_version=fixture_version,
    )
    if len(fixtures) != EXPECTED_FIXTURE_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_FIXTURE_COUNT} rendered fixtures, got {len(fixtures)}"
        )

    needles_payload = build_needles_payload(
        fixtures,
        base_url=base_url,
        fixture_version=fixture_version,
        generated_at=generated_at,
    )
    version_index_html = render_version_index(
        fixtures,
        generated_date=generated_date,
        fixture_version=fixture_version,
    )
    root_index_html = render_root_index(
        generated_date=generated_date,
        fixture_version=fixture_version,
    )

    version_dir = output_dir / fixture_version

    def _populate_staging(staging_dir: Path) -> None:
        for fx in fixtures:
            (staging_dir / fx.filename).write_text(fx.html, encoding="utf-8")
        (staging_dir / "index.html").write_text(version_index_html, encoding="utf-8")
        (staging_dir / "needles.json").write_text(
            json.dumps(needles_payload, indent=2) + "\n",
            encoding="utf-8",
        )

    # Step 2: Atomically stage, validate, fsync, and swap site/<version> in one operation.
    atomic_swap_directory(
        target_dir=version_dir,
        build_fn=_populate_staging,
        validate_fn=validate_staged_build,
    )

    # Step 3: Atomically update top-level site/index.html after version swap succeeds.
    atomic_write_file(output_dir / "index.html", root_index_html)

    if snapshot_out is not None:
        atomic_write_file(snapshot_out, json.dumps(live_data, indent=2) + "\n")

    return needles_payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Atomically generate the 12 static HTML benchmark fixtures and needles.json."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "site",
        help="Static site output directory (default: ./site)",
    )
    parser.add_argument(
        "--version",
        default="v1",
        help="Fixture version subdirectory (default: v1)",
    )
    parser.add_argument(
        "--base-url",
        default="https://test.bachwidy.site",
        help="Canonical deployment base URL recorded in needles.json",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Per-request HTTP timeout in seconds (default: 15)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="HTTP retry count on transient network errors (default: 3)",
    )
    parser.add_argument(
        "--github-token",
        default=None,
        help="Optional GitHub API token (defaults to GITHUB_TOKEN / GH_TOKEN env vars)",
    )
    parser.add_argument(
        "--snapshot-in",
        type=Path,
        default=None,
        help="Optional JSON file of previously fetched live data for offline replay",
    )
    parser.add_argument(
        "--snapshot-out",
        type=Path,
        default=None,
        help="Optional path to save fetched live API data snapshot as JSON",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    live_override = None
    if args.snapshot_in is not None:
        live_override = json.loads(args.snapshot_in.read_text(encoding="utf-8"))

    try:
        payload = generate_site(
            output_dir=args.output_dir,
            fixture_version=args.version,
            base_url=args.base_url,
            github_token=args.github_token,
            timeout=args.timeout,
            retries=args.retries,
            live_data_override=live_override,
            snapshot_out=args.snapshot_out,
        )
    except (FetchError, RuntimeError, OSError) as exc:
        print(
            f"ERROR: generation aborted (existing fixtures preserved untouched): {exc}",
            file=sys.stderr,
        )
        return 1

    print(
        f"Generated {payload['count']} fixtures in {args.output_dir / args.version} "
        f"at {payload['generated_at']}"
    )
    for item in payload["needles"]:
        print(
            f"  [{item['id']}] {item['slug']:33s} | {item['defect_section']:20s} | "
            f"{item['needle_type']:7s} | {item['needle']:22s} ({item['source']}, as of {item['data_as_of']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
