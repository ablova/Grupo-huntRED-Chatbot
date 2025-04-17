#!/bin/bash
############################################################################################
# Nombre: setup_server.sh
# Descripción:
#   Despliega una aplicación Django en una VM Ubuntu 22.04 LTS limpia:
#   - Crea grupo 'ai_huntred' y usuario 'pablollh'.
#   - Instala la última versión estable de Git (LTS) usando el PPA oficial.
#   - Instala y configura Django, Gunicorn, PostgreSQL, Redis, Nginx, Celery, y Certbot SSL.
#   - Purga y reinstala PostgreSQL/Redis; crea DB, corre migraciones, carga datos iniciales.
#   - Configura Redis para systemd y optimiza uso de CPU.
#   - Clona el repositorio Grupo-huntRED-Chatbot en /home/pablollh con autenticación.
#   - Instala requirements en un entorno virtual, incluyendo sentry-sdk.
#   - Configura Gunicorn, Nginx, Celery, y crea un superusuario para Django admin.
#   - Configura HTTPS para ai.huntred.com con Certbot.
#   - Añade alias personalizados al entorno del usuario.
#
# *** ADVERTENCIA: Este script PURGA y REINSTALA todo en la VM ***
# Úsalo para levantar la infraestructura desde cero.
#
# *** NOTA: La eliminación/recreación de la VM debe ejecutarse manualmente desde tu máquina local ***
# Antes de correr este script, elimina y recrea la VM con:
#   gcloud compute instances delete grupo-huntred --project=grupo-huntred --zone=us-central1-a --quiet
#gcloud compute instances create grupo-huntred \
#    --project=grupo-huntred \
#    --zone=us-central1-a \
#    --machine-type=e2-standard-4 \
#    --network-interface=address=34.57.227.244,network-tier=PREMIUM \
#    --image-family=ubuntu-2204-lts \
#    --image-project=ubuntu-os-cloud \
#    --boot-disk-size=30GB \
#    --boot-disk-type=pd-ssd \
#    --tags=http-server,https-server \
#    --service-account=472786450192-compute@developer.gserviceaccount.com \
#    --shielded-secure-boot \
#    --labels=entorno=produccion,proyecto=Inteligencia Artificual Grupo huntRED® \
#    --metadata=startup-script='#!/bin/bash
#        apt-get update
#        apt-get install -y python3 python3-pip python3-venv git
#    '
#
# Uso:
#   1) Subir a la VM: scp setup_server.sh pablollh@34.57.227.244:/home/pablollh/
#   2) Dar permisos: sudo chmod +x /home/pablollh/setup_server.sh
#   3) Ejecutar: sudo /home/pablollh/setup_server.sh
#   sudo nano setup_server.sh && sudo chmod +x /home/pablollh/setup_server.sh && sudo /home/pablollh/setup_server.sh
# Notas:
#   - Configurado para usuario 'pablollh' y grupo 'ai_huntred'.
#   - Usa e2-standard-4 (16 GB RAM) con disco de 30 GB para manejar picos de CPU.
#   - Requiere que ai.huntred.com resuelva a 34.57.227.244 para HTTPS.
#   - Incluye swap de 4 GB para mitigar problemas de memoria.
############################################################################################

set -euo pipefail

################################
##        CONFIGURACIONES     ##
################################

# == Grupo y usuario ==
MAIN_GROUP="ai_huntred"
APP_USER="pablollh"

# == Proyecto ==
PROJECT_DIR="/home/pablollh"
APP_NAME="ai_huntred"
REPO_URL="https://ablova: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@github.com/ablova/Grupo-huntRED-Chatbot.git"
TEMP_CLONE_DIR="/tmp/repo_clone"

