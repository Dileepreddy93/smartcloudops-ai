#!/usr/bin/env python3
"""
SmartCloudOps AI - Secure API Validation & Response Module
=========================================================

Enterprise-grade input validation, output sanitization, and DTO management.
"""

import html
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error for API inputs."""

    pass


class SecurityError(Exception):
    """Security-related error."""

    pass


class ErrorCode(Enum):
    """Standardized error codes for API responses."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INVALID_FORMAT = "INVALID_FORMAT"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    PARAMETER_OUT_OF_RANGE = "PARAMETER_OUT_OF_RANGE"


@dataclass
class APIResponse:
    """Standardized API response structure."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    message: Optional[str] = None
    timestamp: str = None
    request_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                result[key] = value
        return result


@dataclass
class StatusDTO:
    """Data Transfer Object for system status."""

    status: str
    version: str
    environment: str
    timestamp: str
    features_available: int
    auth_enabled: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MLPredictionDTO:
    """Data Transfer Object for ML predictions."""

    anomaly_detected: bool
    confidence_score: float
    severity_level: str
    prediction_id: str
    timestamp: str
    model_version: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HealthCheckDTO:
    """Data Transfer Object for health check responses."""

    status: str
    engine_type: str
    components_healthy: int
    components_total: int
    last_check: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SecureValidator:
    """Comprehensive input validation and sanitization."""

    # Regex patterns for validation
    PATTERNS = {
        "api_key": re.compile(r"^[a-zA-Z0-9_-]{32,128}$"),
        "username": re.compile(r"^[a-zA-Z0-9_-]{3,32}$"),
        "metric_name": re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$"),
        "uuid": re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        ),
        "safe_string": re.compile(r"^[a-zA-Z0-9\s\-_.,!?()]{1,200}$"),
    }

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),
        re.compile(r"expression\s*\(", re.IGNORECASE),
        re.compile(r"url\s*\(", re.IGNORECASE),
        re.compile(r"@import", re.IGNORECASE),
        re.compile(r"vbscript:", re.IGNORECASE),
        re.compile(r"data:.*base64", re.IGNORECASE),
    ]

    @classmethod
    def validate_json_structure(
        cls, data: Any, required_fields: List[str], optional_fields: List[str] = None
    ) -> bool:
        """Validate JSON structure with required and optional fields."""
        if not isinstance(data, dict):
            raise ValidationError("Request body must be a JSON object")

        # Check required fields
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)

        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        # Check for unexpected fields
        allowed_fields = set(required_fields)
        if optional_fields:
            allowed_fields.update(optional_fields)

        unexpected_fields = set(data.keys()) - allowed_fields
        if unexpected_fields:
            logger.warning(f"Unexpected fields in request: {unexpected_fields}")

        return True

    @classmethod
    def sanitize_text(
        cls, text: str, max_length: int = 1000, allow_html: bool = False
    ) -> str:
        """Comprehensive text sanitization."""
        if not isinstance(text, str):
            raise ValidationError("Input must be a string")

        if len(text) > max_length:
            raise ValidationError(
                f"Input exceeds maximum length of {max_length} characters"
            )

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern.search(text):
                raise SecurityError("Input contains potentially dangerous content")

        # Remove null bytes and control characters (except whitespace)
        text = "".join(char for char in text if ord(char) >= 32 or char.isspace())

        # HTML escape if not allowing HTML
        if not allow_html:
            text = html.escape(text, quote=True)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    @classmethod
    def validate_metrics(cls, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Validate and sanitize ML metrics input."""
        if not isinstance(metrics, dict):
            raise ValidationError("Metrics must be a JSON object")

        required_metrics = ["cpu_usage", "memory_usage", "disk_usage", "load_1m"]
        optional_metrics = [
            "load_5m",
            "load_15m",
            "network_rx",
            "network_tx",
            "disk_io_read",
            "disk_io_write",
            "response_time",
            "error_rate",
        ]

        validated_metrics = {}

        # Validate required metrics
        for metric in required_metrics:
            if metric not in metrics:
                raise ValidationError(f"Missing required metric: {metric}")

            value = metrics[metric]
            validated_value = cls._validate_numeric_value(
                value, metric, min_val=0, max_val=100 if metric != "load_1m" else 1000
            )
            validated_metrics[metric] = validated_value

        # Validate optional metrics
        for metric in optional_metrics:
            if metric in metrics:
                value = metrics[metric]
                if value is not None:
                    validated_value = cls._validate_numeric_value(
                        value, metric, min_val=0, max_val=999999999
                    )
                    validated_metrics[metric] = validated_value

        # Check for unexpected metrics
        all_allowed = set(required_metrics + optional_metrics)
        unexpected = set(metrics.keys()) - all_allowed
        if unexpected:
            logger.warning(f"Unexpected metrics in request: {unexpected}")

        return validated_metrics

    @classmethod
    def _validate_numeric_value(
        cls, value: Any, field_name: str, min_val: float = None, max_val: float = None
    ) -> float:
        """Validate and convert numeric values."""
        try:
            # Convert to float
            if isinstance(value, str):
                # Check for dangerous string patterns
                if not re.match(r"^-?\d*\.?\d+([eE][+-]?\d+)?$", value.strip()):
                    raise ValueError(f"Invalid numeric format for {field_name}")
                float_value = float(value)
            else:
                float_value = float(value)

            # Check for infinite or NaN values
            if not (-float("inf") < float_value < float("inf")):
                raise ValueError(f"Invalid numeric value for {field_name}: {value}")

            # Check range
            if min_val is not None and float_value < min_val:
                raise ValidationError(
                    f"{field_name} must be >= {min_val}, got {float_value}"
                )

            if max_val is not None and float_value > max_val:
                raise ValidationError(
                    f"{field_name} must be <= {max_val}, got {float_value}"
                )

            return float_value

        except (ValueError, TypeError):
            raise ValidationError(f"Invalid numeric value for {field_name}: {value}")

    @classmethod
    def validate_pagination(
        cls, page: Any = None, limit: Any = None, max_limit: int = 100
    ) -> tuple[int, int]:
        """Validate pagination parameters."""
        # Validate page
        if page is not None:
            try:
                page_int = int(page)
                if page_int < 1:
                    raise ValidationError("Page must be >= 1")
            except (ValueError, TypeError):
                raise ValidationError("Page must be a valid integer")
        else:
            page_int = 1

        # Validate limit
        if limit is not None:
            try:
                limit_int = int(limit)
                if limit_int < 1:
                    raise ValidationError("Limit must be >= 1")
                if limit_int > max_limit:
                    raise ValidationError(f"Limit must be <= {max_limit}")
            except (ValueError, TypeError):
                raise ValidationError("Limit must be a valid integer")
        else:
            limit_int = 20  # Default limit

        return page_int, limit_int

    @classmethod
    def validate_pattern(cls, value: str, pattern_name: str) -> bool:
        """Validate input against predefined patterns."""
        if pattern_name not in cls.PATTERNS:
            raise ValueError(f"Unknown validation pattern: {pattern_name}")

        pattern = cls.PATTERNS[pattern_name]
        if not pattern.match(value):
            raise ValidationError(f"Invalid format for {pattern_name}")

        return True


