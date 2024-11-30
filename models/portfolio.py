"""
Models for managing and optimizing a curation signal portfolio.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.optimize import minimize

from .subgraph import Subgraph
from .metrics import MetricsAnalyzer

@dataclass
class SignalPosition:
    """Represents a curation signal position."""
    
    subgraph_id: str
    deployment_id: str
    signalled_tokens: int
    signal_amount: int
    entry_date: str
    avg_entry_price: float
    current_value: float
    accrued_fees: float

    def calculate_roi(self) -> float:
        """Calculate return on investment.
        
        Returns:
            ROI as a percentage
        """
        initial_value = self.signalled_tokens * self.avg_entry_price
        if initial_value == 0:
            return 0.0
        
        total_return = (self.current_value + self.accrued_fees - initial_value)
        return (total_return * 100) / initial_value

class Portfolio:
    """Manages a portfolio of curation signals."""
    
    def __init__(
        self,
        positions: List[SignalPosition],
        total_grt: int,
        risk_free_rate: float = 0.02
    ):
        """Initialize portfolio.
        
        Args:
            positions: List of signal positions
            total_grt: Total GRT available
            risk_free_rate: Risk-free rate for calculations
        """
        self.positions = positions
        self.total_grt = total_grt
        self.risk_free_rate = risk_free_rate
        self.metrics_analyzer = MetricsAnalyzer()

    def get_total_value(self) -> float:
        """Get total portfolio value including accrued fees.
        
        Returns:
            Total value in GRT
        """
        return sum(p.current_value + p.accrued_fees for p in self.positions)

    def get_position_weights(self) -> Dict[str, float]:
        """Get current position weights.
        
        Returns:
            Dictionary of subgraph ID to weight
        """
        total_value = self.get_total_value()
        if total_value == 0:
            return {p.subgraph_id: 0.0 for p in self.positions}
            
        return {
            p.subgraph_id: (p.current_value / total_value)
            for p in self.positions
        }

    def calculate_portfolio_metrics(
        self,
        subgraphs: Dict[str, Subgraph]
    ) -> Dict[str, float]:
        """Calculate portfolio-level metrics.
        
        Args:
            subgraphs: Dictionary of subgraph data
            
        Returns:
            Dictionary of calculated metrics
        """
        weights = self.get_position_weights()
        
        # Calculate weighted metrics
        weighted_apr = sum(
            weights.get(s_id, 0) * s.calculate_apr()
            for s_id, s in subgraphs.items()
        )
        
        weighted_risk = sum(
            weights.get(s_id, 0) * s.get_risk_score()
            for s_id, s in subgraphs.items()
        )
        
        # Calculate diversification score
        herfindahl_index = sum(w * w for w in weights.values())
        diversification_score = 1 - herfindahl_index
        
        return {
            'weighted_apr': weighted_apr,
            'weighted_risk': weighted_risk,
            'diversification_score': diversification_score,
            'total_value': self.get_total_value(),
            'total_positions': len(self.positions)
        }

    def optimize_allocation(
        self,
        subgraphs: Dict[str, Subgraph],
        min_position: float = 0.01,
        max_position: float = 0.3
    ) -> Dict[str, float]:
        """Optimize portfolio allocation using mean-variance optimization.
        
        Args:
            subgraphs: Dictionary of subgraph data
            min_position: Minimum position size as fraction
            max_position: Maximum position size as fraction
            
        Returns:
            Dictionary of optimal weights by subgraph ID
        """
        n_assets = len(subgraphs)
        if n_assets == 0:
            return {}
            
        # Extract returns and risks
        returns = np.array([
            s.calculate_apr() / 100  # Convert APR to decimal
            for s in subgraphs.values()
        ])
        
        risks = np.array([
            s.get_risk_score() / 100  # Convert to decimal
            for s in subgraphs.values()
        ])
        
        # Create correlation matrix (simplified)
        corr_matrix = np.eye(n_assets)  # Assume independence
        
        # Define optimization constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
        ]
        
        bounds = [(min_position, max_position) for _ in range(n_assets)]
        
        # Define objective function (Sharpe ratio)
        def objective(weights):
            portfolio_return = np.sum(weights * returns)
            portfolio_risk = np.sqrt(
                np.dot(weights.T, np.dot(
                    np.diag(risks) @ corr_matrix @ np.diag(risks),
                    weights
                ))
            )
            return -(portfolio_return - self.risk_free_rate) / portfolio_risk

        # Initial guess (equal weights)
        initial_weights = np.array([1/n_assets] * n_assets)
        
        # Optimize
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        # Return results as dictionary
        return {
            s_id: float(w)
            for s_id, w in zip(subgraphs.keys(), result.x)
        }

    def get_rebalancing_trades(
        self,
        target_weights: Dict[str, float],
        min_trade_size: int = 100
    ) -> List[Tuple[str, int]]:
        """Calculate trades needed to reach target allocation.
        
        Args:
            target_weights: Target portfolio weights
            min_trade_size: Minimum trade size in GRT
            
        Returns:
            List of (subgraph_id, grt_amount) trades
        """
        current_weights = self.get_position_weights()
        total_value = self.get_total_value()
        
        trades = []
        for subgraph_id, target_weight in target_weights.items():
            current_weight = current_weights.get(subgraph_id, 0.0)
            
            # Calculate trade size
            target_value = total_value * target_weight
            current_value = total_value * current_weight
            trade_value = target_value - current_value
            
            # Skip small trades
            if abs(trade_value) < min_trade_size:
                continue
                
            trades.append((subgraph_id, int(trade_value)))
            
        return trades

    def calculate_impermanent_loss(
        self,
        initial_prices: Dict[str, float]
    ) -> float:
        """Calculate impermanent loss across portfolio.
        
        Args:
            initial_prices: Dictionary of initial GRT prices
            
        Returns:
            Impermanent loss as a percentage
        """
        total_il = 0.0
        total_value = 0.0
        
        for position in self.positions:
            if position.subgraph_id not in initial_prices:
                continue
                
            initial_price = initial_prices[position.subgraph_id]
            current_price = position.current_value / position.signal_amount
            
            # Calculate IL for position
            price_ratio = current_price / initial_price
            il = 2 * np.sqrt(price_ratio) / (1 + price_ratio) - 1
            
            # Weight by position size
            total_il += il * position.current_value
            total_value += position.current_value
            
        if total_value == 0:
            return 0.0
            
        return (total_il / total_value) * 100
