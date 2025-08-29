#!/usr/bin/env python3
"""
SmartCloudOps AI - ML Service
============================

Production-ready machine learning service for anomaly detection and predictive analytics.
"""


import logging
import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                             recall_score)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler, StandardScaler

logger = logging.getLogger(__name__)


class MLModelManager:
    """Manages ML model lifecycle, versioning, and deployment."""

    def __init__(self, model_dir: str = "/app/ml_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.current_model = None
        self.current_scaler = None
        self.model_metadata = {}
        self.model_version = None
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
                self.model_version = model_data.get("version", "1.0")
            else:
                # Legacy format - assume it's just the model
                self.current_model = model_data
                self.current_scaler = None
                self.model_version = "1.0"

            logger.info(f"✅ Model loaded successfully: {model_path.name}")

        except Exception as e:
            logger.error(f"❌ Failed to load model from {model_path}: {e}")
            raise

    def save_model(
        self, model: Any, scaler: Optional[Any] = None, metadata: Optional[Dict] = None
    ) -> str:
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
                "version": self.model_version or "1.0",
            }

            with open(model_path, "wb") as f:
                pickle.dump(model_data, f)

            # Update current model
            self.current_model = model
            self.current_scaler = scaler
            self.model_metadata = metadata or {}

            logger.info(f"✅ Model saved: {model_path}")
            return str(model_path)

        except Exception as e:
            logger.error(f"❌ Failed to save model: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information."""
        return {
            "version": self.model_version,
            "metadata": self.model_metadata,
            "model_type": (
                type(self.current_model).__name__ if self.current_model else None
            ),
            "scaler_type": (
                type(self.current_scaler).__name__ if self.current_scaler else None
            ),
            "created_at": self.model_metadata.get("created_at"),
            "performance": self.model_metadata.get("performance", {}),
        }

    def health_check(self) -> Dict[str, Any]:
        """Check model health."""
        return {
            "status": "healthy" if self.current_model else "unhealthy",
            "model_loaded": self.current_model is not None,
            "model_type": (
                type(self.current_model).__name__ if self.current_model else None
            ),
            "version": self.model_version,
            "last_updated": self.model_metadata.get("created_at"),
        }


class MLService:
    """Production-ready ML service for anomaly detection."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.model_manager = MLModelManager()
        self.feature_columns = [
            "cpu_usage",
            "memory_usage",
            "disk_usage",
            "network_io",
            "response_time",
            "error_rate",
            "request_count",
        ]
        self.anomaly_threshold = -0.5

    def _generate_training_data(self, num_samples: int = 1000) -> pd.DataFrame:
        """Generate realistic training data for anomaly detection."""
        np.random.seed(42)

        # Normal operation data (80% of samples)
        normal_samples = int(num_samples * 0.8)
        normal_data = {
            "cpu_usage": np.random.normal(30, 10, normal_samples),
            "memory_usage": np.random.normal(50, 15, normal_samples),
            "disk_usage": np.random.normal(60, 20, normal_samples),
            "network_io": np.random.normal(100, 30, normal_samples),
            "response_time": np.random.normal(200, 50, normal_samples),
            "error_rate": np.random.normal(2, 1, normal_samples),
            "request_count": np.random.normal(1000, 200, normal_samples),
        }

        # Anomaly data (20% of samples)
        anomaly_samples = num_samples - normal_samples
        anomaly_data = {
            "cpu_usage": np.random.normal(85, 10, anomaly_samples),
            "memory_usage": np.random.normal(90, 5, anomaly_samples),
            "disk_usage": np.random.normal(95, 3, anomaly_samples),
            "network_io": np.random.normal(500, 100, anomaly_samples),
            "response_time": np.random.normal(1000, 200, anomaly_samples),
            "error_rate": np.random.normal(15, 5, anomaly_samples),
            "request_count": np.random.normal(5000, 1000, anomaly_samples),
        }

        # Combine and create labels
        normal_df = pd.DataFrame(normal_data)
        normal_df["is_anomaly"] = 0

        anomaly_df = pd.DataFrame(anomaly_data)
        anomaly_df["is_anomaly"] = 1

        combined_df = pd.concat([normal_df, anomaly_df], ignore_index=True)
        combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)

        return combined_df

    def train_model(self, data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Train a new anomaly detection model."""
        try:
            # Use provided data or generate training data
            if data is None:
                data = self._generate_training_data(2000)

            # Prepare features and labels
            X = data[self.feature_columns]
            y = data["is_anomaly"] if "is_anomaly" in data.columns else None

            # Split data for validation
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            # Create and train model pipeline
            scaler = RobustScaler()
            model = IsolationForest(
                contamination=0.1, random_state=42, n_estimators=100, max_samples="auto"
            )

            # Fit scaler and model
            X_train_scaled = scaler.fit_transform(X_train)
            model.fit(X_train_scaled)

            # Evaluate model
            X_test_scaled = scaler.transform(X_test)
            predictions = model.predict(X_test_scaled)
            scores = model.decision_function(X_test_scaled)

            # Convert isolation forest predictions to binary (1 = anomaly, -1 = normal)
            binary_predictions = (predictions == -1).astype(int)

            # Calculate metrics
            performance_metrics = {
                "accuracy": accuracy_score(y_test, binary_predictions),
                "precision": precision_score(
                    y_test, binary_predictions, zero_division=0
                ),
                "recall": recall_score(y_test, binary_predictions, zero_division=0),
                "f1_score": f1_score(y_test, binary_predictions, zero_division=0),
            }

            # Cross-validation
            cv_scores = cross_val_score(
                model, X_train_scaled, y_train, cv=5, scoring="f1"
            )
            performance_metrics["cv_f1_mean"] = cv_scores.mean()
            performance_metrics["cv_f1_std"] = cv_scores.std()

            # Save model
            metadata = {
                "created_at": datetime.now().isoformat(),
                "performance": performance_metrics,
                "feature_columns": self.feature_columns,
                "training_samples": len(data),
                "anomaly_threshold": self.anomaly_threshold,
            }

            model_path = self.model_manager.save_model(model, scaler, metadata)

            logger.info(
                f"✅ Model trained successfully. F1 Score: {performance_metrics['f1_score']:.3f}"
            )

            return {
                "model_path": model_path,
                "performance": performance_metrics,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"❌ Model training failed: {e}")
            raise

    def predict_anomaly(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Predict anomaly for given metrics."""
        try:
            if not self.model_manager.current_model:
                raise ValueError("No model loaded. Please train a model first.")

            # Extract features
            features = []
            for col in self.feature_columns:
                value = metrics.get(col, 0.0)
                features.append(float(value))

            features_array = np.array(features).reshape(1, -1)

            # Scale features
            if self.model_manager.current_scaler:
                features_scaled = self.model_manager.current_scaler.transform(
                    features_array
                )
            else:
                features_scaled = features_array

            # Make prediction
            anomaly_score = self.model_manager.current_model.decision_function(
                features_scaled
            )[0]
            is_anomaly = anomaly_score < self.anomaly_threshold

            # Calculate confidence based on distance from threshold
            confidence = min(1.0, abs(anomaly_score - self.anomaly_threshold) / 2.0)

            return {
                "anomaly_score": float(anomaly_score),
                "is_anomaly": bool(is_anomaly),
                "confidence": float(confidence),
                "model_version": self.model_manager.model_version,
                "features_used": self.feature_columns,
                "threshold": self.anomaly_threshold,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Prediction failed: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return self.model_manager.get_model_info()

    def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        return self.model_manager.health_check()

    def retrain_model(self, new_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Retrain model with new data."""
        logger.info("🔄 Starting model retraining...")
        return self.train_model(new_data)


# Global ML service instance
ml_service = MLService()
