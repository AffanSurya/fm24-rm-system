import re
import os
from typing import Dict, Any, Tuple
from src.core.config import ATTRIBUTE_MAP, STATUS_FLAGS, FINANCIAL_MULTIPLIERS, WAGE_SUFFIX_MULTIPLIERS
from src.core.schemas import KnowledgeLevel

def check_schema_drift(raw_row: Dict[str, Any]):
    """
    Validates schema against FM patches. 
    Hard fails on critical missing data. Logs warnings on unknown columns.
    """
    raw_keys = [str(k).strip() for k in raw_row.keys()]
    
    # Check Critical
    has_name = "Name" in raw_keys or "name" in raw_keys
    has_age = "Age" in raw_keys or "age" in raw_keys
    
    missing_critical = []
    if not has_name: missing_critical.append("Name")
    if not has_age: missing_critical.append("Age")
        
    if missing_critical:
        raise ValueError(f"CRITICAL DRIFT: Missing core columns {missing_critical}. Cannot proceed.")
        
    # Check Unknown (Warning only)
    unknown_cols = [k for k in raw_keys if k not in ATTRIBUTE_MAP and k.lower() not in ATTRIBUTE_MAP.values()]
    
    # We ignore standard columns like Name, Age, Club, Nat, Inf, Position
    standard = ["Name", "name", "Age", "age", "Club", "club", "Nat", "nat", "Nationality", "nationality", 
                "Inf", "inf", "Position", "position", "Position Selected", "position_selected",
                "Transfer Value", "transfer_value", "Value", "value", "Wage", "wage", "Salary", "salary",
                "Scouting Knowledge", "scouting_knowledge", "Knowledge", "knowledge", "Ability", "ability", "ca", "CA"]
                
    actual_unknown = [c for c in unknown_cols if c not in standard and c.lower() not in [s.lower() for s in standard]]
    
    if actual_unknown:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        log_path = os.path.join(base_dir, "data", "processed", "drift_warnings.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"WARNING: Unknown columns detected: {actual_unknown}\n")

def parse_financial_value(val_str: str) -> Tuple[float, float, float]:
    """
    Parses a financial value like '€6.8M', '€6.8M–€8M', or 'Not for sale'.
    Returns (min_val, max_val, mid_val).
    """
    if not val_str or val_str.lower() in ["not for sale", "n/a", "-"]:
        return 0.0, 0.0, 0.0
        
    # Remove currency symbols and commas
    cleaned = re.sub(r'[^\d.KM\-]', '', val_str.replace("–", "-").upper())
    
    parts = cleaned.split("-")
    
    def parse_single(s: str) -> float:
        if not s:
            return 0.0
        multiplier = 1.0
        if s.endswith("K"):
            multiplier = FINANCIAL_MULTIPLIERS["K"]
            s = s[:-1]
        elif s.endswith("M"):
            multiplier = FINANCIAL_MULTIPLIERS["M"]
            s = s[:-1]
        try:
            return float(s) * multiplier
        except ValueError:
            return 0.0
            
    if len(parts) == 1:
        val = parse_single(parts[0])
        return val, val, val
    elif len(parts) == 2:
        min_val = parse_single(parts[0])
        max_val = parse_single(parts[1])
        return min_val, max_val, (min_val + max_val) / 2.0
    return 0.0, 0.0, 0.0

def parse_wage(wage_str: str) -> float:
    """
    Parses wage string like '€5,750 p/m', '€100K p/w' and annualizes it.
    """
    if not wage_str or wage_str.lower() in ["n/a", "-"]:
        return 0.0
        
    wage_str = wage_str.lower()
    suffix_mult = 1
    
    for suffix, mult in WAGE_SUFFIX_MULTIPLIERS.items():
        if suffix in wage_str:
            suffix_mult = mult
            wage_str = wage_str.replace(suffix, "").strip()
            break
            
    # Clean up to parse the number
    cleaned = re.sub(r'[^\d.km]', '', wage_str)
    
    multiplier = 1.0
    if cleaned.endswith("k"):
        multiplier = FINANCIAL_MULTIPLIERS["K"]
        cleaned = cleaned[:-1]
    elif cleaned.endswith("m"):
        multiplier = FINANCIAL_MULTIPLIERS["M"]
        cleaned = cleaned[:-1]
        
    try:
        base_val = float(cleaned) * multiplier
        return base_val * suffix_mult
    except ValueError:
        return 0.0

def parse_status(inf_str: str) -> Dict[str, bool]:
    """
    Parses the Inf column like 'Wnt, PR, Lst' into boolean flags.
    """
    flags = {v: False for v in STATUS_FLAGS.values()}
    if not inf_str:
        return flags
        
    parts = [p.strip() for p in inf_str.split(",")]
    for p in parts:
        if p in STATUS_FLAGS:
            flags[STATUS_FLAGS[p]] = True
    return flags

def calculate_confidence(knowledge_str: str, ability_str: str) -> Tuple[KnowledgeLevel, float]:
    """
    Returns the knowledge level enum and a confidence score 0.0-1.0
    """
    if not knowledge_str or knowledge_str == "-":
        knowledge_level = KnowledgeLevel.NONE
    else:
        try:
            knowledge_level = KnowledgeLevel(knowledge_str)
        except ValueError:
            knowledge_level = KnowledgeLevel.NONE
            
    scores = {
        KnowledgeLevel.NONE: 0.1,
        KnowledgeLevel.MINIMAL: 0.3,
        KnowledgeLevel.AVERAGE: 0.5,
        KnowledgeLevel.GOOD: 0.7,
        KnowledgeLevel.EXTENSIVE: 0.9,
        KnowledgeLevel.FULL: 1.0,
    }
    
    base_score = scores.get(knowledge_level, 0.1)
    
    # If ability is masked (e.g., empty or contains '-'), reduce confidence
    if not ability_str or "-" in str(ability_str):
        base_score *= 0.8
        
    return knowledge_level, round(base_score, 2)

def normalize_row(raw_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts a raw dictionary to a dictionary matching PlayerRecord schema.
    """
    check_schema_drift(raw_row)
    
    normalized = {}
    
    # Map raw column names to canonical names if possible
    # We create a lookup for keys ignoring case/whitespace
    raw_keys_mapped = {}
    for k in raw_row.keys():
        clean_k = str(k).strip()
        if clean_k in ATTRIBUTE_MAP:
            raw_keys_mapped[ATTRIBUTE_MAP[clean_k]] = raw_row[k]
        else:
            # Fallback: keep original but lowercased, spaces to underscores
            norm_k = clean_k.lower().replace(" ", "_")
            raw_keys_mapped[norm_k] = raw_row[k]
            
    # Name, Nationality, Age, Club
    normalized["name"] = raw_keys_mapped.get("name")
    normalized["nationality"] = raw_keys_mapped.get("nat") or raw_keys_mapped.get("nationality")
    
    age_val = raw_keys_mapped.get("age")
    try:
        normalized["age"] = int(age_val) if age_val else 0
    except ValueError:
        normalized["age"] = 0
        
    normalized["club"] = raw_keys_mapped.get("club")
    
    # Position Eligibility
    normalized["position_eligibility"] = raw_keys_mapped.get("position") or raw_keys_mapped.get("position_selected") or ""
    
    # Status flags
    status_flags = parse_status(raw_keys_mapped.get("inf"))
    normalized.update(status_flags)
    
    # Financials
    transfer_value_raw = raw_keys_mapped.get("transfer_value") or raw_keys_mapped.get("value")
    min_v, max_v, mid_v = parse_financial_value(transfer_value_raw)
    normalized["transfer_value_min"] = min_v
    normalized["transfer_value_max"] = max_v
    normalized["transfer_value_mid"] = mid_v
    
    wage_raw = raw_keys_mapped.get("wage") or raw_keys_mapped.get("salary")
    normalized["wage_annual"] = parse_wage(wage_raw)
    
    # Confidence and knowledge
    knowledge = raw_keys_mapped.get("knowledge") or raw_keys_mapped.get("scouting_knowledge")
    ability = raw_keys_mapped.get("ability") or raw_keys_mapped.get("ca")
    kl, conf = calculate_confidence(knowledge, ability)
    normalized["knowledge_level"] = kl
    normalized["confidence_tier"] = conf
    
    # Attributes
    for attr in ATTRIBUTE_MAP.values():
        val = raw_keys_mapped.get(attr)
        if val:
            try:
                # Handle cases like "15-18" due to masking
                if "-" in str(val):
                    parts = str(val).split("-")
                    # Take lower bound for conservatism, or None
                    normalized[attr] = int(parts[0])
                else:
                    normalized[attr] = int(val)
            except ValueError:
                normalized[attr] = None
        else:
            normalized[attr] = None
            
    return normalized
