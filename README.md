# SmartCloudOps AI

## Latest Updates (August 2025)

- **Python 3.11** is now used for all builds and deployments (Dockerfile, CI/CD).
- **CI/CD workflows** now test both basic and secure Flask apps, plus configuration management.
- **Production CI/CD** explicitly installs `ruff` for linting.
- **Docker health check** uses `/` endpoint for compatibility with authentication.
- **Terraform** now validates that an SSH public key is provided for security.
- **main_secure.py** uses a relative path for scripts directory imports, improving portability.
- **.env.production.template** is present and must be filled with actual secrets for production.

## Quick Start

1. Clone the repo and set up your Python environment:
   ```bash
   python -m venv venv && source venv/bin/activate
   pip install -r app/requirements.txt
   ```
2. Fill in `.env.production` using the provided template.
3. Deploy infrastructure:
   ```bash
   cd terraform
   terraform init
   terraform plan -var-file="terraform-free-tier.tfvars"
   terraform apply
   ```
4. Build and run the Docker container:
   ```bash
   docker build -t smartcloudops-ai:latest .
   docker run -d --name smartcloudops-ai -p 5000:5000 smartcloudops-ai:latest
   ```
5. Run tests and validate endpoints using CI/CD or manually.

## Documentation
- See `.github/copilot-instructions.md` for AI agent guidance and workflow details.
- See `.env.production.template` for required environment variables.
- See `docs/DEPLOYMENT_GUIDE.md` for production deployment steps.

## Security & Compliance
- All endpoints require API key authentication.
- Rate limiting and session management are enforced.
- Infrastructure and application follow best security practices.

## Contact
For issues or contributions, open a GitHub issue or pull request.
