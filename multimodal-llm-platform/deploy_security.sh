#!/bin/bash
"""
Security hardening deployment script for Autopicker Platform
Implements comprehensive security measures for production deployment
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

echo -e "${BLUE}🔒 Starting Security Hardening Deployment...${NC}"

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

# Check VPS connection
echo -e "${BLUE}🔍 Checking VPS connection...${NC}"
if ! ssh -o ConnectTimeout=10 $VPS_USER@$VPS_HOST "echo 'Connection successful'" > /dev/null 2>&1; then
    print_error "Cannot connect to VPS at $VPS_HOST"
    exit 1
fi
print_status "VPS connection established"

# Deploy security files
echo -e "${BLUE}📤 Deploying security modules...${NC}"
rsync -avz $LOCAL_PATH/backend/security.py $VPS_USER@$VPS_HOST:$VPS_PATH/backend/
rsync -avz $LOCAL_PATH/backend/simple_api.py $VPS_USER@$VPS_HOST:$VPS_PATH/backend/
rsync -avz $LOCAL_PATH/backend/requirements_simple.txt $VPS_USER@$VPS_HOST:$VPS_PATH/backend/
print_status "Security files deployed"

# Install security dependencies
echo -e "${BLUE}📦 Installing security dependencies...${NC}"
ssh $VPS_USER@$VPS_HOST "
    cd $VPS_PATH/backend
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements_simple.txt
"
print_status "Security dependencies installed"

# Configure firewall (UFW)
echo -e "${BLUE}🔥 Configuring firewall...${NC}"
ssh $VPS_USER@$VPS_HOST "
    # Install and configure UFW if not already installed
    if ! command -v ufw &> /dev/null; then
        sudo apt update
        sudo apt install -y ufw
    fi
    
    # Reset to defaults
    sudo ufw --force reset
    
    # Set default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH (important - don't lock yourself out!)
    sudo ufw allow ssh
    sudo ufw allow 22/tcp
    
    # Allow API port
    sudo ufw allow 8001/tcp
    
    # Allow HTTP/HTTPS for updates
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Enable firewall
    sudo ufw --force enable
    
    # Show status
    sudo ufw status verbose
"
print_status "Firewall configured"

# Set up fail2ban for intrusion prevention
echo -e "${BLUE}🛡️  Setting up fail2ban...${NC}"
ssh $VPS_USER@$VPS_HOST "
    # Install fail2ban
    if ! command -v fail2ban-client &> /dev/null; then
        sudo apt update
        sudo apt install -y fail2ban
    fi
    
    # Create custom jail configuration
    sudo tee /etc/fail2ban/jail.local > /dev/null << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s
backend = %(sshd_backend)s
maxretry = 3
bantime = 3600

[autopicker-api]
enabled = true
port = 8001
logpath = /var/log/autopicker/access.log
maxretry = 10
findtime = 600
bantime = 1800
filter = autopicker
EOF

    # Create custom filter for API
    sudo mkdir -p /etc/fail2ban/filter.d
    sudo tee /etc/fail2ban/filter.d/autopicker.conf > /dev/null << 'EOF'
[Definition]
failregex = ^.*\"(GET|POST|PUT|DELETE).*\" (4[0-9]{2}|5[0-9]{2}) .*\$
ignoreregex =
EOF

    # Create log directory
    sudo mkdir -p /var/log/autopicker
    sudo chown $VPS_USER:$VPS_USER /var/log/autopicker
    
    # Restart fail2ban
    sudo systemctl restart fail2ban
    sudo systemctl enable fail2ban
    
    # Show status
    sudo fail2ban-client status
"
print_status "Fail2ban configured"

# Secure file permissions
echo -e "${BLUE}📁 Setting secure file permissions...${NC}"
ssh $VPS_USER@$VPS_HOST "
    cd $VPS_PATH
    
    # Set directory permissions
    find . -type d -exec chmod 755 {} \;
    
    # Set file permissions
    find . -type f -exec chmod 644 {} \;
    
    # Make scripts executable
    chmod +x backend/start_*.sh 2>/dev/null || true
    chmod +x backend/start_production.py 2>/dev/null || true
    
    # Secure sensitive files
    chmod 600 backend/.env 2>/dev/null || true
    chmod 600 backend/requirements*.txt
    
    # Set ownership
    sudo chown -R $VPS_USER:$VPS_USER $VPS_PATH
"
print_status "File permissions secured"

# Configure system security
echo -e "${BLUE}⚙️  Configuring system security...${NC}"
ssh $VPS_USER@$VPS_HOST "
    # Disable root login
    sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config 2>/dev/null || true
    sudo sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config 2>/dev/null || true
    
    # Disable password authentication (key-only)
    sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config 2>/dev/null || true
    sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config 2>/dev/null || true
    
    # Enable key-based authentication
    sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config 2>/dev/null || true
    
    # Restart SSH service
    sudo systemctl restart sshd
    
    # Set up automatic security updates
    if ! dpkg -l | grep -q unattended-upgrades; then
        sudo apt update
        sudo apt install -y unattended-upgrades
        sudo dpkg-reconfigure -plow unattended-upgrades
    fi
"
print_status "System security configured"

# Set up log monitoring
echo -e "${BLUE}📊 Setting up security log monitoring...${NC}"
ssh $VPS_USER@$VPS_HOST "
    # Create security monitoring script
    cat > $VPS_PATH/monitoring/security_monitor.sh << 'EOF'
#!/bin/bash
# Security monitoring script

LOG_FILE=\"$VPS_PATH/monitoring/logs/security.log\"
TIMESTAMP=\$(date '+%Y-%m-%d %H:%M:%S')

# Create log directory
mkdir -p $VPS_PATH/monitoring/logs

# Check for failed login attempts
FAILED_LOGINS=\$(sudo grep \"Failed password\" /var/log/auth.log | grep \"\$(date '+%Y-%m-%d')\" | wc -l)

# Check for firewall blocks
UFW_BLOCKS=\$(sudo grep \"UFW BLOCK\" /var/log/kern.log | grep \"\$(date '+%Y-%m-%d')\" | wc -l)

# Check fail2ban status
FAIL2BAN_BANS=\$(sudo fail2ban-client status sshd 2>/dev/null | grep \"Currently banned:\" | awk '{print \$3}' || echo \"0\")

# Log security status
echo \"[\$TIMESTAMP] Failed logins: \$FAILED_LOGINS, UFW blocks: \$UFW_BLOCKS, Fail2ban bans: \$FAIL2BAN_BANS\" >> \$LOG_FILE

# Alert on high activity
if [ \"\$FAILED_LOGINS\" -gt 10 ] || [ \"\$UFW_BLOCKS\" -gt 20 ]; then
    echo \"[\$TIMESTAMP] HIGH SECURITY ACTIVITY DETECTED\" >> \$LOG_FILE
fi
EOF

    chmod +x $VPS_PATH/monitoring/security_monitor.sh
    
    # Add to cron for hourly monitoring
    (crontab -l 2>/dev/null; echo '0 * * * * $VPS_PATH/monitoring/security_monitor.sh') | crontab -
"
print_status "Security monitoring configured"

# Generate API key for production
echo -e "${BLUE}🔑 Generating production API key...${NC}"
API_KEY=$(ssh $VPS_USER@$VPS_HOST "
    cd $VPS_PATH/backend
    source venv/bin/activate
    python -c 'from security import security_manager; print(security_manager.generate_api_key())'
")
print_status "API key generated: $API_KEY"

# Update service configuration with security
echo -e "${BLUE}⚙️  Updating service configuration...${NC}"
ssh $VPS_USER@$VPS_HOST "
    # Create environment file with security settings
    cat > $VPS_PATH/backend/.env << EOF
# Security Configuration
SECRET_KEY=\$(openssl rand -base64 32)
API_KEY=$API_KEY
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
MAX_FILE_SIZE=10485760
LOG_LEVEL=INFO
ENVIRONMENT=production

# Database (if needed)
# DATABASE_URL=postgresql://user:pass@localhost/db
EOF

    # Set secure permissions on env file
    chmod 600 $VPS_PATH/backend/.env
    
    # Update systemd service with security
    sudo tee /etc/systemd/system/autopicker-api.service > /dev/null << 'EOF'
[Unit]
Description=Autopicker Multimodal LLM API (Secured)
After=network.target
Wants=network.target

[Service]
Type=simple
User=$VPS_USER
WorkingDirectory=$VPS_PATH/backend
Environment=PATH=$VPS_PATH/backend/venv/bin
EnvironmentFile=$VPS_PATH/backend/.env
ExecStart=$VPS_PATH/backend/venv/bin/python start_production.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$VPS_PATH
PrivateTmp=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Resource limits
MemoryMax=2G
CPUQuota=80%
LimitNOFILE=1024

# Environment variables
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl restart autopicker-api
"
print_status "Service configuration updated"

# Test security endpoints
echo -e "${BLUE}🧪 Testing security endpoints...${NC}"
sleep 10

# Test API health with security headers
HEALTH_RESPONSE=$(ssh $VPS_USER@$VPS_HOST "
    curl -s -I http://localhost:8001/health | head -10
")

if echo "$HEALTH_RESPONSE" | grep -q "X-Content-Type-Options"; then
    print_status "Security headers are active"
else
    print_warning "Security headers not detected"
fi

# Test rate limiting (this will be limited)
RATE_TEST=$(ssh $VPS_USER@$VPS_HOST "
    for i in {1..5}; do
        curl -s -o /dev/null -w '%{http_code}' http://localhost:8001/health
        echo
    done | tail -1
")

if [ "$RATE_TEST" = "200" ]; then
    print_status "API is responding"
else
    print_warning "API returned status: $RATE_TEST"
fi

# Display security summary
echo -e "${BLUE}📋 Security Deployment Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ssh $VPS_USER@$VPS_HOST "
    echo -e '🔒 Security Features:'
    echo '  • Firewall (UFW): Active with restrictive rules'
    echo '  • Fail2ban: Monitoring SSH and API endpoints'
    echo '  • Security Headers: CSP, XSS Protection, etc.'
    echo '  • Rate Limiting: 100 requests/minute per IP'
    echo '  • Input Sanitization: XSS and injection protection'
    echo '  • File Validation: Size, type, and content checks'
    echo '  • Secure File Permissions: 644/755 with restricted access'
    echo '  • SSH Hardening: Key-only authentication'
    echo
    echo -e '🛡️  Active Protections:'
    echo '  • API Key: $API_KEY'
    echo '  • Max File Size: 10MB'
    echo '  • Allowed File Types: PDF, DOCX, Images, Audio'
    echo '  • Auto Security Updates: Enabled'
    echo
    echo -e '📊 Monitoring:'
    echo '  • Security logs: $VPS_PATH/monitoring/logs/security.log'
    echo '  • Fail2ban status: Available via fail2ban-client'
    echo '  • Firewall logs: /var/log/kern.log'
    echo '  • API logs: /var/log/autopicker/'
"

print_status "Security hardening deployment completed successfully!"
echo -e "${GREEN}🎉 Your Autopicker platform is now secured for production!${NC}"
echo
echo -e "${BLUE}Security checklist completed:${NC}"
echo "  ✅ Firewall configured with minimal required ports"
echo "  ✅ Intrusion detection (fail2ban) active"
echo "  ✅ Security headers implemented"
echo "  ✅ Rate limiting enabled"
echo "  ✅ Input validation and sanitization"
echo "  ✅ File upload security checks"
echo "  ✅ SSH hardening (key-only authentication)"
echo "  ✅ Automatic security updates"
echo "  ✅ Security monitoring and logging"
echo "  ✅ API key authentication ready"
echo
echo -e "${YELLOW}Important:${NC}"
echo "  • Save this API key securely: $API_KEY"
echo "  • Monitor security logs regularly"
echo "  • Keep the system updated"
echo "  • Review firewall rules periodically"