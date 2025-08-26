# SmartCloudOps AI - Complete User Guide

## 🚀 **Welcome to SmartCloudOps AI**

**SmartCloudOps AI** is a comprehensive DevOps automation platform that combines ChatOps, Machine Learning, and Auto-Remediation to streamline your infrastructure operations.

---

## 📋 **Table of Contents**

1. [Quick Start Guide](#quick-start-guide)
2. [Core Features](#core-features)
3. [ChatOps Commands](#chatops-commands)
4. [API Reference](#api-reference)
5. [Monitoring & Alerts](#monitoring--alerts)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## 🚀 **Quick Start Guide**

### **1. Access the Platform**

```bash
# Application URL
http://your-server-ip:5000

# Health Check
curl http://your-server-ip:5000/status
```

### **2. Basic ChatOps Commands**

```bash
# Deploy application
"deploy the smartcloudops app to production"

# Scale infrastructure
"scale servers to 5 instances"

# Monitor system
"show logs of ec2 instances"

# Check costs
"show cost report for this month"
```

### **3. API Usage**

```bash
# Process ChatOps command
curl -X POST http://your-server-ip:5000/api/v1/chatops/process \
  -H "Content-Type: application/json" \
  -d '{"command": "deploy the app to production"}'

# Get system status
curl http://your-server-ip:5000/api/v1/remediation/status
```

---

## 🎯 **Core Features**

### **Phase 1: Infrastructure Management**
- **AWS Resource Management**: VPC, EC2, S3, Security Groups
- **Terraform Automation**: Infrastructure as Code
- **Monitoring Stack**: Prometheus + Grafana

### **Phase 2: ChatOps Application**
- **Flask Web API**: RESTful endpoints
- **GPT Integration**: AI-powered responses
- **Real-time Logging**: Application monitoring

### **Phase 3: ML Anomaly Detection**
- **Predictive Analytics**: Resource usage forecasting
- **Anomaly Detection**: Proactive issue identification
- **Performance Monitoring**: Real-time metrics

### **Phase 4: Auto-Remediation**
- **Rule-based Automation**: Automated incident response
- **Safety Controls**: Manual override capabilities
- **Audit Trails**: Complete action logging

### **Phase 5: NLP-Enhanced ChatOps**
- **Natural Language Processing**: Intent recognition
- **Entity Extraction**: Command parameter parsing
- **AWS Integration**: Safe command execution

---

## 💬 **ChatOps Commands**

### **Deployment Commands**

| Command | Description | Example |
|---------|-------------|---------|
| Deploy | Deploy application to environment | `"deploy the app to production"` |
| Rollback | Revert to previous version | `"rollback to previous version"` |
| Release | Release new version | `"release version 2.1.0"` |

### **Scaling Commands**

| Command | Description | Example |
|---------|-------------|---------|
| Scale Up | Increase resources | `"scale servers to 5 instances"` |
| Scale Down | Decrease resources | `"scale down to 2 instances"` |
| Auto-scale | Enable auto-scaling | `"enable auto-scaling for the app"` |

### **Monitoring Commands**

| Command | Description | Example |
|---------|-------------|---------|
| Show Logs | Display application logs | `"show logs of ec2 instances"` |
| Check Health | System health status | `"check health of the application"` |
| Get Metrics | Performance metrics | `"get metrics for the last hour"` |

### **Cost Management**

| Command | Description | Example |
|---------|-------------|---------|
| Cost Report | View spending | `"show cost report for this month"` |
| Budget Alert | Set budget limits | `"set budget alert at $1000"` |
| Optimize Costs | Cost optimization | `"optimize costs for the infrastructure"` |

### **Security Commands**

| Command | Description | Example |
|---------|-------------|---------|
| Security Scan | Vulnerability scan | `"run security scan on the system"` |
| Compliance Check | Compliance audit | `"check compliance status"` |
| Access Review | Review permissions | `"review user access permissions"` |

---

## 🔌 **API Reference**

### **Core Endpoints**

#### **Application Status**
```http
GET /status
```
**Response:**
```json
{
  "status": "success",
  "data": {
    "application": "SmartCloudOps AI",
    "version": "1.0.0",
    "status": "operational",
    "uptime": "24h 30m 15s"
  }
}
```

#### **ChatOps Processing**
```http
POST /api/v1/chatops/process
```
**Request:**
```json
{
  "command": "deploy the app to production",
  "user_id": "user123",
  "channel": "slack"
}
```
**Response:**
```json
{
  "status": "success",
  "command": "deploy the app to production",
  "nlp_result": {
    "intent": "deploy",
    "entities": {"environment": "production"},
    "confidence": 0.95
  },
  "action_plan": {
    "action": "deploy",
    "estimated_time": "5m",
    "safety_checks": ["deployment_approval", "environment_validation"]
  }
}
```

#### **Remediation Status**
```http
GET /api/v1/remediation/status
```
**Response:**
```json
{
  "status": "success",
  "data": {
    "engine_status": "active",
    "active_rules": 5,
    "recent_actions": 3,
    "last_action": "2025-08-26T10:30:00Z"
  }
}
```

### **ChatOps Endpoints**

#### **Get Supported Intents**
```http
GET /api/v1/chatops/intents
```

#### **Get Command History**
```http
GET /api/v1/chatops/history?limit=10
```

#### **Get Statistics**
```http
GET /api/v1/chatops/statistics
```

#### **Execute Action**
```http
POST /api/v1/chatops/execute
```

#### **Health Check**
```http
GET /api/v1/chatops/health
```

### **Remediation Endpoints**

#### **Test Remediation**
```http
POST /api/v1/remediation/test
```

#### **Get Rules**
```http
GET /api/v1/remediation/rules
```

#### **Add Rule**
```http
POST /api/v1/remediation/rules
```

### **ML Endpoints**

#### **ML Health**
```http
GET /ml/health
```

#### **Predict Anomaly**
```http
POST /ml/predict
```

#### **Get Metrics**
```http
GET /ml/metrics
```

---

## 📊 **Monitoring & Alerts**

### **Dashboard Access**

#### **Grafana Dashboards**
- **URL**: `http://your-server-ip:3000`
- **Default Credentials**: `admin/admin`
- **Dashboards**:
  - System Overview
  - Application Performance
  - ML Model Metrics
  - Cost Analytics

#### **Prometheus Metrics**
- **URL**: `http://your-server-ip:9090`
- **Metrics Endpoint**: `http://your-server-ip:5000/metrics`

### **Key Metrics to Monitor**

#### **System Metrics**
- **CPU Usage**: Should be <80%
- **Memory Usage**: Should be <85%
- **Disk Usage**: Should be <90%
- **Network I/O**: Monitor for spikes

#### **Application Metrics**
- **Response Time**: Should be <100ms
- **Error Rate**: Should be <1%
- **Throughput**: Monitor request/second
- **Uptime**: Should be >99.9%

#### **ML Metrics**
- **Model Accuracy**: Should be >95%
- **Prediction Latency**: Should be <50ms
- **Model Drift**: Monitor for changes
- **Training Frequency**: Track retraining

### **Alert Configuration**

#### **High CPU Usage**
```yaml
alert: HighCPUUsage
expr: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
for: 5m
labels:
  severity: warning
```

#### **Application Down**
```yaml
alert: ApplicationDown
expr: up{job="smartcloudops-ai"} == 0
for: 1m
labels:
  severity: critical
```

#### **High Error Rate**
```yaml
alert: HighErrorRate
expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
for: 2m
labels:
  severity: warning
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. Application Not Starting**
```bash
# Check application logs
tail -f logs/app.log

# Check port availability
netstat -tlnp | grep :5000

# Restart application
sudo systemctl restart smartcloudops-ai
```

#### **2. ChatOps Commands Not Working**
```bash
# Check NLP service
curl http://localhost:5000/api/v1/chatops/health

# Check AWS credentials
aws sts get-caller-identity

# Test command processing
curl -X POST http://localhost:5000/api/v1/chatops/test \
  -H "Content-Type: application/json" \
  -d '{"command": "deploy the app"}'
```

#### **3. ML Model Issues**
```bash
# Check ML service health
curl http://localhost:5000/ml/health

# Check model files
ls -la ml_models/

# Test prediction
curl -X POST http://localhost:5000/ml/predict \
  -H "Content-Type: application/json" \
  -d '{"data": [1.0, 2.0, 3.0]}'
```

#### **4. Monitoring Issues**
```bash
# Check Prometheus
curl http://localhost:9090/-/healthy

# Check Grafana
curl http://localhost:3000/api/health

# Check metrics endpoint
curl http://localhost:5000/metrics
```

### **Log Analysis**

#### **Application Logs**
```bash
# View recent logs
tail -n 100 logs/app.log

# Search for errors
grep "ERROR" logs/app.log

# Monitor real-time
tail -f logs/app.log | grep -E "(ERROR|WARNING|CRITICAL)"
```

#### **System Logs**
```bash
# Check system logs
sudo journalctl -u smartcloudops-ai -f

# Check service status
sudo systemctl status smartcloudops-ai
```

### **Performance Issues**

#### **High CPU Usage**
```bash
# Check CPU usage
top -p $(pgrep -f smartcloudops)

# Check Python processes
ps aux | grep python

# Monitor resource usage
htop
```

#### **Memory Issues**
```bash
# Check memory usage
free -h

# Check Python memory
ps aux | grep python | awk '{print $6}' | sort -n

# Monitor memory in real-time
watch -n 1 'free -h'
```

---

## 📈 **Best Practices**

### **Security Best Practices**

#### **1. Access Control**
- Use API keys for authentication
- Implement role-based access control
- Regularly rotate credentials
- Monitor access logs

#### **2. Network Security**
- Use HTTPS for all communications
- Implement rate limiting
- Use security groups and firewalls
- Monitor network traffic

#### **3. Data Protection**
- Encrypt data at rest and in transit
- Implement backup strategies
- Use secure logging practices
- Regular security audits

### **Performance Best Practices**

#### **1. Resource Optimization**
- Monitor resource usage regularly
- Implement auto-scaling policies
- Optimize database queries
- Use caching strategies

#### **2. Application Optimization**
- Implement connection pooling
- Use async operations where possible
- Optimize ML model inference
- Monitor response times

#### **3. Monitoring Best Practices**
- Set up comprehensive alerting
- Use multiple monitoring tools
- Implement log aggregation
- Regular performance reviews

### **Operational Best Practices**

#### **1. Deployment**
- Use blue-green deployments
- Implement rollback procedures
- Test in staging environment
- Monitor deployment metrics

#### **2. Incident Response**
- Document incident procedures
- Implement escalation policies
- Use automated remediation
- Post-incident reviews

#### **3. Maintenance**
- Regular system updates
- Database maintenance
- Log rotation and cleanup
- Performance tuning

---

## 📞 **Support & Contact**

### **Getting Help**

#### **Documentation**
- **Project Docs**: `/docs/` directory
- **API Docs**: This guide
- **Architecture**: `docs/MASTER_PROJECT_STATUS.md`

#### **Logs & Debugging**
- **Application Logs**: `logs/app.log`
- **System Logs**: `sudo journalctl -u smartcloudops-ai`
- **Error Reports**: `reports/error_log.md`

#### **Health Checks**
```bash
# Run comprehensive health check
./monitoring/health-check.sh

# Check specific services
curl http://localhost:5000/status
curl http://localhost:5000/ml/health
curl http://localhost:5000/api/v1/remediation/status
```

### **Reporting Issues**

#### **Issue Template**
```
**Issue Description:**
[Describe the problem]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Environment:**
- OS: [Operating System]
- Python Version: [Version]
- SmartCloudOps AI Version: [Version]

**Logs:**
[Relevant log entries]

**Additional Information:**
[Any other relevant details]
```

---

## 🎉 **Conclusion**

SmartCloudOps AI provides a comprehensive DevOps automation platform that combines the power of ChatOps, Machine Learning, and Auto-Remediation. By following this user guide, you can effectively utilize all the platform's features to streamline your infrastructure operations.

### **Key Takeaways**
- ✅ **ChatOps**: Use natural language commands for infrastructure management
- ✅ **ML Integration**: Leverage predictive analytics for proactive monitoring
- ✅ **Auto-Remediation**: Automate incident response and recovery
- ✅ **Monitoring**: Comprehensive observability and alerting
- ✅ **Security**: Enterprise-grade security and compliance

### **Next Steps**
1. **Explore the API**: Test different endpoints and commands
2. **Set up Monitoring**: Configure dashboards and alerts
3. **Implement Best Practices**: Follow security and performance guidelines
4. **Customize**: Adapt the platform to your specific needs
5. **Scale**: Expand usage across your infrastructure

---

**📚 For more information, visit the project documentation or contact the development team.**

*SmartCloudOps AI - Complete User Guide v1.0*

