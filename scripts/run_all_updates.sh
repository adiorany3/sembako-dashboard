#!/bin/bash
set -euo pipefail

# Hermes All Updates Orchestrator
# Called by hermes-update.service via systemd timer

HERMES_APP_DIR="${HERMES_APP_DIR:-/opt/hermes/sembako-dashboard}"
HERMES_DATA_DIR="${HERMES_DATA_DIR:-/var/lib/hermes-dashboard/data}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "Starting Hermes data updates..."

cd "$HERMES_APP_DIR"

# Run update scripts
# Add your update scripts here as they are created
# Example: python3 scripts/update_harga.py

log "Updates complete!"
