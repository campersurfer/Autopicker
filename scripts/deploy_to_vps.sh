#!/bin/bash

# Deployment script for Autopicker VPS
set -e

VPS_HOST="38.242.229.78"
VPS_USER="julie"
VPS_PATH="/home/julie/autopicker"
LOCAL_PATH="/Users/juliebush/Autopicker"

echo "🚀 Starting deployment to VPS..."

# Function to check if SSH connection works
check_ssh_connection() {
    echo "🔍 Checking SSH connection..."
    if ssh -o ConnectTimeout=10 "$VPS_USER@$VPS_HOST" "echo 'SSH connection successful'" 2>/dev/null; then
        echo "✅ SSH connection established"
        return 0
    else
        echo "❌ SSH connection failed"
        return 1
    fi
}

# Function to setup VPS directory structure
setup_vps_structure() {
    echo "📁 Setting up VPS directory structure..."
    ssh "$VPS_USER@$VPS_HOST" << 'ENDSSH'
        # Create project directory if it doesn't exist
        mkdir -p /home/julie/autopicker
        mkdir -p /home/julie/autopicker/logs
        mkdir -p /home/julie/autopicker/scripts
        
        # Set permissions
        chmod 755 /home/julie/autopicker
        chmod 755 /home/julie/autopicker/logs
        chmod 755 /home/julie/autopicker/scripts
ENDSSH
    echo "✅ VPS directory structure ready"
}

# Function to sync code to VPS
sync_code() {
    echo "📦 Syncing code to VPS..."
    
    # Use rsync for efficient file transfer
    rsync -avz --delete \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='.env' \
        --exclude='*.log' \
        "$LOCAL_PATH/" "$VPS_USER@$VPS_HOST:$VPS_PATH/"
    
    echo "✅ Code synced successfully"
}

# Function to install dependencies on VPS
install_dependencies() {
    echo "📚 Installing dependencies on VPS..."
    ssh "$VPS_USER@$VPS_HOST" << 'ENDSSH'
        cd /home/julie/autopicker/multimodal-llm-platform/backend
        
        # Update system packages
        sudo apt update -y
        
        # Install Python 3 and pip if not already installed
        sudo apt install -y python3 python3-pip python3-venv
        
        # Create virtual environment if it doesn't exist
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        
        # Activate virtual environment and install requirements
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
ENDSSH
    echo "✅ Dependencies installed"
}

# Function to setup systemd service
setup_systemd_service() {
    echo "🔧 Setting up systemd service..."
    ssh "$VPS_USER@$VPS_HOST" << 'ENDSSH'
        # Create systemd service file
        sudo tee /etc/systemd/system/autopicker-backend.service > /dev/null << 'EOF'
[Unit]
Description=Autopicker Backend Service
After=network.target

[Service]
Type=simple
User=julie
WorkingDirectory=/home/julie/autopicker/multimodal-llm-platform/backend
Environment=PATH=/home/julie/autopicker/multimodal-llm-platform/backend/venv/bin
ExecStart=/home/julie/autopicker/multimodal-llm-platform/backend/venv/bin/python main.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

        # Reload systemd and enable service
        sudo systemctl daemon-reload
        sudo systemctl enable autopicker-backend
ENDSSH
    echo "✅ Systemd service configured"
}

# Function to setup nginx reverse proxy
setup_nginx() {
    echo "🌐 Setting up Nginx reverse proxy..."
    ssh "$VPS_USER@$VPS_HOST" << 'ENDSSH'
        # Install nginx
        sudo apt install -y nginx
        
        # Create nginx configuration
        sudo tee /etc/nginx/sites-available/autopicker > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF
        
        # Enable the site and restart nginx
        sudo ln -sf /etc/nginx/sites-available/autopicker /etc/nginx/sites-enabled/
        sudo rm -f /etc/nginx/sites-enabled/default
        sudo nginx -t
        sudo systemctl enable nginx
        sudo systemctl restart nginx
ENDSSH
    echo "✅ Nginx configured"
}

# Function to start services
start_services() {
    echo "🚀 Starting services..."
    ssh "$VPS_USER@$VPS_HOST" << 'ENDSSH'
        # Start the backend service
        sudo systemctl start autopicker-backend
        sudo systemctl status autopicker-backend --no-pager -l
        
        # Check if service is running
        sleep 3
        if systemctl is-active --quiet autopicker-backend; then
            echo "✅ Backend service is running"
        else
            echo "❌ Backend service failed to start"
            sudo journalctl -u autopicker-backend --no-pager -l
            exit 1
        fi
ENDSSH
    echo "✅ Services started"
}

# Function to perform health check
health_check() {
    echo "🏥 Performing health check..."
    
    # Wait for service to fully start
    sleep 5
    
    # Test local health endpoint on VPS
    ssh "$VPS_USER@$VPS_HOST" << 'ENDSSH'
        # Check local health endpoint
        if curl -f http://localhost:8000/health 2>/dev/null; then
            echo "✅ Local health check passed"
        else
            echo "❌ Local health check failed"
            exit 1
        fi
ENDSSH
    
    # Test external access
    if curl -f "http://$VPS_HOST/health" 2>/dev/null; then
        echo "✅ External health check passed"
    else
        echo "❌ External health check failed"
        return 1
    fi
    
    echo "✅ All health checks passed"
}

# Main deployment function
main() {
    echo "🎯 Autopicker VPS Deployment Script"
    echo "=================================="
    
    # Check prerequisites
    if ! command -v ssh &> /dev/null; then
        echo "❌ SSH not found. Please install SSH client."
        exit 1
    fi
    
    if ! command -v rsync &> /dev/null; then
        echo "❌ rsync not found. Please install rsync."
        exit 1
    fi
    
    # Run deployment steps
    check_ssh_connection || exit 1
    setup_vps_structure
    sync_code
    install_dependencies
    setup_systemd_service
    setup_nginx
    start_services
    health_check
    
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo "🌐 Your application is now available at: http://$VPS_HOST"
    echo "🏥 Health check: http://$VPS_HOST/health"
}

# Run main function
main "$@"