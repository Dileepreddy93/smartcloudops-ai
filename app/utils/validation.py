#!/usr/bin/env python3
"""
SmartCloudOps AI - Input Validation Utilities
===========================================

Comprehensive input validation and sanitization for security and data integrity.
"""

import re
import string
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import numpy as np


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class InputValidator:
    """Comprehensive input validation and sanitization."""

    # Validation patterns
    PATTERNS = {
        "api_key": r"^sk-[a-zA-Z0-9]{20,}$",
        "jwt_token": r"^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$",
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "url": r"^https?://[^\s/$.?#].[^\s]*$",
        "ip_address": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
        "hostname": r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$",
        "port": r"^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$",
    }

    # Limits
    LIMITS = {
        "max_string_length": 2048,
        "max_list_length": 1000,
        "max_dict_keys": 100,
        "max_numeric_value": 1e6,
        "min_numeric_value": -1e6,
        "max_file_size_mb": 10,
    }

    @staticmethod
    def sanitize_string(value: str, max_len: int = None, allowed_chars: str = None) -> str:
        """
        Sanitize a string input.
        
        Args:
            value: Input string to sanitize
            max_len: Maximum allowed length
            allowed_chars: String of allowed characters
            
        Returns:
            Sanitized string
            
        Raises:
            ValidationError: If input is invalid
        """
        if not isinstance(value, str):
            raise ValidationError("Input must be a string")

        # Remove null bytes and control characters
        value = "".join(char for char in value if ord(char) >= 32 or char in "\n\r\t")

        # Apply length limit
        max_len = max_len or InputValidator.LIMITS["max_string_length"]
        if len(value) > max_len:
            raise ValidationError(f"String too long (max {max_len} characters)")

        # Filter allowed characters if specified
        if allowed_chars:
            value = "".join(char for char in value if char in allowed_chars)

        return value.strip()

    @staticmethod
    def validate_api_key(api_key: str) -> str:
        """Validate API key format."""
        if not isinstance(api_key, str):
            raise ValidationError("API key must be a string")

        api_key = api_key.strip()
        if not re.match(InputValidator.PATTERNS["api_key"], api_key):
            raise ValidationError("Invalid API key format")

        return api_key

    @staticmethod
    def validate_jwt_token(token: str) -> str:
        """Validate JWT token format."""
        if not isinstance(token, str):
            raise ValidationError("JWT token must be a string")

        token = token.strip()
        if not re.match(InputValidator.PATTERNS["jwt_token"], token):
            raise ValidationError("Invalid JWT token format")

        return token

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address format."""
        if not isinstance(email, str):
            raise ValidationError("Email must be a string")

        email = email.strip().lower()
        if not re.match(InputValidator.PATTERNS["email"], email):
            raise ValidationError("Invalid email format")

        return email

    @staticmethod
    def validate_url(url: str, allowed_schemes: List[str] = None) -> str:
        """Validate URL format and scheme."""
        if not isinstance(url, str):
            raise ValidationError("URL must be a string")

        url = url.strip()
        if not re.match(InputValidator.PATTERNS["url"], url):
            raise ValidationError("Invalid URL format")

        # Parse URL to validate scheme
        parsed = urlparse(url)
        allowed_schemes = allowed_schemes or ["http", "https"]
        
        if parsed.scheme not in allowed_schemes:
            raise ValidationError(f"URL scheme must be one of: {', '.join(allowed_schemes)}")

        return url

    @staticmethod
    def validate_ip_address(ip: str) -> str:
        """Validate IP address format."""
        if not isinstance(ip, str):
            raise ValidationError("IP address must be a string")

        ip = ip.strip()
        if not re.match(InputValidator.PATTERNS["ip_address"], ip):
            raise ValidationError("Invalid IP address format")

        return ip

    @staticmethod
    def validate_hostname(hostname: str) -> str:
        """Validate hostname format."""
        if not isinstance(hostname, str):
            raise ValidationError("Hostname must be a string")

        hostname = hostname.strip()
        if not re.match(InputValidator.PATTERNS["hostname"], hostname):
            raise ValidationError("Invalid hostname format")

        return hostname

    @staticmethod
    def validate_port(port: Union[str, int]) -> int:
        """Validate port number."""
        try:
            port_int = int(port)
        except (ValueError, TypeError):
            raise ValidationError("Port must be a valid integer")

        port_str = str(port_int)
        if not re.match(InputValidator.PATTERNS["port"], port_str):
            raise ValidationError("Port must be between 1 and 65535")

        return port_int

    @staticmethod
    def validate_numeric(value: Union[str, int, float], 
                        min_val: float = None, 
                        max_val: float = None) -> float:
        """Validate numeric value within range."""
        try:
            numeric_val = float(value)
        except (ValueError, TypeError):
            raise ValidationError("Value must be numeric")

        min_val = min_val or InputValidator.LIMITS["min_numeric_value"]
        max_val = max_val or InputValidator.LIMITS["max_numeric_value"]

        if not (min_val <= numeric_val <= max_val):
            raise ValidationError(f"Value must be between {min_val} and {max_val}")

        return numeric_val

    @staticmethod
    def validate_percentage(value: Union[str, int, float]) -> float:
        """Validate percentage value (0-100)."""
        return InputValidator.validate_numeric(value, 0.0, 100.0)

    @staticmethod
    def validate_metrics(metrics: Dict[str, Any]) -> Dict[str, float]:
        """Validate system metrics dictionary."""
        if not isinstance(metrics, dict):
            raise ValidationError("Metrics must be a dictionary")

        if len(metrics) > InputValidator.LIMITS["max_dict_keys"]:
            raise ValidationError(f"Too many metrics (max {InputValidator.LIMITS['max_dict_keys']})")

        validated_metrics = {}
        required_metrics = ["cpu_usage", "memory_usage", "disk_usage"]
        optional_metrics = ["network_in", "network_out", "response_time"]

        # Validate required metrics
        for metric in required_metrics:
            if metric not in metrics:
                raise ValidationError(f"Required metric missing: {metric}")
            
            validated_metrics[metric] = InputValidator.validate_percentage(metrics[metric])

        # Validate optional metrics
        for metric in optional_metrics:
            if metric in metrics:
                if metric in ["network_in", "network_out", "response_time"]:
                    validated_metrics[metric] = InputValidator.validate_numeric(metrics[metric], 0.0)
                else:
                    validated_metrics[metric] = InputValidator.validate_percentage(metrics[metric])

        return validated_metrics

    @staticmethod
    def validate_list(value: List[Any], max_length: int = None) -> List[Any]:
        """Validate list input."""
        if not isinstance(value, list):
            raise ValidationError("Input must be a list")

        max_length = max_length or InputValidator.LIMITS["max_list_length"]
        if len(value) > max_length:
            raise ValidationError(f"List too long (max {max_length} items)")

        return value

    @staticmethod
    def validate_dict(value: Dict[str, Any], max_keys: int = None) -> Dict[str, Any]:
        """Validate dictionary input."""
        if not isinstance(value, dict):
            raise ValidationError("Input must be a dictionary")

        max_keys = max_keys or InputValidator.LIMITS["max_dict_keys"]
        if len(value) > max_keys:
            raise ValidationError(f"Dictionary too large (max {max_keys} keys)")

        return value

    @staticmethod
    def validate_file_size(size_bytes: int) -> int:
        """Validate file size."""
        max_size_mb = InputValidator.LIMITS["max_file_size_mb"]
        max_size_bytes = max_size_mb * 1024 * 1024

        if size_bytes > max_size_bytes:
            raise ValidationError(f"File too large (max {max_size_mb}MB)")

        return size_bytes

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for security."""
        if not isinstance(filename, str):
            raise ValidationError("Filename must be a string")

        # Remove path traversal attempts
        filename = filename.replace("..", "").replace("/", "").replace("\\", "")
        
        # Remove dangerous characters
        dangerous_chars = '<>:"|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, "")

        # Limit length
        if len(filename) > 255:
            filename = filename[:255]

        return filename.strip()

    @staticmethod
    def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against JSON schema."""
        # Simple JSON schema validation
        validated_data = {}

        for field, field_schema in schema.items():
            if field not in data:
                if field_schema.get("required", False):
                    raise ValidationError(f"Required field missing: {field}")
                continue

            value = data[field]
            field_type = field_schema.get("type")

            # Type validation
            if field_type == "string":
                validated_data[field] = InputValidator.sanitize_string(
                    value, 
                    max_len=field_schema.get("maxLength"),
                    allowed_chars=field_schema.get("pattern")
                )
            elif field_type == "number":
                validated_data[field] = InputValidator.validate_numeric(
                    value,
                    min_val=field_schema.get("minimum"),
                    max_val=field_schema.get("maximum")
                )
            elif field_type == "integer":
                validated_data[field] = int(InputValidator.validate_numeric(
                    value,
                    min_val=field_schema.get("minimum"),
                    max_val=field_schema.get("maximum")
                ))
            elif field_type == "boolean":
                if not isinstance(value, bool):
                    raise ValidationError(f"Field {field} must be boolean")
                validated_data[field] = value
            elif field_type == "array":
                validated_data[field] = InputValidator.validate_list(
                    value,
                    max_length=field_schema.get("maxItems")
                )
            elif field_type == "object":
                validated_data[field] = InputValidator.validate_dict(
                    value,
                    max_keys=field_schema.get("maxProperties")
                )

        return validated_data


# Common validation schemas
CHATOPS_COMMAND_SCHEMA = {
    "command": {
        "type": "string",
        "required": True,
        "maxLength": 2048
    },
    "user_id": {
        "type": "string",
        "required": False,
        "maxLength": 100
    },
    "context": {
        "type": "object",
        "required": False,
        "maxProperties": 20
    }
}

ML_PREDICTION_SCHEMA = {
    "metrics": {
        "type": "object",
        "required": True,
        "maxProperties": 20
    },
    "model_version": {
        "type": "string",
        "required": False,
        "maxLength": 50
    }
}

AUTH_LOGIN_SCHEMA = {
    "username": {
        "type": "string",
        "required": True,
        "maxLength": 100
    },
    "password": {
        "type": "string",
        "required": True,
        "maxLength": 100
    }
}


# Convenience functions
def sanitize_string(value: str, max_len: int = None) -> str:
    """Sanitize string input."""
    return InputValidator.sanitize_string(value, max_len)


def validate_metrics(metrics: Dict[str, Any]) -> Dict[str, float]:
    """Validate system metrics."""
    return InputValidator.validate_metrics(metrics)


def validate_api_key(api_key: str) -> str:
    """Validate API key."""
    return InputValidator.validate_api_key(api_key)


def validate_json_payload(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Validate JSON payload against schema."""
    return InputValidator.validate_json_schema(data, schema)
