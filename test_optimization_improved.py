import pandas as pd
import numpy as np
from scipy.optimize import minimize
from typing import Dict, List

def optimize_signals_improved(subgraphs_data: Dict, total_new_signal: float = 1000.0, min_allocation: float = 10.0) -> pd.DataFrame:
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

# Example usage with test data
if __name__ == "__main__":
    data = {'new_signals': [{'ipfs_hash': 'QmfQ9PWRhQZc2XeFL2hKMkyen33e3RSXxYzcTyhLGVTeGn', 'signal_amount': 148.32804053050063, 'signalled_tokens': 166.9279939015239, 'annual_queries': 50778624, 'total_earnings': 2031.14496, 'curator_share': 203.11449600000003, 'estimated_earnings': 180.48246127485018, 'apr': 601.0175641493462, 'weekly_queries': 976512}, {'ipfs_hash': 'QmYYmaFvdLjAYDpQwhPq4FNkpiyNLiedLNgtcvEDipcGd3', 'signal_amount': 159.1006748320156, 'signalled_tokens': 604.8178153692892, 'annual_queries': 74746412, 'total_earnings': 2989.85648, 'curator_share': 298.985648, 'estimated_earnings': 78.64983000350767, 'apr': 244.17499371785297, 'weekly_queries': 1437431}, {'ipfs_hash': 'QmRwHcwdfBEjJVfHVCsPWZTou5UXEpweccM6MDSUwcgX2c', 'signal_amount': 248.489901, 'signalled_tokens': 253.68487784098485, 'annual_queries': 23403536, 'total_earnings': 936.14144, 'curator_share': 93.61414400000001, 'estimated_earnings': 91.69710694912204, 'apr': 182.272986518575, 'weekly_queries': 450068}, {'ipfs_hash': 'QmQMFbrMLds7uCZPkzQWZZFif3cpzxFGQ6g6HZUTjzNUck', 'signal_amount': 495.98990100000003, 'signalled_tokens': 501.40297093143266, 'annual_queries': 42523104, 'total_earnings': 1700.92416, 'curator_share': 170.09241600000001, 'estimated_earnings': 168.25612424268562, 'apr': 167.5612014496876, 'weekly_queries': 817752}, {'ipfs_hash': 'QmUhiH6Z5xo6o3GNzsSvqpGKLmCt6w5WzKQ1yHk6C8AA8S', 'signal_amount': 988.8005723110655, 'signalled_tokens': 1140.1122660416754, 'annual_queries': 87554220, 'total_earnings': 3502.1688, 'curator_share': 350.21688, 'estimated_earnings': 303.73732630672123, 'apr': 151.72770025866447, 'weekly_queries': 1683735}, {'ipfs_hash': 'Qma7EhueDE5mWWV2AuBnYotcxWMVTx6YPUyJKVLapRUv5k', 'signal_amount': 9530.770373102992, 'signalled_tokens': 10101.818023151041, 'annual_queries': 747526728, 'total_earnings': 29901.06912, 'curator_share': 2990.106912, 'estimated_earnings': 2821.0785725885353, 'apr': 146.20512446646234, 'weekly_queries': 14375514}, {'ipfs_hash': 'QmUv1eeYZnvodEv92JmULdHgoZGacm4391zki6dxPz2vk9', 'signal_amount': 149.50027119220175, 'signalled_tokens': 188.64290301102548, 'annual_queries': 13428012, 'total_earnings': 537.12048, 'curator_share': 53.71204800000001, 'estimated_earnings': 42.567017439395734, 'apr': 140.6392881598775, 'weekly_queries': 258231}, {'ipfs_hash': 'QmXeiwQ4PDExUqtcSNY4Ctwbbv4DSK9ZerLqhS9cHrUFDV', 'signal_amount': 459.8968208556737, 'signalled_tokens': 605.118729894131, 'annual_queries': 40576588, 'total_earnings': 1623.06352, 'curator_share': 162.306352, 'estimated_earnings': 123.35459406873979, 'apr': 132.48610725804383, 'weekly_queries': 780319}, {'ipfs_hash': 'QmSzo43g1vnQCRE3paJXkWwawujVkEs3LqDpB4SoXmbUSP', 'signal_amount': 737.2334157035336, 'signalled_tokens': 1045.6826028750495, 'annual_queries': 68952104, 'total_earnings': 2758.08416, 'curator_share': 275.808416, 'estimated_earnings': 194.45210243376118, 'apr': 130.28158996439834, 'weekly_queries': 1326002}, {'ipfs_hash': 'QmaJW9M9UvtBaDpQhyJiuv5zjwCBBMouxgi2hdMB9rLBMU', 'signal_amount': 1348.2314619301528, 'signalled_tokens': 1393.2824823904064, 'annual_queries': 91768248, 'total_earnings': 3670.72992, 'curator_share': 367.07299200000006, 'estimated_earnings': 355.20388930043373, 'apr': 130.13336909739562, 'weekly_queries': 1764774}]}

    # Run optimization
    result_df = optimize_signals_improved(data, total_new_signal=25000.0, min_allocation=100.0)

    # Display results
    pd.set_option('display.float_format', lambda x: '%.2f' % x)
    print("\nOptimal Signal Allocations:")
    result_display = result_df.sort_values('apr', ascending=False)
    print(result_display.to_string())

    # Print summary statistics
    print("\nSummary Statistics:")
    print(f"Total Allocated Signal: {result_df['new_signal'].sum():,.2f}")
    print(f"Average New APR: {result_df['apr'].mean():.2f}%")
    print(f"Max APR: {result_df['apr'].max():.2f}%")
    print(f"Min APR: {result_df['apr'].min():.2f}%")
    print(f"APR Standard Deviation: {result_df['apr'].std():.2f}%")
