# Example tfvars for free-tier validation
project_name           = "smartcloudops-ai"
environment            = "development"
aws_region             = "us-east-1"

# Provide a compliant strong password (>=12, upper, lower, number, special)
db_password            = "Aa1!CorrectHorseBattery$"

# Replace with your real public key before apply
ssh_public_key         = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIE9Wb0tY8mN9Xl6K2s6b1s0Xh3d2pXq3k9u5t4r2o1p user@example"

# Restrict to your IPs when applying
allowed_ssh_cidrs      = []
allowed_app_cidrs      = []
allowed_monitoring_cidrs = []
admin_ip_cidr          = ""

enable_https           = false
enable_http_redirect   = true
certificate_arn        = ""
domain_name            = ""

enable_secrets_manager = false
openai_api_key         = ""

enable_advanced_monitoring = false
