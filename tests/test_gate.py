"""Tests for Module C — Approval Gate."""

from module_c.gate import ApprovalGate, GateAction
from models.schemas import PulsePayload


def _make_test_pulse() -> PulsePayload:
    return PulsePayload(
        metadata={"app_name": "Test", "source": "Test", "review_count": 200, "generated_at": "01-Jan-2026 10:00"},
        themes=[],
        quotes=[],
        summary_note="Test summary",
        action_items=[],
        footer="Test footer",
        approval_status="PENDING",
    )


def test_approve_sets_status():
    gate = ApprovalGate(_make_test_pulse())
    gate.approve()
    assert gate.is_approved()


def test_reject_sets_status():
    gate = ApprovalGate(_make_test_pulse())
    gate.reject("bad data")
    assert not gate.is_approved()


def test_cannot_export_before_approval():
    gate = ApprovalGate(_make_test_pulse())
    assert not gate.can_export()


def test_can_export_after_approval():
    gate = ApprovalGate(_make_test_pulse())
    gate.approve()
    assert gate.can_export()


def test_process_action_approve_pdf():
    gate = ApprovalGate(_make_test_pulse())
    result = gate.process_action(GateAction.APPROVE_PDF)
    assert result["status"] == "approved"
    assert result["next"] == "export_pdf"
