"""
🏢 Ejemplo Práctico: Configuración Multi-Tenant HuntRED® v2

Este archivo muestra cómo funciona la configuración multi-tenant en la práctica,
con ejemplos reales de configuraciones por Business Unit y por empresa cliente.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class BusinessUnitCode(Enum):
    """Códigos de Business Units"""
    HUNTRED_EXECUTIVE = "huntRED_executive"
    HUNTRED = "huntRED"
    HUNTU = "huntU"
    AMIGRO = "amigro"


@dataclass
class MultiTenantConfig:
    """Configuración multi-tenant resuelta"""
    whatsapp: Dict[str, Any]
    smtp: Dict[str, Any]
    gpt: Dict[str, Any]
    verification: Dict[str, Any]
    video: Dict[str, Any]
    notifications: Dict[str, Any]


class MultiTenantConfigResolver:
    """
    Resuelve configuraciones multi-tenant con precedencia:
    1. Empresa Cliente (más alta)
    2. Business Unit
    3. Configuración por defecto
    """
    
    def __init__(self):
        self.bu_configs = self._load_business_unit_configs()
        self.default_config = self._load_default_config()
    
    def _load_business_unit_configs(self) -> Dict[str, Dict[str, Any]]:
        """Configuraciones específicas por Business Unit"""
        return {
            BusinessUnitCode.HUNTRED_EXECUTIVE.value: {
                "whatsapp": {
                    "api_key": "EXECUTIVE_WHATSAPP_KEY",
                    "phone_number": "+5215512345678",
                    "meta_verified": True,
                    "templates": {
                        "welcome": "Bienvenido a huntRED® Executive Search",
                        "interview": "Su entrevista ejecutiva está programada",
                        "offer": "Oferta de posición ejecutiva"
                    },
                    "rate_limit": 1000  # Mensajes por día
                },
                "smtp": {
                    "host": "smtp.huntred.com",
                    "port": 587,
                    "username": "executive@huntred.com",
                    "password": "EXECUTIVE_SMTP_PASSWORD",
                    "from_email": "executive@huntred.com",
                    "from_name": "huntRED® Executive Search",
                    "use_tls": True
                },
                "gpt": {
                    "api_key": "EXECUTIVE_GPT4_KEY",
                    "model": "gpt-4-turbo",
                    "max_tokens": 4000,
                    "temperature": 0.3,
                    "system_prompt": "Eres un consultor ejecutivo especializado en posiciones C-level."
                },
                "verification": {
                    "provider": "first_advantage",
                    "api_key": "FIRST_ADVANTAGE_PREMIUM_KEY",
                    "level": "executive",
                    "checks": ["criminal", "employment", "education", "reference", "credit"]
                },
                "video": {
                    "platform": "zoom_pro",
                    "api_key": "ZOOM_PRO_KEY",
                    "features": ["recording", "transcription", "breakout_rooms"]
                },
                "notifications": {
                    "channels": ["whatsapp", "email", "sms"],
                    "priority": "high",
                    "escalation": True
                }
            },
            
            BusinessUnitCode.HUNTRED.value: {
                "whatsapp": {
                    "api_key": "HUNTRED_WHATSAPP_KEY",
                    "phone_number": "+5215587654321",
                    "meta_verified": True,
                    "templates": {
                        "welcome": "Bienvenido a huntRED® - Reclutamiento Profesional",
                        "interview": "Su entrevista está programada",
                        "offer": "Oferta de trabajo"
                    },
                    "rate_limit": 500
                },
                "smtp": {
                    "host": "smtp.huntred.com",
                    "port": 587,
                    "username": "reclutamiento@huntred.com",
                    "password": "HUNTRED_SMTP_PASSWORD",
                    "from_email": "reclutamiento@huntred.com",
                    "from_name": "huntRED® Reclutamiento",
                    "use_tls": True
                },
                "gpt": {
                    "api_key": "HUNTRED_GPT35_KEY",
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 2000,
                    "temperature": 0.4,
                    "system_prompt": "Eres un consultor de reclutamiento profesional."
                },
                "verification": {
                    "provider": "sterling",
                    "api_key": "STERLING_STANDARD_KEY",
                    "level": "standard",
                    "checks": ["criminal", "employment", "education"]
                },
                "video": {
                    "platform": "google_meet",
                    "api_key": "GOOGLE_MEET_KEY",
                    "features": ["recording", "screen_share"]
                },
                "notifications": {
                    "channels": ["whatsapp", "email"],
                    "priority": "medium",
                    "escalation": False
                }
            },
            
            BusinessUnitCode.HUNTU.value: {
                "whatsapp": {
                    "api_key": "HUNTU_WHATSAPP_KEY",
                    "phone_number": "+5215598765432",
                    "meta_verified": True,
                    "templates": {
                        "welcome": "¡Hola! Bienvenido a huntU - Talento Universitario 🎓",
                        "interview": "Tu entrevista está programada ¡Éxito! 🚀",
                        "offer": "¡Felicidades! Tienes una oferta de trabajo 🎉"
                    },
                    "rate_limit": 300
                },
                "smtp": {
                    "host": "smtp.huntred.com",
                    "port": 587,
                    "username": "estudiantes@huntred.com",
                    "password": "HUNTU_SMTP_PASSWORD",
                    "from_email": "estudiantes@huntred.com",
                    "from_name": "huntU - Talento Universitario",
                    "use_tls": True
                },
                "gpt": {
                    "api_key": "HUNTU_GPT35_KEY",
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 1500,
                    "temperature": 0.5,
                    "system_prompt": "Eres un mentor para estudiantes y recién graduados universitarios."
                },
                "verification": {
                    "provider": "basic_verification",
                    "api_key": "BASIC_VERIFICATION_KEY",
                    "level": "basic",
                    "checks": ["education", "identity"]
                },
                "video": {
                    "platform": "google_meet",
                    "api_key": "GOOGLE_MEET_BASIC_KEY",
                    "features": ["recording"]
                },
                "notifications": {
                    "channels": ["whatsapp", "email"],
                    "priority": "medium",
                    "escalation": False
                }
            },
            
            BusinessUnitCode.AMIGRO.value: {
                "whatsapp": {
                    "api_key": "AMIGRO_WHATSAPP_KEY",
                    "phone_number": "+5215556789012",
                    "meta_verified": True,
                    "templates": {
                        "welcome": "¡Bienvenido a Amigro! 🌎 Oportunidades para migrantes",
                        "interview": "Tu entrevista está programada 💼",
                        "offer": "¡Tienes una oportunidad de trabajo! 🎯",
                        "group_message": "Mensaje grupal para la comunidad migrante"
                    },
                    "rate_limit": 1000,  # Mayor límite para comunicación masiva
                    "group_messaging": True
                },
                "smtp": {
                    "host": "smtp.huntred.com",
                    "port": 587,
                    "username": "migrantes@huntred.com",
                    "password": "AMIGRO_SMTP_PASSWORD",
                    "from_email": "migrantes@huntred.com",
                    "from_name": "Amigro - Oportunidades Migrantes",
                    "use_tls": True
                },
                "gpt": {
                    "api_key": "AMIGRO_GPT35_KEY",
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 1500,
                    "temperature": 0.6,
                    "system_prompt": "Eres un consejero especializado en migración y oportunidades laborales para migrantes."
                },
                "verification": {
                    "provider": "migration_verification",
                    "api_key": "MIGRATION_VERIFICATION_KEY",
                    "level": "migration",
                    "checks": ["identity", "migration_status", "basic_criminal"]
                },
                "video": {
                    "platform": "google_meet",
                    "api_key": "GOOGLE_MEET_BASIC_KEY",
                    "features": ["recording", "translation"]
                },
                "notifications": {
                    "channels": ["whatsapp", "email", "sms"],
                    "priority": "high",
                    "escalation": True,
                    "group_notifications": True
                }
            }
        }
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto"""
        return {
            "whatsapp": {
                "api_key": "DEFAULT_WHATSAPP_KEY",
                "phone_number": "+5215500000000",
                "meta_verified": False,
                "templates": {
                    "welcome": "Bienvenido a huntRED®",
                    "interview": "Su entrevista está programada",
                    "offer": "Oferta de trabajo"
                },
                "rate_limit": 100
            },
            "smtp": {
                "host": "smtp.huntred.com",
                "port": 587,
                "username": "info@huntred.com",
                "password": "DEFAULT_SMTP_PASSWORD",
                "from_email": "info@huntred.com",
                "from_name": "huntRED®",
                "use_tls": True
            },
            "gpt": {
                "api_key": "DEFAULT_GPT_KEY",
                "model": "gpt-3.5-turbo",
                "max_tokens": 1000,
                "temperature": 0.5,
                "system_prompt": "Eres un asistente de recursos humanos."
            },
            "verification": {
                "provider": "basic",
                "api_key": "BASIC_VERIFICATION_KEY",
                "level": "basic",
                "checks": ["identity"]
            },
            "video": {
                "platform": "basic",
                "api_key": "BASIC_VIDEO_KEY",
                "features": ["recording"]
            },
            "notifications": {
                "channels": ["email"],
                "priority": "low",
                "escalation": False
            }
        }
    
    def resolve_config(self, 
                      business_unit: str, 
                      company_id: Optional[int] = None,
                      client_config: Optional[Dict[str, Any]] = None) -> MultiTenantConfig:
        """
        Resuelve la configuración final con precedencia:
        1. Configuración de empresa cliente (más alta)
        2. Configuración de Business Unit
        3. Configuración por defecto
        """
        
        # 1. Configuración base (por defecto)
        final_config = self.default_config.copy()
        
        # 2. Aplicar configuración de Business Unit
        if business_unit in self.bu_configs:
            bu_config = self.bu_configs[business_unit]
            for service, config in bu_config.items():
                if service in final_config:
                    final_config[service].update(config)
                else:
                    final_config[service] = config
        
        # 3. Aplicar configuración de empresa cliente (prioridad más alta)
        if client_config:
            for service, config in client_config.items():
                if service in final_config:
                    final_config[service].update(config)
                else:
                    final_config[service] = config
        
        return MultiTenantConfig(
            whatsapp=final_config.get("whatsapp", {}),
            smtp=final_config.get("smtp", {}),
            gpt=final_config.get("gpt", {}),
            verification=final_config.get("verification", {}),
            video=final_config.get("video", {}),
            notifications=final_config.get("notifications", {})
        )


