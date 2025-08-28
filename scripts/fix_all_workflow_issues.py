#!/usr/bin/env python3
"""
SmartCloudOps AI - Complete Workflow Issue Resolution System
============================================================

This script continuously monitors GitHub Actions workflows and automatically fixes
all issues until all workflows pass successfully. It runs in a loop until all
workflow issues are resolved.

Features:
- Continuous workflow monitoring
- Automatic issue detection and classification
- Multi-stage fix application
- Dependency management
- Test execution and validation
- Automatic commits and pushes
- Comprehensive reporting
- Retry logic with exponential backoff
"""

import os
import sys
import json
import time
import logging
import subprocess
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workflow_fix_complete.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CompleteWorkflowFixer:
    """Complete workflow issue resolution system."""
    
    def __init__(self, github_token: str = None, repo_owner: str = None, repo_name: str = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.repo_owner = repo_owner or os.getenv("GITHUB_REPOSITORY_OWNER", "your-username")
        self.repo_name = repo_name or os.getenv("GITHUB_REPOSITORY_NAME", "smartcloudops-ai")
        self.max_retries = 10
        self.retry_delay = 60  # seconds
        self.fixes_applied = []
        self.issues_resolved = []
        self.start_time = datetime.now()
        
        if self.github_token:
            self.headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            self.api_base = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        else:
            self.headers = None
            self.api_base = None
    
    def get_workflow_status(self) -> Dict:
        """Get current workflow status from GitHub API."""
        if not self.api_base:
            return {"status": "unknown", "runs": []}
        
        try:
            url = f"{self.api_base}/actions/runs"
            params = {"per_page": 5}
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            runs = response.json()["workflow_runs"]
            return {
                "status": "available",
                "runs": runs,
                "failed_count": len([r for r in runs if r.get("conclusion") == "failure"]),
                "success_count": len([r for r in runs if r.get("conclusion") == "success"]),
                "in_progress_count": len([r for r in runs if r.get("status") == "in_progress"])
            }
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            return {"status": "error", "runs": []}
    
    def fix_dependencies(self) -> bool:
        """Fix dependency-related issues."""
        logger.info("🔧 Fixing dependency issues...")
        
        try:
            # Update pip
            subprocess.run(["python", "-m", "pip", "install", "--upgrade", "pip"], check=True)
            
            # Install Python dependencies
            if os.path.exists("app/requirements.txt"):
                subprocess.run(["pip", "install", "-r", "app/requirements.txt"], check=True)
            
            # Install additional development dependencies
            dev_packages = [
                "pytest", "pytest-cov", "pytest-mock", "pytest-flask",
                "black", "flake8", "isort", "mypy", "bandit", "safety",
                "requests", "pyyaml", "python-dotenv"
            ]
            
            for package in dev_packages:
                try:
                    subprocess.run(["pip", "install", package], check=True)
                except subprocess.CalledProcessError:
                    logger.warning(f"Failed to install {package}")
            
            # Install Node.js dependencies
            if os.path.exists("frontend/package.json"):
                subprocess.run(["npm", "install", "--prefix", "frontend"], check=True)
            
            self.fixes_applied.append("dependencies")
            logger.info("✅ Dependencies fixed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to fix dependencies: {e}")
            return False
    
    def fix_workflow_files(self) -> bool:
        """Fix workflow YAML files."""
        logger.info("🔧 Fixing workflow files...")
        
        try:
            # Run the workflow fixer script
            if os.path.exists("scripts/auto_workflow_fixer.py"):
                subprocess.run([sys.executable, "scripts/auto_workflow_fixer.py"], check=True)
                self.fixes_applied.append("workflow_files")
                logger.info("✅ Workflow files fixed")
                return True
            else:
                logger.warning("Workflow fixer script not found")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to fix workflow files: {e}")
            return False
    
    def fix_test_environment(self) -> bool:
        """Fix test environment and configuration."""
        logger.info("🔧 Fixing test environment...")
        
        try:
            # Create test environment file
            test_env = {
                "JWT_SECRET_KEY": "test-jwt-secret-key-64-characters-long-for-testing-purposes-only",
                "ADMIN_API_KEY": "sk-admin-test-key-32-characters-long-for-testing",
                "ML_API_KEY": "sk-ml-test-key-32-characters-long-for-testing-only",
                "READONLY_API_KEY": "sk-readonly-test-key-32-chars-for-testing",
                "API_KEY_SALT": "test-salt-16-chars",
                "ADMIN_PASSWORD": "test-admin-password-16-chars",
                "FLASK_ENV": "testing",
                "FLASK_DEBUG": "False",
                "DATABASE_URL": "sqlite:///test.db",
                "REDIS_URL": "redis://localhost:6379/0"
            }
            
            with open(".env.test", "w") as f:
                for key, value in test_env.items():
                    f.write(f"{key}={value}\n")
            
            # Create test directories
            os.makedirs("logs", exist_ok=True)
            os.makedirs("data", exist_ok=True)
            os.makedirs("ml_models", exist_ok=True)
            
            self.fixes_applied.append("test_environment")
            logger.info("✅ Test environment fixed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to fix test environment: {e}")
            return False
    
    def fix_code_quality(self) -> bool:
        """Fix code quality issues."""
        logger.info("🔧 Fixing code quality issues...")
        
        try:
            # Python code formatting
            if os.path.exists("app/"):
                subprocess.run(["black", "app/", "--line-length", "127"], check=True)
                subprocess.run(["isort", "app/"], check=True)
            
            # Frontend code formatting
            if os.path.exists("frontend/"):
                subprocess.run(["npm", "run", "lint:fix", "--prefix", "frontend"], check=True)
            
            self.fixes_applied.append("code_quality")
            logger.info("✅ Code quality fixed")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"Code quality fix failed: {e}")
            return False
    
    def run_tests(self) -> bool:
        """Run tests to verify fixes."""
        logger.info("🧪 Running tests...")
        
        try:
            # Set test environment
            os.environ.update({
                "FLASK_ENV": "testing",
                "FLASK_DEBUG": "False"
            })
            
            # Run Python tests
            test_commands = [
                ["python", "-m", "pytest", "tests/phase_1/", "-v", "--tb=short"],
                ["python", "-m", "pytest", "tests/phase_2/", "-v", "--tb=short"],
                ["python", "-m", "pytest", "tests/test_security_fixes.py", "-v", "--tb=short"]
            ]
            
            for cmd in test_commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    if result.returncode != 0:
                        logger.warning(f"Test command failed: {' '.join(cmd)}")
                        logger.warning(f"Output: {result.stdout}")
                        logger.warning(f"Error: {result.stderr}")
                        return False
                except subprocess.TimeoutExpired:
                    logger.warning(f"Test command timed out: {' '.join(cmd)}")
                    return False
            
            # Run frontend tests
            if os.path.exists("frontend/"):
                try:
                    subprocess.run(["npm", "test", "--prefix", "frontend", "--", "--watchAll=false"], 
                                 check=True, timeout=300)
                except subprocess.TimeoutExpired:
                    logger.warning("Frontend tests timed out")
                    return False
            
            logger.info("✅ All tests passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Tests failed: {e}")
            return False
    
    def validate_workflows(self) -> bool:
        """Validate workflow files."""
        logger.info("✅ Validating workflows...")
        
        try:
            workflow_dir = Path(".github/workflows")
            if not workflow_dir.exists():
                logger.error("No workflows directory found")
                return False
            
            for workflow_file in workflow_dir.glob("*.yml"):
                with open(workflow_file, 'r') as f:
                    yaml.safe_load(f)
            
            logger.info("✅ All workflow files are valid")
            return True
            
        except Exception as e:
            logger.error(f"❌ Workflow validation failed: {e}")
            return False
    
    def commit_and_push_fixes(self) -> bool:
        """Commit and push all fixes."""
        logger.info("📝 Committing and pushing fixes...")
        
        try:
            # Add all changes
            subprocess.run(["git", "add", "."], check=True)
            
            # Check if there are changes to commit
            result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if not result.stdout.strip():
                logger.info("No changes to commit")
                return True
            
            # Commit changes
            commit_message = f"🔧 Auto-fix: {', '.join(self.fixes_applied)} - {datetime.now().isoformat()}"
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            
            # Push changes
            subprocess.run(["git", "push"], check=True)
            
            logger.info("✅ Fixes committed and pushed")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Git operation failed: {e}")
            return False
    
    def wait_for_workflow_completion(self, timeout: int = 1800) -> bool:
        """Wait for workflow completion."""
        logger.info("⏳ Waiting for workflow completion...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_workflow_status()
            
            if status["status"] == "available":
                if status["failed_count"] == 0 and status["in_progress_count"] == 0:
                    logger.info("✅ All workflows completed successfully")
                    return True
                elif status["failed_count"] > 0:
                    logger.info(f"❌ {status['failed_count']} workflows failed")
                    return False
            
            time.sleep(30)  # Wait 30 seconds before checking again
        
        logger.error("⏰ Timeout waiting for workflow completion")
        return False
    
    def run_complete_fix_cycle(self) -> bool:
        """Run a complete fix cycle."""
        logger.info("🔄 Starting complete fix cycle...")
        
        # Step 1: Fix dependencies
        if not self.fix_dependencies():
            logger.error("❌ Failed to fix dependencies")
            return False
        
        # Step 2: Fix workflow files
        if not self.fix_workflow_files():
            logger.error("❌ Failed to fix workflow files")
            return False
        
        # Step 3: Fix test environment
        if not self.fix_test_environment():
            logger.error("❌ Failed to fix test environment")
            return False
        
        # Step 4: Fix code quality
        self.fix_code_quality()  # Non-critical, continue even if it fails
        
        # Step 5: Validate workflows
        if not self.validate_workflows():
            logger.error("❌ Workflow validation failed")
            return False
        
        # Step 6: Run tests
        if not self.run_tests():
            logger.error("❌ Tests failed")
            return False
        
        # Step 7: Commit and push fixes
        if not self.commit_and_push_fixes():
            logger.error("❌ Failed to commit and push fixes")
            return False
        
        logger.info("✅ Complete fix cycle finished")
        return True
    
    def monitor_and_fix_until_success(self) -> bool:
        """Monitor workflows and fix issues until all pass."""
        logger.info("🚀 Starting complete workflow issue resolution...")
        
        retry_count = 0
        while retry_count < self.max_retries:
            logger.info(f"🔄 Attempt {retry_count + 1}/{self.max_retries}")
            
            # Check current workflow status
            status = self.get_workflow_status()
            
            if status["status"] == "available":
                if status["failed_count"] == 0:
                    logger.info("🎉 All workflows are passing!")
                    return True
                
                logger.info(f"❌ Found {status['failed_count']} failed workflows")
                
                # Run complete fix cycle
                if self.run_complete_fix_cycle():
                    # Wait for new workflow to complete
                    logger.info("⏳ Waiting for new workflow to complete...")
                    time.sleep(60)  # Wait for workflow to start
                    
                    if self.wait_for_workflow_completion():
                        logger.info("🎉 All workflows are now passing!")
                        return True
                    else:
                        logger.info("❌ New workflow failed, retrying...")
                else:
                    logger.error("❌ Fix cycle failed")
            
            # Wait before next retry
            delay = self.retry_delay * (2 ** retry_count)  # Exponential backoff
            logger.info(f"⏳ Waiting {delay} seconds before next attempt...")
            time.sleep(delay)
            retry_count += 1
        
        logger.error(f"❌ Failed to fix all workflows after {self.max_retries} attempts")
        return False
    
    def generate_final_report(self, success: bool) -> Dict:
        """Generate final report."""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        report = {
            "timestamp": end_time.isoformat(),
            "success": success,
            "duration_seconds": duration.total_seconds(),
            "fixes_applied": self.fixes_applied,
            "issues_resolved": self.issues_resolved,
            "retry_count": len(self.fixes_applied),
            "repo": f"{self.repo_owner}/{self.repo_name}",
            "recommendations": []
        }
        
        if success:
            report["recommendations"].append("All workflow issues have been resolved")
            report["recommendations"].append("Monitor workflows for any new issues")
        else:
            report["recommendations"].append("Manual intervention may be required")
            report["recommendations"].append("Review failed workflows for specific issues")
        
        return report

def main():
    """Main entry point."""
    logger.info("🚀 SmartCloudOps AI - Complete Workflow Issue Resolution")
    logger.info("=" * 60)
    
    # Initialize fixer
    fixer = CompleteWorkflowFixer()
    
    # Run complete monitoring and fixing
    success = fixer.monitor_and_fix_until_success()
    
    # Generate final report
    report = fixer.generate_final_report(success)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"workflow_fix_complete_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*60)
    print("🚀 WORKFLOW ISSUE RESOLUTION COMPLETE")
    print("="*60)
    print(f"📅 Timestamp: {report['timestamp']}")
    print(f"✅ Success: {report['success']}")
    print(f"⏱️  Duration: {report['duration_seconds']:.1f} seconds")
    print(f"🔄 Fixes Applied: {len(report['fixes_applied'])}")
    print(f"🔧 Fixes: {', '.join(report['fixes_applied'])}")
    print("\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"   • {rec}")
    print("="*60)
    
    if success:
        logger.info("🎉 All workflow issues have been resolved!")
        sys.exit(0)
    else:
        logger.error("❌ Failed to resolve all workflow issues")
        sys.exit(1)

if __name__ == "__main__":
    main()
