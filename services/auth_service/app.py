#!/usr/bin/env python3
"""
Authentication Service - SmartCloudOps AI
========================================

Microservice for handling authentication and authorization.
"""



import os
import time
import jwt
import bcrypt
import structlog
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
auth_requests_total = Counter('auth_requests_total', 'Total authentication requests', ['method', 'endpoint', 'status'])
auth_request_duration = Histogram('auth_request_duration_seconds', 'Authentication request duration')

@dataclass
class User:
    """User data model."""
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class AuthService:
    """Authentication service implementation."""
    
    def __init__(self):
        self.secret_key = os.getenv('SECRET_KEY')
        self.algorithm = 'HS256'
        self.token_expiry = int(os.getenv('JWT_EXPIRY_HOURS', '24'))
        
        # In-memory user store (replace with database in production)
        self.users = {
            'admin': User(
                id='1',
                username='admin',
                email='admin@smartcloudops.ai',
                role='admin',
                is_active=True,
                created_at=datetime.utcnow()
            ),
            'ml_user': User(
                id='2',
                username='ml_user',
                email='ml@smartcloudops.ai',
                role='ml',
                is_active=True,
                created_at=datetime.utcnow()
            ),
            'readonly_user': User(
                id='3',
                username='readonly_user',
                email='readonly@smartcloudops.ai',
                role='readonly',
                is_active=True,
                created_at=datetime.utcnow()
            )
        }
        
        # API key mapping
        self.api_keys = {
            os.getenv('ADMIN_API_KEY'): 'admin',
            os.getenv('ML_API_KEY'): 'ml_user',
            os.getenv('READONLY_API_KEY'): 'readonly_user'
        }
    
    def validate_api_key(self, api_key: str) -> Optional[User]:
        """Validate API key and return associated user."""
        if api_key in self.api_keys:
            username = self.api_keys[api_key]
            return self.users.get(username)
        return None
    
    def create_jwt_token(self, user: User) -> str:
        """Create JWT token for user."""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'exp': datetime.now(timezone.utc) + timedelta(hours=self.token_expiry),
            'iat': datetime.now(timezone.utc)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_jwt_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired", token=token[:10] + "...")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT token", error=str(e), token=token[:10] + "...")
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = self.users.get(username)
        if user and user.is_active:
            # In production, verify against stored password hash
            # For demo, accept any password for existing users
            return user
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        for user in self.users.values():
            if user.id == user_id:
                return user
        return None

# Initialize service
auth_service = AuthService()

# Create Flask app
app = Flask(__name__)
CORS(app)

@app.before_request
def before_request():
    """Log request details."""
    g.start_time = time.time()
    g.request_id = request.headers.get('X-Request-ID', 'unknown')
    
    logger.info(
        "Request started",
        method=request.method,
        path=request.path,
        remote_addr=request.remote_addr,
        request_id=g.request_id
    )

@app.after_request
def after_request(response):
    """Log response and record metrics."""
    duration = time.time() - g.start_time
    
    # Record metrics
    auth_requests_total.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code
    ).inc()
    
    auth_request_duration.observe(duration)
    
    # Log response
    logger.info(
        "Request completed",
        method=request.method,
        path=request.path,
        status_code=response.status_code,
        duration=duration,
        request_id=g.request_id
    )
    
    return response

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'auth-service',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0'
    })

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint."""
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                'error': 'Missing username or password',
                'code': 'MISSING_CREDENTIALS'
            }), 400
        
        username = data['username']
        password = data['password']
        
        # Authenticate user
        user = auth_service.authenticate_user(username, password)
        
        if not user:
            return jsonify({
                'error': 'Invalid credentials',
                'code': 'INVALID_CREDENTIALS'
            }), 401
        
        # Create JWT token
        token = auth_service.create_jwt_token(user)
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        
        logger.info(
            "User logged in successfully",
            username=username,
            role=user.role,
            request_id=g.request_id
        )
        
        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            },
            'expires_in': auth_service.token_expiry * 3600
        })
        
    except Exception as e:
        logger.error(
            "Login failed",
            error=str(e),
            request_id=g.request_id,
            exc_info=True
        )
        
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/auth/verify', methods=['POST'])
def verify_token():
    """Verify JWT token endpoint."""
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({
                'error': 'Missing token',
                'code': 'MISSING_TOKEN'
            }), 400
        
        token = data['token']
        
        # Verify token
        payload = auth_service.verify_jwt_token(token)
        
        if not payload:
            return jsonify({
                'error': 'Invalid or expired token',
                'code': 'INVALID_TOKEN'
            }), 401
        
        # Get user
        user = auth_service.get_user_by_id(payload['user_id'])
        
        if not user:
            return jsonify({
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        return jsonify({
            'valid': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            },
            'payload': payload
        })
        
    except Exception as e:
        logger.error(
            "Token verification failed",
            error=str(e),
            request_id=g.request_id,
            exc_info=True
        )
        
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/auth/api-key/verify', methods=['POST'])
def verify_api_key():
    """Verify API key endpoint."""
    try:
        data = request.get_json()
        
        if not data or 'api_key' not in data:
            return jsonify({
                'error': 'Missing API key',
                'code': 'MISSING_API_KEY'
            }), 400
        
        api_key = data['api_key']
        
        # Validate API key
        user = auth_service.validate_api_key(api_key)
        
        if not user:
            return jsonify({
                'error': 'Invalid API key',
                'code': 'INVALID_API_KEY'
            }), 401
        
        return jsonify({
            'valid': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        })
        
    except Exception as e:
        logger.error(
            "API key verification failed",
            error=str(e),
            request_id=g.request_id,
            exc_info=True
        )
        
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/auth/users/<user_id>', methods=['GET'])
def get_user(user_id: str):
    """Get user by ID endpoint."""
    try:
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        })
        
    except Exception as e:
        logger.error(
            "Get user failed",
            error=str(e),
            user_id=user_id,
            request_id=g.request_id,
            exc_info=True
        )
        
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        error=str(e),
        request_id=g.request_id,
        exc_info=True
    )
    
    return jsonify({
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR'
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(
        "Starting authentication service",
        port=port,
        debug=debug
    )
    
    app.run(host='0.0.0.0', port=port, debug=debug)
