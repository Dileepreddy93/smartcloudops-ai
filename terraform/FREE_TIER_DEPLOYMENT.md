# SmartCloudOps AI - FREE TIER Deployment Guide

## 🎯 Cost Analysis: $0/month (AWS Free Tier)

### ✅ FREE TIER Resources Used:
- **2x EC2 t2.micro instances** (750 hours/month each = FREE)
- **S3 Storage** (5GB per bucket = FREE)
- **CloudWatch Logs** (5GB ingestion = FREE)  
- **Data Transfer** (15GB outbound = FREE)
- **VPC & Networking** (Always FREE)

### ❌ Removed Expensive Components:
- ~~ALB ($20/month)~~ → Direct EC2 access
- ~~RDS MySQL ($15/month)~~ → Local SQLite/files
- ~~ECS Fargate ($25/month)~~ → EC2 t2.micro instances

---

## 🚀 Quick Deployment (Phase 1)

### Prerequisites
1. **AWS Account** with free tier eligibility
2. **SSH Key Pair** for EC2 access
3. **Terraform** installed
4. **AWS CLI** configured

### Step 1: Generate SSH Key
```bash
ssh-keygen -t rsa -b 2048 -f ~/.ssh/smartcloudops-ai
chmod 400 ~/.ssh/smartcloudops-ai
```

### Step 2: Configure SSH Key
Edit `terraform-free-tier.tfvars`:
```hcl
# Copy your public key content here
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAA..."
```

### Step 3: Deploy Infrastructure
```bash
cd terraform/

# Use free tier configuration
cp main-free-tier.tf main.tf
cp variables-free-tier.tf variables.tf
cp outputs-free-tier.tf outputs.tf

# Plan deployment
terraform plan -var-file="terraform-free-tier.tfvars"

# Deploy (takes 5-10 minutes)
terraform apply -var-file="terraform-free-tier.tfvars"
```

### Step 4: Access Services

After deployment, get the URLs:
```bash
terraform output grafana_url
terraform output flask_app_url
terraform output prometheus_url
```

**Grafana Dashboard**: `http://<monitoring-ip>:3000`
- Username: `admin`
- Password: `admin123`

**Flask Application**: `http://<application-ip>:5000`
- Endpoints: `/health`, `/status`, `/query`, `/logs`

**Prometheus**: `http://<monitoring-ip>:9090`

---

## 🏗️ Architecture (Phase 1)

```
┌─────────────────────────────────────────────────────────┐
│                    VPC (10.0.0.0/16)                   │
│                                                         │
│  ┌─────────────────────┐    ┌─────────────────────────┐ │
│  │   Public Subnet 1   │    │   Public Subnet 2       │ │
│  │   (10.0.1.0/24)     │    │   (10.0.2.0/24)        │ │
│  │                     │    │                         │ │
│  │  ┌───────────────┐  │    │  ┌───────────────────┐  │ │
│  │  │ Monitoring    │  │    │  │ Application       │  │ │
│  │  │ EC2 t2.micro  │  │    │  │ EC2 t2.micro      │  │ │
│  │  │               │  │    │  │                   │  │ │
│  │  │ • Prometheus  │  │    │  │ • Flask App :5000 │  │ │
│  │  │ • Grafana     │  │    │  │ • Node Exporter   │  │ │
│  │  │ • Node Export │  │    │  │ • Docker          │  │ │
│  │  └───────────────┘  │    │  └───────────────────┘  │ │
│  └─────────────────────┘    └─────────────────────────┘ │
│                                                         │
│  ┌─────────────────────┐    ┌─────────────────────────┐ │
│  │  S3: ML Models      │    │  S3: Logs               │ │
│  │  (5GB FREE)         │    │  (5GB FREE)             │ │
│  └─────────────────────┘    └─────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🔍 Phase 1 Verification

### Check Instance Status
```bash
# SSH to monitoring instance
terraform output ssh_monitoring_command

# Run health check
./health-check.sh
```

### Check Application Status  
```bash
# SSH to application instance
terraform output ssh_application_command

# Run application status
./app-status.sh
```

### Test Endpoints
```bash
# Health check
curl http://<application-ip>:5000/health

# System status
curl http://<application-ip>:5000/status

# ChatOps query
curl -X POST http://<application-ip>:5000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "system status"}'
```

---

## 📊 Monitoring Setup (Phase 1.2)

### Grafana Dashboard
1. Access Grafana: `http://<monitoring-ip>:3000`
2. Login: `admin/admin123`
3. Add Prometheus data source: `http://localhost:9090`
4. Import dashboard for system metrics

### Prometheus Targets
- Prometheus itself: `:9090`
- Node Exporter (monitoring): `:9100`
- Node Exporter (application): `<app-ip>:9100`

---

## 🛠️ Development Workflow

### Deploy Application Updates
```bash
# SSH to application instance
ssh -i ~/.ssh/smartcloudops-ai ec2-user@<application-ip>

# Deploy new version
./deploy-app.sh

# Check status
./app-status.sh
```

### View Logs
```bash
# Application logs
journalctl -u smartcloudops-ai -f

# System logs
tail -f /var/log/messages

# CloudWatch logs (via AWS Console)
```

---

## 📈 Next Steps (Phase 2)

1. **GPT Integration** - Add OpenAI API for ChatOps
2. **Enhanced Monitoring** - Custom dashboards and alerts
3. **CI/CD Pipeline** - GitHub Actions for deployment
4. **SSL/HTTPS** - Let's Encrypt certificates
5. **Database** - Add PostgreSQL container

---

## 🔧 Troubleshooting

### Instance Not Starting
```bash
# Check user data logs
ssh ec2-user@<ip> 'sudo tail -f /var/log/cloud-init-output.log'
```

### Service Issues
```bash
# Check service status
systemctl status smartcloudops-ai
systemctl status prometheus
systemctl status grafana-server

# View service logs
journalctl -u <service-name> -f
```

### Network Issues
```bash
# Check security groups
aws ec2 describe-security-groups --group-ids <sg-id>

# Test connectivity
telnet <ip> <port>
```

---

## 💰 Cost Monitoring

### Free Tier Limits
- **EC2**: 750 hours/month per t2.micro
- **S3**: 5GB storage + 20,000 GET requests
- **CloudWatch**: 5GB log ingestion
- **Data Transfer**: 15GB outbound

### Usage Alerts
Set up billing alerts in AWS Console:
1. Go to Billing Dashboard
2. Create billing alarm for $1 threshold
3. Monitor usage in Free Tier dashboard

---

## 🔒 Security Notes

1. **SSH Access**: Only use key-based authentication
2. **Security Groups**: Restrict source IPs where possible
3. **Instance Updates**: Regular `yum update`
4. **Monitoring**: Enable CloudTrail for API logging
5. **Secrets**: Use AWS Systems Manager Parameter Store

---

## 📚 Documentation Links

- [AWS Free Tier](https://aws.amazon.com/free/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

*This deployment follows Phase 1 of the SmartCloudOps AI project plan with full FREE TIER compliance.*
