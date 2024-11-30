import requests
import json

def query_subgraph_info():
    # The Graph Network Subgraph endpoint
    url = 'https://api.thegraph.com/subgraphs/name/graphprotocol/graph-network-mainnet'
    
    # Query to get subgraph info
    query = """
    {
        subgraph(id: "22327336881714476995743838527991275714210510246126052258699153536276712602530") {
            id
            displayName
            currentVersion {
                id
                subgraphDeployment {
                    id
                    ipfsHash
                }
            }
        }
    }
    """
    
    # Make the request
    response = requests.post(url, json={'query': query})
    print("\nSubgraph Information:")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    query_subgraph_info()
