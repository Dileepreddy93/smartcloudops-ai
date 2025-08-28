#!/usr/bin/env python3
"""
Test ML Service - Comprehensive ML Service Testing
================================================

Tests for the production-ready ML service with real anomaly detection.
"""

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from app.services.ml_service import MLModelManager, MLService


class TestMLModelManager:
    """Test ML Model Manager functionality."""

    def test_model_manager_initialization(self, tmp_path):
        """Test ML model manager initialization."""
        model_dir = tmp_path / "ml_models"
        manager = MLModelManager(str(model_dir))

        assert manager.model_dir == model_dir
        assert manager.current_model is None
        assert manager.current_scaler is None
        assert isinstance(manager.model_metadata, dict)

    def test_save_and_load_model(self, tmp_path):
        """Test model saving and loading."""
        model_dir = tmp_path / "ml_models"
        manager = MLModelManager(str(model_dir))

        # Create mock model and scaler
        mock_model = MagicMock()
        mock_scaler = MagicMock()
        metadata = {"test": "data", "created_at": datetime.now().isoformat()}

        # Save model
        model_path = manager.save_model(mock_model, mock_scaler, metadata)

        # Verify model was saved
        assert model_path is not None
        assert manager.current_model == mock_model
        assert manager.current_scaler == mock_scaler
        assert manager.model_metadata == metadata

    def test_get_model_info(self, tmp_path):
        """Test model information retrieval."""
        model_dir = tmp_path / "ml_models"
        manager = MLModelManager(str(model_dir))

        # Test with no model loaded
        info = manager.get_model_info()
        assert info["version"] is None
        assert info["model_type"] is None

        # Test with model loaded
        mock_model = MagicMock()
        mock_scaler = MagicMock()
        manager.current_model = mock_model
        manager.current_scaler = mock_scaler
        manager.model_version = "1.0"
        manager.model_metadata = {"test": "data"}

        info = manager.get_model_info()
        assert info["version"] == "1.0"
        assert info["model_type"] == "MagicMock"

    def test_health_check(self, tmp_path):
        """Test health check functionality."""
        model_dir = tmp_path / "ml_models"
        manager = MLModelManager(str(model_dir))

        # Test unhealthy state
        health = manager.health_check()
        assert health["status"] == "unhealthy"
        assert health["model_loaded"] is False

        # Test healthy state
        manager.current_model = MagicMock()
        manager.model_version = "1.0"
        manager.model_metadata = {"created_at": "2024-01-01T00:00:00"}

        health = manager.health_check()
        assert health["status"] == "healthy"
        assert health["model_loaded"] is True
        assert health["version"] == "1.0"