# == Gunicorn/Nginx ==
DOMAIN="ai.huntred.com"
EMAIL="hola@huntred.com"
SECRET_KEY="hfmrpTNRwmQ1F7gZI1DNKaQ9gNw3cgayKFB0HK_gt9BKJEnLy60v1v0PnkZtX3OkY48"
GUNICORN_SOCKET="$PROJECT_DIR/gunicorn.sock"
GUNICORN_SERVICE="/etc/systemd/system/gunicorn.service"
NGINX_SITE="/etc/nginx/sites-available/$APP_NAME"
NGINX_LINK="/etc/nginx/sites-enabled/$APP_NAME"

# == PostgreSQL ==
DB_NAME="g_huntred_ai_db"
DB_USER="g_huntred_pablo"
DB_PASSWORD="Natalia&Patricio1113!"
DB_HOST="localhost"
DB_PORT="5432"
DB_CONN_MAX_AGE=60
DB_CONNECT_TIMEOUT=10

# == Python ==
PY_VERSION="python3"
VENV_DIR="$PROJECT_DIR/venv"

# == Celery ==
CELERY_SERVICE="/etc/systemd/system/celery.service"

# == SWAP ==
SWAP_SIZE="4G"

# == Directorios ==
LOG_DIR="$PROJECT_DIR/logs"
STATIC_DIR="$PROJECT_DIR/staticfiles"
MEDIA_DIR="$PROJECT_DIR/media"
TFHUB_CACHE="$PROJECT_DIR/tfhub_cache"

################################
echo "==========================================================="
echo " [1/11] ACTUALIZANDO Y PREPARANDO LA VM "
echo "==========================================================="
sleep 2

apt-get update -y
apt-get upgrade -y
apt-get autoremove -y

# Instalar herramientas base y dependencias
apt-get install -y software-properties-common curl git htop ncdu fail2ban logrotate \
    build-essential python3-dev python3-pip python3-venv libpq-dev \
    libblas-dev liblapack-dev gfortran libjpeg-dev zlib1g-dev libffi-dev libssl-dev

# Instalar la última versión estable de Git
echo "Instalando Git LTS..."
add-apt-repository ppa:git-core/ppa -y
apt-get update -y
apt-get install -y git
git --version

################################
echo "==========================================================="
echo " [2/11] CREANDO Y CONFIGURANDO GRUPO '$MAIN_GROUP' Y USUARIO '$APP_USER' "
echo "==========================================================="
sleep 2

# Crear grupo si no existe
if ! getent group "$MAIN_GROUP" >/dev/null; then
    groupadd "$MAIN_GROUP"
    echo "Grupo '$MAIN_GROUP' creado."
else
    echo "Grupo '$MAIN_GROUP' ya existe."
fi

# Crear usuario pablollh si no existe
if ! id "$APP_USER" >/dev/null 2>&1; then
    useradd -m -s /bin/bash -g "$MAIN_GROUP" "$APP_USER"
    echo "Usuario '$APP_USER' creado."
else
    usermod -g "$MAIN_GROUP" "$APP_USER"
    echo "Usuario '$APP_USER' asignado al grupo '$MAIN_GROUP'."
fi

# Añadir www-data al grupo
usermod -aG "$MAIN_GROUP" www-data 2>/dev/null || true

################################
echo "==========================================================="
echo " [3/11] CONFIGURANDO SWAP "
echo "==========================================================="
sleep 2

if [ ! -f /swapfile ]; then
    echo "Creando SWAP de $SWAP_SIZE"
    fallocate -l "$SWAP_SIZE" /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
else
    echo "SWAP ya existe, omitiendo."
fi

################################
echo "==========================================================="
echo " [4/11] INSTALANDO POSTGRESQL, REDIS, NGINX, CERTBOT, PYTHON "
echo "==========================================================="
sleep 2

# Purgar instalaciones previas
echo "Eliminando instalaciones previas de PostgreSQL, Redis..."
apt purge --auto-remove -y postgresql* redis-server* || true

# Instalar paquetes
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    postgresql postgresql-contrib redis-server nginx certbot python3-certbot-nginx \
    "$PY_VERSION" python3-pip python3-venv libpq-dev

