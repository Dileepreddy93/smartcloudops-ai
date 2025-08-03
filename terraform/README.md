# SmartCloudOps AI - Terraform Infrastructure

This Terraform configuration creates a complete AWS infrastructure for the SmartCloudOps AI platform, including web application hosting, machine learning model storage, monitoring, and database services.

## Architecture Overview

The infrastructure includes:

- **VPC**: Isolated network with public/private subnets across multiple AZs
- **ECS Fargate**: Containerized application hosting with auto-scaling
- **Application Load Balancer**: High-availability load balancing with health checks
- **RDS MySQL**: Managed database for application data
- **S3 Buckets**: Storage for ML models and application logs
- **Lambda**: Serverless functions for ML processing
- **CloudWatch**: Monitoring, logging, and alerting
- **IAM**: Secure role-based access control

## Prerequisites

1. **AWS CLI configured** with appropriate credentials
2. **Terraform >= 1.0** installed
3. **Docker image** built and pushed to ECR
4. **AWS permissions** for creating the required resources

## Quick Start

1. **Clone and navigate to terraform directory:**
   ```bash
   cd terraform/
   ```

2. **Copy and customize variables:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your specific values
   ```

3. **Initialize Terraform:**
   ```bash
   terraform init
   ```

4. **Plan the deployment:**
   ```bash
   terraform plan
   ```

5. **Apply the configuration:**
   ```bash
   terraform apply
   ```

## Configuration

### Required Variables

Edit `terraform.tfvars` and set these required values:

```hcl
# Database credentials
db_password = "your-secure-password"

# Container registry
ecr_repository_url = "your-account-id.dkr.ecr.region.amazonaws.com/smartcloudops-ai"
```

### Optional Customizations

- **Region**: Change `aws_region` for different AWS region
- **Environment**: Set `environment` (dev/staging/prod)
- **Scaling**: Adjust `ecs_desired_count` and auto-scaling settings
- **Resources**: Modify instance types and sizes for your needs
- **SSL**: Add `ssl_certificate_arn` for HTTPS support
- **Domain**: Set `domain_name` for custom domain

## Resource Overview

### Networking
- VPC with configurable CIDR blocks
- Public subnets for load balancer
- Private subnets for application and database
- NAT Gateways for outbound internet access
- Security groups with least-privilege access

### Compute
- ECS Fargate cluster for containerized applications
- Auto-scaling based on CPU utilization
- Application Load Balancer with health checks
- Lambda functions for ML processing

### Storage
- S3 bucket for ML models (versioned, encrypted)
- S3 bucket for logs (with lifecycle policies)
- RDS MySQL with automated backups

### Monitoring
- CloudWatch log groups and metric alarms
- ECS Container Insights
- High CPU/Memory utilization alarms

## Outputs

After successful deployment, Terraform will output:

- **Application URL**: Access your deployed application
- **Database endpoint**: For application configuration
- **S3 bucket names**: For ML model and log storage
- **Resource ARNs**: For additional integrations

## Security Features

- **VPC isolation**: Private subnets for sensitive resources
- **Security groups**: Restricted network access
- **IAM roles**: Principle of least privilege
- **Encrypted storage**: S3 server-side encryption
- **Private networking**: Database in private subnets

## Monitoring and Alerting

The infrastructure includes:

- CloudWatch alarms for high CPU/memory usage
- ECS Container Insights for detailed metrics
- Centralized logging to CloudWatch
- S3 access logging

## Backup and Recovery

- RDS automated backups (configurable retention)
- S3 versioning for ML models
- Cross-AZ deployment for high availability

## Cost Optimization

For development environments:
- Use `db.t3.micro` for RDS
- Set `ecs_desired_count = 1`
- Use smaller ECS CPU/memory allocations

For production:
- Use larger instance types
- Enable multi-AZ RDS deployment
- Implement reserved instances

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will permanently delete all data. Ensure you have backups!

## Troubleshooting

### Common Issues

1. **ECR Repository**: Ensure the ECR repository exists and image is pushed
2. **Permissions**: Verify AWS credentials have required permissions
3. **Quotas**: Check AWS service quotas for your account
4. **Dependencies**: Some resources may take time to become available

### Validation

After deployment, verify:
- Application URL responds correctly
- Database connectivity from ECS tasks
- S3 buckets are accessible
- CloudWatch logs are being generated

## Next Steps

1. **Deploy your application**: Push Docker image to ECR
2. **Configure DNS**: Set up Route 53 or external DNS
3. **Add SSL certificate**: For HTTPS support
4. **Set up monitoring**: Configure additional CloudWatch dashboards
5. **Implement CI/CD**: Automate deployments with GitHub Actions or similar

## Support

For issues with this Terraform configuration:
1. Check AWS CloudFormation events for detailed error messages
2. Review CloudWatch logs for application issues
3. Validate security group and network connectivity
4. Ensure all required variables are set correctly

## File Structure

```
terraform/
├── main.tf                    # Main infrastructure configuration
├── variables.tf               # Variable definitions
├── outputs.tf                 # Output values
├── terraform.tfvars.example   # Example configuration
└── README.md                  # This file
```
