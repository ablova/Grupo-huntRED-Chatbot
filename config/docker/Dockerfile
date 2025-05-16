FROM python:3.10-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=America/Mexico_City
ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH="${PYTHONPATH}:/app"

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    netcat-traditional \
    postgresql-client \
    wkhtmltopdf \
    curl \
    git \
    nginx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Copiar configuración de nginx
COPY ./deploy/nginx.conf /etc/nginx/sites-available/default

# Crear directorios para archivos estáticos y media
RUN mkdir -p /app/staticfiles /app/media

# Exponer puertos
EXPOSE 8000

# Copiar script de entrada
COPY ./deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Establecer script de entrada
ENTRYPOINT ["/entrypoint.sh"]
