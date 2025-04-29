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
#   2) Permisos: sudo nano /home/pablo/setup_server.sh && sudo chmod +x /home/pablo/setup_server.sh && sudo /home/pablo/setup_server.sh
#   3) Ejecutar: sudo /home/pablo/setup_server.sh
#   4) Forzar paso: Edita /home/pablo/setup_status.conf (e.g., PART_7_RUN=enabled)
#
# Antes, elimina y recrea la VM (si necesario):
# gcloud compute instances delete grupo-huntred --project=grupo-huntred --zone=us-central1-a --quiet 
# sleep 5
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
#  sleep 10
#  gcloud compute ssh grupo-huntred --zone=us-central1-a --project=grupo-huntred
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
APP_USER="pablollh"
SECONDARY_USER="pablo"
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
GUNICORN_ACCESS_LOG="$LOG_DIR/gunicorn_access.log"
GUNICORN_ERROR_LOG="$LOG_DIR/gunicorn_error.log"
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
ESSENTIAL_DIRS=("$LOG_DIR" "$STATIC_DIR" "$MEDIA_DIR" "$TFHUB_CACHE" "$SKILLS_DATA")
for dir in "${ESSENTIAL_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        chown "$APP_USER:$MAIN_GROUP" "$dir"
        chmod 770 "$dir"
        echo "Directorio $dir creado con permisos correctos."
    else
        chown "$APP_USER:$MAIN_GROUP" "$dir"
        chmod 770 "$dir"
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
    chmod 660 "$STATUS_FILE"
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
    apt update -y 
    apt upgrade -y  
    apt autoremove -y 
    apt-get clean -y 
    apt clean -y 
    apt-get install -y software-properties-common curl git git-lfs htop ncdu fail2ban logrotate \
        build-essential python3-dev python3-pip python3-venv libpq-dev \
        libblas-dev liblapack-dev gfortran libjpeg-dev zlib1g-dev libffi-dev libssl-dev \
        libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 graphviz
    add-apt-repository ppa:git-core/ppa -y
    apt-get update -y
    apt-get install -y git git-lfs
    git lfs install
    echo "Paquetes instalados."

    # Instalar python-dotenv y django-silk
    pip3 install python-dotenv django-silk || echo "Advertencia: No se pudo instalar python-dotenv o django-silk"

    # Configure logrotate globally
    cat > /etc/logrotate.d/ai_huntred <<EOF
