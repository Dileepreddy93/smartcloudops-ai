#!/usr/bin/env python3
"""
SmartCloudOps AI - API Key Management Script
Creates initial API keys for system setup
"""

import sys
import os
import json
from datetime import datetime

# Add app directory to Python path
sys.path.append('/home/dileep-reddy/smartcloudops-ai/app')

try:
    from auth import APIKeyAuth
except ImportError:
    print("Error: Could not import auth module. Make sure you're in the correct directory.")
    sys.exit(1)

def create_initial_keys():
    """Create initial API keys for system setup"""
    
    print("🔐 SmartCloudOps AI - API Key Setup")
    print("=" * 50)
    
    # Initialize authentication system
    auth = APIKeyAuth()
    
    # Create keys for different access levels
    keys = {}
    
    # Read access key for monitoring systems
    read_key = auth.create_key("monitoring-system", "read")
    keys['read'] = {
        'key': read_key,
        'user': 'monitoring-system',
        'level': 'read',
        'description': 'For monitoring dashboards and health checks'
    }
    
    # Write access key for ChatOps operations
    write_key = auth.create_key("chatops-operator", "write")
    keys['write'] = {
        'key': write_key,
        'user': 'chatops-operator', 
        'level': 'write',
        'description': 'For ChatOps and ML prediction operations'
    }
    
    # Admin access key for system administration
    admin_key = auth.create_key("system-admin", "admin")
    keys['admin'] = {
        'key': admin_key,
        'user': 'system-admin',
        'level': 'admin', 
        'description': 'For metrics access and system administration'
    }
    
    # Display created keys
    print("\n✅ API Keys Created Successfully!")
    print("=" * 50)
    
    for level, info in keys.items():
        print(f"\n{level.upper()} ACCESS:")
        print(f"  User: {info['user']}")
        print(f"  Key:  {info['key']}")
        print(f"  Desc: {info['description']}")
        print(f"  Test: curl -H \"X-API-Key: {info['key']}\" http://44.200.14.5:5000/status")
    
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
        }, indent=2)
    
    print(f"\n💾 Keys saved to: {keys_file}")
    
    # Create individual key files for easy script usage
    for level, info in keys.items():
        key_file = f'/home/dileep-reddy/smartcloudops-ai/{level}_key.txt'
        with open(key_file, 'w') as f:
            f.write(info['key'])
        print(f"   {level.capitalize()} key: {key_file}")
    
    print("\n🛡️  Security Reminders:")
    print("  • These keys provide access to your SmartCloudOps AI system")
    print("  • Store them securely and never commit to version control")
    print("  • Each key has rate limiting (100 requests/hour)")
    print("  • Monitor usage in application logs")
    
    print("\n🚀 Next Steps:")
    print("  1. Test the keys with the curl commands above")
    print("  2. Integrate keys into your monitoring/ChatOps systems")
    print("  3. Review API_KEYS_SETUP.md for detailed usage guide")
    print("  4. Monitor authentication logs for proper operation")
    
    return keys

if __name__ == "__main__":
    try:
        create_initial_keys()
        print("\n✅ Setup complete! API keys are ready for use.")
    except Exception as e:
        print(f"\n❌ Error creating API keys: {e}")
        print("Make sure the authentication system is properly configured.")
        sys.exit(1)
