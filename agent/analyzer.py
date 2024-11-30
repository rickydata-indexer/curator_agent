"""
Analyzer component for data analysis and signal recommendations.
"""

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

from ..models.subgraph import Subgraph
from ..models.portfolio import Portfolio
from ..models.strategy import (
    CurationStrategy,
    APROptimizedStrategy,
    RiskMinimizedStrategy,
    SignalDecision
)
from ..api.graph_api import GraphAPI
from ..api.metrics_api import MetricsAPI

class SignalAnalyzer:
    """Analyzes subgraph data and generates signal recommendations."""
    
    def __init__(
        self,
        graph_api: GraphAPI,
        metrics_api: MetricsAPI,
        strategy: Optional[CurationStrategy] = None
    ):
        """Initialize analyzer.
        
        Args:
            graph_api: Graph API client
            metrics_api: Metrics API client
            strategy: Curation strategy to use
        """
        self.graph_api = graph_api
        self.metrics_api = metrics_api
        self.strategy = strategy or APROptimizedStrategy()
        self.logger = logging.getLogger(__name__)

    async def analyze_opportunities(
        self,
        portfolio: Portfolio,
        available_grt: int,
        min_query_fees: float = 100.0,
        days_history: int = 30
    ) -> List[SignalDecision]:
        """Analyze opportunities and generate recommendations.
        
        Args:
            portfolio: Current portfolio
            available_grt: Available GRT for allocation
            min_query_fees: Minimum query fees threshold
            days_history: Days of historical data to analyze
            
        Returns:
            List of signal decisions
        """
        try:
            # Get top subgraphs by query fees
            top_subgraphs = self.graph_api.get_top_subgraphs(first=100)
            
            # Filter by minimum query fees
            filtered_subgraphs = [
                s for s in top_subgraphs
                if float(s['currentVersion']['subgraphDeployment']['queryFeesAmount']) >= min_query_fees
            ]
            
            # Get detailed metrics for filtered subgraphs
            subgraph_data = {}
            network_metrics = {}
            
            for subgraph in filtered_subgraphs:
                try:
                    # Get detailed subgraph data
                    details = self.graph_api.get_subgraph_by_id(subgraph['id'])
                    
                    # Get performance metrics
                    metrics = self.metrics_api.calculate_subgraph_metrics(
                        subgraph['currentVersion']['subgraphDeployment']['id'],
                        days_history
                    )
                    
                    # Create Subgraph instance
                    subgraph_data[subgraph['id']] = Subgraph.from_graph_data(
                        details,
                        metrics
                    )
                    
                except Exception as e:
                    self.logger.warning(
                        f"Error processing subgraph {subgraph['id']}: {str(e)}"
                    )
                    continue
            
            # Get network metrics
            try:
                network_metrics = self.metrics_api.get_network_metrics(days_history)
            except Exception as e:
                self.logger.error(f"Error fetching network metrics: {str(e)}")
                network_metrics = {}
            
            # Generate decisions using strategy
            decisions = self.strategy.generate_decisions(
                portfolio,
                subgraph_data,
                network_metrics,
                available_grt
            )
            
            # Sort decisions by priority and confidence
            decisions.sort(
                key=lambda x: (x.priority, -x.confidence)
            )
            
            return decisions
            
        except Exception as e:
            self.logger.error(f"Error in opportunity analysis: {str(e)}")
            return []

    def analyze_portfolio_health(
        self,
        portfolio: Portfolio,
        subgraphs: Dict[str, Subgraph]
    ) -> Dict[str, float]:
        """Analyze current portfolio health.
        
        Args:
            portfolio: Current portfolio
            subgraphs: Dictionary of subgraph data
            
        Returns:
            Dictionary of health metrics
        """
        try:
            # Get portfolio metrics
            metrics = portfolio.calculate_portfolio_metrics(subgraphs)
            
            # Calculate additional health metrics
            total_positions = len(portfolio.positions)
            active_positions = sum(
                1 for p in portfolio.positions
                if p.subgraph_id in subgraphs
            )
            
            avg_position_size = (
                portfolio.get_total_value() / total_positions
                if total_positions > 0 else 0
            )
            
            # Calculate concentration risk
            weights = portfolio.get_position_weights()
            max_weight = max(weights.values()) if weights else 0
            
            return {
                'total_value': portfolio.get_total_value(),
                'weighted_apr': metrics['weighted_apr'],
                'weighted_risk': metrics['weighted_risk'],
                'diversification_score': metrics['diversification_score'],
                'total_positions': total_positions,
                'active_positions': active_positions,
                'avg_position_size': avg_position_size,
                'max_position_weight': max_weight
            }
            
        except Exception as e:
            self.logger.error(f"Error in portfolio health analysis: {str(e)}")
            return {}

    def get_rebalancing_recommendations(
        self,
        portfolio: Portfolio,
        subgraphs: Dict[str, Subgraph],
        max_trades: int = 5
    ) -> List[Tuple[str, int]]:
        """Get recommendations for portfolio rebalancing.
        
        Args:
            portfolio: Current portfolio
            subgraphs: Dictionary of subgraph data
            max_trades: Maximum number of trades to recommend
            
        Returns:
            List of (subgraph_id, amount) trade recommendations
        """
        try:
            # Optimize allocation
            target_weights = portfolio.optimize_allocation(
                subgraphs,
                min_position=0.05,
                max_position=0.3
            )
            
            # Get required trades
            trades = portfolio.get_rebalancing_trades(
                target_weights,
                min_trade_size=1000
            )
            
            # Sort trades by absolute size
            trades.sort(key=lambda x: abs(x[1]), reverse=True)
            
            # Return top trades
            return trades[:max_trades]
            
        except Exception as e:
            self.logger.error(f"Error generating rebalancing recommendations: {str(e)}")
            return []

    def get_risk_alerts(
        self,
        portfolio: Portfolio,
        subgraphs: Dict[str, Subgraph]
    ) -> List[str]:
        """Generate risk alerts for the portfolio.
        
        Args:
            portfolio: Current portfolio
            subgraphs: Dictionary of subgraph data
            
        Returns:
            List of risk alert messages
        """
        alerts = []
        try:
            metrics = self.analyze_portfolio_health(portfolio, subgraphs)
            
            # Check concentration risk
            if metrics.get('max_position_weight', 0) > 0.3:
                alerts.append(
                    "High concentration risk: Position exceeds 30% of portfolio"
                )
            
            # Check diversification
            if metrics.get('diversification_score', 1) < 0.5:
                alerts.append(
                    "Low diversification: Portfolio highly concentrated"
                )
            
            # Check position count
            if metrics.get('active_positions', 0) < 5:
                alerts.append(
                    "Low position count: Less than 5 active positions"
                )
            
            # Check weighted APR
            if metrics.get('weighted_apr', 0) < self.strategy.min_apr:
                alerts.append(
                    f"Low APR: Portfolio APR below minimum threshold of {self.strategy.min_apr}%"
                )
            
            # Check weighted risk
            if metrics.get('weighted_risk', 0) > self.strategy.max_risk_score:
                alerts.append(
                    f"High risk: Portfolio risk score above maximum threshold of {self.strategy.max_risk_score}"
                )
            
        except Exception as e:
            self.logger.error(f"Error generating risk alerts: {str(e)}")
            alerts.append(f"Error in risk analysis: {str(e)}")
            
        return alerts
