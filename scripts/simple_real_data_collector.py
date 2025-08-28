#!/usr/bin/env python3
"""Simple Real Data Collector"""


import os
import time
from datetime import datetime

import psutil


def collect_system_metrics():
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
        }
        return metrics
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    print("Starting data collection...")
    os.makedirs("data", exist_ok=True)

    for i in range(3):
        metrics = collect_system_metrics()
        if metrics:
            print(f"Sample {i + 1}: CPU {metrics['cpu_percent']:.1f}%")
        time.sleep(1)

    print("Data collection completed!")


if __name__ == "__main__":
    main()
