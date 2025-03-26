#!/bin/bash
############################################################################################
# Nombre: setup_full_server.sh
# Descripción:
#   Despliega en una VM Ubuntu limpia:
#   - Creación de grupo 'ai_huntred' y añade {pablo, pablollh, www-data, root}
#   - Django + Gunicorn + PostgreSQL + Redis + Nginx + Certbot + Python3
#   - Purga y reinstala PostgreSQL/Redis; crea DB, corre migrations
#   - Ajusta Redis "supervised no" si systemd falla, daemonize
#   - Arregla Git "dubious ownership"
#   - Instala requirements en venv
#   - Configura Gunicorn + Nginx + (opcional) Certbot SSL
#
# *** ADVERTENCIA: Este script asume que se puede PURGAR y REINSTALAR todo en la VM ***
# Úsalo para levantar la infraestructura desde cero.
#
# Uso:
#   1) Subirlo a la VM
#   2) sudo chmod +x setup_full_server.sh
#   3) sudo ./setup_full_server.sh
############################################################################################

set -euo pipefail

################################
##        CONFIGURACIONES     ##
################################

# == Grupo y usuarios ==
MAIN_GROUP="ai_huntred"
ALL_USERS=("pablo" "pablollh" "www-data" "root")

# == Nombre de tu Django app / repositorio ==
APP_USER="pablo"               # Dueño principal del /home/pablo
PROJECT_DIR="/home/$APP_USER"  # Directorio donde clonar
APP_NAME="ai_huntred"          # Nombre (carpeta django principal)
REPO_URL="https://github.com/ablova/Grupo-huntRED-Chatbot.git"

# == Variables para Gunicorn/Nginx ==
DOMAIN="ai.huntred.com"        # Dominio
EMAIL="hola@huntred.com"       # Certbot
SECRET_KEY="hfmrpTNRwmQ1F7gZI1DNKaQ9gNw3cgayKFB0HK_gt9BKJEnLy60v1v0PnkZtX3OkY48"

# == PostgreSQL ==
DB_NAME="g_huntred_ai_db"
DB_USER="g_huntred_pablo"
DB_PASSWORD="Natalia&Patricio1113!"
DB_HOST="localhost"
DB_PORT="5432"
DB_CONN_MAX_AGE=60
DB_CONNECT_TIMEOUT=10

DJANGO_SECRET_KEY=*&p8)wjh(v@l&b*gv$PLLH$dpc(6=iv0)xvw&=pdv&!1=zal+zpj)
DJANGO_SECRET_KEY2=hfmrpTNRwmQ1F7gZI1DNKaQ9gNw3cgayKFB0HK_gt9BKJEnLy60v1v0PnkZtX3OkY48
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=ai.huntred.com,34.57.227.244,localhost,127.0.0.1

# Admin contact (NUEVO)
ADMIN_EMAIL=hola@huntred.com
ADMIN_PHONE=+525518490291

# Niveles de Loggeo
CONSOLE_LOG_LEVEL=INFO
DEBUG_LOG_LEVEL=DEBUG
MESSENGER_LOG_LEVEL=DEBUG
WHATSAPP_LOG_LEVEL=DEBUG
INSTAGRAM_LOG_LEVEL=DEBUG
TELEGRAM_LOG_LEVEL=DEBUG
ROOT_LOG_LEVEL=DEBUG
SENTRY_LOG_LEVEL=WARNING
DB_LOG_LEVEL=INFO
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=3

# Sentry Configuration
SENTRY_DSN=https://e9989a45cedbcefa64566dbcfb2ffd59@o4508638041145344.ingest.us.sentry.io/4508638043766784
SENTRY_SAMPLE_RATE=1.0
SENTRY_SEND_PII=True
SENTRY_DEBUG=False

# Redis/Celery Configuration
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
CELERY_WORKER_CONCURRENCY=2

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOW_CREDENTIALS=False

# Email Configuration
EMAIL_HOST=mail.huntred.com
EMAIL_PORT=587
EMAIL_HOST_USER=hola@huntred.com
EMAIL_HOST_PASSWORD=Natalia&Patricio1113!
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Grupo huntRED® (huntRED, huntU, Amigro)

