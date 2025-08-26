# SmartCloudOps AI - CI/CD Pipeline Guide

## 🎯 **Overview**

The SmartCloudOps AI project uses a comprehensive CI/CD pipeline built with GitHub Actions to ensure code quality, security, and reliable deployments. This guide explains the pipeline structure, jobs, and maintenance procedures.

---

## 📊 **Pipeline Architecture**

### **Workflow Files**
- **`.github/workflows/ci-cd.yml`**: Main CI/CD pipeline with matrix testing
- **`.github/workflows/infra.yml`**: Infrastructure validation and deployment
- **`.github/workflows/code-quality.yml`**: Code quality and security checks

### **Pipeline Stages**
1. **Test** - Matrix testing across Python versions and OS
2. **Security** - Comprehensive security scanning
3. **Docker** - Container build and testing
4. **Infrastructure** - Terraform validation and deployment
5. **Deploy** - Production deployment (main branch only)
6. **Notify** - Results notification

---

## 🔧 **Workflow Details**

### **1. Main CI/CD Pipeline (`ci-cd.yml`)**

#### **Triggers**
- Push to `main` and `develop` branches
- Pull requests to `main` and `develop` branches

#### **Jobs**

##### **Test Job (Matrix)**
```yaml
test:
  strategy:
    matrix:
      os: [ubuntu-latest, ubuntu-20.04]
      python-version: ['3.10', '3.11', '3.12']
```

**Features:**
- Matrix testing across 3 Python versions and 2 OS platforms
- Dependency caching for faster builds
- Comprehensive test suite execution
- Artifact upload for test results

**Steps:**
1. **Setup**: Python environment with caching
2. **Install**: Dependencies and testing tools
3. **Lint**: Black formatting and Ruff linting
4. **Security**: Bandit and Safety scans
5. **Test**: Flask application tests
6. **Pytest**: Full test suite execution
7. **Scripts**: Data collection and ML training tests

##### **Security Job**
```yaml
security:
  needs: test
  runs-on: ubuntu-latest
```

**Features:**
- Comprehensive security scanning
- Vulnerability detection and reporting
- JSON report generation
- Failure on critical vulnerabilities

##### **Docker Job**
```yaml
docker:
  needs: [test, security]
  runs-on: ubuntu-latest
```

**Features:**
- Multi-platform Docker builds
- Container health checks
- API endpoint testing
- Log capture on failure

##### **Infrastructure Job**
```yaml
infrastructure:
  needs: [test, security]
  runs-on: ubuntu-latest
```

**Features:**
- Terraform validation
- Security scanning with tfsec
- Format checking
- Configuration validation

##### **Deploy Job**
```yaml
deploy:
  needs: [test, security, docker, infrastructure]
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  environment: production
```

**Features:**
- Production deployment only
- Environment protection
- Deployment notifications
- Success reporting

### **2. Infrastructure Pipeline (`infra.yml`)**

#### **Triggers**
- Changes to `terraform/` directory
- Pull requests with infrastructure changes

#### **Jobs**

##### **Terraform Validation**
```yaml
terraform-validation:
  runs-on: ubuntu-latest
```

**Features:**
- Format checking with `terraform fmt`
- Configuration validation
- Security scanning with tfsec
- PR commenting with results

##### **Terraform Deploy**
```yaml
terraform-deploy:
  needs: terraform-validation
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  environment: production
```

**Features:**
- AWS credentials configuration
- Terraform plan and apply
- Output capture
- Production environment protection

### **3. Code Quality Pipeline (`code-quality.yml`)**

#### **Triggers**
- All pushes and pull requests

#### **Jobs**

##### **Code Quality**
```yaml
code-quality:
  runs-on: ubuntu-latest
```

**Features:**
- Black formatting checks
- Ruff linting
- MyPy type checking
- Bandit security scanning
- Safety dependency checks

