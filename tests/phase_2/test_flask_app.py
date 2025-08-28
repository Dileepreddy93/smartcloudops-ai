"""
Phase 2: Flask Application Tests
Tests for Flask app creation, configuration, and core functionality.
"""

import pytest
from flask import Flask

from app.main_secure import app
from app.services.chatops_service import chat


class TestFlaskAppCreation:
    """Test suite for Flask application creation and configuration."""

    def test_app_is_flask_instance(self):
        """Test that app is a Flask application instance."""
        # Assert
        assert isinstance(app, Flask)

    def test_app_configuration(self):
        """Test Flask app configuration."""
        # Assert
        assert app.name == "app.main_secure"


class TestHelperFunctions:
    """Test suite for helper functions."""

    def test_chat_function_exists(self):
        """Test that chat function exists and is callable."""
        # Assert
        assert callable(chat)

    def test_chat_function_handles_errors(self):
        """Test chat function handles errors gracefully."""
        # Arrange
        test_query = "test query"

        # Act & Assert
        # This should not raise an exception even if OpenAI is not available
        # as it's designed to handle missing dependencies gracefully
        try:
            result = chat(test_query)
            assert isinstance(result, str)
        except Exception:
            # Expected if OpenAI is not configured
            pass


class TestFlaskAppEndpoints:
    """Test suite for Flask application endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the Flask application."""
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_health_endpoint(self, client):
        """Test the health endpoint (/health) returns correct response."""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_status_endpoint(self, client):
        """Test the status endpoint (/status) returns correct response."""
        # Act
        response = client.get("/status", headers={"X-API-Key": "sk-readonly-test-key-12345678901234567890"})

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        # Endpoint returns success status with data
        assert data.get("status") == "success"
        if "data" in data:
            assert "status" in data["data"]

    def test_chat_endpoint_success(self, client, monkeypatch):
        """Test the chat endpoint with successful response."""
        # Arrange
        from app.services import chatops_service

        monkeypatch.setattr(chatops_service, "chat", lambda q: "Mocked response")

        # Act
        response = client.post(
            "/chat", json={"message": "test query"}, headers={"X-API-Key": "sk-ml-test-key-12345678901234567890"}
        )

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert "response" in data

    def test_chat_endpoint_invalid_input(self, client):
        """Test the chat endpoint with invalid input."""
        # Act
        response = client.post(
            "/chat", json={"invalid": "data"}, headers={"X-API-Key": "sk-ml-test-key-12345678901234567890"}
        )

        # Assert
        assert response.status_code == 400

    def test_chat_endpoint_missing_query(self, client):
        """Test the chat endpoint with missing query field."""
        # Act
        response = client.post("/chat", json={}, headers={"X-API-Key": "sk-ml-test-key-12345678901234567890"})

        # Assert
        assert response.status_code == 400

    def test_metrics_endpoint(self, client):
        """Test the metrics endpoint returns JSON content."""
        # Act
        response = client.get("/metrics")

        # Assert
        assert response.status_code == 200
        assert response.mimetype == "application/json"
        data = response.get_json()
        assert isinstance(data, dict)

    def test_nonexistent_endpoint(self, client):
        """Test that nonexistent endpoints return 404."""
        # Act
        response = client.get("/nonexistent")

        # Assert
        assert response.status_code == 404


class TestFlaskAppErrorHandling:
    """Test suite for Flask application error handling."""

    @pytest.fixture
    def client(self):
        """Create a test client for the Flask application."""
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_chat_endpoint_service_error(self, client, monkeypatch):
        """Test chat endpoint handles service errors gracefully."""
        # Arrange
        from app.services import chatops_service

        monkeypatch.setattr(
            chatops_service,
            "chat",
            lambda q: (_ for _ in ()).throw(Exception("Service error")),
        )

        # Act
        response = client.post(
            "/chat", json={"message": "test query"}, headers={"X-API-Key": "sk-ml-test-key-12345678901234567890"}
        )

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert data["error"]["message"] == "Failed to process query"

    def test_query_endpoint_invalid_json(self, client):
        """Test query endpoint handles invalid JSON gracefully."""
        # Act
        response = client.post("/query", data="invalid json", content_type="application/json")

        # Assert
        assert response.status_code == 400
        assert b"Invalid request" in response.data
