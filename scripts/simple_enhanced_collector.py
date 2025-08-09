#!/usr/bin/env python3
"""
Simple Enhanced Real Data Collector for SmartCloudOps AI
======================================================

Lightweight version that works without additional dependencies.
"""

import json
import os
import time
import psutil
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleEnhancedCollector:
    """Simple enhanced data collector with improved metrics."""
    
    def __init__(self):
        self.collected_data = []
        
    def collect_enhanced_system_metrics(self, duration_minutes: int = 30) -> list:
        """Collect enhanced system metrics with higher resolution."""
        logger.info(f"🔧 Collecting enhanced system metrics for {duration_minutes} minutes")
        
        data_points = []
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        interval_seconds = 30  # Collect every 30 seconds
        current_time = start_time
        
        point_count = 0
        max_points = duration_minutes * 2  # 2 points per minute
        
        while point_count < max_points and current_time <= end_time:
            try:
                # Basic system metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk_usage = psutil.disk_usage('/')
                
                # Try to get additional metrics
                try:
                    load_avg = psutil.getloadavg()
                except:
                    load_avg = (0, 0, 0)
                
                try:
                    disk_io = psutil.disk_io_counters()
                    disk_read = disk_io.read_bytes if disk_io else 0
                    disk_write = disk_io.write_bytes if disk_io else 0
                except:
                    disk_read = disk_write = 0
                
                try:
                    network_io = psutil.net_io_counters()
                    net_rx = network_io.bytes_recv if network_io else 0
                    net_tx = network_io.bytes_sent if network_io else 0
                except:
                    net_rx = net_tx = 0
                
                try:
                    process_count = len(psutil.pids())
                except:
                    process_count = 0
                
                # Enhanced data point
                data_point = {
                    'timestamp': current_time.isoformat(),
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory.percent,
                    'memory_total_gb': memory.total / (1024**3),
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_usage': (disk_usage.used / disk_usage.total) * 100,
                    'disk_total_gb': disk_usage.total / (1024**3),
                    'disk_free_gb': disk_usage.free / (1024**3),
                    'disk_read_bytes': disk_read,
                    'disk_write_bytes': disk_write,
                    'network_rx_bytes': net_rx,
                    'network_tx_bytes': net_tx,
                    'load_1m': load_avg[0],
                    'load_5m': load_avg[1],
                    'load_15m': load_avg[2],
                    'process_count': process_count,
                    'source': 'enhanced_system',
                    
                    # Derived metrics
                    'disk_io_total': disk_read + disk_write,
                    'network_io_total': net_rx + net_tx,
                    'system_stress': (cpu_percent + memory.percent) / 2,
                    
                    # Time-based features
                    'hour': current_time.hour,
                    'day_of_week': current_time.weekday(),
                    'is_weekend': 1 if current_time.weekday() >= 5 else 0,
                    'is_business_hours': 1 if 9 <= current_time.hour <= 17 else 0,
                    'is_night': 1 if current_time.hour >= 22 or current_time.hour <= 6 else 0,
                }
                
                # Add rolling averages if we have enough data
                if len(data_points) >= 5:
                    recent_cpu = [p['cpu_usage'] for p in data_points[-5:]]
                    recent_memory = [p['memory_usage'] for p in data_points[-5:]]
                    data_point['cpu_usage_ma_5'] = sum(recent_cpu) / len(recent_cpu)
                    data_point['memory_usage_ma_5'] = sum(recent_memory) / len(recent_memory)
                else:
                    data_point['cpu_usage_ma_5'] = cpu_percent
                    data_point['memory_usage_ma_5'] = memory.percent
                
                # Enhanced anomaly detection
                anomaly_score = self.calculate_anomaly_score(data_point, data_points)
                data_point['is_anomaly'] = 1 if anomaly_score > 0.7 else 0
                data_point['anomaly_score'] = anomaly_score
                
                # Data quality score
                data_point['data_quality_score'] = self.calculate_quality_score(data_point)
                
                data_points.append(data_point)
                
                # Progress indicator
                if point_count % 10 == 0:
                    print(f"   Collected {point_count + 1}/{max_points} data points...")
                
                point_count += 1
                current_time += timedelta(seconds=interval_seconds)
                
                # Sleep for the interval
                time.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"❌ Error collecting metrics at point {point_count}: {e}")
                current_time += timedelta(seconds=interval_seconds)
                point_count += 1
                continue
        
        logger.info(f"✅ Collected {len(data_points)} enhanced data points")
        return data_points
    
    def calculate_anomaly_score(self, current_point, historical_points):
        """Calculate anomaly score for current data point."""
        if len(historical_points) < 5:
            return 0.0
        
        # Compare against recent history
        recent_points = historical_points[-10:] if len(historical_points) >= 10 else historical_points
        
        anomaly_indicators = 0
        total_checks = 0
        
        # Check key metrics against recent averages
        metrics_to_check = ['cpu_usage', 'memory_usage', 'system_stress']
        
        for metric in metrics_to_check:
            if metric in current_point:
                recent_values = [p.get(metric, 0) for p in recent_points]
                if recent_values:
                    avg_recent = sum(recent_values) / len(recent_values)
                    max_recent = max(recent_values)
                    
                    current_value = current_point[metric]
                    
                    # Check if current value is significantly higher
                    if current_value > avg_recent * 1.5 or current_value > max_recent * 1.2:
                        anomaly_indicators += 1
                    
                    total_checks += 1
        
        # Additional checks
        if current_point.get('cpu_usage', 0) > 85:
            anomaly_indicators += 1
        if current_point.get('memory_usage', 0) > 90:
            anomaly_indicators += 1
        if current_point.get('system_stress', 0) > 80:
            anomaly_indicators += 1
        
        total_checks += 3
        
        # Return anomaly score (0-1)
        return min(anomaly_indicators / total_checks if total_checks > 0 else 0, 1.0)
    
    def calculate_quality_score(self, data_point):
        """Calculate quality score for data point."""
        score = 1.0
        
        # Check for missing or zero values in key metrics
        key_metrics = ['cpu_usage', 'memory_usage', 'disk_usage']
        for metric in key_metrics:
            if data_point.get(metric, 0) == 0:
                score *= 0.9
        
        # Boost score for complete data
        if all(data_point.get(key) is not None for key in data_point.keys()):
            score *= 1.1
        
        return min(score, 1.0)
    
    def add_synthetic_anomalies(self, data_points, anomaly_rate=0.05):
        """Add some synthetic anomalies to improve training."""
        logger.info(f"🚨 Adding synthetic anomalies ({anomaly_rate:.1%} rate)")
        
        num_anomalies = int(len(data_points) * anomaly_rate)
        anomaly_indices = random.sample(range(len(data_points)), num_anomalies)
        
        for idx in anomaly_indices:
            point = data_points[idx]
            
            # Spike some metrics to create realistic anomalies
            if random.random() < 0.7:  # CPU spike
                point['cpu_usage'] = min(100, point['cpu_usage'] * random.uniform(1.5, 2.5))
            
            if random.random() < 0.5:  # Memory spike
                point['memory_usage'] = min(100, point['memory_usage'] * random.uniform(1.3, 2.0))
            
            if random.random() < 0.3:  # System stress
                point['system_stress'] = (point['cpu_usage'] + point['memory_usage']) / 2
            
            # Mark as anomaly
            point['is_anomaly'] = 1
            point['anomaly_score'] = random.uniform(0.7, 1.0)
            point['synthetic_anomaly'] = 1
        
        logger.info(f"✅ Added {num_anomalies} synthetic anomalies")
        return data_points
    
    def save_enhanced_data(self, data_points, output_dir="../data"):
        """Save enhanced data with metadata."""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON format
        json_path = os.path.join(output_dir, f"enhanced_real_data_{timestamp}.json")
        with open(json_path, 'w') as f:
            json.dump(data_points, f, indent=2)
        
        # Save CSV-like format
        csv_path = os.path.join(output_dir, f"enhanced_real_data_{timestamp}.csv")
        if data_points:
            headers = list(data_points[0].keys())
            with open(csv_path, 'w') as f:
                f.write(','.join(headers) + '\n')
                for point in data_points:
                    values = [str(point.get(header, '')) for header in headers]
                    f.write(','.join(values) + '\n')
        
        # Save metadata
        metadata = {
            'collection_timestamp': datetime.now().isoformat(),
            'total_data_points': len(data_points),
            'anomaly_count': sum(1 for p in data_points if p.get('is_anomaly', 0) == 1),
            'anomaly_rate': sum(1 for p in data_points if p.get('is_anomaly', 0) == 1) / len(data_points),
            'features_count': len(data_points[0].keys()) if data_points else 0,
            'collection_interval_seconds': 30,
            'enhancement_version': '1.0',
            'quality_metrics': {
                'avg_quality_score': sum(p.get('data_quality_score', 0) for p in data_points) / len(data_points),
                'complete_data_points': sum(1 for p in data_points if p.get('data_quality_score', 0) >= 0.9)
            }
        }
        
        metadata_path = os.path.join(output_dir, f"enhanced_real_data_{timestamp}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"💾 Enhanced data saved:")
        logger.info(f"   JSON: {json_path}")
        logger.info(f"   CSV: {csv_path}")
        logger.info(f"   Metadata: {metadata_path}")
        
        return json_path
    
    def run_enhanced_collection(self, duration_minutes=120):
        """Run the complete enhanced data collection."""
        logger.info("🚀 Starting enhanced real data collection")
        print("=" * 60)
        print(f"⏱️ Collection Duration: {duration_minutes} minutes")
        print(f"📊 Collection Interval: 30 seconds")
        print(f"📈 Expected Data Points: {duration_minutes * 2}")
        print("=" * 60)
        
        # Collect enhanced system metrics
        data_points = self.collect_enhanced_system_metrics(duration_minutes)
        
        if data_points:
            # Add some synthetic anomalies for better training
            data_points = self.add_synthetic_anomalies(data_points)
            
            # Save enhanced data
            output_path = self.save_enhanced_data(data_points)
            
            # Print summary
            anomaly_count = sum(1 for p in data_points if p.get('is_anomaly', 0) == 1)
            anomaly_rate = anomaly_count / len(data_points)
            avg_quality = sum(p.get('data_quality_score', 0) for p in data_points) / len(data_points)
            
            print(f"\n✅ Enhanced data collection complete!")
            print(f"📊 Total data points: {len(data_points)}")
            print(f"🚨 Anomalies detected: {anomaly_count} ({anomaly_rate:.2%})")
            print(f"🔧 Features per data point: {len(data_points[0].keys())}")
            print(f"⭐ Average quality score: {avg_quality:.2f}")
            print(f"💾 Saved to: {output_path}")
            
            # Show feature improvement
            print(f"\n📈 FEATURE IMPROVEMENTS:")
            print(f"   • Original features: ~13")
            print(f"   • Enhanced features: {len(data_points[0].keys())}")
            print(f"   • Feature increase: +{len(data_points[0].keys()) - 13}")
            print(f"   • Time-based features: 5")
            print(f"   • Derived metrics: 3")
            print(f"   • Quality metrics: 2")
            
            return output_path
        else:
            logger.error("❌ No data collected")
            return ""


def main():
    """Run the enhanced data collection."""
    print("🔍 SmartCloudOps AI - Simple Enhanced Real Data Collection")
    print("=" * 60)
    
    # Initialize collector
    collector = SimpleEnhancedCollector()
    
    # Run enhanced collection (2 hours for optimal data collection)
    output_path = collector.run_enhanced_collection(duration_minutes=120)
    
    if output_path:
        print("\n🎯 IMMEDIATE IMPROVEMENTS ACHIEVED:")
        print("✅ Higher resolution data (30-second intervals)")
        print("✅ Enhanced anomaly detection with scoring")
        print("✅ Rich feature set with 20+ metrics per point")
        print("✅ Data quality scoring for each point")
        print("✅ Time-based and derived features")
        print("✅ Realistic synthetic anomalies for training")
        
        print("\n🚀 NEXT STEPS:")
        print("1. Use this enhanced dataset for model training")
        print("2. Set up continuous collection (every 30 minutes)")
        print("3. Integrate with existing ML pipeline")
        print("4. Monitor and tune anomaly detection thresholds")
    else:
        print("❌ Data collection failed")


if __name__ == "__main__":
    main()
