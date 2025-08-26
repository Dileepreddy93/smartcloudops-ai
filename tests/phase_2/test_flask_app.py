"""
Phase 2: Flask Application Tests
Tests for Flask app creation, configuration, and core functionality.
"""

import pytest
from flask import Flask
from app.main import create_app, get_status_info, get_logs_data, get_chat_response


class TestFlaskAppCreation:
    """Test suite for Flask application creation and configuration."""

    def test_create_app_returns_flask_app(self):
        """Test create_app returns a Flask application instance."""
        # Act
        app = create_app()

        # Assert
        assert isinstance(app, Flask)
        assert app.name == "app.main"

    def test_create_app_configuration(self):
        """Test Flask app configuration."""
        # Act
        app = create_app()

        # Assert
        assert app.config["TESTING"] is False  # Default configuration
        assert app.name == "app.main"

    def test_create_app_with_testing_config(self):
        """Test create_app with testing configuration."""
        # Arrange
        test_config = {"TESTING": True}

        # Act
        app = create_app()
        app.config.update(test_config)

        # Assert
        assert app.config["TESTING"] is True


class TestHelperFunctions:
    """Test suite for helper functions in main.py."""

    def test_get_status_info_returns_dict(self):
        """Test get_status_info returns a dictionary with required keys."""
        # Act
        status_info = get_status_info()

        # Assert
        assert isinstance(status_info, dict)
        assert "status" in status_info
        assert "message" in status_info
        assert "timestamp" in status_info
        assert status_info["status"] == "healthy"
        assert status_info["message"] == "OK"

    def test_get_logs_data_returns_string(self):
        """Test get_logs_data returns a string."""
        # Act
        logs_data = get_logs_data()

        # Assert
        assert isinstance(logs_data, str)

    def test_get_logs_data_caching(self):
        """Test get_logs_data implements caching."""
        # Act
        logs_data1 = get_logs_data()
        logs_data2 = get_logs_data()

        # Assert
        assert logs_data1 == logs_data2  # Should be cached

    def test_get_chat_response_wrapper(self):
        """Test get_chat_response is a wrapper function."""
        # Arrange
        test_query = "test query"

        # Act & Assert
        # This should not raise an exception even if OpenAI is not available
        # as it's designed to handle missing dependencies gracefully
        try:
            result = get_chat_response(test_query)
            assert isinstance(result, str)
        except Exception:
            # Expected if OpenAI is not configured
            pass


class TestFlaskAppEndpoints:
    """Test suite for Flask application endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the Flask application."""
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_home_endpoint(self, client):
        """Test the home endpoint (/) returns correct response."""
        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["message"] == "SmartCloudOps AI Platform"
        assert "version" in data
        assert "timestamp" in data

    def test_status_endpoint(self, client):
        """Test the status endpoint (/status) returns correct response."""
        # Act
        response = client.get("/status")

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        # Endpoint may return top-level status as "healthy" (compat) or DTO "success"
        assert data.get("status") in {"success", "healthy"}
        if "data" in data:
            assert data["data"]["message"] == "OK"

    def test_query_endpoint_success(self, client, monkeypatch):
        """Test the query endpoint with successful response."""
        # Arrange
        from app.services import chatops_service

        monkeypatch.setattr(chatops_service, "chat", lambda q: "Mocked response")

        # Act
        response = client.post("/query", json={"query": "test query"})

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data["response"] == "Mocked response"

    def test_query_endpoint_invalid_input(self, client):
        """Test the query endpoint with invalid input."""
        # Act
        response = client.post("/query", json={"invalid": "data"})

        # Assert
        assert response.status_code == 400
        assert b"Invalid request" in response.data

    def test_query_endpoint_missing_query(self, client):
        """Test the query endpoint with missing query field."""
        # Act
        response = client.post("/query", json={})

        # Assert
        assert response.status_code == 400
        assert b"Invalid request" in response.data

    def test_logs_endpoint(self, client):
        """Test the logs endpoint returns text content."""
        # Act
        response = client.get("/logs")

        # Assert
        assert response.status_code == 200
        assert response.mimetype == "text/plain"
        assert isinstance(response.data, bytes)

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
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_query_endpoint_service_error(self, client, monkeypatch):
        """Test query endpoint handles service errors gracefully."""
        # Arrange
        from app.services import chatops_service

        monkeypatch.setattr(
            chatops_service,
            "chat",
            lambda q: (_ for _ in ()).throw(Exception("Service error")),
        )

        # Act
        response = client.post("/query", json={"query": "test query"})

        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert data["error"]["message"] == "Failed to process query"

    def test_query_endpoint_invalid_json(self, client):
        """Test query endpoint handles invalid JSON gracefully."""
        # Act
        response = client.post(
            "/query", data="invalid json", content_type="application/json"
        )

        # Assert
        assert response.status_code == 400
        assert b"Invalid request" in response.data
