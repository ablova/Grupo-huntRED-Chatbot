#!/bin/bash

set -e

# Esperar a que la base de datos esté disponible
function postgres_ready() {
    python << END
import sys
import psycopg2
import os
import environ

env = environ.Env()
try:
    conn = psycopg2.connect(
        dbname=env("DB_NAME"),
        user=env("DB_USER"),
        password=env("DB_PASSWORD"),
        host=env("DB_HOST"),
        port=env("DB_PORT", default="5432")
    )
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

until postgres_ready; do
    echo "Esperando a que PostgreSQL esté disponible..."
    sleep 2
done

echo "PostgreSQL está disponible, continuando..."

# Validar entorno
if [ "$DJANGO_SETTINGS_MODULE" = "ai_huntred.settings.production" ]; then
    echo "Ejecutando en ambiente de producción"
    # Colectar archivos estáticos
    python manage.py collectstatic --no-input
    # Aplicar migraciones
    python manage.py migrate --no-input
    # Iniciar servidor
    exec gunicorn ai_huntred.wsgi:application --bind 0.0.0.0:8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker --log-level info
else
    echo "Ejecutando en ambiente de desarrollo"
    # Aplicar migraciones
    python manage.py migrate --no-input
    # Iniciar servidor de desarrollo
    exec python manage.py runserver 0.0.0.0:8000
fi
