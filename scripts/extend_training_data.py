#!/usr/bin/env python3
"""
Extend existing real_training_data.csv to 1000 total rows
Following exact patterns from existing data
"""

import random
from datetime import datetime, timedelta

def generate_extension_data():
    # Starting point: next timestamp after the last row
    start_time = datetime.strptime("2025-08-08T15:43:42.092100", "%Y-%m-%dT%H:%M:%S.%f")
    
    # We need 855 more rows (1000 - 145 = 855)
    rows_needed = 855
    
    data_rows = []
    
    for i in range(rows_needed):
        # Increment timestamp by exactly 5 minutes
        current_time = start_time + timedelta(minutes=5 * (i + 1))
        timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%S.%f")
        
        # Determine if this should be an anomaly (3% chance)
        is_anomaly = 1 if random.random() < 0.03 else 0
        
        if is_anomaly == 1:
            # Anomaly row - spike the values
            cpu_usage = random.uniform(80, 95)
            memory_usage = random.uniform(85, 95)
            response_time = random.uniform(1000, 2000)
            disk_io_write = random.uniform(50, 100)
            load_1m = random.uniform(2.0, 5.0)
            disk_usage = random.uniform(0.8, 0.95)
        else:
            # Normal row - follow existing patterns
            # Many fields are 0.0, some have small fluctuating values
            cpu_usage = random.choice([0.0, 0.0, 0.0, random.uniform(0.5, 8.0)])
            memory_usage = random.choice([0.0, 0.0, random.uniform(0.1, 6.0)])
            response_time = 100.0  # Always 100.0 for normal rows
            disk_io_write = 0.0    # Always 0.0 based on pattern
            load_1m = random.choice([0, 0, random.uniform(0.001, 0.2)])
            disk_usage = random.choice([0, 0, random.uniform(0.01, 0.99)])
        
        # Fields that are always 0.0 based on existing pattern
        disk_io = 0.0
        disk_io_read = 0.0
        load_5m = 0.0
        network_io = 0.0
        network_rx = 0.0
        network_tx = 0.0
        
        # Format the row exactly like the existing data
        row = f"{cpu_usage},{disk_io},{disk_io_read},{disk_io_write},{disk_usage},{is_anomaly},{load_1m},{load_5m},{memory_usage},{network_io},{network_rx},{network_tx},{response_time},{timestamp}"
        data_rows.append(row)
    
    return data_rows

if __name__ == "__main__":
    print("🔧 Generating extension data...")
    
    # Generate the data
    new_rows = generate_extension_data()
    
    # Write to a temporary file first
    temp_file = "/home/dileep-reddy/smartcloudops-ai/data/extension_rows.csv"
    with open(temp_file, 'w') as f:
        for row in new_rows:
            f.write(row + '\n')
    
    print(f"✅ Generated {len(new_rows)} additional rows")
    print(f"📝 Saved to: {temp_file}")
    print("📊 Ready to append to real_training_data.csv")
    
    # Show anomaly count
    anomaly_count = sum(1 for row in new_rows if ',1,' in row)
    print(f"🚨 Anomalies generated: {anomaly_count} ({anomaly_count/len(new_rows)*100:.1f}%)")
