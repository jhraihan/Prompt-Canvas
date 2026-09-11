#!/usr/bin/env bash
#
# Prompt Canvas backend deploy. Runs on the VPS as the site user.
#
# bootstrap.sh installs this at /home/prompt-canvas/deploy.sh, which is what the
# GitHub Actions "Deploy backend to VPS" job invokes over SSH. It can also be
# run by hand:
#
#   sudo -u prompt-canvas /home/prompt-canvas/deploy.sh
#
# It restarts the service only after migrations and static files succeed, so a
# failed build leaves the previous version serving.
set -euo pipefail

# Deployment identity comes from the environment, never from a literal in the
# repository. bootstrap.sh writes these into ${SITE_HOME}/.deploy-env, which
# this script sources, so a checkout carries no host-specific values.
DEPLOY_ENV="${DEPLOY_ENV:-/home/${SITE_USER:-prompt-canvas}/.deploy-env}"
[ -f "${DEPLOY_ENV}" ] && . "${DEPLOY_ENV}"

: "${DOMAIN:?DOMAIN is not set. Expected it in ${DEPLOY_ENV} (written by bootstrap.sh).}"
SITE_USER="${SITE_USER:-prompt-canvas}"

APP_ROOT="/home/${SITE_USER}/htdocs/${DOMAIN}"
BACKEND="${APP_ROOT}/backend"
VENV="${BACKEND}/.venv"
GUNICORN_PORT="${GUNICORN_PORT:-8021}"
GIT_BRANCH="${GIT_BRANCH:-main}"

export DJANGO_SETTINGS_MODULE=config.settings.prod

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

cd "${APP_ROOT}" || die "${APP_ROOT} not found. Has bootstrap.sh been run?"

PREVIOUS_REV="$(git rev-parse --short HEAD)"

log "Pulling latest code"
git fetch --quiet origin
git reset --hard --quiet "origin/${GIT_BRANCH}"
NEW_REV="$(git rev-parse --short HEAD)"
echo "    ${PREVIOUS_REV} -> ${NEW_REV}"

log "Installing dependencies"
"${VENV}/bin/pip" install --upgrade pip --quiet
"${VENV}/bin/pip" install -r "${BACKEND}/requirements.txt" --quiet

cd "${BACKEND}"

log "Checking configuration"
# --deploy surfaces missing HTTPS, cookie, and host settings before they reach
# users. A warning here fails the deploy rather than being logged and ignored.
"${VENV}/bin/python" manage.py check --deploy --fail-level WARNING

log "Applying migrations"
"${VENV}/bin/python" manage.py migrate --noinput

log "Collecting static files"
"${VENV}/bin/python" manage.py collectstatic --noinput >/dev/null

log "Restarting the application"
sudo /usr/bin/systemctl restart promptcanvas-api

# gunicorn is reached directly here, bypassing nginx, so the two headers nginx
# would normally add must be supplied by hand:
#   Host              ALLOWED_HOSTS holds the domain, not 127.0.0.1, so without
#                     it Django answers 400 DisallowedHost.
#   X-Forwarded-Proto SECURE_SSL_REDIRECT is on and SECURE_PROXY_SSL_HEADER
#                     trusts this header, so without it Django answers 301.
HEALTH_HEADERS=(-H "Host: ${DOMAIN}" -H "X-Forwarded-Proto: https")

# Give gunicorn a moment to bind before deciding it failed.
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS --max-time 5 "${HEALTH_HEADERS[@]}" "http://127.0.0.1:${GUNICORN_PORT}/api/health/" >/dev/null 2>&1; then
    log "Deployed ${NEW_REV} successfully"
    exit 0
  fi
  sleep 2
done

echo "--- last 40 log lines ---"
journalctl -u promptcanvas-api -n 40 --no-pager 2>/dev/null || true
die "Health check failed after restart. Previous revision was ${PREVIOUS_REV}."
