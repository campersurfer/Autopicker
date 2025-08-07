#!/bin/bash

# Minimal deployment script for Autopicker VPS
set -e

VPS_HOST="38.242.229.78"
VPS_USER="julie"

echo "🚀 Minimal VPS Deployment..."

# Function to deploy minimal API
deploy_minimal() {
    echo "📦 Deploying minimal API..."
    ssh "$VPS_USER@$VPS_HOST" << 'ENDSSH'
        # Navigate to backend directory
        cd /home/julie/autopicker/multimodal-llm-platform/backend
        
        # Install minimal dependencies
        pip3 install --user fastapi uvicorn python-multipart aiofiles httpx PyPDF2 python-docx openpyxl Pillow pydantic
        
        # Kill any existing processes
        pkill -f "python.*main.py" || echo "No existing processes"
        pkill -f "uvicorn.*main" || echo "No existing uvicorn processes"
        
        # Create minimal version of main.py without problematic imports
        cat > minimal_main.py << 'EOF'
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Autopicker Minimal API",
    description="Minimal API for testing deployment",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "autopicker-minimal"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Autopicker Minimal API is running!",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

# Simple test endpoint
@app.post("/test")
async def test_endpoint(data: dict = None):
    """Simple test endpoint"""
    return {
        "message": "Test endpoint working!",
        "received_data": data,
        "status": "success"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
        
        # Start the minimal API
        echo "🚀 Starting minimal API server..."
        nohup python3 -m uvicorn minimal_main:app --host 0.0.0.0 --port 8000 > /tmp/autopicker_minimal.log 2>&1 &
        
        # Wait for startup
        sleep 5
        
        # Check if service is running
        if pgrep -f "uvicorn.*minimal_main" > /dev/null; then
            echo "✅ Minimal API service is running"
            echo "📝 Process info:"
            ps aux | grep "uvicorn.*minimal_main" | grep -v grep
        else
            echo "❌ Service failed to start"
            echo "📝 Log output:"
            tail -20 /tmp/autopicker_minimal.log
            exit 1
        fi
ENDSSH
    
    # Quick health check
    echo "🏥 Health check..."
    sleep 3
    if curl -f "http://$VPS_HOST:8000/health" 2>/dev/null; then
        echo "✅ Health check passed!"
        echo "🌐 Service is running at: http://$VPS_HOST:8000"
        echo "📚 API docs at: http://$VPS_HOST:8000/docs"
        echo "📝 Test endpoint at: http://$VPS_HOST:8000/test"
    else
        echo "❌ Health check failed"
        ssh "$VPS_USER@$VPS_HOST" "tail -20 /tmp/autopicker_minimal.log"
        exit 1
    fi
}

# Main function
main() {
    echo "🎯 Minimal Autopicker VPS Deployment"
    echo "===================================="
    
    deploy_minimal
    
    echo ""
    echo "🎉 Minimal deployment completed!"
    echo "🌐 Application: http://$VPS_HOST:8000"
    echo "🏥 Health check: http://$VPS_HOST:8000/health"
    echo "📚 API docs: http://$VPS_HOST:8000/docs"
    echo "🧪 Test endpoint: http://$VPS_HOST:8000/test"
}

# Run main function
main "$@"