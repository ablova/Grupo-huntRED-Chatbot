#!/bin/bash
############################################################################################
# Nombre: setup_server.sh
# Ubicación: /home/pablo/setup_server.sh
# Descripción:
#   Despliega una aplicación Django en una VM Ubuntu 24.04 LTS limpia:
#   - Crea grupo 'ai_huntred' y usuario 'pablo' con acceso SSH para 'pablo' y 'pablollh'.
#   - Instala Git, Git LFS, Django, Gunicorn, PostgreSQL, Redis, Nginx, Celery, Certbot.
#   - Configura SSH con openssh-server y asegura sshd_config.
#   - Purga y reinstala PostgreSQL/Redis; crea DB con schema permissions.
#   - Clona Grupo-huntRED-Chatbot en /home/pablo con autenticación.
#   - Instala requirements con tensorflow-cpu, caches spaCy model es_core_news_md==3.8.0.
#   - Configura Gunicorn (file-based logs, 50 lines), Nginx, Celery, superuser.
#   - Configura HTTPS para ai.huntred.com con Certbot (postponed until 2025-04-18).
#   - Añade alias optimizados y configura CPU/memory (swap, log rotation).
#   - Usa /home/pablo/setup_status.conf para rastrear pasos completados (PART_X_RUN).
#
# Uso:
#   1) Subir: scp setup_server.sh pablo@34.57.227.244:/home/pablo/
#   2) Permisos: sudo chmod +x /home/pablo/setup_server.sh
#   3) Ejecutar: sudo /home/pablo/setup_server.sh
#   4) Forzar paso: Edita /home/pablo/setup_status.conf (e.g., PART_7_RUN=enabled)
#
# Antes, elimina y recrea la VM (si necesario):
# gcloud compute instances delete grupo-huntred --project=grupo-huntred --zone=us-central1-a --quiet
# gcloud compute instances create grupo-huntred \
#    --project=grupo-huntred \
#    --zone=us-central1-a \
#    --machine-type=e2-standard-4 \
#    --network-interface=address=34.57.227.244,network-tier=PREMIUM \
#    --image-family=ubuntu-2404-lts-amd64 \
#    --image-project=ubuntu-os-cloud \
#    --boot-disk-size=30GB \
#    --boot-disk-type=pd-ssd \
#    --tags=http-server,https-server,ssh-server,allow-ssh,default-allow-health-check \
#    --service-account=472786450192-compute@developer.gserviceaccount.com \
#    --shielded-secure-boot \
#    --labels=entorno=produccion,proyecto=inteligencia-artificial-grupo-huntred \
#    --metadata=startup-script='#!/bin/bash
#        apt-get update
#        apt-get install -y python3 python3-pip python3-venv git openssh-server
#        systemctl enable ssh
#        systemctl start ssh
#        useradd -m -s /bin/bash pablo
#        usermod -aG sudo pablo
#        echo "pablo ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/pablo
#        mkdir -p /home/pablo/.ssh /home/pablo/app /var/log/gunicorn
#        chown -R pablo:pablo /home/pablo /var/log/gunicorn
#        chmod 700 /home/pablo/.ssh
#    '
#
# Notas:
#   - Configurado para usuario 'pablo' y grupo 'ai_huntred', accesible por 'pablollh'.
#   - DB_USER='g_huntred_pablo' no se cambia.
#   - Gunicorn logs en /var/log/gunicorn/{access,error}.log, limitado a 50 líneas.
#   - Requiere ai.huntred.com resuelva a 34.57.227.244.
#   - Usa setup_status.conf para omitir pasos completados (PART_X_RUN=disabled).
############################################################################################

set -euo pipefail

################################
##        CONFIGURACIONES     ##
################################

MAIN_GROUP="ai_huntred"
APP_USER="pablo"
SECONDARY_USER="pablollh"
PROJECT_DIR="/home/pablo"
APP_NAME="ai_huntred"
REPO_URL="https://ablova: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@github.com/ablova/Grupo-huntRED-Chatbot.git"
TEMP_CLONE_DIR="/tmp/repo_clone"
DOMAIN="ai.huntred.com"
EMAIL="hola@huntred.com"
SECRET_KEY="hfmrpTNRwmQ1F7gZI1DNKaQ9gNw3cgayKFB0HK_gt9BKJEnLy60v1v0PnkZtX3OkY48"
GUNICORN_SOCKET="$PROJECT_DIR/gunicorn.sock"
GUNICORN_SERVICE="/etc/systemd/system/gunicorn.service"
NGINX_SITE="/etc/nginx/sites-available/$APP_NAME"
NGINX_LINK="/etc/nginx/sites-enabled/$APP_NAME"
DB_NAME="g_huntred_ai_db"
DB_USER="g_huntred_pablo"
DB_PASSWORD="Natalia&Patricio1113!"
DB_HOST="localhost"
DB_PORT="5432"
DB_CONN_MAX_AGE=60
DB_CONNECT_TIMEOUT=10
PY_VERSION="python3"
VENV_DIR="$PROJECT_DIR/venv"
CELERY_SERVICE="/etc/systemd/system/celery.service"
SWAP_SIZE="8G"
LOG_DIR="$PROJECT_DIR/logs"
STATIC_DIR="$PROJECT_DIR/staticfiles"
MEDIA_DIR="$PROJECT_DIR/media"
TFHUB_CACHE="$PROJECT_DIR/tfhub_cache"
SKILLS_DATA="$PROJECT_DIR/skills_data"
GUNICORN_LOG_DIR="/var/log/gunicorn"
GUNICORN_ACCESS_LOG="$GUNICORN_LOG_DIR/access.log"
GUNICORN_ERROR_LOG="$GUNICORN_LOG_DIR/error.log"
STATUS_FILE="$PROJECT_DIR/setup_status.conf"

