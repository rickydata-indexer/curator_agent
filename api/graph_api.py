"""
Graph Network API interactions for the curator agent.
Handles subgraph queries and network data retrieval.
"""

import os
from typing import Dict, List, Optional
from web3 import Web3
import requests

class GraphAPI:
    """Handles interactions with The Graph Network API and contracts."""
    
    NETWORK_SUBGRAPH = "https://api.thegraph.com/subgraphs/name/graphprotocol/graph-network-arbitrum"
    
    def __init__(self, web3_provider: str, api_key: Optional[str] = None):
        """Initialize the Graph API client.
        
        Args:
            web3_provider: Arbitrum RPC endpoint
            api_key: Optional Graph API key for higher rate limits
        """
        self.w3 = Web3(Web3.HTTPProvider(web3_provider))
        self.api_key = api_key
        
        # Contract addresses on Arbitrum
        self.contracts = {
            'L2GraphToken': '0x9623063377AD1B27544C965cCd7342f7EA7e88C7',
            'L2Curation': '0x22d78fb4bc72e191C765807f8891B5e1785C8014',
            'L2GNS': '0xec9A7fb6CbC2E41926127929c2dcE6e9c5D33Bec',
            'SubgraphNFT': '0x3FbD54f0cc17b7aE649008dEEA12ed7D2622B23f'
        }

    def get_subgraph_by_id(self, subgraph_id: str) -> Dict:
        """Get detailed information about a specific subgraph.
        
        Args:
            subgraph_id: The NFT ID of the subgraph
            
        Returns:
            Dict containing subgraph details
        """
        query = """
        query($id: ID!) {
            subgraph(id: $id) {
                id
                nftID
                owner { id }
                currentVersion {
                    id
                    subgraphDeployment {
                        id
                        signalledTokens
                        signalAmount
                        queryFeesAmount
                        stakedTokens
                    }
                }
                createdAt
                updatedAt
                signalledTokens
                unsignalledTokens
                nameSignalAmount
                nameSignalCount
                metadataHash
                description
                image
                displayName
            }
        }
        """
        
        variables = {'id': subgraph_id}
        result = self._query_network_subgraph(query, variables)
        return result.get('data', {}).get('subgraph', {})

    def get_top_subgraphs(self, first: int = 100) -> List[Dict]:
        """Get list of top subgraphs by signalled tokens.
        
        Args:
            first: Number of subgraphs to fetch
            
        Returns:
            List of subgraph data dictionaries
        """
        query = """
        query($first: Int!) {
            subgraphs(
                first: $first
                orderBy: signalledTokens
                orderDirection: desc
                where: {
                    currentVersion_not: null
                    signalledTokens_gt: 0
                }
            ) {
                id
                nftID
                signalledTokens
                currentVersion {
                    id
                    subgraphDeployment {
                        id
                        queryFeesAmount
                        signalAmount
                    }
                }
                displayName
            }
        }
        """
        
        variables = {'first': first}
        result = self._query_network_subgraph(query, variables)
        return result.get('data', {}).get('subgraphs', [])

    def get_curator_signals(self, curator_address: str) -> List[Dict]:
        """Get all active signals for a curator address.
        
        Args:
            curator_address: Ethereum address of the curator
            
        Returns:
            List of signal data dictionaries
        """
        query = """
        query($curator: String!) {
            curator(id: $curator) {
                id
                totalSignalledTokens
                totalUnsignalledTokens
                signals {
                    id
                    signalledTokens
                    unsignalledTokens
                    subgraphDeployment {
                        id
                        signalAmount
                        queryFeesAmount
                    }
                }
            }
        }
        """
        
        variables = {'curator': curator_address.lower()}
        result = self._query_network_subgraph(query, variables)
        return result.get('data', {}).get('curator', {}).get('signals', [])

    def _query_network_subgraph(self, query: str, variables: Dict = None) -> Dict:
        """Execute a query against the network subgraph.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            
        Returns:
            Query result data
        """
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
            
        response = requests.post(
            self.NETWORK_SUBGRAPH,
            headers=headers,
            json={
                'query': query,
                'variables': variables or {}
            }
        )
        
        response.raise_for_status()
        return response.json()
