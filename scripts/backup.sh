#!/bin/bash
set -euo pipefail

# Hermes Backup Script
# Usage: sudo bash scripts/backup.sh

SOURCE_DIR="/opt/hermes/sembako-dashboard"
DATA_DIR="/var/lib/hermes-dashboard/data"
STATE_DIR="/home/hermes/.hermes"
BACKUP_DIR="/var/backups/hermes-dashboard"
OFFSITE_DIR="${OFFSITE_BACKUP_DIR:-/var/backups/hermes-dashboard/offsite}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
HOSTNAME=$(hostname)

log() { echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $*"; }

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR" "$OFFSITE_DIR"

# Get Git info
cd "$SOURCE_DIR"
COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

log "Starting backup..."

# Create temporary staging directory
STAGING=$(mktemp -d)
trap "rm -rf $STAGING" EXIT

# Backup Hermes state
if [[ -d "$STATE_DIR" ]]; then
    log "Backing up Hermes state..."
    tar --hard-dereference -cf "$STAGING/hermes-state.tar" -C "$(dirname "$STATE_DIR)" "$(basename "$STATE_DIR")"
fi

# Backup dashboard data
if [[ -d "$DATA_DIR" ]]; then
    log "Backing up dashboard data..."
    tar --hard-dereference -cf "$STAGING/dashboard-data.tar" -C "$(dirname "$DATA_DIR")" "$(basename "$DATA_DIR")"
fi

# Backup server config
log "Backing up server config..."
tar -cf "$STAGING/server-config.tar" \
    /etc/hermes-dashboard \
    /etc/systemd/system/hermes-*.service \
    /etc/systemd/system/hermes-*.timer \
    /etc/nginx/sites-available/hermes-dashboard 2>/dev/null || true

# Compress with zstd
log "Compressing archives..."
for tarfile in "$STAGING"/*.tar; do
    [[ -f "$tarfile" ]] || continue
    zstd -T0 -19 "$tarfile" -o "${tarfile%.tar}.tar.zst"
    rm "$tarfile"
done

# Encrypt with age (if available)
if command -v age &>/dev/null; then
    log "Encrypting archives..."
    RECIPIENT_FILE="${BACKUP_ENCRYPTION_RECIPIENT:-}"
    if [[ -n "$RECIPIENT_FILE" && -f "$RECIPIENT_FILE" ]]; then
        for zstfile in "$STAGING"/*.zst; do
            [[ -f "$zstfile" ]] || continue
            age -R "$RECIPIENT_FILE" "$zstfile" -o "${zstfile}.age"
            rm "$zstfile"
        done
    fi
fi

# Calculate checksums
log "Calculating checksums..."
cd "$STAGING"
sha256sum *.zst *.age 2>/dev/null > SHA256SUMS

# Create manifest
log "Creating manifest..."
cat > "$STAGING/backup-manifest.json" << EOF
{
  "schema_version": 1,
  "created_at": "$(date -Iseconds)",
  "hostname": "$HOSTNAME",
  "repository": "adiorany3/sembako-dashboard",
  "branch": "$BRANCH",
  "commit": "$COMMIT",
  "app_dir": "$SOURCE_DIR",
  "data_dir": "$DATA_DIR",
  "state_dir": "$STATE_DIR",
  "timezone": "Asia/Jakarta",
  "archives": [
    $(for f in "$STAGING"/*.zst "$STAGING"/*.age; do [[ -f "$f" ]] && echo -n "{\"name\": \"$(basename $f)\", \"sha256\": \"$(sha256sum "$f" | cut -d' ' -f1)\"},"; done | sed 's/,$//')
  ]
}
EOF

# Move to backup directory
log "Moving to backup directory..."
cp "$STAGING"/* "$BACKUP_DIR/"

# Cleanup old backups (keep 7 daily, 4 weekly, 6 monthly)
log "Cleaning up old backups..."
cd "$BACKUP_DIR"
ls -t hermes-state-*.tar.zst* 2>/dev/null | tail -n +8 | xargs -r rm -f
ls -t dashboard-data-*.tar.zst* 2>/dev/null | tail -n +8 | xargs -r rm -f
ls -t server-config-*.tar.zst* 2>/dev/null | tail -n +8 | xargs -r rm -f

log "Backup complete!"
echo "Files: $BACKUP_DIR"
ls -lh "$BACKUP_DIR"
