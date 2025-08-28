#!/bin/bash

# SmartCloudOps AI - Continuous Workflow Monitor Runner
# ===================================================
#
# This script runs the continuous workflow monitoring system that automatically
# detects and fixes GitHub Actions workflow failures.
#
# Usage: ./scripts/run_continuous_monitor.sh [options]
#
# Options:
#   --interval SECONDS    Check interval in seconds (default: 60)
#   --max-retries N       Maximum retries per issue (default: 5)
#   --token TOKEN         GitHub token (or set GITHUB_TOKEN env var)
#   --repo OWNER/NAME     Repository in format owner/name
#   --help                Show this help message

set -e

# Default configuration
CHECK_INTERVAL=60
MAX_RETRIES=5
GITHUB_TOKEN=""
REPO_OWNER="Dileepreddy93"
REPO_NAME="smartcloudops-ai"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to show help
show_help() {
    cat << EOF
SmartCloudOps AI - Continuous Workflow Monitor

Usage: $0 [options]

Options:
    --interval SECONDS    Check interval in seconds (default: 60)
    --max-retries N       Maximum retries per issue (default: 5)
    --token TOKEN         GitHub token (or set GITHUB_TOKEN env var)
    --repo OWNER/NAME     Repository in format owner/name
    --help                Show this help message

Environment Variables:
    GITHUB_TOKEN          GitHub personal access token
    GITHUB_REPOSITORY_OWNER  Repository owner (default: Dileepreddy93)
    GITHUB_REPOSITORY_NAME   Repository name (default: smartcloudops-ai)
    CHECK_INTERVAL        Check interval in seconds
    MAX_RETRIES           Maximum retries per issue

Examples:
    $0 --interval 30 --max-retries 3
    $0 --token ghp_xxxxxxxx --repo myuser/myrepo
    GITHUB_TOKEN=ghp_xxxxxxxx $0

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --interval)
            CHECK_INTERVAL="$2"
            shift 2
            ;;
        --max-retries)
            MAX_RETRIES="$2"
            shift 2
            ;;
        --token)
            GITHUB_TOKEN="$2"
            shift 2
            ;;
        --repo)
            IFS='/' read -r REPO_OWNER REPO_NAME <<< "$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if we're in the right directory
if [[ ! -f "scripts/continuous_workflow_monitor.py" ]]; then
    print_error "Script not found. Please run from the project root directory."
    exit 1
fi

# Check for GitHub token
if [[ -z "$GITHUB_TOKEN" ]]; then
    GITHUB_TOKEN=$(git config --get github.token 2>/dev/null || echo "")
fi

if [[ -z "$GITHUB_TOKEN" ]]; then
    print_error "GitHub token not found. Please provide --token or set GITHUB_TOKEN environment variable."
    print_warning "You can create a token at: https://github.com/settings/tokens"
    exit 1
fi

# Validate repository format
if [[ -z "$REPO_OWNER" || -z "$REPO_NAME" ]]; then
    print_error "Invalid repository format. Use --repo owner/name"
    exit 1
fi

# Print configuration
print_status "🚀 Starting Continuous Workflow Monitor"
print_status "📊 Configuration:"
print_status "   Repository: $REPO_OWNER/$REPO_NAME"
print_status "   Check Interval: ${CHECK_INTERVAL}s"
print_status "   Max Retries: $MAX_RETRIES"
print_status "   Token: ${GITHUB_TOKEN:0:8}..."

# Check if virtual environment exists
if [[ -d "workflow_monitor_env" ]]; then
    print_status "🔧 Activating virtual environment..."
    source workflow_monitor_env/bin/activate
else
    print_warning "Virtual environment not found. Using system Python."
fi

# Install required dependencies if needed
print_status "📦 Checking dependencies..."
if ! python3 -c "import requests, yaml" 2>/dev/null; then
    print_status "Installing required dependencies..."
    pip install requests pyyaml --break-system-packages
fi

# Set environment variables
export GITHUB_TOKEN="$GITHUB_TOKEN"
export GITHUB_REPOSITORY_OWNER="$REPO_OWNER"
export GITHUB_REPOSITORY_NAME="$REPO_NAME"
export CHECK_INTERVAL="$CHECK_INTERVAL"
export MAX_RETRIES="$MAX_RETRIES"

# Create logs directory
mkdir -p logs

# Run the continuous monitor
print_status "🔄 Starting continuous monitoring..."
print_status "Press Ctrl+C to stop monitoring"

# Run the Python script
python3 scripts/continuous_workflow_monitor.py

# Check exit status
if [[ $? -eq 0 ]]; then
    print_success "Continuous monitoring completed successfully!"
else
    print_error "Continuous monitoring failed!"
    exit 1
fi