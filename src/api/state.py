import os
import json
import asyncio
from typing import List, Dict, Any

from src.models.similarity import PlayerSimilarityModel
from src.features.pipeline import process_features
from src.ingestion.pipeline import process_pipeline

class ApplicationState:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self.similarity_model = PlayerSimilarityModel(n_components=15)
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.data_dir = os.path.join(base_dir, "data")
        self.processed_dir = os.path.join(self.data_dir, "processed")
        
    def get_latest_features_file(self):
        if not os.path.exists(self.processed_dir):
            return None
        files = [f for f in os.listdir(self.processed_dir) if f.startswith("features_") and f.endswith(".jsonl")]
        if not files:
            return None
        # Lexicographical sort works for YYYYMMDDHHMMSS
        files.sort(reverse=True)
        return os.path.join(self.processed_dir, files[0])
        
    def load_data(self):
        """Loads the newest processed JSONL into memory and fits the PCA model."""
        latest_file = self.get_latest_features_file()
        if not latest_file:
            print(f"Warning: No features file found in {self.processed_dir}")
            return
            
        new_records = []
        with open(latest_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    new_records.append(json.loads(line))
                    
        self.records = new_records
        
        if self.records:
            self.similarity_model.fit(self.records)
            print(f"Loaded {len(self.records)} records and fitted PCA model.")
            
    def get_squad(self, team_name: str) -> List[Dict[str, Any]]:
        return [r for r in self.records if isinstance(r.get("club"), str) and team_name.lower() in r.get("club").lower()]
        
    def get_scouted_pool(self, team_name: str) -> List[Dict[str, Any]]:
        return [r for r in self.records if not (isinstance(r.get("club"), str) and team_name.lower() in r.get("club").lower())]
        
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