# Localization (NUEVO)
LANGUAGE_CODE=es-mx
TIMEZONE=America/Mexico_City

# Static and Media Files (NUEVO)
STATIC_URL=/static/
MEDIA_URL=/media/

# API Rate Limiting (NUEVO)
THROTTLE_ANON=100/day
THROTTLE_USER=1000/day

# Security Settings (NUEVO)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY
# == Python ==
PY_VERSION="python3"
VENV_DIR="$PROJECT_DIR/venv"

# == SWAP ==
SWAP_SIZE="4G"

# == Archivos de config gunicorn/nginx ==
GUNICORN_SOCKET="$PROJECT_DIR/gunicorn.sock"
GUNICORN_SERVICE="/etc/systemd/system/gunicorn.service"
NGINX_SITE="/etc/nginx/sites-available/$APP_NAME"
NGINX_LINK="/etc/nginx/sites-enabled/$APP_NAME"

################################
echo "==========================================================="
echo " [1/10] ACTUALIZANDO Y PREPARANDO LA VM "
echo "==========================================================="
sleep 2

apt-get update -y
apt-get upgrade -y
apt-get autoremove -y

# Herramientas base
apt-get install -y software-properties-common curl git htop ncdu fail2ban logrotate build-essential

################################
echo "==========================================================="
echo " [2/10] CREANDO Y CONFIGURANDO GRUPO '$MAIN_GROUP' "
echo "==========================================================="
sleep 2

# Crea el grupo si no existe
if ! getent group "$MAIN_GROUP" >/dev/null; then
    groupadd "$MAIN_GROUP"
    echo "Grupo '$MAIN_GROUP' creado."
else
    echo "Grupo '$MAIN_GROUP' ya existe."
fi

# Añade usuarios al grupo (si existen)
for usr in "${ALL_USERS[@]}"; do
    usermod -aG "$MAIN_GROUP" "$usr" 2>/dev/null || true
done

################################
echo "==========================================================="
echo " [3/10] CONFIGURANDO SWAP "
echo "==========================================================="
sleep 2

if [ ! -f /swapfile ]; then
    echo "Creando SWAP de $SWAP_SIZE"
    fallocate -l $SWAP_SIZE /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
else
    echo "SWAP ya existe, omitiendo."
fi

################################
echo "==========================================================="
echo " [4/10] INSTALANDO POSTGRESQL, REDIS, NGINX, CERTBOT, PYTHON"
echo "==========================================================="
sleep 2

# PURGAR POSTGRES Y REDIS
echo "Eliminando instalaciones previas de PostgreSQL & Redis..."
apt purge --auto-remove -y postgresql* redis-server* || true

echo "Instalando base packages..."
DEBIAN_FRONTEND=noninteractive apt update -y
DEBIAN_FRONTEND=noninteractive apt install -y \
    postgresql postgresql-contrib redis-server nginx certbot python3-certbot-nginx \
    $PY_VERSION $PY_VERSION-dev python3-pip python3-venv libpq-dev

################################
echo "==========================================================="
echo " [5/10] CONFIGURANDO POSTGRESQL Y REDIS "
echo "==========================================================="
sleep 2

# POSTGRES
systemctl enable postgresql
systemctl start postgresql

echo "Recreando DB '$DB_NAME' y usuario '$DB_USER' (ADVERTENCIA: se borran si existen)."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME"
sudo -u postgres psql -c "DROP ROLE IF EXISTS $DB_USER"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD'"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER"

# REDIS: Forzar 'supervised no' y si systemd falla, se lanza manual daemon
echo "Forcing supervised no in /etc/redis/redis.conf..."
sed -i 's/^supervised .*/supervised no/' /etc/redis/redis.conf || true

echo "Disabling redis-server from systemd..."
systemctl disable redis-server || true
systemctl stop redis-server || true

echo "Attempting to start Redis with systemd anyway..."
systemctl enable redis-server || true
if ! systemctl start redis-server; then
    echo "systemd start redis-server failed. Using manual daemonize..."
    redis-server --daemonize yes
fi

################################
echo "==========================================================="
echo " [6/10] CLONANDO REPO GITHUB EN $PROJECT_DIR "
echo "==========================================================="
sleep 2