##### **Auto-fix**
```yaml
auto-fix:
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

**Features:**
- Automatic code formatting
- Linting fixes
- Auto-commit changes
- Skip CI on auto-fixes

---

## 🔒 **Security Features**

### **Dependency Scanning**
- **Safety**: Checks for known vulnerabilities in Python packages
- **Bandit**: Security linting for Python code
- **tfsec**: Security scanning for Terraform configurations

### **Secret Management**
- AWS credentials stored in GitHub Secrets
- No hardcoded credentials in workflows
- Environment-specific secret handling

### **Permissions**
- Minimal required permissions for each job
- Explicit permission declarations
- Security event write access

---

## 🚀 **Deployment Strategy**

### **Environment Protection**
- Production environment requires approval
- Branch protection rules
- Required status checks

### **Deployment Flow**
1. **Development**: All tests pass on feature branches
2. **Staging**: Automated deployment to staging environment
3. **Production**: Manual approval required for production

### **Rollback Strategy**
- Terraform state management
- Docker image versioning
- Database migration safety

---

## 📈 **Performance Optimizations**

### **Caching Strategy**
```yaml
- name: Cache pip dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('app/requirements.txt') }}
```

### **Matrix Strategy**
- Parallel execution across Python versions
- Fail-fast disabled for comprehensive testing
- OS-specific exclusions

### **Artifact Management**
- Test results uploaded as artifacts
- Security reports preserved
- Docker logs on failure

---

## 🛠 **Maintenance Procedures**

### **Adding New Tests**
1. Add test files to `tests/` directory
2. Update workflow to include new test commands
3. Verify test execution in pipeline

### **Updating Dependencies**
1. Update `app/requirements.txt`
2. Test locally with new dependencies
3. Verify pipeline passes with updates
4. Monitor for security vulnerabilities

### **Modifying Infrastructure**
1. Update Terraform configurations
2. Test with `terraform plan`
3. Verify pipeline validation passes
4. Deploy to staging first

### **Adding New Jobs**
1. Define job requirements and dependencies
2. Add appropriate triggers
3. Configure permissions
4. Test locally if possible

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Test Failures**
```bash
# Local testing
python -m pytest tests/ -v
python -m black --check app/
python -m ruff check app/
```

#### **Docker Build Failures**
```bash
# Local Docker testing
docker build -t smartcloudops-ai .
docker run -p 5000:5000 smartcloudops-ai
curl http://localhost:5000/health
```

#### **Terraform Issues**
```bash
# Local Terraform testing
cd terraform
terraform init
terraform validate
terraform plan
```

### **Debugging Workflows**
1. Check workflow logs in GitHub Actions
2. Download artifacts for detailed reports
3. Test locally with same environment
4. Verify secret configuration

---

## 📋 **Required Secrets**

### **AWS Credentials**
- `AWS_ACCESS_KEY_ID`: AWS access key for Terraform
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for Terraform

### **GitHub Token**
- `GITHUB_TOKEN`: Automatically provided by GitHub

### **Environment Variables**
- Configure in repository settings
- Use environment-specific values
- Rotate credentials regularly

---

## 🎯 **Best Practices**

### **Code Quality**
- Run linting locally before pushing
- Use pre-commit hooks for formatting
- Review security scan results
- Address all linting warnings

### **Testing**
- Write comprehensive unit tests
- Test edge cases and error conditions
- Maintain high test coverage
- Use realistic test data

### **Security**
- Regular dependency updates
- Security scan monitoring
- Secret rotation
- Access control review

### **Deployment**
- Use semantic versioning
- Document breaking changes
- Test in staging first
- Monitor deployment health

---

## 📊 **Monitoring & Metrics**

### **Pipeline Metrics**
- Build success rate
- Test execution time
- Security scan results
- Deployment frequency

### **Quality Metrics**
- Code coverage percentage
- Security vulnerability count
- Linting error count
- Type checking issues

### **Performance Metrics**
- Build duration
- Cache hit rate
- Resource utilization
- Cost optimization

---

## 🚀 **Getting Started**

### **For Developers**
1. Fork the repository
2. Create feature branch
3. Make changes and test locally
4. Push and create pull request
5. Monitor CI/CD pipeline results

### **For Maintainers**
1. Review pull requests
2. Monitor pipeline health
3. Update dependencies regularly
4. Maintain documentation
5. Monitor security alerts

---

**📅 Last Updated**: August 26, 2025  
**🔄 Version**: 1.0  
**👥 Maintainers**: SmartCloudOps AI Team
