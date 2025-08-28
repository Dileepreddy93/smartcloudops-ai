#!/usr/bin/env python3
"""
SmartCloudOps AI - Secure Authentication and Authorization Module
================================================================

Enterprise-grade authentication with fail-secure patterns, comprehensive
rate limiting, session management, and audit logging.
"""


import hashlib
import logging
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Dict, List, Optional, Set, Tuple

from flask import g, jsonify, request

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AuthAttempt:
    """Track authentication attempts for security monitoring."""

    timestamp: datetime
    api_key_prefix: str
    ip_address: str
    user_agent: str
    success: bool
    endpoint: str
    permission_required: str


@dataclass
class APIKeyInfo:
    """Structured API key information."""

    key_hash: str
    role: str
    permissions: Set[str]
    user_id: str
    created_at: datetime
    last_used: Optional[datetime]
    rate_limit_per_hour: int
    rate_limit_per_minute: int
    is_active: bool
    allowed_ips: Optional[List[str]]
    expires_at: Optional[datetime]


class SecureAPIKeyAuth:
    """
    Enterprise-grade API Key Authentication with comprehensive security features.

    Features:
    - Fail-secure authentication (denies access on errors)
    - Multi-tier rate limiting (per-minute and per-hour)
    - IP address restrictions
    - Comprehensive audit logging
    - Session tracking
    - Key expiration
    - Brute force protection
    """

    def __init__(self, app=None):
        self.app = app
        self.api_keys: Dict[str, APIKeyInfo] = {}
        self.rate_limits = defaultdict(list)
        self.auth_attempts: List[AuthAttempt] = []
        self.blocked_ips = defaultdict(list)
        self.active_sessions = {}
        self._lock = threading.RLock()

        # Security configuration
        self.max_auth_attempts_per_ip = 10
        self.auth_attempt_window_minutes = 15
        self.session_timeout_minutes = 60

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the authentication with Flask app"""
        self.app = app
        self._load_api_keys()

        # Schedule cleanup tasks
        self._schedule_cleanup()

    def _load_api_keys(self):
        """Load API keys from secure storage with proper hashing"""
        try:
            current_time = datetime.now(timezone.utc)

            # Admin API key - full access
            admin_key = self.app.config.get("ADMIN_API_KEY", "")
            admin_hash = self._hash_api_key(admin_key)
            self.api_keys[admin_hash] = APIKeyInfo(
                key_hash=admin_hash,
                role="admin",
                permissions={
                    "read",
                    "write",
                    "admin",
                    "ml_predict",
                    "system_status",
                    "metrics",
                },
                user_id="system_admin",
                created_at=current_time,
                last_used=None,
                rate_limit_per_hour=1000,
                rate_limit_per_minute=50,
                is_active=True,
                allowed_ips=None,  # Allow from any IP
                expires_at=None,  # Never expires
            )

            # ML Service API key - ML operations only
            ml_key = self.app.config.get("ML_API_KEY", "")
            ml_hash = self._hash_api_key(ml_key)
            self.api_keys[ml_hash] = APIKeyInfo(
                key_hash=ml_hash,
                role="ml_service",
                permissions={"read", "ml_predict"},
                user_id="ml_service",
                created_at=current_time,
                last_used=None,
                rate_limit_per_hour=500,
                rate_limit_per_minute=25,
                is_active=True,
                allowed_ips=None,
                expires_at=current_time + timedelta(days=365),
            )

            # Read-only API key
            readonly_key = self.app.config.get("READONLY_API_KEY", "")
            readonly_hash = self._hash_api_key(readonly_key)
            self.api_keys[readonly_hash] = APIKeyInfo(
                key_hash=readonly_hash,
                role="readonly",
                permissions={"read"},
                user_id="readonly_user",
                created_at=current_time,
                last_used=None,
                rate_limit_per_hour=100,
                rate_limit_per_minute=10,
                is_active=True,
                allowed_ips=None,
                expires_at=current_time + timedelta(days=90),
            )

            logger.info(f"Loaded {len(self.api_keys)} API keys with secure hashing")

        except Exception as e:
            logger.error(f"CRITICAL: Error loading API keys: {e}")
            # Fail-secure: empty keys dict means no access
            self.api_keys = {}

    def _hash_api_key(self, api_key: str) -> str:
        """Securely hash API key for storage and comparison"""
        salt = self.app.config.get("API_KEY_SALT", "smartcloudops_secure_salt_2024")
        return hashlib.sha256((api_key + salt).encode()).hexdigest()

    def validate_api_key(self, api_key: str, required_permission: str = "read") -> Tuple[bool, Optional[Dict], str]:
        """
        Validate API key with comprehensive security checks.

        Returns:
            Tuple[bool, Optional[Dict], str]: (is_valid, user_info, error_message)
        """
        if not api_key:
            return False, None, "API key is required"

        # Get client information for logging
        client_ip = self._get_client_ip()
        user_agent = request.headers.get("User-Agent", "Unknown")
        endpoint = request.endpoint or "unknown"

        try:
            with self._lock:
                # Check if IP is blocked
                if self._is_ip_blocked(client_ip):
                    self._log_auth_attempt(
                        api_key,
                        client_ip,
                        user_agent,
                        endpoint,
                        required_permission,
                        False,
                    )
                    return (
                        False,
                        None,
                        "IP address temporarily blocked due to repeated failures",
                    )

                # Hash the provided key
                key_hash = self._hash_api_key(api_key)

                # Check if key exists
                if not api_key or key_hash not in self.api_keys:
                    self._log_auth_attempt(
                        api_key,
                        client_ip,
                        user_agent,
                        endpoint,
                        required_permission,
                        False,
                    )
                    self._record_failed_attempt(client_ip)
                    return False, None, "Invalid API key"

                key_info = self.api_keys[key_hash]

                # Check if key is active
                if not key_info.is_active:
                    self._log_auth_attempt(
                        api_key,
                        client_ip,
                        user_agent,
                        endpoint,
                        required_permission,
                        False,
                    )
                    return False, None, "API key has been deactivated"

                # Check key expiration
                if key_info.expires_at and datetime.now(timezone.utc) > key_info.expires_at:
                    self._log_auth_attempt(
                        api_key,
                        client_ip,
                        user_agent,
                        endpoint,
                        required_permission,
                        False,
                    )
                    return False, None, "API key has expired"

                # Check IP restrictions
                if key_info.allowed_ips and client_ip not in key_info.allowed_ips:
                    self._log_auth_attempt(
                        api_key,
                        client_ip,
                        user_agent,
                        endpoint,
                        required_permission,
                        False,
                    )
                    return (
                        False,
                        None,
                        f"API key not authorized for IP address: {client_ip}",
                    )

                # Check rate limits
                if self._is_rate_limited(key_hash, key_info):
                    self._log_auth_attempt(
                        api_key,
                        client_ip,
                        user_agent,
                        endpoint,
                        required_permission,
                        False,
                    )
                    return False, None, "Rate limit exceeded"

                # Check permission
                if required_permission not in key_info.permissions:
                    self._log_auth_attempt(
                        api_key,
                        client_ip,
                        user_agent,
                        endpoint,
                        required_permission,
                        False,
                    )
                    return (
                        False,
                        None,
                        f"Insufficient permissions: {required_permission} required",
                    )

                # Success - update last used and create session
                key_info.last_used = datetime.now(timezone.utc)
                session_id = self._create_session(key_info)

                # Record rate limit usage
                self._record_request(key_hash)

                # Log successful authentication
                self._log_auth_attempt(api_key, client_ip, user_agent, endpoint, required_permission, True)

                # Build user info for Flask context
                user_info = {
                    "user_id": key_info.user_id,
                    "role": key_info.role,
                    "permissions": key_info.permissions,
                    "session_id": session_id,
                    "last_used": key_info.last_used.isoformat(),
                    "client_ip": client_ip,
                }

                return True, user_info, "Authentication successful"

        except Exception as e:
            logger.error(f"CRITICAL: Authentication system error: {e}")
            # Fail-secure: deny access on any internal error
            self._log_auth_attempt(api_key, client_ip, user_agent, endpoint, required_permission, False)
            return False, None, "Authentication service temporarily unavailable"

    def _get_client_ip(self) -> str:
        """Get real client IP address considering proxies"""
        # Check X-Forwarded-For header (from load balancers/proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header (from nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to remote_addr
        return request.remote_addr or "unknown"

    def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is temporarily blocked"""
        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time - timedelta(minutes=self.auth_attempt_window_minutes)

        # Clean old blocked attempts
        self.blocked_ips[ip_address] = [
            timestamp for timestamp in self.blocked_ips[ip_address] if timestamp > cutoff_time
        ]

        return len(self.blocked_ips[ip_address]) >= self.max_auth_attempts_per_ip

    def _record_failed_attempt(self, ip_address: str):
        """Record failed authentication attempt for IP blocking"""
        self.blocked_ips[ip_address].append(datetime.now(timezone.utc))

    def _is_rate_limited(self, key_hash: str, key_info: APIKeyInfo) -> bool:
        """Check if API key has exceeded rate limits"""
        current_time = datetime.now(timezone.utc)

        # Clean old rate limit entries
        hour_cutoff = current_time - timedelta(hours=1)
        minute_cutoff = current_time - timedelta(minutes=1)

        self.rate_limits[key_hash] = [timestamp for timestamp in self.rate_limits[key_hash] if timestamp > hour_cutoff]

        # Check hourly limit
        hourly_requests = len(self.rate_limits[key_hash])
        if hourly_requests >= key_info.rate_limit_per_hour:
            return True

        # Check per-minute limit
        minute_requests = len([timestamp for timestamp in self.rate_limits[key_hash] if timestamp > minute_cutoff])
        if minute_requests >= key_info.rate_limit_per_minute:
            return True

        return False

    def _record_request(self, key_hash: str):
        """Record request for rate limiting"""
        self.rate_limits[key_hash].append(datetime.now(timezone.utc))

    def _create_session(self, key_info: APIKeyInfo) -> str:
        """Create secure session for tracking"""
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            "user_id": key_info.user_id,
            "role": key_info.role,
            "created_at": datetime.now(timezone.utc),
            "last_activity": datetime.now(timezone.utc),
            "client_ip": self._get_client_ip(),
        }
        return session_id

    def _log_auth_attempt(
        self,
        api_key: str,
        ip_address: str,
        user_agent: str,
        endpoint: str,
        permission: str,
        success: bool,
    ):
        """Log authentication attempt for security monitoring"""
        attempt = AuthAttempt(
            timestamp=datetime.now(timezone.utc),
            api_key_prefix=api_key[:8] + "..." if api_key else "none",
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            endpoint=endpoint,
            permission_required=permission,
        )

        self.auth_attempts.append(attempt)

        # Log to standard logger
        if success:
            logger.info(f"AUTH SUCCESS: {attempt.api_key_prefix} from {ip_address} to {endpoint}")
        else:
            logger.warning(f"AUTH FAILURE: {attempt.api_key_prefix} from {ip_address} to {endpoint}")

        # Keep only recent attempts (last 1000)
        if len(self.auth_attempts) > 1000:
            self.auth_attempts = self.auth_attempts[-1000:]

    def _schedule_cleanup(self):
        """Schedule periodic cleanup of old sessions and rate limits"""
        # This would be implemented with a background task in production
        pass

    def get_auth_stats(self) -> Dict:
        """Get authentication statistics for monitoring"""
        current_time = datetime.now(timezone.utc)
        recent_cutoff = current_time - timedelta(hours=24)

        recent_attempts = [attempt for attempt in self.auth_attempts if attempt.timestamp > recent_cutoff]

        successful_attempts = [a for a in recent_attempts if a.success]
        failed_attempts = [a for a in recent_attempts if not a.success]

        return {
            "total_api_keys": len(self.api_keys),
            "active_sessions": len(self.active_sessions),
            "recent_attempts_24h": len(recent_attempts),
            "successful_attempts_24h": len(successful_attempts),
            "failed_attempts_24h": len(failed_attempts),
            "blocked_ips": len(self.blocked_ips),
            "success_rate": (len(successful_attempts) / len(recent_attempts) * 100 if recent_attempts else 0),
        }


