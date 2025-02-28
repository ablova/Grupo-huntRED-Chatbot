#!/bin/bash
# setup_server.sh
# Script unificado para configurar la instancia, desplegar la aplicación y optimizar Celery.
# Asegúrate de tener configuradas las variables de entorno necesarias y de que las dependencias estén instaladas.

set -euo pipefail  # Modo estricto para detectar errores

# -------------------- VARIABLES --------------------
APP_USER="pablo"  # Usuario con el que se ejecutará la app
PROJECT_ID="Grupo-huntRED"
ZONE="us-central1-a"
INSTANCE_NAME="grupo-huntred"
MACHINE_TYPE="e2-medium"
DISK_SIZE="20GB"
IMAGE_FAMILY="ubuntu-2204-lts"
IMAGE_PROJECT="ubuntu-os-cloud"
EXTERNAL_IP="34.57.227.244"

# Definimos el directorio del proyecto de forma coherente (se usará para clonar el repo y alojar la app)
PROJECT_DIR="/home/$APP_USER"
VENV_DIR="$PROJECT_DIR/venv"

DB_NAME="grupo_huntred_ai_db"
DB_USER="grupo_huntred_user"
DB_PASSWORD="Natalia&Patricio1113!"
ALLOWED_HOSTS="ai.huntred.com,localhost,$EXTERNAL_IP"
APP_NAME="ai_huntred"
DOMAIN="ai.huntred.com"
EMAIL="hola@huntred.com"
GITHUB_PAT="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"
GITHUB_REPO="https://${GITHUB_PAT}@github.com/ablova/Grupo-huntRED-Chatbot.git"
SWAP_SIZE="4G"
LOG_DIR="/var/log/$APP_NAME"

CELERY_WORKER_SERVICE="celery-worker"
CELERY_SCRAPING_SERVICE="celery-scraping"
CELERY_ML_SERVICE="celery-ml"
CELERY_BEAT_SERVICE="celery-beat"
CELERY_MONITOR_SERVICE="celery-monitor"


set -euo pipefail

echo '=== Actualizando el sistema ==='
sudo apt-get update -y && sudo apt-get upgrade -y && sudo apt-get autoremove -y

echo '=== Instalando dependencias necesarias ==='
sudo apt-get install -y python3 python3-pip python3-venv python3-dev build-essential \
    libpq-dev nginx certbot python3-certbot-nginx postgresql postgresql-contrib git curl \
    htop ncdu fail2ban logrotate redis-server mailutils

echo '=== Configurando SWAP ($SWAP_SIZE) ==='
if [ ! -f /swapfile ]; then
    sudo fallocate -l $SWAP_SIZE /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

echo '=== Configurando PostgreSQL ==='
# Corregido el manejo de comillas para que la consulta se interprete correctamente
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME';\" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;\"
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER';\" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\"

echo '=== Configurando clonación de GitHub ==='
if [ ! -d \"$PROJECT_DIR\" ]; then
    sudo mkdir -p \"$PROJECT_DIR\"
    sudo chown $APP_USER:www-data \"$PROJECT_DIR\"
fi
cd \"$PROJECT_DIR\"
if [ ! -d .git ]; then
    git clone \"$GITHUB_REPO\" .
else
    echo 'Repositorio ya clonado. Haciendo pull...'
    git reset --hard && git pull
fi

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
Description=Gunicorn daemon for $APP_NAME
After=network.target

[Service]
User=$APP_USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/gunicorn --workers 4 --threads 2 --bind unix:$PROJECT_DIR/gunicorn.sock $APP_NAME.wsgi:application
Restart=always
# Opcional: preload-app para reducir uso de memoria (ajusta según pruebas)
# ExecStartPre=$VENV_DIR/bin/python -c 'import multiprocessing; print(multiprocessing.cpu_count())'

[Install]
WantedBy=multi-user.target
EOF

echo '=== Configurando Nginx ==='
cat <<EOF | sudo tee /etc/nginx/sites-available/$APP_NAME
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root $PROJECT_DIR;
        # Habilitar caching estático para mayor eficiencia
        expires max;
        add_header Cache-Control public;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$PROJECT_DIR/gunicorn.sock;
    }

    client_max_body_size 10M;

    # Habilitar gzip para mejorar la eficiencia en la transferencia
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
EOF
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

echo '=== Generando certificado SSL con Certbot ==='
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL || echo 'Certbot falló. Revisa las configuraciones DNS.'

