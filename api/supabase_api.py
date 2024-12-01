"""
Supabase API interactions for query volume data.
"""

import os
import requests
import base64
from datetime import datetime, timedelta
from typing import Dict, Tuple

def get_auth_headers() -> Dict[str, str]:
    """Generate authentication headers for Supabase API."""
    username = os.getenv('SUPABASE_USERNAME')
    password = os.getenv('SUPABASE_PASSWORD')
    
    if not all([username, password]):
        raise Exception("Missing Supabase credentials in .env file")
    
    credentials = f"{username}:{password}"
    auth_bytes = credentials.encode('ascii')
    base64_auth = base64.b64encode(auth_bytes).decode('ascii')
    
    return {
        "Authorization": f"Basic {base64_auth}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def query_supabase() -> list:
    """Query Supabase for query volume data."""
    try:
        # Get data from the last week
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        # Use the same base URL and endpoint as the streamlit app
        base_url = "http://supabasekong-so4w8gock004k8kw8ck84o80.94.130.17.180.sslip.io"
        api_url = f"{base_url}/api/pg-meta/default/query"

        print(f"\nQuerying Supabase at: {api_url}")
        print(f"Using credentials: {os.getenv('SUPABASE_USERNAME')}")

        # SQL query
        sql_query = f"""
        SELECT 
            subgraph_deployment_ipfs_hash,
            SUM(total_query_fees) as total_query_fees,
            SUM(query_count) as query_count
        FROM qos_hourly_query_volume 
        WHERE end_epoch > '{week_ago}'
        GROUP BY subgraph_deployment_ipfs_hash
        """

        print("\nExecuting SQL query:")
        print(sql_query)

        # Execute the query
        response = requests.post(
            api_url,
            headers=get_auth_headers(),
            json={"query": sql_query}
        )

        print(f"\nResponse status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response content: {response.text[:500]}...")  # Print first 500 chars

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error executing query: HTTP {response.status_code} - {response.text}")

    except Exception as e:
        print(f"\nDetailed error in query_supabase: {str(e)}")
        raise Exception(f"Error: {str(e)}")

def process_query_data() -> Tuple[Dict[str, float], Dict[str, int]]:
    """Process query data from Supabase into fees and counts dictionaries."""
    try:
        print("\nProcessing query data...")
        rows = query_supabase()
        
        # Initialize dictionaries
        query_fees = {}
        query_counts = {}

        # Process results
        if rows:
            print(f"\nProcessing {len(rows)} rows of data")
            for row in rows:
                ipfs_hash = row['subgraph_deployment_ipfs_hash']
                if ipfs_hash:
                    query_fees[ipfs_hash] = float(row['total_query_fees'])
                    query_counts[ipfs_hash] = int(row['query_count'])

        print(f"\nProcessed data for {len(query_counts)} subgraphs")
        if query_counts:
            print("\nSample data:")
            sample_ipfs = next(iter(query_counts))
            print(f"IPFS Hash: {sample_ipfs}")
            print(f"Query Count: {query_counts[sample_ipfs]}")
            print(f"Query Fees: {query_fees[sample_ipfs]}")

        return query_fees, query_counts

    except Exception as e:
        print(f"Error querying Supabase: {str(e)}")
        return {}, {}
