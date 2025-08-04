#!/bin/bash

# Quick deployment status check for Autopicker Platform
# Shows service health, process info, and recent logs

VPS_HOST="38.242.229.78"
VPS_USER="julie"

echo "🚀 Autopicker Platform Deployment Status"
echo "========================================"
echo ""

# Check service health
echo "🔍 Service Health Check:"
if curl -f -s http://${VPS_HOST}:8001/health > /dev/null; then
    echo "✅ Service is responding"
    curl -s http://${VPS_HOST}:8001/health | jq .
else
    echo "❌ Service is not responding"
fi
echo ""

# Check process status
echo "🔄 Process Status:"
ssh "${VPS_USER}@${VPS_HOST}" "ps aux | grep -E '(uvicorn|simple_api)' | grep -v grep | head -5" || echo "No processes found"
echo ""

# Check recent logs
echo "📝 Recent Logs (last 10 lines):"
ssh "${VPS_USER}@${VPS_HOST}" "tail -10 /home/julie/autopicker-platform/autopicker.log 2>/dev/null || echo 'No logs found'"
echo ""

# Check auto-update status
echo "⏰ Auto-Update Status:"
ssh "${VPS_USER}@${VPS_HOST}" "crontab -l | grep autopicker_auto_update.sh" || echo "Auto-update not configured"
echo ""

# Check disk space
echo "💾 Disk Usage:"
ssh "${VPS_USER}@${VPS_HOST}" "df -h /home/julie/autopicker-platform | tail -1"
echo ""

echo "🌐 Service URL: http://${VPS_HOST}:8001"
echo "📊 API Docs: http://${VPS_HOST}:8001/docs"