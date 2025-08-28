#!/usr/bin/env python3
"""
SmartCloudOps AI - Workflow Monitor & Auto-Fix System
====================================================

Comprehensive workflow monitoring and automated issue resolution system.
Monitors GitHub Actions workflows, detects failures, and automatically fixes common issues.

Features:
- Real-time workflow status monitoring
- Automatic issue detection and classification
- Auto-fix capabilities for common problems
- Detailed reporting and analytics
- Integration with GitHub API
"""

import json
import os
import sys
import time
import logging
import requests
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workflow_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class WorkflowIssue:
    """Represents a workflow issue with details and fix information."""
    workflow_name: str
    job_name: str
    step_name: str
    issue_type: str
    error_message: str
    severity: str  # critical, high, medium, low
    auto_fixable: bool
    fix_description: str
    fix_script: str
    detected_at: datetime
    status: str = "open"  # open, fixing, fixed, failed

@dataclass
class WorkflowStatus:
    """Represents the status of a workflow run."""
    workflow_id: str
    workflow_name: str
    run_id: str
    status: str  # completed, in_progress, failed, cancelled
    conclusion: str  # success, failure, cancelled, skipped
    created_at: datetime
    updated_at: datetime
    jobs: List[Dict]
    issues: List[WorkflowIssue]

