# SmartCloudOps AI - Copilot Instructions

## Latest Fixes & Workflow Updates (August 2025)
- **Python 3.11** enforced for all builds and deployments (Dockerfile, CI/CD)
- **CI/CD workflows** test both basic and secure Flask apps, plus config management
- **Production CI/CD** explicitly installs `ruff` for linting
- **Docker health check** uses `/` endpoint for compatibility
- **Terraform** validates SSH public key for security
- **main_secure.py** uses relative path for scripts directory imports
- **.env.production.template** present and required for deployment

## Architecture Overview
- **Flask Application** (`app/`): Secure REST API
- **Terraform Infrastructure** (`terraform/`): AWS Free Tier, 25+ resources
- **ML Engine** (`scripts/`): Real-time anomaly detection, S3 model registry
- **Monitoring**: Prometheus + Grafana on EC2
- **Multi-AI Integration**: OpenAI + Gemini

## Critical Workflows
- Always use Python 3.11
- Use `main_secure.py` for production
- All endpoints require API key authentication
- Input validation via `secure_api.py` DTOs
- Secret management via `config.py` (AWS/ENV/File)
- Infrastructure: `terraform init/plan/apply` with validated variables
- ML: Train with `scripts/simple_real_ml_trainer.py`, infer with `scripts/production_inference.py`
- Docker: Build and run with health check on `/`

## File Priority Guide
- `app/main_secure.py` - Main app
- `app/auth_secure.py` - Auth system
- `terraform/main.tf` - Infra definition
- `scripts/production_inference.py` - ML service
- `.env.production.template` - Required for deployment

## Integration Points
- CI/CD: `.github/workflows/` (Python 3.11, explicit dependencies)
- Docker: Multi-stage, non-root, health check
- Terraform: Free tier, validated variables

## Security
- API key authentication, rate limiting, session management
- All production secrets must be set in `.env.production`
