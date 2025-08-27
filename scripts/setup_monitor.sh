#!/bin/bash

# 🚀 SmartCloudOps AI - Workflow Monitor Setup Script
# ===================================================

set -e

echo "🚀 Setting up SmartCloudOps AI Workflow Monitor..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "app/requirements.txt" ]; then
    print_error "This script must be run from the project root directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null; then
    print_error "pip is required but not installed"
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    print_error "git is required but not installed"
    exit 1
fi

print_status "Installing Python dependencies..."

# Install Python dependencies
python3 -m pip install --upgrade pip
pip install -r app/requirements.txt

# Install additional monitoring dependencies
print_status "Installing monitoring dependencies..."
pip install requests python-dotenv

# Check if GitHub token is set
if [ -z "$GITHUB_TOKEN" ]; then
    print_warning "GITHUB_TOKEN environment variable is not set"
    print_status "Please set your GitHub token:"
    echo "export GITHUB_TOKEN=your_github_token_here"
    echo ""
    print_status "You can get a token from: https://github.com/settings/tokens"
    echo ""
    read -p "Do you want to continue without setting the token? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success "GitHub token is configured"
fi

# Make scripts executable
print_status "Making scripts executable..."
chmod +x scripts/auto_workflow_fixer.py
chmod +x scripts/monitor_workflows.py

# Test the setup
print_status "Testing workflow monitor setup..."

# Check if we can import the required modules
python3 -c "
import sys
import os
sys.path.append('scripts')
try:
    from auto_workflow_fixer import WorkflowMonitor
    print('✅ WorkflowMonitor imported successfully')
except ImportError as e:
    print(f'❌ Failed to import WorkflowMonitor: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_success "Setup completed successfully!"
else
    print_error "Setup failed during testing"
    exit 1
fi

echo ""
echo "🎉 SmartCloudOps AI Workflow Monitor is ready!"
echo ""
echo "Usage:"
echo "  Single run:     python3 scripts/monitor_workflows.py"
echo "  Continuous:     python3 scripts/monitor_workflows.py --continuous"
echo "  Custom interval: python3 scripts/monitor_workflows.py --continuous --interval 60"
echo ""
echo "The monitor will:"
echo "  ✅ Check workflow status automatically"
echo "  🔧 Fix common issues (dependencies, tests, linting, security)"
echo "  📝 Commit and push fixes"
echo "  🔄 Wait for new workflow runs"
echo "  📊 Generate reports"
echo ""
print_success "Setup complete! You can now run the workflow monitor."
