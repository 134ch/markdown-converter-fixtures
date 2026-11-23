# markdown-converter-fixtures

Versioned static HTML benchmark fixtures (`v1`) and atomic Python generator for the experiment **"Which Markdown Converter Silently Changes the Answer? (Firecrawl vs Crawl4AI vs Jina Reader)"**, ready to deploy as static files at `https://test.bachwidy.site`.

## Design

- **12 self-contained static HTML pages** grouped cleanly across 6 real-world defect sections (2 pages per section), zero client-side JavaScript, zero external CSS/font dependencies.
- **4 needle types**: `price`, `version`, `stat`, and `code`, with 1 isolated needle per page placed exclusively inside the target HTML structure under test.
- **Harness-ready `needles.json`**: includes extensionless `slug` aligned with `out/{tool}/{slug}_{run}.md` (2 runs per tool, 3 fresh LLM prompts per run), plus `url`, `needle`, `needle_type`, `defect_section`, `defect_class`, `question`, `expected_answer`, `silent_wrong_answer`, `required_footnote`, `source`, `data_as_of`, and `generated_at`.
- **Live build-time open-source data** fetched from DeFiLlama, GitHub Releases, npm Registry, and PyPI Registry where live stats/versions are tested, plus realistic fixed values where table/toggle/footnote structure is the point.
- **Atomic generation**: stages all 12 pages, `v1/index.html`, and `v1/needles.json` into a temp directory on the same filesystem, validates every file and needle, calls `fsync`, and atomically swaps `site/v1` via Linux `renameat2(RENAME_EXCHANGE)` (with rollback-safe fallback on non-Linux systems). If any API call or validation check fails, existing files stay untouched.
- **Visible staleness stamp**: every page renders `Generated on YYYY-MM-DD, data as of YYYY-MM-DD (UTC)`.

## Fixture Catalog (`v1`)

| # | `slug` | Defect Section | Needle Type | Source | Silent Failure Mode |
|---|--------|---------------|-------------|--------|---------------------|
| 01 | `01-pricing-table-rowheader` | Table Cells | `price` | Fixed (`<table>` sticky `<th scope="row">`) | Dropping col 1 shifts `$129/mo` into Starter (`$39/mo`) |
| 02 | `02-pricing-table-grid` | Table Cells | `price` | Fixed (ARIA `role="table"` CSS grid) | Dropping col 1 shifts `$99/mo` into Hobby (`$29/mo`) |
| 03 | `03-pricing-toggle-css-radio` | Price Toggles | `price` | Fixed (CSS radio toggle hiding `.price-annual`) | Returns monthly `$48/mo` instead of annual `$38/mo` |
| 04 | `04-pricing-toggle-tabpanel` | Price Toggles | `price` | Fixed (inactive ARIA `role="tabpanel" hidden`) | Returns monthly `$120/mo` instead of annual `$96/mo` |
| 05 | `05-stat-footnote-tax` | Footnotes | `price` | Fixed (`$1,250` + `<sup>1</sup>` + VAT endnote) | Omits `excluding 20% VAT` (`$1,500` incl. VAT) or outputs `$1,2501` |
| 06 | `06-stat-footnote-aave-tvl` | Footnotes | `stat` | Live DeFiLlama API (`/tvl/aave`) | Omits borrowed/pool2 exclusion footnote or merges `<sup>1</sup>` |
| 07 | `07-changelog-table-fastapi` | Version Columns | `version` | Live GitHub Releases (`fastapi/fastapi`) | Dropping `<th scope="row">` version col yields wrong-row version or `unknown` |
| 08 | `08-changelog-timeline-ruff` | Version Columns | `version` | Live GitHub Releases (`astral-sh/ruff`) | Stripping `<aside class="release-meta">` drops versions or shifts rows |
| 09 | `09-docs-tabs-next` | Tabbed Code | `code` | Live npm Registry (`next`) | Losing Tab 2 drops `pnpm add next@<ver>`, leaving `npm install next@latest` |
| 10 | `10-docs-tabs-pydantic` | Tabbed Code | `code` | Live PyPI Registry (`pydantic`) | Losing hidden Tab 2 drops `pydantic==<ver>`, leaving `pip install pydantic` |
| 11 | `11-loading-placeholder-lido-tvl` | Loading Placeholders | `stat` | Live DeFiLlama API (`/tvl/lido`) | Emits `Loading TVL...` skeleton instead of `<output>` value |
| 12 | `12-loading-placeholder-react` | Loading Placeholders | `version` | Live npm Registry (`react`) | Emits `v0.0.0-loading` / `--` instead of `<data>` value |

## Usage

Requires Python 3.10+ (standard library only, no third-party packages).

```bash
# Regenerate site/v1/ and site/v1/needles.json atomically from live APIs
python3 generate.py

# Optional: pass GITHUB_TOKEN for higher GitHub REST API rate limits in cron
GITHUB_TOKEN=... python3 generate.py

# Optional: save or replay a fetched live-data snapshot
python3 generate.py --snapshot-out snapshot-v1.json
python3 generate.py --snapshot-in snapshot-v1.json

# Run verification tests
python3 -m unittest discover -s tests -v
```

## Expected Benchmark Output Layout

When running Firecrawl, Crawl4AI, and Jina Reader against deployed fixtures:

```text
out/{tool}/{slug}_{run}.md
```

Example: `out/firecrawl/01-pricing-table-rowheader_1.md` and `out/firecrawl/01-pricing-table-rowheader_2.md`. (`out/` is gitignored.)

## Test runner (`run-a2-test.py`)

A single-file script that runs all 12 fixture pages through Firecrawl, Crawl4AI, and Jina Reader, and records whether each tool returns the needle value intact.

What it does:

- Loads the needle list from the live `needles.json` (or a local copy with `--needles`).
- For each tool, run, and page: calls the tool, saves the raw markdown to `out/{tool}/{slug}_{run}.md`, and checks the needle: `found` (expected value present), `wrong` (the silent-wrong value present instead), or `missing`.
- Appends a per-run log to `out/results.json` (latency, character count, errors), merging with earlier runs instead of overwriting them.
- Jina Reader: free `r.jina.ai` endpoint, no key needed; optional `JINA_API_KEY` raises the rate limit. Firecrawl: `api.firecrawl.dev/v1/scrape`, needs `FIRECRAWL_API_KEY` (free tier at firecrawl.dev). Crawl4AI: headless browser crawl, needs `pip install crawl4ai` then `crawl4ai-setup`; skipped with instructions if missing.
- Options: `--tools jina,firecrawl,crawl4ai`, `--runs 1` (or `2`), `--pages` to run only some slugs, `--delay` seconds between requests.

```bash
python3 run-a2-test.py --tools crawl4ai --runs 1
python3 run-a2-test.py --tools firecrawl --runs 1   # needs FIRECRAWL_API_KEY
python3 run-a2-test.py --tools jina --runs 1 --delay 10
```

Why Python:

- Crawl4AI is a Python library. There is no supported way to run it from another language, so the runner has to be Python for that leg.
- The other two legs are plain HTTP calls, done with the standard library (`urllib`) only, so Jina and Firecrawl need no extra packages.
- The fixture generator is Python too, so the whole benchmark is one language and one install.
- The script is short (one file, about 200 lines) and readable, so anyone can audit exactly what was measured.

## Deployment

Deploy the contents of `site/` as the static web root for `https://test.bachwidy.site`:

- `https://test.bachwidy.site/v1/01-pricing-table-rowheader.html` ... `12-loading-placeholder-react.html`
- `https://test.bachwidy.site/v1/needles.json`
- `https://test.bachwidy.site/v1/index.html`
