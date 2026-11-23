"""Live open-source data fetchers for benchmark fixtures.

Fetches build-time values from:
- DeFiLlama API (protocol TVL)
- GitHub Releases API (with gh CLI and public Atom feed fallbacks on rate limit)
- npm Registry API (latest package version and publish date)
- PyPI Registry API (latest package version and upload date)

Uses only the Python standard library for zero-dependency cron execution.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import unescape
from typing import Any

USER_AGENT = "markdown-converter-fixtures/1.0 (+https://test.bachwidy.site)"


class FetchError(RuntimeError):
    """Raised when a required live upstream source cannot be fetched or parsed."""


def format_usd_compact(value: float) -> str:
    """Format a USD float into a concise, unambiguous benchmark string."""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.0f}"


def _extract_iso_date(ts: str | None, fallback: str) -> str:
    if not ts:
        return fallback
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", ts.strip())
    return match.group(1) if match else fallback


def _http_get(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = 15,
    retries: int = 3,
) -> bytes:
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)

    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            last_exc = exc
            # Don't waste retries on definitive client/rate-limit errors;
            # callers may handle 403/429 with dedicated fallbacks.
            if exc.code in (400, 401, 403, 404, 429):
                raise
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_exc = exc

        if attempt < retries:
            time.sleep(min(2 ** (attempt - 1), 4))

    raise FetchError(f"Failed GET {url} after {retries} attempts: {last_exc}") from last_exc


def _http_get_json(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = 15,
    retries: int = 3,
) -> Any:
    raw = _http_get(url, headers=headers, timeout=timeout, retries=retries)
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FetchError(f"Invalid JSON from {url}: {exc}") from exc


def fetch_defillama_tvl(
    protocol_slug: str,
    timeout: int = 15,
    retries: int = 3,
) -> dict[str, Any]:
    """Fetch live protocol TVL in USD from DeFiLlama."""
    url = f"https://api.llama.fi/tvl/{protocol_slug}"
    data = _http_get_json(url, timeout=timeout, retries=retries)
    if not isinstance(data, (int, float)) or data <= 0:
        raise FetchError(f"Unexpected DeFiLlama TVL payload for {protocol_slug}: {data!r}")

    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tvl_float = float(data)
    return {
        "protocol": protocol_slug,
        "raw_tvl_usd": round(tvl_float, 2),
        "formatted_tvl": format_usd_compact(tvl_float),
        "data_as_of": today_utc,
        "source": "defillama",
        "source_url": url,
    }


def _clean_markdown_line(line: str) -> str:
    """Convert a single markdown/HTML bullet line into clean plain prose."""
    text = line.strip()
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"^[-*•]\s+", "", text)
    # Replace markdown links [label](url) with label
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove escaped brackets and backticks
    text = text.replace("\\[", "[").replace("\\]", "]").replace("`", "")
    # Remove leading emoji noise if present
    text = re.sub(r"^[^\w\[(\"'#]+", "", text).strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_release_highlights(body: str, version_tag: str, max_items: int = 3) -> list[str]:
    """Extract concise, authentic highlights while ensuring the version tag never leaks into notes."""
    bare_ver = version_tag.lstrip("v")
    highlights: list[str] = []

    for raw_line in (body or "").splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith(("#", ">")):
            continue
        if not (stripped.startswith(("-", "*")) or stripped.startswith("<li>")):
            continue
        cleaned = _clean_markdown_line(stripped)
        if len(cleaned) < 12:
            continue
        lower = cleaned.lower()
        # Skip boilerplate, translation bots, contributor handles, or full-changelog links
        if any(
            skip in lower
            for skip in (
                "full changelog",
                "update translations",
                "pr-submit",
                "dependabot",
                "released on ",
            )
        ):
            continue
        if cleaned.startswith("@"):
            continue
        # Ensure the needle version string does not leak into the notes column
        if version_tag in cleaned or (bare_ver and bare_ver in cleaned):
            continue
        if len(cleaned) > 150:
            cleaned = cleaned[:147].rstrip() + "..."
        highlights.append(cleaned)
        if len(highlights) >= max_items:
            break

    if not highlights:
        highlights.append("Maintenance updates, stability improvements, and internal refactoring.")
    return highlights


def _parse_github_releases_json(
    payload: list[dict[str, Any]],
    owner: str,
    repo: str,
    limit: int,
    source_url: str,
) -> dict[str, Any]:
    releases: list[dict[str, Any]] = []
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for rel in payload:
        if rel.get("draft") or rel.get("prerelease"):
            continue
        tag = str(rel.get("tag_name") or "").strip()
        if not tag:
            continue
        published_date = _extract_iso_date(
            rel.get("published_at") or rel.get("created_at"), today_utc
        )
        highlights = _extract_release_highlights(str(rel.get("body") or ""), tag)
        releases.append(
            {
                "version": tag.lstrip("v"),
                "tag_name": tag,
                "published_date": published_date,
                "highlights": highlights,
            }
        )
        if len(releases) >= limit:
            break

    if not releases:
        raise FetchError(f"No published releases found for {owner}/{repo}")

    return {
        "repo": f"{owner}/{repo}",
        "latest_version": releases[0]["version"],
        "data_as_of": releases[0]["published_date"],
        "releases": releases,
        "source": "github",
        "source_url": source_url,
    }


def _fetch_github_releases_via_gh(owner: str, repo: str, limit: int) -> list[dict[str, Any]] | None:
    if not shutil.which("gh"):
        return None
    endpoint = f"repos/{owner}/{repo}/releases?per_page={limit * 2}"
    try:
        proc = subprocess.run(
            ["gh", "api", endpoint],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
        parsed = json.loads(proc.stdout)
        return parsed if isinstance(parsed, list) else None
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        return None


def _fetch_github_releases_via_atom(
    owner: str,
    repo: str,
    limit: int,
    timeout: int,
    retries: int,
) -> dict[str, Any]:
    atom_url = f"https://github.com/{owner}/{repo}/releases.atom"
    xml_bytes = _http_get(atom_url, timeout=timeout, retries=retries)
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise FetchError(f"Invalid Atom XML from {atom_url}: {exc}") from exc

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    releases: list[dict[str, Any]] = []

    for entry in root.findall("atom:entry", ns):
        link_el = entry.find("atom:link", ns)
        href = link_el.attrib.get("href", "") if link_el is not None else ""
        tag = href.rstrip("/").split("/")[-1] if "/releases/tag/" in href else ""
        if not tag:
            tag = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
        if not tag:
            continue
        # Skip pre-releases in atom feed heuristically (alpha/beta/rc)
        if re.search(r"-(alpha|beta|rc)\b", tag, re.IGNORECASE):
            continue
        updated = entry.findtext("atom:updated", default="", namespaces=ns)
        published_date = _extract_iso_date(updated, today_utc)
        content_html = entry.findtext("atom:content", default="", namespaces=ns) or ""
        li_items = re.findall(r"<li[^>]*>(.*?)</li>", content_html, flags=re.DOTALL | re.IGNORECASE)
        synthetic_body = "\n".join(f"- {item}" for item in li_items)
        highlights = _extract_release_highlights(synthetic_body, tag)
        releases.append(
            {
                "version": tag.lstrip("v"),
                "tag_name": tag,
                "published_date": published_date,
                "highlights": highlights,
            }
        )
        if len(releases) >= limit:
            break

    if not releases:
        raise FetchError(f"No releases parsed from {atom_url}")

    return {
        "repo": f"{owner}/{repo}",
        "latest_version": releases[0]["version"],
        "data_as_of": releases[0]["published_date"],
        "releases": releases,
        "source": "github",
        "source_url": f"https://api.github.com/repos/{owner}/{repo}/releases",
    }


def fetch_github_releases(
    owner: str,
    repo: str,
    limit: int = 5,
    github_token: str | None = None,
    timeout: int = 15,
    retries: int = 3,
) -> dict[str, Any]:
    """Fetch recent GitHub releases via REST API, with gh CLI and Atom fallbacks on rate limit."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases?per_page={limit * 2}"
    token = github_token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        payload = _http_get_json(api_url, headers=headers, timeout=timeout, retries=retries)
        if not isinstance(payload, list):
            raise FetchError(f"Unexpected GitHub releases payload for {owner}/{repo}")
        return _parse_github_releases_json(
            payload, owner, repo, limit, source_url=f"https://api.github.com/repos/{owner}/{repo}/releases"
        )
    except urllib.error.HTTPError as exc:
        if exc.code not in (403, 429):
            raise FetchError(f"GitHub API HTTP {exc.code} for {owner}/{repo}") from exc

    # Rate-limited on unauthenticated REST API: try authenticated gh CLI first, then public Atom feed.
    gh_payload = _fetch_github_releases_via_gh(owner, repo, limit)
    if gh_payload:
        return _parse_github_releases_json(
            gh_payload, owner, repo, limit, source_url=f"https://api.github.com/repos/{owner}/{repo}/releases"
        )

    return _fetch_github_releases_via_atom(owner, repo, limit, timeout=timeout, retries=retries)


