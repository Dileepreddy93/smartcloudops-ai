#!/bin/bash
# SmartCloudOps AI - Workflow Monitor Runner
# =========================================
# 
# This script runs the complete workflow monitoring and auto-fix system.
# It will continuously monitor workflows and fix issues until all workflows pass.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
REPORTS_DIR="$PROJECT_ROOT/reports"

# Create directories if they don't exist
mkdir -p "$LOG_DIR" "$REPORTS_DIR"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed or not in PATH"
        exit 1
    fi
    
    # Check if required Python packages are installed
    python3 -c "import requests, yaml, json" 2>/dev/null || {
        log_warning "Installing required Python packages..."
        pip3 install requests pyyaml python-dotenv
    }
    
    # Check if Node.js is available (for frontend)
    if ! command -v node &> /dev/null; then
        log_warning "Node.js is not installed - frontend fixes may not work"
    fi
    
    # Check if git is available
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed or not in PATH"
        exit 1
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to check GitHub token
check_github_token() {
    if [ -z "${GITHUB_TOKEN:-}" ]; then
        log_warning "GITHUB_TOKEN environment variable not set"
        log_warning "Some features may not work without GitHub API access"
        log_warning "Set GITHUB_TOKEN to enable full functionality"
        return 1
    fi
    
    log_success "GitHub token found"
    return 0
}

# Function to run workflow monitor
run_workflow_monitor() {
    log "Starting workflow monitor..."
    
    cd "$PROJECT_ROOT"
    
    # Run the workflow monitor
    if python3 scripts/workflow_monitor.py; then
        log_success "Workflow monitor completed successfully"
        return 0
    else
        log_error "Workflow monitor failed"
        return 1
    fi
}

# Function to run workflow fixer
run_workflow_fixer() {
    log "Starting workflow fixer..."
    
    cd "$PROJECT_ROOT"
    
    # Run the workflow fixer
    if python3 scripts/auto_workflow_fixer.py; then
        log_success "Workflow fixer completed successfully"
        return 0
    else
        log_error "Workflow fixer failed"
        return 1
    fi
}

# Function to run complete fix cycle
run_complete_fix_cycle() {
    log "Starting complete fix cycle..."
    
    cd "$PROJECT_ROOT"
    
    # Run the complete fix cycle
    if python3 scripts/fix_all_workflow_issues.py; then
        log_success "Complete fix cycle completed successfully"
        return 0
    else
        log_error "Complete fix cycle failed"
        return 1
    fi
}

# Function to display usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  monitor     Run workflow monitoring only"
    echo "  fix         Run workflow fixing only"
    echo "  complete    Run complete monitoring and fixing cycle"
    echo "  auto        Run automatic mode (default)"
    echo "  help        Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  GITHUB_TOKEN    GitHub API token for workflow monitoring"
    echo "  LOG_LEVEL       Logging level (DEBUG, INFO, WARNING, ERROR)"
    echo ""
    echo "Examples:"
    echo "  $0 monitor      # Run monitoring only"
    echo "  $0 fix          # Run fixing only"
    echo "  $0 complete     # Run complete cycle"
    echo "  $0 auto         # Run automatic mode"
}

# Function to display status
show_status() {
    log "Current status:"
    echo "  Project Root: $PROJECT_ROOT"
    echo "  Script Directory: $SCRIPT_DIR"
    echo "  Log Directory: $LOG_DIR"
    echo "  Reports Directory: $REPORTS_DIR"
    echo "  Python Version: $(python3 --version)"
    echo "  Node Version: $(node --version 2>/dev/null || echo 'Not installed')"
    echo "  Git Repository: $(git remote get-url origin 2>/dev/null || echo 'No remote')"
    echo "  GitHub Token: $([ -n "${GITHUB_TOKEN:-}" ] && echo 'Set' || echo 'Not set')"
}

# Main function
main() {
    local mode="${1:-auto}"
    
    echo "🚀 SmartCloudOps AI - Workflow Monitor & Auto-Fix System"
    echo "========================================================"
    echo ""
    
    # Show status
    show_status
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Check GitHub token
    check_github_token
    
    # Set log level
    export LOG_LEVEL="${LOG_LEVEL:-INFO}"
    
    # Run based on mode
    case "$mode" in
        "monitor")
            log "Running in monitor mode..."
            run_workflow_monitor
            ;;
        "fix")
            log "Running in fix mode..."
            run_workflow_fixer
            ;;
        "complete")
            log "Running in complete mode..."
            run_complete_fix_cycle
            ;;
        "auto")
            log "Running in automatic mode..."
            if run_workflow_monitor; then
                log_success "No issues found, workflows are healthy"
            else
                log_warning "Issues found, running fixer..."
                if run_workflow_fixer; then
                    log_success "Issues fixed successfully"
                else
                    log_warning "Some issues could not be auto-fixed"
                    log "Running complete fix cycle..."
                    run_complete_fix_cycle
                fi
            fi
            ;;
        "help"|"-h"|"--help")
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown mode: $mode"
            show_usage
            exit 1
            ;;
    esac
    
    # Check for generated reports
    if [ -f workflow_monitor_report_*.json ] || [ -f workflow_fix_report_*.json ]; then
        log "Reports generated:"
        ls -la workflow_*_report_*.json 2>/dev/null || true
    fi
    
    log_success "Workflow monitoring session completed"
}

# Run main function with all arguments
main "$@"