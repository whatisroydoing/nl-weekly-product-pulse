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
- [x] **F1 — Fee Scraper** (`module_f/fee_scraper.py`): Scrape exit load data using `playwright`. Cache re-scrape on 2nd Monday.
- [x] **F2 — Fee Explainer** (`module_f/fee_explainer.py`): Template-based 5-bullet exit load explanation.
- [x] **F3 — Google Doc Writer** (`module_f/google_doc_writer.py`): Overwrite Google Doc with structured pulse.
- [x] **Email Integration** (`module_b/email_send.py`): Add fee section to HTML email body.
- [x] **Gmail API Migration**: Moved from SMTP to Gmail API (OAuth2) for production stability.

### Phase 6: Stability & Resilience (Completed ✅)
- [x] **PDF Resilience**: Added XML sanitization to prevent generation failures on large review sets.
- [x] **State Rehydration**: Enabled history-to-dashboard navigation by restoring in-memory state from SQLite.
- [x] **Timezone Alignment**: Switched all timestamps to 24-hour IST format.
- [x] **Deployment Parity**: Finalized Railway/Vercel split with CORS hardening.

### Ongoing ✅
- [x] **Deployment Strategy:** Finalized Docker configuration and Railway plan. (See [Docs/deployment.md](file:///d:/Product%20Management/Upskilling/2026/Git%20Projects/nl-weekly-product-pulse/docs/deployment.md)).
- [x] **Robust Error Handling:** Added exponential backoff retry logic to OpenAI pipeline calls.
- [x] **Frontend Testing:** Added Vitest and React Testing Library tests for core UI in `App.jsx`.
- [x] **CI/CD Pipeline:** Set up GitHub Actions in `.github/workflows/test.yml`.
- [x] **Environment Parity:** Updated `.env.example` with security and deployment keys.
- [x] **Security Hardening:** Restricted CORS origins in `api.py`.
