"""
Dispatcher central para mensajes de WhatsApp huntRED®
Enruta mensajes entre sistemas ATS y Payroll según contexto
"""
import logging
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from app.ats.models import Company
from app.payroll.models import PayrollCompany, PayrollEmployee
from app.core.models import User, ConversationSession

logger = logging.getLogger(__name__)

# Palabras clave para detección de sistema
PAYROLL_KEYWORDS = [
    'nómina', 'nomina', 'payroll', 'sueldo', 'salario', 'pago', 'recibo',
    'asistencia', 'entrada', 'salida', 'checkin', 'checkout', 'hr', 'rh',
    'vacaciones', 'permiso', 'incapacidad', 'finiquito', 'liquidación'
]

ATS_KEYWORDS = [
    'candidato', 'vacante', 'puesto', 'entrevista', 'cv', 'reclutamiento',
    'oferta', 'contratación', 'talent', 'acquisition', 'ats', 'recruiting',
    'sourcing', 'aplicación', 'aplicar'
]

# Prefijos explícitos para forzar sistema
PAYROLL_PREFIXES = ['#nomina', '#payroll', '#rh', '#hr']
ATS_PREFIXES = ['#ats', '#vacantes', '#recruiting']


class WhatsAppMessageDispatcher:
    """
    Dispatcher central para mensajes de WhatsApp.
    Determina si un mensaje debe ser procesado por ATS o Payroll
    basándose en el contexto, prefijos, rol del usuario, etc.
    """
    
    def __init__(self):
        # Cache de handlers para evitar reinicializaciones
        self.ats_handlers = {}  # Map de empresas a sus handlers ATS
        self.payroll_handlers = {}  # Map de empresas a sus handlers Payroll
        
        # Cache de sesiones activas
        self.active_sessions = {}  # Map de números de teléfono a sesiones
        
        # Tiempo de expiración de sesiones en minutos
        self.session_timeout = 30
    
    def dispatch(self, from_number: str, message: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Determina el sistema y empresa correctos para procesar el mensaje
        y lo envía al handler correspondiente
        
        Args:
            from_number: Número de teléfono remitente
            message: Texto del mensaje
            metadata: Metadatos adicionales (tipo mensaje, adjuntos, etc.)
            
        Returns:
            Respuesta del sistema destino
        """
        try:
            logger.info(f"Dispatching message from {from_number}: '{message[:50]}...'")
            
            # Normalizar número
            phone = self._normalize_phone(from_number)
            
            # 1. Identificar la empresa y contexto
            company, system = self._identify_company_and_system(phone, message, metadata)
            
            if not company:
                return self._generate_company_not_found_response()
            
            # 2. Actualizar o crear sesión
            session = self._update_session(phone, company, system)
            
            # 3. Enrutar al handler apropiado
            if system == "payroll":
                return self._route_to_payroll(company, phone, message, metadata, session)
            else:
                return self._route_to_ats(company, phone, message, metadata, session)
                
        except Exception as e:
            logger.error(f"Error dispatching message: {str(e)}")
            return {
                "success": False,
                "message": "Error interno procesando tu mensaje. Por favor intenta nuevamente.",
                "error": str(e)
            }
    
    def _normalize_phone(self, phone: str) -> str:
        """Normaliza formato de número telefónico"""
        # Eliminar formato WhatsApp
        phone = phone.replace('@c.us', '').replace('@g.us', '')
        
        # Asegurar formato internacional
        if not phone.startswith('+'):
            # Asumir México si no tiene código país
            if phone.startswith('52'):
                phone = f"+{phone}"
            else:
                phone = f"+52{phone}"
                
        return phone
    
    def _identify_company_and_system(self, phone: str, message: str, metadata: Dict[str, Any]) -> Tuple[Any, str]:
        """
        Identifica la empresa y el sistema destino (ATS o Payroll)
        basándose en el contenido del mensaje y contexto
        """
        # Verificar prefijos explícitos primero
        system = self._check_explicit_prefixes(message)
        if system:
            # Si hay prefijo explícito, buscar en el sistema correspondiente
            if system == "payroll":
                company = self._find_payroll_company(phone)
                if company:
                    return company, system
            else:
                company = self._find_ats_company(phone)
                if company:
                    return company, system
        
        # Verificar sesión existente
        session = self.active_sessions.get(phone)
        if session and not self._is_session_expired(session):
            # Continuar con la misma empresa y sistema de la sesión
            return session['company'], session['system']
        
        # Buscar usuario en ambos sistemas
        payroll_company = self._find_payroll_company(phone)
        ats_company = self._find_ats_company(phone)
        
        if payroll_company and not ats_company:
            return payroll_company, "payroll"
        elif ats_company and not payroll_company:
            return ats_company, "ats"
        elif payroll_company and ats_company:
            # Usuario existe en ambos sistemas, analizar mensaje
            system = self._analyze_message_content(message)
            if system == "payroll":
                return payroll_company, system
            else:
                return ats_company, system
        else:
            # Usuario no encontrado en ningún sistema
            return None, None
    
    def _check_explicit_prefixes(self, message: str) -> Optional[str]:
        """Verifica si el mensaje tiene prefijos explícitos para un sistema"""
        lower_message = message.lower()
        
        for prefix in PAYROLL_PREFIXES:
            if lower_message.startswith(prefix):
                return "payroll"
                
        for prefix in ATS_PREFIXES:
            if lower_message.startswith(prefix):
                return "ats"
                
        return None
    
    def _analyze_message_content(self, message: str) -> str:
        """Analiza contenido del mensaje para determinar sistema destino"""
        lower_message = message.lower()
        
        payroll_score = 0
        ats_score = 0
        
        # Contar palabras clave de cada sistema
        for keyword in PAYROLL_KEYWORDS:
            if keyword in lower_message:
                payroll_score += 1
                
        for keyword in ATS_KEYWORDS:
            if keyword in lower_message:
                ats_score += 1
        
        # Decisión basada en puntaje
        if payroll_score > ats_score:
            return "payroll"
        elif ats_score > payroll_score:
            return "ats"
        else:
            # Por defecto, ir a ATS
            return "ats"
    
    def _find_payroll_company(self, phone: str) -> Optional[PayrollCompany]:
        """Busca una empresa Payroll por número de teléfono de empleado"""
        try:
            # Buscar empleado por teléfono
            employee = PayrollEmployee.objects.filter(
                Q(phone__contains=phone) | Q(whatsapp_phone__contains=phone)
            ).select_related('company').first()
            
            if employee:
                return employee.company
                
            # Buscar empresa directamente
            company = PayrollCompany.objects.filter(
                Q(whatsapp_phone_number__contains=phone) | 
                Q(contact_phone__contains=phone)
            ).first()
            
            return company
            
        except Exception as e:
            logger.error(f"Error finding payroll company: {str(e)}")
            return None
    
    def _find_ats_company(self, phone: str) -> Optional[Company]:
        """Busca una empresa ATS por número de teléfono"""
        try:
            # Buscar empresa por teléfono
            company = Company.objects.filter(
                Q(whatsapp_phone__contains=phone) |
                Q(contact_phone__contains=phone)
            ).first()
            
            # Si no encontramos empresa, buscar usuarios
            if not company:
                user = User.objects.filter(
                    Q(phone__contains=phone) | Q(whatsapp_phone__contains=phone)
                ).first()
                
                if user and hasattr(user, 'company'):
                    company = user.company
            
            return company
            
        except Exception as e:
            logger.error(f"Error finding ATS company: {str(e)}")
            return None
    
    def _update_session(self, phone: str, company: Any, system: str) -> Dict[str, Any]:
        """Actualiza o crea sesión activa para el número"""
        session = {
            'phone': phone,
            'company': company,
            'system': system,
            'last_activity': datetime.now(),
            'message_count': 1
        }
        
        # Si ya existe, incrementar contador y actualizar
        if phone in self.active_sessions:
            old_session = self.active_sessions[phone]
            session['message_count'] = old_session['message_count'] + 1
            
            # Mantener contexto adicional si existe
            if 'context' in old_session:
                session['context'] = old_session['context']
        
        self.active_sessions[phone] = session
        return session
    
    def _is_session_expired(self, session: Dict[str, Any]) -> bool:
        """Verifica si la sesión ha expirado"""
        now = datetime.now()
        last_activity = session['last_activity']
        delta = now - last_activity
        
        # Expirar después de X minutos de inactividad
        return delta.total_seconds() / 60 > self.session_timeout
    
    def _route_to_payroll(self, company: PayrollCompany, phone: str, 
                         message: str, metadata: Dict[str, Any], 
                         session: Dict[str, Any]) -> Dict[str, Any]:
        """Enruta mensaje al sistema Payroll"""
        from app.payroll.services.unified_whatsapp_service import UnifiedWhatsAppService
        
        # Obtener o crear handler para esta empresa
        if company.id in self.payroll_handlers:
            handler = self.payroll_handlers[company.id]
        else:
            handler = UnifiedWhatsAppService(company)
            self.payroll_handlers[company.id] = handler
        
        # Procesar mensaje
        message_type = metadata.get('type', 'text') if metadata else 'text'
        response = handler.process_message(phone, message, message_type)
        
        return response
    
    def _route_to_ats(self, company: Any, phone: str, 
                     message: str, metadata: Dict[str, Any], 
                     session: Dict[str, Any]) -> Dict[str, Any]:
        """Enruta mensaje al sistema ATS"""
        from app.ats.services.whatsapp_service import WhatsAppATSService
        
        # Obtener o crear handler para esta empresa
        if company.id in self.ats_handlers:
            handler = self.ats_handlers[company.id]
        else:
            handler = WhatsAppATSService(company)
            self.ats_handlers[company.id] = handler
        
        # Procesar mensaje
        message_type = metadata.get('type', 'text') if metadata else 'text'
        response = handler.process_message(phone, message, message_type)
        
        return response
    
    def _generate_company_not_found_response(self) -> Dict[str, Any]:
        """Genera respuesta para usuarios no identificados"""
        return {
            "success": False,
            "message": """❌ No podemos identificar tu empresa o cuenta.

Para utilizar nuestros servicios de WhatsApp, debes estar registrado en nuestro sistema.

Por favor, contacta con soporte si crees que esto es un error."""
        }


# Singleton para uso global
dispatcher = WhatsAppMessageDispatcher()
