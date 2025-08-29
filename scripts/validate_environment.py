#!/usr/bin/env python3
"""
SmartCloudOps.AI Environment Validation Script
Validates that all required environment variables are properly configured.
"""

import os
import sys
import re
from typing import Dict, List, Tuple
from urllib.parse import urlparse

# Color codes for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

class EnvironmentValidator:
    """Validates environment configuration for SmartCloudOps.AI."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        
    def log_error(self, message: str):
        """Log an error message."""
        self.errors.append(message)
        print(f"{RED}❌ ERROR:{NC} {message}")
        
    def log_warning(self, message: str):
        """Log a warning message."""
        self.warnings.append(message)
        print(f"{YELLOW}⚠️  WARNING:{NC} {message}")
        
    def log_success(self, message: str):
        """Log a success message."""
        self.success_count += 1
        print(f"{GREEN}✅ SUCCESS:{NC} {message}")
        
    def log_info(self, message: str):
        """Log an info message."""
        print(f"{BLUE}ℹ️  INFO:{NC} {message}")
        
    def validate_required(self, var_name: str, description: str = None) -> bool:
        """Validate that a required environment variable is set."""
        value = os.getenv(var_name)
        if not value:
            self.log_error(f"Required environment variable '{var_name}' is not set. {description or ''}")
            return False
        self.log_success(f"Required variable '{var_name}' is set")
        return True
        
    def validate_optional(self, var_name: str, default_value: str = None, description: str = None) -> bool:
        """Validate an optional environment variable."""
        value = os.getenv(var_name, default_value)
        if value:
            self.log_success(f"Optional variable '{var_name}' is set")
            return True
        else:
            self.log_warning(f"Optional variable '{var_name}' is not set. {description or ''}")
            return False
            
    def validate_url(self, var_name: str, required: bool = True) -> bool:
        """Validate that a URL environment variable is properly formatted."""
        value = os.getenv(var_name)
        if not value:
            if required:
                self.log_error(f"Required URL variable '{var_name}' is not set")
                return False
            else:
                self.log_warning(f"Optional URL variable '{var_name}' is not set")
                return False
                
        try:
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                self.log_error(f"Invalid URL format for '{var_name}': {value}")
                return False
            self.log_success(f"URL variable '{var_name}' has valid format")
            return True
        except Exception as e:
            self.log_error(f"Invalid URL format for '{var_name}': {value} - {e}")
            return False
            
    def validate_secret_strength(self, var_name: str, min_length: int = 32) -> bool:
        """Validate that a secret has sufficient strength."""
        value = os.getenv(var_name)
        if not value:
            self.log_error(f"Secret variable '{var_name}' is not set")
            return False
            
        if len(value) < min_length:
            self.log_error(f"Secret '{var_name}' is too short (minimum {min_length} characters)")
            return False
            
        # Check for common weak patterns
        weak_patterns = [
            r'password',
            r'123',
            r'test',
            r'demo',
            r'default',
            r'admin',
            r'secret',
            r'key'
        ]
        
        value_lower = value.lower()
        for pattern in weak_patterns:
            if re.search(pattern, value_lower):
                self.log_warning(f"Secret '{var_name}' contains potentially weak pattern: {pattern}")
                
        self.log_success(f"Secret '{var_name}' meets minimum strength requirements")
        return True
        
    def validate_database_url(self) -> bool:
        """Validate database URL configuration."""
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            try:
                parsed = urlparse(db_url)
                if parsed.scheme not in ['postgresql', 'mysql', 'sqlite']:
                    self.log_error(f"Unsupported database scheme in DATABASE_URL: {parsed.scheme}")
                    return False
                self.log_success("DATABASE_URL is properly configured")
                return True
            except Exception as e:
                self.log_error(f"Invalid DATABASE_URL format: {e}")
                return False
        else:
            # Check individual database variables
            required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                self.log_error(f"Missing database configuration variables: {', '.join(missing_vars)}")
                return False
            self.log_success("Database configuration via individual variables is complete")
            return True
            
    def validate_redis_url(self) -> bool:
        """Validate Redis URL configuration."""
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                parsed = urlparse(redis_url)
                if parsed.scheme not in ['redis', 'rediss']:
                    self.log_error(f"Invalid Redis URL scheme: {parsed.scheme}")
                    return False
                self.log_success("REDIS_URL is properly configured")
                return True
            except Exception as e:
                self.log_error(f"Invalid REDIS_URL format: {e}")
                return False
        else:
            # Check individual Redis variables
            required_vars = ['REDIS_HOST', 'REDIS_PORT']
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                self.log_warning(f"Missing Redis configuration variables: {', '.join(missing_vars)}")
                return False
            self.log_success("Redis configuration via individual variables is complete")
            return True
            
    def validate_aws_configuration(self) -> bool:
        """Validate AWS configuration."""
        aws_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION']
        missing_vars = [var for var in aws_vars if not os.getenv(var)]
        
        if missing_vars:
            self.log_warning(f"Missing AWS configuration variables: {', '.join(missing_vars)}")
            return False
            
        self.log_success("AWS configuration is complete")
        return True
        
    def validate_port_numbers(self) -> bool:
        """Validate that port numbers are within valid ranges."""
        port_vars = [
            ('PORT', 1, 65535),
            ('DB_PORT', 1, 65535),
            ('REDIS_PORT', 1, 65535),
        ]
        
        for var_name, min_port, max_port in port_vars:
            value = os.getenv(var_name)
            if value:
                try:
                    port = int(value)
                    if port < min_port or port > max_port:
                        self.log_error(f"Port '{var_name}' value {port} is outside valid range ({min_port}-{max_port})")
                        return False
                except ValueError:
                    self.log_error(f"Port '{var_name}' value '{value}' is not a valid number")
                    return False
                    
        self.log_success("All port numbers are within valid ranges")
        return True
        
    def validate_environment(self) -> bool:
        """Validate the complete environment configuration."""
        print(f"{BLUE}🔍 SmartCloudOps.AI Environment Validation{NC}")
        print("=" * 60)
        
        # Required variables
        required_vars = [
            ('SECRET_KEY', 'Required for Flask session security'),
            ('API_KEY_SALT', 'Required for secure API key hashing'),
        ]
        
        for var_name, description in required_vars:
            self.validate_required(var_name, description)
            
        # Optional but recommended variables
        optional_vars = [
            ('DATABASE_URL', 'Database connection URL'),
            ('REDIS_URL', 'Redis connection URL'),
            ('AWS_DEFAULT_REGION', 'AWS region for services'),
            ('PROMETHEUS_URL', 'Prometheus monitoring endpoint'),
            ('GRAFANA_ENDPOINT', 'Grafana monitoring endpoint'),
        ]
        
        for var_name, description in optional_vars:
            self.validate_optional(var_name, description=description)
            
        # URL validations
        self.validate_database_url()
        self.validate_redis_url()
        
        # Secret strength validations
        self.validate_secret_strength('SECRET_KEY', 32)
        self.validate_secret_strength('API_KEY_SALT', 32)
        
        # AWS configuration
        self.validate_aws_configuration()
        
        # Port number validations
        self.validate_port_numbers()
        
        # Environment-specific validations
        environment = os.getenv('ENVIRONMENT', 'development')
        if environment == 'production':
            self.log_info("Production environment detected - performing additional validations")
            
            # Production-specific requirements
            if os.getenv('FLASK_DEBUG', 'False').lower() == 'true':
                self.log_error("FLASK_DEBUG should be False in production")
                
            if not os.getenv('DATABASE_URL') and not all(os.getenv(var) for var in ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']):
                self.log_error("Database configuration is required in production")
                
        elif environment == 'development':
            self.log_info("Development environment detected")
            
        # Print summary
        print("\n" + "=" * 60)
        print(f"{BLUE}📊 Validation Summary:{NC}")
        print(f"✅ Successful validations: {self.success_count}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Errors: {len(self.errors)}")
        
        if self.warnings:
            print(f"\n{YELLOW}⚠️  Warnings:{NC}")
            for warning in self.warnings:
                print(f"  - {warning}")
                
        if self.errors:
            print(f"\n{RED}❌ Errors:{NC}")
            for error in self.errors:
                print(f"  - {error}")
                
        if not self.errors:
            print(f"\n{GREEN}🎉 Environment validation passed!{NC}")
            return True
        else:
            print(f"\n{RED}❌ Environment validation failed!{NC}")
            return False
            
    def generate_env_template(self) -> str:
        """Generate a template .env file with current values."""
        template = "# SmartCloudOps.AI Environment Configuration\n"
        template += "# Generated by environment validation script\n\n"
        
        # Common environment variables
        common_vars = [
            'ENVIRONMENT', 'PORT', 'HOST', 'SECRET_KEY', 'API_KEY_SALT',
            'DATABASE_URL', 'REDIS_URL', 'AWS_DEFAULT_REGION',
            'PROMETHEUS_URL', 'GRAFANA_ENDPOINT'
        ]
        
        for var in common_vars:
            value = os.getenv(var, '')
            if value:
                template += f"{var}={value}\n"
            else:
                template += f"# {var}=your_value_here\n"
                
        return template

def main():
    """Main function to run environment validation."""
    validator = EnvironmentValidator()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        validator.log_warning(".env file not found. Consider creating one from env.example")
    
    # Run validation
    success = validator.validate_environment()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
