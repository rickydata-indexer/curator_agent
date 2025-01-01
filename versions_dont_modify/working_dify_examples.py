import os
import json
import requests
from dotenv import load_dotenv


def pull_subgraph_query_volume(num_days=7):
    # Load environment variables from .env file
    load_dotenv()
    """Get subgraph query volume data for the specified number of days."""
    url = "https://dify.rickydata.com/v1/workflows/run"
    headers = {
        'Authorization': f"Bearer {os.getenv('KEY_pull_subgraph_query_volume')}",
        'Content-Type': 'application/json'
    }
    payload = {
        'inputs': {
            'num_days': num_days
        },
        'response_mode': 'blocking',
        'user': 'curation_agent_python'
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    
    if response_data.get('data', {}).get('outputs', {}).get('data'):
        return response_data['data']['outputs']['data']
    return response_data

def curation_user_signals():
    # Load environment variables from .env file
    load_dotenv()
    """Get curation user signals data."""
    url = "https://dify.rickydata.com/v1/workflows/run"
    headers = {
        'Authorization': f"Bearer {os.getenv('KEY_curation_user_signals')}",
        'Content-Type': 'application/json'
    }
    payload = {
        'inputs': {},
        'response_mode': 'blocking',
        'user': 'curation_agent_python'
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    
    if response_data.get('data', {}).get('outputs', {}).get('body'):
        # Parse the JSON strings in the body array
        signals = []
        for item in response_data['data']['outputs']['body']:
            try:
                signal_data = json.loads(item)
                if 'new_signals' in signal_data:
                    signals.extend(json.loads(signal_data['new_signals']))
            except json.JSONDecodeError:
                continue
        return signals
    return response_data

if __name__ == "__main__":
    # Test both functions
    print("Testing pull_subgraph_query_volume:")
    result1 = pull_subgraph_query_volume()
    print(result1)
    
    print("\nTesting curation_user_signals:")
    result2 = curation_user_signals()
    print(json.dumps(result2, indent=2))
