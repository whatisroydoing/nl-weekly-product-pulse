"""Tests for Module A3 -- PII Masking."""

import pytest
from module_a.pii_masker import mask_text, mask_analysis
from models.schemas import ThemedAnalysis, Theme, Quote


class TestMaskText:

    def test_mask_email(self):
        result = mask_text("Contact me at john@example.com for details")
        assert "john@example.com" not in result
        assert "[REDACTED]" in result

    def test_mask_phone_with_country_code(self):
        result = mask_text("Call me at +91 98765 43210")
        assert "[REDACTED]" in result

    def test_mask_phone_without_country_code(self):
        result = mask_text("My number is 9876543210")
        assert "[REDACTED]" in result

    def test_mask_account_number(self):
        result = mask_text("My account number is 1234567890")
        assert "[REDACTED]" in result

    def test_mask_name_context(self):
        result = mask_text("My name is John Smith")
        assert "[REDACTED]" in result

    def test_no_false_positive_clean_text(self):
        clean = "This app is great for tracking investments"
        result = mask_text(clean)
        assert "[REDACTED]" not in result

    def test_multiple_pii_in_one_text(self):
        text = "Contact john@test.com or call +91 98765 43210"
        result = mask_text(text)
        assert "john@test.com" not in result
        assert result.count("[REDACTED]") >= 2


class TestMaskAnalysis:

    def test_mask_analysis_masks_quotes(self):
        analysis = ThemedAnalysis(
            themes=[Theme(label="Test", description="desc", review_count=5, is_top_3=True)],
            quotes=[Quote(text="Email me at user@gmail.com", theme_label="Test", rating=3)],
        )
        masked = mask_analysis(analysis)
        assert "user@gmail.com" not in masked.quotes[0].text
        assert "[REDACTED]" in masked.quotes[0].text

    def test_mask_analysis_preserves_themes(self):
        analysis = ThemedAnalysis(
            themes=[Theme(label="Bug Reports", description="Users report bugs", review_count=10, is_top_3=True)],
            quotes=[Quote(text="Clean quote no PII", theme_label="Bug Reports", rating=4)],
        )
        masked = mask_analysis(analysis)
        assert masked.themes[0].label == "Bug Reports"
        assert masked.themes[0].review_count == 10
