#!/bin/bash
# Proper Flask restart — kill old process, pull, restart
echo "1. Killing old Flask process..."
sudo killall python3 2>/dev/null
sleep 2

echo "2. Pulling latest code..."
cd ~/sembako
git pull origin main

echo "3. Restarting Flask..."
sudo systemctl daemon-reload
sudo systemctl restart flask
sleep 3

echo "4. Verifying..."
curl -s http://localhost:5000/api/health
echo ""
echo "Done!"
