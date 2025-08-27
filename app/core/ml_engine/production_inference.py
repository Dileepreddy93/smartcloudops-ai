#!/usr/bin/env python3
"""
SmartCloudOps AI - Production ML Inference Service
=================================================

Production-ready inference service for anomaly detection models.
Integrates with Flask app for real-time predictions.
"""

import logging
import os
import threading
import time
from collections import deque
from datetime import datetime
from typing import Dict, Optional, Tuple

import boto3
import joblib
import numpy as np
import pandas as pd
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionModelRegistry:
    """Production model registry with S3 backend."""

    def __init__(self, s3_bucket: str):
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client("s3")

    def get_latest_model_version(self) -> str:
        """Get the latest model version from S3 across known prefixes."""
        try:
            prefixes = ["models/optimized/", "models/"]
            candidates = []
            for prefix in prefixes:
                try:
                    response = self.s3_client.list_objects_v2(
                        Bucket=self.s3_bucket, Prefix=prefix
                    )
                    if "Contents" in response:
                        for obj in response["Contents"]:
                            if obj["Key"].endswith("_model.pkl"):
                                candidates.append(obj)
                except Exception as inner_e:
                    logger.warning(f"Failed listing S3 prefix {prefix}: {inner_e}")

            if candidates:
                latest = max(candidates, key=lambda x: x["LastModified"])
                return latest["Key"]

            # default to anomaly model naming
            return "models/anomaly_model.pkl"

        except Exception as e:
            logger.error(f"Error getting latest model: {e}")
            return "models/anomaly_model.pkl"

    def load_model_from_s3(
        self, model_key: str, scaler_key: str
    ) -> Tuple[object, object]:
        """Load model and scaler from S3."""
        try:
            # Download model
            model_path = f"/tmp/model_{int(time.time())}.pkl"
            self.s3_client.download_file(self.s3_bucket, model_key, model_path)
            model = joblib.load(model_path)
            os.remove(model_path)

            # Download scaler
            scaler_path = f"/tmp/scaler_{int(time.time())}.pkl"
            self.s3_client.download_file(self.s3_bucket, scaler_key, scaler_path)
            scaler = joblib.load(scaler_path)
            os.remove(scaler_path)

            logger.info(f"✅ Loaded model from S3: {model_key}")
            return model, scaler

        except Exception as e:
            logger.error(f"❌ Error loading model from S3: {e}")
            return None, None


