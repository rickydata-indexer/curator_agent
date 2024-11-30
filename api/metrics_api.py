"""
Metrics API for collecting and analyzing subgraph performance data.
Handles query volume, fee generation, and other key metrics.
"""

from typing import Dict, List, Optional
import requests
from datetime import datetime, timedelta
import pandas as pd

class MetricsAPI:
    """Handles collection and analysis of subgraph performance metrics."""
    
    def __init__(self, metrics_endpoint: str):
        """Initialize the metrics API client.
        
        Args:
            metrics_endpoint: Endpoint for query metrics data
        """
        self.metrics_endpoint = metrics_endpoint

    def get_query_metrics(
        self,
        subgraph_id: str,
        days: int = 30
    ) -> Dict[str, List]:
        """Get query metrics for a subgraph over time period.
        
        Args:
            subgraph_id: The deployment ID of the subgraph
            days: Number of days of historical data to fetch
            
        Returns:
            Dictionary containing timeseries metrics data
        """
        start_date = datetime.now() - timedelta(days=days)
        
        query = """
        query($id: ID!, $startTime: Int!) {
            subgraphDeployment(id: $id) {
                id
                dailyStats(
                    where: {timestamp_gte: $startTime}
                    orderBy: timestamp
                    orderDirection: asc
                ) {
                    timestamp
                    queryFeesAmount
                    queryFeeRebates
                    curatorQueryFees
                    signalledTokens
                    unsignalledTokens
                    dailyQueryFees
                }
            }
        }
        """
        
        variables = {
            'id': subgraph_id,
            'startTime': int(start_date.timestamp())
        }
        
        result = self._query_metrics(query, variables)
        return self._process_timeseries_data(result)

    def get_network_metrics(self, days: int = 30) -> Dict[str, List]:
        """Get network-wide metrics over time period.
        
        Args:
            days: Number of days of historical data to fetch
            
        Returns:
            Dictionary containing network metrics timeseries
        """
        start_date = datetime.now() - timedelta(days=days)
        
        query = """
        query($startTime: Int!) {
            graphNetworks {
                dailyStats(
                    where: {timestamp_gte: $startTime}
                    orderBy: timestamp
                    orderDirection: asc
                ) {
                    timestamp
                    totalQueryFees
                    totalCuratorQueryFees
                    totalSignalledTokens
                    totalSignals
                    activeSubgraphCount
                }
            }
        }
        """
        
        variables = {
            'startTime': int(start_date.timestamp())
        }
        
        result = self._query_metrics(query, variables)
        return self._process_timeseries_data(result)

    def calculate_subgraph_metrics(
        self,
        subgraph_id: str,
        days: int = 30
    ) -> Dict[str, float]:
        """Calculate key performance metrics for a subgraph.
        
        Args:
            subgraph_id: The deployment ID of the subgraph
            days: Number of days of historical data to use
            
        Returns:
            Dictionary of calculated metrics
        """
        metrics = self.get_query_metrics(subgraph_id, days)
        
        if not metrics or not metrics.get('dailyStats'):
            return {}
            
        df = pd.DataFrame(metrics['dailyStats'])
        
        # Calculate key metrics
        avg_daily_fees = df['dailyQueryFees'].mean()
        fee_growth = self._calculate_growth_rate(df['dailyQueryFees'])
        signal_growth = self._calculate_growth_rate(df['signalledTokens'])
        
        # Calculate volatility
        fee_volatility = df['dailyQueryFees'].std() / df['dailyQueryFees'].mean()
        
        # Calculate correlation with network metrics
        network_metrics = self.get_network_metrics(days)
        network_df = pd.DataFrame(network_metrics['dailyStats'])
        
        fee_correlation = df['dailyQueryFees'].corr(
            network_df['totalQueryFees']
        )
        
        return {
            'avg_daily_fees': avg_daily_fees,
            'fee_growth_rate': fee_growth,
            'signal_growth_rate': signal_growth,
            'fee_volatility': fee_volatility,
            'network_correlation': fee_correlation
        }

    def _calculate_growth_rate(self, series: pd.Series) -> float:
        """Calculate exponential growth rate of a metric.
        
        Args:
            series: Pandas series of metric values
            
        Returns:
            Calculated growth rate
        """
        if len(series) < 2:
            return 0.0
            
        start_value = series.iloc[0]
        end_value = series.iloc[-1]
        
        if start_value == 0:
            return 0.0
            
        periods = len(series) - 1
        return (end_value / start_value) ** (1/periods) - 1

    def _query_metrics(self, query: str, variables: Dict) -> Dict:
        """Execute a metrics query.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            Query result data
        """
        response = requests.post(
            self.metrics_endpoint,
            json={
                'query': query,
                'variables': variables
            }
        )
        
        response.raise_for_status()
        return response.json().get('data', {})

    def _process_timeseries_data(self, data: Dict) -> Dict[str, List]:
        """Process raw timeseries data into structured format.
        
        Args:
            data: Raw query result data
            
        Returns:
            Processed timeseries data
        """
        if 'subgraphDeployment' in data:
            return data['subgraphDeployment']
        elif 'graphNetworks' in data and data['graphNetworks']:
            return data['graphNetworks'][0]
        return {}
