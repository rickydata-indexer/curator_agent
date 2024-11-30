"""
Arbitrum contract interactions for The Graph Network.
Handles curation signal transactions and contract calls.
"""

from typing import Dict, Optional
from web3 import Web3
from eth_typing import Address
from web3.contract import Contract
import json

class ArbitrumAPI:
    """Handles interactions with The Graph contracts on Arbitrum."""
    
    # Contract ABIs - Minimal versions for required functions
    ABIS = {
        'L2GraphToken': [
            {
                "inputs": [
                    {"name": "spender", "type": "address"},
                    {"name": "amount", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "account", "type": "address"}
                ],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ],
        'L2Curation': [
            {
                "inputs": [
                    {"name": "subgraphDeploymentID", "type": "bytes32"},
                    {"name": "tokens", "type": "uint256"},
                    {"name": "signalOutMin", "type": "uint256"}
                ],
                "name": "mint",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "subgraphDeploymentID", "type": "bytes32"},
                    {"name": "signal", "type": "uint256"},
                    {"name": "tokensOutMin", "type": "uint256"}
                ],
                "name": "burn",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
    }

    def __init__(
        self,
        web3_provider: str,
        private_key: Optional[str] = None
    ):
        """Initialize the Arbitrum API client.
        
        Args:
            web3_provider: Arbitrum RPC endpoint
            private_key: Optional private key for signing transactions
        """
        self.w3 = Web3(Web3.HTTPProvider(web3_provider))
        
        if private_key:
            self.account = self.w3.eth.account.from_key(private_key)
        else:
            self.account = None
            
        # Contract addresses
        self.contracts = {
            'L2GraphToken': '0x9623063377AD1B27544C965cCd7342f7EA7e88C7',
            'L2Curation': '0x22d78fb4bc72e191C765807f8891B5e1785C8014',
            'L2GNS': '0xec9A7fb6CbC2E41926127929c2dcE6e9c5D33Bec',
            'SubgraphNFT': '0x3FbD54f0cc17b7aE649008dEEA12ed7D2622B23f'
        }
        
        # Initialize contract instances
        self.token_contract = self._get_contract('L2GraphToken')
        self.curation_contract = self._get_contract('L2Curation')

    def add_curation_signal(
        self,
        subgraph_deployment_id: str,
        tokens: int,
        min_signal: int = 0
    ) -> Dict:
        """Add curation signal to a subgraph deployment.
        
        Args:
            subgraph_deployment_id: Deployment ID to signal on
            tokens: Amount of GRT tokens to signal
            min_signal: Minimum signal to receive (slippage protection)
            
        Returns:
            Transaction receipt
        """
        if not self.account:
            raise ValueError("Private key required for transactions")
            
        # Approve tokens first
        approve_tx = self._approve_tokens(self.contracts['L2Curation'], tokens)
        self.w3.eth.wait_for_transaction_receipt(approve_tx)
        
        # Build mint transaction
        deployment_bytes = bytes.fromhex(subgraph_deployment_id)
        tx = self.curation_contract.functions.mint(
            deployment_bytes,
            tokens,
            min_signal
        ).build_transaction({
            'from': self.account.address,
            'gas': 500000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        
        # Sign and send transaction
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)

    def remove_curation_signal(
        self,
        subgraph_deployment_id: str,
        signal: int,
        min_tokens: int = 0
    ) -> Dict:
        """Remove curation signal from a subgraph deployment.
        
        Args:
            subgraph_deployment_id: Deployment ID to remove signal from
            signal: Amount of signal to burn
            min_tokens: Minimum tokens to receive (slippage protection)
            
        Returns:
            Transaction receipt
        """
        if not self.account:
            raise ValueError("Private key required for transactions")
            
        # Build burn transaction
        deployment_bytes = bytes.fromhex(subgraph_deployment_id)
        tx = self.curation_contract.functions.burn(
            deployment_bytes,
            signal,
            min_tokens
        ).build_transaction({
            'from': self.account.address,
            'gas': 500000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        
        # Sign and send transaction
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)

    def get_grt_balance(self, address: Optional[str] = None) -> int:
        """Get GRT token balance for an address.
        
        Args:
            address: Address to check balance for, defaults to account address
            
        Returns:
            Balance in wei
        """
        if not address and not self.account:
            raise ValueError("No address provided")
            
        check_address = address or self.account.address
        return self.token_contract.functions.balanceOf(check_address).call()

    def _approve_tokens(self, spender: str, amount: int) -> str:
        """Approve tokens for contract interaction.
        
        Args:
            spender: Contract address to approve
            amount: Amount of tokens to approve
            
        Returns:
            Transaction hash
        """
        tx = self.token_contract.functions.approve(
            spender,
            amount
        ).build_transaction({
            'from': self.account.address,
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        
        signed_tx = self.account.sign_transaction(tx)
        return self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    def _get_contract(self, name: str) -> Contract:
        """Get Web3 contract instance.
        
        Args:
            name: Contract name
            
        Returns:
            Web3 Contract instance
        """
        address = self.contracts[name]
        abi = self.ABIS[name]
        return self.w3.eth.contract(address=address, abi=abi)
