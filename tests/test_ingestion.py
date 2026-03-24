"""Tests for Module A1 -- Review Ingestion."""

import pytest
from unittest.mock import patch, MagicMock
from module_a.ingestion import fetch_reviews


@pytest.fixture
def mock_config():
    return {
        "app": {"app_id": "in.indwealth", "name": "IndMoney", "source": "Google Play Store"},
        "ingestion": {
            "allowed_review_counts": [200, 300, 400],
            "min_words_per_review": 5,
        },
    }


def _fake_reviews(count):
    """Generate fake google-play-scraper review dicts."""
    reviews = []
    for i in range(count):
        reviews.append({
            "content": f"This is a test review number {i} with enough characters to pass the minimum length filter easily",
            "score": (i % 5) + 1,
            "at": f"2026-03-{10 - (i % 10):02d}",
        })
    return reviews, None


class TestFetchReviews:

    @patch("module_a.ingestion.load_config")
    @patch("module_a.ingestion.reviews")
    def test_valid_count_returns_reviews(self, mock_scraper, mock_cfg, mock_config):
        mock_cfg.return_value = mock_config
        mock_scraper.return_value = _fake_reviews(600)

        result = fetch_reviews(200)
        assert len(result) <= 200
        assert all(hasattr(r, "text") for r in result)

    @patch("module_a.ingestion.load_config")
    def test_invalid_count_raises_error(self, mock_cfg, mock_config):
        mock_cfg.return_value = mock_config

        with pytest.raises(ValueError, match="review_count must be one of"):
            fetch_reviews(999)

    @patch("module_a.ingestion.load_config")
    @patch("module_a.ingestion.reviews")
    def test_short_reviews_filtered(self, mock_scraper, mock_cfg, mock_config):
        mock_cfg.return_value = mock_config
        # Mix of short and long reviews (filter requires >= 5 words)
        short_reviews = [
            {"content": "good", "score": 5, "at": "2026-03-10"},
            {"content": "nice", "score": 4, "at": "2026-03-09"},
            {"content": "This is a long enough review that should pass the minimum word filter easily", "score": 3, "at": "2026-03-08"},
        ]
        mock_scraper.return_value = (short_reviews, None)

        result = fetch_reviews(200)
        assert len(result) == 1  # Only the long one passes

    @patch("module_a.ingestion.load_config")
    @patch("module_a.ingestion.reviews")
    def test_duplicate_reviews_filtered(self, mock_scraper, mock_cfg, mock_config):
        mock_cfg.return_value = mock_config
        dup_reviews = [
            {"content": "This is a duplicate review with enough words to pass the filter", "score": 5, "at": "2026-03-10"},
            {"content": "This is a duplicate review with enough words to pass the filter", "score": 5, "at": "2026-03-09"},
            {"content": "This is a unique review with enough words to pass the filter too", "score": 4, "at": "2026-03-08"},
        ]
        mock_scraper.return_value = (dup_reviews, None)

        result = fetch_reviews(200)
        assert len(result) == 2  # Duplicate removed

    @patch("module_a.ingestion.load_config")
    @patch("module_a.ingestion.reviews")
    def test_empty_text_filtered(self, mock_scraper, mock_cfg, mock_config):
        mock_cfg.return_value = mock_config
        mock_scraper.return_value = ([
            {"content": "", "score": 5, "at": "2026-03-10"},
            {"content": None, "score": 4, "at": "2026-03-09"},
        ], None)

        result = fetch_reviews(200)
        assert len(result) == 0
