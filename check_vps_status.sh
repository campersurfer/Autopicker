#!/bin/bash

# VPS Status Check Script for Autopicker
# Quick status check for all services running on the VPS

set -e

# Configuration
VPS_HOST="${VPS_HOST:-38.242.229.78}"
VPS_USER="${VPS_USER:-julie}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if service is running
check_service() {
    local service_name=$1
    local port=$2
    local endpoint=${3:-"health"}
    
    echo -n "Checking $service_name on port $port... "
    
    # Check if port is open
    if ssh "$VPS_USER@$VPS_HOST" "nc -z localhost $port" 2>/dev/null; then
        # Try to get a response from the health endpoint
        local response=$(ssh "$VPS_USER@$VPS_HOST" "curl -s -o /dev/null -w '%{http_code}' http://localhost:$port/$endpoint" 2>/dev/null)
        
        if [[ "$response" == "200" ]]; then
            log_success "Running (HTTP 200)"
        else
            log_warning "Port open but no valid response (HTTP $response)"
        fi
    else
        log_error "Not responding"
    fi
}

# Main status check
main() {
    echo "🔍 Autopicker VPS Status Check"
    echo "=============================="
    echo "VPS: $VPS_USER@$VPS_HOST"
    echo ""
    
    # Check SSH connection
    log_info "Testing SSH connection..."
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$VPS_USER@$VPS_HOST" exit 2>/dev/null; then
        log_success "SSH connection OK"
    else
        log_error "SSH connection failed"
        exit 1
    fi
    echo ""
    
    # Check core services
    log_info "Checking core services..."
    check_service "Autopicker API" "8001" "health"
    check_service "LiteLLM Proxy" "8000" "health"
    echo ""
    
    # Check infrastructure services
    log_info "Checking infrastructure services..."
    check_service "PostgreSQL" "5432" ""
    check_service "Redis" "6379" ""
    check_service "MinIO" "9000" "minio/health/live"
    check_service "SearXNG" "8888" ""
    check_service "Whisper ASR" "9000" "docs"
    echo ""
    
    # Check Ollama
    log_info "Checking Ollama..."
    echo -n "Ollama service... "
    if ssh "$VPS_USER@$VPS_HOST" "systemctl is-active ollama" >/dev/null 2>&1; then
        log_success "Running"
        
        echo -n "Available models... "
        local model_count=$(ssh "$VPS_USER@$VPS_HOST" "ollama list | grep -v NAME | wc -l" 2>/dev/null)
        if [[ "$model_count" -gt 0 ]]; then
            log_success "$model_count models available"
        else
            log_warning "No models installed"
        fi
    else
        log_error "Not running"
    fi
    echo ""
    
    # System resources
    log_info "System resources..."
    ssh "$VPS_USER@$VPS_HOST" << 'EOF'
echo -n "CPU Usage: "
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//'

echo -n "Memory Usage: "
free | grep Mem | awk '{printf "%.1f%% (%.1fG/%.1fG)\n", $3/$2 * 100.0, $3/1024/1024, $2/1024/1024}'

echo -n "Disk Usage: "
df -h / | awk 'NR==2{printf "%s (%s used)\n", $5, $3}'

echo -n "Load Average: "
uptime | awk -F'load average:' '{print $2}'
EOF
    echo ""
    
    # Check for any issues
    log_info "Checking for issues..."
    
    # Check if any services are failed
    local failed_services=$(ssh "$VPS_USER@$VPS_HOST" "systemctl list-units --failed --no-pager" | grep -c "failed" || echo "0")
    
    if [[ "$failed_services" -gt 0 ]]; then
        log_warning "$failed_services failed systemd services detected"
        ssh "$VPS_USER@$VPS_HOST" "systemctl list-units --failed --no-pager"
    else
        log_success "No failed services"
    fi
    
    # Check disk space
    local disk_usage=$(ssh "$VPS_USER@$VPS_HOST" "df / | awk 'NR==2{print \$5}' | sed 's/%//'" 2>/dev/null)
    if [[ "$disk_usage" -gt 85 ]]; then
        log_warning "Disk usage is high: ${disk_usage}%"
    elif [[ "$disk_usage" -gt 95 ]]; then
        log_error "Disk usage is critical: ${disk_usage}%"
    else
        log_success "Disk usage OK: ${disk_usage}%"
    fi
    
    echo ""
    echo "🌐 Service URLs:"
    echo "  API:      http://$VPS_HOST:8001"
    echo "  LiteLLM:  http://$VPS_HOST:8000"
    echo "  MinIO:    http://$VPS_HOST:9001"
    echo "  SearXNG:  http://$VPS_HOST:8888"
    echo ""
    echo "🔧 Management Commands:"
    echo "  Deploy:   ./deploy_vps.sh"
    echo "  Logs:     ssh $VPS_USER@$VPS_HOST 'journalctl -u autopicker-api -f'"
    echo "  Restart:  ssh $VPS_USER@$VPS_HOST 'sudo systemctl restart autopicker-api'"
}

# Handle command line arguments
case "${1:-status}" in
    "status"|"check"|"")
        main
        ;;
    "quick"|"q")
        echo "🔍 Quick Status Check"
        check_service "API" "8001" "health"
        check_service "LiteLLM" "8000" "health"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [status|quick|help]"
        echo "  status  - Full status check (default)"
        echo "  quick   - Quick health check only"
        echo "  help    - Show this help"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac