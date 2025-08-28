#!/usr/bin/env python3
"""
SmartCloudOps AI - Workflow Monitor Test Suite
==============================================

Test suite to verify the workflow monitoring and auto-fix system works correctly.
This script tests all components of the workflow monitoring system.
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the monitoring classes
try:
    from scripts.workflow_monitor import WorkflowMonitor, WorkflowIssue
    from scripts.auto_workflow_fixer import WorkflowFixer
    from scripts.fix_all_workflow_issues import CompleteWorkflowFixer
except ImportError as e:
    print(f"❌ Failed to import monitoring modules: {e}")
    print("Make sure all required packages are installed:")
    print("pip install requests pyyaml python-dotenv")
    sys.exit(1)

class TestWorkflowMonitor(unittest.TestCase):
    """Test cases for WorkflowMonitor class."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_token = "test_token_12345"
        self.test_owner = "test-owner"
        self.test_repo = "test-repo"
        self.monitor = WorkflowMonitor(self.test_token, self.test_owner, self.test_repo)
    
    def test_monitor_initialization(self):
        """Test WorkflowMonitor initialization."""
        self.assertEqual(self.monitor.github_token, self.test_token)
        self.assertEqual(self.monitor.repo_owner, self.test_owner)
        self.assertEqual(self.monitor.repo_name, self.test_repo)
        self.assertEqual(self.monitor.base_url, f"https://api.github.com/repos/{self.test_owner}/{self.test_repo}")
    
    def test_analyze_workflow_logs(self):
        """Test workflow log analysis."""
        # Test log with Python import error
        test_log = """
        ModuleNotFoundError: No module named 'requests'
        Traceback (most recent call last):
          File "test.py", line 1, in <module>
            import requests
        ModuleNotFoundError: No module named 'requests'
        """
        
        issues = self.monitor.analyze_workflow_logs(test_log)
        self.assertGreater(len(issues), 0)
        
        # Check if Python import error is detected
        python_issues = [issue for issue in issues if issue.issue_type == "python_import_error"]
        self.assertGreater(len(python_issues), 0)
    
    def test_check_workflow_files(self):
        """Test workflow file checking."""
        # Create a temporary workflow directory
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / ".github" / "workflows"
            workflow_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a test workflow file
            test_workflow = workflow_dir / "test.yml"
            test_workflow.write_text("""
name: Test Workflow
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
            """)
            
            # Test workflow file checking
            with patch.object(self.monitor, 'workflow_dir', workflow_dir):
                issues = self.monitor.check_workflow_files()
                self.assertIsInstance(issues, list)
    
    def test_generate_report(self):
        """Test report generation."""
        # Add some test issues
        test_issue = WorkflowIssue(
            workflow_name="test",
            job_name="test-job",
            step_name="test-step",
            issue_type="test_issue",
            error_message="Test error",
            severity="medium",
            auto_fixable=True,
            fix_description="Test fix",
            fix_script="test command",
            detected_at=None
        )
        self.monitor.issues_found.append(test_issue)
        
        # Generate report
        report = self.monitor.generate_report()
        
        # Check report structure
        self.assertIn("timestamp", report)
        self.assertIn("total_issues", report)
        self.assertIn("fixed_issues", report)
        self.assertIn("open_issues", report)
        self.assertIn("issues_by_severity", report)
        self.assertIn("issues_by_type", report)
        self.assertIn("recommendations", report)

class TestWorkflowFixer(unittest.TestCase):
    """Test cases for WorkflowFixer class."""
    
    def setUp(self):
        """Set up test environment."""
        self.fixer = WorkflowFixer()
    
    def test_fixer_initialization(self):
        """Test WorkflowFixer initialization."""
        self.assertIsInstance(self.fixer.workflow_dir, Path)
        self.assertEqual(self.fixer.workflow_dir.name, "workflows")
        self.assertEqual(self.fixer.fixes_applied, [])
        self.assertEqual(self.fixer.issues_found, [])
    
    def test_analyze_workflows(self):
        """Test workflow analysis."""
        # Create a temporary workflow directory
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / ".github" / "workflows"
            workflow_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a test workflow file with issues
            test_workflow = workflow_dir / "test.yml"
            test_workflow.write_text("""
# Missing name field
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v1  # Deprecated action
            """)
            
            # Test workflow analysis
            with patch.object(self.fixer, 'workflow_dir', workflow_dir):
                issues = self.fixer.analyze_workflows()
                self.assertIsInstance(issues, list)
                self.assertGreater(len(issues), 0)
    
    def test_validate_workflows(self):
        """Test workflow validation."""
        # Create a temporary workflow directory with valid workflow
        with tempfile.TemporaryDirectory() as temp_dir:
            workflow_dir = Path(temp_dir) / ".github" / "workflows"
            workflow_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a valid workflow file
            test_workflow = workflow_dir / "test.yml"
            test_workflow.write_text("""
name: Test Workflow
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
            """)
            
            # Test workflow validation
            with patch.object(self.fixer, 'workflow_dir', workflow_dir):
                result = self.fixer.validate_workflows()
                self.assertTrue(result)

