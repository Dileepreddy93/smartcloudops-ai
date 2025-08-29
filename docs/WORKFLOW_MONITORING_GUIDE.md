# 🔍 SmartCloudOps AI - Workflow Monitoring & Auto-Fix System

## 📋 Overview

The SmartCloudOps AI Workflow Monitoring & Auto-Fix System is a comprehensive solution that continuously monitors GitHub Actions workflows, detects issues, and automatically fixes common problems to ensure all workflows pass successfully.

## 🚀 Features

### ✅ Core Capabilities
- **Real-time Workflow Monitoring**: Continuously monitors GitHub Actions workflows
- **Automatic Issue Detection**: Identifies common workflow failures and issues
- **Intelligent Auto-Fixing**: Automatically resolves fixable issues
- **Multi-Stage Resolution**: Progressive fix application with retry logic
- **Comprehensive Reporting**: Detailed reports and analytics
- **GitHub Integration**: Seamless integration with GitHub API

### 🔧 Auto-Fix Capabilities
- **Dependency Issues**: Missing Python/Node.js packages
- **Workflow Configuration**: YAML syntax errors, missing fields
- **Deprecated Actions**: Updates outdated GitHub Actions
- **Security Issues**: Missing permissions, hardcoded secrets
- **Performance Issues**: Missing caching, outdated versions
- **Test Environment**: Environment variables, test configuration
- **Code Quality**: Formatting, linting issues

## 📁 System Components

### 1. **Workflow Monitor** (`scripts/workflow_monitor.py`)
- Monitors GitHub Actions workflows via API
- Analyzes workflow logs for error patterns
- Detects and classifies issues by severity
- Generates comprehensive monitoring reports

### 2. **Workflow Fixer** (`scripts/auto_workflow_fixer.py`)
- Analyzes workflow YAML files for issues
- Applies automatic fixes for common problems
- Updates deprecated GitHub Actions
- Validates workflow configurations

### 3. **Complete Fix Cycle** (`scripts/fix_all_workflow_issues.py`)
- Runs comprehensive monitoring and fixing
- Implements retry logic with exponential backoff
- Handles complex multi-step fixes
- Ensures all workflows pass before completion

### 4. **GitHub Actions Workflow** (`.github/workflows/workflow-monitor.yml`)
- Automated monitoring every 6 hours
- Triggers on workflow failures
- Creates issues for persistent problems
- Provides notifications and reporting

### 5. **Runner Script** (`scripts/run_workflow_monitor.sh`)
- Easy-to-use command-line interface
- Multiple operation modes
- Prerequisites checking
- Status reporting

## 🛠️ Installation & Setup

### Prerequisites
```bash
# Required software
- Python 3.11+
- Node.js 18+
- Git
- GitHub API token

# Required Python packages
pip install requests pyyaml python-dotenv
```

### Environment Variables
```bash
# Required for full functionality
export GITHUB_TOKEN="your-github-token"

# Optional
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
export GITHUB_REPOSITORY_OWNER="your-username"
export GITHUB_REPOSITORY_NAME="smartcloudops-ai"
```

### GitHub Token Setup
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with `repo` and `workflow` permissions
3. Set the token as environment variable: `export GITHUB_TOKEN="your-token"`

## 🚀 Usage

### Quick Start
```bash
# Run the complete monitoring and fixing system
./scripts/run_workflow_monitor.sh

# Or run individual components
python scripts/workflow_monitor.py
python scripts/auto_workflow_fixer.py
python scripts/fix_all_workflow_issues.py
```

### Command Line Options
```bash
# Different operation modes
./scripts/run_workflow_monitor.sh monitor    # Monitoring only
./scripts/run_workflow_monitor.sh fix        # Fixing only
./scripts/run_workflow_monitor.sh complete   # Complete cycle
./scripts/run_workflow_monitor.sh auto       # Automatic mode (default)
./scripts/run_workflow_monitor.sh help       # Show help
```

### GitHub Actions Integration
The system automatically runs via GitHub Actions:
- **Scheduled**: Every 6 hours
- **On Failure**: When other workflows fail
- **Manual**: Via workflow dispatch

## 📊 Monitoring & Reports

### Generated Reports
- `workflow_monitor_report_YYYYMMDD_HHMMSS.json` - Monitoring results
- `workflow_fix_report_YYYYMMDD_HHMMSS.json` - Fix application results
- `workflow_fix_complete_report_YYYYMMDD_HHMMSS.json` - Complete cycle results

### Report Structure
```json
{
  "timestamp": "2024-12-XX...",
  "total_issues": 5,
  "fixed_issues": 3,
  "remaining_issues": 2,
  "issues_by_severity": {
    "critical": 1,
    "high": 2,
    "medium": 1,
    "low": 1
  },
  "issues_by_type": {
    "deprecated_action": 2,
    "missing_cache": 1,
    "yaml_syntax_error": 1
  },
  "recommendations": [
    "Address critical issues manually",
    "Review 2 remaining issues"
  ]
}
```

## 🔍 Issue Detection

### Common Issue Types

#### 1. **Dependency Issues**
- Missing Python packages
- Missing npm packages
- Outdated dependencies
- Version conflicts

#### 2. **Workflow Configuration Issues**
- YAML syntax errors
- Missing required fields
- Invalid workflow structure
- Deprecated GitHub Actions

#### 3. **Security Issues**
- Hardcoded secrets
- Missing permissions
- Insecure configurations
- Vulnerable dependencies

#### 4. **Performance Issues**
- Missing caching
- Outdated runtime versions
- Inefficient configurations
- Resource limitations

