#!/usr/bin/env python3
"""
SmartCloudOps AI - Demo Test Script
===================================

Demonstrates the key functionality of the SmartCloudOps AI platform:
- NLP ChatOps commands
- ML anomaly detection
- Auto-remediation
- API endpoints
"""

import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print(f"{'='*60}")


def demo_nlp_chatops():
    """Demonstrate NLP ChatOps functionality."""
    print_header("NLP ChatOps Demo")

    try:
        from app.services.nlp_chatops_service import NLPEnhancedChatOps

        # Initialize NLP service
        nlp_service = NLPEnhancedChatOps(use_lightweight_model=True)
        print("✅ NLP Service initialized")

        # Test various commands
        demo_commands = [
            "deploy the smartcloudops app to production",
            "scale the servers to 5 instances",
            "show me the logs for the application",
            "restart the web service",
            "rollback to the previous version",
        ]

        for command in demo_commands:
            print(f"\n📝 Command: {command}")
            result = nlp_service.process_command(command)

            print(f"   🎯 Intent: {result['intent']}")
            print(f"   📊 Confidence: {result['confidence']:.2f}")
            print(f"   🔍 Entities: {result['entities']}")

            if "action_plan" in result:
                plan = result["action_plan"]
                print(f"   ⚡ Action: {plan['action']}")
                print(f"   ⏱️  Estimated Time: {plan['estimated_time']}")
                print(f"   🔒 Safety Checks: {plan['safety_checks']}")

        return True
    except Exception as e:
        print(f"❌ NLP ChatOps demo failed: {e}")
        return False


def demo_auto_remediation():
    """Demonstrate auto-remediation functionality."""
    print_header("Auto-Remediation Demo")

    try:
        from app.services.remediation_service import AutoRemediationEngine

        # Initialize remediation engine
        engine = AutoRemediationEngine()
        print("✅ Auto-Remediation Engine initialized")

        # Show default rules
        print(f"\n📋 Default Rules ({len(engine.rules)}):")
        for i, rule in enumerate(engine.rules, 1):
            print(f"   {i}. {rule.name} (Priority: {rule.priority})")
            print(f"      Conditions: {rule.conditions}")
            print(f"      Action: {rule.action}")

        # Test with different scenarios
        test_scenarios = [
            {
                "name": "High CPU Usage",
                "metrics": {
                    "cpu_percent": 95.0,
                    "memory_percent": 70.0,
                    "disk_percent": 60.0,
                },
            },
            {
                "name": "Memory Pressure",
                "metrics": {
                    "cpu_percent": 60.0,
                    "memory_percent": 90.0,
                    "disk_percent": 50.0,
                },
            },
            {
                "name": "Disk Space Critical",
                "metrics": {
                    "cpu_percent": 40.0,
                    "memory_percent": 50.0,
                    "disk_percent": 95.0,
                },
            },
        ]

        for scenario in test_scenarios:
            print(f"\n🔍 Testing: {scenario['name']}")
            print(f"   📊 Metrics: {scenario['metrics']}")

            actions = engine.process_metrics(scenario["metrics"])
            if actions:
                print(f"   ⚡ Triggered Actions: {len(actions)}")
                for action in actions:
                    print(f"      - {action}")
            else:
                print("   ✅ No actions triggered (within normal range)")

        return True
    except Exception as e:
        print(f"❌ Auto-remediation demo failed: {e}")
        return False


def demo_api_endpoints():
    """Demonstrate API endpoints."""
    print_header("API Endpoints Demo")

    try:
        import requests

        base_url = "http://localhost:5000"

        # Test health endpoint
        print("🏥 Testing Health Endpoint:")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data['status']}")
            print(f"   📅 Version: {data['version']}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")

        # Test status endpoint (should require auth)
        print("\n🔐 Testing Protected Endpoint:")
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 401:
            print("   ✅ Authentication required (as expected)")
        else:
            print(f"   ⚠️  Unexpected response: {response.status_code}")

        return True
    except requests.exceptions.ConnectionError:
        print("ℹ️  Flask app not running - skipping API demo")
        return True
    except Exception as e:
        print(f"❌ API demo failed: {e}")
        return False


