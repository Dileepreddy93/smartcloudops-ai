#!/usr/bin/env python3
"""
SmartCloudOps AI - Secure Flask Application
==========================================

Production-ready Flask application with enterprise-grade security:
- Fail-secure authentication with comprehensive rate limiting
- Input validation and sanitization for all endpoints
- Data Transfer Objects to prevent sensitive data exposure
- Comprehensive error handling with security logging
- HTTP security headers and CORS configuration
- Structured API responses with standardized error codes

Version: 3.2.0 Security Hardened
"""





import logging
import time
import traceback
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from functools import wraps

# Flask and security imports
from flask import Flask, g, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge

# Import our secure modules
from app.auth_secure import (
    get_current_user,
    get_request_id,
    get_security_stats,
    require_admin,
    require_api_key,
    require_ml_access,
)
from app.secure_api import (
    ErrorCode,
    HealthCheckDTO,
    MLPredictionDTO,
    SecurityError,
    StatusDTO,
    ValidationError,
    build_error_response,
    build_success_response,
    sanitize_input,
    validate_ml_metrics,
    validate_request_data,
)

# Import application modules
try:
    from app.database_integration import DatabaseService

    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    DatabaseService = None

# Import secure ML inference engine
try:
    import os
    import sys

    # Use relative path for scripts directory
    scripts_path = os.path.join(os.path.dirname(__file__), "../scripts")
    sys.path.append(os.path.abspath(scripts_path))
    # Try importing the existing ML inference engine
    try:
        from app.core.ml_engine.secure_inference import SecureMLInferenceEngine

        ML_ENGINE_AVAILABLE = True
    except ImportError:
        # Fall back to checking for existing inference scripts
        try:
            from app.ml_production_pipeline import MLInferenceEngine

            SecureMLInferenceEngine = MLInferenceEngine
            ML_ENGINE_AVAILABLE = True
        except ImportError:
            ML_ENGINE_AVAILABLE = False
            SecureMLInferenceEngine = None
