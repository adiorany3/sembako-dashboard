#!/bin/bash
# ============================================
# DATA-ONLY UPDATE: Just run scripts, no restart
# Run via crontab: 0 */2 * * * /root/sembako/data-update.sh
# ============================================
cd /root/sembako/core
LOG="/tmp/data-update.log"
TIMEOUT=45

echo "$(date '+%Y-%m-%d %H:%M:%S'): === DATA UPDATE ===" >> "$LOG"

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
        echo "$(date '+%H:%M:%S'): $name ❌" >> "$LOG"
    fi
done

tail -200 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
echo "$(date '+%H:%M:%S'): DONE" >> "$LOG"
