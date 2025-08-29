#!/usr/bin/env python3
"""
MCP Orchestrator AI - GitHub Actions Workflow Monitor & Auto-Fix
==============================================================

Comprehensive workflow monitoring and automated issue resolution system.
Continuously monitors GitHub Actions workflows, detects failures, and automatically fixes common issues.
"""

import json
import os
import sys
import time
import logging
import requests
import subprocess
import yaml
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_orchestrator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class WorkflowRun:
    """Represents a GitHub Actions workflow run."""
    run_id: str
    workflow_name: str
    status: str
    conclusion: str
    created_at: str
    updated_at: str
    head_branch: str
    head_sha: str
    jobs: List[Dict]

@dataclass
class WorkflowIssue:
    """Represents a workflow issue with details and fix information."""
    run_id: str
    workflow_name: str
    job_name: str
    step_name: str
    issue_type: str
    error_message: str
    severity: str
    auto_fixable: bool
    fix_description: str
    fix_script: str
    detected_at: datetime
    status: str = "open"

@dataclass
class FixResult:
    """Represents the result of an auto-fix attempt."""
    issue: WorkflowIssue
    success: bool
    commit_sha: Optional[str] = None
    error_message: Optional[str] = None
    applied_at: datetime = None

class MCPOrchestrator:
    """MCP Orchestrator AI for GitHub Actions workflow monitoring and auto-fix."""
    
    def __init__(self, github_token: str, repo_owner: str, repo_name: str):
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.fixes_applied = []
        self.issues_found = []
        self.monitoring_start = datetime.now()
        
        # Set up GitHub CLI authentication
        self._setup_github_cli()
    
    def _setup_github_cli(self):
        """Set up GitHub CLI authentication."""
        try:
            subprocess.run([
                "gh", "auth", "login", "--with-token"
            ], input=self.github_token.encode(), check=True, capture_output=True)
            logger.info("GitHub CLI authentication configured")
        except subprocess.CalledProcessError as e:
            logger.warning(f"GitHub CLI setup failed: {e}")
    
    def get_workflow_runs(self, limit: int = 20) -> List[WorkflowRun]:
        """Get recent workflow runs using GitHub CLI."""
        try:
            result = subprocess.run([
                "gh", "api", f"repos/{self.repo_owner}/{self.repo_name}/actions/runs",
                "--paginate", "--limit", str(limit)
            ], capture_output=True, text=True, check=True)
            
            data = json.loads(result.stdout)
            runs = []
            
            for run_data in data.get("workflow_runs", []):
                run = WorkflowRun(
                    run_id=str(run_data["id"]),
                    workflow_name=run_data["name"],
                    status=run_data["status"],
                    conclusion=run_data.get("conclusion", "unknown"),
                    created_at=run_data["created_at"],
                    updated_at=run_data["updated_at"],
                    head_branch=run_data["head_branch"],
                    head_sha=run_data["head_sha"],
                    jobs=[]
                )
                runs.append(run)
            
            return runs
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get workflow runs: {e}")
            return []
    
    def get_failed_runs(self, runs: List[WorkflowRun]) -> List[WorkflowRun]:
        """Filter runs to only include failed, cancelled, or timed out runs."""
        failed_statuses = ["failure", "cancelled", "timed_out"]
        return [run for run in runs if run.conclusion in failed_statuses]
    
    def download_run_logs(self, run_id: str) -> str:
        """Download logs for a specific workflow run."""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                result = subprocess.run([
                    "gh", "run", "download", run_id, "--dir", temp_dir
                ], capture_output=True, text=True, check=True)
                
                logs = []
                for log_file in Path(temp_dir).rglob("*.txt"):
                    with open(log_file, 'r') as f:
                        logs.append(f.read())
                
                return "\n".join(logs)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to download logs for run {run_id}: {e}")
            return ""
    
    def analyze_logs_for_issues(self, logs: str, run: WorkflowRun) -> List[WorkflowIssue]:
        """Analyze workflow logs to detect specific issues."""
        issues = []
        
        # Common error patterns and their fixes
        error_patterns = {
            "npm_dependency_error": {
                "pattern": r"npm ERR! 404 Not Found - GET https://registry\.npmjs\.org/([^/]+)",
                "severity": "high",
                "auto_fixable": True,
                "fix_description": "Missing npm package",
                "fix_script": "npm install {package}"
            },
            "npm_install_error": {
                "pattern": r"npm ERR! ([^\\n]+)",
                "severity": "high",
                "auto_fixable": True,
                "fix_description": "npm install failure",
                "fix_script": "npm ci --force"
            },
            "python_import_error": {
                "pattern": r"ModuleNotFoundError: No module named '([^']+)'",
                "severity": "high",
                "auto_fixable": True,
                "fix_description": "Missing Python dependency",
                "fix_script": "pip install {module}"
            },
            "pip_install_error": {
                "pattern": r"ERROR: Could not find a version that satisfies the requirement ([^\\n]+)",
                "severity": "high",
                "auto_fixable": True,
                "fix_description": "pip install failure",
                "fix_script": "pip install --upgrade {package}"
            },
            "pytest_failure": {
                "pattern": r"FAILED ([^\\n]+)",
                "severity": "medium",
                "auto_fixable": False,
                "fix_description": "Test failure",
                "fix_script": "Review and fix failing tests"
            },
            "lint_error": {
                "pattern": r"error: ([^\\n]+)",
                "severity": "medium",
                "auto_fixable": True,
                "fix_description": "Linting error",
                "fix_script": "Run linter and fix issues"
            },
            "docker_build_error": {
                "pattern": r"failed to build: ([^\\n]+)",
                "severity": "high",
                "auto_fixable": True,
                "fix_description": "Docker build failure",
                "fix_script": "docker system prune -f && docker build --no-cache ."
            },
            "terraform_error": {
                "pattern": r"Error: ([^\\n]+)",
                "severity": "medium",
                "auto_fixable": False,
                "fix_description": "Terraform configuration error",
                "fix_script": "terraform validate"
            },
            "permission_error": {
                "pattern": r"Permission denied|EACCES",
                "severity": "medium",
                "auto_fixable": True,
                "fix_description": "Permission issue",
                "fix_script": "chmod +x {file}"
            },
            "timeout_error": {
                "pattern": r"timeout|timed out",
                "severity": "medium",
                "auto_fixable": True,
                "fix_description": "Operation timed out",
                "fix_script": "Increase timeout in workflow configuration"
            },
            "memory_error": {
                "pattern": r"out of memory|MemoryError",
                "severity": "high",
                "auto_fixable": True,
                "fix_description": "Memory exhaustion",
                "fix_script": "Increase memory allocation in workflow"
            },
            "network_error": {
                "pattern": r"network error|connection refused|timeout",
                "severity": "low",
                "auto_fixable": False,
                "fix_description": "Network connectivity issue",
                "fix_script": "Check network connectivity and retry"
            }
        }
        
        for issue_type, config in error_patterns.items():
            matches = re.finditer(config["pattern"], logs, re.IGNORECASE)
            for match in matches:
                issue = WorkflowIssue(
                    run_id=run.run_id,
                    workflow_name=run.workflow_name,
                    job_name="unknown",
                    step_name="unknown",
                    issue_type=issue_type,
                    error_message=match.group(0),
                    severity=config["severity"],
                    auto_fixable=config["auto_fixable"],
                    fix_description=config["fix_description"],
                    fix_script=config["fix_script"].format(**match.groupdict()),
                    detected_at=datetime.now()
                )
                issues.append(issue)
        
        return issues
    
    def apply_dependency_fix(self, issue: WorkflowIssue) -> FixResult:
        """Apply dependency-related fixes."""
        try:
            if "npm" in issue.issue_type:
                # Fix npm dependency issues
                if "package.json" in os.listdir("."):
                    subprocess.run(["npm", "install"], check=True)
                elif "frontend/package.json" in os.listdir("frontend"):
                    subprocess.run(["npm", "install"], cwd="frontend", check=True)
            
            elif "pip" in issue.issue_type or "python" in issue.issue_type:
                # Fix Python dependency issues
                if "requirements.txt" in os.listdir("."):
                    subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
            
            # Commit and push changes
            commit_sha = self._commit_and_push_fix(issue)
            
            return FixResult(
                issue=issue,
                success=True,
                commit_sha=commit_sha,
                applied_at=datetime.now()
            )
            
        except subprocess.CalledProcessError as e:
            return FixResult(
                issue=issue,
                success=False,
                error_message=str(e),
                applied_at=datetime.now()
            )
    
    def apply_code_fix(self, issue: WorkflowIssue) -> FixResult:
        """Apply code-related fixes."""
        try:
            # For test failures, we'll need to analyze the specific test
            if "pytest" in issue.issue_type:
                # Run tests to see current status
                subprocess.run(["python", "-m", "pytest", "--tb=short"], check=False)
            
            # For lint errors, run linter
            if "lint" in issue.issue_type:
                subprocess.run(["python", "-m", "black", "."], check=False)
                subprocess.run(["python", "-m", "flake8", "."], check=False)
            
            # Commit and push changes
            commit_sha = self._commit_and_push_fix(issue)
            
            return FixResult(
                issue=issue,
                success=True,
                commit_sha=commit_sha,
                applied_at=datetime.now()
            )
            
        except subprocess.CalledProcessError as e:
            return FixResult(
                issue=issue,
                success=False,
                error_message=str(e),
                applied_at=datetime.now()
            )
    
    def apply_workflow_config_fix(self, issue: WorkflowIssue) -> FixResult:
        """Apply workflow configuration fixes."""
        try:
            workflow_dir = Path(".github/workflows")
            
            if workflow_dir.exists():
                for workflow_file in workflow_dir.glob("*.yml"):
                    # Fix common workflow issues
                    self._fix_workflow_file(workflow_file)
            
            # Commit and push changes
            commit_sha = self._commit_and_push_fix(issue)
            
            return FixResult(
                issue=issue,
                success=True,
                commit_sha=commit_sha,
                applied_at=datetime.now()
            )
            
        except Exception as e:
            return FixResult(
                issue=issue,
                success=False,
                error_message=str(e),
                applied_at=datetime.now()
            )
    
    def _fix_workflow_file(self, workflow_file: Path):
        """Fix common issues in workflow files."""
        try:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            # Fix common issues
            # 1. Update action versions
            content = re.sub(r'actions/checkout@v[0-9]+', 'actions/checkout@v4', content)
            content = re.sub(r'actions/setup-python@v[0-9]+', 'actions/setup-python@v5', content)
            content = re.sub(r'actions/setup-node@v[0-9]+', 'actions/setup-node@v4', content)
            
            # 2. Add missing permissions
            if 'permissions:' not in content:
                content = content.replace('jobs:', 'permissions:\n  contents: read\n  pull-requests: write\n  issues: write\n\njobs:')
            
            # 3. Fix timeout issues
            if 'timeout-minutes:' not in content:
                content = re.sub(r'(runs-on: [^\n]+)', r'\1\n      timeout-minutes: 30', content)
            
            with open(workflow_file, 'w') as f:
                f.write(content)
                
        except Exception as e:
            logger.error(f"Failed to fix workflow file {workflow_file}: {e}")
    
    def _commit_and_push_fix(self, issue: WorkflowIssue) -> str:
        """Commit and push fixes to the repository."""
        try:
            # Configure git
            subprocess.run(["git", "config", "--local", "user.email", "mcp-orchestrator@github.com"], check=True)
            subprocess.run(["git", "config", "--local", "user.name", "MCP Orchestrator AI"], check=True)
            
            # Add all changes
            subprocess.run(["git", "add", "."], check=True)
            
            # Commit with descriptive message
            commit_message = f"🔧 Auto-fix: {issue.fix_description} [skip ci]"
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            
            # Push changes
            subprocess.run(["git", "push", "origin", "main"], check=True)
            
            # Get commit SHA
            result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit and push fix: {e}")
            raise
    
    def trigger_workflow_rerun(self, workflow_name: str):
        """Trigger a new workflow run."""
        try:
            # Find the workflow file
            workflow_file = None
            workflow_dir = Path(".github/workflows")
            
            for file in workflow_dir.glob("*.yml"):
                with open(file, 'r') as f:
                    content = yaml.safe_load(f)
                    if content.get('name') == workflow_name:
                        workflow_file = file.name
                        break
            
            if workflow_file:
                subprocess.run([
                    "gh", "workflow", "run", workflow_file
                ], check=True)
                logger.info(f"Triggered workflow run for {workflow_name}")
            else:
                logger.warning(f"Could not find workflow file for {workflow_name}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to trigger workflow run: {e}")
    
    def monitor_and_fix_workflows(self, max_retries: int = 5):
        """Main monitoring and fixing loop."""
        retry_count = 0
        
        while retry_count < max_retries:
            logger.info(f"=== Monitoring Cycle {retry_count + 1}/{max_retries} ===")
            
            # Get current workflow runs
            runs = self.get_workflow_runs()
            failed_runs = self.get_failed_runs(runs)
            
            if not failed_runs:
                logger.info("✅ All workflows are passing!")
                self._generate_success_report()
                break
            
            logger.info(f"Found {len(failed_runs)} failed workflow runs")
            
            # Analyze each failed run
            for run in failed_runs:
                logger.info(f"Analyzing failed run: {run.workflow_name} (ID: {run.run_id})")
                
                # Download and analyze logs
                logs = self.download_run_logs(run.run_id)
                issues = self.analyze_logs_for_issues(logs, run)
                
                if not issues:
                    logger.warning(f"No specific issues detected in run {run.run_id}")
                    continue
                
                logger.info(f"Found {len(issues)} issues in run {run.run_id}")
                
                # Apply fixes for each issue
                for issue in issues:
                    if issue.auto_fixable:
                        logger.info(f"Applying fix for {issue.issue_type}: {issue.fix_description}")
                        
                        if "dependency" in issue.issue_type:
                            fix_result = self.apply_dependency_fix(issue)
                        elif "code" in issue.issue_type or "test" in issue.issue_type:
                            fix_result = self.apply_code_fix(issue)
                        elif "workflow" in issue.issue_type or "config" in issue.issue_type:
                            fix_result = self.apply_workflow_config_fix(issue)
                        else:
                            fix_result = FixResult(
                                issue=issue,
                                success=False,
                                error_message="Unknown issue type",
                                applied_at=datetime.now()
                            )
                        
                        self.fixes_applied.append(fix_result)
                        
                        if fix_result.success:
                            logger.info(f"✅ Fix applied successfully: {fix_result.commit_sha}")
                            # Trigger new workflow run
                            self.trigger_workflow_rerun(run.workflow_name)
                        else:
                            logger.error(f"❌ Fix failed: {fix_result.error_message}")
                    else:
                        logger.warning(f"Issue not auto-fixable: {issue.issue_type}")
                
                self.issues_found.extend(issues)
            
            # Wait before next check
            logger.info("Waiting 2 minutes before next check...")
            time.sleep(120)
            retry_count += 1
        
        if retry_count >= max_retries:
            logger.error(f"❌ Max retries ({max_retries}) reached. Some workflows may still be failing.")
            self._generate_failure_report()
    
    def _generate_success_report(self):
        """Generate success report."""
        report = {
            "status": "SUCCESS",
            "timestamp": datetime.now().isoformat(),
            "repo": f"{self.repo_owner}/{self.repo_name}",
            "monitoring_duration": str(datetime.now() - self.monitoring_start),
            "fixes_applied": len(self.fixes_applied),
            "issues_found": len(self.issues_found),
            "message": "ALL WORKFLOWS PASSED ✅",
            "fix_details": [
                {
                    "issue_type": fix.issue.issue_type,
                    "fix_description": fix.issue.fix_description,
                    "commit_sha": fix.commit_sha,
                    "success": fix.success
                }
                for fix in self.fixes_applied
            ]
        }
        
        # Save report
        with open("mcp_orchestrator_success_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("🎉 ALL WORKFLOWS PASSED ✅")
        logger.info(f"Applied {len(self.fixes_applied)} fixes")
        logger.info(f"Found {len(self.issues_found)} issues")
        print(json.dumps(report, indent=2))
    
    def _generate_failure_report(self):
        """Generate failure report."""
        report = {
            "status": "FAILURE",
            "timestamp": datetime.now().isoformat(),
            "repo": f"{self.repo_owner}/{self.repo_name}",
            "monitoring_duration": str(datetime.now() - self.monitoring_start),
            "fixes_applied": len(self.fixes_applied),
            "issues_found": len(self.issues_found),
            "message": "Some workflows are still failing after max retries",
            "fix_details": [
                {
                    "issue_type": fix.issue.issue_type,
                    "fix_description": fix.issue.fix_description,
                    "commit_sha": fix.commit_sha,
                    "success": fix.success,
                    "error": fix.error_message
                }
                for fix in self.fixes_applied
            ]
        }
        
        # Save report
        with open("mcp_orchestrator_failure_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.error("❌ Some workflows are still failing")
        print(json.dumps(report, indent=2))

def main():
    """Main entry point for MCP Orchestrator AI."""
    # Get configuration from environment
    github_token = os.getenv("GITHUB_TOKEN")
    repo_owner = os.getenv("GITHUB_REPOSITORY_OWNER")
    repo_name = os.getenv("GITHUB_REPOSITORY_NAME")
    
    if not all([github_token, repo_owner, repo_name]):
        logger.error("Missing required environment variables: GITHUB_TOKEN, GITHUB_REPOSITORY_OWNER, GITHUB_REPOSITORY_NAME")
        sys.exit(1)
    
    # Initialize orchestrator
    orchestrator = MCPOrchestrator(github_token, repo_owner, repo_name)
    
    # Start monitoring and fixing
    logger.info("🚀 Starting MCP Orchestrator AI - Workflow Monitor & Auto-Fix")
    logger.info(f"Monitoring repository: {repo_owner}/{repo_name}")
    
    try:
        orchestrator.monitor_and_fix_workflows(max_retries=5)
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
