#!/bin/bash

# Quick sync script for development changes
# Syncs only the backend code without full deployment

set -e

# Configuration
VPS_HOST="${VPS_HOST:-38.242.229.78}"
VPS_USER="${VPS_USER:-julie}"
VPS_PATH="${VPS_PATH:-/home/julie/Autopicker}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Sync backend code
sync_backend() {
    log_info "Syncing backend code to VPS..."
    
    # Sync the backend directory
    rsync -avz --delete \
        --exclude="venv/" \
        --exclude="__pycache__/" \
        --exclude="*.pyc" \
        --exclude="uploads/" \
        --exclude="test_*/" \
        ./multimodal-llm-platform/backend/ \
        "$VPS_USER@$VPS_HOST:$VPS_PATH/multimodal-llm-platform/backend/"
    
    log_success "Backend code synced"
}

# Restart services
restart_services() {
    log_info "Restarting services on VPS..."
    
    ssh "$VPS_USER@$VPS_HOST" << 'EOF'
# Restart the API service
sudo systemctl restart autopicker-api

# Restart LiteLLM if config changed
sudo systemctl restart autopicker-litellm

# Wait a moment for services to start
sleep 3

# Check status
echo "Service status:"
sudo systemctl is-active autopicker-api && echo "API: Running" || echo "API: Failed"
sudo systemctl is-active autopicker-litellm && echo "LiteLLM: Running" || echo "LiteLLM: Failed"
EOF
    
    log_success "Services restarted"
}

# Test the deployment
test_deployment() {
    log_info "Testing deployment..."
    
    # Test API health
    if curl -s "http://$VPS_HOST:8001/health" > /dev/null; then
        log_success "API is responding"
    else
        echo "❌ API not responding"
    fi
    
    # Test LiteLLM health
    if curl -s "http://$VPS_HOST:8000/health" > /dev/null; then
        log_success "LiteLLM is responding"
    else
        echo "❌ LiteLLM not responding"
    fi
}

# Main execution
main() {
    echo "🔄 Quick Sync to VPS"
    echo "==================="
    
    case "${1:-sync}" in
        "sync")
            sync_backend
            restart_services
            test_deployment
            ;;
        "restart")
            restart_services
            test_deployment
            ;;
        "test")
            test_deployment
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [sync|restart|test|help]"
            echo "  sync    - Sync code and restart services (default)"
            echo "  restart - Just restart services"
            echo "  test    - Test deployment health"
            echo "  help    - Show this help"
            ;;
        *)
            echo "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
    
    echo ""
    echo "🌐 Services:"
    echo "  API:     http://$VPS_HOST:8001"
    echo "  LiteLLM: http://$VPS_HOST:8000"
}

main "$@"