import logging
from datetime import timedelta
import environ

env = environ.Env()

class MonitoringConfig:
    @staticmethod
    def get_config():
        # Metrics configuration
        metrics_config = {
            'ENABLED': env.bool('ENABLE_METRICS', default=True),
            'COLLECTION_INTERVAL': timedelta(minutes=5),
            'METRICS_ENDPOINT': '/metrics',
            'ENABLE_PROMETHEUS': env.bool('ENABLE_PROMETHEUS', default=True),
        }

        # Alert configuration
        alert_config = {
            'CRITICAL_THRESHOLD': 0.95,  # 95% resource usage
            'WARNING_THRESHOLD': 0.85,   # 85% resource usage
            'ALERT_EMAILS': env.list('ALERT_EMAILS', default=[]),
            'ALERT_INTERVAL': timedelta(hours=1),
        }

        # Health check configuration
        health_check_config = {
            'CHECK_INTERVAL': timedelta(minutes=1),
            'MAX_RETRIES': 3,
            'RETRY_DELAY': timedelta(seconds=30),
            'CHECKS': {
                'database': True,
                'cache': True,
                'celery': True,
                'external_apis': True,
            },
        }

        return {
            'METRICS_CONFIG': metrics_config,
            'ALERT_CONFIG': alert_config,
            'HEALTH_CHECK_CONFIG': health_check_config,
        }

# Initialize logging
logger = logging.getLogger(__name__)

def setup_monitoring():
    config = MonitoringConfig.get_config()
    
    if config['METRICS_CONFIG']['ENABLED']:
        logger.info("Metrics collection enabled")
        
    if config['ALERT_CONFIG']['ALERT_EMAILS']:
        logger.info(f"Alert system configured for {len(config['ALERT_CONFIG']['ALERT_EMAILS'])} recipients")
        
    return config
