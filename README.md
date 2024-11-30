# Automated Curator Agent

An AI-powered agent that automatically manages curation signal on The Graph network by analyzing subgraph performance metrics, indexer allocations, and network data to optimize returns.

## Overview

The curator agent monitors The Graph Network on Arbitrum and automatically manages curation signal by:
1. Analyzing subgraph deployments and their performance metrics
2. Tracking indexer allocations and support
3. Monitoring query volumes and fee generation
4. Making data-driven decisions for signal placement

## Architecture

```
curator_agent/
├── api/
│   ├── graph_api.py         # Graph Network API interactions
│   ├── metrics_api.py       # Performance metrics collection
│   └── arbitrum_api.py      # Contract interactions
├── models/
│   ├── subgraph.py         # Subgraph data models
│   ├── metrics.py          # Performance calculations
│   ├── portfolio.py        # Signal portfolio management
│   └── strategy.py         # Curation strategies
├── agent/
│   ├── analyzer.py         # Data analysis engine
│   ├── executor.py         # Transaction execution
│   └── monitor.py          # Portfolio monitoring
└── utils/
    ├── config.py          # Configuration management
    └── logger.py          # Logging utilities
```

## Key Features

1. **Subgraph Analysis**
   - Track deployment performance
   - Monitor indexer allocations
   - Analyze query metrics
   - Calculate potential returns

2. **Portfolio Management**
   - Automated signal allocation
   - Risk-adjusted position sizing
   - Dynamic rebalancing
   - Gas-optimized transactions

3. **Performance Monitoring**
   - Real-time metric tracking
   - APR calculations
   - Risk assessment
   - Network correlation analysis

## Data Sources

The agent integrates with multiple data sources:

1. **Graph Network Subgraph**
   - Subgraph deployments
   - Indexer allocations
   - Query metrics
   - Network statistics

2. **Smart Contracts**
   - Signal transactions
   - Curation shares
   - Token transfers
   - Network parameters

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

Required environment variables:
```env
# Network Configuration
ARBITRUM_RPC_URL=your_arbitrum_rpc
GRAPH_GATEWAY_URL=your_gateway_url
THEGRAPH_API_KEY=your_api_key

# Wallet Configuration
AGENT_ADDRESS=your_agent_address
PRIVATE_KEY=your_private_key

# Agent Configuration
MIN_APR_THRESHOLD=10.0
MAX_RISK_SCORE=60.0
CHECK_INTERVAL=3600
MAX_SLIPPAGE=0.02
MAX_GAS_PRICE=100
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

## Usage

Run the agent:
```bash
python main.py
```

The agent will:
1. Monitor network metrics and subgraph performance
2. Analyze opportunities based on configured strategies
3. Execute signal allocations when profitable
4. Maintain optimal portfolio balance

## Development Roadmap

1. **Phase 1: Core Infrastructure** (Current)
   - Basic API integration
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
