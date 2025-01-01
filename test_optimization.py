import pandas as pd
import numpy as np
from ortools.linear_solver import pywraplp

def optimize_signals(subgraphs_data, total_new_signal=1000.0, min_allocation=10.0):
    """
    Optimize signal allocation across subgraphs to maximize returns.
    """
    df = pd.DataFrame(subgraphs_data['new_signals'])
    
    # Initialize solver
    solver = pywraplp.Solver.CreateSolver('GLOP')
    
    # Create variables for new signal allocations
    allocations = {}
    for idx, row in df.iterrows():
        allocations[row['ipfs_hash']] = solver.NumVar(0, total_new_signal * 0.5, f'alloc_{idx}')  # Cap each at 50% of total
    
    # Total allocation constraint
    solver.Add(sum(allocations.values()) <= total_new_signal)
    
    # Require at least 20% of total signal to be allocated to non-top subgraphs
    top_apr_hash = df.loc[df['apr'].idxmax(), 'ipfs_hash']
    solver.Add(
        sum(alloc for hash_id, alloc in allocations.items() if hash_id != top_apr_hash) 
        >= total_new_signal * 0.2
    )
    
    # Objective: Maximize expected diluted returns
    objective = solver.Objective()
    
    for idx, row in df.iterrows():
        current_signal = row['signal_amount']
        current_apr = row['apr']
        annual_queries = row['annual_queries']
        new_signal = allocations[row['ipfs_hash']]
        
        # Weight by query volume
        query_weight = np.log1p(annual_queries) / np.log1p(df['annual_queries'].max())
        
        # Calculate expected diluted APR contribution
        # We want to maximize: current_apr * (current_signal / (current_signal + new_signal))
        # Approximate this as: current_apr * (1 - new_signal/(2*current_signal))
        weight = current_apr * query_weight / current_signal
        objective.SetCoefficient(new_signal, weight)
        
        # Add minimum allocation constraint if allocated
        is_allocated = solver.BoolVar(f'is_allocated_{idx}')
        solver.Add(new_signal >= min_allocation * is_allocated)
        solver.Add(new_signal <= total_new_signal * 0.5 * is_allocated)
        
        # Prevent excessive dilution
        solver.Add(new_signal <= current_signal * 5)  # Cap at 5x current signal
    
    objective.SetMaximization()
    
    # Solve
    status = solver.Solve()
    
    if status == pywraplp.Solver.OPTIMAL:
        results = []
        total_allocated = sum(allocations[hash_id].solution_value() for hash_id in allocations)
        
        for idx, row in df.iterrows():
            hash_id = row['ipfs_hash']
            new_signal = allocations[hash_id].solution_value()
            
            if new_signal >= min_allocation:
                # Calculate new APR after dilution
                dilution_factor = row['signal_amount'] / (row['signal_amount'] + new_signal)
                new_apr = row['apr'] * dilution_factor
                
                results.append({
                    'ipfs_hash': hash_id,
                    'signal_amount': row['signal_amount'],
                    'new_signal': new_signal,
                    'allocation_percentage': (new_signal / total_new_signal) * 100,
                    'signalled_tokens': row['signalled_tokens'],
                    'annual_queries': row['annual_queries'],
                    'total_earnings': row['total_earnings'],
                    'curator_share': row['curator_share'],
                    'estimated_earnings': row['estimated_earnings'],
                    'apr': new_apr,
                    'original_apr': row['apr'],
                    'weekly_queries': row['weekly_queries']
                })
        
        return pd.DataFrame(results)
    else:
        raise Exception("No optimal solution found")

# Example usage
data = {'new_signals': [{'ipfs_hash': 'QmfQ9PWRhQZc2XeFL2hKMkyen33e3RSXxYzcTyhLGVTeGn', 'signal_amount': 148.32804053050063, 'signalled_tokens': 166.9279939015239, 'annual_queries': 47356036, 'total_earnings': 1894.24144, 'curator_share': 189.424144, 'estimated_earnings': 168.31755688181724, 'apr': 560.2618128683165, 'weekly_queries': 910693}, {'ipfs_hash': 'QmYYmaFvdLjAYDpQwhPq4FNkpiyNLiedLNgtcvEDipcGd3', 'signal_amount': 159.1006748320156, 'signalled_tokens': 604.8178153692892, 'annual_queries': 74838348, 'total_earnings': 2993.53392, 'curator_share': 299.353392, 'estimated_earnings': 78.74656709867689, 'apr': 244.36807707693768, 'weekly_queries': 1439199}, {'ipfs_hash': 'QmRwHcwdfBEjJVfHVCsPWZTou5UXEpweccM6MDSUwcgX2c', 'signal_amount': 248.489901, 'signalled_tokens': 253.68487784098485, 'annual_queries': 23925200, 'total_earnings': 957.008, 'curator_share': 95.70080000000002, 'estimated_earnings': 93.74103226021636, 'apr': 186.2541042557902, 'weekly_queries': 460100}, {'ipfs_hash': 'QmQMFbrMLds7uCZPkzQWZZFif3cpzxFGQ6g6HZUTjzNUck', 'signal_amount': 495.98990100000003, 'signalled_tokens': 501.40297093143266, 'annual_queries': 42221868, 'total_earnings': 1688.87472, 'curator_share': 168.887472, 'estimated_earnings': 167.0641886341663, 'apr': 166.30120461418235, 'weekly_queries': 811959}, {'ipfs_hash': 'QmUhiH6Z5xo6o3GNzsSvqpGKLmCt6w5WzKQ1yHk6C8AA8S', 'signal_amount': 988.8005723110655, 'signalled_tokens': 1140.1122660416754, 'annual_queries': 87370712, 'total_earnings': 3494.82848, 'curator_share': 349.48284800000005, 'estimated_earnings': 303.1007124544604, 'apr': 151.34326922661808, 'weekly_queries': 1680206}]}

# Run optimization
result_df = optimize_signals(data, total_new_signal=15000.0, min_allocation=100.0)

# Sort and display results
print("\nOptimal Signal Allocations:")
print(result_df)