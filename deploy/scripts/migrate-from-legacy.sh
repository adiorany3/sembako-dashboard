#!/bin/bash
set -euo pipefail

# Migrate from Legacy VPS to New Architecture
# Usage: sudo bash deploy/scripts/migrate-from-legacy.sh

echo "=== Migration from Legacy VPS ==="
echo "WARNING: This script modifies system configuration!"
echo "Press Ctrl+C to abort, or Enter to continue..."
read

# Get current state
echo "Recording current state..."

# Find old paths
OLD_PATHS=(
    "/root/sembako"
    "/home/ubuntu/sembako"
    "/root/hermes-backup"
    "/home/hermes/.hermes"
)

for path in "${OLD_PATHS[@]}"; do
    if [[ -d "$path" ]]; then
        echo "Found: $path"
    fi
done

# Check for old services
echo "Checking for old services..."
for svc in flask dashboard; do
    if systemctl list-unit-files | grep -q "$svc.service"; then
        echo "Found: $svc.service"
    fi
done

# Check for cron jobs
echo "Checking for cron jobs..."
crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" || echo "No user crontab"

echo ""
echo "Migration steps:"
echo "1. Create backup of current state"
echo "2. Create new user 'hermes'"
echo "3. Create new directory structure"
echo "4. Copy application to new location"
echo "5. Update environment variables"
echo "6. Install new services"
echo "7. Test new configuration"
echo "8. Switch traffic"
echo ""
echo "This is a manual process. See HERMES_SERVER_PRD.md for detailed steps."
