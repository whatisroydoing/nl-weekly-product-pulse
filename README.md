# IndMoney Weekly Product Pulse

AI-powered weekly product pulse from Google Play Store reviews.

## What It Does

1. **Fetches** 200/300/400 reviews from Google Play Store
2. **Clusters** into ≤5 themes using OpenAI gpt-4o-mini (1 API call)
3. **Masks PII** via regex (0 API calls)
4. **Generates** summary (≤250 words) + 3 action points using OpenAI gpt-4o-mini (1 API call)
5. **User reviews** the pulse and decides to Download PDF / Send Email
6. **Exports** via MCP (PDF + Email)
7. **Stores** last 3 reports in history

**Total LLM calls per run: 2** (optimized for free-tier usage)

## Architecture

See [Docs/ARCHITECTURE.md](Docs/ARCHITECTURE.md) for full module breakdown.

| Module | Name | Purpose |
|---|---|---|
| A | Analysis Engine | Ingest → Cluster (Gemini) → PII Mask → Summary (Grok) |
| B | Output Actions | PDF export + Email send via MCP |
| C | Approval Gate | User reviews before any output fires |
| D | Report History | Last 3 reports in SQLite |
| E | UI / Frontend | FastAPI backend + Next.js frontend (Vercel) |

## Quick Start (Interactive)

For a detailed, step-by-step guide on setting up the project from scratch, see:
👉 **[Docs/LOCAL_RUN_GUIDE.md](Docs/LOCAL_RUN_GUIDE.md)**

---

## One-Click Start (Windows)

A batch script is provided to start both the backend and frontend simultaneously:

1.  Double-click **`start_local.bat`** in the project root.
2.  Wait for the backend (FastAPI) and frontend (Vite) to initialize.
3.  The app will be available at **http://localhost:5173**.

---

## CLI Usage (Alternative)

## API Server

```bash
uvicorn module_e.api:app --reload
# Open http://localhost:8000/docs for Swagger UI
```

## Project Structure

```
main.py                  # CLI orchestrator
module_a/                # Analysis Engine (Gemini + Grok)
module_b/                # MCP Output Actions (PDF + Email)
module_c/                # Approval Gate
module_d/                # Report History (SQLite)
module_e/                # FastAPI API + Frontend
models/                  # Pydantic schemas
tests/                   # Test suite
```