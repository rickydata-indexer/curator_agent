from tools import curation_user_signals, unsignal_from_subgraph, curation_best_opportunities, pull_grt_balance_from_subgraph, optimize_signals, curate_subgraph
import json
import pandas as pd
import os
import logging
from dotenv import load_dotenv
load_dotenv()

# Configure logging (only used when curating on subgraphs)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ====== Unsignalling ======

print("\nPulling curation user signals...")
signals_response = curation_user_signals("0xAB1D1366de8b5D1E3479f01b0D73BcC93048f6d5")

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
balance = pull_grt_balance_from_subgraph()
balance = balance['balance']
print(balance)

# Find the optimal signal strategy for available tokens
if balance > 1:
    # Find best current opportunities
    print("\n====== Next determine new signalling actions ======")
    best_opportunities = curation_best_opportunities()
    print(best_opportunities)
    new_signals = optimize_signals(best_opportunities, total_new_signal=balance, min_allocation=1.0)
    print(new_signals)
    print("\n====== Open new curation signal positions ======")
    # Create new curation signal positions
    for index, row in new_signals.iterrows():
        try:
            logging.info(f"Processing subgraph {index + 1}/10: {row['ipfs_hash']}")
            logging.info(f"Signal amount: {row['new_signal']}")
            
            print(curate_subgraph(row['ipfs_hash'], row['new_signal']))
            
            logging.info(f"Successfully processed subgraph: {row['ipfs_hash']}")
        except Exception as e:
            logging.error(f"Error processing subgraph {row['ipfs_hash']}: {str(e)}")
        
    logging.info("Finished processing all subgraphs")
else:
    print("Not enough new GRT to open new signals")


# ====== End ======
print("Completed all unsignalling and signaling actions")



# deployment: set it up on hetzner python server to execute daily

# potential improvements:
# - would be better to avoid non-sustained query volume subgraphs (we have dify tool that can be used for query volume)