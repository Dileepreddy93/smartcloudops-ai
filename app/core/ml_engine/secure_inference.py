#!/usr/bin/env python3
"""
SmartCloudOps AI - Secure ML Inference Engine
============================================

Production-ready ML inference engine with proper security and validation.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd

from utils.response import build_error_response, build_success_response
from utils.validation import validate_ml_metrics

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class SecureMLInferenceEngine:
    """Secure ML inference engine for anomaly detection."""

    def __init__(self, model_path: Optional[str] = None):
        """Initialize the ML inference engine."""
        self.logger = logging.getLogger(__name__)
        self.model_path = model_path or os.getenv("ML_MODEL_PATH", "./ml_models")
        self.model = None
        self.model_metadata = {}
        self.feature_names = []
        self.is_initialized = False

        # Initialize the engine
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initialize the ML inference engine."""
        try:
            # Create model directory if it doesn't exist
            Path(self.model_path).mkdir(parents=True, exist_ok=True)

            # Try to load existing model
            if self._load_model():
                self.logger.info("Loaded existing ML model")
            else:
                # Train a new model if none exists
                self.logger.info("No existing model found, training new model")
                self._train_model()

            self.is_initialized = True
            self.logger.info("ML inference engine initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize ML inference engine: {e}")
            raise

    def _load_model(self) -> bool:
        """Load existing ML model."""
        try:
            model_file = Path(self.model_path) / "anomaly_detection_model.pkl"
            metadata_file = Path(self.model_path) / "model_metadata.json"

            if model_file.exists() and metadata_file.exists():
                # Load model
                self.model = joblib.load(model_file)

                # Load metadata
                with open(metadata_file, "r") as f:
                    self.model_metadata = json.load(f)

                # Set feature names
                self.feature_names = self.model_metadata.get("feature_names", [])

                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False

    def _train_model(self) -> None:
        """Train a new anomaly detection model."""
        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.preprocessing import StandardScaler

            # Generate synthetic training data
            training_data = self._generate_training_data()

            # Prepare features
            X = training_data[self.feature_names].values

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Train isolation forest model
            self.model = IsolationForest(
                contamination=0.1, random_state=42, n_estimators=100
            )
            self.model.fit(X_scaled)

            # Save model
            self._save_model(scaler)

            self.logger.info("New ML model trained and saved successfully")

        except Exception as e:
            self.logger.error(f"Failed to train model: {e}")
            raise

    def _generate_training_data(self) -> pd.DataFrame:
        """Generate synthetic training data for model training."""
        np.random.seed(42)

        # Define feature names
        self.feature_names = [
            "cpu_usage",
            "memory_usage",
            "disk_usage",
            "network_io",
            "load_1m",
            "load_5m",
            "load_15m",
            "response_time",
        ]

        # Generate normal data
        n_samples = 1000

        data = {
            "cpu_usage": np.random.normal(50, 15, n_samples),
            "memory_usage": np.random.normal(60, 20, n_samples),
            "disk_usage": np.random.normal(40, 10, n_samples),
            "network_io": np.random.normal(30, 8, n_samples),
            "load_1m": np.random.normal(1.5, 0.5, n_samples),
            "load_5m": np.random.normal(1.4, 0.4, n_samples),
            "load_15m": np.random.normal(1.3, 0.3, n_samples),
            "response_time": np.random.normal(200, 50, n_samples),
        }

        # Add some anomalies
        anomaly_indices = np.random.choice(n_samples, size=50, replace=False)
        for idx in anomaly_indices:
            data["cpu_usage"][idx] = np.random.uniform(90, 100)
            data["memory_usage"][idx] = np.random.uniform(85, 95)
            data["response_time"][idx] = np.random.uniform(800, 1200)

        return pd.DataFrame(data)

    def _save_model(self, scaler) -> None:
        """Save the trained model and metadata."""
        try:
            # Save model
            model_file = Path(self.model_path) / "anomaly_detection_model.pkl"
            joblib.dump(self.model, model_file)

            # Save scaler
            scaler_file = Path(self.model_path) / "feature_scaler.pkl"
            joblib.dump(scaler, scaler_file)

            # Save metadata
            metadata = {
                "model_type": "IsolationForest",
                "feature_names": self.feature_names,
                "training_date": datetime.now(timezone.utc).isoformat(),
                "model_version": "1.0.0",
                "contamination": 0.1,
                "n_estimators": 100,
            }

            metadata_file = Path(self.model_path) / "model_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            self.model_metadata = metadata

        except Exception as e:
            self.logger.error(f"Failed to save model: {e}")
            raise

    def predict(self, metrics: Dict[str, Union[int, float]]) -> Dict[str, Any]:
        """Make anomaly detection prediction."""
        try:
            if not self.is_initialized:
                raise RuntimeError("ML inference engine not initialized")

            # Validate input metrics
            validated_metrics = validate_ml_metrics(metrics)

            # Prepare features
            features = []
            for feature_name in self.feature_names:
                if feature_name in validated_metrics:
                    features.append(validated_metrics[feature_name])
                else:
                    # Use default value if feature is missing
                    features.append(0.0)

            # Convert to numpy array
            X = np.array(features).reshape(1, -1)

            # Load scaler
            scaler_file = Path(self.model_path) / "feature_scaler.pkl"
            if scaler_file.exists():
                scaler = joblib.load(scaler_file)
                X_scaled = scaler.transform(X)
            else:
                X_scaled = X

            # Make prediction
            prediction = self.model.predict(X_scaled)[0]
            anomaly_score = self.model.score_samples(X_scaled)[0]

            # Determine if anomaly
            is_anomaly = prediction == -1

            # Calculate confidence
            confidence = self._calculate_confidence(anomaly_score)

            # Prepare response
            result = {
                "is_anomaly": bool(is_anomaly),
                "anomaly_score": float(anomaly_score),
                "confidence": float(confidence),
                "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
                "model_version": self.model_metadata.get("model_version", "1.0.0"),
                "features_used": self.feature_names,
                "input_metrics": validated_metrics,
            }

            # Log prediction
            self.logger.info(
                f"ML prediction: anomaly={is_anomaly}, score={anomaly_score:.4f}, confidence={confidence:.2f}"
            )

            return result

        except Exception as e:
            self.logger.error(f"Prediction failed: {e}")
            raise

    def _calculate_confidence(self, anomaly_score: float) -> float:
        """Calculate confidence score based on anomaly score."""
        # Convert anomaly score to confidence (0-1)
        # Lower anomaly scores indicate higher confidence in anomaly detection
        confidence = 1.0 - (anomaly_score + 0.5)  # Normalize to 0-1 range
        return max(0.0, min(1.0, confidence))

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        if not self.is_initialized:
            return {"error": "ML inference engine not initialized"}

        return {
            "model_type": self.model_metadata.get("model_type", "Unknown"),
            "model_version": self.model_metadata.get("model_version", "1.0.0"),
            "training_date": self.model_metadata.get("training_date", "Unknown"),
            "feature_names": self.feature_names,
            "is_initialized": self.is_initialized,
            "model_path": self.model_path,
        }

    def retrain_model(self) -> Dict[str, Any]:
        """Retrain the ML model with new data."""
        try:
            self.logger.info("Starting model retraining...")

            # Train new model
            self._train_model()

            return {
                "status": "success",
                "message": "Model retrained successfully",
                "model_version": self.model_metadata.get("model_version", "1.0.0"),
                "training_date": self.model_metadata.get("training_date", "Unknown"),
            }

        except Exception as e:
            self.logger.error(f"Model retraining failed: {e}")
            return {"status": "error", "message": f"Model retraining failed: {str(e)}"}

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the ML inference engine."""
        try:
            # Check if model is loaded
            model_loaded = self.model is not None

            # Check if model files exist
            model_file = Path(self.model_path) / "anomaly_detection_model.pkl"
            metadata_file = Path(self.model_path) / "model_metadata.json"

            files_exist = model_file.exists() and metadata_file.exists()

            # Test prediction with dummy data
            test_metrics = {
                "cpu_usage": 50.0,
                "memory_usage": 60.0,
                "disk_usage": 40.0,
                "network_io": 30.0,
                "load_1m": 1.5,
                "load_5m": 1.4,
                "load_15m": 1.3,
                "response_time": 200.0,
            }

            try:
                test_prediction = self.predict(test_metrics)
                prediction_working = True
            except Exception:
                prediction_working = False

            return {
                "status": (
                    "healthy"
                    if all([model_loaded, files_exist, prediction_working])
                    else "unhealthy"
                ),
                "model_loaded": model_loaded,
                "files_exist": files_exist,
                "prediction_working": prediction_working,
                "is_initialized": self.is_initialized,
                "model_path": self.model_path,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