# Crear grupo ai_huntred si no existe
if ! getent group "$MAIN_GROUP" >/dev/null; then
    groupadd "$MAIN_GROUP"
    echo "Grupo $MAIN_GROUP creado."
else
    echo "Grupo $MAIN_GROUP ya existe."
fi

# Asegurar que pablo y pablollh estén en el grupo ai_huntred
for user in "$APP_USER" "$SECONDARY_USER"; do
    if id "$user" >/dev/null 2>&1 && ! groups "$user" | grep -q "$MAIN_GROUP"; then
        usermod -aG "$MAIN_GROUP" "$user"
        echo "$user añadido a $MAIN_GROUP."
    fi
done

# Validar y crear directorios esenciales
ESSENTIAL_DIRS=("$LOG_DIR" "$STATIC_DIR" "$MEDIA_DIR" "$TFHUB_CACHE" "$SKILLS_DATA" "$GUNICORN_LOG_DIR")
for dir in "${ESSENTIAL_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        chown "$APP_USER:$MAIN_GROUP" "$dir"
        chmod 775 "$dir"
        echo "Directorio $dir creado con permisos correctos."
    else
        chown "$APP_USER:$MAIN_GROUP" "$dir"
        chmod 775 "$dir"
        echo "Permisos de $dir validados y ajustados."
    fi
done

# Initialize status file
if [ ! -f "$STATUS_FILE" ]; then
    cat > "$STATUS_FILE" <<EOF
PART_1_RUN=enabled
PART_2_RUN=enabled
PART_3_RUN=enabled
PART_4_RUN=enabled
PART_5_RUN=enabled
PART_6_RUN=enabled
PART_7_RUN=enabled
PART_8_RUN=enabled
PART_9_RUN=enabled
PART_10_RUN=enabled
PART_11_RUN=enabled
PART_12_RUN=enabled
EOF
    chown "$APP_USER:$MAIN_GROUP" "$STATUS_FILE"
    chmod 664 "$STATUS_FILE"
    echo "Status file $STATUS_FILE creado."
else
    echo "Status file $STATUS_FILE ya existe."
fi

# Source status file
if [ -f "$STATUS_FILE" ]; then
    source "$STATUS_FILE"
    echo "Status file $STATUS_FILE cargado."
else
    echo "Error: Status file $STATUS_FILE no encontrado."
    exit 1
fi

################################
echo "==========================================================="
echo " [1/12] ACTUALIZANDO Y PREPARANDO LA VM "
echo "==========================================================="
sleep 2

if [ "${PART_1_RUN:-enabled}" != "disabled" ]; then
    apt-get update -y
    apt-get upgrade -y
    apt-get autoremove -y
    apt-get install -y software-properties-common curl git git-lfs htop ncdu fail2ban logrotate \
        build-essential python3-dev python3-pip python3-venv libpq-dev \
        libblas-dev liblapack-dev gfortran libjpeg-dev zlib1g-dev libffi-dev libssl-dev \
        libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0
    add-apt-repository ppa:git-core/ppa -y
    apt-get update -y
    apt-get install -y git git-lfs
    git lfs install
    echo "Paquetes instalados."

    # Configure logrotate globally
    cat > /etc/logrotate.d/ai_huntred <<EOF
