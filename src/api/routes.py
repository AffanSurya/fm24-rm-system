from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query, UploadFile, File
from typing import List, Dict, Any
import os
import shutil
import json

from src.api.state import ApplicationState, get_state
from src.api.schemas import TransferRequest, ParetoResponse, FeedbackRequest, GenericResponse
from src.models.recommender import RecommendationEngine
from src.models.optimization import TransferOptimizer
from src.models.feedback import FeedbackLogger

router = APIRouter()
feedback_logger = FeedbackLogger()

@router.post("/ingest", response_model=GenericResponse)
async def ingest_files(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...), state: ApplicationState = Depends(get_state)):
    """Uploads raw FM exports, processes them in the background, and updates the global state."""
    
    # Save uploaded files to temp raw directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    upload_dir = os.path.join(base_dir, "data", "raw", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    html_paths = []
    rtf_paths = []
    
    for file in files:
        file_location = os.path.join(upload_dir, file.filename)
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
            
        if file.filename.endswith(".html"):
            html_paths.append(file_location)
        elif file.filename.endswith(".rtf"):
            rtf_paths.append(file_location)
            
    # Add to background task
    background_tasks.add_task(state.run_ingestion_pipeline_sync, upload_dir)
    
    return GenericResponse(status="Accepted", message="Files received. Ingestion pipeline started in the background.")

@router.get("/squad/depth")
def get_squad_depth(team_name: str, target_tactic: str, state: ApplicationState = Depends(get_state)):
    squad = state.get_squad(team_name)
    if not squad:
        raise HTTPException(status_code=404, detail="No players found for this team. Check spelling or ingest data.")
        
    res = RecommendationEngine.recommend_squad_depth(squad, target_tactic)
    return res

@router.get("/squad/retention")
def get_squad_retention(team_name: str, state: ApplicationState = Depends(get_state)):
    squad = state.get_squad(team_name)
    if not squad:
        raise HTTPException(status_code=404, detail="No players found for this team.")
        
    res = RecommendationEngine.recommend_retention(squad, state.similarity_model)
    return res

@router.post("/transfers/recommend", response_model=ParetoResponse)
def recommend_transfers(request: TransferRequest, team_name: str = Query(..., description="Your team name to exclude squad players"), state: ApplicationState = Depends(get_state)):
    scouted_pool = state.get_scouted_pool(team_name)
    
    # Determine depth count for positional hoarding penalty
    squad = state.get_squad(team_name)
    depth_count = len([p for p in squad if p.get("primary_pos_group") == request.target_position_group])
    
    budget_dict = {
        "max_transfer": request.budget.max_transfer,
        "max_wage": request.budget.max_wage
    }
    
    res = TransferOptimizer.optimize_transfers(
        scouted_pool=scouted_pool,
        target_role=request.target_role,
        budget_constraints=budget_dict,
        depth_count=depth_count,
        weights=request.weights
    )
    
    return res

@router.post("/feedback", response_model=GenericResponse)
def log_feedback(request: FeedbackRequest, state: ApplicationState = Depends(get_state)):
    # Find player record
    player_record = next((r for r in state.records if r.get("name") == request.player_id), None)
    if not player_record:
        # We can still log it with just the ID, but getting full record is better
        player_record = {"name": request.player_id}
        
    feedback_logger.log_decision(player_record, request.context, request.decision)
    return GenericResponse(status="Success", message="Feedback logged for future LTR modeling.")

@router.get("/config/roles")
def get_roles_config():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(base_dir, "config", "role_weights.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

@router.put("/config/roles", response_model=GenericResponse)
def update_roles_config(new_config: Dict[str, Any]):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(base_dir, "config", "role_weights.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(new_config, f, indent=2)
    return GenericResponse(status="Success", message="Tactical weights updated.")
