from tools import pull_subgraph_query_volume, curation_user_signals, unsignal_from_subgraph, curation_best_opportunities, pull_grt_balance_from_subgraph
import json
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

# ====== Unsignalling ======

print("\nPulling curation user signals...")
signals_response = curation_user_signals()

if not signals_response or 'body' not in signals_response:
    print("No active signals found (or all signals are less than 28 days old)")
else:
    # Process the new JSON structure
    signals_data = []
    for signal_str in signals_response['body']:
        try:
            signal_dict = json.loads(signal_str)
            signals_data.append({
                'ipfs_hash': signal_dict['ipfs_subgraph_deployment'],
                'apr': signal_dict['apr'],
                'name_signal': signal_dict['name_signal']
            })
        except json.JSONDecodeError as e:
            print(f"Error parsing signal data: {e}")
            continue
        except KeyError as e:
            print(f"Missing key in signal data: {e}")
            continue

    # Convert the signals_data to a DataFrame
    df = pd.DataFrame(signals_data)
    print("\nAll current signals:")
    print(df)
    
    # Check if required columns exist
    required_columns = ['apr', 'ipfs_hash', 'name_signal']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"\nWarning: DataFrame is missing required columns: {missing_columns}")
        print("Available columns:", df.columns.tolist())
        print("This likely means we just don't need to unsignal from anywhere right now. Could also be issue with Dify backend curation_user_signals")
    else:
        # Filter for APR below 30%
        low_apr_df = df[df['apr'] < 30]
        
        if low_apr_df.empty:
            print("\nNo subgraphs found with APR below 30% - Great news!")
        else:
            print("\nSubgraphs with APR below 30%:")
            print(low_apr_df)
            
            print("\nProcessing unsignaling for low APR subgraphs...")
            for index, row in low_apr_df.iterrows():
                ipfs_hash = row['ipfs_hash']
                amount_to_unsignal = row['name_signal']
                
                print(f"\nUnsignaling {amount_to_unsignal} from subgraph {ipfs_hash}")
                try:
                    result = unsignal_from_subgraph(
                        subgraph_deployment_ipfs_hash=ipfs_hash,
                        amount_signal=amount_to_unsignal
                    )
                    print(f"Unsignaling successful: {result}")
                except Exception as e:
                    print(f"Error unsignaling from {ipfs_hash}: {str(e)}")

# ====== End of Unsignalling path - all works correctly ======
print("====== Unsignalling actions complete ======")

# ====== Choosing new subgraphs to signal on ======
print("====== Next choosing new subgraphs to signal on ======")

# pull GRT balance
print("GRT Balance")
pull_grt_balance_from_subgraph = pull_grt_balance_from_subgraph()
balance = pull_grt_balance_from_subgraph['balance']
print(balance)


# Find best current opportunities
print("\n====== Next determine new signalling actions ======")
curation_best_opportunities = curation_best_opportunities()

print(curation_best_opportunities)

# here figure out optimal signal strategy
# can probably take the ratio and use that to figure out new position impact



# or tools step here to optimize 

# Curate on subgraphs
# when adding new signal if there are additional APR calculations (for safety check) make sure it does NOT use $4 price assumption


# deployment: set it up on hetzner python server to execute daily

# potential improvements:
# - would be better to avoid non-sustained query volume subgraphs (we have dify tool that can be used for query volume)