$LOG_DIR/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 660 $APP_USER $MAIN_GROUP
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
    create 640 root root
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
        chmod 770 "$PROJECT_DIR"

        if [ -f "$PROJECT_DIR/setup_server.sh" ]; then
            mv "$PROJECT_DIR/setup_server.sh" /tmp/setup_server.sh
        fi

        su - "$APP_USER" -c "git clone $REPO_URL $TEMP_CLONE_DIR && cd $TEMP_CLONE_DIR && git lfs install && git lfs pull"
        mv "$TEMP_CLONE_DIR"/* "$TEMP_CLONE_DIR"/.* "$PROJECT_DIR/" 2>/dev/null || true
        rm -rf "$TEMP_CLONE_DIR"

        if [ -f "/tmp/setup_server.sh" ]; then
            mv /tmp/setup_server.sh "$PROJECT_DIR/setup_server.sh"
            chown "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR/setup_server.sh"
            chmod 770 "$PROJECT_DIR/setup_server.sh"
        fi

        # Ajustar permisos del proyecto
        chown -R "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR"
        chmod -R 770 "$PROJECT_DIR"
        find "$PROJECT_DIR" -type f -exec chmod 660 {} \;
        find "$PROJECT_DIR" -type f -name "*.sh" -exec chmod 770 {} \;
        find "$PROJECT_DIR" -type f -name "manage.py" -exec chmod 770 {} \;

        # Asegurar permisos de logs
        mkdir -p "$LOG_DIR"
        chown -R "$APP_USER:$MAIN_GROUP" "$LOG_DIR"
        chmod -R 770 "$LOG_DIR"
        find "$LOG_DIR" -type f -exec chmod 660 {} \;
        touch "$LOG_DIR/nlp.log" "$LOG_DIR/app.log" "$LOG_DIR/celery.log" "$LOG_DIR/chatbot.log" "$LOG_DIR/gunicorn_access.log" "$LOG_DIR/gunicorn_error.log"
        chown "$APP_USER:$MAIN_GROUP" "$LOG_DIR/nlp.log" "$LOG_DIR/app.log" "$LOG_DIR/celery.log" "$LOG_DIR/chatbot.log" "$LOG_DIR/gunicorn_access.log" "$LOG_DIR/gunicorn_error.log"
        chmod 660 "$LOG_DIR/nlp.log" "$LOG_DIR/app.log" "$LOG_DIR/celery.log" "$LOG_DIR/chatbot.log" "$LOG_DIR/gunicorn_access.log" "$LOG_DIR/gunicorn_error.log"

        # Asegurar permisos de staticfiles y media
        mkdir -p "$STATIC_DIR" "$MEDIA_DIR"
        chown -R "$APP_USER:$MAIN_GROUP" "$STATIC_DIR" "$MEDIA_DIR"
        chmod -R 770 "$STATIC_DIR" "$MEDIA_DIR"
        find "$STATIC_DIR" -type f -exec chmod 660 {} \;
        find "$MEDIA_DIR" -type f -exec chmod 660 {} \;

        # Crear gunicorn.sock con permisos correctos
        #touch "$GUNICORN_SOCKET"
        #chown "$APP_USER:$MAIN_GROUP" "$GUNICORN_SOCKET"
        #chmod 660 "$GUNICORN_SOCKET"
        # Eliminar cualquier archivo gunicorn.sock existente para evitar conflictos
        if [ -f "$GUNICORN_SOCKET" ]; then
            sudo rm -f "$GUNICORN_SOCKET"
            echo "Archivo $GUNICORN_SOCKET eliminado para evitar conflictos."
        fi

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

        # Reaplicar permisos
        chown -R "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR"
        chmod -R 770 "$PROJECT_DIR"
        find "$PROJECT_DIR" -type f -exec chmod 660 {} \;
        find "$PROJECT_DIR" -type f -name "*.sh" -exec chmod 770 {} \;
        find "$PROJECT_DIR" -type f -name "manage.py" -exec chmod 770 {} \;

        chown -R "$APP_USER:$MAIN_GROUP" "$LOG_DIR"
        chmod -R 770 "$LOG_DIR"
        find "$LOG_DIR" -type f -exec chmod 660 {} \;
        touch "$LOG_DIR/nlp.log" "$LOG_DIR/app.log" "$LOG_DIR/celery.log" "$LOG_DIR/chatbot.log" "$LOG_DIR/gunicorn_access.log" "$LOG_DIR/gunicorn_error.log"
        chown "$APP_USER:$MAIN_GROUP" "$LOG_DIR/nlp.log" "$LOG_DIR/app.log" "$LOG_DIR/celery.log" "$LOG_DIR/chatbot.log" "$LOG_DIR/gunicorn_access.log" "$LOG_DIR/gunicorn_error.log"
        chmod 660 "$LOG_DIR/nlp.log" "$LOG_DIR/app.log" "$LOG_DIR/celery.log" "$LOG_DIR/chatbot.log" "$LOG_DIR/gunicorn_access.log" "$LOG_DIR/gunicorn_error.log"

        chown -R "$APP_USER:$MAIN_GROUP" "$STATIC_DIR" "$MEDIA_DIR"
        chmod -R 770 "$STATIC_DIR" "$MEDIA_DIR"
        find "$STATIC_DIR" -type f -exec chmod 660 {} \;
        find "$MEDIA_DIR" -type f -exec chmod 660 {} \;

        touch "$GUNICORN_SOCKET"
        chown "$APP_USER:$MAIN_GROUP" "$GUNICORN_SOCKET"
        chmod 660 "$GUNICORN_SOCKET"
    fi

    SKILL_JSON="/home/pablo/skills_data/skill_db_relax_20.json"
    SKILL_URL="https://raw.githubusercontent.com/AnasAito/SkillNER/master/buckets/skills_processed.json"
    if [ ! -f "$SKILL_JSON" ] || [ "$(find "$SKILL_JSON" -mtime +1 2>/dev/null)" ]; then
        mkdir -p /home/pablo/skills_data
        wget "$SKILL_URL" -O "$SKILL_JSON"
        chown "$APP_USER:$MAIN_GROUP" "$SKILL_JSON"
        chmod 660 "$SKILL_JSON"
        echo "Archivo $SKILL_JSON actualizado desde SkillNER."
    else
        echo "Archivo $SKILL_JSON ya existe y está actualizado."
    fi

    ESCO_JSON="/home/pablo/skills_data/ESCO_occup_skills.json"
    ESCO_URL="https://raw.githubusercontent.com/source/ESCO_occup_skills.json" # Replace with actual URL
    if [ ! -f "$ESCO_JSON" ] || [ "$(find "$ESCO_JSON" -mtime +1 2>/dev/null)" ]; then
        wget "$ESCO_URL" -O "$ESCO_JSON" || echo "Advertencia: No se pudo descargar ESCO_occup_skills.json"
        chown "$APP_USER:$MAIN_GROUP" "$ESCO_JSON"
        chmod 660 "$ESCO_JSON"
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
        su - "$APP_USER" -c "$PY_VERSION -m venv $VENV_DIR" || {
            echo "Error: Falló la creación del entorno virtual."
            exit 1
        }
        echo "Entorno virtual creado."
    else
        echo "Entorno virtual ya existe."
    fi

    chown -R "$APP_USER:$MAIN_GROUP" "$VENV_DIR"
    chmod -R 770 "$VENV_DIR"
    find "$VENV_DIR" -type f -exec chmod 660 {} \;
    find "$VENV_DIR" -type f -name "*.sh" -exec chmod 770 {} \;
    chmod -R u+x "$VENV_DIR/bin/"

    # Instalar dependencias principales
    su - "$APP_USER" -c "source $VENV_DIR/bin/activate && \
        pip install --upgrade pip && \
        pip install wheel django gunicorn psycopg2-binary==2.9.9 redis==5.0.8 celery==5.4.0 \
        django-celery-beat django-celery-results sentry-sdk spacy==3.8.4 tensorflow==2.19.0 \
        tf-keras==2.19.0 tensorflow-text==2.19.0 django-silk==5.2.0 python-dotenv==1.0.1 \
        drf-yasg==1.21.7 django-cors-headers==4.7.0 djangorestframework==3.15.2" || {
            echo "Error: Falló la instalación de dependencias principales."
            exit 1
        }
    echo "Dependencias principales instaladas."

    # Instalar el modelo de spaCy
    su - "$APP_USER" -c "source $VENV_DIR/bin/activate && \
        pip install https://github.com/explosion/spacy-models/releases/download/es_core_news_md-3.8.0/es_core_news_md-3.8.0-py3-none-any.whl || python -m spacy download es_core_news_md" || {
            echo "Error: Falló la instalación del modelo de spaCy."
            exit 1
        }
    echo "Modelo de spaCy instalado."

    # Instalar dependencias específicas del proyecto
    su - "$APP_USER" -c "source $VENV_DIR/bin/activate && \
        cd $PROJECT_DIR && [ -f requirements.txt ] && pip install -r requirements.txt --no-deps" || {
            echo "Advertencia: Falló la instalación de requirements.txt, continuando."
        }
    echo "Dependencias específicas del proyecto instaladas."

    # Verificaciones
    echo "Verificando instalación..."
    su - "$APP_USER" -c "source $VENV_DIR/bin/activate && pip check" || {
        echo "Advertencia: pip check encontró problemas en las dependencias."
    }

    echo "Verificando instalación de spaCy..."
    su - "$APP_USER" -c "source $VENV_DIR/bin/activate && python -c 'import spacy; print(f\"spaCy version: {spacy.__version__}\"); nlp = spacy.load(\"es_core_news_md\"); print(\"Modelo NLP cargado correctamente.\")'" || {
        echo "Error: Falló la verificación de spaCy."
        exit 1
    }

    echo "Verificando instalación de TensorFlow..."
    su - "$APP_USER" -c "source $VENV_DIR/bin/activate && python -c 'import tensorflow as tf; print(f\"TF version: {tf.__version__}\")'" || {
        echo "Error: Falló la verificación de TensorFlow."
        exit 1
    }

    # Configurar variables de entorno para TensorFlow
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
    # Crear archivo .env si no existe
    ENV_FILE="$PROJECT_DIR/.env"
    if [ ! -f "$ENV_FILE" ]; then
        # Generar una clave secreta aleatoria
        SECRET_KEY=$(openssl rand -base64 48 | tr -dc 'a-zA-Z0-9' | head -c 50)
        sudo -u "$APP_USER" bash -c "cat > \"$ENV_FILE\" <<EOF
# Django Settings
DJANGO_SECRET_KEY=$SECRET_KEY
DJANGO_SECRET_KEY2=hfmrpTNRwmQ1F7gZI1DNKaQ9gNw3cgayKFB0HK_gt9BKJEnLy60v1v0PnkZtX3OkY48
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=$DOMAIN,127.0.0.1,localhost,34.57.227.244

# Admin contact
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

# Database Configuration
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_CONN_MAX_AGE=60
DB_CONNECT_TIMEOUT=10

# Notificaciones
NTFY_ENABLED=true
NTFY_DEFAULT_TOPIC=ai_huntred_notifications
NTFY_USERNAME=PabloLLH
NTFY_PASSWORD=Natalia&Patricio1113!
NTFY_API=tk_o8jpud5aezsa0ht8ozjm2eeix9d1p

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

# Localization
LANGUAGE_CODE=es-mx
TIMEZONE=America/Mexico_City

# Static and Media Files
STATIC_URL=/static/
STATIC_ROOT=$STATIC_DIR
MEDIA_URL=/media/
MEDIA_ROOT=$MEDIA_DIR

# API Rate Limiting
THROTTLE_ANON=100/day
THROTTLE_USER=1000/day

# Security Settings
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY

# TensorFlow Settings
TF_CPP_MIN_LOG_LEVEL=2
CUDA_VISIBLE_DEVICES=
TFHUB_CACHE_DIR=$TFHUB_CACHE
EOF" || {
            echo "Error: No se pudo crear el archivo $ENV_FILE."
            exit 1
        }
        sudo chown "$APP_USER:$MAIN_GROUP" "$ENV_FILE"
        sudo chmod 660 "$ENV_FILE"
        echo ".env creado con permisos correctos."
    else
        echo ".env ya existe, verificando permisos..."
        sudo chown "$APP_USER:$MAIN_GROUP" "$ENV_FILE"
        sudo chmod 660 "$ENV_FILE"
        echo "Permisos de .env verificados."
    fi

    # Verificar que .env existe
    if [ ! -f "$ENV_FILE" ]; then
        echo "Error: El archivo $ENV_FILE no se encontró después de intentar crearlo."
        exit 1
    fi

    # Configurar Gunicorn
    sudo cat > "$GUNICORN_SERVICE" <<EOF
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
ExecStart=$VENV_DIR/bin/gunicorn --workers 2 --bind unix:$GUNICORN_SOCKET --timeout 120 \
    --log-level debug \
    --access-logfile $GUNICORN_ACCESS_LOG \
    --error-logfile $GUNICORN_ERROR_LOG \
    $APP_NAME.wsgi:application
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
EOF
    sudo chown root:root "$GUNICORN_SERVICE"
    sudo chmod 644 "$GUNICORN_SERVICE"
    echo "Servicio Gunicorn configurado."

    # Configurar Celery
    sudo cat > "$CELERY_SERVICE" <<EOF
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
ExecStart=$VENV_DIR/bin/celery -A $APP_NAME worker --loglevel=info --concurrency=2
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
EOF
    sudo chown root:root "$CELERY_SERVICE"
    sudo chmod 644 "$CELERY_SERVICE"
    echo "Servicio Celery configurado."

    # Configurar truncado de logs
    TRUNCATE_LOGS_SCRIPT="/home/pablo/bin/truncate_logs.sh"
    if ! sudo crontab -u "$APP_USER" -l 2>/dev/null | grep -q "truncate_logs.sh"; then
        sudo mkdir -p /home/pablo/bin
        sudo bash -c "cat > $TRUNCATE_LOGS_SCRIPT <<EOF
#!/bin/bash
tail -n 50 $GUNICORN_ACCESS_LOG > /tmp/gunicorn_access_temp.log && mv /tmp/gunicorn_access_temp.log $GUNICORN_ACCESS_LOG
tail -n 50 $GUNICORN_ERROR_LOG > /tmp/gunicorn_error_temp.log && mv /tmp/gunicorn_error_temp.log $GUNICORN_ERROR_LOG
EOF" || {
            echo "Advertencia: No se pudo crear $TRUNCATE_LOGS_SCRIPT, continuando."
        }
        sudo chmod +x "$TRUNCATE_LOGS_SCRIPT"
        sudo chown "$APP_USER:$MAIN_GROUP" "$TRUNCATE_LOGS_SCRIPT"
        sudo -u "$APP_USER" bash -c "(crontab -l 2>/dev/null; echo \"0 * * * * $TRUNCATE_LOGS_SCRIPT\") | crontab -" || {
            echo "Advertencia: Falló la configuración de la tarea de cron para truncate_logs.sh, continuando."
        }
        echo "Tarea de truncado de logs configurada."
    else
        echo "Tarea de truncado de logs ya existe."
    fi

    # Asegurar archivos de log
    sudo touch "$GUNICORN_ACCESS_LOG" "$GUNICORN_ERROR_LOG"
    sudo chown "$APP_USER:$MAIN_GROUP" "$GUNICORN_ACCESS_LOG" "$GUNICORN_ERROR_LOG"
    sudo chmod 660 "$GUNICORN_ACCESS_LOG" "$GUNICORN_ERROR_LOG"
    echo "Archivos de log de Gunicorn creados con permisos correctos."

    # Eliminar cualquier archivo gunicorn.sock existente para evitar conflictos
    if [ -f "$GUNICORN_SOCKET" ]; then
        sudo rm -f "$GUNICORN_SOCKET"
        echo "Archivo $GUNICORN_SOCKET eliminado para evitar conflictos."
    fi

    # Verificar permisos del directorio del proyecto
    sudo chown "$APP_USER:$MAIN_GROUP" "$PROJECT_DIR"
    sudo chmod 770 "$PROJECT_DIR"
    echo "Permisos del directorio $PROJECT_DIR verificados."

    # Recargar y habilitar servicios
    sudo systemctl daemon-reload || {
        echo "Error: Falló systemctl daemon-reload."
        exit 1
    }
    sudo systemctl enable gunicorn celery || {
        echo "Error: Falló systemctl enable para gunicorn o celery."
        exit 1
    }

    # Reiniciar servicios con verificación
    for service in gunicorn celery; do
        echo "Iniciando servicio $service..."
        sudo systemctl restart "$service" || {
            echo "Error: No se pudo reiniciar el servicio $service."
            sudo journalctl -u "$service" -n 50
            exit 1
        }
        sleep 2
        if ! sudo systemctl is-active --quiet "$service"; then
            echo "Error: El servicio $service no está activo después del reinicio."
            sudo journalctl -u "$service" -n 50
            exit 1
        else
            echo "Servicio $service reiniciado con éxito."
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
        echo "Intentando obtener certificado para $DOMAIN..."
        if certbot --nginx -d "$DOMAIN" -m "$EMAIL" --agree-tos --non-interactive; then
            echo "Certificado obtenido exitosamente."
        else
            echo "ADVERTENCIA: Error al obtener certificado. Revisa límites de Let's Encrypt."
            echo "Comando para ejecutarlo manualmente: sudo certbot --nginx -d $DOMAIN -m $EMAIL --agree-tos --non-interactive"
        fi
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
    # Crear backup de la BD antes de proceder
    if [ -n "$DB_NAME" ] && command -v pg_dump &> /dev/null; then
        echo "Creando backup de la base de datos..."
        BACKUP_FILE="/tmp/${DB_NAME}_backup_$(date +%Y%m%d_%H%M%S).sql"
        if su - postgres -c "pg_dump $DB_NAME > $BACKUP_FILE"; then
            echo "Backup creado en $BACKUP_FILE"
            chown "$APP_USER:$MAIN_GROUP" "$BACKUP_FILE"
            chmod 640 "$BACKUP_FILE"
        else
            echo "Advertencia: No se pudo crear backup de la base de datos."
        fi
    fi

    # Verificación del entorno antes de migraciones
    echo "Verificando entorno Django..."
    if ! su - "$APP_USER" -c "source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py check"; then
        echo "ADVERTENCIA: Problemas detectados en el proyecto. Revise los errores antes de continuar."
        read -p "¿Desea continuar de todos modos? (s/n): " -n 1 -r CONTINUE
        echo
        if [[ ! $CONTINUE =~ ^[Ss]$ ]]; then
            echo "Proceso detenido por el usuario."
            exit 1
        fi
    fi

    # Ejecutar migraciones
    echo "Ejecutando migrate..."
    su - "$APP_USER" -c "source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py migrate --noinput" || {
        echo "ERROR: La migración falló. Revise los logs para más información."
        read -p "¿Desea continuar con el despliegue? (s/n): " -n 1 -r CONTINUE_DEPLOY
        echo
        if [[ ! $CONTINUE_DEPLOY =~ ^[Ss]$ ]]; then
            echo "Proceso detenido por el usuario."
            exit 1
        fi
    }
    echo "migrate completado exitosamente."

    echo "Ejecutando collectstatic..."
    su - "$APP_USER" -c "source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py collectstatic --noinput" || {
        echo "ADVERTENCIA: collectstatic encontró errores."
    }
    echo "collectstatic completado exitosamente."

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
alias logs_gunicorn='tail -f $LOG_DIR/gunicorn_access.log $LOG_DIR/gunicorn_error.log'
alias logs_nginx='sudo tail -f /var/log/nginx/error.log /var/log/nginx/access.log'
alias logs_all='tail -f $LOG_DIR/*.log'
alias rserver='sudo systemctl restart gunicorn nginx celery'
alias check_logs='tail -n 50 $LOG_DIR/*.log'
alias clear_logs='sudo truncate -s 0 $LOG_DIR/*.log && touch $LOG_DIR/gunicorn_access.log $LOG_DIR/gunicorn_error.log'
alias migrate='source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py migrate'
alias collectstatic='source $VENV_DIR/bin/activate && cd $PROJECT_DIR && python manage.py collectstatic --noinput'
alias check_services='systemctl status gunicorn celery nginx redis-server postgresql'
EOF"
        chown "$APP_USER:$APP_USER" "/home/$APP_USER/.bashrc"
        chmod 660 "/home/$APP_USER/.bashrc"
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
echo "  curl -I http://$DOMAIN/admin/"
echo "Revisa /home/pablo/setup_status.conf para estado de pasos."
echo "Logs: tail -f $LOG_DIR/*.log"
echo "==========================================================="