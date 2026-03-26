"""
Module E -- FastAPI Backend API
Exposes endpoints for report generation, export, email, and history.
Wires together Module A (pipeline), Module B (PDF + email), Module C (gate), Module D (history).
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from module_a.pipeline import run_pipeline
from module_b.pdf_export import export_pdf
from module_b.email_send import send_email
from module_c.gate import ApprovalGate, GateAction
from module_d.history import save_report, get_history, get_report, update_pdf_path

from module_f.fee_scraper import get_fee_data
from module_f.fee_explainer import generate_fee_explanation
from module_f.google_doc_writer import append_to_doc


app = FastAPI(
    title="IndMoney Weekly Product Pulse",
    description="AI-powered weekly product pulse from app reviews",
    version="0.2.0",
)

# CORS for frontend
import os
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory pulse store (keyed by pulse_id)
# Maps pulse_id -> {"gate": ApprovalGate, "db_id": int}
_pulse_store: dict[str, dict] = {}


# --- Request/Response Models ---

class GenerateRequest(BaseModel):
    review_count: int  # 200, 300, or 400


class ExportPDFRequest(BaseModel):
    pulse_id: str


class EmailRequest(BaseModel):
    pulse_id: str
    recipients: list[str]  # Max 5


def _rehydrate_pulse(pulse_id: str):
    """
    If pulse_id is missing from _pulse_store, try to find it in the database 
    and re-populate the store. This handles server reloads gracefully.
    """
    if pulse_id in _pulse_store:
        return _pulse_store[pulse_id]
    
    # Search DB for a report where the generated_at matches the pulse_id format
    history = get_history()
    for item in history:
        item_pulse_id = item.get("generated_at", "").replace(" ", "_").replace(":", "-")
        if item_pulse_id == pulse_id:
            # Found a match, lead full report and rehydrate
            pulse = get_report(item["id"])
            if pulse:
                _pulse_store[pulse_id] = {"gate": ApprovalGate(pulse), "db_id": item["id"]}
                return _pulse_store[pulse_id]
                
    return None


# --- Endpoints ---

@app.post("/generate")
def generate_report(request: GenerateRequest):
    """
    Trigger the full Module A pipeline.
    Returns pulse_id + full pulse_payload for review in the UI.
    """
    try:
        pulse = run_pipeline(request.review_count)

        # Save to DB immediately on generation
        db_id = save_report(pulse)

        # Store for gate approval
        pulse_id = pulse.metadata["generated_at"].replace(" ", "_").replace(":", "-")
        _pulse_store[pulse_id] = {"gate": ApprovalGate(pulse), "db_id": db_id}

        return {"pulse_id": pulse_id, "pulse": pulse.model_dump()}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.get("/pulse/{pulse_id}")
def get_pulse(pulse_id: str):
    """Get a pulse payload by its ID."""
    record = _rehydrate_pulse(pulse_id)
    if not record:
        raise HTTPException(status_code=404, detail="Pulse not found")
    return {"pulse_id": pulse_id, "pulse": record["gate"].pulse.model_dump()}


@app.post("/export/pdf")
def export_pdf_endpoint(request: ExportPDFRequest):
    """
    Export pulse as PDF -- implicitly approves the pulse.
    Returns the PDF file path and saves to history.
    """
    record = _rehydrate_pulse(request.pulse_id)
    if not record:
        raise HTTPException(status_code=404, detail="Pulse not found")

    gate = record["gate"]
    db_id = record["db_id"]

    # Implicit approval: clicking "Download PDF" = approval
    gate.process_action(GateAction.APPROVE_PDF)

    # B1: Generate PDF
    result = export_pdf(gate.pulse)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "PDF generation failed"))

    # D: Update history with PDF path
    update_pdf_path(db_id, result["pdf_path"])

    return {"success": True, "pdf_path": result["pdf_path"]}


@app.get("/download/pdf/{pulse_id}")
def download_pdf(pulse_id: str):
    """Download the generated PDF file directly."""
    record = _rehydrate_pulse(pulse_id)
    if not record:
        raise HTTPException(status_code=404, detail="Pulse not found")

    gate = record["gate"]

    # Generate PDF if not already
    result = export_pdf(gate.pulse)
    if not result["success"]:
        raise HTTPException(status_code=500, detail="PDF generation failed")

    return FileResponse(
        result["pdf_path"],
        media_type="application/pdf",
        filename=result["pdf_path"].split("\\")[-1].split("/")[-1],
    )


@app.post("/export/email")
def send_email_endpoint(request: EmailRequest):
    """
    Send pulse via email -- implicitly approves the pulse.
    Attaches the PDF if available.
    """
    record = _rehydrate_pulse(request.pulse_id)
    if not record:
        raise HTTPException(status_code=404, detail="Pulse not found")

    gate = record["gate"]
    db_id = record["db_id"]

    if len(request.recipients) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 recipients allowed")
    if not request.recipients:
        raise HTTPException(status_code=400, detail="At least one recipient required")

    # Implicit approval
    gate.process_action(GateAction.APPROVE_EMAIL)

    # B1: Generate PDF first (to attach)
    pdf_result = export_pdf(gate.pulse)
    pdf_path = pdf_result.get("pdf_path", "") if pdf_result.get("success") else ""

    # F: Generate Fee Explainer details
    fee_explainer = None
    try:
        scrape_data = get_fee_data(force_scrape=False)
        fee_explainer = generate_fee_explanation(scrape_data)
    except Exception as e:
        print(f"Fee explainer generation failed (continuing email without it): {e}")

    # B2: Send email with PDF attached and Fee Explainer
    email_result = send_email(gate.pulse, request.recipients, pdf_path=pdf_path, fee_explainer=fee_explainer)
    if not email_result["success"]:
        raise HTTPException(status_code=500, detail=email_result.get("error", "Email failed"))

    # F3: Append to Google Doc
    try:
        append_to_doc(gate.pulse, fee_explainer)
    except Exception as e:
        print(f"Google Doc append failed: {e}")

    # D: Update history with PDF path if generated
    if pdf_path:
        update_pdf_path(db_id, pdf_path)

    return {"success": True, "message": f"Email sent to {len(request.recipients)} recipients"}

@app.post("/fee-explainer/scrape")
def force_re_scrape_fee_data():
    """Manual trigger to force a re-scrape of the Fee Explainer data."""
    try:
        data = get_fee_data(force_scrape=True)
        return {"success": True, "cache_updated": "last_scraped" in data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scrape failed: {str(e)}")


@app.get("/history")
def list_history():
    """Get the last 3 reports (metadata only)."""
    return get_history()


@app.get("/history/{report_id}")
def get_history_report(report_id: int):
    """Get a full report from history by ID and rehydrate the store."""
    pulse = get_report(report_id)
    if not pulse:
        raise HTTPException(status_code=404, detail="Report not found")
        
    # Re-hydrate the in-memory store so UI exports (PDF/Email) work on past reports
    pulse_id = pulse.metadata.get("generated_at", "").replace(" ", "_").replace(":", "-")
    _pulse_store[pulse_id] = {"gate": ApprovalGate(pulse), "db_id": report_id}

    return {"pulse_id": pulse_id, "pulse": pulse.model_dump()}
