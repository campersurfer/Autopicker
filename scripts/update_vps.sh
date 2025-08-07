#!/bin/bash

# Quick update script for pushing changes to VPS
set -e

VPS_HOST="38.242.229.78"
VPS_USER="julie"
VPS_PATH="/home/julie/autopicker"

echo "🔄 Quick update deployment..."

# Function to update code on VPS via git
update_via_git() {
    echo "📡 Updating code via git pull..."
    ssh "$VPS_USER@$VPS_HOST" << 'ENDSSH'
        cd /home/julie/autopicker
        
        # Pull latest changes
        git pull origin main
        
        # Install any new dependencies
        cd multimodal-llm-platform/backend
        source venv/bin/activate
        pip install -r requirements.txt
        
        # Restart the service
        sudo systemctl restart autopicker-backend
        
        # Wait a moment for service to start
        sleep 3
        
        # Check if service is running
        if systemctl is-active --quiet autopicker-backend; then
            echo "✅ Service restarted successfully"
        else
            echo "❌ Service restart failed"
            sudo journalctl -u autopicker-backend --no-pager -l | tail -20
            exit 1
        fi
ENDSSH
    
    # Quick health check
    echo "🏥 Quick health check..."
    sleep 2
    if curl -f "http://$VPS_HOST/health" 2>/dev/null; then
        echo "✅ Update completed successfully!"
        echo "🌐 Service is running at: http://$VPS_HOST"
    else
        echo "❌ Health check failed after update"
        exit 1
    fi
}

# Run the update
update_via_git