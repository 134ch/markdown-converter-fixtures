"""Verification suite for the 12 v1 markdown converter benchmark fixtures."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from generator.atomic import atomic_swap_directory
from generator.generate import generate_site

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SITE_V1 = PROJECT_ROOT / "site" / "v1"

SAMPLE_LIVE_DATA = {
    "aave_tvl": {
        "protocol": "aave",
        "raw_tvl_usd": 16400000000.0,
        "formatted_tvl": "$16.40B",
        "data_as_of": "2026-11-22",
        "source": "defillama",
        "source_url": "https://api.llama.fi/tvl/aave",
    },
    "lido_tvl": {
        "protocol": "lido",
        "raw_tvl_usd": 16800000000.0,
        "formatted_tvl": "$16.80B",
        "data_as_of": "2026-11-22",
        "source": "defillama",
        "source_url": "https://api.llama.fi/tvl/lido",
    },
    "fastapi_releases": {
        "repo": "fastapi/fastapi",
        "latest_version": "0.165.0",
        "data_as_of": "2026-11-18",
        "releases": [
            {
                "version": "0.165.0",
                "tag_name": "0.165.0",
                "published_date": "2026-11-18",
                "highlights": ["Add configurable form parsing limits."],
            },
            {
                "version": "0.164.0",
                "tag_name": "0.164.0",
                "published_date": "2026-11-18",
                "highlights": ["Add configurable request body size limits."],
            },
        ],
        "source": "github",
        "source_url": "https://api.github.com/repos/fastapi/fastapi/releases",
    },
    "ruff_releases": {
        "repo": "astral-sh/ruff",
        "latest_version": "0.17.6",
        "data_as_of": "2026-11-19",
        "releases": [
            {
                "version": "0.17.6",
                "tag_name": "0.17.6",
                "published_date": "2026-11-19",
                "highlights": ["Fix false negative on duplicate assignments."],
            },
            {
                "version": "0.17.5",
                "tag_name": "0.17.5",
                "published_date": "2026-11-12",
                "highlights": ["Improve JSON diagnostic streaming performance."],
            },
        ],
        "source": "github",
        "source_url": "https://api.github.com/repos/astral-sh/ruff/releases",
    },
    "npm_next": {
        "package": "next",
        "latest_version": "16.4.6",
        "description": "The React Framework",
        "data_as_of": "2026-11-09",
        "source": "npm",
        "source_url": "https://registry.npmjs.org/next/latest",
    },
    "npm_react": {
        "package": "react",
        "latest_version": "19.3.1",
        "description": "React is a JavaScript library for building user interfaces.",
        "data_as_of": "2026-10-14",
        "source": "npm",
        "source_url": "https://registry.npmjs.org/react/latest",
    },
    "pypi_pydantic": {
        "package": "pydantic",
        "latest_version": "2.14.4",
        "summary": "Data validation using Python type hints",
        "requires_python": ">=3.9",
        "data_as_of": "2026-11-19",
        "source": "pypi",
        "source_url": "https://pypi.org/pypi/pydantic/json",
    },
}


class GeneratedFixturesTest(unittest.TestCase):
    """Validate the live-generated static files in ./site/v1."""

    def setUp(self) -> None:
        self.needles_path = SITE_V1 / "needles.json"
        self.assertTrue(self.needles_path.is_file(), "Run generate.py before tests")
        self.manifest = json.loads(self.needles_path.read_text(encoding="utf-8"))

    def test_manifest_structure_and_defect_coverage(self) -> None:
        self.assertEqual(self.manifest["fixture_version"], "v1")
        self.assertEqual(self.manifest["base_url"], "https://test.bachwidy.site")
        self.assertEqual(self.manifest["count"], 12)
        self.assertEqual(
            self.manifest["output_layout"]["path_template"],
            "out/{tool}/{slug}_{run}.md",
        )
        self.assertEqual(self.manifest["output_layout"]["runs_per_tool"], 2)
        self.assertEqual(self.manifest["output_layout"]["llm_prompts_per_run"], 3)

        needles = self.manifest["needles"]
        self.assertEqual(len(needles), 12)

        class_counts = Counter(item["defect_class"] for item in needles)
        self.assertEqual(
            dict(class_counts),
            {
                "pricing_table_first_col": 2,
                "monthly_annual_toggle": 2,
                "stat_with_footnote": 2,
                "versioned_changelog": 2,
                "tabbed_code_docs": 2,
                "loading_placeholder": 2,
            },
        )

        # All 4 needle types from the experiment design are covered
        needle_types = {item["needle_type"] for item in needles}
        self.assertEqual(needle_types, {"price", "version", "stat", "code"})

        sources = {item["source"] for item in needles}
        self.assertEqual(sources, {"fixed", "defillama", "github", "npm", "pypi"})

        for item in needles:
            self.assertFalse(item["slug"].endswith(".html"))
            self.assertEqual(item["filename"], f"{item['slug']}.html")
            self.assertEqual(
                item["url"],
                f"https://test.bachwidy.site/v1/{item['filename']}",
            )
            self.assertTrue(item["question"].strip())
            self.assertTrue(item["expected_answer"].strip())
            self.assertTrue(item["silent_wrong_answer"].strip())
            self.assertRegex(item["data_as_of"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertRegex(item["generated_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_all_pages_static_stamped_and_contain_needle(self) -> None:
        self.assertTrue((PROJECT_ROOT / "site" / "index.html").is_file())
        self.assertTrue((SITE_V1 / "index.html").is_file())

        stamp_re = re.compile(
            r"Generated on \d{4}-\d{2}-\d{2}, data as of \d{4}-\d{2}-\d{2} \(UTC\)"
        )

        for item in self.manifest["needles"]:
            html_path = SITE_V1 / item["filename"]
            self.assertTrue(html_path.is_file(), f"Missing {item['filename']}")
            html = html_path.read_text(encoding="utf-8")

            # Must not use client-side JavaScript
            self.assertNotIn("<script", html.lower(), f"Found <script> in {item['filename']}")

            # Visible generation + data-as-of stamp
            self.assertRegex(html, stamp_re, f"Missing visible date stamp in {item['filename']}")

            # Exact needle present
            self.assertIn(item["needle"], html, f"Needle missing from {item['filename']}")

            # Needle must not leak into <title> or <h1>
            title_match = re.search(r"<title>(.*?)</title>", html, flags=re.DOTALL)
            h1_match = re.search(r"<h1>(.*?)</h1>", html, flags=re.DOTALL)
            self.assertIsNotNone(title_match)
            self.assertIsNotNone(h1_match)
            self.assertNotIn(item["needle"], title_match.group(1))
            self.assertNotIn(item["needle"], h1_match.group(1))

    def test_needle_isolation_in_target_structures(self) -> None:
        by_id = {item["id"]: item for item in self.manifest["needles"]}

        # Page 01: semantic <table> with sticky <th scope="row"> first col so dropping col 1 shifts $129/mo into Starter
        html01 = (SITE_V1 / by_id["01"]["filename"]).read_text(encoding="utf-8")
        self.assertIn('<th scope="row" class="sticky-col">Monthly base price</th>', html01)
        self.assertIn(f'<td class="price-cell">{by_id["01"]["needle"]}</td>', html01)
        self.assertIn("$129/mo", html01)

        # Page 03: needle must appear only inside .price-annual, never in .price-monthly
        html03 = (SITE_V1 / by_id["03"]["filename"]).read_text(encoding="utf-8")
        self.assertEqual(html03.count(by_id["03"]["needle"]), 1)
        self.assertIn(f'<span class="price-annual">{by_id["03"]["needle"]}</span>', html03)

        # Page 04: needle must appear only inside #panel-annual[hidden]
        html04 = (SITE_V1 / by_id["04"]["filename"]).read_text(encoding="utf-8")
        monthly_part, annual_part = html04.split('id="panel-annual"', maxsplit=1)
        self.assertNotIn(by_id["04"]["needle"], monthly_part)
        self.assertIn(by_id["04"]["needle"], annual_part)

        # Pages 05 & 06: footnotes present inside doc-endnotes aside + superscript next to figure
        for pid in ("05", "06"):
            html_fn = (SITE_V1 / by_id[pid]["filename"]).read_text(encoding="utf-8")
            self.assertIn('role="doc-endnotes"', html_fn)
            self.assertIn(f'{by_id[pid]["needle"]}<sup>', html_fn)
            self.assertIn(by_id[pid]["required_footnote"], html_fn)

        # Page 07: FastAPI latest version only in <th scope="row"> version column
        html07 = (SITE_V1 / by_id["07"]["filename"]).read_text(encoding="utf-8")
        self.assertEqual(html07.count(by_id["07"]["needle"]), 1)

        # Page 08: Ruff latest version only in <aside class="release-meta">
        html08 = (SITE_V1 / by_id["08"]["filename"]).read_text(encoding="utf-8")
        self.assertEqual(html08.count(by_id["08"]["needle"]), 1)

        # Page 09: Next.js pinned pnpm command absent from Tab 1 (npm), present in Tab 2 (pnpm)
        html09 = (SITE_V1 / by_id["09"]["filename"]).read_text(encoding="utf-8")
        before_pnpm, after_pnpm = html09.split("panel-pnpm", maxsplit=1)
        self.assertNotIn(by_id["09"]["needle"], before_pnpm)
        self.assertIn(by_id["09"]["needle"], after_pnpm)
        self.assertEqual(by_id["09"]["needle_type"], "code")

        # Page 10: Pydantic requirements.txt pin absent from Tab 1 (pip), present in Tab 2 (uv hidden)
        html10 = (SITE_V1 / by_id["10"]["filename"]).read_text(encoding="utf-8")
        before_uv, after_uv = html10.split('id="panel-uv"', maxsplit=1)
        self.assertNotIn(by_id["10"]["needle"], before_uv)
        self.assertIn(by_id["10"]["needle"], after_uv)
        self.assertEqual(by_id["10"]["needle_type"], "code")

        # Page 11: Lido TVL in <output> alongside CSS-hidden skeleton placeholder
        html11 = (SITE_V1 / by_id["11"]["filename"]).read_text(encoding="utf-8")
        self.assertIn(f'<output class="metric-value" aria-live="polite">{by_id["11"]["needle"]}</output>', html11)
        self.assertIn("Loading TVL...", html11)

        # Page 12: React version in <data> alongside hidden loading-state placeholder
        html12 = (SITE_V1 / by_id["12"]["filename"]).read_text(encoding="utf-8")
        self.assertIn(f'value="{by_id["12"]["needle"]}">v{by_id["12"]["needle"]}</data>', html12)
        self.assertIn("v0.0.0-loading", html12)


class AtomicGenerationTest(unittest.TestCase):
    """Verify failed runs never corrupt existing fixtures or leave staging debris."""

    def test_failed_swap_preserves_previous_version_verbatim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "site"
            generate_site(
                output_dir=out_dir,
                fixture_version="v1",
                live_data_override=SAMPLE_LIVE_DATA,
            )

            v1_dir = out_dir / "v1"
            before_snapshot = {
                p.name: p.read_bytes() for p in sorted(v1_dir.iterdir()) if p.is_file()
            }
            self.assertEqual(len(before_snapshot), 14)  # 12 pages + index.html + needles.json

            def _failing_build(staging: Path) -> None:
                (staging / "01-pricing-table-rowheader.html").write_text("CORRUPT", encoding="utf-8")
                raise RuntimeError("Simulated mid-generation crash")

            with self.assertRaises(RuntimeError):
                atomic_swap_directory(v1_dir, build_fn=_failing_build)

            after_snapshot = {
                p.name: p.read_bytes() for p in sorted(v1_dir.iterdir()) if p.is_file()
            }
            self.assertEqual(before_snapshot, after_snapshot)

            # Ensure no leftover staging directories exist
            leftovers = [p for p in out_dir.iterdir() if p.name.startswith(".staging-")]
            self.assertEqual(leftovers, [])

    def test_atomic_second_run_updates_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "site"
            generate_site(
                output_dir=out_dir,
                fixture_version="v1",
                live_data_override=SAMPLE_LIVE_DATA,
            )

            updated_data = json.loads(json.dumps(SAMPLE_LIVE_DATA))
            updated_data["npm_next"]["latest_version"] = "16.9.9"
            generate_site(
                output_dir=out_dir,
                fixture_version="v1",
                live_data_override=updated_data,
            )

            manifest = json.loads((out_dir / "v1" / "needles.json").read_text(encoding="utf-8"))
            next_entry = next(n for n in manifest["needles"] if n["id"] == "09")
            self.assertEqual(next_entry["needle"], "pnpm add next@16.9.9")

            html09 = (out_dir / "v1" / "09-docs-tabs-next.html").read_text(encoding="utf-8")
            self.assertIn("pnpm add next@16.9.9", html09)
            self.assertNotIn("16.4.6", html09)

            leftovers = [p for p in out_dir.iterdir() if p.name.startswith(".staging-")]
            self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
