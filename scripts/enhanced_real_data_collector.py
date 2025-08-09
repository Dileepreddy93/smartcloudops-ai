#!/usr/bin/env python3
"""
Enhanced Real Data Collector for SmartCloudOps AI
=================================================

Comprehensive data collection system with multiple sources and improved quality.
"""

import json
import logging
import os
import requests
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from scipy import stats

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedRealDataCollector:
    """Enhanced real data collector with multiple sources and improved quality."""
    
    def __init__(self, config_path: str = "real_data_config.json"):
        """Initialize the enhanced data collector."""
        self.config = self.load_config(config_path)
        self.collected_data = []
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "data_sources": {
                "system": {"enabled": True},
                "application_metrics": {"enabled": True},
                "prometheus": {"enabled": True}
            },
            "collection_settings": {
                "default_hours_back": 24,
                "max_data_points": 10000
            }
        }
    
    def collect_system_metrics_enhanced(self, duration_minutes: int = 60) -> List[Dict]:
        """Collect enhanced system metrics with more detail."""
        logger.info(f"🔧 Collecting enhanced system metrics for {duration_minutes} minutes")
        
        data_points = []
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        interval_seconds = 30  # Collect every 30 seconds for higher resolution
        current_time = start_time
        
        while current_time <= end_time:
            try:
                # Basic system metrics
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
                
                # Enhanced metrics
                boot_time = psutil.boot_time()
                
                # Per-CPU metrics
                cpu_per_core = psutil.cpu_percent(percpu=True, interval=1)
                
                # Context switches and interrupts
                cpu_stats = psutil.cpu_stats()
                
                data_point = {
                    'timestamp': current_time.isoformat(),
                    'cpu_usage': cpu_percent,
                    'cpu_count': cpu_count,
                    'cpu_per_core_avg': np.mean(cpu_per_core),
                    'cpu_per_core_max': np.max(cpu_per_core),
                    'cpu_per_core_std': np.std(cpu_per_core),
                    'load_1m': load_avg[0],
                    'load_5m': load_avg[1],
                    'load_15m': load_avg[2],
                    'memory_usage': memory.percent,
                    'memory_total_gb': memory.total / (1024**3),
                    'memory_available_gb': memory.available / (1024**3),
                    'memory_used_gb': memory.used / (1024**3),
                    'swap_usage': swap.percent,
                    'swap_total_gb': swap.total / (1024**3),
                    'disk_usage': (disk_usage.used / disk_usage.total) * 100,
                    'disk_total_gb': disk_usage.total / (1024**3),
                    'disk_free_gb': disk_usage.free / (1024**3),
                    'disk_read_bytes': disk_io.read_bytes if disk_io else 0,
                    'disk_write_bytes': disk_io.write_bytes if disk_io else 0,
                    'disk_read_count': disk_io.read_count if disk_io else 0,
                    'disk_write_count': disk_io.write_count if disk_io else 0,
                    'network_rx_bytes': network_io.bytes_recv if network_io else 0,
                    'network_tx_bytes': network_io.bytes_sent if network_io else 0,
                    'network_rx_packets': network_io.packets_recv if network_io else 0,
                    'network_tx_packets': network_io.packets_sent if network_io else 0,
                    'network_errors': (network_io.errin + network_io.errout) if network_io else 0,
                    'network_dropped': (network_io.dropin + network_io.dropout) if network_io else 0,
                    'process_count': process_count,
                    'context_switches': cpu_stats.ctx_switches,
                    'interrupts': cpu_stats.interrupts,
                    'soft_interrupts': cpu_stats.soft_interrupts,
                    'boot_time': boot_time,
                    'uptime_hours': (time.time() - boot_time) / 3600,
                    'source': 'enhanced_system',
                    'collection_method': 'psutil_enhanced'
                }
                
                # Add derived metrics
                data_point['io_ratio'] = data_point['disk_write_bytes'] / max(data_point['disk_read_bytes'], 1)
                data_point['network_ratio'] = data_point['network_tx_bytes'] / max(data_point['network_rx_bytes'], 1)
                data_point['load_indicator'] = (data_point['cpu_usage'] + data_point['memory_usage']) / 2
                data_point['io_intensity'] = (data_point['disk_read_bytes'] + data_point['disk_write_bytes']) / 1024**2  # MB
                
                data_points.append(data_point)
                current_time += timedelta(seconds=interval_seconds)
                
                # Sleep for the interval
                time.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"❌ Error collecting metrics at {current_time}: {e}")
                current_time += timedelta(seconds=interval_seconds)
                continue
        
        logger.info(f"✅ Collected {len(data_points)} enhanced system data points")
        return data_points
    
    def collect_application_metrics(self) -> List[Dict]:
        """Collect application-level metrics."""
        logger.info("📱 Collecting application metrics")
        
        endpoints = self.config.get("data_sources", {}).get("application_metrics", {}).get("endpoints", [])
        app_data = []
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    # Parse Prometheus format or JSON
                    if 'json' in response.headers.get('content-type', ''):
                        metrics = response.json()
                    else:
                        # Parse Prometheus text format
                        metrics = self.parse_prometheus_metrics(response.text)
                    
                    app_data.append({
                        'timestamp': datetime.now().isoformat(),
                        'endpoint': endpoint,
                        'metrics': metrics,
                        'source': 'application'
                    })
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to collect from {endpoint}: {e}")
        
        return app_data
    
    def parse_prometheus_metrics(self, text: str) -> Dict:
        """Parse Prometheus text format."""
        metrics = {}
        for line in text.split('\n'):
            if line.startswith('#') or not line.strip():
                continue
            try:
                parts = line.split(' ')
                metric_name = parts[0]
                metric_value = float(parts[1])
                metrics[metric_name] = metric_value
            except:
                continue
        return metrics
    
    def add_enhanced_anomaly_detection(self, data_points: List[Dict]) -> List[Dict]:
        """Add multiple anomaly detection methods."""
        logger.info("🔍 Adding enhanced anomaly detection")
        
        if len(data_points) < 10:
            logger.warning("⚠️ Not enough data points for anomaly detection")
            for point in data_points:
                point['is_anomaly'] = 0
                point['anomaly_score'] = 0.0
                point['anomaly_method'] = 'insufficient_data'
            return data_points
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data_points)
        
        # Select numeric columns for anomaly detection
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [col for col in numeric_cols if col not in ['timestamp', 'boot_time']]
        
        if not numeric_cols:
            logger.warning("⚠️ No numeric columns found for anomaly detection")
            for point in data_points:
                point['is_anomaly'] = 0
                point['anomaly_score'] = 0.0
                point['anomaly_method'] = 'no_numeric_data'
            return data_points
        
        # Fill missing values
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        
        # Method 1: IQR-based detection
        iqr_anomalies = self.detect_anomalies_iqr(df[numeric_cols])
        
        # Method 2: Z-score based detection
        zscore_anomalies = self.detect_anomalies_zscore(df[numeric_cols])
        
        # Method 3: Isolation Forest
        isolation_anomalies, isolation_scores = self.detect_anomalies_isolation_forest(df[numeric_cols])
        
        # Method 4: Local Outlier Factor
        lof_anomalies, lof_scores = self.detect_anomalies_lof(df[numeric_cols])
        
        # Combine anomaly detections
        for i, point in enumerate(data_points):
            anomaly_votes = sum([
                iqr_anomalies[i],
                zscore_anomalies[i],
                isolation_anomalies[i],
                lof_anomalies[i]
            ])
            
            # Mark as anomaly if 2 or more methods agree
            point['is_anomaly'] = 1 if anomaly_votes >= 2 else 0
            point['anomaly_score'] = (isolation_scores[i] + lof_scores[i]) / 2
            point['anomaly_votes'] = anomaly_votes
            point['iqr_anomaly'] = iqr_anomalies[i]
            point['zscore_anomaly'] = zscore_anomalies[i]
            point['isolation_anomaly'] = isolation_anomalies[i]
            point['lof_anomaly'] = lof_anomalies[i]
            point['anomaly_method'] = 'ensemble'
        
        anomaly_rate = sum(point['is_anomaly'] for point in data_points) / len(data_points)
        logger.info(f"📊 Enhanced anomaly detection complete. Anomaly rate: {anomaly_rate:.2%}")
        
        return data_points
    
    def detect_anomalies_iqr(self, data: pd.DataFrame) -> List[int]:
        """Detect anomalies using IQR method."""
        anomalies = [0] * len(data)
        
        for col in data.columns:
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            col_anomalies = (data[col] < lower_bound) | (data[col] > upper_bound)
            for i, is_anomaly in enumerate(col_anomalies):
                if is_anomaly:
                    anomalies[i] = 1
        
        return anomalies
    
    def detect_anomalies_zscore(self, data: pd.DataFrame, threshold: float = 3.0) -> List[int]:
        """Detect anomalies using Z-score method."""
        anomalies = [0] * len(data)
        
        for col in data.columns:
            z_scores = np.abs(stats.zscore(data[col]))
            col_anomalies = z_scores > threshold
            
            for i, is_anomaly in enumerate(col_anomalies):
                if is_anomaly:
                    anomalies[i] = 1
        
        return anomalies
    
    def detect_anomalies_isolation_forest(self, data: pd.DataFrame) -> tuple:
        """Detect anomalies using Isolation Forest."""
        try:
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            anomaly_labels = iso_forest.fit_predict(data)
            anomaly_scores = iso_forest.score_samples(data)
            
            # Convert to binary (1 for anomaly, 0 for normal)
            anomalies = [1 if label == -1 else 0 for label in anomaly_labels]
            
            return anomalies, list(anomaly_scores)
            
        except Exception as e:
            logger.warning(f"⚠️ Isolation Forest failed: {e}")
            return [0] * len(data), [0.0] * len(data)
    
    def detect_anomalies_lof(self, data: pd.DataFrame) -> tuple:
        """Detect anomalies using Local Outlier Factor."""
        try:
            lof = LocalOutlierFactor(n_neighbors=min(20, len(data)-1), contamination=0.1)
            anomaly_labels = lof.fit_predict(data)
            anomaly_scores = lof.negative_outlier_factor_
            
            # Convert to binary
            anomalies = [1 if label == -1 else 0 for label in anomaly_labels]
            
            return anomalies, list(anomaly_scores)
            
        except Exception as e:
            logger.warning(f"⚠️ LOF failed: {e}")
            return [0] * len(data), [0.0] * len(data)
    
    def add_feature_engineering(self, data_points: List[Dict]) -> List[Dict]:
        """Add engineered features to improve model performance."""
        logger.info("🔧 Adding feature engineering")
        
        if len(data_points) < 5:
            return data_points
        
        # Convert to DataFrame
        df = pd.DataFrame(data_points)
        
        # Sort by timestamp
        df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp_dt')
        
        # Rolling averages
        for window in [5, 15, 30]:
            if len(df) >= window:
                for col in ['cpu_usage', 'memory_usage', 'load_1m']:
                    if col in df.columns:
                        df[f'{col}_rolling_{window}'] = df[col].rolling(window=window, min_periods=1).mean()
        
        # Derivative features (rate of change)
        for col in ['cpu_usage', 'memory_usage', 'load_1m']:
            if col in df.columns:
                df[f'{col}_diff'] = df[col].diff().fillna(0)
                df[f'{col}_pct_change'] = df[col].pct_change().fillna(0).replace([np.inf, -np.inf], 0)
        
        # Time-based features
        df['hour'] = df['timestamp_dt'].dt.hour
        df['day_of_week'] = df['timestamp_dt'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_business_hours'] = ((df['hour'] >= 9) & (df['hour'] <= 17)).astype(int)
        df['is_night'] = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)
        
        # Interaction features
        df['cpu_memory_product'] = df.get('cpu_usage', 0) * df.get('memory_usage', 0)
        df['load_cpu_ratio'] = df.get('load_1m', 0) / (df.get('cpu_usage', 1) + 1e-6)
        
        # Convert back to list of dictionaries
        df = df.drop(['timestamp_dt'], axis=1)
        enhanced_data = df.to_dict('records')
        
        logger.info(f"✅ Added {len(df.columns) - len(data_points[0])} engineered features")
        return enhanced_data
    
    def save_enhanced_data(self, data_points: List[Dict], output_dir: str = "../data") -> str:
        """Save enhanced data with metadata."""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON format
        json_path = os.path.join(output_dir, f"enhanced_real_data_{timestamp}.json")
        with open(json_path, 'w') as f:
            json.dump(data_points, f, indent=2)
        
        # Save CSV format
        csv_path = os.path.join(output_dir, f"enhanced_real_data_{timestamp}.csv")
        df = pd.DataFrame(data_points)
        df.to_csv(csv_path, index=False)
        
        # Save metadata
        metadata = {
            'collection_timestamp': datetime.now().isoformat(),
            'total_data_points': len(data_points),
            'anomaly_rate': sum(point.get('is_anomaly', 0) for point in data_points) / len(data_points),
            'features_count': len(data_points[0].keys()) if data_points else 0,
            'time_range': {
                'start': min(point['timestamp'] for point in data_points) if data_points else None,
                'end': max(point['timestamp'] for point in data_points) if data_points else None
            },
            'collection_methods': list(set(point.get('source', 'unknown') for point in data_points)),
            'feature_names': list(data_points[0].keys()) if data_points else []
        }
        
        metadata_path = os.path.join(output_dir, f"enhanced_real_data_{timestamp}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"💾 Enhanced data saved:")
        logger.info(f"   JSON: {json_path}")
        logger.info(f"   CSV: {csv_path}")
        logger.info(f"   Metadata: {metadata_path}")
        
        return json_path
    
    def run_enhanced_collection(self, hours_back: int = 2) -> str:
        """Run the complete enhanced data collection pipeline."""
        logger.info("🚀 Starting enhanced real data collection pipeline")
        print("=" * 60)
        
        # Collect system metrics with higher resolution
        duration_minutes = hours_back * 60
        system_data = self.collect_system_metrics_enhanced(duration_minutes=min(duration_minutes, 120))  # Limit to 2 hours for demo
        
        # Collect application metrics
        app_data = self.collect_application_metrics()
        
        # Combine all data
        all_data = system_data
        
        if all_data:
            # Add enhanced anomaly detection
            all_data = self.add_enhanced_anomaly_detection(all_data)
            
            # Add feature engineering
            all_data = self.add_feature_engineering(all_data)
            
            # Save enhanced data
            output_path = self.save_enhanced_data(all_data)
            
            # Print summary
            anomaly_count = sum(point.get('is_anomaly', 0) for point in all_data)
            anomaly_rate = anomaly_count / len(all_data)
            
            print(f"\n✅ Enhanced data collection complete!")
            print(f"📊 Total data points: {len(all_data)}")
            print(f"🚨 Anomalies detected: {anomaly_count} ({anomaly_rate:.2%})")
            print(f"🔧 Features per data point: {len(all_data[0].keys())}")
            print(f"💾 Saved to: {output_path}")
            
            return output_path
        else:
            logger.error("❌ No data collected")
            return ""


def main():
    """Run the enhanced data collection."""
    print("🔍 SmartCloudOps AI - Enhanced Real Data Collection")
    print("=" * 60)
    
    # Initialize collector
    collector = EnhancedRealDataCollector()
    
    # Run enhanced collection
    output_path = collector.run_enhanced_collection(hours_back=1)  # 1 hour of high-resolution data
    
    if output_path:
        print("\n🎯 Next steps to improve your model:")
        print("1. Use this enhanced dataset for training")
        print("2. Experiment with different anomaly detection thresholds")
        print("3. Add more application-specific metrics")
        print("4. Set up continuous data collection")
        print("5. Implement feedback loops for model improvement")
    else:
        print("❌ Data collection failed")


if __name__ == "__main__":
    main()
