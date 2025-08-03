# VPS Deployment Guide

## 🎯 Current Status

✅ **Completed:**
- Removed Ollama from local machine to improve performance
- Set up git repository with complete project structure
- Created VPS deployment automation scripts
- Updated LiteLLM config to use VPS Ollama endpoints
- Implemented development workflow: local → GitHub → VPS

🔄 **Next Steps:**
1. Create GitHub repository and push code
2. Deploy to VPS and install Ollama
3. Test the complete multimodal pipeline

## 🚀 Deployment Workflow

### 1. GitHub Setup
```bash
# Create a new repository on GitHub named "Autopicker"
# Then update the repo URL in deploy_vps.sh and push:

git remote add origin https://github.com/juliebush/Autopicker.git
git branch -M main
git push -u origin main
```

### 2. VPS Deployment
```bash
# Deploy everything to VPS (first time)
./deploy_vps.sh

# Quick sync during development
./sync_to_vps.sh

# Check deployment status
./check_vps_status.sh
```

## 🏗️ VPS Architecture

### Services on VPS:
- **Autopicker API**: Port 8001 (FastAPI backend)
- **LiteLLM Proxy**: Port 8000 (Multi-provider LLM router)
- **Ollama**: Port 11434 (Local models: llama3.2:1b)
- **PostgreSQL**: Port 5432 (Database)
- **Redis**: Port 6379 (Caching)
- **MinIO**: Port 9000/9001 (Object storage)
- **SearXNG**: Port 8888 (Web search)
- **Whisper**: Port 9000 (Audio transcription)

### Systemd Services:
- `autopicker-api.service` - Main API server
- `autopicker-litellm.service` - LiteLLM proxy
- `ollama.service` - Local model server

## 🔧 Development Commands

### Local Development:
```bash
# Test locally
cd multimodal-llm-platform/backend
python3 -m uvicorn main:app --reload --port 8001

# Run tests
python3 test_concurrent.py
python3 test_api.py
```

### VPS Management:
```bash
# Deploy changes
git add . && git commit -m "Update: description" && git push
./sync_to_vps.sh

# Check logs
ssh julie@38.242.229.78 'journalctl -u autopicker-api -f'

# Restart services
ssh julie@38.242.229.78 'sudo systemctl restart autopicker-api'

# Check resources
./check_vps_status.sh
```

## 🌐 Service URLs

After deployment, services will be available at:
- **API Documentation**: http://38.242.229.78:8001/docs
- **LiteLLM**: http://38.242.229.78:8000
- **MinIO Console**: http://38.242.229.78:9001
- **SearXNG**: http://38.242.229.78:8888

## 📊 Resource Usage

**Current VPS Resources:**
- **Storage**: 96GB total, ~23GB free (suitable for multiple projects)
- **RAM**: 3.8GB total, ~2.9GB available
- **CPU**: Adequate for Ollama + services

**Ollama Model Storage:**
- llama3.2:1b ~1.3GB
- Future models can be added as needed

## 🔒 Security Notes

- SSH key authentication to VPS
- Services bound to specific ports
- Firewall configured for necessary ports only
- Environment variables for API keys
- No sensitive data in git repository

## 🚨 Troubleshooting

### Common Issues:
1. **SSH Connection Failed**: Check VPS status and SSH keys
2. **Service Not Starting**: Check logs with `journalctl -u service-name`
3. **Disk Space**: Monitor with `./check_vps_status.sh`
4. **Model Download**: Large models may take time on first setup

### Recovery Commands:
```bash
# Restart all services
ssh julie@38.242.229.78 'sudo systemctl restart autopicker-*'

# Check service status
./check_vps_status.sh

# Full redeployment
./deploy_vps.sh
```

## 🔄 Workflow Summary

1. **Develop locally** - Test and iterate on local machine
2. **Commit changes** - Git commit with descriptive messages  
3. **Push to GitHub** - `git push origin main`
4. **Sync to VPS** - `./sync_to_vps.sh` for quick updates
5. **Monitor status** - `./check_vps_status.sh` for health checks

This workflow keeps your local machine responsive while providing a powerful VPS environment for AI model hosting and 24/7 availability.