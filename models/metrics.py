"""
Models for performance metrics calculations and analysis.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np
from scipy import stats

@dataclass
class QueryMetrics:
    """Daily query metrics for a subgraph."""
    
    timestamp: datetime
    query_fees: float
    fee_rebates: float
    curator_fees: float
    signalled_tokens: int
    unsignalled_tokens: int
    daily_query_fees: float

    @classmethod
    def from_graph_data(cls, data: Dict) -> 'QueryMetrics':
        """Create instance from Graph API response data."""
        return cls(
            timestamp=datetime.fromtimestamp(int(data['timestamp'])),
            query_fees=float(data['queryFeesAmount']),
            fee_rebates=float(data['queryFeeRebates']),
            curator_fees=float(data['curatorQueryFees']),
            signalled_tokens=int(data['signalledTokens']),
            unsignalled_tokens=int(data['unsignalledTokens']),
            daily_query_fees=float(data['dailyQueryFees'])
        )

@dataclass
class NetworkMetrics:
    """Daily network-wide metrics."""
    
    timestamp: datetime
    total_query_fees: float
    total_curator_fees: float
    total_signalled_tokens: int
    total_signals: int
    active_subgraph_count: int

    @classmethod
    def from_graph_data(cls, data: Dict) -> 'NetworkMetrics':
        """Create instance from Graph API response data."""
        return cls(
            timestamp=datetime.fromtimestamp(int(data['timestamp'])),
            total_query_fees=float(data['totalQueryFees']),
            total_curator_fees=float(data['totalCuratorQueryFees']),
            total_signalled_tokens=int(data['totalSignalledTokens']),
            total_signals=int(data['totalSignals']),
            active_subgraph_count=int(data['activeSubgraphCount'])
        )

class MetricsAnalyzer:
    """Analyzes subgraph and network metrics."""

    @staticmethod
    def calculate_growth_rate(values: List[float]) -> float:
        """Calculate exponential growth rate.
        
        Args:
            values: List of metric values
            
        Returns:
            Growth rate as decimal
        """
        if len(values) < 2:
            return 0.0
            
        # Convert to numpy array and remove zeros
        values = np.array(values)
        values = values[values > 0]
        
        if len(values) < 2:
            return 0.0
            
        # Calculate log returns
        log_returns = np.log(values[1:] / values[:-1])
        
        # Average daily growth rate
        daily_growth = np.mean(log_returns)
        
        # Convert to simple growth rate
        return np.exp(daily_growth) - 1

    @staticmethod
    def calculate_volatility(values: List[float]) -> float:
        """Calculate metric volatility.
        
        Args:
            values: List of metric values
            
        Returns:
            Volatility measure
        """
        if len(values) < 2:
            return 0.0
            
        values = np.array(values)
        if np.mean(values) == 0:
            return 0.0
            
        return np.std(values) / np.mean(values)

    @staticmethod
    def calculate_correlation(x: List[float], y: List[float]) -> float:
        """Calculate correlation between two metrics.
        
        Args:
            x: First metric values
            y: Second metric values
            
        Returns:
            Correlation coefficient
        """
        if len(x) != len(y) or len(x) < 2:
            return 0.0
            
        return stats.pearsonr(x, y)[0]

    @staticmethod
    def calculate_sharpe_ratio(
        returns: List[float],
        risk_free_rate: float = 0.02
    ) -> float:
        """Calculate Sharpe ratio for returns.
        
        Args:
            returns: List of return values
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0
            
        returns = np.array(returns)
        
        # Annualize metrics
        avg_return = np.mean(returns) * 365
        volatility = np.std(returns) * np.sqrt(365)
        
        if volatility == 0:
            return 0.0
            
        return (avg_return - risk_free_rate) / volatility

    @staticmethod
    def detect_anomalies(
        values: List[float],
        threshold: float = 2.0
    ) -> List[bool]:
        """Detect anomalous metric values.
        
        Args:
            values: List of metric values
            threshold: Z-score threshold for anomalies
            
        Returns:
            List of booleans indicating anomalies
        """
        if len(values) < 2:
            return [False] * len(values)
            
        values = np.array(values)
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return [False] * len(values)
            
        z_scores = np.abs((values - mean) / std)
        return z_scores > threshold

    @staticmethod
    def calculate_trend_strength(values: List[float]) -> float:
        """Calculate strength of metric trend.
        
        Args:
            values: List of metric values
            
        Returns:
            Trend strength from -1 to 1
        """
        if len(values) < 2:
            return 0.0
            
        # Use Kendall's Tau for trend strength
        x = np.arange(len(values))
        tau, _ = stats.kendalltau(x, values)
        return tau if not np.isnan(tau) else 0.0

    @staticmethod
    def calculate_risk_adjusted_return(
        returns: List[float],
        network_returns: List[float]
    ) -> float:
        """Calculate risk-adjusted return metric.
        
        Args:
            returns: List of subgraph returns
            network_returns: List of network returns
            
        Returns:
            Risk-adjusted return measure
        """
        if len(returns) != len(network_returns) or len(returns) < 2:
            return 0.0
            
        # Calculate excess returns over network
        excess_returns = np.array(returns) - np.array(network_returns)
        
        if len(excess_returns) < 2:
            return 0.0
            
        # Information ratio
        return np.mean(excess_returns) / np.std(excess_returns)
