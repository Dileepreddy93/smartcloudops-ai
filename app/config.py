#!/usr/bin/env python3
"""
SmartCloudOps AI - Environment Configuration Manager
==================================================

Secure, environment-aware configuration management.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

class ConfigManager:
    """Environment-aware configuration manager."""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self._load_environment_config()
    
    def _load_environment_config(self):
        """Load environment-specific configuration."""
        # Load base .env file first
        load_dotenv()
        
        # Load environment-specific .env file
        env_file = f".env.{self.environment}"
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            logging.info(f"✅ Loaded {env_file}")
        else:
            logging.warning(f"⚠️ Environment file {env_file} not found, using defaults")

# Initialize configuration manager
config_manager = ConfigManager()

@dataclass
class PrometheusConfig:
    """Prometheus configuration with validation."""
    url: str
    timeout: int = 30
    ssl_verify: bool = True
    
    def __post_init__(self):
        if not self.url:
            raise ValueError("Prometheus URL is required")
        if not self.url.startswith(('http://', 'https://')):
            raise ValueError("Prometheus URL must start with http:// or https://")

@dataclass 
class AIConfig:
    """AI providers configuration."""
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    provider: str = "auto"  # auto, openai, gemini, fallback
    
    def __post_init__(self):
        if self.provider not in ['auto', 'openai', 'gemini', 'fallback']:
            raise ValueError(f"Invalid AI provider: {self.provider}")

@dataclass
class MLConfig:
    """Machine Learning configuration."""
    model_path: str = "/app/ml_models/real_data_model.json"
    data_path: str = "/app/data/real_training_data.json"
    confidence_threshold: float = 0.7
    max_prediction_time: int = 30
    
    def __post_init__(self):
        if not 0 <= self.confidence_threshold <= 1:
            raise ValueError("Confidence threshold must be between 0 and 1")

class Config:
    """Main configuration class with environment-aware settings."""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # Security settings
        self.secret_key = os.getenv('SECRET_KEY', self._generate_secret_key())
        
        # Prometheus configuration
        prometheus_url = self._get_prometheus_url()
        self.prometheus = PrometheusConfig(
            url=prometheus_url,
            timeout=int(os.getenv('PROMETHEUS_TIMEOUT', '30')),
            ssl_verify=os.getenv('PROMETHEUS_SSL_VERIFY', 'true').lower() == 'true'
        )
        
        # AI configuration
        self.ai = AIConfig(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            provider=os.getenv('AI_PROVIDER', 'auto')
        )
        
        # ML configuration
        self.ml = MLConfig(
            model_path=os.getenv('ML_MODEL_PATH', '/app/ml_models/real_data_model.json'),
            data_path=os.getenv('ML_DATA_PATH', '/app/data/real_training_data.json'),
            confidence_threshold=float(os.getenv('ML_CONFIDENCE_THRESHOLD', '0.7')),
            max_prediction_time=int(os.getenv('ML_MAX_PREDICTION_TIME', '30'))
        )
        
        # Logging configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Validate configuration
        self._validate_config()
    
    def _get_prometheus_url(self) -> str:
        """Get Prometheus URL based on environment with proper service discovery."""
        base_url = os.getenv('PROMETHEUS_URL')
        
        if base_url:
            return base_url
            
        # Fallback to environment-specific defaults
        if self.environment == 'production':
            return 'https://prometheus.internal.smartcloudops.com:9090'
        elif self.environment == 'staging':
            return 'http://staging-prometheus.internal:9090'
        else:
            # Development - check for local instance first
            local_prometheus = 'http://localhost:9090'
            try:
                import requests
                requests.get(f"{local_prometheus}/api/v1/status/config", timeout=2)
                return local_prometheus
            except:
                # Fall back to existing working development URL
                return 'http://3.89.229.102:9090'
    
    def _generate_secret_key(self) -> str:
        """Generate a secret key if none provided."""
        import secrets
        return secrets.token_hex(32)
    
    def _validate_config(self):
        """Validate configuration settings."""
        if self.environment == 'production':
            if not self.ai.openai_api_key and not self.ai.gemini_api_key:
                logging.warning("No AI API keys configured for production")
            
            if self.debug:
                logging.warning("Debug mode enabled in production - this is insecure")
            
            if self.prometheus.url.startswith('http://'):
                logging.warning("Using insecure HTTP for Prometheus in production")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (excluding sensitive data)."""
        return {
            'environment': self.environment,
            'debug': self.debug,
            'prometheus_url': self.prometheus.url,
            'ai_provider': self.ai.provider,
            'log_level': self.log_level,
            'ml_confidence_threshold': self.ml.confidence_threshold
        }

# Global configuration instance
config = Config()

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info(f"✅ Configuration loaded for environment: {config.environment}")
