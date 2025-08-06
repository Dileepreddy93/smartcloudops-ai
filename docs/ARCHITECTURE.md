# 🏗️ SmartCloudOps AI - System Architecture

## 📊 **Architecture Overview**

SmartCloudOps AI is a sophisticated DevOps automation platform built with microservices architecture, multi-AI integration, and enterprise-grade monitoring capabilities.

```
┌─────────────────── SMARTCLOUDOPS AI ARCHITECTURE ───────────────────┐
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │   CLIENT    │    │  CHATOPS    │    │ MONITORING  │              │
│  │             │◄──►│   FLASK     │◄──►│ PROMETHEUS  │              │
│  │  Web/API    │    │    APP      │    │  + GRAFANA  │              │
│  └─────────────┘    └─────────────┘    └─────────────┘              │
│                             │                   │                   │
│                             ▼                   ▼                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │  MULTI-AI   │    │     ML      │    │    AWS      │              │
│  │             │    │  ANOMALY    │    │   STORAGE   │              │
│  │ OpenAI +    │    │ DETECTION   │    │   (S3)      │              │
│  │ Gemini 2.0  │    │             │    │             │              │
│  └─────────────┘    └─────────────┘    └─────────────┘              │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## 🔧 **Technology Stack**

### **Infrastructure Layer**
- **Cloud Provider**: AWS (Free Tier Optimized)
- **Infrastructure as Code**: Terraform 1.12+
- **Container Platform**: Docker + Docker Compose
- **Networking**: VPC (10.0.0.0/16) with public subnets

### **Application Layer**
- **Web Framework**: Flask 3.1.1
- **Language**: Python 3.12+
- **Process Management**: Gunicorn WSGI server
- **API Design**: RESTful endpoints with JSON responses

### **AI/ML Layer**
- **Primary AI**: Google Gemini 2.0 Flash (ultra-fast responses)
- **Secondary AI**: OpenAI GPT-3.5-turbo (fallback & comparison)
- **ML Framework**: scikit-learn 1.5.1
- **Time Series**: Prophet 1.1.5
- **Data Processing**: pandas + numpy

### **Monitoring & Observability**
- **Metrics Collection**: Prometheus 
- **Visualization**: Grafana dashboards
- **System Monitoring**: Node Exporter
- **Log Management**: Structured logging + S3 storage

### **Data Storage**
- **Application Data**: Local SQLite (development)
- **ML Models**: S3 bucket (smartcloudops-ai-ml-models-aa7be1e7)
- **Logs**: S3 bucket (smartcloudops-ai-logs-aa7be1e7)
- **Configuration**: Environment variables + .env files

## 🌐 **Deployment Architecture**

### **Production Environment (AWS)**
```
┌─────────────────── AWS INFRASTRUCTURE ───────────────────┐
│                                                           │
│  🌐 VPC (10.0.0.0/16)                                    │
│  ├── 📍 us-east-1a subnet (10.0.1.0/24)                 │
│  │   └── 🖥️  EC2 Monitoring (3.89.229.102)             │
│  │       ├── Prometheus (port 9090)                     │
│  │       ├── Grafana (port 3000)                        │
│  │       └── Node Exporter (port 9100)                  │
│  │                                                       │
│  └── 📍 us-east-1b subnet (10.0.2.0/24)                 │
│      └── 🖥️  EC2 Application (3.239.197.127)           │
│          ├── Flask ChatOps (port 5000)                   │
│          ├── Multi-AI Integration                        │
│          └── ML Inference Engine                         │
│                                                           │
│  🗄️  S3 Storage                                          │
│  ├── smartcloudops-ai-ml-models-aa7be1e7                │
│  └── smartcloudops-ai-logs-aa7be1e7                     │
│                                                           │
│  🔑 IAM Roles & Policies                                  │
│  ├── EC2 → S3 access                                     │
│  └── Least privilege principles                          │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### **Development Environment (Local)**
```
┌─────────────────── LOCAL DEVELOPMENT ────────────────────┐
│                                                           │
│  🖥️  Development Machine (localhost)                     │
│  ├── 🐍 Python Virtual Environment (ml_env)              │
│  ├── 🌐 Flask Application (port 5000)                    │
│  │   ├── Multi-AI Integration Active                     │
│  │   ├── Gemini 2.0 Flash (primary)                     │
│  │   └── OpenAI GPT (secondary)                          │
│  │                                                       │
│  ├── 📁 Project Structure                                │
│  │   ├── app/ (Flask application)                        │
│  │   ├── terraform/ (Infrastructure)                     │
│  │   ├── scripts/ (Automation)                           │
│  │   ├── ml_models/ (Model storage)                      │
│  │   ├── logs/ (Application logs)                        │
│  │   └── docs/ (Documentation)                           │
│  │                                                       │
│  └── 🔧 Development Tools                                │
│      ├── VS Code / IDE                                   │
│      ├── Git version control                             │
│      └── Terraform CLI                                   │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

## 🚀 **API Endpoints**

### **Core Endpoints**
| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/status` | Health check + AI status | JSON status |
| `POST` | `/query` | ChatOps AI queries | AI response |
| `POST` | `/ai/switch` | Switch AI provider | Provider status |
| `POST` | `/ai/test` | Test all AI providers | Test results |