$LOG_DIR/*.log $GUNICORN_LOG_DIR/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 664 $APP_USER $MAIN_GROUP
    sharedscripts
    postrotate
        systemctl restart gunicorn > /dev/null 2>&1 || true
    endscript
}
/var/log/nginx/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    sharedscripts
    postrotate
        systemctl restart nginx > /dev/null 2>&1 || true
    endscript
}
EOF
    echo "Logrotate configurado para logs de aplicación y Nginx."

    echo "PART_1_RUN=disabled" >> "$STATUS_FILE"
    echo "Paso [1/12] completado."
else
    echo "Paso [1/12] ya completado, omitiendo."
fi

################################
echo "==========================================================="
echo " [2/12] CONFIGURANDO SSH Y FIREWALL "
echo "==========================================================="
sleep 2

if [ "${PART_2_RUN:-enabled}" != "disabled" ]; then
    apt-get install -y openssh-server ufw
    systemctl enable ssh
    systemctl start ssh
    echo "OpenSSH instalado y configurado."

    # Configure SSH
    if [ ! -f "/etc/ssh/sshd_config.d/ai_huntred.conf" ]; then
        cat > /etc/ssh/sshd_config.d/ai_huntred.conf <<EOF
Port 22
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PasswordAuthentication no
PermitRootLogin no
MaxAuthTries 3
AllowUsers $APP_USER $SECONDARY_USER
EOF
        systemctl restart ssh
        echo "sshd_config configurado."
    else
        echo "sshd_config ya configurado."
    fi

    # Configure UFW
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    echo "UFW configurado para SSH, HTTP, HTTPS."

    for user in "$APP_USER" "$SECONDARY_USER"; do
        if [ ! -d "/home/$user/.ssh" ]; then
            mkdir -p "/home/$user/.ssh"
            chown "$user:$MAIN_GROUP" "/home/$user/.ssh"
            chmod 700 "/home/$user/.ssh"
            echo "Directorio SSH para $user creado."
        else
            echo "Directorio SSH para $user ya existe."
        fi
    done

    echo "PART_2_RUN=disabled" >> "$STATUS_FILE"
    echo "Paso [2/12] completado."
else
    echo "Paso [2/12] ya completado, omitiendo."
fi

################################
echo "==========================================================="
echo " [3/12] CREANDO USUARIOS Y GRUPOS "
echo "==========================================================="
sleep 2

if [ "${PART_3_RUN:-enabled}" != "disabled" ]; then
    if ! id "$APP_USER" >/dev/null 2>&1; then
        useradd -m -s /bin/bash -g "$MAIN_GROUP" "$APP_USER"
        echo "Usuario $APP_USER creado."
    else
        echo "Usuario $APP_USER ya existe."
    fi

    if id "$SECONDARY_USER" >/dev/null 2>&1 && ! groups "$SECONDARY_USER" | grep -q "$MAIN_GROUP"; then
        usermod -aG "$MAIN_GROUP" "$SECONDARY_USER"
        echo "$SECONDARY_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$SECONDARY_USER
        chmod 440 /etc/sudoers.d/$SECONDARY_USER
        echo "Usuario $SECONDARY_USER añadido a $MAIN_GROUP y sudoers."
    else
        echo "Usuario $SECONDARY_USER ya en $MAIN_GROUP o no existe."
    fi

    if ! groups www-data | grep -q "$MAIN_GROUP"; then
        usermod -aG "$MAIN_GROUP" www-data
        echo "www-data añadido a $MAIN_GROUP."
    else
        echo "www-data ya en $MAIN_GROUP."
    fi

    if [ ! -f "/etc/sudoers.d/$APP_USER" ]; then
        echo "$APP_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$APP_USER
        chmod 440 /etc/sudoers.d/$APP_USER
        echo "Sudoers configurado para $APP_USER."
    else
        echo "Sudoers ya configurado para $APP_USER."
    fi

    echo "PART_3_RUN=disabled" >> "$STATUS_FILE"
    echo "Paso [3/12] completado."
else
    echo "Paso [3/12] ya completado, omitiendo."
fi

################################
echo "==========================================================="
echo " [4/12] CONFIGURANDO SWAP "
echo "==========================================================="
sleep 2

if [ "${PART_4_RUN:-enabled}" != "disabled" ]; then
    if [ ! -f /swapfile ]; then
        fallocate -l "$SWAP_SIZE" /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
        sysctl vm.swappiness=10
        echo 'vm.swappiness=10' >> /etc/sysctl.conf
        echo "Swap file creado y swappiness configurado."
    else
        echo "Swap file ya existe."
    fi

    echo "PART_4_RUN=disabled" >> "$STATUS_FILE"
    echo "Paso [4/12] completado."
else
    echo "Paso [4/12] ya completado, omitiendo."
fi

################################
echo "==========================================================="
echo " [5/12] INSTALANDO POSTGRESQL, REDIS, NGINX, CERTBOT "
echo "==========================================================="
sleep 2

if [ "${PART_5_RUN:-enabled}" != "disabled" ]; then
    apt-get install -y postgresql postgresql-contrib redis-server nginx certbot python3-certbot-nginx
    echo "Paquetes PostgreSQL, Redis, Nginx, Certbot instalados."

    echo "PART_5_RUN=disabled" >> "$STATUS_FILE"
    echo "Paso [5/12] completado."
else
    echo "Paso [5/12] ya completado, omitiendo."
fi

################################
echo "==========================================================="
echo " [6/12] CONFIGURANDO POSTGRESQL Y REDIS "
echo "==========================================================="
sleep 2

if [ "${PART_6_RUN:-enabled}" != "disabled" ]; then
    systemctl enable postgresql
    systemctl start postgresql
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME" || true
    sudo -u postgres psql -c "DROP ROLE IF EXISTS $DB_USER" || true
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME"
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD'"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER"
    sudo -u postgres psql -d $DB_NAME -c "GRANT ALL ON SCHEMA public TO $DB_USER"
    sudo -u postgres psql -d $DB_NAME -c "ALTER SCHEMA public OWNER TO $DB_USER"
    sudo -u postgres psql -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER"
    sudo -u postgres psql -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER"
    echo "Base de datos $DB_NAME configurada."

    # Configure Redis with memory limits and systemd supervision
    sed -i 's/^supervised .*/supervised systemd/' /etc/redis/redis.conf
    sed -i 's/^daemonize .*/daemonize no/' /etc/redis/redis.conf
    echo "maxmemory 512mb" >> /etc/redis/redis.conf
    echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf
    systemctl enable redis-server
    systemctl restart redis-server
    echo "Redis configurado."

    echo "PART_6_RUN=disabled" >> "$STATUS_FILE"
    echo "Paso [6/12] completado."
