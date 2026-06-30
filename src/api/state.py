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
        self.features_file = os.path.join(self.data_dir, "processed", "features_test_data.jsonl")
        
    def load_data(self):
        """Loads processed JSONL into memory and fits the PCA model."""
        if not os.path.exists(self.features_file):
            print(f"Warning: Features file not found at {self.features_file}")
            return
            
        new_records = []
        with open(self.features_file, "r", encoding="utf-8") as f:
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
        processed_dir = os.path.join(self.data_dir, "processed")
        
        # Phase 1
        res = process_pipeline(raw_dir, processed_dir, batch_id="test_data")
        
        # Phase 2
        export_file = os.path.join(processed_dir, "export_test_data.jsonl")
        process_features(export_file, self.features_file)
        
        # Reload state
        self.load_data()

# Global state singleton
app_state = ApplicationState()

def get_state() -> ApplicationState:
    return app_state
