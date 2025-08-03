#!/bin/bash

# Start API script for Multimodal LLM Platform
# This script starts the FastAPI server with proper configuration

echo "🚀 Starting Multimodal LLM Platform API..."

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export API_PORT=8001
export API_HOST=0.0.0.0
export DEBUG=true
export LOG_LEVEL=info

# Remove DATABASE_URL to avoid LiteLLM database issues for now
unset DATABASE_URL

echo "📝 Environment configured:"
echo "  - API Port: $API_PORT"
echo "  - Host: $API_HOST"
echo "  - Debug: $DEBUG"
echo "  - Log Level: $LOG_LEVEL"

# Start the FastAPI server
echo "🌟 Starting FastAPI server..."
uvicorn main:app --host $API_HOST --port $API_PORT --reload

echo "✅ API server stopped."