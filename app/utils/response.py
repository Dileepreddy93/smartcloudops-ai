#!/usr/bin/env python3
"""
SmartCloudOps AI - Response Utilities
===================================

Standardized response formatting for API endpoints.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from flask import jsonify


def build_success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a standardized success response.

    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        metadata: Additional metadata

    Returns:
        Standardized success response dictionary
    """
    response = {
        "status": "success",
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status_code": status_code,
    }

    if data is not None:
        response["data"] = data

    if metadata:
        response["metadata"] = metadata

    return response


def build_error_response(
    message: str,
    error_code: str = "GENERAL_ERROR",
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a standardized error response.

    Args:
        message: Error message
        error_code: Error code for client handling
        status_code: HTTP status code
        details: Additional error details
        request_id: Request ID for tracking

    Returns:
        Standardized error response dictionary
    """
    response = {
        "status": "error",
        "message": message,
        "error_code": error_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status_code": status_code,
    }

    if details:
        response["details"] = details

    if request_id:
        response["request_id"] = request_id

    return response


def build_ml_prediction_response(
    prediction_result: Dict[str, Any],
    metrics: Dict[str, Any],
    model_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a standardized ML prediction response.

    Args:
        prediction_result: ML model prediction result
        metrics: Input metrics used for prediction
        model_info: Information about the model used

    Returns:
        Standardized ML prediction response
    """
    response = {
        "status": "success",
        "message": "ML prediction completed successfully",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "prediction": prediction_result,
            "input_metrics": metrics,
            "model_info": model_info or {},
        },
    }

    return response


def build_health_check_response(
    components: Dict[str, Any],
    overall_status: str = "healthy",
    version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a standardized health check response.

    Args:
        components: Health status of individual components
        overall_status: Overall system health status
        version: Application version

    Returns:
        Standardized health check response
    """
    response = {
        "status": "success",
        "message": "Health check completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"overall_status": overall_status, "components": components},
    }

    if version:
        response["data"]["version"] = version

    return response


def build_metrics_response(
    metrics: Dict[str, Any],
    collection_time: Optional[str] = None,
    source: str = "system",
) -> Dict[str, Any]:
    """
    Build a standardized metrics response.

    Args:
        metrics: System metrics data
        collection_time: When metrics were collected
        source: Source of the metrics

    Returns:
        Standardized metrics response
    """
    response = {
        "status": "success",
        "message": "Metrics retrieved successfully",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"metrics": metrics, "source": source},
    }

    if collection_time:
        response["data"]["collection_time"] = collection_time

    return response


def build_remediation_response(
    action: str,
    success: bool,
    details: Optional[Dict[str, Any]] = None,
    execution_time: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Build a standardized remediation action response.

    Args:
        action: Remediation action performed
        success: Whether the action was successful
        details: Additional details about the action
        execution_time: Time taken to execute the action

    Returns:
        Standardized remediation response
    """
    response = {
        "status": "success" if success else "error",
        "message": f"Remediation action '{action}' {'completed successfully' if success else 'failed'}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"action": action, "success": success},
    }

    if details:
        response["data"]["details"] = details

    if execution_time is not None:
        response["data"]["execution_time_seconds"] = execution_time

    return response


def build_pagination_response(data: list, page: int, per_page: int, total: int, endpoint: str) -> Dict[str, Any]:
    """
    Build a standardized paginated response.

    Args:
        data: List of items for current page
        page: Current page number
        per_page: Items per page
        total: Total number of items
        endpoint: API endpoint for pagination

    Returns:
        Standardized paginated response
    """
    total_pages = (total + per_page - 1) // per_page

    response = {
        "status": "success",
        "message": "Data retrieved successfully",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }

    # Add pagination links
    base_url = f"/api/v1/{endpoint}"
    response["pagination"]["links"] = {
        "self": f"{base_url}?page={page}&per_page={per_page}",
        "first": f"{base_url}?page=1&per_page={per_page}",
        "last": f"{base_url}?page={total_pages}&per_page={per_page}",
    }

    if page < total_pages:
        response["pagination"]["links"]["next"] = f"{base_url}?page={page + 1}&per_page={per_page}"

    if page > 1:
        response["pagination"]["links"]["prev"] = f"{base_url}?page={page - 1}&per_page={per_page}"

    return response


def json_response(data: Dict[str, Any], status_code: int = 200) -> tuple:
    """
    Create a Flask JSON response with proper headers.

    Args:
        data: Response data
        status_code: HTTP status code

    Returns:
        Flask response tuple (response, status_code)
    """
    response = jsonify(data)
    response.status_code = status_code

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


def error_response(
    message: str,
    error_code: str = "GENERAL_ERROR",
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> tuple:
    """
    Create a standardized error response for Flask.

    Args:
        message: Error message
        error_code: Error code
        status_code: HTTP status code
        details: Additional error details
        request_id: Request ID for tracking

    Returns:
        Flask error response tuple
    """
    error_data = build_error_response(
        message=message,
        error_code=error_code,
        status_code=status_code,
        details=details,
        request_id=request_id,
    )

    return json_response(error_data, status_code)


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
    metadata: Optional[Dict[str, Any]] = None,
) -> tuple:
    """
    Create a standardized success response for Flask.

    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        metadata: Additional metadata

    Returns:
        Flask success response tuple
    """
    success_data = build_success_response(data=data, message=message, status_code=status_code, metadata=metadata)

    return json_response(success_data, status_code)
