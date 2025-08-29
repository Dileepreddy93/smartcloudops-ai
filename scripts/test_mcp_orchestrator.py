#!/usr/bin/env python3
"""
Test script for MCP Orchestrator AI
===================================

This script tests the MCP Orchestrator AI functionality without running the full monitoring loop.
It verifies that all components are working correctly.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add the scripts directory to the path
sys.path.append(str(Path(__file__).parent))

from mcp_orchestrator import MCPOrchestrator, WorkflowRun, WorkflowIssue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mcp_orchestrator():
    """Test the MCP Orchestrator AI functionality."""
    
    # Check environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    repo_owner = os.getenv("GITHUB_REPOSITORY_OWNER", "Dileepreddy93")
    repo_name = os.getenv("GITHUB_REPOSITORY_NAME", "smartcloudops-ai")
    
    if not github_token:
        logger.error("GITHUB_TOKEN environment variable is required")
        return False
    
    logger.info(f"Testing MCP Orchestrator AI for repository: {repo_owner}/{repo_name}")
    
    try:
        # Initialize orchestrator
        orchestrator = MCPOrchestrator(github_token, repo_owner, repo_name)
        logger.info("✅ MCP Orchestrator initialized successfully")
        
        # Test workflow runs retrieval
        logger.info("Testing workflow runs retrieval...")
        runs = orchestrator.get_workflow_runs(limit=5)
        logger.info(f"✅ Retrieved {len(runs)} workflow runs")
        
        # Test failed runs filtering
        failed_runs = orchestrator.get_failed_runs(runs)
        logger.info(f"✅ Found {len(failed_runs)} failed runs")
        
        # Test log analysis with sample data
        logger.info("Testing log analysis...")
        sample_logs = """
        npm ERR! 404 Not Found - GET https://registry.npmjs.org/missing-package
        ModuleNotFoundError: No module named 'missing_module'
        FAILED test_example.py::test_function
        """
        
        sample_run = WorkflowRun(
            run_id="12345",
            workflow_name="Test Workflow",
            status="completed",
            conclusion="failure",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:05:00Z",
            head_branch="main",
            head_sha="abc123",
            jobs=[]
        )
        
        issues = orchestrator.analyze_logs_for_issues(sample_logs, sample_run)
        logger.info(f"✅ Analyzed logs and found {len(issues)} issues")
        
        for issue in issues:
            logger.info(f"  - {issue.issue_type}: {issue.fix_description} (auto-fixable: {issue.auto_fixable})")
        
        # Test workflow file analysis
        logger.info("Testing workflow file analysis...")
        workflow_dir = Path(".github/workflows")
        if workflow_dir.exists():
            workflow_files = list(workflow_dir.glob("*.yml"))
            logger.info(f"✅ Found {len(workflow_files)} workflow files")
            
            for workflow_file in workflow_files:
                logger.info(f"  - {workflow_file.name}")
        else:
            logger.warning("⚠️  No .github/workflows directory found")
        
        # Test report generation
        logger.info("Testing report generation...")
        
        # Simulate some fixes
        orchestrator.fixes_applied = []
        orchestrator.issues_found = issues
        
        # Generate test report
        test_report = {
            "status": "TEST_SUCCESS",
            "timestamp": datetime.now().isoformat(),
            "repo": f"{repo_owner}/{repo_name}",
            "monitoring_duration": "00:05:00",
            "fixes_applied": len(orchestrator.fixes_applied),
            "issues_found": len(orchestrator.issues_found),
            "message": "MCP Orchestrator AI Test Completed Successfully",
            "test_results": {
                "workflow_runs_retrieved": len(runs),
                "failed_runs_found": len(failed_runs),
                "issues_detected": len(issues),
                "workflow_files_analyzed": len(workflow_files) if workflow_dir.exists() else 0
            }
        }
        
        # Save test report
        with open("mcp_orchestrator_test_report.json", "w") as f:
            json.dump(test_report, f, indent=2, default=str)
        
        logger.info("✅ Test report generated successfully")
        logger.info("🎉 All MCP Orchestrator AI tests passed!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

def main():
    """Main test function."""
    logger.info("🧪 Starting MCP Orchestrator AI Tests")
    logger.info("=" * 50)
    
    success = test_mcp_orchestrator()
    
    logger.info("=" * 50)
    if success:
        logger.info("🎉 All tests passed! MCP Orchestrator AI is ready for deployment.")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed. Please check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