def fetch_npm_latest(
    package_name: str,
    timeout: int = 15,
    retries: int = 3,
) -> dict[str, Any]:
    """Fetch latest version and publish date from the npm registry."""
    url = f"https://registry.npmjs.org/{package_name}"
    data = _http_get_json(url, timeout=timeout, retries=retries)
    dist_tags = data.get("dist-tags") or {}
    latest = str(dist_tags.get("latest") or "").strip()
    if not latest:
        raise FetchError(f"Missing dist-tags.latest for npm package {package_name}")

    time_map = data.get("time") or {}
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    published_date = _extract_iso_date(time_map.get(latest), today_utc)

    return {
        "package": package_name,
        "latest_version": latest,
        "description": str(data.get("description") or "").strip(),
        "data_as_of": published_date,
        "source": "npm",
        "source_url": f"https://registry.npmjs.org/{package_name}/latest",
    }


def fetch_pypi_latest(
    package_name: str,
    timeout: int = 15,
    retries: int = 3,
) -> dict[str, Any]:
    """Fetch latest version and upload date from PyPI JSON API."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    data = _http_get_json(url, timeout=timeout, retries=retries)
    info = data.get("info") or {}
    latest = str(info.get("version") or "").strip()
    if not latest:
        raise FetchError(f"Missing info.version for PyPI package {package_name}")

    releases = (data.get("releases") or {}).get(latest) or []
    upload_ts = None
    for file_info in releases:
        if file_info.get("upload_time_iso_8601"):
            upload_ts = file_info["upload_time_iso_8601"]
            break

    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    upload_date = _extract_iso_date(upload_ts, today_utc)

    return {
        "package": package_name,
        "latest_version": latest,
        "summary": str(info.get("summary") or "").strip(),
        "requires_python": str(info.get("requires_python") or ">=3.9").strip(),
        "data_as_of": upload_date,
        "source": "pypi",
        "source_url": url,
    }


def fetch_all_live_data(
    github_token: str | None = None,
    timeout: int = 15,
    retries: int = 3,
) -> dict[str, Any]:
    """Fetch all live datasets required for the 12 v1 benchmark fixtures."""
    return {
        "aave_tvl": fetch_defillama_tvl("aave", timeout=timeout, retries=retries),
        "lido_tvl": fetch_defillama_tvl("lido", timeout=timeout, retries=retries),
        "fastapi_releases": fetch_github_releases(
            "fastapi", "fastapi", limit=5, github_token=github_token, timeout=timeout, retries=retries
        ),
        "ruff_releases": fetch_github_releases(
            "astral-sh", "ruff", limit=5, github_token=github_token, timeout=timeout, retries=retries
        ),
        "npm_next": fetch_npm_latest("next", timeout=timeout, retries=retries),
        "npm_react": fetch_npm_latest("react", timeout=timeout, retries=retries),
        "pypi_pydantic": fetch_pypi_latest("pydantic", timeout=timeout, retries=retries),
    }
