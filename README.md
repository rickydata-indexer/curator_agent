# Curation Agent

A tool for managing and optimizing curation on The Graph protocol using set of Dify modular backend APIs

## Actions using Dify backend
### Unsignal
1. get name signal amounts: curation_user_signals
2. unsignal_from_subgraph
### New signal:
1. find opportunities: curation_best_opportunities
2. check historical steadiness of query volume: visualize_query_volume_by_day_subgraph
3. get balance: pull_grt_balance_agent_tool
4. curate on subgraph: curate_subgraph


## Environment Setup

1. Create a `.env` file in the root directory with the following variables:

```env
# The Graph API key for querying subgraphs
THEGRAPH_API_KEY=your_thegraph_api_key

# Dify API key for workflow execution
KEY_curation_user_signals=your_dify_workflow_backend_api_key
# ... keep adding the rest here

# Infura API key for Arbitrum network access
INFURA_API_KEY=your_infura_api_key

# Base URLs
THEGRAPH_API_URL=https://gateway.thegraph.com/api
DIFY_WORKFLOW_URL=https://dify.rickydata.com/v1/workflows/run
```


... keep going

## Structure

- tools.py takes modular Dify backend tools and makes them available in python
- curation_agent.py uses tools in logical 
