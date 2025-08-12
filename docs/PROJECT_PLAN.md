# Smart CloudOps AI: Project Plan

This document represents the comprehensive project plan for the Smart CloudOps AI system, organized in phases for systematic development and deployment.

## Phase 0: Foundation & Setup

### 0.1 Repo + Branching

**Status: ✅ Complete**

- Create GitHub repo: `smartcloudops-ai`
- Add `.gitignore`, `README.md`, `LICENSE`
- Branches: `main`, `dev`, `infra/terraform`, `app/chatops`

### 0.2 Folder Structure

**Status: ✅ Complete**

```
smartcloudops-ai/
  - terraform/              # Infrastructure as Code
  - app/                    # Flask ChatOps application
  - scripts/                # Automation scripts
  - ml_models/              # Machine learning models
  - .github/workflows/      # CI/CD pipelines
  - docs/                   # Documentation
  - requirements.txt        # Python dependencies
  - docker-compose.yml      # Local development stack
  - Dockerfile              # Container configuration
  - setup.py                # Development environment setup
  - README.md               # Project documentation
```

### 0.3 Tool Installations & Setup

**Status: ✅ Complete**

- Terraform CLI
- Docker & Docker Compose
- AWS CLI
- Python 3.10++ venv
- Added: Automated setup script (`setup.py`)
- Added: CI/CD pipelines for infrastructure and application
- Added: Docker development environment
- Added: Git hooks for code quality

## Phase 1: Infrastructure Provisioning + Monitoring

### 1.1 Terraform Setup

**Status: ✅ Complete**

- Provider & Remote State: Configure `main.tf` with AWS provider and optional S3 backend
- VPC + Subnets: Create VPC (`10.0.0.0/16`) with public subnets
- IGW + route table
- Security Groups: Open ports 22, 80, 3000, 9090, 9100
- EC2 Instances: Create `ec2_monitoring` and `ec2_application` instances
- Added: Comprehensive setup scripts for both servers
- Added: Basic Flask application with metrics endpoint
- Added: Terraform documentation and examples

### 1.2 Monitoring Stack

**Status: ✅ Complete**

- Prometheus: Install and configure `prometheus.yml` on `ec2_monitoring`
- Node Exporter: Install on all EC2 instances on port 9100
- Grafana: Install, add Prometheus as data source, and create dashboards
- Added: Pre-configured dashboards for CPU, RAM, Disk monitoring
- Added: Automated Grafana data source provisioning
- Added: Comprehensive alerting rules for system anomalies
- Added: Post-deployment configuration automation
- Added: Monitoring stack documentation and troubleshooting guide

### 1.3 CI/CD Infra

**Status: ✅ Complete**

- GitHub Actions: Create `infra.yml` to run `terraform fmt` and `validate` on push
- Added: Comprehensive CI/CD with security scanning, testing, Docker builds
- Added: Multi-environment support and pull request automation

## Phase 2: Flask ChatOps App + Dockerization

### 2.1 Flask App Basics

- Create `app/main.py` with endpoints: `/query`, `/status`, `/logs`

### 2.2 GPT Integration

- Use `openai` or `litellm` SDK, implement prompt template, and sanitize input

### 2.3 Dockerization

- Create `Dockerfile` based on `python:3.10`

### 2.4 CI/CD

- Add `ci-app.yml` to auto-build, lint, and push container

## Phase 3: Anomaly Detection (ML Layer)

### 3.1 Data Preparation

- Use Prometheus metrics CSV or node_exporter logs

### 3.2 Model Training

- Use Isolation Forest or Prophet, save model, and validate with F1-score >= 0.85

### 3.3 Inference Pipeline

- Load model in a script to process live metrics and output anomaly status

## Phase 4: Auto-Remediation Logic

### 4.1 Rule Engine

- Trigger remediation based on rules (e.g., high CPU utilization)

### 4.2 Scripts

- Create scripts like `restart_service.py` and `scale_up.py`

### 4.3 Logging

- Implement JSON logging with daily rotation

## Phase 5: ChatOps GPT Layer

### 5.1 NLP Queries

- Handle queries like "What's current CPU?" or "Summarize last 3 anomalies"

### 5.2 Context Window

- Cache last anomalies and use logs/ML outputs for intelligent answers

### 5.3 GPT Prompting

- Define system and user prompts for the DevOps assistant

## Phase 6: Testing, Security & Documentation

### 6.1 Unit & Integration Tests

- Use `pytest` for the app and run load tests for Flask endpoints

### 6.2 Security

- Implement IAM with least privilege, use AWS SSM for secrets, and perform static scans

### 6.3 Documentation

- Create `README.md`, architecture diagrams, and a project walkthrough

## Phase 7: Production Launch & Feedback

### 7.1 Final Deployment

- Deploy all modules to a live AWS VPC and enable alerting

### 7.2 Beta Testing

- Invite users and collect feedback

### 7.3 Final Wrap-up

- Deliver source code, diagrams, pipelines, installation guide, and demo video

---

## Project Overview

This Smart CloudOps AI project aims to create an intelligent cloud operations system that combines:

- Infrastructure as Code (Terraform)
- Monitoring & Observability (Prometheus + Grafana)
- Machine Learning (Anomaly Detection)
- ChatOps (GPT-powered conversational interface)
- Auto-Remediation (Intelligent response to issues)

The project follows a phased approach ensuring each component is properly tested and integrated before moving to the next phase.


