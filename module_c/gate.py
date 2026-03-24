"""
C1 + C2 — Approval Gate Logic
Manages the review state machine for pulse payloads.
Ensures no downstream action fires without explicit user approval.
"""

from enum import Enum
from models.schemas import PulsePayload


class GateAction(str, Enum):
    """Actions the user can take on a pulse."""
    APPROVE_PDF = "approve_pdf"
    APPROVE_EMAIL = "approve_email"
    REJECT = "reject"
    REGENERATE = "regenerate"


class ApprovalGate:
    """
    Manages the implicit approval gate.
    The user reviews the pulse on-screen and explicitly triggers actions.
    """

    def __init__(self, pulse: PulsePayload):
        self.pulse = pulse

    def approve(self) -> PulsePayload:
        """Mark the pulse as approved — enables downstream actions."""
        self.pulse.approval_status = "APPROVED"
        return self.pulse

    def reject(self, feedback: str = "") -> PulsePayload:
        """Reject the pulse — blocks downstream, optionally stores feedback."""
        self.pulse.approval_status = "REJECTED"
        return self.pulse

    def is_approved(self) -> bool:
        """Check if the pulse has been approved."""
        return self.pulse.approval_status == "APPROVED"

    def can_export(self) -> bool:
        """Check if the pulse can be exported (PDF or email)."""
        return self.is_approved()

    def process_action(self, action: GateAction, **kwargs) -> dict:
        """
        Process a user action on the pulse.

        Args:
            action: The GateAction to process.
            **kwargs: Additional arguments (e.g., feedback for reject).

        Returns:
            dict with the action result and next step.
        """
        if action == GateAction.APPROVE_PDF:
            self.approve()
            return {"status": "approved", "next": "export_pdf"}

        elif action == GateAction.APPROVE_EMAIL:
            self.approve()
            return {"status": "approved", "next": "send_email"}

        elif action == GateAction.REJECT:
            feedback = kwargs.get("feedback", "")
            self.reject(feedback)
            return {"status": "rejected", "next": "regenerate", "feedback": feedback}

        elif action == GateAction.REGENERATE:
            self.pulse.approval_status = "PENDING"
            return {"status": "pending", "next": "regenerate"}

        return {"status": "error", "message": f"Unknown action: {action}"}
