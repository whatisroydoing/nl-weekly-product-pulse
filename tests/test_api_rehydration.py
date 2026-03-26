import pytest
from fastapi.testclient import TestClient
from module_e.api import app, _pulse_store
from module_d.history import save_report
from models.schemas import PulsePayload
from datetime import datetime

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_state():
    """Clear memory store and DB before each test."""
    _pulse_store.clear()
    import os
    if os.path.exists("reports.db"):
        os.remove("reports.db")
    yield
    if os.path.exists("reports.db"):
        os.remove("reports.db")

def test_api_auto_rehydrates_from_db():
    """
    Test that if a pulse is in the DB but NOT in memory, 
    the API can still find it and re-populate the store.
    """
    # 1. Create a dummy pulse and save it to DB
    now_str = datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    pulse = PulsePayload(
        summary_note="Test summary",
        themes=[],
        quotes=[],
        action_items=[],
        metadata={"generated_at": now_str, "app_name": "TestApp", "source": "Test", "review_count": 100},
        footer="Test footer",
        approval_status="PENDING"
    )
    db_id = save_report(pulse)
    
    pulse_id = now_str.replace(" ", "_").replace(":", "-")
    
    # 2. Ensure memory store is empty
    _pulse_store.clear()
    assert pulse_id not in _pulse_store
    
    # 3. Call an endpoint that uses the pulse
    # This should trigger _rehydrate_pulse and succeed
    response = client.get(f"/pulse/{pulse_id}")
    
    assert response.status_code == 200
    assert response.json()["pulse"]["summary_note"] == "Test summary"
    
    # 4. Verify it was rehydrated in memory
    assert pulse_id in _pulse_store
    assert _pulse_store[pulse_id]["db_id"] == db_id