class WorkflowMonitor:
    """Main workflow monitoring and auto-fix system."""
    
    def __init__(self, github_token: str, repo_owner: str, repo_name: str):
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.issues_found = []
        self.fixes_applied = []
        
    def get_workflow_runs(self, limit: int = 10) -> List[Dict]:
        """Get recent workflow runs from GitHub API."""
        try:
            url = f"{self.base_url}/actions/runs"
            params = {"per_page": limit}
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()["workflow_runs"]
        except Exception as e:
            logger.error(f"Failed to get workflow runs: {e}")
            return []
    
    def get_workflow_run_details(self, run_id: str) -> Optional[Dict]:
        """Get detailed information about a specific workflow run."""
        try:
            url = f"{self.base_url}/actions/runs/{run_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get workflow run details for {run_id}: {e}")
            return None
    
    def get_job_logs(self, run_id: str, job_id: str) -> str:
        """Get logs for a specific job."""
        try:
            url = f"{self.base_url}/actions/runs/{run_id}/jobs/{job_id}/logs"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to get job logs for {job_id}: {e}")
            return ""
    
    def analyze_workflow_logs(self, logs: str) -> List[WorkflowIssue]:
        """Analyze workflow logs to detect issues."""
        issues = []
        
        # Common error patterns and their fixes
        error_patterns = {
            "python_import_error": {
                "pattern": r"ModuleNotFoundError: No module named '([^']+)'",
                "severity": "high",
                "auto_fixable": True,
                "fix_description": "Missing Python dependency",
                "fix_script": "pip install {module}"
            },
            "node_dependency_error": {
                "pattern": r"npm ERR! 404 Not Found - GET https://registry\.npmjs\.org/([^/]+)",
                "severity": "high",
                "auto_fixable": True,
                "fix_description": "Missing npm package",
                "fix_script": "npm install {package}"
            },
            "terraform_error": {
                "pattern": r"Error: ([^\\n]+)",
                "severity": "medium",
                "auto_fixable": False,
                "fix_description": "Terraform configuration error",
                "fix_script": "terraform validate"
            },
            "docker_build_error": {
                "pattern": r"failed to build: ([^\\n]+)",
                "severity": "high",
                "auto_fixable": True,
                "fix_description": "Docker build failure",
                "fix_script": "docker system prune -f && docker build --no-cache ."
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
                    workflow_name="unknown",
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
    
    def check_workflow_files(self) -> List[WorkflowIssue]:
        """Check workflow YAML files for common issues."""
        issues = []
        workflow_dir = Path(".github/workflows")
        
        if not workflow_dir.exists():
            issue = WorkflowIssue(
                workflow_name="system",
                job_name="workflow_check",
                step_name="file_check",
                issue_type="missing_workflow_dir",
                error_message="No .github/workflows directory found",
                severity="critical",
                auto_fixable=True,
                fix_description="Create workflows directory",
                fix_script="mkdir -p .github/workflows",
                detected_at=datetime.now()
            )
            issues.append(issue)
            return issues
        
        for workflow_file in workflow_dir.glob("*.yml"):
            try:
                with open(workflow_file, 'r') as f:
                    workflow_content = yaml.safe_load(f)
                
                # Check for common issues
                issues.extend(self._analyze_workflow_yaml(workflow_file, workflow_content))
                
            except yaml.YAMLError as e:
                issue = WorkflowIssue(
                    workflow_name=str(workflow_file),
                    job_name="yaml_parsing",
                    step_name="parse",
                    issue_type="yaml_syntax_error",
                    error_message=str(e),
                    severity="critical",
                    auto_fixable=False,
                    fix_description="YAML syntax error in workflow file",
                    fix_script="Fix YAML syntax manually",
                    detected_at=datetime.now()
                )
                issues.append(issue)
        
        return issues
    
    def _analyze_workflow_yaml(self, file_path: Path, content: Dict) -> List[WorkflowIssue]:
        """Analyze workflow YAML content for issues."""
        issues = []
        
        # Check for missing required fields
        if "name" not in content:
            issue = WorkflowIssue(
                workflow_name=str(file_path),
                job_name="yaml_validation",
                step_name="name_check",
                issue_type="missing_workflow_name",
                error_message="Workflow missing 'name' field",
                severity="high",
                auto_fixable=True,
                fix_description="Add workflow name",
                fix_script=f"Add 'name: {file_path.stem}' to {file_path}",
                detected_at=datetime.now()
            )
            issues.append(issue)
        
        # Check for missing jobs
        if "jobs" not in content or not content["jobs"]:
            issue = WorkflowIssue(
                workflow_name=str(file_path),
                job_name="yaml_validation",
                step_name="jobs_check",
                issue_type="missing_jobs",
                error_message="Workflow missing 'jobs' section",
                severity="critical",
                auto_fixable=False,
                fix_description="Add jobs section to workflow",
                fix_script="Add jobs section manually",
                detected_at=datetime.now()
            )
            issues.append(issue)
        
        # Check for deprecated actions
        deprecated_actions = [
            "actions/checkout@v1",
            "actions/checkout@v2",
            "actions/setup-python@v1",
            "actions/setup-python@v2",
            "actions/setup-node@v1",
            "actions/setup-node@v2"
        ]
        
        workflow_str = yaml.dump(content)
        for deprecated_action in deprecated_actions:
            if deprecated_action in workflow_str:
                issue = WorkflowIssue(
                    workflow_name=str(file_path),
                    job_name="yaml_validation",
                    step_name="deprecated_actions",
                    issue_type="deprecated_action",
                    error_message=f"Using deprecated action: {deprecated_action}",
                    severity="medium",
                    auto_fixable=True,
                    fix_description=f"Update deprecated action {deprecated_action}",
                    fix_script=f"Replace {deprecated_action} with latest version",
                    detected_at=datetime.now()
                )
                issues.append(issue)
        
        return issues
    
    def auto_fix_issues(self, issues: List[WorkflowIssue]) -> List[WorkflowIssue]:
        """Automatically fix issues that can be resolved."""
        fixed_issues = []
        
        for issue in issues:
            if not issue.auto_fixable:
                continue
            
            logger.info(f"Attempting to auto-fix: {issue.issue_type}")
            issue.status = "fixing"
            
            try:
                if issue.issue_type == "missing_workflow_dir":
                    os.makedirs(".github/workflows", exist_ok=True)
                    issue.status = "fixed"
                    fixed_issues.append(issue)
                
                elif issue.issue_type == "python_import_error":
                    # Extract module name and install it
                    module_match = re.search(r"No module named '([^']+)'", issue.error_message)
                    if module_match:
                        module = module_match.group(1)
                        subprocess.run(["pip", "install", module], check=True)
                        issue.status = "fixed"
                        fixed_issues.append(issue)
                
                elif issue.issue_type == "node_dependency_error":
                    # Extract package name and install it
                    package_match = re.search(r"registry\.npmjs\.org/([^/]+)", issue.error_message)
                    if package_match:
                        package = package_match.group(1)
                        subprocess.run(["npm", "install", package], check=True)
                        issue.status = "fixed"
                        fixed_issues.append(issue)
                
                elif issue.issue_type == "docker_build_error":
                    # Clean Docker and rebuild
                    subprocess.run(["docker", "system", "prune", "-f"], check=True)
                    subprocess.run(["docker", "build", "--no-cache", "."], check=True)
                    issue.status = "fixed"
                    fixed_issues.append(issue)
                
                elif issue.issue_type == "deprecated_action":
                    # Update deprecated actions in workflow files
                    self._update_deprecated_actions()
                    issue.status = "fixed"
                    fixed_issues.append(issue)
                
            except Exception as e:
                logger.error(f"Failed to auto-fix {issue.issue_type}: {e}")
                issue.status = "failed"
        
        return fixed_issues
    
    def _update_deprecated_actions(self):
        """Update deprecated GitHub Actions to latest versions."""
        workflow_dir = Path(".github/workflows")
        
        for workflow_file in workflow_dir.glob("*.yml"):
            try:
                with open(workflow_file, 'r') as f:
                    content = f.read()
                
                # Update deprecated actions
                content = content.replace("actions/checkout@v1", "actions/checkout@v4")
                content = content.replace("actions/checkout@v2", "actions/checkout@v4")
                content = content.replace("actions/setup-python@v1", "actions/setup-python@v5")
                content = content.replace("actions/setup-python@v2", "actions/setup-python@v5")
                content = content.replace("actions/setup-node@v1", "actions/setup-node@v4")
                content = content.replace("actions/setup-node@v2", "actions/setup-node@v4")
                
                with open(workflow_file, 'w') as f:
                    f.write(content)
                
                logger.info(f"Updated deprecated actions in {workflow_file}")
                
            except Exception as e:
                logger.error(f"Failed to update {workflow_file}: {e}")
    
    def generate_report(self) -> Dict:
        """Generate a comprehensive workflow monitoring report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_issues": len(self.issues_found),
            "fixed_issues": len(self.fixes_applied),
            "open_issues": len([i for i in self.issues_found if i.status == "open"]),
            "issues_by_severity": {},
            "issues_by_type": {},
            "fixes_applied": [asdict(issue) for issue in self.fixes_applied],
            "recommendations": []
        }
        
        # Group issues by severity
        for issue in self.issues_found:
            report["issues_by_severity"][issue.severity] = report["issues_by_severity"].get(issue.severity, 0) + 1
            report["issues_by_type"][issue.issue_type] = report["issues_by_type"].get(issue.issue_type, 0) + 1
        
        # Generate recommendations
        if report["issues_by_severity"].get("critical", 0) > 0:
            report["recommendations"].append("Address critical issues immediately")
        
        if report["issues_by_severity"].get("high", 0) > 0:
            report["recommendations"].append("Fix high severity issues before next deployment")
        
        if report["open_issues"] > 0:
            report["recommendations"].append(f"Review and fix {report['open_issues']} remaining issues")
        
        return report
    
    def run_monitoring_cycle(self) -> Dict:
        """Run a complete monitoring cycle."""
        logger.info("Starting workflow monitoring cycle...")
        
        # Check workflow files
        file_issues = self.check_workflow_files()
        self.issues_found.extend(file_issues)
        
        # Get recent workflow runs
        workflow_runs = self.get_workflow_runs(limit=5)
        
        for run in workflow_runs:
            if run["conclusion"] == "failure":
                # Get detailed run information
                run_details = self.get_workflow_run_details(run["id"])
                if run_details:
                    # Analyze each job
                    for job in run_details.get("jobs", []):
                        if job["conclusion"] == "failure":
                            # Get job logs
                            logs = self.get_job_logs(run["id"], job["id"])
                            job_issues = self.analyze_workflow_logs(logs)
                            
                            # Update issue details
                            for issue in job_issues:
                                issue.workflow_name = run["name"]
                                issue.job_name = job["name"]
                            
                            self.issues_found.extend(job_issues)
        
        # Auto-fix issues
        self.fixes_applied = self.auto_fix_issues(self.issues_found)
        
        # Generate report
        report = self.generate_report()
        
        logger.info(f"Monitoring cycle completed. Found {len(self.issues_found)} issues, fixed {len(self.fixes_applied)}")
        
        return report

def main():
    """Main entry point for the workflow monitor."""
    # Get configuration from environment
    github_token = os.getenv("GITHUB_TOKEN")
    repo_owner = os.getenv("GITHUB_REPOSITORY_OWNER", "your-username")
    repo_name = os.getenv("GITHUB_REPOSITORY_NAME", "smartcloudops-ai")
    
    if not github_token:
        logger.error("GITHUB_TOKEN environment variable is required")
        sys.exit(1)
    
    # Initialize monitor
    monitor = WorkflowMonitor(github_token, repo_owner, repo_name)
    
    # Run monitoring cycle
    report = monitor.run_monitoring_cycle()
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"workflow_monitor_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Report saved to {report_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("🔍 WORKFLOW MONITORING REPORT")
    print("="*60)
    print(f"📅 Timestamp: {report['timestamp']}")
    print(f"🚨 Total Issues: {report['total_issues']}")
    print(f"✅ Fixed Issues: {report['fixed_issues']}")
    print(f"⏳ Open Issues: {report['open_issues']}")
    print("\n📊 Issues by Severity:")
    for severity, count in report['issues_by_severity'].items():
        print(f"   {severity.upper()}: {count}")
    print("\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"   • {rec}")
    print("="*60)

if __name__ == "__main__":
    main()