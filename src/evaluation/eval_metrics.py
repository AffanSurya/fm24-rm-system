import numpy as np

def dcg_at_k(relevances, k):
    relevances = np.asfarray(relevances)[:k]
    if relevances.size:
        return np.sum((np.power(2, relevances) - 1) / np.log2(np.arange(2, relevances.size + 2)))
    return 0.

def ndcg_at_k(relevances, k):
    """
    Normalized Discounted Cumulative Gain.
    relevances: List of true relevance scores in the order predicted by the model.
    """
    dcg = dcg_at_k(relevances, k)
    if not dcg:
        return 0.
    
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = dcg_at_k(ideal_relevances, k)
    
    if not idcg:
        return 0.
        
    return dcg / idcg

def precision_at_k(relevances, k, threshold=1):
    """
    relevances: List of true relevance scores in the order predicted by the model.
    threshold: Minimum score to be considered "relevant".
    """
    k = min(len(relevances), k)
    if k == 0:
        return 0.0
        
    relevant_count = sum(1 for r in relevances[:k] if r >= threshold)
    return relevant_count / k

if __name__ == "__main__":
    # Example Usage for when Feedback JSONL has data
    print("--- Offline Ranking Metrics (Placeholder) ---")
    
    # Imagine our model ranked 5 players. 
    # True relevance based on manager feedback: 3 (Must Buy), 2 (Good), 0 (Bad), 1 (Okay), 0 (Bad)
    simulated_relevances = [3, 2, 0, 1, 0]
    
    print(f"Simulated Ground Truth Relevances (in order predicted by model): {simulated_relevances}")
    print(f"NDCG@3: {ndcg_at_k(simulated_relevances, 3):.4f}")
    print(f"NDCG@5: {ndcg_at_k(simulated_relevances, 5):.4f}")
    print(f"Precision@3 (Threshold=2): {precision_at_k(simulated_relevances, 3, threshold=2):.4f}")
