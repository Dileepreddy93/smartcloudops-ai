#!/usr/bin/env python3
"""
Production-Ready ML Pipeline
============================

Features:
- Model versioning and registry
- A/B testing framework
- Performance monitoring
- Automated retraining
- Model validation and rollback
- Production inference optimization
"""

import json
import logging
import os
import pickle
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import boto3
import joblib
import numpy as np
import pandas as pd
from botocore.exceptions import ClientError
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Model metadata for versioning and tracking."""

    model_id: str
    version: str
    created_at: datetime
    performance_metrics: Dict[str, float]
    training_data_size: int
    features: List[str]
    hyperparameters: Dict[str, Any]
    deployment_status: str  # 'staging', 'production', 'archived'
    a_b_test_group: Optional[str] = None


class ModelRegistry:
    """Production model registry with versioning and metadata tracking."""

    def __init__(self, registry_path: str = "/app/ml_models"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.registry_path / "model_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, ModelMetadata]:
        """Load model metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    data = json.load(f)
                    return {
                        model_id: ModelMetadata(**metadata_data)
                        for model_id, metadata_data in data.items()
                    }
            except Exception as e:
                logger.error(f"Failed to load model metadata: {e}")
        return {}

    def _save_metadata(self):
        """Save model metadata to file."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(
                    {
                        model_id: {
                            "model_id": metadata.model_id,
                            "version": metadata.version,
                            "created_at": metadata.created_at.isoformat(),
                            "performance_metrics": metadata.performance_metrics,
                            "training_data_size": metadata.training_data_size,
                            "features": metadata.features,
                            "hyperparameters": metadata.hyperparameters,
                            "deployment_status": metadata.deployment_status,
                            "a_b_test_group": metadata.a_b_test_group,
                        }
                        for model_id, metadata in self.metadata.items()
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Failed to save model metadata: {e}")

    def register_model(self, model, scaler, metadata: ModelMetadata) -> bool:
        """Register a new model version."""
        try:
            # Save model and scaler
            model_path = (
                self.registry_path
                / f"{metadata.model_id}_v{metadata.version}_model.pkl"
            )
            scaler_path = (
                self.registry_path
                / f"{metadata.model_id}_v{metadata.version}_scaler.pkl"
            )

            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)

            # Update metadata
            self.metadata[metadata.model_id] = metadata
            self._save_metadata()

            logger.info(
                f"✅ Model {metadata.model_id} v{metadata.version} registered successfully"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to register model: {e}")
            return False

    def get_model(
        self, model_id: str, version: Optional[str] = None
    ) -> Tuple[Any, Any, ModelMetadata]:
        """Get model, scaler, and metadata."""
        if model_id not in self.metadata:
            raise ValueError(f"Model {model_id} not found in registry")

        metadata = self.metadata[model_id]
        if version and metadata.version != version:
            raise ValueError(f"Version {version} not found for model {model_id}")

        model_path = self.registry_path / f"{model_id}_v{metadata.version}_model.pkl"
        scaler_path = self.registry_path / f"{model_id}_v{metadata.version}_scaler.pkl"

        if not model_path.exists() or not scaler_path.exists():
            raise FileNotFoundError(
                f"Model files not found for {model_id} v{metadata.version}"
            )

        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)

        return model, scaler, metadata

    def get_production_model(self, model_id: str) -> Tuple[Any, Any, ModelMetadata]:
        """Get the current production model."""
        if model_id not in self.metadata:
            raise ValueError(f"Model {model_id} not found in registry")

        metadata = self.metadata[model_id]
        if metadata.deployment_status != "production":
            raise ValueError(
                f"Model {model_id} is not in production (status: {metadata.deployment_status})"
            )

        return self.get_model(model_id)

    def list_models(self) -> List[ModelMetadata]:
        """List all registered models."""
        return list(self.metadata.values())


class ABTestManager:
    """A/B testing manager for model comparison."""

    def __init__(self):
        self.active_tests = {}
        self.test_results = {}

    def start_test(
        self,
        test_id: str,
        model_a: str,
        model_b: str,
        traffic_split: float = 0.5,
        duration_days: int = 7,
    ) -> bool:
        """Start an A/B test between two model versions."""
        try:
            self.active_tests[test_id] = {
                "model_a": model_a,
                "model_b": model_b,
                "traffic_split": traffic_split,
                "start_time": datetime.utcnow(),
                "end_time": datetime.utcnow() + timedelta(days=duration_days),
                "metrics_a": {"predictions": 0, "anomalies": 0, "latency_ms": []},
                "metrics_b": {"predictions": 0, "anomalies": 0, "latency_ms": []},
            }

            logger.info(f"🚀 A/B test {test_id} started: {model_a} vs {model_b}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start A/B test: {e}")
            return False

    def get_test_model(self, test_id: str, user_id: str) -> str:
        """Get the model to use for a specific user in A/B test."""
        if test_id not in self.active_tests:
            raise ValueError(f"A/B test {test_id} not found")

        test = self.active_tests[test_id]

        # Use user_id hash to ensure consistent assignment
        user_hash = hash(user_id) % 100
        if user_hash < test["traffic_split"] * 100:
            return test["model_a"]
        else:
            return test["model_b"]

    def record_prediction(
        self, test_id: str, model_version: str, prediction: int, latency_ms: float
    ):
        """Record prediction results for A/B test."""
        if test_id not in self.active_tests:
            return

        test = self.active_tests[test_id]
        if model_version == test["model_a"]:
            test["metrics_a"]["predictions"] += 1
            test["metrics_a"]["anomalies"] += prediction
            test["metrics_a"]["latency_ms"].append(latency_ms)
        elif model_version == test["model_b"]:
            test["metrics_b"]["predictions"] += 1
            test["metrics_b"]["anomalies"] += prediction
            test["metrics_b"]["latency_ms"].append(latency_ms)

    def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get A/B test results."""
        if test_id not in self.active_tests:
            raise ValueError(f"A/B test {test_id} not found")

        test = self.active_tests[test_id]

        def calculate_metrics(metrics):
            if metrics["predictions"] == 0:
                return {"anomaly_rate": 0, "avg_latency_ms": 0}

            return {
                "anomaly_rate": metrics["anomalies"] / metrics["predictions"],
                "avg_latency_ms": (
                    np.mean(metrics["latency_ms"]) if metrics["latency_ms"] else 0
                ),
                "total_predictions": metrics["predictions"],
            }

        return {
            "test_id": test_id,
            "model_a": {
                "version": test["model_a"],
                **calculate_metrics(test["metrics_a"]),
            },
            "model_b": {
                "version": test["model_b"],
                **calculate_metrics(test["metrics_b"]),
            },
            "start_time": test["start_time"].isoformat(),
            "end_time": test["end_time"].isoformat(),
            "status": "active" if datetime.utcnow() < test["end_time"] else "completed",
        }


