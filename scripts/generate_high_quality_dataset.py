#!/usr/bin/env python3
"""
High-Quality Server Metrics Dataset Generator
===========================================

Generate 1000 realistic server metric data points with proper anomaly detection.
"""

import random
import csv
from datetime import datetime, timedelta

def generate_high_quality_dataset():
    """Generate 1000 high-quality server metrics with realistic anomalies"""
    
    # Starting parameters
    total_rows = 1000
    anomaly_percentage = 0.03  # 3% anomalies
    start_time = datetime(2025, 8, 9, 0, 0, 0, 92100)  # Start from today
    
    data = []
    
    # Pre-determine which rows will be anomalies
    anomaly_indices = set(random.sample(range(total_rows), int(total_rows * anomaly_percentage)))
    
    for i in range(total_rows):
        # Calculate timestamp (5-minute increments)
        current_time = start_time + timedelta(minutes=5 * i)
        timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%S.%f")
        
        is_anomaly = 1 if i in anomaly_indices else 0
        
        if is_anomaly == 1:
            # ANOMALY ROW - ALL conditions MUST be met
            cpu_usage = random.uniform(90.5, 99.8)           # > 90.0
            memory_usage = random.uniform(85.5, 98.0)        # > 85.0
            response_time = random.uniform(1500.0, 5000.0)   # > 1500.0
            disk_io_write = random.randint(1000000, 50000000) # > 1,000,000
            load_1m = random.uniform(5.1, 15.0)              # > 5.0
            
            # Other fields for anomalies
            disk_io = random.uniform(80.0, 200.0)
            disk_io_read = random.uniform(10000, 100000)
            disk_usage = random.uniform(0.8, 0.95)
            load_5m = random.uniform(3.0, 10.0)
            network_io = random.uniform(50.0, 150.0)
            network_rx = random.uniform(10000, 100000)
            network_tx = random.uniform(5000, 80000)
            
        else:
            # NORMAL ROW - following the original pattern
            is_anomaly = 0
            response_time = 100.0  # Constant for normal rows
            
            # Most fields are 0.0, some have small fluctuating values
            cpu_usage = random.choice([0.0, 0.0, 0.0, random.uniform(0.1, 8.0)])
            memory_usage = random.choice([0.0, 0.0, random.uniform(0.01, 6.0)])
            
            # These fields are almost always 0.0 in normal rows
            disk_io = 0.0
            disk_io_read = 0.0
            disk_io_write = 0.0
            load_5m = 0.0
            network_io = 0.0
            network_rx = 0.0
            network_tx = 0.0
            
            # Occasionally have small values
            load_1m = random.choice([0, 0, 0, random.uniform(0.001, 0.2)])
            disk_usage = random.choice([0, 0, random.uniform(0.01, 0.99)])
        
        # Create the row
        row = {
            'cpu_usage': cpu_usage,
            'disk_io': disk_io,
            'disk_io_read': disk_io_read,
            'disk_io_write': disk_io_write,
            'disk_usage': disk_usage,
            'is_anomaly': is_anomaly,
            'load_1m': load_1m,
            'load_5m': load_5m,
            'memory_usage': memory_usage,
            'network_io': network_io,
            'network_rx': network_rx,
            'network_tx': network_tx,
            'response_time': response_time,
            'timestamp': timestamp
        }
        
        data.append(row)
    
    return data

def save_dataset(data, filename):
    """Save dataset to CSV with exact header format"""
    fieldnames = [
        'cpu_usage', 'disk_io', 'disk_io_read', 'disk_io_write', 'disk_usage',
        'is_anomaly', 'load_1m', 'load_5m', 'memory_usage', 'network_io',
        'network_rx', 'network_tx', 'response_time', 'timestamp'
    ]
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def validate_dataset(data):
    """Validate that anomaly rows meet all requirements"""
    total_rows = len(data)
    anomaly_rows = [row for row in data if row['is_anomaly'] == 1]
    normal_rows = [row for row in data if row['is_anomaly'] == 0]
    
    print(f"📊 Dataset Validation:")
    print(f"   Total rows: {total_rows}")
    print(f"   Normal rows: {len(normal_rows)} ({len(normal_rows)/total_rows*100:.1f}%)")
    print(f"   Anomaly rows: {len(anomaly_rows)} ({len(anomaly_rows)/total_rows*100:.1f}%)")
    
    # Validate anomaly rows
    valid_anomalies = 0
    for row in anomaly_rows:
        conditions_met = (
            row['response_time'] > 1500.0 and
            row['cpu_usage'] > 90.0 and
            row['memory_usage'] > 85.0 and
            row['disk_io_write'] > 1000000 and
            row['load_1m'] > 5.0
        )
        if conditions_met:
            valid_anomalies += 1
    
    print(f"✅ Valid anomalies: {valid_anomalies}/{len(anomaly_rows)} ({valid_anomalies/len(anomaly_rows)*100:.1f}%)")
    
    # Validate normal rows
    valid_normal = 0
    for row in normal_rows:
        if row['response_time'] == 100.0:
            valid_normal += 1
    
    print(f"✅ Valid normal rows: {valid_normal}/{len(normal_rows)} ({valid_normal/len(normal_rows)*100:.1f}%)")

if __name__ == "__main__":
    print("🚀 Generating High-Quality Server Metrics Dataset...")
    
    # Generate the dataset
    dataset = generate_high_quality_dataset()
    
    # Save to file
    output_file = "/home/dileep-reddy/smartcloudops-ai/data/high_quality_server_metrics.csv"
    save_dataset(dataset, output_file)
    
    # Validate the dataset
    validate_dataset(dataset)
    
    print(f"💾 Dataset saved to: {output_file}")
    print("🎯 Ready for ML training and anomaly detection!")
    
    # Show sample anomaly row
    anomaly_sample = next((row for row in dataset if row['is_anomaly'] == 1), None)
    if anomaly_sample:
        print(f"\n🚨 Sample anomaly row:")
        print(f"   CPU: {anomaly_sample['cpu_usage']:.1f}%")
        print(f"   Memory: {anomaly_sample['memory_usage']:.1f}%") 
        print(f"   Response Time: {anomaly_sample['response_time']:.1f}ms")
        print(f"   Disk I/O Write: {anomaly_sample['disk_io_write']:,}")
        print(f"   Load 1m: {anomaly_sample['load_1m']:.2f}")
