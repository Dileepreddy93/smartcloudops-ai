#!/usr/bin/env python3
"""
SmartCloudOps AI - Authentication System
========================================

Secure authentication using JWT tokens and proper API key management.
"""

import os
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Optional, Union

import jwt
from flask import current_app, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

# SECURITY: Use secure configuration manager for secrets
from app.config import config_manager

JWT_SECRET_KEY = config_manager.get_secret("JWT_SECRET_KEY", required=True)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# API Key management (in production, use a database)
API_KEYS = {
    "admin": {
        "key": config_manager.get_secret("ADMIN_API_KEY", required=True),
        "role": "admin",
        "permissions": ["read", "write", "admin", "ml", "remediation"],
    },
    "ml": {
        "key": config_manager.get_secret("ML_API_KEY", required=True),
        "role": "ml",
        "permissions": ["read", "ml"],
    },
    "readonly": {
        "key": config_manager.get_secret("READONLY_API_KEY", required=True),
        "role": "readonly",
        "permissions": ["read"],
    },
}

# User management (in production, use a database)
USERS = {
    "admin": {
        "username": "admin",
        "password_hash": generate_password_hash(config_manager.get_secret("ADMIN_PASSWORD", required=True)),
        "role": "admin",
        "permissions": ["read", "write", "admin", "ml", "remediation"],
    }
}


def generate_jwt_token(user_id: str, role: str, permissions: list) -> str:
    """Generate a JWT token for authenticated user."""
    payload = {
        "user_id": user_id,
        "role": role,
        "permissions": permissions,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Optional[Dict]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_api_key_info(api_key: str) -> Optional[Dict]:
    """Get API key information and validate it."""
    for key_id, key_info in API_KEYS.items():
        if key_info["key"] == api_key:
            return {
                "key_id": key_id,
                "role": key_info["role"],
                "permissions": key_info["permissions"],
            }
    return None


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user with username and password."""
    if username in USERS:
        user = USERS[username]
        if check_password_hash(user["password_hash"], password):
            return {
                "user_id": username,
                "role": user["role"],
                "permissions": user["permissions"],
            }
    return None


def require_auth(permissions: Optional[list] = None):
    """Decorator to require authentication and optional permissions."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check for JWT token first
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                payload = verify_jwt_token(token)
                if payload:
                    if permissions:
                        if not any(perm in payload.get("permissions", []) for perm in permissions):
                            return jsonify({"error": "Insufficient permissions"}), 403
                    return f(*args, **kwargs)

            # Fallback to API key authentication
            api_key = request.headers.get("X-API-Key")
            if not api_key:
                return jsonify({"error": "Authentication required"}), 401

            key_info = get_api_key_info(api_key)
            if not key_info:
                return jsonify({"error": "Invalid API key"}), 401

            if permissions:
                if not any(perm in key_info["permissions"] for perm in permissions):
                    return jsonify({"error": "Insufficient permissions"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def login_required(f):
    """Decorator to require login (username/password authentication)."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return jsonify({"error": "Basic authentication required"}), 401

        try:
            import base64

            credentials = base64.b64decode(auth_header.split(" ")[1]).decode("utf-8")
            username, password = credentials.split(":", 1)

            user_info = authenticate_user(username, password)
            if not user_info:
                return jsonify({"error": "Invalid credentials"}), 401

            return f(*args, **kwargs)
        except Exception:
            return jsonify({"error": "Invalid authentication format"}), 401

    return decorated_function


# Authentication endpoints
def create_auth_blueprint():
    """Create authentication blueprint with login and token endpoints."""
    from flask import Blueprint

    auth_bp = Blueprint("auth", __name__)

    @auth_bp.route("/login", methods=["POST"])
    def login():
        """Login endpoint for username/password authentication."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON data required"}), 400

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        user_info = authenticate_user(username, password)
        if not user_info:
            return jsonify({"error": "Invalid credentials"}), 401

        token = generate_jwt_token(user_info["user_id"], user_info["role"], user_info["permissions"])

        return jsonify(
            {
                "token": token,
                "user_id": user_info["user_id"],
                "role": user_info["role"],
                "permissions": user_info["permissions"],
                "expires_in": JWT_EXPIRATION_HOURS * 3600,
            }
        )

    @auth_bp.route("/verify", methods=["POST"])
    def verify_token():
        """Verify JWT token endpoint."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON data required"}), 400

        token = data.get("token")
        if not token:
            return jsonify({"error": "Token required"}), 400

        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        return jsonify(
            {
                "valid": True,
                "user_id": payload["user_id"],
                "role": payload["role"],
                "permissions": payload["permissions"],
            }
        )

    return auth_bp
