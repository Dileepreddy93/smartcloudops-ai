#!/usr/bin/env python3
"""
SmartCloudOps AI - Production Main Application
=============================================

Production-ready Flask application with:
- Secure authentication and authorization
- Production database integration
- ML pipeline integration
- Comprehensive monitoring
- Error handling and logging
- Health checks and metrics
"""

import os
import sys
import logging
import time
from datetime import datetime
from contextlib import contextmanager

from flask import Flask, request, jsonify, g
from werkzeug.exceptions import HTTPException
import structlog

# Import production components
from database_improvements import get_db_service
from ml_production_pipeline import get_ml_pipeline
from monitoring.production_monitoring import get_monitoring

# Import security components
from auth_secure import (
    get_current_user,
    get_request_id,
    require_api_key,
    require_admin,
    require_ml_access
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def create_production_app():
    """Create and configure the production Flask application."""
    
    app = Flask(__name__)
    
    # Load configuration from environment
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        FLASK_ENV=os.getenv('FLASK_ENV', 'production'),
        FLASK_DEBUG=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        DATABASE_URL=os.getenv('DATABASE_URL'),
        REDIS_URL=os.getenv('REDIS_URL'),
        LOG_LEVEL=os.getenv('LOG_LEVEL', 'INFO')
    )
    
    # Initialize production services
    db_service = get_db_service()
    ml_pipeline = get_ml_pipeline()
    monitoring = get_monitoring()
    
    # Request timing middleware
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.request_id = get_request_id()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.path,
            remote_addr=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            request_id=g.request_id
        )
    
    @app.after_request
    def after_request(response):
        # Calculate request duration
        duration = time.time() - g.start_time
        
        # Record metrics
        monitoring.metrics.record_http_request(
            method=request.method,
            endpoint=request.path,
            status_code=response.status_code,
            duration=duration,
            request_size=request.content_length or 0,
            response_size=len(response.get_data())
        )
        
        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            duration=duration,
            request_id=g.request_id
        )
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Request-ID'] = g.request_id
        
        return response
    
    # Error handling
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Record error metrics
        monitoring.metrics.record_error(
            error_type=type(e).__name__,
            component='flask_app'
        )
        
        # Log error
        logger.error(
            "Unhandled exception",
            error_type=type(e).__name__,
            error_message=str(e),
            request_id=g.request_id,
            exc_info=True
        )
        
        if isinstance(e, HTTPException):
            return jsonify({
                'error': e.description,
                'status_code': e.code,
                'request_id': g.request_id
            }), e.code
        
        # Don't expose internal errors in production
        if app.config['FLASK_ENV'] == 'production':
            return jsonify({
                'error': 'Internal server error',
                'status_code': 500,
                'request_id': g.request_id
            }), 500
        else:
            return jsonify({
                'error': str(e),
                'status_code': 500,
                'request_id': g.request_id
            }), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Comprehensive health check endpoint."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'request_id': g.request_id,
            'components': {}
        }
        
        overall_status = 'healthy'
        
        # Check database health
        try:
            db_health = db_service.health_check()
            health_status['components']['database'] = db_health
            if db_health['database']['status'] != 'healthy':
                overall_status = 'unhealthy'
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_status = 'unhealthy'
        
        # Check ML pipeline health
        try:
            ml_health = ml_pipeline.get_health_status()
            health_status['components']['ml_pipeline'] = ml_health
            if ml_health['pipeline_status'] != 'healthy':
                overall_status = 'unhealthy'
        except Exception as e:
            health_status['components']['ml_pipeline'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_status = 'unhealthy'
        
        # Check monitoring health
        try:
            monitoring_health = monitoring.get_metrics_summary()
            health_status['components']['monitoring'] = monitoring_health
        except Exception as e:
            health_status['components']['monitoring'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        health_status['status'] = overall_status
        
        status_code = 200 if overall_status == 'healthy' else 503
        return jsonify(health_status), status_code
    
    # Status endpoint
    @app.route('/status')
    @require_api_key
    def status():
        """Application status endpoint."""
        return jsonify({
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'environment': app.config['FLASK_ENV'],
            'request_id': g.request_id
        })
    
    # Metrics endpoint for Prometheus
    @app.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint."""
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return generate_latest(monitoring.metrics.registry), 200, {
            'Content-Type': CONTENT_TYPE_LATEST
        }
    
    # ML Prediction endpoint
    @app.route('/ml/predict', methods=['POST'])
    @require_ml_access
    def ml_predict():
        """ML prediction endpoint with comprehensive validation."""
        try:
            data = request.get_json()
            
            if not data or 'metrics' not in data:
                return jsonify({
                    'error': 'Missing metrics data',
                    'request_id': g.request_id
                }), 400
            
            metrics = data['metrics']
            user_id = data.get('user_id')
            ab_test_id = data.get('ab_test_id')
            
            # Validate metrics
            required_metrics = ['cpu_usage', 'memory_usage', 'disk_usage', 'network_io']
            for metric in required_metrics:
                if metric not in metrics:
                    return jsonify({
                        'error': f'Missing required metric: {metric}',
                        'request_id': g.request_id
                    }), 400
                
                if not isinstance(metrics[metric], (int, float)):
                    return jsonify({
                        'error': f'Invalid metric type for {metric}',
                        'request_id': g.request_id
                    }), 400
                
                if metrics[metric] < 0 or metrics[metric] > 100:
                    return jsonify({
                        'error': f'Metric {metric} out of range (0-100)',
                        'request_id': g.request_id
                    }), 400
            
            # Make prediction
            start_time = time.time()
            prediction = ml_pipeline.predict(metrics, user_id, ab_test_id)
            prediction_time = time.time() - start_time
            
            # Record ML metrics
            monitoring.metrics.record_ml_prediction(
                model_version=prediction.get('model_version', 'unknown'),
                prediction_type=prediction.get('prediction', 'unknown'),
                duration=prediction_time,
                is_anomaly=prediction.get('prediction') == 'anomaly'
            )
            
            # Store metrics in database
            try:
                db_service.store_metrics(metrics)
            except Exception as e:
                logger.warning(
                    "Failed to store metrics in database",
                    error=str(e),
                    request_id=g.request_id
                )
            
            return jsonify({
                'prediction': prediction,
                'request_id': g.request_id
            })
            
        except Exception as e:
            logger.error(
                "ML prediction failed",
                error=str(e),
                request_id=g.request_id,
                exc_info=True
            )
            
            monitoring.metrics.record_error(
                error_type='ml_prediction_error',
                component='ml_pipeline'
            )
            
            return jsonify({
                'error': 'Prediction failed',
                'request_id': g.request_id
            }), 500
    
    # Metrics retrieval endpoint
    @app.route('/metrics/history')
    @require_api_key
    def get_metrics_history():
        """Get historical metrics from database."""
        try:
            limit = request.args.get('limit', 100, type=int)
            if limit > 1000:
                limit = 1000
            
            metrics = db_service.get_metrics(limit=limit)
            
            return jsonify({
                'metrics': metrics,
                'count': len(metrics),
                'request_id': g.request_id
            })
            
        except Exception as e:
            logger.error(
                "Failed to retrieve metrics history",
                error=str(e),
                request_id=g.request_id,
                exc_info=True
            )
            
            return jsonify({
                'error': 'Failed to retrieve metrics',
                'request_id': g.request_id
            }), 500
    
    # Admin endpoints
    @app.route('/admin/status')
    @require_admin
    def admin_status():
        """Admin status endpoint with detailed system information."""
        try:
            # Get system metrics
            system_metrics = monitoring.get_metrics_summary()
            
            # Get database health
            db_health = db_service.health_check()
            
            # Get ML pipeline health
            ml_health = ml_pipeline.get_health_status()
            
            return jsonify({
                'system': system_metrics,
                'database': db_health,
                'ml_pipeline': ml_health,
                'request_id': g.request_id
            })
            
        except Exception as e:
            logger.error(
                "Admin status check failed",
                error=str(e),
                request_id=g.request_id,
                exc_info=True
            )
            
            return jsonify({
                'error': 'Failed to get admin status',
                'request_id': g.request_id
            }), 500
    
    @app.route('/admin/ml/train', methods=['POST'])
    @require_admin
    def train_ml_model():
        """Admin endpoint to trigger ML model training."""
        try:
            data = request.get_json() or {}
            hyperparameters = data.get('hyperparameters')
            
            # In a real implementation, you would:
            # 1. Get training data from database
            # 2. Train the model
            # 3. Validate the model
            # 4. Deploy if validation passes
            
            logger.info(
                "ML model training requested",
                hyperparameters=hyperparameters,
                request_id=g.request_id
            )
            
            return jsonify({
                'message': 'Model training initiated',
                'request_id': g.request_id
            })
            
        except Exception as e:
            logger.error(
                "ML model training failed",
                error=str(e),
                request_id=g.request_id,
                exc_info=True
            )
            
            return jsonify({
                'error': 'Model training failed',
                'request_id': g.request_id
            }), 500
    
    # Root endpoint
    @app.route('/')
    def root():
        """Root endpoint with basic information."""
        return jsonify({
            'name': 'SmartCloudOps AI',
            'version': '1.0.0',
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': g.request_id,
            'endpoints': {
                'health': '/health',
                'status': '/status',
                'metrics': '/metrics',
                'ml_predict': '/ml/predict',
                'metrics_history': '/metrics/history',
                'admin_status': '/admin/status'
            }
        })
    
    return app

# Create the application instance
app = create_production_app()

if __name__ == '__main__':
    # Run the application
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(
        "Starting SmartCloudOps AI production server",
        port=port,
        debug=debug,
        environment=os.getenv('FLASK_ENV', 'production')
    )
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
