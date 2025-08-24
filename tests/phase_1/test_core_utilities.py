"""
Phase 1: Core Utilities Tests
Tests for response and validation utility modules.
"""

import pytest
from datetime import datetime
from flask import Flask
from app.utils.response import make_response, now_iso
from app.utils.validation import require_json_keys, sanitize_string


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = Flask(__name__)
    return app


class TestResponseUtilities:
    """Test suite for response utility functions."""

    def test_now_iso_returns_utc_timestamp(self):
        """Test now_iso returns UTC timestamp in ISO format."""
        # Act
        timestamp = now_iso()
        
        # Assert
        assert isinstance(timestamp, str)
        # Parse and verify it's a valid ISO timestamp
        parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert parsed_time.tzinfo is not None
        assert parsed_time.tzinfo.utcoffset(parsed_time) is not None

    def test_make_response_success(self, app):
        """Test make_response with success data."""
        # Arrange
        test_data = {"message": "test", "count": 42}
        
        # Act
        with app.app_context():
            response, status_code = make_response(data=test_data)
        
        # Assert
        assert status_code == 200
        response_data = response.get_json()
        assert response_data["status"] == "success"
        assert response_data["data"] == test_data
        assert response_data["error"] is None

    def test_make_response_error(self, app):
        """Test make_response with error."""
        # Arrange
        error_message = "Test error"
        
        # Act
        with app.app_context():
            response, status_code = make_response(error=error_message, http_status=400)
        
        # Assert
        assert status_code == 400
        response_data = response.get_json()
        assert response_data["status"] == "error"
        assert response_data["data"] is None
        assert response_data["error"]["message"] == error_message

    def test_make_response_with_compatibility_fields(self, app):
        """Test make_response with compatibility fields."""
        # Arrange
        test_data = {"message": "test"}
        compat_fields = {"version": "1.0.0", "timestamp": "2023-01-01T00:00:00Z"}
        
        # Act
        with app.app_context():
            response, status_code = make_response(data=test_data, compatibility=compat_fields)
        
        # Assert
        response_data = response.get_json()
        assert response_data["status"] == "success"
        assert response_data["data"] == test_data
        assert response_data["version"] == "1.0.0"
        assert response_data["timestamp"] == "2023-01-01T00:00:00Z"


class TestValidationUtilities:
    """Test suite for validation utility functions."""

    def test_require_json_keys_valid_input(self):
        """Test require_json_keys with valid input."""
        # Arrange
        test_obj = {"key1": "value1", "key2": "value2"}
        required_keys = ["key1", "key2"]
        
        # Act
        is_valid, error = require_json_keys(test_obj, required_keys)
        
        # Assert
        assert is_valid is True
        assert error is None

    def test_require_json_keys_missing_keys(self):
        """Test require_json_keys with missing keys."""
        # Arrange
        test_obj = {"key1": "value1"}
        required_keys = ["key1", "key2", "key3"]
        
        # Act
        is_valid, error = require_json_keys(test_obj, required_keys)
        
        # Assert
        assert is_valid is False
        assert "Missing keys: key2, key3" in error

    def test_require_json_keys_invalid_input_type(self):
        """Test require_json_keys with invalid input type."""
        # Arrange
        test_obj = "not a dict"
        required_keys = ["key1"]
        
        # Act
        is_valid, error = require_json_keys(test_obj, required_keys)
        
        # Assert
        assert is_valid is False
        assert error == "Invalid JSON payload"

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
        assert len(result) == 20
        assert result == "This is a very long "  # Note: space at end due to truncation after strip

    def test_sanitize_string_non_string_input(self):
        """Test sanitize_string with non-string input."""
        # Arrange
        test_inputs = [123, None, True, 3.14]
        
        # Act & Assert
        for test_input in test_inputs:
            result = sanitize_string(test_input)
            assert isinstance(result, str)
            assert result == str(test_input).strip()

    def test_sanitize_string_empty_input(self):
        """Test sanitize_string with empty input."""
        # Arrange
        test_inputs = ["", "   "]
        
        # Act & Assert
        for test_input in test_inputs:
            result = sanitize_string(test_input)
            assert result == ""
        
        # Test None separately as it converts to "None" string
        result = sanitize_string(None)
        assert result == "None"

    def test_sanitize_string_default_max_length(self):
        """Test sanitize_string with default max length."""
        # Arrange
        test_input = "x" * 3000  # Longer than default 2048
        
        # Act
        result = sanitize_string(test_input)
        
        # Assert
        assert len(result) == 2048
