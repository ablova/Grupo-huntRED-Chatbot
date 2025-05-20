# Configuración de Gunicorn para producción
import multiprocessing
import os

# Configuración básica
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')
workers = os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1)
worker_class = 'uvicorn.workers.UvicornWorker'
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 120))
keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', 5))

# Configuración de workers
max_requests = int(os.environ.get('GUNICORN_MAX_REQUESTS', 1000))
max_requests_jitter = int(os.environ.get('GUNICORN_MAX_REQUESTS_JITTER', 50))
worker_connections = int(os.environ.get('GUNICORN_WORKER_CONNECTIONS', 1000))

# Configuración de logging
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '-')
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '-')
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# Configuración de seguridad
limit_request_line = int(os.environ.get('GUNICORN_LIMIT_REQUEST_LINE', 4094))
limit_request_fields = int(os.environ.get('GUNICORN_LIMIT_REQUEST_FIELDS', 100))
limit_request_field_size = int(os.environ.get('GUNICORN_LIMIT_REQUEST_FIELD_SIZE', 8190))

# Configuración de SSL (si es necesario)
keyfile = os.environ.get('GUNICORN_KEYFILE', None)
certfile = os.environ.get('GUNICORN_CERTFILE', None)

# Configuración de timeouts
graceful_timeout = int(os.environ.get('GUNICORN_GRACEFUL_TIMEOUT', 30))
forwarded_allow_ips = os.environ.get('GUNICORN_FORWARDED_ALLOW_IPS', '*')

# Configuración de preload
preload_app = os.environ.get('GUNICORN_PRELOAD_APP', 'True').lower() == 'true'

# Configuración de daemon
daemon = os.environ.get('GUNICORN_DAEMON', 'False').lower() == 'true'
pidfile = os.environ.get('GUNICORN_PIDFILE', None)

# Configuración de umask
umask = int(os.environ.get('GUNICORN_UMASK', '0o022'), 8)

# Configuración de user/group
user = os.environ.get('GUNICORN_USER', None)
group = os.environ.get('GUNICORN_GROUP', None)

# Configuración de worker temp
worker_tmp_dir = os.environ.get('GUNICORN_WORKER_TMP_DIR', None)

# Configuración de worker class
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'uvicorn.workers.UvicornWorker')

# Configuración de worker processes
worker_processes = int(os.environ.get('GUNICORN_WORKER_PROCESSES', multiprocessing.cpu_count()))

# Configuración de worker threads
worker_threads = int(os.environ.get('GUNICORN_WORKER_THREADS', 2))

# Configuración de worker connections
worker_connections = int(os.environ.get('GUNICORN_WORKER_CONNECTIONS', 1000))

# Configuración de worker class
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'uvicorn.workers.UvicornWorker')

# Configuración de worker processes
worker_processes = int(os.environ.get('GUNICORN_WORKER_PROCESSES', multiprocessing.cpu_count()))

# Configuración de worker threads
worker_threads = int(os.environ.get('GUNICORN_WORKER_THREADS', 2))

# Configuración de worker connections
worker_connections = int(os.environ.get('GUNICORN_WORKER_CONNECTIONS', 1000))

# Configuración de worker class
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'uvicorn.workers.UvicornWorker')

# Configuración de worker processes
worker_processes = int(os.environ.get('GUNICORN_WORKER_PROCESSES', multiprocessing.cpu_count()))

# Configuración de worker threads
worker_threads = int(os.environ.get('GUNICORN_WORKER_THREADS', 2))

# Configuración de worker connections
worker_connections = int(os.environ.get('GUNICORN_WORKER_CONNECTIONS', 1000)) 