#### 5. **Test Environment Issues**
- Missing environment variables
- Incorrect test configuration
- Database connection issues
- Service dependencies

## 🔧 Auto-Fix Capabilities

### Automatic Fixes Applied

#### 1. **Dependency Management**
```bash
# Python dependencies
pip install missing-package

# Node.js dependencies
npm install missing-package

# Update outdated packages
pip install --upgrade package-name
```

#### 2. **Workflow File Updates**
```yaml
# Add missing workflow name
name: "Workflow Name"

# Add default triggers
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

# Add permissions
permissions:
  contents: read
  pull-requests: write
  issues: write
```

#### 3. **GitHub Actions Updates**
```yaml
# Update deprecated actions
- uses: actions/checkout@v4  # Was v1, v2, v3
- uses: actions/setup-python@v5  # Was v1, v2, v3, v4
- uses: actions/setup-node@v4  # Was v1, v2, v3
```

#### 4. **Caching Configuration**
```yaml
# Add pip caching
- name: Cache pip dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

# Add npm caching
- name: Cache npm dependencies
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
```

## 📈 Monitoring Dashboard

### Status Indicators
- 🟢 **Healthy**: All workflows passing
- 🟡 **Warning**: Some issues detected, auto-fixing
- 🔴 **Critical**: Manual intervention required
- ⚫ **Unknown**: Unable to determine status

### Metrics Tracked
- Total workflow runs
- Success/failure rates
- Issue detection accuracy
- Auto-fix success rate
- Resolution time
- Retry attempts

## 🚨 Alerting & Notifications

### Automatic Notifications
- **GitHub Issues**: Created for persistent failures
- **PR Comments**: Notifications on workflow resolution
- **Email Alerts**: For critical issues (if configured)
- **Slack/Teams**: Integration support (if configured)

### Alert Levels
- **Info**: Workflow monitoring completed
- **Warning**: Issues detected, auto-fixing in progress
- **Error**: Auto-fix failed, manual intervention needed
- **Critical**: System-wide workflow failures

## 🔄 Retry Logic

### Exponential Backoff
```python
# Retry configuration
max_retries = 10
base_delay = 60  # seconds
delay = base_delay * (2 ** retry_count)
```

### Retry Conditions
- Workflow failures
- Network issues
- Temporary GitHub API errors
- Dependency installation failures

## 🛡️ Security Considerations

### Token Security
- Use minimal required permissions
- Rotate tokens regularly
- Store tokens securely
- Monitor token usage

### Code Security
- Validate all inputs
- Sanitize workflow files
- Prevent code injection
- Audit auto-fixes

### Access Control
- Limit auto-fix permissions
- Review changes before commit
- Monitor system access
- Log all operations

## 📝 Troubleshooting

### Common Issues

#### 1. **GitHub Token Issues**
```bash
# Check token permissions
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user

# Verify repository access
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/owner/repo
```

#### 2. **Python Dependencies**
```bash
# Install missing packages
pip install -r app/requirements.txt
pip install requests pyyaml python-dotenv

# Check Python version
python3 --version
```

#### 3. **Workflow Validation**
```bash
# Validate workflow files
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci-cd.yml'))"

# Check GitHub Actions syntax
# Use GitHub's workflow validator in the web interface
```

#### 4. **Permission Issues**
```bash
# Check git permissions
git status
git remote -v

# Verify GitHub token permissions
# Ensure token has 'repo' and 'workflow' scopes
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL="DEBUG"
./scripts/run_workflow_monitor.sh

# Check log files
tail -f workflow_monitor.log
tail -f workflow_fixer.log
```

## 🔮 Future Enhancements

### Planned Features
- **Machine Learning**: Predictive issue detection
- **Advanced Analytics**: Detailed performance metrics
- **Custom Rules**: User-defined fix patterns
- **Integration APIs**: Third-party service integration
- **Web Dashboard**: Real-time monitoring interface
- **Mobile Notifications**: Push notifications for critical issues

### Extensibility
- **Plugin System**: Custom fix modules
- **Rule Engine**: Configurable detection rules
- **API Endpoints**: REST API for external integration
- **Webhooks**: Real-time event notifications

## 📚 API Reference

### WorkflowMonitor Class
```python
monitor = WorkflowMonitor(github_token, repo_owner, repo_name)
status = monitor.get_workflow_status()
issues = monitor.analyze_workflow_logs(logs)
report = monitor.run_monitoring_cycle()
```

### WorkflowFixer Class
```python
fixer = WorkflowFixer()
issues = fixer.analyze_workflows()
fixes = fixer.apply_fixes(issues)
report = fixer.generate_report(issues, fixes)
```

### CompleteWorkflowFixer Class
```python
fixer = CompleteWorkflowFixer(github_token, repo_owner, repo_name)
success = fixer.monitor_and_fix_until_success()
report = fixer.generate_final_report(success)
```

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone https://github.com/your-username/smartcloudops-ai.git
cd smartcloudops-ai

# Install development dependencies
pip install -r app/requirements.txt
pip install pytest black flake8 mypy

# Run tests
pytest tests/

# Format code
black scripts/
isort scripts/
```

### Adding New Fix Types
1. Add detection pattern in `analyze_workflow_logs()`
2. Implement fix logic in `auto_fix_issues()`
3. Add tests for new fix type
4. Update documentation

### Reporting Issues
- Use GitHub Issues for bug reports
- Include logs and error messages
- Provide reproduction steps
- Specify environment details

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- GitHub Actions team for the excellent CI/CD platform
- Python community for the robust ecosystem
- Open source contributors for inspiration and tools

---

**🎉 Happy Workflow Monitoring!**

For support and questions, please open an issue on GitHub or contact the development team.
