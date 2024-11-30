"""
Models for handling curation opportunities and calculations.
"""

from typing import Dict, List
from dataclasses import dataclass

@dataclass
class Opportunity:
    """Data class representing a curation opportunity."""
    ipfs_hash: str
    signal_amount: float
    signalled_tokens: float
    annual_queries: int
    total_earnings: float
    curator_share: float
    estimated_earnings: float
    apr: float
    weekly_queries: int

def calculate_opportunities(
    deployments: List[Dict],
    query_fees: Dict[str, float],
    query_counts: Dict[str, int],
    grt_price: float
) -> List[Opportunity]:
    """Calculate investment opportunities from deployment and query data."""
    opportunities = []

    for deployment in deployments:
        ipfs_hash = deployment['ipfsHash']
        signal_amount = float(deployment['signalAmount']) / 1e18  # Convert wei to GRT
        signalled_tokens = float(deployment['signalledTokens']) / 1e18  # Convert wei to GRT

        if ipfs_hash in query_counts:
            weekly_queries = query_counts[ipfs_hash]
            annual_queries = weekly_queries * 52  # Annualize the queries

            # Calculate total earnings based on query fees
            total_earnings = query_fees.get(ipfs_hash, 0) * 12  # Annualize monthly fees

            # Calculate the curator's share (10% of total earnings)
            curator_share = total_earnings * 0.1

            # Calculate the portion owned by the curator
            if signalled_tokens > 0:
                portion_owned = signal_amount / signalled_tokens
            else:
                portion_owned = 0

            # Calculate estimated annual earnings for this curator
            estimated_earnings = curator_share * portion_owned

            # Calculate APR using GRT price
            if signal_amount > 0:
                apr = (estimated_earnings / (signal_amount * grt_price)) * 100
            else:
                apr = 0

            opportunities.append(Opportunity(
                ipfs_hash=ipfs_hash,
                signal_amount=signal_amount,
                signalled_tokens=signalled_tokens,
                annual_queries=annual_queries,
                total_earnings=total_earnings,
                curator_share=curator_share,
                estimated_earnings=estimated_earnings,
                apr=apr,
                weekly_queries=weekly_queries
            ))

    # Filter out subgraphs with zero signal amounts
    opportunities = [opp for opp in opportunities if opp.signal_amount > 0]

    # Sort opportunities by APR in descending order
    return sorted(opportunities, key=lambda x: x.apr, reverse=True)
