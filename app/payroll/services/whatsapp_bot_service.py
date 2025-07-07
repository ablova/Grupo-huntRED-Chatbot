"""
Servicio de Bot de WhatsApp huntRED®
Bot conversacional para empleados, supervisores y RH
"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
from decimal import Decimal

from django.utils import timezone
from django.core.exceptions import ValidationError

from ..models import PayrollEmployee, PayrollCompany, AttendanceRecord, EmployeeRequest
from .severance_calculation_service import SeveranceCalculationService
from .workplace_climate_service import WorkplaceClimateService

logger = logging.getLogger(__name__)


class WhatsAppBotService:
    """
    Servicio de bot de WhatsApp con funcionalidades avanzadas
    """
    
    def __init__(self, company: PayrollCompany):
        self.company = company
        self.severance_service = None  # Se inicializa por empleado
        self.climate_service = WorkplaceClimateService(company)
    
    def process_message(self, platform: str, user_id: str, message: str, 
                       business_unit_name: str = None) -> Dict[str, Any]:
        """
        Procesa mensaje del usuario y retorna respuesta
        
        Args:
            platform: Plataforma (whatsapp, telegram, etc.)
            user_id: ID del usuario
            message: Mensaje del usuario
            business_unit_name: Nombre de la unidad de negocio
            
        Returns:
            Respuesta del bot
        """
        try:
            # Identificar empleado
            employee = self._identify_employee(user_id, platform)
            if not employee:
                return self._generate_unknown_user_response()
            
            # Inicializar servicios específicos del empleado
            self.severance_service = SeveranceCalculationService(employee)
            
            # Procesar comando
            command = self._parse_command(message.lower())
            
            if command['type'] == 'check_in':
                return self._handle_check_in(employee, command)
            elif command['type'] == 'check_out':
                return self._handle_check_out(employee, command)
            elif command['type'] == 'payslip':
                return self._handle_payslip_request(employee, command)
            elif command['type'] == 'balance':
                return self._handle_balance_inquiry(employee, command)
            elif command['type'] == 'schedule':
                return self._handle_schedule_inquiry(employee, command)
            elif command['type'] == 'severance':
                return self._handle_severance_calculation(employee, command)
            elif command['type'] == 'climate':
                return self._handle_climate_inquiry(employee, command)
            elif command['type'] == 'request':
                return self._handle_request_creation(employee, command)
            elif command['type'] == 'help':
                return self._handle_help(employee, command)
            elif command['type'] == 'role_switch':
                return self._handle_role_switch(employee, command)
            else:
                return self._handle_unknown_command(employee, message)
                
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return self._generate_error_response(str(e))
    
    def _identify_employee(self, user_id: str, platform: str) -> Optional[PayrollEmployee]:
        """Identifica empleado por ID de usuario"""
        try:
            # Buscar por número de teléfono
            employee = PayrollEmployee.objects.filter(
                company=self.company,
                phone__contains=user_id.replace('@c.us', '').replace('@g.us', '')
            ).first()
            
            if not employee:
                # Buscar por ID de plataforma
                employee = PayrollEmployee.objects.filter(
                    company=self.company,
                    platform_ids__contains=user_id
                ).first()
            
            return employee
            
        except Exception as e:
            logger.error(f"Error identificando empleado: {str(e)}")
            return None
    
    def _parse_command(self, message: str) -> Dict[str, Any]:
        """Parsea comando del mensaje"""
        message = message.strip()
        
        # Comandos de asistencia
        if any(word in message for word in ['entrada', 'check in', 'llegué', 'presente']):
            return {
                'type': 'check_in',
                'location': self._extract_location(message),
                'time': self._extract_time(message)
            }
        
        elif any(word in message for word in ['salida', 'check out', 'me voy', 'terminé']):
            return {
                'type': 'check_out',
                'location': self._extract_location(message),
                'time': self._extract_time(message)
            }
        
        # Comandos de nómina
        elif any(word in message for word in ['recibo', 'payslip', 'nómina', 'pago']):
            return {
                'type': 'payslip',
                'period': self._extract_period(message)
            }
        
        elif any(word in message for word in ['balance', 'saldo', 'cuánto', 'quedan']):
            return {
                'type': 'balance',
                'category': self._extract_category(message)
            }
        
        elif any(word in message for word in ['horario', 'schedule', 'cuándo', 'días']):
            return {
                'type': 'schedule',
                'detail': self._extract_schedule_detail(message)
            }
        
        # Comandos de finiquito
        elif any(word in message for word in ['finiquito', 'liquidación', 'renuncia', 'terminación']):
            return {
                'type': 'severance',
                'termination_type': self._extract_termination_type(message),
                'date': self._extract_date(message)
            }
        
        # Comandos de clima laboral
        elif any(word in message for word in ['clima', 'ambiente', 'satisfacción', 'encuesta']):
            return {
                'type': 'climate',
                'action': self._extract_climate_action(message)
            }
        
        # Comandos de solicitudes
        elif any(word in message for word in ['solicitud', 'request', 'permiso', 'vacaciones']):
            return {
                'type': 'request',
                'request_type': self._extract_request_type(message),
                'reason': self._extract_reason(message),
                'dates': self._extract_dates(message)
            }
        
        # Comandos de ayuda
        elif any(word in message for word in ['ayuda', 'help', 'comandos', 'opciones']):
            return {
                'type': 'help',
                'category': self._extract_help_category(message)
            }
        
        # Cambio de rol
        elif any(word in message for word in ['rol', 'role', 'cambiar', 'supervisor', 'rh']):
            return {
                'type': 'role_switch',
                'new_role': self._extract_role(message)
            }
        
        else:
            return {
                'type': 'unknown',
                'message': message
            }
    
    def _handle_check_in(self, employee: PayrollEmployee, command: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja registro de entrada"""
        try:
            # Validar geolocalización si está disponible
            location = command.get('location')
            if location and not self._validate_location(location, employee):
                return {
                    'success': False,
                    'message': '❌ Ubicación no válida para el registro de entrada',
                    'quick_replies': [
                        {'text': '📍 Registrar ubicación', 'action': 'location_request'},
                        {'text': '❓ Ayuda', 'action': 'help'}
                    ]
                }
            
            # Crear registro de asistencia
            attendance = AttendanceRecord.objects.create(
                employee=employee,
                date=date.today(),
                check_in_time=timezone.now(),
                location=location,
                status='present',
                platform='whatsapp'
            )
            
            return {
                'success': True,
                'message': f'✅ Entrada registrada exitosamente\n⏰ {timezone.now().strftime("%H:%M")}\n📍 {location or "Ubicación no especificada"}',
                'quick_replies': [
                    {'text': '🚪 Salida', 'action': 'check_out'},
                    {'text': '📊 Mi balance', 'action': 'balance'},
                    {'text': '📅 Horario', 'action': 'schedule'}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error registrando entrada: {str(e)}")
            return self._generate_error_response("Error registrando entrada")
    
    def _handle_check_out(self, employee: PayrollEmployee, command: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja registro de salida"""
        try:
            # Buscar registro de entrada del día
            today_record = AttendanceRecord.objects.filter(
                employee=employee,
                date=date.today()
            ).first()
            
            if not today_record:
                return {
                    'success': False,
                    'message': '❌ No se encontró registro de entrada para hoy',
                    'quick_replies': [
                        {'text': '✅ Entrada', 'action': 'check_in'},
                        {'text': '❓ Ayuda', 'action': 'help'}
                    ]
                }
            
            # Actualizar registro con salida
            location = command.get('location')
            today_record.check_out_time = timezone.now()
            today_record.location_out = location
            today_record.save()
            
            # Calcular horas trabajadas
            hours_worked = (today_record.check_out_time - today_record.check_in_time).total_seconds() / 3600
            
            return {
                'success': True,
                'message': f'✅ Salida registrada exitosamente\n⏰ {timezone.now().strftime("%H:%M")}\n⏱️ Horas trabajadas: {hours_worked:.1f}h\n📍 {location or "Ubicación no especificada"}',
                'quick_replies': [
                    {'text': '📊 Mi balance', 'action': 'balance'},
                    {'text': '📋 Solicitudes', 'action': 'requests'},
                    {'text': '🏠 Menú principal', 'action': 'main_menu'}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error registrando salida: {str(e)}")
            return self._generate_error_response("Error registrando salida")
    
    def _handle_payslip_request(self, employee: PayrollEmployee, command: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja solicitud de recibo de nómina"""
        try:
            period = command.get('period', 'current')
            
            # Buscar cálculo de nómina
            if period == 'current':
                calculation = self._get_current_payroll_calculation(employee)
            else:
                calculation = self._get_payroll_calculation_by_period(employee, period)
            
            if not calculation:
                return {
                    'success': False,
                    'message': '❌ No se encontró recibo de nómina para el período solicitado',
                    'quick_replies': [
                        {'text': '📅 Otro período', 'action': 'payslip_period'},
                        {'text': '❓ Ayuda', 'action': 'help'}
                    ]
                }
            
            # Generar resumen del recibo
            summary = self._generate_payslip_summary(calculation)
            
            return {
                'success': True,
                'message': summary,
                'attachments': [
                    {
                        'type': 'pdf',
                        'url': f'/payroll/payslip/{calculation.id}/pdf/',
                        'filename': f'Recibo_{calculation.period.name}.pdf'
                    }
                ],
                'quick_replies': [
                    {'text': '📊 Desglose detallado', 'action': 'payslip_detail'},
                    {'text': '📅 Otro período', 'action': 'payslip_period'},
                    {'text': '🏠 Menú principal', 'action': 'main_menu'}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error procesando solicitud de recibo: {str(e)}")
            return self._generate_error_response("Error obteniendo recibo de nómina")
    
    def _handle_balance_inquiry(self, employee: PayrollEmployee, command: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja consulta de balance"""
        try:
            category = command.get('category', 'all')
            
            if category == 'vacations':
                balance = self._get_vacation_balance(employee)
                message = f'🏖️ Balance de vacaciones:\n{days} días disponibles'
            elif category == 'permissions':
                balance = self._get_permission_balance(employee)
                message = f'⏰ Balance de permisos:\n{hours} horas disponibles'
            else:
                # Balance general
                vacation_balance = self._get_vacation_balance(employee)
                permission_balance = self._get_permission_balance(employee)
                
                message = f'📊 Tu balance general:\n\n🏖️ Vacaciones: {vacation_balance} días\n⏰ Permisos: {permission_balance} horas'
            
            return {
                'success': True,
                'message': message,
                'quick_replies': [
                    {'text': '🏖️ Solo vacaciones', 'action': 'balance_vacations'},
                    {'text': '⏰ Solo permisos', 'action': 'balance_permissions'},
                    {'text': '📋 Solicitar', 'action': 'request'}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error consultando balance: {str(e)}")
            return self._generate_error_response("Error consultando balance")
    
    def _handle_schedule_inquiry(self, employee: PayrollEmployee, command: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja consulta de horario"""
        try:
            detail = command.get('detail', 'current')
            
            if detail == 'week':
                schedule = self._get_weekly_schedule(employee)
                message = f'📅 Horario semanal:\n{schedule}'
            elif detail == 'month':
                schedule = self._get_monthly_schedule(employee)
                message = f'📅 Horario mensual:\n{schedule}'
            else:
                schedule = self._get_current_schedule(employee)
                message = f'📅 Tu horario actual:\n{schedule}'
            
            return {
                'success': True,
                'message': message,
                'quick_replies': [
                    {'text': '📅 Semana', 'action': 'schedule_week'},
                    {'text': '📅 Mes', 'action': 'schedule_month'},
                    {'text': '🏠 Menú principal', 'action': 'main_menu'}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error consultando horario: {str(e)}")
            return self._generate_error_response("Error consultando horario")
    
    def _handle_severance_calculation(self, employee: PayrollEmployee, command: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja cálculo de finiquito"""
        try:
            termination_type = command.get('termination_type', 'voluntary')
            termination_date = command.get('date', date.today())
            
            # Calcular finiquito
            calculation = self.severance_service.calculate_severance(
                termination_date, termination_type
            )
            
            if not calculation['success']:
                return {
                    'success': False,
                    'message': f'❌ Error calculando finiquito: {calculation["error"]}',
                    'quick_replies': [
                        {'text': '❓ Ayuda', 'action': 'help'},
                        {'text': '🏠 Menú principal', 'action': 'main_menu'}
                    ]
                }
            
            # Generar resumen
            summary = self._generate_severance_summary(calculation)
            
            return {
                'success': True,
                'message': summary,
                'attachments': [
                    {
                        'type': 'txt',
                        'content': self.severance_service.export_breakdown(calculation, 'txt'),
                        'filename': f'Finiquito_{employee.get_full_name()}.txt'
                    }
                ],
                'quick_replies': [
                    {'text': '📊 Desglose completo', 'action': 'severance_detail'},
                    {'text': '📄 Exportar PDF', 'action': 'severance_pdf'},
                    {'text': '🏠 Menú principal', 'action': 'main_menu'}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error calculando finiquito: {str(e)}")
            return self._generate_error_response("Error calculando finiquito")
    
    def _handle_climate_inquiry(self, employee: PayrollEmployee, command: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja consulta de clima laboral"""
        try:
            action = command.get('action', 'general')
            
            if action == 'survey':
                # Generar encuesta de clima laboral
                survey = self._generate_climate_survey(employee)
                return {
                    'success': True,
                    'message': survey['message'],
                    'quick_replies': survey['options']
                }
            
            elif action == 'personal':
                # Análisis personal del empleado
                analysis = self.climate_service.analyze_employee_sentiment(employee)
                
                if analysis['success']:
                    sentiment = analysis['average_sentiment']
                    if sentiment > 0.2:
                        status = "😊 Positivo"
                    elif sentiment < -0.2:
                        status = "😔 Negativo"
                    else:
                        status = "😐 Neutral"
                    
                    message = f'📊 Tu análisis de clima laboral:\n\nEstado: {status}\nTendencia: {analysis["sentiment_trend"]}\nSolicitudes analizadas: {analysis["total_requests"]}'
                else:
                    message = "❌ No se pudo analizar tu clima laboral"
                
                return {
                    'success': True,
                    'message': message,
                    'quick_replies': [
                        {'text': '📝 Encuesta', 'action': 'climate_survey'},
                        {'text': '📊 General', 'action': 'climate_general'},
                        {'text': '🏠 Menú principal', 'action': 'main_menu'}
                    ]
                }
            
            else:
                # Análisis general de la empresa
                climate = self.climate_service.analyze_workplace_climate()
                
                if climate['success']:
                    score = climate['overall_score']
                    if score > 0.7:
                        status = "😊 Excelente"
                    elif score > 0.5:
                        status = "😐 Bueno"
                    else:
                        status = "😔 Necesita mejora"
                    
                    message = f'🏢 Clima laboral de la empresa:\n\nEstado: {status}\nScore: {score:.1%}\nRiesgos detectados: {climate["risk_analysis"]["total_risks"]}'
                else:
                    message = "❌ No se pudo analizar el clima laboral"
                
                return {
                    'success': True,
                    'message': message,
                    'quick_replies': [
                        {'text': '👤 Mi análisis', 'action': 'climate_personal'},
                        {'text': '📝 Encuesta', 'action': 'climate_survey'},
                        {'text': '🏠 Menú principal', 'action': 'main_menu'}
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error consultando clima laboral: {str(e)}")
            return self._generate_error_response("Error consultando clima laboral")
    
    def _handle_request_creation(self, employee: PayrollEmployee, command: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja creación de solicitudes"""
        try:
            request_type = command.get('request_type', 'other')
            reason = command.get('reason', '')
            dates = command.get('dates', {})
            
            if not reason:
                return {
                    'success': False,
                    'message': '❌ Por favor especifica el motivo de tu solicitud',
                    'quick_replies': [
                        {'text': '🏖️ Vacaciones', 'action': 'request_vacation'},
                        {'text': '⏰ Permiso', 'action': 'request_permission'},
                        {'text': '❓ Ayuda', 'action': 'help'}
                    ]
                }
            
            # Crear solicitud
            request = EmployeeRequest.objects.create(
                employee=employee,
                request_type=request_type,
                reason=reason,
                start_date=dates.get('start_date'),
                end_date=dates.get('end_date'),
                days_requested=dates.get('days', 1),
                status='pending'
            )
            
            return {
                'success': True,
                'message': f'✅ Solicitud creada exitosamente\n\n📋 Tipo: {request.get_request_type_display()}\n📅 Estado: Pendiente\n🆔 ID: {request.id}',
                'quick_replies': [
                    {'text': '📋 Mis solicitudes', 'action': 'my_requests'},
                    {'text': '➕ Nueva solicitud', 'action': 'new_request'},
                    {'text': '🏠 Menú principal', 'action': 'main_menu'}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error creando solicitud: {str(e)}")
            return self._generate_error_response("Error creando solicitud")
    
    def _handle_help(self, employee: PayrollEmployee, command: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja solicitudes de ayuda"""
        category = command.get('category', 'general')
        
        if category == 'attendance':
            message = """⏰ Comandos de Asistencia:

✅ Entrada: "entrada", "llegué", "check in"
🚪 Salida: "salida", "me voy", "check out"
📍 Con ubicación: "entrada en oficina"

Ejemplo: "entrada en oficina central" """
        
        elif category == 'payroll':
            message = """💰 Comandos de Nómina:

📄 Recibo: "recibo", "payslip", "nómina"
📊 Balance: "balance", "saldo", "cuánto tengo"
🏖️ Vacaciones: "balance vacaciones"
⏰ Permisos: "balance permisos"

Ejemplo: "recibo del mes pasado" """
        
        elif category == 'severance':
            message = """📋 Comandos de Finiquito:

💼 Finiquito: "finiquito", "liquidación"
📅 Con fecha: "finiquito 15/12/2024"
🔄 Tipo: "finiquito renuncia voluntaria"

Ejemplo: "finiquito para el 31/12/2024" """
        
        else:
            message = """🤖 Comandos disponibles:

⏰ ASISTENCIA
✅ Entrada/Salida con ubicación

💰 NÓMINA  
📄 Recibos y balances

📋 SOLICITUDES
🏖️ Vacaciones y permisos

💼 FINIQUITO
📊 Cálculos de liquidación

🏢 CLIMA LABORAL
📊 Análisis y encuestas

❓ Escribe "ayuda [categoría]" para más detalles"""
        
        return {
            'success': True,
            'message': message,
            'quick_replies': [
                {'text': '⏰ Asistencia', 'action': 'help_attendance'},
                {'text': '💰 Nómina', 'action': 'help_payroll'},
                {'text': '💼 Finiquito', 'action': 'help_severance'},
                {'text': '🏠 Menú principal', 'action': 'main_menu'}
            ]
        }
    
    def _handle_role_switch(self, employee: PayrollEmployee, command: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja cambio de rol en el bot"""
        new_role = command.get('new_role', 'employee')
        
        # Validar permisos del empleado
        if new_role == 'supervisor' and not employee.is_supervisor:
            return {
                'success': False,
                'message': '❌ No tienes permisos de supervisor',
                'quick_replies': [
                    {'text': '👤 Empleado', 'action': 'role_employee'},
                    {'text': '❓ Ayuda', 'action': 'help'}
                ]
            }
        
        elif new_role == 'hr' and not employee.is_hr:
            return {
                'success': False,
                'message': '❌ No tienes permisos de RH',
                'quick_replies': [
                    {'text': '👤 Empleado', 'action': 'role_employee'},
                    {'text': '❓ Ayuda', 'action': 'help'}
                ]
            }
        
        # Generar menú según rol
        if new_role == 'supervisor':
            message = """👨‍💼 Menú de Supervisor:

👥 EQUIPO
📊 Ver asistencia del equipo
📋 Aprobar solicitudes
📈 Reportes de equipo

📊 REPORTES
📅 Asistencia semanal
📊 Productividad
⚠️ Alertas y riesgos

❓ Escribe "ayuda supervisor" para más comandos"""
        
        elif new_role == 'hr':
            message = """👩‍💼 Menú de RH:

🏢 EMPRESA
📊 Clima laboral general
👥 Gestión de empleados
📈 Reportes corporativos

⚠️ RIESGOS
🚨 Detección de rotación
📊 Análisis predictivo
💼 Procesos de terminación

❓ Escribe "ayuda rh" para más comandos"""
        
        else:
            message = """👤 Menú de Empleado:

⏰ ASISTENCIA
✅ Entrada/Salida

💰 NÓMINA
📄 Recibos y balances

📋 SOLICITUDES
🏖️ Vacaciones y permisos

💼 FINIQUITO
📊 Cálculos de liquidación

❓ Escribe "ayuda" para más comandos"""
        
        return {
            'success': True,
            'message': message,
            'quick_replies': [
                {'text': '👤 Empleado', 'action': 'role_employee'},
                {'text': '👨‍💼 Supervisor', 'action': 'role_supervisor'},
                {'text': '👩‍💼 RH', 'action': 'role_hr'}
            ]
        }
    
    def _handle_unknown_command(self, employee: PayrollEmployee, message: str) -> Dict[str, Any]:
        """Maneja comandos desconocidos"""
        return {
            'success': False,
            'message': f'❓ No entiendo el comando: "{message}"\n\nEscribe "ayuda" para ver los comandos disponibles',
            'quick_replies': [
                {'text': '❓ Ayuda', 'action': 'help'},
                {'text': '🏠 Menú principal', 'action': 'main_menu'},
                {'text': '👤 Cambiar rol', 'action': 'role_switch'}
            ]
        }
    
    # Métodos auxiliares
    
    def _extract_location(self, message: str) -> Optional[str]:
        """Extrae ubicación del mensaje"""
        location_keywords = ['en', 'ubicación', 'location', 'oficina', 'casa', 'remoto']
        words = message.split()
        
        for i, word in enumerate(words):
            if word in location_keywords and i + 1 < len(words):
                return ' '.join(words[i+1:])
        
        return None
    
    def _extract_time(self, message: str) -> Optional[str]:
        """Extrae tiempo del mensaje"""
        # Implementar extracción de tiempo
        return None
    
    def _extract_period(self, message: str) -> str:
        """Extrae período del mensaje"""
        if any(word in message for word in ['pasado', 'anterior', 'last']):
            return 'previous'
        elif any(word in message for word in ['actual', 'current', 'este']):
            return 'current'
        else:
            return 'current'
    
    def _extract_category(self, message: str) -> str:
        """Extrae categoría del mensaje"""
        if any(word in message for word in ['vacaciones', 'vacation']):
            return 'vacations'
        elif any(word in message for word in ['permisos', 'permission']):
            return 'permissions'
        else:
            return 'all'
    
    def _extract_termination_type(self, message: str) -> str:
        """Extrae tipo de terminación"""
        if any(word in message for word in ['renuncia', 'voluntaria', 'voluntary']):
            return 'voluntary'
        elif any(word in message for word in ['despido', 'involuntaria', 'involuntary']):
            return 'involuntary'
        else:
            return 'voluntary'
    
    def _extract_date(self, message: str) -> date:
        """Extrae fecha del mensaje"""
        # Implementar extracción de fecha
        return date.today()
    
    def _validate_location(self, location: str, employee: PayrollEmployee) -> bool:
        """Valida ubicación para registro de asistencia"""
        # Implementar validación de geolocalización
        return True
    
    def _get_current_payroll_calculation(self, employee: PayrollEmployee):
        """Obtiene cálculo de nómina actual"""
        # Implementar búsqueda de cálculo actual
        return None
    
    def _get_vacation_balance(self, employee: PayrollEmployee) -> int:
        """Obtiene balance de vacaciones"""
        # Implementar cálculo de balance de vacaciones
        return 12
    
    def _get_permission_balance(self, employee: PayrollEmployee) -> int:
        """Obtiene balance de permisos"""
        # Implementar cálculo de balance de permisos
        return 24
    
    def _generate_severance_summary(self, calculation: Dict[str, Any]) -> str:
        """Genera resumen del finiquito"""
        totals = calculation['totals']
        seniority = calculation['seniority_breakdown']
        
        return f"""💼 FINIQUITO CALCULADO

👤 {calculation['employee_info']['name']}
📅 Antigüedad: {seniority['formatted']}
💰 Total a pagar: ${totals['total_to_pay']:,.2f}

📊 DESGLOSE:
• Percepciones: ${totals['gross_total']:,.2f}
• Deducciones: ${totals['total_deductions']:,.2f}
• Neto: ${totals['net_amount']:,.2f}
• Indemnización: ${totals['indemnization_total']:,.2f}

📄 Escribe "desglose completo" para ver detalles"""
    
    def _generate_climate_survey(self, employee: PayrollEmployee) -> Dict[str, Any]:
        """Genera encuesta de clima laboral"""
        return {
            'message': """📊 ENCUESTA DE CLIMA LABORAL

¿Cómo calificarías tu satisfacción laboral?

1️⃣ Muy insatisfecho
2️⃣ Insatisfecho  
3️⃣ Neutral
4️⃣ Satisfecho
5️⃣ Muy satisfecho

Responde con el número correspondiente.""",
            'options': [
                {'text': '1️⃣ Muy insatisfecho', 'action': 'survey_1'},
                {'text': '2️⃣ Insatisfecho', 'action': 'survey_2'},
                {'text': '3️⃣ Neutral', 'action': 'survey_3'},
                {'text': '4️⃣ Satisfecho', 'action': 'survey_4'},
                {'text': '5️⃣ Muy satisfecho', 'action': 'survey_5'}
            ]
        }
    
    def _generate_unknown_user_response(self) -> Dict[str, Any]:
        """Genera respuesta para usuario desconocido"""
        return {
            'success': False,
            'message': """❌ Usuario no registrado

Para usar el bot de huntRED®, necesitas estar registrado en el sistema de nómina.

Contacta a tu departamento de RH para activar tu cuenta.""",
            'quick_replies': [
                {'text': '📞 Contactar RH', 'action': 'contact_hr'},
                {'text': '❓ Ayuda', 'action': 'help'}
            ]
        }
    
    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """Genera respuesta de error"""
        return {
            'success': False,
            'message': f'❌ Error: {error_message}\n\nPor favor intenta nuevamente o contacta soporte.',
            'quick_replies': [
                {'text': '🔄 Reintentar', 'action': 'retry'},
                {'text': '❓ Ayuda', 'action': 'help'},
                {'text': '📞 Soporte', 'action': 'support'}
            ]
        } 