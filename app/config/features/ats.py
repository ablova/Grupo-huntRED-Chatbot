"""
Configuración específica para el módulo ATS.

Este módulo define la configuración específica para el módulo ATS,
heredando de la configuración base y añadiendo funcionalidades específicas.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
from ..base import BaseConfig, Environment

@dataclass
class ATSConfig(BaseConfig):
    """Configuración específica para el módulo ATS."""
    
    # Directorios específicos de ATS
    ats_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "ats")
    ats_data_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "ats_data")
    ats_logs_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "ats_logs")
    ats_models_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "ats_models")
    
    # Configuración de canales de comunicación
    channels: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'email': {
            'enabled': True,
            'priority': 1,
            'retry_attempts': 3,
            'timeout': 30,
            'subject_prefix': '[huntRED] ',
            'from_email': 'notifications@huntred.com'
        },
        'whatsapp': {
            'enabled': True,
            'priority': 2,
            'retry_attempts': 2,
            'timeout': 20,
            'api_key': '',
            'api_url': 'https://api.whatsapp.com/v1'
        },
        'x': {
            'enabled': True,
            'priority': 3,
            'retry_attempts': 2,
            'timeout': 20,
            'api_key': '',
            'api_secret': ''
        }
    })
    
    # Configuración de workflows
    workflows: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'candidate': {
            'enabled': True,
            'timeout': 3600,  # 1 hora
            'max_retries': 3,
            'notify_on_timeout': True
        },
        'client': {
            'enabled': True,
            'timeout': 7200,  # 2 horas
            'max_retries': 3,
            'notify_on_timeout': True
        },
        'assessment': {
            'enabled': True,
            'timeout': 1800,  # 30 minutos
            'max_retries': 2,
            'notify_on_timeout': True
        }
    })
    
    # Configuración de notificaciones
    notifications: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'templates': {
            'proposal': {
                'enabled': True,
                'channels': ['email', 'whatsapp'],
                'retry_interval': 300  # 5 minutos
            },
            'payment': {
                'enabled': True,
                'channels': ['email', 'whatsapp'],
                'retry_interval': 300
            },
            'opportunity': {
                'enabled': True,
                'channels': ['email', 'whatsapp', 'x'],
                'retry_interval': 300
            }
        },
        'scheduling': {
            'enabled': True,
            'max_retries': 3,
            'retry_interval': 300
        }
    })
    
    # Configuración de ML
    ml: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'models': {
            'matchmaking': {
                'enabled': True,
                'update_frequency': 86400,  # 24 horas
                'min_samples': 100,
                'confidence_threshold': 0.7
            },
            'transition': {
                'enabled': True,
                'update_frequency': 86400,
                'min_samples': 100,
                'confidence_threshold': 0.7
            },
            'market': {
                'enabled': True,
                'update_frequency': 86400,
                'min_samples': 100,
                'confidence_threshold': 0.7
            }
        },
        'training': {
            'batch_size': 32,
            'epochs': 100,
            'validation_split': 0.2,
            'early_stopping': True,
            'patience': 10
        }
    })
    
    # Configuración de caché
    cache: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': True,
        'backend': 'redis',
        'timeout': 300,
        'prefix': 'ats_',
        'max_entries': 1000
    })
    
    # Configuración de logging
    logging: Dict[str, Any] = field(default_factory=lambda: {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': 'ats.log',
        'max_size': 10485760,  # 10MB
        'backup_count': 5
    })
    
    # Configuración de seguridad
    security: Dict[str, Any] = field(default_factory=lambda: {
        'rate_limit': {
            'enabled': True,
            'requests': 100,
            'period': 60  # 1 minuto
        },
        'data_retention': {
            'enabled': True,
            'days': 365,
            'archive_enabled': True
        }
    })
    
    def __post_init__(self):
        """Validación post-inicialización."""
        super().__post_init__()
        self._validate_ats_paths()
        self._validate_channels()
        self._validate_workflows()
        self._validate_notifications()
        self._validate_ml()
    
    def _validate_ats_paths(self):
        """Valida los directorios específicos de ATS."""
        for path in [self.ats_dir, self.ats_data_dir, self.ats_logs_dir, self.ats_models_dir]:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
    
    def _validate_channels(self):
        """Valida la configuración de canales."""
        for channel, config in self.channels.items():
            if config['enabled']:
                if channel == 'email' and not config.get('from_email'):
                    raise ValueError(f"Email channel requires 'from_email' configuration")
                if channel in ['whatsapp', 'x'] and not config.get('api_key'):
                    raise ValueError(f"{channel} channel requires 'api_key' configuration")
    
    def _validate_workflows(self):
        """Valida la configuración de workflows."""
        for workflow, config in self.workflows.items():
            if config['enabled']:
                if config['timeout'] <= 0:
                    raise ValueError(f"Workflow {workflow} timeout must be positive")
                if config['max_retries'] < 0:
                    raise ValueError(f"Workflow {workflow} max_retries must be non-negative")
    
    def _validate_notifications(self):
        """Valida la configuración de notificaciones."""
        for template, config in self.notifications['templates'].items():
            if config['enabled']:
                if not config['channels']:
                    raise ValueError(f"Template {template} must specify at least one channel")
                if config['retry_interval'] <= 0:
                    raise ValueError(f"Template {template} retry_interval must be positive")
    
    def _validate_ml(self):
        """Valida la configuración de ML."""
        for model, config in self.ml['models'].items():
            if config['enabled']:
                if config['update_frequency'] <= 0:
                    raise ValueError(f"Model {model} update_frequency must be positive")
                if config['min_samples'] <= 0:
                    raise ValueError(f"Model {model} min_samples must be positive")
                if not 0 <= config['confidence_threshold'] <= 1:
                    raise ValueError(f"Model {model} confidence_threshold must be between 0 and 1")
    
    def get_channel_config(self, channel: str) -> Optional[Dict[str, Any]]:
        """Obtiene la configuración de un canal específico."""
        return self.channels.get(channel)
    
    def get_workflow_config(self, workflow: str) -> Optional[Dict[str, Any]]:
        """Obtiene la configuración de un workflow específico."""
        return self.workflows.get(workflow)
    
    def get_template_config(self, template: str) -> Optional[Dict[str, Any]]:
        """Obtiene la configuración de una plantilla específica."""
        return self.notifications['templates'].get(template)
    
    def get_model_config(self, model: str) -> Optional[Dict[str, Any]]:
        """Obtiene la configuración de un modelo específico."""
        return self.ml['models'].get(model)
    
    def is_channel_enabled(self, channel: str) -> bool:
        """Verifica si un canal está habilitado."""
        config = self.get_channel_config(channel)
        return bool(config and config['enabled'])
    
    def is_workflow_enabled(self, workflow: str) -> bool:
        """Verifica si un workflow está habilitado."""
        config = self.get_workflow_config(workflow)
        return bool(config and config['enabled'])
    
    def is_template_enabled(self, template: str) -> bool:
        """Verifica si una plantilla está habilitada."""
        config = self.get_template_config(template)
        return bool(config and config['enabled'])
    
    def is_model_enabled(self, model: str) -> bool:
        """Verifica si un modelo está habilitado."""
        config = self.get_model_config(model)
        return bool(config and config['enabled']) 