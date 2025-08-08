#!/usr/bin/env python3
"""
SmartCloudOps AI - Real Data Integration System
=============================================

Replaces synthetic data with real monitoring data from multiple sources.
Supports Prometheus, CloudWatch, system metrics, log files, and external APIs.
"""

import pandas as pd
import numpy as np
import requests
import psutil
import boto3
import json
import csv
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Union
import os
import glob
import sqlite3
from prometheus_collector import PrometheusCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealDataCollector:
    """
    Comprehensive real data collection system supporting multiple data sources.
    """
    
    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.prometheus_collector = PrometheusCollector(
            prometheus_url=self.config.get('prometheus_url', 'http://3.89.229.102:9090')
        )
        
        # Initialize AWS clients if credentials are available
        self.cloudwatch = None
        try:
            self.cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
            logger.info("✅ AWS CloudWatch client initialized")
        except Exception as e:
            logger.warning(f"⚠️ CloudWatch not available: {e}")
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from file or use defaults."""
        default_config = {
            'prometheus_url': 'http://3.89.229.102:9090',
            'data_sources': ['prometheus', 'system', 'logs', 'csv'],
            'collection_interval': 60,  # seconds
            'retention_days': 30,
            'anomaly_detection_threshold': 2.5
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                logger.info(f"📋 Configuration loaded from {config_file}")
            except Exception as e:
                logger.warning(f"⚠️ Error loading config: {e}, using defaults")
        
        return default_config
    
    def collect_prometheus_metrics(self, hours_back: int = 24) -> pd.DataFrame:
        """
        Collect historical data from Prometheus.
        
        Args:
            hours_back: Hours of historical data to collect
            
        Returns:
            DataFrame with Prometheus metrics
        """
        logger.info(f"📊 Collecting Prometheus data for last {hours_back} hours")
        
        if not self.prometheus_collector.test_connection():
            logger.error("❌ Cannot connect to Prometheus")
            return pd.DataFrame()
        
        try:
            # Define time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Prometheus range queries
            range_queries = {
                'cpu_usage': 'avg(100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100))',
                'memory_usage': 'avg((1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100)',
                'disk_io': 'avg(irate(node_disk_io_time_seconds_total[5m]) * 100)',
                'network_rx': 'avg(irate(node_network_receive_bytes_total[5m]))',
                'network_tx': 'avg(irate(node_network_transmit_bytes_total[5m]))',
                'load_1m': 'avg(node_load1)',
                'load_5m': 'avg(node_load5)',
                'load_15m': 'avg(node_load15)',
                'disk_used_percent': 'avg(100 - ((node_filesystem_avail_bytes * 100) / node_filesystem_size_bytes))',
                'response_time': 'avg(rate(prometheus_http_request_duration_seconds_sum[5m]) / rate(prometheus_http_request_duration_seconds_count[5m]))'
            }
            
            all_data = []
            
            # Collect data for each metric
            for metric_name, query in range_queries.items():
                try:
                    url = f"{self.prometheus_collector.prometheus_url}/api/v1/query_range"
                    params = {
                        'query': query,
                        'start': start_time.timestamp(),
                        'end': end_time.timestamp(),
                        'step': '60s'  # 1-minute intervals
                    }
                    
                    response = requests.get(url, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data['status'] == 'success' and data['data']['result']:
                            # Extract time series data
                            for result in data['data']['result']:
                                for timestamp, value in result['values']:
                                    try:
                                        all_data.append({
                                            'timestamp': datetime.fromtimestamp(float(timestamp)),
                                            'metric': metric_name,
                                            'value': float(value),
                                            'source': 'prometheus'
                                        })
                                    except (ValueError, TypeError):
                                        continue
                        else:
                            logger.warning(f"⚠️ No data for {metric_name}")
                    else:
                        logger.error(f"❌ Query failed for {metric_name}: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"❌ Error collecting {metric_name}: {e}")
                    continue
            
            if all_data:
                # Convert to DataFrame and pivot
                df = pd.DataFrame(all_data)
                df_pivot = df.pivot_table(
                    index='timestamp', 
                    columns='metric', 
                    values='value', 
                    aggfunc='mean'
                ).reset_index()
                
                # Fill missing values
                df_pivot = df_pivot.fillna(method='ffill').fillna(method='bfill').fillna(0)
                
                logger.info(f"✅ Collected {len(df_pivot)} Prometheus data points")
                return df_pivot
            else:
                logger.warning("⚠️ No Prometheus data collected")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ Error collecting Prometheus data: {e}")
            return pd.DataFrame()
    
    def collect_system_metrics(self, duration_minutes: int = 60) -> pd.DataFrame:
        """
        Collect real-time system metrics using psutil.
        
        Args:
            duration_minutes: Duration to collect metrics
            
        Returns:
            DataFrame with system metrics
        """
        logger.info(f"💻 Collecting system metrics for {duration_minutes} minutes")
        
        data = []
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        try:
            # Collect metrics every 60 seconds
            current_time = start_time
            while current_time <= end_time:
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count()
                load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
                
                # Memory metrics
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                
                # Disk metrics
                disk_usage = psutil.disk_usage('/')
                disk_io = psutil.disk_io_counters()
                
                # Network metrics
                network_io = psutil.net_io_counters()
                
                # Process metrics
                process_count = len(psutil.pids())
                
                data_point = {
                    'timestamp': current_time,
                    'cpu_usage': cpu_percent,
                    'cpu_count': cpu_count,
                    'load_1m': load_avg[0],
                    'load_5m': load_avg[1],
                    'load_15m': load_avg[2],
                    'memory_usage': memory.percent,
                    'memory_total': memory.total / (1024**3),  # GB
                    'memory_available': memory.available / (1024**3),  # GB
                    'swap_usage': swap.percent,
                    'disk_usage': (disk_usage.used / disk_usage.total) * 100,
                    'disk_total': disk_usage.total / (1024**3),  # GB
                    'disk_free': disk_usage.free / (1024**3),  # GB
                    'disk_read_bytes': disk_io.read_bytes if disk_io else 0,
                    'disk_write_bytes': disk_io.write_bytes if disk_io else 0,
                    'network_rx': network_io.bytes_recv if network_io else 0,
                    'network_tx': network_io.bytes_sent if network_io else 0,
                    'process_count': process_count,
                    'source': 'system'
                }
                
                data.append(data_point)
                current_time += timedelta(minutes=1)
            
            df = pd.DataFrame(data)
            logger.info(f"✅ Collected {len(df)} system metric points")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error collecting system metrics: {e}")
            return pd.DataFrame()
    
    def collect_cloudwatch_metrics(self, hours_back: int = 24) -> pd.DataFrame:
        """
        Collect metrics from AWS CloudWatch.
        
        Args:
            hours_back: Hours of historical data to collect
            
        Returns:
            DataFrame with CloudWatch metrics
        """
        if not self.cloudwatch:
            logger.warning("⚠️ CloudWatch not available")
            return pd.DataFrame()
        
        logger.info(f"☁️ Collecting CloudWatch metrics for last {hours_back} hours")
        
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Define CloudWatch metrics to collect
            metrics = [
                {'Namespace': 'AWS/EC2', 'MetricName': 'CPUUtilization'},
                {'Namespace': 'AWS/EC2', 'MetricName': 'NetworkIn'},
                {'Namespace': 'AWS/EC2', 'MetricName': 'NetworkOut'},
                {'Namespace': 'AWS/EC2', 'MetricName': 'DiskReadBytes'},
                {'Namespace': 'AWS/EC2', 'MetricName': 'DiskWriteBytes'},
            ]
            
            all_data = []
            
            for metric in metrics:
                try:
                    response = self.cloudwatch.get_metric_statistics(
                        Namespace=metric['Namespace'],
                        MetricName=metric['MetricName'],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,  # 5-minute intervals
                        Statistics=['Average', 'Maximum']
                    )
                    
                    for datapoint in response['Datapoints']:
                        all_data.append({
                            'timestamp': datapoint['Timestamp'],
                            'metric': metric['MetricName'].lower(),
                            'value': datapoint['Average'],
                            'max_value': datapoint['Maximum'],
                            'source': 'cloudwatch'
                        })
                        
                except Exception as e:
                    logger.error(f"❌ Error collecting {metric['MetricName']}: {e}")
                    continue
            
            if all_data:
                df = pd.DataFrame(all_data)
                df = df.sort_values('timestamp').reset_index(drop=True)
                logger.info(f"✅ Collected {len(df)} CloudWatch data points")
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ Error collecting CloudWatch data: {e}")
            return pd.DataFrame()
    
    def load_csv_data(self, csv_path: str) -> pd.DataFrame:
        """
        Load metrics from CSV files.
        
        Args:
            csv_path: Path to CSV file or directory with CSV files
            
        Returns:
            DataFrame with CSV data
        """
        logger.info(f"📄 Loading data from CSV: {csv_path}")
        
        try:
            if os.path.isfile(csv_path):
                csv_files = [csv_path]
            elif os.path.isdir(csv_path):
                csv_files = glob.glob(os.path.join(csv_path, "*.csv"))
            else:
                logger.error(f"❌ CSV path not found: {csv_path}")
                return pd.DataFrame()
            
            all_data = []
            
            for file_path in csv_files:
                try:
                    df = pd.read_csv(file_path)
                    
                    # Try to standardize timestamp column
                    timestamp_cols = ['timestamp', 'time', 'datetime', 'date']
                    timestamp_col = None
                    
                    for col in timestamp_cols:
                        if col in df.columns:
                            timestamp_col = col
                            break
                    
                    if timestamp_col:
                        df['timestamp'] = pd.to_datetime(df[timestamp_col])
                        df['source'] = f'csv_{os.path.basename(file_path)}'
                        all_data.append(df)
                        logger.info(f"✅ Loaded {len(df)} rows from {file_path}")
                    else:
                        logger.warning(f"⚠️ No timestamp column found in {file_path}")
                        
                except Exception as e:
                    logger.error(f"❌ Error loading {file_path}: {e}")
                    continue
            
            if all_data:
                combined_df = pd.concat(all_data, ignore_index=True)
                combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
                logger.info(f"✅ Combined {len(combined_df)} CSV data points")
                return combined_df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ Error loading CSV data: {e}")
            return pd.DataFrame()
    
    def parse_log_metrics(self, log_path: str, patterns: Dict[str, str]) -> pd.DataFrame:
        """
        Extract metrics from log files using regex patterns.
        
        Args:
            log_path: Path to log file or directory
            patterns: Dictionary of metric_name -> regex_pattern
            
        Returns:
            DataFrame with parsed log metrics
        """
        logger.info(f"📝 Parsing metrics from logs: {log_path}")
        
        import re
        
        try:
            if os.path.isfile(log_path):
                log_files = [log_path]
            elif os.path.isdir(log_path):
                log_files = glob.glob(os.path.join(log_path, "*.log"))
            else:
                logger.error(f"❌ Log path not found: {log_path}")
                return pd.DataFrame()
            
            all_data = []
            
            for file_path in log_files:
                try:
                    with open(file_path, 'r') as f:
                        for line_num, line in enumerate(f):
                            # Try to extract timestamp
                            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})', line)
                            if not timestamp_match:
                                continue
                            
                            timestamp = pd.to_datetime(timestamp_match.group(1))
                            
                            # Extract metrics using patterns
                            for metric_name, pattern in patterns.items():
                                match = re.search(pattern, line)
                                if match:
                                    try:
                                        value = float(match.group(1))
                                        all_data.append({
                                            'timestamp': timestamp,
                                            'metric': metric_name,
                                            'value': value,
                                            'source': f'log_{os.path.basename(file_path)}',
                                            'line_number': line_num + 1
                                        })
                                    except (ValueError, IndexError):
                                        continue
                                        
                except Exception as e:
                    logger.error(f"❌ Error parsing {file_path}: {e}")
                    continue
            
            if all_data:
                df = pd.DataFrame(all_data)
                df = df.sort_values('timestamp').reset_index(drop=True)
                logger.info(f"✅ Parsed {len(df)} metric points from logs")
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"❌ Error parsing log metrics: {e}")
            return pd.DataFrame()
    
    def collect_comprehensive_dataset(self, hours_back: int = 24) -> pd.DataFrame:
        """
        Collect data from all available sources and combine into unified dataset.
        
        Args:
            hours_back: Hours of historical data to collect
            
        Returns:
            Unified DataFrame with all metrics
        """
        logger.info("🔄 Collecting comprehensive real data from all sources")
        
        datasets = []
        
        # 1. Prometheus data
        prometheus_data = self.collect_prometheus_metrics(hours_back)
        if not prometheus_data.empty:
            datasets.append(prometheus_data)
            logger.info(f"✅ Added Prometheus data: {len(prometheus_data)} points")
        
        # 2. System metrics (collect for 1 hour as sample)
        system_data = self.collect_system_metrics(duration_minutes=60)
        if not system_data.empty:
            datasets.append(system_data)
            logger.info(f"✅ Added system data: {len(system_data)} points")
        
        # 3. CloudWatch data
        cloudwatch_data = self.collect_cloudwatch_metrics(hours_back)
        if not cloudwatch_data.empty:
            datasets.append(cloudwatch_data)
            logger.info(f"✅ Added CloudWatch data: {len(cloudwatch_data)} points")
        
        # 4. CSV data (if available)
        csv_paths = ['../data/', '/var/log/metrics/', './metrics.csv']
        for csv_path in csv_paths:
            if os.path.exists(csv_path):
                csv_data = self.load_csv_data(csv_path)
                if not csv_data.empty:
                    datasets.append(csv_data)
                    logger.info(f"✅ Added CSV data from {csv_path}: {len(csv_data)} points")
        
        # 5. Log file metrics (if available)
        log_patterns = {
            'response_time': r'response_time[:\s]+(\d+\.?\d*)',
            'cpu_usage': r'cpu[:\s]+(\d+\.?\d*)%?',
            'memory_usage': r'memory[:\s]+(\d+\.?\d*)%?',
            'disk_io': r'disk_io[:\s]+(\d+\.?\d*)',
            'network_io': r'network[:\s]+(\d+\.?\d*)'
        }
        
        log_paths = ['/var/log/', '../logs/', './app.log']
        for log_path in log_paths:
            if os.path.exists(log_path):
                log_data = self.parse_log_metrics(log_path, log_patterns)
                if not log_data.empty:
                    datasets.append(log_data)
                    logger.info(f"✅ Added log data from {log_path}: {len(log_data)} points")
        
        # Combine all datasets
        if datasets:
            logger.info("🔄 Combining datasets from all sources")
            
            # Standardize column names and merge
            unified_data = []
            
            for df in datasets:
                # Ensure timestamp column exists
                if 'timestamp' not in df.columns:
                    logger.warning("⚠️ Skipping dataset without timestamp column")
                    continue
                
                # Convert to standard format
                df_std = df.copy()
                df_std['timestamp'] = pd.to_datetime(df_std['timestamp'])
                
                # Add to unified data
                unified_data.append(df_std)
            
            if unified_data:
                # Combine all dataframes
                combined_df = pd.concat(unified_data, ignore_index=True, sort=False)
                
                # Sort by timestamp
                combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
                
                # Remove duplicates
                combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='first')
                
                # Fill missing values
                numeric_columns = combined_df.select_dtypes(include=[np.number]).columns
                combined_df[numeric_columns] = combined_df[numeric_columns].fillna(method='ffill').fillna(method='bfill').fillna(0)
                
                # Add anomaly labels (basic heuristic - can be improved)
                combined_df = self._add_anomaly_labels(combined_df)
                
                logger.info(f"✅ Unified dataset created: {len(combined_df)} total points")
                logger.info(f"📊 Data sources: {combined_df['source'].unique()}")
                logger.info(f"📅 Time range: {combined_df['timestamp'].min()} to {combined_df['timestamp'].max()}")
                
                return combined_df
            else:
                logger.warning("⚠️ No valid datasets found")
                return pd.DataFrame()
        else:
            logger.warning("⚠️ No data sources available")
            return pd.DataFrame()
    
    def _add_anomaly_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add basic anomaly labels using statistical methods.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with anomaly labels
        """
        logger.info("🏷️ Adding anomaly labels using statistical methods")
        
        try:
            df = df.copy()
            df['is_anomaly'] = 0
            
            # Define metrics to check for anomalies
            anomaly_metrics = ['cpu_usage', 'memory_usage', 'disk_io', 'network_rx', 'network_tx', 'response_time']
            
            for metric in anomaly_metrics:
                if metric in df.columns:
                    # Use IQR method for anomaly detection
                    Q1 = df[metric].quantile(0.25)
                    Q3 = df[metric].quantile(0.75)
                    IQR = Q3 - Q1
                    
                    # Define outliers as values outside 1.5 * IQR
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    # Mark anomalies
                    anomalies = (df[metric] < lower_bound) | (df[metric] > upper_bound)
                    df.loc[anomalies, 'is_anomaly'] = 1
            
            anomaly_rate = df['is_anomaly'].mean()
            logger.info(f"📊 Anomaly rate: {anomaly_rate:.2%}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error adding anomaly labels: {e}")
            df['is_anomaly'] = 0
            return df
    
    def save_real_data(self, df: pd.DataFrame, output_path: str = '../data/real_monitoring_data.csv'):
        """
        Save collected real data to file.
        
        Args:
            df: DataFrame to save
            output_path: Output file path
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            df.to_csv(output_path, index=False)
            logger.info(f"💾 Real data saved to {output_path}")
            
            # Also save metadata
            metadata = {
                'collection_timestamp': datetime.now().isoformat(),
                'total_points': len(df),
                'columns': list(df.columns),
                'data_sources': list(df['source'].unique()) if 'source' in df.columns else [],
                'time_range': {
                    'start': df['timestamp'].min().isoformat() if 'timestamp' in df.columns else None,
                    'end': df['timestamp'].max().isoformat() if 'timestamp' in df.columns else None
                },
                'anomaly_rate': df['is_anomaly'].mean() if 'is_anomaly' in df.columns else 0
            }
            
            metadata_path = output_path.replace('.csv', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"📋 Metadata saved to {metadata_path}")
            
        except Exception as e:
            logger.error(f"❌ Error saving data: {e}")

def main():
    """Test the real data collection system."""
    logger.info("🔍 Testing Real Data Collection System")
    print("=" * 50)
    
    # Initialize collector
    collector = RealDataCollector()
    
    # Collect comprehensive dataset
    real_data = collector.collect_comprehensive_dataset(hours_back=12)
    
    if not real_data.empty:
        print(f"\n✅ Successfully collected {len(real_data)} real data points")
        print(f"📊 Columns: {list(real_data.columns)}")
        print(f"📅 Time range: {real_data['timestamp'].min()} to {real_data['timestamp'].max()}")
        
        if 'source' in real_data.columns:
            print(f"🔗 Data sources: {real_data['source'].unique()}")
        
        if 'is_anomaly' in real_data.columns:
            print(f"🚨 Anomaly rate: {real_data['is_anomaly'].mean():.2%}")
        
        # Save the data
        collector.save_real_data(real_data)
        
        print("\n🎯 Real data collection successful! Ready for ML training.")
    else:
        print("❌ No real data collected. Please check data sources.")

if __name__ == "__main__":
    main()
