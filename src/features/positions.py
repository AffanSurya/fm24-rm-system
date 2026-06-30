from typing import Dict, Tuple

ALL_POSITIONS = [
    "GK", 
    "D (R)", "D (L)", "D (C)", 
    "WB (R)", "WB (L)", 
    "DM", 
    "M (R)", "M (L)", "M (C)", 
    "AM (R)", "AM (L)", "AM (C)", 
    "ST (C)"
]

def parse_position_string(pos_str: str) -> Dict[str, float]:
    """
    Parses a string like "M (RC), AM (R)" into a dictionary of positions.
    Assigns 1.0 for primary positions (Natural) and 0.7 for secondary (Accomplished).
    This is an approximation since raw string parsing doesn't perfectly differentiate 
    without the color-coded GUI, but generally the first listed positions or those 
    without brackets are considered Natural.
    """
    pos_dict = {p: 0.0 for p in ALL_POSITIONS}
    if not pos_str:
        return pos_dict
        
    # Split by comma
    parts = [p.strip() for p in pos_str.split(",")]
    
    # We will assume the very first position block listed is Natural (1.0), others 0.7
    # e.g., "M (RC), AM (R)" -> M(C) and M(R) are 1.0, AM(R) is 0.7
    for i, part in enumerate(parts):
        weight = 1.0 if i == 0 else 0.7
        
        # e.g., "M (RC)"
        if "(" in part and ")" in part:
            base, sides = part.split("(")
            base = base.strip()
            sides = sides.replace(")", "").strip()
            
            for side in sides:
                # Map side to full position name
                mapped_pos = f"{base} ({side})"
                if mapped_pos in pos_dict:
                    # Keep the max weight in case it was already set higher
                    pos_dict[mapped_pos] = max(pos_dict[mapped_pos], weight)
        else:
            # Single exact position like "GK" or "ST" -> map ST to ST (C)
            clean_part = part.strip()
            if clean_part == "ST":
                clean_part = "ST (C)"
                
            if clean_part in pos_dict:
                pos_dict[clean_part] = max(pos_dict[clean_part], weight)
                
    return pos_dict

def calculate_versatility(pos_dict: Dict[str, float]) -> float:
    """
    Calculates a versatility score. 
    Natural (1.0) gives full points, Accomplished (0.7) gives partial points.
    """
    return sum(pos_dict.values())
