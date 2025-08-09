#!/usr/bin/env python3
"""
Validate the generated dataset meets all requirements
"""

import pandas as pd

def validate_strict_requirements():
    """Validate that the dataset meets all strict requirements"""
    
    # Load the dataset
    df = pd.read_csv('/home/dileep-reddy/smartcloudops-ai/data/high_quality_server_metrics.csv')
    
    print(f"📊 Dataset Overview:")
    print(f"   Total rows: {len(df)}")
    print(f"   Columns: {list(df.columns)}")
    
    # Separate normal and anomaly rows
    normal_rows = df[df['is_anomaly'] == 0]
    anomaly_rows = df[df['is_anomaly'] == 1]
    
    print(f"\n🔍 Row Distribution:")
    print(f"   Normal rows: {len(normal_rows)} ({len(normal_rows)/len(df)*100:.1f}%)")
    print(f"   Anomaly rows: {len(anomaly_rows)} ({len(anomaly_rows)/len(df)*100:.1f}%)")
    
    # Validate normal rows
    print(f"\n✅ Normal Row Validation:")
    normal_response_time_100 = (normal_rows['response_time'] == 100.0).sum()
    print(f"   Rows with response_time=100.0: {normal_response_time_100}/{len(normal_rows)} ({normal_response_time_100/len(normal_rows)*100:.1f}%)")
    
    # Validate anomaly rows - ALL conditions must be met
    print(f"\n🚨 Anomaly Row Strict Validation:")
    
    conditions = {
        'response_time > 1500.0': (anomaly_rows['response_time'] > 1500.0).sum(),
        'cpu_usage > 90.0': (anomaly_rows['cpu_usage'] > 90.0).sum(),
        'memory_usage > 85.0': (anomaly_rows['memory_usage'] > 85.0).sum(),
        'disk_io_write > 1000000': (anomaly_rows['disk_io_write'] > 1000000).sum(),
        'load_1m > 5.0': (anomaly_rows['load_1m'] > 5.0).sum(),
    }
    
    for condition, count in conditions.items():
        print(f"   {condition}: {count}/{len(anomaly_rows)} ({count/len(anomaly_rows)*100:.1f}%)")
    
    # Check if ALL conditions are met simultaneously
    all_conditions_met = (
        (anomaly_rows['response_time'] > 1500.0) &
        (anomaly_rows['cpu_usage'] > 90.0) &
        (anomaly_rows['memory_usage'] > 85.0) &
        (anomaly_rows['disk_io_write'] > 1000000) &
        (anomaly_rows['load_1m'] > 5.0)
    ).sum()
    
    print(f"\n🎯 CRITICAL VALIDATION:")
    print(f"   Anomaly rows meeting ALL conditions: {all_conditions_met}/{len(anomaly_rows)} ({all_conditions_met/len(anomaly_rows)*100:.1f}%)")
    
    if all_conditions_met == len(anomaly_rows):
        print(f"   ✅ PERFECT! All anomaly rows meet strict requirements!")
    else:
        print(f"   ❌ ERROR: Some anomaly rows don't meet all requirements!")
    
    # Show sample values
    print(f"\n📈 Sample Anomaly Values:")
    sample_anomaly = anomaly_rows.iloc[0]
    print(f"   CPU Usage: {sample_anomaly['cpu_usage']:.2f}% (must be > 90.0)")
    print(f"   Memory Usage: {sample_anomaly['memory_usage']:.2f}% (must be > 85.0)")
    print(f"   Response Time: {sample_anomaly['response_time']:.2f}ms (must be > 1500.0)")
    print(f"   Disk I/O Write: {sample_anomaly['disk_io_write']:,} (must be > 1,000,000)")
    print(f"   Load 1m: {sample_anomaly['load_1m']:.2f} (must be > 5.0)")
    
    print(f"\n📈 Sample Normal Values:")
    sample_normal = normal_rows.iloc[0]
    print(f"   CPU Usage: {sample_normal['cpu_usage']:.2f}%")
    print(f"   Memory Usage: {sample_normal['memory_usage']:.2f}%")
    print(f"   Response Time: {sample_normal['response_time']:.2f}ms")
    print(f"   Disk I/O Write: {sample_normal['disk_io_write']}")
    print(f"   Load 1m: {sample_normal['load_1m']:.2f}")

if __name__ == "__main__":
    validate_strict_requirements()
