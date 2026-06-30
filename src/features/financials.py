import math

def calculate_value_efficiency(role_fit_score: float, transfer_value_mid: float) -> float:
    """
    Calculates log(role_fit_score / transfer_value_mid).
    If transfer value is 0 (e.g. youth player or not for sale), handles gracefully.
    Since FM transfer values scale exponentially, a logarithmic scale normalizes 
    value-for-money without severely punishing elite players.
    """
    if role_fit_score <= 0:
        return 0.0
        
    # Prevent division by zero. Assume a baseline nominal fee if 0.
    if not transfer_value_mid or transfer_value_mid <= 0:
        safe_value = 1000.0 # Nominal 1k
    else:
        safe_value = transfer_value_mid
        
    ratio = role_fit_score / safe_value
    
    # We multiply the ratio by a constant (e.g., 1,000,000) so the log isn't extremely negative
    # e.g. score 15 / value 15,000,000 = 0.000001 -> log10 is -6
    # multiplied by 1,000,000 it's 1 -> log10 is 0
    adjusted_ratio = ratio * 1_000_000
    
    # +1 to ensure positive log results
    return round(math.log10(adjusted_ratio + 1), 3)
