#!/usr/bin/env python3
"""
Simple GitHub Workflow Monitor
=============================

A simplified workflow monitor that works with publicly available GitHub API data.
"""

import sys
import time
import requests
import subprocess


from pathlib import Path


# Configuration
REPO_OWNER = "Dileepreddy93"
REPO_NAME = "smartcloudops-ai"
GITHUB_API_BASE = "https://api.github.com"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SimpleWorkflowMonitor:
    """Simple workflow monitor with basic auto-fixing capabilities."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "SmartCloudOps-Workflow-Monitor/1.0",
                "Accept": "application/vnd.github.v3+json",
            }
        )
        self.fixes_applied = []

    def get_workflow_runs(self, per_page=5):
        """Get recent workflow runs."""
        url = f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
        params = {"per_page": per_page}

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()["workflow_runs"]
        except requests.RequestException as e:
            print(f"❌ Error fetching workflow runs: {e}")
            return []

    def get_workflow_jobs(self, run_id):
        """Get jobs for a specific workflow run."""
        url = f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}/jobs"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()["jobs"]
        except requests.RequestException as e:
            print(f"❌ Error fetching jobs for run {run_id}: {e}")
            return []

    def check_local_issues(self):
        """Check for common local issues that might cause workflow failures."""
        issues = []

        print("🔍 Checking for common local issues...")

        # Check Black formatting
        try:
            result = subprocess.run(
                ["black", "--check", "--diff", "app/", "scripts/", "tests/"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode != 0:
                issues.append(
                    {
                        "type": "black_formatting",
                        "description": "Code formatting issues detected",
                        "fix": "run_black_formatting",
                    }
                )
                print("❌ Black formatting issues found")
            else:
                print("✅ Black formatting is correct")
        except Exception as e:
            print(f"⚠️ Could not check Black formatting: {e}")

        # Check Ruff linting
        try:
            result = subprocess.run(
                ["ruff", "check", "app/", "scripts/", "tests/"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode != 0:
                issues.append(
                    {
                        "type": "ruff_linting",
                        "description": "Linting errors detected",
                        "fix": "run_ruff_fixes",
                    }
                )
                print("❌ Ruff linting issues found")
            else:
                print("✅ Ruff linting is correct")
        except Exception as e:
            print(f"⚠️ Could not check Ruff linting: {e}")

        # Check MyPy type checking
        try:
            result = subprocess.run(
                ["mypy", "app/", "scripts/", "tests/"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode != 0:
                issues.append(
                    {
                        "type": "mypy_errors",
                        "description": "Type checking errors detected",
                        "fix": "run_mypy_fixes",
                    }
                )
                print("❌ MyPy type checking issues found")
            else:
                print("✅ MyPy type checking is correct")
        except Exception as e:
            print(f"⚠️ Could not check MyPy: {e}")

        # Check Bandit security
        try:
            result = subprocess.run(
                ["bandit", "-r", "app/", "-f", "json", "--severity-level", "high"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode != 0:
                issues.append(
                    {
                        "type": "bandit_security",
                        "description": "Security issues detected",
                        "fix": "run_bandit_fixes",
                    }
                )
                print("❌ Bandit security issues found")
            else:
                print("✅ No high-severity security issues found")
        except Exception as e:
            print(f"⚠️ Could not check Bandit: {e}")

        # Check pytest
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode != 0:
                issues.append(
                    {
                        "type": "test_failures",
                        "description": "Test failures detected",
                        "fix": "run_test_fixes",
                    }
                )
                print("❌ Test failures found")
            else:
                print("✅ All tests passing")
        except Exception as e:
            print(f"⚠️ Could not run tests: {e}")

        return issues

    def run_black_formatting(self):
        """Fix Black formatting issues."""
        try:
            print("🔧 Running Black formatting fixes...")
            result = subprocess.run(
                ["black", "app/", "scripts/", "tests/"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                print("✅ Black formatting applied successfully")
                return True
            else:
                print(f"❌ Black formatting failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error running Black: {e}")
            return False

    def run_ruff_fixes(self):
        """Fix Ruff linting issues."""
        try:
            print("🔧 Running Ruff auto-fixes...")
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
                print("✅ Ruff fixes applied successfully")
                return True
            else:
                print(f"❌ Ruff fixes failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error running Ruff: {e}")
            return False

    def run_mypy_fixes(self):
        """Fix MyPy type checking issues."""
        try:
            print("🔧 Installing MyPy dependencies...")
            result = subprocess.run(
                ["pip", "install", "types-requests", "types-PyYAML"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                print("✅ MyPy dependencies installed")
                return True
            else:
                print(f"❌ MyPy dependency installation failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error running MyPy fixes: {e}")
            return False

    def run_bandit_fixes(self):
        """Fix Bandit security issues."""
        try:
            print("🔧 Checking Bandit security issues...")
            result = subprocess.run(
                ["bandit", "-r", "app/", "-f", "json", "--severity-level", "high"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                print("✅ No high-severity security issues found")
                return True
            else:
                print("⚠️ High-severity security issues found - manual review needed")
                return False
        except Exception as e:
            print(f"❌ Error running Bandit: {e}")
            return False

    def run_test_fixes(self):
        """Fix test failures."""
        try:
            print("🔧 Running tests to identify issues...")
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                print("✅ All tests passing")
                return True
            else:
                print(f"❌ Tests still failing: {result.stdout}")
                return False
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False

    def commit_and_push_fixes(self):
        """Commit and push fixes."""
        try:
            print("🔧 Committing and pushing fixes...")

            # Add all changes
            result = subprocess.run(["git", "add", "."], capture_output=True, text=True, cwd=PROJECT_ROOT)

            if result.returncode != 0:
                print(f"❌ Git add failed: {result.stderr}")
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
                print(f"❌ Git commit failed: {result.stderr}")
                return False

            # Push changes
            result = subprocess.run(
                ["git", "push", "origin", "main"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode == 0:
                print("✅ Fixes committed and pushed successfully")
                return True
            else:
                print(f"❌ Git push failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error committing fixes: {e}")
            return False

    def monitor_and_fix(self):
        """Main monitoring and fixing function."""
        print("🚀 Starting simple workflow monitoring and fixing...")
        print("=" * 60)

        # Check current workflow status
        print("📊 Checking current workflow status...")
        runs = self.get_workflow_runs(3)

        if runs:
            print(f"📊 Found {len(runs)} recent workflow runs:")
            for run in runs:
                status = (
                    "✅ SUCCESS"
                    if run["conclusion"] == "success"
                    else "❌ FAILED" if run["conclusion"] == "failure" else "🔄 RUNNING"
                )
                print(f"   • {run['name']}: {status}")

        # Check for local issues
        print("\n🔍 Checking for local issues that might cause failures...")
        issues = self.check_local_issues()

        if issues:
            print(f"\n❌ Found {len(issues)} local issue(s) to fix:")
            for issue in issues:
                print(f"   • {issue['description']}")

            print("\n🔧 Applying fixes...")
            fixes_needed = False

            for issue in issues:
                print(f"\n🔧 Fixing: {issue['description']}")
                fix_method = getattr(self, issue["fix"])
                if fix_method():
                    self.fixes_applied.append(issue["type"])
                    fixes_needed = True
                else:
                    print(f"❌ Failed to fix: {issue['description']}")

            if fixes_needed:
                print("\n🔧 Committing fixes...")
                if self.commit_and_push_fixes():
                    print("✅ Fixes applied successfully!")
                    print("🔄 A new workflow run should start automatically...")
                else:
                    print("❌ Failed to commit fixes")
            else:
                print("❌ No fixes were successfully applied")
        else:
            print("✅ No local issues found!")
            print("💡 If workflows are still failing, the issue might be:")
            print("   • Environment-specific (GitHub Actions vs local)")
            print("   • Dependency version mismatches")
            print("   • Configuration differences")
            print("   • Network or API issues")

        # Generate summary
        print("\n" + "=" * 60)
        print("📊 MONITORING SUMMARY")
        print("=" * 60)
        print(f"✅ Fixes Applied: {len(self.fixes_applied)}")
        print(f"❌ Issues Found: {len(issues)}")

        if self.fixes_applied:
            print("\n🔧 Fixes Applied:")
            for fix in self.fixes_applied:
                print(f"   • {fix}")

        print("\n💡 Next steps:")
        print("   • Wait for new workflow run to complete")
        print("   • Check status: ./scripts/quick_status.sh")
        print("   • Monitor continuously: python scripts/simple_workflow_monitor.py monitor")


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        # Continuous monitoring mode
        monitor = SimpleWorkflowMonitor()
        while True:
            try:
                monitor.monitor_and_fix()
                print("\n🔄 Waiting 5 minutes before next check...")
                time.sleep(300)
            except KeyboardInterrupt:
                print("\n⏹️ Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(60)
    else:
        # Single run mode
        monitor = SimpleWorkflowMonitor()
        monitor.monitor_and_fix()


if __name__ == "__main__":
    main()
