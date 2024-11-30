import os
from web3 import Web3
from dotenv import load_dotenv
from typing import Dict, List
import json
import time

# Import existing modules
from signal_grt import get_token_balance, approve_grt, mint_signal
from api.graph_api import get_subgraph_deployments, get_grt_price, get_user_curation_signal
from models.opportunities import calculate_opportunities, Opportunity
from models.signals import calculate_optimal_allocations

class AutomatedSignaler:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize Web3
        infura_project_id = os.getenv('INFURA_API_KEY')
        self.w3 = Web3(Web3.HTTPProvider(f'https://arbitrum-mainnet.infura.io/v3/{infura_project_id}'))
        
        if not self.w3.is_connected():
            raise Exception("Failed to connect to Arbitrum network")
            
        # Get wallet configuration
        self.wallet_address = os.getenv('AGENT_ONE_ADDRESS')
        self.private_key = os.getenv('AGENT_ONE_PRIVATE_KEY')
        
        if not all([self.wallet_address, self.private_key]):
            raise Exception("Missing wallet configuration in .env file")
            
        # Contract addresses
        self.grt_token = "0x9623063377AD1B27544C965cCd7342f7EA7e88C7"
        self.gns_contract = "0xec9A7fb6CbC2E41926127929c2dcE6e9c5D33Bec"

    def get_balances(self) -> tuple:
        """Get ETH and GRT balances."""
        eth_balance = float(self.w3.from_wei(self.w3.eth.get_balance(self.wallet_address), 'ether'))
        grt_balance = get_token_balance(self.w3, self.grt_token, self.wallet_address)
        return eth_balance, grt_balance

    def calculate_optimal_distribution(self, available_grt: float) -> Dict[str, float]:
        """Calculate optimal signal distribution based on available GRT."""
        # Get required data
        deployments = get_subgraph_deployments()
        
        # Extract query fees and counts from deployments
        query_fees = {}
        query_counts = {}
        for deployment in deployments:
            subgraph_id = deployment['ipfsHash']
            daily_fees = float(deployment.get('dailyQueryFees', 0)) / 1e18  # Convert from wei
            query_fees[subgraph_id] = daily_fees * 30  # Monthly fees
            # Estimate query count from fees (assuming average fee)
            estimated_queries = int(daily_fees * 25000)  # Rough estimate
            query_counts[subgraph_id] = estimated_queries * 30  # Monthly queries
        
        grt_price = get_grt_price()
        
        # Calculate opportunities
        opportunities = calculate_opportunities(deployments, query_fees, query_counts, grt_price)
        
        # Get current signals
        user_signals = get_user_curation_signal(self.wallet_address)
        
        # Calculate optimal allocations (targeting top 5 subgraphs)
        return calculate_optimal_allocations(
            opportunities=opportunities,
            user_signals=user_signals or {},
            total_signal=available_grt,
            grt_price=grt_price,
            num_subgraphs=5
        )

    def present_plan(self, allocations: Dict[str, float]) -> bool:
        """Present the signaling plan to the user and get confirmation."""
        print("\n=== Proposed Signaling Plan ===\n")
        
        total_grt = sum(allocations.values())
        print(f"Total GRT to be signaled: {total_grt:.2f} GRT\n")
        
        print("Allocations:")
        for subgraph_id, amount in allocations.items():
            print(f"\nSubgraph {subgraph_id}:")
            print(f"Amount to signal: {amount:.2f} GRT")
            
        while True:
            response = input("\nProceed with signaling? (yes/no): ").lower()
            if response in ['yes', 'no']:
                return response == 'yes'
            print("Please answer 'yes' or 'no'")

    def execute_signaling(self, allocations: Dict[str, float]):
        """Execute the signaling transactions."""
        for subgraph_id, amount in allocations.items():
            if amount <= 0:
                continue
                
            print(f"\nProcessing subgraph {subgraph_id}")
            print(f"Amount to signal: {amount:.2f} GRT")
            
            try:
                # Approve GRT spending
                print("Approving GRT...")
                approve_tx = approve_grt(
                    self.w3,
                    self.wallet_address,
                    self.private_key,
                    self.gns_contract,
                    amount
                )
                print(f"Approval transaction: {approve_tx}")
                
                # Wait for approval confirmation
                print("Waiting for approval confirmation...")
                self.w3.eth.wait_for_transaction_receipt(approve_tx)
                
                # Execute signaling
                print("Signaling GRT...")
                signal_tx = mint_signal(
                    self.w3,
                    self.wallet_address,
                    self.private_key,
                    int(subgraph_id),
                    amount
                )
                print(f"Signal transaction: {signal_tx}")
                
                # Wait between transactions
                time.sleep(5)
                
            except Exception as e:
                print(f"Error processing subgraph {subgraph_id}: {str(e)}")
                
                # Ask whether to continue with remaining transactions
                while True:
                    response = input("\nContinue with remaining transactions? (yes/no): ").lower()
                    if response == 'no':
                        return
                    elif response == 'yes':
                        break
                    print("Please answer 'yes' or 'no'")

def main():
    try:
        signaler = AutomatedSignaler()
        
        # Check balances
        eth_balance, grt_balance = signaler.get_balances()
        print("\n=== Current Balances ===")
        print(f"ETH Balance: {eth_balance:.6f} ETH")
        print(f"GRT Balance: {grt_balance:.6f} GRT")
        
        if eth_balance == 0:
            print("\nError: No ETH available for gas fees")
            return
            
        if grt_balance == 0:
            print("\nError: No GRT available for signaling")
            return
            
        # Calculate optimal distribution
        print("\nCalculating optimal signal distribution...")
        allocations = signaler.calculate_optimal_distribution(grt_balance)
        
        # Present plan and get confirmation
        if signaler.present_plan(allocations):
            # Execute signaling
            signaler.execute_signaling(allocations)
            print("\nSignaling complete!")
        else:
            print("\nOperation cancelled by user")
            
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main()
