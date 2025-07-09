"""
Servicio unificado de WhatsApp huntRED® para Payroll
Implementación consolidada para sistemas de nómina
"""
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, date, timedelta
from decimal import Decimal

from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError

from ..models import PayrollCompany, PayrollEmployee, AttendanceRecord, EmployeeRequest, PayrollPeriod
from .. import PAYROLL_ROLES, ATTENDANCE_STATUSES, REQUEST_STATUSES
from .severance_calculation_service import SeveranceCalculationService
from .workplace_climate_service import WorkplaceClimateService

# Importamos soporte de internacionalización
from ..i18n import get_message, get_button_text, detect_language, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

# Importamos la clase base del menú ATS para reusabilidad
from app.ats.integrations.menu.base import BaseMenu
from app.ats.integrations.menu.whatsapp import WhatsAppMenu

logger = logging.getLogger(__name__)

class UnifiedWhatsAppService:
    """
    Servicio unificado de WhatsApp para sistema de nómina.
    Consolida funcionalidades de los servicios anteriores.
    """
    
    def __init__(self, company: PayrollCompany):
        """
        Inicializa el servicio con la empresa especificada
        
        Args:
            company: Instancia de PayrollCompany a la que pertenece el servicio
        """
        self.company = company
        
        # Configuración de WhatsApp desde la empresa
        self.webhook_token = company.whatsapp_webhook_token
        self.phone_number = company.whatsapp_phone_number
        self.business_name = company.whatsapp_business_name
        
        # Inicializar servicios auxiliares
        self.severance_service = None  # Se inicializa por empleado
        self.climate_service = WorkplaceClimateService(company)
        
        # Estado de conversaciones y preferencias de idioma
        self.user_sessions = {}
        self.user_languages = {}  # Almacena preferencias de idioma por usuario
        
        # Configuración de la mensajería
        self.messaging_config = company.messaging_config or {
            'enable_quick_replies': True,
            'enable_buttons': True,
            'enable_list_messages': True,
            'enable_template_messages': True,
            'session_timeout_minutes': 30,
            'max_quick_replies': 3,
            'typing_delay_seconds': 1,
            'default_language': DEFAULT_LANGUAGE,
            'supported_languages': list(SUPPORTED_LANGUAGES.keys())
        }
    
    async def process_message(self, from_number: str, message: str, message_type: str = "text") -> Dict[str, Any]:
        """
        Procesa mensaje entrante de WhatsApp
        
        Args:
            from_number: Número del remitente
            message: Texto del mensaje
            message_type: Tipo de mensaje (text, location, button, list)
            
        Returns:
            Respuesta a enviar
        """
        try:
            # Normalizar número de teléfono
            normalized_number = self._normalize_phone(from_number)
            
            # Detectar o recuperar idioma preferido del usuario
            user_language = self._get_user_language(normalized_number)
            
            # Si es mensaje de texto, verificar si es comando de cambio de idioma
            if message_type == "text":
                if self._check_language_change_command(normalized_number, message):
                    # Si era un comando de idioma, devolver respuesta confirmando el cambio
                    return self._create_language_changed_response(normalized_number)
            
            # Identificar empleado
            employee = self._get_employee_by_phone(normalized_number)
            if not employee:
                return await self._handle_unregistered_user(normalized_number, message)
            
            # Inicializar servicios específicos de empleado si es necesario
            if not self.severance_service:
                self.severance_service = SeveranceCalculationService(employee)
            
            # Simulación de "escribiendo..." para mejorar UX
            if self.messaging_config.get('enable_typing_indicators', True):
                await self._send_typing_indicator(normalized_number)
                
            # Procesar según tipo de mensaje
            if message_type == "text":
                command = message.lower().strip()
                return await self._process_text_command(employee, normalized_number, command)
            elif message_type == "location":
                return await self._process_location(employee, normalized_number, message)
            elif message_type == "button":
                button_id = message  # En este caso, message contiene el ID del botón
                return await self._process_button_response(employee, normalized_number, button_id)
            elif message_type == "list":
                list_item_id = message  # En este caso, message contiene el ID del ítem
                return await self._process_list_response(employee, normalized_number, list_item_id)
            else:
                return await self._handle_unsupported_message(employee, normalized_number, message_type)
                
        except Exception as e:
            logger.error(f"Error procesando mensaje de {from_number}: {str(e)}")
            return {
                "success": False,
                "message": "❌ Error procesando tu mensaje. Por favor intenta de nuevo o contacta a RH.",
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
    
    async def _send_typing_indicator(self, phone_number: str, duration_seconds: int = None) -> None:
        """
        Envía indicador de "escribiendo..." a WhatsApp
        
        Args:
            phone_number: Número al que enviar indicador
            duration_seconds: Duración en segundos, si es None usa config por defecto
        """
        if duration_seconds is None:
            duration_seconds = self.messaging_config.get('typing_delay_seconds', 1)
            
        # En implementación real, aquí enviaríamos el indicador a la API
        # En esta implementación, solo esperamos el tiempo indicado
        if duration_seconds > 0:
            await asyncio.sleep(duration_seconds)
    
    def _get_employee_by_phone(self, phone_number: str) -> Optional[PayrollEmployee]:
        """Obtiene empleado por número de teléfono"""
        try:
            # Buscar por número de teléfono exacto o parcial
            employee = PayrollEmployee.objects.filter(
                company=self.company
            ).filter(
                # Buscar en varios campos posibles
                phone__contains=phone_number
            ).first()
            
            if not employee:
                # Buscar por ID de plataforma
                employee = PayrollEmployee.objects.filter(
                    company=self.company,
                    platform_ids__contains=phone_number
                ).first()
            
            return employee
            
        except Exception as e:
            logger.error(f"Error buscando empleado: {str(e)}")
            return None
    
    async def _handle_unregistered_user(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Maneja usuarios no registrados"""
        logger.warning(f"Usuario no registrado intentando usar el servicio: {phone_number}")
        
        # Detectar idioma del mensaje
        lang = self._detect_message_language(message)
        
        return {
            "success": False,
            "message": get_message('system', 'user_not_found', lang),
            "quick_replies": []
        }
    
    async def _handle_unsupported_message(self, employee: PayrollEmployee, 
                                         phone_number: str, message_type: str) -> Dict[str, Any]:
        """Maneja tipos de mensaje no soportados"""
        return {
            "success": True,
            "message": f"Lo siento, actualmente no puedo procesar mensajes de tipo {message_type}. Por favor, envía un mensaje de texto.",
            "quick_replies": [
                {"text": "🏠 Menú principal", "action": "main_menu"},
                {"text": "❓ Ayuda", "action": "help"}
            ]
        }
    
    async def _process_text_command(self, employee: PayrollEmployee, 
                                   phone_number: str, command: str) -> Dict[str, Any]:
        """Procesa comando de texto"""
        # Obtener idioma preferido del usuario
        lang = self._get_user_language(phone_number)
        
        # Comandos de asistencia
        if command in ['entrada', 'checkin', 'llegada', 'inicio', 'check in', 'check-in', 'entrée', 'entrada']:
            return await self._handle_checkin(employee, phone_number)
            
        elif command in ['salida', 'checkout', 'fin', 'check out', 'check-out', 'sortie', 'saída']:
            return await self._handle_checkout(employee, phone_number)
            
        # Comandos de nómina
        elif command in ['recibo', 'payslip', 'nómina', 'nomina', 'pago', 'fiche', 'holerite']:
            return await self._handle_payslip_request(employee, phone_number)
        elif command in ['balance', 'saldo', 'vacaciones', 'permisos', 'solde', 'férias']:
            return await self._handle_balance_inquiry(employee, phone_number)
        
        # Comandos de ayuda
        elif command in ['ayuda', 'help', 'menu', 'menú', 'opciones', 'comandos', 'aide', 'ajuda']:
            return await self._handle_help_command(employee, phone_number)
        
        # Comandos de idioma
        elif command in ['idioma', 'language', 'langue', 'idioma']:
            return self._handle_language_menu(phone_number)
        
        # Comandos de rol y permisos
        elif command in ['rh', 'hr', 'dashboard', 'reportes', 'informes', 'rapports', 'relatórios']:
            if self._check_hr_role(employee):
                return await self._handle_hr_dashboard(employee, phone_number)
            else:
                return {
                    "success": False,
                    "message": get_message('hr', 'unauthorized', lang),
                }
        
            
        # Comando especial para cambio de rol
        elif command in ['rol', 'cambiar rol', 'switch']:
            return await self._handle_role_switch(employee, phone_number)
            
        # Comando desconocido
        else:
            return await self._handle_unknown_command(employee, phone_number, command)
    
    async def _process_location(self, employee: PayrollEmployee, 
                               phone_number: str, location_data: Union[str, Dict]) -> Dict[str, Any]:
        """
        Procesa mensaje de ubicación
        
        Args:
            employee: Empleado que envía ubicación
            phone_number: Número del remitente
            location_data: Datos de ubicación (JSON string o Dict)
        """
        try:
            # Parsear ubicación si viene como string
            if isinstance(location_data, str):
                try:
                    location = json.loads(location_data)
                except json.JSONDecodeError:
                    location = {"error": "Invalid location format"}
            else:
                location = location_data
                
            # Extraer coordenadas
            latitude = location.get('latitude', 0)
            longitude = location.get('longitude', 0)
            
            if latitude == 0 or longitude == 0:
                return {
                    "success": False,
                    "message": "❌ No pudimos leer tu ubicación. Por favor intenta nuevamente.",
                    "quick_replies": [
                        {"text": "🔄 Enviar ubicación", "action": "send_location"},
                        {"text": "📝 Entrada manual", "action": "manual_checkin"}
                    ]
                }
                
            # Verificar si hay sesión pendiente de check-in o check-out
            session = self.user_sessions.get(phone_number, {})
            pending_action = session.get('pending_action')
            
            if pending_action == 'checkin':
                # Validar ubicación para checkin
                is_valid = self._validate_office_location(employee, 
                                                         Decimal(str(latitude)), 
                                                         Decimal(str(longitude)))
                return await self._complete_checkin(employee, phone_number, 
                                                  latitude, longitude, is_valid)
                                                  
            elif pending_action == 'checkout':
                # Validar ubicación para checkout
                is_valid = self._validate_office_location(employee, 
                                                         Decimal(str(latitude)), 
                                                         Decimal(str(longitude)))
                return await self._complete_checkout(employee, phone_number, 
                                                   latitude, longitude, is_valid)
            else:
                # No hay acción pendiente para la ubicación
                return {
                    "success": True,
                    "message": "📍 Recibimos tu ubicación. ¿Qué deseas hacer?",
                    "quick_replies": [
                        {"text": "✅ Registrar entrada", "action": "checkin"},
                        {"text": "🚪 Registrar salida", "action": "checkout"},
                        {"text": "🏠 Menú principal", "action": "main_menu"}
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error procesando ubicación: {str(e)}")
            return {
                "success": False,
                "message": f"❌ Error procesando ubicación: {str(e)}",
                "quick_replies": [
                    {"text": "🔄 Reintentar", "action": "retry"},
                    {"text": "📝 Entrada manual", "action": "manual_checkin"}
                ]
            }

    # Métodos para manejo de check-in y check-out
    
    async def _handle_checkin(self, employee: PayrollEmployee, phone_number: str) -> Dict[str, Any]:
        """Maneja registro de entrada con solicitud de ubicación"""
        # Registrar intención de check-in en la sesión
        self.user_sessions[phone_number] = {
            'pending_action': 'checkin',
            'timestamp': datetime.now(),
            'employee_id': employee.id
        }
        
        # Si la política de la empresa requiere ubicación
        if self.company.location_required_for_attendance:
            return {
                "success": True,
                "message": "📍 Por favor comparte tu ubicación para registrar tu entrada",
                "quick_replies": [
                    {"text": "📍 Compartir ubicación", "action": "send_location"},
                    {"text": "📝 Entrada manual", "action": "manual_checkin"},
                    {"text": "❌ Cancelar", "action": "cancel"}
                ]
            }
        else:
            # Si no requiere ubicación, registrar directamente
            return await self._complete_checkin(employee, phone_number, None, None, True)
    
    async def _complete_checkin(self, employee: PayrollEmployee, phone_number: str,
                             latitude: Optional[float], longitude: Optional[float],
                             is_valid_location: bool) -> Dict[str, Any]:
        """Completa el registro de entrada"""
        try:
            # Limpiar sesión pendiente
            if phone_number in self.user_sessions:
                del self.user_sessions[phone_number]
            
            # Si la ubicación no es válida pero es requerida
            if not is_valid_location and self.company.location_required_for_attendance:
                return {
                    "success": False,
                    "message": "❌ No estás dentro del perímetro autorizado para registrar asistencia.",
                    "quick_replies": [
                        {"text": "🔄 Reintentar", "action": "checkin"},
                        {"text": "📝 Solicitar excepción", "action": "exception_request"},
                        {"text": "🏠 Menú principal", "action": "main_menu"}
                    ]
                }
            
            # Verificar si ya hay registro de entrada hoy
            today = timezone.now().date()
            existing_record = AttendanceRecord.objects.filter(
                employee=employee,
                date=today
            ).first()
            
            if existing_record and existing_record.check_in:
                # Ya tiene registro de entrada
                formatted_time = existing_record.check_in.strftime('%H:%M')
                return {
                    "success": True,
                    "message": f"ℹ️ Ya registraste tu entrada hoy a las {formatted_time}.",
                    "quick_replies": [
                        {"text": "🚪 Registrar salida", "action": "checkout"},
                        {"text": "🏠 Menú principal", "action": "main_menu"}
                    ]
                }
            
            # Crear o actualizar registro
            if not existing_record:
                record = AttendanceRecord(
                    employee=employee,
                    company=self.company,
                    date=today,
                    status=ATTENDANCE_STATUSES.PRESENT
                )
            else:
                record = existing_record
                
            # Registrar entrada
            now = timezone.now()
            record.check_in = now
            
            # Guardar ubicación si está disponible
            if latitude and longitude:
                record.check_in_location = {
                    'latitude': latitude,
                    'longitude': longitude,
                    'timestamp': now.isoformat()
                }
            
            # Guardar registro
            record.save()
            
            # Formato amigable de la hora
            formatted_time = now.strftime('%H:%M:%S')
            
            return {
                "success": True,
                "message": f"✅ Entrada registrada correctamente a las {formatted_time}.",
                "quick_replies": [
                    {"text": "📊 Mi horario hoy", "action": "schedule"},
                    {"text": "🏠 Menú principal", "action": "main_menu"}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error registrando entrada: {str(e)}")
            return {
                "success": False,
                "message": f"❌ Error registrando entrada: {str(e)}",
                "quick_replies": [
                    {"text": "🔄 Reintentar", "action": "checkin"},
                    {"text": "📞 Contactar RH", "action": "contact_hr"}
                ]
            }
    
    async def _handle_checkout(self, employee: PayrollEmployee, phone_number: str) -> Dict[str, Any]:
        """Maneja registro de salida con solicitud de ubicación"""
        # Registrar intención de check-out en la sesión
        self.user_sessions[phone_number] = {
            'pending_action': 'checkout',
            'timestamp': datetime.now(),
            'employee_id': employee.id
        }
        
        # Si la política de la empresa requiere ubicación
        if self.company.location_required_for_attendance:
            return {
                "success": True,
                "message": "📍 Por favor comparte tu ubicación para registrar tu salida",
                "quick_replies": [
                    {"text": "📍 Compartir ubicación", "action": "send_location"},
                    {"text": "📝 Salida manual", "action": "manual_checkout"},
                    {"text": "❌ Cancelar", "action": "cancel"}
                ]
            }
        else:
            # Si no requiere ubicación, registrar directamente
            return await self._complete_checkout(employee, phone_number, None, None, True)
    
    async def _complete_checkout(self, employee: PayrollEmployee, phone_number: str,
                              latitude: Optional[float], longitude: Optional[float],
                              is_valid_location: bool) -> Dict[str, Any]:
        """Completa el registro de salida"""
        try:
            # Limpiar sesión pendiente
            if phone_number in self.user_sessions:
                del self.user_sessions[phone_number]
            
            # Si la ubicación no es válida pero es requerida
            if not is_valid_location and self.company.location_required_for_attendance:
                return {
                    "success": False,
                    "message": "❌ No estás dentro del perímetro autorizado para registrar salida.",
                    "quick_replies": [
                        {"text": "🔄 Reintentar", "action": "checkout"},
                        {"text": "📝 Solicitar excepción", "action": "exception_request"},
                        {"text": "🏠 Menú principal", "action": "main_menu"}
                    ]
                }
            
            # Verificar registro del día
            today = timezone.now().date()
            record = AttendanceRecord.objects.filter(
                employee=employee,
                date=today
            ).first()
            
            if not record or not record.check_in:
                # No hay registro de entrada
                return {
                    "success": False,
                    "message": "❌ No tienes registro de entrada hoy. Primero debes registrar tu entrada.",
                    "quick_replies": [
                        {"text": "✅ Registrar entrada", "action": "checkin"},
                        {"text": "📝 Solicitar corrección", "action": "correction_request"}
                    ]
                }
                
            if record.check_out:
                # Ya tiene registro de salida
                formatted_time = record.check_out.strftime('%H:%M')
                return {
                    "success": True,
                    "message": f"ℹ️ Ya registraste tu salida hoy a las {formatted_time}.",
                    "quick_replies": [
                        {"text": "📊 Mi resumen hoy", "action": "day_summary"},
                        {"text": "🏠 Menú principal", "action": "main_menu"}
                    ]
                }
            
            # Registrar salida
            now = timezone.now()
            record.check_out = now
            
            # Guardar ubicación si está disponible
            if latitude and longitude:
                record.check_out_location = {
                    'latitude': latitude,
                    'longitude': longitude,
                    'timestamp': now.isoformat()
                }
                
            # Calcular horas trabajadas
            if record.check_in:
                delta = now - record.check_in
                record.hours_worked = delta.total_seconds() / 3600  # Convertir a horas
                
            # Guardar registro
            record.save()
            
            # Formato amigable de la hora
            formatted_time = now.strftime('%H:%M:%S')
            
            # Calcular horas trabajadas con formato
            hours_worked = record.hours_worked or 0
            hours = int(hours_worked)
            minutes = int((hours_worked - hours) * 60)
            
            return {
                "success": True,
                "message": f"✅ Salida registrada correctamente a las {formatted_time}.\n\n⏱️ Horas trabajadas hoy: {hours}h {minutes}m",
                "quick_replies": [
                    {"text": "📊 Mi resumen semanal", "action": "week_summary"},
                    {"text": "🏠 Menú principal", "action": "main_menu"}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error registrando salida: {str(e)}")
            return {
                "success": False,
                "message": f"❌ Error registrando salida: {str(e)}",
                "quick_replies": [
                    {"text": "🔄 Reintentar", "action": "checkout"},
                    {"text": "📞 Contactar RH", "action": "contact_hr"}
                ]
            }
    
    # Métodos para solicitudes de información
    
    async def _handle_payslip_request(self, employee: PayrollEmployee, phone_number: str) -> Dict[str, Any]:
        """Maneja solicitud de recibo de nómina"""
        try:
            # Verificar periodos disponibles
            available_periods = PayrollPeriod.objects.filter(
                company=self.company,
                is_closed=True,
                start_date__gte=(timezone.now() - timedelta(days=90)).date()  # Últimos 90 días
            ).order_by('-end_date')
            
            if not available_periods:
                return {
                    "success": True,
                    "message": "ℹ️ No hay periodos de nómina cerrados disponibles en los últimos 90 días.",
                    "quick_replies": [
                        {"text": "📞 Contactar RH", "action": "contact_hr"},
                        {"text": "🏠 Menú principal", "action": "main_menu"}
                    ]
                }
            
            # Mostrar los últimos 3 periodos
            periods_display = []
            for i, period in enumerate(available_periods[:3]):
                start = period.start_date.strftime('%d/%m/%Y')
                end = period.end_date.strftime('%d/%m/%Y')
                periods_display.append(f"📄 Periodo {start} - {end}")
                
            # Crear mensaje con opciones
            message = "📑 Recibos de nómina disponibles:\n\n" + "\n".join(periods_display)
            message += "\n\nSelecciona un periodo o solicita un rango específico."
            
            # Opciones para los periodos
            quick_replies = []
            for i, period in enumerate(available_periods[:3]):
                start = period.start_date.strftime('%d/%m/%Y')
                end = period.end_date.strftime('%d/%m/%Y')
                label = f"Periodo {i+1}"
                action = f"payslip_{period.id}"
                quick_replies.append({"text": label, "action": action})
            
            # Añadir opción de rango personalizado
            quick_replies.append({"text": "📆 Otro periodo", "action": "custom_period"})
            quick_replies.append({"text": "🏠 Menú principal", "action": "main_menu"})
            
            return {
                "success": True,
                "message": message,
                "quick_replies": quick_replies
            }
            
        except Exception as e:
            logger.error(f"Error en solicitud de recibo: {str(e)}")
            return {
                "success": False,
                "message": "❌ Error procesando tu solicitud de recibo de nómina.",
                "quick_replies": [
                    {"text": "🔄 Reintentar", "action": "payslip"},
                    {"text": "📞 Contactar RH", "action": "contact_hr"}
                ]
            }
    
    async def _handle_balance_inquiry(self, employee: PayrollEmployee, phone_number: str) -> Dict[str, Any]:
        """Maneja consulta de saldos (vacaciones, permisos, etc.)"""
        try:
            # Obtener balances del empleado
            vacation_days = self._calculate_vacation_balance(employee)
            sick_days = self._calculate_sick_days_balance(employee)
            permissions = self._calculate_permissions_balance(employee)
            
            # Formatear mensaje
            message = f"📊 BALANCE ACTUAL DE {employee.full_name.upper()}\n\n"
            message += f"🏖️ Días de vacaciones: {vacation_days} días\n"
            message += f"🤒 Días por enfermedad: {sick_days} días\n"
            message += f"🕒 Permisos disponibles: {permissions} horas\n\n"
            
            # Añadir saldos económicos si aplica
            if hasattr(employee, 'savings_balance') and employee.savings_balance:
                message += f"💰 Fondo de ahorro: ${employee.savings_balance:,.2f}\n"
                
            if hasattr(employee, 'loan_balance') and employee.loan_balance:
                message += f"💸 Saldo de préstamos: ${employee.loan_balance:,.2f}\n"
                
            message += "\n¿Qué deseas hacer?"
            
            return {
                "success": True,
                "message": message,
                "quick_replies": [
                    {"text": "🏖️ Solicitar vacaciones", "action": "vacation_request"},
                    {"text": "🕒 Solicitar permiso", "action": "permission_request"},
                    {"text": "🏠 Menú principal", "action": "main_menu"}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error consultando balances: {str(e)}")
            return {
                "success": False,
                "message": "❌ Error consultando tus balances.",
                "quick_replies": [
                    {"text": "🔄 Reintentar", "action": "balance"},
                    {"text": "📞 Contactar RH", "action": "contact_hr"}
                ]
            }
    
    def _calculate_vacation_balance(self, employee: PayrollEmployee) -> int:
        """Calcula balance de vacaciones del empleado"""
        # Implementar cálculo real de vacaciones según antigüedad y ley
        # Por ahora retornamos un valor de ejemplo
        return 12
    
    def _calculate_sick_days_balance(self, employee: PayrollEmployee) -> int:
        """Calcula balance de días por enfermedad"""
        # Implementar cálculo real
        return 7
    
    def _calculate_permissions_balance(self, employee: PayrollEmployee) -> int:
        """Calcula balance de horas de permiso"""
        # Implementar cálculo real
        return 16
    
    # Métodos para manejar botones y acciones
    
    async def _process_button_response(self, employee: PayrollEmployee, 
                                    phone_number: str, button_id: str) -> Dict[str, Any]:
        """Procesa respuesta de botón"""
        try:
            # Determinar acción basada en ID del botón
            action = button_id.lower()
            
            # Mapeo de acciones a métodos
            if action == "checkin":
                return await self._handle_checkin(employee, phone_number)
                
            elif action == "checkout":
                return await self._handle_checkout(employee, phone_number)
                
            elif action == "payslip":
                return await self._handle_payslip_request(employee, phone_number)
                
            elif action == "balance":
                return await self._handle_balance_inquiry(employee, phone_number)
                
            elif action == "schedule":
                return await self._handle_schedule_inquiry(employee, phone_number)
                
            elif action == "help":
                return await self._handle_help_command(employee, phone_number)
                
            elif action == "main_menu":
                return await self._create_main_menu(employee, phone_number)
                
            elif action == "cancel":
                # Limpiar sesión pendiente
                if phone_number in self.user_sessions:
                    del self.user_sessions[phone_number]
                    
                return {
                    "success": True,
                    "message": "❌ Operación cancelada.",
                    "quick_replies": [
                        {"text": "🏠 Menú principal", "action": "main_menu"},
                        {"text": "❓ Ayuda", "action": "help"}
                    ]
                }
                
            elif action.startswith("payslip_"):
                # Extraer ID del periodo
                try:
                    period_id = int(action.split('_')[1])
                    return await self._send_payslip(employee, phone_number, period_id)
                except (ValueError, IndexError):
                    return await self._handle_payslip_request(employee, phone_number)
            
            # Aquí se pueden añadir más mappings según sea necesario
            else:
                return await self._handle_unknown_command(employee, phone_number, action)
                
        except Exception as e:
            logger.error(f"Error procesando botón: {str(e)}")
            return {
                "success": False,
                "message": "❌ Error procesando tu selección.",
                "quick_replies": [
                    {"text": "🔄 Reintentar", "action": "retry"},
                    {"text": "🏠 Menú principal", "action": "main_menu"}
                ]
            }
    
    async def _process_list_response(self, employee: PayrollEmployee, 
                                  phone_number: str, list_item_id: str) -> Dict[str, Any]:
        """Procesa respuesta de lista"""
        # Similar a _process_button_response pero para selecciones de listas
        # Este método es similar al anterior, se implementaría según necesidades específicas
        pass
        
    async def _create_main_menu(self, employee: PayrollEmployee, phone_number: str) -> Dict[str, Any]:
        """Crea menú principal basado en rol del usuario"""
        # Determinar rol del empleado
        is_supervisor = employee.has_role(PAYROLL_ROLES.SUPERVISOR)
        is_hr = employee.has_role(PAYROLL_ROLES.HR)
        
        # Opciones base para todos
        message = f"👋 Hola {employee.first_name}!\n\n🏢 *{self.company.name}*\n"
        message += "\n📱 *MENÚ PRINCIPAL*\n"
        
        # Opciones para empleados
        options = [
            {"text": "✅ Registrar entrada", "action": "checkin"},
            {"text": "🚪 Registrar salida", "action": "checkout"},
            {"text": "📄 Recibo de nómina", "action": "payslip"},
            {"text": "📊 Mis balances", "action": "balance"}
        ]
        
        # Opciones adicionales para supervisores
        if is_supervisor:
            options.extend([
                {"text": "👥 Mi equipo", "action": "team"},
                {"text": "📋 Aprobar solicitudes", "action": "pending_approvals"}
            ])
            
        # Opciones adicionales para RH
        if is_hr:
            options.extend([
                {"text": "📈 Dashboard RH", "action": "hr_dashboard"},
                {"text": "📊 Reportes", "action": "hr_reports"}
            ])
        
        # Opciones generales al final
        options.extend([
            {"text": "❓ Ayuda", "action": "help"},
            {"text": "📞 Contactar RH", "action": "contact_hr"}
        ])
        
        # Limitar a máximo 10 opciones
        if len(options) > 10:
            options = options[:10]
            
        return {
            "success": True,
            "message": message,
            "quick_replies": options
        }
    
    async def _handle_help_command(self, employee: PayrollEmployee, phone_number: str) -> Dict[str, Any]:
        """Maneja comando de ayuda"""
        # Determinar rol del empleado para personalizar ayuda
        is_supervisor = employee.has_role(PAYROLL_ROLES.SUPERVISOR)
        is_hr = employee.has_role(PAYROLL_ROLES.HR)
        
        message = f"❓ *AYUDA* - {self.company.name}\n\n"
        
        # Comandos básicos para todos
        message += "*COMANDOS BÁSICOS:*\n"
        message += "• 'entrada' - Registrar entrada\n"
        message += "• 'salida' - Registrar salida\n"
        message += "• 'recibo' - Solicitar recibo de nómina\n"
        message += "• 'balance' - Consultar balances\n"
        message += "• 'horario' - Ver tu horario\n"
        message += "• 'menú' - Ver menú principal\n\n"
        
        # Comandos para supervisores
        if is_supervisor:
            message += "*COMANDOS DE SUPERVISOR:*\n"
            message += "• 'equipo' - Ver estado de tu equipo\n"
            message += "• 'aprobar' - Revisar solicitudes pendientes\n"
            message += "• 'reporte equipo' - Generar reporte de equipo\n\n"
        
        # Comandos para RH
        if is_hr:
            message += "*COMANDOS DE RH:*\n"
            message += "• 'dashboard' - Ver dashboard de RH\n"
            message += "• 'reporte' - Generar reportes\n"
            message += "• 'enviar reporte' - Enviar reporte por email\n\n"
        
        # Información de contacto
        message += "*CONTACTO:*\n"
        message += f"• RH: {self.company.hr_email or 'rh@empresa.com'}\n"
        message += f"• Soporte: {self.company.support_email or 'soporte@empresa.com'}"
        
        return {
            "success": True,
            "message": message,
            "quick_replies": [
                {"text": "🏠 Menú principal", "action": "main_menu"},
                {"text": "📞 Contactar RH", "action": "contact_hr"}
            ]
        }
    
    async def _handle_unknown_command(self, employee: PayrollEmployee, 
                                   phone_number: str, command: str) -> Dict[str, Any]:
        """Maneja comandos desconocidos"""
        return {
            "success": True,
            "message": f"Lo siento, no entiendo el comando '{command}'.\n\n¿En qué puedo ayudarte?",
            "quick_replies": [
                {"text": "❓ Ayuda", "action": "help"},
                {"text": "🏠 Menú principal", "action": "main_menu"}
            ]
        }
    
    # Métodos auxiliares
    
    def _validate_office_location(self, employee: PayrollEmployee, 
                                user_lat: Decimal, user_lon: Decimal) -> bool:
        """Valida que el empleado esté cerca de la oficina"""
        # Obtener ubicación de la oficina
        office_location = employee.office_location or {}
        office_lat = Decimal(str(office_location.get('latitude', 0)))
        office_lon = Decimal(str(office_location.get('longitude', 0)))
        
        if office_lat == 0 or office_lon == 0:
            # Si no hay ubicación configurada, permitir
            return True
        
        # Calcular distancia (fórmula de Haversine simplificada)
        distance = self._calculate_distance(user_lat, user_lon, office_lat, office_lon)
        
        # Permitir dentro del radio configurado (default 100m)
        max_distance = self.company.max_location_distance or 0.1  # km
        return distance <= max_distance
    
    def _calculate_distance(self, lat1: Decimal, lon1: Decimal, 
                           lat2: Decimal, lon2: Decimal) -> float:
        """Calcula distancia entre dos puntos en km (Haversine)"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convertir a radianes
        lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
        
        # Fórmula de Haversine
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radio de la Tierra en km
        
        return c * r
        
    # =========================================
    # Métodos para soporte multilingüe
    # =========================================
    
    def _get_user_language(self, phone_number: str) -> str:
        """Obtiene el idioma preferido del usuario o el idioma por defecto"""
        return self.user_languages.get(phone_number, self.messaging_config.get('default_language', DEFAULT_LANGUAGE))
    
    def _set_user_language(self, phone_number: str, language: str) -> None:
        """Establece el idioma preferido para un usuario"""
        if language in SUPPORTED_LANGUAGES:
            self.user_languages[phone_number] = language
            logger.info(f"Idioma cambiado para {phone_number}: {language}")
        else:
            logger.warning(f"Intento de establecer idioma no soportado: {language}")
    
    def _detect_message_language(self, message: str) -> str:
        """Detecta el idioma del mensaje"""
        return detect_language(message)
    
    def _check_language_change_command(self, phone_number: str, message: str) -> bool:
        """Verifica si el mensaje es un comando para cambiar el idioma"""
        message = message.lower().strip()
        
        # Comandos explícitos de cambio de idioma
        if message in ['idioma', 'language', 'langue', 'idioma']:
            # Mostrar menú de selección de idioma
            return False  # No es cambio directo, sino solicitud de menú
            
        # Cambios directos de idioma
        if message in ['español', 'spanish', 'es', 'lang:es', 'language:es']:
            self._set_user_language(phone_number, 'es')
            return True
        elif message in ['english', 'inglés', 'ingles', 'en', 'lang:en', 'language:en']:
            self._set_user_language(phone_number, 'en')
            return True
        elif message in ['français', 'francais', 'french', 'fr', 'lang:fr', 'language:fr']:
            self._set_user_language(phone_number, 'fr')
            return True
        elif message in ['português', 'portugues', 'portuguese', 'pt', 'lang:pt', 'language:pt']:
            self._set_user_language(phone_number, 'pt')
            return True
            
        return False
    
    def _create_language_changed_response(self, phone_number: str) -> Dict[str, Any]:
        """Crea respuesta de confirmación de cambio de idioma"""
        lang = self._get_user_language(phone_number)
        
        # Crear mensaje de bienvenida en el nuevo idioma
        message = get_message('system', 'language_changed', lang)
        welcome = get_message('system', 'welcome', lang)
        
        # Añadir opciones de menú principal
        help_text = get_button_text('help', lang)
        menu_text = get_button_text('main_menu', lang)
        
        return {
            "success": True,
            "message": f"{message}\n\n{welcome}",
            "quick_replies": [
                {"text": f"❓ {help_text}", "action": "help"},
                {"text": f"🏠 {menu_text}", "action": "main_menu"}
            ]
        }
    
    def _handle_language_menu(self, phone_number: str) -> Dict[str, Any]:
        """Muestra menú de selección de idioma"""
        lang = self._get_user_language(phone_number)
        
        message = "🌎 *" + get_message('system', 'language_menu', lang, default="Selecciona tu idioma / Select your language") + "*\n\n"
        
        # Añadir opciones para cada idioma soportado
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
            message += f"• {lang_name}: envía '{lang_code}'\n"
        
        return {
            "success": True,
            "message": message,
            "quick_replies": [
                {"text": "🇪🇸 Español", "action": "lang_es"},
                {"text": "🇺🇸 English", "action": "lang_en"},
                {"text": "🇫🇷 Français", "action": "lang_fr"},
                {"text": "🇧🇷 Português", "action": "lang_pt"}
            ]
        }
    
    # Métodos adicionales a implementar:
    # - _handle_schedule_inquiry
    # - _handle_severance_calculation
    # - _handle_climate_inquiry
    # - _handle_request_creation
    # - _handle_role_switch
    # - _send_payslip
    # etc.
