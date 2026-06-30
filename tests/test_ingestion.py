import pytest
from src.ingestion.normalizer import parse_financial_value, parse_wage, parse_status, calculate_confidence, normalize_row
from src.core.schemas import KnowledgeLevel, PlayerRecord
from src.ingestion.resolver import resolve_entities

def test_parse_financial_value():
    assert parse_financial_value("€6.8M–€8M") == (6800000.0, 8000000.0, 7400000.0)
    assert parse_financial_value("€500K") == (500000.0, 500000.0, 500000.0)
    assert parse_financial_value("Not for sale") == (0.0, 0.0, 0.0)
    assert parse_financial_value("-") == (0.0, 0.0, 0.0)

def test_parse_wage():
    assert parse_wage("€5,750 p/m") == 5750.0 * 12
    assert parse_wage("£100K p/w") == 100000.0 * 52
    assert parse_wage("€1.5M p/a") == 1500000.0
    assert parse_wage("N/A") == 0.0

def test_parse_status():
    status = parse_status("Wnt, Inj")
    assert status["is_wanted"] is True
    assert status["is_injured"] is True
    assert status["is_listed"] is False
    
def test_calculate_confidence():
    kl, conf = calculate_confidence("Extensive", "150")
    assert kl == KnowledgeLevel.EXTENSIVE
    assert conf == 0.9
    
    # Masked ability reduces confidence
    kl, conf = calculate_confidence("Extensive", "130-160")
    assert kl == KnowledgeLevel.EXTENSIVE
    assert conf == 0.72 # 0.9 * 0.8
    
    kl, conf = calculate_confidence("-", "-")
    assert kl == KnowledgeLevel.NONE
    assert conf == 0.08 # 0.1 * 0.8
    
def test_normalize_row():
    raw_row = {
        "Name": "Bukayo Saka",
        "Nat": "ENG",
        "Age": "22",
        "Club": "Arsenal",
        "Position Selected": "AM (R)",
        "Inf": "Wnt",
        "Value": "€100M",
        "Wage": "€300K p/w",
        "Knowledge": "Full",
        "Ability": "170",
        "Tck": "10", # Tackling
        "Vis": "16", # Vision
    }
    norm = normalize_row(raw_row)
    assert norm["name"] == "Bukayo Saka"
    assert norm["age"] == 22
    assert norm["is_wanted"] is True
    assert norm["transfer_value_mid"] == 100_000_000.0
    assert norm["wage_annual"] == 300_000.0 * 52
    assert norm["tackling"] == 10
    assert norm["vision"] == 16
    assert norm["knowledge_level"] == KnowledgeLevel.FULL
    
def test_entity_resolution():
    record1 = PlayerRecord(
        name="Joao Maria", nationality="POR", age=20, club="Benfica",
        knowledge_level=KnowledgeLevel.MINIMAL, confidence_tier=0.3,
        vision=10
    )
    record2 = PlayerRecord(
        name="Joao Maria", nationality="POR", age=21, club="Benfica", # Age is +1, within tolerance
        knowledge_level=KnowledgeLevel.FULL, confidence_tier=1.0,
        vision=15
    )
    record3 = PlayerRecord(
        name="Joao Maria", nationality="POR", age=25, club="Benfica", # Age is +5, out of tolerance, different person
        knowledge_level=KnowledgeLevel.FULL, confidence_tier=1.0,
        vision=12
    )
    
    resolved = resolve_entities([record1, record2, record3])
    
    # Should resolve into 2 records: one for age 20/21 cluster, one for age 25
    assert len(resolved) == 2
    
    # The first cluster (20/21) should have taken record2's values because of higher confidence
    young_joao = next(r for r in resolved if r.age in (20, 21))
    assert young_joao.vision == 15
    assert young_joao.age == 21
    
    older_joao = next(r for r in resolved if r.age == 25)
    assert older_joao.vision == 12
