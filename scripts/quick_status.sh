#!/bin/bash

# Quick GitHub Workflows Status Checker
# Usage: ./scripts/quick_status.sh

echo "🔍 Quick GitHub Workflows Status"
echo "================================="

# Get recent workflow runs
echo "📊 Recent Workflow Runs:"
echo ""

curl -s "https://api.github.com/repos/Dileepreddy93/smartcloudops-ai/actions/runs?per_page=3" | \
jq -r '.workflow_runs[] | "🔄 \(.name)\n   Status: \(if .status == "completed" then (if .conclusion == "success" then "✅ SUCCESS" else "❌ FAILED" end) else "🔄 \(.status | ascii_upcase)" end)\n   Created: \(.created_at)\n"' 2>/dev/null

echo ""
echo "💡 For detailed monitoring, run: python scripts/monitor_workflows.py monitor"
echo "💡 For specific workflow: python scripts/monitor_workflows.py 'workflow name'"
