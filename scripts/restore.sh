#!/bin/bash
set -euo pipefail

# Hermes Restore Script
# Usage: sudo bash scripts/restore.sh <backup_archive> [options]
# Example: sudo bash scripts/restore.sh /var/backups/hermes-dashboard/hermes-state-20241215_120000.tar.zst.age

BACKUP_FILE="${1:-}"
SOURCE_DIR="/opt/hermes/sembako-dashboard"
DATA_DIR="/var/lib/hermes-dashboard/data"
STATE_DIR="/home/hermes/.hermes"

log() { echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $*"; }

if [[ -z "$BACKUP_FILE" ]]; then
    echo "Usage: $0 <backup_archive> [options]"
    echo ""
    echo "Options:"
    echo "  --state-only    Restore only Hermes state"
    echo "  --data-only     Restore only dashboard data"
    echo "  --config-only  Restore only server config"
    echo "  --all          Restore everything (default)"
    exit 1
fi

shift || true
RESTORE_ALL=true
for arg in "$@"; do
    case "$arg" in
        --state-only)  RESTORE_STATE_ONLY=true; RESTORE_ALL=false ;;
        --data-only)   RESTORE_DATA_ONLY=true;  RESTORE_ALL=false ;;
        --config-only) RESTORE_CONFIG_ONLY=true; RESTORE_ALL=false ;;
    esac
done

log "Starting restore from: $BACKUP_FILE"

# Verify file exists
if [[ ! -f "$BACKUP_FILE" ]]; then
    log "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Create staging directory
STAGING=$(mktemp -d)
trap "rm -rf $STAGING" EXIT

# Copy backup to staging
cp "$BACKUP_FILE" "$STAGING/"
cd "$STAGING"

# Determine compression and encryption
BASENAME=$(basename "$BACKUP_FILE")
if [[ "$BASENAME" == *.age ]]; then
    # Decrypt first
    if ! command -v age &>/dev/null; then
        log "ERROR: age command not found for decryption"
        exit 1
    fi
    log "Decrypting..."
    age -d "$BASENAME" -o "${BASENAME%.age}"
    BASENAME="${BASENAME%.age}"
fi

if [[ "$BASENAME" == *.zst ]]; then
    log "Decompressing..."
    zstd -d "$BASENAME" -o "${BASENAME%.tar.zst}.tar"
    BASENAME="${BASENAME%.tar.zst}.tar"
fi

# Extract
log "Extracting..."
tar -xf "$BASENAME" -C "$STAGING"

# Restore based on backup type
if [[ "$BASENAME" == hermes-state* ]]; then
    log "Restoring Hermes state..."
    mkdir -p "$(dirname "$STATE_DIR")"
    rsync -aHAX "$STAGING/hermes-state/" "$STATE_DIR/"
    chown -R hermes:hermes "$STATE_DIR"
elif [[ "$BASENAME" == dashboard-data* ]]; then
    log "Restoring dashboard data..."
    mkdir -p "$(dirname "$DATA_DIR")"
    rsync -aHAX --delete "$STAGING/dashboard-data/" "$DATA_DIR/"
    chown -R hermes:hermes "$DATA_DIR"
elif [[ "$BASENAME" == server-config* ]]; then
    log "Restoring server config..."
    rsync -aHAX "$STAGING/server-config/" /etc/
    systemctl daemon-reload
fi

log "Restore complete!"
