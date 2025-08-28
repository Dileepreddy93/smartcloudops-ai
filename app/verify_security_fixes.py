#!/usr/bin/env python3
"""
SmartCloudOps AI - Security Fixes Verification
=============================================

This script verifies that all security fixes have been properly implemented.
"""


import os
import re

from pathlib import Path
from typing import Any, Dict, List


def verify_environment_variables() -> Dict[str, Any]:
    """Verify that all required environment variables are set."""
    print("🔍 Verifying environment variables...")

    required_vars = [
        "JWT_SECRET_KEY",
        "ADMIN_API_KEY",
        "ML_API_KEY",
        "READONLY_API_KEY",
        "API_KEY_SALT",
        "ADMIN_PASSWORD",
    ]

    results = {"missing": [], "weak": [], "valid": []}

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            results["missing"].append(var)
        elif len(value) < 32:
            results["weak"].append(f"{var} (length: {len(value)})")
        elif any(pattern in value.lower() for pattern in ["demo", "test", "default", "password", "123"]):
            results["weak"].append(f"{var} (contains insecure pattern)")
        else:
            results["valid"].append(var)

    return results


def verify_hardcoded_secrets() -> List[Dict[str, Any]]:
    """Verify that no hardcoded secrets remain in the codebase."""
    print("🔍 Verifying no hardcoded secrets...")

    project_root = Path(__file__).parent.parent
    secret_patterns = [
        r"demo-key",
        r"test-key",
        r"default-password",
        r"admin123",
        r"password123",
        r"your-secret-key",
        r"change-in-production",
    ]

    found_secrets = []

    for file_path in project_root.rglob("*.py"):
        if any(skip_dir in str(file_path) for skip_dir in [".venv", "venv", "__pycache__", ".git"]):
            continue

        try:
            content = file_path.read_text()
            for pattern in secret_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    found_secrets.append(
                        {
                            "file": str(file_path.relative_to(project_root)),
                            "line": content[: match.start()].count("\n") + 1,
                            "pattern": pattern,
                            "match": match.group(),
                        }
                    )
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")

    return found_secrets


def verify_authentication_service() -> Dict[str, Any]:
    """Verify that the authentication service is properly configured."""
    print("🔍 Verifying authentication service...")

    try:
        from app.services.auth_service import AuthenticationService

        # Test initialization
        auth_service = AuthenticationService()

        # Test API key validation
        admin_key = os.getenv("ADMIN_API_KEY")
        if admin_key:
            key_info = auth_service.get_api_key_info(admin_key)
            if key_info and key_info["role"] == "admin":
                return {
                    "status": "PASS",
                    "message": "Authentication service properly configured",
                }
            else:
                return {"status": "FAIL", "message": "Admin API key validation failed"}
        else:
            return {"status": "FAIL", "message": "ADMIN_API_KEY not set"}

    except Exception as e:
        return {"status": "FAIL", "message": f"Authentication service error: {str(e)}"}


def verify_file_permissions() -> List[Dict[str, Any]]:
    """Verify file permissions for sensitive files."""
    print("🔍 Verifying file permissions...")

    project_root = Path(__file__).parent.parent
    sensitive_files = [".env", ".env.local", ".env.production"]
    permission_issues = []

    for file_name in sensitive_files:
        file_path = project_root / file_name
        if file_path.exists():
            stat = file_path.stat()
            if stat.st_mode & 0o004:  # World readable
                permission_issues.append(
                    {
                        "file": file_name,
                        "issue": "World readable",
                        "recommendation": "Set permissions to 600",
                    }
                )

    return permission_issues


def verify_security_headers() -> Dict[str, Any]:
    """Verify that security headers are properly configured."""
    print("🔍 Verifying security headers...")

    try:
        from app.main_secure import app

        # Test that security headers are configured
        if hasattr(app, "config") and app.config.get("SECURITY_HEADERS_ENABLED"):
            return {"status": "PASS", "message": "Security headers enabled"}
        else:
            return {
                "status": "WARN",
                "message": "Security headers not explicitly configured",
            }

    except Exception as e:
        return {
            "status": "FAIL",
            "message": f"Could not verify security headers: {str(e)}",
        }


def main():
    """Run comprehensive security verification."""
    print("🔒 SmartCloudOps AI - Security Fixes Verification")
    print("=" * 60)

    # Run all verifications
    env_results = verify_environment_variables()
    hardcoded_secrets = verify_hardcoded_secrets()
    auth_results = verify_authentication_service()
    permission_issues = verify_file_permissions()
    header_results = verify_security_headers()

    # Print results
    print("\n📊 Verification Results:")
    print("-" * 30)

    # Environment variables
    print("Environment Variables:")
    print(f"  ✅ Valid: {len(env_results['valid'])}")
    print(f"  ⚠️ Weak: {len(env_results['weak'])}")
    print(f"  ❌ Missing: {len(env_results['missing'])}")

    if env_results["missing"]:
        print(f"    Missing: {', '.join(env_results['missing'])}")
    if env_results["weak"]:
        print(f"    Weak: {', '.join(env_results['weak'])}")

    # Hardcoded secrets
    print("\nHardcoded Secrets:")
    print(f"  ❌ Found: {len(hardcoded_secrets)}")
    if hardcoded_secrets:
        for secret in hardcoded_secrets:
            print(f"    {secret['file']}:{secret['line']} - {secret['pattern']}")

    # Authentication service
    print("\nAuthentication Service:")
    print(f"  {auth_results['status']}: {auth_results['message']}")

    # File permissions
    print("\nFile Permissions:")
    print(f"  ❌ Issues: {len(permission_issues)}")
    if permission_issues:
        for issue in permission_issues:
            print(f"    {issue['file']}: {issue['issue']}")

    # Security headers
    print("\nSecurity Headers:")
    print(f"  {header_results['status']}: {header_results['message']}")

    # Overall assessment
    total_issues = (
        len(env_results["missing"])
        + len(env_results["weak"])
        + len(hardcoded_secrets)
        + len(permission_issues)
        + (1 if auth_results["status"] == "FAIL" else 0)
        + (1 if header_results["status"] == "FAIL" else 0)
    )

    print("\n" + "=" * 60)
    print("OVERALL ASSESSMENT")
    print("=" * 60)

    if total_issues == 0:
        print("✅ ALL SECURITY FIXES VERIFIED SUCCESSFULLY!")
        print("🔒 The application is ready for production deployment.")
    else:
        print(f"⚠️ {total_issues} SECURITY ISSUES REMAIN")
        print("🔧 Please address the issues above before production deployment.")

    print("=" * 60)


if __name__ == "__main__":
    main()
