# Project Status & TO-DO

This document tracks the implemented details of the IndMoney Weekly Product Pulse project as defined in the `ARCHITECTURE.md` and what remains to be done.

## Completed ✅

### Phase 1: Core Analysis Engine (Module A)
- **Review Ingestion** (`ingestion.py`): Google Play Scraper integrated, >=5 words filtering, English language enforcement, and 2.5x batch processing handles.
- **Theme Clustering** (`clustering.py`): OpenAI `gpt-4o-mini` batch clustering and quote extraction.
- **PII Masking** (`pii_masker.py`): Regex-based sensitive data reduction functional.
- **Pulse Generator** (`pulse_generator.py`): AI-generated summary and actions enabled.
- **Pipeline Orchestrator** (`pipeline.py`): Connecting A1 to A4.

### Phase 2: Action & History Layers (Modules B, C, D)
- **PDF Export** (`pdf_export.py`): ReportLab generation working.
- **Email Send** (`email_send.py`): SMTP integration functional.
- **Approval Gate** (`gate.py`): Mechanisms for human intervention prior to generation functional.
- **Report History** (`history.py`): SQLite schema and query logic (retention of last 3 reports) working fine.

### Phase 3: Web Stack (Module E)
- **FastAPI Endpoints** (`api.py`): Configured endpoints for generating, fetching, and exporting reports.
- **Frontend UI** (`module_e/frontend`): Built with React, Vite, and Tailwind CSS. The primary UI components (`App.jsx`, `PulseReview.jsx`) have been structured accurately.

### Phase 4: Test Suite (Completed ✅)
- **Ingestion tests** (`test_ingestion.py`): Fixed stale truncation test, aligned config with real `config.yaml`.
- **Pulse Generator tests** (`test_pulse_generator.py`): Implemented 4 tests with OpenAI mocking.
- **MCP/Gate tests** (`test_mcp_actions.py`): Implemented 5 gate-enforced action tests.
- **API Endpoint tests** (`test_api.py`): 9 tests covering all FastAPI endpoints.
- **E2E Integration tests** (`test_e2e_pipeline.py`): 3 full pipeline tests (A1→A4→PDF→History).
- **Test Documentation** (`docs/test_cases.md`): 59 tests documented across 10 files.

## Left / Pending (TO-DO) ⏳

### Phase 5: Fee Explainer (Module F) (Completed ✅)
- [x] **F1 — Fee Scraper** (`module_f/fee_scraper.py`): Scrape exit load data from 2 IndMoney fund pages using `playwright` (headless Chromium). Cache to `data/fee_cache.json`, re-scrape on 2nd Monday of each month.
- [x] **F2 — Fee Explainer** (`module_f/fee_explainer.py`): Template-based 5-bullet exit load explanation. Both funds cited in a single bullet. 2 source links. "Last checked: {date}". Neutral tone, no recommendations.
- [x] **F3 — Google Doc Writer** (`module_f/google_doc_writer.py`): Overwrite Google Doc with structured pulse (date, summary, fee scenario, bullets, sources) via Docs API on each email send.
- [x] **Schema Update** (`models/schemas.py`): Add `FeeExplainerResult` Pydantic model.
- [x] **Email Integration** (`module_b/email_send.py`): Add fee explainer section to HTML email body (below action items, above footer). Email-only — not on UI or PDF.
- [x] **API Wiring** (`module_e/api.py`): Wire Module F into `/api/export/email` endpoint. Add `POST /api/fee-explainer/scrape` endpoint for manual re-scrape.
- [x] **Config & Dependencies**: Add `fee_explainer` section to `config.yaml`, Google Doc env vars to `.env.example`, `playwright` / `google-api-python-client` / `google-auth` to `requirements.txt`.
- [x] **Tests** (`tests/test_fee_explainer.py`): Template output compliance, neutral tone check, schema validation, cache logic, Google Doc writer mock.

### Prerequisites for Phase 5
- [ ] **Playwright Setup**: `pip install playwright && playwright install chromium`
- [ ] **Google Cloud Setup**: Create GCP project → enable Docs API → create service account → download JSON key → share target Google Doc with service account email.

### Ongoing ✅
- [x] **Deployment Strategy:** Finalized Docker configuration and Railway plan. (See [Docs/deployment.md](file:///d:/Product%20Management/Upskilling/2026/Git%20Projects/nl-weekly-product-pulse/docs/deployment.md)).
- [x] **Robust Error Handling:** Added exponential backoff retry logic to OpenAI pipeline calls.
- [x] **Frontend Testing:** Added Vitest and React Testing Library tests for core UI in `App.jsx`.
- [x] **CI/CD Pipeline:** Set up GitHub Actions in `.github/workflows/test.yml`.
- [x] **Environment Parity:** Updated `.env.example` with security and deployment keys.
- [x] **Security Hardening:** Restricted CORS origins in `api.py`.
