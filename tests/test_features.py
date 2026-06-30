import pytest
from src.features.roles import RoleScorer
from src.features.positions import parse_position_string, calculate_versatility
from src.features.tactics import TacticalProfiler
from src.features.financials import calculate_value_efficiency
from src.features.age_curves import classify_role_group, calculate_current_fit_trajectory, calculate_value_trajectory

def test_parse_position_string():
    pos_str = "M (RC), AM (R)"
    pos_dict = parse_position_string(pos_str)
    
    # M(C) and M(R) should be Natural (1.0)
    assert pos_dict["M (C)"] == 1.0
    assert pos_dict["M (R)"] == 1.0
    
    # AM(R) is secondary block so Accomplished (0.7)
    assert pos_dict["AM (R)"] == 0.7
    
    # Others 0.0
    assert pos_dict["ST (C)"] == 0.0
    assert pos_dict["D (L)"] == 0.0
    
    # Versatility score
    v_score = calculate_versatility(pos_dict)
    assert v_score == 2.7 # 1.0 + 1.0 + 0.7

def test_tactical_profiler():
    player = {
        "stamina": 16,
        "work_rate": 16,
        "aggression": 14,
        "pace": 15,
        "teamwork": 14
    }
    score = TacticalProfiler.calculate_compatibility(player, "Gegenpress")
    # All high stats for Gegenpress, should be close to 15+
    assert score > 14.0
    
def test_value_efficiency():
    # log10( (15 / 15,000,000) * 1,000,000 + 1) -> log10(1 + 1) -> 0.301
    eff = calculate_value_efficiency(15.0, 15_000_000.0)
    assert eff == 0.301
    
    eff_cheap = calculate_value_efficiency(15.0, 1_500_000.0)
    # (15 / 1.5M) * 1M = 10. -> log10(11) -> 1.041
    assert eff_cheap > eff # Cheaper for same output = higher efficiency

def test_age_curves():
    # Winger (Physical Reliant)
    group = classify_role_group("Advanced Forward")
    assert group == "physical_reliant"
    
    assert calculate_current_fit_trajectory(25, group) == 0.0 # Peak
    assert calculate_current_fit_trajectory(30, group) == -0.9 # Sharp decline
    
    # Playmaker (Technical)
    group_tech = classify_role_group("Deep Lying Playmaker")
    assert group_tech == "technical_reliant"
    
    assert calculate_current_fit_trajectory(25, group_tech) == 0.6 # Still rising
    assert calculate_current_fit_trajectory(30, group_tech) == 0.0 # Peak
    assert calculate_current_fit_trajectory(33, group_tech) == -0.1 # Very slow decline

def test_value_trajectory():
    # Young player = Rising
    assert calculate_value_trajectory(21, 5_000_000) == "Rising"
    
    # Peak player = Stable
    assert calculate_value_trajectory(26, 5_000_000) == "Stable"
    
    # Old player with wide band = Highly Depressed
    assert calculate_value_trajectory(32, 15_000_000) == "Highly Depressed"
