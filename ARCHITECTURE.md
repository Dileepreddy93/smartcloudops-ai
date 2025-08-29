SmartCloudOps.AI Architecture
=============================

Overview
--------
SmartCloudOps.AI is a production-grade platform for DevOps observability, anomaly detection, and ChatOps-driven remediation. The system is composed of a Flask backend, a React frontend, Terraform-managed AWS infrastructure, and a monitoring stack built on Prometheus and Grafana. Security, reliability, and maintainability are first-class concerns.

Repository Structure
--------------------

- `app/`: Flask backend (blueprints in `app/api`, services in `app/services`, configs in `app/config`, background workers in `app/background_tasks`). Entry point: `app/main.py`.
- `frontend/`: React dashboard (TypeScript, TailwindCSS). Commands via `react-scripts`.
- `monitoring/`: Prometheus alerts, Grafana dashboards, and production monitoring scripts.
- `terraform/`: IaC for AWS. Uses S3 backend and DynamoDB locking for remote state. Environment-specific `.tfvars` files in `terraform/production`.
- `services/`: Service boundaries for `auth_service` and `ml_service` (shared contracts or microservice stubs).
- `ml/` and `ml_models/`: Model training utilities and serialized artifacts (ignored in VCS via `.gitignore`).
- `docs/`: Product and ops documentation (deployment, CI/CD, user guides).
- `reports/`: Generated reports (testing, pipelines, audits) moved out of the root for cleanliness.
- `tests/`: Pytest-based unit tests.
- `scripts/`: Developer and CI utility scripts.

Backend (Flask)
---------------

- App initialization: `app/main.py` wires configuration, database, caching, background tasks, and registers blueprints under `app/api/v1` (e.g., `health`, `metrics`, `ml`, `remediation`, `chatops`).
- Config: `app/config/` provides environment-aware configuration; secrets are pulled via AWS SSM or environment variables. No secrets in VCS.
- Security: `app/auth_secure.py` and `app/secrets_manager.py` enforce API key, RBAC, request correlation IDs, and secure secret retrieval.
- Background processing: `app/background_tasks.py` defines Celery tasks and task status endpoints.
- Data & caching: `app/database_integration.py` and `app/cache_service.py` abstract persistence and Redis caching respectively.
- ML inference: `app/core/` provides secured inference hooks; models are loaded from `ml_models/` at runtime.

Frontend (React)
----------------

- Located in `frontend/`. Uses TailwindCSS, React Router, and Axios for API calls to the Flask backend (proxy defaults to `http://localhost:5000`).
- Standard scripts: `start`, `build`, `test`, `lint`, and `type-check`.

Infrastructure (Terraform)
-------------------------

- Backend: `terraform/production/main.tf` defines the remote backend with S3 and DynamoDB locking.
- Modules: Located under `terraform/modules/` and composed in environment roots (`terraform/production`).
- State: Local `terraform.tfstate*` files are not committed (enforced in `.gitignore`).

Monitoring Stack
----------------

- Prometheus scrapes Node Exporter at port 9100. Alert rules in `monitoring/prometheus-alerts.yml`.
- Grafana runs on port 3000. Dashboards shipped via `monitoring/grafana-dashboards/`.
- Production monitoring automation in `monitoring/production_monitoring.py`.

Anomaly Detection
-----------------

- Isolation Forest or Prophet for anomaly detection.
- Models are saved to `ml_models/anomaly_model.pkl` and loaded by the backend.
- Model validation targets F1 ≥ 0.85; testing summaries are kept in `reports/`.

Auto-Remediation
----------------

- Rule examples: `if cpu > 90% for >3min → trigger scale_up.py`.
- Actions are logged with timestamp and result in `/logs/` (directory is retained with `.gitkeep`).

Security & DevSecOps
--------------------

- IAM policies are least-privilege; secrets via AWS SSM.
- Static analysis with Bandit and container scans with Trivy (CI workflows under `.github/workflows`).
- `.gitignore` hardened to exclude env files, state files, coverage, and workflow artifacts.

CI/CD
-----

- Workflows in `.github/workflows` handle linting, tests, code quality, infrastructure validation, and optional deployment.
- Terraform CI uses `terraform fmt`, `init -backend=false`, and `validate` for PRs; deployment jobs are gated.

Local Development
-----------------

- Backend: `python -m app.main` or gunicorn entry depending on `Dockerfile`.
- Frontend: `npm install && npm start` inside `frontend/`.
- Environment: Copy `env.example` to `.env` and populate required variables; never commit `.env`.

Operational Notes
-----------------

- Logs are rotated and not committed; `logs/` remains in repo with `.gitkeep`.
- Reports are centralized under `reports/` for easier housekeeping.
- Terraform state must remain remote; local state files are ignored.
