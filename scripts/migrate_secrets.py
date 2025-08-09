#!/usr/bin/env python3
"""
SmartCloudOps AI - Secrets Manager Migration Tool
Migrates API keys from local files to AWS Secrets Manager
"""

import json
import boto3
import sys
import os
from datetime import datetime

def migrate_api_keys_to_secrets_manager():
    """Migrate API keys from local files to AWS Secrets Manager"""
    
    print("🔐 SmartCloudOps AI - Secrets Manager Migration")
    print("=" * 60)
    
    # Initialize AWS clients
    try:
        secrets_client = boto3.client('secretsmanager')
        print("✅ Connected to AWS Secrets Manager")
    except Exception as e:
        print(f"❌ Failed to connect to AWS Secrets Manager: {e}")
        print("   Make sure AWS credentials are configured properly")
        return False
    
    project_name = "smartcloudops-ai"
    migration_success = True
    
    # Load existing API keys database
    api_keys_file = '/home/dileep-reddy/smartcloudops-ai/api_keys_db.json'
    if os.path.exists(api_keys_file):
        try:
            with open(api_keys_file, 'r') as f:
                api_keys_db = json.load(f)
            print(f"✅ Loaded API keys database: {len(api_keys_db)} keys found")
        except Exception as e:
            print(f"❌ Failed to load API keys database: {e}")
            return False
    else:
        print("⚠️  No API keys database found - creating empty database")
        api_keys_db = {}
    
    # Migrate API keys database to Secrets Manager
    secret_name = f"{project_name}/app/api-keys-db"
    try:
        # Prepare the secret value
        secret_value = {
            "api_keys_database": api_keys_db,
            "migrated_at": datetime.now().isoformat(),
            "migration_source": "local_file",
            "key_count": len(api_keys_db)
        }
        
        # Store in Secrets Manager
        response = secrets_client.put_secret_value(
            SecretId=secret_name,
            SecretString=json.dumps(secret_value, indent=2)
        )
        
        print(f"✅ Migrated API keys database to Secrets Manager")
        print(f"   Secret ARN: {response['ARN']}")
        print(f"   Version ID: {response['VersionId']}")
        
    except secrets_client.exceptions.ResourceNotFoundException:
        print(f"❌ Secret '{secret_name}' not found in Secrets Manager")
        print("   Make sure Terraform infrastructure is deployed with enable_secrets_manager = true")
        migration_success = False
    except Exception as e:
        print(f"❌ Failed to migrate API keys database: {e}")
        migration_success = False
    
    # Migrate individual OpenAI key if available
    openai_key_file = '/home/dileep-reddy/smartcloudops-ai/.env'
    if os.path.exists(openai_key_file):
        try:
            with open(openai_key_file, 'r') as f:
                env_content = f.read()
            
            # Extract OpenAI API key
            for line in env_content.split('\n'):
                if line.startswith('OPENAI_API_KEY='):
                    openai_key = line.split('=', 1)[1].strip().strip('"\'')
                    
                    if openai_key and openai_key != "your_openai_api_key_here":
                        secret_name = f"{project_name}/openai/api-key"
                        try:
                            response = secrets_client.put_secret_value(
                                SecretId=secret_name,
                                SecretString=json.dumps({
                                    "api_key": openai_key,
                                    "migrated_at": datetime.now().isoformat()
                                })
                            )
                            print(f"✅ Migrated OpenAI API key to Secrets Manager")
                        except Exception as e:
                            print(f"❌ Failed to migrate OpenAI key: {e}")
                            migration_success = False
                    break
                    
        except Exception as e:
            print(f"⚠️  Could not process .env file: {e}")
    
    # Generate migration report
    print("\n📋 Migration Report")
    print("=" * 30)
    print(f"API Keys Database: {'✅ Migrated' if migration_success else '❌ Failed'}")
    print(f"Secrets in AWS: {len(api_keys_db)} application keys")
    
    # Test secret retrieval
    print("\n🧪 Testing Secret Retrieval")
    print("=" * 30)
    try:
        response = secrets_client.get_secret_value(
            SecretId=f"{project_name}/app/api-keys-db"
        )
        secret_data = json.loads(response['SecretString'])
        print(f"✅ Successfully retrieved API keys database from Secrets Manager")
        print(f"   Keys count: {secret_data.get('key_count', 0)}")
        print(f"   Migrated at: {secret_data.get('migrated_at', 'unknown')}")
    except Exception as e:
        print(f"❌ Failed to retrieve secret: {e}")
        migration_success = False
    
    # Security recommendations
    print("\n🛡️  Security Recommendations")
    print("=" * 30)
    print("1. Delete local API key files after successful migration:")
    print("   rm /home/dileep-reddy/smartcloudops-ai/api_keys_db.json")
    print("   rm /home/dileep-reddy/smartcloudops-ai/*_key.txt")
    print("   rm /home/dileep-reddy/smartcloudops-ai/generated_keys.json")
    
    print("\n2. Update application to use Secrets Manager:")
    print("   Modify app/main.py to retrieve keys from AWS Secrets Manager")
    print("   Remove hardcoded API keys from environment variables")
    
    print("\n3. Set up key rotation:")
    print("   Configure automatic rotation for sensitive API keys")
    print("   Monitor secret access in CloudTrail logs")
    
    return migration_success

def create_secrets_integration_script():
    """Create a Python script for applications to use Secrets Manager"""
    
    script_content = '''#!/usr/bin/env python3
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
'''
    
    script_file = '/home/dileep-reddy/smartcloudops-ai/app/secrets_manager.py'
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    print(f"✅ Created Secrets Manager integration script: {script_file}")

if __name__ == "__main__":
    try:
        print("🚀 Starting API Keys Migration to AWS Secrets Manager")
        print("=" * 60)
        
        # Check AWS credentials
        try:
            boto3.client('sts').get_caller_identity()
            print("✅ AWS credentials configured")
        except Exception as e:
            print(f"❌ AWS credentials not configured: {e}")
            print("   Configure AWS CLI: aws configure")
            sys.exit(1)
        
        # Perform migration
        success = migrate_api_keys_to_secrets_manager()
        
        # Create integration script
        create_secrets_integration_script()
        
        if success:
            print("\n🎉 Migration completed successfully!")
            print("   API keys are now securely stored in AWS Secrets Manager")
        else:
            print("\n⚠️  Migration completed with some errors")
            print("   Check the error messages above and retry if needed")
            
    except Exception as e:
        print(f"\n💥 Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
