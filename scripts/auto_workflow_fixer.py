#!/usr/bin/env python3
"""
Automated GitHub Workflow Monitor & Auto-Fixer
=============================================

Monitors GitHub workflows, detects failures, and automatically fixes common issues.
"""

import requests
import json
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import logging

# Configuration
REPO_OWNER = "Dileepreddy93"
REPO_NAME = "smartcloudops-ai"
GITHUB_API_BASE = "https://api.github.com"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("workflow_monitor.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class WorkflowMonitor:
    """Monitor and auto-fix GitHub workflows."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "SmartCloudOps-Workflow-Monitor/1.0",
                "Accept": "application/vnd.github.v3+json",
            }
        )
        self.fixes_applied = []
        self.issues_found = []

    def get_workflow_runs(self, per_page=5):
        """Get recent workflow runs."""
        url = f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
        params = {"per_page": per_page}

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()["workflow_runs"]
        except requests.RequestException as e:
            logger.error(f"Error fetching workflow runs: {e}")
            return []

    def get_workflow_jobs(self, run_id):
        """Get jobs for a specific workflow run."""
        url = f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}/jobs"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()["jobs"]
        except requests.RequestException as e:
            logger.error(f"Error fetching jobs for run {run_id}: {e}")
            return []

    def get_job_logs(self, run_id, job_id):
        """Get logs for a specific job."""
        url = f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}/jobs/{job_id}/logs"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching logs for job {job_id}: {e}")
            return ""

    def analyze_failure(self, run_id, job_name, logs):
        """Analyze failure and determine fix strategy."""
        issues = []

        # Common failure patterns
        if "Black formatting" in logs or "would reformat" in logs:
            issues.append(
                {
                    "type": "black_formatting",
                    "severity": "medium",
                    "description": "Code formatting issues detected",
                    "fix": "run_black_formatting",
                }
            )

        if "Ruff linting" in logs and "Found" in logs and "errors" in logs:
            issues.append(
                {
                    "type": "ruff_linting",
                    "severity": "medium",
                    "description": "Linting errors detected",
                    "fix": "run_ruff_fixes",
                }
            )

        if "MyPy" in logs and "Found" in logs and "errors" in logs:
            issues.append(
                {
                    "type": "mypy_errors",
                    "severity": "medium",
                    "description": "Type checking errors detected",
                    "fix": "run_mypy_fixes",
                }
            )

        if "Bandit" in logs and "Found" in logs and "issues" in logs:
            issues.append(
                {
                    "type": "bandit_security",
                    "severity": "high",
                    "description": "Security issues detected",
                    "fix": "run_bandit_fixes",
                }
            )

        if "ModuleNotFoundError" in logs or "No module named" in logs:
            issues.append(
                {
                    "type": "missing_dependencies",
                    "severity": "high",
                    "description": "Missing Python dependencies",
                    "fix": "install_missing_deps",
                }
            )

        if "pytest" in logs and "FAILED" in logs:
            issues.append(
                {
                    "type": "test_failures",
                    "severity": "high",
                    "description": "Test failures detected",
                    "fix": "run_test_fixes",
                }
            )

        return issues

    def run_black_formatting(self):
        """Fix Black formatting issues."""
        try:
            logger.info("🔧 Running Black formatting fixes...")
            result = subprocess.run(
                ["black", "app/", "scripts/", "tests/"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                logger.info("✅ Black formatting applied successfully")
                return True
            else:
                logger.error(f"❌ Black formatting failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ Error running Black: {e}")
            return False

    def run_ruff_fixes(self):
        """Fix Ruff linting issues."""
        try:
            logger.info("🔧 Running Ruff auto-fixes...")
            result = subprocess.run(
                [
                    "ruff",
                    "check",
                    "app/",
                    "scripts/",
                    "tests/",
                    "--fix",
                    "--unsafe-fixes",
                ],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                logger.info("✅ Ruff fixes applied successfully")
                return True
            else:
                logger.error(f"❌ Ruff fixes failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ Error running Ruff: {e}")
            return False

    def run_mypy_fixes(self):
        """Fix MyPy type checking issues."""
        try:
            logger.info("🔧 Running MyPy fixes...")
            # Install missing type stubs
            result = subprocess.run(
                ["pip", "install", "types-requests", "types-PyYAML"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                logger.info("✅ MyPy dependencies installed")
                return True
            else:
                logger.error(f"❌ MyPy dependency installation failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ Error running MyPy fixes: {e}")
            return False

    def run_bandit_fixes(self):
        """Fix Bandit security issues."""
        try:
            logger.info("🔧 Running Bandit security fixes...")
            # Check for high-severity issues only
            result = subprocess.run(
                [
                    "bandit",
                    "-r",
                    "app/",
                    "-f",
                    "json",
                    "-o",
                    "bandit-report.json",
                    "--severity-level",
                    "high",
                ],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                logger.info("✅ No high-severity security issues found")
                return True
            else:
                logger.warning(
                    "⚠️ High-severity security issues found - manual review needed"
                )
                return False
        except Exception as e:
            logger.error(f"❌ Error running Bandit: {e}")
            return False

    def install_missing_deps(self):
        """Install missing dependencies."""
        try:
            logger.info("🔧 Installing missing dependencies...")
            result = subprocess.run(
                ["pip", "install", "-r", "app/requirements.txt"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                logger.info("✅ Dependencies installed successfully")
                return True
            else:
                logger.error(f"❌ Dependency installation failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ Error installing dependencies: {e}")
            return False

    def run_test_fixes(self):
        """Fix test failures."""
        try:
            logger.info("🔧 Running test fixes...")
            # Run tests with verbose output to identify issues
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                logger.info("✅ All tests passing")
                return True
            else:
                logger.error(f"❌ Tests still failing: {result.stdout}")
                return False
        except Exception as e:
            logger.error(f"❌ Error running tests: {e}")
            return False

    def commit_and_push_fixes(self):
        """Commit and push fixes."""
        try:
            logger.info("🔧 Committing and pushing fixes...")

            # Add all changes
            result = subprocess.run(
                ["git", "add", "."], capture_output=True, text=True, cwd=PROJECT_ROOT
            )

            if result.returncode != 0:
                logger.error(f"❌ Git add failed: {result.stderr}")
                return False

            # Commit changes
            commit_message = f"🔧 AUTO-FIX: {', '.join(self.fixes_applied)}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode != 0:
                logger.error(f"❌ Git commit failed: {result.stderr}")
                return False

            # Push changes
            result = subprocess.run(
                ["git", "push", "origin", "main"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                logger.info("✅ Fixes committed and pushed successfully")
                return True
            else:
                logger.error(f"❌ Git push failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ Error committing fixes: {e}")
            return False

    def monitor_and_fix(self, max_iterations=3):
        """Main monitoring and fixing loop."""
        logger.info("🚀 Starting automated workflow monitoring and fixing...")

        for iteration in range(max_iterations):
            logger.info(f"📊 Iteration {iteration + 1}/{max_iterations}")

            # Get recent workflow runs
            runs = self.get_workflow_runs(3)
            if not runs:
                logger.warning("⚠️ No workflow runs found")
                time.sleep(60)
                continue

            # Check for failed workflows
            failed_runs = [
                run
                for run in runs
                if run["status"] == "completed" and run["conclusion"] == "failure"
            ]

            if not failed_runs:
                logger.info("✅ No failed workflows found - all good!")
                break

            logger.info(f"❌ Found {len(failed_runs)} failed workflow(s)")

            # Analyze each failed workflow
            fixes_needed = False

            for run in failed_runs:
                logger.info(
                    f"🔍 Analyzing failed workflow: {run['name']} (ID: {run['id']})"
                )

                # Get jobs for this run
                jobs = self.get_workflow_jobs(run["id"])

                for job in jobs:
                    if job["conclusion"] == "failure":
                        logger.info(f"🔍 Analyzing failed job: {job['name']}")

                        # Get job logs
                        logs = self.get_job_logs(run["id"], job["id"])

                        # Analyze failure
                        issues = self.analyze_failure(run["id"], job["name"], logs)

                        if issues:
                            logger.info(f"🔧 Found {len(issues)} issue(s) to fix")

                            for issue in issues:
                                logger.info(f"🔧 Fixing: {issue['description']}")

                                # Apply fix
                                fix_method = getattr(self, issue["fix"])
                                if fix_method():
                                    self.fixes_applied.append(issue["type"])
                                    fixes_needed = True
                                else:
                                    self.issues_found.append(issue)

            if fixes_needed:
                logger.info("🔧 Applying fixes...")

                # Commit and push fixes
                if self.commit_and_push_fixes():
                    logger.info(
                        "✅ Fixes applied successfully - waiting for new workflow run..."
                    )
                    time.sleep(120)  # Wait for new workflow to start
                else:
                    logger.error("❌ Failed to apply fixes")
                    break
            else:
                logger.info(
                    "ℹ️ No automatic fixes available - manual intervention needed"
                )
                break

        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate monitoring report."""
        logger.info("📊 Generating monitoring report...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "fixes_applied": self.fixes_applied,
            "issues_found": [issue["description"] for issue in self.issues_found],
            "summary": {
                "total_fixes": len(self.fixes_applied),
                "total_issues": len(self.issues_found),
                "success_rate": (
                    len(self.fixes_applied)
                    / (len(self.fixes_applied) + len(self.issues_found))
                    if (len(self.fixes_applied) + len(self.issues_found)) > 0
                    else 0
                ),
            },
        }

        # Save report
        with open("workflow_monitor_report.json", "w") as f:
            json.dump(report, f, indent=2)

        logger.info("📊 Report saved to workflow_monitor_report.json")

        # Print summary
        print("\n" + "=" * 60)
        print("📊 WORKFLOW MONITORING REPORT")
        print("=" * 60)
        print(f"✅ Fixes Applied: {len(self.fixes_applied)}")
        print(f"❌ Issues Found: {len(self.issues_found)}")
        print(f"📈 Success Rate: {report['summary']['success_rate']:.1%}")

        if self.fixes_applied:
            print("\n🔧 Fixes Applied:")
            for fix in self.fixes_applied:
                print(f"   • {fix}")

        if self.issues_found:
            print("\n❌ Issues Requiring Manual Attention:")
            for issue in self.issues_found:
                print(f"   • {issue['description']} ({issue['severity']} severity)")


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        # Continuous monitoring mode
        monitor = WorkflowMonitor()
        while True:
            try:
                monitor.monitor_and_fix(max_iterations=1)
                print("🔄 Waiting 5 minutes before next check...")
                time.sleep(300)
            except KeyboardInterrupt:
                print("\n⏹️ Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                time.sleep(60)
    else:
        # Single run mode
        monitor = WorkflowMonitor()
        monitor.monitor_and_fix()


if __name__ == "__main__":
    main()
