#!/usr/bin/env python3
"""
SmartCloudOps AI - Exception Hierarchy
======================================

Comprehensive exception classes for proper error handling.
"""

from typing import Any, Dict, Optional


class SmartCloudOpsException(Exception):
    """Base exception for all SmartCloudOps AI errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(SmartCloudOpsException):
    """Raised when input validation fails."""

    pass


class AuthenticationError(SmartCloudOpsException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(SmartCloudOpsException):
    """Raised when authorization fails."""

    pass


class DatabaseError(SmartCloudOpsException):
    """Raised when database operations fail."""

    pass


class MLServiceError(SmartCloudOpsException):
    """Raised when ML service operations fail."""

    pass


class ChatOpsServiceError(SmartCloudOpsException):
    """Raised when ChatOps service operations fail."""

    pass


class RemediationServiceError(SmartCloudOpsException):
    """Raised when remediation service operations fail."""

    pass


class MonitoringServiceError(SmartCloudOpsException):
    """Raised when monitoring service operations fail."""

    pass


class IntegrationServiceError(SmartCloudOpsException):
    """Raised when external service integration fails."""

    pass


class ConfigurationError(SmartCloudOpsException):
    """Raised when configuration is invalid or missing."""

    pass


class SecretsManagerError(SmartCloudOpsException):
    """Raised when secrets management operations fail."""

    pass


class RateLimitError(SmartCloudOpsException):
    """Raised when rate limits are exceeded."""

    pass


class ResourceNotFoundError(SmartCloudOpsException):
    """Raised when a requested resource is not found."""

    pass


class ServiceUnavailableError(SmartCloudOpsException):
    """Raised when a service is temporarily unavailable."""

    pass


class ExternalAPIError(SmartCloudOpsException):
    """Raised when external API calls fail."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
    ):
        super().__init__(
            message,
            "ExternalAPIError",
            {"status_code": status_code, "response_data": response_data},
        )
        self.status_code = status_code
        self.response_data = response_data


class ModelTrainingError(SmartCloudOpsException):
    """Raised when ML model training fails."""

    pass


class ModelInferenceError(SmartCloudOpsException):
    """Raised when ML model inference fails."""

    pass


class DataProcessingError(SmartCloudOpsException):
    """Raised when data processing operations fail."""

    pass


class LoggingError(SmartCloudOpsException):
    """Raised when logging operations fail."""

    pass


class MetricsError(SmartCloudOpsException):
    """Raised when metrics collection or processing fails."""

    pass


class AlertingError(SmartCloudOpsException):
    """Raised when alerting operations fail."""

    pass


class BackupError(SmartCloudOpsException):
    """Raised when backup operations fail."""

    pass


class DeploymentError(SmartCloudOpsException):
    """Raised when deployment operations fail."""

    pass


class HealthCheckError(SmartCloudOpsException):
    """Raised when health checks fail."""

    pass


# HTTP status code mappings
HTTP_STATUS_CODES = {
    ValidationError: 400,
    AuthenticationError: 401,
    AuthorizationError: 403,
    ResourceNotFoundError: 404,
    RateLimitError: 429,
    ServiceUnavailableError: 503,
    ExternalAPIError: 502,
    ConfigurationError: 500,
    DatabaseError: 500,
    MLServiceError: 500,
    ChatOpsServiceError: 500,
    RemediationServiceError: 500,
    MonitoringServiceError: 500,
    IntegrationServiceError: 500,
    SecretsManagerError: 500,
    ModelTrainingError: 500,
    ModelInferenceError: 500,
    DataProcessingError: 500,
    LoggingError: 500,
    MetricsError: 500,
    AlertingError: 500,
    BackupError: 500,
    DeploymentError: 500,
    HealthCheckError: 500,
    SmartCloudOpsException: 500,
}


def get_http_status_code(exception: SmartCloudOpsException) -> int:
    """Get HTTP status code for an exception."""
    return HTTP_STATUS_CODES.get(type(exception), 500)


def handle_exception(exception: Exception) -> tuple[Dict[str, Any], int]:
    """Handle an exception and return appropriate response."""
    if isinstance(exception, SmartCloudOpsException):
        return exception.to_dict(), get_http_status_code(exception)

    # Handle unexpected exceptions
    error = SmartCloudOpsException(
        message="An unexpected error occurred",
        error_code="InternalServerError",
        details={"original_error": str(exception)},
    )
    return error.to_dict(), 500
