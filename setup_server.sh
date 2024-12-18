#!/bin/bash

set -e  # Termina el script si ocurre un error

# Variables globales
EXTERNAL_IP="35.209.109.141"
PROJECT_DIR="/home/pablollh"
VENV_DIR="$PROJECT_DIR/venv"
GITHUB_REPO="https://ablova:${GITHUB_PAT}@github.com/ablova/Grupo-huntRED-Chatbot.git"
DB_NAME="chatbot_db"
DB_USER="amigro_user"
DB_PASSWORD="Natalia&Patricio1113!"
ALLOWED_HOSTS="chatbot.amigro.org,localhost,$EXTERNAL_IP"
APP_NAME="chatbot_django"
DOMAIN="chatbot.amigro.org"
EMAIL="hola@huntred.com"
GITHUB_PAT="github_pat_.......hi84"
SWAP_SIZE="4G"  # Tamaño del SWAP
LOG_DIR="/var/log/$APP_NAME"

# -------------------- INICIO --------------------

echo "=== Actualizando el sistema ==="
sudo apt-get update -y && sudo apt-get upgrade -y && sudo apt-get autoremove -y

echo "=== Configurando Firewall ==="
#sudo ufw allow OpenSSH
#sudo ufw allow 'Nginx Full'
#sudo ufw enable

echo "=== Instalando dependencias necesarias ==="
sudo apt-get install -y python3 python3-pip python3-venv python3-dev build-essential \
    libpq-dev nginx certbot python3-certbot-nginx postgresql postgresql-contrib git curl \
    htop ncdu fail2ban logrotate

# ----------------- CONFIGURACIÓN DE SWAP -----------------
echo "=== Configurando SWAP ($SWAP_SIZE) ==="
sudo fallocate -l $SWAP_SIZE /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# ---------------- CONFIGURACIÓN DE GITHUB ----------------
echo "=== Configurando GitHub PAT ==="
if [ ! -f "$HOME/.github_pat" ]; then
    echo "$GITHUB_PAT" > "$HOME/.github_pat"
    chmod 600 "$HOME/.github_pat"
fi

echo "=== Clonando el repositorio desde GitHub ==="
if [ ! -d "$PROJECT_DIR" ]; then
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown -R $USER:$USER "$PROJECT_DIR"
    git clone "$GITHUB_REPO" "$PROJECT_DIR"
else
    echo "El directorio del proyecto ya existe. Actualizando..."
    cd "$PROJECT_DIR"
    git pull origin main
fi

# ---------------- CONFIGURACIÓN DE POSTGRESQL ----------------
echo "=== Configurando PostgreSQL ==="
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" || echo "Base de datos ya creada."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || echo "Usuario ya creado."
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# ---------------- CREACIÓN DE ENTORNO VIRTUAL ----------------
echo "=== Creando entorno virtual ==="
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

echo "=== Instalando dependencias del proyecto ==="
pip install --upgrade pip
pip install -r "$PROJECT_DIR/requirements.txt"

# ---------------- CONFIGURACIÓN DE GUNICORN ----------------
echo "=== Configurando Gunicorn ==="
cat <<EOF | sudo tee /etc/systemd/system/gunicorn.service
[Unit]
Description=gunicorn daemon for $APP_NAME
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/gunicorn --workers 4 --threads 2 --bind unix:$PROJECT_DIR/gunicorn.sock $APP_NAME.wsgi:application
LimitNOFILE=4096
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# ---------------- CONFIGURACIÓN DE CELERY ----------------
echo "=== Configurando Celery ==="
cat <<EOF | sudo tee /etc/systemd/system/celery.service
[Unit]
Description=Celery Service
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/celery -A $APP_NAME worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# ---------------- CONFIGURACIÓN DE CELERYBEAT ----------------
echo "=== Configurando Celerybeat ==="
cat <<EOF | sudo tee /etc/systemd/system/celerybeat.service
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/celery -A $APP_NAME beat --loglevel=info --pidfile=/tmp/celerybeat.pid
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# ---------------- CONFIGURACIÓN DE NGINX ----------------
echo "=== Configurando Nginx (HTTP) ==="
cat <<EOF | sudo tee /etc/nginx/sites-available/$APP_NAME
server {
    listen 80;
    server_name $DOMAIN;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root $PROJECT_DIR;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$PROJECT_DIR/gunicorn.sock;
    }

    client_max_body_size 10M;
}
EOF

sudo ln -s /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo "=== Generando certificado SSL con Certbot ==="
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL

echo "=== Configurando rotación de logs ==="
sudo mkdir -p $LOG_DIR
cat <<EOF | sudo tee /etc/logrotate.d/$APP_NAME
$LOG_DIR/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 $USER www-data
    sharedscripts
    postrotate
        systemctl reload $APP_NAME > /dev/null 2>/dev/null || true
    endscript
}
EOF

# ---------------- MIGRACIONES Y ESTÁTICOS ----------------
echo "=== Aplicando migraciones de Django ==="
python "$PROJECT_DIR/manage.py" makemigrations
python "$PROJECT_DIR/manage.py" migrate
python "$PROJECT_DIR/manage.py" collectstatic --noinput


# ---------------- HABILITANDO SERVICIOS ----------------
echo "=== Habilitando servicios Gunicorn, Celery y Celerybeat ==="
sudo systemctl daemon-reload
sudo systemctl enable gunicorn celery celerybeat
sudo systemctl start gunicorn celery celerybeat

echo "=== Verificando servicios ==="
sudo systemctl status gunicorn celery celerybeat
sudo systemctl status nginx

python "$PROJECT_DIR/manage.py" migrate django_celery_beat
echo "=== Configuración completada con éxito ==="