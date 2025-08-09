#!/usr/bin/env python3
"""
SmartCloudOps AI - Simple API Key Generator
Creates API keys without needing complex imports
"""

import secrets
import hashlib
import json
import os
from datetime import datetime

def generate_api_key(length=32):
    """Generate a cryptographically secure API key"""
    return secrets.token_urlsafe(length)

def hash_key(key):
    """Hash API key with SHA256"""
    return hashlib.sha256(key.encode()).hexdigest()

def create_initial_keys():
    """Create initial API keys for system setup"""
    
    print("🔐 SmartCloudOps AI - Simple API Key Generator")
    print("=" * 50)
    
    # Create keys for different access levels
    keys = {}
    
    # Generate raw keys
    read_key = generate_api_key()
    write_key = generate_api_key()
    admin_key = generate_api_key()
    
    keys['read'] = {
        'key': read_key,
        'hash': hash_key(read_key),
        'user': 'monitoring-system',
        'level': 'read',
        'description': 'For monitoring dashboards and health checks'
    }
    
    keys['write'] = {
        'key': write_key,
        'hash': hash_key(write_key),
        'user': 'chatops-operator', 
        'level': 'write',
        'description': 'For ChatOps and ML prediction operations'
    }
    
    keys['admin'] = {
        'key': admin_key,
        'hash': hash_key(admin_key),
        'user': 'system-admin',
        'level': 'admin', 
        'description': 'For metrics access and system administration'
    }
    
    # Display created keys
    print("\n✅ API Keys Generated Successfully!")
    print("=" * 50)
    
    for level, info in keys.items():
        print(f"\n{level.upper()} ACCESS:")
        print(f"  User: {info['user']}")
        print(f"  Key:  {info['key']}")
        print(f"  Hash: {info['hash'][:16]}...")
        print(f"  Desc: {info['description']}")
    
    # Save keys to file for easy access
    keys_file = '/home/dileep-reddy/smartcloudops-ai/generated_keys.json'
    with open(keys_file, 'w') as f:
        json.dump({
            'created_at': datetime.now().isoformat(),
            'keys': keys,
            'usage_examples': {
                'read': f'curl -H "X-API-Key: {keys["read"]["key"]}" http://44.200.14.5:5000/status',
                'write': f'curl -H "X-API-Key: {keys["write"]["key"]}" -H "Content-Type: application/json" -d \'{{\"message\": \"What is the system status?\"}}\' http://44.200.14.5:5000/chat',
                'admin': f'curl -H "X-API-Key: {keys["admin"]["key"]}" http://44.200.14.5:5000/metrics'
            }
        }, f, indent=2)
    
    print(f"\n💾 Keys saved to: {keys_file}")
    
    # Create individual key files for easy script usage
    for level, info in keys.items():
        key_file = f'/home/dileep-reddy/smartcloudops-ai/{level}_key.txt'
        with open(key_file, 'w') as f:
            f.write(info['key'])
        print(f"   {level.capitalize()} key: {key_file}")
    
    # Create auth database format for manual integration
    auth_db = {}
    for level, info in keys.items():
        auth_db[info['hash']] = {
            'name': info['user'],
            'level': info['level'],
            'created': datetime.now().isoformat(),
            'rate_limit': 100
        }
    
    auth_db_file = '/home/dileep-reddy/smartcloudops-ai/api_keys_db.json'
    with open(auth_db_file, 'w') as f:
        json.dump(auth_db, f, indent=2)
    
    print(f"   Auth DB: {auth_db_file}")
    
    print("\n🧪 Test Commands:")
    print(f"   curl -H \"X-API-Key: {keys['read']['key']}\" http://44.200.14.5:5000/status")
    print(f"   curl -H \"X-API-Key: {keys['write']['key']}\" -d '{{\"message\":\"test\"}}' http://44.200.14.5:5000/chat")
    print(f"   curl -H \"X-API-Key: {keys['admin']['key']}\" http://44.200.14.5:5000/metrics")
    
    print("\n🛡️  Security Reminders:")
    print("  • These keys provide access to your SmartCloudOps AI system")
    print("  • Store them securely and never commit to version control")
    print("  • Each key has rate limiting (100 requests/hour)")
    print("  • Monitor usage in application logs")
    
    return keys

if __name__ == "__main__":
    try:
        create_initial_keys()
        print("\n✅ Setup complete! API keys are ready for use.")
    except Exception as e:
        print(f"\n❌ Error creating API keys: {e}")
        import traceback
        traceback.print_exc()