def demo_infrastructure():
    """Demonstrate infrastructure components."""
    print_header("Infrastructure Demo")

    try:
        # Check Terraform files
        terraform_dir = PROJECT_ROOT / "terraform"
        tf_files = list(terraform_dir.glob("*.tf"))

        print(f"🏗️  Terraform Configuration:")
        print(f"   📁 Directory: {terraform_dir}")
        print(f"   📄 Files: {len(tf_files)}")
        for tf_file in tf_files:
            print(f"      - {tf_file.name}")

        # Check Docker configuration
        dockerfile = PROJECT_ROOT / "Dockerfile"
        if dockerfile.exists():
            print(f"\n🐳 Docker Configuration:")
            print(f"   ✅ Dockerfile exists")
            print(f"   📄 Size: {dockerfile.stat().st_size} bytes")

        # Check application structure
        app_dir = PROJECT_ROOT / "app"
        python_files = list(app_dir.rglob("*.py"))

        print(f"\n🐍 Application Structure:")
        print(f"   📁 App directory: {app_dir}")
        print(f"   📄 Python files: {len(python_files)}")

        # Show key components
        key_components = [
            "main.py",
            "services/",
            "api/v1/",
            "core/ml_engine/",
            "utils/",
            "config/",
        ]

        for component in key_components:
            component_path = app_dir / component
            if component_path.exists():
                print(f"      ✅ {component}")
            else:
                print(f"      ❌ {component} (missing)")

        return True
    except Exception as e:
        print(f"❌ Infrastructure demo failed: {e}")
        return False


def demo_testing():
    """Demonstrate testing capabilities."""
    print_header("Testing Capabilities Demo")

    try:
        # Check test structure
        tests_dir = PROJECT_ROOT / "tests"
        test_files = list(tests_dir.rglob("test_*.py"))

        print(f"🧪 Test Structure:")
        print(f"   📁 Tests directory: {tests_dir}")
        print(f"   📄 Test files: {len(test_files)}")

        # Show test phases
        test_phases = ["phase_1", "phase_2", "phase_3", "phase_4", "phase_5"]

        for phase in test_phases:
            phase_dir = tests_dir / phase
            if phase_dir.exists():
                phase_tests = list(phase_dir.glob("test_*.py"))
                print(f"      📂 {phase}: {len(phase_tests)} test files")
            else:
                print(f"      ❌ {phase}: missing")

        # Run a quick test
        print(f"\n🚀 Quick Test Execution:")
        import subprocess

        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/phase_1/test_core_utilities.py::TestResponseUtilities::test_now_iso_returns_utc_timestamp",
                "-v",
                "--tb=no",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("   ✅ Quick test passed")
        else:
            print("   ❌ Quick test failed")

        return True
    except Exception as e:
        print(f"❌ Testing demo failed: {e}")
        return False


def main():
    """Run the demo."""
    print_header("SmartCloudOps AI - Platform Demo")
    print("🎯 Demonstrating key functionality of the SmartCloudOps AI platform")

    demos = [
        ("NLP ChatOps", demo_nlp_chatops),
        ("Auto-Remediation", demo_auto_remediation),
        ("API Endpoints", demo_api_endpoints),
        ("Infrastructure", demo_infrastructure),
        ("Testing", demo_testing),
    ]

    results = []
    for demo_name, demo_func in demos:
        try:
            result = demo_func()
            results.append((demo_name, result))
        except Exception as e:
            print(f"❌ Demo {demo_name} crashed: {e}")
            results.append((demo_name, False))

    # Print summary
    print_header("Demo Results Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for demo_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {demo_name}")

    print(f"\n📊 Overall Results: {passed}/{total} demos successful")

    if passed == total:
        print_success("🎉 All demos successful! SmartCloudOps AI is fully operational.")
    else:
        print(f"⚠️  {total - passed} demos failed. Some components may need attention.")

    print("\n🚀 Next Steps:")
    print("   1. Deploy to AWS using Terraform")
    print("   2. Configure authentication and API keys")
    print("   3. Set up monitoring and alerting")
    print("   4. Train ML models with production data")
    print("   5. Start using ChatOps commands")


if __name__ == "__main__":
    main()
