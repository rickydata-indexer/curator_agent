"""
Graph Network API interactions for the curator agent.
"""

import os
from typing import Dict, List, Optional
from web3 import Web3
import requests
import logging

class GraphAPI:
    """Handles interactions with The Graph Network API and contracts."""
    
    def __init__(self, web3_provider: str, api_key: Optional[str] = None):
        """Initialize the Graph API client."""
        self.w3 = Web3(Web3.HTTPProvider(web3_provider))
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        
        # Get network subgraph endpoint from environment
        self.NETWORK_SUBGRAPH = os.getenv('GRAPH_GATEWAY_URL')
        if not self.NETWORK_SUBGRAPH:
            raise ValueError("GRAPH_GATEWAY_URL not set in environment")
        
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
        result = self._query_network_subgraph(query, variables)
        return result.get('data', {}).get('subgraphDeployment', {})

    def get_subgraph_deployments(self, first: int = 100) -> List[Dict]:
        """Get list of subgraph deployments."""
        query = """
        query($first: Int!) {
            subgraphDeployments(
                first: $first,
                orderBy: id,
                orderDirection: desc
            ) {
                id
                allocationDataPoints(
                    first: 1,
                    orderBy: id,
                    orderDirection: desc
                ) {
                    id
                    indexer {
                        id
                    }
                }
                queryDailyDataPoints(
                    first: 1,
                    orderBy: id,
                    orderDirection: desc
                ) {
                    id
                }
            }
        }
        """
        
        variables = {'first': first}
        result = self._query_network_subgraph(query, variables)
        if result is None:
            self.logger.error("Received None response from query")
            return []
            
        deployments = result.get('data', {}).get('subgraphDeployments', [])
        self.logger.info(f"Found {len(deployments)} deployments")
        return deployments

    def get_indexer_data(self, indexer_id: str) -> Dict:
        """Get detailed information about a specific indexer."""
        query = """
        query($id: ID!) {
            indexer(id: $id) {
                id
                indexerDailyDataPoints(
                    first: 30,
                    orderBy: id,
                    orderDirection: desc
                ) {
                    id
                }
                allocationDataPoints(
                    first: 30,
                    orderBy: id,
                    orderDirection: desc
                ) {
                    id
                    subgraphDeployment {
                        id
                    }
                }
            }
        }
        """
        
        variables = {'id': indexer_id}
        result = self._query_network_subgraph(query, variables)
        return result.get('data', {}).get('indexer', {})

    def get_indexers(self, first: int = 100) -> List[Dict]:
        """Get list of indexers."""
        query = """
        query($first: Int!) {
            indexers(
                first: $first,
                orderBy: id,
                orderDirection: desc
            ) {
                id
                indexerDailyDataPoints(
                    first: 30,
                    orderBy: id,
                    orderDirection: desc
                ) {
                    id
                }
                allocationDataPoints(
                    first: 1,
                    orderBy: id,
                    orderDirection: desc
                ) {
                    id
                    subgraphDeployment {
                        id
                    }
                }
            }
        }
        """
        
        variables = {'first': first}
        result = self._query_network_subgraph(query, variables)
        if result is None:
            self.logger.error("Received None response from query")
            return []
            
        indexers = result.get('data', {}).get('indexers', [])
        self.logger.info(f"Found {len(indexers)} indexers")
        return indexers

    def get_network_metrics(self, days: int = 30) -> Dict:
        """Get network-wide metrics."""
        query = """
        query($days: Int!) {
            messageDataPoints(
                first: $days,
                orderBy: id,
                orderDirection: desc
            ) {
                id
            }
            allocationDataPoints(
                first: $days,
                orderBy: id,
                orderDirection: desc
            ) {
                id
                indexer {
                    id
                }
                subgraphDeployment {
                    id
                }
            }
            queryDailyDataPoints(
                first: $days,
                orderBy: id,
                orderDirection: desc
            ) {
                id
            }
        }
        """
        
        variables = {'days': days}
        result = self._query_network_subgraph(query, variables)
        if result is None:
            self.logger.error("Received None response from query")
            return {}
            
        return result.get('data', {})

    def _query_network_subgraph(self, query: str, variables: Dict = None) -> Dict:
        """Execute a query against the network subgraph."""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}' if self.api_key else ''
        }
        
        try:
            self.logger.info(f"Querying {self.NETWORK_SUBGRAPH}")
            self.logger.debug(f"Query: {query}")
            self.logger.debug(f"Variables: {variables}")
            
            response = requests.post(
                self.NETWORK_SUBGRAPH,
                headers=headers,
                json={
                    'query': query,
                    'variables': variables or {}
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            self.logger.debug(f"Response: {result}")
            
            if 'errors' in result:
                self.logger.error(f"GraphQL errors: {result['errors']}")
                return None
                
            return result
            
        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            return None
