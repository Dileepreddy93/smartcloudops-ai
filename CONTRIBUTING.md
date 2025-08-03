# Contributing to SmartCloudOps AI

We love your input! We want to make contributing to SmartCloudOps AI as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## 🚀 Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### Branch Strategy
- `main` - Stable releases, production-ready code
- `dev` - Development integration branch
- `feature/*` - Feature development branches
- `hotfix/*` - Critical bug fixes

## 📋 Current Development Priorities

### **Phase 2** - ChatOps Development (In Progress)
- [ ] Complete GPT integration in Flask app
- [ ] Implement natural language query processing
- [ ] Add comprehensive error handling
- [ ] Create GitHub Actions CI/CD pipeline

### **Phase 3** - ML Anomaly Detection (Next)
- [ ] Implement Isolation Forest algorithm
- [ ] Create data pipeline from Prometheus metrics
- [ ] Model training and validation scripts
- [ ] Real-time inference engine

### **Phase 4** - Auto-Remediation (Upcoming)
- [ ] Rule engine for trigger conditions
- [ ] Remediation scripts (restart, scale, etc.)
- [ ] Audit logging and compliance
- [ ] Safety mechanisms and rollback

## 🛠️ Development Setup

### Prerequisites
- Python 3.10+
- Terraform 1.0+
- AWS CLI
- Docker
- Git

### Local Development
```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/smartcloudops-ai.git
cd smartcloudops-ai

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r app/requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# 4. Set up pre-commit hooks
pre-commit install

# 5. Run tests
pytest tests/

# 6. Start development server
cd app
python main.py
```

### Infrastructure Testing
```bash
# Test Terraform configuration
cd terraform
terraform fmt
terraform validate
terraform plan -var-file="terraform-free-tier.tfvars"
```

## 📝 Pull Request Process

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Write clear, readable code
- Add tests for new functionality
- Update documentation as needed
- Follow the coding standards below

### 3. Test Your Changes
```bash
# Run all tests
pytest tests/

# Test Terraform
terraform validate

# Check code formatting
black app/
flake8 app/

# Security scan
bandit -r app/
```

### 4. Submit Pull Request
- Use a clear and descriptive title
- Reference any related issues
- Include screenshots for UI changes
- Provide a detailed description of changes

### Pull Request Template
```markdown
## Description
Brief description of what this PR does.

## Related Issue
Fixes #(issue_number)

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Manual testing completed

## Screenshots (if applicable)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No security vulnerabilities introduced
```

## 🎨 Coding Standards

### Python (Flask App)
```python
# Use Black for formatting
black app/

# Follow PEP 8
# Use type hints
def process_query(query: str) -> dict:
    """Process a ChatOps query and return response."""
    return {"response": f"Processed: {query}"}

# Use docstrings
def anomaly_detection(metrics: list) -> bool:
    """
    Detect anomalies in system metrics.
    
    Args:
        metrics: List of metric values
        
    Returns:
        True if anomaly detected, False otherwise
    """
    pass
```

### Terraform (Infrastructure)
```hcl
# Use consistent naming
resource "aws_instance" "monitoring" {
  # Use variables for configuration
  instance_type = var.ec2_instance_type
  
  # Always add tags
  tags = {
    Name = "${var.project_name}-monitoring"
    Type = "monitoring"
  }
}

# Comment complex logic
# Security group for monitoring instance
# Allows Grafana (3000) and Prometheus (9090) access
resource "aws_security_group" "monitoring" {
  # Configuration here
}
```

### Documentation
- Use clear, concise language
- Include code examples
- Update README.md for significant changes
- Add inline comments for complex logic

## 🐛 Bug Reports

Use GitHub Issues to report bugs. Great bug reports include:

### Template
```markdown
**Bug Description**
A clear and concise description of the bug.

**Reproduction Steps**
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment**
- OS: [e.g. Ubuntu 20.04]
- Python Version: [e.g. 3.10.2]
- Terraform Version: [e.g. 1.12.2]
- AWS Region: [e.g. us-east-1]

**Additional Context**
Any other context about the problem.
```

