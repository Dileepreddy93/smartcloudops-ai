#!/usr/bin/env python3
"""
SmartCloudOps AI - Real-time Anomaly Detection Inference
=======================================================

Real-time inference system for deployed anomaly detection models.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
import joblib
import boto3
import requests
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyInferenceEngine:
    """
    Real-time anomaly detection inference engine.
    """
    
    def __init__(self, model_path="ml_models/optimized", prometheus_url: str | None = None):
        self.model_path = model_path
        self.prometheus_url = prometheus_url or os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
        self.model = None
        self.scaler = None
        self.feature_columns = None
        
        self.load_models()
    
    def load_models(self):
        """Load trained models and metadata."""
        try:
            # Load the anomaly model
            model_file = os.path.join(self.model_path, "anomaly_model.pkl")
            scaler_file = os.path.join(self.model_path, "anomaly_scaler.pkl")
            
            if os.path.exists(model_file) and os.path.exists(scaler_file):
                self.model = joblib.load(model_file)
                self.scaler = joblib.load(scaler_file)
                logger.info("✅ Models loaded successfully from local storage")
            else:
                logger.warning("⚠️ Local models not found, would load from S3 in production")
                
        except Exception as e:
            logger.error(f"❌ Error loading models: {e}")
    
    def collect_current_metrics(self):
        """Collect current metrics for inference."""
        try:
            queries = {
                'cpu_usage': 'avg(100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100))',
                'memory_usage': 'avg((1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100)',
                'disk_io': 'avg(irate(node_disk_io_time_seconds_total[5m]) * 100)',
                'network_io': 'avg(irate(node_network_receive_bytes_total[5m]) + irate(node_network_transmit_bytes_total[5m]))',
                'response_time': 'avg(prometheus_http_request_duration_seconds{handler="/api/v1/query"})'
            }
            
            metrics = {}
            for metric_name, query in queries.items():
                try:
                    response = requests.get(
                        f"{self.prometheus_url}/api/v1/query",
                        params={'query': query},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data['status'] == 'success' and data['data']['result']:
                            value = float(data['data']['result'][0]['value'][1])
                            metrics[metric_name] = value
                        else:
                            metrics[metric_name] = 0.0
                    else:
                        metrics[metric_name] = 0.0
                        
                except:
                    metrics[metric_name] = 0.0
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error collecting metrics: {e}")
            return {}
    
    def predict_anomaly(self, metrics):
        """Predict if current metrics indicate an anomaly."""
        if not self.model or not self.scaler:
            logger.error("❌ Models not loaded")
            return {"error": "Models not available"}
        
        try:
            # Create a DataFrame with the metrics
            df = pd.DataFrame([metrics])
            df['timestamp'] = datetime.now()
            
            # Basic feature engineering (simplified for real-time)
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            df['is_business_hours'] = ((df['hour'] >= 9) & (df['hour'] <= 17) & (~df['is_weekend'].astype(bool))).astype(int)
            
            # Cross-metric features
            df['cpu_memory_ratio'] = df['cpu_usage'] / (df['memory_usage'] + 1e-6)
            df['io_total'] = df['disk_io'] + df['network_io']
            df['load_indicator'] = (df['cpu_usage'] + df['memory_usage']) / 2
            
            # Select features (simplified set for real-time)
            feature_cols = ['cpu_usage', 'memory_usage', 'disk_io', 'network_io', 
                           'response_time', 'hour', 'day_of_week', 'is_weekend', 
                           'is_business_hours', 'cpu_memory_ratio', 'io_total', 'load_indicator']
            
            X = df[feature_cols].fillna(0)
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Predict
            prediction = self.model.predict(X_scaled)[0]
            anomaly_score = self.model.decision_function(X_scaled)[0]
            
            is_anomaly = prediction == -1
            confidence = abs(anomaly_score)
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'is_anomaly': bool(is_anomaly),
                'anomaly_score': float(anomaly_score),
                'confidence': float(confidence),
                'metrics': metrics,
                'status': 'ANOMALY DETECTED' if is_anomaly else 'NORMAL'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in prediction: {e}")
            return {"error": str(e)}

def main():
    """Test real-time inference."""
    print("🔍 SmartCloudOps AI - Real-time Anomaly Detection")
    print("=" * 50)
    
    engine = AnomalyInferenceEngine()
    
    # Collect current metrics
    metrics = engine.collect_current_metrics()
    
    if metrics:
        print(f"\n📊 Current Infrastructure Metrics:")
        for metric, value in metrics.items():
            print(f"   {metric}: {value:.2f}")
        
        # Predict anomaly
        result = engine.predict_anomaly(metrics)
        
        print(f"\n🤖 Anomaly Detection Result:")
        print(f"   Status: {result.get('status', 'ERROR')}")
        print(f"   Is Anomaly: {result.get('is_anomaly', 'N/A')}")
        
        anomaly_score = result.get('anomaly_score', 'N/A')
        confidence = result.get('confidence', 'N/A')
        
        if anomaly_score != 'N/A':
            print(f"   Anomaly Score: {anomaly_score:.4f}")
        else:
            print(f"   Anomaly Score: {anomaly_score}")
            
        if confidence != 'N/A':
            print(f"   Confidence: {confidence:.4f}")
        else:
            print(f"   Confidence: {confidence}")
        
        if result.get('is_anomaly'):
            print(f"   🚨 ALERT: Anomaly detected in infrastructure!")
        else:
            print(f"   ✅ All systems operating normally")
    else:
        print("❌ Could not collect metrics")

if __name__ == "__main__":
    main()
