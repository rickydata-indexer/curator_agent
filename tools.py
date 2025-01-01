import os
import json
import requests
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from typing import Dict, List

# Functions to interact with Dify backend. Tools defined by the API keys, which all need to be set in .env
def curation_user_signals():
    # Load environment variables from .env file
    load_dotenv()
    """Use Dify workflow to get curation agent signals data"""
    url = "https://dify.rickydata.com/v1/workflows/run"
    headers = {
        'Authorization': f"Bearer {os.getenv('KEY_curation_user_signals')}",
        'Content-Type': 'application/json'
    }
    payload = {
        'inputs': {
            'user_wallet': "0xAB1D1366de8b5D1E3479f01b0D73BcC93048f6d5",
            'infura_api_key': f"{os.getenv('INFURA_API_KEY')}"
        },
        'response_mode': 'blocking',
        'user': 'curation_agent_python'
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    
    if response_data.get('data', {}).get('outputs', {}):
        return response_data['data']['outputs']
    return response_data

def unsignal_from_subgraph(subgraph_deployment_ipfs_hash, amount_signal=0.001):
    # Load environment variables from .env file
    load_dotenv()
    """Use unsignal from subgraph data Dify workflow"""
    url = "https://dify.rickydata.com/v1/workflows/run"
    headers = {
        'Authorization': f"Bearer {os.getenv('KEY_unsignal_from_subgraph')}",
        'Content-Type': 'application/json'
    }
    payload = {
        'inputs': {
            'amount_signal': amount_signal,
            'subgraph_deployment_ipfs_hash': subgraph_deployment_ipfs_hash,
            'infura_api_key': f"{os.getenv('INFURA_API_KEY')}" 
        },
        'response_mode': 'blocking',
        'user': 'curation_agent_python'
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    
    if response_data.get('data', {}).get('outputs', {}):
        return response_data['data']['outputs']
    return response_data

def curation_best_opportunities(min_apr=20, min_weekly_queries=100000, min_subgraph_signal=1):
    # Load environment variables from .env file
    load_dotenv()
    """Use Dify workflow to find best opportunities"""
    url = "https://dify.rickydata.com/v1/workflows/run"
    headers = {
        'Authorization': f"Bearer {os.getenv('KEY_curation_best_opportunities')}",
        'Content-Type': 'application/json'
    }
    payload = {
        'inputs': {
            'min_apr': min_apr,
            'min_weekly_queries': min_weekly_queries,
            'min_subgraph_signal': min_subgraph_signal
        },
        'response_mode': 'blocking',
        'user': 'curation_agent_python'
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    
    if response_data.get('data', {}).get('outputs', {}):
        return response_data['data']['outputs']
    return response_data

def pull_grt_balance_from_subgraph():
    # Load environment variables from .env file
    load_dotenv()
    """Use Dify workflow to find best opportunities"""
    url = "https://dify.rickydata.com/v1/workflows/run"
    headers = {
        'Authorization': f"Bearer {os.getenv('KEY_pull_grt_balance_from_subgraph')}",
        'Content-Type': 'application/json'
    }
    payload = {
        'inputs': {
            'thegraph_api_key': f"{os.getenv('THEGRAPH_API_KEY')}",
            'user_wallet': f"{os.getenv('AGENT_WALLET')}",
        },
        'response_mode': 'blocking',
        'user': 'curation_agent_python'
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    
    if response_data.get('data', {}).get('outputs', {}):
        return response_data['data']['outputs']
    return response_data

def optimize_signals(subgraphs_data: Dict, total_new_signal: float = 1000.0, min_allocation: float = 10.0) -> pd.DataFrame:
    """
    Optimize signal allocation across subgraphs using non-linear optimization.
    Uses the true mathematical relationship between signal and returns.
    
    Args:
        subgraphs_data: Dictionary containing subgraph data
        total_new_signal: Total amount of signal to allocate
        min_allocation: Minimum allocation per subgraph
    
    Returns:
        DataFrame containing optimized allocations and metrics
    """
    df = pd.DataFrame(subgraphs_data['new_signals'])
    n_subgraphs = len(df)
    
    # Extract key metrics
    current_signals = df['signal_amount'].values
    query_fees = df['total_earnings'].values  # Annual earnings from query fees
    
    def objective(allocations: np.ndarray) -> float:
        """
        Objective function to minimize (negative of total returns).
        For each subgraph:
        new_apr = (query_fees / (current_signal + new_signal)) * 100
        total_return = Σ (new_signal * new_apr)
        """
        # Calculate new APRs
        new_aprs = (query_fees / (current_signals + allocations)) * 100
        
        # Calculate total returns (allocation * diluted APR)
        returns = np.sum(allocations * new_aprs)
        
        # Return negative since we're minimizing
        return -returns
    
    def objective_gradient(allocations: np.ndarray) -> np.ndarray:
        """
        Gradient of the objective function.
        ∂(Return)/∂allocation_i = new_apr_i - allocation_i * query_fees_i / (current_signal_i + allocation_i)^2 * 100
        """
        # Gradient of APR with respect to allocation
        grad_returns = (query_fees / (current_signals + allocations)) * 100 - (allocations * query_fees / (current_signals + allocations)**2) * 100
        
        return -grad_returns
    
    # Constraint: total allocation must equal total_new_signal
    constraints = [{
        'type': 'eq',
        'fun': lambda x: np.sum(x) - total_new_signal,
        'jac': lambda x: np.ones_like(x)  # Gradient of the sum constraint
    }]
    
    # Bounds for each allocation
    bounds = [(min_allocation, None) for _ in range(n_subgraphs)]
    
    # Initial guess: proportional to query fees
    initial_allocation = total_new_signal * (query_fees / np.sum(query_fees))
    # Ensure minimum allocation
    initial_allocation = np.maximum(initial_allocation, min_allocation)
    # Scale to meet total signal constraint
    initial_allocation *= total_new_signal / np.sum(initial_allocation)
    
    # Run optimization
    result = minimize(
        objective,
        initial_allocation,
        method='SLSQP',
        jac=objective_gradient,
        bounds=bounds,
        constraints=constraints,
        options={'ftol': 1e-8, 'maxiter': 1000}
    )
    
    if not result.success:
        raise ValueError(f"Optimization failed: {result.message}")
    
    # Process results
    optimal_allocations = result.x
    results = []
    
    for idx, row in df.iterrows():
        new_signal = optimal_allocations[idx]
        
        # Calculate effective APR using true mathematical relationship
        dilution_factor = row['signal_amount'] / (row['signal_amount'] + new_signal)
        effective_apr = row['apr'] * dilution_factor
        
        results.append({
            'ipfs_hash': row['ipfs_hash'],
            'signal_amount': row['signal_amount'],
            'new_signal': new_signal,
            'allocation_percentage': (new_signal / total_new_signal) * 100,
            'apr': effective_apr,
            'original_apr': row['apr'],
            'weekly_queries': row['weekly_queries']
        })
    
    result_df = pd.DataFrame(results)
    return result_df


if __name__ == "__main__":
    # Test functions
    print("\nTesting curation_user_signals:")
    result = curation_user_signals()
    print(json.dumps(result, indent=2))

    print("\nTesting unsignal_from_subgraph:")
    result2 = unsignal_from_subgraph("QmUzRg2HHMpbgf6Q4VHKNDbtBEJnyp5JWCh2gUX9AV6jXv", amount_signal=0.001)
    print(result2)

    print("\nTesting curation_best_opportunities:")
    result3 = curation_best_opportunities()
    print(result3)

    print("\nTesting pull_grt_balance_from_subgraph:")
    result4 = pull_grt_balance_from_subgraph()
    print(result4)

    print("\nTesting optimize_signals:")
    sample_data = result3 # uses results from curation_best_opportunities
    # Run optimization
    result5 = optimize_signals(sample_data, total_new_signal=25000.0, min_allocation=100.0)
    print(result5)
    
