from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class BudgetConstraints(BaseModel):
    max_transfer: float = Field(default=float('inf'), description="Maximum transfer fee budget")
    max_wage: float = Field(default=float('inf'), description="Maximum annual wage budget")

class TransferRequest(BaseModel):
    target_role: str = Field(..., description="The tactical role to rank candidates for (e.g., 'Advanced Forward')")
    budget: BudgetConstraints = Field(default_factory=BudgetConstraints)
    target_position_group: str = Field(..., description="Position group (e.g., 'ST', 'M') to penalize hoarding")
    weights: Optional[Dict[str, float]] = Field(
        default={"fit": 0.33, "value": 0.33, "investment": 0.33},
        description="Weights for the blended Pareto score."
    )

class ParetoResponse(BaseModel):
    best_fit: Optional[Dict[str, Any]]
    best_value: Optional[Dict[str, Any]]
    best_investment: Optional[Dict[str, Any]]
    best_blended: Optional[Dict[str, Any]]
    all_feasible: List[Dict[str, Any]]

class FeedbackRequest(BaseModel):
    player_id: str = Field(..., description="The name or ID of the player")
    context: str = Field(..., description="Context of the decision, e.g., 'transfer_recommendation'")
    decision: str = Field(..., description="The decision, e.g., 'shortlist', 'ignore', 'sell', 'keep'")
    
class GenericResponse(BaseModel):
    status: str
    message: str
