#!/usr/bin/env python3
"""
SmartCloudOps AI - Optimized Real Data Model Training
====================================================

Optimized training focused on achieving ALL target metrics:
- Target Accuracy: 95%+
- Target Precision: 85%+
- Target Recall: 90%+ (PRIORITY)
- Target F1-Score: 87%+

Key optimizations:
- Recall-focused threshold optimization
- Advanced ensemble techniques
- Improved class balancing strategies
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import json
import warnings
from typing import Dict, List, Tuple
import joblib

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score,
    precision_recall_curve
)
from sklearn.preprocessing import RobustScaler
from sklearn.feature_selection import SelectKBest, f_classif
from imblearn.over_sampling import SMOTE
from imblearn.combine import SMOTETomek

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedRealDataTrainer:
    """
    Optimized trainer specifically tuned for real data with focus on recall.
    """
    
    def __init__(self):
        """Initialize the optimized trainer."""
        self.target_performance = {
            'accuracy': 0.95,
            'precision': 0.85,
            'recall': 0.90,  # PRIMARY FOCUS
            'f1_score': 0.87,
            'auc_roc': 0.92
        }
        
        self.best_model = None
        self.scaler = None
        self.feature_selector = None
        self.optimal_threshold = 0.5
        
        print("🎯 Optimized Real Data Trainer - RECALL FOCUSED")
        print("=" * 60)
    
    def load_and_preprocess_data(self, data_path: str) -> pd.DataFrame:
        """Load and preprocess real training data."""
        df = pd.read_csv(data_path)
        
        print(f"📊 Loaded dataset: {len(df)} samples")
        
        # Basic data cleaning
        df = df.fillna(0)
        df = df.replace([np.inf, -np.inf], 0)
        
        # Enhanced feature engineering for real data
        df_enhanced = self.create_optimized_features(df)
        
        return df_enhanced
    
    def create_optimized_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create optimized features for anomaly detection."""
        df_new = df.copy()
        
        print("🔧 Creating optimized features...")
        
        # 1. Statistical aggregations
        numeric_cols = ['cpu_usage', 'memory_usage', 'load_1m', 'disk_usage']
        
        # Rolling statistics for time series patterns
        if 'timestamp' in df_new.columns:
            df_new['timestamp'] = pd.to_datetime(df_new['timestamp'])
            df_new = df_new.sort_values('timestamp')
            
            for col in numeric_cols:
                if col in df_new.columns:
                    # Rolling means
                    df_new[f'{col}_roll3'] = df_new[col].rolling(3, min_periods=1).mean()
                    df_new[f'{col}_roll5'] = df_new[col].rolling(5, min_periods=1).mean()
                    
                    # Rolling standard deviation (volatility)
                    df_new[f'{col}_rollstd'] = df_new[col].rolling(3, min_periods=1).std().fillna(0)
                    
                    # Rate of change
                    df_new[f'{col}_change'] = df_new[col].pct_change().fillna(0)
                    df_new[f'{col}_change'] = df_new[f'{col}_change'].replace([np.inf, -np.inf], 0)
        
        # 2. Interaction features
        if 'cpu_usage' in df_new.columns and 'memory_usage' in df_new.columns:
            df_new['cpu_mem_product'] = df_new['cpu_usage'] * df_new['memory_usage']
            df_new['cpu_mem_sum'] = df_new['cpu_usage'] + df_new['memory_usage']
        
        # 3. Threshold-based features (domain knowledge)
        thresholds = {
            'cpu_usage': [50, 75, 90],
            'memory_usage': [60, 80, 95],
            'load_1m': [1.0, 2.0, 5.0],
            'disk_usage': [70, 85, 95]
        }
        
        for metric, thresh_list in thresholds.items():
            if metric in df_new.columns:
                for i, threshold in enumerate(thresh_list):
                    df_new[f'{metric}_above_{threshold}'] = (df_new[metric] > threshold).astype(int)
        
        # 4. Percentile ranks
        for col in numeric_cols:
            if col in df_new.columns:
                df_new[f'{col}_percentile'] = df_new[col].rank(pct=True)
        
        # 5. System stress indicators
        if all(col in df_new.columns for col in ['cpu_usage', 'memory_usage', 'load_1m']):
            df_new['stress_score'] = (
                (df_new['cpu_usage'] > 75).astype(int) +
                (df_new['memory_usage'] > 80).astype(int) +
                (df_new['load_1m'] > 2.0).astype(int)
            )
            df_new['high_stress'] = (df_new['stress_score'] >= 2).astype(int)
        
        print(f"✅ Feature engineering complete: {len(df_new.columns)} features")
        return df_new
    
    def optimize_for_recall(self, model, X_train, y_train, X_val, y_val):
        """
        Optimize model threshold for maximum recall while maintaining precision.
        """
        print("🎯 Optimizing threshold for recall...")
        
        # Get prediction probabilities
        y_proba = model.predict_proba(X_val)[:, 1]
        
        # Test different thresholds
        thresholds = np.arange(0.1, 0.9, 0.05)
        best_threshold = 0.5
        best_score = 0
        
        results = []
        
        for threshold in thresholds:
            y_pred = (y_proba >= threshold).astype(int)
            
            precision = precision_score(y_val, y_pred, zero_division=0)
            recall = recall_score(y_val, y_pred, zero_division=0)
            f1 = f1_score(y_val, y_pred, zero_division=0)
            
            # Score prioritizing recall but requiring minimum precision
            if precision >= 0.5:  # Minimum precision threshold
                score = recall * 0.7 + f1 * 0.3  # Recall-focused scoring
                
                results.append({
                    'threshold': threshold,
                    'precision': precision,
                    'recall': recall,
                    'f1': f1,
                    'score': score
                })
                
                if score > best_score:
                    best_score = score
                    best_threshold = threshold
        
        self.optimal_threshold = best_threshold
        
        print(f"✅ Optimal threshold: {best_threshold:.3f}")
        
        # Show best threshold performance
        if results:
            best_result = next((r for r in results if r['threshold'] == best_threshold), None)
            if best_result:
                print(f"   Precision: {best_result['precision']:.3f}")
                print(f"   Recall: {best_result['recall']:.3f}")
                print(f"   F1-Score: {best_result['f1']:.3f}")
            else:
                print("   Using default threshold (no valid results found)")
        else:
            print("   Using default threshold (no results generated)")
        
        return best_threshold
    
    def train_recall_optimized_models(self, X_train, y_train, X_val, y_val):
        """
        Train models optimized for recall.
        """
        print("🤖 Training recall-optimized models...")
        
        models = {}
        
        # 1. Random Forest with recall-focused parameters
        rf_params = {
            'n_estimators': 300,
            'max_depth': 15,
            'min_samples_split': 2,
            'min_samples_leaf': 1,
            'class_weight': 'balanced_subsample',  # Helps with recall
            'random_state': 42
        }
        
        rf_model = RandomForestClassifier(**rf_params)
        rf_model.fit(X_train, y_train)
        rf_threshold = self.optimize_for_recall(rf_model, X_train, y_train, X_val, y_val)
        
        models['random_forest'] = {
            'model': rf_model,
            'threshold': rf_threshold
        }
        
        # 2. Gradient Boosting with recall focus
        gb_params = {
            'n_estimators': 200,
            'learning_rate': 0.1,
            'max_depth': 5,
            'subsample': 0.9,
            'random_state': 42
        }
        
        gb_model = GradientBoostingClassifier(**gb_params)
        gb_model.fit(X_train, y_train)
        gb_threshold = self.optimize_for_recall(gb_model, X_train, y_train, X_val, y_val)
        
        models['gradient_boosting'] = {
            'model': gb_model,
            'threshold': gb_threshold
        }
        
        # 3. Logistic Regression with class weight
        lr_params = {
            'C': 10,
            'class_weight': 'balanced',
            'max_iter': 2000,
            'random_state': 42
        }
        
        lr_model = LogisticRegression(**lr_params)
        lr_model.fit(X_train, y_train)
        lr_threshold = self.optimize_for_recall(lr_model, X_train, y_train, X_val, y_val)
        
        models['logistic_regression'] = {
            'model': lr_model,
            'threshold': lr_threshold
        }
        
        return models
    
    def evaluate_with_threshold(self, model_info, X_test, y_test):
        """Evaluate model with optimized threshold."""
        model = model_info['model']
        threshold = model_info['threshold']
        
        # Get predictions with optimized threshold
        y_proba = model.predict_proba(X_test)[:, 1]
        y_pred = (y_proba >= threshold).astype(int)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc_roc = roc_auc_score(y_test, y_proba)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        cm_dict = {
            'true_positives': int(cm[1, 1]) if cm.shape == (2, 2) else 0,
            'false_positives': int(cm[0, 1]) if cm.shape == (2, 2) else 0,
            'true_negatives': int(cm[0, 0]) if cm.shape == (2, 2) else 0,
            'false_negatives': int(cm[1, 0]) if cm.shape == (2, 2) else 0
        }
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'auc_roc': auc_roc,
            'confusion_matrix': cm_dict,
            'threshold': threshold
        }
    
    def train_optimized_model(self, data_path: str):
        """Complete optimized training pipeline."""
        print("🚀 Starting Optimized Real Data Training")
        print("🎯 PRIMARY GOAL: Achieve 90%+ Recall")
        print("=" * 60)
        
        # 1. Load and preprocess data
        df = self.load_and_preprocess_data(data_path)
        
        # 2. Prepare features
        feature_cols = [col for col in df.columns if col not in ['is_anomaly', 'timestamp']]
        X = df[feature_cols].select_dtypes(include=[np.number])
        y = df['is_anomaly']
        
        print(f"📊 Features: {X.shape[1]}")
        print(f"📊 Samples: {len(X)}")
        print(f"📊 Anomaly rate: {y.mean()*100:.1f}%")
        
        # 3. Split data
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
        )
        
        print(f"📊 Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        # 4. Scale features
        self.scaler = RobustScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 5. Handle class imbalance with SMOTE-Tomek (better for recall)
        print("⚖️ Applying SMOTE-Tomek for class balancing...")
        smote_tomek = SMOTETomek(random_state=42)
        X_train_balanced, y_train_balanced = smote_tomek.fit_resample(X_train_scaled, y_train)
        
        # 6. Feature selection
        print("🔍 Selecting top features...")
        self.feature_selector = SelectKBest(f_classif, k=min(30, X_train_balanced.shape[1]))
        X_train_selected = self.feature_selector.fit_transform(X_train_balanced, y_train_balanced)
        X_val_selected = self.feature_selector.transform(X_val_scaled)
        X_test_selected = self.feature_selector.transform(X_test_scaled)
        
        # 7. Train models
        models = self.train_recall_optimized_models(
            X_train_selected, y_train_balanced, X_val_selected, y_val
        )
        
        # 8. Evaluate all models
        print("\n📊 Model Evaluation Results:")
        print("=" * 60)
        
        best_model_name = None
        best_score = 0
        results = {}
        
        for name, model_info in models.items():
            perf = self.evaluate_with_threshold(model_info, X_test_selected, y_test)
            results[name] = perf
            
            # Calculate recall-focused score
            recall_score_val = perf['recall'] * 0.6 + perf['f1_score'] * 0.4
            
            print(f"\n🤖 {name}:")
            print(f"   Accuracy: {perf['accuracy']:.4f}")
            print(f"   Precision: {perf['precision']:.4f}")
            print(f"   Recall: {perf['recall']:.4f} {'✅' if perf['recall'] >= 0.90 else '❌'}")
            print(f"   F1-Score: {perf['f1_score']:.4f}")
            print(f"   AUC-ROC: {perf['auc_roc']:.4f}")
            print(f"   Threshold: {perf['threshold']:.3f}")
            print(f"   Recall Score: {recall_score_val:.4f}")
            
            if recall_score_val > best_score:
                best_score = recall_score_val
                best_model_name = name
        
        # 9. Select best model
        best_performance = results[best_model_name]
        self.best_model = models[best_model_name]['model']
        self.optimal_threshold = models[best_model_name]['threshold']
        
        print(f"\n🥇 Best Model: {best_model_name}")
        print("=" * 60)
        
        # 10. Generate report
        report = self.generate_optimized_report(best_model_name, best_performance)
        
        return report
    
    def generate_optimized_report(self, model_name: str, performance: Dict):
        """Generate comprehensive report."""
        report = {
            'model_type': 'optimized_real_data',
            'version': '4.0.0',
            'training_timestamp': datetime.now().isoformat(),
            'created_by': 'optimized_real_data_trainer',
            'description': 'Optimized model for real data with recall focus',
            
            'best_model': {
                'name': model_name,
                'optimal_threshold': self.optimal_threshold
            },
            
            'performance': performance,
            
            'target_achievement': {
                'accuracy_achieved': performance['accuracy'] >= self.target_performance['accuracy'],
                'precision_achieved': performance['precision'] >= self.target_performance['precision'],
                'recall_achieved': performance['recall'] >= self.target_performance['recall'],
                'f1_achieved': performance['f1_score'] >= self.target_performance['f1_score'],
                'auc_achieved': performance['auc_roc'] >= self.target_performance['auc_roc']
            },
            
            'optimizations': [
                'recall_focused_threshold_optimization',
                'enhanced_feature_engineering',
                'smote_tomek_class_balancing',
                'domain_knowledge_features',
                'stress_indicator_features',
                'time_series_features'
            ],
            
            'thresholds': {
                'cpu_threshold': 75.0,
                'memory_threshold': 80.0,
                'load_threshold': 2.0,
                'disk_threshold': 85.0,
                'prediction_threshold': self.optimal_threshold
            }
        }
        
        print("\n🏆 FINAL PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"🥇 Model: {model_name}")
        print(f"📊 Accuracy: {performance['accuracy']:.4f} {'✅' if report['target_achievement']['accuracy_achieved'] else '❌'}")
        print(f"📊 Precision: {performance['precision']:.4f} {'✅' if report['target_achievement']['precision_achieved'] else '❌'}")
        print(f"📊 Recall: {performance['recall']:.4f} {'✅' if report['target_achievement']['recall_achieved'] else '❌'}")
        print(f"📊 F1-Score: {performance['f1_score']:.4f} {'✅' if report['target_achievement']['f1_achieved'] else '❌'}")
        print(f"📊 AUC-ROC: {performance['auc_roc']:.4f} {'✅' if report['target_achievement']['auc_achieved'] else '❌'}")
        print(f"🎯 Optimal Threshold: {self.optimal_threshold:.3f}")
        
        # Overall achievement
        achieved_count = sum(report['target_achievement'].values())
        total_targets = len(report['target_achievement'])
        
        print(f"\n🎯 Targets Achieved: {achieved_count}/{total_targets}")
        if achieved_count == total_targets:
            print("🏆 ALL TARGETS ACHIEVED! 🎉")
        elif achieved_count >= 4:
            print("🥈 Excellent Performance!")
        else:
            print("🥉 Good Performance - Room for improvement")
        
        return report
    
    def save_model(self, report: Dict, output_path: str):
        """Save the optimized model."""
        try:
            # Save model artifacts
            artifacts = {
                'model': self.best_model,
                'scaler': self.scaler,
                'feature_selector': self.feature_selector,
                'optimal_threshold': self.optimal_threshold,
                'report': report
            }
            
            model_path = output_path.replace('.json', '_optimized.pkl')
            joblib.dump(artifacts, model_path)
            
            # Save JSON report
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            print(f"\n✅ Model saved to: {model_path}")
            print(f"✅ Report saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"❌ Error saving model: {e}")

def main():
    """Main execution."""
    trainer = OptimizedRealDataTrainer()
    
    # Train optimized model
    data_path = '/home/dileep-reddy/smartcloudops-ai/data/real_training_data.csv'
    report = trainer.train_optimized_model(data_path)
    
    # Save model
    output_path = '/home/dileep-reddy/smartcloudops-ai/ml_models/optimized_real_model.json'
    trainer.save_model(report, output_path)
    
    print("\n🎉 Optimized Training Complete!")

if __name__ == "__main__":
    main()