mkdir -p "$PROJECT_DIR"
chgrp -R "$MAIN_GROUP" "$PROJECT_DIR"
chmod -R g+rwX "$PROJECT_DIR"

if [ ! -d "$PROJECT_DIR/.git" ]; then
  echo "Clonando repo: $REPO_URL"
  git clone "$REPO_URL" "$PROJECT_DIR"
else
  echo "Repositorio ya existe, haciendo reset/pull..."
  cd "$PROJECT_DIR"
  git reset --hard || true
  git pull || true
fi

echo "Configuring git safe.directory for $PROJECT_DIR"
# Make sure we set safe.directory so “dubious ownership” is resolved
sudo -u "$APP_USER" git config --global --add safe.directory "$PROJECT_DIR" || true

chown -R "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR"
chmod -R g+rwX "$PROJECT_DIR"

echo "Done. Redis should be running, and Git safe.directory set."

################################
echo "==========================================================="
echo " [7/10] CREANDO ENTORNO VIRTUAL E INSTALANDO REQUIREMENTS "
echo "==========================================================="
sleep 2

if [ ! -d "$VENV_DIR" ]; then
    su - "$APP_USER" -c "$PY_VERSION -m venv $VENV_DIR"
fi

# Instalar requirements
sudo -i -u "$APP_USER" bash <<EOF
cd "$PROJECT_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
pip install wheel

# IMPORTANTE: si en tu requirements.txt hay dependencias imposibles (ej: torch==2.5.1+cpu),
# quítalas o coméntalas. De lo contrario fallará.
if [ -f requirements.txt ]; then
    pip install -r requirements.txt || true
fi
EOF

################################
echo "==========================================================="
echo " [8/10] CONFIGURANDO GUNICORN SYSTEMD "
echo "==========================================================="
sleep 2

cat > "$GUNICORN_SERVICE" <<EOF
[Unit]
Description=Gunicorn for $APP_NAME
After=network.target

[Service]
User=$APP_USER
Group=$MAIN_GROUP
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/gunicorn --workers 3 --bind unix:$GUNICORN_SOCKET $APP_NAME.wsgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable gunicorn
systemctl restart gunicorn

################################
echo "==========================================================="
echo " [9/10] CONFIGURANDO NGINX + CERTBOT "
echo "==========================================================="
sleep 2

rm -f "$NGINX_LINK" || true

cat > "$NGINX_SITE" <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    location /static/ {
        root $PROJECT_DIR;
        expires 30d;
        access_log off;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$GUNICORN_SOCKET;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    client_max_body_size 10M;
}
EOF

ln -sf "$NGINX_SITE" "$NGINX_LINK"
nginx -t && systemctl restart nginx

# Certbot SSL (opcional)
if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "localhost" ]; then
  certbot --nginx -d "$DOMAIN" -m "$EMAIL" --agree-tos --non-interactive || echo "Certbot falló o dominio no apunta."
fi

################################
echo "==========================================================="
echo " [10/10] MIGRACIONES DJANGO, COLLECTSTATIC, ETC. "
echo "==========================================================="
sleep 2

# .env + Migrate
sudo -i -u "$APP_USER" bash <<EOF
cd "$PROJECT_DIR"
source "$VENV_DIR/bin/activate"

# Generamos .env con DB/SECRET/REDIS info
cat > .env <<ENDENV
# Django / Python
DJANGO_SECRET_KEY=$SECRET_KEY
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=$DOMAIN,127.0.0.1,localhost

# PostgreSQL
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT

# Redis
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
ENDENV

python manage.py migrate --noinput || true
python manage.py collectstatic --noinput || true
EOF

systemctl restart gunicorn
systemctl restart nginx

echo "==========================================================="
echo "DEPLOY FINALIZADO."
echo "==========================================================="
echo "Verifica con: "
echo "  systemctl status gunicorn"
echo "  systemctl status nginx"
echo "  systemctl status redis-server"
echo "  curl -I http://\$DOMAIN"
echo
echo "Si todo está bien, tu Django está en http://$DOMAIN/ (HTTP)."
echo "Si Certbot funcionó, deberías poder usar HTTPS."
echo "==========================================================="