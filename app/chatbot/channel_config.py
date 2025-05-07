from typing import Dict, Any
import environ

env = environ.Env()

class ChannelConfig:
    @staticmethod
    def get_config() -> Dict[str, Dict[str, Any]]:
        return {
            'whatsapp': {
                'retry_attempts': 3,
                'retry_delay': 5,  # segundos
                'batch_size': 50,
                'rate_limit': 20,  # mensajes por minuto
                'max_message_length': 4096,
                'media_supported': True,
                'fallback_channel': 'email',
                'metrics': {
                    'enabled': True,
                    'collection_interval': 60,  # segundos
                    'metrics_to_track': ['delivery_rate', 'response_time', 'error_rate']
                }
            },
            'telegram': {
                'retry_attempts': 3,
                'retry_delay': 3,
                'batch_size': 100,
                'rate_limit': 30,
                'max_message_length': 4096,
                'media_supported': True,
                'fallback_channel': 'email',
                'metrics': {
                    'enabled': True,
                    'collection_interval': 60,
                    'metrics_to_track': ['delivery_rate', 'response_time', 'error_rate']
                }
            },
            'messenger': {
                'retry_attempts': 2,
                'retry_delay': 2,
                'batch_size': 100,
                'rate_limit': 30,
                'max_message_length': 2000,
                'media_supported': True,
                'fallback_channel': 'email',
                'metrics': {
                    'enabled': True,
                    'collection_interval': 60,
                    'metrics_to_track': ['delivery_rate', 'response_time', 'error_rate']
                }
            },
            'instagram': {
                'retry_attempts': 1,
                'retry_delay': 10,
                'batch_size': 20,
                'rate_limit': 10,
                'max_message_length': 2200,
                'media_supported': True,
                'fallback_channel': 'email',
                'metrics': {
                    'enabled': True,
                    'collection_interval': 60,
                    'metrics_to_track': ['delivery_rate', 'response_time', 'error_rate']
                }
            },
            'slack': {
                'retry_attempts': 3,
                'retry_delay': 3,
                'batch_size': 100,
                'rate_limit': 100,
                'max_message_length': 40000,
                'media_supported': True,
                'fallback_channel': 'email',
                'metrics': {
                    'enabled': True,
                    'collection_interval': 60,
                    'metrics_to_track': ['delivery_rate', 'response_time', 'error_rate']
                }
            },
            'email': {
                'retry_attempts': 2,
                'retry_delay': 30,
                'batch_size': 100,
                'rate_limit': 100,
                'max_message_length': 100000,
                'media_supported': True,
                'metrics': {
                    'enabled': True,
                    'collection_interval': 60,
                    'metrics_to_track': ['delivery_rate', 'response_time', 'error_rate']
                }
            }
        }
