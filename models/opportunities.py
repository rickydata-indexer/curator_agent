"""
Models for handling curation opportunities and calculations.
"""

from typing import Dict, List
from dataclasses import dataclass

@dataclass
class Opportunity:
    """Data class representing a curation opportunity."""
    ipfs_hash: str
    nft_id: str
    signal_amount: float
    signalled_tokens: float
    annual_queries: int
    total_earnings: float
    curator_share: float
    estimated_earnings: float
    current_apr: float
    potential_apr: float
    weekly_queries: int

def calculate_opportunity_metrics(
    signal_amount: float,
    signalled_tokens: float,
    annual_queries: int,
    grt_price: float,
    is_new_position: bool = False
) -> tuple:
    """Calculate metrics for an opportunity using streamlit app's logic."""
    ENTRY_COST_PERCENTAGE = 0.005  # 0.5% entry cost
    CURATOR_SHARE = 0.10  # 10% of query fees
    EARNINGS_PER_100K_QUERIES = 4  # $4 per 100k queries
    
    # Calculate total earnings based on $4 per 100k queries
    total_earnings = (float(annual_queries) / 100000) * EARNINGS_PER_100K_QUERIES
    
    # Calculate curator share (10% of total earnings)
    curator_share = total_earnings * CURATOR_SHARE
    
    # Calculate portion owned
    portion_owned = signal_amount / signalled_tokens if signalled_tokens > 0 else 0
    
    # Calculate estimated earnings
    estimated_earnings = curator_share * portion_owned
    
    # Calculate APR
    apr = (estimated_earnings / (signal_amount * grt_price)) * 100 if signal_amount > 0 else 0
    
    # Apply entry cost if this is a new position
    if is_new_position:
        apr -= (ENTRY_COST_PERCENTAGE * 100)
    
    return total_earnings, curator_share, estimated_earnings, apr

def calculate_opportunities(
    deployments: List[Dict],
    query_fees: Dict[str, float],
    query_counts: Dict[str, int],
    grt_price: float
) -> List[Opportunity]:
    """Calculate investment opportunities from deployment and query data."""
    opportunities = []
    MIN_SIGNAL = 100  # Minimum signal amount in GRT

    for deployment in deployments:
        try:
            ipfs_hash = deployment['ipfsHash']
            nft_id = str(deployment.get('nftID', ''))  # Convert NFT ID to string
            
            # Convert signal amounts from wei to GRT
            try:
                signal_amount = float(deployment['signalAmount']) / 1e18
                signalled_tokens = float(deployment['signalledTokens']) / 1e18
            except (ValueError, TypeError):
                continue  # Skip if signal amounts are invalid
            
            if ipfs_hash in query_counts:
                weekly_queries = query_counts[ipfs_hash]
                annual_queries = weekly_queries * 52  # Annualize the queries

                # Calculate current metrics
                total_earnings, curator_share, estimated_earnings, current_apr = calculate_opportunity_metrics(
                    signal_amount,
                    signalled_tokens,
                    annual_queries,
                    grt_price,
                    False
                )

                # Calculate potential metrics with minimum signal
                potential_signal = signal_amount + MIN_SIGNAL
                potential_signalled = signalled_tokens + MIN_SIGNAL
                _, _, potential_earnings, potential_apr = calculate_opportunity_metrics(
                    potential_signal,
                    potential_signalled,
                    annual_queries,
                    grt_price,
                    signal_amount == 0  # Is new position if current signal is 0
                )

                # Only include opportunities where potential APR is positive
                # and weekly queries are above a minimum threshold
                MIN_WEEKLY_QUERIES = 1000  # Minimum weekly queries threshold
                if potential_apr > 0 and weekly_queries >= MIN_WEEKLY_QUERIES:
                    opportunities.append(Opportunity(
                        ipfs_hash=ipfs_hash,
                        nft_id=nft_id,
                        signal_amount=signal_amount,
                        signalled_tokens=signalled_tokens,
                        annual_queries=annual_queries,
                        total_earnings=total_earnings,
                        curator_share=curator_share,
                        estimated_earnings=estimated_earnings,
                        current_apr=current_apr,
                        potential_apr=potential_apr,
                        weekly_queries=weekly_queries
                    ))
        except Exception as e:
            print(f"Error processing deployment {deployment.get('ipfsHash', 'unknown')}: {str(e)}")
            continue

    # Sort opportunities by potential APR in descending order
    return sorted(opportunities, key=lambda x: x.potential_apr, reverse=True)
