#!/bin/bash

# Simple deployment script for Autopicker VPS
set -e

VPS_HOST="38.242.229.78"
VPS_USER="julie"
VPS_PATH="/home/julie/autopicker"

echo "🚀 Simple VPS Deployment..."

# Function to deploy and run the simple API
deploy_simple_api() {
    echo "📦 Deploying simple API..."
    ssh "$VPS_USER@$VPS_HOST" << 'ENDSSH'
        # Navigate to project directory
        cd /home/julie/autopicker/multimodal-llm-platform/backend
        
        # Pull latest changes
        git pull origin main || echo "Repository sync issue, continuing..."
        
        # Install basic dependencies only
        pip3 install --user fastapi uvicorn python-multipart aiofiles httpx
        
        # Kill any existing processes
        pkill -f "python.*simple_api.py" || echo "No existing processes"
        pkill -f "uvicorn.*simple_api" || echo "No existing uvicorn processes"
        
        # Start the simple API
        echo "🚀 Starting simple API server..."
        nohup python3 -m uvicorn simple_api:app --host 0.0.0.0 --port 8000 > /tmp/autopicker.log 2>&1 &
        
        # Wait for startup
        sleep 5
        
        # Check if service is running
        if pgrep -f "uvicorn.*simple_api" > /dev/null; then
            echo "✅ Simple API service is running"
            echo "📝 Process info:"
            ps aux | grep "uvicorn.*simple_api" | grep -v grep
        else
            echo "❌ Service failed to start"
            echo "📝 Log output:"
            tail -20 /tmp/autopicker.log
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
    else
        echo "❌ Health check failed"
        ssh "$VPS_USER@$VPS_HOST" "tail -20 /tmp/autopicker.log"
        exit 1
    fi
}

# Main deployment
main() {
    echo "🎯 Simple Autopicker VPS Deployment"
    echo "==================================="
    
    deploy_simple_api
    
    echo ""
    echo "🎉 Simple deployment completed!"
    echo "🌐 Application: http://$VPS_HOST:8000"
    echo "🏥 Health check: http://$VPS_HOST:8000/health"
    echo "📚 API docs: http://$VPS_HOST:8000/docs"
}

# Run main function
main "$@"