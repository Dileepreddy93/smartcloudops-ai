#!/usr/bin/env python3
"""
SmartCloudOps AI - Enhanced Production Inference with Real Data
==============================================================

Production inference engine that uses real infrastructure data.
"""

import json
import os
import sys
import time
from datetime import datetime

class RealDataInferenceEngine:
    """Production inference using real data."""
    
    def __init__(self):
        self.model_config = None
        self.thresholds = None
        self.load_model()
        
        # Initialize real data collector
        try:
            sys.path.append(os.path.dirname(__file__))
            from simple_real_data_collector import SimpleRealDataCollector
            self.data_collector = SimpleRealDataCollector()
            print("✅ Real data collector initialized")
        except Exception as e:
            print(f"⚠️ Real data collector unavailable: {e}")
            self.data_collector = None
    
    def load_model(self):
        """Load the trained real data model."""
        try:
            # Try multiple possible paths
            possible_paths = [
                "../ml_models/real_data_model.json",
                "ml_models/real_data_model.json",
                os.path.join(os.path.dirname(__file__), "..", "ml_models", "real_data_model.json")
            ]
            
            for model_path in possible_paths:
                if os.path.exists(model_path):
                    with open(model_path, 'r') as f:
                        self.model_config = json.load(f)
                    
                    self.thresholds = self.model_config.get('thresholds', {})
                    print(f"✅ Loaded real data model from {model_path}")
                    print(f"📊 Model F1-Score: {self.model_config.get('performance', {}).get('f1_score', 0):.3f}")
                    return True
            
            print(f"❌ Model file not found in any expected location")
            return False
                
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def collect_live_metrics(self):
        """Collect live infrastructure metrics."""
        if self.data_collector:
            return self.data_collector.collect_current_metrics()
        else:
            print("❌ Data collector not available")
            return None
    
    def predict_anomaly(self, metrics=None):
        """Predict anomaly using real data model."""
        start_time = time.time()
        
        try:
            # Collect metrics if not provided
            if metrics is None:
                metrics = self.collect_live_metrics()
                
            if not metrics or not self.thresholds:
                return {
                    'error': 'No metrics or model available',
                    'anomaly': False,
                    'confidence': 0.0
                }
            
            # Apply real data model rules
            cpu_high = metrics.get('cpu_usage', 0) > self.thresholds.get('cpu_threshold', 100)
            memory_high = metrics.get('memory_usage', 0) > self.thresholds.get('memory_threshold', 100)
            load_high = metrics.get('load_1m', 0) > self.thresholds.get('load_threshold', 10)
            disk_high = metrics.get('disk_usage', 0) > self.thresholds.get('disk_threshold', 100)
            
            is_anomaly = cpu_high or memory_high or load_high or disk_high
            
            # Calculate confidence based on how many thresholds are exceeded
            confidence = 0.0
            if cpu_high:
                confidence += 0.3
            if memory_high:
                confidence += 0.3
            if load_high:
                confidence += 0.2
            if disk_high:
                confidence += 0.2
            
            confidence = min(confidence, 1.0)
            
            prediction_time = time.time() - start_time
            
            result = {
                'anomaly': is_anomaly,
                'confidence': confidence,
                'metrics': metrics,
                'thresholds_exceeded': {
                    'cpu': cpu_high,
                    'memory': memory_high,
                    'load': load_high,
                    'disk': disk_high
                },
                'prediction_time_ms': prediction_time * 1000,
                'timestamp': datetime.now().isoformat(),
                'model_type': 'real_data_based'
            }
            
            # Log prediction
            status = "🚨 ANOMALY" if is_anomaly else "✅ NORMAL"
            print(f"🔍 Prediction: {status} (confidence: {confidence:.3f}, time: {prediction_time*1000:.1f}ms)")
            
            return result
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return {
                'error': str(e),
                'anomaly': False,
                'confidence': 0.0,
                'timestamp': datetime.now().isoformat()
            }
    
    def health_check(self):
        """Check system health."""
        health = {
            'status': 'healthy',
            'model_loaded': self.model_config is not None,
            'thresholds_available': self.thresholds is not None,
            'data_collector_available': self.data_collector is not None,
            'prometheus_connection': False
        }
        
        # Test Prometheus connection
        if self.data_collector:
            try:
                test_metrics = self.data_collector.collect_current_metrics()
                health['prometheus_connection'] = test_metrics is not None
            except:
                pass
        
        # Overall health
        if not all([health['model_loaded'], health['thresholds_available']]):
            health['status'] = 'unhealthy'
        elif not health['data_collector_available']:
            health['status'] = 'degraded'
            
        return health
    
    def get_model_info(self):
        """Get information about the current model."""
        if not self.model_config:
            return {'error': 'No model loaded'}
        
        return {
            'model_type': self.model_config.get('model_type'),
            'training_timestamp': self.model_config.get('training_timestamp'),
            'training_data_size': self.model_config.get('training_data_size'),
            'performance': self.model_config.get('performance'),
            'thresholds': self.thresholds
        }

# Global instance
real_inference_engine = None

def get_real_inference_engine():
    """Get or create the global real inference engine."""
    global real_inference_engine
    if real_inference_engine is None:
        real_inference_engine = RealDataInferenceEngine()
    return real_inference_engine

def main():
    """Test the real data inference engine."""
    print("🔍 SmartCloudOps AI - Real Data Inference Test")
    print("=" * 50)
    
    # Initialize engine
    engine = RealDataInferenceEngine()
    
    # Health check
    print("\n1. Health Check:")
    health = engine.health_check()
    for key, value in health.items():
        status = "✅" if value else "❌"
        print(f"   {status} {key}: {value}")
    
    # Model info
    print("\n2. Model Information:")
    model_info = engine.get_model_info()
    if 'error' not in model_info:
        print(f"   Model Type: {model_info.get('model_type')}")
        print(f"   Training Data: {model_info.get('training_data_size')} points")
        print(f"   F1-Score: {model_info.get('performance', {}).get('f1_score', 0):.3f}")
        print(f"   Accuracy: {model_info.get('performance', {}).get('accuracy', 0):.3f}")
    
    # Test predictions
    print("\n3. Live Anomaly Detection:")
    for i in range(3):
        print(f"\n   Test {i+1}:")
        result = engine.predict_anomaly()
        
        if 'error' not in result:
            status = "🚨 ANOMALY DETECTED" if result['anomaly'] else "✅ SYSTEM NORMAL"
            print(f"   Status: {status}")
            print(f"   Confidence: {result['confidence']:.3f}")
            print(f"   CPU: {result['metrics'].get('cpu_usage', 0):.1f}%")
            print(f"   Memory: {result['metrics'].get('memory_usage', 0):.1f}%")
            print(f"   Load: {result['metrics'].get('load_1m', 0):.2f}")
        else:
            print(f"   Error: {result['error']}")
        
        if i < 2:  # Wait between tests
            time.sleep(2)
    
    print("\n" + "=" * 50)
    print("🎯 Real Data Inference Engine Ready!")
    print("🚀 Now detecting anomalies using REAL infrastructure data!")

if __name__ == "__main__":
    main()
