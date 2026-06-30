import json
import os
import pandas as pd
from typing import List, Dict, Any

from src.features.roles import RoleScorer
from src.features.positions import parse_position_string, calculate_versatility
from src.features.tactics import TacticalProfiler
from src.features.financials import calculate_value_efficiency
from src.features.age_curves import classify_role_group, calculate_current_fit_trajectory, calculate_potential_realization, calculate_value_trajectory

def determine_primary_position_group(pos_dict: Dict[str, float]) -> str:
    """
    Returns a broad positional group based on the highest weight position.
    e.g., 'ST', 'M', 'D', 'GK'
    """
    if not pos_dict or max(pos_dict.values(), default=0.0) == 0.0:
        return "Unknown"
        
    best_pos = max(pos_dict.items(), key=lambda x: x[1])[0]
    
    if "GK" in best_pos: return "GK"
    if "ST" in best_pos: return "ST"
    if "AM" in best_pos: return "AM"
    if "M " in best_pos: return "M"
    if "DM" in best_pos: return "DM"
    if "WB" in best_pos: return "WB"
    if "D " in best_pos: return "D"
    return "Unknown"

def process_features(input_filepath: str, output_filepath: str):
    """
    End-to-end feature engineering pipeline.
    """
    records = []
    with open(input_filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
                
    scorer = RoleScorer()
    
    # Enrich records with independent features
    for r in records:
        # Positions
        pos_str = r.get("position_eligibility", "")
        pos_dict = parse_position_string(pos_str)
        r["multi_hot_positions"] = pos_dict
        r["versatility"] = calculate_versatility(pos_dict)
        r["primary_pos_group"] = determine_primary_position_group(pos_dict)
        
        # Tactics
        r["tactical_compatibility"] = TacticalProfiler.calculate_all_styles(r)
        
        # Financials and Age Curves (Base)
        age = r.get("age", 0)
        pot = r.get("potential")
        tv_mid = r.get("transfer_value_mid", 0)
        tv_min = r.get("transfer_value_min", 0)
        tv_max = r.get("transfer_value_max", 0)
        band_width = tv_max - tv_min
        
        r["value_trajectory"] = calculate_value_trajectory(age, band_width)
        
        # Roles
        role_scores = scorer.calculate_all_roles(r)
        r["role_scores"] = role_scores
        
        # Age trajectories per role group and Value Efficiency per role
        r["role_trajectories"] = {}
        r["value_efficiencies"] = {}
        r["is_developing_fit"] = {}
        
        for role, score in role_scores.items():
            r_group = classify_role_group(role)
            r["role_trajectories"][role] = calculate_current_fit_trajectory(age, r_group)
            r["value_efficiencies"][role] = calculate_value_efficiency(score, tv_mid)
            r["is_developing_fit"][role] = calculate_potential_realization(age, pot, score)
            
    # Percentile Normalization (comparing apples to apples)
    # We load into a pandas DataFrame to easily compute grouped rank percentiles
    df = pd.DataFrame(records)
    
    # We want to normalize base attributes (like tackling, finishing) WITHIN their primary_pos_group
    attributes_to_normalize = ["tackling", "finishing", "vision", "pace", "stamina", "passing"]
    
    for attr in attributes_to_normalize:
        # Some rows might have None for attributes, fill with 0 temporarily for ranking
        col_name = f"{attr}_percentile"
        
        def calculate_pct(series):
            return series.rank(pct=True).fillna(0.0).round(3)
            
        # Group by primary position group and calculate percentile
        if attr in df.columns:
            # We use transform to keep the same shape
            df[col_name] = df.groupby("primary_pos_group")[attr].transform(calculate_pct)
            
    # Convert back to dict and save
    final_records = df.to_dict(orient="records")
    
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    with open(output_filepath, "w", encoding="utf-8") as f:
        for r in final_records:
            f.write(json.dumps(r) + "\n")
            
    return {
        "status": "success",
        "processed_records": len(final_records)
    }
