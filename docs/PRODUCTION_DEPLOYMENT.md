# 🚀 SmartCloudOps AI - Production Deployment Guide

## **Overview**

This guide provides step-by-step instructions for deploying SmartCloudOps AI to production environments with enterprise-grade security, scalability, and monitoring.

## **📋 Prerequisites**

### **Required Tools**
- **Docker & Docker Compose** (v20.10+)
- **Kubernetes** (v1.24+) or **AWS ECS/EKS**
- **Terraform** (v1.5+)
- **AWS CLI** (v2.0+)
- **kubectl** (for Kubernetes deployments)
- **Helm** (v3.0+)

### **Required Services**
- **AWS Account** with appropriate permissions
- **Domain Name** (for SSL certificates)
- **SSL Certificate** (Let's Encrypt or AWS Certificate Manager)
- **Monitoring Stack** (Prometheus, Grafana, AlertManager)

## **🏗️ Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │    │   Application   │    │   RDS Database  │
│   (CDN + SSL)   │◄──►│   Load Balancer │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
    ┌───────────▼──────────┐    │    ┌──────────▼──────────┐
    │   ECS/EKS Cluster    │    │    │   ElastiCache       │
    │   (Auto-scaling)     │    │    │   (Redis)           │
    └──────────────────────┘    │    └──────────────────────┘
                                │
    ┌───────────▼──────────┐    │    ┌──────────▼──────────┐
    │   S3 Storage         │    │    │   CloudWatch        │
    │   (ML Models)        │    │    │   (Logs + Metrics)  │
    └──────────────────────┘    │    └──────────────────────┘
                                │
                ┌───────────────▼───────────────┐
                │        Monitoring Stack       │
                │   (Prometheus + Grafana)      │
                └───────────────────────────────┘
```

## **🔧 Step 1: Environment Setup**

### **1.1 Clone Repository**
```bash
git clone https://github.com/your-org/smartcloudops-ai.git
cd smartcloudops-ai
```

### **1.2 Configure Environment Variables**
```bash
# Copy environment template
cp env.example .env.production

# Generate secure secrets
python3 -c "
import secrets
print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))
print('ADMIN_API_KEY=sk-admin-' + secrets.token_urlsafe(32))
print('ML_API_KEY=sk-ml-' + secrets.token_urlsafe(32))
print('READONLY_API_KEY=sk-readonly-' + secrets.token_urlsafe(32))
print('API_KEY_SALT=' + secrets.token_urlsafe(16))
print('ADMIN_PASSWORD=' + secrets.token_urlsafe(16))
" > .env.production
```

### **1.3 Configure AWS Credentials**
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and default region
```

## **🏗️ Step 2: Infrastructure Deployment**

### **2.1 Deploy Core Infrastructure**
```bash
cd terraform/production

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file="terraform-production.tfvars"

# Deploy infrastructure
terraform apply -var-file="terraform-production.tfvars"
```

### **2.2 Verify Infrastructure**
```bash
# Check all resources are created
terraform output

# Verify VPC and networking
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=smartcloudops-vpc"

# Verify RDS instance
aws rds describe-db-instances --db-instance-identifier smartcloudops-db
```

## **🐳 Step 3: Container Deployment**

### **3.1 Build and Push Docker Images**
```bash
# Build production image
docker build -t smartcloudops-ai:latest .

# Tag for registry
docker tag smartcloudops-ai:latest your-registry/smartcloudops-ai:latest

# Push to registry
docker push your-registry/smartcloudops-ai:latest
```

### **3.2 Deploy to ECS/EKS**

#### **Option A: ECS Deployment**
```bash
# Deploy ECS service
aws ecs update-service --cluster smartcloudops-cluster --service smartcloudops-service --force-new-deployment

# Check deployment status
aws ecs describe-services --cluster smartcloudops-cluster --services smartcloudops-service
```

#### **Option B: Kubernetes Deployment**
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Check deployment status
kubectl get pods -n smartcloudops
kubectl get services -n smartcloudops
```

## **🔒 Step 4: Security Configuration**

### **4.1 SSL Certificate Setup**
```bash
# Using AWS Certificate Manager
aws acm request-certificate \
    --domain-name your-domain.com \
    --validation-method DNS \
    --subject-alternative-names "*.your-domain.com"