class ResponseBuilder:
    """Secure response builder with data sanitization."""

    @staticmethod
    def success_response(
        data: Dict[str, Any], request_id: str = None
    ) -> Dict[str, Any]:
        """Build successful API response."""
        response = APIResponse(
            success=True,
            data=ResponseBuilder._sanitize_output_data(data),
            request_id=request_id,
        )
        return response.to_dict()

    @staticmethod
    def error_response(
        error_code: ErrorCode, message: str, details: str = None, request_id: str = None
    ) -> Dict[str, Any]:
        """Build error API response."""
        response = APIResponse(
            success=False,
            error=error_code.value,
            message=message,
            request_id=request_id,
        )

        # Only add details in development mode
        if details and logger.level <= logging.DEBUG:
            response.data = {"details": details}

        return response.to_dict()

    @staticmethod
    def _sanitize_output_data(data: Any) -> Any:
        """Recursively sanitize output data to prevent information disclosure."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Filter out sensitive keys
                if ResponseBuilder._is_sensitive_key(key):
                    continue
                sanitized[key] = ResponseBuilder._sanitize_output_data(value)
            return sanitized

        elif isinstance(data, list):
            return [ResponseBuilder._sanitize_output_data(item) for item in data]

        elif isinstance(data, str):
            # Remove any potential information disclosure
            return ResponseBuilder._sanitize_string_output(data)

        else:
            return data

    @staticmethod
    def _is_sensitive_key(key: str) -> bool:
        """Check if a key contains sensitive information."""
        sensitive_patterns = [
            "password",
            "secret",
            "key",
            "token",
            "private",
            "internal",
            "debug",
            "trace",
            "stack",
            "path",
            "_id",
            "hash",
            "salt",
            "credential",
        ]

        key_lower = key.lower()
        return any(pattern in key_lower for pattern in sensitive_patterns)

    @staticmethod
    def _sanitize_string_output(text: str) -> str:
        """Sanitize string output to prevent information disclosure."""
        # Remove file paths
        text = re.sub(r"/[a-zA-Z0-9_/.-]*\.(py|json|conf|log)", "[PATH_REMOVED]", text)

        # Remove IP addresses (keep localhost patterns)
        text = re.sub(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", "[IP_REMOVED]", text)

        # Remove potential SQL/NoSQL queries
        text = re.sub(
            r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)\b.*",
            "[QUERY_REMOVED]",
            text,
            flags=re.IGNORECASE,
        )

        return text


# Export functions for use in main application
def validate_request_data(
    data: Any, required_fields: List[str], optional_fields: List[str] = None
) -> bool:
    """Public interface for request validation."""
    return SecureValidator.validate_json_structure(
        data, required_fields, optional_fields
    )


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Public interface for input sanitization."""
    return SecureValidator.sanitize_text(text, max_length)


def validate_ml_metrics(metrics: Dict[str, Any]) -> Dict[str, float]:
    """Public interface for metrics validation."""
    return SecureValidator.validate_metrics(metrics)


def build_success_response(
    data: Dict[str, Any], request_id: str = None
) -> Dict[str, Any]:
    """Public interface for success responses."""
    return ResponseBuilder.success_response(data, request_id)


def build_error_response(
    error_code: ErrorCode, message: str, details: str = None, request_id: str = None
) -> Dict[str, Any]:
    """Public interface for error responses."""
    return ResponseBuilder.error_response(error_code, message, details, request_id)


__all__ = [
    "ValidationError",
    "SecurityError",
    "ErrorCode",
    "APIResponse",
    "StatusDTO",
    "MLPredictionDTO",
    "HealthCheckDTO",
    "SecureValidator",
    "ResponseBuilder",
    "validate_request_data",
    "sanitize_input",
    "validate_ml_metrics",
    "build_success_response",
    "build_error_response",
]
