"""
Models for handling curation signal calculations and optimizations.
"""

from typing import Dict, List
from dataclasses import dataclass
from .opportunities import Opportunity

@dataclass
class UserOpportunity:
    """Data class representing a user's curation opportunity."""
    ipfs_hash: str
    user_signal: float
    total_signal: float
    portion_owned: float
    estimated_earnings: float
    apr: float
    weekly_queries: int

def calculate_optimal_allocations(
    opportunities: List[Opportunity],
    user_signals: Dict[str, float],
    total_signal: float,
    grt_price: float,
    num_subgraphs: int = 5,
    min_allocation: float = 100  # Minimum GRT per allocation
) -> Dict[str, float]:
    """Calculate optimal allocation of signals considering current holdings.
    
    Args:
        opportunities: List of available opportunities
        user_signals: Current user signal allocations
        total_signal: Total GRT available for allocation
        grt_price: Current GRT price in USD
        num_subgraphs: Maximum number of subgraphs to allocate to
        min_allocation: Minimum GRT to allocate per subgraph
        
    Returns:
        Dictionary mapping subgraph IDs to GRT amounts to signal
    """
    # Sort opportunities by APR
    sorted_opps = sorted(opportunities, key=lambda x: x.apr, reverse=True)
    
    # Take top N opportunities
    top_opportunities = sorted_opps[:num_subgraphs]
    
    # Initialize allocations
    allocations = {opp.ipfs_hash: 0.0 for opp in top_opportunities}
    remaining_signal = total_signal
    
    # First pass: ensure minimum allocation
    min_total = min_allocation * len(top_opportunities)
    if total_signal < min_total:
        # If we can't meet minimum allocation, distribute evenly
        per_allocation = total_signal / len(top_opportunities)
        return {opp.ipfs_hash: per_allocation for opp in top_opportunities}
    
    # Allocate minimum amount to each opportunity
    for opp in top_opportunities:
        allocations[opp.ipfs_hash] = min_allocation
        remaining_signal -= min_allocation
    
    # Second pass: distribute remaining signal proportionally to APR
    while remaining_signal > min_allocation:
        best_apr = -1
        best_opp = None
        
        for opp in top_opportunities:
            # Calculate new APR if we add min_allocation more
            current_allocation = allocations[opp.ipfs_hash]
            new_signal_amount = opp.signal_amount + current_allocation + min_allocation
            new_signalled_tokens = opp.signalled_tokens + current_allocation + min_allocation
            
            # Calculate new metrics
            portion_owned = new_signal_amount / new_signalled_tokens if new_signalled_tokens > 0 else 0
            estimated_earnings = opp.curator_share * portion_owned
            apr = (estimated_earnings / (new_signal_amount * grt_price)) * 100 if new_signal_amount > 0 else 0
            
            if apr > best_apr:
                best_apr = apr
                best_opp = opp
        
        if best_opp:
            # Add min_allocation to the best opportunity
            allocations[best_opp.ipfs_hash] += min_allocation
            remaining_signal -= min_allocation
        else:
            break
    
    # Remove any allocations that are below minimum
    return {k: v for k, v in allocations.items() if v >= min_allocation}

def calculate_user_opportunities(
    user_signals: Dict[str, float],
    opportunities: List[Opportunity],
    grt_price: float
) -> List[UserOpportunity]:
    """Calculate user-specific opportunities from their current signals."""
    user_opportunities = []
    
    for opp in opportunities:
        ipfs_hash = opp.ipfs_hash
        
        if ipfs_hash in user_signals:
            user_signal = user_signals[ipfs_hash]
            total_signal = opp.signalled_tokens
            portion_owned = user_signal / total_signal if total_signal > 0 else 0
            estimated_earnings = opp.curator_share * portion_owned
            apr = (estimated_earnings / (user_signal * grt_price)) * 100 if user_signal > 0 else 0
            
            user_opportunities.append(UserOpportunity(
                ipfs_hash=ipfs_hash,
                user_signal=user_signal,
                total_signal=total_signal,
                portion_owned=portion_owned,
                estimated_earnings=estimated_earnings,
                apr=apr,
                weekly_queries=opp.weekly_queries
            ))
    
    return sorted(user_opportunities, key=lambda x: x.apr, reverse=True)
