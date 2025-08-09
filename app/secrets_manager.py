#!/usr/bin/env python3
"""
SmartCloudOps AI - Secrets Manager Integration
Helper functions to retrieve secrets from AWS Secrets Manager
"""

import boto3
import json
import logging
from functools import lru_cache
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SecretsManagerClient:
    """AWS Secrets Manager client for SmartCloudOps AI"""
    
    def __init__(self, project_name: str = "smartcloudops-ai"):
        self.project_name = project_name
        self.client = boto3.client('secretsmanager')
    
    @lru_cache(maxsize=10)
    def get_secret(self, secret_name: str) -> Optional[Dict]:
        """Retrieve and cache secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            return None
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from Secrets Manager"""
        secret = self.get_secret(f"{self.project_name}/openai/api-key")
        return secret.get('api_key') if secret else None
    
    def get_gemini_api_key(self) -> Optional[str]:
        """Get Gemini API key from Secrets Manager"""
        secret = self.get_secret(f"{self.project_name}/gemini/api-key")
        return secret.get('api_key') if secret else None
    
    def get_api_keys_database(self) -> Dict:
        """Get application API keys database from Secrets Manager"""
        secret = self.get_secret(f"{self.project_name}/app/api-keys-db")
        if secret:
            return secret.get('api_keys_database', {})
        return {}
    
    def refresh_cache(self):
        """Clear the cache to force fresh secret retrieval"""
        self.get_secret.cache_clear()

# Global instance for easy import
secrets_manager = SecretsManagerClient()

# Usage example:
if __name__ == "__main__":
    # Test secret retrieval
    sm = SecretsManagerClient()
    
    print("Testing Secrets Manager integration...")
    
    # Test API keys database
    api_keys = sm.get_api_keys_database()
    print(f"API keys database loaded: {len(api_keys)} keys")
    
    # Test OpenAI key
    openai_key = sm.get_openai_api_key()
    print(f"OpenAI API key: {'✅ Found' if openai_key else '❌ Not found'}")
    
    # Test Gemini key
    gemini_key = sm.get_gemini_api_key()
    print(f"Gemini API key: {'✅ Found' if gemini_key else '❌ Not found'}")
