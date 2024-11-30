"""
Graph Network API interactions for the curator agent.
"""

import os
from typing import Dict, List, Optional
from web3 import Web3
import requests
import logging

# Initialize API key and gateway URL from environment
THEGRAPH_API_KEY = os.getenv('THEGRAPH_API_KEY')
GRAPH_GATEWAY_URL = os.getenv('GRAPH_GATEWAY_URL')

def get_subgraph_deployments() -> List[Dict]:
    """Get list of subgraph deployments with signaling data."""
    query = """
    query {
        subgraphDeployments(
            first: 100,
            orderBy: signalledTokens,
            orderDirection: desc
        ) {
            id
            ipfsHash
            signalAmount
            signalledTokens
            queryFeesAmount
            queryFeeRebates
            curatorFeeRewards
            dailyQueryFees
        }
    }
    """
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            GRAPH_GATEWAY_URL,
            headers=headers,
            json={'query': query}
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'errors' in result:
                print(f"GraphQL errors: {result['errors']}")
                return []
            return result.get('data', {}).get('subgraphDeployments', [])
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return []
    except Exception as e:
        print(f"Error fetching subgraph deployments: {str(e)}")
        return []

def get_user_curation_signal(wallet_address: str) -> Dict[str, float]:
    """Get user's current curation signals."""
    query = """
    query($curator: String!) {
        curator(id: $curator) {
            signals {
                subgraphDeployment {
                    id
                }
                signalAmount
            }
        }
    }
    """
    
    variables = {'curator': wallet_address.lower()}
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            GRAPH_GATEWAY_URL,
            headers=headers,
            json={
                'query': query,
                'variables': variables
            }
        )
        
        signals = {}
        if response.status_code == 200:
            result = response.json()
            if 'errors' in result:
                print(f"GraphQL errors: {result['errors']}")
                return {}
                
            curator_data = result.get('data', {}).get('curator', {})
            if curator_data and 'signals' in curator_data:
                for signal in curator_data['signals']:
                    deployment_id = signal['subgraphDeployment']['id']
                    amount = float(signal['signalAmount']) / 1e18  # Convert from wei
                    signals[deployment_id] = amount
                    
        return signals
    except Exception as e:
        print(f"Error fetching user signals: {str(e)}")
        return {}

def get_grt_price() -> float:
    """Get current GRT price."""
    # For testing purposes, return a fixed price
    # In production, this would fetch from an oracle or price feed
    return 0.15

class GraphAPI:
    """Handles interactions with The Graph Network API and contracts."""
    
    def __init__(self, web3_provider: str, api_key: Optional[str] = None):
        """Initialize the Graph API client."""
        self.w3 = Web3(Web3.HTTPProvider(web3_provider))
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        
        # Contract addresses on Arbitrum
        self.contracts = {
            'L2GraphToken': '0x9623063377AD1B27544C965cCd7342f7EA7e88C7',
            'L2Curation': '0x22d78fb4bc72e191C765807f8891B5e1785C8014',
            'L2GNS': '0xec9A7fb6CbC2E41926127929c2dcE6e9c5D33Bec',
            'SubgraphNFT': '0x3FbD54f0cc17b7aE649008dEEA12ed7D2622B23f'
        }

    def get_subgraph_deployment(self, deployment_id: str) -> Dict:
        """Get detailed information about a specific subgraph deployment."""
        query = """
        query($id: ID!) {
            subgraphDeployment(id: $id) {
                id
                allocationDataPoints(
                    first: 30,
                    orderBy: id,
                    orderDirection: desc
                ) {
                    id
                    indexer {
                        id
                    }
                }
                queryDailyDataPoints(
                    first: 30,
                    orderBy: id,
                    orderDirection: desc
                ) {
                    id
                }
            }
        }
        """
        
        variables = {'id': deployment_id}
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                GRAPH_GATEWAY_URL,
                headers=headers,
                json={
                    'query': query,
                    'variables': variables
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'errors' in result:
                    self.logger.error(f"GraphQL errors: {result['errors']}")
                    return {}
                return result.get('data', {}).get('subgraphDeployment', {})
            else:
                self.logger.error(f"Request failed with status code: {response.status_code}")
                return {}
        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            return {}
