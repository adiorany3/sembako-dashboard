#!/bin/bash
# Auto-deploy: pull latest code + restart Flask if code changed
cd /root/sembako || exit 1

# Pull latest
git fetch origin main 2>/dev/null
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "$(date): No changes."
    exit 0
fi

echo "$(date): New code detected! Pulling..."
git pull origin main 2>&1

# Install new deps if requirements changed
if git diff "$LOCAL" "$REMOTE" --name-only | grep -q "requirements"; then
    pip3 install -r requirements.txt --break-system-packages 2>/dev/null
fi

# Restart Flask
echo "$(date): Restarting Flask..."
pkill -f "python3 /root/sembako/core/app.py" 2>/dev/null
sleep 1
cd /root/sembako/core
nohup python3 app.py > /tmp/flask.log 2>&1 &
sleep 2

# Verify
if curl -s --max-time 3 http://localhost:5000/api/health | grep -q "healthy"; then
    echo "$(date): Flask restarted OK ✓"
else
    echo "$(date): Flask restart FAILED ✗"
fi
