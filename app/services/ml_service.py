#!/usr/bin/env python3
"""
SmartCloudOps AI - ML Service
============================

Production-ready machine learning service for anomaly detection and predictive analytics.
"""

import json
import logging
import os
import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, precision_score, recall_score

from app.config import config_manager

logger = logging.getLogger(__name__)


class MLModelManager:
    """Manages ML model lifecycle, versioning, and deployment."""

    def __init__(self, model_dir: str = "/app/ml_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.current_model = None
        self.current_scaler = None
        self.model_metadata = {}
        self._load_latest_model()

    def _load_latest_model(self) -> bool:
        """Load the most recent model from disk."""
        try:
            model_files = list(self.model_dir.glob("*.pkl"))
            if not model_files:
                logger.warning("No model files found in model directory")
                return False

            # Get the most recent model file
            latest_model = max(model_files, key=lambda x: x.stat().st_mtime)
            self._load_model(latest_model)
            logger.info(f"✅ Loaded model: {latest_model.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            return False

    def _load_model(self, model_path: Path) -> None:
        """Load model and scaler from file."""
        try:
            with open(model_path, "rb") as f:
                model_data = pickle.load(f)

            if isinstance(model_data, dict):
                self.current_model = model_data.get("model")
                self.current_scaler = model_data.get("scaler")
                self.model_metadata = model_data.get("metadata", {})
            else:
                # Legacy format - assume it's just the model
                self.current_model = model_data
                self.current_scaler = None

            logger.info(f"✅ Model loaded successfully: {model_path.name}")

        except Exception as e:
            logger.error(f"❌ Failed to load model from {model_path}: {e}")
            raise

    def save_model(self, model: Any, scaler: Optional[Any] = None, 
                   metadata: Optional[Dict] = None) -> str:
        """Save model with metadata."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_filename = f"anomaly_model_{timestamp}.pkl"
            model_path = self.model_dir / model_filename

            model_data = {
                "model": model,
                "scaler": scaler,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }

            with open(model_path, "wb") as f:
                pickle.dump(model_data, f)

            # Update current model
            self.current_model = model
            self.current_scaler = scaler
            self.model_metadata = metadata or {}

            logger.info(f"✅ Model saved: {model_filename}")
            return str(model_path)

        except Exception as e:
            logger.error(f"❌ Failed to save model: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        if not self.current_model:
            return {"status": "no_model_loaded"}

        return {
            "status": "loaded",
            "model_type": type(self.current_model).__name__,
            "has_scaler": self.current_scaler is not None,
            "metadata": self.model_metadata,
            "model_dir": str(self.model_dir)
        }

    def is_model_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self.current_model is not None


class AnomalyDetector:
    """Anomaly detection service using machine learning."""

    def __init__(self, model_manager: MLModelManager):
        self.model_manager = model_manager
        self.confidence_threshold = float(
            config_manager.get_secret("ML_CONFIDENCE_THRESHOLD") or "0.7"
        )
        self.max_prediction_time = int(
            config_manager.get_secret("ML_MAX_PREDICTION_TIME") or "30"
        )

    def detect_anomaly(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Detect anomalies in system metrics.
        
        Args:
            metrics: Dictionary of system metrics (cpu_usage, memory_usage, etc.)
            
        Returns:
            Dictionary with anomaly detection results
        """
        if not self.model_manager.is_model_loaded():
            return {
                "error": "No model loaded",
                "anomaly_score": None,
                "is_anomaly": False,
                "confidence": 0.0
            }

        try:
            start_time = time.time()

            # Prepare features
            features = self._prepare_features(metrics)
            if features is None:
                return {
                    "error": "Invalid metrics format",
                    "anomaly_score": None,
                    "is_anomaly": False,
                    "confidence": 0.0
                }

            # Make prediction
            anomaly_score = self._predict_anomaly(features)
            
            # Calculate confidence and determine if anomaly
            confidence = self._calculate_confidence(anomaly_score)
            is_anomaly = confidence > self.confidence_threshold

            prediction_time = time.time() - start_time

            return {
                "anomaly_score": float(anomaly_score),
                "is_anomaly": bool(is_anomaly),
                "confidence": float(confidence),
                "prediction_time": float(prediction_time),
                "threshold": float(self.confidence_threshold),
                "features_used": list(features.keys()),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Anomaly detection failed: {e}")
            return {
                "error": str(e),
                "anomaly_score": None,
                "is_anomaly": False,
                "confidence": 0.0
            }

    def _prepare_features(self, metrics: Dict[str, float]) -> Optional[Dict[str, float]]:
        """Prepare features for anomaly detection."""
        try:
            # Required features for anomaly detection
            required_features = [
                "cpu_usage", "memory_usage", "disk_usage", 
                "network_in", "network_out", "response_time"
            ]

            # Create feature vector with defaults for missing values
            features = {}
            for feature in required_features:
                features[feature] = metrics.get(feature, 0.0)

            # Add derived features
            features["cpu_memory_ratio"] = (
                features["cpu_usage"] / (features["memory_usage"] + 1e-6)
            )
            features["disk_cpu_ratio"] = (
                features["disk_usage"] / (features["cpu_usage"] + 1e-6)
            )
            features["network_total"] = features["network_in"] + features["network_out"]

            # Validate features
            for key, value in features.items():
                if not isinstance(value, (int, float)) or np.isnan(value) or np.isinf(value):
                    features[key] = 0.0

            return features

        except Exception as e:
            logger.error(f"❌ Feature preparation failed: {e}")
            return None

    def _predict_anomaly(self, features: Dict[str, float]) -> float:
        """Make anomaly prediction using the loaded model."""
        try:
            # Convert features to numpy array
            feature_values = np.array(list(features.values())).reshape(1, -1)

            # Scale features if scaler is available
            if self.model_manager.current_scaler:
                feature_values = self.model_manager.current_scaler.transform(feature_values)

            # Make prediction
            if hasattr(self.model_manager.current_model, 'predict'):
                # For models that return -1 (anomaly) or 1 (normal)
                prediction = self.model_manager.current_model.predict(feature_values)[0]
                # Convert to anomaly score (0 = normal, 1 = anomaly)
                anomaly_score = 1.0 if prediction == -1 else 0.0
            elif hasattr(self.model_manager.current_model, 'score_samples'):
                # For models that return anomaly scores
                scores = self.model_manager.current_model.score_samples(feature_values)
                # Normalize scores to 0-1 range
                anomaly_score = 1.0 - (scores[0] + 0.5)  # Assuming scores are roughly -0.5 to 0.5
                anomaly_score = max(0.0, min(1.0, anomaly_score))
            else:
                # Fallback
                anomaly_score = 0.5

            return float(anomaly_score)

        except Exception as e:
            logger.error(f"❌ Prediction failed: {e}")
            return 0.5  # Neutral score on error

    def _calculate_confidence(self, anomaly_score: float) -> float:
        """Calculate confidence in the anomaly prediction."""
        # Simple confidence calculation based on distance from decision boundary
        # Higher confidence when score is further from 0.5
        confidence = abs(anomaly_score - 0.5) * 2.0
        return min(1.0, max(0.0, confidence))


class ModelTrainer:
    """Train and evaluate anomaly detection models."""

    def __init__(self, model_manager: MLModelManager):
        self.model_manager = model_manager

    def train_model(self, training_data: List[Dict[str, float]], 
                   test_data: Optional[List[Dict[str, float]]] = None) -> Dict[str, Any]:
        """
        Train a new anomaly detection model.
        
        Args:
            training_data: List of metric dictionaries for training
            test_data: Optional test data for evaluation
            
        Returns:
            Training results and model performance metrics
        """
        try:
            logger.info(f"🚀 Starting model training with {len(training_data)} samples")

            # Prepare training features
            X_train, y_train = self._prepare_training_data(training_data)
            
            # Prepare test features if provided
            X_test, y_test = None, None
            if test_data:
                X_test, y_test = self._prepare_training_data(test_data)

            # Train model
            model, scaler, training_metrics = self._train_isolation_forest(
                X_train, y_train, X_test, y_test
            )

            # Save model
            model_path = self.model_manager.save_model(
                model, scaler, training_metrics
            )

            logger.info(f"✅ Model training completed: {model_path}")
            
            return {
                "status": "success",
                "model_path": model_path,
                "training_metrics": training_metrics,
                "model_info": self.model_manager.get_model_info()
            }

        except Exception as e:
            logger.error(f"❌ Model training failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _prepare_training_data(self, data: List[Dict[str, float]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from raw metrics."""
        try:
            features = []
            labels = []

            for sample in data:
                # Extract features
                feature_vector = [
                    sample.get("cpu_usage", 0.0),
                    sample.get("memory_usage", 0.0),
                    sample.get("disk_usage", 0.0),
                    sample.get("network_in", 0.0),
                    sample.get("network_out", 0.0),
                    sample.get("response_time", 0.0),
                    sample.get("cpu_usage", 0.0) / (sample.get("memory_usage", 0.0) + 1e-6),
                    sample.get("disk_usage", 0.0) / (sample.get("cpu_usage", 0.0) + 1e-6),
                    sample.get("network_in", 0.0) + sample.get("network_out", 0.0)
                ]

                # Extract label (1 for normal, -1 for anomaly)
                label = sample.get("is_anomaly", False)
                label = -1 if label else 1

                features.append(feature_vector)
                labels.append(label)

            return np.array(features), np.array(labels)

        except Exception as e:
            logger.error(f"❌ Training data preparation failed: {e}")
            raise

    def _train_isolation_forest(self, X_train: np.ndarray, y_train: np.ndarray,
                               X_test: Optional[np.ndarray] = None,
                               y_test: Optional[np.ndarray] = None) -> Tuple[Any, Any, Dict]:
        """Train Isolation Forest model."""
        try:
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)

            # Train model
            model = IsolationForest(
                contamination=0.1,  # Expected proportion of anomalies
                n_estimators=100,
                max_samples='auto',
                random_state=42
            )
            
            model.fit(X_train_scaled)

            # Evaluate model
            training_metrics = self._evaluate_model(
                model, scaler, X_train, y_train, X_test, y_test
            )

            return model, scaler, training_metrics

        except Exception as e:
            logger.error(f"❌ Model training failed: {e}")
            raise

    def _evaluate_model(self, model: Any, scaler: Any, 
                       X_train: np.ndarray, y_train: np.ndarray,
                       X_test: Optional[np.ndarray] = None,
                       y_test: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Evaluate model performance."""
        try:
            metrics = {}

            # Training metrics
            X_train_scaled = scaler.transform(X_train)
            y_train_pred = model.predict(X_train_scaled)
            
            # Convert predictions to binary (1 for normal, 0 for anomaly)
            y_train_binary = (y_train == 1).astype(int)
            y_train_pred_binary = (y_train_pred == 1).astype(int)

            metrics["train_f1"] = f1_score(y_train_binary, y_train_pred_binary, average='weighted')
            metrics["train_precision"] = precision_score(y_train_binary, y_train_pred_binary, average='weighted')
            metrics["train_recall"] = recall_score(y_train_binary, y_train_pred_binary, average='weighted')

            # Test metrics if available
            if X_test is not None and y_test is not None:
                X_test_scaled = scaler.transform(X_test)
                y_test_pred = model.predict(X_test_scaled)
                
                y_test_binary = (y_test == 1).astype(int)
                y_test_pred_binary = (y_test_pred == 1).astype(int)

                metrics["test_f1"] = f1_score(y_test_binary, y_test_pred_binary, average='weighted')
                metrics["test_precision"] = precision_score(y_test_binary, y_test_pred_binary, average='weighted')
                metrics["test_recall"] = recall_score(y_test_binary, y_test_pred_binary, average='weighted')

            # Model info
            metrics["model_type"] = "IsolationForest"
            metrics["n_features"] = X_train.shape[1]
            metrics["n_samples"] = X_train.shape[0]
            metrics["contamination"] = model.contamination
            metrics["n_estimators"] = model.n_estimators

            return metrics

        except Exception as e:
            logger.error(f"❌ Model evaluation failed: {e}")
            return {"error": str(e)}


class MLService:
    """Main ML service interface."""

    def __init__(self):
        self.model_manager = MLModelManager()
        self.anomaly_detector = AnomalyDetector(self.model_manager)
        self.model_trainer = ModelTrainer(self.model_manager)

    def predict_anomaly(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Predict anomalies in system metrics."""
        return self.anomaly_detector.detect_anomaly(metrics)

    def train_model(self, training_data: List[Dict[str, float]], 
                   test_data: Optional[List[Dict[str, float]]] = None) -> Dict[str, Any]:
        """Train a new anomaly detection model."""
        return self.model_trainer.train_model(training_data, test_data)

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return self.model_manager.get_model_info()

    def get_model_accuracy(self) -> Dict[str, Any]:
        """Get model accuracy metrics."""
        info = self.model_manager.get_model_info()
        if info.get("status") != "loaded":
            return {"error": "No model loaded"}
        
        return {
            "f1_score": info.get("metadata", {}).get("test_f1", 0.0),
            "precision": info.get("metadata", {}).get("test_precision", 0.0),
            "recall": info.get("metadata", {}).get("test_recall", 0.0),
            "model_type": info.get("model_type", "unknown"),
            "last_updated": info.get("metadata", {}).get("created_at", "unknown")
        }

    def health_check(self) -> Dict[str, Any]:
        """Health check for the ML service."""
        try:
            model_info = self.model_manager.get_model_info()
            
            return {
                "status": "healthy" if model_info.get("status") == "loaded" else "degraded",
                "model_loaded": self.model_manager.is_model_loaded(),
                "model_info": model_info,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ ML service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global ML service instance
ml_service = MLService()
