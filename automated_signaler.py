import os
import requests
from web3 import Web3
from dotenv import load_dotenv
from typing import Dict, List
import json
import time

# Import existing modules
from signal_grt import get_token_balance, approve_grt, mint_signal
from api import get_subgraph_deployments, get_grt_price, get_account_balance, process_query_data
from models.opportunities import calculate_opportunities, Opportunity
from models.signals import AllocationOptimizer

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

    def calculate_optimal_distribution(self, available_grt: float) -> tuple[Dict[str, float], List[Opportunity]]:
        """Calculate optimal signal distribution based on available GRT."""
        # Get current versions and their deployments
        print("\nFetching current versions...")
        current_versions = self._get_current_versions()
        print(f"Found {len(current_versions)} current versions")
        
        # Get query fees and counts from Supabase
        print("\nFetching query data from Supabase...")
        query_fees, query_counts = process_query_data()
        print(f"Found query data for {len(query_counts)} subgraphs")
        
        # Filter query data to only include current versions
        filtered_query_fees = {}
        filtered_query_counts = {}
        for ipfs_hash, data in current_versions.items():
            if ipfs_hash in query_counts:
                filtered_query_fees[ipfs_hash] = query_fees[ipfs_hash]
                filtered_query_counts[ipfs_hash] = query_counts[ipfs_hash]
        
        print(f"\nFiltered to {len(filtered_query_counts)} current versions with query data")
        
        # Get deployments data
        deployments = get_subgraph_deployments()
        
        # Filter deployments to only include current versions
        filtered_deployments = []
        for deployment in deployments:
            if deployment['ipfsHash'] in current_versions:
                deployment['nftID'] = current_versions[deployment['ipfsHash']]['nftID']
                filtered_deployments.append(deployment)
        
        print(f"Found {len(filtered_deployments)} matching deployments")
        
        grt_price = get_grt_price()
        print(f"\nCurrent GRT price: ${grt_price:.4f}")
        
        # Calculate opportunities using filtered data
        print("\nCalculating opportunities...")
        opportunities = calculate_opportunities(filtered_deployments, filtered_query_fees, filtered_query_counts, grt_price)
        print(f"Found {len(opportunities)} viable opportunities")
        
        if opportunities:
            print("\nTop 5 opportunities by potential APR:")
            for i, opp in enumerate(opportunities[:5], 1):
                print(f"\n{i}. IPFS Hash: {opp.ipfs_hash}")
                print(f"   Weekly Queries: {opp.weekly_queries:,}")
                print(f"   Current APR: {opp.current_apr:.2f}%")
                print(f"   Potential APR: {opp.potential_apr:.2f}%")
        
        # Initialize optimizer with opportunities
        optimizer = AllocationOptimizer(opportunities, grt_price)
        
        # Get optimal allocation
        print("\nOptimizing allocations...")
        result = optimizer.optimize_allocation(available_grt)
        
        # Convert allocations to use NFT IDs
        nft_allocations = {}
        for ipfs_hash, amount in result.allocations.items():
            nft_id = current_versions[ipfs_hash]['nftID']
            nft_allocations[nft_id] = amount
        
        print(f"\nFound {len(nft_allocations)} optimal allocations")
        
        return nft_allocations, opportunities

    def _get_current_versions(self) -> Dict[str, Dict]:
        """Get current versions of all subgraphs."""
        query = """
        {
          subgraphs {
            nftID
            currentVersion {
              subgraphDeployment {
                ipfsHash
              }
            }
          }
        }
        """
        
        response = requests.post(
            f"https://gateway.thegraph.com/api/{os.getenv('THEGRAPH_API_KEY')}/subgraphs/id/DZz4kDTdmzWLWsV373w2bSmoar3umKKH9y82SUKr5qmp",
            json={'query': query}
        )
        
        if response.status_code != 200:
            print("Warning: Failed to fetch current versions")
            return {}
            
        data = response.json()
        current_versions = {}
        
        for subgraph in data.get('data', {}).get('subgraphs', []):
            if (subgraph.get('currentVersion') and 
                subgraph['currentVersion'].get('subgraphDeployment') and 
                subgraph.get('nftID')):
                ipfs_hash = subgraph['currentVersion']['subgraphDeployment']['ipfsHash']
                current_versions[ipfs_hash] = {
                    'nftID': subgraph['nftID']
                }
        
        return current_versions

    def present_plan(self, allocations: Dict[str, float], opportunities: List[Opportunity]) -> bool:
        """Present the signaling plan to the user and get confirmation."""
        print("\n=== Proposed Signaling Plan ===\n")
        
        total_grt = sum(allocations.values())
        print(f"Total GRT to be signaled: {total_grt:.2f} GRT\n")
        
        print("Allocations:")
        # Create a reverse mapping of NFT ID to opportunity for lookup
        opp_by_nft = {opp.nft_id: opp for opp in opportunities}
        
        for nft_id, amount in allocations.items():
            opp = opp_by_nft.get(str(nft_id))  # Convert NFT ID to string for lookup
            if opp:
                print(f"\nSubgraph NFT ID: {nft_id}")
                print(f"IPFS Hash: {opp.ipfs_hash}")
                print(f"Amount to signal: {amount:.2f} GRT")
                print(f"Current APR: {opp.current_apr:.2f}%")
                print(f"Potential APR: {opp.potential_apr:.2f}%")
                print(f"Weekly Queries: {opp.weekly_queries:,}")
                print(f"Est. Annual Earnings: ${opp.estimated_earnings:.2f}")
            else:
                print(f"\nSubgraph NFT ID: {nft_id}")
                print(f"Amount to signal: {amount:.2f} GRT")
            
        while True:
            response = input("\nProceed with signaling? (yes/no): ").lower()
            if response in ['yes', 'no']:
                return response == 'yes'
            print("Please answer 'yes' or 'no'")

    def execute_signaling(self, allocations: Dict[str, float]):
        """Execute the signaling transactions."""
        for nft_id, amount in allocations.items():
            if amount <= 0:
                continue
                
            print(f"\nProcessing subgraph NFT ID: {nft_id}")
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
                    int(nft_id),  # Use NFT ID for signaling
                    amount
                )
                print(f"Signal transaction: {signal_tx}")
                
                # Wait between transactions
                time.sleep(5)
                
            except Exception as e:
                print(f"Error processing subgraph NFT ID {nft_id}: {str(e)}")
                
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
        allocations, opportunities = signaler.calculate_optimal_distribution(grt_balance)
        
        # Present plan and get confirmation
        if signaler.present_plan(allocations, opportunities):
            # Execute signaling
            signaler.execute_signaling(allocations)
            print("\nSignaling complete!")
        else:
            print("\nOperation cancelled by user")
            
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main()
