#!/bin/bash
set -e

echo "=== [$(date)] Starting update ==="

cd /root/sembako

# Pull latest code
echo "Pulling latest code..."
git pull origin main

# Kill old processes
echo "Killing old Flask processes..."
sudo killall python3 2>/dev/null || true
sleep 2

# Restart via systemd
echo "Restarting Flask service..."
sudo systemctl restart flask-dashboard

# Wait and check
sleep 5
if systemctl is-active --quiet flask-dashboard; then
    echo "✅ Flask restarted successfully"
    curl -s http://localhost:5000/api/health || echo "Health check failed"
else
    echo "❌ Flask failed to start. Check logs:"
    sudo journalctl -u flask-dashboard -n 20 --no-pager
fi
