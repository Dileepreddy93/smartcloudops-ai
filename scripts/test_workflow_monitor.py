#!/usr/bin/env python3
"""
🧪 SmartCloudOps AI - Workflow Monitor Test Suite
=================================================

This script tests the workflow monitoring system to ensure all components
work correctly before running in production.

Tests include:
- Dependency installation
- GitHub API connectivity
- Workflow analysis capabilities
- Fix application logic
- Git operations
- Error handling
"""


import sys
import tempfile
import subprocess


import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))


class TestWorkflowMonitor(unittest.TestCase):
    """Test suite for workflow monitoring system"""

    def setUp(self):
        """Set up test environment"""
        self.test_token = "test_token_12345"
        self.test_repo_owner = "test_owner"
        self.test_repo_name = "test_repo"

        # Create temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Initialize git repository for testing
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            check=True,
            capture_output=True,
        )

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_import_workflow_monitor(self):
        """Test that WorkflowMonitor can be imported"""
        try:
            from auto_workflow_fixer import WorkflowMonitor

            self.assertTrue(True, "WorkflowMonitor imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import WorkflowMonitor: {e}")

    def test_workflow_monitor_initialization(self):
        """Test WorkflowMonitor initialization"""
        from auto_workflow_fixer import WorkflowMonitor

        monitor = WorkflowMonitor(
            self.test_repo_owner, self.test_repo_name, self.test_token
        )

        self.assertEqual(monitor.repo_owner, self.test_repo_owner)
        self.assertEqual(monitor.repo_name, self.test_repo_name)
        self.assertEqual(monitor.token, self.test_token)
        self.assertEqual(
            monitor.api_base,
            f"https://api.github.com/repos/{self.test_repo_owner}/{self.test_repo_name}",
        )
        self.assertIn("Authorization", monitor.headers)
        self.assertIn("Accept", monitor.headers)

    @patch("requests.get")
    def test_get_workflow_runs(self, mock_get):
        """Test getting workflow runs"""
        from auto_workflow_fixer import WorkflowMonitor

        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "workflow_runs": [
                {
                    "name": "Test Workflow",
                    "status": "completed",
                    "conclusion": "success",
                    "id": 123,
                    "html_url": "https://github.com/test/repo/actions/runs/123",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:01:00Z",
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        monitor = WorkflowMonitor(
            self.test_repo_owner, self.test_repo_name, self.test_token
        )
        runs = monitor.get_workflow_runs()

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].name, "Test Workflow")
        self.assertEqual(runs[0].status, "completed")
        self.assertEqual(runs[0].conclusion, "success")
        self.assertEqual(runs[0].run_id, 123)

    def test_analyze_failure_patterns(self):
        """Test failure pattern analysis"""
        from auto_workflow_fixer import WorkflowMonitor

        monitor = WorkflowMonitor(
            self.test_repo_owner, self.test_repo_name, self.test_token
        )

        # Test dependency issues
        logs_with_deps = "ModuleNotFoundError: No module named 'requests'"
        issues = monitor.analyze_failure(logs_with_deps)
        self.assertTrue(any("dependency" in issue for issue in issues))

        # Test test failures
        logs_with_tests = "FAILED test_example.py::test_function"
        issues = monitor.analyze_failure(logs_with_tests)
        self.assertTrue(any("test" in issue for issue in issues))

        # Test linting issues
        logs_with_lint = "flake8 found 5 errors"
        issues = monitor.analyze_failure(logs_with_lint)
        self.assertTrue(any("linting" in issue for issue in issues))

        # Test security issues
        logs_with_security = "bandit found security issues"
        issues = monitor.analyze_failure(logs_with_security)
        self.assertTrue(any("security" in issue for issue in issues))

        # Test build issues
        logs_with_build = "docker build failed"
        issues = monitor.analyze_failure(logs_with_build)
        self.assertTrue(any("build" in issue for issue in issues))

    def test_fix_dependency_issues(self):
        """Test dependency issue fixing"""
        from auto_workflow_fixer import WorkflowMonitor

        monitor = WorkflowMonitor(
            self.test_repo_owner, self.test_repo_name, self.test_token
        )

        # Create a test requirements file
        with open("requirements.txt", "w") as f:
            f.write("requests==2.31.0\npython-dotenv==1.0.0\n")

        # Test dependency fixing
        result = monitor.fix_dependency_issues()
        self.assertTrue(result)
        self.assertIn("dependency_issues", monitor.fixes_applied)

    def test_fix_test_issues(self):
        """Test test issue fixing"""
        from auto_workflow_fixer import WorkflowMonitor

        monitor = WorkflowMonitor(
            self.test_repo_owner, self.test_repo_name, self.test_token
        )

        # Test test fixing
        result = monitor.fix_test_issues()
        self.assertTrue(result)
        self.assertIn("test_issues", monitor.fixes_applied)

        # Check if test environment file was created
        self.assertTrue(os.path.exists(".env.test"))

    def test_fix_linting_issues(self):
        """Test linting issue fixing"""
        from auto_workflow_fixer import WorkflowMonitor

        monitor = WorkflowMonitor(
            self.test_repo_owner, self.test_repo_name, self.test_token
        )

        # Create a test Python file
        with open("test_file.py", "w") as f:
            f.write("import os\nprint('hello world')\n")

        # Test linting fixing
        result = monitor.fix_linting_issues()
        self.assertTrue(result)
        self.assertIn("linting_issues", monitor.fixes_applied)

    def test_fix_security_issues(self):
        """Test security issue fixing"""
        from auto_workflow_fixer import WorkflowMonitor

        monitor = WorkflowMonitor(
            self.test_repo_owner, self.test_repo_name, self.test_token
        )

        # Test security fixing
        result = monitor.fix_security_issues()
        self.assertTrue(result)
        self.assertIn("security_issues", monitor.fixes_applied)

    def test_commit_and_push_fixes(self):
        """Test committing and pushing fixes"""
        from auto_workflow_fixer import WorkflowMonitor

        monitor = WorkflowMonitor(
            self.test_repo_owner, self.test_repo_name, self.test_token
        )

        # Create a test file to commit
        with open("test_fix.txt", "w") as f:
            f.write("This is a test fix")

        # Test commit and push
        result = monitor.commit_and_push_fixes()
        self.assertTrue(result)

    def test_generate_report(self):
        """Test report generation"""
        from auto_workflow_fixer import WorkflowMonitor

        monitor = WorkflowMonitor(
            self.test_repo_owner, self.test_repo_name, self.test_token
        )
        monitor.fixes_applied = ["dependency_issues", "test_issues"]

        report = monitor.generate_report()

        self.assertIn("timestamp", report)
        self.assertIn("repo", report)
        self.assertIn("fixes_applied", report)
        self.assertIn("max_retries", report)
        self.assertIn("status", report)
        self.assertEqual(
            report["repo"], f"{self.test_repo_owner}/{self.test_repo_name}"
        )
        self.assertEqual(report["fixes_applied"], ["dependency_issues", "test_issues"])


