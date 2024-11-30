"""
Main entry point for the curator agent.
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from typing import Optional

from api.graph_api import GraphAPI
from api.metrics_api import MetricsAPI
from api.arbitrum_api import ArbitrumAPI
from models.strategy import APROptimizedStrategy, RiskMinimizedStrategy
from agent.analyzer import SignalAnalyzer
from agent.executor import SignalExecutor
from agent.monitor import PortfolioMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CuratorAgent:
    """Main curator agent class."""
    
    def __init__(
        self,
        strategy_type: str = "apr",
        min_apr: float = 15.0,
        max_risk_score: float = 60.0,
        check_interval: int = 3600,  # 1 hour
        max_slippage: float = 0.02,
        max_gas_price: int = 100  # gwei
    ):
        """Initialize curator agent.
        
        Args:
            strategy_type: Type of strategy to use ('apr' or 'risk')
            min_apr: Minimum acceptable APR
            max_risk_score: Maximum acceptable risk score
            check_interval: Interval between checks in seconds
            max_slippage: Maximum acceptable slippage
            max_gas_price: Maximum gas price in gwei
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize APIs
        self.graph_api = GraphAPI(
            web3_provider=os.getenv('ARBITRUM_RPC_URL'),
            api_key=os.getenv('GRAPH_API_KEY')
        )
        
        self.metrics_api = MetricsAPI(
            metrics_endpoint=os.getenv('METRICS_ENDPOINT')
        )
        
        self.arbitrum_api = ArbitrumAPI(
            web3_provider=os.getenv('ARBITRUM_RPC_URL'),
            private_key=os.getenv('PRIVATE_KEY')
        )
        
        # Initialize strategy
        if strategy_type == "risk":
            self.strategy = RiskMinimizedStrategy(
                min_apr=min_apr,
                max_risk_score=max_risk_score
            )
        else:
            self.strategy = APROptimizedStrategy(
                min_apr=min_apr,
                max_risk_score=max_risk_score
            )
        
        # Initialize components
        self.analyzer = SignalAnalyzer(
            self.graph_api,
            self.metrics_api,
            self.strategy
        )
        
        self.executor = SignalExecutor(
            self.arbitrum_api,
            self.graph_api,
            max_slippage=max_slippage,
            max_gas_price=max_gas_price
        )
        
        self.monitor = PortfolioMonitor(
            self.graph_api,
            self.metrics_api,
            check_interval=check_interval
        )
        
        self.check_interval = check_interval
        self.running = False

    async def start(self):
        """Start the curator agent."""
        try:
            self.running = True
            logger.info("Starting curator agent...")
            
            # Start monitoring task
            monitor_task = asyncio.create_task(
                self.monitor.start_monitoring()
            )
            
            # Main agent loop
            while self.running:
                try:
                    await self._process_cycle()
                except Exception as e:
                    logger.error(f"Error in agent cycle: {str(e)}")
                
                await asyncio.sleep(self.check_interval)
            
            # Clean up
            monitor_task.cancel()
            
        except Exception as e:
            logger.error(f"Error starting agent: {str(e)}")
            self.running = False

    def stop(self):
        """Stop the curator agent."""
        self.running = False
        logger.info("Stopping curator agent...")

    async def _process_cycle(self):
        """Process one agent cycle."""
        try:
            # Get current portfolio state
            portfolio_metrics = await self.monitor.check_portfolio()
            if not portfolio_metrics:
                logger.warning("Failed to get portfolio metrics")
                return
            
            # Check for pending transactions
            pending_txs = self.executor.get_pending_transactions()
            if pending_txs:
                logger.info(f"Waiting for {len(pending_txs)} pending transactions")
                return
            
            # Get available GRT
            available_grt = self.arbitrum_api.get_grt_balance()
            
            # Analyze opportunities
            decisions = await self.analyzer.analyze_opportunities(
                self.monitor.portfolio,
                available_grt
            )
            
            if not decisions:
                logger.info("No actions needed")
                return
            
            # Execute decisions
            results = await self.executor.execute_decisions(decisions)
            
            # Log results
            success_count = sum(1 for r in results.values() if r)
            logger.info(
                f"Executed {len(results)} decisions, {success_count} successful"
            )
            
            # Generate performance report
            report = self.monitor.get_performance_report()
            logger.info(f"Performance report: {report}")
            
            # Check for risk alerts
            alerts = self.analyzer.get_risk_alerts(
                self.monitor.portfolio,
                {}  # TODO: Pass current subgraph data
            )
            
            if alerts:
                logger.warning("Risk alerts detected:")
                for alert in alerts:
                    logger.warning(f"- {alert}")
            
        except Exception as e:
            logger.error(f"Error in processing cycle: {str(e)}")

def main():
    """Main entry point."""
    try:
        # Create agent instance
        agent = CuratorAgent(
            strategy_type=os.getenv('STRATEGY_TYPE', 'apr'),
            min_apr=float(os.getenv('MIN_APR', '15.0')),
            max_risk_score=float(os.getenv('MAX_RISK_SCORE', '60.0')),
            check_interval=int(os.getenv('CHECK_INTERVAL', '3600')),
            max_slippage=float(os.getenv('MAX_SLIPPAGE', '0.02')),
            max_gas_price=int(os.getenv('MAX_GAS_PRICE', '100'))
        )
        
        # Run agent
        asyncio.run(agent.start())
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