# Ejemplos de uso práctico

def ejemplo_huntred_executive():
    """Ejemplo: Configuración para huntRED® Executive"""
    resolver = MultiTenantConfigResolver()
    
    config = resolver.resolve_config(
        business_unit=BusinessUnitCode.HUNTRED_EXECUTIVE.value
    )
    
    print("🏢 huntRED® Executive Configuration:")
    print(f"WhatsApp: {config.whatsapp['phone_number']}")
    print(f"SMTP: {config.smtp['from_email']}")
    print(f"GPT Model: {config.gpt['model']}")
    print(f"Verification Level: {config.verification['level']}")
    print()


def ejemplo_huntu_con_cliente():
    """Ejemplo: huntU con configuración específica de empresa cliente"""
    resolver = MultiTenantConfigResolver()
    
    # Configuración específica de una universidad cliente
    client_config = {
        "smtp": {
            "host": "smtp.universidad.edu.mx",
            "username": "reclutamiento@universidad.edu.mx",
            "from_email": "reclutamiento@universidad.edu.mx",
            "from_name": "Universidad XYZ - Bolsa de Trabajo"
        },
        "notifications": {
            "channels": ["email", "whatsapp"],
            "custom_templates": {
                "welcome": "Bienvenido al programa de empleabilidad de Universidad XYZ"
            }
        }
    }
    
    config = resolver.resolve_config(
        business_unit=BusinessUnitCode.HUNTU.value,
        client_config=client_config
    )
    
    print("🎓 huntU + Universidad Cliente Configuration:")
    print(f"SMTP: {config.smtp['from_email']}")
    print(f"From Name: {config.smtp['from_name']}")
    print(f"Channels: {config.notifications['channels']}")
    print()


