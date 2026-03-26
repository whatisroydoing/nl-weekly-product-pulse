import sys
sys.path.append('.')
from models.schemas import PulsePayload, Theme, Quote, ActionItem
from module_b.pdf_export import export_pdf

# 10,000 words is definitely larger than one A4 page
huge_text = "Word " * 10000 

pulse = PulsePayload(
    metadata={"app_name": "TestApp", "source": "Test", "review_count": "450", "generated_at": "26-Mar-2026 12:00"},
    summary_note="Test summary.",
    themes=[
        Theme(label="Theme 1", description="Desc", is_top_3=True, sentiment_score=80.0, review_count=100)
    ],
    quotes=[
        Quote(theme_label="Theme 1", text="Normal quote", rating=1)
    ],
    action_items=[
        ActionItem(id=1, linked_theme="Theme 1", title="Action 1", description=huge_text)
    ],
    footer="Test foot"
)

result = export_pdf(pulse, "exports")
print("PDF Export Result:", result)
