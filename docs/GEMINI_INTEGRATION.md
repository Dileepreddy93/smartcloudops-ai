# 🤖 Gemini 2.0 Flash Integration Guide

## Overview

SmartCloudOps AI now supports **Google Gemini 2.0 Flash** alongside OpenAI GPT for enhanced ChatOps functionality. This multi-AI approach provides:

- **Redundancy**: Fallback between providers
- **Performance**: Choose the best AI for specific tasks
- **Cost Optimization**: Flexible provider switching
- **Enhanced Capabilities**: Leverage different AI strengths

---

## 🚀 Quick Setup

### 1. Get Your Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Create a new project or use existing
3. Generate API key from the API Keys section
4. Copy your API key

### 2. Configure Environment

```bash
# Option 1: Environment Variable (Recommended)
export GEMINI_API_KEY="your-gemini-api-key-here"

# Option 2: .env File
echo "GEMINI_API_KEY=your-gemini-api-key-here" >> app/.env

# Optional: Set AI provider preference
export AI_PROVIDER="gemini"  # Options: auto, gemini, openai, fallback
```

### 3. Install Dependencies

```bash
# Install Gemini SDK
pip install google-generativeai==0.8.3

# Or install all requirements
pip install -r app/requirements.txt
```

### 4. Restart Application

```bash
# If running locally
python app/main.py

# If running on EC2 via systemd
sudo systemctl restart smartcloudops-ai
```

---

## 🔧 API Configuration

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `GEMINI_API_KEY` | Your Google AI API key | None | `AIzaSyC...` |
| `AI_PROVIDER` | Active AI provider | `auto` | `gemini`, `openai`, `auto`, `fallback` |
| `OPENAI_API_KEY` | OpenAI API key (optional) | None | `sk-...` |

### Provider Selection Logic

```python
# Auto mode priority:
1. Gemini (if configured)
2. OpenAI (if configured) 
3. Fallback (basic responses)

# Manual mode:
- gemini: Force Gemini usage
- openai: Force OpenAI usage
- fallback: Basic responses only
```

---

## 📡 Enhanced API Endpoints

### Status Check with AI Info
```bash
curl http://your-server:5000/status
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-06T16:30:00.000Z",
  "version": "2.2.1",
  "phase": "2.2 - Multi-AI Integration (OpenAI + Gemini)",
  "ai_status": {
    "provider": "gemini",
    "openai_available": true,
    "gemini_available": true,
    "openai_configured": true,
    "gemini_configured": true
  }
}
```

### Enhanced ChatOps Query
```bash
curl -X POST http://your-server:5000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I check disk usage on Linux?"}'
```

**Response:**
```json
{
  "query": "How do I check disk usage on Linux?",
  "response": "Use 'df -h' to check disk usage by filesystem or 'du -h' for directory usage. For detailed analysis, try 'ncdu' for interactive disk usage.",
  "timestamp": "2025-08-06T16:30:00.000Z",
  "status": "success",
  "ai_provider": "gemini",
  "phase": "2.2 - Multi-AI Integration"
}
```

### Switch AI Provider
```bash
curl -X POST http://your-server:5000/ai/switch \
  -H "Content-Type: application/json" \
  -d '{"provider": "gemini"}'
```

### Test All Providers
```bash
curl -X POST http://your-server:5000/ai/test
```

---

## 🎯 Gemini 2.0 Flash Features

### Model Capabilities
- **Speed**: Ultra-fast response times
- **Context**: Large context window
- **Multimodal**: Text processing (image support coming)
- **Quality**: High-quality technical responses

### Optimized Settings
```python
generation_config = {
    "temperature": 0.7,      # Balanced creativity
    "max_output_tokens": 200, # Concise responses
    "top_p": 0.8,            # Focused sampling
    "top_k": 40              # Token diversity
}
```

---

## 🔄 Provider Comparison

