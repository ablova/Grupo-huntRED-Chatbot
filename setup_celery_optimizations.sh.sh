#!/bin/bash
# setup_celery_optimizations.sh - Apply all Celery optimizations

set -e

echo "===== Setting up Celery Optimizations ====="

# Backup existing files
echo "Creating backups of current configuration..."
if [ -f /home/pablo/ai_huntred/celery.py ]; then
    cp /home/pablo/ai_huntred/celery.py /home/pablo/ai_huntred/celery.py.bak.$(date +%Y%m%d)
fi

for service in celery-worker celery-scraping celery-ml celery-beat; do
    if [ -f /etc/systemd/system/$service.service ]; then
        sudo cp /etc/systemd/system/$service.service /etc/systemd/system/$service.service.bak.$(date +%Y%m%d)
    fi
done

# Copy new configuration files
echo "Copying optimized Celery configuration..."
cat > /home/pablo/ai_huntred/celery.py << 'EOF'
from __future__ import absolute_import, unicode_literals
import os
import django
import logging
from celery import Celery
from celery.schedules import crontab
from celery.signals import after_setup_task_logger, worker_ready
from django.db.utils import OperationalError

logger = logging.getLogger("app.tasks")

# Set Django settings if not already set
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')
    django.setup()

app = Celery('ai_huntred')

# Initialize task annotations dictionary
app.conf.task_annotations = {}

