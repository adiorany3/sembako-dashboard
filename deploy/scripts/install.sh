#!/bin/bash
set -euo pipefail

# Hermes Dashboard Installation Script
# Usage: sudo bash deploy/scripts/install.sh

echo "=== Hermes Dashboard Installation ==="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

# Check OS
if [[ ! -f /etc/os-release ]]; then
    log_error "Cannot detect OS"
    exit 1
fi

source /etc/os-release
if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
    log_warn "This script is designed for Ubuntu/Debian. Continuing anyway..."
fi

log_info "Installing system packages..."
apt-get update
apt-get install -y \
    git nginx python3 python3-venv python3-pip \
    curl jq rsync unzip zstd ca-certificates

log_info "Creating user 'hermes'..."
if ! id hermes &>/dev/null; then
    useradd --create-home --shell /bin/bash hermes
    log_info "User 'hermes' created"
else
    log_warn "User 'hermes' already exists"
fi

log_info "Creating directories..."
mkdir -p \
    /opt/hermes \
    /var/lib/hermes-dashboard/data \
    /var/lib/hermes-dashboard/cache \
    /var/log/hermes-dashboard \
    /etc/hermes-dashboard \
    /var/backups/hermes-dashboard

chown -R hermes:hermes \
    /opt/hermes \
    /var/lib/hermes-dashboard \
    /var/log/hermes-dashboard \
    /var/backups/hermes-dashboard

log_info "Cloning repository..."
if [[ -d /opt/hermes/sembako-dashboard ]]; then
    log_warn "Directory already exists, skipping clone"
else
    sudo -u hermes git clone \
        https://github.com/adiorany3/sembako-dashboard.git \
        /opt/hermes/sembako-dashboard
fi

log_info "Creating environment file..."
if [[ ! -f /etc/hermes-dashboard/hermes-dashboard.env ]]; then
    cat > /etc/hermes-dashboard/hermes-dashboard.env << 'EOF'
HERMES_APP_DIR=/opt/hermes/sembako-dashboard
HERMES_DATA_DIR=/var/lib/hermes-dashboard/data
HERMES_CACHE_DIR=/var/lib/hermes-dashboard/cache
HERMES_LOG_DIR=/var/log/hermes-dashboard
HERMES_STATE_DIR=/home/hermes/.hermes
TZ=Asia/Jakarta

# Add your secrets below (DO NOT commit to Git):
# GROQ_API_KEY=your_key_here
# TELEGRAM_BOT_TOKEN=your_token_here
# TELEGRAM_CHAT_ID=your_chat_id_here
EOF
    chown root:hermes /etc/hermes-dashboard/hermes-dashboard.env
    chmod 640 /etc/hermes-dashboard/hermes-dashboard.env
    log_info "Environment file created at /etc/hermes-dashboard/hermes-dashboard.env"
else
    log_warn "Environment file already exists"
fi

log_info "Setting up Python virtual environment..."
cd /opt/hermes/sembako-dashboard
sudo -u hermes python3 -m venv .venv
sudo -u hermes .venv/bin/pip install --upgrade pip
if [[ -f requirements.txt ]]; then
    sudo -u hermes .venv/bin/pip install -r requirements.txt
else
    log_warn "requirements.txt not found, installing basic dependencies..."
    sudo -u hermes .venv/bin/pip install flask pandas openpyxl requests sqlalchemy gunicorn
fi
sudo -u hermes .venv/bin/pip freeze > requirements.lock.txt

log_info "Installing systemd services..."
cp deploy/systemd/hermes-dashboard.service /etc/systemd/system/
cp deploy/systemd/hermes-update.service /etc/systemd/system/
cp deploy/systemd/hermes-update.timer /etc/systemd/system/
cp deploy/systemd/hermes-backup.service /etc/systemd/system/
cp deploy/systemd/hermes-backup.timer /etc/systemd/system/

systemctl daemon-reload
systemctl enable --now hermes-dashboard.service
systemctl enable --now hermes-update.timer
systemctl enable --now hermes-backup.timer

log_info "Installing Nginx..."
cp deploy/nginx/hermes-dashboard.conf /etc/nginx/sites-available/hermes-dashboard
ln -sfn /etc/nginx/sites-available/hermes-dashboard /etc/nginx/sites-enabled/hermes-dashboard
nginx -t
systemctl reload nginx

log_info "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit /etc/hermes-dashboard/hermes-dashboard.env with your secrets"
echo "2. Run: sudo systemctl restart hermes-dashboard"
echo "3. Check health: curl http://127.0.0.1/api/health"
