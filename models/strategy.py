"""
Models for curation strategies and decision-making logic.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

from .subgraph import Subgraph
from .portfolio import Portfolio, SignalPosition
from .metrics import MetricsAnalyzer

class SignalAction(Enum):
    """Possible signal actions."""
    ADD = "add"
    REMOVE = "remove"
    HOLD = "hold"

@dataclass
class SignalDecision:
    """Represents a signal allocation decision."""
    
    subgraph_id: str
    action: SignalAction
    amount: int
    reason: str
    confidence: float
    priority: int

class CurationStrategy:
    """Base class for curation strategies."""
    
    def __init__(
        self,
        min_apr: float = 10.0,
        max_risk_score: float = 70.0,
        min_position_size: int = 1000,
        max_position_size: int = 100000
    ):
        """Initialize strategy.
        
        Args:
            min_apr: Minimum acceptable APR
            max_risk_score: Maximum acceptable risk score
            min_position_size: Minimum position size in GRT
            max_position_size: Maximum position size in GRT
        """
        self.min_apr = min_apr
        self.max_risk_score = max_risk_score
        self.min_position_size = min_position_size
        self.max_position_size = max_position_size
        self.metrics_analyzer = MetricsAnalyzer()

    def evaluate_subgraph(
        self,
        subgraph: Subgraph,
        network_metrics: Dict
    ) -> Tuple[bool, float, str]:
        """Evaluate if a subgraph meets strategy criteria.
        
        Args:
            subgraph: Subgraph to evaluate
            network_metrics: Current network metrics
            
        Returns:
            Tuple of (meets_criteria, confidence, reason)
        """
        apr = subgraph.calculate_apr()
        risk_score = subgraph.get_risk_score()
        
        if apr < self.min_apr:
            return (False, 0.0, f"APR {apr:.1f}% below minimum {self.min_apr}%")
            
        if risk_score > self.max_risk_score:
            return (False, 0.0, f"Risk score {risk_score:.1f} above maximum {self.max_risk_score}")
            
        # Calculate confidence based on metrics
        confidence = self._calculate_confidence(subgraph, network_metrics)
        
        return (True, confidence, "Meets strategy criteria")

    def _calculate_confidence(
        self,
        subgraph: Subgraph,
        network_metrics: Dict
    ) -> float:
        """Calculate confidence score for a subgraph.
        
        Args:
            subgraph: Subgraph to evaluate
            network_metrics: Current network metrics
            
        Returns:
            Confidence score from 0 to 1
        """
        # Factors that increase confidence
        positive_factors = [
            subgraph.fee_growth_rate > 0,
            subgraph.signal_growth_rate > 0,
            subgraph.network_correlation > 0.5,
            subgraph.fee_volatility < 0.5
        ]
        
        # Weight the factors
        weights = [0.3, 0.2, 0.3, 0.2]
        
        return sum(f * w for f, w in zip(positive_factors, weights))

class APROptimizedStrategy(CurationStrategy):
    """Strategy focused on maximizing APR with risk constraints."""
    
    def __init__(
        self,
        min_apr: float = 15.0,
        max_risk_score: float = 60.0,
        min_position_size: int = 1000,
        max_position_size: int = 100000,
        target_positions: int = 10
    ):
        """Initialize APR-optimized strategy.
        
        Args:
            min_apr: Minimum acceptable APR
            max_risk_score: Maximum acceptable risk score
            min_position_size: Minimum position size in GRT
            max_position_size: Maximum position size in GRT
            target_positions: Target number of positions
        """
        super().__init__(min_apr, max_risk_score, min_position_size, max_position_size)
        self.target_positions = target_positions

    def generate_decisions(
        self,
        portfolio: Portfolio,
        subgraphs: Dict[str, Subgraph],
        network_metrics: Dict,
        available_grt: int
    ) -> List[SignalDecision]:
        """Generate signal allocation decisions.
        
        Args:
            portfolio: Current portfolio
            subgraphs: Available subgraphs
            network_metrics: Current network metrics
            available_grt: Available GRT for allocation
            
        Returns:
            List of signal decisions
        """
        decisions = []
        current_positions = len(portfolio.positions)
        
        # Evaluate existing positions
        for position in portfolio.positions:
            if position.subgraph_id not in subgraphs:
                continue
                
            subgraph = subgraphs[position.subgraph_id]
            meets_criteria, confidence, reason = self.evaluate_subgraph(
                subgraph,
                network_metrics
            )
            
            if not meets_criteria:
                decisions.append(SignalDecision(
                    subgraph_id=position.subgraph_id,
                    action=SignalAction.REMOVE,
                    amount=position.signalled_tokens,
                    reason=reason,
                    confidence=confidence,
                    priority=1  # High priority for removing poor performers
                ))
        
        # Find new opportunities
        if current_positions < self.target_positions:
            opportunities = []
            for s_id, subgraph in subgraphs.items():
                # Skip existing positions
                if any(p.subgraph_id == s_id for p in portfolio.positions):
                    continue
                    
                meets_criteria, confidence, reason = self.evaluate_subgraph(
                    subgraph,
                    network_metrics
                )
                
                if meets_criteria:
                    opportunities.append((subgraph, confidence, reason))
            
            # Sort opportunities by APR
            opportunities.sort(
                key=lambda x: x[0].calculate_apr(),
                reverse=True
            )
            
            # Generate add decisions
            positions_to_add = self.target_positions - current_positions
            for subgraph, confidence, reason in opportunities[:positions_to_add]:
                # Calculate position size based on APR weight
                total_apr = sum(s.calculate_apr() for s, _, _ in opportunities[:positions_to_add])
                weight = subgraph.calculate_apr() / total_apr if total_apr > 0 else 1.0
                amount = int(available_grt * weight)
                
                # Enforce size limits
                amount = max(self.min_position_size, min(amount, self.max_position_size))
                
                decisions.append(SignalDecision(
                    subgraph_id=subgraph.id,
                    action=SignalAction.ADD,
                    amount=amount,
                    reason=f"New opportunity: {reason}",
                    confidence=confidence,
                    priority=2  # Medium priority for new positions
                ))
        
        return decisions

class RiskMinimizedStrategy(CurationStrategy):
    """Strategy focused on minimizing risk while maintaining acceptable returns."""
    
    def __init__(
        self,
        min_apr: float = 10.0,
        max_risk_score: float = 50.0,
        min_position_size: int = 1000,
        max_position_size: int = 50000,
        max_correlation: float = 0.7
    ):
        """Initialize risk-minimized strategy.
        
        Args:
            min_apr: Minimum acceptable APR
            max_risk_score: Maximum acceptable risk score
            min_position_size: Minimum position size in GRT
            max_position_size: Maximum position size in GRT
            max_correlation: Maximum correlation between positions
        """
        super().__init__(min_apr, max_risk_score, min_position_size, max_position_size)
        self.max_correlation = max_correlation

    def generate_decisions(
        self,
        portfolio: Portfolio,
        subgraphs: Dict[str, Subgraph],
        network_metrics: Dict,
        available_grt: int
    ) -> List[SignalDecision]:
        """Generate signal allocation decisions.
        
        Args:
            portfolio: Current portfolio
            subgraphs: Available subgraphs
            network_metrics: Current network metrics
            available_grt: Available GRT for allocation
            
        Returns:
            List of signal decisions
        """
        decisions = []
        
        # Calculate portfolio risk metrics
        portfolio_metrics = portfolio.calculate_portfolio_metrics(subgraphs)
        
        # Evaluate existing positions
        for position in portfolio.positions:
            if position.subgraph_id not in subgraphs:
                continue
                
            subgraph = subgraphs[position.subgraph_id]
            
            # Check correlation with other positions
            correlations = []
            for other_pos in portfolio.positions:
                if other_pos.subgraph_id == position.subgraph_id:
                    continue
                    
                if other_pos.subgraph_id in subgraphs:
                    other_subgraph = subgraphs[other_pos.subgraph_id]
                    corr = self.metrics_analyzer.calculate_correlation(
                        [subgraph.avg_daily_fees],
                        [other_subgraph.avg_daily_fees]
                    )
                    correlations.append(abs(corr))
            
            avg_correlation = np.mean(correlations) if correlations else 0
            
            if avg_correlation > self.max_correlation:
                decisions.append(SignalDecision(
                    subgraph_id=position.subgraph_id,
                    action=SignalAction.REMOVE,
                    amount=position.signalled_tokens,
                    reason=f"High correlation ({avg_correlation:.2f})",
                    confidence=0.8,
                    priority=1
                ))
                continue
            
            # Standard evaluation
            meets_criteria, confidence, reason = self.evaluate_subgraph(
                subgraph,
                network_metrics
            )
            
            if not meets_criteria:
                decisions.append(SignalDecision(
                    subgraph_id=position.subgraph_id,
                    action=SignalAction.REMOVE,
                    amount=position.signalled_tokens,
                    reason=reason,
                    confidence=confidence,
                    priority=1
                ))
        
        # Find decorrelated opportunities
        if available_grt >= self.min_position_size:
            opportunities = []
            for s_id, subgraph in subgraphs.items():
                # Skip existing positions
                if any(p.subgraph_id == s_id for p in portfolio.positions):
                    continue
                    
                meets_criteria, confidence, reason = self.evaluate_subgraph(
                    subgraph,
                    network_metrics
                )
                
                if meets_criteria:
                    # Check correlation with current portfolio
                    correlations = []
                    for position in portfolio.positions:
                        if position.subgraph_id in subgraphs:
                            pos_subgraph = subgraphs[position.subgraph_id]
                            corr = self.metrics_analyzer.calculate_correlation(
                                [subgraph.avg_daily_fees],
                                [pos_subgraph.avg_daily_fees]
                            )
                            correlations.append(abs(corr))
                    
                    avg_correlation = np.mean(correlations) if correlations else 0
                    
                    if avg_correlation <= self.max_correlation:
                        opportunities.append((
                            subgraph,
                            confidence,
                            reason,
                            avg_correlation
                        ))
            
            # Sort opportunities by risk-adjusted return
            opportunities.sort(
                key=lambda x: x[0].calculate_apr() * (1 - x[3]),
                reverse=True
            )
            
            # Add best opportunity
            if opportunities:
                subgraph, confidence, reason, correlation = opportunities[0]
                amount = min(available_grt, self.max_position_size)
                
                decisions.append(SignalDecision(
                    subgraph_id=subgraph.id,
                    action=SignalAction.ADD,
                    amount=amount,
                    reason=f"Low correlation opportunity ({correlation:.2f}): {reason}",
                    confidence=confidence,
                    priority=2
                ))
        
        return decisions
