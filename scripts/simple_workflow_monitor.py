#!/usr/bin/env python3
"""
Simple Workflow Monitor - GitHub Actions Status Checker
=====================================================

A simple script to monitor GitHub Actions workflow status and report pass/fail results.
"""

import json
import subprocess
import sys
from datetime import datetime
from typing import List, Dict

def run_gh_command(cmd: List[str]) -> Dict:
    """Run a GitHub CLI command and return JSON result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from command {' '.join(cmd)}: {e}")
        return {}

def get_workflow_runs(owner: str, repo: str, limit: int = 20) -> List[Dict]:
    """Get recent workflow runs."""
    cmd = [
        "gh", "api", 
        f"repos/{owner}/{repo}/actions/runs",
        "--jq", f".workflow_runs[0:{limit}]"
    ]
    result = run_gh_command(cmd)
    return result if isinstance(result, list) else []

def get_workflow_status_summary(runs: List[Dict]) -> Dict:
    """Generate a summary of workflow status."""
    summary = {
        "total_runs": len(runs),
        "successful": 0,
        "failed": 0,
        "in_progress": 0,
        "cancelled": 0,
        "skipped": 0,
        "failed_workflows": [],
        "recent_successes": []
    }
    
    for run in runs:
        conclusion = run.get("conclusion", "unknown")
        status = run.get("status", "unknown")
        name = run.get("name", "Unknown Workflow")
        run_number = run.get("run_number", 0)
        created_at = run.get("created_at", "")
        
        if status == "in_progress":
            summary["in_progress"] += 1
        elif conclusion == "success":
            summary["successful"] += 1
            summary["recent_successes"].append({
                "name": name,
                "run_number": run_number,
                "created_at": created_at
            })
        elif conclusion == "failure":
            summary["failed"] += 1
            summary["failed_workflows"].append({
                "name": name,
                "run_number": run_number,
                "created_at": created_at,
                "url": run.get("html_url", "")
            })
        elif conclusion == "cancelled":
            summary["cancelled"] += 1
        elif conclusion == "skipped":
            summary["skipped"] += 1
    
    return summary

def get_workflow_logs(run_id: str) -> str:
    """Get logs for a specific workflow run."""
    try:
        result = subprocess.run([
            "gh", "run", "view", run_id, "--log"
        ], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError:
        return "Unable to retrieve logs"

def analyze_failure_patterns(logs: str) -> List[str]:
    """Analyze logs for common failure patterns."""
    patterns = []
    
    if "npm ERR!" in logs:
        patterns.append("npm dependency error")
    if "ModuleNotFoundError" in logs:
        patterns.append("Python import error")
    if "FAILED" in logs and "test" in logs.lower():
        patterns.append("Test failure")
    if "error:" in logs and "lint" in logs.lower():
        patterns.append("Linting error")
    if "failed to build" in logs:
        patterns.append("Docker build error")
    if "timeout" in logs.lower():
        patterns.append("Timeout error")
    if "permission denied" in logs.lower():
        patterns.append("Permission error")
    if "out of memory" in logs.lower():
        patterns.append("Memory error")
    
    return patterns

def print_status_report(summary: Dict):
    """Print a formatted status report."""
    print("\n" + "="*60)
    print("🚀 GITHUB ACTIONS WORKFLOW STATUS REPORT")
    print("="*60)
    print(f"📊 Total Runs Analyzed: {summary['total_runs']}")
    print(f"✅ Successful: {summary['successful']}")
    print(f"❌ Failed: {summary['failed']}")
    print(f"🔄 In Progress: {summary['in_progress']}")
    print(f"⏹️  Cancelled: {summary['cancelled']}")
    print(f"⏭️  Skipped: {summary['skipped']}")
    
    if summary['failed_workflows']:
        print(f"\n❌ FAILED WORKFLOWS ({len(summary['failed_workflows'])}):")
        print("-" * 40)
        for workflow in summary['failed_workflows'][:5]:  # Show last 5 failures
            print(f"• {workflow['name']} (Run #{workflow['run_number']})")
            print(f"  Created: {workflow['created_at']}")
            print(f"  URL: {workflow['url']}")
            print()
    
    if summary['recent_successes']:
        print(f"✅ RECENT SUCCESSES ({len(summary['recent_successes'])}):")
        print("-" * 40)
        for workflow in summary['recent_successes'][:3]:  # Show last 3 successes
            print(f"• {workflow['name']} (Run #{workflow['run_number']})")
            print(f"  Created: {workflow['created_at']}")
            print()
    
    # Overall status
    if summary['failed'] == 0:
        print("🎉 ALL WORKFLOWS ARE PASSING! ✅")
    else:
        print(f"⚠️  {summary['failed']} WORKFLOW(S) NEED ATTENTION ❌")
    
    print("="*60)

def main():
    """Main function to monitor workflows."""
    # Configuration
    owner = "Dileepreddy93"
    repo = "smartcloudops-ai"
    limit = 20
    
    print(f"🔍 Monitoring workflows for {owner}/{repo}")
    print(f"⏰ Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get workflow runs
    print("\n📋 Fetching recent workflow runs...")
    runs = get_workflow_runs(owner, repo, limit)
    
    if not runs:
        print("❌ No workflow runs found or unable to fetch data")
        sys.exit(1)
    
    # Generate summary
    summary = get_workflow_status_summary(runs)
    
    # Print report
    print_status_report(summary)
    
    # If there are failures, offer to analyze them
    if summary['failed_workflows']:
        print("\n🔍 Would you like to analyze specific failed workflows?")
        print("Run this script with --analyze <run_id> to get detailed logs")
        
        # Show the most recent failure
        latest_failure = summary['failed_workflows'][0]
        print(f"\n📋 Latest failure: {latest_failure['name']} (Run #{latest_failure['run_number']})")
        print(f"🔗 URL: {latest_failure['url']}")

if __name__ == "__main__":
    main()
