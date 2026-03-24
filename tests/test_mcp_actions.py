"""Tests for Module B — MCP Output Actions (Gate + Export integration)."""

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from models.schemas import PulsePayload, Theme, Quote, ActionItem
from module_c.gate import ApprovalGate, GateAction
from module_b.email_send import send_email
from module_b.pdf_export import export_pdf


def _make_pulse() -> PulsePayload:
    """Build a realistic PulsePayload for testing."""
    return PulsePayload(
        metadata={
            "app_name": "IndMoney",
            "source": "Google Play Store",
            "review_count": 200,
            "generated_at": datetime.now().strftime("%d-%b-%Y %H:%M"),
        },
        themes=[Theme(label="Bugs", description="Crashes reported", review_count=20, is_top_3=True)],
        quotes=[Quote(text="App keeps crashing", theme_label="Bugs", rating=1)],
        summary_note="Test summary for gating tests.",
        action_items=[ActionItem(id=1, title="Fix Bugs", description="Fix crash issues.", linked_theme="Bugs")],
        footer="Test footer",
        approval_status="PENDING",
    )


class TestGateEnforcedPDFExport:

    def test_pdf_export_works_after_approval(self, tmp_path):
        """PDF export succeeds when pulse is approved via gate."""
        pulse = _make_pulse()
        gate = ApprovalGate(pulse)

        # Approve first
        gate.process_action(GateAction.APPROVE_PDF)
        assert gate.is_approved()

        # Export should succeed
        result = export_pdf(gate.pulse, output_dir=str(tmp_path))
        assert result["success"] is True

    def test_pulse_starts_pending(self):
        """A new pulse starts in PENDING status — gate blocks export."""
        pulse = _make_pulse()
        gate = ApprovalGate(pulse)
        assert not gate.can_export(), "Gate should block export before approval"
        assert pulse.approval_status == "PENDING"


class TestGateEnforcedEmail:

    def test_email_rejects_more_than_5_recipients(self):
        """Email send rejects > 5 recipients."""
        pulse = _make_pulse()
        result = send_email(pulse, recipients=["a@b.com"] * 6)
        assert result["success"] is False
        assert "Maximum 5" in result["error"]

    def test_email_requires_at_least_1_recipient(self):
        """Email send requires at least 1 recipient."""
        pulse = _make_pulse()
        result = send_email(pulse, recipients=[])
        assert result["success"] is False
        assert "At least one" in result["error"]

    def test_gate_reject_blocks_further_actions(self):
        """Rejecting via gate sets status to REJECTED and blocks export."""
        pulse = _make_pulse()
        gate = ApprovalGate(pulse)
        gate.process_action(GateAction.REJECT, feedback="Bad data")
        assert not gate.can_export()
        assert pulse.approval_status == "REJECTED"
