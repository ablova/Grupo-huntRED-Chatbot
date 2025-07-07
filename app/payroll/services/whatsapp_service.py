"""
Servicio de WhatsApp huntRED® Payroll
Bot dedicado por cliente con META Conversations 2025 y Quick Replies
"""
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
from decimal import Decimal

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings

from ..models import PayrollCompany, PayrollEmployee, AttendanceRecord, EmployeeRequest, PayrollPeriod
from .. import PAYROLL_ROLES, ATTENDANCE_STATUSES, REQUEST_STATUSES

logger = logging.getLogger(__name__)


class WhatsAppPayrollBot:
    """
    Bot de WhatsApp dedicado por empresa cliente
    CON META CONVERSATIONS 2025 Y QUICK REPLIES
    """
    
    def __init__(self, company: PayrollCompany):
        self.company = company
        self.webhook_token = company.whatsapp_webhook_token
        self.phone_number = company.whatsapp_phone_number
        self.business_name = company.whatsapp_business_name
        
        # Configuración de mensajería
        self.messaging_config = company.messaging_config
        
        # Estados de conversación por usuario
        self.user_sessions = {}
        
        # Configuración META Conversations 2025
        self.conversation_config = {
            'enable_quick_replies': True,
            'enable_buttons': True,
            'enable_list_messages': True,
            'enable_template_messages': True,
            'session_timeout_minutes': 30,
            'max_quick_replies': 3,
            'enable_typing_indicators': True
        }
    
    async def process_message(self, from_number: str, message_text: str, message_type: str = "text") -> Dict[str, Any]:
        """
        Procesa mensaje entrante de WhatsApp con META Conversations 2025
        
        Args:
            from_number: Número del remitente
            message_text: Texto del mensaje
            message_type: Tipo de mensaje
            
        Returns:
            Respuesta a enviar
        """
        try:
            # Identificar empleado
            employee = self._get_employee_by_phone(from_number)
            
            if not employee:
                return await self._handle_unregistered_user(from_number, message_text)
            
            # Normalizar comando
            command = message_text.lower().strip()
            
            # Procesar según tipo de mensaje
            if message_type == "text":
                return await self._process_text_command(employee, from_number, command)
            elif message_type == "location":
                return await self._process_location_message(employee, from_number, message_text)
            elif message_type == "button":
                return await self._process_button_response(employee, from_number, message_text)
            elif message_type == "list":
                return await self._process_list_response(employee, from_number, message_text)
            else:
                return await self._handle_unsupported_message(employee, from_number, message_type)
                
        except Exception as e:
            logger.error(f"Error procesando mensaje de {from_number}: {str(e)}")
            return {
                "success": False,
                "message": "❌ Error procesando tu mensaje. Por favor intenta de nuevo o contacta a RH.",
                "error": str(e)
            }
    
    async def _process_text_command(self, employee: PayrollEmployee, from_number: str, command: str) -> Dict[str, Any]:
        """Procesa comando de texto con Quick Replies"""
        
        # Comandos de asistencia
        if command in ['entrada', 'checkin', 'llegada', 'inicio']:
            return await self._handle_checkin(employee, from_number)
        elif command in ['salida', 'checkout', 'fin']:
            return await self._handle_checkout(employee, from_number)
        
        # Comandos de consulta
        elif command in ['recibo', 'nomina', 'pago']:
            return await self._handle_payslip_request(employee, from_number)
        elif command in ['saldo', 'vacaciones', 'balance']:
            return await self._handle_balance_inquiry(employee, from_number)
        elif command in ['horario', 'schedule', 'jornada']:
            return await self._handle_schedule_inquiry(employee, from_number)
        
        # Comandos de solicitudes
        elif command in ['vacaciones', 'permiso', 'solicitud']:
            return await self._handle_request_flow(employee, from_number, command)
        
        # Comandos de supervisor
        elif employee.supervisor and command in ['equipo', 'aprobaciones', 'reporte']:
            return await self._handle_supervisor_commands(employee, from_number, command)
        
        # Comandos de ayuda
        elif command in ['ayuda', 'help', 'menu', 'comandos']:
            return await self._handle_help_command(employee, from_number)
        
        else:
            return await self._handle_unknown_command(employee, from_number, command)
    
    async def _handle_checkin(self, employee: PayrollEmployee, from_number: str) -> Dict[str, Any]:
        """Maneja entrada del empleado con Quick Replies"""
        
        # Verificar si ya tiene entrada registrada hoy
        today = date.today()
        existing_checkin = AttendanceRecord.objects.filter(
            employee=employee,
            date=today,
            check_in_time__isnull=False
        ).first()
        
        if existing_checkin:
            message = f"""❌ Ya tienes registrada tu entrada de hoy

🕐 Hora de entrada: {existing_checkin.check_in_time.strftime('%H:%M')}
📅 Fecha: {today.strftime('%d/%m/%Y')}

Si necesitas corregir algo, contacta a RH."""
            
            # Quick Replies para acciones adicionales
            quick_replies = [
                {
                    "id": "view_schedule",
                    "title": "📅 Ver Horario",
                    "description": "Consulta tu horario de trabajo"
                },
                {
                    "id": "contact_hr",
                    "title": "📞 Contactar RH",
                    "description": "Solicitar ayuda o corrección"
                },
                {
                    "id": "main_menu",
                    "title": "🏠 Menú Principal",
                    "description": "Volver al menú principal"
                }
            ]
            
            return {
                "success": True,
                "message": message,
                "quick_replies": quick_replies,
                "status": "already_checked_in"
            }
        
        # Solicitar ubicación con Quick Replies
        message = f"""📍 Para registrar tu entrada, comparte tu ubicación:

1. Toca el ícono de adjuntar (📎)
2. Selecciona "Ubicación"  
3. Elige "Ubicación actual"

Esto es para verificar que estés en la oficina.

⏰ Hora actual: {datetime.now().strftime('%H:%M')}"""
        
        # Quick Replies para entrada
        quick_replies = [
            {
                "id": "share_location",
                "title": "📍 Compartir Ubicación",
                "description": "Registrar entrada con ubicación"
            },
            {
                "id": "manual_checkin",
                "title": "✏️ Entrada Manual",
                "description": "Registrar entrada sin ubicación"
            },
            {
                "id": "cancel_checkin",
                "title": "❌ Cancelar",
                "description": "Cancelar registro de entrada"
            }
        ]
        
        # Guardar estado esperando ubicación
        self.user_sessions[from_number] = {
            "action": "checkin",
            "timestamp": datetime.now(),
            "employee_id": str(employee.id)
        }
        
        return {
            "success": True,
            "message": message,
            "quick_replies": quick_replies,
            "status": "waiting_location"
        }
    
    async def _handle_checkout(self, employee: PayrollEmployee, from_number: str) -> Dict[str, Any]:
        """Maneja salida del empleado con Quick Replies"""
        
        today = date.today()
        attendance = AttendanceRecord.objects.filter(
            employee=employee,
            date=today
        ).first()
        
        if not attendance or not attendance.check_in_time:
            message = """❌ No tienes una entrada registrada para hoy.

Primero debes registrar tu entrada con el comando 'entrada'."""
            
            # Quick Replies para acciones
            quick_replies = [
                {
                    "id": "checkin_first",
                    "title": "✅ Registrar Entrada",
                    "description": "Registrar entrada primero"
                },
                {
                    "id": "contact_hr",
                    "title": "📞 Contactar RH",
                    "description": "Solicitar ayuda"
                },
                {
                    "id": "main_menu",
                    "title": "🏠 Menú Principal",
                    "description": "Volver al menú principal"
                }
            ]
            
            return {
                "success": True,
                "message": message,
                "quick_replies": quick_replies,
                "status": "no_checkin_found"
            }
        
        if attendance.check_out_time:
            message = f"""❌ Ya tienes registrada tu salida de hoy

🕐 Entrada: {attendance.check_in_time.strftime('%H:%M')}
🕐 Salida: {attendance.check_out_time.strftime('%H:%M')}
⏱️ Horas trabajadas: {attendance.hours_worked}"""
            
            return {
                "success": True,
                "message": message,
                "status": "already_checked_out"
            }
        
        # Solicitar ubicación con Quick Replies
        message = """📍 Para registrar tu salida, comparte tu ubicación:

1. Toca el ícono de adjuntar (📎)
2. Selecciona "Ubicación"  
3. Elige "Ubicación actual"

Esto es para verificar que estés en la oficina."""
        
        # Quick Replies para salida
        quick_replies = [
            {
                "id": "share_location",
                "title": "📍 Compartir Ubicación",
                "description": "Registrar salida con ubicación"
            },
            {
                "id": "manual_checkout",
                "title": "✏️ Salida Manual",
                "description": "Registrar salida sin ubicación"
            },
            {
                "id": "cancel_checkout",
                "title": "❌ Cancelar",
                "description": "Cancelar registro de salida"
            }
        ]
        
        # Guardar estado esperando ubicación
        self.user_sessions[from_number] = {
            "action": "checkout",
            "timestamp": datetime.now(),
            "employee_id": str(employee.id)
        }
        
        return {
            "success": True,
            "message": message,
            "quick_replies": quick_replies,
            "status": "waiting_location"
        }
    
    async def _handle_payslip_request(self, employee: PayrollEmployee, from_number: str) -> Dict[str, Any]:
        """Maneja solicitud de recibo de nómina con Quick Replies"""
        
        # Obtener último período de nómina
        latest_period = PayrollPeriod.objects.filter(
            company=self.company,
            status__in=['calculated', 'approved', 'disbursed']
        ).order_by('-end_date').first()
        
        if not latest_period:
            message = """📄 No hay recibos de nómina disponibles.

Contacta a RH para más información."""
            
            quick_replies = [
                {
                    "id": "contact_hr",
                    "title": "📞 Contactar RH",
                    "description": "Solicitar información de nómina"
                },
                {
                    "id": "main_menu",
                    "title": "🏠 Menú Principal",
                    "description": "Volver al menú principal"
                }
            ]
            
            return {
                "success": True,
                "message": message,
                "quick_replies": quick_replies,
                "status": "no_payslips"
            }
        
        # Obtener cálculo del empleado
        calculation = latest_period.calculations.filter(employee=employee).first()
        
        if not calculation:
            message = """📄 No se encontró tu recibo de nómina.

Contacta a RH para verificar tu información."""
            
            quick_replies = [
                {
                    "id": "contact_hr",
                    "title": "📞 Contactar RH",
                    "description": "Verificar información de nómina"
                },
                {
                    "id": "main_menu",
                    "title": "🏠 Menú Principal",
                    "description": "Volver al menú principal"
                }
            ]
            
            return {
                "success": True,
                "message": message,
                "quick_replies": quick_replies,
                "status": "no_calculation"
            }
        
        # Formatear recibo
        message = f"""📄 Recibo de Nómina - {latest_period.period_name}

💰 Percepciones:
   • Salario base: ${calculation.base_salary:,.2f}
   • Horas extra: ${calculation.overtime_amount:,.2f}
   • Bonos: ${calculation.bonuses:,.2f}
   • Total bruto: ${calculation.gross_income:,.2f}

💸 Deducciones:
   • ISR: ${calculation.isr_withheld:,.2f}
   • IMSS: ${calculation.imss_employee:,.2f}
   • Total deducciones: ${calculation.total_deductions:,.2f}

💵 Neto a pagar: ${calculation.net_pay:,.2f}

📅 Período: {latest_period.start_date.strftime('%d/%m/%Y')} - {latest_period.end_date.strftime('%d/%m/%Y')}
📊 Estado: {latest_period.get_status_display()}"""
        
        # Quick Replies para acciones con recibo
        quick_replies = [
            {
                "id": "download_payslip",
                "title": "📥 Descargar PDF",
                "description": "Descargar recibo en PDF"
            },
            {
                "id": "previous_payslip",
                "title": "📄 Recibo Anterior",
                "description": "Ver recibo del período anterior"
            },
            {
                "id": "main_menu",
                "title": "🏠 Menú Principal",
                "description": "Volver al menú principal"
            }
        ]
        
        return {
            "success": True,
            "message": message,
            "quick_replies": quick_replies,
            "status": "payslip_sent"
        }
    
    async def _handle_balance_inquiry(self, employee: PayrollEmployee, from_number: str) -> Dict[str, Any]:
        """Maneja consulta de saldos con Quick Replies"""
        
        # Obtener solicitudes pendientes
        pending_requests = EmployeeRequest.objects.filter(
            employee=employee,
            status='pending'
        ).count()
        
        # Obtener días de vacaciones (ejemplo)
        vacation_days = 15  # Esto debería venir de configuración del empleado
        
        message = f"""📊 Estado de tu cuenta

🏖️ Días de vacaciones disponibles: {vacation_days}
📋 Solicitudes pendientes: {pending_requests}

Para solicitar vacaciones, usa el comando 'vacaciones'."""
        
        # Quick Replies para acciones
        quick_replies = [
            {
                "id": "request_vacation",
                "title": "🏖️ Solicitar Vacaciones",
                "description": "Crear solicitud de vacaciones"
            },
            {
                "id": "view_requests",
                "title": "📋 Ver Solicitudes",
                "description": "Ver estado de solicitudes"
            },
            {
                "id": "main_menu",
                "title": "🏠 Menú Principal",
                "description": "Volver al menú principal"
            }
        ]
        
        return {
            "success": True,
            "message": message,
            "quick_replies": quick_replies,
            "status": "balance_sent"
        }
    
    async def _handle_schedule_inquiry(self, employee: PayrollEmployee, from_number: str) -> Dict[str, Any]:
        """Maneja consulta de horario con Quick Replies"""
        
        working_hours = employee.working_hours
        
        message = f"""🕐 Tu horario de trabajo

📅 Días laborales: Lunes a Viernes
⏰ Horario: {working_hours.get('start_time', '09:00')} - {working_hours.get('end_time', '18:00')}
⏱️ Horas por día: {working_hours.get('hours_per_day', 8)}
📊 Días por mes: {working_hours.get('days_per_month', 22)}

📍 Ubicación de oficina: {self._format_location(employee.office_location)}"""
        
        # Quick Replies para horario
        quick_replies = [
            {
                "id": "checkin_now",
                "title": "✅ Registrar Entrada",
                "description": "Registrar entrada ahora"
            },
            {
                "id": "checkout_now",
                "title": "🏁 Registrar Salida",
                "description": "Registrar salida ahora"
            },
            {
                "id": "main_menu",
                "title": "🏠 Menú Principal",
                "description": "Volver al menú principal"
            }
        ]
        
        return {
            "success": True,
            "message": message,
            "quick_replies": quick_replies,
            "status": "schedule_sent"
        }
    
    async def _handle_help_command(self, employee: PayrollEmployee, from_number: str) -> Dict[str, Any]:
        """Maneja comando de ayuda con menú dinámico"""
        
        # Crear menú dinámico basado en rol del empleado
        menu_items = self._create_dynamic_menu(employee)
        
        message = f"""🤖 {self.business_name} - Menú Principal

Selecciona una opción:"""
        
        return {
            "success": True,
            "message": message,
            "list_message": {
                "title": "Menú Principal",
                "description": "Selecciona la opción que necesitas",
                "button_text": "Ver Opciones",
                "sections": menu_items
            },
            "status": "help_sent"
        }
    
    def _create_dynamic_menu(self, employee: PayrollEmployee) -> List[Dict]:
        """Crea menú dinámico basado en rol del empleado"""
        menu_items = []
        
        # Sección de Asistencia
        attendance_section = {
            "title": "📱 Asistencia",
            "rows": [
                {
                    "id": "checkin",
                    "title": "✅ Registrar Entrada",
                    "description": "Registrar entrada al trabajo"
                },
                {
                    "id": "checkout",
                    "title": "🏁 Registrar Salida",
                    "description": "Registrar salida del trabajo"
                },
                {
                    "id": "schedule",
                    "title": "🕐 Ver Horario",
                    "description": "Consultar horario de trabajo"
                }
            ]
        }
        menu_items.append(attendance_section)
        
        # Sección de Consultas
        queries_section = {
            "title": "📄 Consultas",
            "rows": [
                {
                    "id": "payslip",
                    "title": "💰 Ver Recibo",
                    "description": "Consultar último recibo de nómina"
                },
                {
                    "id": "balance",
                    "title": "📊 Estado de Cuenta",
                    "description": "Ver saldos y solicitudes"
                }
            ]
        }
        menu_items.append(queries_section)
        
        # Sección de Solicitudes
        requests_section = {
            "title": "📋 Solicitudes",
            "rows": [
                {
                    "id": "vacation",
                    "title": "🏖️ Solicitar Vacaciones",
                    "description": "Crear solicitud de vacaciones"
                },
                {
                    "id": "permission",
                    "title": "📝 Solicitar Permiso",
                    "description": "Crear solicitud de permiso"
                }
            ]
        }
        menu_items.append(requests_section)
        
        # Sección de Supervisor (solo si es supervisor)
        if employee.supervisor:
            supervisor_section = {
                "title": "👥 Supervisor",
                "rows": [
                    {
                        "id": "team_attendance",
                        "title": "👥 Equipo",
                        "description": "Ver asistencia del equipo"
                    },
                    {
                        "id": "approvals",
                        "title": "✅ Aprobaciones",
                        "description": "Gestionar solicitudes pendientes"
                    }
                ]
            }
            menu_items.append(supervisor_section)
        
        # Sección de Ayuda
        help_section = {
            "title": "❓ Ayuda",
            "rows": [
                {
                    "id": "contact_hr",
                    "title": "📞 Contactar RH",
                    "description": "Solicitar ayuda o soporte"
                },
                {
                    "id": "help",
                    "title": "❓ Ayuda",
                    "description": "Ver comandos disponibles"
                }
            ]
        }
        menu_items.append(help_section)
        
        return menu_items
    
    async def _process_button_response(self, employee: PayrollEmployee, from_number: str, button_id: str) -> Dict[str, Any]:
        """Procesa respuesta de botón"""
        
        if button_id == "share_location":
            return {
                "success": True,
                "message": "📍 Por favor comparte tu ubicación tocando el ícono de adjuntar (📎) y seleccionando 'Ubicación'.",
                "status": "waiting_location"
            }
        elif button_id == "manual_checkin":
            return await self._handle_manual_checkin(employee, from_number)
        elif button_id == "manual_checkout":
            return await self._handle_manual_checkout(employee, from_number)
        elif button_id == "main_menu":
            return await self._handle_help_command(employee, from_number)
        elif button_id == "contact_hr":
            return await self._handle_contact_hr(employee, from_number)
        else:
            return await self._handle_unknown_command(employee, from_number, button_id)
    
    async def _process_list_response(self, employee: PayrollEmployee, from_number: str, list_item_id: str) -> Dict[str, Any]:
        """Procesa respuesta de lista"""
        
        if list_item_id == "checkin":
            return await self._handle_checkin(employee, from_number)
        elif list_item_id == "checkout":
            return await self._handle_checkout(employee, from_number)
        elif list_item_id == "schedule":
            return await self._handle_schedule_inquiry(employee, from_number)
        elif list_item_id == "payslip":
            return await self._handle_payslip_request(employee, from_number)
        elif list_item_id == "balance":
            return await self._handle_balance_inquiry(employee, from_number)
        elif list_item_id == "vacation":
            return await self._handle_vacation_request(employee, from_number)
        elif list_item_id == "permission":
            return await self._handle_permission_request(employee, from_number)
        else:
            return await self._handle_unknown_command(employee, from_number, list_item_id)
    
    async def _handle_manual_checkin(self, employee: PayrollEmployee, from_number: str) -> Dict[str, Any]:
        """Maneja entrada manual sin ubicación"""
        
        today = date.today()
        now = datetime.now()
        
        # Crear registro de asistencia
        attendance, created = AttendanceRecord.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={
                "status": "present",
                "check_in_method": "whatsapp_manual"
            }
        )
        
        attendance.check_in_time = now
        attendance.save()
        
        message = f"""✅ Entrada registrada manualmente

🕐 Hora: {now.strftime('%H:%M')}
📅 Fecha: {today.strftime('%d/%m/%Y')}
⚠️ Nota: Registro sin verificación de ubicación

¡Que tengas un excelente día de trabajo! 💪"""
        
        quick_replies = [
            {
                "id": "checkout_later",
                "title": "🏁 Salida Más Tarde",
                "description": "Registrar salida al final del día"
            },
            {
                "id": "main_menu",
                "title": "🏠 Menú Principal",
                "description": "Volver al menú principal"
            }
        ]
        
        return {
            "success": True,
            "message": message,
            "quick_replies": quick_replies,
            "status": "manual_checkin_success"
        }
    
    async def _handle_manual_checkout(self, employee: PayrollEmployee, from_number: str) -> Dict[str, Any]:
        """Maneja salida manual sin ubicación"""
        
        today = date.today()
        attendance = AttendanceRecord.objects.filter(
            employee=employee,
            date=today
        ).first()
        
        if not attendance or not attendance.check_in_time:
            return {
                "success": False,
                "message": "❌ No tienes una entrada registrada para hoy.",
                "status": "no_checkin_found"
            }
        
        now = datetime.now()
        attendance.check_out_time = now
        attendance.check_out_method = "whatsapp_manual"
        attendance.calculate_hours_worked()
        attendance.save()
        
        message = f"""✅ Salida registrada manualmente

🕐 Entrada: {attendance.check_in_time.strftime('%H:%M')}
🕐 Salida: {now.strftime('%H:%M')}
⏱️ Horas trabajadas: {attendance.hours_worked}
⚠️ Nota: Registro sin verificación de ubicación

¡Descansa bien! 😊"""
        
        quick_replies = [
            {
                "id": "main_menu",
                "title": "🏠 Menú Principal",
                "description": "Volver al menú principal"
            }
        ]
        
        return {
            "success": True,
            "message": message,
            "quick_replies": quick_replies,
            "status": "manual_checkout_success"
        }
    
    async def _handle_contact_hr(self, employee: PayrollEmployee, from_number: str) -> Dict[str, Any]:
        """Maneja contacto con RH"""
        
        message = f"""📞 Contacto con Recursos Humanos

👤 Empleado: {employee.get_full_name()}
📧 Email: {employee.email}
📱 WhatsApp: {self.phone_number}

Horarios de atención:
🕐 Lunes a Viernes: 9:00 AM - 6:00 PM
📅 Sábados: 9:00 AM - 2:00 PM

Para emergencias fuera de horario, contacta a tu supervisor directo."""
        
        quick_replies = [
            {
                "id": "main_menu",
                "title": "🏠 Menú Principal",
                "description": "Volver al menú principal"
            }
        ]
        
        return {
            "success": True,
            "message": message,
            "quick_replies": quick_replies,
            "status": "contact_hr_sent"
        }
    
    async def _handle_vacation_request(self, employee: PayrollEmployee, from_number: str) -> Dict[str, Any]:
        """Maneja solicitud de vacaciones"""
        
        # Iniciar flujo de solicitud de vacaciones
        self.user_sessions[from_number] = {
            "action": "vacation_request",
            "timestamp": datetime.now(),
            "employee_id": str(employee.id),
            "step": "start"
        }
        
        message = """🏖️ Solicitud de Vacaciones

Para crear tu solicitud, necesito algunos datos:

📅 ¿Cuándo quieres tomar las vacaciones?

Responde con las fechas en formato:
DD/MM/AAAA - DD/MM/AAAA

Ejemplo: 15/03/2024 - 22/03/2024"""
        
        quick_replies = [
            {
                "id": "cancel_request",
                "title": "❌ Cancelar",
                "description": "Cancelar solicitud de vacaciones"
            }
        ]
        
        return {
            "success": True,
            "message": message,
            "quick_replies": quick_replies,
            "status": "vacation_request_started"
        }
    
    async def _handle_permission_request(self, employee: PayrollEmployee, from_number: str) -> Dict[str, Any]:
        """Maneja solicitud de permiso"""
        
        # Iniciar flujo de solicitud de permiso
        self.user_sessions[from_number] = {
            "action": "permission_request",
            "timestamp": datetime.now(),
            "employee_id": str(employee.id),
            "step": "start"
        }
        
        message = """📝 Solicitud de Permiso

Para crear tu solicitud, necesito algunos datos:

📅 ¿Cuándo necesitas el permiso?

Responde con las fechas en formato:
DD/MM/AAAA - DD/MM/AAAA

Ejemplo: 15/03/2024 - 15/03/2024"""
        
        quick_replies = [
            {
                "id": "cancel_request",
                "title": "❌ Cancelar",
                "description": "Cancelar solicitud de permiso"
            }
        ]
        
        return {
            "success": True,
            "message": message,
            "quick_replies": quick_replies,
            "status": "permission_request_started"
        }
    
    async def _handle_unknown_command(self, employee: PayrollEmployee, from_number: str, command: str) -> Dict[str, Any]:
        """Maneja comandos desconocidos con Quick Replies"""
        
        message = f"""❓ Comando no reconocido: "{command}"

Usa 'ayuda' para ver los comandos disponibles.

O contacta a RH si necesitas asistencia."""
        
        quick_replies = [
            {
                "id": "help",
                "title": "❓ Ayuda",
                "description": "Ver comandos disponibles"
            },
            {
                "id": "contact_hr",
                "title": "📞 Contactar RH",
                "description": "Solicitar asistencia"
            },
            {
                "id": "main_menu",
                "title": "🏠 Menú Principal",
                "description": "Volver al menú principal"
            }
        ]
        
        return {
            "success": True,
            "message": message,
            "quick_replies": quick_replies,
            "status": "unknown_command"
        }
    
    def _get_employee_by_phone(self, phone_number: str) -> Optional[PayrollEmployee]:
        """Obtiene empleado por número de teléfono"""
        return PayrollEmployee.objects.filter(
            company=self.company,
            is_active=True
        ).filter(
            models.Q(phone=phone_number) | 
            models.Q(whatsapp_number=phone_number)
        ).first()
    
    def _validate_office_location(self, employee: PayrollEmployee, user_lat: Decimal, user_lon: Decimal) -> bool:
        """Valida que el empleado esté cerca de la oficina"""
        office_location = employee.office_location
        office_lat = Decimal(str(office_location.get('latitude', 0)))
        office_lon = Decimal(str(office_location.get('longitude', 0)))
        
        if office_lat == 0 or office_lon == 0:
            # Si no hay ubicación configurada, permitir
            return True
        
        # Calcular distancia (fórmula de Haversine simplificada)
        distance = self._calculate_distance(user_lat, user_lon, office_lat, office_lon)
        
        # Permitir dentro de 100 metros
        return distance <= 0.1
    
    def _calculate_distance(self, lat1: Decimal, lon1: Decimal, lat2: Decimal, lon2: Decimal) -> float:
        """Calcula distancia entre dos puntos (km)"""
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
    
    def _format_location(self, location: Dict[str, Any]) -> str:
        """Formatea ubicación para mostrar"""
        lat = location.get('latitude', 0)
        lon = location.get('longitude', 0)
        address = location.get('address', '')
        
        if address:
            return address
        else:
            return f"{lat}, {lon}"


