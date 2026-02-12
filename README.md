# KoinX Blog Tax Content Auditor

An automated tool that audits KoinX cryptocurrency tax blog posts against current US tax laws and IRS guidance, identifying outdated, inaccurate, or incomplete content.

## Features

- **Automated Blog Crawling**: Fetches posts from KoinX blog via WordPress REST API (Tax Guides category, US-only filtering)
- **AI-Powered Analysis**: Uses Mistral AI (`mistral-large-latest`) to detect tax law accuracy gaps
- **IRS Reference Integration**: Scrapes IRS.gov for current guidance + comprehensive hardcoded tax rules
- **Multi-Factor Confidence Scoring**: Combines LLM confidence, post age, source specificity, issue type, and cross-references
- **Change Detection**: Tracks new, recurring, and resolved findings across runs using SHA-256 content hashing
- **Excel Reports**: Color-coded priority reports with hyperlinks, auto-filters, and multiple sheets
- **Daily Scheduling**: APScheduler cron job for automated daily audits at 2 AM

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  WP REST API │────▶│ Content      │────▶│ Content Chunker │
│  (Blog Posts)│     │ Parser       │     │ (by sections)   │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
┌─────────────┐     ┌──────────────┐              │
│  IRS.gov    │────▶│ Tax Reference│──────────────┤
│  Scraper    │     │ Store (SQLite)│              │
└─────────────┘     └──────────────┘              ▼
                                          ┌───────────────┐
                                          │ Mistral AI    │
                                          │ Gap Detection │
                                          └───────┬───────┘
                                                  │
                    ┌──────────────┐              │
                    │ Confidence   │◀─────────────┘
                    │ Rescorer     │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
      ┌──────────┐ ┌────────────┐ ┌──────────┐
      │ SQLite   │ │ Change     │ │ Excel    │
      │ Storage  │ │ Tracker    │ │ Report   │
      └──────────┘ └────────────┘ └──────────┘
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API key

Create a `.env` file in the project root:

```
MISTRAL_API_KEY=your_mistral_api_key_here
```

Get your API key from [Mistral AI Console](https://console.mistral.ai/).

### 3. Run

```bash
# Full audit of all US tax guide posts
python main.py run

# Audit a single post by WordPress ID
python main.py run --post-id 12345

# Start daily scheduler (runs at 2 AM)
python main.py schedule
```

## Output

Reports are saved to `output/tax_audit_report_YYYYMMDD_HHMMSS.xlsx` with three sheets:

| Sheet | Contents |
|-------|----------|
| **Summary** | Run statistics, finding counts by priority/status, API usage |
| **Findings** | Blog Link, Blog Title, Current Text, Suggested Updated Text, Source, Confidence, Priority, Status |
| **Tax Law Sources** | All IRS references used during the audit |

### Priority Color Coding

- 🔴 **HIGH** — Affects tax liability calculation (e.g., wrong rates, incorrect taxable event classification)
- 🟡 **MEDIUM** — Compliance/procedural issues (e.g., missing Form 1099-DA info, wrong filing requirements)
- 🟢 **LOW** — Cosmetic/clarity improvements

### Finding Statuses

- **New** — First time detected in this run
- **Previously Identified** — Was found in a prior run and still exists
- **Resolved** — Was in a prior run but no longer detected

## Project Structure

```
koinx-tax-auditor/
├── config/settings.py          # Configuration (API keys, URLs, thresholds)
├── crawler/
│   ├── wp_api_client.py        # WordPress REST API client with pagination
│   └── content_parser.py       # HTML → structured sections parser
├── tax_sources/
│   ├── irs_fetcher.py          # IRS.gov scraper + hardcoded tax rules
│   └── tax_reference_store.py  # SQLite-cached tax reference corpus
├── analyzer/
│   ├── prompts.py              # System + gap detection prompt templates
│   ├── content_chunker.py      # Section-based chunking (max 4000 chars)
│   ├── mistral_client.py       # Mistral API wrapper (rate limit, retry)
│   ├── gap_detector.py         # Main orchestrator pipeline
│   └── confidence_scorer.py    # Multi-factor confidence rescoring
├── storage/
│   ├── database.py             # SQLite schema + connection
│   └── change_tracker.py       # New/recurring/resolved detection
├── output/
│   └── excel_generator.py      # Color-coded Excel report generator
├── scheduler/
│   └── job_manager.py          # APScheduler daily cron
├── main.py                     # CLI entry point
└── requirements.txt
```

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Data source | WP REST API | Structured JSON, no JS rendering, 3 API calls for all posts |
| US filtering | Category exclusion + title keywords | Tax Guides category includes non-US posts |
| LLM model | `mistral-large-latest` | Best reasoning for factual analysis, JSON output support |
| Chunking | Section-based (h2/h3 headings) | Preserves context, natural boundaries |
| Temperature | 0.1 | Low for factual accuracy, minimizes hallucination |
| Change detection | SHA-256(blog_url + exact_quote) | Deterministic, survives re-runs |
| Rate limiting | Token bucket at 30 RPM | Stays within Mistral API limits |

## Estimated API Usage

- ~100 US tax posts × ~5 chunks each = ~500 Mistral API calls per full run
- ~2.75M tokens per full audit
- Runtime: ~17 minutes (at 30 RPM rate limit)
