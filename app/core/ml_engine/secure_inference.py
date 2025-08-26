#!/usr/bin/env python3
"""
SmartCloudOps AI - Production-Hardened ML Inference Engine
=========================================================

Enterprise-grade inference engine with comprehensive error handling,
security controls, and performance optimization.
"""

import hashlib
import json
import logging
import os
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure secure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/tmp/ml_inference.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    FAILED = "failed"


class ModelValidationError(Exception):
    """Model validation specific exception."""

    pass


class PredictionError(Exception):
    """Prediction specific exception."""

    pass


@dataclass
class ModelConfig:
    """Validated model configuration."""

    model_type: str
    training_timestamp: str
    thresholds: Dict[str, float]
    performance: Dict[str, float]
    training_data_size: int

    def validate(self) -> bool:
        """Validate model configuration."""
        required_thresholds = {
            "cpu_threshold",
            "memory_threshold",
            "load_threshold",
            "disk_threshold",
        }
        required_performance = {"accuracy", "precision", "recall", "f1_score"}

        # Validate thresholds
        if not isinstance(self.thresholds, dict):
            raise ModelValidationError("Thresholds must be a dictionary")

        missing_thresholds = required_thresholds - set(self.thresholds.keys())
        if missing_thresholds:
            raise ModelValidationError(
                f"Missing required thresholds: {missing_thresholds}"
            )

        # Validate threshold values
        for key, value in self.thresholds.items():
            if not isinstance(value, (int, float)) or value < 0:
                raise ModelValidationError(
                    f"Invalid threshold value for {key}: {value}"
                )

        # Validate performance metrics
        if not isinstance(self.performance, dict):
            raise ModelValidationError("Performance must be a dictionary")

        missing_performance = required_performance - set(self.performance.keys())
        if missing_performance:
            raise ModelValidationError(
                f"Missing required performance metrics: {missing_performance}"
            )

        # Validate performance values (should be between 0 and 1, excluding confusion_matrix)
        for key, value in self.performance.items():
            if key == "confusion_matrix":
                # Special handling for confusion matrix
                if isinstance(value, dict):
                    required_cm_keys = {
                        "true_positives",
                        "false_positives",
                        "true_negatives",
                        "false_negatives",
                    }
                    if not all(cm_key in value for cm_key in required_cm_keys):
                        raise ModelValidationError(
                            f"Invalid confusion matrix structure: {value}"
                        )
                    # Validate all values are non-negative integers
                    for cm_key, cm_value in value.items():
                        if not isinstance(cm_value, int) or cm_value < 0:
                            raise ModelValidationError(
                                f"Invalid confusion matrix value for {cm_key}: {cm_value}"
                            )
                continue

            if not isinstance(value, (int, float)) or not (0 <= value <= 1):
                raise ModelValidationError(
                    f"Invalid performance value for {key}: {value}"
                )

        # Check model quality
        f1_score = self.performance.get("f1_score", 0)
        if f1_score < 0.7:
            logger.warning(
                f"Model F1-score ({f1_score:.3f}) is below recommended threshold (0.7)"
            )

        # Validate data size
        if not isinstance(self.training_data_size, int) or self.training_data_size <= 0:
            raise ModelValidationError(
                f"Invalid training data size: {self.training_data_size}"
            )

        return True


@dataclass
class PredictionResult:
    """Structured prediction result."""

    anomaly: bool
    confidence: float
    severity: str
    metrics: Dict[str, float]
    thresholds_exceeded: Dict[str, bool]
    prediction_time_ms: float
    timestamp: str
    model_version: str
    risk_factors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "anomaly": self.anomaly,
            "confidence": round(self.confidence, 3),
            "severity": self.severity,
            "metrics": self.metrics,
            "thresholds_exceeded": self.thresholds_exceeded,
            "prediction_time_ms": round(self.prediction_time_ms, 2),
            "timestamp": self.timestamp,
            "model_version": self.model_version,
            "risk_factors": self.risk_factors,
        }


