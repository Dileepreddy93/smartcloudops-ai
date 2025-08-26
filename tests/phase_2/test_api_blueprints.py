"""
Phase 2: API Blueprints Tests
Tests for API v1 blueprints (health, chatops, logs, ml).
"""

import pytest
from flask import Flask
from app.api.v1 import health, chatops, logs, ml


class TestHealthBlueprint:
    """Test suite for health blueprint."""

    @pytest.fixture
    def app(self):
        """Create a test Flask application with health blueprint."""
        app = Flask(__name__)
        app.register_blueprint(health.bp)
        app.config["TESTING"] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        with app.test_client() as client:
            yield client

    def test_status_endpoint(self, client, monkeypatch):
        """Test the /status endpoint."""
        # Arrange

        class MockEngine:
            def health_check(self):
                return {"status": "healthy", "metrics": {"test": "data"}}

        monkeypatch.setattr(
            "app.api.v1.health.get_secure_inference_engine", lambda: MockEngine()
        )

        # Act
        response = client.get("/status")

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        # Compatibility fields override DTO status
        assert data["status"] == "healthy"  # Compatibility field overrides DTO
        assert data["data"]["message"] == "OK"
        assert "ml" in data["data"]

    def test_home_endpoint(self, client):
        """Test the / endpoint."""
        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["message"] == "SmartCloudOps AI Platform"
        assert "version" in data
        assert "timestamp" in data


class TestChatOpsBlueprint:
    """Test suite for chatops blueprint."""

    @pytest.fixture
    def app(self):
        """Create a test Flask application with chatops blueprint."""
        app = Flask(__name__)
        app.register_blueprint(chatops.bp)
        app.config["TESTING"] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        with app.test_client() as client:
            yield client

    def test_query_endpoint_success(self, client, monkeypatch):
        """Test the /query endpoint with valid input."""
        # Arrange
        monkeypatch.setattr(
            "app.api.v1.chatops.get_chat_response", lambda q: "Mocked AI response"
        )

        # Act
        response = client.post("/query", json={"query": "test query"})

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["response"] == "Mocked AI response"

    def test_query_endpoint_missing_query(self, client):
        """Test the /query endpoint with missing query field."""
        # Act
        response = client.post("/query", json={"other_field": "value"})

        # Assert
        assert response.status_code == 400
        assert b"Invalid request" in response.data

    def test_query_endpoint_empty_json(self, client):
        """Test the /query endpoint with empty JSON."""
        # Act
        response = client.post("/query", json={})

        # Assert
        assert response.status_code == 400
        assert b"Invalid request" in response.data

    def test_query_endpoint_service_error(self, client, monkeypatch):
        """Test the /query endpoint handles service errors."""
        # Arrange
        monkeypatch.setattr(
            "app.api.v1.chatops.get_chat_response",
            lambda q: (_ for _ in ()).throw(Exception("Service error")),
        )

        # Act
        response = client.post("/query", json={"query": "test query"})

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert data["error"]["message"] == "Failed to process query"


class TestLogsBlueprint:
    """Test suite for logs blueprint."""

    @pytest.fixture
    def app(self):
        """Create a test Flask application with logs blueprint."""
        app = Flask(__name__)
        app.register_blueprint(logs.bp)
        app.config["TESTING"] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        with app.test_client() as client:
            yield client

    def test_logs_endpoint(self, client, monkeypatch):
        """Test the /logs endpoint."""
        # Arrange
        monkeypatch.setattr("app.main.get_logs_data", lambda: "Mocked log content")

        # Act
        response = client.get("/logs")

        # Assert
        assert response.status_code == 200
        assert response.mimetype == "text/plain"
        assert response.data.decode() == "Mocked log content"

    def test_logs_endpoint_empty_content(self, client, monkeypatch):
        """Test the /logs endpoint with empty content."""
        # Arrange
        monkeypatch.setattr("app.main.get_logs_data", lambda: "")

        # Act
        response = client.get("/logs")

        # Assert
        assert response.status_code == 200
        assert response.data.decode() == ""


class TestMLBlueprint:
    """Test suite for ML blueprint."""

    @pytest.fixture
    def app(self):
        """Create a test Flask application with ML blueprint."""
        app = Flask(__name__)
        app.register_blueprint(ml.bp)
        app.config["TESTING"] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        with app.test_client() as client:
            yield client

    def test_ml_health_endpoint(self, client, monkeypatch):
        """Test the /ml/health endpoint."""
        # Arrange

        class MockEngine:
            def health_check(self):
                return {"status": "healthy", "model_loaded": True}

        monkeypatch.setattr(
            "app.api.v1.ml.get_secure_inference_engine", lambda: MockEngine()
        )

        # Act
        response = client.get("/ml/health")

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["status"] == "healthy"

    def test_ml_predict_endpoint_success(self, client, monkeypatch):
        """Test the /ml/predict endpoint with valid input."""
        # Arrange

        class MockEngine:
            def predict_anomaly(self, metrics=None, user_id=None):
                return {"anomaly": False, "confidence": 0.9, "metrics": metrics}

        monkeypatch.setattr(
            "app.api.v1.ml.get_secure_inference_engine", lambda: MockEngine()
        )

        # Act
        response = client.post(
            "/ml/predict",
            json={
                "metrics": {
                    "cpu_usage": 50.0,
                    "memory_usage": 60.0,
                    "load_1m": 1.5,
                    "disk_usage": 30.0,
                }
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["anomaly"] is False
        assert data["data"]["confidence"] == 0.9

    def test_ml_predict_endpoint_invalid_metrics(self, client):
        """Test the /ml/predict endpoint with invalid metrics."""
        # Act
        response = client.post("/ml/predict", json={"metrics": "not a dict"})

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"

    def test_ml_predict_endpoint_missing_metrics(self, client):
        """Test the /ml/predict endpoint with missing metrics."""
        # Act
        response = client.post("/ml/predict", json={})

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"

    def test_ml_predict_endpoint_engine_error(self, client, monkeypatch):
        """Test the /ml/predict endpoint handles engine errors."""
        # Arrange

        class MockEngine:
            def predict_anomaly(self, metrics=None, user_id=None):
                return {"error": "Engine error", "anomaly": False, "confidence": 0.0}

        monkeypatch.setattr(
            "app.api.v1.ml.get_secure_inference_engine", lambda: MockEngine()
        )

        # Act
        response = client.post("/ml/predict", json={"metrics": {"cpu_usage": 50.0}})

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"

    def test_ml_metrics_endpoint(self, client, monkeypatch):
        """Test the /ml/metrics endpoint."""
        # Arrange

        class MockEngine:
            def health_check(self):
                return {
                    "status": "healthy",
                    "metrics": {"prediction_count": 100},
                    "model_info": {"type": "iforest"},
                }

        monkeypatch.setattr(
            "app.api.v1.ml.get_secure_inference_engine", lambda: MockEngine()
        )

        # Act
        response = client.get("/ml/metrics")

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["status"] == "healthy"
        assert "metrics" in data["data"]
        assert "model_info" in data["data"]
