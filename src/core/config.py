from typing import Dict, List

# Multipliers for financial fields
FINANCIAL_MULTIPLIERS = {
    "K": 1_000,
    "M": 1_000_000,
}

# Wage Suffix Multipliers (to annualize)
WAGE_SUFFIX_MULTIPLIERS = {
    "p/w": 52,
    "p/m": 12,
    "p/a": 1,
}

# Known Information Status Flags (Inf column)
STATUS_FLAGS = {
    "Inj": "is_injured",
    "Wnt": "is_wanted",
    "Lst": "is_listed",
    "Unh": "is_unhappy",
    "PR": "is_pending_release",
    "Slt": "is_shortlisted",
    "Fgn": "is_foreign",
    "HG": "is_homegrown",
}

# Canonical Mapping for FM Attributes 
# Keys are common FM column names (can be slightly different depending on language/patch)
ATTRIBUTE_MAP: Dict[str, str] = {
    # Technical
    "Cor": "corners",
    "Cro": "crossing",
    "Dri": "dribbling",
    "Fin": "finishing",
    "Fir": "first_touch",
    "Fre": "free_kicks",
    "Hea": "heading",
    "Lon": "long_shots",
    "L Th": "long_throws",
    "Mar": "marking",
    "Pas": "passing",
    "Pen": "penalty_taking",
    "Tck": "tackling",
    "Tec": "technique",
    
    # Mental
    "Agg": "aggression",
    "Ant": "anticipation",
    "Bra": "bravery",
    "Cmp": "composure",
    "Cnt": "concentration",
    "Dec": "decisions",
    "Det": "determination",
    "Fla": "flair",
    "Ldr": "leadership",
    "Otb": "off_the_ball",
    "Pos": "positioning",
    "Tea": "teamwork",
    "Vis": "vision",
    "Wor": "work_rate",
    
    # Physical
    "Acc": "acceleration",
    "Agi": "agility",
    "Bal": "balance",
    "Jum": "jumping_reach",
    "Nat": "natural_fitness",
    "Pac": "pace",
    "Sta": "stamina",
    "Str": "strength",
    
    # Goalkeeping
    "Aer": "aerial_reach",
    "Cmd": "command_of_area",
    "Com": "communication",
    "Ecc": "eccentricity",
    "Han": "handling",
    "Kic": "kicking",
    "1v1": "one_on_ones",
    "Ref": "reflexes",
    "TRO": "rushing_out",
    "Pun": "punching",
    "Thr": "throwing"
}

# Define categories for downstream normalization
ATTRIBUTE_CATEGORIES = {
    "technical": ["corners", "crossing", "dribbling", "finishing", "first_touch", "free_kicks", "heading", "long_shots", "long_throws", "marking", "passing", "penalty_taking", "tackling", "technique"],
    "mental": ["aggression", "anticipation", "bravery", "composure", "concentration", "decisions", "determination", "flair", "leadership", "off_the_ball", "positioning", "teamwork", "vision", "work_rate"],
    "physical": ["acceleration", "agility", "balance", "jumping_reach", "natural_fitness", "pace", "stamina", "strength"],
    "goalkeeping": ["aerial_reach", "command_of_area", "communication", "eccentricity", "handling", "kicking", "one_on_ones", "reflexes", "rushing_out", "punching", "throwing"]
}
