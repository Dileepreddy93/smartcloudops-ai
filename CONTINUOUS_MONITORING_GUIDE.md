# 🚀 SmartCloudOps AI - Continuous Workflow Monitoring System

## 📋 Overview

The Continuous Workflow Monitoring System automatically monitors GitHub Actions workflows, detects failures, and applies fixes until all workflows pass successfully. This system ensures your CI/CD pipeline remains healthy and automatically resolves common issues.

## ✨ Features

### 🔍 **Automatic Monitoring**
- Real-time workflow status checking
- Configurable check intervals (default: 60 seconds)
- Continuous monitoring until all workflows pass
- Graceful shutdown with signal handling

### 🛠️ **Auto-Fix Capabilities**
- **Missing Dependencies**: Automatically adds missing packages to requirements.txt
- **Import Errors**: Fixes missing function imports
- **Environment Variables**: Sets required environment variables with secure values
- **YAML Syntax**: Fixes workflow file syntax errors
- **Permission Issues**: Detects and reports permission problems
- **Network Errors**: Identifies connectivity issues

### 📊 **Comprehensive Reporting**
- Detailed issue classification and severity assessment
- Auto-fix success/failure tracking
- Real-time monitoring reports
- Final summary with success rates
- JSON and log file outputs

### 🔄 **Retry Logic**
- Configurable maximum retries per issue (default: 5)
- Exponential backoff for failed fixes
- Consecutive pass verification (3 successful checks required)

## 🚀 Quick Start

### 1. **Local Testing (No GitHub Token Required)**

```bash
# Run the test simulation
python3 scripts/test_continuous_monitor.py
```

This demonstrates the system without requiring API access.

### 2. **Local Monitoring (Requires GitHub Token)**

```bash
# Set your GitHub token
export GITHUB_TOKEN="your_github_token_here"

# Run continuous monitoring
./scripts/run_continuous_monitor.sh

# Or with custom settings
./scripts/run_continuous_monitor.sh --interval 30 --max-retries 3 --repo youruser/yourrepo
```

### 3. **GitHub Actions (Automatic)**

The system automatically runs via GitHub Actions:
- **Scheduled**: Every 30 minutes
- **Triggered**: When other workflows fail
- **Manual**: Via workflow dispatch

## 📁 File Structure

```
scripts/
├── continuous_workflow_monitor.py    # Main monitoring system
├── run_continuous_monitor.sh         # Shell script runner
├── test_continuous_monitor.py        # Test simulation
└── workflow_monitor.py              # Original monitor

.github/workflows/
└── continuous-monitor.yml           # GitHub Actions workflow

logs/
├── continuous_workflow_monitor.log   # Main monitoring logs
└── test_continuous_monitor.log      # Test simulation logs

reports/
├── continuous_monitoring_report_*.json    # Iteration reports
└── continuous_monitoring_final_report.json # Final summary
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub personal access token | Required |
| `GITHUB_REPOSITORY_OWNER` | Repository owner | `Dileepreddy93` |
| `GITHUB_REPOSITORY_NAME` | Repository name | `smartcloudops-ai` |
| `CHECK_INTERVAL` | Check interval in seconds | `60` |
| `MAX_RETRIES` | Maximum retries per issue | `5` |

### Command Line Options

```bash
./scripts/run_continuous_monitor.sh [options]

Options:
  --interval SECONDS    Check interval in seconds (default: 60)
  --max-retries N       Maximum retries per issue (default: 5)
  --token TOKEN         GitHub token (or set GITHUB_TOKEN env var)
  --repo OWNER/NAME     Repository in format owner/name
  --help                Show this help message
