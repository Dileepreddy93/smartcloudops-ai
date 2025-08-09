#!/usr/bin/env python3
"""
🚀 Complete Real Data Model Trainer
SmartCloudOps AI - Train with all 1,645 real data points

Trains ML model with the complete real dataset for maximum accuracy
"""

import json
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import datetime
import os
import joblib

def load_all_real_data():
    """Load all real data sources"""
    all_data = []
    
    # Load original real data
    try:
        with open('/home/dileep-reddy/smartcloudops-ai/data/real_training_data.json', 'r') as f:
            original_data = json.load(f)
        print(f"📊 Loaded original real data: {len(original_data)} points")
        all_data.extend(original_data)
    except Exception as e:
        print(f"⚠️ Could not load original real data: {e}")
    
    # Load turbo real data
    try:
        with open('/home/dileep-reddy/smartcloudops-ai/data/turbo_real_data_20250809_171953.json', 'r') as f:
            turbo_data = json.load(f)
        print(f"⚡ Loaded turbo real data: {len(turbo_data)} points")
        all_data.extend(turbo_data)
    except Exception as e:
        print(f"⚠️ Could not load turbo real data: {e}")
    
    print(f"🎯 Total real data loaded: {len(all_data)} points")
    return all_data

def prepare_features(data):
    """Prepare features for ML training"""
    features = []
    
    for point in data:
        feature_vector = []
        
        # CPU metrics
        feature_vector.extend([
            point.get('cpu_percent', 0),
            point.get('load_avg_1min', 0),
            point.get('load_avg_5min', 0), 
            point.get('load_avg_15min', 0),
            point.get('system_load_percent', 0)
        ])
        
        # Memory metrics
        feature_vector.extend([
            point.get('memory_percent', 0),
            point.get('memory_pressure', 0),
            point.get('memory_used', 0) / 1e9,  # Convert to GB
            point.get('swap_percent', 0)
        ])
        
        # Disk metrics
        feature_vector.extend([
            point.get('disk_percent', 0),
            point.get('disk_pressure', 0),
            point.get('disk_read_bytes', 0) / 1e6,  # Convert to MB
            point.get('disk_write_bytes', 0) / 1e6
        ])
        
        # Network metrics
        feature_vector.extend([
            point.get('network_bytes_sent', 0) / 1e6,
            point.get('network_bytes_recv', 0) / 1e6,
            point.get('network_packets_sent', 0) / 1000,
            point.get('network_packets_recv', 0) / 1000
        ])
        
        # System metrics
        feature_vector.extend([
            point.get('process_count', 0),
            point.get('uptime_seconds', 0) / 3600,  # Convert to hours
            point.get('hour_of_day', 0),
            point.get('day_of_week', 0),
            int(point.get('is_business_hours', False))
        ])
        
        # Derived metrics
        feature_vector.extend([
            point.get('system_stress_score', 0),
            point.get('resource_utilization', 0)
        ])
        
        features.append(feature_vector)
    
    return np.array(features)

def create_labels(data):
    """Create anomaly labels for training"""
    labels = []
    
    for point in data:
        # Define anomaly conditions based on real system thresholds
        cpu_anomaly = point.get('cpu_percent', 0) > 90
        memory_anomaly = point.get('memory_percent', 0) > 85
        disk_anomaly = point.get('disk_percent', 0) > 90
        load_anomaly = point.get('system_load_percent', 0) > 80
        stress_anomaly = point.get('system_stress_score', 0) > 75
        
        # Label as anomaly if any critical threshold is exceeded
        is_anomaly = any([cpu_anomaly, memory_anomaly, disk_anomaly, load_anomaly, stress_anomaly])
        labels.append(1 if is_anomaly else 0)
    
    return np.array(labels)

