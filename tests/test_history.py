"""Tests for Module D -- Report History."""

import os
import pytest
from datetime import datetime

from models.schemas import PulsePayload, Theme, Quote, ActionItem
from module_d.history import save_report, get_history, get_report, delete_report


@pytest.fixture
def mock_pulse():
    return PulsePayload(
        metadata={
            "app_name": "IndMoney",
            "source": "Google Play Store",
            "review_count": 100,
            "generated_at": datetime.now().strftime("%d-%b-%Y %H:%M"),
        },
        themes=[Theme(label="Test", description="desc", review_count=5, is_top_3=True)],
        quotes=[Quote(text="test quote", theme_label="Test", rating=4)],
        summary_note="Test summary.",
        action_items=[ActionItem(id=1, title="Action", description="desc", linked_theme="Test")],
        footer="Test footer",
        approval_status="APPROVED",
    )


@pytest.fixture(autouse=True)
def clean_db():
    """Remove test DB before and after each test."""
    if os.path.exists("reports.db"):
        os.remove("reports.db")
    yield
    if os.path.exists("reports.db"):
        os.remove("reports.db")


class TestSaveReport:

    def test_save_returns_id(self, mock_pulse):
        report_id = save_report(mock_pulse, pdf_path="test.pdf")
        assert isinstance(report_id, int)
        assert report_id > 0

    def test_save_with_no_pdf(self, mock_pulse):
        report_id = save_report(mock_pulse)
        assert report_id > 0


class TestGetHistory:

    def test_empty_history(self):
        history = get_history()
        assert history == []

    def test_history_returns_saved_reports(self, mock_pulse):
        save_report(mock_pulse)
        save_report(mock_pulse)
        history = get_history()
        assert len(history) == 2

    def test_history_max_3(self, mock_pulse):
        for _ in range(5):
            save_report(mock_pulse)
        history = get_history()
        assert len(history) <= 3


class TestGetReport:

    def test_get_existing_report(self, mock_pulse):
        report_id = save_report(mock_pulse)
        report = get_report(report_id)
        assert report is not None
        assert report.metadata["app_name"] == "IndMoney"

    def test_get_nonexistent_report(self):
        report = get_report(9999)
        assert report is None


class TestDeleteReport:

    def test_delete_existing(self, mock_pulse):
        report_id = save_report(mock_pulse)
        assert delete_report(report_id) is True
        assert get_report(report_id) is None

    def test_delete_nonexistent(self):
        assert delete_report(9999) is False
