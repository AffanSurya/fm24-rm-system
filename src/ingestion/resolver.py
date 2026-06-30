from typing import List, Dict
from src.core.schemas import PlayerRecord

def generate_group_key(record: PlayerRecord) -> str:
    """
    Generate a base grouping key. We exclude Age here because it can 
    vary by +/- 1 year across exports.
    """
    name = record.name.lower().strip() if record.name else "unknown"
    nat = record.nationality.lower().strip() if record.nationality else "unknown"
    club = record.club.lower().strip() if record.club else "free_agent"
    return f"{name}|{nat}|{club}"

def resolve_entities(records: List[PlayerRecord]) -> List[PlayerRecord]:
    """
    Merges duplicate player records.
    Uses Name + Nationality + Club as a hard grouping key, 
    and allows a +/- 1 year tolerance for Age.
    Retains the record (attributes) from the one with the higher confidence_tier.
    """
    # Group by base key
    grouped: Dict[str, List[PlayerRecord]] = {}
    for r in records:
        key = generate_group_key(r)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(r)
        
    resolved_records = []
    
    for key, group in grouped.items():
        if len(group) == 1:
            resolved_records.append(group[0])
            continue
            
        # We have multiple records for the same Name/Nat/Club. 
        # Cluster them by Age (+/- 1 year tolerance).
        clusters = []
        for record in group:
            placed = False
            for cluster in clusters:
                # Check if age matches any existing cluster member within tolerance
                if any(abs(record.age - member.age) <= 1 for member in cluster):
                    cluster.append(record)
                    placed = True
                    break
            if not placed:
                clusters.append([record])
                
        # Resolve each cluster
        for cluster in clusters:
            if len(cluster) == 1:
                resolved_records.append(cluster[0])
            else:
                # Sort by confidence tier descending, take the best one
                best_record = max(cluster, key=lambda x: x.confidence_tier)
                # In a more advanced implementation, we could selectively merge non-null fields
                # from lower-confidence records, but taking the highest confidence is safest
                resolved_records.append(best_record)
                
    return resolved_records
