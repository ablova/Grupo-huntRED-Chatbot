# /home/pablo/ai_huntred/config/monitoring.py
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
            'API_METRICS': {
                'whatsapp': {
                    'ENABLED': True,
                    'COLLECTION_INTERVAL': timedelta(minutes=1),
                    'METRICS': ['message_count', 'response_time', 'error_rate']
                },
                'telegram': {
                    'ENABLED': True,
                    'COLLECTION_INTERVAL': timedelta(minutes=1),
                    'METRICS': ['message_count', 'response_time', 'error_rate']
                },
                'messenger': {
                    'ENABLED': True,
                    'COLLECTION_INTERVAL': timedelta(minutes=1),
                    'METRICS': ['message_count', 'response_time', 'error_rate']
                },
                'instagram': {
                    'ENABLED': True,
                    'COLLECTION_INTERVAL': timedelta(minutes=1),
                    'METRICS': ['message_count', 'response_time', 'error_rate']
                }
            }
        }

        # Alert configuration
        alert_config = {
            'CRITICAL_THRESHOLD': 0.95,  # 95% resource usage
            'WARNING_THRESHOLD': 0.85,   # 85% resource usage
            'ALERT_EMAILS': env.list('ALERT_EMAILS', default=[]),
            'ALERT_INTERVAL': timedelta(hours=1),
            'API_ALERTS': {
                'whatsapp': {
                    'ERROR_RATE_THRESHOLD': 0.05,  # 5% error rate
                    'RESPONSE_TIME_THRESHOLD': 2.0,  # 2 seconds
                    'NOTIFICATION_CHANNELS': ['email', 'slack']
                },
                'telegram': {
                    'ERROR_RATE_THRESHOLD': 0.05,
                    'RESPONSE_TIME_THRESHOLD': 2.0,
                    'NOTIFICATION_CHANNELS': ['email', 'slack']
                },
                'messenger': {
                    'ERROR_RATE_THRESHOLD': 0.05,
                    'RESPONSE_TIME_THRESHOLD': 2.0,
                    'NOTIFICATION_CHANNELS': ['email', 'slack']
                },
                'instagram': {
                    'ERROR_RATE_THRESHOLD': 0.05,
                    'RESPONSE_TIME_THRESHOLD': 2.0,
                    'NOTIFICATION_CHANNELS': ['email', 'slack']
                }
            }
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
                'whatsapp_api': True,
                'telegram_api': True,
                'messenger_api': True,
                'instagram_api': True
            },
            'API_HEALTH_CHECKS': {
                'whatsapp': {
                    'ENDPOINT': '/api/whatsapp/health',
                    'TIMEOUT': 5,
                    'EXPECTED_STATUS': 200
                },
                'telegram': {
                    'ENDPOINT': '/api/telegram/health',
                    'TIMEOUT': 5,
                    'EXPECTED_STATUS': 200
                },
                'messenger': {
                    'ENDPOINT': '/api/messenger/health',
                    'TIMEOUT': 5,
                    'EXPECTED_STATUS': 200
                },
                'instagram': {
                    'ENDPOINT': '/api/instagram/health',
                    'TIMEOUT': 5,
                    'EXPECTED_STATUS': 200
                }
            }
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
        for api, api_config in config['METRICS_CONFIG']['API_METRICS'].items():
            if api_config['ENABLED']:
                logger.info(f"Metrics collection enabled for {api}")
        
    if config['ALERT_CONFIG']['ALERT_EMAILS']:
        logger.info(f"Alert system configured for {len(config['ALERT_CONFIG']['ALERT_EMAILS'])} recipients")
        for api, api_alerts in config['ALERT_CONFIG']['API_ALERTS'].items():
            logger.info(f"Alert system configured for {api} with channels: {api_alerts['NOTIFICATION_CHANNELS']}")
        
    return config
