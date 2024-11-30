"""
Test script to introspect the Graph Gateway schema.
"""

import os
import requests
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    gateway_url = os.getenv('GRAPH_GATEWAY_URL')
    api_key = os.getenv('THEGRAPH_API_KEY')
    
    # GraphQL introspection query
    query = """
    query IntrospectionQuery {
      __schema {
        queryType {
          name
          fields {
            name
            description
            args {
              name
              type {
                name
              }
            }
          }
        }
      }
    }
    """
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}' if api_key else ''
    }
    
    print(f"\nQuerying schema at: {gateway_url}")
    
    try:
        response = requests.post(
            gateway_url,
            headers=headers,
            json={'query': query}
        )
        
        response.raise_for_status()
        result = response.json()
        
        if 'errors' in result:
            print("\nGraphQL Errors:")
            print(result['errors'])
            return
            
        print("\nAvailable Query Fields:")
        fields = result['data']['__schema']['queryType']['fields']
        for field in fields:
            print(f"\nField: {field['name']}")
            if field['description']:
                print(f"Description: {field['description']}")
            if field['args']:
                print("Arguments:")
                for arg in field['args']:
                    print(f"  - {arg['name']}: {arg['type']['name']}")
                    
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
