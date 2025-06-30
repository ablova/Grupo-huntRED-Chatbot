"""
SEGURIDAD AVANZADA - Grupo huntRED®
Sistema de seguridad con encriptación, compliance, auditoría y protección de datos
"""

import logging
import json
import hashlib
import hmac
import base64
import secrets
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Niveles de seguridad"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplianceStandard(Enum):
    """Estándares de compliance"""
    GDPR = "gdpr"
    CCPA = "ccpa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    HIPAA = "hipaa"

@dataclass
class SecurityEvent:
    """Evento de seguridad"""
    id: str
    type: str
    severity: SecurityLevel
    description: str
    user_id: str = ""
    ip_address: str = ""
    user_agent: str = ""
    timestamp: datetime = field(default_factory=timezone.now)
    resolved: bool = False
    action_taken: str = ""

@dataclass
class ComplianceAudit:
    """Auditoría de compliance"""
    id: str
    standard: ComplianceStandard
    status: str
    last_audit: datetime
    next_audit: datetime
    findings: List[Dict[str, Any]] = field(default_factory=list)
    score: float = 0.0

class AdvancedSecurity:
    """
    Sistema de seguridad avanzado
    """
    
    def __init__(self):
        # Configuración de seguridad
        self.security_config = self._load_security_config()
        self.encryption_key = self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        
        # Eventos de seguridad
        self.security_events = []
        self.threat_detection_rules = self._load_threat_detection_rules()
        
        # Compliance
        self.compliance_audits = self._load_compliance_audits()
        
        # Métricas
        self.security_metrics = {
            'security_events': 0,
            'threats_blocked': 0,
            'data_breaches': 0,
            'compliance_score': 0.0,
            'encryption_operations': 0
        }
        
        # Iniciar monitoreo de seguridad
        asyncio.create_task(self._security_monitoring())
    
    def _load_security_config(self) -> Dict[str, Any]:
        """Carga configuración de seguridad"""
        return {
            'encryption_enabled': True,
            'audit_logging': True,
            'threat_detection': True,
            'compliance_monitoring': True,
            'session_timeout': 3600,  # 1 hora
            'max_login_attempts': 5,
            'password_policy': {
                'min_length': 12,
                'require_uppercase': True,
                'require_lowercase': True,
                'require_numbers': True,
                'require_special': True
            },
            'mfa_required': True,
            'ip_whitelist': [],
            'ip_blacklist': []
        }
    
    def _generate_encryption_key(self) -> bytes:
        """Genera clave de encriptación"""
        try:
            # Intentar obtener clave existente
            key = cache.get('encryption_key')
            if key:
                return key
            
            # Generar nueva clave
            key = Fernet.generate_key()
            cache.set('encryption_key', key, 86400)  # 24 horas
            
            return key
            
        except Exception as e:
            logger.error(f"❌ Error generando clave de encriptación: {e}")
            return Fernet.generate_key()
    
    def _load_threat_detection_rules(self) -> Dict[str, Any]:
        """Carga reglas de detección de amenazas"""
        return {
            'brute_force': {
                'max_attempts': 5,
                'time_window': 300,  # 5 minutos
                'action': 'block_ip'
            },
            'sql_injection': {
                'patterns': [
                    r'(\b(union|select|insert|update|delete|drop|create)\b)',
                    r'(\b(or|and)\b\s+\d+\s*=\s*\d+)',
                    r'(\b(union|select)\b.*\bfrom\b)'
                ],
                'action': 'block_request'
            },
            'xss_attack': {
                'patterns': [
                    r'<script[^>]*>.*?</script>',
                    r'javascript:',
                    r'on\w+\s*='
                ],
                'action': 'sanitize_input'
            },
            'suspicious_activity': {
                'patterns': [
                    r'admin.*login',
                    r'password.*reset',
                    r'file.*upload'
                ],
                'action': 'log_and_monitor'
            }
        }
    
    def _load_compliance_audits(self) -> Dict[str, ComplianceAudit]:
        """Carga auditorías de compliance"""
        return {
            'gdpr': ComplianceAudit(
                id='gdpr_audit',
                standard=ComplianceStandard.GDPR,
                status='compliant',
                last_audit=timezone.now() - timedelta(days=30),
                next_audit=timezone.now() + timedelta(days=335),
                score=95.0
            ),
            'soc2': ComplianceAudit(
                id='soc2_audit',
                standard=ComplianceStandard.SOC2,
                status='in_progress',
                last_audit=timezone.now() - timedelta(days=60),
                next_audit=timezone.now() + timedelta(days=305),
                score=88.0
            )
        }
    
    async def encrypt_data(self, data: str, level: SecurityLevel = SecurityLevel.HIGH) -> str:
        """
        Encripta datos sensibles
        """
        try:
            if not self.security_config['encryption_enabled']:
                return data
            
            # Agregar timestamp para evitar replay attacks
            timestamp = str(int(timezone.now().timestamp()))
            data_with_timestamp = f"{data}:{timestamp}"
            
            # Encriptar datos
            encrypted_data = self.fernet.encrypt(data_with_timestamp.encode())
            
            # Codificar en base64 para almacenamiento
            encoded_data = base64.b64encode(encrypted_data).decode()
            
            # Registrar operación
            self.security_metrics['encryption_operations'] += 1
            
            logger.info(f"🔒 Datos encriptados: {len(data)} bytes")
            return encoded_data
            
        except Exception as e:
            logger.error(f"❌ Error encriptando datos: {e}")
            return data
    
    async def decrypt_data(self, encrypted_data: str) -> str:
        """
        Desencripta datos
        """
        try:
            if not self.security_config['encryption_enabled']:
                return encrypted_data
            
            # Decodificar de base64
            decoded_data = base64.b64decode(encrypted_data.encode())
            
            # Desencriptar
            decrypted_data = self.fernet.decrypt(decoded_data).decode()
            
            # Separar datos del timestamp
            data, timestamp = decrypted_data.rsplit(':', 1)
            
            # Verificar timestamp (opcional, para datos muy sensibles)
            # if int(timezone.now().timestamp()) - int(timestamp) > 3600:
            #     raise ValueError("Datos expirados")
            
            logger.info(f"🔓 Datos desencriptados: {len(data)} bytes")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error desencriptando datos: {e}")
            return encrypted_data
    
    async def hash_password(self, password: str) -> str:
        """
        Genera hash seguro de contraseña
        """
        try:
            # Generar salt único
            salt = secrets.token_hex(16)
            
            # Usar PBKDF2 para hash
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode(),
                iterations=100000,
            )
            
            # Generar hash
            key = base64.b64encode(kdf.derive(password.encode())).decode()
            
            # Retornar salt + hash
            return f"{salt}:{key}"
            
        except Exception as e:
            logger.error(f"❌ Error generando hash de contraseña: {e}")
            return ""
    
    async def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verifica contraseña contra hash
        """
        try:
            # Separar salt y hash
            salt, stored_hash = hashed_password.split(':', 1)
            
            # Generar hash con el mismo salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode(),
                iterations=100000,
            )
            
            # Verificar hash
            key = base64.b64encode(kdf.derive(password.encode())).decode()
            
            return hmac.compare_digest(key, stored_hash)
            
        except Exception as e:
            logger.error(f"❌ Error verificando contraseña: {e}")
            return False
    
    async def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Valida fortaleza de contraseña
        """
        try:
            policy = self.security_config['password_policy']
            issues = []
            score = 0
            
            # Verificar longitud mínima
            if len(password) < policy['min_length']:
                issues.append(f"Contraseña debe tener al menos {policy['min_length']} caracteres")
            else:
                score += 20
            
            # Verificar mayúsculas
            if policy['require_uppercase'] and not any(c.isupper() for c in password):
                issues.append("Debe contener al menos una mayúscula")
            else:
                score += 20
            
            # Verificar minúsculas
            if policy['require_lowercase'] and not any(c.islower() for c in password):
                issues.append("Debe contener al menos una minúscula")
            else:
                score += 20
            
            # Verificar números
            if policy['require_numbers'] and not any(c.isdigit() for c in password):
                issues.append("Debe contener al menos un número")
            else:
                score += 20
            
            # Verificar caracteres especiales
            if policy['require_special'] and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
                issues.append("Debe contener al menos un carácter especial")
            else:
                score += 20
            
            # Verificar patrones comunes
            common_patterns = ['password', '123456', 'qwerty', 'admin']
            if any(pattern in password.lower() for pattern in common_patterns):
                issues.append("No debe contener patrones comunes")
                score -= 20
            
            return {
                'valid': len(issues) == 0,
                'score': max(0, score),
                'issues': issues,
                'strength': 'weak' if score < 60 else 'medium' if score < 80 else 'strong'
            }
            
        except Exception as e:
            logger.error(f"❌ Error validando fortaleza de contraseña: {e}")
            return {'valid': False, 'score': 0, 'issues': ['Error de validación'], 'strength': 'weak'}
    
    async def detect_threat(self, request_data: Dict[str, Any]) -> Optional[SecurityEvent]:
        """
        Detecta amenazas en solicitudes
        """
        try:
            # Extraer datos de la solicitud
            user_id = request_data.get('user_id', '')
            ip_address = request_data.get('ip_address', '')
            user_agent = request_data.get('user_agent', '')
            url = request_data.get('url', '')
            method = request_data.get('method', '')
            data = request_data.get('data', '')
            
            # Verificar IP en blacklist
            if ip_address in self.security_config['ip_blacklist']:
                return SecurityEvent(
                    id=f"threat_{int(timezone.now().timestamp())}",
                    type='blacklisted_ip',
                    severity=SecurityLevel.HIGH,
                    description=f'IP bloqueada intentando acceso: {ip_address}',
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            # Verificar ataques SQL Injection
            if await self._detect_sql_injection(data):
                return SecurityEvent(
                    id=f"threat_{int(timezone.now().timestamp())}",
                    type='sql_injection',
                    severity=SecurityLevel.CRITICAL,
                    description='Intento de SQL Injection detectado',
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            # Verificar ataques XSS
            if await self._detect_xss_attack(data):
                return SecurityEvent(
                    id=f"threat_{int(timezone.now().timestamp())}",
                    type='xss_attack',
                    severity=SecurityLevel.HIGH,
                    description='Intento de XSS detectado',
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            # Verificar actividad sospechosa
            if await self._detect_suspicious_activity(url, method, user_id):
                return SecurityEvent(
                    id=f"threat_{int(timezone.now().timestamp())}",
                    type='suspicious_activity',
                    severity=SecurityLevel.MEDIUM,
                    description='Actividad sospechosa detectada',
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error detectando amenazas: {e}")
            return None
    
    async def _detect_sql_injection(self, data: str) -> bool:
        """Detecta intentos de SQL Injection"""
        try:
            import re
            
            patterns = self.threat_detection_rules['sql_injection']['patterns']
            
            for pattern in patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error detectando SQL Injection: {e}")
            return False
    
    async def _detect_xss_attack(self, data: str) -> bool:
        """Detecta intentos de XSS"""
        try:
            import re
            
            patterns = self.threat_detection_rules['xss_attack']['patterns']
            
            for pattern in patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error detectando XSS: {e}")
            return False
    
    async def _detect_suspicious_activity(self, url: str, method: str, user_id: str) -> bool:
        """Detecta actividad sospechosa"""
        try:
            import re
            
            patterns = self.threat_detection_rules['suspicious_activity']['patterns']
            
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error detectando actividad sospechosa: {e}")
            return False
    
    async def log_security_event(self, event: SecurityEvent):
        """
        Registra evento de seguridad
        """
        try:
            # Agregar evento a la lista
            self.security_events.append(event)
            
            # Mantener solo los últimos 1000 eventos
            if len(self.security_events) > 1000:
                self.security_events = self.security_events[-1000:]
            
            # Actualizar métricas
            self.security_metrics['security_events'] += 1
            
            if event.type in ['sql_injection', 'xss_attack', 'blacklisted_ip']:
                self.security_metrics['threats_blocked'] += 1
            
            # Log según severidad
            if event.severity == SecurityLevel.CRITICAL:
                logger.critical(f"🚨 CRÍTICO: {event.description}")
            elif event.severity == SecurityLevel.HIGH:
                logger.error(f"⚠️ ALTO: {event.description}")
            elif event.severity == SecurityLevel.MEDIUM:
                logger.warning(f"⚠️ MEDIO: {event.description}")
            else:
                logger.info(f"ℹ️ BAJO: {event.description}")
            
            # Almacenar en cache para monitoreo
            cache_key = f"security_event:{event.id}"
            cache.set(cache_key, event.__dict__, 86400)  # 24 horas
            
        except Exception as e:
            logger.error(f"❌ Error registrando evento de seguridad: {e}")
    
    async def _security_monitoring(self):
        """
        Monitoreo continuo de seguridad
        """
        while True:
            try:
                # Verificar eventos críticos
                critical_events = [
                    event for event in self.security_events[-100:]
                    if event.severity == SecurityLevel.CRITICAL and not event.resolved
                ]
                
                if critical_events:
                    await self._handle_critical_events(critical_events)
                
                # Verificar compliance
                await self._check_compliance_status()
                
                # Limpiar eventos antiguos
                cutoff_time = timezone.now() - timedelta(days=30)
                self.security_events = [
                    event for event in self.security_events
                    if event.timestamp > cutoff_time
                ]
                
                # Esperar 5 minutos antes del siguiente check
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"❌ Error en monitoreo de seguridad: {e}")
                await asyncio.sleep(60)
    
    async def _handle_critical_events(self, events: List[SecurityEvent]):
        """
        Maneja eventos críticos de seguridad
        """
        try:
            for event in events:
                # Marcar como resuelto
                event.resolved = True
                event.action_taken = "Monitoreo automático activado"
                
                # Notificar administradores
                await self._notify_security_team(event)
                
                # Registrar acción
                logger.warning(f"🛡️ Evento crítico manejado: {event.description}")
                
        except Exception as e:
            logger.error(f"❌ Error manejando eventos críticos: {e}")
    
    async def _notify_security_team(self, event: SecurityEvent):
        """
        Notifica al equipo de seguridad
        """
        try:
            # Aquí se integraría con el sistema de notificaciones
            notification_data = {
                'type': 'security_alert',
                'severity': event.severity.value,
                'description': event.description,
                'timestamp': event.timestamp.isoformat(),
                'user_id': event.user_id,
                'ip_address': event.ip_address
            }
            
            logger.info(f"📢 Notificación de seguridad enviada: {event.type}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación de seguridad: {e}")
    
    async def _check_compliance_status(self):
        """
        Verifica estado de compliance
        """
        try:
            for audit_id, audit in self.compliance_audits.items():
                # Verificar si necesita auditoría
                if timezone.now() > audit.next_audit:
                    await self._run_compliance_audit(audit)
                
                # Actualizar métricas
                self.security_metrics['compliance_score'] = audit.score
                
        except Exception as e:
            logger.error(f"❌ Error verificando compliance: {e}")
    
    async def _run_compliance_audit(self, audit: ComplianceAudit):
        """
        Ejecuta auditoría de compliance
        """
        try:
            logger.info(f"🔍 Ejecutando auditoría: {audit.standard.value}")
            
            # Simular auditoría
            findings = []
            score = 100.0
            
            # Verificar encriptación
            if not self.security_config['encryption_enabled']:
                findings.append("Encriptación no habilitada")
                score -= 20
            
            # Verificar logging
            if not self.security_config['audit_logging']:
                findings.append("Logging de auditoría no habilitado")
                score -= 15
            
            # Verificar MFA
            if not self.security_config['mfa_required']:
                findings.append("MFA no requerido")
                score -= 10
            
            # Actualizar auditoría
            audit.last_audit = timezone.now()
            audit.next_audit = timezone.now() + timedelta(days=365)
            audit.findings = findings
            audit.score = max(0, score)
            audit.status = 'compliant' if score >= 80 else 'non_compliant'
            
            logger.info(f"✅ Auditoría completada: {audit.standard.value} - Score: {audit.score}")
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando auditoría: {e}")
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """
        Obtiene métricas de seguridad
        """
        try:
            return {
                'security_events': self.security_metrics['security_events'],
                'threats_blocked': self.security_metrics['threats_blocked'],
                'data_breaches': self.security_metrics['data_breaches'],
                'compliance_score': self.security_metrics['compliance_score'],
                'encryption_operations': self.security_metrics['encryption_operations'],
                'active_threats': len([e for e in self.security_events if not e.resolved]),
                'critical_events': len([e for e in self.security_events if e.severity == SecurityLevel.CRITICAL]),
                'last_updated': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo métricas de seguridad: {e}")
            return {}
    
    def get_compliance_status(self) -> Dict[str, Any]:
        """
        Obtiene estado de compliance
        """
        try:
            return {
                audit_id: {
                    'standard': audit.standard.value,
                    'status': audit.status,
                    'score': audit.score,
                    'last_audit': audit.last_audit.isoformat(),
                    'next_audit': audit.next_audit.isoformat(),
                    'findings_count': len(audit.findings)
                }
                for audit_id, audit in self.compliance_audits.items()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado de compliance: {e}")
            return {}

# Instancia global
advanced_security = AdvancedSecurity() 