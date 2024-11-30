"""
Test script for curator agent API interactions.
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from api.graph_api import GraphAPI
from api.arbitrum_api import ArbitrumAPI

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize Graph API with existing credentials
    graph_api = GraphAPI(
        web3_provider=f"https://arb1.arbitrum.io/rpc",
        api_key=os.getenv('THEGRAPH_API_KEY')
    )
    
    print("\nTesting Graph API interactions...")
    
    try:
        # Simple connectivity test
        print("\nTesting basic query...")
        query = """
        query {
            _meta {
                block {
                    number
                }
                deployment
            }
        }
        """
        
        result = graph_api._query_network_subgraph(query)
        if result:
            print("\nConnection successful!")
            print(f"Result: {result}")
            
            # If basic query works, try simple subgraph deployment query
            print("\nFetching subgraph deployments (basic)...")
            query = """
            query {
                subgraphDeployments(first: 5) {
                    id
                }
            }
            """
            
            result = graph_api._query_network_subgraph(query)
            if result and 'data' in result:
                deployments = result['data'].get('subgraphDeployments', [])
                print(f"\nFound {len(deployments)} deployments:")
                for deployment in deployments:
                    print(f"ID: {deployment.get('id')}")
                    
                # If we get deployments, try getting data for first one
                if deployments:
                    first_id = deployments[0].get('id')
                    print(f"\nFetching details for deployment {first_id}...")
                    query = f"""
                    query {{
                        subgraphDeployment(id: "{first_id}") {{
                            id
                            allocationDataPoints(first: 1) {{
                                id
                            }}
                        }}
                    }}
                    """
                    
                    result = graph_api._query_network_subgraph(query)
                    if result and 'data' in result:
                        print(f"Deployment details: {result['data']}")
        else:
            print("\nFailed to connect to Graph Gateway")
            
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
