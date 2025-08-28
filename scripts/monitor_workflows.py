#!/usr/bin/env python3
"""
🔄 SmartCloudOps AI - Continuous Workflow Monitor
=================================================

This script runs continuously in the background to monitor GitHub Actions workflows
and automatically fix issues as they arise. It will:

1. Monitor workflow status every 30 seconds
2. Detect failures and analyze root causes
3. Apply automatic fixes
4. Commit and push fixes
5. Wait for new workflow runs
6. Repeat until all workflows pass

Usage:
    python scripts/monitor_workflows.py [--continuous] [--interval SECONDS]
"""

import argparse
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from auto_workflow_fixer import WorkflowMonitor

# Add the parent directory to the path to import the workflow fixer
sys.path.append(str(Path(__file__).parent.parent))


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("continuous_workflow_monitor.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class ContinuousWorkflowMonitor:
    """Continuous workflow monitoring system"""

    def __init__(self, interval: int = 30):
        self.interval = interval
        self.running = True
        self.monitor = None
        self.stats = {
            "checks": 0,
            "fixes_applied": 0,
            "workflows_fixed": 0,
            "start_time": datetime.now(),
            "last_check": None,
        }

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False

    def initialize_monitor(self):
        """Initialize the workflow monitor"""
        try:
            # Get GitHub token
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                logger.error("❌ GITHUB_TOKEN environment variable not set")
                return False

            # Get repository info
            import subprocess

            result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True)
            remote_url = result.stdout.strip()

            if "github.com" in remote_url:
                parts = remote_url.split("github.com/")[1].split(".git")[0].split("/")
                repo_owner = parts[0]
                repo_name = parts[1]
            else:
                logger.error("❌ Could not parse repository information")
                return False

            self.monitor = WorkflowMonitor(repo_owner, repo_name, token)
            logger.info(f"✅ Initialized monitor for {repo_owner}/{repo_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize monitor: {e}")
            return False

    def check_workflows(self):
        """Check current workflow status"""
        try:
            self.stats["checks"] += 1
            self.stats["last_check"] = datetime.now()

            logger.info(f"🔍 Check #{self.stats['checks']} - Checking workflow status...")

            # Get current workflow runs
            runs = self.monitor.get_workflow_runs()
            if not runs:
                logger.warning("No workflow runs found")
                return True

            # Check for failed runs
            failed_runs = [run for run in runs if run.conclusion == "failure"]

            if not failed_runs:
                logger.info("✅ All workflows are passing!")
                return True

            logger.info(f"❌ Found {len(failed_runs)} failed workflows")

            # Analyze and fix each failed workflow
            for run in failed_runs:
                logger.info(f"🔍 Analyzing failed workflow: {run.name} (ID: {run.run_id})")

                # Get logs
                logs = self.monitor.get_workflow_logs(run.run_id)
                if not logs:
                    continue

                # Analyze failure
                issues = self.monitor.analyze_failure(logs)
                logger.info(f"Identified issues: {issues}")

                # Apply fixes
                fixes_applied = False

                if any("dependency" in issue for issue in issues):
                    fixes_applied |= self.monitor.fix_dependency_issues()

                if any("test" in issue for issue in issues):
                    fixes_applied |= self.monitor.fix_test_issues()

                if any("linting" in issue for issue in issues):
                    fixes_applied |= self.monitor.fix_linting_issues()

                if any("security" in issue for issue in issues):
                    fixes_applied |= self.monitor.fix_security_issues()

                if any("build" in issue for issue in issues):
                    fixes_applied |= self.monitor.fix_build_issues()

                # If no specific issues found, try general fixes
                if not issues:
                    logger.info("No specific issues identified, applying general fixes...")
                    fixes_applied |= self.monitor.fix_dependency_issues()
                    fixes_applied |= self.monitor.fix_test_issues()
                    fixes_applied |= self.monitor.fix_linting_issues()

                # Commit and push fixes if any were applied
                if fixes_applied:
                    self.stats["fixes_applied"] += 1
                    if self.monitor.commit_and_push_fixes():
                        logger.info("🔄 Waiting for new workflow to complete...")
                        self.stats["workflows_fixed"] += 1
                        return False  # Wait longer for new workflow
                    else:
                        logger.error("Failed to commit and push fixes")

            return True

        except Exception as e:
            logger.error(f"❌ Error checking workflows: {e}")
            return True

    def print_stats(self):
        """Print monitoring statistics"""
        runtime = datetime.now() - self.stats["start_time"]
        logger.info("📊 Monitoring Statistics:")
        logger.info(f"   Runtime: {runtime}")
        logger.info(f"   Checks performed: {self.stats['checks']}")
        logger.info(f"   Fixes applied: {self.stats['fixes_applied']}")
        logger.info(f"   Workflows fixed: {self.stats['workflows_fixed']}")
        if self.stats["last_check"]:
            logger.info(f"   Last check: {self.stats['last_check']}")

    def run(self):
        """Main monitoring loop"""
        logger.info("🚀 Starting continuous workflow monitoring...")

        if not self.initialize_monitor():
            logger.error("❌ Failed to initialize monitor")
            return False

        logger.info(f"⏰ Monitoring interval: {self.interval} seconds")
        logger.info("🔄 Press Ctrl+C to stop monitoring")

        try:
            while self.running:
                try:
                    # Check workflows
                    success = self.check_workflows()

                    if success:
                        logger.info(f"✅ All workflows passing - waiting {self.interval} seconds...")
                        time.sleep(self.interval)
                    else:
                        logger.info("🔄 Fixes applied - waiting 60 seconds for new workflow...")
                        time.sleep(60)

                except KeyboardInterrupt:
                    logger.info("🛑 Monitoring stopped by user")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in monitoring loop: {e}")
                    time.sleep(self.interval)

        finally:
            self.print_stats()
            logger.info("🛑 Continuous monitoring stopped")

        return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Continuous Workflow Monitor")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Monitoring interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run in continuous mode (default: single run)",
    )

    args = parser.parse_args()

    if args.continuous:
        # Continuous monitoring mode
        monitor = ContinuousWorkflowMonitor(interval=args.interval)
        monitor.run()
    else:
        # Single run mode
        logger.info("🔄 Running single workflow check...")

        # Get GitHub token
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            logger.error("❌ GITHUB_TOKEN environment variable not set")
            sys.exit(1)

        # Get repository info
        import subprocess

        try:
            result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True)
            remote_url = result.stdout.strip()

            if "github.com" in remote_url:
                parts = remote_url.split("github.com/")[1].split(".git")[0].split("/")
                repo_owner = parts[0]
                repo_name = parts[1]
            else:
                logger.error("❌ Could not parse repository information")
                sys.exit(1)

        except Exception as e:
            logger.error(f"❌ Failed to get repository information: {e}")
            sys.exit(1)

        # Create monitor and run single check
        monitor = WorkflowMonitor(repo_owner, repo_name, token)
        success = monitor.monitor_and_fix()

        if success:
            logger.info("🎉 All workflows are now passing!")
            sys.exit(0)
        else:
            logger.error("❌ Failed to fix all workflows")
            sys.exit(1)


if __name__ == "__main__":
    main()
