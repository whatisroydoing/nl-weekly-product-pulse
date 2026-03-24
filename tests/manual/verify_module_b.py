"""
Module B test — verifies PDF generation with full 9 quotes (3 per top theme).
Email test is skipped unless GMAIL_USER is set in .env.
"""

import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from models.schemas import PulsePayload, Theme, Quote, ActionItem
from module_b.pdf_export import export_pdf
from module_b.email_send import send_email

load_dotenv()


def _mock_pulse() -> PulsePayload:
    """Build a realistic mock PulsePayload with 9 quotes (3 per top theme)."""
    themes = [
        Theme(label="App Functionality Issues",
              description="Users report persistent bugs, crashes, and issues with order modification and graph display after recent updates.",
              review_count=20, is_top_3=True),
        Theme(label="User Experience",
              description="General praise for ease of use, clean UI, and smooth navigation across the app.",
              review_count=12, is_top_3=True),
        Theme(label="Customer Service Complaints",
              description="Slow support response times on WhatsApp and toll-free. Tickets closed without resolution.",
              review_count=10, is_top_3=True),
        Theme(label="Feature Requests",
              description="Users want better analytics, charts, balance sheets, and average NAV for mutual funds.",
              review_count=8, is_top_3=False),
        Theme(label="Performance & Stability",
              description="App speed issues on older phones, frequent syncing interruptions, and forced updates.",
              review_count=6, is_top_3=False),
    ]

    quotes = [
        # App Functionality Issues — 3 quotes
        Quote(text="Most buggy app in existence of internet. I am unable to make any investments. It just shows please update your KYC and when I click the button it shows it's successful but the issue persists.",
              theme_label="App Functionality Issues", rating=1),
        Quote(text="New update dated 5th march is terrible, line patterns are not accurately showing in graph. So many useless changes done which is irritating towards the easiness of trading!",
              theme_label="App Functionality Issues", rating=1),
        Quote(text="Lot of issues in modifying orders. The app is good but these bugs are taking lots of time. I raise tickets and they just close saying cancel and place order again.",
              theme_label="App Functionality Issues", rating=1),

        # User Experience — 3 quotes
        Quote(text="Very smooth app, it's very easy to use. Best trading app with clean interface and low brokerage charges.",
              theme_label="User Experience", rating=5),
        Quote(text="Pretty great app for investments in US stocks. Simple UI, easy to understand interface and easier deposit process.",
              theme_label="User Experience", rating=5),
        Quote(text="This is the best app for traders and investors. Brokerage charges are negligible and it automatically forms charts like bullish and bearish flags.",
              theme_label="User Experience", rating=5),

        # Customer Service Complaints — 3 quotes
        Quote(text="Customer service is getting worst day by day. No responses on WhatsApp, when you call the toll-free it just says everyone is busy call back later.",
              theme_label="Customer Service Complaints", rating=1),
        Quote(text="I was cheated. The app said I need to pay my credit card bill for a 5 dollar reward, I did. Then it said invest 5000 in US stocks. Finally the reward shows expired. Such a cheating app.",
              theme_label="Customer Service Complaints", rating=1),
        Quote(text="The refresh option of external portfolio has become absurd. Earlier it was just an OTP. Now some QR code is generated. Please revert back to the previous option.",
              theme_label="Customer Service Complaints", rating=1),
    ]

    actions = [
        ActionItem(id=1, title="Enhance App Stability",
                   description="Run a focused bug-fix sprint targeting the top reported crashes and order modification issues. Prioritize the graph display fix from the 5th March update.",
                   linked_theme="App Functionality Issues"),
        ActionItem(id=2, title="Revamp Customer Service Protocols",
                   description="Set a 24-hour SLA for all support tickets. Reopen auto-closed tickets where the user reported the issue persists. Staff the toll-free line during market hours.",
                   linked_theme="Customer Service Complaints"),
        ActionItem(id=3, title="Leverage Positive User Feedback",
                   description="Use the high-rated reviews highlighting ease of use and low brokerage for Play Store listing optimization and marketing campaigns.",
                   linked_theme="User Experience"),
    ]

    return PulsePayload(
        metadata={
            "app_name":     "IndMoney",
            "source":       "Google Play Store",
            "review_count": 100,
            "generated_at": datetime.now().strftime("%d-%b-%Y %H:%M"),
        },
        themes=themes,
        quotes=quotes,
        summary_note=(
            "Users have expressed significant concerns regarding app functionality, "
            "highlighting persistent bugs, crashes, and issues with order modifications "
            "following recent updates. The graph display changes from the 5th March update "
            "were particularly criticised. However, positive feedback centres around the "
            "app's ease of use, clean interface, and competitive brokerage charges, with "
            "several users calling it the best trading app available. Customer service "
            "remains a pain point — users report unresponsive WhatsApp support, "
            "auto-closed tickets, and understaffed toll-free lines. Feature requests "
            "indicate appetite for deeper analytics including charts, balance sheets, "
            "and average NAV tracking for mutual funds."
        ),
        action_items=actions,
        footer=f"Report generated on {datetime.now().strftime('%d-%b-%Y %H:%M')} for google play store",
        approval_status="APPROVED",
    )


def test_pdf():
    print("\n[B1] Testing PDF Export...")
    pulse = _mock_pulse()
    result = export_pdf(pulse, output_dir="exports")
    if result["success"]:
        path = result["pdf_path"]
        size = Path(path).stat().st_size
        print(f"     SUCCESS: PDF created at {path} ({size:,} bytes)")
        print(f"     Themes: {len(pulse.themes)}, Quotes: {len(pulse.quotes)}, Actions: {len(pulse.action_items)}")
    else:
        print(f"     ERROR: {result.get('error')}")
    return result


def test_email(pdf_path: str = ""):
    gmail_user = os.environ.get("GMAIL_USER", "")
    if not gmail_user:
        print("\n[B2] Skipping email test — GMAIL_USER not set in .env")
        return

    print(f"\n[B2] Testing Email Send to {gmail_user}...")
    pulse = _mock_pulse()
    result = send_email(pulse, recipients=[gmail_user], pdf_path=pdf_path)
    if result["success"]:
        print(f"     SUCCESS: Email sent to {gmail_user}")
    else:
        print(f"     ERROR: {result.get('error')}")


if __name__ == "__main__":
    print("Testing Module B pipeline...")
    pdf_result = test_pdf()
    pdf_path = pdf_result.get("pdf_path", "") if pdf_result.get("success") else ""
    test_email(pdf_path=pdf_path)
    print("\nModule B test complete!")
