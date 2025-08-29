#!/usr/bin/env python3
"""
SmartCloudOps AI - Unified Configuration System
==============================================

Production-ready configuration management with environment-specific settings,
secure secret handling, and comprehensive validation.
"""


import logging
import os
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv


class SecretProvider(ABC):
    """Abstract secret provider interface for secure secret management."""

    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve secret by key."""
        pass

    @abstractmethod
    def get_priority(self) -> int:
        """Return provider priority (lower = higher priority)."""
        pass


class AWSSecretsProvider(SecretProvider):
    """AWS Secrets Manager provider for production secrets."""

    def __init__(self):
        self.available = False
        try:
            import boto3
            self.client = boto3.client("secretsmanager")
            self.available = True
            logging.info("✅ AWS Secrets Manager provider initialized")
        except Exception as e:
            logging.warning(f"⚠️ AWS Secrets Manager not available: {e}")

    def get_priority(self) -> int:
        return 1  # Highest priority for production

    @lru_cache(maxsize=50)
    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve secret from AWS Secrets Manager with caching."""
        if not self.available:
            return None

        try:
            response = self.client.get_secret_value(SecretId=key)
            secret_data = json.loads(response["SecretString"])
            
            # Handle both direct values and nested structures
            if isinstance(secret_data, dict):
                return secret_data.get("value") or secret_data.get(key.split("/")[-1])
            return secret_data
            
        except self.client.exceptions.ResourceNotFoundException:
            logging.debug(f"Secret {key} not found in AWS Secrets Manager")
            return None
        except Exception as e:
            logging.error(f"Failed to retrieve AWS secret {key}: {e}")
            return None


