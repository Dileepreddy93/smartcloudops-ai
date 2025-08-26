#!/usr/bin/env python3
"""
SmartCloudOps AI - Production Flask Application
==============================================

Security-hardened multi-AI ChatOps application with real data ML integration.
"""

import logging
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from flask import Flask, jsonify, request

# Secure path handling for ML imports
app_dir = Path(__file__).parent
scripts_dir = app_dir.parent / "scripts"
if scripts_dir.exists():
    sys.path.insert(0, str(scripts_dir))

# Import configuration manager
try:
    from config import config, logger
except ImportError:
    # Fallback logging if config import fails
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    config = None
    logger.warning("Config module not available, using fallback configuration")

# Import authentication module
try:
    from auth import auth, require_admin, require_api_key, require_read, require_write

    AUTH_AVAILABLE = True
    logger.info("✅ Authentication module loaded")
except ImportError as e:
    AUTH_AVAILABLE = False
    logger.error(f"❌ Authentication module not available: {e}")

    # Create dummy decorators for fallback
    def require_api_key(permissions=None):
        def decorator(f):
            return f

        return decorator

    require_read = require_write = require_admin = require_api_key

# Import database integration
try:
    from app.database_integration import db_service

    DATABASE_AVAILABLE = True
    logger.info("✅ Database integration loaded")
except ImportError:
    try:
        # Try local import
        from database_integration import db_service  # type: ignore

        DATABASE_AVAILABLE = True
        logger.info("✅ Database integration loaded (local)")
    except ImportError as e:
        DATABASE_AVAILABLE = False
        db_service = None  # type: ignore
        logger.warning(f"⚠️ Database integration not available: {e}")

# Import secrets manager for Phase 3 integration
try:
    from secrets_manager import secrets_manager

    SECRETS_MANAGER_AVAILABLE = True
    logger.info("✅ AWS Secrets Manager integration loaded")
except ImportError as e:
    SECRETS_MANAGER_AVAILABLE = False
    logger.warning(f"⚠️ AWS Secrets Manager not available: {e}")
    secrets_manager = None

# AI Provider Imports with error handling
OPENAI_AVAILABLE = False
GEMINI_AVAILABLE = False

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
    logger.info("✅ OpenAI module available")
except ImportError as e:
    logger.warning(f"❌ OpenAI not available: {e}")

try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
    logger.info("✅ Gemini module available")
except ImportError as e:
    logger.warning(f"❌ Gemini not available: {e}")

# ML Engine Imports with error handling
ML_ENGINE_AVAILABLE = False
RealDataInferenceEngine = None
MLModel = None

try:
    from real_data_inference_engine import RealDataInferenceEngine  # type: ignore

    ML_ENGINE_AVAILABLE = True
    logger.info("✅ Real Data ML Engine available")
except ImportError as e:
    logger.warning(f"❌ Real Data ML Engine not available: {e}")
    try:
        # Fallback to Phase 3 ML
        from phase3_anomaly_detection import MLModel  # type: ignore

        ML_ENGINE_AVAILABLE = True
        logger.info("✅ Phase 3 ML Engine available as fallback")
    except ImportError as e2:
        logger.error(f"❌ No ML Engine available: {e2}")

# Initialize Flask app with secure configuration
app = Flask(__name__)

# Configure Flask with secure settings
try:
    app.config["SECRET_KEY"] = config.secret_key
    app.config["DEBUG"] = config.debug

    # Security headers
    app.config["SESSION_COOKIE_SECURE"] = config.environment == "production"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Content security
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

    logger.info(f"✅ Flask configured securely for {config.environment}")

except Exception as e:
    logger.error(f"❌ Failed to configure Flask with secure config: {e}")
    # Emergency fallback
    app.config["SECRET_KEY"] = os.urandom(32)
    app.config["DEBUG"] = False
    logger.warning("🚨 Using emergency Flask configuration")

# Initialize authentication
if AUTH_AVAILABLE:
    auth.init_app(app)
    logger.info("✅ API Authentication enabled")
else:
    logger.warning("⚠️ API Authentication disabled - fallback mode")


# 🔒 SECURITY: Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    # Add authentication info to response headers (if authenticated)
    if hasattr(request, "auth_info") and request.auth_info:
        response.headers["X-Auth-User"] = request.auth_info.get("name", "unknown")

    return response


# 🔒 SECURITY: Input validation functions


