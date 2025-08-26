#!/usr/bin/env python3
"""
SmartCloudOps AI - Security Fixes Validation Tests
"""

import os
import pytest
from unittest.mock import patch
from flask import Flask

# Test the validation utilities directly
from app.utils.validation import InputValidator, ValidationError
from app.utils.response import APIResponse


class TestInputValidation:
    """Test input validation security."""

    def test_string_sanitization(self):
        """Test string sanitization."""
        result = InputValidator.sanitize_string("hello world")
        assert result == "hello world"

        # Test string with control characters
        result = InputValidator.sanitize_string("hello\x00world")
        assert result == "helloworld"

    def test_api_key_validation_pattern(self):
        """Test API key validation pattern."""
        # Valid API keys - must match pattern: sk-[a-zA-Z0-9]{20,}
        valid_keys = [
            "sk-admin12345678901234567890",
            "sk-mlabcdefghijklmnopqrstuvwxyz1234567890"
        ]
        
        for key in valid_keys:
            result = InputValidator.validate_api_key(key)
            assert result == key

        # Invalid API keys
        invalid_keys = [
            "invalid-key",
            "sk-",
            "sk-admin",
            "sk-admin-123",  # Contains hyphen
            "sk-admin123"  # Too short (less than 20 chars after sk-)
        ]
        
        for key in invalid_keys:
            with pytest.raises(ValidationError):
                InputValidator.validate_api_key(key)

    def test_metrics_validation(self):
        """Test metrics validation."""
        # Valid metrics
        valid_metrics = {
            "cpu_usage": 50.0,
            "memory_usage": 75.0,
            "disk_usage": 60.0
        }
        
        result = InputValidator.validate_metrics(valid_metrics)
        assert result == valid_metrics

        # Invalid metrics - missing required
        invalid_metrics = {
            "cpu_usage": 50.0
        }
        
        with pytest.raises(ValidationError):
            InputValidator.validate_metrics(invalid_metrics)


class TestResponseSecurity:
    """Test response security and standardization."""

    def setup_method(self):
        """Setup Flask app context for response tests."""
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def teardown_method(self):
        """Cleanup Flask app context."""
        self.app_context.pop()

    def test_success_response_format(self):
        """Test success response format."""
        response, status_code = APIResponse.success(
            data={"test": "data"},
            message="Test success"
        )
        
        assert status_code == 200
        response_data = response.get_json()
        assert response_data["status"] == "success"
        assert response_data["message"] == "Test success"

    def test_error_response_format(self):
        """Test error response format."""
        response, status_code = APIResponse.error(
            message="Test error",
            status_code=400,
            error_code="TEST_ERROR"
        )
        
        assert status_code == 400
        response_data = response.get_json()
        assert response_data["status"] == "error"
        assert response_data["message"] == "Test error"

    def test_validation_error_response(self):
        """Test validation error response."""
        errors = ["Field is required", "Invalid format"]
        response, status_code = APIResponse.validation_error(errors)
        
        assert status_code == 422
        response_data = response.get_json()
        assert response_data["error_code"] == "VALIDATION_ERROR"
        assert response_data["details"]["errors"] == errors


class TestDockerComposeSecurity:
    """Test Docker Compose security configuration."""

    def test_docker_compose_exists(self):
        """Test that Docker Compose file exists and is not empty."""
        compose_path = "docker/docker-compose.yml"
        assert os.path.exists(compose_path)
        
        with open(compose_path, 'r') as f:
            content = f.read()
            assert len(content) > 0

    def test_docker_compose_services(self):
        """Test Docker Compose services configuration."""
        compose_path = "docker/docker-compose.yml"
        
        with open(compose_path, 'r') as f:
            content = f.read()
            
            # Check for required services
            assert "smartcloudops-app:" in content
            assert "postgres:" in content
            assert "redis:" in content
            assert "prometheus:" in content
            assert "grafana:" in content

    def test_docker_compose_networks(self):
        """Test Docker Compose network configuration."""
        compose_path = "docker/docker-compose.yml"
        
        with open(compose_path, 'r') as f:
            content = f.read()
            
            # Check for network configuration
            assert "networks:" in content
            assert "smartcloudops-network:" in content


class TestOverallSecurity:
    """Test overall security improvements."""

    def test_validation_utilities_available(self):
        """Test that validation utilities are available."""
        from app.utils.validation import InputValidator, ValidationError
        assert InputValidator is not None
        assert ValidationError is not None

    def test_response_utilities_available(self):
        """Test that response utilities are available."""
        from app.utils.response import APIResponse
        assert APIResponse is not None

    def test_ml_service_file_exists(self):
        """Test that ML service file exists and is not empty."""
        ml_service_path = "app/services/ml_service.py"
        assert os.path.exists(ml_service_path)
        
        with open(ml_service_path, 'r') as f:
            content = f.read()
            assert len(content) > 0
            assert "class MLService" in content

    def test_main_app_refactored(self):
        """Test that main app has been refactored."""
        main_path = "app/main.py"
        assert os.path.exists(main_path)
        
        with open(main_path, 'r') as f:
            content = f.read()
            # Check for refactored structure
            assert "def create_app():" in content
            assert "def register_blueprints(app:" in content
            assert "def register_error_handlers(app:" in content
            assert "APIResponse" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
