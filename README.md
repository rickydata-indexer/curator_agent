# Automated Curation Agent

An AI-powered agent that automatically manages curation signal on The Graph network to optimize returns and support high-quality subgraphs.

## Overview

This agent analyzes subgraph metrics and market data to automatically allocate curation signal, aiming to:
- Maximize curation returns through strategic signal placement
- Support high-quality subgraphs with proven reliability
- Rebalance signal allocations based on performance metrics
- Maintain a diversified curation portfolio

## Project Structure

```
curator_agent/
├── api/
│   ├── graph_api.py         # The Graph Network API interactions
│   ├── metrics_api.py       # Query metrics and performance data
│   └── arbitrum_api.py      # Arbitrum contract interactions
├── models/
│   ├── subgraph.py         # Subgraph data models
│   ├── metrics.py          # Performance metrics calculations
│   ├── portfolio.py        # Signal portfolio management
│   └── strategy.py         # Curation strategy models
├── agent/
│   ├── analyzer.py         # Data analysis and signal recommendations
│   ├── executor.py         # Transaction execution
│   └── monitor.py          # Portfolio monitoring
├── utils/
│   ├── config.py          # Configuration management
│   ├── contracts.py       # Contract ABIs and addresses
│   └── logger.py          # Logging utilities
└── main.py                # Agent entry point
```

## Key Features

1. **Automated Analysis**
   - Query volume tracking
   - Fee generation analysis
   - Historical performance metrics
   - Network-wide curation trends

2. **Smart Signal Management**
   - Automated signal allocation
   - Risk-adjusted position sizing
   - Dynamic rebalancing
   - Gas-optimized transactions

3. **Portfolio Optimization**
   - APR optimization
   - Risk diversification
   - Correlation analysis
   - Performance tracking

4. **Risk Management**
   - Signal concentration limits
   - Slippage protection
   - Gas price monitoring
   - Emergency withdrawal capabilities

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```env
# Network Configuration
ARBITRUM_RPC_URL=your_arbitrum_rpc_url
GRAPH_API_KEY=your_graph_api_key

# Wallet Configuration
CURATOR_ADDRESS=your_curator_address
PRIVATE_KEY=your_private_key

# Agent Configuration
MIN_APR_THRESHOLD=10
MAX_SIGNAL_PER_SUBGRAPH=100000
GAS_PRICE_LIMIT=100
REBALANCE_INTERVAL=86400
```

3. Initialize the agent:
```bash
python main.py
```

## Contract Addresses (Arbitrum)

```python
CONTRACTS = {
    'L2GraphToken': '0x9623063377AD1B27544C965cCd7342f7EA7e88C7',
    'L2Curation': '0x22d78fb4bc72e191C765807f8891B5e1785C8014',
    'L2GNS': '0xec9A7fb6CbC2E41926127929c2dcE6e9c5D33Bec',
    'SubgraphNFT': '0x3FbD54f0cc17b7aE649008dEEA12ed7D2622B23f'
}
```

## Strategy Components

1. **Signal Allocation Strategy**
   - APR-weighted allocation
   - Query volume growth trends
   - Network positioning score
   - Historical reliability metrics

2. **Rebalancing Logic**
   - Performance-based rebalancing
   - Gas-optimized batching
   - Slippage-aware execution
   - Portfolio drift monitoring

3. **Risk Management**
   - Maximum allocation limits
   - Minimum liquidity requirements
   - Network diversity targets
   - Emergency circuit breakers

## Development Roadmap

1. **Phase 1: Core Infrastructure**
   - Basic API integration
   - Contract interaction layer
   - Data collection pipeline
   - Simple allocation strategy

2. **Phase 2: Advanced Analytics**
   - Machine learning models
   - Network analysis
   - Risk scoring system
   - Performance prediction

3. **Phase 3: Optimization**
   - Gas optimization
   - Advanced portfolio strategies
   - Multi-factor allocation
   - Automated rebalancing

4. **Phase 4: Risk Management**
   - Advanced risk controls
   - Emergency procedures
   - Performance monitoring
   - Audit system

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License