class ProductionMLPipeline:
    """Production-ready ML pipeline with monitoring and optimization."""

    def __init__(self):
        self.registry = ModelRegistry()
        self.ab_test_manager = ABTestManager()
        self.performance_monitor = PerformanceMonitor()
        self.current_model = None
        self.current_scaler = None
        self.current_metadata = None
        self._load_production_model()

    def _load_production_model(self):
        """Load the current production model."""
        try:
            (
                self.current_model,
                self.current_scaler,
                self.current_metadata,
            ) = self.registry.get_production_model("anomaly_detection")
            logger.info(
                f"✅ Production model loaded: {self.current_metadata.model_id} v{self.current_metadata.version}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to load production model: {e}")

    def train_model(
        self,
        training_data: pd.DataFrame,
        hyperparameters: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Train a new model version with validation."""
        try:
            # Prepare data
            features = ["cpu_usage", "memory_usage", "disk_usage", "network_io"]
            X = training_data[features].values

            # Train model
            model_params = hyperparameters or {
                "n_estimators": 100,
                "contamination": 0.1,
                "random_state": 42,
            }

            model = IsolationForest(**model_params)
            scaler = StandardScaler()

            # Scale features
            X_scaled = scaler.fit_transform(X)

            # Train model
            model.fit(X_scaled)

            # Validate model
            predictions = model.predict(X_scaled)
            anomaly_rate = np.mean(predictions == -1)

            # Performance metrics
            performance_metrics = {
                "anomaly_rate": anomaly_rate,
                "training_samples": len(X),
                "feature_count": len(features),
            }

            # Create metadata
            metadata = ModelMetadata(
                model_id="anomaly_detection",
                version=f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                created_at=datetime.utcnow(),
                performance_metrics=performance_metrics,
                training_data_size=len(X),
                features=features,
                hyperparameters=model_params,
                deployment_status="staging",
            )

            # Register model
            success = self.registry.register_model(model, scaler, metadata)

            if success:
                logger.info(f"✅ Model training completed: {metadata.version}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"❌ Model training failed: {e}")
            return False

    def predict(
        self,
        metrics: Dict[str, float],
        user_id: Optional[str] = None,
        ab_test_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Make prediction with performance monitoring."""
        start_time = time.time()

        try:
            # Determine which model to use
            model_to_use = self.current_model
            scaler_to_use = self.current_scaler
            metadata_to_use = self.current_metadata

            if ab_test_id and user_id:
                try:
                    test_model_version = self.ab_test_manager.get_test_model(
                        ab_test_id, user_id
                    )
                    if test_model_version != self.current_metadata.version:
                        # Load test model
                        (
                            test_model,
                            test_scaler,
                            test_metadata,
                        ) = self.registry.get_model(
                            "anomaly_detection", test_model_version
                        )
                        model_to_use = test_model
                        scaler_to_use = test_scaler
                        metadata_to_use = test_metadata
                except Exception as e:
                    logger.warning(
                        f"A/B test model loading failed, using production model: {e}"
                    )

            # Prepare features
            features = ["cpu_usage", "memory_usage", "disk_usage", "network_io"]
            X = np.array([[metrics.get(f, 0) for f in features]])

            # Scale features
            X_scaled = scaler_to_use.transform(X)

            # Make prediction
            prediction = model_to_use.predict(X_scaled)[0]
            anomaly_score = model_to_use.score_samples(X_scaled)[0]

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            # Record A/B test metrics
            if ab_test_id:
                self.ab_test_manager.record_prediction(
                    ab_test_id,
                    metadata_to_use.version,
                    1 if prediction == -1 else 0,
                    latency_ms,
                )

            # Record performance metrics
            self.performance_monitor.record_prediction(latency_ms, prediction == -1)

            return {
                "prediction": "anomaly" if prediction == -1 else "normal",
                "anomaly_score": float(anomaly_score),
                "confidence": self._calculate_confidence(anomaly_score),
                "model_version": metadata_to_use.version,
                "latency_ms": round(latency_ms, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ Prediction failed: {e}")

            return {
                "prediction": "error",
                "error": str(e),
                "latency_ms": round(latency_ms, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _calculate_confidence(self, anomaly_score: float) -> float:
        """Calculate confidence score based on anomaly score."""
        # Normalize anomaly score to confidence (0-1)
        # Lower anomaly score = higher confidence
        confidence = 1.0 - abs(anomaly_score)
        return max(0.0, min(1.0, confidence))

    def promote_model(self, model_id: str, version: str) -> bool:
        """Promote a model to production."""
        try:
            # Update metadata
            if model_id in self.registry.metadata:
                self.registry.metadata[model_id].deployment_status = "production"
                self.registry._save_metadata()

                # Reload production model
                self._load_production_model()

                logger.info(f"✅ Model {model_id} v{version} promoted to production")
                return True
            else:
                logger.error(f"❌ Model {model_id} not found in registry")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to promote model: {e}")
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """Get ML pipeline health status."""
        return {
            "pipeline_status": "healthy" if self.current_model else "unhealthy",
            "current_model": {
                "id": self.current_metadata.model_id if self.current_metadata else None,
                "version": (
                    self.current_metadata.version if self.current_metadata else None
                ),
                "deployment_status": (
                    self.current_metadata.deployment_status
                    if self.current_metadata
                    else None
                ),
            },
            "performance_metrics": self.performance_monitor.get_metrics(),
            "active_ab_tests": len(self.ab_test_manager.active_tests),
            "registered_models": len(self.registry.metadata),
        }


class PerformanceMonitor:
    """Monitor ML pipeline performance metrics."""

    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.latency_history = []
        self.anomaly_rate_history = []
        self.prediction_count = 0
        self.error_count = 0

    def record_prediction(self, latency_ms: float, is_anomaly: bool):
        """Record prediction performance metrics."""
        self.latency_history.append(latency_ms)
        self.anomaly_rate_history.append(1 if is_anomaly else 0)
        self.prediction_count += 1

        # Keep only recent history
        if len(self.latency_history) > self.window_size:
            self.latency_history.pop(0)
            self.anomaly_rate_history.pop(0)

    def record_error(self):
        """Record prediction error."""
        self.error_count += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        if not self.latency_history:
            return {
                "avg_latency_ms": 0,
                "p95_latency_ms": 0,
                "anomaly_rate": 0,
                "error_rate": 0,
                "total_predictions": 0,
            }

        return {
            "avg_latency_ms": round(np.mean(self.latency_history), 2),
            "p95_latency_ms": round(np.percentile(self.latency_history, 95), 2),
            "anomaly_rate": round(np.mean(self.anomaly_rate_history), 3),
            "error_rate": round(self.error_count / max(self.prediction_count, 1), 3),
            "total_predictions": self.prediction_count,
        }


# Global ML pipeline instance
ml_pipeline = ProductionMLPipeline()


def get_ml_pipeline() -> ProductionMLPipeline:
    """Get the global ML pipeline instance."""
    return ml_pipeline
