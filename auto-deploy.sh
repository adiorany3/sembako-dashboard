#!/bin/bash
# ============================================
# AUTO-DEPLOY: Pull + Update Data + Restart
# Run via VPS crontab: */15 * * * * /root/sembako/auto-deploy.sh
# ============================================
set -e

cd /root/sembako || exit 1
LOG="/tmp/auto-deploy.log"

echo "$(date '+%Y-%m-%d %H:%M:%S'): === AUTO-DEPLOY START ===" >> "$LOG"

# 1. Pull latest code
git fetch origin main 2>/dev/null
LOCAL=$(git rev-parse HEAD 2>/dev/null)
REMOTE=$(git rev-parse origin/main 2>/dev/null)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "$(date '+%H:%M:%S'): No code changes." >> "$LOG"
else
    echo "$(date '+%H:%M:%S'): New code detected! Pulling..." >> "$LOG"
    git pull origin main 2>&1 >> "$LOG"
    chmod +x auto-deploy.sh
fi

# 2. Run ALL data update scripts (with timeout)
cd /root/sembako/core
TIMEOUT=45

echo "$(date '+%H:%M:%S'): Updating data..." >> "$LOG"

for script in \
    ../scripts/update_harga.py \
    ../scripts/update_crypto.py \
    ../scripts/update_emas.py \
    ../scripts/update_pertanian.py \
    ../scripts/update_peternakan.py \
    ../scripts/update_saham.py \
    ../scripts/update_kurs.py \
    ../scripts/update_oil.py \
    ../scripts/update_bi_rate.py \
    ../scripts/update_cpo.py \
    ../scripts/sentimen_berita.py \
    ../scripts/price_alerts.py; do
    
    name=$(basename "$script" .py)
    if timeout $TIMEOUT python3 "$script" >> "$LOG" 2>&1; then
        echo "$(date '+%H:%M:%S'): $name ✅" >> "$LOG"
    else
        echo "$(date '+%H:%M:%S'): $name ❌ (timeout/error)" >> "$LOG"
    fi
done

# 3. Restart Flask if code changed
if [ "$LOCAL" != "$REMOTE" ]; then
    echo "$(date '+%H:%M:%S'): Code changed, restarting Flask..." >> "$LOG"
    pkill -f "python3.*app.py" 2>/dev/null || true
    sleep 2
    pkill -9 -f "python3.*app.py" 2>/dev/null || true
    sleep 1
    cd /root/sembako/core
    nohup python3 app.py > /tmp/flask.log 2>&1 &
    sleep 3
    if curl -s --max-time 3 http://localhost:5000/api/health | grep -q "healthy"; then
        echo "$(date '+%H:%M:%S'): Flask restarted OK ✅" >> "$LOG"
    else
        echo "$(date '+%H:%M:%S'): Flask restart FAILED ❌" >> "$LOG"
    fi
else
    # No code change — verify Flask is alive
    if ! curl -s --max-time 3 http://localhost:5000/api/health | grep -q "healthy"; then
        echo "$(date '+%H:%M:%S'): Flask dead, restarting..." >> "$LOG"
        cd /root/sembako/core
        nohup python3 app.py > /tmp/flask.log 2>&1 &
        sleep 3
    fi
fi

# 4. Log rotation (keep last 500 lines)
tail -500 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"

echo "$(date '+%H:%M:%S'): === AUTO-DEPLOY DONE ===" >> "$LOG"