class ModelPerformanceMonitor:
    """Monitor model performance and detect drift."""

    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.predictions: deque = deque(maxlen=window_size)
        self.features: deque = deque(maxlen=window_size)
        self.prediction_times: deque = deque(maxlen=window_size)
        self.lock = threading.Lock()

    def track_prediction(
        self, features: Dict, prediction: int, confidence: float, prediction_time: float
    ):
        """Track a prediction for monitoring."""
        with self.lock:
            self.predictions.append(
                {
                    "prediction": prediction,
                    "confidence": confidence,
                    "timestamp": datetime.now(),
                }
            )
            self.features.append(features)
            self.prediction_times.append(prediction_time)

    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics."""
        with self.lock:
            if not self.predictions:
                return {"status": "no_data"}

            recent_predictions = list(self.predictions)[-100:]  # Last 100 predictions
            recent_times = list(self.prediction_times)[-100:]

            anomaly_rate = sum(
                1 for p in recent_predictions if p["prediction"] == 1
            ) / len(recent_predictions)
            avg_confidence = np.mean([p["confidence"] for p in recent_predictions])
            avg_prediction_time = np.mean(recent_times) if recent_times else 0

            return {
                "anomaly_rate": anomaly_rate,
                "avg_confidence": avg_confidence,
                "avg_prediction_time_ms": avg_prediction_time * 1000,
                "total_predictions": len(self.predictions),
                "last_prediction": recent_predictions[-1]["timestamp"].isoformat(),
            }


class ProductionInferenceEngine:
    """Production-ready anomaly detection inference engine."""

    def __init__(
        self,
        s3_bucket: str = None,
        prometheus_url: str = "http://3.89.229.102:9090",
        model_cache_ttl: int = 3600,  # 1 hour
        use_real_data: bool = True,
    ):
        # Allow overriding via environment variable
        env_bucket = os.getenv("S3_ML_MODELS_BUCKET")
        self.s3_bucket = env_bucket or s3_bucket or os.getenv("ML_MODELS_BUCKET")
        # Allow overriding Prometheus endpoint via environment
        env_prom = os.getenv("PROMETHEUS_URL")
        self.prometheus_url = env_prom or prometheus_url
        self.model_cache_ttl = model_cache_ttl
        self.use_real_data = use_real_data

        # Initialize components
        self.model_registry = ProductionModelRegistry(s3_bucket)
        self.monitor = ModelPerformanceMonitor()

        # Real data collector for live features
        if self.use_real_data:
            try:
                from prometheus_collector import PrometheusCollector

                self.prometheus_collector = PrometheusCollector(prometheus_url)
                logger.info("✅ Real data collector initialized")
            except Exception as e:
                logger.warning(f"⚠️ Real data collector unavailable: {e}")
                self.prometheus_collector = None
        else:
            self.prometheus_collector = None

        # Model cache
        self.model = None
        self.scaler = None
        self.model_loaded_at = None
        self.feature_columns = None

        # Load models on initialization
        self._load_models()

    def _load_models(self):
        """Load models with fallback to local storage."""
        try:
            # Try loading from S3 first if bucket is configured
            if self.model_registry.s3_bucket:
                model_key = self.model_registry.get_latest_model_version()
                scaler_key = model_key.replace("_model.pkl", "_scaler.pkl")
                model, scaler = self.model_registry.load_model_from_s3(
                    model_key, scaler_key
                )
                if model and scaler:
                    self.model = model
                    self.scaler = scaler
                    self.model_loaded_at = datetime.now()
                    logger.info("✅ Models loaded from S3")
                    return
        except Exception as e:
            logger.warning(f"⚠️ S3 model loading failed: {e}")

        # Fallback to local models
        try:
            # Try multiple local paths
            candidate_local_paths = [
                ("../ml_models/anomaly_model.pkl", "../ml_models/anomaly_scaler.pkl"),
                (
                    "../ml_models/optimized/anomaly_model.pkl",
                    "../ml_models/optimized/anomaly_scaler.pkl",
                ),
                (
                    "../ml_models/isolation_forest_model.pkl",
                    "../ml_models/isolation_forest_scaler.pkl",
                ),
                (
                    "/opt/smartcloudops-ai/ml_models/optimized/anomaly_model.pkl",
                    "/opt/smartcloudops-ai/ml_models/optimized/anomaly_scaler.pkl",
                ),
            ]

            loaded = False
            for model_path, scaler_path in candidate_local_paths:
                if os.path.exists(model_path) and os.path.exists(scaler_path):
                    self.model = joblib.load(model_path)
                    self.scaler = joblib.load(scaler_path)
                    self.model_loaded_at = datetime.now()
                    logger.info(f"✅ Models loaded from local storage: {model_path}")
                    loaded = True
                    break

            if not loaded:
                logger.error("❌ No models found locally or in S3")

        except Exception as e:
            logger.error(f"❌ Error loading local models: {e}")

    def _should_reload_model(self) -> bool:
        """Check if model should be reloaded."""
        if not self.model_loaded_at:
            return True

        return (datetime.now() - self.model_loaded_at).seconds > self.model_cache_ttl

    def health_check(self) -> Dict:
        """Comprehensive health check."""
        health = {
            "status": "healthy",
            "model_loaded": self.model is not None,
            "scaler_loaded": self.scaler is not None,
            "model_age_seconds": 0,
            "prometheus_connection": False,
            "performance_metrics": {},
        }

        if self.model_loaded_at:
            health["model_age_seconds"] = (
                datetime.now() - self.model_loaded_at
            ).seconds

        # Test Prometheus connection
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/status/config", timeout=5
            )
            health["prometheus_connection"] = response.status_code == 200
        except Exception:
            pass

        # Get performance metrics
        health["performance_metrics"] = self.monitor.get_performance_metrics()

        # Overall health status
        if not self.model or not self.scaler:
            health["status"] = "unhealthy"
        elif health["model_age_seconds"] > self.model_cache_ttl:
            health["status"] = "stale"

        return health

    def collect_current_metrics(self) -> Dict:
        """Collect current system metrics from real data sources."""
        metrics = {}

        # Try real data sources first
        if self.use_real_data and self.prometheus_collector:
            try:
                real_metrics = self.prometheus_collector.collect_current_metrics()
                if real_metrics:
                    metrics.update(real_metrics)
                    logger.info("✅ Collected real-time metrics from Prometheus")
                    return metrics
            except Exception as e:
                logger.warning(f"⚠️ Failed to collect real metrics: {e}")

        # Fallback to API queries
        try:
            queries = {
                "cpu_usage": 'avg(100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100))',
                "memory_usage": "avg((1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100)",
                "disk_io": "avg(irate(node_disk_io_time_seconds_total[5m]) * 100)",
                "network_io": "avg(irate(node_network_receive_bytes_total[5m]) + irate(node_network_transmit_bytes_total[5m]))",
                "response_time": 'avg(prometheus_http_request_duration_seconds{handler="/api/v1/query"})',
            }

            for metric_name, query in queries.items():
                try:
                    response = requests.get(
                        f"{self.prometheus_url}/api/v1/query",
                        params={"query": query},
                        timeout=5,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if data["status"] == "success" and data["data"]["result"]:
                            value = float(data["data"]["result"][0]["value"][1])
                            metrics[metric_name] = value
                        else:
                            metrics[metric_name] = 0.0
                    else:
                        metrics[metric_name] = 0.0

                except Exception as e:
                    logger.warning(f"⚠️ Failed to collect {metric_name}: {e}")
                    metrics[metric_name] = 0.0

            return metrics

        except Exception as e:
            logger.error(f"❌ Error collecting metrics: {e}")
            return {
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "disk_io": 0.0,
                "network_io": 0.0,
                "response_time": 0.0,
            }

    def predict_anomaly(self, metrics: Optional[Dict] = None) -> Dict:
        """Predict if current or provided metrics indicate an anomaly."""
        start_time = time.time()

        try:
            # Reload model if needed
            if self._should_reload_model():
                logger.info("🔄 Reloading models...")
                self._load_models()

            if not self.model or not self.scaler:
                return {
                    "error": "Models not available",
                    "anomaly": False,
                    "confidence": 0.0,
                }

            # Collect metrics if not provided
            if metrics is None:
                metrics = self.collect_current_metrics()

            # Ensure required base metrics exist before feature engineering
            base_metrics = [
                "cpu_usage",
                "memory_usage",
                "disk_io",
                "network_io",
                "response_time",
            ]
            for base in base_metrics:
                if base not in metrics or metrics[base] is None:
                    metrics[base] = 0.0

            # Create DataFrame with basic features
            df = pd.DataFrame([metrics])

            # Add time-based features
            now = datetime.now()
            df["hour"] = now.hour
            df["day_of_week"] = now.weekday()
            df["is_weekend"] = int(now.weekday() >= 5)
            df["is_business_hours"] = int(9 <= now.hour <= 17 and now.weekday() < 5)

            # Add basic derived features
            df["cpu_memory_ratio"] = df["cpu_usage"] / (df["memory_usage"] + 1e-6)
            df["io_ratio"] = df["disk_io"] / (df["network_io"] + 1e-6)
            df["load_indicator"] = (df["cpu_usage"] + df["memory_usage"]) / 2
            df["performance_indicator"] = df["response_time"] / (
                df["load_indicator"] + 1e-6
            )

            # Fill any missing columns with zeros (for production robustness)
            expected_features = [
                "cpu_usage",
                "memory_usage",
                "disk_io",
                "network_io",
                "response_time",
                "hour",
                "day_of_week",
                "is_weekend",
                "is_business_hours",
                "cpu_memory_ratio",
                "io_ratio",
                "load_indicator",
                "performance_indicator",
            ]

            for feature in expected_features:
                if feature not in df.columns:
                    df[feature] = 0.0

            # Select features and scale
            X = df[expected_features].fillna(0)
            X_scaled = self.scaler.transform(X)

            # Make prediction
            prediction = self.model.predict(X_scaled)[0]
            decision_score = self.model.decision_function(X_scaled)[0]

            # Convert to boolean and confidence
            is_anomaly = prediction == -1
            confidence = abs(decision_score)

            prediction_time = time.time() - start_time

            # Track prediction for monitoring
            self.monitor.track_prediction(
                features=metrics,
                prediction=int(is_anomaly),
                confidence=confidence,
                prediction_time=prediction_time,
            )

            result = {
                "anomaly": is_anomaly,
                "confidence": confidence,
                "decision_score": decision_score,
                "metrics": metrics,
                "prediction_time_ms": prediction_time * 1000,
                "timestamp": datetime.now().isoformat(),
                "model_age_seconds": (
                    (datetime.now() - self.model_loaded_at).seconds
                    if self.model_loaded_at
                    else 0
                ),
            }

            logger.info(
                f"🔍 Prediction: {'🚨 ANOMALY' if is_anomaly else '✅ NORMAL'} (confidence: {confidence:.3f})"
            )
            return result

        except Exception as e:
            logger.error(f"❌ Prediction error: {e}")
            return {
                "error": str(e),
                "anomaly": False,
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat(),
            }


# Global inference engine instance
inference_engine = None


def get_inference_engine() -> ProductionInferenceEngine:
    """Get or create the global inference engine."""
    global inference_engine
    if inference_engine is None:
        inference_engine = ProductionInferenceEngine()
    return inference_engine


def initialize_models():
    """Initialize models on application startup."""
    logger.info("🚀 Initializing ML models...")
    get_inference_engine()
    logger.info("✅ ML models initialized")


if __name__ == "__main__":
    # Test the inference engine
    engine = ProductionInferenceEngine()

    print("🔍 Testing Production Inference Engine")
    print("=" * 50)

    # Health check
    health = engine.health_check()
    print(f"Health Status: {health['status']}")
    print(f"Model Loaded: {health['model_loaded']}")

    if health["model_loaded"]:
        # Test prediction
        result = engine.predict_anomaly()
        print(f"Test Prediction: {'🚨 ANOMALY' if result['anomaly'] else '✅ NORMAL'}")
        print(f"Confidence: {result.get('confidence', 0):.3f}")
        print(f"Prediction Time: {result.get('prediction_time_ms', 0):.2f}ms")