# Or using Let's Encrypt
certbot certonly --dns-route53 -d your-domain.com -d *.your-domain.com
```

### **4.2 Security Group Configuration**
```bash
# Update security groups to allow only necessary traffic
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxx \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0
```

### **4.3 IAM Role Configuration**
```bash
# Create IAM role for application
aws iam create-role --role-name SmartCloudOpsAppRole --assume-role-policy-document file://trust-policy.json

# Attach necessary policies
aws iam attach-role-policy --role-name SmartCloudOpsAppRole --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

## **📊 Step 5: Monitoring Setup**

### **5.1 Deploy Monitoring Stack**
```bash
# Deploy Prometheus and Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring

# Deploy custom dashboards
kubectl apply -f monitoring/grafana-dashboards/
```

### **5.2 Configure CloudWatch**
```bash
# Enable CloudWatch logging
aws logs create-log-group --log-group-name /aws/ecs/smartcloudops

# Configure log retention
aws logs put-retention-policy --log-group-name /aws/ecs/smartcloudops --retention-in-days 30
```

### **5.3 Set Up Alerts**
```bash
# Create CloudWatch alarms
aws cloudwatch put-metric-alarm \
    --alarm-name "SmartCloudOps-HighCPU" \
    --alarm-description "High CPU utilization" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold
```

## **🔧 Step 6: Application Configuration**

### **6.1 Database Migration**
```bash
# Run database migrations
docker run --rm \
    -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
    smartcloudops-ai:latest \
    python -m alembic upgrade head
```

### **6.2 ML Model Training**
```bash
# Train initial ML models
docker run --rm \
    -e ML_MODEL_PATH="/app/ml_models" \
    smartcloudops-ai:latest \
    python -c "from app.core.ml_engine.secure_inference import SecureMLInferenceEngine; engine = SecureMLInferenceEngine(); engine._train_model()"
```

### **6.3 Initialize Admin User**
```bash
# Create admin user
curl -X POST https://your-domain.com/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -H "X-API-Key: your-admin-api-key" \
    -d '{
        "username": "admin",
        "password": "secure-password",
        "email": "admin@your-domain.com",
        "role": "admin"
    }'
```

## **🧪 Step 7: Testing & Validation**

### **7.1 Health Check**
```bash
# Test application health
curl -X GET https://your-domain.com/health

# Expected response:
{
    "status": "success",
    "message": "Health check completed",
    "data": {
        "overall_status": "healthy",
        "components": {
            "database": true,
            "ml_service": true,
            "cache": true
        }
    }
}
```

### **7.2 API Testing**
```bash
# Test ML prediction endpoint
curl -X POST https://your-domain.com/api/v1/ml/predict \
    -H "Content-Type: application/json" \
    -H "X-API-Key: your-ml-api-key" \
    -d '{
        "metrics": {
            "cpu_usage": 75.0,
            "memory_usage": 60.0,
            "disk_usage": 45.0,
            "network_io": 25.0,
            "load_1m": 2.5,
            "load_5m": 2.3,
            "load_15m": 2.1,
            "response_time": 250.0
        }
    }'
```

### **7.3 Load Testing**
```bash
# Install k6 for load testing
curl -L https://github.com/grafana/k6/releases/download/v0.45.0/k6-v0.45.0-linux-amd64.tar.gz | tar xz

# Run load test
./k6 run load-tests/api-load-test.js
```

## **📈 Step 8: Performance Optimization**

### **8.1 Auto-scaling Configuration**
```bash
# Configure ECS auto-scaling
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --scalable-dimension ecs:service:DesiredCount \
    --resource-id service/smartcloudops-cluster/smartcloudops-service \
    --min-capacity 2 \
    --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --scalable-dimension ecs:service:DesiredCount \
    --resource-id service/smartcloudops-cluster/smartcloudops-service \
    --policy-name cpu-scaling-policy \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

### **8.2 CDN Configuration**
```bash
# Configure CloudFront distribution
aws cloudfront create-distribution \
    --distribution-config file://cloudfront-config.json

# Update DNS records
aws route53 change-resource-record-sets \
    --hosted-zone-id Z1234567890ABC \
    --change-batch file://dns-changes.json