def ejemplo_amigro_masivo():
    """Ejemplo: Amigro con comunicación masiva"""
    resolver = MultiTenantConfigResolver()
    
    config = resolver.resolve_config(
        business_unit=BusinessUnitCode.AMIGRO.value
    )
    
    print("🌎 Amigro Configuration:")
    print(f"WhatsApp: {config.whatsapp['phone_number']}")
    print(f"Rate Limit: {config.whatsapp['rate_limit']} msg/day")
    print(f"Group Messaging: {config.whatsapp.get('group_messaging', False)}")
    print(f"Verification: {config.verification['provider']}")
    print()


def ejemplo_empresa_nomina():
    """Ejemplo: Empresa cliente con servicio de nómina"""
    resolver = MultiTenantConfigResolver()
    
    # Configuración específica de empresa que contrata servicios de nómina
    payroll_client_config = {
        "smtp": {
            "host": "smtp.empresacliente.com",
            "username": "nomina@empresacliente.com",
            "from_email": "nomina@empresacliente.com",
            "from_name": "Empresa Cliente - Nómina"
        },
        "whatsapp": {
            "api_key": "CLIENT_WHATSAPP_KEY",
            "phone_number": "+5215599887766",
            "templates": {
                "payroll_ready": "Su nómina está lista para revisión",
                "tax_reminder": "Recordatorio: Declaración de impuestos"
            }
        },
        "notifications": {
            "channels": ["whatsapp", "email"],
            "recipients": ["rh@empresacliente.com", "nomina@empresacliente.com"],
            "schedule": {
                "payroll_notifications": "bi-weekly",
                "tax_reminders": "monthly"
            }
        }
    }
    
    config = resolver.resolve_config(
        business_unit=BusinessUnitCode.HUNTRED.value,  # Usando huntRED® para servicios de nómina
        client_config=payroll_client_config
    )
    
    print("💼 Empresa Cliente - Servicio de Nómina:")
    print(f"SMTP: {config.smtp['from_email']}")
    print(f"WhatsApp: {config.whatsapp['phone_number']}")
    print(f"Channels: {config.notifications['channels']}")
    print()


if __name__ == "__main__":
    print("🏢 Ejemplos de Configuración Multi-Tenant HuntRED® v2\n")
    
    ejemplo_huntred_executive()
    ejemplo_huntu_con_cliente()
    ejemplo_amigro_masivo()
    ejemplo_empresa_nomina()
    
    print("✅ Todos los ejemplos ejecutados correctamente")
    print("\nLa arquitectura multi-tenant permite:")
    print("• Configuraciones específicas por Business Unit")
    print("• Configuraciones personalizadas por empresa cliente")
    print("• Resolución automática con precedencia")
    print("• Escalabilidad para múltiples tenants")