## 💡 Feature Requests

We love feature ideas! Use GitHub Issues with the "enhancement" label.

### Template
```markdown
**Feature Description**
A clear and concise description of what you want to happen.

**Problem Statement**
What problem does this solve? What's the current pain point?

**Proposed Solution**
Describe your ideal solution.

**Alternatives Considered**
Any alternative solutions or features you've considered.

**Additional Context**
Screenshots, mockups, or examples.
```

## 🏷️ Issue Labels

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements to documentation
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention is needed
- `phase-1`, `phase-2`, etc. - Phase-specific work
- `priority-high` - Critical issues
- `priority-low` - Nice to have

## 🧪 Testing Guidelines

### Unit Tests
```python
# tests/test_app.py
import pytest
from app.main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert b'healthy' in response.data
```

### Integration Tests
```python
# tests/test_integration.py
def test_prometheus_metrics():
    """Test Prometheus metrics collection."""
    # Test actual metrics endpoint
    pass

def test_s3_connectivity():
    """Test S3 bucket access."""
    # Test actual S3 operations
    pass
```

### Infrastructure Tests
```bash
# Test Terraform deployment
terraform plan -out=test.plan
terraform apply test.plan
# Run validation tests
terraform destroy -auto-approve
```

## 🔒 Security Guidelines

### Reporting Security Issues
- **DO NOT** create public GitHub issues for security vulnerabilities
- Email security issues to: security@smartcloudops-ai.com
- Include detailed steps to reproduce
- Allow us 90 days to address before public disclosure

### Security Best Practices
```python
# Never commit secrets
# Use environment variables
import os
api_key = os.getenv('OPENAI_API_KEY')

# Validate inputs
def sanitize_query(query: str) -> str:
    """Sanitize user input to prevent injection."""
    # Remove dangerous characters
    return re.sub(r'[<>\"\'&]', '', query)

# Use parameterized queries
# Never use string concatenation for SQL
```

### AWS Security
```hcl
# Use least privilege IAM policies
resource "aws_iam_policy" "ec2_policy" {
  policy = jsonencode({
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",  # Only specific actions needed
          "s3:PutObject"
        ]
        Resource = [
          aws_s3_bucket.logs.arn,
          "${aws_s3_bucket.logs.arn}/*"
        ]
      }
    ]
  })
}
```

## 📦 Release Process

### Versioning
We use [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- `1.0.0` - Phase 1 complete (Infrastructure)
- `2.0.0` - Phase 2 complete (ChatOps)
- `3.0.0` - Phase 3 complete (ML)

### Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Security scan completed
- [ ] Performance testing done
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Git tag created

## 🎓 Learning Resources

### Getting Started
- [Terraform Tutorial](https://learn.hashicorp.com/terraform)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [AWS Free Tier Guide](https://aws.amazon.com/free/)
- [Prometheus Documentation](https://prometheus.io/docs/)

### Advanced Topics
- [Machine Learning for DevOps](https://github.com/awesome-mlops/awesome-mlops)
- [ChatOps Best Practices](https://github.com/exAspArk/awesome-chatops)
- [Infrastructure as Code](https://www.terraform.io/docs/)

## 🤝 Code of Conduct

### Our Pledge
We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards
Examples of behavior that contributes to creating a positive environment include:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Enforcement
Report unacceptable behavior to: conduct@smartcloudops-ai.com

## 📞 Getting Help

### Community Support
- 💬 [GitHub Discussions](https://github.com/Dileepreddy93/smartcloudops-ai/discussions)
- 🐛 [GitHub Issues](https://github.com/Dileepreddy93/smartcloudops-ai/issues)
- 📧 Email: help@smartcloudops-ai.com

### Documentation
- 📖 [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current progress
- 🚀 [FREE_TIER_DEPLOYMENT.md](terraform/FREE_TIER_DEPLOYMENT.md) - Deployment
- 🏗️ [Architecture Documentation](docs/)

## 🎉 Recognition

Contributors will be recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- Project documentation
- Annual contributor appreciation

Thank you for contributing to SmartCloudOps AI! 🚀
