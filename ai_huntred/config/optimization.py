# /home/pablo/ai_huntred/config/optimization.py
import os
import environ
from django.conf import settings
import logging

env = environ.Env()

class OptimizationConfig:
    @staticmethod
    def get_config():
        """
        Retrieves optimized configuration with fallback for Redis URL.
        """
        # Cache configuration
        try:
            redis_url = env('REDIS_URL', default=None)
            if redis_url is None:
                # Fallback to REDIS_CONFIG from settings
                redis_config = getattr(settings, 'REDIS_CONFIG', {})
                redis_host = redis_config.get('host', 'localhost')
                redis_port = redis_config.get('port', 6379)
                redis_db = redis_config.get('db', 0)
                redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
        except Exception as e:
            # Log error and use fallback
            logging.error(f"Error retrieving REDIS_URL: {e}")
            redis_url = "redis://localhost:6379/0"

        cache_config = {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': redis_url,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'SOCKET_CONNECT_TIMEOUT': 5,  # Seconds
                'SOCKET_TIMEOUT': 5,  # Seconds
                'PICKLE_VERSION': -1,  # Latest pickle protocol
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 100,  # Limit connection pool size
                    'retry_on_timeout': True,  # Retry on connection timeout
                },
            },
            'KEY_PREFIX': 'ai_huntred_',
            'TIMEOUT': getattr(settings, 'REDIS_CONFIG', {}).get('ttl', 3600),
        }

        # Session configuration with Redis
        session_config = {
            'BACKEND': 'django.contrib.sessions.backends.cache',
            'CACHE_ALIAS': 'default',
            'SESSION_ENGINE': 'django.contrib.sessions.backends.cache',
            'SESSION_CACHE_ALIAS': 'default',
            'SESSION_COOKIE_AGE': 86400,  # 24 hours
            'SESSION_SAVE_EVERY_REQUEST': True,
            'SESSION_EXPIRE_AT_BROWSER_CLOSE': False,
        }

        # Database optimization
        db_config = {
            'CONN_MAX_AGE': 600,  # 10 minutes
            'CONN_HEALTH_CHECKS': True,
            'OPTIONS': {
                'timeout': 10,
                'connect_timeout': 10,
                'read_preference': 'primaryPreferred',
            },
        }

        # File handling optimization
        file_config = {
            'MAX_UPLOAD_SIZE': 10485760,  # 10MB
            'FILE_UPLOAD_PERMISSIONS': 0o644,
            'FILE_UPLOAD_TEMP_DIR': os.path.join(settings.MEDIA_ROOT, 'temp'),
            'FILE_UPLOAD_MAX_MEMORY_SIZE': 2621440,  # 2.5MB
            'MEDIA_HANDLING': {
                'IMAGE_MAX_SIZE': 5242880,  # 5MB
                'VIDEO_MAX_SIZE': 104857600,  # 100MB
                'AUDIO_MAX_SIZE': 20971520,  # 20MB
                'DOCUMENT_MAX_SIZE': 10485760,  # 10MB
                'ALLOWED_IMAGE_TYPES': ['image/jpeg', 'image/png', 'image/gif'],
                'ALLOWED_VIDEO_TYPES': ['video/mp4', 'video/quicktime'],
                'ALLOWED_AUDIO_TYPES': ['audio/mpeg', 'audio/wav'],
                'ALLOWED_DOCUMENT_TYPES': ['application/pdf', 'application/msword'],
                'IMAGE_QUALITY': 85,  # JPEG quality
                'THUMBNAIL_SIZE': (200, 200),  # Thumbnail dimensions
                'COMPRESSION_ENABLED': True,
                'STORAGE_BACKEND': 'django.core.files.storage.FileSystemStorage',
                'CDN_ENABLED': env.bool('CDN_ENABLED', default=False),
                'CDN_DOMAIN': env('CDN_DOMAIN', default=None),
            }
        }

        # Async task optimization
        celery_config = {
            'BROKER_POOL_LIMIT': 10,
            'BROKER_CONNECTION_TIMEOUT': 10,
            'BROKER_HEARTBEAT': 300,
            'WORKER_PREFETCH_MULTIPLIER': 1,
            'TASK_ACKS_LATE': True,
            'TASK_REJECT_ON_WORKER_LOST': True,
            'TASK_ROUTES': {
                'app.ats.tasks.process_media.*': {'queue': 'media'},
                'app.ats.tasks.send_message.*': {'queue': 'messages'},
                'app.ats.tasks.analyze_content.*': {'queue': 'analysis'},
            },
            'TASK_DEFAULT_QUEUE': 'default',
            'TASK_QUEUES': {
                'default': {
                    'exchange': 'default',
                    'routing_key': 'default',
                },
                'media': {
                    'exchange': 'media',
                    'routing_key': 'media',
                },
                'messages': {
                    'exchange': 'messages',
                    'routing_key': 'messages',
                },
                'analysis': {
                    'exchange': 'analysis',
                    'routing_key': 'analysis',
                },
            },
        }

        return {
            'CACHE_CONFIG': cache_config,
            'SESSION_CONFIG': session_config,
            'DB_CONFIG': db_config,
            'FILE_CONFIG': file_config,
            'CELERY_CONFIG': celery_config,
        }