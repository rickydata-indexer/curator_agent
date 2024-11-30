"""
Data models for subgraph information and analysis.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime

@dataclass
class SubgraphDeployment:
    """Represents a specific subgraph deployment."""
    
    id: str
    signalled_tokens: int
    signal_amount: int
    query_fees_amount: int
    staked_tokens: int

    @classmethod
    def from_graph_data(cls, data: Dict) -> 'SubgraphDeployment':
        """Create instance from Graph API response data."""
        return cls(
            id=data['id'],
            signalled_tokens=int(data.get('signalledTokens', 0)),
            signal_amount=int(data.get('signalAmount', 0)),
            query_fees_amount=int(data.get('queryFeesAmount', 0)),
            staked_tokens=int(data.get('stakedTokens', 0))
        )

@dataclass
class SubgraphVersion:
    """Represents a version of a subgraph."""
    
    id: str
    deployment: SubgraphDeployment
    created_at: datetime

    @classmethod
    def from_graph_data(cls, data: Dict) -> 'SubgraphVersion':
        """Create instance from Graph API response data."""
        return cls(
            id=data['id'],
            deployment=SubgraphDeployment.from_graph_data(
                data['subgraphDeployment']
            ),
            created_at=datetime.fromtimestamp(int(data.get('createdAt', 0)))
        )

@dataclass
class Subgraph:
    """Represents a subgraph with its metadata and metrics."""
    
    id: str
    nft_id: str
    owner_id: str
    current_version: Optional[SubgraphVersion]
    created_at: datetime
    updated_at: datetime
    signalled_tokens: int
    unsignalled_tokens: int
    name_signal_amount: int
    name_signal_count: int
    metadata_hash: str
    description: str
    image: str
    display_name: str
    
    # Performance metrics
    avg_daily_fees: float = 0.0
    fee_growth_rate: float = 0.0
    signal_growth_rate: float = 0.0
    fee_volatility: float = 0.0
    network_correlation: float = 0.0

    @classmethod
    def from_graph_data(cls, data: Dict, metrics: Optional[Dict] = None) -> 'Subgraph':
        """Create instance from Graph API response data and metrics."""
        current_version = None
        if data.get('currentVersion'):
            current_version = SubgraphVersion.from_graph_data(
                data['currentVersion']
            )
            
        instance = cls(
            id=data['id'],
            nft_id=data['nftID'],
            owner_id=data['owner']['id'],
            current_version=current_version,
            created_at=datetime.fromtimestamp(int(data['createdAt'])),
            updated_at=datetime.fromtimestamp(int(data['updatedAt'])),
            signalled_tokens=int(data.get('signalledTokens', 0)),
            unsignalled_tokens=int(data.get('unsignalledTokens', 0)),
            name_signal_amount=int(data.get('nameSignalAmount', 0)),
            name_signal_count=int(data.get('nameSignalCount', 0)),
            metadata_hash=data.get('metadataHash', ''),
            description=data.get('description', ''),
            image=data.get('image', ''),
            display_name=data.get('displayName', '')
        )
        
        if metrics:
            instance.avg_daily_fees = metrics.get('avg_daily_fees', 0.0)
            instance.fee_growth_rate = metrics.get('fee_growth_rate', 0.0)
            instance.signal_growth_rate = metrics.get('signal_growth_rate', 0.0)
            instance.fee_volatility = metrics.get('fee_volatility', 0.0)
            instance.network_correlation = metrics.get('network_correlation', 0.0)
            
        return instance

    def calculate_apr(self) -> float:
        """Calculate the annual percentage rate based on fees and signal.
        
        Returns:
            Calculated APR as a percentage
        """
        if not self.current_version or self.current_version.deployment.signal_amount == 0:
            return 0.0
            
        # Calculate daily fee rate
        daily_fees = self.avg_daily_fees
        total_signal = self.current_version.deployment.signal_amount
        
        # Annualize and convert to percentage
        annual_rate = (daily_fees * 365 * 100) / total_signal
        return annual_rate

    def get_signal_share(self) -> float:
        """Calculate share of total network signal.
        
        Returns:
            Signal share as a percentage
        """
        if not self.current_version:
            return 0.0
            
        total_network_signal = self.signalled_tokens
        if total_network_signal == 0:
            return 0.0
            
        deployment_signal = self.current_version.deployment.signalled_tokens
        return (deployment_signal * 100) / total_network_signal

    def get_risk_score(self) -> float:
        """Calculate risk score based on various metrics.
        
        Returns:
            Risk score from 0 (lowest risk) to 100 (highest risk)
        """
        if not self.current_version:
            return 100.0
            
        # Factors that reduce risk
        positive_factors = [
            self.network_correlation,  # Higher correlation = lower risk
            self.get_signal_share(),   # Higher share = lower risk
            self.name_signal_count     # More curators = lower risk
        ]
        
        # Factors that increase risk
        negative_factors = [
            self.fee_volatility,      # Higher volatility = higher risk
            -self.fee_growth_rate,    # Negative growth = higher risk
            -self.signal_growth_rate  # Negative signal growth = higher risk
        ]
        
        # Calculate weighted average
        risk_score = (
            sum(negative_factors) - sum(positive_factors)
        ) / (len(negative_factors) + len(positive_factors))
        
        # Normalize to 0-100 scale
        normalized_score = (risk_score + 1) * 50
        return max(0.0, min(100.0, normalized_score))
