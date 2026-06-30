from fastapi.testclient import TestClient
from src.api.main import app
from src.api.state import get_state
import json
import os

client = TestClient(app)

def test_config_roles():
    response = client.get("/config/roles")
    assert response.status_code == 200
    data = response.json()
    assert "Advanced Forward" in data

def test_squad_depth_no_data():
    # Will be 404 because "NonExistentTeam" is not in the data
    response = client.get("/squad/depth?team_name=NonExistentTeam&target_tactic=Gegenpress")
    assert response.status_code == 404

def test_transfers_recommend():
    req_body = {
        "target_role": "Advanced Forward",
        "budget": {
            "max_transfer": 50000000.0,
            "max_wage": 5000000.0
        },
        "target_position_group": "ST"
    }
    # It might return empty list if no players match, but should be 200 OK
    response = client.post("/transfers/recommend?team_name=SomeTeam", json=req_body)
    assert response.status_code == 200
    data = response.json()
    assert "best_fit" in data
    assert "all_feasible" in data

def test_feedback():
    req_body = {
        "player_id": "Test Player",
        "context": "transfer_recommendation",
        "decision": "shortlist"
    }
    response = client.post("/feedback", json=req_body)
    assert response.status_code == 200
    assert response.json()["status"] == "Success"
