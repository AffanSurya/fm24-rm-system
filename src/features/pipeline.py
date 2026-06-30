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
    df = pd.read_json(input_filepath, lines=True)
    if df.empty:
        return {"status": "success", "processed_records": 0}
        
    scorer = RoleScorer()
    
    def safe_dict(row):
        d = row.to_dict()
        res = {}
        for k, v in d.items():
            if isinstance(v, float) and pd.isna(v):
                res[k] = None
            else:
                res[k] = v
        return res
    
    # 1. Positions
    df['multi_hot_positions'] = df['position_eligibility'].fillna("").apply(parse_position_string)
    df['versatility'] = df['multi_hot_positions'].apply(calculate_versatility)
    df['primary_pos_group'] = df['multi_hot_positions'].apply(determine_primary_position_group)
    
    # 2. Tactics
    df['tactical_compatibility'] = df.apply(lambda row: TacticalProfiler.calculate_all_styles(safe_dict(row)), axis=1)
    
    # 3. Financials & Curves
    tv_min = df.get('transfer_value_min', pd.Series(0, index=df.index)).fillna(0)
    tv_max = df.get('transfer_value_max', pd.Series(0, index=df.index)).fillna(0)
    band_width = tv_max - tv_min
    
    df['value_trajectory'] = df.apply(lambda row: calculate_value_trajectory(
        row.get('age', 0) if pd.notna(row.get('age')) else 0, 
        band_width[row.name]
    ), axis=1)
    
    # 4. Roles
    df['role_scores'] = df.apply(lambda row: scorer.calculate_all_roles(safe_dict(row)), axis=1)
    
    # 5. Role trajectories and efficiencies
    def calculate_role_derivatives(row):
        age = row.get('age', 0) if pd.notna(row.get('age')) else 0
        pot = row.get('potential') if pd.notna(row.get('potential')) else None
        tv_mid = row.get('transfer_value_mid', 0) if pd.notna(row.get('transfer_value_mid')) else 0
        
        trajectories = {}
        efficiencies = {}
        developing_fit = {}
        
        for role, score in row['role_scores'].items():
            r_group = classify_role_group(role)
            trajectories[role] = calculate_current_fit_trajectory(age, r_group)
            efficiencies[role] = calculate_value_efficiency(score, tv_mid)
            developing_fit[role] = calculate_potential_realization(age, pot, score)
            
        return pd.Series([trajectories, efficiencies, developing_fit])

    df[['role_trajectories', 'value_efficiencies', 'is_developing_fit']] = df.apply(calculate_role_derivatives, axis=1)
    
    # Percentile Normalization (comparing apples to apples)
    attributes_to_normalize = ["tackling", "finishing", "vision", "pace", "stamina", "passing"]
    
    for attr in attributes_to_normalize:
        col_name = f"{attr}_percentile"
        
        def calculate_pct(series):
            return pd.to_numeric(series, errors='coerce').rank(pct=True).fillna(0.0).round(3)
            
        if attr in df.columns:
            df[col_name] = df.groupby("primary_pos_group")[attr].transform(calculate_pct)
            
    # Convert back to dict and save atomically
    final_records = df.where(pd.notnull(df), None).to_dict(orient="records")
    
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    
    temp_file_path = output_filepath + ".tmp"
    with open(temp_file_path, "w", encoding="utf-8") as f:
        for r in final_records:
            f.write(json.dumps(r) + "\n")
    os.replace(temp_file_path, output_filepath)
            
    return {
        "status": "success",
        "processed_records": len(final_records)
    }
