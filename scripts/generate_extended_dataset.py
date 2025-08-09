#!/usr/bin/env python3
"""
SmartCloudOps AI - Extended Dataset Generator
============================================

Generate realistic sensor/metric data for training and testing purposes.
"""

import csv
import random
from datetime import datetime, timedelta

def generate_extended_dataset():
    """Generate extended dataset from ID 145 to 1000"""
    
    # Starting parameters
    start_id = 145
    end_id = 1000
    start_time = datetime.now()
    
    # Value parameters (hovering around 250, between 150-350)
    base_value = 250.0
    min_value = 150.0
    max_value = 350.0
    
    # Status distribution: 85% OK, 10% WARNING, 5% ERROR
    status_choices = ['OK'] * 85 + ['WARNING'] * 10 + ['ERROR'] * 5
    
    # Generate data
    data = []
    current_time = start_time
    
    for record_id in range(start_id, end_id + 1):
        # Generate realistic timestamp (5-30 minute increments)
        time_increment = random.randint(5, 30)
        current_time += timedelta(minutes=time_increment)
        
        # Generate realistic value with some drift and noise
        # Add some randomness around the base value
        value_drift = random.uniform(-50, 50)  # Drift factor
        noise = random.uniform(-20, 20)        # Random noise
        value = base_value + value_drift + noise
        
        # Ensure value stays within bounds
        value = max(min_value, min(max_value, value))
        value = round(value, 3)
        
        # Generate status based on distribution
        status = random.choice(status_choices)
        
        # Create record
        record = {
            'ID': record_id,
            'Timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'Value': value,
            'Status': status
        }
        
        data.append(record)
    
    return data

def save_to_csv(data, filename):
    """Save data to CSV file"""
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['ID', 'Timestamp', 'Value', 'Status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in data:
            writer.writerow(row)

if __name__ == '__main__':
    print("🔧 Generating extended dataset...")
    
    # Generate the dataset
    dataset = generate_extended_dataset()
    
    # Save to CSV
    output_file = '/home/dileep-reddy/smartcloudops-ai/data/extended_sensor_data.csv'
    save_to_csv(dataset, output_file)
    
    print(f"✅ Generated {len(dataset)} data points")
    print(f"✅ Saved to: {output_file}")
    print(f"📊 Dataset range: ID {dataset[0]['ID']} to {dataset[-1]['ID']}")
    print(f"⏰ Time range: {dataset[0]['Timestamp']} to {dataset[-1]['Timestamp']}")
    
    # Show status distribution
    status_counts = {}
    for record in dataset:
        status = record['Status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("📈 Status distribution:")
    for status, count in status_counts.items():
        percentage = (count / len(dataset)) * 100
        print(f"   {status}: {count} ({percentage:.1f}%)")
