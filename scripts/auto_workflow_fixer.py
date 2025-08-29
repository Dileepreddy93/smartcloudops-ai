#!/usr/bin/env python3
"""
SmartCloudOps AI - Automated Workflow Fixer
==========================================

Automated system to detect and fix common GitHub Actions workflow issues.
This script analyzes workflow files and automatically applies fixes for common problems.

Features:
- Automatic workflow file analysis
- Common issue detection and fixing
- Dependency management
- Configuration validation
- Auto-commit and push fixes
"""

import os
import sys
import json
import yaml
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workflow_fixer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WorkflowFixer:
    """Automated workflow issue detection and fixing system."""
    
    def __init__(self):
        self.workflow_dir = Path(".github/workflows")
        self.fixes_applied = []
        self.issues_found = []
        
    def analyze_workflows(self) -> List[Dict]:
        """Analyze all workflow files for issues."""
        issues = []
        
        if not self.workflow_dir.exists():
            logger.error("No .github/workflows directory found")
            return issues
        
        for workflow_file in self.workflow_dir.glob("*.yml"):
            logger.info(f"Analyzing {workflow_file}")
            file_issues = self._analyze_workflow_file(workflow_file)
            issues.extend(file_issues)
        
        return issues
    
    def _analyze_workflow_file(self, file_path: Path) -> List[Dict]:
        """Analyze a single workflow file for issues."""
        issues = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                workflow = yaml.safe_load(content)
            
            # Check for common issues
            issues.extend(self._check_missing_fields(file_path, workflow))
            issues.extend(self._check_deprecated_actions(file_path, content))
            issues.extend(self._check_security_issues(file_path, workflow))
            issues.extend(self._check_performance_issues(file_path, workflow))
            issues.extend(self._check_dependency_issues(file_path, workflow))
            
        except yaml.YAMLError as e:
            issues.append({
                "file": str(file_path),
                "type": "yaml_syntax_error",
                "severity": "critical",
                "message": f"YAML syntax error: {e}",
                "fixable": False
            })
        except Exception as e:
            issues.append({
                "file": str(file_path),
                "type": "parsing_error",
                "severity": "high",
                "message": f"Error parsing file: {e}",
                "fixable": False
            })
        
        return issues
    
    def _check_missing_fields(self, file_path: Path, workflow: Dict) -> List[Dict]:
        """Check for missing required fields."""
        issues = []
        
        if "name" not in workflow:
            issues.append({
                "file": str(file_path),
                "type": "missing_name",
                "severity": "high",
                "message": "Workflow missing 'name' field",
                "fixable": True,
                "fix": lambda: self._add_workflow_name(file_path, workflow)
            })
        
        if "on" not in workflow:
            issues.append({
                "file": str(file_path),
                "type": "missing_triggers",
                "severity": "critical",
                "message": "Workflow missing 'on' triggers",
                "fixable": True,
                "fix": lambda: self._add_default_triggers(file_path, workflow)
            })
        
        if "jobs" not in workflow or not workflow["jobs"]:
            issues.append({
                "file": str(file_path),
                "type": "missing_jobs",
                "severity": "critical",
                "message": "Workflow missing 'jobs' section",
                "fixable": False
            })
        
        return issues
    
    def _check_deprecated_actions(self, file_path: Path, content: str) -> List[Dict]:
        """Check for deprecated GitHub Actions."""
        issues = []
        
        deprecated_actions = {
            "actions/checkout@v1": "actions/checkout@v4",
            "actions/checkout@v2": "actions/checkout@v4",
            "actions/checkout@v3": "actions/checkout@v4",
            "actions/setup-python@v1": "actions/setup-python@v5",
            "actions/setup-python@v2": "actions/setup-python@v5",
            "actions/setup-python@v3": "actions/setup-python@v5",
            "actions/setup-python@v4": "actions/setup-python@v5",
            "actions/setup-node@v1": "actions/setup-node@v4",
            "actions/setup-node@v2": "actions/setup-node@v4",
            "actions/setup-node@v3": "actions/setup-node@v4",
            "actions/upload-artifact@v1": "actions/upload-artifact@v4",
            "actions/upload-artifact@v2": "actions/upload-artifact@v4",
            "actions/upload-artifact@v3": "actions/upload-artifact@v4",
            "actions/download-artifact@v1": "actions/download-artifact@v4",
            "actions/download-artifact@v2": "actions/download-artifact@v4",
            "actions/download-artifact@v3": "actions/download-artifact@v4"
        }
        
        for old_action, new_action in deprecated_actions.items():
            if old_action in content:
                issues.append({
                    "file": str(file_path),
                    "type": "deprecated_action",
                    "severity": "medium",
                    "message": f"Using deprecated action: {old_action}",
                    "fixable": True,
                    "fix": lambda f=file_path, old=old_action, new=new_action: self._update_action(f, old, new)
                })
        
        return issues
    
    def _check_security_issues(self, file_path: Path, workflow: Dict) -> List[Dict]:
        """Check for security issues in workflows."""
        issues = []
        
        # Check for hardcoded secrets
        workflow_str = yaml.dump(workflow)
        if re.search(r'password.*=.*["\'][^"\']+["\']', workflow_str, re.IGNORECASE):
            issues.append({
                "file": str(file_path),
                "type": "hardcoded_secret",
                "severity": "critical",
                "message": "Hardcoded secrets found in workflow",
                "fixable": False
            })
        
        # Check for missing permissions
        if "permissions" not in workflow:
            issues.append({
                "file": str(file_path),
                "type": "missing_permissions",
                "severity": "medium",
                "message": "Missing explicit permissions configuration",
                "fixable": True,
                "fix": lambda: self._add_default_permissions(file_path, workflow)
            })
        
        return issues
    
    def _check_performance_issues(self, file_path: Path, workflow: Dict) -> List[Dict]:
        """Check for performance issues in workflows."""
        issues = []
        
        # Check for missing caching
        workflow_str = yaml.dump(workflow)
        if "setup-python" in workflow_str and "cache" not in workflow_str:
            issues.append({
                "file": str(file_path),
                "type": "missing_cache",
                "severity": "low",
                "message": "Missing pip cache configuration",
                "fixable": True,
                "fix": lambda: self._add_pip_cache(file_path, workflow)
            })
        
        if "setup-node" in workflow_str and "cache" not in workflow_str:
            issues.append({
                "file": str(file_path),
                "type": "missing_cache",
                "severity": "low",
                "message": "Missing npm cache configuration",
                "fixable": True,
                "fix": lambda: self._add_npm_cache(file_path, workflow)
            })
        
        return issues
    
    def _check_dependency_issues(self, file_path: Path, workflow: Dict) -> List[Dict]:
        """Check for dependency and environment issues."""
        issues = []
        
        # Check for outdated Python version
        workflow_str = yaml.dump(workflow)
        if "python-version" in workflow_str:
            python_versions = re.findall(r'python-version.*["\']([^"\']+)["\']', workflow_str)
            for version in python_versions:
                if version.startswith("3.8") or version.startswith("3.9"):
                    issues.append({
                        "file": str(file_path),
                        "type": "outdated_python",
                        "severity": "medium",
                        "message": f"Using outdated Python version: {version}",
                        "fixable": True,
                        "fix": lambda: self._update_python_version(file_path, version, "3.11")
                    })
        
        # Check for outdated Node.js version
        if "node-version" in workflow_str:
            node_versions = re.findall(r'node-version.*["\']([^"\']+)["\']', workflow_str)
            for version in node_versions:
                if version.startswith("16") or version.startswith("14"):
                    issues.append({
                        "file": str(file_path),
                        "type": "outdated_node",
                        "severity": "medium",
                        "message": f"Using outdated Node.js version: {version}",
                        "fixable": True,
                        "fix": lambda: self._update_node_version(file_path, version, "18")
                    })
        
        return issues
    
    def apply_fixes(self, issues: List[Dict]) -> List[Dict]:
        """Apply fixes for detected issues."""
        applied_fixes = []
        
        for issue in issues:
            if issue.get("fixable", False) and "fix" in issue:
                try:
                    logger.info(f"Applying fix for {issue['type']} in {issue['file']}")
                    issue["fix"]()
                    applied_fixes.append(issue)
                    logger.info(f"✅ Fixed {issue['type']} in {issue['file']}")
                except Exception as e:
                    logger.error(f"Failed to fix {issue['type']}: {e}")
                    issue["fix_error"] = str(e)
        
        return applied_fixes
    
    def _add_workflow_name(self, file_path: Path, workflow: Dict):
        """Add missing workflow name."""
        workflow["name"] = file_path.stem.replace("_", " ").title()
        self._save_workflow(file_path, workflow)
    
    def _add_default_triggers(self, file_path: Path, workflow: Dict):
        """Add default workflow triggers."""
        workflow["on"] = {
            "push": {"branches": ["main", "develop"]},
            "pull_request": {"branches": ["main"]}
        }
        self._save_workflow(file_path, workflow)
    
    def _add_default_permissions(self, file_path: Path, workflow: Dict):
        """Add default permissions configuration."""
        workflow["permissions"] = {
            "contents": "read",
            "pull-requests": "write",
            "issues": "write"
        }
        self._save_workflow(file_path, workflow)
    
    def _add_pip_cache(self, file_path: Path, workflow: Dict):
        """Add pip cache configuration."""
        for job_name, job in workflow["jobs"].items():
            for step in job.get("steps", []):
                if step.get("uses", "").startswith("actions/setup-python"):
                    # Add cache step after setup-python
                    cache_step = {
                        "name": "Cache pip dependencies",
                        "uses": "actions/cache@v4",
                        "with": {
                            "path": "~/.cache/pip",
                            "key": "${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}",
                            "restore-keys": "| ${{ runner.os }}-pip-"
                        }
                    }
                    job["steps"].insert(job["steps"].index(step) + 1, cache_step)
                    break
        
        self._save_workflow(file_path, workflow)
    
    def _add_npm_cache(self, file_path: Path, workflow: Dict):
        """Add npm cache configuration."""
        for job_name, job in workflow["jobs"].items():
            for step in job.get("steps", []):
                if step.get("uses", "").startswith("actions/setup-node"):
                    # Add cache step after setup-node
                    cache_step = {
                        "name": "Cache npm dependencies",
                        "uses": "actions/cache@v4",
                        "with": {
                            "path": "~/.npm",
                            "key": "${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}",
                            "restore-keys": "| ${{ runner.os }}-node-"
                        }
                    }
                    job["steps"].insert(job["steps"].index(step) + 1, cache_step)
                    break
        
        self._save_workflow(file_path, workflow)
    
    def _update_action(self, file_path: Path, old_action: str, new_action: str):
        """Update deprecated action to new version."""
        with open(file_path, 'r') as f:
            content = f.read()
        
        content = content.replace(old_action, new_action)
        
        with open(file_path, 'w') as f:
            f.write(content)
    
    def _update_python_version(self, file_path: Path, old_version: str, new_version: str):
        """Update Python version in workflow."""
        with open(file_path, 'r') as f:
            content = f.read()
        
        content = content.replace(f'python-version: "{old_version}"', f'python-version: "{new_version}"')
        content = content.replace(f"python-version: '{old_version}'", f"python-version: '{new_version}'")
        
        with open(file_path, 'w') as f:
            f.write(content)
    
    def _update_node_version(self, file_path: Path, old_version: str, new_version: str):
        """Update Node.js version in workflow."""
        with open(file_path, 'r') as f:
            content = f.read()
        
        content = content.replace(f'node-version: "{old_version}"', f'node-version: "{new_version}"')
        content = content.replace(f"node-version: '{old_version}'", f"node-version: '{new_version}'")
        
        with open(file_path, 'w') as f:
            f.write(content)
    
    def _save_workflow(self, file_path: Path, workflow: Dict):
        """Save workflow configuration back to file."""
        with open(file_path, 'w') as f:
            yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)
    
    def validate_workflows(self) -> bool:
        """Validate all workflow files after fixes."""
        try:
            for workflow_file in self.workflow_dir.glob("*.yml"):
                with open(workflow_file, 'r') as f:
                    yaml.safe_load(f)
            return True
        except Exception as e:
            logger.error(f"Workflow validation failed: {e}")
            return False
    
    def commit_fixes(self, commit_message: str = None) -> bool:
        """Commit and push the applied fixes."""
        try:
            # Add all workflow files
            subprocess.run(["git", "add", ".github/workflows/"], check=True)
            
            # Check if there are changes to commit
            result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if not result.stdout.strip():
                logger.info("No changes to commit")
                return True
            
            # Commit changes
            if not commit_message:
                commit_message = "fix: auto-fix workflow issues [skip ci]"
            
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            logger.info(f"✅ Committed fixes: {commit_message}")
            
            # Push changes
            subprocess.run(["git", "push"], check=True)
            logger.info("✅ Pushed fixes to remote repository")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git operation failed: {e}")
            return False
    
    def generate_report(self, issues: List[Dict], applied_fixes: List[Dict]) -> Dict:
        """Generate a comprehensive fix report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_issues": len(issues),
            "applied_fixes": len(applied_fixes),
            "remaining_issues": len([i for i in issues if not i.get("fixable", False)]),
            "issues_by_severity": {},
            "issues_by_type": {},
            "applied_fixes_details": applied_fixes,
            "recommendations": []
        }
        
        # Group issues by severity and type
        for issue in issues:
            report["issues_by_severity"][issue["severity"]] = report["issues_by_severity"].get(issue["severity"], 0) + 1
            report["issues_by_type"][issue["type"]] = report["issues_by_type"].get(issue["type"], 0) + 1
        
        # Generate recommendations
        if report["issues_by_severity"].get("critical", 0) > 0:
            report["recommendations"].append("Address critical issues manually")
        
        if report["remaining_issues"] > 0:
            report["recommendations"].append(f"Review {report['remaining_issues']} remaining issues")
        
        if report["applied_fixes"] > 0:
            report["recommendations"].append("Test workflows after applied fixes")
        
        return report

def main():
    """Main entry point for the workflow fixer."""
    logger.info("🔧 Starting automated workflow fixer...")
    
    # Initialize fixer
    fixer = WorkflowFixer()
    
    # Analyze workflows
    logger.info("🔍 Analyzing workflow files...")
    issues = fixer.analyze_workflows()
    
    if not issues:
        logger.info("✅ No issues found in workflows")
        return
    
    # Print found issues
    print(f"\n🚨 Found {len(issues)} issues:")
    for issue in issues:
        print(f"   {issue['severity'].upper()}: {issue['type']} - {issue['message']}")
    
    # Apply fixes
    logger.info("🔧 Applying automatic fixes...")
    applied_fixes = fixer.apply_fixes(issues)
    
    # Validate workflows after fixes
    logger.info("✅ Validating workflows after fixes...")
    if not fixer.validate_workflows():
        logger.error("❌ Workflow validation failed after fixes")
        return
    
    # Generate report
    report = fixer.generate_report(issues, applied_fixes)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"workflow_fix_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*60)
    print("🔧 WORKFLOW FIX REPORT")
    print("="*60)
    print(f"📅 Timestamp: {report['timestamp']}")
    print(f"🚨 Total Issues: {report['total_issues']}")
    print(f"✅ Applied Fixes: {report['applied_fixes']}")
    print(f"⏳ Remaining Issues: {report['remaining_issues']}")
    print("\n📊 Issues by Severity:")
    for severity, count in report['issues_by_severity'].items():
        print(f"   {severity.upper()}: {count}")
    print("\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"   • {rec}")
    print("="*60)
    
    # Ask user if they want to commit fixes
    if applied_fixes:
        response = input("\n🤔 Do you want to commit and push these fixes? (y/N): ")
        if response.lower() in ['y', 'yes']:
            if fixer.commit_fixes():
                logger.info("✅ Fixes committed and pushed successfully")
            else:
                logger.error("❌ Failed to commit fixes")
    
    logger.info(f"📄 Report saved to {report_file}")

if __name__ == "__main__":
    main()
