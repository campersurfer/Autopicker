#!/bin/bash
"""
Production deployment script with monitoring setup for VPS
Deploys the Autopicker platform with comprehensive monitoring
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VPS_HOST="38.242.229.78"
VPS_USER="julie"
VPS_PATH="/home/julie/autopicker-platform"
LOCAL_PATH="/Users/juliebush/Autopicker/multimodal-llm-platform"

echo -e "${BLUE}🚀 Starting Production Deployment with Monitoring...${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we can connect to VPS
echo -e "${BLUE}🔍 Checking VPS connection...${NC}"
if ! ssh -o ConnectTimeout=10 $VPS_USER@$VPS_HOST "echo 'Connection successful'" > /dev/null 2>&1; then
    print_error "Cannot connect to VPS at $VPS_HOST"
    echo "Please check:"
    echo "  1. VPS is running"
    echo "  2. SSH key is configured"
    echo "  3. Network connectivity"
    exit 1
fi
print_status "VPS connection established"

# Create VPS directory structure
echo -e "${BLUE}📁 Setting up VPS directory structure...${NC}"
ssh $VPS_USER@$VPS_HOST "
    mkdir -p $VPS_PATH/{backend,web-app,mobile-app,logs,monitoring}
    mkdir -p $VPS_PATH/backend/{uploads,venv}
    mkdir -p $VPS_PATH/monitoring/{dashboards,alerts,logs}
"
print_status "Directory structure created"

# Sync backend code
echo -e "${BLUE}📤 Syncing backend code...${NC}"
rsync -avz --delete \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache/' \
    --exclude='uploads/' \
    $LOCAL_PATH/backend/ $VPS_USER@$VPS_HOST:$VPS_PATH/backend/
print_status "Backend code synced"

# Sync monitoring dashboard
echo -e "${BLUE}📊 Setting up monitoring dashboard...${NC}"
rsync -avz $LOCAL_PATH/web-app/src/app/analytics/ $VPS_USER@$VPS_HOST:$VPS_PATH/monitoring/dashboards/
print_status "Monitoring dashboard files synced"

# Install dependencies on VPS
echo -e "${BLUE}📦 Installing Python dependencies on VPS...${NC}"
ssh $VPS_USER@$VPS_HOST "
    cd $VPS_PATH/backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d 'venv' ]; then
        python3 -m venv venv
    fi
    
    # Activate and install
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements_simple.txt
"
print_status "Python dependencies installed"

# Check Ollama status
echo -e "${BLUE}🤖 Checking Ollama status...${NC}"
OLLAMA_STATUS=$(ssh $VPS_USER@$VPS_HOST "
    if pgrep -f ollama > /dev/null; then
        echo 'running'
    else
        echo 'stopped'
    fi
")

if [ "$OLLAMA_STATUS" = "stopped" ]; then
    print_warning "Ollama is not running, attempting to start..."
    ssh $VPS_USER@$VPS_HOST "
        # Try to start ollama
        nohup ollama serve > /tmp/ollama.log 2>&1 &
        sleep 5
        
        # Check if it started
        if pgrep -f ollama > /dev/null; then
            echo 'Ollama started successfully'
        else
            echo 'Failed to start Ollama automatically'
        fi
    "
else
    print_status "Ollama is running"
fi

# Check if model is available
echo -e "${BLUE}🧠 Checking AI model availability...${NC}"
MODEL_CHECK=$(ssh $VPS_USER@$VPS_HOST "
    curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q 'llama3.2' && echo 'available' || echo 'missing'
")

if [ "$MODEL_CHECK" = "missing" ]; then
    print_warning "llama3.2:1b model not found, downloading..."
    ssh $VPS_USER@$VPS_HOST "
        ollama pull llama3.2:1b
    "
    print_status "Model downloaded"
else
    print_status "AI model is available"
fi

# Create systemd service for the API
echo -e "${BLUE}⚙️  Setting up systemd service...${NC}"
ssh $VPS_USER@$VPS_HOST "
    # Create systemd service file
    sudo tee /etc/systemd/system/autopicker-api.service > /dev/null << 'EOF'
[Unit]
Description=Autopicker Multimodal LLM API
After=network.target
Wants=network.target

[Service]
Type=simple
User=$VPS_USER
WorkingDirectory=$VPS_PATH/backend
Environment=PATH=$VPS_PATH/backend/venv/bin
ExecStart=$VPS_PATH/backend/venv/bin/python simple_api.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits
MemoryMax=2G
CPUQuota=80%

# Environment variables
Environment=PYTHONUNBUFFERED=1
Environment=LOG_LEVEL=INFO

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable autopicker-api
"
print_status "Systemd service configured"

# Start the service
echo -e "${BLUE}🚀 Starting API service...${NC}"
ssh $VPS_USER@$VPS_HOST "
    sudo systemctl restart autopicker-api
    sleep 5
    
    # Check status
    if sudo systemctl is-active --quiet autopicker-api; then
        echo 'API service is running'
    else
        echo 'API service failed to start'
        sudo systemctl status autopicker-api --no-pager -l
        exit 1
    fi
"
print_status "API service is running"

# Test API endpoints
echo -e "${BLUE}🧪 Testing API endpoints...${NC}"
sleep 10  # Give service time to fully start

# Test health endpoint
HEALTH_STATUS=$(ssh $VPS_USER@$VPS_HOST "
    curl -s -o /dev/null -w '%{http_code}' http://localhost:8001/health
")

if [ "$HEALTH_STATUS" = "200" ]; then
    print_status "Health endpoint is responding"
else
    print_warning "Health endpoint returned status: $HEALTH_STATUS"
fi

# Test monitoring endpoint
MONITORING_STATUS=$(ssh $VPS_USER@$VPS_HOST "
    curl -s -o /dev/null -w '%{http_code}' http://localhost:8001/api/v1/monitoring/health
")

if [ "$MONITORING_STATUS" = "200" ]; then
    print_status "Monitoring endpoint is active"
else
    print_warning "Monitoring endpoint returned status: $MONITORING_STATUS"
fi

# Create monitoring script
echo -e "${BLUE}📊 Setting up monitoring alerts...${NC}"
ssh $VPS_USER@$VPS_HOST "
    # Create monitoring check script
    cat > $VPS_PATH/monitoring/check_health.sh << 'EOF'
#!/bin/bash
# Health check script for monitoring

API_URL='http://localhost:8001/api/v1/monitoring/health'
LOG_FILE='$VPS_PATH/monitoring/logs/health_check.log'

# Create log directory
mkdir -p $VPS_PATH/monitoring/logs

# Check API health
RESPONSE=\$(curl -s \$API_URL 2>/dev/null)
HTTP_CODE=\$(curl -s -o /dev/null -w '%{http_code}' \$API_URL 2>/dev/null)

TIMESTAMP=\$(date '+%Y-%m-%d %H:%M:%S')

if [ \"\$HTTP_CODE\" = \"200\" ]; then
    # Parse status from response
    STATUS=\$(echo \$RESPONSE | grep -o '\"status\":\"[^\"]*\"' | cut -d'\"' -f4)
    echo \"[\$TIMESTAMP] API Health: \$STATUS (HTTP \$HTTP_CODE)\" >> \$LOG_FILE
    
    # Check for critical alerts
    CRITICAL_ALERTS=\$(echo \$RESPONSE | grep -o '\"critical_alerts\":[0-9]*' | cut -d':' -f2)
    
    if [ \"\$CRITICAL_ALERTS\" -gt 0 ]; then
        echo \"[\$TIMESTAMP] WARNING: \$CRITICAL_ALERTS critical alerts detected\" >> \$LOG_FILE
        # Here you could add email/slack notifications
    fi
else
    echo \"[\$TIMESTAMP] ERROR: API health check failed (HTTP \$HTTP_CODE)\" >> \$LOG_FILE
fi
EOF

    chmod +x $VPS_PATH/monitoring/check_health.sh
"

# Set up cron job for monitoring
ssh $VPS_USER@$VPS_HOST "
    # Add cron job for health checks every 5 minutes
    (crontab -l 2>/dev/null; echo '*/5 * * * * $VPS_PATH/monitoring/check_health.sh') | crontab -
    
    # Add daily log rotation
    (crontab -l 2>/dev/null; echo '0 0 * * * find $VPS_PATH/monitoring/logs -name \"*.log\" -mtime +7 -delete') | crontab -
"
print_status "Monitoring alerts configured"

# Display final status
echo -e "${BLUE}📋 Deployment Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get system status
ssh $VPS_USER@$VPS_HOST "
    echo -e '🖥️  System Status:'
    echo '  • CPU Usage:' \$(top -bn1 | grep 'Cpu(s)' | awk '{print \$2}' | cut -d'%' -f1)%
    echo '  • Memory Usage:' \$(free | grep Mem | awk '{printf \"%.1f%%\", \$3/\$2 * 100.0}')
    echo '  • Disk Usage:' \$(df -h / | awk 'NR==2 {print \$5}')
    echo
    echo -e '🚀 Services Status:'
    echo '  • API Service:' \$(sudo systemctl is-active autopicker-api)
    echo '  • Ollama:' \$(pgrep -f ollama > /dev/null && echo 'running' || echo 'stopped')
    echo
    echo -e '🌐 Endpoints:'
    echo '  • API: http://$VPS_HOST:8001'
    echo '  • Health: http://$VPS_HOST:8001/health'
    echo '  • Monitoring: http://$VPS_HOST:8001/api/v1/monitoring/health'
    echo '  • Docs: http://$VPS_HOST:8001/docs'
    echo
    echo -e '📊 Monitoring:'
    echo '  • Health checks: Every 5 minutes'
    echo '  • Log files: $VPS_PATH/monitoring/logs/'
    echo '  • System metrics: Real-time via API'
    echo '  • Auto log rotation: Daily cleanup'
"

print_status "Production deployment with monitoring completed successfully!"
echo -e "${GREEN}🎉 Your Autopicker platform is now running 24/7 with full monitoring!${NC}"
echo
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Access monitoring dashboard: http://$VPS_HOST:8001/api/v1/monitoring/health"
echo "  2. Check logs: ssh $VPS_USER@$VPS_HOST 'tail -f $VPS_PATH/monitoring/logs/health_check.log'"
echo "  3. Monitor service: ssh $VPS_USER@$VPS_HOST 'sudo systemctl status autopicker-api'"
echo "  4. View real-time metrics via the monitoring API endpoints"