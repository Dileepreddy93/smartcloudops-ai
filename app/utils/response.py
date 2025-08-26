#!/usr/bin/env python3
"""
SmartCloudOps AI - Standardized Response Utilities
================================================

Standardized API response formatting and error handling.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from flask import jsonify, Response

logger = logging.getLogger(__name__)


class APIResponse:
    """Standardized API response formatter."""

    @staticmethod
    def success(data: Any = None, message: str = "Success", 
                status_code: int = 200, meta: Optional[Dict] = None) -> Response:
        """
        Create a standardized success response.
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            meta: Additional metadata
            
        Returns:
            Flask Response object
        """
        response_data = {
            "status": "success",
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        if meta:
            response_data["meta"] = meta
            
        return jsonify(response_data), status_code

    @staticmethod
    def error(message: str, status_code: int = 400, 
              error_code: Optional[str] = None, details: Optional[Dict] = None) -> Response:
        """
        Create a standardized error response.
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Optional error code for client handling
            details: Additional error details
            
        Returns:
            Flask Response object
        """
        response_data = {
            "status": "error",
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "error_code": error_code
        }
        
        if details:
            response_data["details"] = details
            
        return jsonify(response_data), status_code

    @staticmethod
    def validation_error(errors: List[str], field_errors: Optional[Dict] = None) -> Response:
        """
        Create a validation error response.
        
        Args:
            errors: List of validation error messages
            field_errors: Field-specific validation errors
            
        Returns:
            Flask Response object
        """
        details = {"errors": errors}
        if field_errors:
            details["field_errors"] = field_errors
            
        return APIResponse.error(
            message="Validation failed",
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details
        )

    @staticmethod
    def not_found(resource: str = "Resource") -> Response:
        """Create a not found response."""
        return APIResponse.error(
            message=f"{resource} not found",
            status_code=404,
            error_code="NOT_FOUND"
        )

    @staticmethod
    def unauthorized(message: str = "Authentication required") -> Response:
        """Create an unauthorized response."""
        return APIResponse.error(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED"
        )

    @staticmethod
    def forbidden(message: str = "Insufficient permissions") -> Response:
        """Create a forbidden response."""
        return APIResponse.error(
            message=message,
            status_code=403,
            error_code="FORBIDDEN"
        )

    @staticmethod
    def internal_error(message: str = "Internal server error", 
                      error_id: Optional[str] = None) -> Response:
        """Create an internal server error response."""
        details = {}
        if error_id:
            details["error_id"] = error_id
            
        return APIResponse.error(
            message=message,
            status_code=500,
            error_code="INTERNAL_ERROR",
            details=details
        )

    @staticmethod
    def service_unavailable(service: str = "Service") -> Response:
        """Create a service unavailable response."""
        return APIResponse.error(
            message=f"{service} temporarily unavailable",
            status_code=503,
            error_code="SERVICE_UNAVAILABLE"
        )

    @staticmethod
    def rate_limited(retry_after: Optional[int] = None) -> Response:
        """Create a rate limit exceeded response."""
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
            
        return APIResponse.error(
            message="Rate limit exceeded",
            status_code=429,
            error_code="RATE_LIMITED",
            details=details
        )


class ErrorHandler:
    """Centralized error handling for the application."""

    @staticmethod
    def handle_validation_error(error) -> Response:
        """Handle validation errors."""
        logger.warning(f"Validation error: {error}")
        return APIResponse.validation_error([str(error)])

    @staticmethod
    def handle_authentication_error(error) -> Response:
        """Handle authentication errors."""
        logger.warning(f"Authentication error: {error}")
        return APIResponse.unauthorized(str(error))

    @staticmethod
    def handle_permission_error(error) -> Response:
        """Handle permission errors."""
        logger.warning(f"Permission error: {error}")
        return APIResponse.forbidden(str(error))

    @staticmethod
    def handle_not_found_error(error) -> Response:
        """Handle not found errors."""
        logger.info(f"Resource not found: {error}")
        return APIResponse.not_found(str(error))

    @staticmethod
    def handle_internal_error(error) -> Response:
        """Handle internal server errors."""
        error_id = f"ERR_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.error(f"Internal error {error_id}: {error}", exc_info=True)
        return APIResponse.internal_error(
            message="An unexpected error occurred",
            error_id=error_id
        )

    @staticmethod
    def handle_service_error(error, service_name: str = "Service") -> Response:
        """Handle service errors."""
        logger.error(f"Service error in {service_name}: {error}")
        return APIResponse.service_unavailable(service_name)

    @staticmethod
    def handle_rate_limit_error(error) -> Response:
        """Handle rate limit errors."""
        logger.warning(f"Rate limit exceeded: {error}")
        return APIResponse.rate_limited()

    @staticmethod
    def handle_ml_error(error) -> Response:
        """Handle ML service errors."""
        logger.error(f"ML service error: {error}")
        return APIResponse.service_unavailable("ML Service")

    @staticmethod
    def handle_database_error(error) -> Response:
        """Handle database errors."""
        logger.error(f"Database error: {error}")
        return APIResponse.service_unavailable("Database")


class ResponseFormatter:
    """Format specific response types."""

    @staticmethod
    def format_health_check(status: str, details: Optional[Dict] = None) -> Response:
        """Format health check response."""
        data = {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
        if details:
            data.update(details)
            
        return APIResponse.success(data=data, message="Health check completed")

    @staticmethod
    def format_metrics(metrics: Dict[str, Any]) -> Response:
        """Format metrics response."""
        data = {
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return APIResponse.success(data=data, message="Metrics retrieved successfully")

    @staticmethod
    def format_ml_prediction(prediction: Dict[str, Any]) -> Response:
        """Format ML prediction response."""
        if "error" in prediction:
            return APIResponse.error(
                message=prediction["error"],
                status_code=422,
                error_code="ML_PREDICTION_ERROR"
            )
            
        return APIResponse.success(
            data=prediction,
            message="Anomaly detection completed"
        )

    @staticmethod
    def format_chatops_response(response: str, intent: Optional[str] = None,
                               confidence: Optional[float] = None) -> Response:
        """Format ChatOps response."""
        data = {
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if intent:
            data["intent"] = intent
        if confidence is not None:
            data["confidence"] = confidence
            
        return APIResponse.success(
            data=data,
            message="ChatOps command processed successfully"
        )

    @staticmethod
    def format_logs(logs: str, log_type: str = "application") -> Response:
        """Format logs response."""
        data = {
            "logs": logs,
            "log_type": log_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return APIResponse.success(
            data=data,
            message="Logs retrieved successfully"
        )

    @staticmethod
    def format_list_response(items: List[Any], total: Optional[int] = None,
                           page: Optional[int] = None, per_page: Optional[int] = None) -> Response:
        """Format list response with pagination."""
        data = {
            "items": items,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        meta = {}
        if total is not None:
            meta["total"] = total
        if page is not None:
            meta["page"] = page
        if per_page is not None:
            meta["per_page"] = per_page
            
        return APIResponse.success(
            data=data,
            message="Data retrieved successfully",
            meta=meta
        )


# Convenience functions for common responses
def success_response(data: Any = None, message: str = "Success") -> Response:
    """Create a success response."""
    return APIResponse.success(data=data, message=message)


def error_response(message: str, status_code: int = 400) -> Response:
    """Create an error response."""
    return APIResponse.error(message=message, status_code=status_code)


def validation_error_response(errors: List[str]) -> Response:
    """Create a validation error response."""
    return APIResponse.validation_error(errors)


def not_found_response(resource: str = "Resource") -> Response:
    """Create a not found response."""
    return APIResponse.not_found(resource)


def unauthorized_response(message: str = "Authentication required") -> Response:
    """Create an unauthorized response."""
    return APIResponse.unauthorized(message)


def forbidden_response(message: str = "Insufficient permissions") -> Response:
    """Create a forbidden response."""
    return APIResponse.forbidden(message)


def internal_error_response(message: str = "Internal server error") -> Response:
    """Create an internal error response."""
    return APIResponse.internal_error(message)


def service_unavailable_response(service: str = "Service") -> Response:
    """Create a service unavailable response."""
    return APIResponse.service_unavailable(service)