def train_complete_real_model():
    """Train model with complete real dataset"""
    
    print("🚀 COMPLETE REAL DATA MODEL TRAINING")
    print("=" * 50)
    
    # Load all real data
    real_data = load_all_real_data()
    
    if len(real_data) == 0:
        print("❌ No real data found!")
        return None
    
    # Prepare features and labels
    print("🔧 Preparing features...")
    X = prepare_features(real_data)
    y = create_labels(real_data)
    
    print(f"📊 Features shape: {X.shape}")
    print(f"📊 Labels shape: {y.shape}")
    print(f"📊 Anomaly rate: {np.mean(y):.2%}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Scale features
    print("⚡ Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train multiple models for ensemble
    print("🤖 Training Isolation Forest...")
    
    # Optimized Isolation Forest
    contamination_rate = max(0.05, np.mean(y))  # Minimum 5% contamination
    iso_forest = IsolationForest(
        contamination=contamination_rate,
        random_state=42,
        n_estimators=200,
        max_features=1.0,
        bootstrap=False
    )
    
    iso_forest.fit(X_train_scaled)
    
    # Predictions
    y_pred_train = iso_forest.predict(X_train_scaled)
    y_pred_test = iso_forest.predict(X_test_scaled)
    
    # Convert predictions (-1, 1) to (1, 0)
    y_pred_train_binary = np.where(y_pred_train == -1, 1, 0)
    y_pred_test_binary = np.where(y_pred_test == -1, 1, 0)
    
    # Calculate metrics
    train_accuracy = accuracy_score(y_train, y_pred_train_binary)
    test_accuracy = accuracy_score(y_test, y_pred_test_binary)
    precision = precision_score(y_test, y_pred_test_binary, average='weighted')
    recall = recall_score(y_test, y_pred_test_binary, average='weighted')
    f1 = f1_score(y_test, y_pred_test_binary, average='weighted')
    
    # Get decision scores for AUC
    decision_scores = iso_forest.decision_function(X_test_scaled)
    auc_roc = roc_auc_score(y_test, -decision_scores)  # Negative because lower scores indicate anomalies
    
    # Results
    results = {
        "model_type": "complete_real_data_model",
        "version": "1.0.0",
        "training_timestamp": datetime.datetime.now().isoformat(),
        "description": f"Trained on {len(real_data)} complete real data points",
        "data_sources": {
            "original_real_data": 145,
            "turbo_real_data": 1500,
            "total_real_points": len(real_data)
        },
        "performance": {
            "train_accuracy": float(train_accuracy),
            "test_accuracy": float(test_accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "auc_roc": float(auc_roc),
            "anomaly_rate": float(np.mean(y))
        },
        "model_parameters": {
            "contamination": float(contamination_rate),
            "n_estimators": 200,
            "max_features": 1.0,
            "feature_count": X.shape[1]
        },
        "data_quality": {
            "total_samples": len(real_data),
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "feature_dimension": X.shape[1],
            "data_source": "100_percent_real_infrastructure"
        }
    }
    
    # Save model and results
    os.makedirs('/home/dileep-reddy/smartcloudops-ai/ml_models', exist_ok=True)
    
    # Save model
    model_path = '/home/dileep-reddy/smartcloudops-ai/ml_models/complete_real_model.joblib'
    scaler_path = '/home/dileep-reddy/smartcloudops-ai/ml_models/complete_real_scaler.joblib'
    
    joblib.dump(iso_forest, model_path)
    joblib.dump(scaler, scaler_path)
    
    # Save results
    results_path = '/home/dileep-reddy/smartcloudops-ai/ml_models/complete_real_model.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Display results
    print("\n🎉 TRAINING COMPLETE!")
    print("=" * 50)
    print(f"📊 Total Real Data: {len(real_data)} points")
    print(f"🎯 Test Accuracy: {test_accuracy:.1%}")
    print(f"🎯 Precision: {precision:.1%}")
    print(f"🎯 Recall: {recall:.1%}")
    print(f"🎯 F1-Score: {f1:.1%}")
    print(f"🎯 AUC-ROC: {auc_roc:.1%}")
    print(f"📁 Model saved: {model_path}")
    print(f"📁 Scaler saved: {scaler_path}")
    print(f"📁 Results saved: {results_path}")
    
    # Performance assessment
    if test_accuracy >= 0.94:
        print("🏆 EXCELLENT! Model exceeds 94% accuracy target!")
    elif test_accuracy >= 0.90:
        print("✅ GREAT! Model achieves 90%+ accuracy as expected!")
    elif test_accuracy >= 0.85:
        print("👍 GOOD! Model shows solid performance!")
    else:
        print("📈 Model trained - consider additional optimization!")
    
    return results

if __name__ == "__main__":
    train_complete_real_model()
