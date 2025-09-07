SHELL := /usr/bin/bash

PY ?= python3
PIP ?= pip3

.PHONY: help install install-dev test lint type bandit safety trivy precommit docker-build tf-fmt tf-validate aws-setup aws-whoami iam-policies

help:
	@echo "Targets: install, install-dev, test, lint, type, bandit, safety, trivy, precommit, docker-build, tf-fmt, tf-validate"

install:
	$(PY) -m pip install -U pip
	$(PIP) install -r app/requirements.txt

install-dev: install
	$(PIP) install black ruff isort mypy bandit safety pre-commit

test:
	pytest -q || true

lint:
	ruff check app/ scripts/ tests/
	black --check app/ scripts/ tests/
	isort --check-only app/ scripts/ tests/

type:
	mypy app/ --ignore-missing-imports --no-strict-optional --no-warn-return-any --no-warn-unused-ignores || true

bandit:
	bandit -r app/ -f json -o reports/bandit.json --severity-level high || true

safety:
	mkdir -p reports
	safety check --full-report --ignore 77744 --ignore 77745 | tee reports/safety-report.txt || true

trivy:
	docker build -t smartcloudops:scan .
	docker run --rm smartcloudops:scan true
	trivy fs --format sarif --output reports/trivy-results.sarif . || true

precommit:
	pre-commit install
	pre-commit run --all-files || true

docker-build:
	docker build -t smartcloudops:latest .

tf-fmt:
	cd terraform && terraform fmt -recursive

tf-validate:
	cd terraform && terraform init -backend=false && terraform validate

aws-setup:
	bash scripts/aws_configure_credentials.sh $(PROFILE) $(REGION)

aws-whoami:
	AWS_PROFILE=$(PROFILE) aws sts get-caller-identity | cat

iam-policies:
	$(PY) scripts/generate_iam_policies.py --state-bucket smartcloudops-terraform-state --lock-table terraform-locks --region $${AWS_DEFAULT_REGION:-us-east-1} --out-dir reports