echo '=== Aplicando migraciones de Django y colectando estáticos ==='
python \"$PROJECT_DIR/manage.py\" makemigrations
python \"$PROJECT_DIR/manage.py\" migrate
python \"$PROJECT_DIR/manage.py\" collectstatic --noinput

echo '=== Configurando y habilitando Gunicorn ==='
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn

# -------------------- CONFIGURACIÓN DE CELERY Y OPTIMIZACIONES --------------------
echo '=== Configurando servicios de Celery y optimizaciones ==='

# 1. celery-worker.service
sudo bash -c 'cat > /etc/systemd/system/celery-worker.service' << "EOF"
[Unit]
Description=Celery Worker for $APP_NAME (Default and Notifications)
After=network.target redis.service postgresql.service
Wants=redis.service postgresql.service

[Service]
Type=simple
User=$APP_USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PYTHONPATH=$PROJECT_DIR"
Environment="DJANGO_SETTINGS_MODULE=$APP_NAME.settings"
ExecStart=$VENV_DIR/bin/celery -A $APP_NAME worker -Q notifications,default --loglevel=INFO --concurrency=2 --max-tasks-per-child=3 --pool=prefork --without-gossip --without-mingle -n worker@%h
ExecStop=/bin/sh -c \"pkill -TERM -P \$MAINPID\"
TimeoutStopSec=300
Restart=on-failure
RestartSec=30
LimitNOFILE=65536
MemoryLimit=600M
CPUQuota=80%
[Install]
WantedBy=multi-user.target
EOF

# 2. celery-scraping.service
sudo bash -c 'cat > /etc/systemd/system/celery-scraping.service' << "EOF"
[Unit]
Description=Celery Worker Scraping for $APP_NAME
After=network.target redis.service postgresql.service
Wants=redis.service postgresql.service

[Service]
Type=simple
User=$APP_USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PYTHONPATH=$PROJECT_DIR"
Environment="DJANGO_SETTINGS_MODULE=$APP_NAME.settings"
ExecStart=$VENV_DIR/bin/celery -A $APP_NAME worker -Q scraping --loglevel=INFO --concurrency=1 --max-tasks-per-child=1 --pool=prefork --without-gossip --without-mingle -n worker_scraping@%h
ExecStop=/bin/sh -c \"pkill -TERM -P \$MAINPID\"
TimeoutStopSec=300
Restart=on-failure
RestartSec=60
LimitNOFILE=65536
MemoryLimit=800M
CPUQuota=90%
[Install]
WantedBy=multi-user.target
EOF

# 3. celery-ml.service
sudo bash -c 'cat > /etc/systemd/system/celery-ml.service' << "EOF"
[Unit]
Description=Celery Worker ML for $APP_NAME
After=network.target redis.service postgresql.service
Wants=redis.service postgresql.service

[Service]
Type=simple
User=$APP_USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PYTHONPATH=$PROJECT_DIR"
Environment="DJANGO_SETTINGS_MODULE=$APP_NAME.settings"
ExecStart=$VENV_DIR/bin/celery -A $APP_NAME worker -Q ml --loglevel=INFO --concurrency=1 --max-tasks-per-child=1 --pool=prefork --without-gossip --without-mingle -n worker_ml@%h
ExecStop=/bin/sh -c \"pkill -TERM -P \$MAINPID\"
TimeoutStopSec=600
Restart=on-failure
RestartSec=120
LimitNOFILE=65536
MemoryLimit=1G
CPUQuota=90%
[Install]
WantedBy=multi-user.target
EOF

# 4. celery-beat.service
sudo bash -c 'cat > /etc/systemd/system/celery-beat.service' << "EOF"
[Unit]
Description=Celery Beat Service for $APP_NAME
After=network.target redis.service postgresql.service
Wants=redis.service postgresql.service

[Service]
Type=simple
User=$APP_USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PYTHONPATH=$PROJECT_DIR"
Environment="DJANGO_SETTINGS_MODULE=$APP_NAME.settings"
ExecStartPre=/bin/sleep 10
ExecStart=$VENV_DIR/bin/celery -A $APP_NAME beat --loglevel=INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler --max-interval=300
ExecStop=/bin/kill -s TERM \$MAINPID
TimeoutStopSec=180
Restart=on-failure
RestartSec=60
LimitNOFILE=65536
MemoryLimit=200M
CPUQuota=30%
[Install]
WantedBy=multi-user.target
EOF

# 5. Crear script de monitoreo para Celery y servicio systemd asociado
echo '=== Creando script de monitoreo para Celery ==='
sudo mkdir -p /home/$APP_USER/scripts
cat > /home/$APP_USER/scripts/monitor_celery.sh << "EOF"
#!/bin/bash
# Script para monitorear y reiniciar servicios de Celery si es necesario

