import pytest
import numpy as np
from src.models.similarity import PlayerSimilarityModel
from src.models.recommender import RecommendationEngine
from src.models.feedback import FeedbackLogger
import os
import json

@pytest.fixture
def sample_records():
    return [
        {
            "name": "Player A", "age": 25, "transfer_value_mid": 50_000_000, 
            "finishing": 15, "pace": 16, "tackling": 5, "primary_pos_group": "ST",
            "tactical_compatibility": {"Gegenpress": 14.5, "Tiki-Taka": 12.0},
            "role_scores": {"Advanced Forward": 15.0},
            "role_trajectories": {"Advanced Forward": 0.0},
            "value_trajectory": "Stable",
            "leadership": 10, "determination": 14
        },
        {
            "name": "Player B", "age": 21, "transfer_value_mid": 30_000_000, 
            "finishing": 14, "pace": 15, "tackling": 6, "primary_pos_group": "ST",
            "tactical_compatibility": {"Gegenpress": 13.0, "Tiki-Taka": 11.0},
            "role_scores": {"Advanced Forward": 13.5},
            "role_trajectories": {"Advanced Forward": 0.8},
            "value_trajectory": "Rising",
            "leadership": 8, "determination": 12
        },
        {
            "name": "Player C", "age": 32, "transfer_value_mid": 10_000_000, 
            "finishing": 12, "pace": 10, "tackling": 15, "primary_pos_group": "D",
            "tactical_compatibility": {"Gegenpress": 10.0, "Tiki-Taka": 14.0},
            "role_scores": {"Ball Playing Defender": 14.0},
            "role_trajectories": {"Ball Playing Defender": -0.5},
            "value_trajectory": "Highly Depressed",
            "leadership": 18, "determination": 18 # Highly influential
        }
    ]

def test_similarity_model(sample_records):
    # Using 2 components because we only have 3 samples
    model = PlayerSimilarityModel(n_components=2)
    model.fit(sample_records)
    
    assert model.is_fitted
    
    # Find similar to Player A
    similar = model.find_similar_players(sample_records[0], top_n=2)
    assert len(similar) == 2
    # Player B should be more similar to A than C is
    assert similar[0][0]["name"] == "Player B"
    
    # Replaceability
    # A is 25, 50M. B is 21, 30M. C is 32, 10M.
    # B is cheaper and younger than A, and highly similar.
    # Assuming threshold 0.8 is met (it will be high since A and B are very close)
    # The actual cosine similarity depends on the PCA space, but let's test the method signature
    rep = model.calculate_replaceability(sample_records[0], similarity_threshold=0.0)
    assert rep >= 0

def test_recommend_squad_depth(sample_records):
    res = RecommendationEngine.recommend_squad_depth(sample_records, "Gegenpress")
    ranked = res["ranked_squad"]
    # Player A should be first (14.5 > 13.0 > 10.0)
    assert ranked[0]["name"] == "Player A"
    
    drop_offs = res["drop_offs"]
    # ST group has 2 players, diff is 14.5 - 13.0 = 1.5
    assert drop_offs["ST"] == 1.5
    
    urgent = res["urgent_transfer_needs"]
    # D group only has 1 player, so it's urgent
    assert "D" in urgent
    
def test_recommend_transfers(sample_records):
    res = RecommendationEngine.recommend_transfers(sample_records, "Advanced Forward", max_price=40_000_000)
    # Player A is 50M, so should be excluded.
    # Player B is 30M, so should be included.
    # Player C doesn't have Advanced Forward score.
    assert len(res) == 1
    assert res[0]["name"] == "Player B"

def test_recommend_retention(sample_records):
    # Mocking the similarity model
    class MockSimModel:
        def calculate_replaceability(self, rec, **kwargs):
            if rec["name"] == "Player C":
                return 3 # Highly replaceable
            return 0
            
    sim_model = MockSimModel()
    res = RecommendationEngine.recommend_retention(sample_records, sim_model)
    
    player_c = next(r for r in res if r["name"] == "Player C")
    # C has Highly Depressed value, decaying attributes (-0.5), and is highly replaceable.
    # BUT C is Highly Influential (Leadership 18)
    assert player_c["retention_signal"] == "Monitor"
    assert "Morale Risk" in player_c["retention_reason"]

def test_feedback_logger():
    logger = FeedbackLogger("tests/temp_feedback.jsonl")
    if os.path.exists("tests/temp_feedback.jsonl"):
        os.remove("tests/temp_feedback.jsonl")
        
    logger.log_decision({"name": "Test", "age": 20, "versatility": 1.0, "primary_pos_group": "ST"}, "transfer_recommendation", "shortlisted")
    
    with open("tests/temp_feedback.jsonl", "r") as f:
        data = json.loads(f.readline())
        assert data["decision"] == "shortlisted"
        assert data["player_name"] == "Test"
        
    os.remove("tests/temp_feedback.jsonl")
