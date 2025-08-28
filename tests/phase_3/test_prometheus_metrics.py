"""
Phase 3: Prometheus Metrics Tests
Tests for Prometheus metrics collection, exposure, and monitoring functionality.
"""

import pytest
from prometheus_client import Counter, generate_latest

from app.api.v1.metrics import bp as metrics_bp
from app.api.v1.ml import ML_PREDICTION_REQUESTS


class TestPrometheusMetrics:
    """Test suite for Prometheus metrics functionality."""

    @pytest.fixture
    def app(self):
        """Create a test Flask application with metrics blueprint."""
        from flask import Flask

        app = Flask(__name__)
        app.register_blueprint(metrics_bp)
        app.config["TESTING"] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        with app.test_client() as client:
            yield client

    def test_metrics_endpoint_returns_prometheus_format(self, client):
        """Test that /metrics endpoint returns Prometheus format."""
        # Act
        response = client.get("/metrics")

        # Assert
        assert response.status_code == 200
        assert "text/plain" in response.content_type
        assert "version=0.0.4" in response.content_type
        assert b"# HELP" in response.data
        assert b"# TYPE" in response.data

    def test_metrics_endpoint_contains_ml_metrics(self, client):
        """Test that /metrics endpoint contains ML-related metrics."""
        # Act
        response = client.get("/metrics")

        # Assert
        assert b"ml_prediction_requests_total" in response.data

    def test_ml_predict_success_counter(self):
        """Test ML prediction success counter."""
        # Act
        ML_PREDICTION_REQUESTS.labels(status="success").inc()

        # Assert
        # Verify the counter was incremented by checking the metrics output
        metrics_content = generate_latest()
        assert b'ml_prediction_requests_total{status="success"}' in metrics_content

    def test_ml_predict_error_counter(self):
        """Test ML prediction error counter."""
        # Act
        ML_PREDICTION_REQUESTS.labels(status="error").inc()

        # Assert
        # Verify the counter was incremented by checking the metrics output
        metrics_content = generate_latest()
        assert b'ml_prediction_requests_total{status="error"}' in metrics_content

    def test_metrics_endpoint_content_structure(self, client):
        """Test that metrics endpoint returns properly structured content."""
        # Act
        response = client.get("/metrics")
        content = response.data.decode("utf-8")

        # Assert
        lines = content.split("\n")
        assert any(line.startswith("# HELP") for line in lines)
        assert any(line.startswith("# TYPE") for line in lines)
        assert any(line.startswith("ml_prediction_") for line in lines)

    def test_metrics_endpoint_headers(self, client):
        """Test that metrics endpoint returns correct headers."""
        # Act
        response = client.get("/metrics")

        # Assert
        assert "text/plain" in response.headers.get("Content-Type", "")
        assert "version=0.0.4" in response.headers.get("Content-Type", "")
        assert "Content-Length" in response.headers

    def test_metrics_endpoint_caching_disabled(self, client):
        """Test that metrics endpoint has caching disabled."""
        # Act
        response = client.get("/metrics")

        # Assert
        # Prometheus metrics should not be cached, so no cache headers should be set
        assert "Cache-Control" not in response.headers

    def test_metrics_generation_with_custom_metrics(self):
        """Test metrics generation with custom metrics."""
        # Arrange
        custom_counter = Counter("test_counter", "Test counter")
        custom_counter.inc(5)

        # Act
        metrics_content = generate_latest()

        # Assert
        assert b"test_counter_total 5.0" in metrics_content

    def test_metrics_endpoint_returns_valid_prometheus_format(self, client):
        """Test that metrics endpoint returns valid Prometheus format."""
        # Act
        response = client.get("/metrics")
        content = response.data.decode("utf-8")

        # Assert
        # Check for basic Prometheus format requirements
        assert "# HELP" in content
        assert "# TYPE" in content
        assert "ml_prediction_requests_total" in content

        # Check that metrics have proper format
        lines = content.split("\n")
        metric_lines = [line for line in lines if line.startswith("ml_prediction_") and not line.startswith("#")]
        for line in metric_lines:
            assert " " in line  # Should have space between metric name and value
            parts = line.split(" ")
            assert len(parts) >= 2  # Should have at least name and value
            # Handle scientific notation and regular numbers
            value = parts[1]
            try:
                float(value)  # Should be a valid number
            except ValueError:
                assert False, f"Invalid metric value: {value}"

    def test_metrics_endpoint_performance(self, client):
        """Test that metrics endpoint responds quickly."""
        import time

        # Act
        start_time = time.time()
        response = client.get("/metrics")
        end_time = time.time()

        # Assert
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second

    def test_metrics_endpoint_content_length(self, client):
        """Test that metrics endpoint returns reasonable content length."""
        # Act
        response = client.get("/metrics")

        # Assert
        assert response.content_length > 0
        assert response.content_length < 100000  # Should not be unreasonably large

    def test_metrics_endpoint_utf8_encoding(self, client):
        """Test that metrics endpoint returns UTF-8 encoded content."""
        # Act
        response = client.get("/metrics")

        # Assert
        content = response.data.decode("utf-8")
        assert isinstance(content, str)
        # Should be able to decode without errors
        assert len(content) > 0
