#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# Update system
apt-get update && apt-get upgrade -y

# Install system dependencies
apt-get install -y \
    python3-venv \
    python3-dev \
    build-essential \
    libpq-dev \
    redis-server \
    supervisor \
    nginx

# Create project directory
PROJECT_DIR="/home/pablo/"
if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
fi

# Create virtual environment
python3 -m venv "$PROJECT_DIR/venv"
source "$PROJECT_DIR/venv/bin/activate"

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure Django
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

# Configure Redis
systemctl enable redis-server
systemctl start redis-server

# Configure Supervisor
supervisorctl reread
supervisorctl update
supervisorctl restart all

# Configure Nginx
nginx -t
systemctl restart nginx

# Configure Celery
systemctl enable celery
systemctl start celery

# Configure Monitoring
systemctl enable prometheus
systemctl start prometheus

# Create log directories
mkdir -p /var/log/huntred/
chown -R www-data:www-data /var/log/huntred/

# Set permissions
chown -R www-data:www-data "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"

# Show status
echo "Migration completed successfully!"
echo "System services status:"
systemctl status redis-server celery nginx supervisor