# Initialize global auth instance
auth = SecureAPIKeyAuth()


def require_api_key(permission: str = "read"):
    """
    Secure decorator to require API key authentication with specific permission.

    FAIL-SECURE DESIGN: This decorator will DENY access if:
    - Authentication system fails
    - API key is missing or invalid
    - Required permission is not granted
    - Rate limits are exceeded
    - Any security check fails
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get API key from header
                api_key = request.headers.get("X-API-Key")

                if not api_key:
                    logger.warning(f"Missing API key for {request.endpoint} from {request.remote_addr}")
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "AUTHENTICATION_REQUIRED",
                                "message": "API key required in X-API-Key header",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        ),
                        401,
                    )

                # Validate API key with comprehensive security checks
                is_valid, user_info, error_message = auth.validate_api_key(api_key, permission)

                if not is_valid:
                    logger.warning(f"Authentication failed for {request.endpoint}: {error_message}")

                    # Determine appropriate error code
                    if "rate limit" in error_message.lower():
                        status_code = 429
                        error_code = "RATE_LIMITED"
                    elif "permission" in error_message.lower():
                        status_code = 403
                        error_code = "AUTHORIZATION_DENIED"
                    else:
                        status_code = 401
                        error_code = "AUTHENTICATION_FAILED"

                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": error_code,
                                "message": error_message,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        ),
                        status_code,
                    )

                # Store user info in Flask context for use in endpoint
                g.current_user = user_info
                g.request_id = str(uuid.uuid4())
                g.auth_timestamp = datetime.now(timezone.utc)

                # Execute the protected endpoint
                return f(*args, **kwargs)

            except Exception as e:
                logger.error(f"CRITICAL: Authentication decorator error: {e}")
                # FAIL-SECURE: Deny access on any unexpected error
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "AUTHENTICATION_SERVICE_ERROR",
                            "message": "Authentication service temporarily unavailable",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    ),
                    503,
                )

        return decorated_function

    return decorator


def require_admin():
    """Decorator to require admin role"""
    return require_api_key("admin")


def require_ml_access():
    """Decorator to require ML prediction access"""
    return require_api_key("ml_predict")


def require_write_access():
    """Decorator to require write access"""
    return require_api_key("write")


def get_current_user() -> Optional[Dict]:
    """Get current authenticated user info"""
    return getattr(g, "current_user", None)


def get_request_id() -> Optional[str]:
    """Get current request ID for tracking"""
    return getattr(g, "request_id", None)


def has_permission(permission: str) -> bool:
    """Check if current user has specific permission"""
    user = get_current_user()
    if not user:
        return False
    return permission in user.get("permissions", set())


# Security monitoring functions
def get_security_stats() -> Dict:
    """Get security statistics for monitoring dashboard"""
    return auth.get_auth_stats()


def get_recent_auth_attempts(limit: int = 100) -> List[Dict]:
    """Get recent authentication attempts for security monitoring"""
    recent_attempts = sorted(auth.auth_attempts, key=lambda x: x.timestamp, reverse=True)[:limit]
    return [asdict(attempt) for attempt in recent_attempts]
