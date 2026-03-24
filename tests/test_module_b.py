"""Tests for Module B -- PDF Export and Email Send."""

import os
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from models.schemas import PulsePayload, Theme, Quote, ActionItem
from module_b.pdf_export import export_pdf
from module_b.email_send import send_email


@pytest.fixture
def mock_pulse():
    """Build a mock PulsePayload for testing."""
    return PulsePayload(
        metadata={
            "app_name": "IndMoney",
            "source": "Google Play Store",
            "review_count": 100,
            "generated_at": datetime.now().strftime("%d-%b-%Y %H:%M"),
        },
        themes=[
            Theme(label="Bugs", description="Crashes", review_count=20, is_top_3=True),
            Theme(label="UX", description="Good UI", review_count=12, is_top_3=True),
            Theme(label="Support", description="Slow", review_count=10, is_top_3=True),
        ],
        quotes=[
            Quote(text="App crashes often", theme_label="Bugs", rating=1),
            Quote(text="Very smooth app", theme_label="UX", rating=5),
            Quote(text="Support never responds", theme_label="Support", rating=1),
        ],
        summary_note="Test summary note for unit testing.",
        action_items=[
            ActionItem(id=1, title="Fix Bugs", description="Fix crashes.", linked_theme="Bugs"),
        ],
        footer="Test footer",
        approval_status="APPROVED",
    )


class TestPDFExport:

    def test_pdf_creates_file(self, mock_pulse, tmp_path):
        result = export_pdf(mock_pulse, output_dir=str(tmp_path))
        assert result["success"] is True
        assert Path(result["pdf_path"]).exists()
        assert Path(result["pdf_path"]).stat().st_size > 0

    def test_pdf_filename_format(self, mock_pulse, tmp_path):
        result = export_pdf(mock_pulse, output_dir=str(tmp_path))
        filename = Path(result["pdf_path"]).name
        assert filename.startswith("IndMoney_Pulse_")
        assert filename.endswith(".pdf")

    def test_pdf_creates_output_dir(self, mock_pulse, tmp_path):
        nested = str(tmp_path / "nested" / "dir")
        result = export_pdf(mock_pulse, output_dir=nested)
        assert result["success"] is True
        assert Path(nested).exists()


class TestEmailSend:

    def test_empty_recipients_error(self, mock_pulse):
        result = send_email(mock_pulse, recipients=[])
        assert result["success"] is False
        assert "At least one" in result["error"]

    def test_too_many_recipients_error(self, mock_pulse):
        result = send_email(mock_pulse, recipients=["a@b.com"] * 6)
        assert result["success"] is False
        assert "Maximum 5" in result["error"]

    def test_missing_credentials_error(self, mock_pulse):
        with patch.dict(os.environ, {"GMAIL_USER": "", "GMAIL_APP_PASSWORD": ""}, clear=False):
            result = send_email(mock_pulse, recipients=["test@example.com"])
            assert result["success"] is False
            assert "not set" in result["error"]

    @patch("module_b.email_send.smtplib.SMTP")
    def test_email_sends_with_valid_config(self, mock_smtp, mock_pulse):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        with patch.dict(os.environ, {"GMAIL_USER": "test@gmail.com", "GMAIL_APP_PASSWORD": "testpass"}):
            result = send_email(mock_pulse, recipients=["user@example.com"])
            assert result["success"] is True
