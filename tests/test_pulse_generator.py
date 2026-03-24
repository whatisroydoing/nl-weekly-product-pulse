"""Tests for Module A4 — Pulse Generation."""

import json
import pytest
from unittest.mock import patch, MagicMock

from models.schemas import ThemedAnalysis, Theme, Quote
from module_a.pulse_generator import generate_pulse


@pytest.fixture
def mock_analysis():
    """Build a realistic ThemedAnalysis fixture matching A2+A3 output."""
    return ThemedAnalysis(
        themes=[
            Theme(label="App Crashes", description="Frequent crashes on Android 14", review_count=40, is_top_3=True),
            Theme(label="Great UI", description="Users love the clean design", review_count=30, is_top_3=True),
            Theme(label="Slow Support", description="Customer support response time is poor", review_count=25, is_top_3=True),
            Theme(label="Feature Requests", description="Users want more chart types", review_count=10, is_top_3=False),
        ],
        quotes=[
            Quote(text="App crashes every time I open portfolio", theme_label="App Crashes", rating=1),
            Quote(text="The UI is very smooth and intuitive", theme_label="Great UI", rating=5),
            Quote(text="Support took 2 weeks to respond", theme_label="Slow Support", rating=1),
        ],
    )


@pytest.fixture
def mock_openai_pulse_response():
    """Fake OpenAI response for pulse generation."""
    data = {
        "summary_note": (
            "This week's analysis of 200 Google Play Store reviews reveals a mixed sentiment. "
            "App stability remains the top concern with users reporting frequent crashes. "
            "However, the UI design continues to receive strong praise."
        ),
        "action_items": [
            {"id": 1, "title": "Fix Android 14 Crashes", "description": "Investigate crash logs for Android 14 devices.", "linked_theme": "App Crashes"},
            {"id": 2, "title": "Expand Chart Options", "description": "Add candlestick and comparison charts.", "linked_theme": "Feature Requests"},
            {"id": 3, "title": "Improve Support SLA", "description": "Reduce first-response time to under 24 hours.", "linked_theme": "Slow Support"},
        ],
    }
    mock_message = MagicMock()
    mock_message.content = json.dumps(data)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


class TestPulseGenerator:

    @patch("module_a.pulse_generator.OpenAI")
    def test_summary_within_word_limit(self, mock_openai_cls, mock_analysis, mock_openai_pulse_response):
        """Test that summary_note is ≤ 250 words."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_pulse_response
        mock_openai_cls.return_value = mock_client

        pulse = generate_pulse(mock_analysis, review_count=200)
        word_count = len(pulse.summary_note.split())
        assert word_count <= 250, f"Summary has {word_count} words (max 250)"

    @patch("module_a.pulse_generator.OpenAI")
    def test_exactly_3_action_items(self, mock_openai_cls, mock_analysis, mock_openai_pulse_response):
        """Test that exactly 3 action items are generated."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_pulse_response
        mock_openai_cls.return_value = mock_client

        pulse = generate_pulse(mock_analysis, review_count=200)
        assert len(pulse.action_items) == 3

    @patch("module_a.pulse_generator.OpenAI")
    def test_action_items_linked_to_themes(self, mock_openai_cls, mock_analysis, mock_openai_pulse_response):
        """Test that each action item is linked to a valid theme label."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_pulse_response
        mock_openai_cls.return_value = mock_client

        pulse = generate_pulse(mock_analysis, review_count=200)
        theme_labels = {t.label for t in pulse.themes}
        for action in pulse.action_items:
            assert action.linked_theme in theme_labels, (
                f"Action '{action.title}' linked to '{action.linked_theme}' which is not a valid theme"
            )

    @patch("module_a.pulse_generator.OpenAI")
    def test_pulse_payload_structure(self, mock_openai_cls, mock_analysis, mock_openai_pulse_response):
        """Test that the returned PulsePayload has all required fields."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_pulse_response
        mock_openai_cls.return_value = mock_client

        pulse = generate_pulse(mock_analysis, review_count=200)
        assert pulse.approval_status == "PENDING"
        assert pulse.metadata["app_name"] == "IndMoney"
        assert pulse.metadata["review_count"] == 200
        assert pulse.metadata["source"] == "Google Play Store"
        assert len(pulse.footer) > 0
        assert len(pulse.themes) > 0
        assert len(pulse.quotes) > 0
