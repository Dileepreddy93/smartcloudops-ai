![Lint & Test](https://github.com/Dileepreddy93/smartcloudops-ai/workflows/Lint%20and%20Test/badge.svg)
![Deploy](https://img.shields.io/badge/Deploy-passing-brightgreen)
![Build](https://github.com/Dileepreddy93/smartcloudops-ai/workflows/Build/badge.svg)
![Code Quality](https://github.com/Dileepreddy93/smartcloudops-ai/workflows/Code%20Quality/badge.svg)
## SmartCloudOps AI

Production-ready DevOps and ML platform combining a Flask backend, Terraform IaC, Dockerized monitoring (Prometheus/Grafana), and a ChatOps layer.

### Key Features
- **Secure Flask API** with modular blueprints: health, status, metrics, ML, remediation, ChatOps
- **ML Anomaly Detection** pipeline with Isolation Forest and Prophet models in `ml_models/`
- **Observability Stack**: Prometheus + Grafana dashboards with Node Exporter (port 9100)
- **Infrastructure as Code**: Terraform modules for AWS with remote state and environment-specific configs
- **CI/CD Pipeline**: GitHub Actions for lint, test, build, deploy, and code quality checks
- **Security Hardening**: Bandit, Safety, Trivy scans with pinned dependencies and IAM policies
- **ChatOps Integration**: Natural language command processing via `/api/v1/chatops` endpoints
- **Auto-Remediation**: Rule-based system monitoring with automated response actions

---

## 🚀 Recent Updates

### Security & Dependencies (Latest)
- **Security Hardening**: Upgraded PyJWT to 2.10.1, cryptography to 44.0.1, uWSGI to 2.0.26
- **Dependency Management**: Pinned protobuf 5.29.5, nltk 3.9.1 for stability
- **Vulnerability Scanning**: Integrated Bandit, Safety, and Trivy in CI/CD pipeline
- **IAM Policies**: Generated least-privilege policies with `make iam-policies`

### CI/CD Enhancements
- **GitHub Actions**: Comprehensive workflows for lint, test, build, deploy, and code quality
- **Workflow Monitoring**: Automated failure detection and status reporting
- **Status Badges**: Real-time workflow status indicators
- **Multi-Environment**: Support for dev, staging, and production deployments

### Infrastructure Improvements
- **Terraform Validation**: Fixed regex validations and added secure defaults
- **Monitoring Stack**: Enhanced Prometheus alerts and Grafana dashboards
- **Docker Production**: Optimized production Dockerfile and compose configurations

---

### Quickstart

Prerequisites: Python 3.11+, Docker (optional), Terraform (optional)

```bash
# Clone and enter
git clone https://github.com/Dileepreddy93/smartcloudops-ai.git
cd smartcloudops-ai

# Python deps
make install     # base
make install-dev # dev tools (formatter, linter, type checker, security)

# Quality gates
make lint && make type && make bandit && make safety && make trivy

# Tests
make test

# Run backend (development)
python app/main.py
# API: http://localhost:5000 (health: /health, status: /status, metrics: /metrics)
```

#### Frontend (React + Tailwind)
```bash
cd frontend
npm install
npm start
# UI: http://localhost:3000 (proxy to backend http://localhost:5000)
```

---

### Docker (App + DB + Cache + Monitoring)
```bash
docker compose -f docker/docker-compose.yml up -d

# Health
curl -s http://localhost:5000/health | jq

# Logs
docker logs -f smartcloudops-app

# Ports
# - App:        5000
# - Postgres:   5432
# - Redis:      6379
# - Prometheus: 9090
# - Grafana:    3000 (login admin / ${GRAFANA_ADMIN_PASSWORD:-admin})
```

---

### Terraform IaC (AWS)
Terraform configuration lives in `terraform/` with tfvars for different targets.

```bash
# Format & validate
make tf-fmt && make tf-validate

# Initialize and plan (choose appropriate tfvars)
cd terraform
terraform init
terraform plan -var-file=terraform-free-tier.tfvars

# Apply (example)
terraform apply -var-file=terraform-free-tier.tfvars
```

Notes:
- Configure AWS credentials first (e.g., `make aws-setup PROFILE=yourprofile REGION=us-east-1`).
- For production, use S3 remote state and DynamoDB locking (see `terraform/TERRAFORM_MASTER_DOCUMENTATION.md`).

---

### Environment Setup
Copy `env.example` to `.env` and adjust values as needed.

Required highlights:
- `DATABASE_URL` or individual `DB_*` settings
- `REDIS_URL` (proxy/cache for ChatOps and ML)
- `OPENAI_API_KEY` (for ChatOps/generative assistance)
- `GITHUB_TOKEN` (for workflow monitor tooling in `docs/` and `scripts/`)
- `PROMETHEUS_URL` and `GRAFANA_URL` (monitoring)

```bash
cp env.example .env
# then edit .env
```

---

### API Essentials
- Health: `GET /health`
- Status: `GET /status`
- Metrics: `GET /metrics`
- Versioned APIs mounted at `app/api/v1/` (e.g., remediation, ml, logs)

All JSON responses follow the shape: `{ "status": "success|error", "data": ..., "error": ... }`.

---

### Monitoring
- Prometheus configured via `monitoring/prometheus-alerts.yml` and Docker Compose service
- Grafana on port 3000 with dashboards provisioned from `monitoring/`
- Node Exporter on port 9100 for system metrics

---

### ChatOps API (Phase 5)
All endpoints are prefixed with `/api/v1/chatops` (see `app/routes/phase5_routes.py`).

Examples:
```bash
# Process a natural language command
curl -sX POST http://localhost:5000/api/v1/chatops/process \
  -H 'Content-Type: application/json' \
  -d '{"command":"deploy the app to production"}' | jq

# List supported intents
curl -s http://localhost:5000/api/v1/chatops/intents | jq

# View recent commands
curl -s http://localhost:5000/api/v1/chatops/history?limit=5 | jq

# Execute an action directly
curl -sX POST http://localhost:5000/api/v1/chatops/execute \
  -H 'Content-Type: application/json' \
  -d '{"action":"deploy","parameters":{"app_name":"smartcloudops-ai","environment":"production"}}' | jq

# Health and statistics
curl -s http://localhost:5000/api/v1/chatops/health | jq
curl -s http://localhost:5000/api/v1/chatops/statistics | jq
```

---

### Useful Make Targets
```bash
# Development
make install       # install app deps
make install-dev   # install dev tools
make test          # run tests
make lint          # ruff/black/isort
make type          # mypy

# Security & Quality
make bandit        # security scan (code)
make safety        # vulnerability scan (deps)
make trivy         # filesystem/container scan
make iam-policies  # generate IAM policies

# Infrastructure
make tf-fmt        # terraform fmt -recursive
make tf-validate   # terraform validate (no-backend)
make aws-setup     # configure AWS credentials

# Docker & Deployment
make docker-build  # build app image
make docker-run    # run with docker-compose
```

---

### Documentation
- **Architecture & Deployment**: `docs/`
  - `docs/PRODUCTION_DEPLOYMENT.md` - Production deployment guide
  - `docs/AWS_SETUP.md` - AWS infrastructure setup
  - `docs/CI-CD-Guide.md` - CI/CD pipeline documentation
  - `docs/README_WORKFLOW_MONITORING.md` - Workflow monitoring utilities
- **Monitoring Assets**: `monitoring/`
  - `monitoring/prometheus-alerts.yml` - Alert rules
  - `monitoring/grafana-dashboards/` - Dashboard configurations
- **Infrastructure**: `terraform/`
  - `terraform/TERRAFORM_MASTER_DOCUMENTATION.md` - Complete Terraform guide

---

### Security & Testing
- Least-privilege IAM for Terraform and runtime services
- Secrets via `.env` locally and AWS SSM in production
- Run security scans: `make bandit && make safety && make trivy`
- Run unit tests: `make test` (see `tests/`)

---

### Contributing
1. Create a feature branch
2. Implement changes with tests
3. Run quality gates (lint, type, security)
4. Open a PR with a concise summary

### License
MIT — see `LICENSE`.

### Support
- Docs: `docs/`
  - `docs/USER_GUIDE.md`
  - `docs/PRODUCTION_DEPLOYMENT.md`
  - `docs/DEPLOYMENT_GUIDE.md`
  - `docs/MASTER_PROJECT_STATUS.md`
- Issues: use GitHub Issues on the repository
- Discussions: GitHub Discussions

---

### ML Anomaly Detection
- Models: Isolation Forest and Prophet
- Model artifact: `ml_models/anomaly_model.pkl`
- Validation: F1-score ≥ 0.85 on validation set
- Live inference: Served via `/ml/predict`; metrics at `/ml/metrics`

### Auto-Remediation
- Rule engine watches Prometheus alerts and system metrics
- Example condition: if cpu > 90% for >3min → triggers `scripts/scale_up.py`
- Audit logs: actions stored in `logs/` with timestamp, action, result

### Secrets & IAM
- Secrets via AWS SSM in production; `.env` locally
- Enforce least-privilege IAM; generate starter policies:
```bash
make iam-policies
```

### Terraform Remote State
- Recommended: S3 backend with DynamoDB locking
- See `terraform/TERRAFORM_MASTER_DOCUMENTATION.md`
- Quick init example:
```bash
cd terraform
terraform init \
  -backend-config="bucket=<your-state-bucket>" \
  -backend-config="key=envs/dev/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=<your-lock-table>"
```

### Docker Production
- Production Dockerfile: `Dockerfile.production`
- Compose stack: `docker/docker-compose.yml` includes app, DB, Redis, Prometheus, Grafana

### CI/CD & Workflow Monitoring
- Guides in `docs/CI-CD-Guide.md` and `docs/README_WORKFLOW_MONITORING.md`
- Generated reports in `reports/`
