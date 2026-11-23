"""Realistic static HTML fixture templates for the 12 v1 benchmark pages.

All 12 pages are pure static HTML + CSS with zero client-side JavaScript so
experiments measure HTML-to-Markdown conversion accuracy, not JS execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any


@dataclass(frozen=True)
class RenderedFixture:
    id: str
    slug: str
    filename: str
    title: str
    defect_section: str
    defect_class: str
    needle: str
    needle_type: str
    needle_context: str
    question: str
    expected_answer: str
    silent_wrong_answer: str
    required_footnote: str | None
    source: str
    source_url: str | None
    data_as_of: str
    html: str


BASE_CSS = """
:root {
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-alt: #f1f5f9;
  --text: #0f172a;
  --muted: #475569;
  --border: #cbd5e1;
  --accent: #2563eb;
  --accent-soft: #eff6ff;
  --badge-bg: #e2e8f0;
  --code-bg: #0f172a;
  --code-fg: #e2e8f0;
  --warn-bg: #fefce8;
  --warn-border: #fde047;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
  line-height: 1.6;
  color: var(--text);
  background: var(--bg);
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.site-header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0.9rem 1.5rem;
}
.site-header-inner {
  max-width: 980px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}
.brand {
  font-weight: 700;
  font-size: 1.05rem;
  color: var(--text);
  letter-spacing: -0.01em;
}
.site-nav {
  display: flex;
  gap: 1.25rem;
  font-size: 0.9rem;
  color: var(--muted);
}
.site-nav a { color: var(--muted); }
.page-wrap {
  max-width: 980px;
  margin: 2rem auto;
  padding: 0 1.5rem 3rem;
}
.fixture-stamp {
  display: inline-block;
  margin: 0 0 1.25rem;
  padding: 0.35rem 0.75rem;
  font-size: 0.82rem;
  color: var(--muted);
  background: var(--surface-alt);
  border: 1px solid var(--border);
  border-radius: 6px;
}
.hero {
  margin-bottom: 1.75rem;
}
.hero h1 {
  margin: 0 0 0.5rem;
  font-size: 1.9rem;
  line-height: 1.25;
  letter-spacing: -0.02em;
}
.hero p {
  margin: 0;
  color: var(--muted);
  max-width: 68ch;
}
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}
.section-title {
  margin: 0 0 0.75rem;
  font-size: 1.15rem;
}
.prose-note {
  color: var(--muted);
  font-size: 0.95rem;
}
.table-scroll {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}
th, td {
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--border);
  text-align: left;
  vertical-align: top;
}
thead th {
  background: var(--surface-alt);
  font-weight: 600;
  font-size: 0.88rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
tbody tr:last-child th,
tbody tr:last-child td {
  border-bottom: none;
}
.sticky-col {
  position: sticky;
  left: 0;
  background: var(--surface);
  z-index: 2;
  border-right: 1px solid var(--border);
}
thead .sticky-col {
  background: var(--surface-alt);
  z-index: 3;
}
.site-footer {
  max-width: 980px;
  margin: 2.5rem auto 0;
  padding: 1.25rem 1.5rem 2.5rem;
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.85rem;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.footnotes {
  margin-top: 2rem;
  padding: 1rem 1.25rem;
  background: var(--surface-alt);
  border-top: 2px solid var(--border);
  border-radius: 8px;
  font-size: 0.86rem;
  color: var(--muted);
}
.footnotes h2 {
  margin: 0 0 0.5rem;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.footnotes ol {
  margin: 0;
  padding-left: 1.25rem;
}
pre {
  margin: 0;
  padding: 1rem 1.15rem;
  background: var(--code-bg);
  color: var(--code-fg);
  border-radius: 8px;
  overflow-x: auto;
  font-size: 0.88rem;
  line-height: 1.5;
}
code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
p code, li code {
  background: var(--surface-alt);
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  font-size: 0.88em;
}
"""


def _render_shell(
    *,
    title: str,
    brand: str,
    nav_items: list[str],
    generated_date: str,
    data_as_of: str,
    extra_css: str,
    main_html: str,
    footer_note: str,
    fixture_version: str,
) -> str:
    nav_links = "\n".join(
        f'          <a href="#section-{idx}">{escape(label)}</a>'
        for idx, label in enumerate(nav_items, start=1)
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
{BASE_CSS}
{extra_css}
  </style>
</head>
<body>
  <header class="site-header">
    <div class="site-header-inner">
      <div class="brand">{escape(brand)}</div>
      <nav class="site-nav" aria-label="Primary">
{nav_links}
      </nav>
    </div>
  </header>
  <main class="page-wrap">
    <p class="fixture-stamp">Generated on {escape(generated_date)}, data as of {escape(data_as_of)} (UTC)</p>
{main_html}
  </main>
  <footer class="site-footer">
    <span>{escape(footer_note)}</span>
    <span>Fixture set {escape(fixture_version)} &middot; <a href="./index.html">All fixtures</a></span>
  </footer>
</body>
</html>
"""


def _page_01_pricing_table_rowheader(generated_date: str, fixture_version: str) -> RenderedFixture:
    extra_css = """
.price-cell { font-size: 1.08rem; font-weight: 700; color: var(--accent); white-space: nowrap; }
.faq-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; margin-top: 1.5rem; }
"""
    main_html = """    <section class="hero" id="section-1">
      <h1>CloudPulse Observability — Plan Pricing &amp; Quotas</h1>
      <p>Predictable flat-tier pricing for application metrics, distributed traces, and structured log ingestion. Every plan includes unlimited dashboards, alerting webhooks, and SAML-ready audit logs on higher tiers.</p>
    </section>

    <section class="card" id="section-2">
      <h2 class="section-title">Tier Comparison</h2>
      <p class="prose-note">Compare monthly base prices and included telemetry quotas across all four CloudPulse tiers. Overage events are billed at $0.18 per 100,000 additional events.</p>
      <div class="table-scroll">
        <table class="pricing-table" aria-label="CloudPulse pricing tiers">
          <thead>
            <tr>
              <th scope="col" class="sticky-col" aria-label="Feature"></th>
              <th scope="col">Starter</th>
              <th scope="col">Growth</th>
              <th scope="col">Scale</th>
              <th scope="col">Enterprise</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row" class="sticky-col">Monthly base price</th>
              <td class="price-cell">$39/mo</td>
              <td class="price-cell">$129/mo</td>
              <td class="price-cell">$349/mo</td>
              <td class="price-cell">$899/mo</td>
            </tr>
            <tr>
              <th scope="row" class="sticky-col">Included monthly events</th>
              <td>500,000</td>
              <td>2,500,000</td>
              <td>10,000,000</td>
              <td>50,000,000</td>
            </tr>
            <tr>
              <th scope="row" class="sticky-col">Log retention</th>
              <td>14 days</td>
              <td>30 days</td>
              <td>90 days</td>
              <td>365 days</td>
            </tr>
            <tr>
              <th scope="row" class="sticky-col">Team seats</th>
              <td>Up to 5 seats</td>
              <td>Up to 20 seats</td>
              <td>Unlimited</td>
              <td>Unlimited</td>
            </tr>
            <tr>
              <th scope="row" class="sticky-col">Support SLA</th>
              <td>Next business day</td>
              <td>4-hour response</td>
              <td>1-hour response</td>
              <td>15-minute 24/7 SLA</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="faq-grid" id="section-3">
      <div class="card">
        <h3 class="section-title">No per-host surprises</h3>
        <p class="prose-note">Containers, ephemeral preview environments, and serverless functions report metrics without per-node fees. You only pay for the tier quota you select.</p>
      </div>
      <div class="card">
        <h3 class="section-title">Instant tier upgrades</h3>
        <p class="prose-note">Upgrade or downgrade between plans from the workspace billing page. Prorated adjustments appear automatically on the following invoice.</p>
      </div>
    </section>"""
    html = _render_shell(
        title="CloudPulse Observability — Plan Pricing & Quotas",
        brand="CloudPulse",
        nav_items=["Overview", "Pricing", "FAQ"],
        generated_date=generated_date,
        data_as_of=generated_date,
        extra_css=extra_css,
        main_html=main_html,
        footer_note="CloudPulse Systems Inc. — Synthetic benchmark fixture",
        fixture_version=fixture_version,
    )
    return RenderedFixture(
        id="01",
        slug="01-pricing-table-rowheader",
        filename="01-pricing-table-rowheader.html",
        title="CloudPulse Observability — Plan Pricing & Quotas",
        defect_section="Table Cells",
        defect_class="pricing_table_first_col",
        needle="$39/mo",
        needle_type="price",
        needle_context="Starter tier monthly base price in semantic <table> with empty corner <th> and sticky <th scope='row'> first column (dropping col 1 shifts $129/mo into Starter)",
        question="What is the monthly base price for the CloudPulse Starter plan?",
        expected_answer="$39/mo",
        silent_wrong_answer="$129/mo",
        required_footnote=None,
        source="fixed",
        source_url=None,
        data_as_of=generated_date,
        html=html,
    )


def _page_02_pricing_table_grid(generated_date: str, fixture_version: str) -> RenderedFixture:
    extra_css = """
.matrix-wrap {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
}
.pricing-matrix {
  display: grid;
  min-width: 680px;
}
.matrix-row {
  display: grid;
  grid-template-columns: 220px repeat(4, minmax(110px, 1fr));
  border-bottom: 1px solid var(--border);
}
.matrix-row:last-child { border-bottom: none; }
.matrix-head {
  background: var(--surface-alt);
  font-weight: 700;
  font-size: 0.88rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--muted);
}
.matrix-cell {
  padding: 0.85rem 1rem;
  font-size: 0.94rem;
}
.matrix-row [role="rowheader"] {
  font-weight: 600;
  background: var(--surface);
  border-right: 1px solid var(--border);
  position: sticky;
  left: 0;
  z-index: 2;
}
.matrix-head .corner {
  border-right: 1px solid var(--border);
  position: sticky;
  left: 0;
  background: var(--surface-alt);
  z-index: 3;
}
.price-highlight { font-weight: 700; color: var(--accent); font-size: 1.05rem; }
"""
    main_html = """    <section class="hero" id="section-1">
      <h1>VaultDB Cloud — Managed Postgres Pricing Matrix</h1>
      <p>Dedicated NVMe-backed PostgreSQL clusters with automated daily snapshots, connection pooling, and zero-downtime minor upgrades across 14 global regions.</p>
    </section>

    <section class="card" id="section-2">
      <h2 class="section-title">Feature &amp; Tier Comparison</h2>
      <p class="prose-note">Each column lists the monthly base rate and provisioned resources for a single primary database instance.</p>
      <div class="matrix-wrap">
        <div class="pricing-matrix" role="table" aria-label="VaultDB Cloud pricing matrix">
          <div class="matrix-row matrix-head" role="row">
            <div class="matrix-cell corner" role="columnheader" aria-label="Feature"></div>
            <div class="matrix-cell" role="columnheader">Hobby</div>
            <div class="matrix-cell" role="columnheader">Pro</div>
            <div class="matrix-cell" role="columnheader">Team</div>
            <div class="matrix-cell" role="columnheader">Enterprise</div>
          </div>
          <div class="matrix-row" role="row">
            <div class="matrix-cell sticky-col" role="rowheader">Monthly base price</div>
            <div class="matrix-cell price-highlight" role="cell">$29/mo</div>
            <div class="matrix-cell price-highlight" role="cell">$99/mo</div>
            <div class="matrix-cell price-highlight" role="cell">$299/mo</div>
            <div class="matrix-cell price-highlight" role="cell">$799/mo</div>
          </div>
          <div class="matrix-row" role="row">
            <div class="matrix-cell sticky-col" role="rowheader">Dedicated vCPU / RAM</div>
            <div class="matrix-cell" role="cell">2 vCPU / 4 GB</div>
            <div class="matrix-cell" role="cell">4 vCPU / 16 GB</div>
            <div class="matrix-cell" role="cell">8 vCPU / 32 GB</div>
            <div class="matrix-cell" role="cell">32 vCPU / 128 GB</div>
          </div>
          <div class="matrix-row" role="row">
            <div class="matrix-cell sticky-col" role="rowheader">Included NVMe storage</div>
            <div class="matrix-cell" role="cell">40 GB</div>
            <div class="matrix-cell" role="cell">200 GB</div>
            <div class="matrix-cell" role="cell">1 TB</div>
            <div class="matrix-cell" role="cell">4 TB</div>
          </div>
          <div class="matrix-row" role="row">
            <div class="matrix-cell sticky-col" role="rowheader">Point-in-time recovery</div>
            <div class="matrix-cell" role="cell">7 days</div>
            <div class="matrix-cell" role="cell">14 days</div>
            <div class="matrix-cell" role="cell">30 days</div>
            <div class="matrix-cell" role="cell">90 days</div>
          </div>
          <div class="matrix-row" role="row">
            <div class="matrix-cell sticky-col" role="rowheader">Read replicas included</div>
            <div class="matrix-cell" role="cell">0</div>
            <div class="matrix-cell" role="cell">1 replica</div>
            <div class="matrix-cell" role="cell">3 replicas</div>
            <div class="matrix-cell" role="cell">Up to 10 replicas</div>
          </div>
        </div>
      </div>
    </section>

    <section class="card" id="section-3">
      <h2 class="section-title">Storage &amp; Network Transfer</h2>
      <p class="prose-note">Additional NVMe storage expands automatically in 10 GB increments at $0.15/GB-month. Private VPC peering and intra-region replication traffic are included at no extra cost.</p>
    </section>"""
    html = _render_shell(
        title="VaultDB Cloud — Managed Postgres Pricing Matrix",
        brand="VaultDB Cloud",
        nav_items=["Overview", "Pricing Matrix", "Storage"],
        generated_date=generated_date,
        data_as_of=generated_date,
        extra_css=extra_css,
        main_html=main_html,
        footer_note="VaultDB Cloud Ltd. — Synthetic benchmark fixture",
        fixture_version=fixture_version,
    )
    return RenderedFixture(
        id="02",
        slug="02-pricing-table-grid",
        filename="02-pricing-table-grid.html",
        title="VaultDB Cloud — Managed Postgres Pricing Matrix",
        defect_section="Table Cells",
        defect_class="pricing_table_first_col",
        needle="$29/mo",
        needle_type="price",
        needle_context="Hobby tier monthly base price in ARIA role='table' CSS grid with sticky rowheader column (dropping col 1 shifts $99/mo into Hobby)",
        question="What is the monthly base price for the VaultDB Cloud Hobby tier?",
        expected_answer="$29/mo",
        silent_wrong_answer="$99/mo",
        required_footnote=None,
        source="fixed",
        source_url=None,
        data_as_of=generated_date,
        html=html,
    )


def _page_03_pricing_toggle_css_radio(generated_date: str, fixture_version: str) -> RenderedFixture:
    extra_css = """
.billing-switch-wrap { position: relative; }
.billing-radio {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}
.billing-toggle-bar {
  display: inline-flex;
  background: var(--surface-alt);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.25rem;
  gap: 0.25rem;
  margin-bottom: 1.5rem;
}
.billing-toggle-bar label {
  cursor: pointer;
  padding: 0.45rem 1rem;
  border-radius: 999px;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--muted);
  user-select: none;
}
#billing-monthly:checked ~ .billing-toggle-bar label[for="billing-monthly"],
#billing-annual:checked ~ .billing-toggle-bar label[for="billing-annual"] {
  background: var(--accent);
  color: #ffffff;
}
.save-pill {
  display: inline-block;
  margin-left: 0.35rem;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  font-size: 0.75rem;
  background: #dcfce7;
  color: #166534;
}
.tier-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.25rem;
}
.tier-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.5rem;
}
.tier-card.featured {
  border: 2px solid var(--accent);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.08);
}
.tier-card h2 { margin: 0 0 0.35rem; font-size: 1.2rem; }
.tier-price {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin: 0.75rem 0 0.25rem;
}
.billing-caption { font-size: 0.84rem; color: var(--muted); margin: 0 0 1rem; }
.feature-list { margin: 0; padding-left: 1.15rem; color: var(--muted); font-size: 0.92rem; }
.feature-list li { margin-bottom: 0.35rem; }
.price-annual { display: none; }
#billing-annual:checked ~ .tier-cards .price-monthly { display: none; }
#billing-annual:checked ~ .tier-cards .price-annual { display: inline; }
"""
    main_html = """    <section class="hero" id="section-1">
      <h1>MetricFlow Analytics — Simple Workspace Pricing</h1>
      <p>Product funnel analytics, session cohorts, and SQL-backed reporting for engineering and growth teams. Switch between monthly and annual billing below to view discounted annual rates.</p>
    </section>

    <section class="billing-switch-wrap" id="section-2" aria-label="Billing interval toggle">
      <input class="billing-radio" type="radio" name="billing-cycle" id="billing-monthly" checked>
      <input class="billing-radio" type="radio" name="billing-cycle" id="billing-annual">

      <div class="billing-toggle-bar" role="radiogroup" aria-label="Billing frequency">
        <label for="billing-monthly">Monthly billing</label>
        <label for="billing-annual">Annual billing <span class="save-pill">Save 20%</span></label>
      </div>

      <div class="tier-cards">
        <article class="tier-card">
          <h2>Starter</h2>
          <p class="prose-note">For early-stage products tracking core activation funnels.</p>
          <div class="tier-price">
            <span class="price-monthly">$15/mo</span>
            <span class="price-annual">$12/mo</span>
          </div>
          <p class="billing-caption">
            <span class="price-monthly">Billed monthly, cancel anytime</span>
            <span class="price-annual">Billed annually ($144/year)</span>
          </p>
          <ul class="feature-list">
            <li>250,000 tracked events per month</li>
            <li>6-month historical retention</li>
            <li>3 team members included</li>
          </ul>
        </article>

        <article class="tier-card featured">
          <h2>Pro</h2>
          <p class="prose-note">For growing teams running retention cohorts and SQL queries.</p>
          <div class="tier-price">
            <span class="price-monthly">$48/mo</span>
            <span class="price-annual">$38/mo</span>
          </div>
          <p class="billing-caption">
            <span class="price-monthly">Billed monthly, cancel anytime</span>
            <span class="price-annual">Billed annually ($456/year)</span>
          </p>
          <ul class="feature-list">
            <li>2,000,000 tracked events per month</li>
            <li>24-month historical retention</li>
            <li>Unlimited team seats &amp; warehouse sync</li>
          </ul>
        </article>

        <article class="tier-card">
          <h2>Business</h2>
          <p class="prose-note">For high-volume SaaS workspaces with governance controls.</p>
          <div class="tier-price">
            <span class="price-monthly">$140/mo</span>
            <span class="price-annual">$112/mo</span>
          </div>
          <p class="billing-caption">
            <span class="price-monthly">Billed monthly, cancel anytime</span>
            <span class="price-annual">Billed annually ($1,344/year)</span>
          </p>
          <ul class="feature-list">
            <li>15,000,000 tracked events per month</li>
            <li>60-month historical retention</li>
            <li>SSO, RBAC, and dedicated Slack channel</li>
          </ul>
        </article>
      </div>
    </section>

    <section class="card" id="section-3" style="margin-top: 1.5rem;">
      <h2 class="section-title">Annual Billing Policy</h2>
      <p class="prose-note">Annual subscriptions lock in a 20% discount across all plans for 12 months. Unused event quotas roll over for up to 30 days on Pro and Business plans.</p>
    </section>"""
    html = _render_shell(
        title="MetricFlow Analytics — Workspace Pricing",
        brand="MetricFlow",
        nav_items=["Overview", "Plans", "Billing Policy"],
        generated_date=generated_date,
        data_as_of=generated_date,
        extra_css=extra_css,
        main_html=main_html,
        footer_note="MetricFlow Analytics Inc. — Synthetic benchmark fixture",
        fixture_version=fixture_version,
    )
    return RenderedFixture(
        id="03",
        slug="03-pricing-toggle-css-radio",
        filename="03-pricing-toggle-css-radio.html",
        title="MetricFlow Analytics — Workspace Pricing",
        defect_section="Price Toggles",
        defect_class="monthly_annual_toggle",
        needle="$38/mo",
        needle_type="price",
        needle_context="Pro tier annual price inside .price-annual (display: none by default behind CSS radio toggle)",
        question="What is the monthly rate for the MetricFlow Pro plan when billed annually?",
        expected_answer="$38/mo",
        silent_wrong_answer="$48/mo",
        required_footnote=None,
        source="fixed",
        source_url=None,
        data_as_of=generated_date,
        html=html,
    )


def _page_04_pricing_toggle_tabpanel(generated_date: str, fixture_version: str) -> RenderedFixture:
    extra_css = """
.billing-tabs { position: relative; }
.tab-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}
.tablist {
  display: inline-flex;
  border-bottom: 2px solid var(--border);
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}
.tablist label {
  cursor: pointer;
  padding: 0.6rem 1.15rem;
  font-weight: 600;
  font-size: 0.94rem;
  color: var(--muted);
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}
#tab-monthly:checked ~ .tablist label[for="tab-monthly"],
#tab-annual:checked ~ .tablist label[for="tab-annual"] {
  color: var(--accent);
  border-bottom-color: var(--accent);
}
.plan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.25rem;
}
.plan-box {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.4rem;
}
.plan-box h3 { margin: 0 0 0.25rem; }
.plan-rate { font-size: 1.85rem; font-weight: 800; color: var(--text); margin: 0.65rem 0 0.2rem; }
.plan-meta { font-size: 0.85rem; color: var(--muted); margin: 0 0 0.85rem; }
#tab-annual:checked ~ .tab-panels #panel-monthly { display: none; }
#tab-annual:checked ~ .tab-panels #panel-annual[hidden] { display: block; }
"""
    main_html = """    <section class="hero" id="section-1">
      <h1>DeployKit CI — Hosted Build Runner Plans</h1>
      <p>Fast x86 and ARM64 Linux build runners with persistent layer caching, artifact retention, and zero queue times. Compare standard monthly rates and annual commitment discounts below.</p>
    </section>

    <section class="card billing-tabs" id="section-2">
      <h2 class="section-title">Select Billing Schedule</h2>
      <input class="tab-input" type="radio" name="deploykit-billing" id="tab-monthly" checked>
      <input class="tab-input" type="radio" name="deploykit-billing" id="tab-annual">

      <div class="tablist" role="tablist" aria-label="Billing schedule">
        <label role="tab" id="label-monthly" for="tab-monthly" aria-controls="panel-monthly" aria-selected="true">Monthly Billing</label>
        <label role="tab" id="label-annual" for="tab-annual" aria-controls="panel-annual" aria-selected="false">Annual Billing (20% Off)</label>
      </div>

      <div class="tab-panels">
        <div id="panel-monthly" role="tabpanel" aria-labelledby="label-monthly">
          <div class="plan-grid">
            <div class="plan-box">
              <h3>Developer</h3>
              <div class="plan-rate">$35/mo</div>
              <p class="plan-meta">Monthly subscription &middot; 2,500 build minutes</p>
              <p class="prose-note">4-core runners, 20 GB build cache, GitHub &amp; GitLab status checks.</p>
            </div>
            <div class="plan-box">
              <h3>Team</h3>
              <div class="plan-rate">$120/mo</div>
              <p class="plan-meta">Monthly subscription &middot; 12,000 build minutes</p>
              <p class="prose-note">8-core runners, 100 GB build cache, parallel matrix jobs, SOC 2 reports.</p>
            </div>
            <div class="plan-box">
              <h3>Scale</h3>
              <div class="plan-rate">$320/mo</div>
              <p class="plan-meta">Monthly subscription &middot; 40,000 build minutes</p>
              <p class="prose-note">16-core runners, private networking, SAML SSO, priority support.</p>
            </div>
          </div>
        </div>

        <div id="panel-annual" role="tabpanel" aria-labelledby="label-annual" hidden>
          <div class="plan-grid">
            <div class="plan-box">
              <h3>Developer</h3>
              <div class="plan-rate">$28/mo</div>
              <p class="plan-meta">Billed annually ($336/year) &middot; 2,500 build minutes</p>
              <p class="prose-note">4-core runners, 20 GB build cache, GitHub &amp; GitLab status checks.</p>
            </div>
            <div class="plan-box">
              <h3>Team</h3>
              <div class="plan-rate">$96/mo</div>
              <p class="plan-meta">Billed annually ($1,152/year) &middot; 12,000 build minutes</p>
              <p class="prose-note">8-core runners, 100 GB build cache, parallel matrix jobs, SOC 2 reports.</p>
            </div>
            <div class="plan-box">
              <h3>Scale</h3>
              <div class="plan-rate">$256/mo</div>
              <p class="plan-meta">Billed annually ($3,072/year) &middot; 40,000 build minutes</p>
              <p class="prose-note">16-core runners, private networking, SAML SSO, priority support.</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="card" id="section-3">
      <h2 class="section-title">Overages &amp; Concurrency</h2>
      <p class="prose-note">Additional build minutes above your monthly allowance are metered at $0.008 per vCPU-minute. Concurrent job caps can be raised on request for release sprints.</p>
    </section>"""
    html = _render_shell(
        title="DeployKit CI — Hosted Build Runner Plans",
        brand="DeployKit CI",
        nav_items=["Overview", "Plans", "Metering"],
        generated_date=generated_date,
        data_as_of=generated_date,
        extra_css=extra_css,
        main_html=main_html,
        footer_note="DeployKit Cloud Inc. — Synthetic benchmark fixture",
        fixture_version=fixture_version,
    )
    return RenderedFixture(
        id="04",
        slug="04-pricing-toggle-tabpanel",
        filename="04-pricing-toggle-tabpanel.html",
        title="DeployKit CI — Hosted Build Runner Plans",
        defect_section="Price Toggles",
        defect_class="monthly_annual_toggle",
        needle="$96/mo",
        needle_type="price",
        needle_context="Team tier annual price inside inactive ARIA role='tabpanel' with hidden attribute",
        question="What is the monthly rate for the DeployKit CI Team plan under annual billing?",
        expected_answer="$96/mo",
        silent_wrong_answer="$120/mo",
        required_footnote=None,
        source="fixed",
        source_url=None,
        data_as_of=generated_date,
        html=html,
    )


def _page_05_stat_footnote_tax(generated_date: str, fixture_version: str) -> RenderedFixture:
    extra_css = """
.quote-banner {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
  background: var(--accent-soft);
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}
.hero-figure {
  font-size: 2.4rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text);
}
.hero-figure sup {
  font-size: 0.48em;
  vertical-align: super;
  margin-left: 0.05em;
}
.hero-unit {
  font-size: 1rem;
  color: var(--muted);
  font-weight: 500;
}
.spec-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.85rem;
  list-style: none;
  padding: 0;
  margin: 0;
}
.spec-list li {
  background: var(--surface-alt);
  padding: 0.85rem 1rem;
  border-radius: 8px;
  font-size: 0.92rem;
}
.spec-list strong { display: block; color: var(--text); margin-bottom: 0.15rem; }
"""
    main_html = """    <section class="hero" id="section-1">
      <h1>VectorHost Dedicated — Managed Inference Node</h1>
      <p>Single-tenant bare-metal GPU infrastructure for low-latency model serving, private embeddings, and batch fine-tuning in Frankfurt (eu-central-1) and Virginia (us-east-1).</p>
    </section>

    <section class="quote-banner" id="section-2" aria-label="Monthly node rate">
      <div>
        <div class="prose-note">Standard Reserved Monthly Rate (Node VH-A100-4x)</div>
        <div>
          <span class="hero-figure">$1,250<sup><a href="#fn-1" id="fnref-1" aria-label="Footnote 1">1</a></sup></span>
          <span class="hero-unit">per month</span>
        </div>
      </div>
      <div class="prose-note">99.95% uptime SLA &middot; Direct 25 Gbps private uplink</div>
    </section>

    <section class="card" id="section-3">
      <h2 class="section-title">Hardware Specifications</h2>
      <ul class="spec-list">
        <li><strong>Accelerators</strong>4 &times; 80 GB PCIe Compute GPUs</li>
        <li><strong>Host Compute</strong>64-core EPYC CPU &middot; 512 GB ECC RAM</li>
        <li><strong>Local Storage</strong>7.68 TB RAID-10 NVMe Scratch</li>
        <li><strong>Bandwidth</strong>50 TB monthly outbound included</li>
      </ul>
    </section>

    <section class="card">
      <h2 class="section-title">Deployment &amp; Billing Terms</h2>
      <p class="prose-note">Nodes are provisioned within 4 hours of order confirmation with Ubuntu LTS or container-optimized images. Invoices are issued on the first calendar day of each month via wire transfer or corporate card.</p>
    </section>

    <aside class="footnotes" role="doc-endnotes" aria-label="Footnotes">
      <h2>Footnotes</h2>
      <ol>
        <li id="fn-1">All listed cluster rates are quoted in USD, <strong>excluding 20% VAT</strong> and any applicable local digital services taxes. Customers in the European Union without a reverse-charge VAT ID are invoiced VAT at the standard statutory rate. <a href="#fnref-1" aria-label="Back to content">&#8617;</a></li>
      </ol>
    </aside>"""
    html = _render_shell(
        title="VectorHost Dedicated — Managed Inference Node Pricing",
        brand="VectorHost",
        nav_items=["Overview", "Pricing", "Hardware"],
        generated_date=generated_date,
        data_as_of=generated_date,
        extra_css=extra_css,
        main_html=main_html,
        footer_note="VectorHost Infrastructure GmbH — Synthetic benchmark fixture",
        fixture_version=fixture_version,
    )
    return RenderedFixture(
        id="05",
        slug="05-stat-footnote-tax",
        filename="05-stat-footnote-tax.html",
        title="VectorHost Dedicated — Managed Inference Node Pricing",
        defect_section="Footnotes",
        defect_class="stat_with_footnote",
        needle="$1,250",
        needle_type="price",
        needle_context="Monthly node rate with adjacent <sup>1</sup> and tax-exclusion footnote inside <aside role='doc-endnotes'> (incl. 20% VAT is $1,500)",
        question="What is the monthly price for the VectorHost VH-A100-4x node, and does it include VAT?",
        expected_answer="$1,250/month excluding 20% VAT ($1,500/month including 20% VAT)",
        silent_wrong_answer="$1,250/month (omits 20% VAT exclusion or merges superscript into $1,2501)",
        required_footnote="excluding 20% VAT",
        source="fixed",
        source_url=None,
        data_as_of=generated_date,
        html=html,
    )


def _page_06_stat_footnote_aave_tvl(
    live_data: dict[str, Any], generated_date: str, fixture_version: str
) -> RenderedFixture:
    aave = live_data["aave_tvl"]
    formatted_tvl = aave["formatted_tvl"]
    data_as_of = aave["data_as_of"]

    extra_css = """
.kpi-hero {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.75rem;
  margin-bottom: 1.5rem;
}
.kpi-label {
  font-size: 0.86rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
}
.kpi-number {
  margin: 0.35rem 0 0.5rem;
  font-size: 2.6rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text);
}
.kpi-number sup {
  font-size: 0.45em;
  vertical-align: super;
  margin-left: 0.05em;
}
.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  font-size: 0.9rem;
  color: var(--muted);
}
"""
    main_html = f"""    <section class="hero" id="section-1">
      <h1>DeFi Benchmark Desk — Aave Protocol Liquidity Overview</h1>
      <p>Independent cross-chain liquidity snapshot tracking Aave v2 and v3 lending markets across Ethereum mainnet, Arbitrum, Optimism, Polygon, Base, and Avalanche.</p>
    </section>

    <section class="kpi-hero" id="section-2" aria-label="Headline TVL figure">
      <div class="kpi-label">Aave Protocol Total Value Locked (USD)</div>
      <div class="kpi-number">{escape(formatted_tvl)}<sup><a href="#fn-1" id="fnref-1" aria-label="Methodology footnote 1">1</a></sup></div>
      <div class="meta-row">
        <span>Category: Decentralized Lending</span>
        <span>Data provider: DeFiLlama Public API</span>
        <span>Snapshot date: {escape(data_as_of)}</span>
      </div>
    </section>

    <section class="card" id="section-3">
      <h2 class="section-title">Market Structure Context</h2>
      <p class="prose-note">Lending protocol liquidity metrics vary substantially depending on whether outstanding loans, staked governance tokens, and recursive loop positions are included. Analysts comparing protocols should always retain the methodology qualifier attached to headline TVL numbers.</p>
    </section>

    <aside class="footnotes" role="doc-endnotes" aria-label="Methodology footnotes">
      <h2>Methodology Footnotes</h2>
      <ol>
        <li id="fn-1">Headline TVL reflects net collateral deposited in active smart contracts, <strong>excluding borrowed liquidity and pool2 staking</strong> per DeFiLlama standard TVL methodology. Including active borrowed balances increases gross market size materially. <a href="#fnref-1" aria-label="Back to content">&#8617;</a></li>
      </ol>
    </aside>"""
    html = _render_shell(
        title="DeFi Benchmark Desk — Aave Protocol Liquidity Overview",
        brand="DeFi Benchmark Desk",
        nav_items=["Overview", "Headline TVL", "Methodology"],
        generated_date=generated_date,
        data_as_of=data_as_of,
        extra_css=extra_css,
        main_html=main_html,
        footer_note="Data sourced at build time from DeFiLlama API — Benchmark fixture",
        fixture_version=fixture_version,
    )
    return RenderedFixture(
        id="06",
        slug="06-stat-footnote-aave-tvl",
        filename="06-stat-footnote-aave-tvl.html",
        title="DeFi Benchmark Desk — Aave Protocol Liquidity Overview",
        defect_section="Footnotes",
        defect_class="stat_with_footnote",
        needle=formatted_tvl,
        needle_type="stat",
        needle_context="Live Aave TVL from DeFiLlama with adjacent <sup>1</sup> and methodology exclusion footnote in <aside role='doc-endnotes'>",
        question="What is Aave's headline TVL on this page, and does it include borrowed liquidity?",
        expected_answer=f"{formatted_tvl} (excluding borrowed liquidity and pool2 staking)",
        silent_wrong_answer=f"{formatted_tvl} (omits borrowed liquidity exclusion or merges superscript into {formatted_tvl}1)",
        required_footnote="excluding borrowed liquidity and pool2 staking",
        source=aave["source"],
        source_url=aave["source_url"],
        data_as_of=data_as_of,
        html=html,
    )


def _page_07_changelog_table_fastapi(
    live_data: dict[str, Any], generated_date: str, fixture_version: str
) -> RenderedFixture:
    rel_data = live_data["fastapi_releases"]
    latest_version = rel_data["latest_version"]
    data_as_of = rel_data["data_as_of"]

    rows_html: list[str] = []
    for idx, rel in enumerate(rel_data["releases"]):
        ver = rel["version"]
        date = rel["published_date"]
        badge_class = "version-pill latest" if idx == 0 else "version-pill"
        bullets = "".join(f"<li>{escape(item)}</li>" for item in rel["highlights"])
        rows_html.append(
            f"""            <tr>
              <th scope="row" class="col-version sticky-col">
                <span class="{badge_class}">{escape(ver)}</span>
              </th>
              <td class="col-date"><time datetime="{escape(date)}">{escape(date)}</time></td>
              <td><ul class="changelog-bullets">{bullets}</ul></td>
            </tr>"""
        )

    extra_css = """
.col-version { white-space: nowrap; width: 130px; }
.col-date { white-space: nowrap; width: 130px; color: var(--muted); font-size: 0.9rem; }
.version-pill {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 6px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.88rem;
  font-weight: 700;
  background: var(--badge-bg);
  color: var(--text);
}
.version-pill.latest {
  background: var(--accent-soft);
  color: var(--accent);
  border: 1px solid #bfdbfe;
}
.changelog-bullets {
  margin: 0;
  padding-left: 1.1rem;
  font-size: 0.92rem;
}
.changelog-bullets li { margin-bottom: 0.25rem; }
"""
    main_html = f"""    <section class="hero" id="section-1">
      <h1>FastAPI — Recent Release Changelog</h1>
      <p>Summary of the latest published releases from the upstream <code>fastapi/fastapi</code> GitHub repository. The top row reflects the most recent stable release available for production upgrades.</p>
    </section>

    <section class="card" id="section-2">
      <h2 class="section-title">Published Releases</h2>
      <div class="table-scroll">
        <table class="changelog-table" aria-label="FastAPI release history">
          <thead>
            <tr>
              <th scope="col" class="col-version sticky-col">Version</th>
              <th scope="col">Release Date</th>
              <th scope="col">Release Highlights</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(rows_html)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="card" id="section-3">
      <h2 class="section-title">Upgrade Guidance</h2>
      <p class="prose-note">Pin exact framework versions in production lockfiles and review middleware or request-parsing defaults before rolling out minor upgrades across API gateways.</p>
    </section>"""
    html = _render_shell(
        title="FastAPI — Recent Release Changelog",
        brand="FastAPI Release Tracker",
        nav_items=["Overview", "Releases", "Upgrade Guide"],
        generated_date=generated_date,
        data_as_of=data_as_of,
        extra_css=extra_css,
        main_html=main_html,
        footer_note="Release metadata fetched at build time from GitHub Releases API",
        fixture_version=fixture_version,
    )
    top_highlight = rel_data["releases"][0]["highlights"][0]
    prev_version = rel_data["releases"][1]["version"] if len(rel_data["releases"]) > 1 else "unknown"
    return RenderedFixture(
        id="07",
        slug="07-changelog-table-fastapi",
        filename="07-changelog-table-fastapi.html",
        title="FastAPI — Recent Release Changelog",
        defect_section="Version Columns",
        defect_class="versioned_changelog",
        needle=latest_version,
        needle_type="version",
        needle_context="Latest FastAPI release version in sticky <th scope='row' class='col-version sticky-col'> first column of changelog table",
        question=f"Which FastAPI release version introduced: {top_highlight}",
        expected_answer=latest_version,
        silent_wrong_answer=f"{prev_version} (wrong row) or unknown",
        required_footnote=None,
        source=rel_data["source"],
        source_url=rel_data["source_url"],
        data_as_of=data_as_of,
        html=html,
    )


def _page_08_changelog_timeline_ruff(
    live_data: dict[str, Any], generated_date: str, fixture_version: str
) -> RenderedFixture:
    rel_data = live_data["ruff_releases"]
    latest_version = rel_data["latest_version"]
    data_as_of = rel_data["data_as_of"]

    entries_html: list[str] = []
    for idx, rel in enumerate(rel_data["releases"]):
        ver = rel["version"]
        date = rel["published_date"]
        tag_label = "Latest stable" if idx == 0 else "Release"
        bullets = "".join(f"<li>{escape(item)}</li>" for item in rel["highlights"])
        entries_html.append(
            f"""      <article class="release-entry">
        <aside class="release-meta" aria-label="Release version metadata">
          <div class="version-badge">{escape(ver)}</div>
          <time class="release-date" datetime="{escape(date)}">{escape(date)}</time>
          <span class="release-tag">{tag_label}</span>
        </aside>
        <div class="release-notes">
          <h3>Changes in this release</h3>
          <ul>{bullets}</ul>
        </div>
      </article>"""
        )

    extra_css = """
.timeline { display: flex; flex-direction: column; gap: 1.25rem; }
.release-entry {
  display: grid;
  grid-template-columns: 165px 1fr;
  gap: 1.5rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.35rem 1.5rem;
}
.release-meta {
  position: sticky;
  top: 1rem;
  align-self: start;
  border-right: 1px solid var(--border);
  padding-right: 1rem;
}
.version-badge {
  display: inline-block;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid #bfdbfe;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
}
.release-date {
  display: block;
  margin-top: 0.45rem;
  font-size: 0.85rem;
  color: var(--muted);
}
.release-tag {
  display: inline-block;
  margin-top: 0.35rem;
  font-size: 0.76rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.release-notes h3 { margin: 0 0 0.5rem; font-size: 1rem; }
.release-notes ul { margin: 0; padding-left: 1.15rem; font-size: 0.93rem; }
.release-notes li { margin-bottom: 0.3rem; }
@media (max-width: 640px) {
  .release-entry { grid-template-columns: 1fr; }
  .release-meta { position: static; border-right: none; border-bottom: 1px solid var(--border); padding: 0 0 0.75rem; }
}
"""
    main_html = f"""    <section class="hero" id="section-1">
      <h1>Ruff — Linter &amp; Formatter Changelog</h1>
      <p>Chronological release stream for <code>astral-sh/ruff</code>. Each entry pairs the release version in the sticky left rail with key rule fixes and performance changes.</p>
    </section>

    <section class="timeline" id="section-2" aria-label="Ruff release timeline">
{chr(10).join(entries_html)}
    </section>"""
    html = _render_shell(
        title="Ruff — Linter & Formatter Changelog",
        brand="Ruff Changelog",
        nav_items=["Overview", "Release Timeline"],
        generated_date=generated_date,
        data_as_of=data_as_of,
        extra_css=extra_css,
        main_html=main_html,
        footer_note="Release metadata fetched at build time from GitHub Releases API",
        fixture_version=fixture_version,
    )
    top_highlight = rel_data["releases"][0]["highlights"][0]
    prev_version = rel_data["releases"][1]["version"] if len(rel_data["releases"]) > 1 else "unknown"
    return RenderedFixture(
        id="08",
        slug="08-changelog-timeline-ruff",
        filename="08-changelog-timeline-ruff.html",
        title="Ruff — Linter & Formatter Changelog",
        defect_section="Version Columns",
        defect_class="versioned_changelog",
        needle=latest_version,
        needle_type="version",
        needle_context="Latest Ruff release version in sticky left <aside class='release-meta'> column of two-column timeline changelog",
        question=f"Which Ruff release version included: {top_highlight}",
        expected_answer=latest_version,
        silent_wrong_answer=f"{prev_version} (wrong row) or unknown",
        required_footnote=None,
        source=rel_data["source"],
        source_url=rel_data["source_url"],
        data_as_of=data_as_of,
        html=html,
    )


def _page_09_docs_tabs_next(
    live_data: dict[str, Any], generated_date: str, fixture_version: str
) -> RenderedFixture:
    npm_next = live_data["npm_next"]
    version = npm_next["latest_version"]
    data_as_of = npm_next["data_as_of"]
    pinned_cmd = f"pnpm add next@{version}"

    extra_css = """
.code-tabs {
  position: relative;
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  background: var(--surface);
}
.code-tab-radio {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}
.code-tab-bar {
  display: flex;
  background: var(--surface-alt);
  border-bottom: 1px solid var(--border);
  padding: 0 0.5rem;
}
.code-tab-bar label {
  cursor: pointer;
  padding: 0.65rem 1rem;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--muted);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}
#pkg-npm:checked ~ .code-tab-bar label[for="pkg-npm"],
#pkg-pnpm:checked ~ .code-tab-bar label[for="pkg-pnpm"],
#pkg-yarn:checked ~ .code-tab-bar label[for="pkg-yarn"] {
  color: var(--accent);
  border-bottom-color: var(--accent);
  background: var(--surface);
}
.code-tab-panel {
  display: none;
  padding: 1.15rem;
}
#pkg-npm:checked ~ .code-tab-panels .panel-npm,
#pkg-pnpm:checked ~ .code-tab-panels .panel-pnpm,
#pkg-yarn:checked ~ .code-tab-panels .panel-yarn {
  display: block;
}
.panel-caption {
  margin: 0 0 0.75rem;
  font-size: 0.9rem;
  color: var(--muted);
}
"""
    main_html = f"""    <section class="hero" id="section-1">
      <h1>Next.js — Installation &amp; Pinned Upgrade Guide</h1>
      <p>Install the Next.js framework in a new or existing Node.js workspace. Use the package-manager tabs below to choose between floating latest installs or an exact registry-pinned lockfile install.</p>
    </section>

    <section class="card" id="section-2">
      <h2 class="section-title">Install Next.js</h2>
      <p class="prose-note">Requires Node.js 20.9 or later. Switch to the <strong>pnpm (Pinned)</strong> tab when reproducing an exact production build version.</p>

      <div class="code-tabs">
        <input class="code-tab-radio" type="radio" name="next-pkg-mgr" id="pkg-npm" checked>
        <input class="code-tab-radio" type="radio" name="next-pkg-mgr" id="pkg-pnpm">
        <input class="code-tab-radio" type="radio" name="next-pkg-mgr" id="pkg-yarn">

        <div class="code-tab-bar" role="tablist" aria-label="Package manager">
          <label role="tab" for="pkg-npm" aria-selected="true">npm</label>
          <label role="tab" for="pkg-pnpm" aria-selected="false">pnpm (Pinned)</label>
          <label role="tab" for="pkg-yarn" aria-selected="false">yarn</label>
        </div>

        <div class="code-tab-panels">
          <div class="code-tab-panel panel-npm" role="tabpanel">
            <p class="panel-caption">Install the floating latest dist-tag with npm:</p>
            <pre><code>npm install next@latest react@latest react-dom@latest</code></pre>
          </div>

          <div class="code-tab-panel panel-pnpm" role="tabpanel">
            <p class="panel-caption">Pin the exact current npm registry release with pnpm:</p>
            <pre><code>{escape(pinned_cmd)}

# package.json excerpt
{{
  "dependencies": {{
    "next": "{escape(version)}"
  }}
}}</code></pre>
          </div>

          <div class="code-tab-panel panel-yarn" role="tabpanel">
            <p class="panel-caption">Install the floating latest dist-tag with Yarn:</p>
            <pre><code>yarn add next@latest react@latest react-dom@latest</code></pre>
          </div>
        </div>
      </div>
    </section>

    <section class="card" id="section-3">
      <h2 class="section-title">Verify Scripts</h2>
      <p class="prose-note">After installation, ensure your <code>package.json</code> defines <code>dev</code>, <code>build</code>, and <code>start</code> scripts invoking the <code>next</code> CLI binary.</p>
    </section>"""
    html = _render_shell(
        title="Next.js — Installation & Pinned Upgrade Guide",
        brand="Next.js Docs",
        nav_items=["Overview", "Installation", "Scripts"],
        generated_date=generated_date,
        data_as_of=data_as_of,
        extra_css=extra_css,
        main_html=main_html,
        footer_note="Version fetched at build time from npm Registry API — Benchmark fixture",
        fixture_version=fixture_version,
    )
    return RenderedFixture(
        id="09",
        slug="09-docs-tabs-next",
        filename="09-docs-tabs-next.html",
        title="Next.js — Installation & Pinned Upgrade Guide",
        defect_section="Tabbed Code",
        defect_class="tabbed_code_docs",
        needle=pinned_cmd,
        needle_type="code",
        needle_context="Live Next.js pinned pnpm install command located exclusively inside second code tab (display: none by default)",
        question="What is the exact pinned pnpm command shown for installing the current Next.js release?",
        expected_answer=pinned_cmd,
        silent_wrong_answer="npm install next@latest or unknown",
        required_footnote=None,
        source=npm_next["source"],
        source_url=npm_next["source_url"],
        data_as_of=data_as_of,
        html=html,
    )


def _page_10_docs_tabs_pydantic(
    live_data: dict[str, Any], generated_date: str, fixture_version: str
) -> RenderedFixture:
    pypi = live_data["pypi_pydantic"]
    version = pypi["latest_version"]
    requires_python = pypi["requires_python"]
    data_as_of = pypi["data_as_of"]
    pinned_spec = f"pydantic=={version}"

    extra_css = """
.aria-tabs {
  position: relative;
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  background: var(--surface);
}
.aria-tab-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}
.aria-tablist {
  display: flex;
  background: var(--surface-alt);
  border-bottom: 1px solid var(--border);
  padding: 0 0.5rem;
}
.aria-tablist label {
  cursor: pointer;
  padding: 0.65rem 1rem;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--muted);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}
#py-pip:checked ~ .aria-tablist label[for="py-pip"],
#py-uv:checked ~ .aria-tablist label[for="py-uv"] {
  color: var(--accent);
  border-bottom-color: var(--accent);
  background: var(--surface);
}
.aria-tabpanel { padding: 1.15rem; }
#py-uv:checked ~ .aria-tabpanels #panel-pip { display: none; }
#py-uv:checked ~ .aria-tabpanels #panel-uv[hidden] { display: block; }
"""
    main_html = f"""    <section class="hero" id="section-1">
      <h1>Pydantic — Python Installation &amp; Lockfile Pinning</h1>
      <p>Data validation using Python type hints, backed by a Rust core validator. Supported Python versions: <code>{escape(requires_python)}</code>.</p>
    </section>

    <section class="card" id="section-2">
      <h2 class="section-title">Install Package</h2>
      <p class="prose-note">Choose <strong>pip</strong> for quick local prototyping or open the <strong>uv / requirements.txt (Pinned)</strong> tab for reproducible CI deployments.</p>

      <div class="aria-tabs">
        <input class="aria-tab-input" type="radio" name="pydantic-installer" id="py-pip" checked>
        <input class="aria-tab-input" type="radio" name="pydantic-installer" id="py-uv">

        <div class="aria-tablist" role="tablist" aria-label="Python package installer">
          <label role="tab" id="tab-pip" for="py-pip" aria-controls="panel-pip" aria-selected="true">pip</label>
          <label role="tab" id="tab-uv" for="py-uv" aria-controls="panel-uv" aria-selected="false">uv / requirements.txt (Pinned)</label>
        </div>

        <div class="aria-tabpanels">
          <div id="panel-pip" class="aria-tabpanel" role="tabpanel" aria-labelledby="tab-pip">
            <p class="prose-note" style="margin-top:0;">Install the latest compatible release via pip:</p>
            <pre><code>pip install pydantic</code></pre>
          </div>

          <div id="panel-uv" class="aria-tabpanel" role="tabpanel" aria-labelledby="tab-uv" hidden aria-hidden="true">
            <p class="prose-note" style="margin-top:0;">Pin the exact current PyPI release in uv or requirements.txt:</p>
            <pre><code>uv add "{escape(pinned_spec)}"

# requirements.txt
{escape(pinned_spec)}</code></pre>
          </div>
        </div>
      </div>
    </section>

    <section class="card" id="section-3">
      <h2 class="section-title">Quick Validation Example</h2>
      <pre><code>from pydantic import BaseModel

class Invoice(BaseModel):
    account_id: int
    currency: str = "USD"
    amount_cents: int</code></pre>
    </section>"""
    html = _render_shell(
        title="Pydantic — Python Installation & Lockfile Pinning",
        brand="Pydantic Docs",
        nav_items=["Overview", "Install", "Example"],
        generated_date=generated_date,
        data_as_of=data_as_of,
        extra_css=extra_css,
        main_html=main_html,
        footer_note="Version fetched at build time from PyPI JSON API — Benchmark fixture",
        fixture_version=fixture_version,
    )
    return RenderedFixture(
        id="10",
        slug="10-docs-tabs-pydantic",
        filename="10-docs-tabs-pydantic.html",
        title="Pydantic — Python Installation & Lockfile Pinning",
        defect_section="Tabbed Code",
        defect_class="tabbed_code_docs",
        needle=pinned_spec,
        needle_type="code",
        needle_context="Live Pydantic requirements.txt pin string located exclusively inside second ARIA tabpanel (hidden aria-hidden='true')",
        question="What exact requirements.txt version pin string is shown for Pydantic?",
        expected_answer=pinned_spec,
        silent_wrong_answer="pip install pydantic or unknown",
        required_footnote=None,
        source=pypi["source"],
        source_url=pypi["source_url"],
        data_as_of=data_as_of,
        html=html,
    )


def _page_11_loading_placeholder_lido_tvl(
    live_data: dict[str, Any], generated_date: str, fixture_version: str
) -> RenderedFixture:
    lido = live_data["lido_tvl"]
    formatted_tvl = lido["formatted_tvl"]
    data_as_of = lido["data_as_of"]

    extra_css = """
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}
.metric-loader {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.5rem;
}
.metric-label {
  font-size: 0.84rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  margin-bottom: 0.45rem;
}
.skeleton-placeholder {
  display: inline-block;
  padding: 0.3rem 0.65rem;
  border-radius: 6px;
  background: var(--surface-alt);
  color: var(--muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.95rem;
}
.metric-loader[data-state="loaded"] .skeleton-placeholder {
  display: none;
}
.metric-value {
  display: block;
  font-size: 2.35rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text);
}
.metric-sub {
  margin-top: 0.35rem;
  font-size: 0.85rem;
  color: var(--muted);
}
"""
    main_html = f"""    <section class="hero" id="section-1">
      <h1>Staking Pulse — Lido Protocol Live TVL</h1>
      <p>Real-time staking telemetry for the Lido liquid staking protocol. Metric cards below are pre-rendered in their hydrated state with build-time values from DeFiLlama.</p>
    </section>

    <section class="dashboard-grid" id="section-2" aria-label="Lido protocol telemetry">
      <div class="metric-loader" data-state="loaded" aria-busy="false">
        <div class="metric-label">Lido Total Value Locked (USD)</div>
        <span class="skeleton-placeholder" role="status" aria-hidden="true">Loading TVL...</span>
        <output class="metric-value" aria-live="polite">{escape(formatted_tvl)}</output>
        <div class="metric-sub">Source: DeFiLlama &middot; Status: Synchronized</div>
      </div>

      <div class="metric-loader" data-state="loaded" aria-busy="false">
        <div class="metric-label">Primary Staking Asset</div>
        <span class="skeleton-placeholder" role="status" aria-hidden="true">Loading asset...</span>
        <output class="metric-value" aria-live="polite">stETH</output>
        <div class="metric-sub">Liquid staking receipt token on Ethereum</div>
      </div>
    </section>

    <section class="card" id="section-3">
      <h2 class="section-title">How Staking TVL Is Reported</h2>
      <p class="prose-note">Lido protocol TVL aggregates USD value of staked assets deposited across active validator pools as tracked by the DeFiLlama protocol feed. Values are baked directly into static HTML during scheduled builds.</p>
    </section>"""
    html = _render_shell(
        title="Staking Pulse — Lido Protocol Live TVL",
        brand="Staking Pulse",
        nav_items=["Overview", "Telemetry", "Notes"],
        generated_date=generated_date,
        data_as_of=data_as_of,
        extra_css=extra_css,
        main_html=main_html,
        footer_note="TVL fetched at build time from DeFiLlama API — Benchmark fixture",
        fixture_version=fixture_version,
    )
    return RenderedFixture(
        id="11",
        slug="11-loading-placeholder-lido-tvl",
        filename="11-loading-placeholder-lido-tvl.html",
        title="Staking Pulse — Lido Protocol Live TVL",
        defect_section="Loading Placeholders",
        defect_class="loading_placeholder",
        needle=formatted_tvl,
        needle_type="stat",
        needle_context="Live Lido TVL in <output aria-live='polite'> next to CSS-hidden .skeleton-placeholder ('Loading TVL...') inside [data-state='loaded']",
        question="What is Lido's Total Value Locked (USD) reported on this page?",
        expected_answer=formatted_tvl,
        silent_wrong_answer="Loading TVL...",
        required_footnote=None,
        source=lido["source"],
        source_url=lido["source_url"],
        data_as_of=data_as_of,
        html=html,
    )


def _page_12_loading_placeholder_react(
    live_data: dict[str, Any], generated_date: str, fixture_version: str
) -> RenderedFixture:
    npm_react = live_data["npm_react"]
    version = npm_react["latest_version"]
    data_as_of = npm_react["data_as_of"]

    extra_css = """
.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}
.registry-status-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.5rem;
}
.status-label {
  font-size: 0.84rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  margin-bottom: 0.45rem;
}
.placeholder-dash {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 1.5rem;
  color: var(--muted);
}
.registry-status-card[data-hydrated="true"] .placeholder-dash {
  display: none;
}
.version-readout {
  display: inline-block;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 2.15rem;
  font-weight: 800;
  color: var(--accent);
}
.status-meta {
  margin-top: 0.45rem;
  font-size: 0.86rem;
  color: var(--muted);
}
"""
    main_html = f"""    <section class="hero" id="section-1">
      <h1>Package Telemetry — React npm Release Status</h1>
      <p>Build-time registry telemetry tracking the current stable <code>latest</code> dist-tag for the <code>react</code> package on the public npm registry.</p>
    </section>

    <section class="status-grid" id="section-2" aria-label="Registry release status">
      <div class="registry-status-card" data-hydrated="true" aria-busy="false">
        <div class="status-label">React Stable Release (npm dist-tag: latest)</div>
        <div class="loading-state" hidden>
          <span>Fetching latest release... (v0.0.0-loading)</span>
        </div>
        <span class="placeholder-dash" aria-hidden="true">--</span>
        <div class="loaded-state">
          <data class="version-readout" value="{escape(version)}">v{escape(version)}</data>
        </div>
        <div class="status-meta">Published: {escape(data_as_of)} &middot; Registry: registry.npmjs.org</div>
      </div>

      <div class="registry-status-card" data-hydrated="true" aria-busy="false">
        <div class="status-label">Package License &amp; Distribution</div>
        <div class="loading-state" hidden>
          <span>Loading package metadata...</span>
        </div>
        <div class="loaded-state">
          <data class="version-readout" value="MIT" style="color: var(--text);">MIT</data>
        </div>
        <div class="status-meta">Public npm registry &middot; ESM &amp; CJS builds</div>
      </div>
    </section>

    <section class="card" id="section-3">
      <h2 class="section-title">Release Verification</h2>
      <p class="prose-note">Before upgrading React in production applications, verify that <code>react</code> and <code>react-dom</code> resolve to matching exact versions in your lockfile.</p>
    </section>"""
    html = _render_shell(
        title="Package Telemetry — React npm Release Status",
        brand="Package Telemetry",
        nav_items=["Overview", "Release Status", "Verification"],
        generated_date=generated_date,
        data_as_of=data_as_of,
        extra_css=extra_css,
        main_html=main_html,
        footer_note="Version fetched at build time from npm Registry API — Benchmark fixture",
        fixture_version=fixture_version,
    )
    return RenderedFixture(
        id="12",
        slug="12-loading-placeholder-react",
        filename="12-loading-placeholder-react.html",
        title="Package Telemetry — React npm Release Status",
        defect_section="Loading Placeholders",
        defect_class="loading_placeholder",
        needle=version,
        needle_type="version",
        needle_context="Live React version in <data class='version-readout'> alongside hidden .loading-state ('v0.0.0-loading') and CSS-hidden '--' placeholder",
        question="What is the latest stable React npm release version shown on this page?",
        expected_answer=version,
        silent_wrong_answer="v0.0.0-loading or --",
        required_footnote=None,
        source=npm_react["source"],
        source_url=npm_react["source_url"],
        data_as_of=data_as_of,
        html=html,
    )


def render_all_fixtures(
    live_data: dict[str, Any],
    generated_date: str,
    fixture_version: str = "v1",
) -> list[RenderedFixture]:
    """Render all 12 static benchmark fixture pages."""
    return [
        _page_01_pricing_table_rowheader(generated_date, fixture_version),
        _page_02_pricing_table_grid(generated_date, fixture_version),
        _page_03_pricing_toggle_css_radio(generated_date, fixture_version),
        _page_04_pricing_toggle_tabpanel(generated_date, fixture_version),
        _page_05_stat_footnote_tax(generated_date, fixture_version),
        _page_06_stat_footnote_aave_tvl(live_data, generated_date, fixture_version),
        _page_07_changelog_table_fastapi(live_data, generated_date, fixture_version),
        _page_08_changelog_timeline_ruff(live_data, generated_date, fixture_version),
        _page_09_docs_tabs_next(live_data, generated_date, fixture_version),
        _page_10_docs_tabs_pydantic(live_data, generated_date, fixture_version),
        _page_11_loading_placeholder_lido_tvl(live_data, generated_date, fixture_version),
        _page_12_loading_placeholder_react(live_data, generated_date, fixture_version),
    ]


def render_version_index(
    fixtures: list[RenderedFixture],
    generated_date: str,
    fixture_version: str,
) -> str:
    """Render /v1/index.html listing all 12 fixtures grouped by defect section."""
    rows: list[str] = []
    for fx in fixtures:
        rows.append(
            f"""          <tr>
            <td><code>{escape(fx.id)}</code></td>
            <td>{escape(fx.defect_section)}</td>
            <td><a href="./{escape(fx.filename)}">{escape(fx.title)}</a></td>
            <td><code>{escape(fx.needle_type)}</code></td>
            <td>{escape(fx.source)}</td>
            <td>{escape(fx.data_as_of)}</td>
          </tr>"""
        )

    main_html = f"""    <section class="hero" id="section-1">
      <h1>Markdown Converter Benchmark — Fixture Set {escape(fixture_version)}</h1>
      <p>12 static HTML benchmark pages grouped across 6 real-world defect types for evaluating Firecrawl, Crawl4AI, and Jina Reader. Machine-readable ground truth is published in <a href="./needles.json"><code>needles.json</code></a>.</p>
    </section>

    <section class="card" id="section-2">
      <h2 class="section-title">Fixture Catalog ({len(fixtures)} pages)</h2>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Defect Section</th>
              <th>Fixture Page</th>
              <th>Needle Type</th>
              <th>Source</th>
              <th>Data As Of</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(rows)}
          </tbody>
        </table>
      </div>
    </section>"""
    return _render_shell(
        title=f"Markdown Converter Benchmark — Fixtures ({fixture_version})",
        brand="test.bachwidy.site",
        nav_items=["Overview", "Catalog"],
        generated_date=generated_date,
        data_as_of=generated_date,
        extra_css="",
        main_html=main_html,
        footer_note="Static benchmark fixture catalog",
        fixture_version=fixture_version,
    )


def render_root_index(generated_date: str, fixture_version: str) -> str:
    """Render top-level /index.html linking to the versioned fixture directory."""
    main_html = f"""    <section class="hero" id="section-1">
      <h1>Markdown Converter Accuracy Fixtures</h1>
      <p>Versioned static HTML test fixtures for evaluating whether HTML-to-Markdown converters preserve numeric facts across real-world page structures.</p>
    </section>

    <section class="card" id="section-2">
      <h2 class="section-title">Available Fixture Sets</h2>
      <ul>
        <li><a href="./{escape(fixture_version)}/index.html"><strong>{escape(fixture_version)}</strong> — 12 fixture pages across 6 defect classes</a> (<a href="./{escape(fixture_version)}/needles.json"><code>needles.json</code></a>)</li>
      </ul>
    </section>"""
    return _render_shell(
        title="Markdown Converter Accuracy Fixtures — test.bachwidy.site",
        brand="test.bachwidy.site",
        nav_items=["Overview", "Versions"],
        generated_date=generated_date,
        data_as_of=generated_date,
        extra_css="",
        main_html=main_html,
        footer_note="Static files ready for deployment to test.bachwidy.site",
        fixture_version=fixture_version,
    )
