![Build](https://img.shields.io/badge/Build-failing-red)
![Lint & Test](https://img.shields.io/badge/Lint & Test-failing-red)
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

### Contributing
1. Create a feature branch
2. Implement changes with tests
3. Run quality gates (lint, type, security)
4. Open a PR with a concise summary

### License
MIT — see `LICENSE`.

### Support
- Docs: `docs/`
- Issues: use GitHub Issues on the repository
- Discussions: GitHub Discussions
