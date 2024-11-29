import os
from web3 import Web3
from dotenv import load_dotenv
from decimal import Decimal

# Load environment variables
load_dotenv()

def get_token_balance(w3: Web3, token_address: str, wallet_address: str) -> float:
    """Get GRT token balance."""
    try:
        # Create contract instance with minimal ABI for ERC20
        contract = w3.eth.contract(
            address=w3.to_checksum_address(token_address),
            abi=[{
                "constant": True,
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }]
        )
        
        # Get balance
        balance = contract.functions.balanceOf(wallet_address).call()
        return float(w3.from_wei(balance, 'ether'))
    except Exception as e:
        raise Exception(f"Failed to get token balance: {str(e)}")

def approve_grt(w3: Web3, from_address: str, private_key: str, spender: str, amount_in_grt: float) -> str:
    """Approve GRT spending."""
    try:
        # L2GraphToken contract on Arbitrum
        grt_token = w3.to_checksum_address("0x9623063377AD1B27544C965cCd7342f7EA7e88C7")
        
        # Create contract instance with minimal ABI for ERC20
        contract = w3.eth.contract(
            address=grt_token,
            abi=[{
                "inputs": [
                    {"name": "spender", "type": "address"},
                    {"name": "amount", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
        )
        
        # Build transaction
        transaction = contract.functions.approve(
            w3.to_checksum_address(spender),
            w3.to_wei(amount_in_grt, 'ether')  # GRT uses 18 decimals like ETH
        ).build_transaction({
            'from': from_address,
            'gas': 300000,
            'maxFeePerGas': w3.eth.gas_price,  # For EIP-1559
            'maxPriorityFeePerGas': w3.eth.gas_price,  # For EIP-1559
            'nonce': w3.eth.get_transaction_count(from_address),
            'chainId': w3.eth.chain_id,
        })

        # Sign and send the transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_receipt['transactionHash'].hex()
    except Exception as e:
        raise Exception(f"Approval failed: {str(e)}")

def mint_signal(w3: Web3, from_address: str, private_key: str, subgraph_id: int, amount_in_grt: float) -> str:
    """Mint signal for a subgraph."""
    try:
        # L2GNS contract address on Arbitrum
        gns_contract = w3.to_checksum_address("0xec9A7fb6CbC2E41926127929c2dcE6e9c5D33Bec")
        
        # Create contract instance with minimal ABI
        contract = w3.eth.contract(
            address=gns_contract,
            abi=[{
                "inputs": [
                    {"name": "_subgraphID", "type": "uint256"},
                    {"name": "_tokensIn", "type": "uint256"},
                    {"name": "_nSignalOutMin", "type": "uint256"}
                ],
                "name": "mintSignal",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }]
        )
        
        # Build transaction
        transaction = contract.functions.mintSignal(
            subgraph_id,
            w3.to_wei(amount_in_grt, 'ether'),  # GRT uses 18 decimals
            0  # _nSignalOutMin - set to 0 for simplicity
        ).build_transaction({
            'from': from_address,
            'gas': 500000,
            'maxFeePerGas': w3.eth.gas_price,  # For EIP-1559
            'maxPriorityFeePerGas': w3.eth.gas_price,  # For EIP-1559
            'nonce': w3.eth.get_transaction_count(from_address),
            'chainId': w3.eth.chain_id,
        })

        # Sign and send the transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_receipt['transactionHash'].hex()
    except Exception as e:
        raise Exception(f"Signaling failed: {str(e)}")

def main():
    # Connect to Arbitrum network
    infura_project_id = os.getenv('INFURA_API_KEY')
    w3 = Web3(Web3.HTTPProvider(f'https://arbitrum-mainnet.infura.io/v3/{infura_project_id}'))

    if not w3.is_connected():
        print("Error: Failed to connect to Arbitrum network")
        return

    # Get wallet addresses from environment
    wallet_one = os.getenv('AGENT_ONE_ADDRESS')
    wallet_one_key = os.getenv('AGENT_ONE_PRIVATE_KEY')
    
    print("\n=== GRT Signaling Tool ===\n")
    
    try:
        # Check ETH balance
        eth_balance = float(w3.from_wei(w3.eth.get_balance(wallet_one), 'ether'))
        print(f"ETH Balance on Arbitrum: {eth_balance:.6f} ETH")
        
        # Check GRT balance
        grt_token = "0x9623063377AD1B27544C965cCd7342f7EA7e88C7"
        grt_balance = get_token_balance(w3, grt_token, wallet_one)
        print(f"GRT Balance on Arbitrum: {grt_balance:.6f} GRT")
        
        # Verify sufficient balances
        if eth_balance == 0:
            print("\nError: No ETH available for gas fees on Arbitrum")
            print("Please bridge some ETH to Arbitrum first")
            return
            
        if grt_balance < 1:
            print("\nError: Insufficient GRT balance on Arbitrum")
            print("Please ensure you have at least 1 GRT on Arbitrum")
            return
        
        # Example subgraph ID (this should be replaced with the actual NFT ID)
        subgraph_id = 22327336881714476995743838527991275714210510246126052258699153536276712602530
        
        # Set signal amount
        signal_amount = 1  # 1 GRT
        
        # First approve GRT spending
        gns_contract = "0xec9A7fb6CbC2E41926127929c2dcE6e9c5D33Bec"
        print(f"\nApproving {signal_amount} GRT for signaling...")
        
        try:
            approve_tx = approve_grt(w3, wallet_one, wallet_one_key, gns_contract, signal_amount)
            print(f"Approval successful! Transaction hash: {approve_tx}")
            
            # Wait for a few blocks to ensure approval is processed
            print("\nWaiting for approval confirmation...")
            w3.eth.wait_for_transaction_receipt(approve_tx)
            
            # Now mint signal
            print(f"\nMinting signal with {signal_amount} GRT...")
            signal_tx = mint_signal(w3, wallet_one, wallet_one_key, subgraph_id, signal_amount)
            print("\nSignaling successful!")
            print(f"Transaction hash: {signal_tx}")
            
        except Exception as e:
            print(f"\nError during transaction: {str(e)}")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
