#!/usr/bin/env python3
"""
SmartCloudOps AI - Simple Real Data ML Trainer
=============================================

ML training pipeline using real infrastructure data.
Uses only standard library plus simple imports.
"""

import json
import os
import sys
from datetime import datetime
import urllib.request
import urllib.parse

class SimpleMLTrainer:
    """Simple ML trainer using real data."""
    
    def __init__(self):
        self.real_data = []
        self.model_metrics = {}
        
    def load_real_data(self, filepath="../data/real_training_data.json"):
        """Load real data from file."""
        try:
            # Try multiple possible paths
            possible_paths = [
                filepath,
                "../data/real_training_data.json",
                "data/real_training_data.json",
                os.path.join(os.path.dirname(__file__), "..", "data", "real_training_data.json")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        self.real_data = json.load(f)
                    print(f"✅ Loaded {len(self.real_data)} real data points from {path}")
                    return True
            
            print("❌ No real data file found in any of the expected locations")
            return False
        except Exception as e:
            print(f"❌ Error loading real data: {e}")
            return False
    
    def analyze_real_data(self):
        """Analyze the real data patterns."""
        if not self.real_data:
            print("❌ No real data available")
            return
        
        print("\n📊 REAL DATA ANALYSIS")
        print("-" * 30)
        
        # Calculate statistics for key metrics
        metrics = ['cpu_usage', 'memory_usage', 'disk_usage', 'load_1m']
        
        for metric in metrics:
            values = [float(point.get(metric, 0)) for point in self.real_data]
            if values:
                avg_val = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)
                print(f"{metric:15}: avg={avg_val:6.2f}, min={min_val:6.2f}, max={max_val:6.2f}")
        
        # Anomaly analysis
        anomalies = [point for point in self.real_data if point.get('is_anomaly', 0) == 1]
        normal = [point for point in self.real_data if point.get('is_anomaly', 0) == 0]
        
        print(f"\nAnomaly rate: {len(anomalies)/len(self.real_data):.1%} ({len(anomalies)}/{len(self.real_data)})")
        print(f"Normal points: {len(normal)}")
        
        return {
            'total_points': len(self.real_data),
            'anomaly_count': len(anomalies),
            'normal_count': len(normal),
            'anomaly_rate': len(anomalies) / len(self.real_data)
        }
    
    def create_simple_rules(self):
        """Create simple rule-based anomaly detection."""
        print("\n🧠 Creating rule-based anomaly detection...")
        
        if not self.real_data:
            return None
        
        # Analyze normal behavior to set thresholds
        normal_points = [p for p in self.real_data if p.get('is_anomaly', 0) == 0]
        
        if not normal_points:
            print("❌ No normal data points found")
            return None
        
        # Calculate thresholds based on normal data
        cpu_values = [p.get('cpu_usage', 0) for p in normal_points]
        memory_values = [p.get('memory_usage', 0) for p in normal_points]
        load_values = [p.get('load_1m', 0) for p in normal_points]
        disk_values = [p.get('disk_usage', 0) for p in normal_points]
        
        # Set thresholds at 95th percentile of normal data
        def percentile_95(values):
            if not values:
                return 0
            sorted_vals = sorted(values)
            idx = int(0.95 * len(sorted_vals))
            return sorted_vals[min(idx, len(sorted_vals)-1)]
        
        thresholds = {
            'cpu_threshold': percentile_95(cpu_values),
            'memory_threshold': percentile_95(memory_values),
            'load_threshold': percentile_95(load_values),
            'disk_threshold': percentile_95(disk_values)
        }
        
        print(f"📊 Calculated thresholds from real data:")
        for key, value in thresholds.items():
            print(f"   {key}: {value:.2f}")
        
        return thresholds
    
    def test_simple_model(self, thresholds):
        """Test the simple rule-based model."""
        print("\n🧪 Testing rule-based model...")
        
        if not thresholds or not self.real_data:
            return None
        
        correct_predictions = 0
        total_predictions = len(self.real_data)
        
        predictions = []
        
        for point in self.real_data:
            # Apply rules
            cpu_high = point.get('cpu_usage', 0) > thresholds['cpu_threshold']
            memory_high = point.get('memory_usage', 0) > thresholds['memory_threshold']
            load_high = point.get('load_1m', 0) > thresholds['load_threshold']
            disk_high = point.get('disk_usage', 0) > thresholds['disk_threshold']
            
            # Predict anomaly if any threshold is exceeded
            predicted_anomaly = 1 if (cpu_high or memory_high or load_high or disk_high) else 0
            actual_anomaly = point.get('is_anomaly', 0)
            
            predictions.append({
                'predicted': predicted_anomaly,
                'actual': actual_anomaly,
                'correct': predicted_anomaly == actual_anomaly
            })
            
            if predicted_anomaly == actual_anomaly:
                correct_predictions += 1
        
        accuracy = correct_predictions / total_predictions
        
        # Calculate confusion matrix
        tp = sum(1 for p in predictions if p['predicted'] == 1 and p['actual'] == 1)
        fp = sum(1 for p in predictions if p['predicted'] == 1 and p['actual'] == 0)
        tn = sum(1 for p in predictions if p['predicted'] == 0 and p['actual'] == 0)
        fn = sum(1 for p in predictions if p['predicted'] == 0 and p['actual'] == 1)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        results = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'confusion_matrix': {
                'true_positives': tp,
                'false_positives': fp,
                'true_negatives': tn,
                'false_negatives': fn
            }
        }
        
        print(f"🎯 Model Performance on Real Data:")
        print(f"   Accuracy:  {accuracy:.3f}")
        print(f"   Precision: {precision:.3f}")
        print(f"   Recall:    {recall:.3f}")
        print(f"   F1-Score:  {f1_score:.3f}")
        
        return results
    
    def save_trained_model(self, thresholds, results):
        """Save the trained model configuration."""
        try:
            model_config = {
                'model_type': 'rule_based_real_data',
                'training_timestamp': datetime.now().isoformat(),
                'thresholds': thresholds,
                'performance': results,
                'training_data_size': len(self.real_data)
            }
            
            os.makedirs("../ml_models", exist_ok=True)
            model_path = "../ml_models/real_data_model.json"
            
            with open(model_path, 'w') as f:
                json.dump(model_config, f, indent=2)
            
            print(f"💾 Model saved to {model_path}")
            return model_path
            
        except Exception as e:
            print(f"❌ Error saving model: {e}")
            return None
    
    def predict_anomaly(self, metrics, thresholds):
        """Predict if given metrics indicate an anomaly."""
        if not thresholds:
            return False, 0.0
        
        # Apply rules
        cpu_high = metrics.get('cpu_usage', 0) > thresholds['cpu_threshold']
        memory_high = metrics.get('memory_usage', 0) > thresholds['memory_threshold']
        load_high = metrics.get('load_1m', 0) > thresholds['load_threshold']
        disk_high = metrics.get('disk_usage', 0) > thresholds['disk_threshold']
        
        is_anomaly = cpu_high or memory_high or load_high or disk_high
        
        # Simple confidence calculation
        confidence = 0.0
        if cpu_high:
            confidence += 0.3
        if memory_high:
            confidence += 0.3
        if load_high:
            confidence += 0.2
        if disk_high:
            confidence += 0.2
        
        return is_anomaly, min(confidence, 1.0)

