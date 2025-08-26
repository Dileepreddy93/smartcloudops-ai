# 🔍 GitHub Workflow Monitoring & Auto-Fixing Guide

## 📋 Overview

This guide provides comprehensive tools and instructions for monitoring your GitHub workflows, detecting failures, and automatically fixing common issues.

## 🛠️ Available Tools

### 1. **Quick Status Checker**
```bash
./scripts/quick_status.sh
```
- **Purpose**: Fast overview of recent workflow runs
- **Output**: Shows last 3 workflows with status and timestamps
- **Best for**: Quick status checks

### 2. **Simple Workflow Monitor**
```bash
python scripts/simple_workflow_monitor.py
```
- **Purpose**: Check local issues and auto-fix common problems
- **Features**: 
  - Detects formatting, linting, type checking, and test issues
  - Automatically applies fixes
  - Commits and pushes changes
- **Best for**: Proactive issue prevention

### 3. **Continuous Monitoring**
```bash
python scripts/simple_workflow_monitor.py monitor
```
- **Purpose**: Continuous monitoring with auto-refresh
- **Features**: Runs every 5 minutes, auto-fixes issues
- **Best for**: Long-term monitoring and maintenance

### 4. **Advanced Workflow Monitor**
```bash
python scripts/auto_workflow_fixer.py
```
- **Purpose**: Advanced monitoring with detailed analysis
- **Features**: 
  - Analyzes workflow logs
  - Detailed failure pattern recognition
  - Comprehensive reporting
- **Best for**: Deep debugging and analysis

## 📦 Required Dependencies

### Python Dependencies
```bash
pip install -r scripts/requirements_monitor.txt
```

**Included packages:**
- `requests>=2.31.0` - HTTP requests for GitHub API
- `black>=23.0.0` - Code formatting
- `ruff>=0.1.0` - Linting and auto-fixing
- `mypy>=1.5.0` - Type checking
- `bandit>=1.7.5` - Security scanning
- `pytest>=7.4.0` - Testing
- `types-requests>=2.31.0` - Type stubs
- `types-PyYAML>=6.0.12` - Type stubs

### System Dependencies
```bash
# Install jq for JSON processing
sudo apt-get install jq  # Ubuntu/Debian
sudo yum install jq      # CentOS/RHEL
brew install jq          # macOS

# Install curl (usually pre-installed)
sudo apt-get install curl  # Ubuntu/Debian
sudo yum install curl      # CentOS/RHEL
```

### Setup Script
```bash
chmod +x scripts/setup_monitor.sh
./scripts/setup_monitor.sh
```

## 🔧 Auto-Fixing Capabilities

### Issues Automatically Fixed

1. **Code Formatting (Black)**
   - Detects: `would reformat` errors
   - Fix: Applies Black formatting to all Python files
   - Files: `app/`, `scripts/`, `tests/`

2. **Linting (Ruff)**
   - Detects: Linting errors and warnings
   - Fix: Applies auto-fixes with `--fix --unsafe-fixes`
   - Coverage: All Python files

3. **Type Checking (MyPy)**
   - Detects: Type annotation errors
   - Fix: Installs missing type stubs
   - Dependencies: `types-requests`, `types-PyYAML`

4. **Security (Bandit)**
   - Detects: High-severity security issues
   - Fix: Reports issues for manual review
   - Configuration: `--severity-level high`

5. **Test Failures (pytest)**
   - Detects: Failed test cases
   - Fix: Runs tests with verbose output for debugging
   - Coverage: All test files

## 📊 Monitoring Workflows

### Workflow Status Types

- **✅ SUCCESS**: All jobs completed successfully
- **❌ FAILED**: One or more jobs failed
- **🔄 RUNNING**: Workflow is currently executing
- **⏳ QUEUED**: Workflow is waiting to start
- **⏹️ CANCELLED**: Workflow was cancelled

### Common Failure Patterns

1. **Code Quality Issues**
   ```
   Black formatting issues detected
   Ruff linting errors found
   MyPy type checking errors
   ```

