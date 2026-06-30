from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum

class KnowledgeLevel(str, Enum):
    NONE = "None"
    MINIMAL = "Minimal"
    AVERAGE = "Average"
    GOOD = "Good"
    EXTENSIVE = "Extensive"
    FULL = "Full"

class PlayerRecord(BaseModel):
    # Core Identifiers
    name: str
    nationality: Optional[str] = None
    age: int
    club: Optional[str] = None
    
    # Derived Metadata
    knowledge_level: KnowledgeLevel = KnowledgeLevel.NONE
    confidence_tier: float = Field(0.0, ge=0.0, le=1.0)
    
    # Categorical & Tactical
    position_eligibility: str = ""
    best_pos: Optional[str] = None
    best_role: Optional[str] = None
    best_duty: Optional[str] = None
    
    # Financial (Normalized to floats)
    transfer_value_min: Optional[float] = None
    transfer_value_max: Optional[float] = None
    transfer_value_mid: Optional[float] = None
    wage_annual: Optional[float] = None
    
    # Status Flags
    is_injured: bool = False
    is_wanted: bool = False
    is_listed: bool = False
    is_unhappy: bool = False
    is_pending_release: bool = False
    is_shortlisted: bool = False
    is_foreign: bool = False
    is_homegrown: bool = False
    
    # Hidden / Masked
    ability: Optional[float] = None
    potential: Optional[float] = None
    
    # Attributes (Technical)
    corners: Optional[int] = Field(None, ge=1, le=20)
    crossing: Optional[int] = Field(None, ge=1, le=20)
    dribbling: Optional[int] = Field(None, ge=1, le=20)
    finishing: Optional[int] = Field(None, ge=1, le=20)
    first_touch: Optional[int] = Field(None, ge=1, le=20)
    free_kicks: Optional[int] = Field(None, ge=1, le=20)
    heading: Optional[int] = Field(None, ge=1, le=20)
    long_shots: Optional[int] = Field(None, ge=1, le=20)
    long_throws: Optional[int] = Field(None, ge=1, le=20)
    marking: Optional[int] = Field(None, ge=1, le=20)
    passing: Optional[int] = Field(None, ge=1, le=20)
    penalty_taking: Optional[int] = Field(None, ge=1, le=20)
    tackling: Optional[int] = Field(None, ge=1, le=20)
    technique: Optional[int] = Field(None, ge=1, le=20)
    
    # Attributes (Mental)
    aggression: Optional[int] = Field(None, ge=1, le=20)
    anticipation: Optional[int] = Field(None, ge=1, le=20)
    bravery: Optional[int] = Field(None, ge=1, le=20)
    composure: Optional[int] = Field(None, ge=1, le=20)
    concentration: Optional[int] = Field(None, ge=1, le=20)
    decisions: Optional[int] = Field(None, ge=1, le=20)
    determination: Optional[int] = Field(None, ge=1, le=20)
    flair: Optional[int] = Field(None, ge=1, le=20)
    leadership: Optional[int] = Field(None, ge=1, le=20)
    off_the_ball: Optional[int] = Field(None, ge=1, le=20)
    positioning: Optional[int] = Field(None, ge=1, le=20)
    teamwork: Optional[int] = Field(None, ge=1, le=20)
    vision: Optional[int] = Field(None, ge=1, le=20)
    work_rate: Optional[int] = Field(None, ge=1, le=20)
    
    # Attributes (Physical)
    acceleration: Optional[int] = Field(None, ge=1, le=20)
    agility: Optional[int] = Field(None, ge=1, le=20)
    balance: Optional[int] = Field(None, ge=1, le=20)
    jumping_reach: Optional[int] = Field(None, ge=1, le=20)
    natural_fitness: Optional[int] = Field(None, ge=1, le=20)
    pace: Optional[int] = Field(None, ge=1, le=20)
    stamina: Optional[int] = Field(None, ge=1, le=20)
    strength: Optional[int] = Field(None, ge=1, le=20)
    
    # Attributes (Goalkeeping)
    aerial_reach: Optional[int] = Field(None, ge=1, le=20)
    command_of_area: Optional[int] = Field(None, ge=1, le=20)
    communication: Optional[int] = Field(None, ge=1, le=20)
    eccentricity: Optional[int] = Field(None, ge=1, le=20)
    handling: Optional[int] = Field(None, ge=1, le=20)
    kicking: Optional[int] = Field(None, ge=1, le=20)
    one_on_ones: Optional[int] = Field(None, ge=1, le=20)
    reflexes: Optional[int] = Field(None, ge=1, le=20)
    rushing_out: Optional[int] = Field(None, ge=1, le=20)
    punching: Optional[int] = Field(None, ge=1, le=20)
    throwing: Optional[int] = Field(None, ge=1, le=20)
