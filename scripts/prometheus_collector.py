#!/usr/bin/env python3
"""
SmartCloudOps AI - Prometheus Data Collector
==========================================

Collects real-time metrics from Prometheus for anomaly detection training.
"""

import requests
import os
import pandas as pd
import json
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrometheusCollector:
    """
    Collects metrics from Prometheus monitoring stack.
    """
    
    def __init__(self, prometheus_url: str | None = None):
        self.prometheus_url = prometheus_url or os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
        
        # Common Prometheus queries for infrastructure monitoring
        self.queries = {
            'cpu_usage': 'avg(100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100))',
            'memory_usage': 'avg((1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100)',
            'disk_io': 'avg(irate(node_disk_io_time_seconds_total[5m]) * 100)',
            'network_io': 'avg(irate(node_network_receive_bytes_total[5m]) + irate(node_network_transmit_bytes_total[5m]))',
            'http_requests': 'avg(rate(prometheus_http_requests_total[5m]))',
            'up_status': 'up'
        }
    
    def test_connection(self):
        """Test connection to Prometheus."""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/status/config", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Prometheus connection successful")
                return True
            else:
                logger.error(f"❌ Prometheus connection failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Error connecting to Prometheus: {e}")
            return False
    
    def collect_current_metrics(self):
        """Collect current metric values."""
        metrics = {}
        
        for metric_name, query in self.queries.items():
            try:
                url = f"{self.prometheus_url}/api/v1/query"
                params = {'query': query}
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data['status'] == 'success' and data['data']['result']:
                        value = float(data['data']['result'][0]['value'][1])
                        metrics[metric_name] = value
                        logger.info(f"📊 {metric_name}: {value:.2f}")
                    else:
                        logger.warning(f"⚠️ No data for {metric_name}")
                        metrics[metric_name] = 0.0
                else:
                    logger.error(f"❌ Query failed for {metric_name}: {response.status_code}")
                    metrics[metric_name] = 0.0
                    
            except Exception as e:
                logger.error(f"❌ Error collecting {metric_name}: {e}")
                metrics[metric_name] = 0.0
        
        return metrics

def main():
    """Test Prometheus data collection."""
    collector = PrometheusCollector()
    
    print("🔍 Testing Prometheus Data Collection")
    print("=" * 40)
    
    # Test connection
    if collector.test_connection():
        # Collect current metrics
        metrics = collector.collect_current_metrics()
        
        print("\n📊 Current Metrics:")
        for metric, value in metrics.items():
            print(f"   {metric}: {value}")
    else:
        print("❌ Cannot connect to Prometheus. Using synthetic data for training.")

if __name__ == "__main__":
    main()
