import json
import os

def check_consistency(features_jsonl_path: str):
    """
    Calculates Hit Rate@3: Does FM's 'Best Role' appear in our Top 3 recommended roles?
    """
    total_records = 0
    hits_at_3 = 0
    exact_matches = 0
    
    if not os.path.exists(features_jsonl_path):
        print(f"Error: Could not find {features_jsonl_path}")
        return
        
    with open(features_jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
                
            record = json.loads(line)
            fm_best_role = record.get("best_role")
            
            # We can only test this if the export included the Best Role column
            if not fm_best_role:
                continue
                
            role_scores = record.get("role_scores", {})
            if not role_scores:
                continue
                
            # Sort our custom roles by score descending
            top_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)
            top_3_roles = [r[0] for r in top_roles[:3]]
            top_1_role = top_roles[0][0]
            
            total_records += 1
            
            if fm_best_role in top_3_roles:
                hits_at_3 += 1
                
            if fm_best_role == top_1_role:
                exact_matches += 1
                
    if total_records == 0:
        print("No records with 'Best Role' column found in export data to evaluate.")
        return
        
    hr_3 = (hits_at_3 / total_records) * 100
    exact = (exact_matches / total_records) * 100
    
    print(f"--- Consistency Check vs FM Native Engine ---")
    print(f"Total Evaluated Records: {total_records}")
    print(f"Hit Rate@3 (FM role in our Top 3): {hr_3:.2f}%")
    print(f"Exact Match Rate (FM role is our #1): {exact:.2f}%")
    print(f"Note: 100% is not the goal. High HR@3 means we are grounded in reality.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    features_path = os.path.join(base_dir, "data", "processed", "features_test_data.jsonl")
    check_consistency(features_path)
