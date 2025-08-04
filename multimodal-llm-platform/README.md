# Multimodal LLM Platform

A comprehensive platform for processing multimodal content using various LLM providers with intelligent routing and concurrent processing capabilities.

## Project Structure

```
.
├── backend/          # FastAPI backend with LiteLLM integration
├── routing/          # Intelligent model routing logic
├── web-app/          # Next.js web application
├── mobile-app/       # React Native mobile app
├── docs/             # Documentation
└── k8s/              # Kubernetes deployment files
```

## Features

- **Enhanced Model Router**: Access to 10+ AI models through OpenRouter (GPT-4, Claude, Gemini, Llama)
- **Multimodal Processing**: Handle text, images, audio, and documents  
- **Intelligent Routing**: Smart model selection based on content complexity and cost
- **Concurrent Processing**: Parallel file processing and streaming responses
- **Multiple Interfaces**: Web app, mobile app, and OpenAI-compatible API
- **Production Ready**: Auto-scaling, monitoring, and enterprise-grade reliability

## Quick Start

### 1. Setup API Keys

```bash
# Copy environment template
cp .env.example .env

# Add your OpenRouter API key (recommended)
OPENROUTER_API_KEY=your-key-here
```

Get your OpenRouter API key at https://openrouter.ai/keys

### 2. Start Development

```bash
# Start local development environment
docker-compose up -d

# Run backend
cd backend && uvicorn simple_api:app --reload --host 0.0.0.0 --port 8001

# Run web app  
cd web-app && npm run dev

# Run mobile app
cd mobile-app && expo start
```

### 3. Access the Platform

- **Interactive API**: http://localhost:8001/docs
- **Web App**: http://localhost:3000
- **Mobile App**: Expo Go app

## Available Models

The Enhanced Model Router provides access to:

- **GPT-4o** - Latest OpenAI model with vision capabilities
- **GPT-4o Mini** - Fast and cost-effective GPT-4
- **Claude 3.5 Sonnet** - Excellent for analysis and reasoning  
- **Claude 3 Haiku** - Fast and affordable Claude model
- **Llama 3.1 405B/70B/8B** - Powerful open-source models
- **Gemini Pro** - Google's flagship model
- **Local Ollama** - Free fallback model (always available)

## Development Progress

This project follows a 12-week development plan. See [plan.md](../plan.md) for detailed timeline and tasks.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details