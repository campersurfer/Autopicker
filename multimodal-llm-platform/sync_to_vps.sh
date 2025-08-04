#!/bin/bash

# Sync local changes to VPS and restart service
# This is a manual sync script for immediate deployment

set -e

VPS_HOST="38.242.229.78"
VPS_USER="julie"
VPS_PATH="/home/julie/autopicker-platform"

echo "🚀 Syncing Autopicker Platform to VPS..."

# Sync the deployment script first
echo "📤 Uploading deployment script..."
scp vps_deploy_and_restart.sh "${VPS_USER}@${VPS_HOST}:/home/julie/"
ssh "${VPS_USER}@${VPS_HOST}" "chmod +x /home/julie/vps_deploy_and_restart.sh"

# Run the deployment script on VPS
echo "🔄 Running deployment on VPS..."
ssh "${VPS_USER}@${VPS_HOST}" "/home/julie/vps_deploy_and_restart.sh"

echo ""
echo "✅ Deployment completed!"
echo "🌐 Your Autopicker Platform should be running at: http://${VPS_HOST}:8001"
echo "📊 Check status with: ./check_vps_status.sh"