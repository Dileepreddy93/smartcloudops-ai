"""
Phase 1: Core Utilities Tests
Tests for response and validation utility modules.
"""

import time
from datetime import datetime

import pytest
from flask import Flask

from app.utils.response import build_success_response, error_response, success_response
from app.utils.validation import sanitize_string, validate_user_input


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = Flask(__name__)
    return app


class TestResponseUtilities:
    """Test suite for response utility functions."""

    def test_timestamp_in_response(self):
        """Test that responses include UTC timestamp in ISO format."""
        # Act
        response_data = build_success_response(data={"test": "data"})

        # Assert
        assert "timestamp" in response_data
        timestamp = response_data["timestamp"]
        assert isinstance(timestamp, str)
        # Parse and verify it's a valid ISO timestamp
        parsed_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed_time.tzinfo is not None
        assert parsed_time.tzinfo.utcoffset(parsed_time) is not None

    def test_success_response(self, app):
        """Test success_response with data."""
        # Arrange
        test_data = {"message": "test", "count": 42}

        # Act
        with app.app_context():
            response = success_response(data=test_data)

        # Assert
        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data["status"] == "success"
        assert response_data["data"] == test_data

    def test_error_response(self, app):
        """Test error_response with error message."""
        # Arrange
        error_message = "Test error"

        # Act
        with app.app_context():
            response = error_response(message=error_message, status_code=400)

        # Assert
        assert response.status_code == 400
        response_data = response.get_json()
        assert response_data["status"] == "error"
        assert response_data["message"] == error_message

    def test_success_response_with_metadata(self, app):
        """Test success_response with metadata."""
        # Arrange
        test_data = {"message": "test"}
        metadata = {"version": "1.0.0"}

        # Act
        with app.app_context():
            response = success_response(data=test_data, metadata=metadata)

        # Assert
        response_data = response.get_json()
        assert response_data["status"] == "success"
        assert response_data["data"] == test_data
        assert response_data["metadata"]["version"] == "1.0.0"


class TestValidationUtilities:
    """Test suite for validation utility functions."""

    def test_validate_user_input_valid_input(self):
        """Test validate_user_input with valid input."""
        # Arrange
        test_data = {"username": "testuser", "email": "test@example.com"}
        required_fields = ["username", "email"]

        # Act
        validated_data = validate_user_input(test_data, required_fields)

        # Assert
        assert validated_data["username"] == "testuser"
        assert validated_data["email"] == "test@example.com"

    def test_validate_user_input_missing_keys(self):
        """Test validate_user_input with missing keys."""
        # Arrange
        test_data = {"username": "testuser"}
        required_fields = ["username", "email"]

        # Act & Assert
        with pytest.raises(ValueError, match="Missing required fields"):
            validate_user_input(test_data, required_fields)

    def test_validate_user_input_invalid_input_type(self):
        """Test validate_user_input with invalid input type."""
        # Arrange
        test_data = "not a dict"
        required_fields = ["username"]

        # Act & Assert
        with pytest.raises(ValueError, match="Input data must be a dictionary"):
            validate_user_input(test_data, required_fields)

    def test_sanitize_string_normal_input(self):
        """Test sanitize_string with normal input."""
        # Arrange
        test_input = "  Hello World  "
        max_len = 50

        # Act
        result = sanitize_string(test_input, max_len)

        # Assert
        assert result == "Hello World"

    def test_sanitize_string_truncation(self):
        """Test sanitize_string with truncation."""
        # Arrange
        test_input = "This is a very long string that should be truncated"
        max_len = 20

        # Act
        result = sanitize_string(test_input, max_len)

        # Assert
        assert len(result) == 19  # "This is a very long" is 19 characters
        assert result == "This is a very long"

    def test_sanitize_string_non_string_input(self):
        """Test sanitize_string with non-string input."""
        # Arrange
        test_inputs = [123, True, 3.14]

        # Act & Assert
        for test_input in test_inputs:
            result = sanitize_string(test_input)
            assert isinstance(result, str)
            assert result == str(test_input).strip()

        # Test None separately
        result = sanitize_string(None)
        assert isinstance(result, str)
        assert result == ""

    def test_sanitize_string_empty_input(self):
        """Test sanitize_string with empty input."""
        # Arrange
        test_inputs = ["", "   "]

        # Act & Assert
        for test_input in test_inputs:
            result = sanitize_string(test_input)
            assert result == ""

        # Test None separately
        result = sanitize_string(None)
        assert result == ""

    def test_sanitize_string_default_max_length(self):
        """Test sanitize_string with default max length."""
        # Arrange
        test_input = "x" * 3000  # Longer than default 1000

        # Act
        result = sanitize_string(test_input)

        # Assert
        assert len(result) == 1000
