#!/bin/bash

# VPS Auto-Deploy Script for Autopicker Platform
# This script runs on your VPS to pull latest changes and restart services

set -e  # Exit on any error

PROJECT_DIR="/home/julie/autopicker-platform"
REPO_URL="https://github.com/campersurfer/Autopicker.git"
LOG_FILE="/home/julie/autopicker_deploy.log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Starting Autopicker Platform Deployment ==="

# Create project directory if it doesn't exist
if [ ! -d "$PROJECT_DIR" ]; then
    log "Creating project directory: $PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    git clone "$REPO_URL" .
else
    cd "$PROJECT_DIR"
    log "Pulling latest changes from GitHub..."
    git fetch origin
    git reset --hard origin/main
fi

# Navigate to the backend directory
cd "$PROJECT_DIR/multimodal-llm-platform/backend"

log "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

log "Installing/updating Python dependencies..."
pip install --upgrade pip
pip install -r requirements_simple.txt

log "Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp ../.env.example .env
    log "Created .env file - please update with your API keys"
else
    log ".env file already exists"
fi

# Create uploads directory
mkdir -p uploads

# Stop existing service if running
log "Stopping existing Autopicker service..."
pkill -f "simple_api.py" || true
sleep 2

# Start the service using uvicorn properly
log "Starting Autopicker Platform service..."
nohup python -m uvicorn simple_api:app --host 0.0.0.0 --port 8001 --workers 1 > ../autopicker.log 2>&1 &
SERVICE_PID=$!

# Wait a moment and check if service started
sleep 5
if ps -p $SERVICE_PID > /dev/null; then
    log "✅ Autopicker Platform started successfully (PID: $SERVICE_PID)"
    
    # Test the service
    sleep 10
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        log "✅ Health check passed - service is responding"
    else
        log "⚠️  Health check failed - service may not be fully ready"
    fi
else
    log "❌ Failed to start Autopicker Platform service"
    exit 1
fi

log "=== Deployment completed successfully ==="
log "Service running on: http://$(hostname -I | awk '{print $1}'):8001"
log "View logs: tail -f $PROJECT_DIR/autopicker.log"

# Create a status file
echo "{ \"status\": \"running\", \"pid\": $SERVICE_PID, \"deployed_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"version\": \"$(git rev-parse HEAD)\" }" > /home/julie/autopicker_status.json

log "Status file created: /home/julie/autopicker_status.json"