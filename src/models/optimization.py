from typing import List, Dict, Any

class TransferOptimizer:
    @staticmethod
    def calculate_amortized_cost(player: Dict[str, Any]) -> float:
        """
        amortized_cost = transfer_fee_mid + (wage_annual * contract_length_years)
        Defaults to 4 years.
        """
        transfer_fee = player.get("transfer_value_mid", 0.0)
        wage_annual = player.get("wage_annual", 0.0)
        return transfer_fee + (wage_annual * 4.0)

    @staticmethod
    def calculate_age_adjusted_return(player: Dict[str, Any], role_score: float) -> float:
        """
        (role_score * estimated_remaining_peak_years) / amortized_cost
        """
        amortized_cost = TransferOptimizer.calculate_amortized_cost(player)
        if amortized_cost <= 0:
            amortized_cost = 1000.0 # Prevent div by zero
            
        age = player.get("age", 25)
        
        if age < 23:
            remaining_peak = 8.0
        elif 23 <= age <= 28:
            remaining_peak = max(1.0, 31.0 - age)
        else:
            remaining_peak = max(0.5, 33.0 - age)
            
        return (role_score * remaining_peak) / amortized_cost * 1_000_000

    @staticmethod
    def optimize_transfers(scouted_pool: List[Dict[str, Any]], target_role: str, budget_constraints: Dict[str, float], depth_count: int = 0, weights: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Multi-objective optimization returning the Pareto frontier options.
        """
        max_transfer = budget_constraints.get("max_transfer", float('inf'))
        max_wage = budget_constraints.get("max_wage", float('inf'))
        
        if weights is None:
            # Default balanced weights
            weights = {"fit": 0.33, "value": 0.33, "investment": 0.33}
            
        feasible = []
        for r in scouted_pool:
            if "role_scores" not in r or target_role not in r["role_scores"]:
                continue
            
            # Hard Constraints First
            tv = r.get("transfer_value_mid", 0.0)
            wage = r.get("wage_annual", 0.0)
            
            if tv > max_transfer or wage > max_wage:
                continue
                
            role_score = r["role_scores"][target_role]
            val_eff = r.get("value_efficiencies", {}).get(target_role, 0.0)
            age_adj_ret = TransferOptimizer.calculate_age_adjusted_return(r, role_score)
            
            # Soft Constraints
            multiplier = 1.0
            if depth_count >= 3:
                multiplier -= 0.05 # Penalty for positional hoarding
            if r.get("is_homegrown", False):
                multiplier += 0.05 # Bonus for squad registration
                
            candidate = r.copy()
            candidate["opt_role_score"] = role_score
            candidate["opt_value_eff"] = val_eff
            candidate["opt_age_adj_ret"] = age_adj_ret
            candidate["opt_multiplier"] = multiplier
            feasible.append(candidate)
            
        if not feasible:
            return {"best_fit": None, "best_value": None, "best_investment": None, "best_blended": None, "all_feasible": []}
            
        # Normalize to 0-1 for blending
        max_rs = max(c["opt_role_score"] for c in feasible) or 1.0
        max_ve = max(c["opt_value_eff"] for c in feasible) or 1.0
        max_aar = max(c["opt_age_adj_ret"] for c in feasible) or 1.0
        
        for c in feasible:
            norm_rs = c["opt_role_score"] / max_rs
            norm_ve = c["opt_value_eff"] / max_ve
            norm_aar = c["opt_age_adj_ret"] / max_aar
            
            base_blend = (norm_rs * weights["fit"]) + (norm_ve * weights["value"]) + (norm_aar * weights["investment"])
            c["opt_blended"] = round(base_blend * c["opt_multiplier"], 3)
            
        return {
            "best_fit": max(feasible, key=lambda x: x["opt_role_score"]),
            "best_value": max(feasible, key=lambda x: x["opt_value_eff"]),
            "best_investment": max(feasible, key=lambda x: x["opt_age_adj_ret"]),
            "best_blended": max(feasible, key=lambda x: x["opt_blended"]),
            "all_feasible": sorted(feasible, key=lambda x: x["opt_blended"], reverse=True)
        }
