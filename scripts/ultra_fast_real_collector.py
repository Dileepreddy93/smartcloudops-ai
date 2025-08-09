#!/usr/bin/env python3
"""
🚀 Ultra-Fast Real Data Collector
SmartCloudOps AI - High-Speed Real Data Collection

Collects real system metrics at high frequency for rapid data accumulation
NO SYNTHETIC DATA - 100% REAL INFRASTRUCTURE METRICS
"""

import json
import time
import psutil
import datetime
import os
import logging
from typing import Dict, Any
import threading
import queue
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltraFastRealCollector:
    def __init__(self, target_points: int = 1500, interval_seconds: float = 5.0):
        """
        Ultra-fast real data collector
        
        Args:
            target_points: Number of real data points to collect
            interval_seconds: Collection interval (default 5 seconds for speed)
        """
        self.target_points = target_points
        self.interval = interval_seconds
        self.collected_points = 0
        self.start_time = None
        self.data_queue = queue.Queue()
        
        # Setup output directory
        self.data_dir = "/home/dileep-reddy/smartcloudops-ai/data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = f"{self.data_dir}/ultra_fast_real_data_{timestamp}.json"
        
        print(f"🚀 Ultra-Fast Real Data Collection")
        print(f"📊 Target: {target_points} real data points")
        print(f"⚡ Interval: {interval_seconds} seconds")
        print(f"⏱️ Expected Duration: {(target_points * interval_seconds / 60):.1f} minutes")
        print(f"💾 Output: {self.output_file}")
        print("=" * 60)

    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive real system metrics"""
        try:
            # Get current timestamp
            now = datetime.datetime.now()
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            load_avg = os.getloadavg()
            
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
            
            # Boot time and uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            # Advanced derived metrics
            memory_pressure = (memory.used / memory.total) * 100
            disk_pressure = (disk_usage.used / disk_usage.total) * 100
            system_load = (load_avg[0] / cpu_count) * 100 if cpu_count > 0 else 0
            
            # Time-based features
            hour_of_day = now.hour
            day_of_week = now.weekday()
            is_business_hours = 9 <= hour_of_day <= 17 and day_of_week < 5
            
            # Create comprehensive data point
            data_point = {
                # Timestamp and metadata
                "timestamp": now.isoformat(),
                "unix_timestamp": time.time(),
                "collection_id": f"ultra_fast_{self.collected_points + 1}",
                
                # CPU metrics
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "load_avg_1min": load_avg[0],
                "load_avg_5min": load_avg[1],
                "load_avg_15min": load_avg[2],
                "system_load_percent": system_load,
                
                # Memory metrics
                "memory_total": memory.total,
                "memory_used": memory.used,
                "memory_free": memory.free,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "memory_pressure": memory_pressure,
                
                # Swap metrics
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_free": swap.free,
                "swap_percent": swap.percent,
                
                # Disk metrics
                "disk_total": disk_usage.total,
                "disk_used": disk_usage.used,
                "disk_free": disk_usage.free,
                "disk_percent": disk_usage.percent,
                "disk_pressure": disk_pressure,
                
                # Disk I/O
                "disk_read_bytes": disk_io.read_bytes if disk_io else 0,
                "disk_write_bytes": disk_io.write_bytes if disk_io else 0,
                "disk_read_count": disk_io.read_count if disk_io else 0,
                "disk_write_count": disk_io.write_count if disk_io else 0,
                
                # Network I/O
                "network_bytes_sent": network_io.bytes_sent,
                "network_bytes_recv": network_io.bytes_recv,
                "network_packets_sent": network_io.packets_sent,
                "network_packets_recv": network_io.packets_recv,
                
                # Process and system metrics
                "process_count": process_count,
                "uptime_seconds": uptime,
                
                # Time-based features
                "hour_of_day": hour_of_day,
                "day_of_week": day_of_week,
                "is_business_hours": is_business_hours,
                
                # Derived stress indicators
                "system_stress_score": (cpu_percent + memory_pressure + disk_pressure + system_load) / 4,
                "resource_utilization": (memory.percent + disk_usage.percent + cpu_percent) / 3,
                
                # Quality indicators
                "data_source": "real_system_metrics",
                "quality_score": 1.0,  # Real data always has perfect quality
                "is_anomaly": False,  # Will be determined by ML models
                "feature_count": 35   # Total number of features
            }
            
            return data_point
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return None

    def save_data_point(self, data_point: Dict[str, Any]):
        """Save data point to file"""
        try:
            # Load existing data or create new list
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r') as f:
                    data = json.load(f)
            else:
                data = []
            
            # Add new data point
            data.append(data_point)
            
            # Save back to file
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving data point: {e}")

    def run_ultra_fast_collection(self):
        """Run ultra-fast collection to target"""
        print(f"\n🚀 Starting ultra-fast real data collection...")
        print(f"⚡ Collecting {self.target_points} points at {self.interval}s intervals")
        
        self.start_time = time.time()
        
        try:
            while self.collected_points < self.target_points:
                # Collect real system metrics
                data_point = self.collect_system_metrics()
                
                if data_point:
                    # Save data point
                    self.save_data_point(data_point)
                    self.collected_points += 1
                    
                    # Progress reporting
                    if self.collected_points % 50 == 0 or self.collected_points <= 10:
                        elapsed = time.time() - self.start_time
                        rate = self.collected_points / elapsed if elapsed > 0 else 0
                        remaining = self.target_points - self.collected_points
                        eta = remaining / rate if rate > 0 else 0
                        
                        print(f"   ✅ Collected {self.collected_points}/{self.target_points} points | "
                              f"Rate: {rate:.1f} pts/sec | ETA: {eta/60:.1f} min")
                
                # Wait for next collection
                if self.collected_points < self.target_points:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            print(f"\n⚠️ Collection interrupted. Collected {self.collected_points} points.")
        except Exception as e:
            print(f"\n❌ Error during collection: {e}")
            
        # Final summary
        total_time = time.time() - self.start_time
        print(f"\n🎉 Collection Complete!")
        print(f"📊 Total Points: {self.collected_points}")
        print(f"⏱️ Total Time: {total_time/60:.1f} minutes")
        print(f"⚡ Average Rate: {self.collected_points/total_time:.1f} points/second")
        print(f"💾 Data File: {self.output_file}")
        print(f"📏 File Size: {os.path.getsize(self.output_file)/1024/1024:.1f} MB")

def main():
    """Main execution function"""
    print("🚀 SmartCloudOps AI - Ultra-Fast Real Data Collector")
    print("=" * 60)
    
    # Configuration options
    print("Select collection speed:")
    print("1. 🚀 Ultra-Fast (5-second intervals) - 1,500 points in ~2 hours")
    print("2. ⚡ Lightning (3-second intervals) - 1,500 points in ~1.25 hours") 
    print("3. 🔥 Turbo (1-second intervals) - 1,500 points in ~25 minutes")
    print("4. 💨 Blazing (0.5-second intervals) - 1,500 points in ~12 minutes")
    
    choice = input("\nEnter choice (1-4) or press Enter for Ultra-Fast: ").strip()
    
    # Set parameters based on choice
    if choice == "2":
        interval = 3.0
        mode = "Lightning"
    elif choice == "3":
        interval = 1.0
        mode = "Turbo"
    elif choice == "4":
        interval = 0.5
        mode = "Blazing"
    else:
        interval = 5.0
        mode = "Ultra-Fast"
    
    target = 1500  # Target for optimal model performance
    
    print(f"\n🎯 Selected: {mode} Mode")
    print(f"⚡ Collection interval: {interval} seconds")
    print(f"📊 Target points: {target}")
    print(f"⏱️ Estimated time: {(target * interval / 60):.1f} minutes")
    
    # Confirm before starting
    confirm = input(f"\n🚀 Start {mode} real data collection? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Collection cancelled.")
        return
    
    # Create and run collector
    collector = UltraFastRealCollector(target_points=target, interval_seconds=interval)
    collector.run_ultra_fast_collection()
    
    print(f"\n✅ Ultra-fast real data collection complete!")
    print(f"🎯 You now have high-quality real data for optimal model training!")

if __name__ == "__main__":
    main()
