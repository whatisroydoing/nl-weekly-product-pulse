"""
Module D test -- verifies SQLite report history (save, list, get, prune).
Uses a mock PulsePayload -- no API calls needed.
"""

import os
from datetime import datetime

from models.schemas import PulsePayload, Theme, Quote, ActionItem
from module_d.history import save_report, get_history, get_report, delete_report


def _mock_pulse(label: str = "Test") -> PulsePayload:
    """Build a minimal mock PulsePayload."""
    return PulsePayload(
        metadata={
            "app_name": "IndMoney",
            "source": "Google Play Store",
            "review_count": 100,
            "generated_at": datetime.now().strftime("%d-%b-%Y %H:%M"),
        },
        themes=[
            Theme(label=f"{label} Theme 1", description="Test theme", review_count=20, is_top_3=True),
            Theme(label=f"{label} Theme 2", description="Test theme", review_count=10, is_top_3=False),
        ],
        quotes=[
            Quote(text="Sample quote", theme_label=f"{label} Theme 1", rating=4),
        ],
        summary_note=f"This is a test summary for {label}.",
        action_items=[
            ActionItem(id=1, title=f"{label} Action", description="Test action.", linked_theme=f"{label} Theme 1"),
        ],
        footer=f"Test report -- {label}",
        approval_status="APPROVED",
    )


def test_history():
    print("Testing Module D -- Report History...\n")

    # Clean up any existing test DB
    if os.path.exists("reports.db"):
        os.remove("reports.db")
        print("[Setup] Removed old reports.db")

    # 1. Save 4 reports (should prune to keep only 3)
    print("\n[D1] Saving 4 reports (max_reports=3, should prune oldest)...")
    ids = []
    for i in range(1, 5):
        pulse = _mock_pulse(label=f"Report_{i}")
        report_id = save_report(pulse, pdf_path=f"exports/test_{i}.pdf")
        ids.append(report_id)
        print(f"     Saved Report_{i} -> id={report_id}")

    # 2. Get history -- should only return 3
    print("\n[D2] Getting history (should be 3 reports)...")
    history = get_history()
    print(f"     Found {len(history)} reports:")
    for h in history:
        print(f"       id={h['id']} | {h['report_name']} | {h['review_count']} reviews | PDF: {h['pdf_path']}")

    assert len(history) <= 3, f"Expected max 3 reports, got {len(history)}"
    print("     PASS: Pruning works -- only 3 reports kept")

    # 3. Get a specific report
    latest_id = history[0]["id"]
    print(f"\n[D3] Getting full report for id={latest_id}...")
    report = get_report(latest_id)
    if report:
        print(f"     PASS: Retrieved: {report.metadata['app_name']} -- {report.summary_note[:60]}...")
    else:
        print("     FAIL: Report not found!")

    # 4. Get a non-existent report
    print("\n[D4] Getting non-existent report (id=9999)...")
    missing = get_report(9999)
    assert missing is None, "Expected None for missing report"
    print("     PASS: Returns None for missing ID")

    # 5. Delete a report
    print(f"\n[D5] Deleting report id={latest_id}...")
    deleted = delete_report(latest_id)
    assert deleted, "Expected deletion to succeed"
    remaining = get_history()
    print(f"     PASS: Deleted. {len(remaining)} reports remaining.")

    print("\nSUCCESS: Module D -- All tests passed!")


if __name__ == "__main__":
    test_history()
