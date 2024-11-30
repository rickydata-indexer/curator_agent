"""
Monitor component for portfolio monitoring and performance tracking.
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import json
import os
import asyncio

from ..models.portfolio import Portfolio, SignalPosition
from ..models.subgraph import Subgraph
from ..api.graph_api import GraphAPI
from ..api.metrics_api import MetricsAPI

class PortfolioMonitor:
    """Monitors portfolio performance and tracks metrics."""
    
    def __init__(
        self,
        graph_api: GraphAPI,
        metrics_api: MetricsAPI,
        state_file: str = "portfolio_state.json",
        check_interval: int = 3600  # 1 hour
    ):
        """Initialize monitor.
        
        Args:
            graph_api: Graph API client
            metrics_api: Metrics API client
            state_file: File to store portfolio state
            check_interval: Interval between checks in seconds
        """
        self.graph_api = graph_api
        self.metrics_api = metrics_api
        self.state_file = state_file
        self.check_interval = check_interval
        self.logger = logging.getLogger(__name__)
        
        # Initialize state
        self.portfolio_history = []
        self.performance_metrics = {}
        self.last_check = None
        
        # Load existing state
        self._load_state()

    async def start_monitoring(self):
        """Start continuous portfolio monitoring."""
        while True:
            try:
                await self.check_portfolio()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying

    async def check_portfolio(self) -> Dict:
        """Check current portfolio status.
        
        Returns:
            Dictionary of current portfolio metrics
        """
        try:
            # Get curator signals
            curator_address = self.graph_api.arbitrum_api.account.address
            signals = self.graph_api.get_curator_signals(curator_address)
            
            # Build current portfolio
            positions = []
            for signal in signals:
                deployment = signal['subgraphDeployment']
                
                position = SignalPosition(
                    subgraph_id=deployment['id'],
                    deployment_id=deployment['id'],
                    signalled_tokens=int(signal['signalledTokens']),
                    signal_amount=int(deployment['signalAmount']),
                    entry_date=signal.get('createdAt', ''),
                    avg_entry_price=0.0,  # Calculate from historical data
                    current_value=float(deployment['signalAmount']),
                    accrued_fees=float(deployment['queryFeesAmount'])
                )
                positions.append(position)
            
            # Create portfolio instance
            portfolio = Portfolio(
                positions=positions,
                total_grt=sum(p.signalled_tokens for p in positions)
            )
            
            # Calculate current metrics
            current_metrics = self._calculate_metrics(portfolio)
            
            # Update history
            self.portfolio_history.append({
                'timestamp': datetime.now().isoformat(),
                'metrics': current_metrics
            })
            
            # Trim history to last 90 days
            cutoff = datetime.now() - timedelta(days=90)
            self.portfolio_history = [
                h for h in self.portfolio_history
                if datetime.fromisoformat(h['timestamp']) > cutoff
            ]
            
            # Update performance metrics
            self._update_performance_metrics()
            
            # Save state
            self._save_state()
            
            return current_metrics
            
        except Exception as e:
            self.logger.error(f"Error checking portfolio: {str(e)}")
            return {}

    def get_performance_report(
        self,
        days: int = 30
    ) -> Dict:
        """Generate performance report.
        
        Args:
            days: Number of days to include in report
            
        Returns:
            Performance report dictionary
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            # Filter history
            relevant_history = [
                h for h in self.portfolio_history
                if datetime.fromisoformat(h['timestamp']) > cutoff
            ]
            
            if not relevant_history:
                return {}
            
            # Calculate period metrics
            start_metrics = relevant_history[0]['metrics']
            end_metrics = relevant_history[-1]['metrics']
            
            # Calculate returns
            value_return = (
                (end_metrics['total_value'] - start_metrics['total_value'])
                / start_metrics['total_value']
                if start_metrics['total_value'] > 0 else 0
            )
            
            # Calculate additional metrics
            avg_apr = sum(
                h['metrics'].get('weighted_apr', 0)
                for h in relevant_history
            ) / len(relevant_history)
            
            max_drawdown = self._calculate_max_drawdown(
                [h['metrics']['total_value'] for h in relevant_history]
            )
            
            return {
                'period_days': days,
                'start_date': relevant_history[0]['timestamp'],
                'end_date': relevant_history[-1]['timestamp'],
                'total_return': value_return * 100,
                'avg_apr': avg_apr,
                'max_drawdown': max_drawdown * 100,
                'current_metrics': end_metrics,
                'performance_metrics': self.performance_metrics
            }
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {str(e)}")
            return {}

    def get_position_history(
        self,
        subgraph_id: str,
        days: int = 30
    ) -> List[Dict]:
        """Get historical data for a specific position.
        
        Args:
            subgraph_id: Subgraph ID to get history for
            days: Number of days of history
            
        Returns:
            List of historical position data
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            position_history = []
            for h in self.portfolio_history:
                timestamp = datetime.fromisoformat(h['timestamp'])
                if timestamp <= cutoff:
                    continue
                    
                # Find position in historical snapshot
                for pos in h['metrics'].get('positions', []):
                    if pos['subgraph_id'] == subgraph_id:
                        position_history.append({
                            'timestamp': h['timestamp'],
                            'signalled_tokens': pos['signalled_tokens'],
                            'current_value': pos['current_value'],
                            'accrued_fees': pos['accrued_fees']
                        })
                        break
            
            return position_history
            
        except Exception as e:
            self.logger.error(
                f"Error getting position history for {subgraph_id}: {str(e)}"
            )
            return []

    def _calculate_metrics(self, portfolio: Portfolio) -> Dict:
        """Calculate current portfolio metrics.
        
        Args:
            portfolio: Current portfolio
            
        Returns:
            Dictionary of calculated metrics
        """
        metrics = {
            'total_value': portfolio.get_total_value(),
            'total_positions': len(portfolio.positions),
            'positions': []
        }
        
        # Add position details
        for position in portfolio.positions:
            metrics['positions'].append({
                'subgraph_id': position.subgraph_id,
                'signalled_tokens': position.signalled_tokens,
                'current_value': position.current_value,
                'accrued_fees': position.accrued_fees
            })
        
        return metrics

    def _update_performance_metrics(self):
        """Update rolling performance metrics."""
        try:
            if len(self.portfolio_history) < 2:
                return
            
            values = [h['metrics']['total_value'] for h in self.portfolio_history]
            
            # Calculate returns
            returns = [
                (values[i] - values[i-1]) / values[i-1]
                for i in range(1, len(values))
            ]
            
            # Calculate metrics
            self.performance_metrics = {
                'total_return': (values[-1] - values[0]) / values[0] * 100,
                'volatility': np.std(returns) * np.sqrt(365) * 100,
                'sharpe_ratio': self._calculate_sharpe_ratio(returns),
                'max_drawdown': self._calculate_max_drawdown(values) * 100
            }
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {str(e)}")

    def _calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02
    ) -> float:
        """Calculate Sharpe ratio.
        
        Args:
            returns: List of return values
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Calculated Sharpe ratio
        """
        if not returns:
            return 0.0
            
        excess_returns = [r - (risk_free_rate/365) for r in returns]
        if not excess_returns:
            return 0.0
            
        avg_excess_return = np.mean(excess_returns)
        return_std = np.std(excess_returns)
        
        if return_std == 0:
            return 0.0
            
        return (avg_excess_return / return_std) * np.sqrt(365)

    def _calculate_max_drawdown(self, values: List[float]) -> float:
        """Calculate maximum drawdown.
        
        Args:
            values: List of portfolio values
            
        Returns:
            Maximum drawdown as decimal
        """
        if not values:
            return 0.0
            
        peak = values[0]
        max_dd = 0.0
        
        for value in values[1:]:
            if value > peak:
                peak = value
            else:
                dd = (peak - value) / peak
                max_dd = max(max_dd, dd)
        
        return max_dd

    def _save_state(self):
        """Save current state to file."""
        try:
            state = {
                'portfolio_history': self.portfolio_history,
                'performance_metrics': self.performance_metrics,
                'last_check': datetime.now().isoformat()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
                
        except Exception as e:
            self.logger.error(f"Error saving state: {str(e)}")

    def _load_state(self):
        """Load state from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    
                self.portfolio_history = state.get('portfolio_history', [])
                self.performance_metrics = state.get('performance_metrics', {})
                last_check = state.get('last_check')
                if last_check:
                    self.last_check = datetime.fromisoformat(last_check)
                    
        except Exception as e:
            self.logger.error(f"Error loading state: {str(e)}")
