#!/usr/bin/env python3
"""
SmartCloudOps AI - Rate Limiting
===============================

Comprehensive rate limiting system for API protection.
"""

import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, Optional, Tuple

from flask import g, jsonify, request

from app.utils.response import error_response

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiting implementation with sliding window."""

    def __init__(self):
        self.requests = defaultdict(lambda: deque())
        self.limits = {
            "default": {"requests": 100, "window": 60},  # 100 requests per minute
            "ml_predict": {
                "requests": 50,
                "window": 60,
            },  # 50 ML predictions per minute
            "chatops": {"requests": 30, "window": 60},  # 30 ChatOps queries per minute
            "admin": {"requests": 200, "window": 60},  # 200 admin requests per minute
            "health": {"requests": 1000, "window": 60},  # 1000 health checks per minute
        }

    def _get_client_identifier(self) -> str:
        """Get unique client identifier for rate limiting."""
        # Try to get API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key[:16]}"  # Use first 16 chars for privacy

        # Fall back to IP address
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        return f"ip:{client_ip}"

    def _get_endpoint_type(self, endpoint: str) -> str:
        """Determine endpoint type for rate limiting."""
        if "ml" in endpoint or "predict" in endpoint:
            return "ml_predict"
        elif "chatops" in endpoint or "query" in endpoint:
            return "chatops"
        elif "admin" in endpoint:
            return "admin"
        elif "health" in endpoint:
            return "health"
        else:
            return "default"

    def _clean_old_requests(self, client_id: str, window_seconds: int):
        """Remove requests outside the current window."""
        current_time = time.time()
        cutoff_time = current_time - window_seconds

        # Remove old requests
        while self.requests[client_id] and self.requests[client_id][0] < cutoff_time:
            self.requests[client_id].popleft()

    def is_rate_limited(self, endpoint: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if request should be rate limited."""
        client_id = self._get_client_identifier()
        endpoint_type = self._get_endpoint_type(endpoint)
        limit_config = self.limits.get(endpoint_type, self.limits["default"])

        # Clean old requests
        self._clean_old_requests(client_id, limit_config["window"])

        # Check if limit exceeded
        current_requests = len(self.requests[client_id])
        is_limited = current_requests >= limit_config["requests"]

        # Add current request if not limited
        if not is_limited:
            self.requests[client_id].append(time.time())

        # Calculate remaining requests and reset time
        remaining_requests = max(
            0, limit_config["requests"] - current_requests - (0 if is_limited else 1)
        )

        # Calculate reset time
        if self.requests[client_id]:
            oldest_request = self.requests[client_id][0]
            reset_time = int(oldest_request + limit_config["window"])
        else:
            reset_time = int(time.time() + limit_config["window"])

        return is_limited, {
            "limit": limit_config["requests"],
            "remaining": remaining_requests,
            "reset": reset_time,
            "window": limit_config["window"],
            "client_id": client_id[:20] + "..." if len(client_id) > 20 else client_id,
        }

    def get_rate_limit_headers(self, endpoint: str) -> Dict[str, str]:
        """Get rate limit headers for response."""
        _, info = self.is_rate_limited(endpoint)
        return {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info["remaining"]),
            "X-RateLimit-Reset": str(info["reset"]),
            "X-RateLimit-Window": str(info["window"]),
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(endpoint_type: Optional[str] = None):
    """Decorator for rate limiting endpoints."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine endpoint
            endpoint = endpoint_type or request.endpoint

            # Check rate limit
            is_limited, limit_info = rate_limiter.is_rate_limited(endpoint)

            if is_limited:
                logger.warning(
                    f"Rate limit exceeded for {limit_info['client_id']} on {endpoint}"
                )

                # Return rate limit error
                error_data = {
                    "message": "Rate limit exceeded",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "details": {
                        "limit": limit_info["limit"],
                        "remaining": limit_info["remaining"],
                        "reset": limit_info["reset"],
                        "retry_after": max(0, limit_info["reset"] - int(time.time())),
                    },
                }

                response = error_response(
                    message=error_data["message"],
                    error_code=error_data["error_code"],
                    status_code=429,
                    details=error_data["details"],
                )

                # Add rate limit headers
                headers = rate_limiter.get_rate_limit_headers(endpoint)
                for key, value in headers.items():
                    response[0].headers[key] = value

                return response

            # Add rate limit headers to successful response
            g.rate_limit_headers = rate_limiter.get_rate_limit_headers(endpoint)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def add_rate_limit_headers(response):
    """Add rate limit headers to response."""
    if hasattr(g, "rate_limit_headers"):
        for key, value in g.rate_limit_headers.items():
            response.headers[key] = value
    return response


class RateLimitMiddleware:
    """Middleware for applying rate limiting to all requests."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Store original start_response
        original_start_response = start_response

        def custom_start_response(status, headers, exc_info=None):
            # Add rate limit headers if available
            if hasattr(g, "rate_limit_headers"):
                for key, value in g.rate_limit_headers.items():
                    headers.append((key, value))

            return original_start_response(status, headers, exc_info)

        return self.app(environ, custom_start_response)


def configure_rate_limiting(app):
    """Configure rate limiting for Flask app."""
    # Add middleware
    app.wsgi_app = RateLimitMiddleware(app.wsgi_app)

    # Add after_request handler
    app.after_request(add_rate_limit_headers)

    logger.info("Rate limiting configured successfully")


# Rate limit configurations for different endpoints
RATE_LIMIT_CONFIGS = {
    "health": {"requests": 1000, "window": 60},
    "metrics": {"requests": 500, "window": 60},
    "ml_predict": {"requests": 50, "window": 60},
    "chatops_query": {"requests": 30, "window": 60},
    "remediation_action": {"requests": 20, "window": 60},
    "admin": {"requests": 200, "window": 60},
    "default": {"requests": 100, "window": 60},
}
