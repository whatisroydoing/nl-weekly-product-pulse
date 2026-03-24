"""Tests for Module E — FastAPI API Endpoints."""

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from fastapi.testclient import TestClient

from models.schemas import PulsePayload, Theme, Quote, ActionItem
from module_e.api import app, _pulse_store


client = TestClient(app)


def _make_pulse() -> PulsePayload:
    """Build a realistic PulsePayload for testing."""
    return PulsePayload(
        metadata={
            "app_name": "IndMoney",
            "source": "Google Play Store",
            "review_count": 200,
            "generated_at": datetime.now().strftime("%d-%b-%Y %H:%M"),
        },
        themes=[
            Theme(label="Bugs", description="Crashes reported", review_count=20, is_top_3=True),
            Theme(label="UX", description="Good UI", review_count=15, is_top_3=True),
            Theme(label="Support", description="Slow support", review_count=10, is_top_3=True),
        ],
        quotes=[
            Quote(text="App crashes often", theme_label="Bugs", rating=1),
            Quote(text="Love the design", theme_label="UX", rating=5),
        ],
        summary_note="Test summary for API endpoint testing.",
        action_items=[
            ActionItem(id=1, title="Fix Bugs", description="Fix crashes.", linked_theme="Bugs"),
        ],
        footer="Test footer",
        approval_status="PENDING",
    )


@pytest.fixture(autouse=True)
def clear_pulse_store():
    """Clear the in-memory pulse store before each test."""
    _pulse_store.clear()
    yield
    _pulse_store.clear()


@pytest.fixture(autouse=True)
def clean_db():
    """Remove test DB before and after each test."""
    if os.path.exists("reports.db"):
        os.remove("reports.db")
    yield
    if os.path.exists("reports.db"):
        os.remove("reports.db")


class TestGenerateEndpoint:

    @patch("module_e.api.run_pipeline")
    def test_generate_returns_pulse(self, mock_pipeline):
        """POST /api/generate returns pulse_id and pulse payload."""
        mock_pipeline.return_value = _make_pulse()
        response = client.post("/api/generate", json={"review_count": 200})
        assert response.status_code == 200
        data = response.json()
        assert "pulse_id" in data
        assert "pulse" in data
        assert data["pulse"]["approval_status"] == "PENDING"

    @patch("module_e.api.run_pipeline")
    def test_generate_invalid_count_returns_400(self, mock_pipeline):
        """POST /api/generate with invalid count returns 400."""
        mock_pipeline.side_effect = ValueError("review_count must be one of [200, 300, 400]")
        response = client.post("/api/generate", json={"review_count": 999})
        assert response.status_code == 400


class TestGetPulseEndpoint:

    def test_get_pulse_not_found(self):
        """GET /api/pulse/{id} for unknown ID returns 404."""
        response = client.get("/api/pulse/nonexistent_id")
        assert response.status_code == 404

    @patch("module_e.api.run_pipeline")
    def test_get_pulse_after_generate(self, mock_pipeline):
        """GET /api/pulse/{id} returns the correct pulse after generation."""
        mock_pipeline.return_value = _make_pulse()
        gen_response = client.post("/api/generate", json={"review_count": 200})
        pulse_id = gen_response.json()["pulse_id"]

        response = client.get(f"/api/pulse/{pulse_id}")
        assert response.status_code == 200
        assert response.json()["pulse"]["metadata"]["review_count"] == 200


class TestExportEndpoints:

    @patch("module_e.api.export_pdf")
    @patch("module_e.api.run_pipeline")
    def test_export_pdf_endpoint(self, mock_pipeline, mock_pdf):
        """POST /api/export/pdf generates PDF and saves to history."""
        mock_pipeline.return_value = _make_pulse()
        mock_pdf.return_value = {"success": True, "pdf_path": "exports/test.pdf"}

        gen_resp = client.post("/api/generate", json={"review_count": 200})
        pulse_id = gen_resp.json()["pulse_id"]

        response = client.post("/api/export/pdf", json={"pulse_id": pulse_id})
        assert response.status_code == 200
        assert response.json()["success"] is True

    @patch("module_e.api.run_pipeline")
    def test_email_max_recipients_rejected(self, mock_pipeline):
        """POST /api/export/email with >5 recipients returns 400."""
        mock_pipeline.return_value = _make_pulse()
        gen_resp = client.post("/api/generate", json={"review_count": 200})
        pulse_id = gen_resp.json()["pulse_id"]

        response = client.post("/api/export/email", json={
            "pulse_id": pulse_id,
            "recipients": ["a@b.com"] * 6,
        })
        assert response.status_code == 400

    def test_export_pdf_pulse_not_found(self):
        """POST /api/export/pdf for unknown pulse returns 404."""
        response = client.post("/api/export/pdf", json={"pulse_id": "fake_id"})
        assert response.status_code == 404


class TestHistoryEndpoints:

    def test_history_empty(self):
        """GET /api/history on clean DB returns empty list."""
        response = client.get("/api/history")
        assert response.status_code == 200
        assert response.json() == []

    @patch("module_e.api.run_pipeline")
    def test_history_returns_saved_report_on_generate(self, mock_pipeline):
        """Immediately after generating, history returns the saved report."""
        mock_pipeline.return_value = _make_pulse()

        client.post("/api/generate", json={"review_count": 200})

        response = client.get("/api/history")
        assert response.status_code == 200
        history = response.json()
        assert len(history) >= 1
        assert history[0]["review_count"] == 200
        assert history[0]["pdf_path"] is None  # No PDF yet

    @patch("module_e.api.export_pdf")
    @patch("module_e.api.run_pipeline")
    def test_history_export_updates_pdf_path(self, mock_pipeline, mock_pdf):
        """Exporting to PDF updates the pdf_path for the generated report."""
        mock_pipeline.return_value = _make_pulse()
        mock_pdf.return_value = {"success": True, "pdf_path": "exports/test.pdf"}

        gen_resp = client.post("/api/generate", json={"review_count": 200})
        pulse_id = gen_resp.json()["pulse_id"]
        
        client.post("/api/export/pdf", json={"pulse_id": pulse_id})

        response = client.get("/api/history")
        history = response.json()
        assert history[0]["pdf_path"] == "exports/test.pdf"

    @patch("module_e.api.run_pipeline")
    def test_get_history_report_rehydrates_store(self, mock_pipeline):
        """GET /api/history/{id} re-hydrates the _pulse_store."""
        mock_pipeline.return_value = _make_pulse()
        client.post("/api/generate", json={"review_count": 200})
        
        history = client.get("/api/history").json()
        report_id = history[0]["id"]

        # Clear the memory store to simulate a server restart
        _pulse_store.clear()
        assert len(_pulse_store) == 0

        # Fetch the past report
        resp = client.get(f"/api/history/{report_id}")
        assert resp.status_code == 200
        
        # Verify store is re-hydrated
        assert len(_pulse_store) == 1
        pulse_id = list(_pulse_store.keys())[0]
        assert _pulse_store[pulse_id]["db_id"] == report_id