################################
echo "==========================================================="
echo " [5/11] CONFIGURANDO POSTGRESQL Y REDIS "
echo "==========================================================="
sleep 2

# PostgreSQL
systemctl enable postgresql
systemctl start postgresql

echo "Configurando base de datos '$DB_NAME' y usuario '$DB_USER'..."
cd /tmp
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME" || true
sudo -u postgres psql -c "DROP ROLE IF EXISTS $DB_USER" || true
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD'"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER"
cd - >/dev/null

# Redis
echo "Configurando Redis..."
sed -i 's/^supervised .*/supervised systemd/' /etc/redis/redis.conf || true
sed -i 's/^daemonize .*/daemonize no/' /etc/redis/redis.conf || true
echo "maxmemory 512mb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf

systemctl enable redis-server
systemctl restart redis-server

################################
echo "==========================================================="
echo " [6/11] CLONANDO O ACTUALIZANDO REPOSITORIO EN $PROJECT_DIR "
echo "==========================================================="
sleep 2

# Asegurar que el directorio existe
mkdir -p "$PROJECT_DIR"
chown "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR"
chmod 775 "$PROJECT_DIR"

# Mover setup_server.sh temporalmente si existe
if [ -f "$PROJECT_DIR/setup_server.sh" ]; then
    mv "$PROJECT_DIR/setup_server.sh" /tmp/setup_server.sh
fi

# Verificar si el repositorio ya está clonado
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "Repositorio ya existe en $PROJECT_DIR, actualizando..."
    su - "$APP_USER" -c "cd $PROJECT_DIR && git fetch && git reset --hard origin/main && git pull"
    if [ $? -ne 0 ]; then
        echo "Error: No se pudo actualizar el repositorio. Verifica la conexión o el token."
        exit 1
    fi
