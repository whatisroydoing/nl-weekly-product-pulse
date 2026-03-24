"""End-to-End Integration Tests — Full pipeline with mocked external services."""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from models.schemas import RawReview
from module_a.pipeline import run_pipeline
from module_b.pdf_export import export_pdf
from module_d.history import save_report, get_history, get_report


def _fake_scraper_result(count):
    """Generate realistic fake google-play-scraper results."""
    results = []
    for i in range(count):
        results.append({
            "content": f"This is a realistic review number {i} with enough text to pass all quality filters in the ingestion module",
            "score": (i % 5) + 1,
            "at": f"2026-03-{10 - (i % 10):02d}",
        })
    return results, None


def _fake_clustering_response():
    """Fake OpenAI response for clustering (A2)."""
    data = {
        "themes": [
            {"label": "App Stability", "description": "Frequent crashes and freezes", "review_count": 30, "is_top_3": True},
            {"label": "Great Design", "description": "Users love the clean UI", "review_count": 25, "is_top_3": True},
            {"label": "Slow Support", "description": "Customer support is slow", "review_count": 20, "is_top_3": True},
            {"label": "Missing Features", "description": "Need more chart types", "review_count": 10, "is_top_3": False},
        ],
        "quotes": [
            {"text": "The app crashes every morning", "theme_label": "App Stability", "rating": 1},
            {"text": "Need better crash handling", "theme_label": "App Stability", "rating": 2},
            {"text": "Too many bugs lately", "theme_label": "App Stability", "rating": 1},
            {"text": "Beautiful and intuitive", "theme_label": "Great Design", "rating": 5},
            {"text": "Best finance app UI", "theme_label": "Great Design", "rating": 5},
            {"text": "Love the clean layout", "theme_label": "Great Design", "rating": 4},
            {"text": "Support never responds", "theme_label": "Slow Support", "rating": 1},
            {"text": "Waited 10 days for reply", "theme_label": "Slow Support", "rating": 2},
            {"text": "No help from support team", "theme_label": "Slow Support", "rating": 1},
        ],
    }
    mock_msg = MagicMock()
    mock_msg.content = json.dumps(data)
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    return mock_resp


def _fake_pulse_response():
    """Fake OpenAI response for pulse generation (A4)."""
    data = {
        "summary_note": (
            "This week reveals significant stability concerns alongside strong praise for the app's design. "
            "Users report crashes on Android 14 that need urgent attention, while the UI continues to delight. "
            "Support responsiveness remains a recurring pain point."
        ),
        "action_items": [
            {"id": 1, "title": "Fix Android 14 Crashes", "description": "Investigate and fix crash logs.", "linked_theme": "App Stability"},
            {"id": 2, "title": "Improve Support SLA", "description": "Reduce response time to 24hrs.", "linked_theme": "Slow Support"},
            {"id": 3, "title": "Add Chart Types", "description": "Introduce candlestick charts.", "linked_theme": "Missing Features"},
        ],
    }
    mock_msg = MagicMock()
    mock_msg.content = json.dumps(data)
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    return mock_resp


@pytest.fixture(autouse=True)
def clean_db():
    """Remove test DB before and after each test."""
    if os.path.exists("reports.db"):
        os.remove("reports.db")
    yield
    if os.path.exists("reports.db"):
        os.remove("reports.db")


class TestFullPipeline:
    """End-to-end tests mocking only external services (scraper + OpenAI)."""

    @patch("module_a.pulse_generator.OpenAI")
    @patch("module_a.clustering.OpenAI")
    @patch("module_a.ingestion.reviews")
    def test_full_pipeline_200_reviews(self, mock_scraper, mock_cluster_openai, mock_pulse_openai):
        """Full pipeline A1→A2→A3→A4 produces a valid PulsePayload."""
        # Mock scraper
        mock_scraper.return_value = _fake_scraper_result(600)

        # Mock clustering OpenAI
        mock_cluster_client = MagicMock()
        mock_cluster_client.chat.completions.create.return_value = _fake_clustering_response()
        mock_cluster_openai.return_value = mock_cluster_client

        # Mock pulse OpenAI
        mock_pulse_client = MagicMock()
        mock_pulse_client.chat.completions.create.return_value = _fake_pulse_response()
        mock_pulse_openai.return_value = mock_pulse_client

        pulse = run_pipeline(200)

        # Validate complete payload structure
        assert pulse.approval_status == "PENDING"
        assert pulse.metadata["review_count"] == 200
        assert len(pulse.themes) >= 1
        assert len(pulse.themes) <= 5
        assert len(pulse.quotes) >= 1
        assert len(pulse.action_items) == 3
        assert len(pulse.summary_note.split()) <= 250
        assert len(pulse.footer) > 0

    @patch("module_a.pulse_generator.OpenAI")
    @patch("module_a.clustering.OpenAI")
    @patch("module_a.ingestion.reviews")
    def test_pipeline_then_pdf_export(self, mock_scraper, mock_cluster_openai, mock_pulse_openai, tmp_path):
        """Pipeline → PDF export produces a valid file."""
        mock_scraper.return_value = _fake_scraper_result(600)

        mock_cluster_client = MagicMock()
        mock_cluster_client.chat.completions.create.return_value = _fake_clustering_response()
        mock_cluster_openai.return_value = mock_cluster_client

        mock_pulse_client = MagicMock()
        mock_pulse_client.chat.completions.create.return_value = _fake_pulse_response()
        mock_pulse_openai.return_value = mock_pulse_client

        pulse = run_pipeline(200)
        result = export_pdf(pulse, output_dir=str(tmp_path))

        assert result["success"] is True
        assert Path(result["pdf_path"]).exists()
        assert Path(result["pdf_path"]).stat().st_size > 0

    @patch("module_a.pulse_generator.OpenAI")
    @patch("module_a.clustering.OpenAI")
    @patch("module_a.ingestion.reviews")
    def test_pipeline_then_save_history(self, mock_scraper, mock_cluster_openai, mock_pulse_openai):
        """Pipeline → Save to DB → Retrieve from history."""
        mock_scraper.return_value = _fake_scraper_result(600)

        mock_cluster_client = MagicMock()
        mock_cluster_client.chat.completions.create.return_value = _fake_clustering_response()
        mock_cluster_openai.return_value = mock_cluster_client

        mock_pulse_client = MagicMock()
        mock_pulse_client.chat.completions.create.return_value = _fake_pulse_response()
        mock_pulse_openai.return_value = mock_pulse_client

        pulse = run_pipeline(200)
        report_id = save_report(pulse)

        # Verify in history
        history = get_history()
        assert len(history) == 1
        assert history[0]["review_count"] == 200

        # Verify full payload retrieval
        saved = get_report(report_id)
        assert saved is not None
        assert saved.metadata["app_name"] == "IndMoney"
        assert len(saved.action_items) == 3
