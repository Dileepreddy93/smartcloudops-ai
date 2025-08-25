"""
Phase 3: ML Inference Tests
Tests for ML inference engine, model loading, and prediction functionality.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timezone
from app.core.ml_engine.secure_inference import (
    get_secure_inference_engine,
    SecureMLInferenceEngine,
    ModelConfig,
    PredictionResult,
    HealthStatus
)


class TestSecureMLInferenceEngine:
    """Test suite for SecureMLInferenceEngine."""

    @pytest.fixture
    def mock_model_config(self):
        """Create a mock model configuration."""
        return ModelConfig(
            model_type="isolation_forest",
            training_timestamp="2023-01-01T00:00:00Z",
            thresholds={
                "cpu_threshold": 80.0,
                "memory_threshold": 85.0,
                "load_threshold": 5.0,
                "disk_threshold": 90.0
            },
            performance={
                "accuracy": 0.95,
                "precision": 0.92,
                "recall": 0.88,
                "f1_score": 0.90,
                "confusion_matrix": {
                    "true_positives": 100,
                    "false_positives": 8,
                    "true_negatives": 900,
                    "false_negatives": 12
                }
            },
            training_data_size=1000
        )

    @pytest.fixture
    def mock_engine(self, mock_model_config):
        """Create a mock inference engine."""
        engine = SecureMLInferenceEngine()
        engine._model_config = mock_model_config
        engine._initialized = True
        engine._health_status = HealthStatus.HEALTHY
        engine._data_collector = Mock()  # Mock data collector to avoid degraded status
        engine._prediction_count = 0
        engine._error_count = 0
        engine._last_health_check = datetime.now(timezone.utc)
        return engine

    def test_engine_initialization(self):
        """Test engine initialization."""
        # Act
        engine = SecureMLInferenceEngine()
        
        # Assert
        assert hasattr(engine, '_lock')
        assert hasattr(engine, '_initialized')
        assert hasattr(engine, '_model_config')
        assert hasattr(engine, '_max_prediction_time')

    def test_health_check_healthy_status(self, mock_engine):
        """Test health check with healthy status."""
        # Act
        health = mock_engine.health_check()
        
        # Assert
        assert health["status"] == "healthy"
        assert health["components"]["model_loaded"] is True
        assert health["components"]["engine_initialized"] is True
        assert "metrics" in health
        assert "model_info" in health

    def test_health_check_unhealthy_status(self):
        """Test health check with unhealthy status."""
        # Arrange
        engine = SecureMLInferenceEngine()
        engine._health_status = HealthStatus.UNHEALTHY
        engine._data_collector = Mock()  # Mock data collector
        engine._prediction_count = 100
        engine._error_count = 60  # High error rate to trigger unhealthy status
        engine._last_health_check = datetime.now(timezone.utc)
        
        # Act
        health = engine.health_check()
        
        # Assert
        assert health["status"] == "unhealthy"

    def test_predict_anomaly_success(self, mock_engine):
        """Test successful anomaly prediction."""
        # Arrange
        test_metrics = {
            "cpu_usage": 50.0,
            "memory_usage": 60.0,
            "load_1m": 1.5,
            "disk_usage": 30.0
        }
        
        # Act
        result = mock_engine.predict_anomaly(metrics=test_metrics, user_id="test_user")
        
        # Assert
        assert "anomaly" in result
        assert "confidence" in result
        assert "severity" in result
        assert "metrics" in result
        assert "timestamp" in result
        assert "model_version" in result
        assert "risk_factors" in result

    def test_predict_anomaly_high_cpu(self, mock_engine):
        """Test anomaly prediction with high CPU usage."""
        # Arrange
        test_metrics = {
            "cpu_usage": 95.0,  # Above threshold
            "memory_usage": 60.0,
            "load_1m": 1.5,
            "disk_usage": 30.0
        }
        
        # Act
        result = mock_engine.predict_anomaly(metrics=test_metrics, user_id="test_user")
        
        # Assert
        assert "anomaly" in result
        assert "confidence" in result
        assert "severity" in result

    def test_predict_anomaly_multiple_thresholds_exceeded(self, mock_engine):
        """Test anomaly prediction with multiple thresholds exceeded."""
        # Arrange
        test_metrics = {
            "cpu_usage": 90.0,  # Above threshold
            "memory_usage": 90.0,  # Above threshold
            "load_1m": 6.0,  # Above threshold
            "disk_usage": 95.0  # Above threshold
        }
        
        # Act
        result = mock_engine.predict_anomaly(metrics=test_metrics, user_id="test_user")
        
        # Assert
        assert "anomaly" in result
        assert "confidence" in result
        assert "severity" in result
        assert len(result["risk_factors"]) > 0

    def test_predict_anomaly_invalid_metrics(self, mock_engine):
        """Test anomaly prediction with invalid metrics."""
        # Arrange
        invalid_metrics = "not a dict"
        
        # Act
        result = mock_engine.predict_anomaly(metrics=invalid_metrics, user_id="test_user")
        
        # Assert
        assert "error" in result
        assert result["error_code"] == "PREDICTION_ERROR"

    def test_predict_anomaly_missing_metrics(self, mock_engine):
        """Test anomaly prediction with missing metrics."""
        # Arrange
        incomplete_metrics = {
            "cpu_usage": 50.0
            # Missing other required metrics
        }
        
        # Act
        result = mock_engine.predict_anomaly(metrics=incomplete_metrics, user_id="test_user")
        
        # Assert
        assert "anomaly" in result
        assert "confidence" in result
        # Should handle missing metrics gracefully

    def test_predict_anomaly_engine_not_initialized(self):
        """Test anomaly prediction when engine is not initialized."""
        # Arrange
        engine = SecureMLInferenceEngine()
        engine._initialized = False
        
        # Act
        result = engine.predict_anomaly(metrics={}, user_id="test_user")
        
        # Assert
        assert "error" in result
        assert result["error_code"] == "PREDICTION_ERROR"

    def test_get_model_info(self, mock_engine):
        """Test getting model information."""
        # Act
        model_info = mock_engine.get_model_info()
        
        # Assert
        assert "model_type" in model_info
        assert "training_timestamp" in model_info
        assert "training_data_size" in model_info
        assert "performance" in model_info
        assert "thresholds" in model_info
        assert model_info["model_type"] == "isolation_forest"

    def test_get_model_info_no_model(self):
        """Test getting model information when no model is loaded."""
        # Arrange
        engine = SecureMLInferenceEngine()
        
        # Act
        model_info = engine.get_model_info()
        
        # Assert
        assert "error" in model_info
        assert model_info["error"] == "No model loaded"


class TestModelConfig:
    """Test suite for ModelConfig validation."""

    def test_model_config_validation_success(self):
        """Test successful model configuration validation."""
        # Arrange
        config = ModelConfig(
            model_type="isolation_forest",
            training_timestamp="2023-01-01T00:00:00Z",
            thresholds={
                "cpu_threshold": 80.0,
                "memory_threshold": 85.0,
                "load_threshold": 5.0,
                "disk_threshold": 90.0
            },
            performance={
                "accuracy": 0.95,
                "precision": 0.92,
                "recall": 0.88,
                "f1_score": 0.90,
                "confusion_matrix": {
                    "true_positives": 100,
                    "false_positives": 8,
                    "true_negatives": 900,
                    "false_negatives": 12
                }
            },
            training_data_size=1000
        )
        
        # Act
        result = config.validate()
        
        # Assert
        assert result is True

    def test_model_config_validation_missing_thresholds(self):
        """Test model configuration validation with missing thresholds."""
        # Arrange
        config = ModelConfig(
            model_type="isolation_forest",
            training_timestamp="2023-01-01T00:00:00Z",
            thresholds={
                "cpu_threshold": 80.0
                # Missing other thresholds
            },
            performance={
                "accuracy": 0.95,
                "precision": 0.92,
                "recall": 0.88,
                "f1_score": 0.90
            },
            training_data_size=1000
        )
        
        # Act & Assert
        with pytest.raises(Exception):
            config.validate()

    def test_model_config_validation_invalid_performance(self):
        """Test model configuration validation with invalid performance metrics."""
        # Arrange
        config = ModelConfig(
            model_type="isolation_forest",
            training_timestamp="2023-01-01T00:00:00Z",
            thresholds={
                "cpu_threshold": 80.0,
                "memory_threshold": 85.0,
                "load_threshold": 5.0,
                "disk_threshold": 90.0
            },
            performance={
                "accuracy": 1.5,  # Invalid: > 1.0
                "precision": 0.92,
                "recall": 0.88,
                "f1_score": 0.90
            },
            training_data_size=1000
        )
        
        # Act & Assert
        with pytest.raises(Exception):
            config.validate()


class TestPredictionResult:
    """Test suite for PredictionResult."""

    def test_prediction_result_creation(self):
        """Test creating a prediction result."""
        # Arrange
        result = PredictionResult(
            anomaly=True,
            confidence=0.85,
            severity="high",
            metrics={"cpu_usage": 90.0},
            thresholds_exceeded={"cpu_high": True},
            prediction_time_ms=150.0,
            timestamp="2023-01-01T00:00:00Z",
            model_version="iforest_v1.0",
            risk_factors=["cpu_exceeded_1.2x"]
        )
        
        # Act
        result_dict = result.to_dict()
        
        # Assert
        assert result_dict["anomaly"] is True
        assert result_dict["confidence"] == 0.85
        assert result_dict["severity"] == "high"
        assert result_dict["metrics"]["cpu_usage"] == 90.0
        assert result_dict["prediction_time_ms"] == 150.0
        assert result_dict["model_version"] == "iforest_v1.0"
        assert "cpu_exceeded_1.2x" in result_dict["risk_factors"]


class TestGlobalFunctions:
    """Test suite for global functions."""

    def test_get_secure_inference_engine_singleton(self):
        """Test that get_secure_inference_engine returns a singleton."""
        # Act
        engine1 = get_secure_inference_engine()
        engine2 = get_secure_inference_engine()
        
        # Assert
        assert engine1 is engine2
        assert isinstance(engine1, SecureMLInferenceEngine)
