#!/bin/bash

# MCP Orchestrator AI - Runner Script
# ===================================
# This script sets up the environment and runs the MCP Orchestrator AI
# for monitoring and auto-fixing GitHub Actions workflows.

set -e  # Exit on any error

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check environment variables
check_env_vars() {
    print_status "Checking environment variables..."
    
    if [ -z "$GITHUB_TOKEN" ]; then
        print_error "GITHUB_TOKEN environment variable is not set"
        print_status "Please set it with: export GITHUB_TOKEN='your_token'"
        exit 1
    fi
    
    if [ -z "$GITHUB_REPOSITORY_OWNER" ]; then
        print_warning "GITHUB_REPOSITORY_OWNER not set, using default: Dileepreddy93"
        export GITHUB_REPOSITORY_OWNER="Dileepreddy93"
    fi
    
    if [ -z "$GITHUB_REPOSITORY_NAME" ]; then
        print_warning "GITHUB_REPOSITORY_NAME not set, using default: smartcloudops-ai"
        export GITHUB_REPOSITORY_NAME="smartcloudops-ai"
    fi
    
    print_success "Environment variables configured"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if ! command_exists python3; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_status "Python version: $PYTHON_VERSION"
    
    # Check GitHub CLI
    if ! command_exists gh; then
        print_warning "GitHub CLI (gh) is not installed"
        print_status "Installing GitHub CLI..."
        
        # Install GitHub CLI
        if command_exists curl; then
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
            sudo apt update
            sudo apt install gh -y
        else
            print_error "curl is not installed. Please install GitHub CLI manually."
            exit 1
        fi
    fi
    
    # Check if we're in a git repository
    if [ ! -d ".git" ]; then
        print_error "Not in a git repository. Please run this script from the repository root."
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
}

# Function to install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Check if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
    else
        # Install minimal dependencies
        pip3 install requests pyyaml python-dotenv
    fi
    
    print_success "Python dependencies installed"
}

# Function to authenticate GitHub CLI
authenticate_github() {
    print_status "Authenticating GitHub CLI..."
    
    # Check if already authenticated
    if gh auth status >/dev/null 2>&1; then
        print_success "GitHub CLI already authenticated"
        return
    fi
    
    # Authenticate with token
    echo "$GITHUB_TOKEN" | gh auth login --with-token
    
    if gh auth status >/dev/null 2>&1; then
        print_success "GitHub CLI authenticated successfully"
    else
        print_error "Failed to authenticate GitHub CLI"
        exit 1
    fi
}

# Function to run tests
run_tests() {
    print_status "Running MCP Orchestrator tests..."
    
    if [ -f "scripts/test_mcp_orchestrator.py" ]; then
        python3 scripts/test_mcp_orchestrator.py
        if [ $? -eq 0 ]; then
            print_success "Tests passed"
        else
            print_warning "Tests failed, but continuing..."
        fi
    else
        print_warning "Test script not found, skipping tests"
    fi
}

# Function to run the orchestrator
run_orchestrator() {
    print_status "Starting MCP Orchestrator AI..."
    print_status "Repository: $GITHUB_REPOSITORY_OWNER/$GITHUB_REPOSITORY_NAME"
    print_status "Max retries: ${MAX_RETRIES:-5}"
    
    # Set max retries if provided
    if [ ! -z "$MAX_RETRIES" ]; then
        export MAX_RETRIES="$MAX_RETRIES"
    fi
    
    # Run the orchestrator
    python3 scripts/mcp_orchestrator.py
    
    if [ $? -eq 0 ]; then
        print_success "MCP Orchestrator completed successfully"
    else
        print_error "MCP Orchestrator failed"
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "MCP Orchestrator AI - Runner Script"
    echo "==================================="
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -t, --test          Run tests only"
    echo "  -r, --retries N     Set maximum retry attempts (default: 5)"
    echo "  -v, --verbose       Enable verbose output"
    echo ""
    echo "Environment Variables:"
    echo "  GITHUB_TOKEN              GitHub personal access token (required)"
    echo "  GITHUB_REPOSITORY_OWNER   Repository owner (default: Dileepreddy93)"
    echo "  GITHUB_REPOSITORY_NAME    Repository name (default: smartcloudops-ai)"
    echo "  MAX_RETRIES               Maximum retry attempts (default: 5)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run with defaults"
    echo "  $0 --test                             # Run tests only"
    echo "  $0 --retries 10                       # Run with 10 max retries"
    echo "  MAX_RETRIES=10 $0                     # Set retries via environment"
    echo ""
}

# Main function
main() {
    echo "🚀 MCP Orchestrator AI - Workflow Monitor & Auto-Fix"
    echo "=================================================="
    echo ""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -t|--test)
                TEST_ONLY=true
                shift
                ;;
            -r|--retries)
                MAX_RETRIES="$2"
                shift 2
                ;;
            -v|--verbose)
                set -x
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Check environment variables
    check_env_vars
    
    # Check prerequisites
    check_prerequisites
    
    # Install dependencies
    install_dependencies
    
    # Authenticate GitHub CLI
    authenticate_github
    
    # Run tests if requested or if not test-only mode
    if [ "$TEST_ONLY" = true ]; then
        run_tests
        exit 0
    else
        run_tests
    fi
    
    # Run the orchestrator
    run_orchestrator
    
    echo ""
    print_success "MCP Orchestrator AI execution completed!"
    echo ""
    echo "📊 Check the following files for results:"
    echo "  - mcp_orchestrator_success_report.json (if successful)"
    echo "  - mcp_orchestrator_failure_report.json (if failed)"
    echo "  - mcp_orchestrator.log (detailed logs)"
    echo ""
}

# Run main function with all arguments
main "$@"
