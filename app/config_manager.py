#!/usr/bin/env python3
"""
SmartCloudOps AI - Environment Configuration Manager
==================================================

Centralized configuration management for all environments.
Replaces hardcoded values with environment-aware configuration.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration settings"""

    type: str = "sqlite"
    host: str = "localhost"
    port: int = 5432
    name: str = "smartcloudops"
    user: str = ""
    password: str = ""
    ssl_mode: str = "prefer"


@dataclass
class SecurityConfig:
    """Security configuration settings"""

    secret_key: str = ""
    api_key_expiry_days: int = 30
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    max_login_attempts: int = 5
    session_timeout_minutes: int = 30


@dataclass
class MLConfig:
    """ML Engine configuration settings"""

    model_path: str = "ml_models"
    min_f1_score: float = 0.7
    prediction_timeout_seconds: int = 5
    max_batch_size: int = 100
    enable_real_data: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""

    prometheus_endpoint: str = "http://localhost:9090"
    grafana_endpoint: str = "http://localhost:3000"
    enable_metrics: bool = True
    enable_health_checks: bool = True
    log_level: str = "INFO"


class EnvironmentConfigManager:
    """Centralized environment configuration manager"""

    def __init__(self, environment: Optional[str] = None):
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config_dir.mkdir(exist_ok=True)

        # Load configuration
        self.database = DatabaseConfig()
        self.security = SecurityConfig()
        self.ml = MLConfig()
        self.monitoring = MonitoringConfig()

        self._load_configuration()
        self._validate_configuration()

    def _load_configuration(self):
        """Load configuration from environment variables and files"""

        # Database Configuration
        self.database.type = os.getenv("DB_TYPE", "sqlite")
        self.database.host = os.getenv("DB_HOST", "localhost")
        self.database.port = int(os.getenv("DB_PORT", "5432"))
        self.database.name = os.getenv("DB_NAME", "smartcloudops")
        self.database.user = os.getenv("DB_USER", "")
        self.database.password = os.getenv("DB_PASSWORD", "")
        self.database.ssl_mode = os.getenv("DB_SSL_MODE", "prefer")

        # Security Configuration
        self.security.secret_key = os.getenv("SECRET_KEY", self._generate_secret_key())
        self.security.api_key_expiry_days = int(os.getenv("API_KEY_EXPIRY_DAYS", "30"))
        self.security.rate_limit_per_minute = int(
            os.getenv("RATE_LIMIT_PER_MINUTE", "60")
        )
        self.security.rate_limit_per_hour = int(
            os.getenv("RATE_LIMIT_PER_HOUR", "1000")
        )
        self.security.max_login_attempts = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self.security.session_timeout_minutes = int(
            os.getenv("SESSION_TIMEOUT_MINUTES", "30")
        )

        # ML Configuration
        self.ml.model_path = os.getenv("ML_MODEL_PATH", "ml_models")
        self.ml.min_f1_score = float(os.getenv("ML_MIN_F1_SCORE", "0.7"))
        self.ml.prediction_timeout_seconds = int(
            os.getenv("ML_PREDICTION_TIMEOUT", "5")
        )
        self.ml.max_batch_size = int(os.getenv("ML_MAX_BATCH_SIZE", "100"))
        self.ml.enable_real_data = (
            os.getenv("ML_ENABLE_REAL_DATA", "true").lower() == "true"
        )

        # Monitoring Configuration - Environment Aware
        self._configure_monitoring_endpoints()
        self.monitoring.enable_metrics = (
            os.getenv("ENABLE_METRICS", "true").lower() == "true"
        )
        self.monitoring.enable_health_checks = (
            os.getenv("ENABLE_HEALTH_CHECKS", "true").lower() == "true"
        )
        self.monitoring.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Load environment-specific configuration file if exists
        env_config_file = self.config_dir / f"{self.environment}.json"
        if env_config_file.exists():
            self._load_from_file(env_config_file)

    def _configure_monitoring_endpoints(self):
        """Configure monitoring endpoints based on environment"""

        if self.environment == "production":
            # Production endpoints - replace with actual production URLs
            self.monitoring.prometheus_endpoint = os.getenv(
                "PROMETHEUS_ENDPOINT", "https://prometheus.smartcloudops.ai"
            )
            self.monitoring.grafana_endpoint = os.getenv(
                "GRAFANA_ENDPOINT", "https://grafana.smartcloudops.ai"
            )
        elif self.environment == "staging":
            # Staging endpoints
            self.monitoring.prometheus_endpoint = os.getenv(
                "PROMETHEUS_ENDPOINT", "https://prometheus-staging.smartcloudops.ai"
            )
            self.monitoring.grafana_endpoint = os.getenv(
                "GRAFANA_ENDPOINT", "https://grafana-staging.smartcloudops.ai"
            )
        else:
            # Development endpoints (localhost)
            self.monitoring.prometheus_endpoint = os.getenv(
                "PROMETHEUS_ENDPOINT", "http://localhost:9090"
            )
            self.monitoring.grafana_endpoint = os.getenv(
                "GRAFANA_ENDPOINT", "http://localhost:3000"
            )

    def _load_from_file(self, config_file: Path):
        """Load configuration from JSON file"""
        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)

            # Update configurations from file
            if "database" in config_data:
                for key, value in config_data["database"].items():
                    if hasattr(self.database, key):
                        setattr(self.database, key, value)

            if "security" in config_data:
                for key, value in config_data["security"].items():
                    if hasattr(self.security, key):
                        setattr(self.security, key, value)

            if "ml" in config_data:
                for key, value in config_data["ml"].items():
                    if hasattr(self.ml, key):
                        setattr(self.ml, key, value)

            if "monitoring" in config_data:
                for key, value in config_data["monitoring"].items():
                    if hasattr(self.monitoring, key):
                        setattr(self.monitoring, key, value)

        except Exception as e:
            logging.warning(f"Failed to load config from {config_file}: {e}")

    def _generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        import secrets

        return secrets.token_hex(32)

    def _validate_configuration(self):
        """Validate configuration values"""
        errors = []

        # Validate security settings
        if len(self.security.secret_key) < 32:
            errors.append("SECRET_KEY must be at least 32 characters long")

        if self.security.rate_limit_per_minute < 1:
            errors.append("RATE_LIMIT_PER_MINUTE must be positive")

        if self.security.max_login_attempts < 1:
            errors.append("MAX_LOGIN_ATTEMPTS must be positive")

        # Validate ML settings
        if self.ml.min_f1_score < 0 or self.ml.min_f1_score > 1:
            errors.append("ML_MIN_F1_SCORE must be between 0 and 1")

        if self.ml.prediction_timeout_seconds < 1:
            errors.append("ML_PREDICTION_TIMEOUT must be positive")

        # Validate database settings
        if self.database.type not in ["sqlite", "postgresql", "mysql"]:
            errors.append(f"Unsupported database type: {self.database.type}")

        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")

    def get_database_url(self) -> str:
        """Get database connection URL"""
        if self.database.type == "sqlite":
            return f"sqlite:///{self.database.name}.db"
        elif self.database.type == "postgresql":
            return (
                f"postgresql://{self.database.user}:{self.database.password}@"
                f"{self.database.host}:{self.database.port}/{self.database.name}"
            )
        elif self.database.type == "mysql":
            return (
                f"mysql://{self.database.user}:{self.database.password}@"
                f"{self.database.host}:{self.database.port}/{self.database.name}"
            )
        else:
            raise ValueError(f"Unsupported database type: {self.database.type}")

    def get_flask_config(self) -> Dict[str, Any]:
        """Get Flask application configuration"""
        return {
            "SECRET_KEY": self.security.secret_key,
            "SQLALCHEMY_DATABASE_URI": self.get_database_url(),
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "DEBUG": self.environment == "development",
            "TESTING": self.environment == "testing",
            "ENV": self.environment,
            "LOG_LEVEL": self.monitoring.log_level,
            "RATE_LIMIT_PER_MINUTE": self.security.rate_limit_per_minute,
            "RATE_LIMIT_PER_HOUR": self.security.rate_limit_per_hour,
            "ML_MODEL_PATH": self.ml.model_path,
            "ML_MIN_F1_SCORE": self.ml.min_f1_score,
            "PROMETHEUS_ENDPOINT": self.monitoring.prometheus_endpoint,
            "GRAFANA_ENDPOINT": self.monitoring.grafana_endpoint,
        }

    def save_template_configs(self):
        """Save template configuration files for different environments"""

        # Production configuration template
        prod_config = {
            "database": {
                "type": "postgresql",
                "host": "prod-db.smartcloudops.ai",
                "port": 5432,
                "name": "smartcloudops_prod",
                "ssl_mode": "require",
            },
            "security": {
                "api_key_expiry_days": 30,
                "rate_limit_per_minute": 100,
                "rate_limit_per_hour": 5000,
                "max_login_attempts": 3,
                "session_timeout_minutes": 60,
            },
            "ml": {
                "min_f1_score": 0.85,
                "prediction_timeout_seconds": 3,
                "max_batch_size": 200,
                "enable_real_data": True,
            },
            "monitoring": {
                "prometheus_endpoint": "https://prometheus.smartcloudops.ai",
                "grafana_endpoint": "https://grafana.smartcloudops.ai",
                "enable_metrics": True,
                "enable_health_checks": True,
                "log_level": "WARNING",
            },
        }

        # Staging configuration template
        staging_config = {
            "database": {
                "type": "postgresql",
                "host": "staging-db.smartcloudops.ai",
                "port": 5432,
                "name": "smartcloudops_staging",
                "ssl_mode": "require",
            },
            "security": {
                "api_key_expiry_days": 7,
                "rate_limit_per_minute": 120,
                "rate_limit_per_hour": 2000,
                "max_login_attempts": 5,
                "session_timeout_minutes": 30,
            },
            "ml": {
                "min_f1_score": 0.7,
                "prediction_timeout_seconds": 5,
                "max_batch_size": 100,
                "enable_real_data": True,
            },
            "monitoring": {
                "prometheus_endpoint": "https://prometheus-staging.smartcloudops.ai",
                "grafana_endpoint": "https://grafana-staging.smartcloudops.ai",
                "enable_metrics": True,
                "enable_health_checks": True,
                "log_level": "INFO",
            },
        }

        # Development configuration template
        dev_config = {
            "database": {"type": "sqlite", "name": "smartcloudops_dev"},
            "security": {
                "api_key_expiry_days": 1,
                "rate_limit_per_minute": 1000,
                "rate_limit_per_hour": 10000,
                "max_login_attempts": 10,
                "session_timeout_minutes": 120,
            },
            "ml": {
                "min_f1_score": 0.5,
                "prediction_timeout_seconds": 10,
                "max_batch_size": 50,
                "enable_real_data": False,
            },
            "monitoring": {
                "prometheus_endpoint": "http://localhost:9090",
                "grafana_endpoint": "http://localhost:3000",
                "enable_metrics": True,
                "enable_health_checks": True,
                "log_level": "DEBUG",
            },
        }

        # Save configuration files
        configs = {
            "production.json": prod_config,
            "staging.json": staging_config,
            "development.json": dev_config,
        }

        for filename, config in configs.items():
            config_file = self.config_dir / filename
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

        logging.info(f"✅ Saved configuration templates to {self.config_dir}")

    def print_summary(self):
        """Print configuration summary"""
        print(f"\n🔧 SmartCloudOps AI Configuration Summary")
        print(f"=" * 50)
        print(f"Environment: {self.environment}")
        print(
            f"Database: {self.database.type} at {self.database.host}:{self.database.port}"
        )
        print(f"Security: Rate limit {self.security.rate_limit_per_minute}/min")
        print(
            f"ML Engine: Min F1 {self.ml.min_f1_score}, Timeout {self.ml.prediction_timeout_seconds}s"
        )
        print(f"Monitoring: {self.monitoring.prometheus_endpoint}")
        print(f"Log Level: {self.monitoring.log_level}")
        print("")


# Global configuration instance
config_manager = None


def get_config(environment: Optional[str] = None) -> EnvironmentConfigManager:
    """Get global configuration manager instance"""
    global config_manager
    if config_manager is None:
        config_manager = EnvironmentConfigManager(environment)
    return config_manager


def main():
    """CLI for configuration management"""
    import argparse

    parser = argparse.ArgumentParser(
        description="SmartCloudOps AI Configuration Manager"
    )
    parser.add_argument(
        "--environment",
        "-e",
        default="development",
        help="Environment (development, staging, production)",
    )
    parser.add_argument(
        "--save-templates", action="store_true", help="Save configuration templates"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate current configuration"
    )

    args = parser.parse_args()

    try:
        config = EnvironmentConfigManager(args.environment)

        if args.save_templates:
            config.save_template_configs()
            print("✅ Configuration templates saved")

        if args.validate:
            print("✅ Configuration validation passed")

        config.print_summary()

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