def validate_and_sanitize_input(text, max_length=1000):
    """Validate and sanitize user input"""
    if not text or not isinstance(text, str):
        raise ValueError("Invalid input: must be non-empty string")

    if len(text) > max_length:
        raise ValueError(f"Input too long: maximum {max_length} characters")

    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', "", text)

    # HTML escape for XSS prevention
    text = escape(text)

    # Limit to printable ASCII + basic unicode
    text = "".join(char for char in text if char.isprintable() or char.isspace())

    return text.strip()


def validate_json_input(data, required_fields):
    """Validate JSON input structure"""
    if not isinstance(data, dict):
        raise ValueError("Invalid input: must be JSON object")

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    return True


# Prometheus metrics support
try:
    from prometheus_client import (
        Counter,
        Histogram,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True

    # Define metrics
    REQUEST_COUNT = Counter(
        "smartcloudops_requests_total", "Total requests", ["method", "endpoint"]
    )
    REQUEST_DURATION = Histogram(
        "smartcloudops_request_duration_seconds", "Request duration"
    )
    ML_PREDICTIONS = Counter(
        "smartcloudops_ml_predictions_total", "Total ML predictions", ["status"]
    )
    AI_REQUESTS = Counter(
        "smartcloudops_ai_requests_total", "Total AI requests", ["provider"]
    )

    logger.info("✅ Prometheus metrics initialized")
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("❌ Prometheus client not available")


# AI Configuration with Secure Secret Management
def get_ai_api_keys():
    """Get AI API keys from secure configuration with proper fallback chain"""
    try:
        # Use the secure configuration manager
        openai_key = config.ai.openai_api_key
        gemini_key = config.ai.gemini_api_key
        anthropic_key = config.ai.anthropic_api_key

        keys_found = []
        if openai_key:
            keys_found.append("OpenAI")
        if gemini_key:
            keys_found.append("Gemini")
        if anthropic_key:
            keys_found.append("Anthropic")

        if keys_found:
            logger.info(f"✅ AI API keys available: {', '.join(keys_found)}")
        else:
            logger.warning("⚠️ No AI API keys available - using fallback mode")

        return {
            "openai": openai_key,
            "gemini": gemini_key,
            "anthropic": anthropic_key,
            "provider": config.ai.provider,
        }

    except Exception as e:
        logger.error(f"❌ Failed to retrieve AI keys: {e}")
        return {
            "openai": None,
            "gemini": None,
            "anthropic": None,
            "provider": "fallback",
        }


# Get API keys using the new secure method
ai_keys = get_ai_api_keys()
OPENAI_API_KEY = ai_keys["openai"]
GEMINI_API_KEY = ai_keys["gemini"]
ANTHROPIC_API_KEY = ai_keys["anthropic"]
AI_PROVIDER = ai_keys["provider"]

# Initialize AI clients with error handling
openai_client = None
gemini_model = None

if OPENAI_AVAILABLE and OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("✅ OpenAI client initialized")
    except Exception as e:
        logger.error(f"❌ OpenAI client initialization failed: {e}")

if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-2.0-flash-exp")
        logger.info("✅ Gemini 2.0 Flash client initialized")
    except Exception as e:
        logger.error(f"❌ Gemini client initialization failed: {e}")

# Determine active AI provider
if AI_PROVIDER == "auto":
    if gemini_model:
        AI_PROVIDER = "gemini"
    elif openai_client:
        AI_PROVIDER = "openai"
    else:
        AI_PROVIDER = "fallback"

logger.info(f"🤖 Active AI Provider: {AI_PROVIDER.upper()}")

# ML Engine Configuration with improved error handling
ML_ENGINE_TYPE = "none"
ml_engine_instance = None

# Get ML engine setting from environment
ml_engine_preference = os.getenv("ML_ENGINE", "auto")

if ML_ENGINE_AVAILABLE:
    try:
        if ml_engine_preference == "real_data" and RealDataInferenceEngine:
            ml_engine_instance = RealDataInferenceEngine()
            ML_ENGINE_TYPE = "real_data"
            logger.info("✅ Real Data ML Engine initialized")
        elif ml_engine_preference == "secure" or ml_engine_preference == "production":
            # Try to load secure enhanced engine
            try:
                from secure_ml_inference_engine import get_secure_inference_engine

                ml_engine_instance = get_secure_inference_engine()
                ML_ENGINE_TYPE = "secure_enhanced"
                logger.info("✅ Secure ML Engine initialized")
            except ImportError:
                logger.warning(
                    "Secure ML Engine not available, falling back to real_data"
                )
                ml_engine_instance = RealDataInferenceEngine()  # type: ignore
                ML_ENGINE_TYPE = "real_data"
        elif ml_engine_preference == "phase3" and MLModel:
            ml_engine_instance = MLModel()  # type: ignore
            ML_ENGINE_TYPE = "phase3"
            logger.info("✅ Phase 3 ML Engine initialized")
        elif ml_engine_preference == "auto":
            # Auto-detection: prefer secure > real_data > phase3
            try:
                from secure_ml_inference_engine import get_secure_inference_engine

                ml_engine_instance = get_secure_inference_engine()
                ML_ENGINE_TYPE = "secure_enhanced"
                logger.info("✅ Secure ML Engine auto-selected")
            except ImportError:
                if RealDataInferenceEngine:
                    ml_engine_instance = RealDataInferenceEngine()  # type: ignore
                    ML_ENGINE_TYPE = "real_data"
                    logger.info("✅ Real Data ML Engine auto-selected")
                elif MLModel:
                    ml_engine_instance = MLModel()  # type: ignore
                    ML_ENGINE_TYPE = "phase3"
                    logger.info("✅ Phase 3 ML Engine auto-selected")
        else:
            logger.warning(
                f"⚠️ Requested ML engine '{ml_engine_preference}' not available"
            )
    except Exception as e:
        logger.error(f"❌ ML Engine initialization failed: {e}")
        ML_ENGINE_TYPE = "none"
else:
    logger.warning("⚠️ No ML engines available")


def get_inference_engine():
    """Get the available inference engine."""
    if ML_ENGINE_TYPE == "real_data" and ml_engine_instance:
        return ml_engine_instance
    elif ML_ENGINE_TYPE == "phase3" and ml_engine_instance:
        return ml_engine_instance
    else:
        return None


def get_real_inference_engine():
    """Get real data inference engine if available."""
    if ML_ENGINE_TYPE == "real_data" and ml_engine_instance:
        return ml_engine_instance
    return None


# Enhanced DevOps assistant prompt
DEVOPS_PROMPT = """You are an intelligent DevOps assistant for SmartCloudOps AI. 
You help with infrastructure monitoring, troubleshooting, and automation tasks.
Provide concise, actionable responses for DevOps operations."""


def process_with_ai(user_query):
    """Multi-AI processing with provider selection and error handling"""
    try:
        if AI_PROVIDER == "gemini" and gemini_model:
            return process_with_gemini(user_query)
        elif AI_PROVIDER == "openai" and openai_client:
            return process_with_openai(user_query)
        else:
            return process_fallback(user_query)
    except Exception as e:
        logger.error(f"AI processing error: {e}")
        return f"AI processing temporarily unavailable. Error: {str(e)}"


def process_with_gemini(user_query):
    """Process query with Gemini"""
    try:
        response = gemini_model.generate_content(
            f"{DEVOPS_PROMPT}\n\nUser: {user_query}"
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini processing error: {e}")
        return f"Gemini AI temporarily unavailable: {str(e)}"


def process_with_openai(user_query):
    """Process query with OpenAI"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": DEVOPS_PROMPT},
                {"role": "user", "content": user_query},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI processing error: {e}")
        return f"OpenAI temporarily unavailable: {str(e)}"


def process_fallback(user_query):
    """Fallback processing when AI is unavailable"""
    logger.info("Using fallback AI processing")

    # Simple keyword-based responses
    query_lower = user_query.lower()

    if any(word in query_lower for word in ["status", "health", "check"]):
        return "System status: Monitoring active. Use /status endpoint for detailed health information."
    elif any(word in query_lower for word in ["cpu", "memory", "disk"]):
        return "Resource monitoring: Check /ml/metrics endpoint for current infrastructure metrics."
    elif any(word in query_lower for word in ["anomaly", "alert", "error"]):
        return "Anomaly detection: Use /ml/predict endpoint for real-time anomaly detection."
    else:
        return f"DevOps Assistant: Received '{user_query}'. Available endpoints: /status, /ml/health, /ml/predict, /ml/metrics"


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return (
        jsonify(
            {
                "error": "Not Found",
                "message": "The requested endpoint does not exist",
                "available_endpoints": [
                    "/status",
                    "/chat",
                    "/ml/health",
                    "/ml/predict",
                    "/ml/metrics",
                ],
            }
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return (
        jsonify(
            {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        500,
    )


@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    logger.error(traceback.format_exc())
    return (
        jsonify(
            {
                "error": "Application Error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        500,
    )


# Routes
@app.route("/status")
@require_read()
def status():
    """Application health status - requires read access"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "3.1.0",
            "environment": config.environment if config else "unknown",
            "ai_provider": AI_PROVIDER,
            "ml_engine": ML_ENGINE_TYPE,
            "features": {
                "openai": OPENAI_AVAILABLE and bool(openai_client),
                "gemini": GEMINI_AVAILABLE and bool(gemini_model),
                "ml_inference": ML_ENGINE_AVAILABLE and bool(ml_engine_instance),
            },
            "auth": {
                "authenticated": hasattr(request, "auth_info"),
                "user": (
                    request.auth_info.get("name", "unknown")
                    if hasattr(request, "auth_info")
                    else None
                ),
            },
        }
    )


