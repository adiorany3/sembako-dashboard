#!/bin/bash
cd ~/sembako
LOG=logs/update_$(date +%Y%m%d_%H%M%S).log
mkdir -p logs

exec > $LOG 2>&1

ERRORS=0

for script in \
  scripts/update_harga.py \
  scripts/update_crypto.py \
  scripts/update_emas.py \
  scripts/update_pertanian.py \
  scripts/update_peternakan.py \
  scripts/update_kurs.py \
  scripts/update_oil.py \
  scripts/update_cpo.py \
  scripts/update_bi_rate.py \
  scripts/update_saham.py \
  scripts/sentimen_berita.py
do
  echo "=== Running $script ==="
  python3 "$script" || { echo "FAILED: $script"; ERRORS=$((ERRORS+1)); }
done

echo "=== Dedup ==="
python3 scripts/dedup_excel.py || true

echo "=== Validate ==="
python3 scripts/validate_data.py || true

echo "=== Done. Errors: $ERRORS ==="
exit $ERRORS
