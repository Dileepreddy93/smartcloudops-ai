#!/usr/bin/env python3
"""
Production Setup Test Script
===========================

Simple test script to validate the production setup without requiring pytest.
This script tests the critical components and provides a summary report.
"""


import os
import sys
import time
import json
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../app"))


def test_environment_variables():
    """Test that required environment variables are set."""
    print("🔍 Testing environment variables...")

    required_vars = [
        "SECRET_KEY",
        "ADMIN_API_KEY",
        "ML_API_KEY",
        "READONLY_API_KEY",
        "API_KEY_SALT",
        "DB_PASSWORD",
    ]

    missing_vars = []
    insecure_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif len(value) < 32:
            insecure_vars.append(f"{var} (too short: {len(value)} chars)")
        elif any(
            pattern in value.lower()
            for pattern in ["demo", "test", "default", "password", "123"]
        ):
            insecure_vars.append(f"{var} (contains insecure pattern)")

    if missing_vars:
        print(f"❌ Missing required variables: {', '.join(missing_vars)}")
        return False

    if insecure_vars:
        print(f"⚠️ Potentially insecure variables: {', '.join(insecure_vars)}")

    print("✅ Environment variables test passed")
    return True


def test_database_components():
    """Test database-related components."""
    print("🗄️ Testing database components...")

    try:
        # Test if we can import the database module
        from database_improvements import get_db_service

        # Test if we can create a database service instance
        db_service = get_db_service()

        print("✅ Database components test passed")
        return True

    except Exception as e:
        print(f"❌ Database components test failed: {e}")
        return False


def test_ml_components():
    """Test ML pipeline components."""
    print("🤖 Testing ML pipeline components...")

    try:
        # Test if we can import the ML module
        from ml_production_pipeline import get_ml_pipeline

        # Test if we can create an ML pipeline instance
        ml_pipeline = get_ml_pipeline()

        print("✅ ML pipeline components test passed")
        return True

    except Exception as e:
        print(f"❌ ML pipeline components test failed: {e}")
        return False


def test_monitoring_components():
    """Test monitoring components."""
    print("📊 Testing monitoring components...")

    try:
        # Test if we can import the monitoring module
        from monitoring.production_monitoring import get_monitoring

        # Test if we can create a monitoring instance
        monitoring = get_monitoring()

        print("✅ Monitoring components test passed")
        return True

    except Exception as e:
        print(f"❌ Monitoring components test failed: {e}")
        return False


def test_production_app():
    """Test production application components."""
    print("🚀 Testing production application...")

    try:
        # Test if we can import the production app
        from main_production import create_production_app

        # Test if we can create the app
        app = create_production_app()

        print("✅ Production application test passed")
        return True

    except Exception as e:
        print(f"❌ Production application test failed: {e}")
        return False


def test_security_components():
    """Test security components."""
    print("🔒 Testing security components...")

    try:
        # Test if we can import security modules
        from auth_secure import get_request_id

        # Test request ID generation
        request_id = get_request_id()
        if request_id and len(request_id) > 0:
            print("✅ Security components test passed")
            return True
        else:
            print("❌ Security components test failed: invalid request ID")
            return False

    except Exception as e:
        print(f"❌ Security components test failed: {e}")
        return False


def test_terraform_configuration():
    """Test Terraform configuration files."""
    print("🏗️ Testing Terraform configuration...")

    terraform_files = [
        "terraform/production/main.tf",
        "terraform/production/variables.tf",
        "terraform/production/terraform.tfvars.example",
        "terraform/production/user_data.sh",
    ]

    missing_files = []

    for file_path in terraform_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing Terraform files: {', '.join(missing_files)}")
        return False

    print("✅ Terraform configuration test passed")
    return True


def test_docker_configuration():
    """Test Docker configuration files."""
    print("🐳 Testing Docker configuration...")

    docker_files = ["Dockerfile.production", "docker/docker-compose.yml"]

    missing_files = []

    for file_path in docker_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing Docker files: {', '.join(missing_files)}")
        return False

    print("✅ Docker configuration test passed")
    return True


def test_scripts():
    """Test deployment and setup scripts."""
    print("📜 Testing deployment scripts...")

    script_files = [
        "scripts/setup_secure_environment.sh",
        "scripts/deploy_production.sh",
        "scripts/test_production_setup.py",
    ]

    missing_files = []

    for file_path in script_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing script files: {', '.join(missing_files)}")
        return False

    print("✅ Deployment scripts test passed")
    return True


def generate_test_report(results):
    """Generate a comprehensive test report."""
    print("\n" + "=" * 60)
    print("📋 PRODUCTION SETUP TEST REPORT")
    print("=" * 60)

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")

    print("\nDetailed Results:")
    print("-" * 40)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")

    if failed_tests > 0:
        print(f"\n❌ {failed_tests} test(s) failed. Please fix the issues above.")
        return False
    else:
        print(f"\n🎉 All {total_tests} tests passed! Production setup is ready.")
        return True


def main():
    """Run all production setup tests."""
    print("🧪 SmartCloudOps AI - Production Setup Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Run all tests
    test_results = {
        "Environment Variables": test_environment_variables(),
        "Database Components": test_database_components(),
        "ML Pipeline Components": test_ml_components(),
        "Monitoring Components": test_monitoring_components(),
        "Production Application": test_production_app(),
        "Security Components": test_security_components(),
        "Terraform Configuration": test_terraform_configuration(),
        "Docker Configuration": test_docker_configuration(),
        "Deployment Scripts": test_scripts(),
    }

    # Generate report
    success = generate_test_report(test_results)

    # Save detailed results to file
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(test_results),
        "passed_tests": sum(1 for result in test_results.values() if result),
        "failed_tests": sum(1 for result in test_results.values() if not result),
        "results": test_results,
        "success": success,
    }

    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")

    if success:
        print("\n🎉 PRODUCTION SETUP VALIDATION COMPLETED SUCCESSFULLY!")
        print("\n📝 Next Steps:")
        print("1. Run: ./scripts/setup_secure_environment.sh")
        print("2. Update AWS credentials in .env file")
        print("3. Run: ./scripts/deploy_production.sh")
        print("4. Monitor deployment and verify all services")
        return 0
    else:
        print("\n❌ PRODUCTION SETUP VALIDATION FAILED!")
        print("Please fix the issues above before proceeding with deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
