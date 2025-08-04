#!/bin/bash

# Setup auto-update cron job on VPS
# This script sets up automatic deployment whenever you push to GitHub

VPS_HOST="38.242.229.78"
VPS_USER="julie"

echo "⚙️  Setting up auto-update system on VPS..."

# Create the auto-update script on VPS
ssh "${VPS_USER}@${VPS_HOST}" 'cat > /home/julie/autopicker_auto_update.sh << "EOF"
#!/bin/bash

# Auto-update script for Autopicker Platform
# This runs every 5 minutes to check for GitHub updates

PROJECT_DIR="/home/julie/autopicker-platform"
LOG_FILE="/home/julie/autopicker_auto_update.log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    log "Project directory not found, skipping auto-update"
    exit 0
fi

cd "$PROJECT_DIR"

# Check for remote updates
git fetch origin
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/main)

if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
    log "New commits detected, updating..."
    /home/julie/vps_deploy_and_restart.sh >> "$LOG_FILE" 2>&1
    log "Auto-update completed"
else
    # Uncomment this line for verbose logging
    # log "No updates available"
    true
fi
EOF'

# Make it executable
ssh "${VPS_USER}@${VPS_HOST}" "chmod +x /home/julie/autopicker_auto_update.sh"

# Add to crontab (check every 5 minutes)
ssh "${VPS_USER}@${VPS_HOST}" "
    # Remove any existing autopicker cron jobs
    crontab -l 2>/dev/null | grep -v 'autopicker_auto_update.sh' | crontab -
    
    # Add new cron job
    (crontab -l 2>/dev/null; echo '*/5 * * * * /home/julie/autopicker_auto_update.sh') | crontab -
    
    echo 'Cron job added:'
    crontab -l | grep autopicker_auto_update.sh
"

echo "✅ Auto-update system configured!"
echo "🔄 VPS will now check for updates every 5 minutes"
echo "📝 Auto-update logs: /home/julie/autopicker_auto_update.log"
echo ""
echo "To disable auto-updates, run:"
echo "ssh ${VPS_USER}@${VPS_HOST} \"crontab -l | grep -v 'autopicker_auto_update.sh' | crontab -\""