else
    echo "Clonando el repositorio en $TEMP_CLONE_DIR..."
    rm -rf "$TEMP_CLONE_DIR"
    su - "$APP_USER" -c "git clone $REPO_URL $TEMP_CLONE_DIR"
    if [ $? -ne 0 ]; then
        echo "Error: No se pudo clonar el repositorio. Verifica la URL, el token o los permisos."
        exit 1
    fi
    echo "Moviendo archivos a $PROJECT_DIR..."
    mv "$TEMP_CLONE_DIR"/* "$TEMP_CLONE_DIR"/.* "$PROJECT_DIR/" 2>/dev/null || true
    rm -rf "$TEMP_CLONE_DIR"
fi

# Ajustar permisos finales
chown -R "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR"
chmod -R 775 "$PROJECT_DIR"

# Restaurar setup_server.sh si fue movido
if [ -f "/tmp/setup_server.sh" ]; then
    mv /tmp/setup_server.sh "$PROJECT_DIR/setup_server.sh"
    chown "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR/setup_server.sh"
    chmod 775 "$PROJECT_DIR/setup_server.sh"
fi

echo "Repositorio clonado o actualizado exitosamente en $PROJECT_DIR."

################################
echo "==========================================================="
echo " [7/11] CREANDO ENTORNO VIRTUAL E INSTALANDO REQUIREMENTS "
echo "==========================================================="
sleep 2

if [ ! -d "$VENV_DIR" ]; then
    su - "$APP_USER" -c "$PY_VERSION -m venv $VENV_DIR"
fi

su - "$APP_USER" -c "source $VENV_DIR/bin/activate && \
    python -m pip install --upgrade pip && \
    pip install wheel && \
    pip install django gunicorn psycopg2-binary redis celery django-celery-beat django-celery-results sentry-sdk && \
    cd $PROJECT_DIR && [ -f requirements.txt ] && pip install -r requirements.txt --no-deps || true"

chown -R "$APP_USER:$MAIN_GROUP" "$VENV_DIR"
chmod -R 775 "$VENV_DIR"

################################
echo "==========================================================="
echo " [8/11] CONFIGURANDO GUNICORN Y CELERY SYSTEMD "
echo "==========================================================="
sleep 2

# Gunicorn
cat > "$GUNICORN_SERVICE" <<EOF
[Unit]
Description=Gunicorn for $APP_NAME
After=network.target

[Service]
User=$APP_USER
Group=$MAIN_GROUP
WorkingDirectory=$PROJECT_DIR
Environment="PYTHONPATH=$PROJECT_DIR"
Environment="DJANGO_SETTINGS_MODULE=$APP_NAME.settings"
ExecStart=$VENV_DIR/bin/gunicorn --workers 2 --bind unix:$GUNICORN_SOCKET --timeout 120 $APP_NAME.wsgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Celery
cat > "$CELERY_SERVICE" <<EOF
[Unit]
Description=Celery Service for $APP_NAME
After=network.target redis-server.service

[Service]
User=$APP_USER
Group=$MAIN_GROUP
WorkingDirectory=$PROJECT_DIR
Environment="PYTHONPATH=$PROJECT_DIR"
Environment="DJANGO_SETTINGS_MODULE=$APP_NAME.settings"
Environment="TFHUB_CACHE_DIR=$TFHUB_CACHE"
Environment="TF_CPP_MIN_LOG_LEVEL=2"
ExecStart=$VENV_DIR/bin/celery -A $APP_NAME worker --loglevel=info --concurrency=2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable gunicorn celery
systemctl restart gunicorn celery

################################
echo "==========================================================="
echo " [9/11] CONFIGURANDO NGINX Y CERTBOT "
echo "==========================================================="
sleep 2

rm -f "$NGINX_LINK" || true

# Configurar Nginx con un bloque HTTP inicial
cat > "$NGINX_SITE" <<EOF
server {
    listen 80;
    server_name $DOMAIN 127.0.0.1 localhost 34.57.227.244;

    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    location /static/ {
        root $PROJECT_DIR;
        expires 30d;
        access_log off;
    }

    location /media/ {
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
        proxy_read_timeout 120;
    }

    client_max_body_size 10M;
}
EOF

ln -sf "$NGINX_SITE" "$NGINX_LINK"
nginx -t && systemctl restart nginx

# Verificar resolución DNS y ejecutar Certbot
echo "Verificando resolución DNS para $DOMAIN..."
if nslookup "$DOMAIN" >/dev/null 2>&1; then
    echo "Dominio $DOMAIN resuelve correctamente. Configurando HTTPS con Certbot..."
    certbot --nginx -d "$DOMAIN" -m "$EMAIL" --agree-tos --non-interactive --redirect || {
        echo "Certbot falló, verifica la configuración DNS o ejecuta manualmente: certbot --nginx -d $DOMAIN"
    }
else
    echo "Advertencia: $DOMAIN no resuelve. Certbot no se ejecutará. Configura el registro DNS A para $DOMAIN a 34.57.227.244 y ejecuta manualmente: certbot --nginx -d $DOMAIN"
fi

################################
echo "==========================================================="
echo " [10/11] MIGRACIONES DJANGO, COLLECTSTATIC, LOADDATA, SUPERUSUARIO "
echo "==========================================================="
sleep 2

# Crear directorios
mkdir -p "$LOG_DIR" "$STATIC_DIR" "$MEDIA_DIR" "$TFHUB_CACHE"
chown -R "$APP_USER:$MAIN_GROUP" "$LOG_DIR" "$STATIC_DIR" "$MEDIA_DIR" "$TFHUB_CACHE"
chmod -R 775 "$LOG_DIR" "$STATIC_DIR" "$MEDIA_DIR" "$TFHUB_CACHE"

# Configurar .env
su - "$APP_USER" -c "cat > $PROJECT_DIR/.env <<ENDENV
DJANGO_SECRET_KEY=$SECRET_KEY
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=$DOMAIN,127.0.0.1,localhost,34.57.227.244
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_CONN_MAX_AGE=$DB_CONN_MAX_AGE
DB_CONNECT_TIMEOUT=$DB_CONNECT_TIMEOUT
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
CELERY_WORKER_CONCURRENCY=2
EMAIL_HOST=mail.huntred.com
EMAIL_PORT=587
EMAIL_HOST_USER=hola@huntred.com
EMAIL_HOST_PASSWORD=Natalia&Patricio1113!
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Grupo huntRED® (huntRED, huntU, Amigro)
SENTRY_DSN=https://e9989a45cedbcefa64566dbcfb2ffd59@o4508638041145344.ingest.us.sentry.io/4508638043766784
SENTRY_SAMPLE_RATE=1.0
SENTRY_SEND_PII=True
SENTRY_DEBUG=False
LANGUAGE_CODE=es-mx
TIMEZONE=America/Mexico_City
STATIC_URL=/static/
MEDIA_URL=/media/
THROTTLE_ANON=100/day
THROTTLE_USER=1000/day
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOW_CREDENTIALS=False
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
GIT_USER=ablova@gmail.com
GIT_PASSWORD=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
ENDENV"

# Ajustar permisos de .env
chmod 600 "$PROJECT_DIR/.env"
chown "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR/.env"

# Configurar credenciales de Git para autenticación automática
su - "$APP_USER" -c "
    git config --global credential.helper store
    echo 'https://ablova@gmail.com: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@github.com' > ~/.git-credentials
    chmod 600 ~/.git-credentials
    git config --global user.email 'ablova@gmail.com'
    git config --global user.name 'ablova'
"

# Ejecutar comandos Django
su - "$APP_USER" -c "source $VENV_DIR/bin/activate && cd $PROJECT_DIR && \
    python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    python manage.py loaddata /home/pablollh/app/fixtures/initial_data.json && \
    echo 'from django.contrib.auth.models import User; User.objects.create_superuser(\"admin\", \"admin@huntred.com\", \"admin123\")' | python manage.py shell"

# Ajustar permisos finales
chown -R "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR"
chmod -R 775 "$PROJECT_DIR"

systemctl restart gunicorn celery nginx

################################
echo "==========================================================="
echo " [11/11] CONFIGURANDO ALIAS Y ENTORNO "
echo "==========================================================="
sleep 2

# Añadir alias a .bashrc
su - "$APP_USER" -c "cat >> /home/$APP_USER/.bashrc << 'EOF'
# === Activar colores en la terminal ===
export LS_OPTIONS='--color=auto'
alias ls='ls \$LS_OPTIONS'
alias ll='ls -la \$LS_OPTIONS'
alias grep='grep --color=auto'

# === Personalizar el prompt (PS1) con colores ===
export PS1=\"\\[\033[1;32m\\]\u@\h:\\[\033[1;34m\\]\w\\[\033[1;36m\\]\$ \\[\033[0m\\]\"

# === Alias generales ===
alias iniciar='cd /home/pablollh && source venv/bin/activate'
alias apt-todo='sudo apt-get update -y && sudo apt-get upgrade -y && sudo apt autoremove -y'

# === Alias para edición rápida de archivos principales ===
alias edit_ai_urls='sudo nano /home/pablollh/ai_huntred/urls.py'
alias edit_settings='sudo nano /home/pablollh/ai_huntred/settings.py'
alias edit_celery='sudo nano /home/pablollh/ai_huntred/celery.py'

alias edit_models='sudo nano /home/pablollh/app/models.py'
alias edit_tasks='sudo nano /home/pablollh/app/tasks.py'
alias edit_admin='sudo nano /home/pablollh/app/admin.py'
alias edit_urls='sudo nano /home/pablollh/app/urls.py'
alias edit_signal='sudo nano /home/pablollh/app/signal.py'
alias edit_monitoring='sudo nano /home/pablollh/app/monitoring.py'

# === Alias para edición de archivos en utilidades ===
alias edit_catalogs='sudo nano /home/pablollh/app/utilidades/catalogs.py'
alias edit_loader='sudo nano /home/pablollh/app/utilidades/loader.py'
alias edit_calendar='sudo nano /home/pablollh/app/utilidades/google_calendar.py'
alias edit_reports='sudo nano /home/pablollh/app/utilidades/report_generator.py'
alias edit_parser='sudo nano /home/pablollh/app/utilidades/parser.py'
alias edit_vacantes='sudo nano /home/pablollh/app/utilidades/vacantes.py'
alias edit_linkedin='sudo nano /home/pablollh/app/utilidades/linkedin.py'

# === Alias para Utilidades ===
alias edit_email='sudo nano /home/pablollh/app/utilidades/email_scraper.py'
alias edit_salario='sudo nano /home/pablollh/app/utilidades/salario.py'
alias edit_scraping='sudo nano /home/pablollh/app/utilidades/scraping.py'

# === Alias para chatbot e integraciones ===
alias edit_chatbot='sudo nano /home/pablollh/app/chatbot/chatbot.py'
alias edit_nlp='sudo nano /home/pablollh/app/chatbot/nlp.py'
alias edit_gpt='sudo nano /home/pablollh/app/chatbot/gpt.py'
alias edit_utils='sudo nano /home/pablollh/app/chatbot/utils.py'
alias edit_intent='sudo nano /home/pablollh/app/chatbot/intents_handler.py'
alias edit_whatsapp='sudo nano /home/pablollh/app/chatbot/integrations/whatsapp.py'
alias edit_telegram='sudo nano /home/pablollh/app/chatbot/integrations/telegram.py'
alias edit_messenger='sudo nano /home/pablollh/app/chatbot/integrations/messenger.py'
alias edit_instagram='sudo nano /home/pablollh/app/chatbot/integrations/instagram.py'
alias edit_services='sudo nano /home/pablollh/app/chatbot/integrations/services.py'
alias edit_common='sudo nano /home/pablollh/app/chatbot/workflow/common.py'
alias edit_amigro='sudo nano /home/pablollh/app/chatbot/workflow/amigro.py'
alias edit_executive='sudo nano /home/pablollh/app/chatbot/workflow/executive.py'
alias edit_huntred='sudo nano /home/pablollh/app/chatbot/workflow/huntred.py'
alias edit_huntu='sudo nano /home/pablollh/app/chatbot/workflow/huntu.py'

# === Alias para edición de views ===
alias edit_views='sudo nano /home/pablollh/app/views.py'
alias edit_candidatos_views='sudo nano /home/pablollh/app/views/candidatos_views.py'
alias edit_vacantes_views='sudo nano /home/pablollh/app/views/vacantes_views.py'
alias edit_clientes_views='sudo nano /home/pablollh/app/views/clientes_views.py'
alias edit_chatbot_views='sudo nano /home/pablollh/app/views/chatbot_views.py'
alias edit_utilidades_views='sudo nano /home/pablollh/app/views/utilidades_views.py'
alias edit_integraciones_views='sudo nano /home/pablollh/app/views/integraciones_views.py'
alias edit_auth_views='sudo nano /home/pablollh/app/views/auth_views.py'

alias edit_forms='sudo nano /home/pablollh/app/forms.py'
alias edit_serializers='sudo nano /home/pablollh/app/serializers.py'
alias edit_permissions='sudo nano /home/pablollh/app/permissions.py'
alias edit_middlewares='sudo nano /home/pablollh/app/middleware.py'

# === Alias para logs y procesos en segundo plano ===
alias logs_celery='sudo journalctl -u celery -f'
alias logs_gunicorn='sudo journalctl -u gunicorn -f'
alias logs_nginx='sudo journalctl -u nginx -f'
alias logs_all='sudo tail -f /home/pablollh/logs/*.log'

# === Alias generales ===
alias reload_aliases='source ~/.bashrc'
alias rserver='sudo systemctl restart gunicorn nginx'
alias check_logs='tail -f /home/pablollh/logs/*.log'
alias clear_logs='sudo rm -rf /home/pablollh/logs/*.log && touch /home/pablollh/logs/empty.log'
alias edit_env='sudo nano /home/pablollh/.env'
alias edit_alias='nano ~/.bashrc'

# === Alias para gestión del sistema ===
alias migrate='python /home/pablollh/manage.py migrate'
alias makemigrations='python /home/pablollh/manage.py makemigrations'
alias collectstatic='python /home/pablollh/manage.py collectstatic --noinput'
alias shell='python /home/pablollh/manage.py shell'
alias monitor_django='python /home/pablollh/manage.py runprofileserver'
alias inspect_model='python /home/pablollh/manage.py inspectdb'
alias restart_celery='sudo systemctl restart celery'
alias restart_gunicorn='sudo systemctl restart gunicorn'
alias restart_nginx='sudo systemctl restart nginx'
alias smart_reload='cd /home/pablollh && python manage.py check && (systemctl is-active --quiet celery && sudo systemctl restart celery) && (systemctl is-active --quiet gunicorn && sudo systemctl restart gunicorn)'
alias restart_all='sudo systemctl restart gunicorn celery nginx'
alias up_git='sudo truncate -s 0 /home/pablollh/logs/*.log && sudo truncate -s 0 /var/log/nginx/access.log && sudo truncate -s 0 /var/log/nginx/error.log && sudo truncate -s 0 /var/log/syslog && sudo truncate -s 0 /var/log/auth.log && sudo truncate -s 0 /var/log/dmesg && sudo truncate -s 0 /var/log/kern.log && sudo logrotate -f /etc/logrotate.conf && sudo journalctl --vacuum-time=1s && sudo journalctl --vacuum-size=50M && sleep 5'
alias up2_git='cd /home/pablollh && source venv/bin/activate && git fetch origin && git reset --hard origin/main && git clean -fd && git status && git log -1 && sleep 10 && sudo systemctl restart gunicorn nginx && python manage.py makemigrations && python manage.py migrate'
alias zombie='sudo kill -9 \$(ps -ef | grep \"systemctl.*less\" | awk \"{print \$2,\$3}\" | tr \" \" \"\n\" | sort -u) && sudo find /var/log -type f -size +10M'
alias rmem='sudo sysctl vm.drop_caches=3 && sudo rm -rf /tmp/* && sudo journalctl --vacuum-time=10m && sleep 40 && swapon --show && sudo swapon -a'
EOF"

# Asegurar permisos correctos para .bashrc
chown "$APP_USER:$APP_USER" "/home/$APP_USER/.bashrc"
chmod 644 "/home/$APP_USER/.bashrc"

# Cargar los alias en la sesión actual
su - "$APP_USER" -c "source /home/$APP_USER/.bashrc"

echo "Alias y entorno configurados para el usuario $APP_USER."

echo "==========================================================="
echo "DEPLOY FINALIZADO."
echo "==========================================================="
echo "Verifica con:"
echo "  systemctl status gunicorn"
echo "  systemctl status celery"
echo "  systemctl status nginx"
echo "  systemctl status redis-server"
echo "  systemctl status postgresql"
echo "  curl -I https://$DOMAIN"
echo
echo "Admin: https://$DOMAIN/admin/ (usuario: admin, contraseña: admin123)"
echo "Chatbot: Prueba enviando un mensaje al webhook (verifica configuración de WhatsApp)."
echo "Silk: https://$DOMAIN/silk/ (usa el mismo usuario admin)"
echo
echo "Si Certbot no configuró HTTPS, ejecuta manualmente: certbot --nginx -d $DOMAIN"
echo "Asegúrate de que $DOMAIN resuelve a 34.57.227.244 en tu DNS."
echo "==========================================================="