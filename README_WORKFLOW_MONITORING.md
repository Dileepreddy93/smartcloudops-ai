# 🔍 SmartCloudOps AI - Workflow Monitoring & Auto-Fix System

## 🎯 Overview

The SmartCloudOps AI Workflow Monitoring & Auto-Fix System is a comprehensive solution that continuously monitors GitHub Actions workflows, detects issues, and automatically fixes common problems to ensure all workflows pass successfully.

## 🚀 Quick Start

### 1. Run the Demo
```bash
# See the system in action without setup
python3 scripts/demo_workflow_monitor.py
```

### 2. Basic Usage
```bash
# Run the complete monitoring system
./scripts/run_workflow_monitor.sh

# Or run individual components
python3 scripts/workflow_monitor.py
python3 scripts/auto_workflow_fixer.py
python3 scripts/fix_all_workflow_issues.py
```

### 3. GitHub Actions Integration
The system automatically runs via GitHub Actions:
- **Scheduled**: Every 6 hours
- **On Failure**: When other workflows fail
- **Manual**: Via workflow dispatch

## 📁 System Components

| Component | File | Purpose |
|-----------|------|---------|
| **Workflow Monitor** | `scripts/workflow_monitor.py` | Monitors workflows via GitHub API |
| **Workflow Fixer** | `scripts/auto_workflow_fixer.py` | Fixes workflow YAML issues |
| **Complete Fixer** | `scripts/fix_all_workflow_issues.py` | Full monitoring and fixing cycle |
| **Runner Script** | `scripts/run_workflow_monitor.sh` | Easy-to-use command-line interface |
| **GitHub Action** | `.github/workflows/workflow-monitor.yml` | Automated monitoring |
| **Demo Script** | `scripts/demo_workflow_monitor.py` | System demonstration |

## 🔧 Auto-Fix Capabilities

### ✅ Dependency Issues
- Missing Python packages
- Missing npm packages
- Outdated dependencies
- Version conflicts

### ✅ Workflow Configuration
- YAML syntax errors
- Missing required fields
- Deprecated GitHub Actions
- Invalid workflow structure

### ✅ Security Issues
- Hardcoded secrets
- Missing permissions
- Insecure configurations
- Vulnerable dependencies

### ✅ Performance Issues
- Missing caching
- Outdated runtime versions
- Inefficient configurations
- Resource limitations

### ✅ Test Environment
- Missing environment variables
- Incorrect test configuration
- Database connection issues
- Service dependencies

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

## 📊 Usage Examples

### Command Line Options
```bash
# Different operation modes
./scripts/run_workflow_monitor.sh monitor    # Monitoring only
./scripts/run_workflow_monitor.sh fix        # Fixing only
./scripts/run_workflow_monitor.sh complete   # Complete cycle
./scripts/run_workflow_monitor.sh auto       # Automatic mode (default)
./scripts/run_workflow_monitor.sh help       # Show help
```

### Direct Python Usage
```bash
# Monitor workflows
python3 scripts/workflow_monitor.py

# Fix workflow issues
python3 scripts/auto_workflow_fixer.py

# Complete monitoring and fixing
python3 scripts/fix_all_workflow_issues.py
```

## 📈 Monitoring & Reports

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

#### 1. GitHub Token Issues
```bash
# Check token permissions
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user

# Verify repository access
curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/owner/repo
```

#### 2. Python Dependencies
```bash
# Install missing packages
pip install -r app/requirements.txt
pip install requests pyyaml python-dotenv

# Check Python version
python3 --version
```

#### 3. Workflow Validation
```bash
# Validate workflow files
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci-cd.yml'))"

# Check GitHub Actions syntax
# Use GitHub's workflow validator in the web interface
```

#### 4. Permission Issues
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

## 🎯 Success Metrics

The workflow monitoring system has been designed to achieve:

- **95%+ automatic issue resolution**
- **80% reduction in manual intervention**
- **95% workflow success rate**
- **2-3 hours saved per day** in manual workflow management

## 🚀 Getting Started Checklist

- [ ] Set up GitHub token with appropriate permissions
- [ ] Install required Python packages
- [ ] Run the demo script to verify setup
- [ ] Configure environment variables
- [ ] Test with a simple workflow
- [ ] Review and customize auto-fix rules
- [ ] Set up monitoring schedule
- [ ] Configure alerting preferences

---

**🎉 Happy Workflow Monitoring!**

For support and questions, please open an issue on GitHub or contact the development team.

**📖 For detailed documentation, see [WORKFLOW_MONITORING_GUIDE.md](WORKFLOW_MONITORING_GUIDE.md)**