LOG_FILE="/var/log/celery_monitor.log"
SERVICES=("celery-worker" "celery-scraping" "celery-ml" "celery-beat")
EMAIL="pablo@example.com"  # Cambia este correo por el tuyo

touch \$LOG_FILE
chmod 644 \$LOG_FILE

log() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S') - \$1" >> \$LOG_FILE
    echo "\$(date '+%Y-%m-%d %H:%M:%S') - \$1"
}

check_redis() {
    if ! redis-cli ping > /dev/null 2>&1; then
        log 'ERROR: Redis no responde. Reiniciando...'
        sudo systemctl restart redis
        sleep 5
        if ! redis-cli ping > /dev/null 2>&1; then
            log 'CRÍTICO: Reinicio de Redis fallido.'
            echo \"Redis falló en \$(hostname)\" | mail -s 'CRÍTICO: Redis Down' \$EMAIL
            return 1
        else
            log 'Redis reiniciado correctamente.'
            return 0
        fi
    fi
    return 0
}

check_celery_services() {
    local restart_count=0
    for service in \"\${SERVICES[@]}\"; do
        if ! systemctl is-active --quiet \$service; then
            log \"ADVERTENCIA: \$service no está activo. Reiniciando...\"
            sudo systemctl restart \$service
            sleep 10
            restart_count=\$((restart_count + 1))
            if ! systemctl is-active --quiet \$service; then
                log \"ERROR: Falló reinicio de \$service\"
            else
                log \"\$service reiniciado correctamente.\"
            fi
        fi
        pid=\$(pgrep -f \"celery.*\$service\" | head -n1)
        if [ ! -z \"\$pid\" ]; then
            mem_usage=\$(ps -o rss= -p \$pid | awk '{print \$1/1024}')
            if (( \$(echo \"\$mem_usage > 900\" | bc -l) )); then
                log \"ADVERTENCIA: \$service usando \${mem_usage}MB. Reiniciando...\"
                sudo systemctl restart \$service
                sleep 10
                restart_count=\$((restart_count + 1))
            fi
        fi
    done
    if [ \$restart_count -gt 2 ]; then
        log 'Múltiples servicios reiniciados. Posible problema en el sistema.'
        echo \"Varios servicios Celery reiniciados en \$(hostname)\" | mail -s 'ADVERTENCIA: Reinicios de Celery' \$EMAIL
    fi
}

# Usar PROJECT_DIR para mayor consistencia
rm -f \"$PROJECT_DIR\"/*.pid 2>/dev/null

log 'Iniciando monitoreo de servicios Celery'

while true; do
    check_redis
    check_celery_services
    free_mem=\$(free -m | awk 'NR==2{print \$4}')
    if [ \$free_mem -lt 200 ]; then
        log \"ADVERTENCIA: Memoria baja (\$free_mem MB libres). Limpiando caché...\"
        sudo sync && sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
    fi
    sleep 300
done
EOF
sudo chmod +x /home/$APP_USER/scripts/monitor_celery.sh

# Crear servicio systemd para el monitoreo de Celery
sudo bash -c 'cat > /etc/systemd/system/celery-monitor.service' << "EOF"
[Unit]
Description=Monitoreo y recuperación automática de servicios Celery
After=network.target

[Service]
Type=simple
User=root
ExecStart=/home/$APP_USER/scripts/monitor_celery.sh
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

sudo chmod 644 /etc/systemd/system/celery-monitor.service

echo '=== Recargando systemd y arrancando servicios de Celery ==='
sudo systemctl daemon-reload

# Detener servicios existentes (si los hay)
for service in celery-worker celery-scraping celery-ml celery-beat; do
    sudo systemctl stop \$service || true
done

rm -f \"$PROJECT_DIR\"/*.pid 2>/dev/null || true

# Iniciar servicios en orden
sudo systemctl start celery-beat
sleep 5
sudo systemctl start celery-worker
sleep 5
sudo systemctl start celery-scraping
sleep 5
sudo systemctl start celery-ml
sleep 5

# Habilitar servicios en arranque
for service in celery-worker celery-scraping celery-ml celery-beat celery-monitor; do
    sudo systemctl enable \$service
done

sudo systemctl start celery-monitor

echo '===== Configuración completa de servidor y Celery finalizada ====='
echo 'Logs de monitoreo en: /var/log/celery_monitor.log'