class TestContinuousMonitor(unittest.TestCase):
    """Test suite for continuous monitoring"""

    def setUp(self):
        """Set up test environment"""
        self.test_token = "test_token_12345"

    def test_continuous_monitor_import(self):
        """Test that ContinuousWorkflowMonitor can be imported"""
        try:
            from monitor_workflows import ContinuousWorkflowMonitor

            self.assertTrue(True, "ContinuousWorkflowMonitor imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import ContinuousWorkflowMonitor: {e}")

    def test_continuous_monitor_initialization(self):
        """Test ContinuousWorkflowMonitor initialization"""
        from monitor_workflows import ContinuousWorkflowMonitor

        monitor = ContinuousWorkflowMonitor(interval=60)

        self.assertEqual(monitor.interval, 60)
        self.assertTrue(monitor.running)
        self.assertIsNone(monitor.monitor)
        self.assertEqual(monitor.stats["checks"], 0)
        self.assertEqual(monitor.stats["fixes_applied"], 0)
        self.assertEqual(monitor.stats["workflows_fixed"], 0)


def run_integration_tests():
    """Run integration tests"""
    print("🧪 Running integration tests...")

    # Test dependency installation
    print("  📦 Testing dependency installation...")
    try:
        import subprocess

        subprocess.run(
            [sys.executable, "-m", "pip", "install", "requests", "python-dotenv"],
            check=True,
            capture_output=True,
        )
        print("    ✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"    ❌ Failed to install dependencies: {e}")
        return False

    # Test git operations
    print("  🔧 Testing git operations...")
    try:
        import subprocess

        result = subprocess.run(["git", "status"], capture_output=True, text=True)
        if result.returncode == 0:
            print("    ✅ Git operations working")
        else:
            print("    ❌ Git operations failed")
            return False
    except Exception as e:
        print(f"    ❌ Git test failed: {e}")
        return False

    # Test Python imports
    print("  🐍 Testing Python imports...")
    try:
        import json
        import subprocess

        import requests

        print("    ✅ Python imports working")
    except ImportError as e:
        print(f"    ❌ Python import failed: {e}")
        return False

    return True


def main():
    """Main test function"""
    print("🧪 SmartCloudOps AI - Workflow Monitor Test Suite")
    print("=" * 60)

    # Run integration tests first
    if not run_integration_tests():
        print("❌ Integration tests failed")
        sys.exit(1)

    print("✅ Integration tests passed")
    print("")

    # Run unit tests
    print("🧪 Running unit tests...")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestContinuousMonitor))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("")
    print("📊 Test Summary:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
