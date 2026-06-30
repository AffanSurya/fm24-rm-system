from typing import List, Dict, Any

class RecommendationEngine:
    @staticmethod
    def recommend_squad_depth(squad_records: List[Dict[str, Any]], target_tactic: str) -> Dict[str, Any]:
        """
        Ranks current players against a tactical style and calculates the Drop-off Score per position group.
        """
        # Filter out players missing tactical compatibility
        valid_squad = [r for r in squad_records if "tactical_compatibility" in r]
        
        # Sort entire squad by tactical fit
        sorted_squad = sorted(
            valid_squad, 
            key=lambda x: x["tactical_compatibility"].get(target_tactic, 0.0), 
            reverse=True
        )
        
        # Group by primary position to find drop-offs
        pos_groups = {}
        for r in sorted_squad:
            grp = r.get("primary_pos_group", "Unknown")
            if grp not in pos_groups:
                pos_groups[grp] = []
            pos_groups[grp].append(r)
            
        drop_offs = {}
        search_flags = []
        
        for grp, players in pos_groups.items():
            if len(players) >= 2:
                best_score = players[0]["tactical_compatibility"].get(target_tactic, 0.0)
                second_score = players[1]["tactical_compatibility"].get(target_tactic, 0.0)
                delta = round(best_score - second_score, 2)
                drop_offs[grp] = delta
                
                # If drop-off is severe (e.g., > 2.0 in a 20 point scale), flag for transfer search
                if delta > 2.0:
                    search_flags.append(grp)
            else:
                drop_offs[grp] = None
                search_flags.append(grp) # Need backup!
                
        return {
            "ranked_squad": sorted_squad,
            "drop_offs": drop_offs,
            "urgent_transfer_needs": search_flags
        }

    @staticmethod
    def recommend_transfers(scouted_records: List[Dict[str, Any]], target_role: str, max_price: float = None) -> List[Dict[str, Any]]:
        """
        Ranks candidates for a specific role.
        """
        valid_candidates = []
        for r in scouted_records:
            if "role_scores" not in r or target_role not in r["role_scores"]:
                continue
                
            if max_price is not None:
                tv_mid = r.get("transfer_value_mid", 0)
                # Allow players whose max value isn't strictly known if mid is within budget
                if tv_mid > max_price:
                    continue
                    
            valid_candidates.append(r)
            
        # Sort by role_fit_score descending
        sorted_candidates = sorted(
            valid_candidates,
            key=lambda x: x["role_scores"].get(target_role, 0.0),
            reverse=True
        )
        
        return sorted_candidates

    @staticmethod
    def recommend_retention(squad_records: List[Dict[str, Any]], similarity_model) -> List[Dict[str, Any]]:
        """
        Evaluates the squad for Keep, Sell, or Monitor signals.
        """
        results = []
        
        for r in squad_records:
            val_traj = r.get("value_trajectory", "Stable")
            replaceability = similarity_model.calculate_replaceability(r, similarity_threshold=0.8)
            
            # Find the best role trajectory
            role_trajs = r.get("role_trajectories", {})
            best_traj = max(role_trajs.values()) if role_trajs else 0.0
            
            # Proxy for Highly Influential / Team Leader
            leadership = r.get("leadership", 5)
            determination = r.get("determination", 5)
            is_influential = (leadership >= 15 or determination >= 16)
            
            signal = "Keep"
            reason = []
            
            # Hard Sell Logic
            if val_traj in ["Depressed", "Highly Depressed"] and replaceability > 2:
                if best_traj < 0.0: # Attributes are also decaying
                    if is_influential:
                        signal = "Monitor"
                        reason.append("Morale Risk: Value and attributes decaying, highly replaceable, but selling may disrupt squad dynamics.")
                    else:
                        signal = "Sell"
                        reason.append("Hard Sell: Value and attributes are decaying, and multiple cheaper replacements exist.")
                else:
                    signal = "Keep"
                    reason.append("Hold: Value is depressed, but current-fit trajectory is still in peak phase.")
            
            elif val_traj == "Rising" and best_traj > 0.0:
                signal = "Keep"
                reason.append("Core Asset: Improving fit and rising value.")
                
            elif replaceability == 0 and best_traj >= 0.0:
                signal = "Keep"
                reason.append("Irreplaceable: No immediate cheaper alternatives found.")
                
            else:
                signal = "Monitor"
                reason.append("Stable performer, monitor market conditions.")
                
            r_out = r.copy()
            r_out["retention_signal"] = signal
            r_out["retention_reason"] = " ".join(reason)
            r_out["replaceability_count"] = replaceability
            
            results.append(r_out)
            
        return results
