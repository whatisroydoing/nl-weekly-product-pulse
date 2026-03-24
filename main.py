"""
IndMoney Weekly Product Pulse — Main Orchestrator

Root entry point for running the analysis pipeline.
Can be used for CLI testing before the UI is built.

Usage:
    python main.py --reviews 200
    python main.py --reviews 400
    python main.py --reviews 600
"""

import argparse
import json
import sys

from module_a.ingestion import fetch_reviews
from module_a.clustering import cluster_themes
from module_a.pii_masker import mask_analysis
from module_a.pulse_generator import generate_pulse
from module_c.gate import ApprovalGate, GateAction
from module_b.pdf_export import export_pdf_sync
from module_b.email_send import send_email_sync
from module_d.history import save_report


def run_pipeline(review_count: int) -> dict:
    """
    Execute the full pipeline: A1 → A2 → A3 → A4 → C → (B1/B2) → D.

    Args:
        review_count: Number of reviews to fetch (200, 400, or 600).

    Returns:
        The pulse payload as a dict.
    """
    print(f"\n{'='*60}")
    print(f"  IndMoney Weekly Product Pulse")
    print(f"  Analyzing {review_count} reviews from Google Play Store")
    print(f"{'='*60}\n")

    # --- Module A: Analysis Engine ---

    # A1: Ingestion
    print("[A1] Fetching reviews...")
    raw_reviews = fetch_reviews(review_count)
    print(f"     ✓ Fetched {len(raw_reviews)} reviews\n")

    # A2: Clustering (Gemini — 1 API call)
    print("[A2] Clustering themes with Gemini...")
    analysis = cluster_themes(raw_reviews)
    print(f"     ✓ Found {len(analysis.themes)} themes, {len(analysis.quotes)} quotes\n")

    # A3: PII Masking (Regex — 0 API calls)
    print("[A3] Masking PII...")
    analysis = mask_analysis(analysis)
    print(f"     ✓ PII masked\n")

    # A4: Pulse Generation (Grok — 1 API call)
    print("[A4] Generating pulse with Grok...")
    pulse = generate_pulse(analysis=analysis, review_count=review_count)
    print(f"     ✓ Summary: {len(pulse.summary_note.split())} words")
    print(f"     ✓ Action items: {len(pulse.action_items)}\n")

    # --- Module C: Approval Gate ---
    print(f"{'='*60}")
    print("  PULSE REVIEW")
    print(f"{'='*60}\n")

    # Display summary
    print(f"📋 THEMES ({len(pulse.themes)} total, top 3 marked ★):\n")
    for t in pulse.themes:
        marker = " ★" if t.is_top_3 else ""
        print(f"   • {t.label}{marker} — {t.description} ({t.review_count} reviews)")

    print(f"\n💬 QUOTES:\n")
    for q in pulse.quotes:
        print(f'   [{q.theme_label}] "{q.text}" ({q.rating}★)')

    print(f"\n📝 SUMMARY ({len(pulse.summary_note.split())} words):\n")
    print(f"   {pulse.summary_note}\n")

    print(f"🎯 ACTION ITEMS:\n")
    for a in pulse.action_items:
        print(f"   {a.id}. {a.title} [{a.linked_theme}]")
        print(f"      {a.description}\n")

    print(f"📎 {pulse.footer}\n")

    # --- Gate Decision ---
    gate = ApprovalGate(pulse)

    print(f"{'='*60}")
    print("  Choose an action:")
    print("  [1] Download PDF")
    print("  [2] Send Email")
    print("  [3] Regenerate")
    print("  [4] Exit (save to history only)")
    print(f"{'='*60}")

    choice = input("\n  Your choice (1-4): ").strip()

    if choice == "1":
        gate.process_action(GateAction.APPROVE_PDF)
        result = export_pdf_sync(pulse)
        print(f"\n  ✓ PDF exported: {result}")
        save_report(pulse, pdf_path=result.get("data", {}).get("pdf_path", ""))

    elif choice == "2":
        recipients_input = input("  Enter email addresses (comma-separated, max 5): ")
        recipients = [e.strip() for e in recipients_input.split(",") if e.strip()][:5]
        gate.process_action(GateAction.APPROVE_EMAIL)
        result = send_email_sync(pulse, recipients)
        print(f"\n  ✓ Email sent: {result}")
        save_report(pulse)

    elif choice == "3":
        print("\n  ↻ Regenerating...")
        return run_pipeline(review_count)  # Recursive re-run

    else:
        print("\n  Saving to history and exiting.")
        save_report(pulse)

    return pulse.model_dump()


def main():
    parser = argparse.ArgumentParser(
        description="IndMoney Weekly Product Pulse — CLI"
    )
    parser.add_argument(
        "--reviews",
        type=int,
        choices=[200, 300, 400],
        default=200,
        help="Number of reviews to analyze (200, 300, or 400)",
    )
    args = parser.parse_args()

    try:
        result = run_pipeline(args.reviews)
        print(f"\n✅ Pipeline complete.\n")
    except KeyboardInterrupt:
        print("\n\n  Cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
