# Deployment Guide - Autopicker Platform

Complete deployment guide for setting up the Autopicker Multimodal LLM Platform in production.

## 🚀 Quick Setup

### 1. Environment Configuration

Copy and configure environment variables:

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your actual values
nano .env
```

### 2. Required API Keys Setup

The platform uses an **Enhanced Model Router** that provides access to multiple AI models through different providers.

#### OpenRouter (Recommended - Primary Provider)

OpenRouter provides access to multiple models through a single API:

1. **Sign up**: Visit https://openrouter.ai/keys
2. **Create API key**: Generate a new API key in your dashboard
3. **Add credits**: Add $5-10 for testing, more for production
4. **Configure**: Set `OPENROUTER_API_KEY` in your `.env` file

```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

**Models available through OpenRouter**:
- **GPT-4o** - Latest OpenAI model with vision
- **GPT-4o Mini** - Fast and cost-effective GPT-4
- **Claude 3.5 Sonnet** - Excellent for analysis and reasoning
- **Claude 3 Haiku** - Fast and affordable Claude model
- **Llama 3.1 405B/70B/8B** - Open-source models
- **Gemini Pro** - Google's flagship model

#### Direct Provider APIs (Optional Fallbacks)

For additional redundancy, you can also configure direct provider access:

**OpenAI Direct**:
```bash
# Visit: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-key-here
```

**Anthropic Direct**:
```bash
# Visit: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

### 3. Model Selection Configuration

Configure how the system selects models:

```bash
# Automatic model selection (recommended)
DEFAULT_MODEL=auto

# Preference settings
PREFER_FAST_MODELS=false      # Set true for faster responses
PREFER_CHEAP_MODELS=false     # Set true for cost optimization
MAX_COST_PER_1K_TOKENS=10.0   # Maximum cost per 1K tokens

# Domain for API headers
DOMAIN_NAME=autopicker.ai
```

## 💰 Pricing Tiers

The platform supports **dual pricing tiers** for competitive advantage:

- **Standard Tier**: OpenRouter (easy setup, all models)
- **Enterprise Tier**: Direct APIs (better margins, enterprise pricing)

See [Pricing Tiers Guide](pricing-tiers.md) for detailed strategy and implementation.

## 🔧 Production Deployment

### Docker Deployment

1. **Build the image**:
```bash
docker build -t autopicker-platform .
```

2. **Run with environment file**:
```bash
docker run -d \
  --name autopicker \
  --env-file .env \
  -p 8001:8001 \
  autopicker-platform
```

### VPS Deployment

1. **Update system**:
```bash
sudo apt update && sudo apt upgrade -y
```

2. **Install Python 3.11+**:
```bash
sudo apt install python3.11 python3.11-venv python3.11-dev
```

3. **Clone and setup**:
```bash
git clone https://github.com/yourusername/multimodal-llm-platform.git
cd multimodal-llm-platform
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Start the service**:
```bash
# Development
uvicorn backend.simple_api:app --host 0.0.0.0 --port 8001

# Production with gunicorn
gunicorn backend.simple_api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

## 🔐 API Key Management

### Cost Optimization

**For Development**:
```bash
PREFER_CHEAP_MODELS=true
MAX_COST_PER_1K_TOKENS=1.0
```

**For Production**:
```bash
PREFER_FAST_MODELS=false
MAX_COST_PER_1K_TOKENS=5.0
```

### Model Selection Strategy

The Enhanced Model Router automatically selects models based on:

- **Request complexity** (message length, file count, file size)
- **Required capabilities** (text, vision, function calling)
- **Cost constraints** (configurable limits)
- **Performance preferences** (speed vs. accuracy)

**Complexity Scoring**:
- **Low** (0-30): Simple text questions → Fast/cheap models
- **Medium** (30-70): Multi-file analysis → Balanced models  
- **High** (70-100): Complex reasoning → Powerful models

### Fallback Strategy

1. **Primary**: OpenRouter (if API key available)
2. **Secondary**: Direct provider APIs (if configured)
3. **Fallback**: Local Ollama model (always available)

## 📊 Monitoring & Health Checks

### Health Endpoint

Monitor your deployment:

```bash
curl http://your-server:8001/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "models_available": 12,
  "openrouter_status": "connected"
}
```

### Model Status

Check available models:

```bash
curl http://your-server:8001/api/v1/models
```

### Performance Metrics

Key metrics to monitor:
- Response time per request
- Model selection distribution
- API key usage and costs
- Error rates by provider

## 🔒 Security Configuration

### Rate Limiting

```bash
RATE_LIMIT_REQUESTS_PER_MINUTE=100
```

### CORS Configuration

```bash
CORS_ORIGINS=https://your-domain.com,https://app.your-domain.com
```

### File Upload Security

```bash
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_TYPES=pdf,docx,txt,jpg,jpeg,png,mp3,wav
```

## 🚨 Troubleshooting

### Common Issues

**"No API key configured"**:
- Ensure `OPENROUTER_API_KEY` is set in `.env`
- Check API key is valid and has credits
- Verify `.env` file is loaded correctly

**"Model not available"**:
- Check OpenRouter account has sufficient credits
- Verify model is still available on OpenRouter
- System will fallback to available models automatically

**"Slow responses"**:
- Set `PREFER_FAST_MODELS=true` for development
- Check internet connection to API providers
- Consider using smaller files or more specific questions

**"High costs"**:
- Set lower `MAX_COST_PER_1K_TOKENS` value
- Enable `PREFER_CHEAP_MODELS=true`
- Monitor usage through OpenRouter dashboard

### Debug Mode

Enable detailed logging:

```bash
DEBUG=true
LOG_LEVEL=debug
```

### API Key Testing

Test your configuration:

```bash
# Test basic chat
curl -X POST http://localhost:8001/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello, test message"}],
    "model": "auto"
  }'
```

## 📋 Pre-Deployment Checklist

- [ ] Environment variables configured in `.env`
- [ ] OpenRouter API key added and funded
- [ ] Model preferences set appropriately
- [ ] Health endpoint responding
- [ ] Rate limiting configured
- [ ] CORS origins set for your domain
- [ ] File upload limits appropriate
- [ ] Monitoring/logging configured
- [ ] SSL/TLS certificates configured (for production)
- [ ] Firewall rules configured
- [ ] Backup strategy in place

## 🔄 Updates and Maintenance

### Updating the Platform

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart autopicker
```

### API Key Rotation

1. Generate new API key in provider dashboard
2. Update `.env` file with new key
3. Restart the service
4. Verify functionality
5. Revoke old key

### Monitoring Costs

- **OpenRouter**: Check dashboard at https://openrouter.ai/activity
- **OpenAI**: Monitor usage at https://platform.openai.com/usage
- **Anthropic**: Check console at https://console.anthropic.com/

## 🆘 Support

- **System Health**: Check `/health` endpoint
- **API Status**: Check `/api/v1/models` endpoint  
- **Logs**: Monitor application logs for errors
- **Documentation**: Reference API docs at `/docs`

For issues with specific providers:
- **OpenRouter**: https://openrouter.ai/docs
- **OpenAI**: https://platform.openai.com/docs
- **Anthropic**: https://docs.anthropic.com/

---

Ready to deploy? Start with the [Quick Setup](#quick-setup) section and follow the steps for your deployment environment.