class EnvironmentProvider(SecretProvider):
    """Environment variable provider - fallback for development."""

    def get_priority(self) -> int:
        return 2  # Lower priority than AWS

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve secret from environment variables."""
        return os.getenv(key)


class DevFileProvider(SecretProvider):
    """Development file-based provider for persistent local secrets."""

    def __init__(self):
        self.dev_secret_file = ".dev-secret"

    def get_priority(self) -> int:
        return 3  # Lowest priority

    def get_secret(self, key: str) -> Optional[str]:
        """Get or create persistent development secrets."""
        if key == "SECRET_KEY":
            return self._get_or_create_dev_secret()
        return None

    def _get_or_create_dev_secret(self) -> str:
        """Get or create persistent development secret key."""
        if os.path.exists(self.dev_secret_file):
            try:
                with open(self.dev_secret_file, "r") as f:
                    return f.read().strip()
            except Exception as e:
                logging.error(f"Failed to read dev secret: {e}")

        # Create new persistent secret
        new_secret = secrets.token_hex(32)
        try:
            with open(self.dev_secret_file, "w") as f:
                f.write(new_secret)
            os.chmod(self.dev_secret_file, 0o600)  # Restrict permissions
            logging.info("✅ Created persistent development secret")
            return new_secret
        except Exception as e:
            logging.error(f"Failed to create dev secret: {e}")
            return secrets.token_hex(32)  # Fallback to temporary


class SecureConfigManager:
    """Production-ready configuration manager with multiple secret providers."""

    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv("APP_ENV", "development")
        self.providers: List[SecretProvider] = []
        self._setup_secret_providers()
        self._load_base_environment()
        logging.info(f"✅ Secure config manager initialized for {self.environment}")

    def _setup_secret_providers(self):
        """Setup secret providers based on environment."""
        if self.environment == "production":
            self.providers = [
                AWSSecretsProvider(),
                EnvironmentProvider(),  # Emergency fallback only
            ]
        elif self.environment == "testing":
            self.providers = [
                EnvironmentProvider(),
                DevFileProvider(),
            ]
        else:  # development
            self.providers = [
                DevFileProvider(),
                EnvironmentProvider(),
            ]

        # Sort by priority
        self.providers.sort(key=lambda p: p.get_priority())

    def _load_base_environment(self):
        """Load base environment configuration safely."""
        # Only load .env.example or basic .env in development
        if self.environment == "development":
            if os.path.exists(".env"):
                load_dotenv(".env")
                logging.info("✅ Loaded development .env file")
            else:
                logging.info("ℹ️ No .env file found, using environment variables only")

    def get_secret(self, key: str, required: bool = False, secret_key: str = None) -> Optional[str]:
        """
        Get secret from configured providers with fallback chain.
        
        Args:
            key: Environment variable key
            required: Raise error if not found
            secret_key: AWS Secrets Manager key (if different from env key)
        """
        # Try AWS Secrets Manager key first if provided
        if secret_key:
            for provider in self.providers:
                if isinstance(provider, AWSSecretsProvider):
                    value = provider.get_secret(secret_key)
                    if value:
                        return value

        # Try regular key
        for provider in self.providers:
            value = provider.get_secret(key)
            if value:
                logging.debug(f"Secret '{key}' retrieved from {provider.__class__.__name__}")
                return value

        if required:
            raise ValueError(f"Required secret '{key}' not found in any provider")

        logging.warning(f"Secret '{key}' not found in any provider")
        return None

    def validate_production_secrets(self):
        """Validate that all required production secrets are available."""
        if self.environment != "production":
            return

        required_secrets = [
            ("SECRET_KEY", "smartcloudops/app/secret-key"),
            ("DATABASE_URL", "smartcloudops/database/url"),
            ("REDIS_URL", "smartcloudops/redis/url"),
            ("OPENAI_API_KEY", "smartcloudops/openai/api-key"),
        ]

        missing_secrets = []
        for env_key, aws_key in required_secrets:
            if not self.get_secret(env_key, secret_key=aws_key):
                missing_secrets.append(env_key)

        if missing_secrets:
            raise ValueError(f"Production deployment blocked - missing required secrets: {missing_secrets}")

        logging.info("✅ All production secrets validated")


# Global secure configuration manager
config_manager = SecureConfigManager()


@dataclass
class DatabaseConfig:
    """Database configuration with validation."""
    
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    def __post_init__(self):
        if not self.url:
            raise ValueError("Database URL is required")
        if self.pool_size <= 0:
            raise ValueError("Pool size must be positive")
        if self.max_overflow < 0:
            raise ValueError("Max overflow must be non-negative")


@dataclass
class RedisConfig:
    """Redis configuration with validation."""
    
    url: str
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    
    def __post_init__(self):
        if not self.url:
            raise ValueError("Redis URL is required")
        if not self.url.startswith(("redis://", "rediss://")):
            raise ValueError("Redis URL must start with redis:// or rediss://")


@dataclass
class SecurityConfig:
    """Security configuration with environment-specific validation."""
    
    secret_key: str
    cors_origins: List[str]
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    rate_limit: str = "500/hour"
    
    def __post_init__(self):
        if len(self.secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        
        # Validate CORS origins format
        for origin in self.cors_origins:
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid CORS origin format: {origin}")


class UnifiedConfig:
    """
    Immutable, validated configuration with secure secret handling.
    
    This class ensures:
    1. No secrets are logged or exposed
    2. Production requires proper secret sources
    3. Configuration is validated on initialization
    4. Environment-specific security rules are enforced
    """
    
    def __init__(self, config_manager: SecureConfigManager):
        self.environment = config_manager.environment
        self.debug = self._get_debug_setting(config_manager)
        self.config_manager = config_manager
        
        # Validate production requirements first
        if self.environment == "production":
            config_manager.validate_production_secrets()
        
        # Security configuration
        self.security = self._build_security_config(config_manager)
        
        # Database configuration
        self.database = self._build_database_config(config_manager)
        
        # Redis configuration
        self.redis = self._build_redis_config(config_manager)
        
        # Logging configuration
        self.log_level = config_manager.get_secret("LOG_LEVEL") or "INFO"
        
        # Final security validation
        self._validate_security_rules()
        
        logging.info(f"✅ Unified configuration initialized for {self.environment}")
    
    def _get_debug_setting(self, config_manager: SecureConfigManager) -> bool:
        """Get debug setting with environment-specific validation."""
        debug_str = config_manager.get_secret("DEBUG", required=False) or "false"
        debug = debug_str.lower() == "true"
        
        # Security rule: Never allow debug in production
        if self.environment == "production" and debug:
            raise ValueError("DEBUG mode is forbidden in production environment")
        
        return debug
    
    def _build_security_config(self, config_manager: SecureConfigManager) -> SecurityConfig:
        """Build security configuration with environment-specific rules."""
        # Get secret key
        secret_key = config_manager.get_secret(
            "SECRET_KEY", 
            required=True,
            secret_key=("smartcloudops/app/secret-key" if self.environment == "production" else None)
        )
        
        # Get CORS origins
        cors_origins_str = config_manager.get_secret("CORS_ORIGINS") or self._get_default_cors_origins()
        cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]
        
        # SSL configuration for production
        ssl_cert_path = None
        ssl_key_path = None
        if self.environment == "production":
            ssl_cert_path = config_manager.get_secret("SSL_CERT_PATH")
            ssl_key_path = config_manager.get_secret("SSL_KEY_PATH")
        
        rate_limit = config_manager.get_secret("RATE_LIMIT") or self._get_default_rate_limit()
        
        return SecurityConfig(
            secret_key=secret_key,
            cors_origins=cors_origins,
            ssl_cert_path=ssl_cert_path,
            ssl_key_path=ssl_key_path,
            rate_limit=rate_limit,
        )
    
    def _build_database_config(self, config_manager: SecureConfigManager) -> DatabaseConfig:
        """Build database configuration with environment-specific defaults."""
        database_url = config_manager.get_secret(
            "DATABASE_URL", 
            required=True,
            secret_key=("smartcloudops/database/url" if self.environment == "production" else None)
        )
        
        pool_size = int(config_manager.get_secret("DB_POOL_SIZE") or "10")
        max_overflow = int(config_manager.get_secret("DB_MAX_OVERFLOW") or "20")
        pool_timeout = int(config_manager.get_secret("DB_POOL_TIMEOUT") or "30")
        pool_recycle = int(config_manager.get_secret("DB_POOL_RECYCLE") or "3600")
        
        return DatabaseConfig(
            url=database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
        )
    
    def _build_redis_config(self, config_manager: SecureConfigManager) -> RedisConfig:
        """Build Redis configuration with environment-specific defaults."""
        redis_url = config_manager.get_secret(
            "REDIS_URL", 
            required=True,
            secret_key=("smartcloudops/redis/url" if self.environment == "production" else None)
        )
        
        max_connections = int(config_manager.get_secret("REDIS_MAX_CONNECTIONS") or "10")
        socket_timeout = int(config_manager.get_secret("REDIS_SOCKET_TIMEOUT") or "5")
        socket_connect_timeout = int(config_manager.get_secret("REDIS_SOCKET_CONNECT_TIMEOUT") or "5")
        retry_on_timeout = config_manager.get_secret("REDIS_RETRY_ON_TIMEOUT", required=False) != "false"
        
        return RedisConfig(
            url=redis_url,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            retry_on_timeout=retry_on_timeout,
        )
    
    def _get_default_cors_origins(self) -> str:
        """Get environment-specific CORS origins."""
        if self.environment == "production":
            return "https://smartcloudops.com,https://dashboard.smartcloudops.com"
        elif self.environment == "testing":
            return "http://localhost:3000,http://localhost:5000"
        else:
            return "http://localhost:3000,http://localhost:5000"
    
    def _get_default_rate_limit(self) -> str:
        """Get environment-specific rate limits."""
        if self.environment == "production":
            return "1000/hour"
        elif self.environment == "testing":
            return "500/hour"
        else:
            return "100/hour"
    
    def _validate_security_rules(self):
        """Validate environment-specific security rules."""
        if self.environment == "production":
            # Production security validations
            if not self.database.url.startswith(("postgresql://", "mysql://")):
                raise ValueError("Production database must use PostgreSQL or MySQL")
            
            if not self.redis.url.startswith("rediss://"):
                raise ValueError("Production Redis must use SSL")
            
            if not all(origin.startswith("https://") for origin in self.security.cors_origins):
                raise ValueError("Production CORS origins must use HTTPS")
    
    @property
    def secret_key(self) -> str:
        """Access secret key (for Flask configuration)."""
        return self.security.secret_key
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert config to dictionary for logging/debugging.
        NEVER includes sensitive data.
        """
        return {
            "environment": self.environment,
            "debug": self.debug,
            "database_url": self.database.url.split("@")[-1] if "@" in self.database.url else "configured",
            "redis_url": self.redis.url.split("@")[-1] if "@" in self.redis.url else "configured",
            "log_level": self.log_level,
            "cors_origins_count": len(self.security.cors_origins),
            "ssl_enabled": bool(self.security.ssl_cert_path),
        }


# Global unified configuration instance
try:
    config = UnifiedConfig(config_manager)
    
    # Configure logging with secure settings
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"✅ Unified configuration loaded: {config.to_dict()}")
    
except Exception as e:
    # Fallback configuration for emergencies
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Failed to load unified configuration: {e}")
    logger.error("🚨 Using emergency fallback configuration")
    
    class EmergencyConfig:
        def __init__(self):
            self.environment = "emergency"
            self.debug = False
            self.secret_key = secrets.token_hex(32)
            self.log_level = "ERROR"
            self.database = DatabaseConfig(url="sqlite:///emergency.db")
            self.redis = RedisConfig(url="redis://localhost:6379/0")
            self.security = SecurityConfig(
                secret_key=secrets.token_hex(32),
                cors_origins=["http://localhost:3000"]
            )
        
        def to_dict(self):
            return {"environment": "emergency", "status": "fallback_mode"}
    
    config = EmergencyConfig()
