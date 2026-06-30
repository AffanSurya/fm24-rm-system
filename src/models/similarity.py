import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Tuple

from src.core.config import ATTRIBUTE_MAP

class PlayerSimilarityModel:
    def __init__(self, n_components: int = 15):
        self.scaler = StandardScaler()
        # 15 components usually capture 90%+ variance for FM's 47 attributes
        self.pca = PCA(n_components=n_components)
        self.is_fitted = False
        
        self.player_names = []
        self.embeddings = None
        self.records = []
        
        # We use the canonical attribute names
        self.feature_cols = list(ATTRIBUTE_MAP.values())
        
    def _extract_features(self, records: List[Dict[str, Any]]) -> np.ndarray:
        features = []
        for r in records:
            # We use the percentile-normalized values if available, otherwise raw attributes.
            # E.g. 'tackling_percentile' or 'tackling'
            row = []
            for col in self.feature_cols:
                pct_col = f"{col}_percentile"
                if pct_col in r:
                    val = r[pct_col]
                else:
                    val = r.get(col)
                    
                # Handle None
                if val is None:
                    val = 0.5 if pct_col in r else 10.0
                row.append(val)
            features.append(row)
        return np.array(features)
        
    def fit(self, records: List[Dict[str, Any]]):
        if not records:
            return
            
        X = self._extract_features(records)
        X_scaled = self.scaler.fit_transform(X)
        
        # Handle edge case where n_samples < n_components
        if len(records) < self.pca.n_components:
            self.pca = PCA(n_components=len(records))
            
        self.embeddings = self.pca.fit_transform(X_scaled)
        
        self.player_names = [r.get("name", f"Unknown_{i}") for i, r in enumerate(records)]
        self.records = records
        self.is_fitted = True
        
    def transform(self, records: List[Dict[str, Any]]) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model must be fitted before calling transform.")
        X = self._extract_features(records)
        X_scaled = self.scaler.transform(X)
        return self.pca.transform(X_scaled)
        
    def find_similar_players(self, target_record: Dict[str, Any], top_n: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
            
        target_embedding = self.transform([target_record])
        similarities = cosine_similarity(target_embedding, self.embeddings)[0]
        
        # Argsort descending
        top_indices = np.argsort(similarities)[::-1]
        
        results = []
        for idx in top_indices:
            # Skip self
            if self.records[idx].get("name") == target_record.get("name"):
                continue
            
            sim_score = round(float(similarities[idx]), 3)
            results.append((self.records[idx], sim_score))
            
            if len(results) >= top_n:
                break
                
        return results
        
    def calculate_replaceability(self, target_record: Dict[str, Any], similarity_threshold: float = 0.8) -> int:
        """
        Returns how many similar players exist in the pool that are cheaper and younger.
        """
        if not self.is_fitted:
            return 0
            
        target_value = target_record.get("transfer_value_mid", 0.0)
        target_age = target_record.get("age", 99)
        
        target_embedding = self.transform([target_record])
        similarities = cosine_similarity(target_embedding, self.embeddings)[0]
        
        replaceable_count = 0
        for idx, sim in enumerate(similarities):
            if sim >= similarity_threshold:
                candidate = self.records[idx]
                if candidate.get("name") == target_record.get("name"):
                    continue
                    
                cand_value = candidate.get("transfer_value_mid", 0.0)
                cand_age = candidate.get("age", 99)
                
                # Treat missing/0 transfer value carefully (might be untransferable or very cheap)
                # But typically, if cand_value <= target_value and cand_age <= target_age:
                if cand_value <= target_value and cand_age <= target_age:
                    replaceable_count += 1
                    
        return replaceable_count
