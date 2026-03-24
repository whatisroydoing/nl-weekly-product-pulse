# IndMoney Weekly Product Pulse — Architecture

## Overview

AI workflow that ingests Google Play reviews, produces a **Weekly Product Pulse** (themes, quotes, summary, action points), and — after human review — exports to PDF and/or emails up to 5 recipients.

---

## User Journey

1. **Start:** The user selects how many reviews to analyze (200, 300, or 400) and clicks "Generate Pulse".
2. **Analysis:** The system automatically fetches the reviews, extracts themes, masks sensitive data, and creates a summary. 
3. **Review:** The front-end displays this parsed "Review Pulse", allowing the user to review the insights.
4. **Action:** The user chooses to either:
   - **Download PDF:** Immediately generates and downloads a branded PDF report.
   - **Send Email:** Emails the report to specified team members directly from the interface.

---

## System Data Flow Journey

1. **Ingestion (Module A1):** Takes the user's requested review count, scrapes 2.5x from Google Play, and filters down to high-quality English reviews.
2. **Clustering (Module A2):** The AI groups these reviews into themes and pulls top quotes.
3. **Masking (Module A3):** Identifies private info (PII) like names or phone numbers and redacts them.
4. **Generation (Module A4):** Based on the themes, the AI generates an overarching summary and key actionable items.
5. **Approval & Storage (Module C & D):** The final structured data is passed to the UI for user review. It is also auto-saved to SQLite for history retention.
6. **Output (Module B):** Upon user approval, the data generates a final artifact (PDF or Email).

---

## Tech Stack & Rationale

| Layer | Choice | Rationale |
|---|---|---|
| **LLM** | OpenAI `gpt-4o-mini` | **Why:** Best balance of reasoning speed and cost. `mini` excels at structured JSON extraction (clustering) and concise summarization without the latency/cost of larger models. |
| **Logic/API** | FastAPI (Python) | **Why:** Async-first, high performance, and rapid developer experience. Native Pydantic v2 support ensures strict schema validation for the `PulsePayload`. |
| **Frontend** | React + Vite + Tailwind | **Why:** Modern, ultra-fast build toolchain. Tailwind allows for rapid design iteration of the complex 6-section Pulse Review screen without custom CSS overhead. |
| **PDF Engine** | ReportLab | **Why:** Low-level control over PDF layout. Unlike template-based generators, it allows for dynamic multi-page report generation with branded styling in pure Python. |
| **History Layer**| SQLite | **Why:** Zero-config, file-based database. Perfect for a local-first prototype to track the history of the last 3 reports without needing a separate DB server. |
| **Scraping** | `google-play-scraper` | **Why:** Robust, lightweight library that doesn't require a browser/webdriver, minimizing infrastructure overhead. |

---

## Modules

| Module | Name | Responsibility |
|---|---|---|
| **A** | Analysis Engine | Ingest reviews → cluster themes (AI) → mask PII → generate summary (AI) |
| **B** | Output Actions | PDF export + email send |
| **C** | Approval Gate | Review screen — user approves before any output fires |
| **D** | Report History | Store last 3 reports, re-download / re-send |
| **E** | UI / Frontend | Web interface (React) + API backend (FastAPI) |
| **F** | Fee Explainer | Scrape exit load data → template bullets → email body + Google Doc append |

---

## Module A — Analysis Engine

### A1 · Review Ingestion (`module_a/ingestion.py`)
- Input: review count (200 / 300 / 400)
- Source: Google Play Store via `google-play-scraper`
- Scrapes 2.5× the requested count to ensure quality after filtering
- **Quality Filters:**
  - Skips reviews with < 5 words
  - Skips non-English reviews
  - Skips duplicate reviews
  - Skips rating-only (empty text) reviews
- Output: `raw_reviews[]` + saved to `data/raw_reviews.json`

### A2 · Theme Clustering (`module_a/clustering.py`)
- LLM: `gpt-4o-mini`
- Processes reviews in batches of 50 (configurable)
- Returns: ≤5 themes + top 3 flagged + 3 quotes per top theme (9 total)
- Prompt: `module_a/prompts/clustering.txt`

### A3 · PII Masking (`module_a/pii_masker.py`)
- Regex-based: emails, phone numbers, account IDs, names
- Replaces matches with `[REDACTED]`

### A4 · Pulse Generation (`module_a/pulse_generator.py`)
- LLM: `gpt-4o-mini`
- Returns: summary note (≤250 words) + 3 action points (≤400 words)
- Prompt: `module_a/prompts/pulse.txt`

