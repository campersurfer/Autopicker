# Autopicker - Multimodal LLM Platform

A comprehensive multimodal LLM platform supporting file processing, web search, and concurrent operations across multiple AI providers.

## 🚀 Features

- **Multimodal File Processing**: PDF, images, DOCX, XLSX, CSV, JSON, and text files
- **Web Search Integration**: SearXNG-powered search with fallback options
- **Concurrent Processing**: Parallel file processing and search operations
- **Multiple LLM Providers**: OpenAI, Anthropic, Google, Cohere, and local Ollama models
- **RESTful API**: FastAPI-based backend with comprehensive endpoints
- **Docker Support**: Complete containerized development environment

## 🏗️ Architecture

```
├── backend/                 # FastAPI backend
│   ├── main.py             # Main API application
│   ├── processors/         # File processing modules
│   ├── services/          # Business logic services
│   └── requirements.txt   # Python dependencies
├── docker-compose.yml     # Local development stack
├── searxng/              # Search engine configuration
└── plan.md              # 12-week development roadmap
```

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.13
- **LLM Router**: LiteLLM with multi-provider support
- **Database**: PostgreSQL, Redis
- **Storage**: MinIO (S3-compatible)
- **Search**: SearXNG
- **Audio**: Whisper ASR
- **Containerization**: Docker & Docker Compose

## 🔧 Development Setup

### Prerequisites
- Python 3.13+
- Docker & Docker Compose
- Git

### Local Development
```bash
# Clone the repository
git clone <repository-url>
cd Autopicker

# Start infrastructure services
docker-compose up -d

# Install backend dependencies
cd multimodal-llm-platform/backend
pip install -r requirements.txt

# Run the API server
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### VPS Deployment
```bash
# Deploy to VPS (requires SSH access)
./deploy_vps.sh

# Check deployment status
./check_vps_status.sh
```

## 📡 API Endpoints

### Core Features
- `POST /api/v1/chat/completions` - Chat with any LLM provider
- `POST /api/v1/upload` - Upload files for processing
- `POST /api/v1/files/{file_id}/process` - Process uploaded files
- `POST /api/v1/search` - Web search functionality
- `POST /api/v1/process/concurrent` - Concurrent file + search processing

### File Processing
- Supports: PDF, DOCX, XLSX, CSV, JSON, TXT, images
- Extracts text, metadata, and structured content
- Provides summaries and content analysis

### Search Integration
- Web search via SearXNG
- Context-enhanced search using file content
- Multiple search engines support

### Concurrent Operations
- Parallel file processing
- Simultaneous search operations
- Batch processing for large datasets

## 🤖 LLM Provider Support

### Cloud Providers
- **OpenAI**: GPT-3.5, GPT-4, GPT-4 Turbo, GPT-4o
- **Anthropic**: Claude 3 (Opus, Sonnet, Haiku)
- **Google**: Gemini Pro, Gemini Pro Vision
- **Cohere**: Command R, Command R+

### Local Models (VPS)
- **Ollama**: Llama 3.2, LLaVA (multimodal)
- Self-hosted on VPS for cost efficiency

## 🔄 Development Workflow (CI/CD Ready!)

1. **Local Development**: Code and test on Mac
2. **Version Control**: Push changes to GitHub (`git push origin main`)
3. **Automatic Deployment**: GitHub Actions deploys to VPS automatically
4. **Production Testing**: Live at http://38.242.229.78
5. **Health Check**: http://38.242.229.78/health

### Manual Deployment Scripts
- `./scripts/deploy_to_vps.sh` - Full deployment setup
- `./scripts/update_vps.sh` - Quick updates only

## 📋 Development Progress

Following a 12-week development plan (see `plan.md`):

- ✅ **Phase 1**: Development Environment (Week 1-2)
- ✅ **Phase 2**: Web Search Integration (Week 3)
- 🔄 **Phase 3**: Multimodal Models (Week 4-5)
- 📋 **Phase 4**: Web Application (Week 6-7)
- 📋 **Phase 5**: Mobile App (Week 8-9)
- 📋 **Phase 6**: Production Prep (Week 10-11)
- 📋 **Phase 7**: Launch Prep (Week 12)

## 🚀 Quick Start

```bash
# Test the API
curl http://localhost:8001/health

# Upload a file
curl -X POST "http://localhost:8001/api/v1/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@example.pdf"

# Process the file
curl -X POST "http://localhost:8001/api/v1/files/{file_id}/process"

# Search the web
curl -X POST "http://localhost:8001/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "num_results": 5}'
```

## 🔐 Environment Variables

```bash
# LLM Provider API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
COHERE_API_KEY=your_cohere_key

# VPS Configuration
VPS_HOST=your_vps_ip
VPS_USER=your_username
VPS_PATH=/path/to/project
```

## 🏥 Health Monitoring

- `/health` - API health check
- `/api/v1/search/status` - Search service status
- VPS monitoring via deployment scripts

## 📚 Documentation

- **API Docs**: Available at `/docs` (Swagger UI)
- **ReDoc**: Available at `/redoc`
- **Development Plan**: See `plan.md` for detailed roadmap

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of a comprehensive multimodal AI platform development initiative.