except Exception:
    ML_ENGINE_AVAILABLE = False
    SecureMLInferenceEngine = None

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.FileHandler("/tmp/smartcloudops_api.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Initialize Flask application with security configuration
app = Flask(__name__)

# SECURITY: Remove all hardcoded secrets - require environment variables
app.config.update(
    {
        "SECRET_KEY": os.environ.get("SECRET_KEY"),  # Must be set
        "DEBUG": os.environ.get("FLASK_DEBUG", "False").lower() == "true",
        "TESTING": False,
        "PROPAGATE_EXCEPTIONS": False,  # Handle exceptions securely
        "ADMIN_API_KEY": os.environ.get("ADMIN_API_KEY"),  # Must be set
        "ML_API_KEY": os.environ.get("ML_API_KEY"),  # Must be set
        "READONLY_API_KEY": os.environ.get("READONLY_API_KEY"),  # Must be set
        "API_KEY_SALT": os.environ.get("API_KEY_SALT"),  # Must be set
    }
)

# Validate required environment variables
required_env_vars = [
    "SECRET_KEY",
    "ADMIN_API_KEY",
    "ML_API_KEY",
    "READONLY_API_KEY",
    "API_KEY_SALT",
]

missing_vars = [var for var in required_env_vars if not app.config.get(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


# Initialize simple rate limiting (without external dependencies)
class SimpleRateLimiter:
    """Simple rate limiter using in-memory storage"""

    def __init__(self):
        self.requests = defaultdict(list)
        self.blocked_ips = defaultdict(list)

    def is_allowed(self, ip_address: str, limit_per_minute: int = 10, limit_per_hour: int = 100) -> bool:
        """Check if request is allowed based on rate limits"""
        current_time = time.time()

        # Clean old entries
        minute_cutoff = current_time - 60
        hour_cutoff = current_time - 3600

        self.requests[ip_address] = [timestamp for timestamp in self.requests[ip_address] if timestamp > hour_cutoff]

        # Check limits
        minute_requests = len([t for t in self.requests[ip_address] if t > minute_cutoff])
        hour_requests = len(self.requests[ip_address])

        if minute_requests >= limit_per_minute or hour_requests >= limit_per_hour:
            return False

        # Record this request
        self.requests[ip_address].append(current_time)
        return True


# Initialize rate limiter
rate_limiter = SimpleRateLimiter()


def rate_limit(per_minute: int = 10, per_hour: int = 100):
    """Rate limiting decorator"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr or "unknown"

            if not rate_limiter.is_allowed(client_ip, per_minute, per_hour):
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return (
                    jsonify(
                        build_error_response(
                            ErrorCode.RATE_LIMITED,
                            "Rate limit exceeded. Please try again later.",
                            request_id=getattr(g, "request_id", None),
                        )
                    ),
                    429,
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Simple CORS handler
@app.after_request
def after_request(response):
    """Add CORS headers manually"""
    origin = request.headers.get("Origin")
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

    if origin in allowed_origins or "*" in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin or "*"

    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key, Authorization"
    response.headers["Access-Control-Max-Age"] = "86400"

    return response


# Initialize services
db_service = DatabaseService() if DATABASE_AVAILABLE else None
ml_engine = None


def init_ml_engine():
    """Initialize ML inference engine with error handling"""
    global ml_engine
    if ML_ENGINE_AVAILABLE:
        try:
            ml_engine = SecureMLInferenceEngine()
            logger.info("✅ Secure ML Inference Engine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize ML engine: {e}")
            ml_engine = None
            return False
    else:
        logger.warning("⚠️ ML Inference Engine not available")
        return False


# Initialize components
init_ml_engine()


# Security middleware
@app.before_request
def security_headers():
    """Apply security headers to all requests"""
    # Generate request ID for tracking
    g.request_id = str(uuid.uuid4())
    g.start_time = datetime.now(timezone.utc)

    # Log incoming request
    logger.info(f"REQUEST: {request.method} {request.path} - IP: {request.remote_addr} - ID: {g.request_id}")


@app.after_request
def apply_security_headers(response):
    """Apply comprehensive security headers"""
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    # API-specific headers
    response.headers["X-Request-ID"] = getattr(g, "request_id", "unknown")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    # Log response
    duration = (datetime.now(timezone.utc) - getattr(g, "start_time", datetime.now(timezone.utc))).total_seconds()
    logger.info(
        f"RESPONSE: {response.status_code} - Duration: {duration:.3f}s - ID: {getattr(g, 'request_id', 'unknown')}"
    )

    return response


# Error handlers with secure responses
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    """Handle validation errors securely"""
    logger.warning(f"Validation error: {str(e)} - Request ID: {getattr(g, 'request_id', 'unknown')}")
    return (
        jsonify(
            build_error_response(
                ErrorCode.VALIDATION_ERROR,
                "Invalid input provided",
                request_id=getattr(g, "request_id", None),
            )
        ),
        400,
    )


@app.errorhandler(SecurityError)
def handle_security_error(e):
    """Handle security errors with strict logging"""
    logger.error(
        f"SECURITY VIOLATION: {str(e)} - IP: {request.remote_addr} - Request ID: {getattr(g, 'request_id', 'unknown')}"
    )
    return (
        jsonify(
            build_error_response(
                ErrorCode.VALIDATION_ERROR,
                "Request rejected for security reasons",
                request_id=getattr(g, "request_id", None),
            )
        ),
        400,
    )


@app.errorhandler(RequestEntityTooLarge)
def handle_large_request(e):
    """Handle requests that are too large"""
    logger.warning(f"Request too large from IP: {request.remote_addr}")
    return (
        jsonify(
            build_error_response(
                ErrorCode.VALIDATION_ERROR,
                "Request payload too large",
                request_id=getattr(g, "request_id", None),
            )
        ),
        413,
    )


@app.errorhandler(429)
def handle_rate_limit(e):
    """Handle rate limit exceeded"""
    logger.warning(f"Rate limit exceeded for IP: {request.remote_addr}")
    return (
        jsonify(
            build_error_response(
                ErrorCode.RATE_LIMITED,
                "Rate limit exceeded. Please try again later.",
                request_id=getattr(g, "request_id", None),
            )
        ),
        429,
    )


@app.errorhandler(500)
def handle_internal_error(e):
    """Handle internal server errors securely"""
    error_id = str(uuid.uuid4())
    logger.error(f"Internal error {error_id}: {str(e)}\n{traceback.format_exc()}")

    # Return generic error message to prevent information disclosure
    return (
        jsonify(
            build_error_response(
                ErrorCode.INTERNAL_ERROR,
                "An internal error occurred. Please contact support.",
                request_id=getattr(g, "request_id", None),
            )
        ),
        500,
    )


# API Endpoints with comprehensive security


@app.route("/status", methods=["GET"])
@require_api_key("read")
@rate_limit(per_minute=20, per_hour=200)
def get_status():
    """
    Get system status with secure, sanitized information.

    Returns only safe, non-sensitive status information.
    """
    try:
        user = get_current_user()

        # Build secure status response
        status_data = StatusDTO(
            status="operational",
            version="3.2.0-security",
            environment=os.environ.get("ENVIRONMENT", "production")[:20],  # Limit length
            timestamp=datetime.now(timezone.utc).isoformat(),
            features_available=3,  # Count of available features
            auth_enabled=True,
        )

        logger.info(f"Status requested by user: {user.get('user_id', 'unknown')}")

        return (
            jsonify(build_success_response(status_data.to_dict(), request_id=get_request_id())),
            200,
        )

    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return (
            jsonify(
                build_error_response(
                    ErrorCode.INTERNAL_ERROR,
                    "Unable to retrieve system status",
                    request_id=get_request_id(),
                )
            ),
            500,
        )


@app.route("/chat", methods=["POST"])
@require_api_key("write")
@rate_limit(per_minute=10, per_hour=100)
def chat():
    """
    Handle chat interactions with comprehensive input validation.
    """
    try:
        # Validate request format
        if not request.is_json:
            raise ValidationError("Request must be JSON")

        data = request.get_json()

        # Validate required fields
        validate_request_data(data, ["message"], ["context", "session_id"])

        # Sanitize inputs
        message = sanitize_input(data["message"], max_length=1000)
        (sanitize_input(data.get("context", ""), max_length=500) if data.get("context") else None)
        session_id = data.get("session_id", str(uuid.uuid4()))

        user = get_current_user()
        logger.info(f"Chat request from user: {user.get('user_id', 'unknown')} - Message length: {len(message)}")

        # Simulate chat response (replace with actual chat logic)
        response_data = {
            "response": f"Echo: {message}",
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user.get("user_id", "unknown"),
        }

        return (
            jsonify(build_success_response(response_data, request_id=get_request_id())),
            200,
        )

    except ValidationError as e:
        raise e
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return (
            jsonify(
                build_error_response(
                    ErrorCode.INTERNAL_ERROR,
                    "Chat service temporarily unavailable",
                    request_id=get_request_id(),
                )
            ),
            500,
        )


@app.route("/ml/health", methods=["GET"])
@require_api_key("read")
@rate_limit(per_minute=30, per_hour=300)
def ml_health():
    """
    Check ML inference engine health with secure response.
    """
    try:
        if not ml_engine:
            health_data = HealthCheckDTO(
                status="unavailable",
                engine_type="SecureMLInferenceEngine",
                components_healthy=0,
                components_total=3,
                last_check=datetime.now(timezone.utc).isoformat(),
            )
        else:
            # Perform health check
            health_status = ml_engine.health_check() if hasattr(ml_engine, "health_check") else {"status": "healthy"}

            health_data = HealthCheckDTO(
                status=health_status.get("status", "unknown"),
                engine_type="SecureMLInferenceEngine",
                components_healthy=health_status.get("healthy_components", 3),
                components_total=3,
                last_check=datetime.now(timezone.utc).isoformat(),
            )

        user = get_current_user()
        logger.info(f"ML health check by user: {user.get('user_id', 'unknown')}")

        return (
            jsonify(build_success_response(health_data.to_dict(), request_id=get_request_id())),
            200,
        )

    except Exception as e:
        logger.error(f"ML health endpoint error: {e}")
        return (
            jsonify(
                build_error_response(
                    ErrorCode.SERVICE_UNAVAILABLE,
                    "ML health check unavailable",
                    request_id=get_request_id(),
                )
            ),
            503,
        )


@app.route("/ml/predict", methods=["POST"])
@require_ml_access()
@rate_limit(per_minute=25, per_hour=500)
def ml_predict():
    """
    ML prediction endpoint with comprehensive input validation and security.
    """
    try:
        # Validate request format
        if not request.is_json:
            raise ValidationError("Request must be JSON")

        data = request.get_json()

        # Validate required fields
        validate_request_data(data, ["metrics"], ["threshold", "model_version"])

        # Validate and sanitize metrics with comprehensive security checks
        metrics = validate_ml_metrics(data["metrics"])

        # Validate optional parameters
        threshold = None
        if "threshold" in data:
            if not isinstance(data["threshold"], (int, float)) or not 0 <= data["threshold"] <= 1:
                raise ValidationError("Threshold must be a number between 0 and 1")
            threshold = float(data["threshold"])

        (sanitize_input(data.get("model_version", "latest"), max_length=50) if data.get("model_version") else "latest")

        user = get_current_user()
        logger.info(
            f"ML prediction request from user: {user.get('user_id', 'unknown')} - Metrics: {list(metrics.keys())}"
        )

        # Check ML engine availability
        if not ml_engine:
            logger.error("ML engine not available for prediction")
            return (
                jsonify(
                    build_error_response(
                        ErrorCode.SERVICE_UNAVAILABLE,
                        "ML inference service temporarily unavailable",
                        request_id=get_request_id(),
                    )
                ),
                503,
            )

        # Perform prediction with error handling
        try:
            prediction_result = ml_engine.predict(metrics, threshold=threshold)

            # Build secure prediction response
            prediction_data = MLPredictionDTO(
                anomaly_detected=prediction_result.get("anomaly_detected", False),
                confidence_score=round(prediction_result.get("confidence_score", 0.0), 4),
                severity_level=prediction_result.get("severity_level", "unknown"),
                prediction_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc).isoformat(),
                model_version=prediction_result.get("model_version", "unknown"),
            )

            # Log prediction for audit
            logger.info(
                f"ML prediction completed - Anomaly: {prediction_data.anomaly_detected}, "
                f"Confidence: {prediction_data.confidence_score}, User: {user.get('user_id', 'unknown')}"
            )

            return (
                jsonify(build_success_response(prediction_data.to_dict(), request_id=get_request_id())),
                200,
            )

        except Exception as e:
            logger.error(f"ML prediction engine error: {e}")
            return (
                jsonify(
                    build_error_response(
                        ErrorCode.INTERNAL_ERROR,
                        "ML prediction failed. Please try again.",
                        request_id=get_request_id(),
                    )
                ),
                500,
            )

    except ValidationError as e:
        raise e
    except Exception as e:
        logger.error(f"ML predict endpoint error: {e}")
        return (
            jsonify(
                build_error_response(
                    ErrorCode.INTERNAL_ERROR,
                    "ML prediction service error",
                    request_id=get_request_id(),
                )
            ),
            500,
        )


@app.route("/ml/metrics", methods=["GET"])
@require_api_key("read")
@rate_limit(per_minute=20, per_hour=200)
def ml_metrics():
    """
    Get ML engine performance metrics (sanitized for security).
    """
    try:
        user = get_current_user()

        if not ml_engine:
            metrics_data = {
                "service_status": "unavailable",
                "total_predictions": 0,
                "average_response_time_ms": 0,
                "model_version": "unknown",
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        else:
            # Get sanitized metrics (no sensitive internal data)
            raw_metrics = ml_engine.get_performance_metrics() if hasattr(ml_engine, "get_performance_metrics") else {}

            metrics_data = {
                "service_status": "operational",
                "total_predictions": raw_metrics.get("total_predictions", 0),
                "average_response_time_ms": round(raw_metrics.get("avg_response_time", 0) * 1000, 2),
                "model_version": raw_metrics.get("model_version", "unknown")[:20],  # Limit length
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

        logger.info(f"ML metrics requested by user: {user.get('user_id', 'unknown')}")

        return (
            jsonify(build_success_response(metrics_data, request_id=get_request_id())),
            200,
        )

    except Exception as e:
        logger.error(f"ML metrics endpoint error: {e}")
        return (
            jsonify(
                build_error_response(
                    ErrorCode.INTERNAL_ERROR,
                    "Unable to retrieve ML metrics",
                    request_id=get_request_id(),
                )
            ),
            500,
        )


@app.route("/metrics", methods=["GET"])
@require_api_key("metrics")
@rate_limit(per_minute=10, per_hour=100)
def system_metrics():
    """
    Get system performance metrics (admin/monitoring access only).
    """
    try:
        user = get_current_user()

        # Only provide basic system metrics, no sensitive data
        metrics_data = {
            "api_version": "3.2.0-security",
            "uptime_hours": 0,  # Would calculate from app start time
            "total_requests_24h": 0,  # Would get from monitoring
            "authentication_stats": get_security_stats(),
            "services_status": {
                "database": "operational" if db_service else "unavailable",
                "ml_engine": "operational" if ml_engine else "unavailable",
                "authentication": "operational",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"System metrics requested by user: {user.get('user_id', 'unknown')}")

        return (
            jsonify(build_success_response(metrics_data, request_id=get_request_id())),
            200,
        )

    except Exception as e:
        logger.error(f"System metrics endpoint error: {e}")
        return (
            jsonify(
                build_error_response(
                    ErrorCode.INTERNAL_ERROR,
                    "Unable to retrieve system metrics",
                    request_id=get_request_id(),
                )
            ),
            500,
        )


# Security monitoring endpoint
@app.route("/security/audit", methods=["GET"])
@require_admin()
@rate_limit(per_minute=5, per_hour=50)
def security_audit():
    """
    Security audit endpoint for administrators only.
    """
    try:
        user = get_current_user()

        # Get security audit data
        from app.auth_secure import get_recent_auth_attempts

        audit_data = {
            "security_stats": get_security_stats(),
            "recent_attempts": get_recent_auth_attempts(50),  # Last 50 attempts
            "system_security_level": "high",
            "security_features_enabled": [
                "api_key_authentication",
                "rate_limiting",
                "input_validation",
                "fail_secure_design",
                "audit_logging",
                "ip_blocking",
            ],
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Security audit accessed by admin: {user.get('user_id', 'unknown')}")

        return (
            jsonify(build_success_response(audit_data, request_id=get_request_id())),
            200,
        )

    except Exception as e:
        logger.error(f"Security audit endpoint error: {e}")
        return (
            jsonify(
                build_error_response(
                    ErrorCode.INTERNAL_ERROR,
                    "Security audit temporarily unavailable",
                    request_id=get_request_id(),
                )
            ),
            500,
        )


# Health check endpoint (public, no authentication required)
@app.route("/health", methods=["GET"])
@rate_limit(per_minute=100, per_hour=1000)
def health_check():
    """
    Public health check endpoint for load balancers and monitoring.
    """
    return (
        jsonify(
            {
                "status": "healthy",
                "version": "3.2.0-security",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        200,
    )


if __name__ == "__main__":
    """
    Production startup with comprehensive security configuration.
    """
    # Initialize authentication system
    from app.auth_secure import auth

    auth.init_app(app)

    # Startup logging
    logger.info("🔒 SmartCloudOps AI - Secure API Server Starting")
    logger.info(f"🔧 Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    logger.info(f"🔧 Database Available: {DATABASE_AVAILABLE}")
    logger.info(f"🔧 ML Engine Available: {ML_ENGINE_AVAILABLE}")
    logger.info("🔒 Security Features Enabled:")
    logger.info("   ✅ Fail-secure authentication")
    logger.info("   ✅ Multi-tier rate limiting")
    logger.info("   ✅ Comprehensive input validation")
    logger.info("   ✅ Data sanitization and DTOs")
    logger.info("   ✅ Security headers and CORS")
    logger.info("   ✅ Audit logging and monitoring")

    # Production configuration
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("ENVIRONMENT", "production") == "development"

    if debug:
        logger.warning("⚠️ Running in DEBUG mode - disable for production!")

    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)