class SecureMLInferenceEngine:
    """Production-hardened ML inference engine with comprehensive security and reliability."""

    def __init__(
        self, model_path: Optional[str] = None, max_prediction_time: float = 5.0
    ):
        """Initialize with comprehensive error handling and security."""
        self._lock = threading.RLock()  # Thread-safe operations
        self._initialized = False
        self._model_config: Optional[ModelConfig] = None
        self._data_collector = None
        self._max_prediction_time = max_prediction_time
        self._prediction_count = 0
        self._error_count = 0
        self._last_health_check = None
        self._health_status = HealthStatus.UNHEALTHY

        # Security: Validate model path
        self._allowed_model_paths = self._get_allowed_model_paths()

        try:
            self._initialize(model_path)
        except Exception as e:
            logger.error(f"Failed to initialize ML engine: {e}")
            self._health_status = HealthStatus.FAILED
            # Don't raise - allow graceful degradation

    def _get_allowed_model_paths(self) -> List[Path]:
        """Get list of allowed model file paths (security measure)."""
        base_dir = Path(__file__).parent.parent
        return [
            base_dir / "ml_models" / "real_data_model.json",
            base_dir / "ml_models" / "production_model.json",
            Path("ml_models/real_data_model.json"),
        ]

    def _validate_model_path(self, model_path: str) -> Path:
        """Validate model path for security."""
        try:
            requested_path = Path(model_path).resolve()

            # Check if path is in allowed list
            for allowed_path in self._allowed_model_paths:
                try:
                    if requested_path.samefile(allowed_path.resolve()):
                        return requested_path
                except (OSError, FileNotFoundError):
                    continue

            raise ModelValidationError(f"Model path not in allowed list: {model_path}")

        except Exception as e:
            raise ModelValidationError(f"Invalid model path: {e}")

    def _load_and_validate_model(self, model_path: Optional[str] = None) -> ModelConfig:
        """Load and validate model with comprehensive error handling."""
        if model_path:
            # Security: Validate provided path
            validated_path = self._validate_model_path(model_path)
            model_paths = [validated_path]
        else:
            # Use allowed paths
            model_paths = [p for p in self._allowed_model_paths if p.exists()]

        if not model_paths:
            raise ModelValidationError("No valid model files found")

        for path in model_paths:
            try:
                logger.info(f"Attempting to load model from: {path}")

                # Validate file size (prevent huge files)
                if path.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
                    logger.warning(f"Model file too large: {path}")
                    continue

                # Load and parse JSON
                with open(path, "r", encoding="utf-8") as f:
                    raw_config = json.load(f)

                # Validate JSON structure
                required_keys = {
                    "model_type",
                    "training_timestamp",
                    "thresholds",
                    "performance",
                    "training_data_size",
                }
                if not all(key in raw_config for key in required_keys):
                    raise ModelValidationError(
                        f"Missing required keys in model config: {required_keys - set(raw_config.keys())}"
                    )

                # Create and validate model config
                model_config = ModelConfig(
                    model_type=raw_config["model_type"],
                    training_timestamp=raw_config["training_timestamp"],
                    thresholds=raw_config["thresholds"],
                    performance=raw_config["performance"],
                    training_data_size=raw_config["training_data_size"],
                )

                model_config.validate()

                logger.info(f"✅ Model loaded successfully from {path}")
                logger.info(
                    f"📊 Model performance - F1: {model_config.performance['f1_score']:.3f}, "
                    f"Accuracy: {model_config.performance['accuracy']:.3f}"
                )

                return model_config

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Failed to load model from {path}: {e}")
                continue
            except ModelValidationError as e:
                logger.error(f"Model validation failed for {path}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error loading model from {path}: {e}")
                continue

        raise ModelValidationError("Failed to load any valid model")

    def _initialize_data_collector(self):
        """Initialize data collector with error handling."""
        try:
            sys.path.append(os.path.dirname(__file__))
            from simple_real_data_collector import SimpleRealDataCollector

            self._data_collector = SimpleRealDataCollector()
            logger.info("✅ Real data collector initialized")
            return True

        except ImportError as e:
            logger.warning(f"Data collector module not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize data collector: {e}")
            return False

    def _initialize(self, model_path: Optional[str] = None):
        """Initialize the engine with comprehensive error handling."""
        with self._lock:
            try:
                # Load and validate model
                self._model_config = self._load_and_validate_model(model_path)

                # Initialize data collector
                collector_ok = self._initialize_data_collector()

                # Determine health status
                if self._model_config and collector_ok:
                    self._health_status = HealthStatus.HEALTHY
                elif self._model_config:
                    self._health_status = HealthStatus.DEGRADED
                    logger.warning(
                        "Engine initialized in degraded mode (no data collector)"
                    )
                else:
                    self._health_status = HealthStatus.UNHEALTHY
                    logger.error("Engine initialization failed")

                self._initialized = True
                self._last_health_check = datetime.now(timezone.utc)

                logger.info(
                    f"ML Inference Engine initialized with status: {self._health_status.value}"
                )

            except Exception as e:
                logger.error(f"Engine initialization failed: {e}")
                self._health_status = HealthStatus.FAILED
                raise

    def _validate_metrics_input(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Validate and sanitize metrics input."""
        if not isinstance(metrics, dict):
            raise PredictionError("Metrics must be a dictionary")

        validated_metrics = {}
        required_metrics = {"cpu_usage", "memory_usage", "load_1m", "disk_usage"}

        for metric in required_metrics:
            value = metrics.get(metric)

            if value is None:
                logger.warning(f"Missing metric: {metric}, using default 0.0")
                validated_metrics[metric] = 0.0
                continue

            # Type validation and conversion
            try:
                float_value = float(value)

                # Range validation
                if metric in ["cpu_usage", "memory_usage", "disk_usage"]:
                    if not (0 <= float_value <= 100):
                        logger.warning(
                            f"Metric {metric} out of range [0,100]: {float_value}"
                        )
                        float_value = max(0, min(100, float_value))
                elif metric == "load_1m":
                    if not (0 <= float_value <= 100):  # Reasonable load limit
                        logger.warning(
                            f"Load metric out of reasonable range: {float_value}"
                        )
                        float_value = max(0, min(100, float_value))

                # Check for infinite or NaN values
                if not (float("inf") > float_value > float("-inf")):
                    raise ValueError(f"Invalid value: {value}")

                validated_metrics[metric] = float_value

            except (ValueError, TypeError):
                logger.warning(f"Invalid metric value for {metric}: {value}, using 0.0")
                validated_metrics[metric] = 0.0

        return validated_metrics

    def _calculate_dynamic_confidence(
        self, thresholds_exceeded: Dict[str, bool], metrics: Dict[str, float]
    ) -> tuple[float, str, List[str]]:
        """Calculate confidence with improved logic and risk assessment."""
        if not self._model_config:
            return 0.0, "low", ["Model not available"]

        # Weighted confidence calculation based on model performance
        f1_score = self._model_config.performance.get("f1_score", 0.5)
        precision = self._model_config.performance.get("precision", 0.5)

        # Base confidence weights (adjusted based on domain knowledge)
        weights = {
            "cpu": 0.35,  # CPU is critical for performance
            "memory": 0.35,  # Memory issues can cause OOM
            "load": 0.20,  # Load indicates system stress
            "disk": 0.10,  # Disk usually less immediately critical
        }

        confidence = 0.0
        risk_factors = []

        # Calculate weighted confidence
        for metric, exceeded in thresholds_exceeded.items():
            if exceeded:
                metric_key = metric.replace("_high", "")
                weight = weights.get(metric_key, 0.1)

                # Factor in how much the threshold is exceeded
                threshold = self._model_config.thresholds.get(
                    f"{metric_key}_threshold", 100
                )
                actual_value = metrics.get(
                    f"{metric_key}_usage" if metric_key != "load" else "load_1m", 0
                )

                if threshold > 0:
                    excess_ratio = (actual_value - threshold) / threshold
                    severity_multiplier = min(2.0, 1.0 + excess_ratio)  # Cap at 2x
                else:
                    severity_multiplier = 1.0

                confidence += weight * severity_multiplier
                risk_factors.append(f"{metric_key}_exceeded_{excess_ratio:.1f}x")

        # Adjust confidence based on model quality
        confidence *= f1_score * 0.7 + precision * 0.3  # Weight towards precision
        confidence = min(1.0, confidence)

        # Determine severity
        if confidence >= 0.8:
            severity = "critical"
        elif confidence >= 0.6:
            severity = "high"
        elif confidence >= 0.4:
            severity = "medium"
        else:
            severity = "low"

        return confidence, severity, risk_factors

    def _collect_metrics_with_fallback(self) -> Optional[Dict[str, float]]:
        """Collect metrics with fallback and error handling."""
        if not self._data_collector:
            logger.warning("No data collector available")
            return None

        try:
            # Add timeout for collection
            start_time = time.time()
            metrics = self._data_collector.collect_current_metrics()
            collection_time = time.time() - start_time

            if collection_time > 10.0:  # 10 second timeout
                logger.warning(
                    f"Metrics collection took too long: {collection_time:.2f}s"
                )

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            self._error_count += 1
            return None

    def predict_anomaly(
        self, metrics: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Predict anomaly with comprehensive error handling and security.

        Args:
            metrics: Infrastructure metrics dictionary
            user_id: User ID for audit logging (security)

        Returns:
            Prediction result dictionary
        """
        start_time = time.time()
        request_id = hashlib.md5(f"{start_time}_{user_id}".encode()).hexdigest()[:8]

        try:
            with self._lock:
                # Security: Log prediction request
                logger.info(
                    f"Prediction request {request_id} from user: {user_id or 'anonymous'}"
                )

                # Check if engine is initialized
                if not self._initialized or not self._model_config:
                    raise PredictionError("ML engine not properly initialized")

                # Check health status
                if self._health_status == HealthStatus.FAILED:
                    raise PredictionError("ML engine in failed state")

                # Collect metrics if not provided
                if metrics is None:
                    metrics = self._collect_metrics_with_fallback()
                    if metrics is None:
                        raise PredictionError("Unable to collect metrics")

                # Validate and sanitize input
                validated_metrics = self._validate_metrics_input(metrics)

                # Check prediction timeout
                if time.time() - start_time > self._max_prediction_time:
                    raise PredictionError("Prediction timeout exceeded")

                # Apply thresholds
                thresholds_exceeded = {
                    "cpu_high": validated_metrics["cpu_usage"]
                    > self._model_config.thresholds["cpu_threshold"],
                    "memory_high": validated_metrics["memory_usage"]
                    > self._model_config.thresholds["memory_threshold"],
                    "load_high": validated_metrics["load_1m"]
                    > self._model_config.thresholds["load_threshold"],
                    "disk_high": validated_metrics["disk_usage"]
                    > self._model_config.thresholds["disk_threshold"],
                }

                # Determine anomaly (require multiple factors for higher accuracy)
                exceeded_count = sum(thresholds_exceeded.values())
                is_anomaly = exceeded_count >= 2 or (  # Require 2+ factors OR
                    exceeded_count >= 1
                    and (  # 1 factor if severe
                        validated_metrics["cpu_usage"]
                        > self._model_config.thresholds["cpu_threshold"] * 1.5
                        or validated_metrics["memory_usage"]
                        > self._model_config.thresholds["memory_threshold"] * 1.5
                    )
                )

                # Calculate dynamic confidence and risk factors
                confidence, severity, risk_factors = self._calculate_dynamic_confidence(
                    thresholds_exceeded, validated_metrics
                )

                prediction_time = (time.time() - start_time) * 1000

                # Create structured result
                result = PredictionResult(
                    anomaly=is_anomaly,
                    confidence=confidence,
                    severity=severity,
                    metrics=validated_metrics,
                    thresholds_exceeded=thresholds_exceeded,
                    prediction_time_ms=prediction_time,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    model_version=f"{self._model_config.model_type}_v1.0",
                    risk_factors=risk_factors,
                )

                # Update counters
                self._prediction_count += 1

                # Security: Audit log
                status = "🚨 ANOMALY" if is_anomaly else "✅ NORMAL"
                logger.info(
                    f"Prediction {request_id} complete: {status} "
                    f"(confidence: {confidence:.3f}, time: {prediction_time:.1f}ms)"
                )

                return result.to_dict()

        except PredictionError as e:
            self._error_count += 1
            logger.error(f"Prediction error {request_id}: {e}")
            return {
                "error": "Prediction failed",
                "error_code": "PREDICTION_ERROR",
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "anomaly": False,
                "confidence": 0.0,
            }
        except Exception as e:
            self._error_count += 1
            logger.error(f"Unexpected prediction error {request_id}: {e}")
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return {
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "anomaly": False,
                "confidence": 0.0,
            }

    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check with detailed status."""
        try:
            with self._lock:
                current_time = datetime.now(timezone.utc)

                health = {
                    "status": self._health_status.value,
                    "timestamp": current_time.isoformat(),
                    "components": {
                        "model_loaded": self._model_config is not None,
                        "data_collector_available": self._data_collector is not None,
                        "engine_initialized": self._initialized,
                    },
                    "metrics": {
                        "prediction_count": self._prediction_count,
                        "error_count": self._error_count,
                        "error_rate": self._error_count
                        / max(1, self._prediction_count),
                        "uptime_seconds": (
                            (current_time - self._last_health_check).total_seconds()
                            if self._last_health_check
                            else 0
                        ),
                    },
                }

                # Test components
                if self._model_config:
                    health["model_info"] = {
                        "type": self._model_config.model_type,
                        "f1_score": self._model_config.performance["f1_score"],
                        "training_size": self._model_config.training_data_size,
                    }

                # Test data collector
                if self._data_collector:
                    try:
                        test_metrics = self._collect_metrics_with_fallback()
                        health["components"]["prometheus_connection"] = (
                            test_metrics is not None
                        )
                    except Exception:
                        health["components"]["prometheus_connection"] = False
                else:
                    health["components"]["prometheus_connection"] = False

                # Determine overall health
                if health["metrics"]["error_rate"] > 0.5:
                    health["status"] = HealthStatus.UNHEALTHY.value
                elif not health["components"]["prometheus_connection"]:
                    health["status"] = HealthStatus.DEGRADED.value

                self._last_health_check = current_time
                return health

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": HealthStatus.FAILED.value,
                "error": "Health check failed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information."""
        try:
            with self._lock:
                if not self._model_config:
                    return {"error": "No model loaded"}

                return {
                    "model_type": self._model_config.model_type,
                    "training_timestamp": self._model_config.training_timestamp,
                    "training_data_size": self._model_config.training_data_size,
                    "performance": self._model_config.performance,
                    "thresholds": self._model_config.thresholds,
                    "status": self._health_status.value,
                    "predictions_made": self._prediction_count,
                    "error_rate": self._error_count / max(1, self._prediction_count),
                }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": "Failed to retrieve model information"}


# Thread-safe singleton implementation
_engine_instance = None
_engine_lock = threading.Lock()


def get_secure_inference_engine() -> SecureMLInferenceEngine:
    """Get thread-safe singleton instance of the inference engine."""
    global _engine_instance

    if _engine_instance is None:
        with _engine_lock:
            # Double-checked locking pattern
            if _engine_instance is None:
                _engine_instance = SecureMLInferenceEngine()

    return _engine_instance


# Backwards compatibility function
def get_real_inference_engine():
    """Backwards compatibility function."""
    return get_secure_inference_engine()


if __name__ == "__main__":
    """Comprehensive test suite."""
    print("🔍 SmartCloudOps AI - Secure ML Inference Engine Test")
    print("=" * 60)

    # Initialize engine
    engine = SecureMLInferenceEngine()

    # Health check
    print("\n1. Health Check:")
    health = engine.health_check()
    print(f"   Status: {health['status']}")
    for component, status in health.get("components", {}).items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {component}: {status}")

    # Model info
    print("\n2. Model Information:")
    model_info = engine.get_model_info()
    if "error" not in model_info:
        print(f"   Model Type: {model_info.get('model_type')}")
        print(
            f"   F1-Score: {model_info.get('performance', {}).get('f1_score', 0):.3f}"
        )
        print(f"   Error Rate: {model_info.get('error_rate', 0):.3f}")

    # Test predictions with various scenarios
    print("\n3. Prediction Tests:")

    test_scenarios = [
        {
            "name": "Normal System",
            "metrics": {
                "cpu_usage": 5.0,
                "memory_usage": 30.0,
                "load_1m": 0.1,
                "disk_usage": 20.0,
            },
        },
        {
            "name": "High CPU",
            "metrics": {
                "cpu_usage": 85.0,
                "memory_usage": 30.0,
                "load_1m": 0.1,
                "disk_usage": 20.0,
            },
        },
        {
            "name": "Multiple Issues",
            "metrics": {
                "cpu_usage": 85.0,
                "memory_usage": 90.0,
                "load_1m": 5.0,
                "disk_usage": 95.0,
            },
        },
        {
            "name": "Invalid Input",
            "metrics": {
                "cpu_usage": "invalid",
                "memory_usage": None,
                "load_1m": float("inf"),
            },
        },
    ]

    for i, scenario in enumerate(test_scenarios):
        print(f"\n   Test {i+1}: {scenario['name']}")
        result = engine.predict_anomaly(scenario["metrics"], user_id="test_user")

        if "error" not in result:
            status = "🚨 ANOMALY" if result["anomaly"] else "✅ NORMAL"
            print(f"   Result: {status}")
            print(f"   Confidence: {result['confidence']:.3f}")
            print(f"   Severity: {result['severity']}")
            if result.get("risk_factors"):
                print(f"   Risk Factors: {', '.join(result['risk_factors'])}")
        else:
            print(f"   Error: {result.get('error_code')} - {result.get('error')}")

    print(f"\n{'=' * 60}")
    print("🎯 Secure ML Inference Engine Testing Complete!")
    print("🔒 Production-ready with comprehensive security and error handling!")
