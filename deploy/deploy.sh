#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Ligisoo Marketplace production deployment
# Usage:
#   First time : sudo bash deploy/deploy.sh --install
#   Updates    : bash deploy/deploy.sh --update
# =============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
die()     { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Config — adjust these if your paths differ
# ---------------------------------------------------------------------------
APP_USER="ligisoo_ke"
APP_DIR="/home/ligisoo_ke/marketplace"
VENV_DIR="${APP_DIR}/.venv"
DEPLOY_DIR="${APP_DIR}/deploy"
DOMAIN="ligisoo.co.ke"
CERTBOT_EMAIL="ligisoo.ke@gmail.com"

MODE="${1:-}"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
need_root() {
    [[ $EUID -eq 0 ]] || die "This script must be run as root for the --install step. Use: sudo bash deploy/deploy.sh --install"
}

as_app() {
    # Run a command as the app user
    sudo -u "${APP_USER}" bash -c "$*"
}

# ---------------------------------------------------------------------------
# --install  (first-time full setup, requires root)
# ---------------------------------------------------------------------------
do_install() {
    need_root
    info "Starting full installation..."

    # 1. System packages
    info "Installing system packages..."
    apt-get update -qq
    apt-get install -y -qq \
        python3-pip python3-venv \
        postgresql postgresql-contrib \
        redis-server \
        nginx \
        certbot python3-certbot-nginx \
        build-essential libpq-dev \
        git curl

    success "System packages installed."

    # 2. PostgreSQL database
    info "Setting up PostgreSQL..."
    # Load DB credentials from .env
    # shellcheck disable=SC1090
    set -a; source "${APP_DIR}/.env"; set +a

    sudo -u postgres psql -tc "SELECT 1 FROM pg_user WHERE usename = '${DB_USER}';" | grep -q 1 || \
        sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"

    sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}';" | grep -q 1 || \
        sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"
    success "PostgreSQL ready: database '${DB_NAME}', user '${DB_USER}'."

    # 3. Redis (already installed, just ensure it's enabled)
    systemctl enable --now redis-server
    success "Redis running."

    # 4. Add app user to www-data group (so nginx can read the socket)
    usermod -aG www-data "${APP_USER}"
    success "User '${APP_USER}' added to www-data group."

    # 5. Virtualenv and Python dependencies
    do_venv

    # 6. Django setup
    do_django_setup

    # 7. Systemd services
    do_systemd

    # 8. Nginx
    do_nginx

    # 9. SSL certificate
    do_certbot

    success "============================================"
    success " Installation complete!"
    success " Check status: systemctl status ligisoo"
    success " View logs:    journalctl -u ligisoo -f"
    success "============================================"
}

# ---------------------------------------------------------------------------
# --update  (pull latest code and restart, no root needed for most steps)
# ---------------------------------------------------------------------------
do_update() {
    info "Pulling latest code..."
    cd "${APP_DIR}"
    git pull

    # Activate venv and update deps
    info "Updating Python dependencies..."
    # shellcheck disable=SC1090
    source "${VENV_DIR}/bin/activate"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt

    do_django_setup

    info "Reloading Gunicorn (zero-downtime)..."
    sudo systemctl reload ligisoo || sudo systemctl restart ligisoo

    success "Update complete."
}

# ---------------------------------------------------------------------------
# Helper: create venv + install deps
# ---------------------------------------------------------------------------
do_venv() {
    info "Setting up Python virtual environment..."
    if [[ ! -d "${VENV_DIR}" ]]; then
        as_app "python3 -m venv ${VENV_DIR}"
    fi
    as_app "${VENV_DIR}/bin/pip install -q --upgrade pip"
    as_app "${VENV_DIR}/bin/pip install -q -r ${APP_DIR}/requirements.txt"
    success "Virtualenv ready at ${VENV_DIR}."
}

# ---------------------------------------------------------------------------
# Helper: Django management commands
# ---------------------------------------------------------------------------
do_django_setup() {
    info "Running Django management commands..."
    cd "${APP_DIR}"
    # shellcheck disable=SC1090
    set -a; source "${APP_DIR}/.env"; set +a
    export DJANGO_SETTINGS_MODULE=config.settings.production

    as_app "cd ${APP_DIR} && ${VENV_DIR}/bin/python manage.py migrate --noinput"
    as_app "cd ${APP_DIR} && ${VENV_DIR}/bin/python manage.py collectstatic --noinput --clear"

    # Create logs directory if it doesn't exist
    as_app "mkdir -p ${APP_DIR}/logs"

    success "Django migrations and static files done."
}

# ---------------------------------------------------------------------------
# Helper: install and enable systemd services
# ---------------------------------------------------------------------------
do_systemd() {
    info "Installing systemd service units..."

    # Gunicorn / Django
    cp "${DEPLOY_DIR}/ligisoo.service"                 /etc/systemd/system/ligisoo.service

    # Tip scheduler
    cp "${APP_DIR}/tip-scheduler.service"              /etc/systemd/system/tip-scheduler.service

    systemctl daemon-reload

    systemctl enable --now ligisoo
    systemctl enable --now tip-scheduler

    success "Systemd services enabled and started."
}

# ---------------------------------------------------------------------------
# Helper: nginx site config
# ---------------------------------------------------------------------------
do_nginx() {
    info "Configuring nginx..."

    cp "${DEPLOY_DIR}/ligisoo-nginx.conf" /etc/nginx/sites-available/ligisoo

    # Enable site (idempotent)
    ln -sf /etc/nginx/sites-available/ligisoo /etc/nginx/sites-enabled/ligisoo

    # Disable the default nginx site
    rm -f /etc/nginx/sites-enabled/default

    nginx -t && systemctl reload nginx
    success "Nginx configured and reloaded."
}

# ---------------------------------------------------------------------------
# Helper: obtain SSL certificate
# ---------------------------------------------------------------------------
do_certbot() {
    info "Obtaining SSL certificate for ${DOMAIN}..."

    # Stop nginx temporarily so certbot can bind to port 80
    # (or use the nginx plugin — both work)
    certbot --nginx \
        -d "${DOMAIN}" \
        -d "www.${DOMAIN}" \
        --non-interactive \
        --agree-tos \
        --email "${CERTBOT_EMAIL}" \
        --redirect || warn "certbot failed — check DNS and try manually: sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"

    # Ensure auto-renewal timer is enabled
    systemctl enable --now certbot.timer 2>/dev/null || \
        systemctl enable --now snap.certbot.renew.timer 2>/dev/null || \
        warn "Could not enable certbot timer — set up a cron job manually."

    success "SSL certificate obtained and renewal timer enabled."
}

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
case "${MODE}" in
    --install) do_install ;;
    --update)  do_update  ;;
    *)
        echo "Usage: $0 --install | --update"
        echo
        echo "  --install   Full first-time setup (must run as root: sudo bash deploy/deploy.sh --install)"
        echo "  --update    Pull latest code and reload services (no root needed)"
        exit 1
        ;;
esac
