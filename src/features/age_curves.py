from typing import Literal

def classify_role_group(role_name: str) -> str:
    """
    Classifies a role into one of the 5 age-curve groups.
    """
    role = role_name.lower()
    if "keeper" in role:
        return "goalkeeper"
    elif any(x in role for x in ["winger", "full back", "wing back", "advanced forward"]):
        return "physical_reliant"
    elif any(x in role for x in ["box to box", "carrilero", "pressing forward", "ball winning"]):
        return "box_to_box"
    elif any(x in role for x in ["playmaker", "trequartista", "enganche", "false nine"]):
        return "technical_reliant"
    elif any(x in role for x in ["defender", "center back", "anchor", "half back"]):
        return "defensive_reliant"
    return "box_to_box" # Default fallback

def calculate_current_fit_trajectory(age: int, role_group: str) -> float:
    """
    Returns a trajectory scalar from -1.0 (declining fast) to 1.0 (improving fast).
    0.0 represents peak / holding steady.
    """
    if role_group == "physical_reliant":
        if age < 23: return 0.8
        elif 23 <= age <= 27: return 0.0
        elif 28 <= age <= 29: return -0.4
        else: return -0.9 # Sharp drop-off
        
    elif role_group == "box_to_box":
        if age < 25: return 0.7
        elif 25 <= age <= 29: return 0.0
        elif 30 <= age <= 32: return -0.3 # Gradual decline
        else: return -0.6
        
    elif role_group == "technical_reliant":
        if age < 27: return 0.6
        elif 27 <= age <= 31: return 0.0
        elif 32 <= age <= 34: return -0.1 # Very slow decline
        else: return -0.3
        
    elif role_group == "defensive_reliant":
        if age < 28: return 0.5
        elif 28 <= age <= 32: return 0.0
        elif 33 <= age <= 34: return -0.2
        else: return -0.5
        
    elif role_group == "goalkeeper":
        if age < 29: return 0.4
        elif 29 <= age <= 33: return 0.0
        elif 34 <= age <= 36: return -0.1 # Extremely slow
        else: return -0.3
        
    return 0.0

def calculate_potential_realization(age: int, potential: float, current_fit: float) -> bool:
    """
    Flags if a player is a "developing fit" (young, high potential, current fit isn't elite yet).
    """
    if age > 23:
        return False
        
    # If we don't know potential, we can't reliably flag this
    if not potential:
        return False
        
    # E.g. potential > 150 and current fit is decent but not maxed
    if potential >= 140 and current_fit < 14.0:
        return True
        
    return False

def calculate_value_trajectory(age: int, transfer_value_band_width: float) -> str:
    """
    Categorical trajectory: "Rising", "Stable", "Depressed".
    Wide bands at older ages generally indicate value is widening downward.
    """
    if age <= 23:
        return "Rising"
    elif 24 <= age <= 28:
        return "Stable"
    elif age >= 29:
        # If the band width is large relative to age, it's highly depressed
        if transfer_value_band_width > 10_000_000: 
            return "Highly Depressed"
        return "Depressed"
    return "Stable"
