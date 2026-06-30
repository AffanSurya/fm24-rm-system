import os
import json
from datetime import datetime
from typing import Dict, Any

class FeedbackLogger:
    def __init__(self, log_path: str = None):
        if not log_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            log_path = os.path.join(base_dir, "data", "models", "feedback.jsonl")
            
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        
    def log_decision(self, player_record: Dict[str, Any], context: str, decision: str):
        """
        Logs a managerial decision for future LightGBM/XGBoost training.
        context: e.g., "transfer_recommendation", "retention_analysis"
        decision: e.g., "shortlisted", "ignored", "keep", "sell"
        """
        # We strip out nested dicts that aren't base features for simplicity in training
        # but keep core features and derived scalars
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "decision": decision,
            "player_name": player_record.get("name"),
            "age": player_record.get("age"),
            "primary_pos_group": player_record.get("primary_pos_group"),
            "versatility": player_record.get("versatility"),
            "value_trajectory": player_record.get("value_trajectory")
        }
        
        # In a real scenario, we'd log the specific role_score that triggered this,
        # but this is a solid scaffolding for the cold-start phase.
        
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
