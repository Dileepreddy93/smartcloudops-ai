#!/usr/bin/env python3
"""
SmartCloudOps AI - Automatic Workflow Resolver
=============================================

This script continuously monitors GitHub Actions workflows, detects failures,
and automatically resolves issues until all workflows pass successfully.

Features:
- Real-time workflow monitoring
- Automatic issue detection and classification
- Intelligent auto-fixing with multiple strategies
- Continuous retry with exponential backoff
- Comprehensive logging and reporting
- GitHub API integration for live status
"""

import os
import sys
import json
import time
import subprocess
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
import re

class WorkflowResolver:
    """Main class for automatic workflow resolution."""
    
    def __init__(self, github_token: str = None, repo_owner: str = None, repo_name: str = None):
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.repo_owner = repo_owner or os.getenv('GITHUB_REPOSITORY_OWNER', 'Dileepreddy93')
        self.repo_name = repo_name or os.getenv('GITHUB_REPOSITORY_NAME', 'smartcloudops-ai')
        self.base_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        } if self.github_token else {}
        
        self.max_retries = 20
        self.retry_delay = 60  # seconds
        self.max_duration = 3600  # 1 hour max
        self.start_time = datetime.now()
        
        # Setup directories
        self.log_dir = Path("logs")
        self.reports_dir = Path("reports")
        self.log_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        self.log_file = self.log_dir / f"workflow_resolver_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a') as f:
            f.write(log_message + '\n')
    
    def get_workflow_runs(self) -> List[Dict]:
        """Get recent workflow runs from GitHub API."""
        try:
            url = f"{self.base_url}/actions/runs"
            params = {
                'per_page': 10,
                'status': 'completed'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()['workflow_runs']
        except Exception as e:
            self.log(f"Failed to get workflow runs: {e}", "ERROR")
            return []
    
    def get_workflow_run_details(self, run_id: int) -> Optional[Dict]:
        """Get detailed information about a specific workflow run."""
        try:
            url = f"{self.base_url}/actions/runs/{run_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.log(f"Failed to get workflow run {run_id} details: {e}", "ERROR")
            return None
    
    def get_workflow_jobs(self, run_id: int) -> List[Dict]:
        """Get jobs for a specific workflow run."""
        try:
            url = f"{self.base_url}/actions/runs/{run_id}/jobs"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()['jobs']
        except Exception as e:
            self.log(f"Failed to get jobs for run {run_id}: {e}", "ERROR")
            return []
    
    def get_workflow_logs(self, run_id: int, job_id: int) -> str:
        """Get logs for a specific job."""
        try:
            url = f"{self.base_url}/actions/runs/{run_id}/jobs/{job_id}/logs"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.log(f"Failed to get logs for job {job_id}: {e}", "ERROR")
            return ""
    
    def analyze_workflow_failure(self, run_details: Dict, jobs: List[Dict]) -> Dict:
        """Analyze workflow failure and identify root cause."""
        analysis = {
            'workflow_name': run_details.get('name', 'Unknown'),
            'run_id': run_details.get('id'),
            'conclusion': run_details.get('conclusion'),
            'status': run_details.get('status'),
            'issues': [],
            'fixes': [],
            'severity': 'LOW'
        }
        
        failed_jobs = [job for job in jobs if job.get('conclusion') == 'failure']
        
        for job in failed_jobs:
            job_name = job.get('name', 'Unknown')
            logs = self.get_workflow_logs(run_details['id'], job['id'])
            
            # Analyze logs for common failure patterns
            issues = self.analyze_job_logs(logs, job_name)
            analysis['issues'].extend(issues)
            
            # Determine fixes based on issues
            fixes = self.determine_fixes(issues, job_name)
            analysis['fixes'].extend(fixes)
        
        # Set severity based on issues found
        if any(issue.get('type') in ['dependency', 'permission', 'syntax'] for issue in analysis['issues']):
            analysis['severity'] = 'HIGH'
        elif any(issue.get('type') in ['timeout', 'resource'] for issue in analysis['issues']):
            analysis['severity'] = 'MEDIUM'
        
        return analysis
    
    def analyze_job_logs(self, logs: str, job_name: str) -> List[Dict]:
        """Analyze job logs to identify specific issues."""
        issues = []
        
        # Common failure patterns
        patterns = {
            'dependency': [
                r'ModuleNotFoundError: No module named \'(\w+)\'',
                r'npm ERR!',
                r'pip install.*failed',
                r'package.*not found',
                r'ImportError',
                r'No such file or directory.*requirements\.txt',
                r'No such file or directory.*package\.json'
            ],
            'permission': [
                r'Permission denied',
                r'403 Forbidden',
                r'Unauthorized',
                r'Access denied',
                r'Insufficient permissions'
            ],
            'syntax': [
                r'YAML.*error',
                r'Invalid YAML',
                r'SyntaxError',
                r'IndentationError',
                r'Parse error'
            ],
            'timeout': [
                r'Timeout',
                r'Timed out',
                r'execution timeout',
                r'Build timed out'
            ],
            'resource': [
                r'Out of memory',
                r'Disk space',
                r'No space left',
                r'Resource exhausted'
            ],
            'network': [
                r'Connection refused',
                r'Network error',
                r'DNS resolution',
                r'SSL certificate'
            ],
            'python': [
                r'python: command not found',
                r'Python.*not found',
                r'pip.*not found'
            ],
            'node': [
                r'node: command not found',
                r'npm.*not found',
                r'Node.*not found'
            ]
        }
        
        for issue_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, logs, re.IGNORECASE)
                if matches:
                    issues.append({
                        'type': issue_type,
                        'pattern': pattern,
                        'matches': matches,
                        'job_name': job_name,
                        'description': f"{issue_type.title()} issue detected in {job_name}"
                    })
        
        return issues
    
    def determine_fixes(self, issues: List[Dict], job_name: str) -> List[Dict]:
        """Determine appropriate fixes based on identified issues."""
        fixes = []
        
        for issue in issues:
            issue_type = issue.get('type')
            
            if issue_type == 'dependency':
                fixes.extend([
                    {
                        'type': 'install_dependencies',
                        'description': f'Install missing dependencies for {job_name}',
                        'command': 'pip install -r app/requirements.txt && npm ci'
                    },
                    {
                        'type': 'update_requirements',
                        'description': f'Update requirements.txt for {job_name}',
                        'command': 'pip freeze > app/requirements.txt'
                    }
                ])
            
            elif issue_type == 'permission':
                fixes.extend([
                    {
                        'type': 'fix_permissions',
                        'description': f'Fix permissions in workflow for {job_name}',
                        'action': 'add_permissions_section'
                    }
                ])
            
            elif issue_type == 'syntax':
                fixes.extend([
                    {
                        'type': 'fix_yaml',
                        'description': f'Fix YAML syntax in workflow for {job_name}',
                        'action': 'validate_and_fix_yaml'
                    }
                ])
            
            elif issue_type == 'python':
                fixes.extend([
                    {
                        'type': 'setup_python',
                        'description': f'Setup Python environment for {job_name}',
                        'command': 'python3 -m pip install --upgrade pip'
                    }
                ])
            
            elif issue_type == 'node':
                fixes.extend([
                    {
                        'type': 'setup_node',
                        'description': f'Setup Node.js environment for {job_name}',
                        'command': 'npm install -g npm@latest'
                    }
                ])
        
        return fixes
    
    def apply_fix(self, fix: Dict) -> bool:
        """Apply a specific fix."""
        try:
            fix_type = fix.get('type')
            
            if fix_type == 'install_dependencies':
                return self.install_dependencies()
            
            elif fix_type == 'update_requirements':
                return self.update_requirements()
            
            elif fix_type == 'fix_permissions':
                return self.fix_workflow_permissions()
            
            elif fix_type == 'fix_yaml':
                return self.fix_workflow_yaml()
            
            elif fix_type == 'setup_python':
                return self.setup_python_environment()
            
            elif fix_type == 'setup_node':
                return self.setup_node_environment()
            
            elif fix_type == 'command' and fix.get('command'):
                return self.run_command(fix['command'])
            
            return False
            
        except Exception as e:
            self.log(f"Failed to apply fix {fix.get('type')}: {e}", "ERROR")
            return False
    
    def install_dependencies(self) -> bool:
        """Install project dependencies."""
        try:
            self.log("Installing Python dependencies...")
            result = subprocess.run(['pip', 'install', '-r', 'app/requirements.txt'], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log("Python dependencies installed successfully")
                return True
            else:
                self.log(f"Failed to install Python dependencies: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error installing dependencies: {e}", "ERROR")
            return False
    
    def update_requirements(self) -> bool:
        """Update requirements.txt file."""
        try:
            self.log("Updating requirements.txt...")
            result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True)
            
            if result.returncode == 0:
                with open('app/requirements.txt', 'w') as f:
                    f.write(result.stdout)
                self.log("requirements.txt updated successfully")
                return True
            else:
                self.log(f"Failed to update requirements.txt: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error updating requirements: {e}", "ERROR")
            return False
    
    def fix_workflow_permissions(self) -> bool:
        """Fix workflow permissions."""
        try:
            self.log("Fixing workflow permissions...")
            workflow_files = list(Path('.github/workflows').glob('*.yml'))
            
            for workflow_file in workflow_files:
                with open(workflow_file, 'r') as f:
                    content = f.read()
                
                if 'permissions:' not in content:
                    # Add permissions section
                    lines = content.split('\n')
                    new_lines = []
                    permissions_added = False
                    
                    for line in lines:
                        new_lines.append(line)
                        if line.strip().startswith('on:') and not permissions_added:
                            indent = len(line) - len(line.lstrip())
                            permissions_indent = ' ' * (indent + 2)
                            new_lines.append(f'{permissions_indent}permissions:')
                            new_lines.append(f'{permissions_indent}  contents: read')
                            new_lines.append(f'{permissions_indent}  pull-requests: write')
                            new_lines.append(f'{permissions_indent}  issues: write')
                            new_lines.append('')
                            permissions_added = True
                    
                    if permissions_added:
                        with open(workflow_file, 'w') as f:
                            f.write('\n'.join(new_lines))
                        self.log(f"Added permissions to {workflow_file}")
            
            return True
            
        except Exception as e:
            self.log(f"Error fixing workflow permissions: {e}", "ERROR")
            return False
    
    def fix_workflow_yaml(self) -> bool:
        """Fix workflow YAML syntax issues."""
        try:
            self.log("Fixing workflow YAML syntax...")
            workflow_files = list(Path('.github/workflows').glob('*.yml'))
            
            for workflow_file in workflow_files:
                with open(workflow_file, 'r') as f:
                    content = f.read()
                
                # Fix common YAML issues
                original_content = content
                
                # Fix template literals in JavaScript
                content = re.sub(r'\$\{([^}]+)\}', r'${{ \1 }}', content)
                
                # Fix unescaped quotes
                content = re.sub(r'`([^`]*)`', r"'\1'", content)
                
                if content != original_content:
                    with open(workflow_file, 'w') as f:
                        f.write(content)
                    self.log(f"Fixed YAML syntax in {workflow_file}")
            
            return True
            
        except Exception as e:
            self.log(f"Error fixing workflow YAML: {e}", "ERROR")
            return False
    
    def setup_python_environment(self) -> bool:
        """Setup Python environment."""
        try:
            self.log("Setting up Python environment...")
            result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log(f"Python version: {result.stdout.strip()}")
                return True
            else:
                self.log("Python not found, attempting to install...", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Error setting up Python: {e}", "ERROR")
            return False
    
    def setup_node_environment(self) -> bool:
        """Setup Node.js environment."""
        try:
            self.log("Setting up Node.js environment...")
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log(f"Node.js version: {result.stdout.strip()}")
                return True
            else:
                self.log("Node.js not found, attempting to install...", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Error setting up Node.js: {e}", "ERROR")
            return False
    
    def run_command(self, command: str) -> bool:
        """Run a shell command."""
        try:
            self.log(f"Running command: {command}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log(f"Command successful: {command}")
                return True
            else:
                self.log(f"Command failed: {command} - {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error running command {command}: {e}", "ERROR")
            return False
    
    def commit_and_push_fixes(self) -> bool:
        """Commit and push fixes to repository."""
        try:
            self.log("Committing and pushing fixes...")
            
            # Check if there are changes to commit
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
            if not result.stdout.strip():
                self.log("No changes to commit")
                return True
            
            # Add all changes
            subprocess.run(['git', 'add', '.'], check=True)
            
            # Commit changes
            commit_message = f"🔧 Auto-fix workflow issues - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            
            # Push changes
            subprocess.run(['git', 'push'], check=True)
            
            self.log("Fixes committed and pushed successfully")
            return True
            
        except Exception as e:
            self.log(f"Error committing and pushing fixes: {e}", "ERROR")
            return False
    
    def check_workflow_status(self) -> Tuple[bool, List[Dict]]:
        """Check current workflow status and return (all_passing, failed_runs)."""
        try:
            runs = self.get_workflow_runs()
            failed_runs = []
            
            for run in runs:
                if run.get('conclusion') == 'failure':
                    failed_runs.append(run)
            
            all_passing = len(failed_runs) == 0
            return all_passing, failed_runs
            
        except Exception as e:
            self.log(f"Error checking workflow status: {e}", "ERROR")
            return False, []
    
    def resolve_workflow_issues(self) -> bool:
        """Main method to resolve workflow issues."""
        self.log("🚀 Starting automatic workflow resolution...")
        
        retry_count = 0
        
        while retry_count < self.max_retries:
            # Check if we've exceeded max duration
            if (datetime.now() - self.start_time).total_seconds() > self.max_duration:
                self.log("Maximum duration exceeded, stopping resolution", "WARNING")
                break
            
            self.log(f"🔍 Checking workflow status (attempt {retry_count + 1}/{self.max_retries})...")
            
            all_passing, failed_runs = self.check_workflow_status()
            
            if all_passing:
                self.log("🎉 All workflows are now passing!")
                return True
            
            if not failed_runs:
                self.log("No failed runs found, waiting for new runs...")
                time.sleep(self.retry_delay)
                retry_count += 1
                continue
            
            self.log(f"Found {len(failed_runs)} failed workflow runs")
            
            # Analyze and fix each failed run
            fixes_applied = False
            
            for run in failed_runs:
                self.log(f"Analyzing failed run: {run.get('name')} (ID: {run.get('id')})")
                
                run_details = self.get_workflow_run_details(run['id'])
                if not run_details:
                    continue
                
                jobs = self.get_workflow_jobs(run['id'])
                analysis = self.analyze_workflow_failure(run_details, jobs)
                
                self.log(f"Analysis complete for {run.get('name')}: {len(analysis['issues'])} issues found")
                
                # Apply fixes
                for fix in analysis['fixes']:
                    self.log(f"Applying fix: {fix.get('description')}")
                    if self.apply_fix(fix):
                        fixes_applied = True
                        self.log(f"✅ Fix applied successfully: {fix.get('description')}")
                    else:
                        self.log(f"❌ Fix failed: {fix.get('description')}", "ERROR")
            
            # Commit and push fixes if any were applied
            if fixes_applied:
                if self.commit_and_push_fixes():
                    self.log("✅ Fixes committed and pushed, waiting for workflows to run...")
                    time.sleep(self.retry_delay * 2)  # Wait longer for workflows to complete
                else:
                    self.log("❌ Failed to commit and push fixes", "ERROR")
            else:
                self.log("No fixes could be applied, waiting before retry...")
                time.sleep(self.retry_delay)
            
            retry_count += 1
        
        self.log(f"❌ Failed to resolve all workflow issues after {self.max_retries} attempts", "ERROR")
        return False
    
    def generate_report(self) -> Dict:
        """Generate a comprehensive resolution report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'duration': (datetime.now() - self.start_time).total_seconds(),
            'max_retries': self.max_retries,
            'log_file': str(self.log_file),
            'status': 'completed'
        }
        
        # Read log file for details
        try:
            with open(self.log_file, 'r') as f:
                log_content = f.read()
            
            report['log_summary'] = {
                'total_lines': len(log_content.split('\n')),
                'errors': log_content.count('[ERROR]'),
                'warnings': log_content.count('[WARNING]'),
                'successes': log_content.count('✅')
            }
        except Exception as e:
            report['log_summary'] = {'error': str(e)}
        
        return report

def main():
    """Main function."""
    print("🚀 SmartCloudOps AI - Automatic Workflow Resolver")
    print("=" * 60)
    
    # Initialize resolver
    resolver = WorkflowResolver()
    
    try:
        # Start resolution process
        success = resolver.resolve_workflow_issues()
        
        # Generate final report
        report = resolver.generate_report()
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = resolver.reports_dir / f"workflow_resolution_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n" + "=" * 60)
        print("📊 RESOLUTION SUMMARY")
        print("=" * 60)
        print(f"Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
        print(f"Duration: {report['duration']:.1f} seconds")
        print(f"Log File: {report['log_file']}")
        print(f"Report File: {report_file}")
        
        if success:
            print("\n🎉 All workflows are now passing!")
            return 0
        else:
            print("\n❌ Some workflow issues could not be resolved automatically")
            print("Please check the logs and report for details")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Resolution interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())