#!/bin/bash

# Script de despliegue para AI HuntRED
# Autor: Pablo LLH
# Fecha: 2024-03-19

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Función para imprimir mensajes
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Verificar si se está ejecutando como root
if [ "$EUID" -ne 0 ]; then
    print_error "Este script debe ejecutarse como root"
    exit 1
fi

# Directorio del proyecto
PROJECT_DIR="/var/www/huntred"
VENV_DIR="$PROJECT_DIR/venv"

# Crear directorios necesarios
print_message "Creando directorios necesarios..."
mkdir -p $PROJECT_DIR
mkdir -p /var/log/supervisor
mkdir -p /var/log/nginx
mkdir -p /var/www/staticfiles
mkdir -p /var/www/media
mkdir -p /etc/nginx/ssl

# Instalar dependencias del sistema
print_message "Instalando dependencias del sistema..."
apt-get update
apt-get install -y python3-pip python3-venv nginx supervisor postgresql postgresql-contrib redis-server

# Configurar PostgreSQL
print_message "Configurando PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE g_huntred_ai_db;"
sudo -u postgres psql -c "CREATE USER g_huntred_pablo WITH PASSWORD 'Natalia&Patricio1113!';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE g_huntred_ai_db TO g_huntred_pablo;"

# Crear y activar entorno virtual
print_message "Creando entorno virtual..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Instalar dependencias de Python
print_message "Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Copiar archivos de configuración
print_message "Copiando archivos de configuración..."
cp nginx.conf /etc/nginx/nginx.conf
cp supervisor.conf /etc/supervisor/conf.d/huntred.conf
cp gunicorn_config.py $PROJECT_DIR/

# Configurar permisos
print_message "Configurando permisos..."
chown -R www-data:www-data $PROJECT_DIR
chown -R www-data:www-data /var/www/staticfiles
chown -R www-data:www-data /var/www/media
chmod -R 755 $PROJECT_DIR

# Recolectar archivos estáticos
print_message "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Aplicar migraciones
print_message "Aplicando migraciones..."
python manage.py migrate

# Reiniciar servicios
print_message "Reiniciando servicios..."
supervisorctl reread
supervisorctl update
supervisorctl restart all
systemctl restart nginx

print_message "¡Despliegue completado con éxito!"
print_message "El sistema está disponible en https://ai.huntred.com" 