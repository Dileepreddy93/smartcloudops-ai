#!/usr/bin/env python3
"""
GitHub Workflows Monitor
=======================

Simple script to monitor the status of GitHub Actions workflows.
"""

import requests
import json
import time
from datetime import datetime
import os

# Configuration
REPO_OWNER = "Dileepreddy93"
REPO_NAME = "smartcloudops-ai"
GITHUB_API_BASE = "https://api.github.com"

def get_workflow_runs(per_page=5):
    """Get recent workflow runs."""
    url = f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
    params = {"per_page": per_page}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()["workflow_runs"]
    except requests.RequestException as e:
        print(f"❌ Error fetching workflow runs: {e}")
        return []

def get_workflow_jobs(run_id):
    """Get jobs for a specific workflow run."""
    url = f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}/jobs"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()["jobs"]
    except requests.RequestException as e:
        print(f"❌ Error fetching jobs for run {run_id}: {e}")
        return []

def format_status(status, conclusion):
    """Format status with emoji."""
    if status == "completed":
        if conclusion == "success":
            return "✅ SUCCESS"
        elif conclusion == "failure":
            return "❌ FAILED"
        elif conclusion == "cancelled":
            return "⏹️ CANCELLED"
        else:
            return f"❓ {conclusion.upper()}"
    elif status == "in_progress":
        return "🔄 RUNNING"
    elif status == "queued":
        return "⏳ QUEUED"
    else:
        return f"❓ {status.upper()}"

def monitor_workflows():
    """Monitor workflow status."""
    print("🔍 GitHub Workflows Monitor")
    print("=" * 50)
    
    while True:
        # Clear screen (works on most terminals)
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print(f"🔍 GitHub Workflows Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Get recent workflow runs
        runs = get_workflow_runs(5)
        
        if not runs:
            print("❌ No workflow runs found or error occurred")
            time.sleep(30)
            continue
        
        print(f"📊 Recent Workflow Runs ({len(runs)}):")
        print("-" * 60)
        
        for run in runs:
            # Format timestamp
            created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
            time_ago = datetime.now(created_at.tzinfo) - created_at
            
            print(f"\n🔄 {run['name']}")
            print(f"   ID: {run['id']}")
            print(f"   Status: {format_status(run['status'], run.get('conclusion', ''))}")
            print(f"   Created: {time_ago.total_seconds():.0f}s ago")
            
            # Get job details if completed
            if run['status'] == 'completed':
                jobs = get_workflow_jobs(run['id'])
                if jobs:
                    print("   Jobs:")
                    for job in jobs:
                        job_status = format_status(job['status'], job.get('conclusion', ''))
                        print(f"     • {job['name']}: {job_status}")
        
        print("\n" + "=" * 60)
        print("🔄 Refreshing in 30 seconds... (Ctrl+C to stop)")
        
        time.sleep(30)

def check_specific_workflow(workflow_name=None):
    """Check status of a specific workflow."""
    runs = get_workflow_runs(10)
    
    if workflow_name:
        runs = [run for run in runs if workflow_name.lower() in run['name'].lower()]
    
    print(f"📊 Workflow Status Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    for run in runs:
        created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
        time_ago = datetime.now(created_at.tzinfo) - created_at
        
        print(f"\n🔄 {run['name']}")
        print(f"   ID: {run['id']}")
        print(f"   Status: {format_status(run['status'], run.get('conclusion', ''))}")
        print(f"   Created: {time_ago.total_seconds():.0f}s ago")
        
        if run['status'] == 'completed':
            jobs = get_workflow_jobs(run['id'])
            if jobs:
                print("   Jobs:")
                for job in jobs:
                    job_status = format_status(job['status'], job.get('conclusion', ''))
                    print(f"     • {job['name']}: {job_status}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "monitor":
            monitor_workflows()
        else:
            check_specific_workflow(sys.argv[1])
    else:
        check_specific_workflow()