def collect_live_metrics():
    """Collect live metrics from Prometheus for testing."""
    try:
        from simple_real_data_collector import SimpleRealDataCollector
        collector = SimpleRealDataCollector()
        return collector.collect_current_metrics()
    except Exception as e:
        print(f"❌ Error collecting live metrics: {e}")
        return None

def main():
    """Main training and testing pipeline."""
    print("🚀 SmartCloudOps AI - Real Data ML Training")
    print("=" * 50)
    
    # Initialize trainer
    trainer = SimpleMLTrainer()
    
    # Step 1: Load real data
    print("\n1. Loading real training data...")
    if not trainer.load_real_data():
        print("❌ Failed to load real data. Run simple_real_data_collector.py first.")
        return
    
    # Step 2: Analyze data
    print("\n2. Analyzing real data patterns...")
    analysis = trainer.analyze_real_data()
    
    # Step 3: Create model
    print("\n3. Training rule-based model on real data...")
    thresholds = trainer.create_simple_rules()
    
    if not thresholds:
        print("❌ Failed to create model")
        return
    
    # Step 4: Test model
    print("\n4. Testing model performance...")
    results = trainer.test_simple_model(thresholds)
    
    # Step 5: Save model
    print("\n5. Saving trained model...")
    model_path = trainer.save_trained_model(thresholds, results)
    
    # Step 6: Test with live data
    print("\n6. Testing with live infrastructure data...")
    live_metrics = collect_live_metrics()
    
    if live_metrics:
        is_anomaly, confidence = trainer.predict_anomaly(live_metrics, thresholds)
        
        print(f"🔍 Live Prediction:")
        print(f"   Status: {'🚨 ANOMALY' if is_anomaly else '✅ NORMAL'}")
        print(f"   Confidence: {confidence:.3f}")
        print(f"   CPU Usage: {live_metrics.get('cpu_usage', 0):.2f}%")
        print(f"   Memory Usage: {live_metrics.get('memory_usage', 0):.2f}%")
        print(f"   Load: {live_metrics.get('load_1m', 0):.2f}")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 REAL DATA TRAINING COMPLETE")
    print("=" * 50)
    print(f"✅ Training data: {analysis['total_points']} real data points")
    print(f"✅ Model accuracy: {results['accuracy']:.3f}")
    print(f"✅ F1-Score: {results['f1_score']:.3f}")
    print(f"✅ Model saved: {model_path}")
    print("\n🚀 Your anomaly detection now uses REAL infrastructure data!")

if __name__ == "__main__":
    main()
