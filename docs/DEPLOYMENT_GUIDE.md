# �� SmartCloudOps AI - Deployment Guide

**Complete deployment guide for SmartCloudOps AI platform**

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [AWS Production Deployment](#aws-production-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Monitoring Setup](#monitoring-setup)
7. [Security Configuration](#security-configuration)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Required Software
- **Docker & Docker Compose** (v20.10+)
- **Node.js** (v18+)
- **Python** (v3.11+)
- **AWS CLI** (v2.0+)
- **Terraform** (v1.0+)
- **kubectl** (v1.25+) - for Kubernetes

### Required Accounts
- **GitHub** - for source code
- **AWS** - for production deployment
- **Docker Hub** or **GitHub Container Registry** - for container images

---

## 🏠 Local Development

### 1. Clone Repository
```bash
git clone https://github.com/your-org/smartcloudops-ai.git
cd smartcloudops-ai
```

### 2. Environment Setup
```bash
# Copy environment template
cp env.example .env

# Generate secure secrets
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('ADMIN_API_KEY=sk-admin-' + secrets.token_hex(32))"
python -c "import secrets; print('ML_API_KEY=sk-ml-' + secrets.token_hex(32))"
python -c "import secrets; print('READONLY_API_KEY=sk-readonly-' + secrets.token_hex(32))"
python -c "import secrets; print('API_KEY_SALT=' + secrets.token_hex(16))"

# Edit .env with generated values
nano .env
```

### 3. Frontend Development
```bash
cd frontend
npm install
npm start
# Frontend runs on http://localhost:3000
```

### 4. Backend Development
```bash
cd app
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main_secure.py
# Backend runs on http://localhost:5000
```

### 5. Run Tests
```bash
# Backend tests
cd app
pytest tests/ --cov=. --cov-report=html

# Frontend tests
cd frontend
npm test
npm run test:coverage
```

---

## 🐳 Docker Deployment

### 1. Build Docker Image
```bash
# Build production image
docker build -t smartcloudops-ai:latest .

# Build with specific tag
docker build -t smartcloudops-ai:v1.0.0 .
```

### 2. Run with Docker
```bash
# Run with environment file
docker run -d \
  --name smartcloudops-ai \
  -p 5000:5000 \
  --env-file .env \
  smartcloudops-ai:latest

# Run with environment variables
docker run -d \
  --name smartcloudops-ai \
  -p 5000:5000 \
  -e SECRET_KEY=your-secret-key \
  -e ADMIN_API_KEY=your-admin-key \
  -e ML_API_KEY=your-ml-key \
  -e READONLY_API_KEY=your-readonly-key \
  -e API_KEY_SALT=your-salt \
  smartcloudops-ai:latest
```

### 3. Docker Compose (Recommended)
```bash
# Create docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    environment:
      - FLASK_ENV=production
    volumes:
      - ./logs:/app/logs
      - ./ml_models:/app/ml_models
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: smartcloudops
      POSTGRES_USER: smartcloudops
      POSTGRES_PASSWORD: your-secure-password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
EOF

# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

---

## ☁️ AWS Production Deployment

### 1. AWS Prerequisites
```bash
# Configure AWS CLI
aws configure

# Create S3 bucket for Terraform state
aws s3 mb s3://smartcloudops-terraform-state

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name smartcloudops-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

### 2. Terraform Configuration
```bash
cd terraform

# Initialize Terraform
terraform init \
  -backend-config="bucket=smartcloudops-terraform-state" \
  -backend-config="key=production/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=smartcloudops-terraform-locks"

# Plan deployment
terraform plan -var-file=terraform-production.tfvars

# Apply deployment
terraform apply -var-file=terraform-production.tfvars
```

### 3. Environment Variables for Production
```bash
# Create production environment file
cat > .env.production << EOF
# Security
SECRET_KEY=your-production-secret-key
ADMIN_API_KEY=sk-admin-production-key
ML_API_KEY=sk-ml-production-key
READONLY_API_KEY=sk-readonly-production-key
API_KEY_SALT=your-production-salt

# Database
DATABASE_URL=postgresql://user:pass@your-rds-endpoint:5432/smartcloudops

# Redis
REDIS_URL=redis://your-elasticache-endpoint:6379/0

# AWS
AWS_REGION=us-east-1
S3_BUCKET_NAME=smartcloudops-ml-models

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
LOG_LEVEL=INFO

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
EOF
```

### 4. Deploy to ECS
```bash
# Build and push Docker image
docker build -t smartcloudops-ai:production .
docker tag smartcloudops-ai:production your-registry/smartcloudops-ai:production
docker push your-registry/smartcloudops-ai:production

# Deploy to ECS
aws ecs update-service \
  --cluster smartcloudops-cluster \
  --service smartcloudops-service \
  --force-new-deployment
```

---

## ☸️ Kubernetes Deployment

### 1. Create Namespace
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: smartcloudops
```

### 2. Create ConfigMap
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: smartcloudops-config
  namespace: smartcloudops
data:
  FLASK_ENV: "production"
  LOG_LEVEL: "INFO"
  PROMETHEUS_PORT: "9090"
  GRAFANA_PORT: "3000"
```

### 3. Create Secret
```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: smartcloudops-secrets
  namespace: smartcloudops
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret-key>
  ADMIN_API_KEY: <base64-encoded-admin-key>
  ML_API_KEY: <base64-encoded-ml-key>
  READONLY_API_KEY: <base64-encoded-readonly-key>
  API_KEY_SALT: <base64-encoded-salt>
```

### 4. Create Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: smartcloudops-app
  namespace: smartcloudops
spec:
  replicas: 3
  selector:
    matchLabels:
      app: smartcloudops
  template:
    metadata:
      labels:
        app: smartcloudops
    spec:
      containers:
      - name: app
        image: your-registry/smartcloudops-ai:production
        ports:
        - containerPort: 5000
        envFrom:
        - configMapRef:
            name: smartcloudops-config
        - secretRef:
            name: smartcloudops-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
```

### 5. Create Service
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: smartcloudops-service
  namespace: smartcloudops
spec:
  selector:
    app: smartcloudops
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
```

### 6. Deploy to Kubernetes
```bash
# Apply all resources
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n smartcloudops
kubectl get services -n smartcloudops

# View logs
kubectl logs -f deployment/smartcloudops-app -n smartcloudops
```

---

## 📊 Monitoring Setup

### 1. Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'smartcloudops'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
```

### 2. Grafana Dashboard
```json
// monitoring/grafana-dashboard.json
{
  "dashboard": {
    "title": "SmartCloudOps AI Dashboard",
    "panels": [
      {
        "title": "System Metrics",
        "type": "graph",
        "targets": [
          {
            "expr": "cpu_usage",
            "legendFormat": "CPU Usage"
          },
          {
            "expr": "memory_usage",
            "legendFormat": "Memory Usage"
          }
        ]
      }
    ]
  }
}
```

### 3. Alert Rules
```yaml
# monitoring/alerts.yml
groups:
  - name: smartcloudops
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 80% for 5 minutes"

      - alert: AnomalyDetected
        expr: anomaly_score < -0.5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Anomaly detected"
          description: "System anomaly detected with high confidence"
```

---

## 🔒 Security Configuration

### 1. Network Security
```bash
# Configure security groups
aws ec2 create-security-group \
  --group-name smartcloudops-sg \
  --description "SmartCloudOps AI Security Group"

# Allow HTTPS only
aws ec2 authorize-security-group-ingress \
  --group-name smartcloudops-sg \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

### 2. SSL/TLS Configuration
```bash
# Generate SSL certificate
aws acm import-certificate \
  --certificate fileb://certificate.pem \
  --private-key fileb://private-key.pem \
  --certificate-chain fileb://chain.pem
```

### 3. Secrets Management
```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name smartcloudops/production \
  --secret-string '{
    "SECRET_KEY": "your-secret-key",
    "ADMIN_API_KEY": "your-admin-key",
    "ML_API_KEY": "your-ml-key",
    "READONLY_API_KEY": "your-readonly-key",
    "API_KEY_SALT": "your-salt"
  }'
```

### 4. IAM Roles
```json
// iam/ecs-task-role.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:region:account:secret:smartcloudops/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::smartcloudops-ml-models/*"
    }
  ]
}
```

---

## 🛠 Troubleshooting

### Common Issues

#### 1. Application Won't Start
```bash
# Check environment variables
docker run --rm --env-file .env smartcloudops-ai:latest env | grep -E "(SECRET|API)"

# Check logs
docker logs smartcloudops-ai

# Check health endpoint
curl http://localhost:5000/health
```

#### 2. Database Connection Issues
```bash
# Test database connection
docker exec -it smartcloudops-ai python -c "
import psycopg2
conn = psycopg2.connect('postgresql://user:pass@host:5432/db')
print('Database connection successful')
"
```

#### 3. ML Model Issues
```bash
# Check model directory
docker exec -it smartcloudops-ai ls -la /app/ml_models

# Train new model
curl -X POST http://localhost:5000/ml/train \
  -H "Authorization: Bearer your-token"
```

#### 4. Frontend Issues
```bash
# Check frontend build
cd frontend
npm run build

# Check API connectivity
curl http://localhost:5000/status
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Create indexes
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX idx_logs_level ON logs(level);

-- Optimize queries
EXPLAIN ANALYZE SELECT * FROM metrics WHERE timestamp > NOW() - INTERVAL '1 hour';
```

#### 2. Caching Strategy
```python
# Redis caching configuration
CACHE_CONFIG = {
    'default': {
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': 'redis://localhost:6379/0',
        'CACHE_DEFAULT_TIMEOUT': 300
    }
}
```

#### 3. Load Balancing
```bash
# Configure nginx load balancer
upstream smartcloudops {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

server {
    listen 80;
    location / {
        proxy_pass http://smartcloudops;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📈 Scaling

### 1. Horizontal Scaling
```bash
# Scale ECS service
aws ecs update-service \
  --cluster smartcloudops-cluster \
  --service smartcloudops-service \
  --desired-count 5

# Scale Kubernetes deployment
kubectl scale deployment smartcloudops-app --replicas=5 -n smartcloudops
```

### 2. Auto Scaling
```yaml
# ECS auto scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/smartcloudops-cluster/smartcloudops-service \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/smartcloudops-cluster/smartcloudops-service \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }'
```

---

## 📞 Support

### Getting Help
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/smartcloudops-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/smartcloudops-ai/discussions)

### Emergency Contacts
- **DevOps Team**: devops@yourcompany.com
- **Security Team**: security@yourcompany.com
- **On-Call**: +1-555-123-4567

---

**SmartCloudOps AI** - Production deployment made simple and secure.