else
    echo "Paso [6/12] ya completado, omitiendo."
fi

################################
echo "==========================================================="
echo " [7/12] CLONANDO REPOSITORIO "
echo "==========================================================="
sleep 2

if [ "${PART_7_RUN:-enabled}" != "disabled" ]; then
    if [ ! -d "$PROJECT_DIR/.git" ]; then
        mkdir -p "$PROJECT_DIR"
        chown "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR"
        chmod 775 "$PROJECT_DIR"

        if [ -f "$PROJECT_DIR/setup_server.sh" ]; then
            mv "$PROJECT_DIR/setup_server.sh" /tmp/setup_server.sh
        fi

        su - "$APP_USER" -c "git clone $REPO_URL $TEMP_CLONE_DIR && cd $TEMP_CLONE_DIR && git lfs install && git lfs pull"
        mv "$TEMP_CLONE_DIR"/* "$TEMP_CLONE_DIR"/.* "$PROJECT_DIR/" 2>/dev/null || true
        rm -rf "$TEMP_CLONE_DIR"

        if [ -f "/tmp/setup_server.sh" ]; then
            mv /tmp/setup_server.sh "$PROJECT_DIR/setup_server.sh"
            chown "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR/setup_server.sh"
            chmod 775 "$PROJECT_DIR/setup_server.sh"
        fi

        chown -R "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR"
        chmod -R 775 "$PROJECT_DIR"
        find "$PROJECT_DIR" -type f -exec chmod 664 {} \;
        echo "Repositorio clonado y permisos ajustados."
    else
        echo "Repositorio ya existe, verificando actualizaciones..."
        su - "$APP_USER" -c "cd $PROJECT_DIR && git fetch"
        if su - "$APP_USER" -c "cd $PROJECT_DIR && git status" | grep -q "Your branch is behind"; then
            su - "$APP_USER" -c "cd $PROJECT_DIR && git reset --hard origin/main && git pull && git lfs pull"
            echo "Repositorio actualizado."
        else
            echo "Repositorio ya está actualizado."
        fi
    fi

    SKILL_JSON="/home/pablo/skills_data/skill_db_relax_20.json"
    SKILL_URL="https://raw.githubusercontent.com/AnasAito/SkillNER/master/buckets/skills_processed.json"
    if [ ! -f "$SKILL_JSON" ] || [ "$(find "$SKILL_JSON" -mtime +1 2>/dev/null)" ]; then
        mkdir -p /home/pablo/skills_data
        wget "$SKILL_URL" -O "$SKILL_JSON"
        chown "$APP_USER:$MAIN_GROUP" "$SKILL_JSON"
        chmod 664 "$SKILL_JSON"
        echo "Archivo $SKILL_JSON actualizado desde SkillNER."
    else
        echo "Archivo $SKILL_JSON ya existe y está actualizado."
    fi

    ESCO_JSON="/home/pablo/skills_data/ESCO_occup_skills.json"
    ESCO_URL="https://raw.githubusercontent.com/source/ESCO_occup_skills.json" # Replace with actual URL
    if [ ! -f "$ESCO_JSON" ] || [ "$(find "$ESCO_JSON" -mtime +1 2>/dev/null)" ]; then
        wget "$ESCO_URL" -O "$ESCO_JSON" || echo "Advertencia: No se pudo descargar ESCO_occup_skills.json"
        chown "$APP_USER:$MAIN_GROUP" "$ESCO_JSON"
        chmod 664 "$ESCO_JSON"
        echo "Archivo $ESCO_JSON actualizado."
    else
        echo "Archivo $ESCO_JSON ya existe y está actualizado."
    fi

    echo "PART_7_RUN=disabled" >> "$STATUS_FILE"
    echo "Paso [7/12] completado."
else
    echo "Paso [7/12] ya completado, omitiendo."
fi

################################
echo "==========================================================="
echo " [8/12] CREANDO ENTORNO VIRTUAL "
echo "==========================================================="
sleep 2

if [ "${PART_8_RUN:-enabled}" != "disabled" ]; then
    if [ ! -d "$VENV_DIR" ]; then
        su - "$APP_USER" -c "$PY_VERSION -m venv $VENV_DIR"
        echo "Entorno virtual creado."
    else
        echo "Entorno virtual ya existe."
    fi

    chown -R "$APP_USER:$MAIN_GROUP" "$VENV_DIR"
    chmod -R 775 "$VENV_DIR"

    su - "$APP_USER" -c "source $VENV_DIR/bin/activate && \
        pip install --upgrade pip && \
        pip install wheel django gunicorn psycopg2-binary redis celery django-celery-beat django-celery-results sentry-sdk spacy==3.8.0 tensorflow-cpu==2.19.0 tf-keras tensorflow-text && \
        python -m spacy download es_core_news_md==3.8.0 && \
        cd $PROJECT_DIR && [ -f requirements.txt ] && pip install -r requirements.txt --no-deps"
    echo "Dependencias instaladas."

    # Set TF_CPP_MIN_LOG_LEVEL in virtualenv
    echo "export TF_CPP_MIN_LOG_LEVEL=2" >> "$VENV_DIR/bin/activate"
    echo "export CUDA_VISIBLE_DEVICES=" >> "$VENV_DIR/bin/activate"
    echo "TensorFlow environment variables configurados."

    echo "PART_8_RUN=disabled" >> "$STATUS_FILE"
    echo "Paso [8/12] completado."
else
    echo "Paso [8/12] ya completado, omitiendo."
fi

################################
echo "==========================================================="
echo " [9/12] CONFIGURANDO GUNICORN Y CELERY "
echo "==========================================================="
sleep 2

if [ "${PART_9_RUN:-enabled}" != "disabled" ]; then
    if [ ! -f "/home/$APP_USER/run_gunicorn.sh" ]; then
        cat > /home/$APP_USER/run_gunicorn.sh <<EOF
#!/bin/bash
source $VENV_DIR/bin/activate
exec gunicorn --workers 1 --bind unix:$GUNICORN_SOCKET --timeout 120 \
    --log-level debug \
    --access-logfile $GUNICORN_ACCESS_LOG \
    --error-logfile $GUNICORN_ERROR_LOG \
    $APP_NAME.wsgi:application
EOF
        chmod +x /home/$APP_USER/run_gunicorn.sh
        chown $APP_USER:$MAIN_GROUP /home/$APP_USER/run_gunicorn.sh
        echo "Script wrapper para Gunicorn creado."
    else
        echo "Script wrapper para Gunicorn ya existe."
    fi

    if [ ! -f "/home/$APP_USER/run_celery.sh" ]; then
        cat > /home/$APP_USER/run_celery.sh <<EOF
#!/bin/bash
source $VENV_DIR/bin/activate
exec celery -A $APP_NAME worker --loglevel=info --concurrency=2
EOF
        chmod +x /home/$APP_USER/run_celery.sh
        chown $APP_USER:$MAIN_GROUP /home/$APP_USER/run_celery.sh
        echo "Script wrapper para Celery creado."
    else
        echo "Script wrapper para Celery ya existe."
    fi

    if [ ! -f "$GUNICORN_SERVICE" ]; then
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
Environment="TF_CPP_MIN_LOG_LEVEL=2"
Environment="CUDA_VISIBLE_DEVICES="
ExecStart=/home/$APP_USER/run_gunicorn.sh
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
EOF
        echo "Servicio Gunicorn creado."
    else
        echo "Servicio Gunicorn ya existe."
    fi

    if [ ! -f "$CELERY_SERVICE" ]; then
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
Environment="CUDA_VISIBLE_DEVICES="
ExecStart=/home/$APP_USER/run_celery.sh
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
EOF
        echo "Servicio Celery creado."
    else
        echo "Servicio Celery ya existe."
    fi

    if [ ! -f "/home/$APP_USER/truncate_logs.sh" ]; then
        cat > /home/$APP_USER/truncate_logs.sh <<EOF
#!/bin/bash
tail -n 50 $GUNICORN_ACCESS_LOG > /tmp/gunicorn_access_temp.log && mv /tmp/gunicorn_access_temp.log $GUNICORN_ACCESS_LOG
tail -n 50 $GUNICORN_ERROR_LOG > /tmp/gunicorn_error_temp.log && mv /tmp/gunicorn_error_temp.log $GUNICORN_ERROR_LOG
EOF
        chmod +x /home/$APP_USER/truncate_logs.sh
        chown $APP_USER:$MAIN_GROUP /home/$APP_USER/truncate_logs.sh
        (crontab -l 2>/dev/null; echo "0 * * * * /home/$APP_USER/truncate_logs.sh") | crontab -
        echo "Script de truncado de logs creado."
    else
        echo "Script de truncado de logs ya existe."
    fi

    # Ensure log files exist with correct permissions
    touch "$GUNICORN_ACCESS_LOG" "$GUNICORN_ERROR_LOG"
    chown "$APP_USER:$MAIN_GROUP" "$GUNICORN_ACCESS_LOG" "$GUNICORN_ERROR_LOG"
    chmod 664 "$GUNICORN_ACCESS_LOG" "$GUNICORN_ERROR_LOG"
    echo "Archivos de log de Gunicorn creados con permisos correctos."

    systemctl daemon-reload
    systemctl enable gunicorn celery
    for service in gunicorn celery; do
        if ! systemctl is-active --quiet "$service"; then
            systemctl restart "$service"
            sleep 2
            if ! systemctl is-active --quiet "$service"; then
                echo "Error: El servicio $service no se pudo iniciar. Revisa los logs."
                journalctl -u "$service" -n 50
                exit 1
            fi
            echo "Servicio $service reiniciado con éxito."
        else
            echo "Servicio $service ya está corriendo."
        fi
    done

    echo "PART_9_RUN=disabled" >> "$STATUS_FILE"
    echo "Paso [9/12] completado."
else
    echo "Paso [9/12] ya completado, omitiendo."
fi

################################
echo "==========================================================="
echo " [10/12] CONFIGURANDO NGINX AND CERTBOT "
echo "==========================================================="
sleep 2

if [ "${PART_10_RUN:-enabled}" != "disabled" ]; then
    rm -f "$NGINX_LINK" /etc/nginx/sites-enabled/default
    echo "Configuraciones previas de Nginx eliminadas."

    cat > "$NGINX_SITE" <<EOF
upstream app_server {
    server unix:$GUNICORN_SOCKET fail_timeout=0;
}

server {
    listen 80;
    server_name $DOMAIN 127.0.0.1 localhost 34.57.227.244;

    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    location /static/ {
        alias $STATIC_DIR/;
        expires 30d;
        access_log off;
    }

    location /media/ {
        alias $MEDIA_DIR/;
        expires 30d;
        access_log off;
    }

    location / {
        proxy_pass http://app_server;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    client_max_body_size 10M;
}
EOF
    ln -sf "$NGINX_SITE" "$NGINX_LINK"
    nginx -t && systemctl restart nginx || {
        echo "Error: Nginx configuration test failed. Check /var/log/nginx/error.log"
        cat /var/log/nginx/error.log
        exit 1
    }
    echo "Configuración HTTP de Nginx creada."

    # Certbot configuration with rate limit check
    if certbot certificates | grep -q "$DOMAIN"; then
        echo "Certificado SSL ya existe para $DOMAIN."
    else
        echo "Advertencia: Certbot no se ejecutará debido a límites de Let's Encrypt."
        echo "Ejecuta después de 2025-04-18 01:19:06 UTC:"
        echo "sudo certbot --nginx -d $DOMAIN -m $EMAIL --agree-tos --non-interactive"
    fi

    echo "PART_10_RUN=disabled" >> "$STATUS_FILE"
    echo "Paso [10/12] completado."
else
    echo "Paso [10/12] ya completado, omitiendo."
fi

################################
echo "==========================================================="
echo " [11/12] MIGRACIONES DJANGO Y CONFIGURACIÓN "
echo "==========================================================="
sleep 2

if [ "${PART_11_RUN:-enabled}" != "disabled" ]; then
    if [ -f "$PROJECT_DIR/.env" ]; then
        chown "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR/.env"
        chmod 660 "$PROJECT_DIR/.env"
        echo "Permisos de .env validados y ajustados."
    else
        su - "$APP_USER" -c "cat > $PROJECT_DIR/.env <<EOF
DJANGO_SECRET_KEY=$SECRET_KEY
DJANGO_DEBUG=False
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
DEFAULT_FROM_EMAIL=Grupo huntRED® <hola@huntred.com>
SENTRY_DSN=https://e9989a45cedbcefa64566dbcfb2ffd59@o4508638041145344.ingest.us.sentry.io/4508638043766784
SENTRY_SAMPLE_RATE=1.0
SENTRY_SEND_PII=True
SENTRY_DEBUG=False
LANGUAGE_CODE=es-mx
TIMEZONE=America/Mexico_City
STATIC_URL=/static/
STATIC_ROOT=$STATIC_DIR
MEDIA_URL=/media/
MEDIA_ROOT=$MEDIA_DIR
THROTTLE_ANON=100/day
THROTTLE_USER=1000/day
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOW_CREDENTIALS=False
CORS_ALLOWED_ORIGINS=https://$DOMAIN
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
GIT_USER=ablova@gmail.com
GIT_PASSWORD=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
TF_CPP_MIN_LOG_LEVEL=2
CUDA_VISIBLE_DEVICES=
TFHUB_CACHE_DIR=$TFHUB_CACHE
EOF"
        chown "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR/.env"
        chmod 660 "$PROJECT_DIR/.env"
        echo ".env creado con permisos correctos."
    fi

    if [ ! -f "/home/$APP_USER/.git-credentials" ]; then
        su - "$APP_USER" -c "
            git config --global credential.helper store
            echo 'https://ablova@gmail.com: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@github.com' > ~/.git-credentials
            chmod 600 ~/.git-credentials
            git config --global user.email 'ablova@gmail.com'
            git config --global user.name 'ablova'
        "
        echo "Credenciales de Git configuradas."
    else
        echo "Credenciales de Git ya configuradas."
    fi

    export CUDA_VISIBLE_DEVICES=""
    export SKIP_NLP_INIT=1
    echo "Ejecutando makemigrations..."
    time su - "$APP_USER" -c "source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py makemigrations --noinput"
    echo "makemigrations completado."

    echo "Ejecutando migrate..."
    time su - "$APP_USER" -c "source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py migrate --noinput"
    echo "migrate completado."

    unset SKIP_NLP_INIT
    echo "Ejecutando collectstatic..."
    time su - "$APP_USER" -c "source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py collectstatic --noinput"
    echo "collectstatic completado."

    echo "Ejecutando loaddata..."
    if [ -f "$PROJECT_DIR/app/fixtures/initial_data.json" ]; then
        time su - "$APP_USER" -c "source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py loaddata /home/pablo/app/fixtures/initial_data.json"
        echo "loaddata completado."
    else
        echo "Advertencia: initial_data.json no encontrado, omitiendo loaddata."
    fi

    echo "Creando superusuario..."
    time su - "$APP_USER" -c "source $VENV_DIR/bin/activate && cd $PROJECT_DIR && \
        echo 'from django.contrib.auth.models import User; \
        if not User.objects.filter(username=\"PabloLLH\").exists(): \
            User.objects.create_superuser(\"PabloLLH\", \"pablo@huntred.com\", \"Natalia&Patricio1113!\")' | python manage.py shell"
    echo "Superusuario creado."

    chown -R "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR"
    chmod -R 775 "$PROJECT_DIR"
    find "$PROJECT_DIR" -type f -exec chmod 664 {} \;
    chmod 660 "$PROJECT_DIR/.env"

    for service in gunicorn celery nginx; do
        if ! systemctl is-active --quiet "$service"; then
            systemctl restart "$service"
            sleep 2
            if ! systemctl is-active --quiet "$service"; then
                echo "Error: El servicio $service no se pudo iniciar. Revisa los logs."
                journalctl -u "$service" -n 50
                exit 1
            fi
            echo "Servicio $service reiniciado con éxito."
        else
            echo "Servicio $service ya está corriendo."
        fi
    done

    echo "PART_11_RUN=disabled" >> "$STATUS_FILE"
    echo "Paso [11/12] completado."
else
    echo "Paso [11/12] ya completado, omitiendo."
fi

################################
echo "==========================================================="
echo " [12/12] CONFIGURANDO ALIAS Y ENTORNO "
echo "==========================================================="
sleep 2

if [ "${PART_12_RUN:-enabled}" != "disabled" ]; then
    if ! grep -q "alias iniciar" "/home/$APP_USER/.bashrc"; then
        su - "$APP_USER" -c "cat >> /home/$APP_USER/.bashrc << 'EOF'
export LS_OPTIONS='--color=auto'
alias ls='ls \$LS_OPTIONS'
alias ll='ls -la \$LS_OPTIONS'
alias grep='grep --color=auto'
export PS1=\"\\[\033[1;32m\\]\u@\h:\\[\033[1;34m\\]\w\\[\033[1;36m\\]\$ \\[\033[0m\\]\"
alias iniciar='cd /home/pablo && source venv/bin/activate'
alias apt-todo='sudo apt-get update -y && sudo apt-get upgrade -y && sudo apt autoremove -y'
alias edit_settings='sudo nano /home/pablo/ai_huntred/settings.py'
alias edit_urls='sudo nano /home/pablo/ai_huntred/urls.py'
alias edit_celery='sudo nano /home/pablo/ai_huntred/celery_app.py'
alias edit_nlp='sudo nano /home/pablo/app/chatbot/nlp.py'
alias edit_utils='sudo nano /home/pablo/app/chatbot/utils.py'
alias edit_generate_embeddings='sudo nano /home/pablo/app/chatbot/generate_embeddings.py'
alias edit_config='sudo nano /home/pablo/app/chatbot/config.py'
alias logs_celery='sudo journalctl -u celery -f'
alias logs_gunicorn='tail -f $GUNICORN_ACCESS_LOG $GUNICORN_ERROR_LOG'
alias logs_nginx='sudo tail -f /var/log/nginx/error.log /var/log/nginx/access.log'
alias logs_nlp='tail -f $LOG_DIR/nlp.log'
alias logs_all='tail -f $LOG_DIR/*.log $GUNICORN_LOG_DIR/*.log'
alias reload_aliases='source ~/.bashrc'
alias rserver='sudo systemctl restart gunicorn nginx celery'
alias check_logs='tail -n 50 $LOG_DIR/*.log $GUNICORN_LOG_DIR/*.log'
alias clear_logs='sudo truncate -s 0 $LOG_DIR/*.log $GUNICORN_LOG_DIR/*.log && touch $GUNICORN_ACCESS_LOG $GUNICORN_ERROR_LOG'
alias edit_env='sudo nano /home/pablo/.env'
alias edit_nginx='sudo nano $NGINX_SITE'
alias migrate='source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py migrate'
alias makemigrations='source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py makemigrations'
alias collectstatic='source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py collectstatic --noinput'
alias shell='source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py shell'
alias restart_celery='sudo systemctl restart celery'
alias restart_gunicorn='sudo systemctl restart gunicorn'
alias restart_nginx='sudo systemctl restart nginx'
alias smart_reload='source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py check && sudo systemctl restart celery gunicorn nginx'
alias clear_cache='sudo find /home/pablo -name "*.pyc" -delete && sudo find /home/pablo -name "__pycache__" -type d -exec rm -r {} + && rm -rf /tmp/tfhub_modules/*'
alias test_nlp='source $VENV_DIR/bin/activate && export TF_CPP_MIN_LOG_LEVEL=2 && python -c "import os; os.environ[\"DJANGO_SETTINGS_MODULE\"] = \"ai_huntred.settings\"; import django; django.setup(); from app.chatbot.nlp import load_skills_catalog; catalog = load_skills_catalog(\"candidate\", \"deep\"); print(f\"Total skills: {sum(len(v) for v in catalog.values())}\")"'
alias run_embeddings='source $VENV_DIR/bin/activate && export TF_CPP_MIN_LOG_LEVEL=2 && python /home/pablo/app/chatbot/generate_embeddings.py'
alias check_services='systemctl status gunicorn celery nginx redis-server postgresql'
export TF_ENABLE_ONEDNN_OPTS=0
export TF_CPP_MIN_LOG_LEVEL=2
export CUDA_VISIBLE_DEVICES=""
EOF"
        chown "$APP_USER:$APP_USER" "/home/$APP_USER/.bashrc"
        chmod 644 "/home/$APP_USER/.bashrc"
        su - "$APP_USER" -c "source /home/$APP_USER/.bashrc"
        echo ".bashrc configurado con alias y variables de entorno."
    else
        echo ".bashrc ya configurado con alias."
    fi

    echo "PART_12_RUN=disabled" >> "$STATUS_FILE"
    echo "Paso [12/12] completado."
else
    echo "Paso [12/12] ya completado, omitiendo."
fi

echo "==========================================================="
echo "DEPLOY FINALIZADO."
echo "==========================================================="
echo "Verifica con:"
echo "  systemctl status gunicorn celery nginx redis-server postgresql"
echo "  curl -I http://$DOMAIN/admin/  # HTTP hasta que Certbot se ejecute"
echo "Admin: http://$DOMAIN/admin/ (usuario: PabloLLH, contraseña: Natalia&Patricio1113!)"
echo "Silk: http://$DOMAIN/silk/ (usa PabloLLH)"
echo "Si Certbot falló, ejecuta después de 2025-04-18 01:19:06 UTC: sudo certbot --nginx -d $DOMAIN"
echo "Asegúrate de que $DOMAIN resuelve a 34.57.227.244."
echo "Revisa /home/pablo/setup_status.conf para estado de pasos."
echo "Para forzar un paso, edita setup_status.conf (e.g., PART_7_RUN=enabled) y vuelve a ejecutar."
echo "Logs: tail -f $LOG_DIR/nlp.log $GUNICORN_LOG_DIR/{access,error}.log"
echo "Test NLP: source $VENV_DIR/bin/activate && python -c 'from app.chatbot.nlp import load_skills_catalog; catalog = load_skills_catalog(\"candidate\", \"deep\"); print(f\"Total skills: {sum(len(v) for v in catalog.values())}\")'"
echo "==========================================================="