```

## **🔍 Step 9: Monitoring & Alerting**

### **9.1 Dashboard Setup**
```bash
# Import Grafana dashboards
curl -X POST http://admin:admin@grafana:3000/api/dashboards/db \
    -H "Content-Type: application/json" \
    -d @monitoring/dashboards/system-overview.json
```

### **9.2 Alert Configuration**
```bash
# Configure Prometheus alerts
kubectl apply -f monitoring/prometheus-alerts.yaml

# Configure Slack notifications
kubectl apply -f monitoring/alertmanager-config.yaml
```

## **🛡️ Step 10: Security Hardening**

### **10.1 Network Security**
```bash
# Configure WAF rules
aws wafv2 create-web-acl \
    --name SmartCloudOpsWAF \
    --scope REGIONAL \
    --default-action Allow={} \
    --rules file://waf-rules.json

# Associate with ALB
aws wafv2 associate-web-acl \
    --web-acl-arn arn:aws:wafv2:region:account:regional/webacl/SmartCloudOpsWAF/ID \
    --resource-arn arn:aws:elasticloadbalancing:region:account:loadbalancer/app/ALB/ID
```

### **10.2 Secrets Management**
```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
    --name smartcloudops/database \
    --description "Database credentials" \
    --secret-string '{"username":"dbuser","password":"securepassword"}'

# Update application to use secrets
aws ecs update-service \
    --cluster smartcloudops-cluster \
    --service smartcloudops-service \
    --task-definition smartcloudops-task:1
```

## **📋 Step 11: Backup & Disaster Recovery**

### **11.1 Database Backup**
```bash
# Enable automated backups
aws rds modify-db-instance \
    --db-instance-identifier smartcloudops-db \
    --backup-retention-period 7 \
    --preferred-backup-window "03:00-04:00"

# Create manual backup
aws rds create-db-snapshot \
    --db-instance-identifier smartcloudops-db \
    --db-snapshot-identifier smartcloudops-backup-$(date +%Y%m%d)
```

### **11.2 Application Backup**
```bash
# Backup ML models
aws s3 sync s3://smartcloudops-ml-models s3://smartcloudops-backup/ml-models/$(date +%Y%m%d)

# Backup configuration
aws s3 cp .env.production s3://smartcloudops-backup/config/$(date +%Y%m%d)/.env
```

## **✅ Step 12: Go-Live Checklist**

### **Pre-Launch Verification**
- [ ] All infrastructure components deployed and healthy
- [ ] SSL certificates installed and valid
- [ ] Database migrations completed successfully
- [ ] ML models trained and deployed
- [ ] Monitoring and alerting configured
- [ ] Security groups and IAM roles configured
- [ ] Load testing completed successfully
- [ ] Backup and recovery procedures tested
- [ ] Documentation updated
- [ ] Team trained on monitoring and incident response

### **Launch Commands**
```bash
# Final health check
curl -X GET https://your-domain.com/health

# Monitor application logs
aws logs tail /aws/ecs/smartcloudops --follow

# Check monitoring dashboards
open https://grafana.your-domain.com
```

## **🚨 Troubleshooting**

### **Common Issues**

#### **Application Not Starting**
```bash
# Check ECS service logs
aws logs describe-log-streams --log-group-name /aws/ecs/smartcloudops
aws logs get-log-events --log-group-name /aws/ecs/smartcloudops --log-stream-name <stream-name>

# Check container logs
docker logs <container-id>
```

#### **Database Connection Issues**
```bash
# Test database connectivity
aws rds describe-db-instances --db-instance-identifier smartcloudops-db
aws rds describe-db-security-groups --db-security-group-name smartcloudops-db-sg
```

#### **ML Service Issues**
```bash
# Check ML model status
curl -X GET https://your-domain.com/api/v1/ml/health

# Retrain models if needed
docker run --rm smartcloudops-ai:latest python -c "from app.core.ml_engine.secure_inference import SecureMLInferenceEngine; engine = SecureMLInferenceEngine(); engine.retrain_model()"
```

## **📞 Support**

For production deployment support:
- **Email**: support@smartcloudops.ai
- **Documentation**: https://docs.smartcloudops.ai
- **GitHub Issues**: https://github.com/your-org/smartcloudops-ai/issues

---

**🎯 Congratulations! Your SmartCloudOps AI platform is now deployed and ready for production use.**
