"""Tests for Module A2 -- Theme Clustering."""

import json
import pytest
from unittest.mock import patch, MagicMock
from models.schemas import RawReview
from module_a.clustering import cluster_themes


@pytest.fixture
def mock_reviews():
    """Generate a set of mock raw reviews."""
    return [
        RawReview(text=f"This is review {i} with enough text to be meaningful", rating=(i % 5) + 1, date="2026-03-10", source="Google Play Store")
        for i in range(20)
    ]


@pytest.fixture
def mock_openai_response():
    """Build a fake OpenAI chat completion response."""
    data = {
        "themes": [
            {"label": "App Bugs", "description": "Users report crashes", "review_count": 8, "is_top_3": True},
            {"label": "UX Praise", "description": "Positive feedback", "review_count": 6, "is_top_3": True},
            {"label": "Customer Service", "description": "Slow support", "review_count": 4, "is_top_3": True},
            {"label": "Feature Requests", "description": "Want more charts", "review_count": 2, "is_top_3": False},
        ],
        "quotes": [
            {"text": "Quote 1", "theme_label": "App Bugs", "rating": 1},
            {"text": "Quote 2", "theme_label": "App Bugs", "rating": 2},
            {"text": "Quote 3", "theme_label": "App Bugs", "rating": 1},
            {"text": "Quote 4", "theme_label": "UX Praise", "rating": 5},
            {"text": "Quote 5", "theme_label": "UX Praise", "rating": 5},
            {"text": "Quote 6", "theme_label": "UX Praise", "rating": 4},
            {"text": "Quote 7", "theme_label": "Customer Service", "rating": 1},
            {"text": "Quote 8", "theme_label": "Customer Service", "rating": 2},
            {"text": "Quote 9", "theme_label": "Customer Service", "rating": 1},
        ],
    }

    mock_message = MagicMock()
    mock_message.content = json.dumps(data)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


class TestClusterThemes:

    @patch("module_a.clustering.OpenAI")
    def test_returns_themed_analysis(self, mock_openai_cls, mock_reviews, mock_openai_response):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_cls.return_value = mock_client

        result = cluster_themes(mock_reviews)
        assert len(result.themes) <= 5
        assert len(result.quotes) <= 9

    @patch("module_a.clustering.OpenAI")
    def test_top_3_flagged(self, mock_openai_cls, mock_reviews, mock_openai_response):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_cls.return_value = mock_client

        result = cluster_themes(mock_reviews)
        top_3 = [t for t in result.themes if t.is_top_3]
        assert len(top_3) == 3

    @patch("module_a.clustering.OpenAI")
    def test_quotes_per_theme(self, mock_openai_cls, mock_reviews, mock_openai_response):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_cls.return_value = mock_client

        result = cluster_themes(mock_reviews)
        quotes_by_theme = {}
        for q in result.quotes:
            quotes_by_theme.setdefault(q.theme_label, []).append(q)

        for theme_label, quotes in quotes_by_theme.items():
            assert len(quotes) <= 3, f"Theme '{theme_label}' has {len(quotes)} quotes (max 3)"
