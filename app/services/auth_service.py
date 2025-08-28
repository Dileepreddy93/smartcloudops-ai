#!/usr/bin/env python3
"""
SmartCloudOps AI - Authentication Service
=========================================

Dedicated service for handling authentication and authorization.
"""


import os
import time
import secrets

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

from .base_service import BaseService


class AuthenticationService(BaseService):
    """Service for handling authentication and authorization."""

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)

        # Validate and get JWT secret
        self.jwt_secret = self._get_secure_jwt_secret()
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = self.get_config("jwt_expiration_hours", 24)

        # Initialize API keys with proper validation
        self.api_keys = self._initialize_api_keys()

        # User management (in production, use a database)
        self.users = self._initialize_users()

        # Initialize the service
        self._initialize_service()

    def _get_secure_jwt_secret(self) -> str:
        """Get JWT secret with proper validation."""
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret:
            raise ValueError("JWT_SECRET_KEY environment variable is required")
        if len(jwt_secret) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return jwt_secret

    def _initialize_api_keys(self) -> Dict:
        """Initialize API keys with proper validation."""
        api_keys = {}

        # Admin API key
        admin_key = os.getenv("ADMIN_API_KEY")
        if not admin_key:
            raise ValueError("ADMIN_API_KEY environment variable is required")
        if len(admin_key) < 32:
            raise ValueError("ADMIN_API_KEY must be at least 32 characters long")

        api_keys["admin"] = {
            "key": admin_key,
            "role": "admin",
            "permissions": ["read", "write", "admin", "ml", "remediation"],
        }

        # ML API key
        ml_key = os.getenv("ML_API_KEY")
        if not ml_key:
            raise ValueError("ML_API_KEY environment variable is required")
        if len(ml_key) < 32:
            raise ValueError("ML_API_KEY must be at least 32 characters long")

        api_keys["ml"] = {"key": ml_key, "role": "ml", "permissions": ["read", "ml"]}

        # Readonly API key
        readonly_key = os.getenv("READONLY_API_KEY")
        if not readonly_key:
            raise ValueError("READONLY_API_KEY environment variable is required")
        if len(readonly_key) < 32:
            raise ValueError("READONLY_API_KEY must be at least 32 characters long")

        api_keys["readonly"] = {
            "key": readonly_key,
            "role": "readonly",
            "permissions": ["read"],
        }

        return api_keys

    def _initialize_users(self) -> Dict:
        """Initialize users with proper validation."""
        users = {}

        # Admin user
        admin_password = os.getenv("ADMIN_PASSWORD")
        if not admin_password:
            raise ValueError("ADMIN_PASSWORD environment variable is required")
        if len(admin_password) < 8:
            raise ValueError("ADMIN_PASSWORD must be at least 8 characters long")

        users["admin"] = {
            "username": "admin",
            "password_hash": generate_password_hash(admin_password),
            "role": "admin",
            "permissions": ["read", "write", "admin", "ml", "remediation"],
        }

        return users

    def _initialize_service(self) -> None:
        """Initialize the authentication service."""
        # Validate JWT secret
        if len(self.jwt_secret) < 32:
            raise ValueError("JWT secret is too short")

        # Validate API keys
        for key_id, key_info in self.api_keys.items():
            if len(key_info["key"]) < 32:
                raise ValueError(f"API key for {key_id} is too short")

        self.logger.info("Authentication service initialized with secure configuration")

    def generate_jwt_token(self, user_id: str, role: str, permissions: List[str]) -> str:
        """Generate a JWT token for authenticated user."""
        payload = {
            "user_id": user_id,
            "role": role,
            "permissions": permissions,
            "exp": datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours),
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16),  # JWT ID for uniqueness
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def verify_jwt_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            self.logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError:
            self.logger.warning("Invalid JWT token")
            return None

    def get_api_key_info(self, api_key: str) -> Optional[Dict]:
        """Get API key information and validate it."""
        for key_id, key_info in self.api_keys.items():
            if key_info["key"] == api_key:
                return {
                    "key_id": key_id,
                    "role": key_info["role"],
                    "permissions": key_info["permissions"],
                }
        return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with username and password."""
        if username in self.users:
            user = self.users[username]
            if check_password_hash(user["password_hash"], password):
                self.log_operation("user_login", {"username": username, "success": True})
                return {
                    "user_id": username,
                    "role": user["role"],
                    "permissions": user["permissions"],
                }

        self.log_operation("user_login", {"username": username, "success": False})
        return None

    def has_permission(self, user_permissions: List[str], required_permissions: List[str]) -> bool:
        """Check if user has required permissions."""
        return any(perm in user_permissions for perm in required_permissions)

    def create_user(self, username: str, password: str, role: str, permissions: List[str]) -> bool:
        """Create a new user."""
        if username in self.users:
            return False

        # Validate password strength
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        self.users[username] = {
            "username": username,
            "password_hash": generate_password_hash(password),
            "role": role,
            "permissions": permissions,
        }

        self.log_operation("user_created", {"username": username, "role": role})
        return True

    def update_user_permissions(self, username: str, permissions: List[str]) -> bool:
        """Update user permissions."""
        if username not in self.users:
            return False

        self.users[username]["permissions"] = permissions
        self.log_operation(
            "user_permissions_updated",
            {"username": username, "permissions": permissions},
        )
        return True

    def create_api_key(self, key_id: str, role: str, permissions: List[str]) -> str:
        """Create a new API key."""
        api_key = f"sk-{key_id}-{secrets.token_urlsafe(32)}"

        self.api_keys[key_id] = {
            "key": api_key,
            "role": role,
            "permissions": permissions,
        }

        self.log_operation("api_key_created", {"key_id": key_id, "role": role})
        return api_key

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        if key_id in self.api_keys:
            del self.api_keys[key_id]
            self.log_operation("api_key_revoked", {"key_id": key_id})
            return True
        return False

    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information."""
        if username in self.users:
            user = self.users[username].copy()
            user.pop("password_hash", None)  # Don't return password hash
            return user
        return None

    def list_users(self) -> List[Dict]:
        """List all users (without sensitive information)."""
        users = []
        for username, user in self.users.items():
            user_info = user.copy()
            user_info.pop("password_hash", None)
            users.append(user_info)
        return users

    def list_api_keys(self) -> List[Dict]:
        """List all API keys (without the actual keys)."""
        keys = []
        for key_id, key_info in self.api_keys.items():
            keys.append(
                {
                    "key_id": key_id,
                    "role": key_info["role"],
                    "permissions": key_info["permissions"],
                    "key_preview": (key_info["key"][:10] + "..." if len(key_info["key"]) > 10 else key_info["key"]),
                }
            )
        return keys
