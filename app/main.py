#!/usr/bin/env python3
"""
SmartCloudOps AI - Main Flask Application
========================================

Production-ready Flask application with secure configuration and standardized responses.
"""

import logging
from datetime import datetime

from flask import Flask, request
from flask_cors import CORS

from app.auth import create_auth_blueprint, require_auth
from app.config import config
from app.services.ml_service import ml_service
from app.utils.response import APIResponse, ErrorHandler, ResponseFormatter
from app.utils.validation import validate_json_payload, CHATOPS_COMMAND_SCHEMA, ML_PREDICTION_SCHEMA

logger = logging.getLogger(__name__)


def get_status_info() -> dict:
    """Get system status information."""
    try:
        # Get ML service health
        ml_health = ml_service.health_check()
        
        return {
            "status": "healthy",
            "message": "SmartCloudOps AI Platform is operational",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": {
                "ml_service": ml_health.get("status", "unknown"),
                "model_loaded": ml_health.get("model_loaded", False)
            }
        }
    except Exception as e:
        logger.error(f"Error getting status info: {e}")
        return {
            "status": "degraded",
            "message": "System status check failed",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


def get_logs_data() -> str:
    """Get application logs."""
    log_path = "logs/app.log"
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "No log file found"
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return f"Error reading logs: {e}"


def get_chat_response(user_query: str) -> str:
    """Get ChatOps response from AI service."""
    try:
        from app.services.chatops_service import chat
        return chat(user_query)
    except Exception as e:
        logger.error(f"ChatOps service error: {e}")
        return f"Sorry, I encountered an error: {str(e)}"


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Configure Flask
    app.config['SECRET_KEY'] = config.secret_key
    app.config['DEBUG'] = config.debug
    
    # Configure CORS
    CORS(app, origins=config.security.cors_origins)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register routes
    register_routes(app)
    
    logger.info("✅ Flask application created successfully")
    return app


def register_blueprints(app: Flask):
    """Register Flask blueprints."""
    try:
        # Authentication blueprint
        auth_bp = create_auth_blueprint()
        app.register_blueprint(auth_bp, url_prefix="/auth")
        
        # API v1 blueprints
        from app.api.v1 import health as health_v1
        from app.api.v1 import chatops as chatops_v1
        from app.api.v1 import logs as logs_v1
        from app.api.v1 import ml as ml_v1
        from app.api.v1 import metrics as metrics_v1
        from app.api.v1 import remediation as remediation_v1
        from app.api.v1 import integration as integration_v1
        
        app.register_blueprint(health_v1.bp)
        app.register_blueprint(chatops_v1.bp)
        app.register_blueprint(logs_v1.bp)
        app.register_blueprint(ml_v1.bp)
        app.register_blueprint(metrics_v1.bp)
        app.register_blueprint(remediation_v1.bp)
        app.register_blueprint(integration_v1.bp)
        
        # Phase 5 routes
        from app.routes.phase5_routes import phase5_bp
        app.register_blueprint(phase5_bp)
        
        logger.info("✅ All blueprints registered successfully")
        
    except ImportError as e:
        logger.warning(f"⚠️ Some blueprints could not be imported: {e}")
        logger.info("ℹ️ Using fallback routes")


def register_error_handlers(app: Flask):
    """Register error handlers."""
    
    @app.errorhandler(400)
    def bad_request(error):
        return APIResponse.error("Bad request", 400)
    
    @app.errorhandler(401)
    def unauthorized(error):
        return APIResponse.unauthorized()
    
    @app.errorhandler(403)
    def forbidden(error):
        return APIResponse.forbidden()
    
    @app.errorhandler(404)
    def not_found(error):
        return APIResponse.not_found()
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return APIResponse.error("Method not allowed", 405)
    
    @app.errorhandler(500)
    def internal_error(error):
        return ErrorHandler.handle_internal_error(error)
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        return ErrorHandler.handle_internal_error(error)


def register_routes(app: Flask):
    """Register application routes."""
    
    @app.route("/")
    @require_auth(["read"])
    def home():
        """Home endpoint."""
        return ResponseFormatter.format_health_check(
            status="operational",
            details={
                "service": "SmartCloudOps AI",
                "version": "1.0.0"
            }
        )
    
    @app.route("/status")
    @require_auth(["read"])
    def status():
        """System status endpoint."""
        status_info = get_status_info()
        return APIResponse.success(
            data=status_info,
            message="System status retrieved successfully"
        )
    
    @app.route("/query", methods=["POST"])
    @require_auth(["read", "write"])
    def query():
        """ChatOps query endpoint."""
        try:
            # Validate request
            data = request.get_json(silent=True)
            if not data:
                return APIResponse.error("Invalid JSON payload", 400)
            
            validated_data = validate_json_payload(data, CHATOPS_COMMAND_SCHEMA)
            user_query = validated_data["command"]
            
            # Get response
            ai_response = get_chat_response(user_query)
            
            return ResponseFormatter.format_chatops_response(
                response=ai_response,
                intent="general_query"
            )
            
        except Exception as e:
            logger.error(f"Query endpoint error: {e}")
            return ErrorHandler.handle_internal_error(e)
    
    @app.route("/logs")
    @require_auth(["read"])
    def logs():
        """Logs endpoint."""
        try:
            content = get_logs_data()
            return ResponseFormatter.format_logs(content)
            
        except Exception as e:
            logger.error(f"Logs endpoint error: {e}")
            return ErrorHandler.handle_internal_error(e)
    
    @app.route("/ml/predict", methods=["POST"])
    @require_auth(["ml"])
    def ml_predict():
        """ML prediction endpoint."""
        try:
            # Validate request
            data = request.get_json(silent=True)
            if not data:
                return APIResponse.error("Invalid JSON payload", 400)
            
            validated_data = validate_json_payload(data, ML_PREDICTION_SCHEMA)
            metrics = validated_data["metrics"]
            
            # Make prediction
            prediction = ml_service.predict_anomaly(metrics)
            
            return ResponseFormatter.format_ml_prediction(prediction)
            
        except Exception as e:
            logger.error(f"ML prediction error: {e}")
            return ErrorHandler.handle_ml_error(e)
    
    @app.route("/ml/health")
    @require_auth(["read"])
    def ml_health():
        """ML service health endpoint."""
        try:
            health = ml_service.health_check()
            return APIResponse.success(
                data=health,
                message="ML service health check completed"
            )
            
        except Exception as e:
            logger.error(f"ML health check error: {e}")
            return ErrorHandler.handle_ml_error(e)
    
    @app.route("/ml/model-info")
    @require_auth(["read"])
    def ml_model_info():
        """ML model information endpoint."""
        try:
            model_info = ml_service.get_model_info()
            return APIResponse.success(
                data=model_info,
                message="Model information retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"ML model info error: {e}")
            return ErrorHandler.handle_ml_error(e)
    
    @app.route("/health")
    def health():
        """Health check endpoint (no auth required)."""
        try:
            status_info = get_status_info()
            return ResponseFormatter.format_health_check(
                status=status_info["status"],
                details={
                    "services": status_info.get("services", {}),
                    "timestamp": status_info["timestamp"]
                }
            )
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return APIResponse.error(
                "Health check failed",
                status_code=503,
                error_code="HEALTH_CHECK_FAILED"
            )


# Create app instance for Gunicorn
app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0", 
        port=5000,
        debug=config.debug
    )
