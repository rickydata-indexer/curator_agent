import os
import json
import requests
from dotenv import load_dotenv

# Functions to interact with Dify backend. Tools defined by the API keys, which all need to be set in .env
def curation_user_signals():
    # Load environment variables from .env file
    load_dotenv()
    """Use Dify workflow to get curation agent signals data"""
    url = "https://dify.rickydata.com/v1/workflows/run"
    headers = {
        'Authorization': f"Bearer {os.getenv('KEY_curation_user_signals')}",
        'Content-Type': 'application/json'
    }
    payload = {
        'inputs': {
            'user_wallet': "0xAB1D1366de8b5D1E3479f01b0D73BcC93048f6d5",
            'infura_api_key': f"{os.getenv('INFURA_API_KEY')}"
        },
        'response_mode': 'blocking',
        'user': 'curation_agent_python'
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    
    if response_data.get('data', {}).get('outputs', {}):
        return response_data['data']['outputs']
    return response_data

def unsignal_from_subgraph(subgraph_deployment_ipfs_hash, amount_signal=0.001):
    # Load environment variables from .env file
    load_dotenv()
    """Use unsignal from subgraph data Dify workflow"""
    url = "https://dify.rickydata.com/v1/workflows/run"
    headers = {
        'Authorization': f"Bearer {os.getenv('KEY_unsignal_from_subgraph')}",
        'Content-Type': 'application/json'
    }
    payload = {
        'inputs': {
            'amount_signal': amount_signal,
            'subgraph_deployment_ipfs_hash': subgraph_deployment_ipfs_hash,
            'infura_api_key': f"{os.getenv('INFURA_API_KEY')}" 
        },
        'response_mode': 'blocking',
        'user': 'curation_agent_python'
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    
    if response_data.get('data', {}).get('outputs', {}):
        return response_data['data']['outputs']
    return response_data

def curation_best_opportunities():
    # Load environment variables from .env file
    load_dotenv()
    """Use Dify workflow to find best opportunities"""
    url = "https://dify.rickydata.com/v1/workflows/run"
    headers = {
        'Authorization': f"Bearer {os.getenv('KEY_curation_best_opportunities')}",
        'Content-Type': 'application/json'
    }
    payload = {
        'inputs': {
            'min_apr': 20,
            'min_weekly_queries': 100000,
            'min_subgraph_signal': 1
        },
        'response_mode': 'blocking',
        'user': 'curation_agent_python'
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    
    if response_data.get('data', {}).get('outputs', {}):
        return response_data['data']['outputs']
    return response_data

def pull_grt_balance_from_subgraph():
    # Load environment variables from .env file
    load_dotenv()
    """Use Dify workflow to find best opportunities"""
    url = "https://dify.rickydata.com/v1/workflows/run"
    headers = {
        'Authorization': f"Bearer {os.getenv('KEY_pull_grt_balance_from_subgraph')}",
        'Content-Type': 'application/json'
    }
    payload = {
        'inputs': {
            'thegraph_api_key': f"{os.getenv('THEGRAPH_API_KEY')}",
            'user_wallet': f"{os.getenv('AGENT_WALLET')}",
        },
        'response_mode': 'blocking',
        'user': 'curation_agent_python'
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    
    if response_data.get('data', {}).get('outputs', {}):
        return response_data['data']['outputs']
    return response_data


if __name__ == "__main__":
    # Test functions
    print("\nTesting curation_user_signals:")
    result = curation_user_signals()
    print(json.dumps(result, indent=2))

    print("\nTesting unsignal_from_subgraph:")
    result2 = unsignal_from_subgraph("QmUzRg2HHMpbgf6Q4VHKNDbtBEJnyp5JWCh2gUX9AV6jXv", amount_signal=0.001)
    print(result2)

    print("\nTesting curation_best_opportunities:")
    result3 = curation_best_opportunities()
    print(result3)

    print("\nTesting pull_grt_balance_from_subgraph:")
    result4 = pull_grt_balance_from_subgraph()
    print(result4)
    
