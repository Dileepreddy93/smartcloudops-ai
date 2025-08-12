#!/usr/bin/env python3
"""
SmartCloudOps AI - Production Configuration Manager
=================================================

Handles environment-specific configuration with proper secrets management.
Eliminates hardcoded values and provides production-ready config management.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    type: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    name: str = "smartcloudops"
    user: str = "smartcloudops"
    password: str = ""
    ssl_mode: str = "require"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

@dataclass
class CacheConfig:
    """Redis cache configuration"""
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    secret_key: str = ""
    api_key_expiry_days: int = 30
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    max_login_attempts: int = 5
    session_timeout_minutes: int = 30
    cors_origins: list = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["https://app.smartcloudops.ai"]

@dataclass
class MLConfig:
    """ML Engine configuration settings"""
    model_path: str = "ml_models"
    min_f1_score: float = 0.7
    prediction_timeout_seconds: int = 5
    max_batch_size: int = 100
    enable_real_data: bool = True
    model_refresh_hours: int = 24
    anomaly_threshold: float = 0.8

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    prometheus_endpoint: str = "http://localhost:9090"
    grafana_endpoint: str = "http://localhost:3000"
    log_level: str = "INFO"
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    alert_email: str = ""
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""

@dataclass
class ApplicationConfig:
    """Main application configuration"""
    environment: str = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 5000
    workers: int = 4
    worker_class: str = "gevent"
    max_requests: int = 1000
    timeout: int = 30
    keepalive: int = 2

class ConfigurationManager:
    """Production-ready configuration management"""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.config_dir = Path(__file__).parent.parent / 'config'
        self.secrets_client = None
        self.setup_logging()
        
        # Initialize AWS Secrets Manager if in AWS environment
        if self.environment in ['staging', 'production']:
            try:
                self.secrets_client = boto3.client('secretsmanager')
            except Exception as e:
                self.logger.warning(f"Could not initialize AWS Secrets Manager: {e}")
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager or environment"""
        # Try AWS Secrets Manager first (for production)
        if self.secrets_client:
            try:
                response = self.secrets_client.get_secret_value(SecretId=secret_name)
                return response['SecretString']
            except ClientError as e:
                self.logger.warning(f"Could not retrieve secret {secret_name}: {e}")
        
        # Fallback to environment variable
        return os.getenv(secret_name)
    
    def load_database_config(self) -> DatabaseConfig:
        """Load database configuration"""
        return DatabaseConfig(
            type=os.getenv('DB_TYPE', 'postgresql'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            name=os.getenv('DB_NAME', 'smartcloudops'),
            user=os.getenv('DB_USER', 'smartcloudops'),
            password=self.get_secret('DB_PASSWORD') or os.getenv('DB_PASSWORD', ''),
            ssl_mode=os.getenv('DB_SSL_MODE', 'require'),
            pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '20')),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '30')),
            pool_recycle=int(os.getenv('DB_POOL_RECYCLE', '3600'))
        )
    
    def load_cache_config(self) -> CacheConfig:
        """Load Redis cache configuration"""
        return CacheConfig(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            password=self.get_secret('REDIS_PASSWORD') or os.getenv('REDIS_PASSWORD', ''),
            db=int(os.getenv('REDIS_DB', '0')),
            max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '50')),
            socket_timeout=int(os.getenv('REDIS_SOCKET_TIMEOUT', '5')),
            socket_connect_timeout=int(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', '5'))
        )
    
    def load_security_config(self) -> SecurityConfig:
        """Load security configuration"""
        cors_origins = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else None
        
        return SecurityConfig(
            secret_key=self.get_secret('SECRET_KEY') or os.getenv('SECRET_KEY', ''),
            api_key_expiry_days=int(os.getenv('API_KEY_EXPIRY_DAYS', '30')),
            rate_limit_per_minute=int(os.getenv('RATE_LIMIT_PER_MINUTE', '60')),
            rate_limit_per_hour=int(os.getenv('RATE_LIMIT_PER_HOUR', '1000')),
            max_login_attempts=int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
            session_timeout_minutes=int(os.getenv('SESSION_TIMEOUT_MINUTES', '30')),
            cors_origins=cors_origins
        )
    
    def load_ml_config(self) -> MLConfig:
        """Load ML configuration"""
        return MLConfig(
            model_path=os.getenv('ML_MODEL_PATH', 'ml_models'),
            min_f1_score=float(os.getenv('ML_MIN_F1_SCORE', '0.7')),
            prediction_timeout_seconds=int(os.getenv('ML_PREDICTION_TIMEOUT', '5')),
            max_batch_size=int(os.getenv('ML_MAX_BATCH_SIZE', '100')),
            enable_real_data=os.getenv('ML_ENABLE_REAL_DATA', 'true').lower() == 'true',
            model_refresh_hours=int(os.getenv('ML_MODEL_REFRESH_HOURS', '24')),
            anomaly_threshold=float(os.getenv('ML_ANOMALY_THRESHOLD', '0.8'))
        )
    
    def load_monitoring_config(self) -> MonitoringConfig:
        """Load monitoring configuration"""
        return MonitoringConfig(
            prometheus_endpoint=os.getenv('PROMETHEUS_ENDPOINT', 'http://localhost:9090'),
            grafana_endpoint=os.getenv('GRAFANA_ENDPOINT', 'http://localhost:3000'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            metrics_enabled=os.getenv('METRICS_ENABLED', 'true').lower() == 'true',
            tracing_enabled=os.getenv('TRACING_ENABLED', 'true').lower() == 'true',
            alert_email=os.getenv('ALERT_EMAIL', ''),
            smtp_server=os.getenv('SMTP_SERVER', ''),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_username=self.get_secret('SMTP_USERNAME') or os.getenv('SMTP_USERNAME', ''),
            smtp_password=self.get_secret('SMTP_PASSWORD') or os.getenv('SMTP_PASSWORD', '')
        )
    
    def load_application_config(self) -> ApplicationConfig:
        """Load application configuration"""
        # Environment-specific defaults
        defaults = {
            'development': {
                'debug': True,
                'workers': 1,
                'log_level': 'DEBUG'
            },
            'staging': {
                'debug': False,
                'workers': 2,
                'log_level': 'INFO'
            },
            'production': {
                'debug': False,
                'workers': 4,
                'log_level': 'WARNING'
            }
        }
        
        env_defaults = defaults.get(self.environment, defaults['development'])
        
        return ApplicationConfig(
            environment=self.environment,
            debug=os.getenv('DEBUG', str(env_defaults['debug'])).lower() == 'true',
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '5000')),
            workers=int(os.getenv('WORKERS', str(env_defaults['workers']))),
            worker_class=os.getenv('WORKER_CLASS', 'gevent'),
            max_requests=int(os.getenv('MAX_REQUESTS', '1000')),
            timeout=int(os.getenv('TIMEOUT', '30')),
            keepalive=int(os.getenv('KEEPALIVE', '2'))
        )
    
    def load_all_configs(self) -> Dict[str, Any]:
        """Load all configuration objects"""
        return {
            'database': self.load_database_config(),
            'cache': self.load_cache_config(),
            'security': self.load_security_config(),
            'ml': self.load_ml_config(),
            'monitoring': self.load_monitoring_config(),
            'application': self.load_application_config()
        }
    
    def validate_configuration(self, configs: Dict[str, Any]) -> bool:
        """Validate configuration for production readiness"""
        errors = []
        
        # Database validation
        db_config = configs['database']
        if not db_config.password and self.environment == 'production':
            errors.append("Database password is required for production")
        
        # Security validation
        security_config = configs['security']
        if not security_config.secret_key and self.environment == 'production':
            errors.append("Secret key is required for production")
        
        # Monitoring validation
        monitoring_config = configs['monitoring']
        if not monitoring_config.alert_email and self.environment == 'production':
            errors.append("Alert email is required for production")
        
        if errors:
            for error in errors:
                self.logger.error(f"Configuration error: {error}")
            return False
        
        return True
    
    def save_config_template(self, environment: str):
        """Save configuration template for environment"""
        template = {
            'database': {
                'type': 'postgresql',
                'host': 'your-db-host.amazonaws.com' if environment == 'production' else 'localhost',
                'port': 5432,
                'name': 'smartcloudops',
                'user': 'smartcloudops',
                'password': '${DB_PASSWORD}',  # Will be replaced by secrets manager
                'ssl_mode': 'require' if environment == 'production' else 'prefer'
            },
            'cache': {
                'host': 'your-redis-host.amazonaws.com' if environment == 'production' else 'localhost',
                'port': 6379,
                'password': '${REDIS_PASSWORD}',
                'db': 0
            },
            'security': {
                'secret_key': '${SECRET_KEY}',
                'rate_limit_per_minute': 100 if environment == 'production' else 60,
                'cors_origins': [
                    'https://app.smartcloudops.ai' if environment == 'production' else 'http://localhost:3000'
                ]
            },
            'monitoring': {
                'prometheus_endpoint': f'http://{"internal-prometheus" if environment == "production" else "localhost"}:9090',
                'alert_email': 'alerts@smartcloudops.ai',
                'log_level': 'WARNING' if environment == 'production' else 'INFO'
            }
        }
        
        # Create config directory
        self.config_dir.mkdir(exist_ok=True)
        
        # Save template
        config_file = self.config_dir / f'{environment}.json'
        with open(config_file, 'w') as f:
            json.dump(template, f, indent=2)
        
        self.logger.info(f"Configuration template saved to {config_file}")
    
    def create_environment_file(self, environment: str):
        """Create .env file for environment"""
        env_vars = {
            'development': {
                'ENVIRONMENT': 'development',
                'DEBUG': 'true',
                'LOG_LEVEL': 'DEBUG',
                'DB_TYPE': 'sqlite',
                'DB_NAME': 'smartcloudops.db',
                'PROMETHEUS_ENDPOINT': 'http://localhost:9090',
                'GRAFANA_ENDPOINT': 'http://localhost:3000'
            },
            'staging': {
                'ENVIRONMENT': 'staging',
                'DEBUG': 'false',
                'LOG_LEVEL': 'INFO',
                'DB_TYPE': 'postgresql',
                'DB_HOST': 'staging-db.amazonaws.com',
                'DB_NAME': 'smartcloudops_staging',
                'REDIS_HOST': 'staging-redis.amazonaws.com',
                'PROMETHEUS_ENDPOINT': 'http://internal-prometheus-staging:9090'
            },
            'production': {
                'ENVIRONMENT': 'production',
                'DEBUG': 'false',
                'LOG_LEVEL': 'WARNING',
                'DB_TYPE': 'postgresql',
                'DB_HOST': 'prod-db.amazonaws.com',
                'DB_NAME': 'smartcloudops_production',
                'REDIS_HOST': 'prod-redis.amazonaws.com',
                'PROMETHEUS_ENDPOINT': 'http://internal-prometheus:9090',
                'CORS_ORIGINS': 'https://app.smartcloudops.ai',
                'RATE_LIMIT_PER_MINUTE': '100',
                'RATE_LIMIT_PER_HOUR': '2000'
            }
        }
        
        env_file = Path(f'.env.{environment}')
        with open(env_file, 'w') as f:
            f.write(f"# SmartCloudOps AI - {environment.title()} Environment\n")
            f.write(f"# Generated on {os.getenv('DATE', 'unknown')}\n\n")
            
            for key, value in env_vars[environment].items():
                f.write(f"{key}={value}\n")
            
            # Add sensitive variables as placeholders
            if environment in ['staging', 'production']:
                f.write("\n# Sensitive variables (set in AWS Secrets Manager or environment)\n")
                f.write("DB_PASSWORD=\n")
                f.write("REDIS_PASSWORD=\n")
                f.write("SECRET_KEY=\n")
                f.write("SMTP_USERNAME=\n")
                f.write("SMTP_PASSWORD=\n")
        
        self.logger.info(f"Environment file created: {env_file}")

def main():
    """CLI for configuration management"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python config_manager.py <command> [environment]")
        print("Commands: validate, template, env-file, test")
        sys.exit(1)
    
    command = sys.argv[1]
    environment = sys.argv[2] if len(sys.argv) > 2 else 'development'
    
    config_manager = ConfigurationManager(environment)
    
    if command == 'validate':
        configs = config_manager.load_all_configs()
        if config_manager.validate_configuration(configs):
            print("✅ Configuration validation passed")
        else:
            print("❌ Configuration validation failed")
            sys.exit(1)
    
    elif command == 'template':
        config_manager.save_config_template(environment)
        print(f"✅ Configuration template created for {environment}")
    
    elif command == 'env-file':
        config_manager.create_environment_file(environment)
        print(f"✅ Environment file created for {environment}")
    
    elif command == 'test':
        configs = config_manager.load_all_configs()
        print(f"🔧 Configuration for {environment}:")
        for name, config in configs.items():
            print(f"  {name}: {type(config).__name__}")
            # Don't print sensitive values
            config_dict = asdict(config)
            for key, value in config_dict.items():
                if 'password' in key.lower() or 'secret' in key.lower():
                    value = '*' * len(str(value)) if value else '(not set)'
                print(f"    {key}: {value}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
