import os
from django.core.cache import cache
from django.conf import settings

import environ

env = environ.Env()

class OptimizationConfig:
    @staticmethod
    def get_config():
        # Cache configuration
        cache_config = {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': env('REDIS_URL'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            },
            'TIMEOUT': 3600,  # 1 hour
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
        }

        # Async task optimization
        celery_config = {
            'BROKER_POOL_LIMIT': 10,
            'BROKER_CONNECTION_TIMEOUT': 10,
            'BROKER_HEARTBEAT': 300,
            'WORKER_PREFETCH_MULTIPLIER': 1,
            'TASK_ACKS_LATE': True,
            'TASK_REJECT_ON_WORKER_LOST': True,
        }

        return {
            'CACHE_CONFIG': cache_config,
            'DB_CONFIG': db_config,
            'FILE_CONFIG': file_config,
            'CELERY_CONFIG': celery_config,
        }
