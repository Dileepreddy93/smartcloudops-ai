#!/usr/bin/env python3
"""
SmartCloudOps AI - Security Fixes Test Suite
===========================================

Test suite to verify that all security fixes are working correctly.
"""

import os
import sys
from app.services.auth_service import AuthenticationService


from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestSecurityFixes:
    """Test class for security fixes verification."""

    def setup_method(self):
        """Set up test environment."""
        # Set up test environment variables
        self.test_env_vars = {
            "JWT_SECRET_KEY": "test-jwt-secret-key-64-characters-long-for-testing-purposes-only",
            "ADMIN_API_KEY": "sk-admin-test-key-32-characters-long-for-testing",
            "ML_API_KEY": "sk-ml-test-key-32-characters-long-for-testing-only",
            "READONLY_API_KEY": "sk-readonly-test-key-32-chars-for-testing",
            "API_KEY_SALT": "test-salt-16-chars",
            "ADMIN_PASSWORD": "test-admin-password-16-chars",
        }

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_environment_variables(self):
        """Test that missing environment variables raise appropriate errors."""
        with pytest.raises(ValueError, match="JWT_SECRET_KEY environment variable is required"):
            AuthenticationService()

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "short",
            "ADMIN_API_KEY": "short",
            "ML_API_KEY": "short",
            "READONLY_API_KEY": "short",
            "API_KEY_SALT": "short",
            "ADMIN_PASSWORD": "short",
        },
    )
    def test_weak_environment_variables(self):
        """Test that weak environment variables raise appropriate errors."""
        with pytest.raises(ValueError, match="JWT_SECRET_KEY must be at least 32 characters long"):
            AuthenticationService()

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "test-jwt-secret-key-64-characters-long-for-testing-purposes-only",
            "ADMIN_API_KEY": "sk-admin-test-key-32-characters-long-for-testing",
            "ML_API_KEY": "sk-ml-test-key-32-characters-long-for-testing-only",
            "READONLY_API_KEY": "sk-readonly-test-key-32-chars-for-testing",
            "API_KEY_SALT": "test-salt-16-chars",
            "ADMIN_PASSWORD": "test-admin-password-16-chars",
        },
    )
    def test_valid_environment_variables(self):
        """Test that valid environment variables work correctly."""
        auth_service = AuthenticationService()
        assert auth_service is not None
        assert len(auth_service.jwt_secret) >= 32
        assert len(auth_service.api_keys["admin"]["key"]) >= 32

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "test-jwt-secret-key-64-characters-long-for-testing-purposes-only",
            "ADMIN_API_KEY": "sk-admin-test-key-32-characters-long-for-testing",
            "ML_API_KEY": "sk-ml-test-key-32-characters-long-for-testing-only",
            "READONLY_API_KEY": "sk-readonly-test-key-32-chars-for-testing",
            "API_KEY_SALT": "test-salt-16-chars",
            "ADMIN_PASSWORD": "test-admin-password-16-chars",
        },
    )
    def test_api_key_validation(self):
        """Test API key validation functionality."""
        auth_service = AuthenticationService()

        # Test valid admin key
        admin_key = auth_service.api_keys["admin"]["key"]
        key_info = auth_service.get_api_key_info(admin_key)
        assert key_info is not None
        assert key_info["role"] == "admin"
        assert "read" in key_info["permissions"]

        # Test invalid key
        invalid_key = "invalid-key"
        key_info = auth_service.get_api_key_info(invalid_key)
        assert key_info is None

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "test-jwt-secret-key-64-characters-long-for-testing-purposes-only",
            "ADMIN_API_KEY": "sk-admin-test-key-32-characters-long-for-testing",
            "ML_API_KEY": "sk-ml-test-key-32-characters-long-for-testing-only",
            "READONLY_API_KEY": "sk-readonly-test-key-32-chars-for-testing",
            "API_KEY_SALT": "test-salt-16-chars",
            "ADMIN_PASSWORD": "test-admin-password-16-chars",
        },
    )
    def test_jwt_token_generation(self):
        """Test JWT token generation and validation."""
        auth_service = AuthenticationService()

        # Generate token
        token = auth_service.generate_jwt_token(user_id="test_user", role="admin", permissions=["read", "write"])

        assert token is not None
        assert len(token) > 0

        # Verify token
        payload = auth_service.verify_jwt_token(token)
        assert payload is not None
        assert payload["user_id"] == "test_user"
        assert payload["role"] == "admin"
        assert "read" in payload["permissions"]

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "test-jwt-secret-key-64-characters-long-for-testing-purposes-only",
            "ADMIN_API_KEY": "sk-admin-test-key-32-characters-long-for-testing",
            "ML_API_KEY": "sk-ml-test-key-32-characters-long-for-testing-only",
            "READONLY_API_KEY": "sk-readonly-test-key-32-chars-for-testing",
            "API_KEY_SALT": "test-salt-16-chars",
            "ADMIN_PASSWORD": "test-admin-password-16-chars",
        },
    )
    def test_user_authentication(self):
        """Test user authentication functionality."""
        auth_service = AuthenticationService()

        # Test valid authentication
        admin_password = os.getenv("ADMIN_PASSWORD")
        user_info = auth_service.authenticate_user("admin", admin_password)
        assert user_info is not None
        assert user_info["user_id"] == "admin"
        assert user_info["role"] == "admin"

        # Test invalid authentication
        user_info = auth_service.authenticate_user("admin", "wrong_password")
        assert user_info is None

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "test-jwt-secret-key-64-characters-long-for-testing-purposes-only",
            "ADMIN_API_KEY": "sk-admin-test-key-32-characters-long-for-testing",
            "ML_API_KEY": "sk-ml-test-key-32-characters-long-for-testing-only",
            "READONLY_API_KEY": "sk-readonly-test-key-32-chars-for-testing",
            "API_KEY_SALT": "test-salt-16-chars",
            "ADMIN_PASSWORD": "test-admin-password-16-chars",
        },
    )
    def test_permission_checking(self):
        """Test permission checking functionality."""
        auth_service = AuthenticationService()

        # Test valid permissions
        user_permissions = ["read", "write", "admin"]
        assert auth_service.has_permission(user_permissions, ["read"])
        assert auth_service.has_permission(user_permissions, ["write"])
        assert auth_service.has_permission(user_permissions, ["admin"])

        # Test invalid permissions
        assert not auth_service.has_permission(user_permissions, ["invalid_permission"])

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "test-jwt-secret-key-64-characters-long-for-testing-purposes-only",
            "ADMIN_API_KEY": "sk-admin-test-key-32-characters-long-for-testing",
            "ML_API_KEY": "sk-ml-test-key-32-characters-long-for-testing-only",
            "READONLY_API_KEY": "sk-readonly-test-key-32-chars-for-testing",
            "API_KEY_SALT": "test-salt-16-chars",
            "ADMIN_PASSWORD": "test-admin-password-16-chars",
        },
    )
    def test_user_creation(self):
        """Test user creation functionality."""
        auth_service = AuthenticationService()

        # Test valid user creation
        success = auth_service.create_user(
            username="test_user", password="test-password-16-chars-long", role="user", permissions=["read"]
        )
        assert success is True

        # Test duplicate user creation
        success = auth_service.create_user(
            username="test_user", password="another-password", role="user", permissions=["read"]
        )
        assert success is False

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "test-jwt-secret-key-64-characters-long-for-testing-purposes-only",
            "ADMIN_API_KEY": "sk-admin-test-key-32-characters-long-for-testing",
            "ML_API_KEY": "sk-ml-test-key-32-characters-long-for-testing-only",
            "READONLY_API_KEY": "sk-readonly-test-key-32-chars-for-testing",
            "API_KEY_SALT": "test-salt-16-chars",
            "ADMIN_PASSWORD": "test-admin-password-16-chars",
        },
    )
    def test_weak_password_validation(self):
        """Test that weak passwords are rejected."""
        auth_service = AuthenticationService()

        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            auth_service.create_user(username="test_user", password="short", role="user", permissions=["read"])

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "test-jwt-secret-key-64-characters-long-for-testing-purposes-only",
            "ADMIN_API_KEY": "sk-admin-test-key-32-characters-long-for-testing",
            "ML_API_KEY": "sk-ml-test-key-32-characters-long-for-testing-only",
            "READONLY_API_KEY": "sk-readonly-test-key-32-chars-for-testing",
            "API_KEY_SALT": "test-salt-16-chars",
            "ADMIN_PASSWORD": "test-admin-password-16-chars",
        },
    )
    def test_api_key_creation(self):
        """Test API key creation functionality."""
        auth_service = AuthenticationService()

        # Create new API key
        new_key = auth_service.create_api_key(key_id="test_key", role="user", permissions=["read"])

        assert new_key is not None
        assert new_key.startswith("sk-test_key-")
        assert len(new_key) > 32

        # Verify the key is stored
        key_info = auth_service.get_api_key_info(new_key)
        assert key_info is not None
        assert key_info["role"] == "user"

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "test-jwt-secret-key-64-characters-long-for-testing-purposes-only",
            "ADMIN_API_KEY": "sk-admin-test-key-32-characters-long-for-testing",
            "ML_API_KEY": "sk-ml-test-key-32-characters-long-for-testing-only",
            "READONLY_API_KEY": "sk-readonly-test-key-32-chars-for-testing",
            "API_KEY_SALT": "test-salt-16-chars",
            "ADMIN_PASSWORD": "test-admin-password-16-chars",
        },
    )
    def test_api_key_revocation(self):
        """Test API key revocation functionality."""
        auth_service = AuthenticationService()

        # Create and then revoke API key
        new_key = auth_service.create_api_key(key_id="test_revoke", role="user", permissions=["read"])

        # Verify key exists
        key_info = auth_service.get_api_key_info(new_key)
        assert key_info is not None

        # Revoke key
        success = auth_service.revoke_api_key("test_revoke")
        assert success is True

        # Verify key is revoked
        key_info = auth_service.get_api_key_info(new_key)
        assert key_info is None

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "test-jwt-secret-key-64-characters-long-for-testing-purposes-only",
            "ADMIN_API_KEY": "sk-admin-test-key-32-characters-long-for-testing",
            "ML_API_KEY": "sk-ml-test-key-32-characters-long-for-testing-only",
            "READONLY_API_KEY": "sk-readonly-test-key-32-chars-for-testing",
            "API_KEY_SALT": "test-salt-16-chars",
            "ADMIN_PASSWORD": "test-admin-password-16-chars",
        },
    )
    def test_user_info_retrieval(self):
        """Test user information retrieval without sensitive data."""
        auth_service = AuthenticationService()

        # Get user info
        user_info = auth_service.get_user_info("admin")
        assert user_info is not None
        assert user_info["username"] == "admin"
        assert user_info["role"] == "admin"
        assert "password_hash" not in user_info  # Sensitive data should not be exposed

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "test-jwt-secret-key-64-characters-long-for-testing-purposes-only",
            "ADMIN_API_KEY": "sk-admin-test-key-32-characters-long-for-testing",
            "ML_API_KEY": "sk-ml-test-key-32-characters-long-for-testing-only",
            "READONLY_API_KEY": "sk-readonly-test-key-32-chars-for-testing",
            "API_KEY_SALT": "test-salt-16-chars",
            "ADMIN_PASSWORD": "test-admin-password-16-chars",
        },
    )
    def test_api_key_listing(self):
        """Test API key listing without exposing actual keys."""
        auth_service = AuthenticationService()

        # List API keys
        keys = auth_service.list_api_keys()
        assert len(keys) > 0

        for key_info in keys:
            assert "key_id" in key_info
            assert "role" in key_info
            assert "permissions" in key_info
            assert "key_preview" in key_info
            # Actual key should not be exposed
            assert "key" not in key_info


def test_security_audit_script():
    """Test that the security audit script can be imported and run."""
    try:
        from scripts.security_audit import SecurityAuditor

        auditor = SecurityAuditor()
        assert auditor is not None
    except ImportError as e:
        pytest.skip(f"Security audit script not available: {e}")


def test_verify_security_fixes_script():
    """Test that the security verification script can be imported."""
    try:
        from app.verify_security_fixes import verify_environment_variables

        assert callable(verify_environment_variables)
    except ImportError as e:
        pytest.skip(f"Security verification script not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
