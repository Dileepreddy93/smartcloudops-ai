#!/bin/bash

# SmartCloudOps AI - Workflow Monitor Starter
# ==========================================

set -euo pipefail

echo "🚀 SmartCloudOps AI - Starting Workflow Monitor"
echo "=============================================="

# Check if we're in the right directory
if [ ! -d ".github/workflows" ]; then
    echo "❌ Error: No .github/workflows directory found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 is not installed or not in PATH"
    exit 1
fi

# Check if Git is available
if ! command -v git &> /dev/null; then
    echo "❌ Error: Git is not installed or not in PATH"
    exit 1
fi

# Create necessary directories
mkdir -p logs reports

echo "✅ Environment check passed"
echo "✅ Python3: $(python3 --version)"
echo "✅ Git: $(git --version)"
echo ""

# Check if the monitor script exists
if [ ! -f "scripts/continuous_workflow_monitor.py" ]; then
    echo "❌ Error: scripts/continuous_workflow_monitor.py not found"
    exit 1
fi

echo "🔍 Starting continuous workflow monitoring..."
echo "📝 Logs will be saved to logs/ directory"
echo "📊 Reports will be saved to reports/ directory"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

# Start the continuous monitor
python3 scripts/continuous_workflow_monitor.py

echo ""
echo "🏁 Workflow monitoring completed"