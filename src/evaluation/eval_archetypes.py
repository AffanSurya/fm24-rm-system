import json
import os
from typing import Dict, List, Tuple

def compare_roles(role_1: str, role_2: str, weights: Dict[str, Dict[str, float]]) -> List[Tuple[str, float]]:
    """
    Finds the biggest mathematical differences between two tactical roles.
    """
    if role_1 not in weights or role_2 not in weights:
        raise ValueError(f"One or both roles not found in weights config.")
        
    w1 = weights[role_1]
    w2 = weights[role_2]
    
    # Get all unique attributes mentioned in both
    all_attrs = set(w1.keys()).union(set(w2.keys()))
    
    differences = []
    for attr in all_attrs:
        val1 = w1.get(attr, 0.0)
        val2 = w2.get(attr, 0.0)
        diff = val1 - val2
        differences.append((attr, diff))
        
    # Sort by absolute difference
    differences.sort(key=lambda x: abs(x[1]), reverse=True)
    return differences

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(base_dir, "config", "role_weights.json")
    
    with open(config_path, "r", encoding="utf-8") as f:
        role_weights = json.load(f)
        
    print("=== Role Archetype Diagnostics ===")
    
    # Let's compare some roles if they exist
    roles = list(role_weights.keys())
    if len(roles) >= 2:
        r1 = roles[0]
        r2 = roles[1]
        
        print(f"\nComparing '{r1}' vs '{r2}':")
        diffs = compare_roles(r1, r2, role_weights)
        
        print(f"Top 5 defining attributes for {r1} (Positive = More important for {r1}):")
        for attr, diff in diffs[:5]:
            print(f"  - {attr}: {diff:+.2f}")
            
    else:
        print("Not enough roles configured to compare.")