def setup_webhooks():
    """Configura webhooks de WhatsApp para todas las empresas"""
    companies = PayrollCompany.objects.filter(is_active=True)
    
    for company in companies:
        logger.info(f"Configurando webhook para empresa: {company.name}")
        # Aquí se configurarían los webhooks con WhatsApp Business API
        # Esto dependería de la implementación específica de WhatsApp


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """Vista para webhooks de WhatsApp con META Conversations 2025"""
    
    def post(self, request, company_id: str):
        """Procesa webhook de WhatsApp"""
        try:
            # Verificar token
            webhook_token = request.headers.get('X-Webhook-Token')
            if not webhook_token:
                return JsonResponse({"error": "Token requerido"}, status=401)
            
            # Obtener empresa
            company = PayrollCompany.objects.get(id=company_id, is_active=True)
            if company.whatsapp_webhook_token != webhook_token:
                return JsonResponse({"error": "Token inválido"}, status=401)
            
            # Parsear datos del webhook
            webhook_data = json.loads(request.body)
            
            # Extraer mensaje
            message = self._extract_message(webhook_data)
            if not message:
                return JsonResponse({"status": "no_message"})
            
            # Procesar mensaje
            bot = WhatsAppPayrollBot(company)
            response = asyncio.run(bot.process_message(
                from_number=message['from'],
                message_text=message.get('text', ''),
                message_type=message.get('type', 'text')
            ))
            
            return JsonResponse(response)
            
        except PayrollCompany.DoesNotExist:
            return JsonResponse({"error": "Empresa no encontrada"}, status=404)
        except Exception as e:
            logger.error(f"Error en webhook: {str(e)}")
            return JsonResponse({"error": "Error interno"}, status=500)
    
    def _extract_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extrae mensaje de los datos del webhook"""
        try:
            entry = webhook_data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])
            
            if messages:
                return messages[0]
            
            return None
            
        except (IndexError, KeyError):
            return None 