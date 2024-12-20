#!/bin/bash

set -e  # Termina el script si ocurre un error

# -------------------- VARIABLES --------------------
PROJECT_ID="Grupo-huntRED"
ZONE="us-central1-a"
INSTANCE_NAME="grupo-huntred"
MACHINE_TYPE="e2-medium"
DISK_SIZE="15GB"
IMAGE_FAMILY="ubuntu-2204-lts"
IMAGE_PROJECT="ubuntu-os-cloud"
EXTERNAL_IP="34.57.227.244"
PROJECT_DIR="/home/pablollh"
VENV_DIR="$PROJECT_DIR/venv"
GITHUB_REPO="https://${GITHUB_PAT}@github.com/ablova/Grupo-huntRED-Chatbot.git"
DB_NAME="grupo_huntred_ai_db"
DB_USER="grupo_huntred_user"
DB_PASSWORD="Natalia&Patricio1113!"
ALLOWED_HOSTS="ai.huntred.com,localhost,$EXTERNAL_IP"
APP_NAME="ai_huntred"
DOMAIN="ai.huntred.com"
EMAIL="hola@huntred.com"
GITHUB_PAT="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"
SWAP_SIZE="4G"
LOG_DIR="/var/log/$APP_NAME"

# -------------------- CREAR INSTANCIA --------------------
echo "=== Creando la instancia en Google Cloud ==="
gcloud compute instances create $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --boot-disk-size=$DISK_SIZE \
    --image-family=$IMAGE_FAMILY \
    --image-project=$IMAGE_PROJECT \
    --tags=http-server,https-server \
    --quiet

echo "=== Esperando a que la instancia esté activa... ==="
sleep 60

# -------------------- CONFIGURACIÓN REMOTA --------------------
echo "=== Conectando y configurando la instancia ==="
gcloud compute ssh $INSTANCE_NAME --project=$PROJECT_ID --zone=$ZONE --command "
    set -e  # Termina el script si ocurre un error

    echo '=== Actualizando el sistema ==='
    sudo apt-get update -y && sudo apt-get upgrade -y && sudo apt-get autoremove -y

    echo '=== Instalando dependencias necesarias ==='
    sudo apt-get install -y python3 python3-pip python3-venv python3-dev build-essential \
        libpq-dev nginx certbot python3-certbot-nginx postgresql postgresql-contrib git curl \
        htop ncdu fail2ban logrotate

    echo '=== Configurando SWAP ($SWAP_SIZE) ==='
    if [ ! -f /swapfile ]; then
        sudo fallocate -l $SWAP_SIZE /swapfile
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    fi

    echo '=== Configurando PostgreSQL ==='
    sudo -u postgres psql -tc \"SELECT 1 FROM pg_database WHERE datname = '$DB_NAME';\" | grep -q 1 || \
        sudo -u postgres psql -c \"CREATE DATABASE $DB_NAME;\"
    sudo -u postgres psql -tc \"SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER';\" | grep -q 1 || \
        sudo -u postgres psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\"
    sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\"

    echo '=== Configurando clonación de GitHub ==='
    if [ ! -d \"$PROJECT_DIR\" ]; then
        sudo mkdir -p \"$PROJECT_DIR\"
        sudo chown \$USER:www-data \"$PROJECT_DIR\"
    fi
    cd \"$PROJECT_DIR\"
    git clone \"$GITHUB_REPO\" . || (echo 'Repositorio ya clonado. Haciendo pull...' && git reset --hard && git pull)

    echo '=== Creando entorno virtual ==='
    if [ ! -d \"$VENV_DIR\" ]; then
        python3 -m venv \"$VENV_DIR\"
    fi
    source \"$VENV_DIR/bin/activate\"

    echo '=== Instalando dependencias del proyecto ==='
    pip install --upgrade pip
    pip install -r \"$PROJECT_DIR/requirements.txt\"

    echo '=== Configurando Gunicorn ==='
    cat <<EOF | sudo tee /etc/systemd/system/gunicorn.service
[Unit]
Description=gunicorn daemon for $APP_NAME
After=network.target

[Service]
User=\$USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/gunicorn --workers 4 --threads 2 --bind unix:$PROJECT_DIR/gunicorn.sock $APP_NAME.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    echo '=== Configurando Nginx ==='
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
    sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx

    echo '=== Generando certificado SSL con Certbot ==='
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL || echo 'Certbot falló. Revisa las configuraciones DNS.'

    echo '=== Aplicando migraciones de Django ==='
    python \"$PROJECT_DIR/manage.py\" makemigrations
    python \"$PROJECT_DIR/manage.py\" migrate
    python \"$PROJECT_DIR/manage.py\" collectstatic --noinput

    echo '=== Habilitando servicios ==='
    sudo systemctl daemon-reload
    sudo systemctl enable gunicorn
    sudo systemctl start gunicorn

    echo '=== Configuración completada ==='
"