| Feature | Gemini 2.0 Flash | OpenAI GPT-3.5 | Fallback |
|---------|------------------|-----------------|----------|
| **Speed** | ⚡ Ultra Fast | 🚀 Fast | ⚡ Instant |
| **Quality** | 🎯 Excellent | 🎯 Excellent | ⚠️ Basic |
| **Cost** | 💰 Low | 💰 Medium | 🆓 Free |
| **DevOps Focus** | ✅ Good | ✅ Good | ❌ Generic |
| **Availability** | 🌍 Global | 🌍 Global | ✅ Always |

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Gemini not configured or available"
```bash
# Check API key
echo $GEMINI_API_KEY

# Verify SDK installation
python -c "import google.generativeai; print('✅ Gemini SDK installed')"

# Check logs
curl http://your-server:5000/status | jq '.ai_status'
```

#### 2. API Rate Limits
```bash
# Switch to OpenAI temporarily
curl -X POST http://your-server:5000/ai/switch \
  -d '{"provider": "openai"}'

# Or use fallback mode
curl -X POST http://your-server:5000/ai/switch \
  -d '{"provider": "fallback"}'
```

#### 3. Dependency Issues
```bash
# Reinstall Gemini SDK
pip uninstall google-generativeai
pip install google-generativeai==0.8.3

# Check compatibility
python -c "import google.generativeai as genai; print(f'Version: {genai.__version__}')"
```

### Logs and Monitoring

```bash
# View application logs
journalctl -u smartcloudops-ai -f

# Test connectivity
curl -X POST http://your-server:5000/ai/test

# Check provider status
curl http://your-server:5000/status | jq '.ai_status'
```

---

## 🚀 Production Deployment

### EC2 Instance Configuration

1. **Install Dependencies**
```bash
sudo systemctl stop smartcloudops-ai
cd /opt/smartcloudops-ai
source venv/bin/activate
pip install google-generativeai==0.8.3
```

2. **Set Environment Variables**
```bash
# Add to systemd service file
sudo systemctl edit smartcloudops-ai

# Add environment variables:
[Service]
Environment="GEMINI_API_KEY=your-key-here"
Environment="AI_PROVIDER=auto"
```

3. **Restart Service**
```bash
sudo systemctl daemon-reload
sudo systemctl restart smartcloudops-ai
sudo systemctl status smartcloudops-ai
```

### Security Best Practices

- ✅ Use environment variables (never hardcode keys)
- ✅ Rotate API keys regularly
- ✅ Monitor usage and costs
- ✅ Implement rate limiting
- ✅ Use HTTPS in production

---

## 📊 Usage Examples

### DevOps Queries
```bash
# Infrastructure monitoring
curl -X POST http://your-server:5000/query \
  -d '{"query": "How to monitor CPU usage with Prometheus?"}'

# Troubleshooting
curl -X POST http://your-server:5000/query \
  -d '{"query": "Container keeps restarting, how to debug?"}'

# Automation
curl -X POST http://your-server:5000/query \
  -d '{"query": "Write a bash script to backup database daily"}'
```

### Performance Testing
```bash
# Test response times
time curl -X POST http://your-server:5000/query \
  -d '{"query": "Explain Docker networking"}'

# Compare providers
curl -X POST http://your-server:5000/ai/test
```

---

## 🎯 Next Steps

1. ✅ **Get Gemini API Key**: ~~Visit [Google AI Studio](https://aistudio.google.com/)~~ **COMPLETED**
2. ✅ **Configure Environment**: ~~Set `GEMINI_API_KEY` environment variable~~ **CONFIGURED**
3. ✅ **Test Integration**: ~~Use `/ai/test` endpoint~~ **TESTED & WORKING**
4. **Monitor Usage**: Check costs and performance
5. **Optimize Settings**: Adjust temperature and token limits

🚀 **Integration Status**: **ACTIVE** - Gemini 2.0 Flash is now your primary AI provider!

For support, check the [main documentation](../README.md) or create an issue on GitHub.
