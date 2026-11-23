#!/usr/bin/env python3
"""A2 test runner: run the 12 fixture pages through Firecrawl, Crawl4AI, Jina.

Usage (from this folder):
  python3 run-a2-test.py --tools jina --runs 1
  python3 run-a2-test.py --tools jina,firecrawl,crawl4ai --runs 2

Prereqs:
  - Jina: none (free reader endpoint).
  - Firecrawl: FIRECRAWL_API_KEY env var (free tier at firecrawl.dev).
  - Crawl4AI: pip install crawl4ai, then crawl4ai-setup (playwright browsers).
    Skipped with instructions if the library is missing.

Outputs:
  out/{tool}/{slug}_{run}.md   raw markdown per tool per run
  out/results.json             per-run log: needle found, latency, errors
"""
import argparse
import asyncio
import json
import os
import sys
import time
import urllib.request
import urllib.error

BASE = "https://test.bachwidy.site"
NEEDLES_URL = BASE + "/v1/needles.json"


def load_needles(path=None):
    if path:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        req = urllib.request.Request(NEEDLES_URL, headers={"User-Agent": "manicule-a2-test/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    return data["needles"]


def check_needle(markdown, needle, silent_wrong):
    """Return: found | wrong | missing. Wrong means the silent-wrong value is present."""
    if needle in markdown:
        return "found"
    if silent_wrong and silent_wrong in markdown:
        return "wrong"
    return "missing"


def run_jina(url):
    headers = {"User-Agent": "manicule-a2-test/1.0", "X-Return-Format": "markdown"}
    jina_key = os.environ.get("JINA_API_KEY", "")
    if jina_key:
        headers["Authorization"] = "Bearer " + jina_key
    req = urllib.request.Request("https://r.jina.ai/" + url, headers=headers)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=90) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    return text, time.time() - t0, None


def run_firecrawl(url, api_key):
    payload = json.dumps({"url": url, "formats": ["markdown"]}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.firecrawl.dev/v1/scrape",
        data=payload,
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.load(resp)
    md = (data.get("data") or {}).get("markdown") or ""
    return md, time.time() - t0, None


def run_crawl4ai(url):
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    except ImportError:
        return None, 0, "crawl4ai not installed: pip install crawl4ai, then crawl4ai-setup"

    async def _crawl():
        async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
            return await crawler.arun(url, config=CrawlerRunConfig())

    t0 = time.time()
    result = asyncio.run(_crawl())
    md = result.markdown or ""
    return md, time.time() - t0, None


RUNNERS = {
    "jina": lambda url, key: run_jina(url),
    "firecrawl": lambda url, key: run_firecrawl(url, key),
    "crawl4ai": lambda url, key: run_crawl4ai(url),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", default="jina", help="comma list: jina,firecrawl,crawl4ai")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--out", default="out")
    ap.add_argument("--needles", default=None, help="local needles.json path (default: fetch live)")
    ap.add_argument("--pages", default=None, help="comma list of slugs to run (default: all)")
    ap.add_argument("--delay", type=float, default=1, help="seconds between requests (default: 1)")
    args = ap.parse_args()

    tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    api_key = os.environ.get("FIRECRAWL_API_KEY", "")
    needles = load_needles(args.needles)
    if args.pages:
        wanted = {s.strip() for s in args.pages.split(",") if s.strip()}
        needles = [n for n in needles if n["slug"] in wanted]
    print(f"loaded {len(needles)} needles")

    results = []
    for tool in tools:
        if tool == "firecrawl" and not api_key:
            print("SKIP firecrawl: FIRECRAWL_API_KEY not set")
            continue
        for run in range(1, args.runs + 1):
            for n in needles:
                slug = n["slug"]
                url = n["url"]
                out_dir = os.path.join(args.out, tool)
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, f"{slug}_{run}.md")
                try:
                    md, latency, err = RUNNERS[tool](url, api_key)
                except urllib.error.HTTPError as e:
                    md, latency, err = "", 0, f"HTTP {e.code}"
                except Exception as e:  # noqa: BLE001 - record and continue
                    md, latency, err = "", 0, f"{type(e).__name__}: {e}"
                if err:
                    status = "error"
                    print(f"[{tool} r{run}] {slug}: ERROR {err}")
                else:
                    with open(out_path, "w", encoding="utf-8") as fh:
                        fh.write(md)
                    status = check_needle(md, n["needle"], n.get("silent_wrong_answer"))
                    print(f"[{tool} r{run}] {slug}: {status} ({latency:.1f}s, {len(md)} chars)")
                results.append({
                    "tool": tool, "run": run, "slug": slug,
                    "needle": n["needle"], "status": status,
                    "latency_s": round(latency, 2),
                    "chars": len(md) if not err else 0,
                    "error": err,
                })
                time.sleep(args.delay)  # be polite to the reader endpoints

    results_path = os.path.join(args.out, "results.json")
    os.makedirs(args.out, exist_ok=True)
    # Merge with earlier runs instead of overwriting them.
    merged = []
    if os.path.exists(results_path):
        try:
            merged = json.load(open(results_path, encoding="utf-8"))
        except json.JSONDecodeError:
            merged = []
    keys = {(r["tool"], r["run"], r["slug"]) for r in results}
    merged = [r for r in merged if (r["tool"], r["run"], r["slug"]) not in keys] + results
    with open(results_path, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, indent=2)
    summary = {}
    for r in results:
        summary.setdefault(r["tool"], {}).setdefault(r["status"], 0)
        summary[r["tool"]][r["status"]] += 1
    print("summary:", json.dumps(summary))
    print("wrote", results_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