@app.route("/chat", methods=["POST"])
@require_write()
def chat():
    """Multi-AI chat endpoint with security validation - requires write access"""
    try:
        # Track metrics if available
        if PROMETHEUS_AVAILABLE:
            AI_REQUESTS.labels(provider=AI_PROVIDER).inc()

        # 🔒 SECURITY: Validate JSON structure
        data = request.get_json()
        validate_json_input(data, ["message"])

        # 🔒 SECURITY: Validate and sanitize input
        user_message = validate_and_sanitize_input(data["message"], max_length=500)

        # Log authenticated request
        user_name = (
            request.auth_info.get("name", "unknown")
            if hasattr(request, "auth_info")
            else "anonymous"
        )
        logger.info(f"Chat request from {user_name}: {user_message[:50]}...")

        # Process with AI
        ai_response = process_with_ai(user_message)

        return jsonify(
            {
                "response": ai_response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "provider": AI_PROVIDER,
                "status": "success",
                "user": user_name,
            }
        )

    except ValueError as e:
        logger.warning(f"Invalid input in chat endpoint: {e}")
        return (
            jsonify(
                {
                    "error": "Invalid input",
                    "message": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            400,
        )
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return (
            jsonify(
                {
                    "error": "Chat processing failed",
                    "message": "An unexpected error occurred",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@app.route("/ml/health")
@require_read()
def ml_health():
    """ML inference engine health check - requires read access"""
    try:
        if not ML_ENGINE_AVAILABLE:
            return (
                jsonify(
                    {
                        "status": "unavailable",
                        "message": "No ML engine available",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                503,
            )

        inference_engine = get_inference_engine()
        if not inference_engine:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "ML engine not initialized",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                503,
            )

        # Get health status from ML engine
        try:
            health_status = inference_engine.health_check()
            return jsonify(
                {
                    "status": "healthy",
                    "engine_type": ML_ENGINE_TYPE,
                    "health_details": health_status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"ML health check failed: {e}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Health check failed",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"ML health endpoint error: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Health check unavailable",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@app.route("/ml/predict", methods=["POST"])
@require_write()
def ml_predict():
    """ML anomaly prediction endpoint - requires write access"""
    try:
        # 🔒 SECURITY: Validate JSON structure
        data = request.get_json()
        validate_json_input(data, ["metrics"])

        # Track metrics if available
        if PROMETHEUS_AVAILABLE:
            ML_PREDICTIONS.labels(status="attempted").inc()

        if not ML_ENGINE_AVAILABLE:
            return (
                jsonify(
                    {
                        "error": "ML engine unavailable",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                503,
            )

        inference_engine = get_inference_engine()
        if not inference_engine:
            return (
                jsonify(
                    {
                        "error": "ML engine not initialized",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                503,
            )

        # Get prediction with audit logging
        metrics = data["metrics"]
        user_name = (
            request.auth_info.get("name", "anonymous")
            if hasattr(request, "auth_info")
            else "anonymous"
        )

        # Enhanced prediction call with user context and error handling
        if hasattr(inference_engine, "predict_anomaly"):
            # Use new secure engine API if available
            prediction = inference_engine.predict_anomaly(metrics, user_id=user_name)
        else:
            # Fallback to old API
            prediction = inference_engine.predict(metrics)

        # Store prediction in database if available
        if DATABASE_AVAILABLE and db_service.is_available():
            stored = db_service.store_prediction(metrics, prediction)
            if stored:
                logger.info("✅ Prediction stored in database")
            else:
                logger.warning("⚠️ Failed to store prediction in database")

        # Log prediction request with enhanced details
        logger.info(
            f"ML prediction request from {user_name}: "
            f"anomaly={prediction.get('anomaly', False)}, "
            f"confidence={prediction.get('confidence', 0):.3f}"
        )

        if PROMETHEUS_AVAILABLE:
            ML_PREDICTIONS.labels(status="success").inc()

        return jsonify(
            {
                "prediction": prediction,
                "engine_type": ML_ENGINE_TYPE,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user": user_name,
            }
        )

    except ValueError as e:
        logger.warning(f"Invalid input in ML predict endpoint: {e}")
        if PROMETHEUS_AVAILABLE:
            ML_PREDICTIONS.labels(status="validation_error").inc()
        return (
            jsonify(
                {
                    "error": "Invalid input",
                    "message": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            400,
        )
    except Exception as e:
        logger.error(f"ML predict endpoint error: {e}")
        if PROMETHEUS_AVAILABLE:
            ML_PREDICTIONS.labels(status="error").inc()
        return (
            jsonify(
                {
                    "error": "Prediction failed",
                    "message": "An unexpected error occurred",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@app.route("/ml/metrics")
@require_admin()
def ml_metrics():
    """Current infrastructure metrics - requires admin access"""
    try:
        # 🔒 SECURITY: Admin-only endpoint for ML metrics

        # Get metrics from database if available
        if DATABASE_AVAILABLE and db_service.is_available():
            performance_summary = db_service.get_performance_summary()
            latest_metrics = db_service.get_latest_metrics(10)
            recent_anomalies = db_service.get_anomalies(5)
            model_info = db_service.get_model_info()

            metrics = {
                "source": "database",
                "performance_summary": performance_summary,
                "latest_metrics": latest_metrics,
                "recent_anomalies": recent_anomalies,
                "model_info": model_info,
                "database_status": "connected",
            }
        else:
            # Fallback to inference engine
            engine = get_inference_engine()
            if engine and hasattr(engine, "get_current_metrics"):
                metrics = engine.get_current_metrics()
                metrics["source"] = "inference_engine"
                metrics["database_status"] = "unavailable"
            else:
                metrics = {
                    "source": "fallback",
                    "error": "No metrics sources available",
                    "database_status": "unavailable",
                    "inference_engine_status": "unavailable",
                }

        # Add authentication info
        user_name = (
            request.auth_info.get("name", "unknown")
            if hasattr(request, "auth_info")
            else "anonymous"
        )
        logger.info(f"ML metrics accessed by admin user: {user_name}")

        return jsonify(
            {
                "metrics": metrics,
                "engine_type": ML_ENGINE_TYPE,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "accessed_by": user_name,
            }
        )

    except Exception as e:
        logger.error(f"Metrics collection error: {e}")
        return (
            jsonify(
                {
                    "error": "Metrics collection failed",
                    "message": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@app.route("/metrics")
@require_admin()
def prometheus_metrics():
    """Prometheus metrics endpoint - requires admin access"""
    try:
        # 🔒 SECURITY: Admin-only Prometheus metrics
        if not PROMETHEUS_AVAILABLE:
            return (
                "# Prometheus client not available\n",
                200,
                {"Content-Type": "text/plain"},
            )

        # Log metrics access
        user_name = (
            request.auth_info.get("name", "unknown")
            if hasattr(request, "auth_info")
            else "anonymous"
        )
        logger.info(f"Prometheus metrics accessed by admin user: {user_name}")

        # Generate and return Prometheus metrics
        return (
            generate_latest(),
            200,
            {"Content-Type": "text/plain; version=0.0.4; charset=utf-8"},
        )
    except Exception as e:
        logger.error(f"Prometheus metrics endpoint error: {e}")
        return "# Error generating metrics\n", 500, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = config.debug if config else False

    logger.info(f"🚀 Starting SmartCloudOps AI on port {port}")
    logger.info(f"🔧 Debug mode: {debug}")
    logger.info(f"🤖 AI Provider: {AI_PROVIDER}")
    logger.info(f"🧠 ML Engine: {ML_ENGINE_TYPE}")

    # 🚨 SECURITY: Never use Flask development server in production!
    # This code should only run in development environments
    if os.getenv("ENVIRONMENT", "development") == "development":
        logger.warning("⚠️ Using Flask development server - NOT for production!")
        app.run(host="127.0.0.1", port=port, debug=debug)
    else:
        logger.error("❌ SECURITY: Use Gunicorn in production, not Flask dev server!")
        logger.error("Run: gunicorn --bind 0.0.0.0:5000 --workers 2 app.main:app")
        exit(1)
