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

Create a `.env` file in the root directory with the following variables:

```env
# The Graph API key for querying subgraphs
THEGRAPH_API_KEY=add
# Dify API key for specific workflow executions
KEY_curation_user_signals=add
KEY_pull_subgraph_query_volume=add
KEY_unsignal_from_subgraph=add
KEY_curation_best_opportunities=add
KEY_pull_grt_balance_from_subgraph=add
KEY_curate_subgraph=add

# RPC URL to perform transactions
RPC_URL="add"
# Agent info
AGENT_WALLET=add

# Base URLs
THEGRAPH_API_URL="add"
DIFY_URL="add"
```

## Structure

- tools.py takes modular Dify backend tools and makes them available in python
- curation_agent.py uses tools in logical 

## Running the agent

1. execute tools.py to confirm tools are working correctly
2. run curation_agent.py on a schedule

