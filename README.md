![Lint ![Lint & Test](https://img.shields.io/badge/Lint & Test-failing-red) Test](https://img.shields.io/badge/Lint ![Lint & Test](https://img.shields.io/badge/Lint & Test-failing-red) Test-failing-red)
![Deploy](https://img.shields.io/badge/Deploy-passing-brightgreen)
![Build](https://img.shields.io/badge/Build-failing-red)
## SmartCloudOps AI

Production-ready DevOps and ML platform combining a Flask backend, Terraform IaC, Dockerized monitoring (Prometheus/Grafana), and a ChatOps layer.

### Key Features
- Secure Flask API with modular blueprints: health, status, metrics, ML, remediation
- ML anomaly detection pipeline with model persistence in `ml_models/`
- Observability: Prometheus scrape + Grafana dashboards; Node Exporter on port 9100
- Terraform modules for AWS (remote state ready; tfvars for environments)
- CI/CD and workflow monitoring utilities under `docs/` and `scripts/`

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
make install       # install app deps
make install-dev   # install dev tools
make test          # run tests
make lint          # ruff/black/isort
make type          # mypy
make bandit        # security scan (code)
make safety        # vulnerability scan (deps)
make trivy         # filesystem/container scan
make docker-build  # build app image
make tf-fmt        # terraform fmt -recursive
make tf-validate   # terraform validate (no-backend)
```

---

### Documentation
- Architecture and deployment: `docs/`
  - `docs/PRODUCTION_DEPLOYMENT.md`
  - `docs/AWS_SETUP.md`
  - `docs/CI-CD-Guide.md`
  - `docs/README_WORKFLOW_MONITORING.md`
- Monitoring assets: `monitoring/`

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
