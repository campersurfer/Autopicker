#!/bin/bash

# VPS Deployment Script for Autopicker Multimodal LLM Platform
# Deploys the project to VPS and manages the running services

set -e  # Exit on any error

# Configuration
VPS_HOST="${VPS_HOST:-38.242.229.78}"
VPS_USER="${VPS_USER:-julie}"
VPS_PATH="${VPS_PATH:-/home/julie/Autopicker}"
PROJECT_NAME="autopicker"
GITHUB_REPO="https://github.com/campersurfer/Autopicker.git"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we can SSH to the VPS
check_vps_connection() {
    log_info "Checking VPS connection..."
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$VPS_USER@$VPS_HOST" exit 2>/dev/null; then
        log_success "VPS connection successful"
        return 0
    else
        log_error "Cannot connect to VPS. Please check your SSH configuration."
        return 1
    fi
}

# Deploy to VPS
deploy_to_vps() {
    log_info "Starting deployment to VPS..."
    
    # Create deployment script to run on VPS
    cat << 'EOF' > /tmp/vps_deploy.sh
#!/bin/bash
set -e

PROJECT_PATH="/home/julie/Autopicker"
BACKUP_PATH="/home/julie/backups/autopicker-$(date +%Y%m%d-%H%M%S)"

# Create backup of existing installation
if [ -d "$PROJECT_PATH" ]; then
    echo "Creating backup..."
    mkdir -p "$(dirname "$BACKUP_PATH")"
    cp -r "$PROJECT_PATH" "$BACKUP_PATH"
    echo "Backup created at: $BACKUP_PATH"
fi

# Clone or update repository
if [ -d "$PROJECT_PATH" ]; then
    echo "Updating existing repository..."
    cd "$PROJECT_PATH"
    git fetch origin
    git reset --hard origin/main
    git clean -fd
else
    echo "Cloning repository..."
    git clone https://github.com/campersurfer/Autopicker.git "$PROJECT_PATH"
    cd "$PROJECT_PATH"
fi

# Install system dependencies if needed
echo "Checking system dependencies..."
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Install Ollama
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Start Ollama service
    sudo systemctl enable ollama
    sudo systemctl start ollama
    
    # Wait for Ollama to start
    sleep 5
    
    # Pull essential models
    echo "Pulling Ollama models..."
    ollama pull llama3.2:1b
    echo "Ollama setup complete"
fi

# Setup Python environment
echo "Setting up Python environment..."
cd "$PROJECT_PATH/multimodal-llm-platform/backend"

# Install Python dependencies
if ! command -v python3 &> /dev/null; then
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Setup Docker services
echo "Starting Docker services..."
cd "$PROJECT_PATH"
docker-compose down || true
docker-compose up -d postgres redis minio searxng whisper

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Start the API server with systemd service
echo "Setting up API server service..."
sudo tee /etc/systemd/system/autopicker-api.service > /dev/null << EOSERVICE
[Unit]
Description=Autopicker Multimodal LLM Platform API
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=julie
WorkingDirectory=$PROJECT_PATH/multimodal-llm-platform/backend
Environment=PATH=/home/julie/Autopicker/multimodal-llm-platform/backend/venv/bin
ExecStart=/home/julie/Autopicker/multimodal-llm-platform/backend/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOSERVICE

# Start and enable the service
sudo systemctl daemon-reload
sudo systemctl enable autopicker-api
sudo systemctl restart autopicker-api

# Setup LiteLLM service
echo "Setting up LiteLLM service..."
sudo tee /etc/systemd/system/autopicker-litellm.service > /dev/null << EOSERVICE
[Unit]
Description=Autopicker LiteLLM Proxy
After=network.target
After=autopicker-api.service

[Service]
Type=simple
User=julie
WorkingDirectory=$PROJECT_PATH/multimodal-llm-platform/backend
Environment=PATH=/home/julie/Autopicker/multimodal-llm-platform/backend/venv/bin
ExecStart=/home/julie/Autopicker/multimodal-llm-platform/backend/venv/bin/litellm --config litellm_config.yaml --port 8000 --host 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOSERVICE

sudo systemctl daemon-reload
sudo systemctl enable autopicker-litellm
sudo systemctl restart autopicker-litellm

echo "Deployment completed successfully!"
echo "API running on: http://$(hostname -I | awk '{print $1}'):8001"
echo "LiteLLM running on: http://$(hostname -I | awk '{print $1}'):8000"

# Check service status
echo "Service status:"
sudo systemctl status autopicker-api --no-pager
sudo systemctl status autopicker-litellm --no-pager
EOF

    # Copy and execute deployment script on VPS
    log_info "Copying deployment script to VPS..."
    scp /tmp/vps_deploy.sh "$VPS_USER@$VPS_HOST:/tmp/"
    
    log_info "Executing deployment on VPS..."
    ssh "$VPS_USER@$VPS_HOST" "chmod +x /tmp/vps_deploy.sh && /tmp/vps_deploy.sh"
    
    # Cleanup
    rm /tmp/vps_deploy.sh
    
    log_success "Deployment completed!"
}

# Check deployment status
check_deployment() {
    log_info "Checking deployment status..."
    
    ssh "$VPS_USER@$VPS_HOST" << 'EOF'
echo "=== Service Status ==="
sudo systemctl status autopicker-api --no-pager
echo ""
sudo systemctl status autopicker-litellm --no-pager
echo ""

echo "=== API Health Check ==="
curl -s http://localhost:8001/health || echo "API not responding"
echo ""

echo "=== LiteLLM Health Check ==="
curl -s http://localhost:8000/health || echo "LiteLLM not responding"
echo ""

echo "=== Docker Services ==="
docker-compose ps
echo ""

echo "=== Ollama Status ==="
ollama list
echo ""

echo "=== Disk Usage ==="
df -h /
echo ""

echo "=== Memory Usage ==="
free -h
EOF
}

# Main execution
main() {
    echo "🚀 Autopicker VPS Deployment Script"
    echo "===================================="
    
    if ! check_vps_connection; then
        exit 1
    fi
    
    case "${1:-deploy}" in
        "deploy")
            deploy_to_vps
            check_deployment
            ;;
        "status"|"check")
            check_deployment
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [deploy|status|help]"
            echo "  deploy  - Deploy the project to VPS (default)"
            echo "  status  - Check deployment status"
            echo "  help    - Show this help message"
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

main "$@"