class TestMLService:
    """Test ML Service functionality."""

    @pytest.fixture
    def ml_service(self, tmp_path):
        """Create ML service instance for testing."""
        with patch("app.services.ml_service.MLModelManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            service = MLService()
            service.model_manager = mock_manager
            return service

    def test_ml_service_initialization(self, ml_service):
        """Test ML service initialization."""
        assert ml_service.feature_columns == [
            "cpu_usage",
            "memory_usage",
            "disk_usage",
            "network_io",
            "response_time",
            "error_rate",
            "request_count",
        ]
        assert ml_service.anomaly_threshold == -0.5

    def test_generate_training_data(self, ml_service):
        """Test training data generation."""
        data = ml_service._generate_training_data(100)

        assert isinstance(data, pd.DataFrame)
        assert len(data) == 100
        assert "is_anomaly" in data.columns
        assert all(col in data.columns for col in ml_service.feature_columns)

        # Check data distribution
        anomaly_count = data["is_anomaly"].sum()
        assert 15 <= anomaly_count <= 25  # ~20% anomalies

    def test_train_model_success(self, ml_service):
        """Test successful model training."""
        # Mock the model manager
        ml_service.model_manager.save_model.return_value = "/path/to/model.pkl"

        # Train model
        result = ml_service.train_model()

        assert result["status"] == "success"
        assert result["model_path"] == "/path/to/model.pkl"
        assert "performance" in result
        assert "f1_score" in result["performance"]

        # Verify model manager was called
        ml_service.model_manager.save_model.assert_called_once()

    def test_train_model_with_custom_data(self, ml_service):
        """Test model training with custom data."""
        # Create custom training data
        custom_data = pd.DataFrame(
            {
                "cpu_usage": [30, 85, 40, 90],
                "memory_usage": [50, 90, 60, 95],
                "disk_usage": [60, 95, 70, 98],
                "network_io": [100, 500, 150, 600],
                "response_time": [200, 1000, 250, 1200],
                "error_rate": [2, 15, 3, 20],
                "request_count": [1000, 5000, 1200, 6000],
                "is_anomaly": [0, 1, 0, 1],
            }
        )

        ml_service.model_manager.save_model.return_value = "/path/to/model.pkl"

        result = ml_service.train_model(custom_data)

        assert result["status"] == "success"
        assert result["model_path"] == "/path/to/model.pkl"

    def test_predict_anomaly_success(self, ml_service):
        """Test successful anomaly prediction."""
        # Mock model and scaler
        mock_model = MagicMock()
        mock_model.decision_function.return_value = np.array([-0.8])
        ml_service.model_manager.current_model = mock_model
        ml_service.model_manager.current_scaler = MagicMock()
        ml_service.model_manager.current_scaler.transform.return_value = np.array(
            [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]]
        )
        ml_service.model_manager.model_version = "1.0"

        # Test metrics
        metrics = {
            "cpu_usage": 85.0,
            "memory_usage": 90.0,
            "disk_usage": 75.0,
            "network_io": 500.0,
            "response_time": 1000.0,
            "error_rate": 15.0,
            "request_count": 5000.0,
        }

        result = ml_service.predict_anomaly(metrics)

        assert result["anomaly_score"] == -0.8
        assert result["is_anomaly"] is True  # -0.8 < -0.5 threshold
        assert result["confidence"] > 0
        assert result["model_version"] == "1.0"
        assert result["features_used"] == ml_service.feature_columns

    def test_predict_anomaly_no_model(self, ml_service):
        """Test prediction without loaded model."""
        ml_service.model_manager.current_model = None

        metrics = {"cpu_usage": 50.0}

        with pytest.raises(ValueError, match="No model loaded"):
            ml_service.predict_anomaly(metrics)

    def test_predict_anomaly_missing_features(self, ml_service):
        """Test prediction with missing features."""
        # Mock model and scaler
        mock_model = MagicMock()
        mock_model.decision_function.return_value = np.array([0.1])
        ml_service.model_manager.current_model = mock_model
        ml_service.model_manager.current_scaler = MagicMock()
        ml_service.model_manager.current_scaler.transform.return_value = np.array(
            [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]]
        )
        ml_service.model_manager.model_version = "1.0"

        # Test with missing features (should use defaults)
        metrics = {"cpu_usage": 50.0}  # Missing other features

        result = ml_service.predict_anomaly(metrics)

        assert result["anomaly_score"] == 0.1
        assert result["is_anomaly"] is False  # 0.1 > -0.5 threshold
        assert result["features_used"] == ml_service.feature_columns

    def test_get_model_info(self, ml_service):
        """Test model information retrieval."""
        mock_info = {"version": "1.0", "model_type": "IsolationForest"}
        ml_service.model_manager.get_model_info.return_value = mock_info

        result = ml_service.get_model_info()

        assert result == mock_info
        ml_service.model_manager.get_model_info.assert_called_once()

    def test_health_check(self, ml_service):
        """Test health check functionality."""
        mock_health = {"status": "healthy", "model_loaded": True}
        ml_service.model_manager.health_check.return_value = mock_health

        result = ml_service.health_check()

        assert result == mock_health
        ml_service.model_manager.health_check.assert_called_once()

    def test_retrain_model(self, ml_service):
        """Test model retraining."""
        ml_service.train_model = MagicMock(return_value={"status": "success"})

        result = ml_service.retrain_model()

        assert result["status"] == "success"
        ml_service.train_model.assert_called_once()


class TestMLServiceIntegration:
    """Integration tests for ML service."""

    def test_full_ml_pipeline(self, tmp_path):
        """Test complete ML pipeline from training to prediction."""
        # Create ML service
        service = MLService()

        # Train model
        training_result = service.train_model()
        assert training_result["status"] == "success"

        # Check model is loaded
        health = service.health_check()
        assert health["status"] == "healthy"
        assert health["model_loaded"] is True

        # Make predictions
        normal_metrics = {
            "cpu_usage": 30.0,
            "memory_usage": 50.0,
            "disk_usage": 60.0,
            "network_io": 100.0,
            "response_time": 200.0,
            "error_rate": 2.0,
            "request_count": 1000.0,
        }

        anomaly_metrics = {
            "cpu_usage": 85.0,
            "memory_usage": 90.0,
            "disk_usage": 95.0,
            "network_io": 500.0,
            "response_time": 1000.0,
            "error_rate": 15.0,
            "request_count": 5000.0,
        }

        # Test normal metrics
        normal_result = service.predict_anomaly(normal_metrics)
        assert isinstance(normal_result["anomaly_score"], float)
        assert isinstance(normal_result["is_anomaly"], bool)
        assert isinstance(normal_result["confidence"], float)

        # Test anomaly metrics
        anomaly_result = service.predict_anomaly(anomaly_metrics)
        assert isinstance(anomaly_result["anomaly_score"], float)
        assert isinstance(anomaly_result["is_anomaly"], bool)
        assert isinstance(anomaly_result["confidence"], float)

        # Get model info
        model_info = service.get_model_info()
        assert "version" in model_info
        assert "performance" in model_info

    def test_model_performance(self, tmp_path):
        """Test model performance metrics."""
        service = MLService()

        # Train model
        result = service.train_model()

        # Check performance metrics
        performance = result["performance"]
        assert "accuracy" in performance
        assert "precision" in performance
        assert "recall" in performance
        assert "f1_score" in performance

        # Performance should be reasonable
        assert 0.7 <= performance["accuracy"] <= 1.0
        assert 0.5 <= performance["f1_score"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
