import os
import json
import threading
import pandas as pd
import numpy as np
from typing import List, Dict, Any

from src.models.similarity import PlayerSimilarityModel
from src.features.pipeline import process_features
from src.ingestion.pipeline import process_pipeline

class ApplicationState:
    def __init__(self):
        self.lock = threading.Lock()
        self.df = pd.DataFrame()
        self.similarity_model = PlayerSimilarityModel(n_components=15)
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.data_dir = os.path.join(base_dir, "data")
        self.processed_dir = os.path.join(self.data_dir, "processed")
        
    def get_latest_features_file(self):
        if not os.path.exists(self.processed_dir):
            return None
        files = [os.path.join(self.processed_dir, f) for f in os.listdir(self.processed_dir) if f.startswith("features_") and f.endswith(".jsonl")]
        if not files:
            return None
        
        # Sort by modification time, newest first
        files.sort(key=os.path.getmtime, reverse=True)
        return files[0]
        
    def load_data(self):
        """Loads the newest processed JSONL into memory and fits the PCA model."""
        latest_file = self.get_latest_features_file()
        if not latest_file:
            print(f"Warning: No features file found in {self.processed_dir}")
            return
            
        with self.lock:
            try:
                # Load JSON lines directly into Pandas
                self.df = pd.read_json(latest_file, lines=True)
                
                if not self.df.empty:
                    # Convert to list of dicts purely for the PCA fit
                    # PCA fit expects list of dicts based on the original similarity.py signature
                    records = self._safe_to_dict(self.df)
                    self.similarity_model.fit(records)
                    print(f"Loaded {len(self.df)} records and fitted PCA model.")
            except Exception as e:
                print(f"Error loading state data: {e}")
                self.df = pd.DataFrame()
            
    def _get_club_mask(self, team_name: str, include: bool):
        if self.df.empty:
            return pd.Series(dtype=bool)
            
        club_col = self.df['club'].astype(str).str.lower().str.strip()
        mask_exact = club_col == team_name.lower().strip()
        mask_null = self.df['club'].isna() | (club_col == "nan") | (club_col == "-") | (club_col == "none") | (club_col == "")
        
        mask = mask_exact | mask_null
        return mask if include else ~mask

    def _safe_to_dict(self, df_subset: pd.DataFrame) -> List[Dict[str, Any]]:
        # Convert NaN back to None for correct JSON serialization by FastAPI
        return df_subset.replace({np.nan: None}).to_dict(orient='records')

    def get_squad(self, team_name: str) -> List[Dict[str, Any]]:
        with self.lock:
            if self.df.empty:
                return []
            mask = self._get_club_mask(team_name, include=True)
            return self._safe_to_dict(self.df[mask])
        
    def get_scouted_pool(self, team_name: str) -> List[Dict[str, Any]]:
        with self.lock:
            if self.df.empty:
                return []
            mask = self._get_club_mask(team_name, include=False)
            return self._safe_to_dict(self.df[mask])
            
    @property
    def records(self):
        """Backward compatibility property if anything external tries to access records directly."""
        with self.lock:
            if self.df.empty:
                return []
            return self._safe_to_dict(self.df)
        
    def run_ingestion_pipeline_sync(self, raw_dir: str):
        """Runs the entire pipeline Phase 1 -> Phase 2 and reloads data."""
        from datetime import datetime
        
        batch_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Phase 1
        res = process_pipeline(raw_dir, self.processed_dir, batch_id=batch_id)
        
        # Phase 2
        export_file = os.path.join(self.processed_dir, f"export_{batch_id}.jsonl")
        features_file = os.path.join(self.processed_dir, f"features_{batch_id}.jsonl")
        process_features(export_file, features_file)
        
        # Reload state
        self.load_data()

# Global state singleton
app_state = ApplicationState()

def get_state() -> ApplicationState:
    return app_state
