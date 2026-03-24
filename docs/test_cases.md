# Test Cases — IndMoney Weekly Product Pulse

> Run all tests: `py -m pytest tests/ -v`

---

## Module A1 — Review Ingestion (`test_ingestion.py`)

| # | Test | What it verifies |
|---|---|---|
| 1 | `test_valid_count_returns_reviews` | Fetching 200 reviews returns ≤ 200 `RawReview` objects |
| 2 | `test_invalid_count_raises_error` | Passing count outside `[200, 300, 400]` raises `ValueError` |
| 3 | `test_short_reviews_filtered` | Reviews with < 5 words are discarded |
| 4 | `test_duplicate_reviews_filtered` | Duplicate review texts are de-duped |
| 5 | `test_empty_text_filtered` | Empty / `None` review texts are discarded |

---

## Module A2 — Theme Clustering (`test_clustering.py`)

| # | Test | What it verifies |
|---|---|---|
| 1 | `test_returns_themed_analysis` | Returns ≤ 5 themes and ≤ 9 quotes |
| 2 | `test_top_3_flagged` | Exactly 3 themes are flagged `is_top_3=True` |
| 3 | `test_quotes_per_theme` | Max 3 quotes per theme label |

---

## Module A3 — PII Masking (`test_pii_masker.py`)

| # | Test | What it verifies |
|---|---|---|
| 1 | `test_mask_email` | Emails replaced with `[REDACTED]` |
| 2 | `test_mask_phone_with_country_code` | `+91 98765 43210` → `[REDACTED]` |
| 3 | `test_mask_phone_without_country_code` | `9876543210` → `[REDACTED]` |
| 4 | `test_mask_account_number` | Account numbers → `[REDACTED]` |
| 5 | `test_mask_name_context` | "My name is John Smith" → `[REDACTED]` |
| 6 | `test_no_false_positive_clean_text` | Clean text passes through unchanged |
| 7 | `test_multiple_pii_in_one_text` | Both email + phone masked in same string |
| 8 | `test_mask_analysis_masks_quotes` | Full `ThemedAnalysis` quotes are PII-masked |
| 9 | `test_mask_analysis_preserves_themes` | Theme metadata is untouched by masking |

---

## Module A4 — Pulse Generation (`test_pulse_generator.py`)

| # | Test | What it verifies |
|---|---|---|
| 1 | `test_summary_within_word_limit` | `summary_note` ≤ 250 words |
| 2 | `test_exactly_3_action_items` | Exactly 3 action items returned |
| 3 | `test_action_items_linked_to_themes` | Each action's `linked_theme` matches a real theme label |
| 4 | `test_pulse_payload_structure` | Correct `approval_status`, `metadata`, `footer`, themes, quotes |

---

## Module B — PDF Export & Email (`test_module_b.py`)

| # | Test | What it verifies |
|---|---|---|
| 1 | `test_pdf_creates_file` | PDF file is created and non-empty |
| 2 | `test_pdf_filename_format` | Filename starts with `IndMoney_Pulse_` and ends `.pdf` |
| 3 | `test_pdf_creates_output_dir` | Missing nested output dir is auto-created |
| 4 | `test_empty_recipients_error` | Empty recipient list → error |
| 5 | `test_too_many_recipients_error` | >5 recipients → error |
| 6 | `test_missing_credentials_error` | Missing Gmail env vars → error |
| 7 | `test_email_sends_with_valid_config` | SMTP send succeeds with mocked server |

---

## Module C — Approval Gate (`test_gate.py`)

| # | Test | What it verifies |
|---|---|---|
| 1 | `test_approve_sets_status` | `approve()` sets status to `APPROVED` |
| 2 | `test_reject_sets_status` | `reject()` blocks `is_approved()` |
| 3 | `test_cannot_export_before_approval` | Gate blocks export when `PENDING` |
| 4 | `test_can_export_after_approval` | Gate allows export after `approve()` |
| 5 | `test_process_action_approve_pdf` | `GateAction.APPROVE_PDF` returns correct next step |

---

## Module C+B — Gate-Enforced Actions (`test_mcp_actions.py`)

| # | Test | What it verifies |
|---|---|---|
| 1 | `test_pdf_export_works_after_approval` | PDF export succeeds only after gate approval |
| 2 | `test_pulse_starts_pending` | New pulse starts `PENDING`, gate blocks export |
| 3 | `test_email_rejects_more_than_5_recipients` | >5 recipients → rejected |
| 4 | `test_email_requires_at_least_1_recipient` | 0 recipients → rejected |
| 5 | `test_gate_reject_blocks_further_actions` | `REJECT` action blocks all downstream |

---

## Module D — Report History (`test_history.py`)

| # | Test | What it verifies |
|---|---|---|
| 1 | `test_save_returns_id` | `save_report()` returns a valid integer ID |
| 2 | `test_save_with_no_pdf` | Save works without a PDF path |
| 3 | `test_empty_history` | Empty DB returns `[]` |
| 4 | `test_history_returns_saved_reports` | Saved reports appear in history |
| 5 | `test_history_max_3` | History auto-prunes to last 3 reports |
| 6 | `test_get_existing_report` | Full payload retrieval by ID |
| 7 | `test_get_nonexistent_report` | Unknown ID returns `None` |
| 8 | `test_delete_existing` | Delete removes the report |
| 9 | `test_delete_nonexistent` | Delete returns `False` for unknown ID |

---

## Module E — FastAPI API (`test_api.py`)

| # | Test | What it verifies |
|---|---|---|
| 1 | `test_generate_returns_pulse` | `POST /api/generate` returns `pulse_id` + payload |
| 2 | `test_generate_invalid_count_returns_400` | Invalid review count → HTTP 400 |
| 3 | `test_get_pulse_not_found` | `GET /api/pulse/{id}` → HTTP 404 for unknown ID |
| 4 | `test_get_pulse_after_generate` | Correct payload returned after generation |
| 5 | `test_export_pdf_endpoint` | `POST /api/export/pdf` generates PDF + saves to history |
| 6 | `test_email_max_recipients_rejected` | >5 recipients → HTTP 400 |
| 7 | `test_export_pdf_pulse_not_found` | Unknown pulse → HTTP 404 |
| 8 | `test_history_empty` | Empty DB returns `[]` |
| 9 | `test_history_returns_saved_report` | History returns reports after export |

---

## E2E Integration (`test_e2e_pipeline.py`)

| # | Test | What it verifies |
|---|---|---|
| 1 | `test_full_pipeline_200_reviews` | Full A1→A4 pipeline produces valid `PulsePayload` |
| 2 | `test_pipeline_then_pdf_export` | Pipeline → PDF produces a valid file on disk |
| 3 | `test_pipeline_then_save_history` | Pipeline → SQLite save → retrieval from history works |

---

## Summary

| Module | File | Tests |
|---|---|---|
| A1 — Ingestion | `test_ingestion.py` | 5 |
| A2 — Clustering | `test_clustering.py` | 3 |
| A3 — PII Masking | `test_pii_masker.py` | 9 |
| A4 — Pulse Gen | `test_pulse_generator.py` | 4 |
| B — PDF/Email | `test_module_b.py` | 7 |
| C — Gate | `test_gate.py` | 5 |
| C+B — Gate Actions | `test_mcp_actions.py` | 5 |
| D — History | `test_history.py` | 9 |
| E — API | `test_api.py` | 9 |
| E2E Integration | `test_e2e_pipeline.py` | 3 |
| **Total** | | **59** |
