"""
Executor component for transaction execution and signal management.
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime
import asyncio

from ..models.strategy import SignalDecision, SignalAction
from ..api.arbitrum_api import ArbitrumAPI
from ..api.graph_api import GraphAPI

class SignalExecutor:
    """Executes signal transactions and manages positions."""
    
    def __init__(
        self,
        arbitrum_api: ArbitrumAPI,
        graph_api: GraphAPI,
        max_slippage: float = 0.02,
        max_gas_price: int = 100,  # gwei
        confirmation_blocks: int = 2
    ):
        """Initialize executor.
        
        Args:
            arbitrum_api: Arbitrum API client
            graph_api: Graph API client
            max_slippage: Maximum acceptable slippage
            max_gas_price: Maximum gas price in gwei
            confirmation_blocks: Blocks to wait for confirmation
        """
        self.arbitrum_api = arbitrum_api
        self.graph_api = graph_api
        self.max_slippage = max_slippage
        self.max_gas_price = max_gas_price
        self.confirmation_blocks = confirmation_blocks
        self.logger = logging.getLogger(__name__)
        
        # Track pending transactions
        self.pending_txs = {}

    async def execute_decisions(
        self,
        decisions: List[SignalDecision]
    ) -> Dict[str, bool]:
        """Execute a list of signal decisions.
        
        Args:
            decisions: List of signal decisions to execute
            
        Returns:
            Dictionary of decision ID to success status
        """
        results = {}
        
        for decision in decisions:
            try:
                # Check gas price
                current_gas = self.arbitrum_api.w3.eth.gas_price
                if current_gas > self.max_gas_price * 10**9:
                    self.logger.warning(
                        f"Gas price {current_gas/10**9} gwei above maximum {self.max_gas_price}"
                    )
                    continue
                
                # Execute decision
                if decision.action == SignalAction.ADD:
                    success = await self._add_signal(
                        decision.subgraph_id,
                        decision.amount
                    )
                elif decision.action == SignalAction.REMOVE:
                    success = await self._remove_signal(
                        decision.subgraph_id,
                        decision.amount
                    )
                else:  # HOLD
                    success = True
                    
                results[decision.subgraph_id] = success
                
                if not success:
                    self.logger.error(
                        f"Failed to execute {decision.action.value} "
                        f"for {decision.subgraph_id}"
                    )
                    
                # Wait between transactions
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(
                    f"Error executing decision for {decision.subgraph_id}: {str(e)}"
                )
                results[decision.subgraph_id] = False
                
        return results

    async def _add_signal(
        self,
        subgraph_id: str,
        amount: int
    ) -> bool:
        """Add signal to a subgraph.
        
        Args:
            subgraph_id: Subgraph ID to signal on
            amount: Amount of tokens to signal
            
        Returns:
            Success status
        """
        try:
            # Get subgraph deployment ID
            subgraph = self.graph_api.get_subgraph_by_id(subgraph_id)
            if not subgraph or not subgraph.get('currentVersion'):
                raise ValueError("Invalid subgraph or no current version")
                
            deployment_id = subgraph['currentVersion']['subgraphDeployment']['id']
            
            # Calculate minimum signal with slippage protection
            min_signal = int(amount * (1 - self.max_slippage))
            
            # Execute transaction
            tx_receipt = self.arbitrum_api.add_curation_signal(
                deployment_id,
                amount,
                min_signal
            )
            
            # Track pending transaction
            tx_hash = tx_receipt['transactionHash'].hex()
            self.pending_txs[tx_hash] = {
                'type': 'add',
                'subgraph_id': subgraph_id,
                'amount': amount,
                'timestamp': datetime.now()
            }
            
            # Wait for confirmations
            await self._wait_for_confirmation(tx_hash)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding signal: {str(e)}")
            return False

    async def _remove_signal(
        self,
        subgraph_id: str,
        amount: int
    ) -> bool:
        """Remove signal from a subgraph.
        
        Args:
            subgraph_id: Subgraph ID to remove signal from
            amount: Amount of signal to remove
            
        Returns:
            Success status
        """
        try:
            # Get subgraph deployment ID
            subgraph = self.graph_api.get_subgraph_by_id(subgraph_id)
            if not subgraph or not subgraph.get('currentVersion'):
                raise ValueError("Invalid subgraph or no current version")
                
            deployment_id = subgraph['currentVersion']['subgraphDeployment']['id']
            
            # Calculate minimum tokens with slippage protection
            min_tokens = int(amount * (1 - self.max_slippage))
            
            # Execute transaction
            tx_receipt = self.arbitrum_api.remove_curation_signal(
                deployment_id,
                amount,
                min_tokens
            )
            
            # Track pending transaction
            tx_hash = tx_receipt['transactionHash'].hex()
            self.pending_txs[tx_hash] = {
                'type': 'remove',
                'subgraph_id': subgraph_id,
                'amount': amount,
                'timestamp': datetime.now()
            }
            
            # Wait for confirmations
            await self._wait_for_confirmation(tx_hash)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing signal: {str(e)}")
            return False

    async def _wait_for_confirmation(self, tx_hash: str) -> bool:
        """Wait for transaction confirmation.
        
        Args:
            tx_hash: Transaction hash to monitor
            
        Returns:
            Success status
        """
        try:
            # Get transaction receipt
            receipt = await self.arbitrum_api.w3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=300  # 5 minutes
            )
            
            # Check confirmations
            current_block = self.arbitrum_api.w3.eth.block_number
            conf_blocks = current_block - receipt['blockNumber']
            
            while conf_blocks < self.confirmation_blocks:
                await asyncio.sleep(1)
                current_block = self.arbitrum_api.w3.eth.block_number
                conf_blocks = current_block - receipt['blockNumber']
            
            # Remove from pending
            if tx_hash in self.pending_txs:
                del self.pending_txs[tx_hash]
            
            return receipt['status'] == 1
            
        except Exception as e:
            self.logger.error(f"Error waiting for confirmation: {str(e)}")
            return False

    def get_pending_transactions(self) -> Dict:
        """Get currently pending transactions.
        
        Returns:
            Dictionary of pending transactions
        """
        return self.pending_txs

    async def check_transaction_status(self, tx_hash: str) -> Optional[Dict]:
        """Check status of a specific transaction.
        
        Args:
            tx_hash: Transaction hash to check
            
        Returns:
            Transaction status information
        """
        try:
            receipt = await self.arbitrum_api.w3.eth.get_transaction_receipt(tx_hash)
            
            current_block = self.arbitrum_api.w3.eth.block_number
            confirmations = current_block - receipt['blockNumber']
            
            return {
                'status': 'success' if receipt['status'] == 1 else 'failed',
                'confirmations': confirmations,
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'effective_gas_price': receipt['effectiveGasPrice']
            }
            
        except Exception as e:
            self.logger.error(f"Error checking transaction status: {str(e)}")
            return None
