## AWS Credentials Setup (Non-Interactive)

This project provides a non-interactive script to configure AWS credentials locally and verify identity. It supports reading values from environment variables and the `.env` file.

### Prerequisites
- AWS Access Key ID and Secret Access Key with permissions to at least call `sts:GetCallerIdentity`. For Terraform, see policies below.
- `aws` CLI (installed automatically if missing).

### 1) Populate `.env` or export env vars
Set at least these variables (either export them or put them in `.env`):

```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...    # optional
AWS_DEFAULT_REGION=us-east-1
```

### 2) Configure credentials and verify

Using Makefile (recommended):

```
make aws-setup PROFILE=smartcloudops REGION=us-east-1
make aws-whoami PROFILE=smartcloudops
```

Or call the script directly:

```
bash scripts/aws_configure_credentials.sh smartcloudops us-east-1
```

This writes entries to `~/.aws/credentials` and `~/.aws/config` and verifies with `sts get-caller-identity`.

### 3) Generate IAM policies

Generate least-privilege policies for Terraform backend and developer operations:

```
make iam-policies
```

Outputs will be written to `reports/`:
- `terraform_backend_policy.json`
- `smartcloudops_dev_policy.json`

The Terraform backend in `terraform/production/main.tf` uses:
- S3 bucket: `smartcloudops-terraform-state`
- DynamoDB table: `terraform-locks`

Attach the backend policy to the IAM principal used by Terraform (user/role). Consider scoping the developer policy further to match your environment and follow least-privilege principles.

### Notes
- Do not commit real credentials to the repo.
- For temporary credentials, include `AWS_SESSION_TOKEN`.
- You can switch profiles with `AWS_PROFILE=smartcloudops`.