### A5 · Pipeline Orchestrator (`module_a/pipeline.py`)
- Single `run_pipeline(review_count)` function
- Chains A1 → A2 → A3 → A4 and returns `PulsePayload`

### Token Optimization
- Exactly **2 LLM calls** per run.
- Reviews truncated to **500 chars** each before LLM call.
- PII masking is regex-only (no LLM tokens spent).

---

## Module B — Output Actions

### B1 · PDF Export (`module_b/pdf_export.py`)
- Trigger: user clicks "Download PDF"
- Library: `reportlab`
- Standardized, multi-page branded layout.

### B2 · Email Send (`module_b/email_send.py`)
- Trigger: user clicks "Send on email" + up to 5 addresses.
- SMTP via Gmail or configurable SMTP credentials.
- **Fee Explainer section** is appended to the email body (below action items, above footer) when available.

---

## Module C — Approval Gate (`module_c/gate.py`)

Implicit gate — user reviews the full pulse on screen, then explicitly clicks:
- **Download PDF** → triggers B1
- **Send Email** → triggers B2 + Module F (fee section in email + Google Doc append)
- **Regenerate** → back to A2

No output action fires without explicit user click.

---

## Module D — Report History (`module_d/history.py`)

- Storage: SQLite (`reports.db`)
- Retention: last 3 reports
- Auto-named: `IndMoney Pulse — DD MMM YYYY`

---

## Module E — UI / Frontend

### Backend (`module_e/api.py`)
- FastAPI with endpoints:
  - `POST /api/generate` — trigger Module A pipeline
  - `GET /api/pulse/{id}` — get pulse payload
  - `POST /api/export/pdf` — trigger B1
  - `POST /api/export/email` — trigger B2 + Module F
  - `GET /api/history` — last 3 reports
  - `POST /api/fee-explainer/scrape` — manually trigger fee data re-scrape

### Frontend (`module_e/frontend/`)
- React app built with Vite.
- Views: Generate Report + Report History.
- Fee Explainer is **not displayed in the UI** — it is email-only.

---

## Module F — Fee Explainer

### F1 · Fee Scraper (`module_f/fee_scraper.py`)
- Scrapes exit load data from 2 IndMoney fund pages using `playwright` (headless Chromium)
- **Schedule:** Runs on the 2nd Monday of each month; cached between scrapes
- Cache: `data/fee_cache.json` with timestamp
- Falls back to cached data if scraping fails
- **Resilient Matching:** Scraper uses case-insensitive URL matching to reliably identify funds and avoid "Not Found" errors.
- **Funds scraped:**
  - ICICI Prudential Value Fund (exit load: 1% within 12 months)
  - ICICI Prudential Corporate Bond Fund (exit load: Nil)

### F2 · Fee Explainer (`module_f/fee_explainer.py`)
- **Template-based** bullet generation (no LLM, zero cost, deterministic output)
- Generates exactly **5 bullets** explaining exit load with both funds cited as examples in a single bullet
- Includes 2 official source links (IndMoney URLs)
- Appends "Last checked: {date}" using cache timestamp
- Neutral, facts-only tone — no recommendations or comparisons
- Returns a `FeeExplainerResult` Pydantic model

### F3 · Google Doc Writer (`module_f/google_doc_writer.py`)
- **Overwrites** the entire Google Doc with a structured report on each email send to ensure the Doc always reflects the latest pulse.
- Payload: `{ date, weekly_pulse, fee_scenario, explanation_bullets, source_links }`
- Uses Google Docs API via service account authentication
- Support for branded headers using `HEADING_1` and `HEADING_2` styles.
- Requires `GOOGLE_SERVICE_ACCOUNT_JSON` and `GOOGLE_DOC_ID` env vars.

---

## Clarifications & Design Trade-offs

- **Model Selection:** `gpt-4o-mini` was chosen over `gpt-4o` because the task is primarily extraction and summarization, where the latency and cost of a frontier model provide diminishing returns for this specific use case.
- **PII Trade-off:** Regex-based masking is used instead of LLM-based masking to preserve privacy without sending un-masked data to an LLM provider and to eliminate the token cost associated with PII detection.
- **SQLite vs Vector JSON:** SQLite was chosen for history because it allows for easy expansion (e.g., searching by date or review count) while maintaining the single-file portability desired for the prototype.
- **Fee Explainer — Template vs LLM:** Template-based generation was chosen for the fee bullets because the output is structured, factual, and short. This guarantees deterministic, compliant output without hallucination risk and at zero API cost.
- **Playwright for Scraping:** IndMoney pages are JS-rendered and return HTTP 403 for direct requests, requiring a headless browser. Scraping is scheduled monthly (2nd Monday) to minimize resource usage.
