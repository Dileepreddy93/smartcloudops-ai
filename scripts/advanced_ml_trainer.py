#!/usr/bin/env python3
"""
SmartCloudOps AI - Advanced ML Training Pipeline
===============================================

High-performance ML training pipeline designed to achieve optimal scores:
- Target Accuracy: 95%+
- Target Precision: 85%+
- Target Recall: 90%+
- Target F1-Score: 87%+

Features:
- Advanced feature engineering
- Multiple ML algorithms
- Hyperparameter optimization
- Cross-validation
- Class imbalance handling
- Data augmentation
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import os
import json
import warnings
from typing import Dict, List, Tuple, Optional
import joblib
from dataclasses import dataclass

# ML Libraries
from sklearn.ensemble import RandomForestClassifier, IsolationForest, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import (
    train_test_split, cross_val_score, GridSearchCV, 
    StratifiedKFold, RandomizedSearchCV
)
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score,
    precision_recall_curve, roc_curve
)
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from imblearn.over_sampling import SMOTE, ADASYN
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTETomek

# Advanced ML libraries
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("⚠️ XGBoost not available. Install with: pip install xgboost")

try:
    import lightgbm as lgb
    LGB_AVAILABLE = True
except ImportError:
    LGB_AVAILABLE = False
    print("⚠️ LightGBM not available. Install with: pip install lightgbm")

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelPerformance:
    """Container for model performance metrics."""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    confusion_matrix: Dict
    cv_scores: List[float]
    training_time: float

class AdvancedMLTrainer:
    """
    Advanced ML trainer with state-of-the-art techniques for optimal performance.
    """
    
    def __init__(self, target_performance: Dict[str, float] = None):
        """
        Initialize the advanced ML trainer.
        
        Args:
            target_performance: Dict with target metrics
        """
        self.target_performance = target_performance or {
            'accuracy': 0.95,
            'precision': 0.85,
            'recall': 0.90,
            'f1_score': 0.87,
            'auc_roc': 0.92
        }
        
        self.models = {}
        self.best_model = None
        self.scaler = None
        self.feature_selector = None
        self.performance_results = []
        
        print("🚀 Advanced ML Trainer Initialized")
        print(f"📊 Target Performance Metrics:")
        for metric, target in self.target_performance.items():
            print(f"   {metric}: {target:.1%}")
    
    def load_data(self, data_path: str) -> pd.DataFrame:
        """Load and validate training data."""
        try:
            if data_path.endswith('.csv'):
                df = pd.read_csv(data_path)
            elif data_path.endswith('.json'):
                df = pd.read_json(data_path)
            else:
                raise ValueError(f"Unsupported file format: {data_path}")
            
            print(f"📊 Loaded dataset: {len(df)} samples")
            print(f"📊 Features: {df.columns.tolist()}")
            
            # Validate required columns
            required_cols = ['is_anomaly']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            raise
    
    def advanced_feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Advanced feature engineering to improve model performance.
        """
        print("🔧 Performing advanced feature engineering...")
        
        df_engineered = df.copy()
        
        # 1. Rolling statistics (time-series features)
        if 'timestamp' in df.columns:
            df_engineered['timestamp'] = pd.to_datetime(df_engineered['timestamp'])
            df_engineered = df_engineered.sort_values('timestamp')
            
            for col in ['cpu_usage', 'memory_usage', 'load_1m']:
                if col in df_engineered.columns:
                    # Rolling averages
                    df_engineered[f'{col}_rolling_3'] = df_engineered[col].rolling(3, min_periods=1).mean()
                    df_engineered[f'{col}_rolling_5'] = df_engineered[col].rolling(5, min_periods=1).mean()
                    df_engineered[f'{col}_rolling_10'] = df_engineered[col].rolling(10, min_periods=1).mean()
                    
                    # Rolling standard deviation
                    df_engineered[f'{col}_rolling_std'] = df_engineered[col].rolling(5, min_periods=1).std().fillna(0)
                    
                    # Rate of change
                    df_engineered[f'{col}_rate_change'] = df_engineered[col].pct_change().fillna(0)
                    
                    # Exponential moving average
                    df_engineered[f'{col}_ema'] = df_engineered[col].ewm(span=5).mean()
        
        # 2. Interaction features
        if 'cpu_usage' in df_engineered.columns and 'memory_usage' in df_engineered.columns:
            df_engineered['cpu_memory_interaction'] = df_engineered['cpu_usage'] * df_engineered['memory_usage']
            # Use numpy.divide to handle division by zero safely
            df_engineered['cpu_memory_ratio'] = np.divide(
                df_engineered['cpu_usage'], 
                df_engineered['memory_usage'] + 1e-8,
                out=np.zeros_like(df_engineered['cpu_usage']),
                where=(df_engineered['memory_usage'] + 1e-8) != 0
            )
        
        # 3. Statistical features
        numeric_cols = df_engineered.select_dtypes(include=[np.number]).columns
        numeric_cols = [col for col in numeric_cols if col != 'is_anomaly']
        
        # Percentile features
        for col in numeric_cols[:5]:  # Limit to avoid too many features
            if col in df_engineered.columns:
                df_engineered[f'{col}_percentile'] = df_engineered[col].rank(pct=True)
        
        # 4. Anomaly score features (unsupervised)
        if len(numeric_cols) >= 3:
            isolation_forest = IsolationForest(contamination=0.1, random_state=42)
            df_engineered['isolation_anomaly_score'] = isolation_forest.fit_predict(
                df_engineered[numeric_cols].fillna(0)
            )
        
        # 5. Binning features
        for col in ['cpu_usage', 'memory_usage']:
            if col in df_engineered.columns:
                df_engineered[f'{col}_binned'] = pd.cut(
                    df_engineered[col], 
                    bins=5, 
                    labels=['very_low', 'low', 'medium', 'high', 'very_high']
                )
                # One-hot encode
                binned_dummies = pd.get_dummies(df_engineered[f'{col}_binned'], prefix=f'{col}_bin')
                df_engineered = pd.concat([df_engineered, binned_dummies], axis=1)
                df_engineered.drop(f'{col}_binned', axis=1, inplace=True)
        
        # 6. Time-based features
        if 'timestamp' in df_engineered.columns:
            df_engineered['hour'] = df_engineered['timestamp'].dt.hour
            df_engineered['day_of_week'] = df_engineered['timestamp'].dt.dayofweek
            df_engineered['is_weekend'] = (df_engineered['day_of_week'] >= 5).astype(int)
            df_engineered['is_business_hours'] = (
                (df_engineered['hour'] >= 9) & (df_engineered['hour'] <= 17)
            ).astype(int)
        
        print(f"✅ Feature engineering complete: {len(df_engineered.columns)} features")
        return df_engineered
    
    def handle_class_imbalance(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Handle class imbalance using advanced techniques.
        """
        # Check current class distribution
        unique, counts = np.unique(y, return_counts=True)
        class_ratio = counts[0] / counts[1] if len(counts) > 1 else 1
        
        print(f"📊 Original class distribution: {dict(zip(unique, counts))}")
        print(f"📊 Class ratio (normal:anomaly): {class_ratio:.1f}:1")
        
        if class_ratio > 10:  # Severe imbalance
            print("⚖️ Applying SMOTE-Tomek for severe class imbalance...")
            smote_tomek = SMOTETomek(random_state=42)
            X_resampled, y_resampled = smote_tomek.fit_resample(X, y)
        elif class_ratio > 5:  # Moderate imbalance
            print("⚖️ Applying ADASYN for moderate class imbalance...")
            adasyn = ADASYN(random_state=42)
            X_resampled, y_resampled = adasyn.fit_resample(X, y)
        else:  # Mild imbalance
            print("⚖️ Applying SMOTE for mild class imbalance...")
            smote = SMOTE(random_state=42)
            X_resampled, y_resampled = smote.fit_resample(X, y)
        
        unique_new, counts_new = np.unique(y_resampled, return_counts=True)
        print(f"✅ Resampled class distribution: {dict(zip(unique_new, counts_new))}")
        
        return X_resampled, y_resampled
    
    def optimize_hyperparameters(self, model, param_grid: Dict, X_train: np.ndarray, 
                                y_train: np.ndarray, cv_folds: int = 5) -> object:
        """
        Optimize hyperparameters using GridSearchCV or RandomizedSearchCV.
        """
        print(f"🔍 Optimizing hyperparameters for {model.__class__.__name__}...")
        
        # Use RandomizedSearchCV for large parameter spaces
        if len(param_grid) > 50:
            search = RandomizedSearchCV(
                model, param_grid, cv=cv_folds, 
                scoring='f1', n_iter=20, random_state=42, n_jobs=-1
            )
        else:
            search = GridSearchCV(
                model, param_grid, cv=cv_folds, 
                scoring='f1', n_jobs=-1
            )
        
        search.fit(X_train, y_train)
        
        print(f"✅ Best parameters: {search.best_params_}")
        print(f"✅ Best CV F1-score: {search.best_score_:.4f}")
        
        return search.best_estimator_
    
    def train_ensemble_models(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict:
        """
        Train multiple state-of-the-art models with hyperparameter optimization.
        """
        print("🤖 Training ensemble of advanced ML models...")
        
        models_config = {
            'random_forest': {
                'model': RandomForestClassifier(random_state=42),
                'params': {
                    'n_estimators': [100, 200, 300],
                    'max_depth': [10, 20, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4],
                    'class_weight': ['balanced', 'balanced_subsample']
                }
            },
            'gradient_boosting': {
                'model': GradientBoostingClassifier(random_state=42),
                'params': {
                    'n_estimators': [100, 200],
                    'learning_rate': [0.05, 0.1, 0.2],
                    'max_depth': [3, 5, 7],
                    'subsample': [0.8, 1.0]
                }
            },
            'logistic_regression': {
                'model': LogisticRegression(random_state=42, max_iter=1000),
                'params': {
                    'C': [0.1, 1, 10, 100],
                    'penalty': ['l1', 'l2'],
                    'solver': ['liblinear', 'saga'],
                    'class_weight': ['balanced']
                }
            }
        }
        
        # Add XGBoost if available
        if XGB_AVAILABLE:
            models_config['xgboost'] = {
                'model': xgb.XGBClassifier(random_state=42, eval_metric='logloss'),
                'params': {
                    'n_estimators': [100, 200],
                    'learning_rate': [0.05, 0.1, 0.2],
                    'max_depth': [3, 5, 7],
                    'subsample': [0.8, 1.0],
                    'colsample_bytree': [0.8, 1.0]
                }
            }
        
        # Add LightGBM if available
        if LGB_AVAILABLE:
            models_config['lightgbm'] = {
                'model': lgb.LGBMClassifier(random_state=42, verbose=-1),
                'params': {
                    'n_estimators': [100, 200],
                    'learning_rate': [0.05, 0.1, 0.2],
                    'max_depth': [3, 5, 7],
                    'subsample': [0.8, 1.0],
                    'colsample_bytree': [0.8, 1.0]
                }
            }
        
        trained_models = {}
        
        for name, config in models_config.items():
            try:
                start_time = datetime.now()
                
                # Optimize hyperparameters
                optimized_model = self.optimize_hyperparameters(
                    config['model'], config['params'], X_train, y_train
                )
                
                training_time = (datetime.now() - start_time).total_seconds()
                trained_models[name] = {
                    'model': optimized_model,
                    'training_time': training_time
                }
                
                print(f"✅ {name} trained successfully in {training_time:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ Error training {name}: {e}")
                continue
        
        return trained_models
    
    def evaluate_model_comprehensive(self, model, X_test: np.ndarray, y_test: np.ndarray,
                                   model_name: str, X_train: np.ndarray, y_train: np.ndarray) -> ModelPerformance:
        """
        Comprehensive model evaluation with all metrics.
        """
        # Predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
        
        # Basic metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        # AUC-ROC
        auc_roc = roc_auc_score(y_test, y_pred_proba) if y_pred_proba is not None else 0.0
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        cm_dict = {
            'true_positives': int(cm[1, 1]) if cm.shape == (2, 2) else 0,
            'false_positives': int(cm[0, 1]) if cm.shape == (2, 2) else 0,
            'true_negatives': int(cm[0, 0]) if cm.shape == (2, 2) else 0,
            'false_negatives': int(cm[1, 0]) if cm.shape == (2, 2) else 0
        }
        
        # Cross-validation scores
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1')
        
        return ModelPerformance(
            model_name=model_name,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            auc_roc=auc_roc,
            confusion_matrix=cm_dict,
            cv_scores=cv_scores.tolist(),
            training_time=0.0  # Will be set by caller
        )
    
    def select_best_model(self, performances: List[ModelPerformance]) -> ModelPerformance:
        """
        Select the best model based on target metrics priority.
        """
        print("🏆 Selecting best model based on target performance...")
        
        # Calculate composite score based on target metrics
        best_score = -1
        best_performance = None
        
        for perf in performances:
            # Weighted composite score prioritizing F1, then accuracy, then precision
            composite_score = (
                perf.f1_score * 0.4 +
                perf.accuracy * 0.3 +
                perf.precision * 0.2 +
                perf.recall * 0.1
            )
            
            print(f"📊 {perf.model_name}:")
            print(f"   Accuracy: {perf.accuracy:.4f} (target: {self.target_performance['accuracy']:.4f})")
            print(f"   Precision: {perf.precision:.4f} (target: {self.target_performance['precision']:.4f})")
            print(f"   Recall: {perf.recall:.4f} (target: {self.target_performance['recall']:.4f})")
            print(f"   F1-Score: {perf.f1_score:.4f} (target: {self.target_performance['f1_score']:.4f})")
            print(f"   AUC-ROC: {perf.auc_roc:.4f}")
            print(f"   Composite Score: {composite_score:.4f}")
            print()
            
            if composite_score > best_score:
                best_score = composite_score
                best_performance = perf
        
        print(f"🥇 Best model: {best_performance.model_name}")
        return best_performance
    
    def train_advanced_model(self, data_path: str) -> Dict:
        """
        Complete advanced training pipeline.
        """
        print("🚀 Starting Advanced ML Training Pipeline")
        print("=" * 60)
        
        # 1. Load data
        df = self.load_data(data_path)
        
        # 2. Advanced feature engineering
        df_engineered = self.advanced_feature_engineering(df)
        
        # 3. Prepare features and target
        feature_cols = [col for col in df_engineered.columns 
                       if col not in ['is_anomaly', 'timestamp']]
        X = df_engineered[feature_cols].fillna(0)
        
        # Handle infinite values
        X = X.replace([np.inf, -np.inf], 0)
        
        # Ensure all values are finite
        X = X.select_dtypes(include=[np.number])
        
        y = df_engineered['is_anomaly']
        
        print(f"📊 Final feature set: {X.shape[1]} features")
        print(f"📊 Training samples: {len(X)}")
        
        # 4. Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # 5. Scale features
        self.scaler = RobustScaler()  # More robust to outliers
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 6. Handle class imbalance
        X_train_balanced, y_train_balanced = self.handle_class_imbalance(
            X_train_scaled, y_train
        )
        
        # 7. Feature selection
        print("🔍 Performing feature selection...")
        self.feature_selector = SelectKBest(f_classif, k=min(50, X_train_balanced.shape[1]))
        X_train_selected = self.feature_selector.fit_transform(X_train_balanced, y_train_balanced)
        X_test_selected = self.feature_selector.transform(X_test_scaled)
        
        selected_features = X.columns[self.feature_selector.get_support()].tolist()
        print(f"✅ Selected {len(selected_features)} most important features")
        
        # 8. Train ensemble models
        trained_models = self.train_ensemble_models(X_train_selected, y_train_balanced)
        
        # 9. Evaluate all models
        performances = []
        for name, model_info in trained_models.items():
            perf = self.evaluate_model_comprehensive(
                model_info['model'], X_test_selected, y_test, name,
                X_train_selected, y_train_balanced
            )
            perf.training_time = model_info['training_time']
            performances.append(perf)
            self.performance_results.append(perf)
        
        # 10. Select best model
        best_performance = self.select_best_model(performances)
        self.best_model = trained_models[best_performance.model_name]['model']
        
        # 11. Generate final report
        return self.generate_training_report(best_performance, selected_features)
    
    def generate_training_report(self, best_performance: ModelPerformance, 
                               selected_features: List[str]) -> Dict:
        """
        Generate comprehensive training report.
        """
        report = {
            'model_type': 'advanced_ensemble',
            'version': '3.0.0',
            'training_timestamp': datetime.now().isoformat(),
            'created_by': 'advanced_ml_trainer',
            'description': 'Advanced ML model with feature engineering and optimization',
            
            'best_model': {
                'name': best_performance.model_name,
                'training_time': best_performance.training_time
            },
            
            'performance': {
                'accuracy': best_performance.accuracy,
                'precision': best_performance.precision,
                'recall': best_performance.recall,
                'f1_score': best_performance.f1_score,
                'auc_roc': best_performance.auc_roc,
                'confusion_matrix': best_performance.confusion_matrix,
                'cv_scores': best_performance.cv_scores,
                'cv_mean': np.mean(best_performance.cv_scores),
                'cv_std': np.std(best_performance.cv_scores)
            },
            
            'target_achievement': {
                'accuracy_achieved': best_performance.accuracy >= self.target_performance['accuracy'],
                'precision_achieved': best_performance.precision >= self.target_performance['precision'],
                'recall_achieved': best_performance.recall >= self.target_performance['recall'],
                'f1_achieved': best_performance.f1_score >= self.target_performance['f1_score'],
                'auc_achieved': best_performance.auc_roc >= self.target_performance['auc_roc']
            },
            
            'features': {
                'total_engineered': len(selected_features),
                'selected_features': selected_features[:20],  # Top 20
                'feature_engineering': [
                    'rolling_statistics',
                    'interaction_features',
                    'statistical_features',
                    'anomaly_scores',
                    'binning_features',
                    'time_features'
                ]
            },
            
            'techniques_used': [
                'advanced_feature_engineering',
                'class_imbalance_handling',
                'hyperparameter_optimization',
                'cross_validation',
                'ensemble_methods',
                'feature_selection'
            ],
            
            'model_metadata': {
                'preprocessing': 'RobustScaler + SelectKBest',
                'class_balancing': 'SMOTE/ADASYN/SMOTETomek',
                'hyperparameter_tuning': 'GridSearchCV/RandomizedSearchCV',
                'cross_validation_folds': 5,
                'feature_selection_method': 'SelectKBest with f_classif'
            }
        }
        
        print("\n" + "=" * 60)
        print("🏆 TRAINING COMPLETE - PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"🥇 Best Model: {best_performance.model_name}")
        print(f"📊 Accuracy: {best_performance.accuracy:.4f} (target: {self.target_performance['accuracy']:.4f}) {'✅' if report['target_achievement']['accuracy_achieved'] else '❌'}")
        print(f"📊 Precision: {best_performance.precision:.4f} (target: {self.target_performance['precision']:.4f}) {'✅' if report['target_achievement']['precision_achieved'] else '❌'}")
        print(f"📊 Recall: {best_performance.recall:.4f} (target: {self.target_performance['recall']:.4f}) {'✅' if report['target_achievement']['recall_achieved'] else '❌'}")
        print(f"📊 F1-Score: {best_performance.f1_score:.4f} (target: {self.target_performance['f1_score']:.4f}) {'✅' if report['target_achievement']['f1_achieved'] else '❌'}")
        print(f"📊 AUC-ROC: {best_performance.auc_roc:.4f} (target: {self.target_performance['auc_roc']:.4f}) {'✅' if report['target_achievement']['auc_achieved'] else '❌'}")
        print("=" * 60)
        
        return report
    
    def save_model(self, output_path: str, report: Dict):
        """
        Save the trained model and report.
        """
        try:
            # Save model artifacts
            model_artifacts = {
                'model': self.best_model,
                'scaler': self.scaler,
                'feature_selector': self.feature_selector,
                'report': report
            }
            
            # Save as pickle
            model_path = output_path.replace('.json', '_model.pkl')
            joblib.dump(model_artifacts, model_path)
            
            # Save report as JSON
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            print(f"✅ Model saved to: {model_path}")
            print(f"✅ Report saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"❌ Error saving model: {e}")

def main():
    """
    Main training function.
    """
    print("🚀 SmartCloudOps AI - Advanced ML Training Pipeline")
    print("Target: 95%+ Accuracy, 85%+ Precision, 90%+ Recall, 87%+ F1-Score")
    print("=" * 80)
    
    # Initialize trainer with target performance
    target_performance = {
        'accuracy': 0.95,
        'precision': 0.85,
        'recall': 0.90,
        'f1_score': 0.87,
        'auc_roc': 0.92
    }
    
    trainer = AdvancedMLTrainer(target_performance)
    
    # Train model
    data_path = '/home/dileep-reddy/smartcloudops-ai/data/real_training_data.csv'
    report = trainer.train_advanced_model(data_path)
    
    # Save model and report
    output_path = '/home/dileep-reddy/smartcloudops-ai/ml_models/advanced_model.json'
    trainer.save_model(output_path, report)
    
    print("\n🎉 Advanced ML Training Complete!")
    print("📊 Check the performance summary above for detailed results.")

if __name__ == "__main__":
    main()
