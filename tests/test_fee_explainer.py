"""
Tests for Module F — Fee Explainer
"""

import sys
import os
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.schemas import FeeExplainerResult, PulsePayload
from module_f.fee_explainer import generate_fee_explanation
from module_f.fee_scraper import _should_rescrape, _is_second_monday, CACHE_FILE, get_fee_data
from module_f.google_doc_writer import append_to_doc

# --- F2 Template Tests ---

@pytest.fixture
def sample_scrape_data():
    return {
        "last_scraped": "2026-03-24",
        "funds": {
            "ICICI Prudential Value Fund": {
                "exit_load": "1% test load",
                "url": "https://url1.com"
            },
            "ICICI Prudential Corporate Bond Fund": {
                "exit_load": "Nil test load",
                "url": "https://url2.com"
            }
        }
    }

def test_template_output_compliance(sample_scrape_data):
    """Verify fee_explainer returns exactly 5 bullets, 2 source links, and valid date"""
    result = generate_fee_explanation(sample_scrape_data)
    
    assert isinstance(result, FeeExplainerResult)
    assert len(result.bullets) == 5
    assert len(result.source_links) == 2
    assert result.last_checked == "2026-03-24"
    assert result.scenario == "Exit Load"
    
    # Check that both funds are cited in a single bullet
    combined_bullet = result.bullets[1]
    assert "ICICI Prudential Value Fund" in combined_bullet
    assert "ICICI Prudential Corporate Bond Fund" in combined_bullet
    assert "1% test load" in combined_bullet
    assert "Nil test load" in combined_bullet

def test_neutral_tone_check(sample_scrape_data):
    """Assert bullets contain no recommendation words"""
    result = generate_fee_explanation(sample_scrape_data)
    forbidden_words = ["should", "recommend", "better", "best", "must", "always", "never"]
    
    for bullet in result.bullets:
        bullet_lower = bullet.lower()
        for word in forbidden_words:
            assert word not in bullet_lower, f"Found forbidden word '{word}' in bullet: {bullet}"

def test_fee_explainer_schema(sample_scrape_data):
    """Validate the Pydantic model serializes/deserializes correctly"""
    result = generate_fee_explanation(sample_scrape_data)
    json_data = result.model_dump_json()
    
    # Needs to parse back into the exact same structure
    parsed = FeeExplainerResult.model_validate_json(json_data)
    assert parsed.bullets == result.bullets
    assert parsed.source_links == result.source_links

# --- F1 Cache Tests ---

def test_is_second_monday():
    # 2026-03-09 is a Monday (2nd Monday of March 2026)
    assert _is_second_monday(datetime(2026, 3, 9)) is True
    # 2026-03-02 is a Monday (1st Monday)
    assert _is_second_monday(datetime(2026, 3, 2)) is False
    # 2026-03-10 is a Tuesday
    assert _is_second_monday(datetime(2026, 3, 10)) is False

@patch("module_f.fee_scraper.CACHE_FILE")
def test_should_rescrape_no_cache(mock_cache_file):
    mock_cache_file.exists.return_value = False
    assert _should_rescrape() is True

@patch("module_f.fee_scraper.datetime")
@patch("module_f.fee_scraper.CACHE_FILE")
def test_should_not_rescrape_if_not_second_monday(mock_cache_file, mock_datetime, tmp_path):
    # Setup cache file
    cache_path = tmp_path / "fee_cache.json"
    cache_path.write_text('{"last_scraped": "2026-03-01"}')
    mock_cache_file.exists.return_value = True
    
    # Open real file instead of mocked path when called
    with patch('builtins.open', open):
        with patch('module_f.fee_scraper.CACHE_FILE', cache_path):
            # Today is not 2nd Monday
            mock_datetime.now.return_value = datetime(2026, 3, 10) 
            assert _should_rescrape() is False

# --- F3 Google Doc Writer Tests ---

@patch("module_f.google_doc_writer.build")
@patch("module_f.google_doc_writer._get_credentials")
@patch.dict(os.environ, {"GOOGLE_DOC_ID": "test_doc_id"})
def test_google_doc_append(mock_get_creds, mock_build):
    # Mock pulse
    pulse = PulsePayload(
        metadata={"generated_at": "2026-03-24 10:00:00"},
        themes=[],
        quotes=[],
        summary_note="Test Weekly Pulse Summary",
        action_items=[],
        footer="Test Footer"
    )
    
    # Mock fee explainer
    fee = FeeExplainerResult(
        scenario="Exit Load",
        bullets=["Bullet 1", "Bullet 2"],
        source_links=["http://link1", "http://link2"],
        last_checked="2026-03-24"
    )
    
    # Mock API client
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_documents = MagicMock()
    mock_service.documents.return_value = mock_documents
    
    # Mock documents().get().execute() for document length
    mock_get = MagicMock()
    mock_documents.get.return_value = mock_get
    mock_get.execute.return_value = {
        "body": {
            "content": [{"endIndex": 1}]
        }
    }
    
    mock_batch_update = MagicMock()
    mock_documents.batchUpdate.return_value = mock_batch_update
    mock_batch_update.execute.return_value = {}
    
    # Run
    result = append_to_doc(pulse, fee)
    
    # Assertions
    assert result is True
    mock_get_creds.assert_called_once()
    mock_build.assert_called_once()
    mock_documents.batchUpdate.assert_called_once()
    
    # Inspect the payload sent
    call_args = mock_documents.batchUpdate.call_args[1]
    assert call_args["documentId"] == "test_doc_id"
    requests = call_args["body"]["requests"]
    assert len(requests) == 5
    
    insert_text = requests[0]["insertText"]["text"]
    assert "Test Weekly Pulse Summary" in insert_text
    assert "Exit Load" in insert_text
    assert "Bullet 1" in insert_text
    assert "http://link1" in insert_text
