#!/bin/bash

# Setup script for Workflow Monitoring System
# This script installs all required dependencies

echo "🔧 Setting up Workflow Monitoring System..."
echo "=========================================="

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "💡 Consider activating your virtual environment first"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r scripts/requirements_monitor.txt

# Install system dependencies (if needed)
echo "🔧 Checking system dependencies..."

# Check for jq (JSON processor)
if ! command -v jq &> /dev/null; then
    echo "📦 Installing jq..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y jq
    elif command -v yum &> /dev/null; then
        sudo yum install -y jq
    elif command -v brew &> /dev/null; then
        brew install jq
    else
        echo "⚠️  Please install jq manually for JSON processing"
    fi
fi

# Check for curl
if ! command -v curl &> /dev/null; then
    echo "📦 Installing curl..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y curl
    elif command -v yum &> /dev/null; then
        sudo yum install -y curl
    elif command -v brew &> /dev/null; then
        brew install curl
    else
        echo "⚠️  Please install curl manually"
    fi
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/monitor_workflows.py
chmod +x scripts/auto_workflow_fixer.py
chmod +x scripts/quick_status.sh

# Test the monitoring system
echo "🧪 Testing monitoring system..."
python scripts/monitor_workflows.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Available monitoring tools:"
echo "   • Quick status: ./scripts/quick_status.sh"
echo "   • Monitor workflows: python scripts/monitor_workflows.py"
echo "   • Auto-fix workflows: python scripts/auto_workflow_fixer.py"
echo "   • Continuous monitoring: python scripts/auto_workflow_fixer.py monitor"
echo ""
echo "💡 For continuous monitoring, run:"
echo "   python scripts/auto_workflow_fixer.py monitor"
