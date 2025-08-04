#!/bin/bash

# Check Autopicker Platform Status on VPS
# Run this locally to check the remote service status

VPS_HOST="38.242.229.78"
VPS_USER="julie"

echo "🔍 Checking Autopicker Platform status on VPS..."

# Check if VPS is reachable
if ! ping -c 1 "$VPS_HOST" > /dev/null 2>&1; then
    echo "❌ VPS is not reachable at $VPS_HOST"
    exit 1
fi

echo "✅ VPS is reachable"

# Check service status
echo ""
echo "📊 Service Status:"
ssh "${VPS_USER}@${VPS_HOST}" "
    if [ -f /home/julie/autopicker_status.json ]; then
        echo '✅ Status file exists'
        cat /home/julie/autopicker_status.json | python3 -m json.tool
    else
        echo '❌ Status file not found'
    fi
"

echo ""
echo "🌐 Health Check:"
if timeout 10 curl -s "http://${VPS_HOST}:8001/health" > /dev/null; then
    echo "✅ Service is responding"
    curl -s "http://${VPS_HOST}:8001/health" | python3 -m json.tool
else
    echo "❌ Service is not responding on port 8001"
fi

echo ""
echo "📋 Process Status:"
ssh "${VPS_USER}@${VPS_HOST}" "
    if pgrep -f 'simple_api.py' > /dev/null; then
        echo '✅ Autopicker process is running'
        ps aux | grep simple_api.py | grep -v grep
    else
        echo '❌ Autopicker process is not running'
    fi
"

echo ""
echo "📝 Recent Logs:"
ssh "${VPS_USER}@${VPS_HOST}" "
    if [ -f /home/julie/autopicker-platform/autopicker.log ]; then
        echo 'Last 10 lines of autopicker.log:'
        tail -10 /home/julie/autopicker-platform/autopicker.log
    else
        echo 'No log file found'
    fi
"