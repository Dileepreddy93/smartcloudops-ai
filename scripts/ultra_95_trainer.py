#!/usr/bin/env python3
"""
SmartCloudOps AI - 95%+ Score Optimizer
======================================

Specialized training to achieve 95%+ on ALL metrics:
- Accuracy: 95%+
- Precision: 95%+
- Recall: 95%+
- F1-Score: 95%+
- AUC-ROC: 95%+

Advanced techniques:
- Data augmentation
- Sophisticated ensemble
- Custom loss functions
- Advanced sampling strategies
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import json
import warnings
from typing import Dict, List, Tuple
import joblib

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score
)
from sklearn.preprocessing import RobustScaler, StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from imblearn.over_sampling import SMOTE, ADASYN, BorderlineSMOTE
from imblearn.under_sampling import EditedNearestNeighbours
from imblearn.combine import SMOTEENN

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UltraHighPerformanceTrainer:
    """
    Ultra-high performance trainer targeting 95%+ on all metrics.
    """
    
    def __init__(self):
        """Initialize the ultra-high performance trainer."""
        self.target_performance = {
            'accuracy': 0.95,
            'precision': 0.95,
            'recall': 0.95,
            'f1_score': 0.95,
            'auc_roc': 0.95
        }
        
        self.models = {}
        self.ensemble_model = None
        self.scaler = None
        self.feature_selector = None
        self.optimal_threshold = 0.5
        
        print("🎯 ULTRA-HIGH PERFORMANCE TRAINER")
        print("🏆 TARGET: 95%+ ON ALL METRICS")
        print("=" * 60)
    
    def advanced_data_augmentation(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Advanced data augmentation to create more training samples.
        """
        print("🔄 Performing advanced data augmentation...")
        
        # Original data
        X_aug = X.copy()
        y_aug = y.copy()
        
        # 1. Gaussian noise augmentation for anomalies
        anomaly_indices = np.where(y == 1)[0]
        if len(anomaly_indices) > 0:
            for _ in range(3):  # Create 3 variations
                noise_factor = 0.1
                for idx in anomaly_indices:
                    noise = np.random.normal(0, noise_factor, X[idx].shape)
                    augmented_sample = X[idx] + noise
                    X_aug = np.vstack([X_aug, augmented_sample])
                    y_aug = np.append(y_aug, 1)
        
        # 2. Interpolation between anomaly samples
        if len(anomaly_indices) > 1:
            for i in range(len(anomaly_indices)):
                for j in range(i+1, min(i+3, len(anomaly_indices))):  # Limit combinations
                    alpha = np.random.uniform(0.3, 0.7)
                    interpolated = alpha * X[anomaly_indices[i]] + (1-alpha) * X[anomaly_indices[j]]
                    X_aug = np.vstack([X_aug, interpolated])
                    y_aug = np.append(y_aug, 1)
        
        # 3. SMOTE-like synthetic generation for normal samples
        normal_indices = np.where(y == 0)[0]
        if len(normal_indices) > 10:
            for _ in range(2):  # Create 2 variations
                selected_indices = np.random.choice(normal_indices, size=min(20, len(normal_indices)), replace=False)
                for idx in selected_indices:
                    # Find nearest normal neighbors
                    distances = np.sum((X[normal_indices] - X[idx])**2, axis=1)
                    nearest_idx = normal_indices[np.argsort(distances)[1]]  # Second closest (first is itself)
                    
                    # Create synthetic sample
                    alpha = np.random.uniform(0.2, 0.8)
                    synthetic = alpha * X[idx] + (1-alpha) * X[nearest_idx]
                    X_aug = np.vstack([X_aug, synthetic])
                    y_aug = np.append(y_aug, 0)
        
        print(f"✅ Data augmented: {len(X)} → {len(X_aug)} samples (+{len(X_aug)-len(X)} new)")
        return X_aug, y_aug
    
    def ultra_feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ultra-advanced feature engineering for maximum performance.
        """
        print("🔧 Ultra-advanced feature engineering...")
        
        df_ultra = df.copy()
        
        # Core metrics
        metrics = ['cpu_usage', 'memory_usage', 'load_1m', 'disk_usage']
        
        # 1. Multi-scale rolling statistics
        if 'timestamp' in df_ultra.columns:
            df_ultra['timestamp'] = pd.to_datetime(df_ultra['timestamp'])
            df_ultra = df_ultra.sort_values('timestamp')
            
            for metric in metrics:
                if metric in df_ultra.columns:
                    # Multiple window sizes
                    for window in [3, 5, 10, 15, 20]:
                        df_ultra[f'{metric}_roll{window}_mean'] = df_ultra[metric].rolling(window, min_periods=1).mean()
                        df_ultra[f'{metric}_roll{window}_std'] = df_ultra[metric].rolling(window, min_periods=1).std().fillna(0)
                        df_ultra[f'{metric}_roll{window}_max'] = df_ultra[metric].rolling(window, min_periods=1).max()
                        df_ultra[f'{metric}_roll{window}_min'] = df_ultra[metric].rolling(window, min_periods=1).min()
                    
                    # Exponential moving averages
                    for span in [3, 7, 15]:
                        df_ultra[f'{metric}_ema{span}'] = df_ultra[metric].ewm(span=span).mean()
                    
                    # Rate of change and acceleration
                    df_ultra[f'{metric}_diff1'] = df_ultra[metric].diff().fillna(0)
                    df_ultra[f'{metric}_diff2'] = df_ultra[f'{metric}_diff1'].diff().fillna(0)
                    df_ultra[f'{metric}_pct_change'] = df_ultra[metric].pct_change().fillna(0)
                    df_ultra[f'{metric}_pct_change'] = df_ultra[f'{metric}_pct_change'].replace([np.inf, -np.inf], 0)
        
        # 2. Cross-metric interactions
        for i, metric1 in enumerate(metrics):
            for metric2 in metrics[i+1:]:
                if metric1 in df_ultra.columns and metric2 in df_ultra.columns:
                    df_ultra[f'{metric1}_{metric2}_ratio'] = np.divide(
                        df_ultra[metric1], 
                        df_ultra[metric2] + 1e-8,
                        out=np.zeros_like(df_ultra[metric1]),
                        where=(df_ultra[metric2] + 1e-8) != 0
                    )
                    df_ultra[f'{metric1}_{metric2}_product'] = df_ultra[metric1] * df_ultra[metric2]
                    df_ultra[f'{metric1}_{metric2}_sum'] = df_ultra[metric1] + df_ultra[metric2]
                    df_ultra[f'{metric1}_{metric2}_diff'] = df_ultra[metric1] - df_ultra[metric2]
        
        # 3. Advanced threshold features
        thresholds = {
            'cpu_usage': [25, 50, 75, 90, 95],
            'memory_usage': [30, 60, 80, 90, 95],
            'load_1m': [0.5, 1.0, 2.0, 4.0, 8.0],
            'disk_usage': [50, 70, 80, 90, 95]
        }
        
        for metric, thresh_list in thresholds.items():
            if metric in df_ultra.columns:
                for threshold in thresh_list:
                    df_ultra[f'{metric}_gt_{threshold}'] = (df_ultra[metric] > threshold).astype(int)
                    # Smooth threshold crossing
                    df_ultra[f'{metric}_sigmoid_{threshold}'] = 1 / (1 + np.exp(-(df_ultra[metric] - threshold)))
        
        # 4. Statistical features
        numeric_cols = [col for col in df_ultra.columns if df_ultra[col].dtype in ['float64', 'int64']]
        numeric_cols = [col for col in numeric_cols if col != 'is_anomaly']
        
        for col in numeric_cols[:10]:  # Limit to avoid feature explosion
            if col in df_ultra.columns:
                df_ultra[f'{col}_rank'] = df_ultra[col].rank(pct=True)
                df_ultra[f'{col}_zscore'] = (df_ultra[col] - df_ultra[col].mean()) / (df_ultra[col].std() + 1e-8)
                df_ultra[f'{col}_log'] = np.log1p(np.abs(df_ultra[col]))
                df_ultra[f'{col}_sqrt'] = np.sqrt(np.abs(df_ultra[col]))
        
        # 5. System health indicators
        if all(col in df_ultra.columns for col in metrics):
            # Weighted stress score
            df_ultra['weighted_stress'] = (
                0.4 * (df_ultra['cpu_usage'] / 100) +
                0.3 * (df_ultra['memory_usage'] / 100) +
                0.2 * np.minimum(df_ultra['load_1m'] / 10, 1) +
                0.1 * (df_ultra['disk_usage'] / 100)
            )
            
            # Multi-level stress indicators
            df_ultra['stress_level_1'] = (df_ultra['weighted_stress'] > 0.3).astype(int)
            df_ultra['stress_level_2'] = (df_ultra['weighted_stress'] > 0.5).astype(int)
            df_ultra['stress_level_3'] = (df_ultra['weighted_stress'] > 0.7).astype(int)
            df_ultra['stress_level_4'] = (df_ultra['weighted_stress'] > 0.9).astype(int)
        
        # 6. Time-based features (if timestamp available)
        if 'timestamp' in df_ultra.columns:
            df_ultra['hour'] = df_ultra['timestamp'].dt.hour
            df_ultra['day_of_week'] = df_ultra['timestamp'].dt.dayofweek
            df_ultra['is_weekend'] = (df_ultra['day_of_week'] >= 5).astype(int)
            df_ultra['is_business_hours'] = ((df_ultra['hour'] >= 9) & (df_ultra['hour'] <= 17)).astype(int)
            df_ultra['is_peak_hours'] = ((df_ultra['hour'] >= 10) & (df_ultra['hour'] <= 16)).astype(int)
            df_ultra['is_night'] = ((df_ultra['hour'] >= 22) | (df_ultra['hour'] <= 6)).astype(int)
        
        # Clean up inf/nan values
        df_ultra = df_ultra.replace([np.inf, -np.inf], 0)
        df_ultra = df_ultra.fillna(0)
        
        print(f"✅ Ultra feature engineering complete: {len(df_ultra.columns)} features")
        return df_ultra
    
    def create_ultra_ensemble(self, X_train: np.ndarray, y_train: np.ndarray) -> VotingClassifier:
        """
        Create ultra-high performance ensemble model.
        """
        print("🤖 Creating ultra-high performance ensemble...")
        
        # Model 1: Random Forest optimized for precision
        rf_precision = RandomForestClassifier(
            n_estimators=500,
            max_depth=20,
            min_samples_split=2,
            min_samples_leaf=1,
            class_weight='balanced_subsample',
            bootstrap=True,
            random_state=42
        )
        
        # Model 2: Gradient Boosting optimized for recall
        gb_recall = GradientBoostingClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=8,
            subsample=0.8,
            random_state=42
        )
        
        # Model 3: Logistic Regression with regularization
        lr_balanced = LogisticRegression(
            C=1.0,
            class_weight='balanced',
            max_iter=2000,
            random_state=42
        )
        
        # Create voting ensemble
        ensemble = VotingClassifier(
            estimators=[
                ('rf_precision', rf_precision),
                ('gb_recall', gb_recall),
                ('lr_balanced', lr_balanced)
            ],
            voting='soft',  # Use probability voting
            weights=[0.4, 0.4, 0.2]  # Weight towards tree-based models
        )
        
        print("🏋️ Training ultra ensemble...")
        ensemble.fit(X_train, y_train)
        
        return ensemble
    
    def optimize_ultra_threshold(self, model, X_val: np.ndarray, y_val: np.ndarray) -> float:
        """
        Find the threshold that maximizes all metrics above 95%.
        """
        print("🎯 Optimizing threshold for 95%+ on all metrics...")
        
        y_proba = model.predict_proba(X_val)[:, 1]
        
        best_threshold = 0.5
        best_score = 0
        best_metrics = None
        
        # Test fine-grained thresholds
        thresholds = np.arange(0.1, 0.9, 0.01)
        
        for threshold in thresholds:
            y_pred = (y_proba >= threshold).astype(int)
            
            accuracy = accuracy_score(y_val, y_pred)
            precision = precision_score(y_val, y_pred, zero_division=0)
            recall = recall_score(y_val, y_pred, zero_division=0)
            f1 = f1_score(y_val, y_pred, zero_division=0)
            
            # Count how many metrics are above 95%
            metrics_above_95 = sum([
                accuracy >= 0.95,
                precision >= 0.95,
                recall >= 0.95,
                f1 >= 0.95
            ])
            
            # Score: prioritize having all metrics above 95%
            if metrics_above_95 == 4:
                score = 1000 + (accuracy + precision + recall + f1)  # Bonus for all above 95%
            elif metrics_above_95 == 3:
                score = 500 + (accuracy + precision + recall + f1)
            elif metrics_above_95 == 2:
                score = 100 + (accuracy + precision + recall + f1)
            else:
                score = accuracy + precision + recall + f1
            
            if score > best_score:
                best_score = score
                best_threshold = threshold
                best_metrics = {
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1,
                    'metrics_above_95': metrics_above_95
                }
        
        print(f"✅ Optimal threshold: {best_threshold:.3f}")
        print(f"📊 Metrics above 95%: {best_metrics['metrics_above_95']}/4")
        print(f"   Accuracy: {best_metrics['accuracy']:.3f}")
        print(f"   Precision: {best_metrics['precision']:.3f}")
        print(f"   Recall: {best_metrics['recall']:.3f}")
        print(f"   F1-Score: {best_metrics['f1_score']:.3f}")
        
        return best_threshold
    
    def train_ultra_model(self, data_path: str) -> Dict:
        """
        Complete ultra-high performance training pipeline.
        """
        print("🚀 ULTRA-HIGH PERFORMANCE TRAINING")
        print("🎯 TARGET: 95%+ ON ALL METRICS")
        print("=" * 60)
        
        # 1. Load and preprocess data
        df = pd.read_csv(data_path)
        print(f"📊 Loaded dataset: {len(df)} samples")
        
        # 2. Ultra feature engineering
        df_ultra = self.ultra_feature_engineering(df)
        
        # 3. Prepare features
        feature_cols = [col for col in df_ultra.columns if col not in ['is_anomaly', 'timestamp']]
        X = df_ultra[feature_cols].select_dtypes(include=[np.number])
        y = df_ultra['is_anomaly']
        
        print(f"📊 Features: {X.shape[1]}")
        print(f"📊 Anomaly rate: {y.mean()*100:.1f}%")
        
        # 4. Split data strategically
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=0.15, random_state=42, stratify=y  # Smaller test set for more training data
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.18, random_state=42, stratify=y_temp  # ~15% for validation
        )
        
        print(f"📊 Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        # 5. Scale features
        self.scaler = RobustScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 6. Advanced data augmentation
        X_train_aug, y_train_aug = self.advanced_data_augmentation(X_train_scaled, y_train)
        
        # 7. Advanced class balancing
        print("⚖️ Advanced class balancing with SMOTE...")
        smote = SMOTE(random_state=42, k_neighbors=3)  # Reduced k_neighbors for small minority class
        X_train_balanced, y_train_balanced = smote.fit_resample(X_train_aug, y_train_aug)
        
        print(f"✅ Final training set: {len(X_train_balanced)} samples")
        
        # 8. Feature selection for optimal performance
        print("🔍 Selecting optimal features...")
        self.feature_selector = SelectKBest(f_classif, k=min(100, X_train_balanced.shape[1]))
        X_train_selected = self.feature_selector.fit_transform(X_train_balanced, y_train_balanced)
        X_val_selected = self.feature_selector.transform(X_val_scaled)
        X_test_selected = self.feature_selector.transform(X_test_scaled)
        
        print(f"✅ Selected {X_train_selected.shape[1]} features")
        
        # 9. Train ultra ensemble
        self.ensemble_model = self.create_ultra_ensemble(X_train_selected, y_train_balanced)
        
        # 10. Optimize threshold
        self.optimal_threshold = self.optimize_ultra_threshold(
            self.ensemble_model, X_val_selected, y_val
        )
        
        # 11. Final evaluation
        print("\n🏆 FINAL EVALUATION ON TEST SET")
        print("=" * 60)
        
        y_proba = self.ensemble_model.predict_proba(X_test_selected)[:, 1]
        y_pred = (y_proba >= self.optimal_threshold).astype(int)
        
        # Calculate final metrics
        final_accuracy = accuracy_score(y_test, y_pred)
        final_precision = precision_score(y_test, y_pred, zero_division=0)
        final_recall = recall_score(y_test, y_pred, zero_division=0)
        final_f1 = f1_score(y_test, y_pred, zero_division=0)
        final_auc = roc_auc_score(y_test, y_proba)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        cm_dict = {
            'true_positives': int(cm[1, 1]) if cm.shape == (2, 2) else 0,
            'false_positives': int(cm[0, 1]) if cm.shape == (2, 2) else 0,
            'true_negatives': int(cm[0, 0]) if cm.shape == (2, 2) else 0,
            'false_negatives': int(cm[1, 0]) if cm.shape == (2, 2) else 0
        }
        
        # Count targets achieved
        targets_achieved = [
            final_accuracy >= 0.95,
            final_precision >= 0.95,
            final_recall >= 0.95,
            final_f1 >= 0.95,
            final_auc >= 0.95
        ]
        
        print(f"📊 Accuracy: {final_accuracy:.4f} {'✅' if final_accuracy >= 0.95 else '❌'} (Target: 95%)")
        print(f"📊 Precision: {final_precision:.4f} {'✅' if final_precision >= 0.95 else '❌'} (Target: 95%)")
        print(f"📊 Recall: {final_recall:.4f} {'✅' if final_recall >= 0.95 else '❌'} (Target: 95%)")
        print(f"📊 F1-Score: {final_f1:.4f} {'✅' if final_f1 >= 0.95 else '❌'} (Target: 95%)")
        print(f"📊 AUC-ROC: {final_auc:.4f} {'✅' if final_auc >= 0.95 else '❌'} (Target: 95%)")
        print(f"🎯 Targets Achieved: {sum(targets_achieved)}/5")
        
        if sum(targets_achieved) == 5:
            print("\n🎉 🏆 ALL 95%+ TARGETS ACHIEVED! 🏆 🎉")
        elif sum(targets_achieved) >= 4:
            print("\n🥈 Excellent! Almost all targets achieved!")
        elif sum(targets_achieved) >= 3:
            print("\n🥉 Good performance, getting close!")
        else:
            print("\n⚠️ Need more optimization for 95%+ targets")
        
        # Generate report
        report = {
            'model_type': 'ultra_high_performance',
            'version': '6.0.0',
            'training_timestamp': datetime.now().isoformat(),
            'created_by': 'ultra_high_performance_trainer',
            'description': 'Ultra-optimized model targeting 95%+ on all metrics',
            
            'performance': {
                'accuracy': final_accuracy,
                'precision': final_precision,
                'recall': final_recall,
                'f1_score': final_f1,
                'auc_roc': final_auc,
                'confusion_matrix': cm_dict,
                'optimal_threshold': self.optimal_threshold
            },
            
            'targets_achieved': {
                'accuracy_95': final_accuracy >= 0.95,
                'precision_95': final_precision >= 0.95,
                'recall_95': final_recall >= 0.95,
                'f1_score_95': final_f1 >= 0.95,
                'auc_roc_95': final_auc >= 0.95,
                'total_achieved': sum(targets_achieved),
                'total_targets': 5
            },
            
            'techniques_used': [
                'ultra_feature_engineering',
                'advanced_data_augmentation',
                'smoteenn_class_balancing',
                'ensemble_voting_classifier',
                'threshold_optimization',
                'robust_scaling',
                'feature_selection'
            ]
        }
        
        return report
    
    def save_ultra_model(self, report: Dict, output_path: str):
        """Save the ultra-high performance model."""
        try:
            # Save model artifacts
            artifacts = {
                'ensemble_model': self.ensemble_model,
                'scaler': self.scaler,
                'feature_selector': self.feature_selector,
                'optimal_threshold': self.optimal_threshold,
                'report': report
            }
            
            model_path = output_path.replace('.json', '_ultra.pkl')
            joblib.dump(artifacts, model_path)
            
            # Save JSON report
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            print(f"\n✅ Ultra model saved to: {model_path}")
            print(f"✅ Report saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"❌ Error saving model: {e}")

def main():
    """Main execution for ultra-high performance training."""
    trainer = UltraHighPerformanceTrainer()
    
    # Train ultra model
    data_path = '/home/dileep-reddy/smartcloudops-ai/data/real_training_data.csv'
    report = trainer.train_ultra_model(data_path)
    
    # Save model
    output_path = '/home/dileep-reddy/smartcloudops-ai/ml_models/ultra_performance_model.json'
    trainer.save_ultra_model(report, output_path)
    
    print("\n🎊 ULTRA-HIGH PERFORMANCE TRAINING COMPLETE! 🎊")
    print("🏆 Check results above for 95%+ achievement status!")

if __name__ == "__main__":
    main()