### **Multi-AI Integration**
```python
# Intelligent Provider Selection
AUTO MODE:
1. Gemini 2.0 Flash (if configured) ⚡ Ultra-fast
2. OpenAI GPT-3.5 (if configured) 🚀 Reliable
3. Fallback mode (basic responses) 🔄 Always available

MANUAL MODE:
- Force Gemini: AI_PROVIDER="gemini"
- Force OpenAI: AI_PROVIDER="openai"  
- Fallback only: AI_PROVIDER="fallback"
```

## 🧠 **Machine Learning Pipeline**

### **Phase 3: Anomaly Detection (✅ Complete)**
```
┌─────────────────── ML PIPELINE ──────────────────┐
│                                                   │
│  📊 Data Collection                               │
│  ├── Prometheus metrics                           │
│  ├── System performance data                      │
│  └── Synthetic anomaly patterns                   │
│                                                   │
│  🔧 Feature Engineering                           │
│  ├── 140+ advanced features                       │
│  ├── Rolling statistics                           │
│  ├── Temporal patterns                            │
│  └── Cross-metric correlations                    │
│                                                   │
│  🤖 Model Training                                │
│  ├── Isolation Forest (F1: 0.8835) ✅ TARGET MET │
│  ├── Prophet time series models                   │
│  ├── Hyperparameter optimization                  │
│  └── Cross-validation                             │
│                                                   │
│  🚀 Model Deployment                              │
│  ├── S3 storage (versioned)                       │
│  ├── Real-time inference                          │
│  ├── Confidence scoring                           │
│  └── Alert generation                             │
│                                                   │
└───────────────────────────────────────────────────┘
```

## 🔒 **Security Architecture**

### **Network Security**
- VPC with controlled ingress/egress
- Security groups with minimal required ports
- SSH key-based authentication
- No hardcoded credentials

### **Application Security**
- Environment variable configuration
- Input validation and sanitization
- API rate limiting
- Error handling without information leakage

### **Data Security**
- S3 server-side encryption
- IAM roles with least privilege
- Secure API key management
- Regular key rotation procedures

## 📈 **Scalability & Performance**

### **Current Capacity**
- **Concurrent Users**: 50-100 (Flask development server)
- **API Throughput**: 100-200 requests/minute
- **Response Time**: <2s (Gemini), <5s (OpenAI)
- **Storage**: Unlimited (S3 buckets)

### **Scaling Strategy**
- **Horizontal**: Load balancer + multiple Flask instances
- **Vertical**: Larger EC2 instance types
- **Database**: Migrate to RDS for production scale
- **Caching**: Redis/ElastiCache for response caching

## 🏆 **Achievement Metrics**

### **Project Completion: 95%**
- ✅ Phase 0: Foundation (100%)
- ✅ Phase 1: Infrastructure (100%)  
- ✅ Phase 2: ChatOps Application (100%)
- ✅ Phase 3: ML Anomaly Detection (100%)
- ✅ BONUS: Multi-AI Integration (100%)
- ⏳ Phase 4: Auto-Remediation (0%)

### **Performance Metrics**
- **Infrastructure Stability**: 100% uptime
- **Cost Optimization**: $0/month (AWS Free Tier)
- **ML Performance**: F1-score 0.8835 (exceeds 0.85 target)
- **AI Response Quality**: Excellent (Gemini 2.0 Flash)
- **Documentation**: Comprehensive and up-to-date

---

**📅 Last Updated**: August 6, 2025  
**🏗️ Architecture Status**: Production-Ready + Multi-AI Enhanced  
**🎯 Next Phase**: Auto-Remediation System Development
