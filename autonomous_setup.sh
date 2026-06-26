#!/bin/bash
# ============================================
# AUTONOMOUS DASHBOARD SETUP
# VPS akan jalan sendiri, pull dari GitHub
# ============================================

set -e

REPO_URL="https://github.com/adiorany3/sembako-dashboard.git"
APP_DIR="/home/ubuntu/sembako"
LOG_FILE="$APP_DIR/autonomous_setup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "AUTONOMOUS DASHBOARD SETUP"
log "=========================================="

# 1. Install dependencies
log "[1/7] Installing Python packages..."
pip3 install --break-system-packages flask flask-cors openpyxl pandas requests schedule > /dev/null 2>&1 || true
log "✅ Packages installed"

# 2. Clone or pull repo
log "[2/7] Syncing with GitHub..."
if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR"
    git pull origin main > /dev/null 2>&1 && log "✅ Git pull done" || log "⚠️ Git pull failed (may need token)"
else
    cd /home/ubuntu
    git clone "$REPO_URL" "$APP_DIR" > /dev/null 2>&1 && log "✅ Repo cloned" || log "⚠️ Clone failed - check repo visibility"
fi

# 3. Setup systemd service
log "[3/7] Setting up Flask service..."
sudo bash -c "cat > /etc/systemd/system/flask.service << 'EOF'
[Unit]
Description=Flask Dashboard - Sembako Monitor
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/python3 $APP_DIR/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"
sudo systemctl daemon-reload
sudo systemctl enable flask
sudo systemctl restart flask
log "✅ Flask service enabled and started"

# 4. Setup auto-pull from GitHub (hourly)
log "[4/7] Setting up auto-pull cron..."
PULL_SCRIPT="$APP_DIR/pull_from_github.sh"
cat > "$PULL_SCRIPT" << 'EOF'
#!/bin/bash
cd /home/ubuntu/sembako
git pull origin main > /dev/null 2>&1
# Restart Flask if files changed
if [ $? -eq 0 ]; then
    systemctl restart flask > /dev/null 2>&1
fi
EOF
chmod +x "$PULL_SCRIPT"

# Add to crontab (every hour at minute 0)
(crontab -l 2>/dev/null | grep -v "pull_from_github"; echo "0 * * * * /home/ubuntu/sembako/pull_from_github.sh >> /home/ubuntu/sembako/pull.log 2>&1") | crontab -
sudo service cron start 2>/dev/null || true
log "✅ Auto-pull cron enabled (hourly)"

# 5. Setup data update cron jobs
log "[5/7] Setting up data update cron jobs..."
CRON_UPDATE="$APP_DIR/run_updates.sh"
cat > "$CRON_UPDATE" << 'EOF'
#!/bin/bash
cd /home/ubuntu/sembako

# Run price updates
python3 update_harga.py > /dev/null 2>&1 &
python3 update_crypto.py > /dev/null 2>&1 &
python3 update_emas.py > /dev/null 2>&1 &
EOF
chmod +x "$CRON_UPDATE"

(crontab -l 2>/dev/null | grep -v "run_updates"; echo "0 7,12,18 * * * /home/ubuntu/sembako/run_updates.sh >> /home/ubuntu/sembako/update.log 2>&1") | crontab -
log "✅ Data update cron enabled (7AM, 12PM, 6PM)"

# 6. Verify Flask is running
log "[6/7] Verifying Flask..."
sleep 3
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ | grep -q "200"; then
    log "✅ Flask is running at http://localhost:5000"
else
    log "⚠️ Flask may not be responding yet"
fi

# 7. Summary
log "[7/7] Setup complete!"
log ""
log "=========================================="
log "SUMMARY"
log "=========================================="
log "📁 App directory: $APP_DIR"
log "🌐 Dashboard: http://43.153.196.161:5000"
log "🔒 Keuangan: http://43.153.196.161:5000/keuangan"
log "📜 Auto-pull: Every hour from GitHub"
log "📊 Data updates: 7AM, 12PM, 6PM"
log "🔄 Flask auto-restart: On boot + On git pull"
log ""
log "TO MANUALLY UPDATE FROM GITHUB:"
log "  cd $APP_DIR && git pull origin main"
log ""
log "TO CHECK STATUS:"
log "  sudo systemctl status flask"
log "  crontab -l"
log "=========================================="