# Improved broker and backend configuration with connection pool settings
app.conf.update(
    broker_url='redis://127.0.0.1:6379/0',
    result_backend='redis://127.0.0.1:6379/0',
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',
    timezone='America/Mexico_City',
    enable_utc=False,  # Use local timezone
    
    # Connection management - prevent connection issues
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    broker_pool_limit=10,  # Increased from 1 to allow more connections
    broker_heartbeat=10,  # Add heartbeat to detect connection issues
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_remote_tracebacks=True,  # Enable detailed error tracing
    result_expires=3600,  # 1 hour
    
    # Memory optimization
    worker_max_memory_per_child=150000,  # Reduced from 200MB to 150MB
    worker_max_tasks_per_child=3,  # Reduced from 5 to 3 tasks before worker restart
    worker_concurrency=1,
    worker_prefetch_multiplier=1,
    
    # Task time constraints
    task_time_limit=600,  # Increased to 10 minutes
    task_soft_time_limit=540,  # 9 minutes - gives workers time to clean up
    
    # Add visibility settings for tasks
    task_track_started=True,
    task_send_sent_event=True,
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# =========================================================
# Queue and routing definitions
# =========================================================

task_queues = {
    'default': {'exchange': 'default', 'routing_key': 'default'},
    'ml': {'exchange': 'ml', 'routing_key': 'ml.#'},
    'scraping': {'exchange': 'scraping', 'routing_key': 'scraping.#'},
    'notifications': {'exchange': 'notifications', 'routing_key': 'notifications.#'},
}

task_routes = {
    'app.tasks.execute_ml_and_scraping': {'queue': 'ml'},
    'app.tasks.ejecutar_scraping': {'queue': 'scraping'},
    'app.tasks.send_whatsapp_message': {'queue': 'notifications'},
    'app.tasks.send_telegram_message': {'queue': 'notifications'},
    'app.tasks.send_messenger_message': {'queue': 'notifications'},
    # Add explicit routing for all other tasks
    'app.tasks.*': {'queue': 'default'},
}

app.conf.task_queues = task_queues
app.conf.task_routes = task_routes

# =========================================================
# Beat schedule definition with better distribution
# =========================================================

# =========================================================
# Beat schedule definition with better distribution and more descriptive names
# =========================================================

SCHEDULE_DICT = {
    # Staggered the execution times to avoid concurrent resource usage
    'Ejecutar ML y Scraping (mañana)': {
        'task': 'app.tasks.execute_ml_and_scraping',
        'schedule': crontab(hour=7, minute=30),
    },
    'Ejecutar ML y Scraping (mediodía)': {
        'task': 'app.tasks.execute_ml_and_scraping',
        'schedule': crontab(hour=12, minute=15),
    },
    'Enviar notificaciones diarias': {
        'task': 'app.tasks.send_daily_notification',
        'schedule': crontab(minute=15, hour='*/2'),
    },
    'Generar y enviar reportes consolidados': {
        'task': 'app.tasks.generate_and_send_reports',
        'schedule': crontab(hour=8, minute=40),
    },
    'Generar y enviar reportes de aniversario': {
        'task': 'app.tasks.generate_and_send_anniversary_reports',
        'schedule': crontab(hour=9, minute=10),
    },
    'Enviar reporte diario completo': {
        'task': 'app.tasks.enviar_reporte_diario',
        'schedule': crontab(hour=23, minute=45),
    },
    'Limpieza trimestral de vacantes antiguas': {
        'task': 'app.tasks.limpieza_vacantes',
        'schedule': crontab(day_of_month='1', month_of_year='1,4,7,11', hour=1, minute=30),
    },
    'Ejecución diaria de scraping': {
        'task': 'app.tasks.ejecutar_scraping',
        'schedule': crontab(hour=2, minute=30),
    },
    'Verificación diaria de dominios de scraping': {
        'task': 'app.tasks.verificar_dominios_scraping',
        'schedule': crontab(hour=3, minute=30),
    },
    'Entrenamiento diario de modelos ML': {
        'task': 'app.tasks.train_ml_task',
        'schedule': crontab(hour=4, minute=0),
    },
    'Revisión de emails cada 2 horas': {
        'task': 'app.tasks.check_emails_and_parse_cvs',
        'schedule': crontab(minute=30, hour='*/2'),
    },
    'Scraping de emails (mañana)': {
        'task': 'tasks.execute_email_scraper',
        'schedule': crontab(hour=8, minute=45),
    },
    'Scraping de emails (noche)': {
        'task': 'tasks.execute_email_scraper',
        'schedule': crontab(hour=22, minute=45),
    },
    'Invitaciones para completar perfil': {
        'task': 'app.tasks.enviar_invitaciones_completar_perfil',
        'schedule': crontab(minute=45, hour='*/6'),
    },
}

# =========================================================
# Improved periodic task registration with better error handling
# =========================================================

@worker_ready.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Register periodic tasks only when Celery is ready and Django apps are loaded.
    Includes better error handling and retry logic.
    """
    from django.apps import apps
    import time
    
    # Check Django readiness up to 3 times with a delay
    for attempt in range(3):
        if apps.ready:
            break
            
        logger.warning(f"⏳ Django not ready on attempt {attempt+1}. Waiting...")
        time.sleep(5)
    
    if not apps.ready:
        logger.error("❌ Django still not ready after retries. Scheduling will be handled by beat service.")
        return
    
    sender.conf.beat_schedule = SCHEDULE_DICT
    
    # Register tasks in django_celery_beat with better error handling
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            from django_celery_beat.models import CrontabSchedule, PeriodicTask
            from django.db import transaction
            
            with transaction.atomic():
                for name, config in SCHEDULE_DICT.items():
                    schedule, _ = CrontabSchedule.objects.get_or_create(
                        minute=config["schedule"].minute,
                        hour=config["schedule"].hour,
                        day_of_week=config["schedule"].day_of_week,
                        day_of_month=config["schedule"].day_of_month,
                        month_of_year=config["schedule"].month_of_year,
                    )
                    
                    task_defaults = {"crontab": schedule, "enabled": True}
                    
                    # Add task arguments if present
                    if "args" in config:
                        task_defaults["args"] = config["args"]
                    if "kwargs" in config:
                        task_defaults["kwargs"] = config["kwargs"]
                        
                    PeriodicTask.objects.update_or_create(
                        name=name,
                        task=config["task"],
                        defaults=task_defaults,
                    )
                
                logger.info(f"✅ Successfully registered {len(SCHEDULE_DICT)} periodic tasks")
                break
                
        except OperationalError:
            logger.warning(f"⚠️ Database not available on attempt {attempt+1}/{max_attempts}")
            if attempt < max_attempts - 1:
                time.sleep(10)  # Wait 10 seconds before retrying
        except Exception as e:
            logger.error(f"❌ Error registering periodic tasks: {str(e)}")
            break

# Connect setup function to Celery configuration signal
app.on_after_configure.connect(setup_periodic_tasks)

# Autodiscover tasks
app.autodiscover_tasks()

# Task-specific rate limits and resource constraints with better limits
app.conf.task_annotations.update({
    'app.tasks.generate_and_send_reports': {
        'rate_limit': '3/m',
        'time_limit': 300,  # 5 minutes
        'soft_time_limit': 270,  # 4.5 minutes
    },
    'app.tasks.send_daily_notification': {
        'rate_limit': '3/m',
        'time_limit': 300,
    },
    'app.tasks.execute_ml_and_scraping': {
        'rate_limit': '1/h',
        'time_limit': 2700,  # 45 minutes
        'soft_time_limit': 2400,  # 40 minutes
    },
    'app.tasks.ejecutar_scraping': {
        'rate_limit': '1/h',
        'time_limit': 2700,
        'soft_time_limit': 2400,
    },
    'app.tasks.train_ml_task': {
        'rate_limit': '1/d',
        'time_limit': 5400,  # 1.5 hours
        'soft_time_limit': 4800,  # 1.3 hours
    },
})
EOF

# Create systemd service files
echo "Creating optimized systemd service files..."

# Create celery-worker service
sudo bash -c 'cat > /etc/systemd/system/celery-worker.service' << 'EOF'
[Unit]
Description=Celery Worker for ai_huntred (Default and Notifications)
After=network.target redis.service postgresql.service
Wants=redis.service postgresql.service
# Changed Requires to Wants to prevent service dependency failures

[Service]
Type=simple
User=pablollh
Group=ai_huntred
WorkingDirectory=/home/pablo/
Environment="PYTHONPATH=/home/pablo/"
Environment="DJANGO_SETTINGS_MODULE=ai_huntred.settings"
# Added memory limit and increased timeout
Environment="CELERY_WORKER_MAX_MEMORY_PER_CHILD=150000"
Environment="CELERY_WORKER_HIJACK_ROOT_LOGGER=FALSE"

# Command with improved parameters
ExecStart=/home/pablo/venv/bin/celery -A ai_huntred worker \
    -Q notifications,default \
    --loglevel=INFO \
    --concurrency=2 \
    --max-tasks-per-child=3 \
    --pool=prefork \
    --without-gossip \
    --without-mingle \
    -n worker@%%h

# Graceful shutdown with timeout
ExecStop=/bin/sh -c 'pkill -TERM -P $MAINPID'
TimeoutStopSec=300

# Improved restart settings
Restart=on-failure
RestartSec=30

# System resource limits
LimitNOFILE=65536
MemoryLimit=600M
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF

# Create celery-scraping service
sudo bash -c 'cat > /etc/systemd/system/celery-scraping.service' << 'EOF'
[Unit]
Description=Celery Worker Scraping for ai_huntred
After=network.target redis.service postgresql.service
Wants=redis.service postgresql.service

[Service]
Type=simple
User=pablollh
Group=ai_huntred
WorkingDirectory=/home/pablo/
Environment="PYTHONPATH=/home/pablo/"
Environment="DJANGO_SETTINGS_MODULE=ai_huntred.settings"
Environment="CELERY_WORKER_MAX_MEMORY_PER_CHILD=150000"
Environment="CELERY_WORKER_HIJACK_ROOT_LOGGER=FALSE"

ExecStart=/home/pablo/venv/bin/celery -A ai_huntred worker \
    -Q scraping \
    --loglevel=INFO \
    --concurrency=1 \
    --max-tasks-per-child=1 \
    --pool=prefork \
    --without-gossip \
    --without-mingle \
    -n worker_scraping@%%h
    
ExecStop=/bin/sh -c 'pkill -TERM -P $MAINPID'
TimeoutStopSec=300

Restart=on-failure
RestartSec=60

LimitNOFILE=65536
MemoryLimit=800M
CPUQuota=90%

[Install]
WantedBy=multi-user.target
EOF

# Create celery-ml service
sudo bash -c 'cat > /etc/systemd/system/celery-ml.service' << 'EOF'
[Unit]
Description=Celery Worker ML for ai_huntred
After=network.target redis.service postgresql.service
Wants=redis.service postgresql.service

[Service]
Type=simple
User=pablollh
Group=ai_huntred
WorkingDirectory=/home/pablo/
Environment="PYTHONPATH=/home/pablo/"
Environment="DJANGO_SETTINGS_MODULE=ai_huntred.settings"
Environment="CELERY_WORKER_MAX_MEMORY_PER_CHILD=150000"
Environment="CELERY_WORKER_HIJACK_ROOT_LOGGER=FALSE"

ExecStart=/home/pablo/venv/bin/celery -A ai_huntred worker \
    -Q ml \
    --loglevel=INFO \
    --concurrency=1 \
    --max-tasks-per-child=1 \
    --pool=prefork \
    --without-gossip \
    --without-mingle \
    -n worker_ml@%%h
    
ExecStop=/bin/sh -c 'pkill -TERM -P $MAINPID'
TimeoutStopSec=600

Restart=on-failure
RestartSec=120

LimitNOFILE=65536
MemoryLimit=1G
CPUQuota=90%

[Install]
WantedBy=multi-user.target
EOF

# Create celery-beat service
sudo bash -c 'cat > /etc/systemd/system/celery-beat.service' << 'EOF'
[Unit]
Description=Celery Beat Service for ai_huntred
After=network.target redis.service postgresql.service
Wants=redis.service postgresql.service

[Service]
Type=simple
User=pablollh
Group=ai_huntred
WorkingDirectory=/home/pablo/
Environment="PYTHONPATH=/home/pablo/"
Environment="DJANGO_SETTINGS_MODULE=ai_huntred.settings"

# Added database connection parameters
ExecStartPre=/bin/sleep 10
ExecStart=/home/pablo/venv/bin/celery -A ai_huntred beat \
    --loglevel=INFO \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler \
    --max-interval=300
    
ExecStop=/bin/kill -s TERM $MAINPID
TimeoutStopSec=180

Restart=on-failure
RestartSec=60

# Lower resource limits for beat
LimitNOFILE=65536
MemoryLimit=200M
CPUQuota=30%

[Install]
WantedBy=multi-user.target
EOF

# Set correct permissions
echo "Setting correct permissions..."
sudo chmod 644 /etc/systemd/system/celery-*.service

# Create monitoring script
echo "Creating monitoring script..."
mkdir -p /home/pablo/scripts

cat > /home/pablo/scripts/monitor_celery.sh << 'EOF'
#!/bin/bash
# /home/pablo/scripts/monitor_celery.sh
# Monitors Celery services and restarts them if issues are detected

LOG_FILE="/var/log/celery_monitor.log"
SERVICES=("celery-worker" "celery-scraping" "celery-ml" "celery-beat")
EMAIL="pablo@example.com"  # Change to your email

# Create log file if it doesn't exist
touch $LOG_FILE
chmod 644 $LOG_FILE

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

check_redis() {
    if ! redis-cli ping > /dev/null 2>&1; then
        log "ERROR: Redis is not responding. Attempting to restart..."
        sudo systemctl restart redis
        sleep 5
        
        if ! redis-cli ping > /dev/null 2>&1; then
            log "CRITICAL: Redis restart failed!"
            echo "Redis service failed to restart on $(hostname)" | mail -s "CRITICAL: Redis Down" $EMAIL
            return 1
        else
            log "Redis restarted successfully"
            return 0
        fi
    fi
    return 0
}

check_celery_services() {
    local restart_count=0
    
    for service in "${SERVICES[@]}"; do
        # Check if service is active
        if ! systemctl is-active --quiet $service; then
            log "WARNING: $service is not running. Attempting to restart..."
            sudo systemctl restart $service
            sleep 10
            restart_count=$((restart_count + 1))
            
            if ! systemctl is-active --quiet $service; then
                log "ERROR: Failed to restart $service"
            else
                log "$service restarted successfully"
            fi
        fi
        
        # Check memory usage of the service
        pid=$(pgrep -f "celery.*$service" | head -n1)
        if [ ! -z "$pid" ]; then
            mem_usage=$(ps -o rss= -p $pid | awk '{print $1/1024}')
            if (( $(echo "$mem_usage > 900" | bc -l) )); then
                log "WARNING: $service using ${mem_usage}MB memory. Restarting..."
                sudo systemctl restart $service
                sleep 10
                restart_count=$((restart_count + 1))
            fi
        fi
    done
    
    if [ $restart_count -gt 2 ]; then
        log "Multiple services needed restart. Possible system issue."
        echo "Multiple Celery services needed restart on $(hostname)" | mail -s "WARNING: Celery Services Restarted" $EMAIL
    fi
}

# Clear old Celery PIDs if they exist
rm -f /home/pablo/ai_huntred/*.pid 2>/dev/null

# Main monitoring loop
log "Starting Celery monitoring service"

while true; do
    check_redis
    check_celery_services
    
    # Check for memory pressure
    free_mem=$(free -m | awk 'NR==2{print $4}')
    if [ $free_mem -lt 200 ]; then
        log "WARNING: Low memory ($free_mem MB free). Clearing system caches..."
        sudo sync && sudo echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
    fi
    
    # Sleep for 5 minutes
    sleep 300
done
EOF

chmod +x /home/pablo/scripts/monitor_celery.sh

# Set up monitoring service
echo "Setting up monitoring service..."
sudo bash -c 'cat > /etc/systemd/system/celery-monitor.service' << 'EOF'
[Unit]
Description=Celery Monitor and Auto-Recovery Service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/home/pablo/scripts/monitor_celery.sh
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

sudo chmod 644 /etc/systemd/system/celery-monitor.service

# Reload systemd and restart services
echo "Reloading systemd and restarting services..."
sudo systemctl daemon-reload

# Stop all services first
for service in celery-worker celery-scraping celery-ml celery-beat; do
    sudo systemctl stop $service || true
done

# Clear any leftover PID files
rm -f /home/pablo/ai_huntred/*.pid 2>/dev/null || true

# Start services in the correct order
sudo systemctl start celery-beat
sleep 5
sudo systemctl start celery-worker
sleep 5
sudo systemctl start celery-scraping
sleep 5
sudo systemctl start celery-ml
sleep 5

# Enable services on boot
for service in celery-worker celery-scraping celery-ml celery-beat celery-monitor; do
    sudo systemctl enable $service
done

# Start monitoring service
sudo systemctl start celery-monitor

echo "===== Celery optimization setup complete! ====="
echo "Monitoring logs will be available at: /var/log/celery_monitor.log"