import json
import os
from typing import Dict, Any

class RoleScorer:
    def __init__(self, config_path: str = None):
        if not config_path:
            # Default to the project root's config
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(base_dir, "config", "role_weights.json")
            
        with open(config_path, "r", encoding="utf-8") as f:
            self.weights = json.load(f)
            
    def calculate_role_score(self, player_record: dict, role: str) -> float:
        """
        Calculates a weighted score for a given role based on player attributes.
        Returns a score typically between 0 and 20 (if attributes max at 20).
        """
        if role not in self.weights:
            return 0.0
            
        role_weights = self.weights[role]
        total_weight = 0.0
        weighted_sum = 0.0
        
        for attr, weight in role_weights.items():
            val = player_record.get(attr)
            # Treat missing attributes as poor rather than 0 to avoid punishing completely
            # but usually they should be normalized to some baseline. For now, 5.
            attr_val = val if val is not None else 5.0
            
            weighted_sum += (attr_val * weight)
            total_weight += weight
            
        if total_weight == 0:
            return 0.0
            
        return round(weighted_sum / total_weight, 2)
        
    def calculate_all_roles(self, player_record: dict) -> Dict[str, float]:
        """
        Calculates scores for all known roles.
        """
        return {role: self.calculate_role_score(player_record, role) 
                for role in self.weights if role != "_metadata"}
