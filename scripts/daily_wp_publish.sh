#!/bin/bash
# Daily WordPress publish script - runs on VPS via cron
# Pulls latest code, generates article, publishes to WordPress

cd /root/sembako

# Pull latest
git pull origin main 2>/dev/null

# Publish to WordPress (draft first for safety)
python3 scripts/wp_publisher.py draft >> /root/sembako/logs/wp_publish.log 2>&1

echo "[$(date)] Published via daily cron" >> /root/sembako/logs/wp_publish.log
