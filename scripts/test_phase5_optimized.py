#!/usr/bin/env python3
"""
SmartCloudOps AI - Phase 5 Optimized Test Runner
===============================================

Optimized test runner for Phase 5 ChatOps functionality with resource monitoring.
"""

import os
import sys
import time
import psutil
import subprocess
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set environment variables for resource optimization
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"
os.environ["TESTING"] = "true"


def monitor_resources():
    """Monitor system resources during test execution."""
    process = psutil.Process()
    memory_info = process.memory_info()
    cpu_percent = process.cpu_percent()

    print(f"Memory Usage: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"CPU Usage: {cpu_percent:.2f}%")

    return memory_info.rss, cpu_percent


def run_optimized_tests():
    """Run Phase 5 tests with optimized settings."""
    print("🚀 Starting Phase 5 Optimized Test Runner")
    print("=" * 50)

    # Monitor initial resources
    print("📊 Initial Resource Usage:")
    initial_memory, initial_cpu = monitor_resources()

    # Test 1: Basic NLP service initialization
    print("\n🧪 Test 1: NLP Service Initialization")
    start_time = time.time()

    try:
        from app.services.nlp_chatops_service import NLPEnhancedChatOps

        nlp_service = NLPEnhancedChatOps(use_lightweight_model=True)
        init_time = time.time() - start_time
        print(f"✅ NLP Service initialized in {init_time:.2f}s")

        # Test basic functionality
        result = nlp_service.process_command("deploy the app")
        assert result["status"] == "success"
        assert result["intent"] == "deploy"
        print("✅ Basic command processing works")

    except Exception as e:
        print(f"❌ NLP Service test failed: {e}")
        return False

    # Test 2: AWS Integration Service
    print("\n🧪 Test 2: AWS Integration Service")
    try:
        from app.services.aws_integration_service import AWSIntegrationService

        aws_service = AWSIntegrationService()

        # Test safety limits
        result = aws_service._check_safety_limits("scale", {"count": 5})
        assert result["safe"] is True
        print("✅ AWS service safety checks work")

    except Exception as e:
        print(f"❌ AWS Service test failed: {e}")
        return False

    # Test 3: Pytest execution
    print("\n🧪 Test 3: Pytest Execution")
    pytest_start = time.time()

    try:
        # Run a subset of tests with optimized settings
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_phase5_chatops.py::TestNLPEnhancedChatOps::test_initialization",
            "-v",
            "--tb=short",
            "--maxfail=1",
            "--disable-warnings",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env=dict(os.environ, OMP_NUM_THREADS="1", TOKENIZERS_PARALLELISM="false"),
        )

        pytest_time = time.time() - pytest_start

        if result.returncode == 0:
            print(f"✅ Pytest completed in {pytest_time:.2f}s")
            print("✅ All tests passed")
        else:
            print(f"❌ Pytest failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Pytest timed out after 60s")
        return False
    except Exception as e:
        print(f"❌ Pytest execution failed: {e}")
        return False

    # Monitor final resources
    print("\n📊 Final Resource Usage:")
    final_memory, final_cpu = monitor_resources()

    # Calculate resource usage
    memory_diff = (final_memory - initial_memory) / 1024 / 1024
    print(f"\n📈 Resource Summary:")
    print(f"Memory Increase: {memory_diff:.2f} MB")
    print(f"CPU Usage: {final_cpu:.2f}%")

    print("\n✅ Phase 5 Optimized Test Runner completed successfully!")
    return True


def main():
    """Main function."""
    try:
        success = run_optimized_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
