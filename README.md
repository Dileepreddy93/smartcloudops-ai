# SmartCloudOps AI 🤖☁️

> **Intelligent DevOps Automation Platform - FULLY DEPLOYED & OPERATIONAL**  
> Combining infrastructure monitoring, anomaly detection, and ChatOps for proactive cloud management.

[![AWS Free Tier](https://img.shields.io/badge/AWS-Free%20Tier-green)](https://aws.amazon.com/free/)
[![Terraform](https://img.shields.io/badge/Terraform-1.12+-blue)](https://terraform.io)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-DEPLOYED-success)](README.md)

---

## 🎯 What is SmartCloudOps AI?

**SmartCloudOps AI** is an end-to-end DevOps automation platform that:

- 🔍 **Monitors** your infrastructure with Prometheus + Grafana ✅ **OPERATIONAL**
- 🧠 **Detects** anomalies using machine learning algorithms ⏳ **Phase 3 Ready**
- 🔧 **Auto-heals** issues with intelligent remediation scripts ⏳ **Phase 4 Ready**
- 💬 **Provides** ChatOps interface for natural language queries ✅ **DEPLOYED**
- 💰 **Costs** $0/month using AWS Free Tier ✅ **VERIFIED**

## 🏆 **CURRENT STATUS: PHASES 0-2 COMPLETE (1 DAY AHEAD)**

### ✅ **LIVE INFRASTRUCTURE**
- **🖥️ Grafana Dashboard**: [http://3.89.229.102:3000](http://3.89.229.102:3000) (HTTP 200 ✅)
- **📊 Prometheus Monitoring**: [http://3.89.229.102:9090](http://3.89.229.102:9090) (Running ✅)
- **🤖 ChatOps Flask App**: [http://3.239.197.127:5000](http://3.239.197.127:5000) (Deployed ✅)
- **📦 Total AWS Resources**: 25 deployed successfully
- **💰 Monthly Cost**: $0.00 (AWS Free Tier)

---

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites
```bash
# Check requirements
terraform --version  # >= 1.0
aws --version        # >= 2.0
python3 --version    # >= 3.10
```

### 2. Generate SSH Key
```bash
ssh-keygen -t rsa -b 2048 -f ~/.ssh/smartcloudops-ai
```

### 3. Configure & Deploy
```bash
git clone https://github.com/Dileepreddy93/smartcloudops-ai.git
cd smartcloudops-ai/terraform

# Add your SSH public key to terraform-free-tier.tfvars
echo 'ssh_public_key = "'$(cat ~/.ssh/smartcloudops-ai.pub)'"' >> terraform-free-tier.tfvars

# Deploy infrastructure
terraform init
terraform apply -var-file="terraform-free-tier.tfvars"
```

### 4. Access Services
```bash
# Get service URLs
terraform output grafana_url      # Grafana dashboard
terraform output flask_app_url    # ChatOps API
terraform output prometheus_url   # Metrics

# Example: Test ChatOps
curl -X POST http://<app-ip>:5000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "system status"}'
```

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "AWS Free Tier VPC"
        subgraph "Monitoring (t2.micro)"
            A[Prometheus] 
            B[Grafana]
            C[Node Exporter]
        end
        
        subgraph "Application (t2.micro)"
            D[Flask API]
            E[ChatOps Bot]
            F[ML Engine]
        end
        
        G[S3: ML Models]
        H[S3: Logs]
        I[CloudWatch]
    end
    
    J[User] --> B
    J --> D
    A --> C
    A --> F
    D --> G
    D --> H
    D --> I
```

---

## 📊 Current Status

| Phase | Status | Completion |
|-------|--------|------------|
| **Phase 0**: Foundation & Setup | ✅ Complete | 100% |
| **Phase 1**: Infrastructure & Monitoring | ✅ Complete | 100% |
| **Phase 2**: Flask App & ChatOps | 🔄 In Progress | 75% |
| **Phase 3**: ML Anomaly Detection | ⏳ Pending | 0% |
| **Phase 4**: Auto-Remediation | ⏳ Pending | 0% |
| **Phase 5**: GPT Integration | ⏳ Pending | 0% |
| **Phase 6**: Testing & Security | ⏳ Pending | 0% |
| **Phase 7**: Production Launch | ⏳ Pending | 0% |

👉 **See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed progress**

---

## 🔧 Features

### ✅ **Currently Available**
- **Infrastructure as Code**: Complete Terraform setup
- **Monitoring Stack**: Prometheus + Grafana + Node Exporter
- **Cost Optimized**: $0/month AWS Free Tier deployment
- **Auto-Deployment**: User data scripts for instant setup
- **Basic ChatOps**: REST API endpoints for system queries

### 🔄 **In Development**
- **GPT Integration**: Natural language processing
- **CI/CD Pipeline**: GitHub Actions automation
- **Enhanced Dashboards**: Custom Grafana visualizations

### ⏳ **Planned Features**
- **ML Anomaly Detection**: Isolation Forest algorithms
- **Auto-Remediation**: Intelligent healing scripts
- **Advanced ChatOps**: Conversational AI interface
- **Security Hardening**: IAM least privilege, secrets management

---

## 🛠️ Technology Stack

### **Infrastructure**
- **Cloud**: AWS (Free Tier optimized)
- **IaC**: Terraform 1.12+
- **Compute**: 2x EC2 t2.micro instances
- **Storage**: S3 buckets (5GB each)
- **Networking**: VPC with public subnets

### **Monitoring**
- **Metrics**: Prometheus
- **Visualization**: Grafana
- **Logs**: CloudWatch + S3
- **Alerting**: CloudWatch Alarms

### **Application**
- **Backend**: Python 3.10+ Flask
- **ML**: Scikit-learn, Prophet
- **AI**: OpenAI GPT API
- **Container**: Docker
- **CI/CD**: GitHub Actions

---

## 📁 Project Structure

```
smartcloudops-ai/
├── terraform/                 # Infrastructure as Code
│   ├── main.tf               # Main Terraform configuration
│   ├── variables.tf          # Variable definitions
│   ├── outputs.tf            # Output values
│   ├── user_data/            # EC2 bootstrap scripts
│   └── FREE_TIER_DEPLOYMENT.md
├── app/                      # Flask application
│   ├── main.py              # Main application
│   └── requirements.txt     # Python dependencies
├── scripts/                  # Automation scripts
│   └── remediation/         # Auto-healing scripts
├── ml_models/               # ML models and training
├── docs/                    # Documentation
├── .github/workflows/       # CI/CD pipelines
├── PROJECT_STATUS.md        # Detailed progress tracking
└── README.md               # This file
```

---

## 🔍 Monitoring & Observability

### **Grafana Dashboards**
- **System Metrics**: CPU, Memory, Disk usage
- **Application Metrics**: API response times, error rates
- **ML Metrics**: Anomaly detection accuracy, model performance

### **Available Endpoints**
```bash
# Health check
GET /health

# System status
GET /status

# ChatOps queries
POST /query
{
  "query": "What's the current CPU usage?"
}

# Application logs
GET /logs
```

### **Key Metrics**
- Response time: <200ms target
- Uptime: 99.9% target
- Error rate: <1% target
- Anomaly detection accuracy: >85% target

---

## 💰 Cost Analysis

### **Current**: $0/month (AWS Free Tier)
| Resource | Quantity | Free Tier Limit | Used | Status |
|----------|----------|-----------------|------|--------|
| EC2 t2.micro | 2 instances | 750 hrs/month each | ~1,440 hrs | ✅ FREE |
| S3 Storage | 2 buckets | 5GB each | <1GB | ✅ FREE |
| CloudWatch Logs | All logs | 5GB ingestion | <1GB | ✅ FREE |
| Data Transfer | Outbound | 15GB/month | <5GB | ✅ FREE |

### **Previous**: $70/month (Production Setup)
- ❌ ALB: $20/month → ✅ Direct EC2 access
- ❌ RDS MySQL: $15/month → ✅ Local SQLite  
- ❌ ECS Fargate: $25/month → ✅ t2.micro instances
- ❌ NAT Gateway: $10/month → ✅ Public subnets only

---

## 🚦 Getting Started

### **For Developers**
1. **Fork** the repository
2. **Follow** the Quick Start guide above
3. **Read** [PROJECT_STATUS.md](PROJECT_STATUS.md) for current work
4. **Check** open issues for contribution opportunities

### **For DevOps Engineers**
1. **Deploy** the infrastructure using Terraform
2. **Access** Grafana at `http://<monitoring-ip>:3000` (admin/admin123)
3. **Monitor** system metrics and set up alerts
4. **Test** ChatOps API endpoints

### **For Data Scientists**
1. **Explore** the ML models in `ml_models/` directory
2. **Review** anomaly detection algorithms (Phase 3)
3. **Contribute** to model improvement and validation

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### **Current Priorities**
1. **GPT Integration** (Phase 2)
2. **CI/CD Pipeline** setup
3. **ML Anomaly Detection** (Phase 3)
4. **Documentation** improvements

### **Development Setup**
```bash
# Clone and setup
git clone https://github.com/Dileepreddy93/smartcloudops-ai.git
cd smartcloudops-ai

# Install dependencies
pip install -r app/requirements.txt

# Run tests
pytest tests/

# Start development server
python app/main.py
```

---

## 📋 Roadmap

### **Q3 2025 (Current)**
- ✅ Infrastructure & Monitoring (Phase 1)
- 🔄 ChatOps Development (Phase 2)
- ⏳ ML Integration (Phase 3)

### **Q4 2025**
- Auto-Remediation (Phase 4)
- Advanced ChatOps (Phase 5)
- Security & Testing (Phase 6)

### **Q1 2026**
- Production Launch (Phase 7)
- Community Feedback
- Feature Enhancements

---

## 🆘 Support

### **Documentation**
- 📖 [PROJECT_STATUS.md](PROJECT_STATUS.md) - Detailed progress
- 🚀 [FREE_TIER_DEPLOYMENT.md](terraform/FREE_TIER_DEPLOYMENT.md) - Deployment guide
- 🏗️ [Architecture docs](docs/) - Technical details

### **Community**
- 🐛 [Issues](https://github.com/Dileepreddy93/smartcloudops-ai/issues) - Bug reports
- 💡 [Discussions](https://github.com/Dileepreddy93/smartcloudops-ai/discussions) - Ideas
- 📧 Email: dileepreddy93@example.com

### **Troubleshooting**
```bash
# Check service status
ssh ec2-user@<monitoring-ip> './health-check.sh'
ssh ec2-user@<application-ip> './app-status.sh'

# View logs
journalctl -u smartcloudops-ai -f
tail -f /var/log/cloud-init-output.log
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **AWS Free Tier** for enabling zero-cost development
- **Terraform** for infrastructure automation
- **Prometheus/Grafana** for monitoring excellence
- **Open Source Community** for inspiration and tools

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

Made with ❤️ by [Dileep Reddy](https://github.com/Dileepreddy93)

</div>
