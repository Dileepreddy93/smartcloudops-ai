#!/usr/bin/env python3
"""
SmartCloudOps AI - Validation Utilities
=====================================

Validation functions for API inputs, ML metrics, and data integrity.
"""


import logging
import time
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def validate_ml_metrics(metrics: Dict[str, Any]) -> Dict[str, float]:
    """
    Validate and sanitize ML metrics input.

    Args:
        metrics: Dictionary of metrics to validate

    Returns:
        Validated metrics dictionary with float values

    Raises:
        ValueError: If metrics are invalid
    """
    if not isinstance(metrics, dict):
        raise ValueError("Metrics must be a dictionary")

    validated_metrics = {}

    # Define expected metrics with their validation rules
    metric_rules = {
        "cpu_usage": {"min": 0.0, "max": 100.0, "default": 0.0},
        "memory_usage": {"min": 0.0, "max": 100.0, "default": 0.0},
        "disk_usage": {"min": 0.0, "max": 100.0, "default": 0.0},
        "network_io": {"min": 0.0, "max": 1000.0, "default": 0.0},
        "load_1m": {"min": 0.0, "max": 100.0, "default": 0.0},
        "load_5m": {"min": 0.0, "max": 100.0, "default": 0.0},
        "load_15m": {"min": 0.0, "max": 100.0, "default": 0.0},
        "response_time": {"min": 0.0, "max": 10000.0, "default": 0.0},
    }

    for metric_name, rules in metric_rules.items():
        value = metrics.get(metric_name)

        if value is None:
            validated_metrics[metric_name] = rules["default"]
            continue

        try:
            float_value = float(value)

            # Check for infinite or NaN values
            if not (float("inf") > float_value > float("-inf")):
                logger.warning(f"Invalid value for {metric_name}: {value}, using default")
                validated_metrics[metric_name] = rules["default"]
                continue

            # Apply range validation
            if float_value < rules["min"] or float_value > rules["max"]:
                logger.warning(f"Value for {metric_name} out of range [{rules['min']}, {rules['max']}]: {float_value}")
                # Clamp to valid range
                float_value = max(rules["min"], min(rules["max"], float_value))

            validated_metrics[metric_name] = float_value

        except (ValueError, TypeError):
            logger.warning(f"Invalid value for {metric_name}: {value}, using default")
            validated_metrics[metric_name] = rules["default"]

    return validated_metrics


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format.

    Args:
        api_key: API key to validate

    Returns:
        True if valid, False otherwise
    """
    if not api_key or not isinstance(api_key, str):
        return False

    # Check if it starts with sk- and has sufficient length
    if not api_key.startswith("sk-"):
        return False

    if len(api_key) < 32:
        return False

    # Check for valid characters (alphanumeric and hyphens)
    if not re.match(r"^sk-[a-zA-Z0-9-]+$", api_key):
        return False

    return True


def validate_jwt_token(token: str) -> bool:
    """
    Validate JWT token format.

    Args:
        token: JWT token to validate

    Returns:
        True if valid format, False otherwise
    """
    if not token or not isinstance(token, str):
        return False

    # JWT tokens have 3 parts separated by dots
    parts = token.split(".")
    if len(parts) != 3:
        return False

    # Each part should be base64 encoded
    for part in parts:
        if not part or not re.match(r"^[A-Za-z0-9+/=]+$", part):
            return False

    return True


def validate_user_input(input_data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """
    Validate user input data.

    Args:
        input_data: Input data to validate
        required_fields: List of required field names

    Returns:
        Validated input data

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(input_data, dict):
        raise ValueError("Input data must be a dictionary")

    # Check required fields
    missing_fields = [field for field in required_fields if field not in input_data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    # Validate field types and values
    validated_data = {}

    for field, value in input_data.items():
        if field in required_fields:
            # Basic type validation
            if value is None:
                raise ValueError(f"Field '{field}' cannot be None")

            # String fields
            if field in ["username", "email", "role"]:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"Field '{field}' must be a non-empty string")
                validated_data[field] = value.strip()

            # Numeric fields
            elif field in ["cpu_threshold", "memory_threshold", "disk_threshold"]:
                try:
                    float_value = float(value)
                    if float_value < 0 or float_value > 100:
                        raise ValueError(f"Field '{field}' must be between 0 and 100")
                    validated_data[field] = float_value
                except (ValueError, TypeError):
                    raise ValueError(f"Field '{field}' must be a valid number")

            # Boolean fields
            elif field in ["enabled", "auto_remediate"]:
                if isinstance(value, bool):
                    validated_data[field] = value
                elif isinstance(value, str):
                    validated_data[field] = value.lower() in ["true", "1", "yes", "on"]
                else:
                    validated_data[field] = bool(value)

            # List fields
            elif field in ["permissions", "tags"]:
                if isinstance(value, list):
                    validated_data[field] = [str(item) for item in value if item]
                elif isinstance(value, str):
                    validated_data[field] = [item.strip() for item in value.split(",") if item.strip()]
                else:
                    raise ValueError(f"Field '{field}' must be a list or comma-separated string")

            # Default: keep as is
            else:
                validated_data[field] = value

    return validated_data


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False

    # Basic email regex pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Returns:
        Dictionary with validation results
    """
    if not password or not isinstance(password, str):
        return {"valid": False, "errors": ["Password must be a non-empty string"]}

    errors = []
    warnings = []

    # Check minimum length
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    elif len(password) < 12:
        warnings.append("Consider using a password at least 12 characters long")

    # Check for uppercase letters
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")

    # Check for lowercase letters
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")

    # Check for numbers
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number")

    # Check for special characters
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        warnings.append("Consider using special characters for better security")

    # Check for common patterns
    common_patterns = ["password", "123456", "qwerty", "admin"]
    if any(pattern in password.lower() for pattern in common_patterns):
        errors.append("Password contains common patterns that are not secure")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "strength_score": max(0, 10 - len(errors) - len(warnings)),
    }


def validate_timestamp(timestamp: str) -> bool:
    """
    Validate ISO timestamp format.

    Args:
        timestamp: Timestamp string to validate

    Returns:
        True if valid, False otherwise
    """
    if not timestamp or not isinstance(timestamp, str):
        return False

    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def sanitize_string(input_string: str, max_length: int = 1000) -> str:
    """
    Sanitize string input.

    Args:
        input_string: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not input_string:
        return ""

    # Convert to string if needed
    string_value = str(input_string)

    # Remove null bytes and control characters
    string_value = "".join(char for char in string_value if ord(char) >= 32 or char in "\n\r\t")

    # Truncate if too long
    if len(string_value) > max_length:
        string_value = string_value[:max_length]

    return string_value.strip()


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate data against a JSON schema.

    Args:
        data: Data to validate
        schema: JSON schema definition

    Returns:
        Validation result dictionary

    Raises:
        ValueError: If validation fails
    """
    # This is a simplified schema validation
    # In production, use a proper JSON schema library like jsonschema

    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")

    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dictionary")

    errors = []

    # Check required fields
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Check field types
    properties = schema.get("properties", {})
    for field, value in data.items():
        if field in properties:
            field_schema = properties[field]
            expected_type = field_schema.get("type")

            if expected_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{field}' must be a string")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' must be a number")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(f"Field '{field}' must be a boolean")
            elif expected_type == "array" and not isinstance(value, list):
                errors.append(f"Field '{field}' must be an array")
            elif expected_type == "object" and not isinstance(value, dict):
                errors.append(f"Field '{field}' must be an object")

    if errors:
        raise ValueError(f"Validation errors: {'; '.join(errors)}")

    return data