2. **Dependency Issues**
   ```
   ModuleNotFoundError: No module named 'openai'
   ImportError: cannot import name 'X'
   ```

3. **Test Failures**
   ```
   pytest FAILED
   AssertionError
   ```

4. **Security Issues**
   ```
   Bandit found X issues
   High severity security warnings
   ```

## 🚀 Usage Examples

### Basic Monitoring
```bash
# Quick status check
./scripts/quick_status.sh

# Single monitoring run
python scripts/simple_workflow_monitor.py
```

### Continuous Monitoring
```bash
# Start continuous monitoring
python scripts/simple_workflow_monitor.py monitor

# Stop monitoring (Ctrl+C)
```

### Advanced Monitoring
```bash
# Detailed analysis
python scripts/auto_workflow_fixer.py

# Continuous advanced monitoring
python scripts/auto_workflow_fixer.py monitor
```

## 📈 Monitoring Reports

### Generated Files

1. **`workflow_monitor.log`**
   - Detailed logging of all monitoring activities
   - Timestamps and error details

2. **`workflow_monitor_report.json`**
   - JSON report with statistics
   - Fixes applied and issues found

3. **Console Output**
   - Real-time status updates
   - Color-coded success/failure indicators

### Report Structure
```json
{
  "timestamp": "2025-08-26T14:53:30.953",
  "fixes_applied": ["black_formatting", "ruff_linting"],
  "issues_found": ["Type checking errors detected"],
  "summary": {
    "total_fixes": 2,
    "total_issues": 1,
    "success_rate": 0.67
  }
}
```

## 🔍 Troubleshooting

### Common Issues

1. **Git Push Rejected**
   ```bash
   # Solution: Pull latest changes first
   git pull --rebase origin main
   git push origin main
   ```

2. **Permission Denied**
   ```bash
   # Solution: Make scripts executable
   chmod +x scripts/*.py scripts/*.sh
   ```

3. **Missing Dependencies**
   ```bash
   # Solution: Install monitoring dependencies
   pip install -r scripts/requirements_monitor.txt
   ```

4. **API Rate Limits**
   - GitHub API has rate limits for unauthenticated requests
   - Consider using GitHub token for higher limits

### Manual Fixes

If auto-fixing fails, you can run fixes manually:

```bash
# Format code
black app/ scripts/ tests/

# Fix linting
ruff check app/ scripts/ tests/ --fix --unsafe-fixes

# Install type stubs
pip install types-requests types-PyYAML

# Run tests
python -m pytest tests/ -v

# Security scan
bandit -r app/ --severity-level high
```

## 🎯 Best Practices

### 1. **Regular Monitoring**
- Run monitoring tools before pushing changes
- Use continuous monitoring for active development
- Check status after each workflow run

### 2. **Proactive Fixing**
- Fix issues locally before they reach CI/CD
- Use pre-commit hooks for automatic checks
- Maintain consistent code quality standards

### 3. **Documentation**
- Keep monitoring reports for analysis
- Document manual fixes for future reference
- Update this guide with new patterns

### 4. **Security**
- Review security scan results manually
- Don't auto-fix high-severity security issues
- Keep dependencies updated

## 📞 Support

### Getting Help

1. **Check Logs**: Review `workflow_monitor.log` for detailed error information
2. **Manual Testing**: Run individual tools to isolate issues
3. **GitHub Issues**: Check workflow logs on GitHub for additional context

### Contributing

To improve the monitoring system:

1. Add new failure patterns to `analyze_failure()` method
2. Implement new fix methods for specific issues
3. Update this documentation with new features
4. Test thoroughly before deploying

---

## 🎉 Quick Start Checklist

- [ ] Install dependencies: `pip install -r scripts/requirements_monitor.txt`
- [ ] Make scripts executable: `chmod +x scripts/*.py scripts/*.sh`
- [ ] Test quick status: `./scripts/quick_status.sh`
- [ ] Run initial monitoring: `python scripts/simple_workflow_monitor.py`
- [ ] Set up continuous monitoring: `python scripts/simple_workflow_monitor.py monitor`

**You're now ready to monitor and auto-fix your GitHub workflows! 🚀**
