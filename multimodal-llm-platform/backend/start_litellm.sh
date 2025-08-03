#!/bin/bash

# Start LiteLLM proxy script
# This script starts the LiteLLM proxy with proper configuration

echo "🚀 Starting LiteLLM Proxy..."

# Activate virtual environment
source venv/bin/activate

# Remove DATABASE_URL to avoid database issues for now
unset DATABASE_URL

echo "📝 Configuration:"
echo "  - Config: litellm_simple_config.yaml"
echo "  - Port: 8000"
echo "  - Database: disabled (for now)"

# Check if config file exists
if [ ! -f "litellm_simple_config.yaml" ]; then
    echo "❌ Error: litellm_simple_config.yaml not found!"
    exit 1
fi

# Start LiteLLM proxy
echo "🌟 Starting LiteLLM proxy..."
echo "⚠️  Note: This will fail without valid API keys in environment variables"
echo "   To use with real API keys, set:"
echo "   export OPENAI_API_KEY=your-key-here"
echo "   export ANTHROPIC_API_KEY=your-key-here"
echo ""

litellm --config litellm_simple_config.yaml --port 8000

echo "✅ LiteLLM proxy stopped."