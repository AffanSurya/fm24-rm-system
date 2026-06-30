from typing import Dict, Any

TACTICAL_STYLES = {
    "Gegenpress": {
        "stamina": 5,
        "work_rate": 5,
        "aggression": 4,
        "pace": 4,
        "teamwork": 3
    },
    "Tiki-Taka": {
        "passing": 5,
        "vision": 5,
        "first_touch": 5,
        "composure": 4,
        "anticipation": 4,
        "decisions": 4
    },
    "Fluid Counter-Attack": {
        "pace": 5,
        "acceleration": 5,
        "passing": 4,
        "off_the_ball": 4,
        "work_rate": 3,
        "stamina": 3
    },
    "Catenaccio": {
        "positioning": 5,
        "concentration": 5,
        "marking": 4,
        "tackling": 4,
        "jumping_reach": 3,
        "strength": 3
    }
}

class TacticalProfiler:
    @staticmethod
    def calculate_compatibility(player_record: dict, style: str) -> float:
        """
        Calculates how well a player's baseline attributes fit a specific tactical style.
        Returns a score between 0 and 20.
        """
        if style not in TACTICAL_STYLES:
            return 0.0
            
        weights = TACTICAL_STYLES[style]
        total_weight = 0.0
        weighted_sum = 0.0
        
        for attr, weight in weights.items():
            val = player_record.get(attr)
            attr_val = val if val is not None else 5.0
            weighted_sum += (attr_val * weight)
            total_weight += weight
            
        if total_weight == 0:
            return 0.0
            
        return round(weighted_sum / total_weight, 2)
        
    @staticmethod
    def calculate_all_styles(player_record: dict) -> Dict[str, float]:
        """
        Calculates scores for all known tactical styles.
        """
        return {style: TacticalProfiler.calculate_compatibility(player_record, style) 
                for style in TACTICAL_STYLES}