```

## 🔧 Issue Types and Fixes

### 1. **Missing Dependencies** (`missing_dependency`)
- **Detection**: `ModuleNotFoundError: No module named 'package'`
- **Fix**: Adds missing package to `app/requirements.txt`
- **Severity**: High
- **Auto-fixable**: ✅ Yes

### 2. **Import Errors** (`import_error`)
- **Detection**: `ImportError: cannot import name 'function'`
- **Fix**: Adds missing functions to modules
- **Severity**: High
- **Auto-fixable**: ✅ Yes

### 3. **Missing Environment Variables** (`missing_env_vars`)
- **Detection**: `ValueError: Missing required environment variables`
- **Fix**: Sets secure values in `.env` file
- **Severity**: Critical
- **Auto-fixable**: ✅ Yes

### 4. **YAML Syntax Errors** (`yaml_syntax_error`)
- **Detection**: YAML parsing errors in workflow files
- **Fix**: Corrects syntax issues
- **Severity**: Critical
- **Auto-fixable**: ✅ Yes

### 5. **Permission Errors** (`permission_error`)
- **Detection**: `Permission denied` errors
- **Fix**: Manual investigation required
- **Severity**: Medium
- **Auto-fixable**: ❌ No

### 6. **Network Errors** (`network_error`)
- **Detection**: Connection timeouts and network issues
- **Fix**: Automatic retry with backoff
- **Severity**: Low
- **Auto-fixable**: ❌ No

## 📊 Monitoring Reports

### Iteration Reports
Generated after each monitoring cycle:
```json
{
  "timestamp": "2025-08-28T18:30:00",
  "iteration": 5,
  "total_issues_found": 12,
  "total_fixes_applied": 8,
  "issues_by_type": {
    "missing_dependency": 3,
    "import_error": 2,
    "missing_env_vars": 1
  },
  "fixes_by_type": {
    "missing_dependency": 3,
    "import_error": 2,
    "missing_env_vars": 1
  }
}
```

### Final Report
Generated when monitoring completes:
```json
{
  "monitoring_started": "2025-08-28T18:00:00",
  "monitoring_ended": "2025-08-28T19:15:00",
  "total_iterations": 15,
  "total_issues_found": 25,
  "total_fixes_applied": 22,
  "success_rate": "88.0%",
  "issues": [...],
  "fixes": [...]
}
```

## 🔍 Monitoring Process

### 1. **Initialization**
- Load configuration from environment variables
- Set up GitHub API connection
- Initialize logging and reporting

### 2. **Monitoring Loop**
```
Start → Check Workflow Status → Detect Issues → Apply Fixes → Commit Changes → Wait → Repeat
```

### 3. **Issue Resolution**
- **Auto-fixable Issues**: Apply fixes and commit changes
- **Manual Issues**: Mark for manual intervention
- **Network Issues**: Retry with exponential backoff

### 4. **Success Criteria**
- All workflows passing for 3 consecutive checks
- No critical issues remaining
- Auto-fixes applied successfully

## 🛡️ Security Features

### GitHub Token Security
- Uses GitHub personal access tokens
- Minimal required permissions
- Secure token handling

### Environment Variable Security
- Generates secure random values for secrets
- Uses appropriate key lengths
- Follows security best practices

### Logging Security
- No sensitive data in logs
- Secure error handling
- Audit trail for all actions

## 🚨 Troubleshooting

### Common Issues

#### 1. **GitHub Token Issues**
```bash
# Check token permissions
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# Verify repository access
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/repos/OWNER/REPO
```

#### 2. **Permission Denied**
```bash
# Check file permissions
ls -la scripts/run_continuous_monitor.sh
chmod +x scripts/run_continuous_monitor.sh
```

#### 3. **Missing Dependencies**
```bash
# Install required packages
pip install requests pyyaml python-dotenv
```

#### 4. **Network Issues**
- Check internet connectivity
- Verify GitHub API access
- Review firewall settings

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
./scripts/run_continuous_monitor.sh
```

### Manual Intervention

For issues requiring manual fixes:
1. Check the monitoring reports
2. Review the specific error messages
3. Apply fixes manually
4. Restart monitoring

## 📈 Performance Optimization

### Check Intervals
- **Development**: 30-60 seconds
- **Production**: 2-5 minutes
- **GitHub Actions**: 2 minutes (due to runtime limits)

### Resource Usage
- **Memory**: ~50MB per monitoring cycle
- **CPU**: Minimal impact
- **Network**: API calls every check interval

### Scaling Considerations
- Multiple repositories: Run separate instances
- High-frequency checks: Consider rate limits
- Large repositories: Increase timeout values

## 🔄 Integration with CI/CD

### GitHub Actions Integration
The system integrates seamlessly with existing workflows:

```yaml
# Trigger monitoring when workflows fail
on:
  workflow_run:
    workflows: ["CI/CD Pipeline", "Tests", "Security Scan"]
    types: [completed]
```

### Webhook Integration
For external systems:
```bash
# Webhook endpoint for monitoring status
curl -X POST https://your-webhook-url \
  -H "Content-Type: application/json" \
  -d '{"status": "monitoring_complete", "issues_fixed": 5}'
```

## 📚 API Reference

### ContinuousWorkflowMonitor Class

```python
monitor = ContinuousWorkflowMonitor(
    github_token="your_token",
    repo_owner="owner",
    repo_name="repo",
    check_interval=60,
    max_retries=5
)

# Start monitoring
monitor.run_continuous_monitoring()
```

### Key Methods

- `check_workflow_status()`: Check current workflow status
- `analyze_workflow_failure()`: Analyze failed workflows
- `apply_auto_fix()`: Apply automatic fixes
- `commit_and_push_fixes()`: Commit and push changes
- `generate_monitoring_report()`: Generate reports

## 🤝 Contributing

### Adding New Issue Types

1. Add pattern to `issue_patterns` in `analyze_job_logs()`
2. Implement fix method in `apply_auto_fix()`
3. Add tests for the new issue type
4. Update documentation

### Adding New Fix Methods

```python
def fix_new_issue_type(self, issue: WorkflowIssue) -> bool:
    """Fix new issue type."""
    try:
        # Implementation here
        return True
    except Exception as e:
        logger.error(f"Failed to fix new issue: {e}")
        return False
```

## 📄 License

This project is part of SmartCloudOps AI and follows the same licensing terms.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the monitoring reports
3. Check GitHub Actions logs
4. Create an issue in the repository

---

**🎉 Happy Monitoring!** 

The Continuous Workflow Monitoring System will keep your CI/CD pipeline healthy and automatically resolve common issues, allowing you to focus on development rather than pipeline maintenance.