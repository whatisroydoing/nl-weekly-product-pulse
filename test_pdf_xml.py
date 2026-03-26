import sys
sys.path.append('.')
from models.schemas import PulsePayload, Theme, Quote, ActionItem
from module_b.pdf_export import export_pdf

# Testing explicitly "< 3" since the LLM might write "ratings < 3"
text_with_bracket = "The user said their rating was < 3 stars."

pulse = PulsePayload(
    metadata={"app_name": "TestApp", "source": "Test", "review_count": "450", "generated_at": "26-Mar-2026 12:00"},
    summary_note="Test summary.",
    themes=[
        Theme(label="Theme 1", description="Desc", is_top_3=True, sentiment_score=80.0, review_count=100)
    ],
    quotes=[
        Quote(theme_label="Theme 1", text="Normal", rating=1)
    ],
    action_items=[
        ActionItem(id=1, linked_theme="Theme 1", title="Action 1", description=text_with_bracket)
    ],
    footer="Test foot"
)

result = export_pdf(pulse, "exports")
print("PDF Export Result:", result)
