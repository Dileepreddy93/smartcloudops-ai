#!/usr/bin/env python3
"""
SmartCloudOps AI - Secrets Manager
==================================

Secure secrets management using environment variables and AWS Secrets Manager.
"""


import json
import logging
import os
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class SecretsManager:
    """Secure secrets management for SmartCloudOps AI."""

    def __init__(self, use_aws_secrets_manager: bool = True):
        """Initialize secrets manager."""
        self.use_aws_secrets_manager = use_aws_secrets_manager

        if use_aws_secrets_manager:
            try:
                self.secrets_client = boto3.client("secretsmanager")
                logger.info("✅ AWS Secrets Manager client initialized")
            except NoCredentialsError:
                logger.warning("⚠️ AWS credentials not found, falling back to environment variables")
                self.use_aws_secrets_manager = False
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize AWS Secrets Manager: {e}")
                self.use_aws_secrets_manager = False

        # Load secrets from environment variables as fallback
        self._load_environment_secrets()

    def _load_environment_secrets(self):
        """Load secrets from environment variables."""
        self.secrets = {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "gemini_api_key": os.getenv("GEMINI_API_KEY"),
            "admin_api_key": os.getenv("ADMIN_API_KEY"),
            "ml_api_key": os.getenv("ML_API_KEY"),
            "readonly_api_key": os.getenv("READONLY_API_KEY"),
            "jwt_secret_key": os.getenv("JWT_SECRET_KEY"),
            "database_password": os.getenv("DATABASE_PASSWORD"),
            "admin_password": os.getenv("ADMIN_PASSWORD"),
        }

        # Validate required secrets
        self._validate_secrets()

    def _validate_secrets(self):
        """Validate that required secrets are present."""
        required_secrets = [
            "admin_api_key",
            "ml_api_key",
            "readonly_api_key",
            "jwt_secret_key",
        ]

        missing_secrets = []
        for secret in required_secrets:
            if not self.secrets.get(secret):
                missing_secrets.append(secret)

        if missing_secrets:
            logger.warning(f"⚠️ Missing required secrets: {missing_secrets}")
            logger.warning("   Set environment variables or use AWS Secrets Manager")

    def get_secret(self, secret_name: str) -> Optional[str]:
        """Get a secret value."""
        # Try AWS Secrets Manager first
        if self.use_aws_secrets_manager:
            try:
                response = self.secrets_client.get_secret_value(SecretId=secret_name)
                if "SecretString" in response:
                    secret_data = json.loads(response["SecretString"])
                    return secret_data.get("value") or secret_data.get("secret")
                return response.get("SecretBinary")
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    logger.warning(f"Secret {secret_name} not found in AWS Secrets Manager")
                else:
                    logger.error(f"Error retrieving secret {secret_name}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error retrieving secret {secret_name}: {e}")

        # Fallback to environment variables
        return self.secrets.get(secret_name)

    def set_secret(self, secret_name: str, secret_value: str, description: str = "") -> bool:
        """Set a secret value in AWS Secrets Manager."""
        if not self.use_aws_secrets_manager:
            logger.warning("AWS Secrets Manager not available, cannot set secret")
            return False

        try:
            secret_data = {
                "value": secret_value,
                "description": description,
                "created_by": "smartcloudops-ai",
            }

            self.secrets_client.create_secret(
                Name=secret_name,
                SecretString=json.dumps(secret_data),
                Description=description,
            )

            logger.info(f"✅ Secret {secret_name} created successfully")
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceExistsException":
                # Update existing secret
                try:
                    self.secrets_client.update_secret(SecretId=secret_name, SecretString=json.dumps(secret_data))
                    logger.info(f"✅ Secret {secret_name} updated successfully")
                    return True
                except Exception as update_error:
                    logger.error(f"Error updating secret {secret_name}: {update_error}")
                    return False
            else:
                logger.error(f"Error creating secret {secret_name}: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error setting secret {secret_name}: {e}")
            return False

    def list_secrets(self) -> list:
        """List all secrets in AWS Secrets Manager."""
        if not self.use_aws_secrets_manager:
            return list(self.secrets.keys())

        try:
            response = self.secrets_client.list_secrets()
            return [secret["Name"] for secret in response.get("SecretList", [])]
        except Exception as e:
            logger.error(f"Error listing secrets: {e}")
            return []

    def delete_secret(self, secret_name: str) -> bool:
        """Delete a secret from AWS Secrets Manager."""
        if not self.use_aws_secrets_manager:
            logger.warning("AWS Secrets Manager not available, cannot delete secret")
            return False

        try:
            self.secrets_client.delete_secret(SecretId=secret_name, ForceDeleteWithoutRecovery=True)
            logger.info(f"✅ Secret {secret_name} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting secret {secret_name}: {e}")
            return False

    def rotate_secret(self, secret_name: str) -> bool:
        """Rotate a secret in AWS Secrets Manager."""
        if not self.use_aws_secrets_manager:
            logger.warning("AWS Secrets Manager not available, cannot rotate secret")
            return False

        try:
            self.secrets_client.rotate_secret(SecretId=secret_name)
            logger.info(f"✅ Secret {secret_name} rotation initiated")
            return True
        except Exception as e:
            logger.error(f"Error rotating secret {secret_name}: {e}")
            return False

    def get_api_keys(self) -> Dict[str, str]:
        """Get all API keys."""
        return {
            "admin": self.get_secret("admin_api_key") or self.secrets.get("admin_api_key"),
            "ml": self.get_secret("ml_api_key") or self.secrets.get("ml_api_key"),
            "readonly": self.get_secret("readonly_api_key") or self.secrets.get("readonly_api_key"),
        }

    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key and return its metadata."""
        api_keys = self.get_api_keys()

        for key_type, key_value in api_keys.items():
            if key_value == api_key:
                return {
                    "type": key_type,
                    "permissions": self._get_key_permissions(key_type),
                    "valid": True,
                }

        return None

    def _get_key_permissions(self, key_type: str) -> list:
        """Get permissions for a key type."""
        permissions = {
            "admin": ["read", "write", "admin", "ml", "remediation"],
            "ml": ["read", "ml"],
            "readonly": ["read"],
        }
        return permissions.get(key_type, [])

    def health_check(self) -> Dict[str, Any]:
        """Perform health check of secrets manager."""
        try:
            if self.use_aws_secrets_manager:
                # Test AWS Secrets Manager connection
                self.secrets_client.list_secrets()
                aws_status = "healthy"
            else:
                aws_status = "not_configured"

            # Check environment secrets
            env_secrets_count = len([v for v in self.secrets.values() if v])

            return {
                "status": "healthy",
                "aws_secrets_manager": aws_status,
                "environment_secrets": env_secrets_count,
                "total_secrets": len(self.secrets),
                "missing_secrets": [k for k, v in self.secrets.items() if not v],
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global secrets manager instance
secrets_manager = SecretsManager()


def get_secret(secret_name: str) -> Optional[str]:
    """Get a secret value."""
    return secrets_manager.get_secret(secret_name)


def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """Validate an API key."""
    return secrets_manager.validate_api_key(api_key)