class TestCompleteWorkflowFixer(unittest.TestCase):
    """Test cases for CompleteWorkflowFixer class."""
    
    def setUp(self):
        """Set up test environment."""
        self.fixer = CompleteWorkflowFixer("test_token", "test-owner", "test-repo")
    
    def test_fixer_initialization(self):
        """Test CompleteWorkflowFixer initialization."""
        self.assertEqual(self.fixer.github_token, "test_token")
        self.assertEqual(self.fixer.repo_owner, "test-owner")
        self.assertEqual(self.fixer.repo_name, "test-repo")
        self.assertEqual(self.fixer.max_retries, 10)
        self.assertEqual(self.fixer.retry_delay, 60)
    
    def test_get_workflow_status(self):
        """Test workflow status retrieval."""
        # Mock the GitHub API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "workflow_runs": [
                {"conclusion": "success", "status": "completed"},
                {"conclusion": "failure", "status": "completed"},
                {"conclusion": None, "status": "in_progress"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.get', return_value=mock_response):
            status = self.fixer.get_workflow_status()
            
            self.assertEqual(status["status"], "available")
            self.assertEqual(status["failed_count"], 1)
            self.assertEqual(status["success_count"], 1)
            self.assertEqual(status["in_progress_count"], 1)
    
    def test_generate_final_report(self):
        """Test final report generation."""
        success = True
        report = self.fixer.generate_final_report(success)
        
        # Check report structure
        self.assertIn("timestamp", report)
        self.assertIn("success", report)
        self.assertIn("duration_seconds", report)
        self.assertIn("fixes_applied", report)
        self.assertIn("issues_resolved", report)
        self.assertIn("retry_count", report)
        self.assertIn("repo", report)
        self.assertIn("recommendations", report)
        
        self.assertTrue(report["success"])
        self.assertEqual(report["repo"], "test-owner/test-repo")

def run_integration_test():
    """Run integration test to verify the complete system."""
    print("🧪 Running integration test...")
    
    # Test 1: Check if all required files exist
    required_files = [
        "scripts/workflow_monitor.py",
        "scripts/auto_workflow_fixer.py", 
        "scripts/fix_all_workflow_issues.py",
        "scripts/run_workflow_monitor.sh",
        ".github/workflows/workflow-monitor.yml"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    else:
        print("✅ All required files found")
    
    # Test 2: Check if scripts are executable
    script_files = [
        "scripts/workflow_monitor.py",
        "scripts/auto_workflow_fixer.py",
        "scripts/fix_all_workflow_issues.py"
    ]
    
    for script_file in script_files:
        if not os.access(script_file, os.X_OK):
            print(f"⚠️  Script not executable: {script_file}")
    
    # Test 3: Test workflow directory structure
    workflow_dir = Path(".github/workflows")
    if workflow_dir.exists():
        workflow_files = list(workflow_dir.glob("*.yml"))
        print(f"✅ Found {len(workflow_files)} workflow files")
    else:
        print("⚠️  No .github/workflows directory found")
    
    # Test 4: Test environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        print("✅ GitHub token found")
    else:
        print("⚠️  GitHub token not set (GITHUB_TOKEN)")
    
    print("✅ Integration test completed")
    return True

def main():
    """Main test runner."""
    print("🚀 SmartCloudOps AI - Workflow Monitor Test Suite")
    print("=" * 60)
    
    # Run integration test
    integration_success = run_integration_test()
    print()
    
    # Run unit tests
    print("🧪 Running unit tests...")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowFixer))
    suite.addTests(loader.loadTestsFromTestCase(TestCompleteWorkflowFixer))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Integration Test: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    print(f"Unit Tests: {'✅ PASSED' if result.wasSuccessful() else '❌ FAILED'}")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    # Overall result
    overall_success = integration_success and result.wasSuccessful()
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())
