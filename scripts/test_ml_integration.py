#!/usr/bin/env python3
"""
SmartCloudOps AI - ML Integration Test
====================================

Test script to validate ML model integration with Flask app.
"""

import requests
import json
import time
from datetime import datetime

def test_ml_endpoints(base_url="http://localhost:5000"):
    """Test all ML endpoints."""
    
    print("🧪 Testing SmartCloudOps AI ML Integration")
    print("=" * 50)
    
    # Test 1: Application status
    print("\n1️⃣ Testing application status...")
    try:
        response = requests.get(f"{base_url}/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data['status']}")
            print(f"📊 ML Available: {data.get('ml_status', {}).get('ml_available', False)}")
            ml_available = data.get('ml_status', {}).get('ml_available', False)
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return
    
    if not ml_available:
        print("⚠️ ML not available, skipping ML tests")
        return
    
    # Test 2: ML Health Check
    print("\n2️⃣ Testing ML health check...")
    try:
        response = requests.get(f"{base_url}/ml/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ ML Health: {data['status']}")
            print(f"📊 Model Loaded: {data.get('health', {}).get('model_loaded', False)}")
        else:
            print(f"❌ ML health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ ML health check error: {e}")
    
    # Test 3: Current Metrics
    print("\n3️⃣ Testing metrics collection...")
    try:
        response = requests.get(f"{base_url}/ml/metrics", timeout=10)
        if response.status_code == 200:
            data = response.json()
            metrics = data.get('metrics', {})
            print(f"✅ Metrics collected:")
            for key, value in metrics.items():
                print(f"   {key}: {value:.2f}" if isinstance(value, (int, float)) else f"   {key}: {value}")
        else:
            print(f"❌ Metrics collection failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Metrics collection error: {e}")
    
    # Test 4: Anomaly Prediction (without custom metrics)
    print("\n4️⃣ Testing anomaly prediction...")
    try:
        response = requests.post(f"{base_url}/ml/predict", 
                               headers={'Content-Type': 'application/json'},
                               json={}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            anomaly = data.get('anomaly', False)
            confidence = data.get('confidence', 0)
            prediction_time = data.get('prediction_time_ms', 0)
            
            print(f"✅ Prediction: {'🚨 ANOMALY' if anomaly else '✅ NORMAL'}")
            print(f"📊 Confidence: {confidence:.3f}")
            print(f"⚡ Prediction Time: {prediction_time:.2f}ms")
        else:
            print(f"❌ Anomaly prediction failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Anomaly prediction error: {e}")
    
    # Test 5: Anomaly Prediction with Custom Metrics
    print("\n5️⃣ Testing anomaly prediction with custom metrics...")
    try:
        # Test with suspicious metrics (high CPU, memory, response time)
        custom_metrics = {
            "metrics": {
                "cpu_usage": 95.0,
                "memory_usage": 90.0,
                "disk_io": 80.0,
                "network_io": 1000.0,
                "response_time": 5.0
            }
        }
        
        response = requests.post(f"{base_url}/ml/predict",
                               headers={'Content-Type': 'application/json'},
                               json=custom_metrics, timeout=10)
        if response.status_code == 200:
            data = response.json()
            anomaly = data.get('anomaly', False)
            confidence = data.get('confidence', 0)
            
            print(f"✅ Custom Metrics Prediction: {'🚨 ANOMALY' if anomaly else '✅ NORMAL'}")
            print(f"📊 Confidence: {confidence:.3f}")
        else:
            print(f"❌ Custom metrics prediction failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Custom metrics prediction error: {e}")
    
    # Test 6: Performance Metrics
    print("\n6️⃣ Testing performance metrics...")
    try:
        response = requests.get(f"{base_url}/ml/performance", timeout=10)
        if response.status_code == 200:
            data = response.json()
            performance = data.get('performance', {})
            print(f"✅ Performance Metrics:")
            for key, value in performance.items():
                if isinstance(value, (int, float)):
                    print(f"   {key}: {value:.3f}")
                else:
                    print(f"   {key}: {value}")
        else:
            print(f"❌ Performance metrics failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Performance metrics error: {e}")
    
    print("\n🎯 ML Integration Test Complete!")

def test_load_performance(base_url="http://localhost:5000", num_requests=10):
    """Test prediction performance under load."""
    
    print(f"\n🚀 Testing prediction performance ({num_requests} requests)...")
    
    times = []
    successes = 0
    
    for i in range(num_requests):
        try:
            start_time = time.time()
            response = requests.post(f"{base_url}/ml/predict",
                                   headers={'Content-Type': 'application/json'},
                                   json={}, timeout=5)
            end_time = time.time()
            
            if response.status_code == 200:
                successes += 1
                times.append((end_time - start_time) * 1000)  # Convert to ms
                
        except Exception as e:
            print(f"❌ Request {i+1} failed: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"✅ Load Test Results:")
        print(f"   Success Rate: {successes}/{num_requests} ({successes/num_requests*100:.1f}%)")
        print(f"   Average Time: {avg_time:.2f}ms")
        print(f"   Min Time: {min_time:.2f}ms")
        print(f"   Max Time: {max_time:.2f}ms")
    else:
        print("❌ No successful requests")

if __name__ == "__main__":
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    print(f"🎯 Testing against: {base_url}")
    
    # Basic functionality tests
    test_ml_endpoints(base_url)
    
    # Load performance test
    test_load_performance(base_url, 5)
