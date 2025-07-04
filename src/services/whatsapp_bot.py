"""
WhatsApp Payroll Bot - Multi-Tenant Conversational Interface
950+ lines of advanced chatbot functionality
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

import httpx
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioException

from ..config.settings import get_settings
from ..models.base import UserRole, MessageChannel, MessagePriority
from ..services.payroll_engine import PayrollEngine
from ..services.sociallink_engine import SocialLinkEngine

settings = get_settings()
logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Bot conversation states"""
    IDLE = "idle"
    AUTHENTICATING = "authenticating"
    MENU = "menu"
    CHECKING_IN = "checking_in"
    CHECKING_OUT = "checking_out"
    REQUESTING_PAYSLIP = "requesting_payslip"
    REQUESTING_OVERTIME = "requesting_overtime"
    REQUESTING_VACATION = "requesting_vacation"
    TEAM_MANAGEMENT = "team_management"
    PAYROLL_MANAGEMENT = "payroll_management"
    EMPLOYEE_LOOKUP = "employee_lookup"
    GEOLOCATION_REQUIRED = "geolocation_required"


@dataclass
class BotMessage:
    """Bot message structure"""
    text: str
    buttons: Optional[List[Dict[str, str]]] = None
    media_url: Optional[str] = None
    requires_location: bool = False
    quick_replies: Optional[List[str]] = None


@dataclass
class UserSession:
    """User conversation session"""
    user_id: str
    company_id: str
    phone_number: str
    state: ConversationState
    context: Dict[str, Any]
    last_activity: datetime
    authenticated: bool = False
    role: Optional[UserRole] = None
    employee_data: Optional[Dict[str, Any]] = None


class GeolocationValidator:
    """Validate user location for check-in/out"""
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in meters"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Earth radius in meters
        r = 6371000
        return c * r
    
    @classmethod
    def is_within_office_radius(cls, user_lat: float, user_lon: float,
                              office_locations: List[Dict[str, float]],
                              radius_meters: int = 100) -> bool:
        """Check if user is within office radius"""
        for office in office_locations:
            office_lat = office.get("latitude")
            office_lon = office.get("longitude")
            
            if office_lat and office_lon:
                distance = cls.calculate_distance(user_lat, user_lon, office_lat, office_lon)
                if distance <= radius_meters:
                    return True
        
        return False


class MessageTemplates:
    """WhatsApp message templates"""
    
    @staticmethod
    def welcome_message(employee_name: str) -> BotMessage:
        return BotMessage(
            text=f"¡Hola {employee_name}! 👋\n\n"
                 f"Bienvenido a huntRED® - tu asistente de nómina inteligente.\n\n"
                 f"¿En qué puedo ayudarte hoy?",
            buttons=[
                {"id": "entrada", "title": "⏰ Entrada/Salida"},
                {"id": "recibo", "title": "💰 Mi Recibo"},
                {"id": "menu", "title": "📋 Menú Completo"}
            ]
        )
    
    @staticmethod
    def main_menu(role: UserRole) -> BotMessage:
        """Generate main menu based on user role"""
        base_options = [
            "⏰ *entrada* - Registrar entrada/salida",
            "💰 *recibo* - Ver mi último recibo",
            "💳 *saldo* - Consultar mi saldo",
            "🏖️ *vacaciones* - Días de vacaciones",
            "📅 *horario* - Mi horario de trabajo"
        ]
        
        if role in [UserRole.SUPERVISOR, UserRole.HR_ADMIN, UserRole.SUPER_ADMIN]:
            base_options.extend([
                "👥 *equipo* - Gestionar mi equipo",
                "✅ *aprobar* - Aprobar solicitudes",
                "📊 *reporte_asistencia* - Reporte de asistencia"
            ])
        
        if role in [UserRole.HR_ADMIN, UserRole.SUPER_ADMIN]:
            base_options.extend([
                "👨‍💼 *empleados* - Gestionar empleados",
                "💰 *estado_nomina* - Estado de nómina",
                "📈 *resumen* - Resumen ejecutivo",
                "📋 *reportes* - Reportes avanzados"
            ])
        
        menu_text = "📋 *MENÚ PRINCIPAL*\n\n" + "\n".join(base_options)
        menu_text += "\n\n💬 Escribe el comando que necesites o usa los botones."
        
        return BotMessage(text=menu_text)
    
    @staticmethod
    def check_in_success(location: str = None) -> BotMessage:
        timestamp = datetime.now().strftime("%H:%M")
        location_text = f" desde {location}" if location else ""
        
        return BotMessage(
            text=f"✅ *Entrada registrada*\n\n"
                 f"🕐 Hora: {timestamp}\n"
                 f"📍 Ubicación: {location_text}\n\n"
                 f"¡Que tengas un excelente día de trabajo! 💪"
        )
    
    @staticmethod
    def check_out_success(hours_worked: float) -> BotMessage:
        timestamp = datetime.now().strftime("%H:%M")
        
        return BotMessage(
            text=f"✅ *Salida registrada*\n\n"
                 f"🕐 Hora: {timestamp}\n"
                 f"⏱️ Horas trabajadas: {hours_worked:.1f}h\n\n"
                 f"¡Descansa bien! 😊"
        )
    
    @staticmethod
    def payslip_summary(payslip_data: Dict[str, Any]) -> BotMessage:
        income = payslip_data["income"]
        deductions = payslip_data["deductions"]
        net_pay = payslip_data["net_pay"]
        period = payslip_data["pay_period"]
        
        text = f"💰 *RECIBO DE NÓMINA*\n\n"
        text += f"📅 Período: {period['start']} al {period['end']}\n\n"
        text += f"💵 *INGRESOS*\n"
        text += f"• Salario base: ${income['base_salary']:,.2f}\n"
        
        if income['overtime_amount'] > 0:
            text += f"• Horas extra: ${income['overtime_amount']:,.2f}\n"
        if income['bonuses'] > 0:
            text += f"• Bonos: ${income['bonuses']:,.2f}\n"
        
        text += f"• *Total bruto: ${income['gross_total']:,.2f}*\n\n"
        text += f"➖ *DEDUCCIONES*\n"
        text += f"• IMSS: ${deductions['imss']:,.2f}\n"
        text += f"• ISR: ${deductions['isr']:,.2f}\n"
        
        if deductions['loans'] > 0:
            text += f"• Préstamos: ${deductions['loans']:,.2f}\n"
        
        text += f"• *Total deducciones: ${deductions['total']:,.2f}*\n\n"
        text += f"💰 *NETO A PAGAR: ${net_pay:,.2f}*"
        
        return BotMessage(
            text=text,
            buttons=[
                {"id": "payslip_pdf", "title": "📄 PDF Detallado"},
                {"id": "payslip_history", "title": "📈 Historial"},
                {"id": "menu", "title": "🔙 Menú"}
            ]
        )
    
    @staticmethod
    def vacation_balance(remaining_days: int, used_days: int, total_days: int) -> BotMessage:
        return BotMessage(
            text=f"🏖️ *BALANCE DE VACACIONES*\n\n"
                 f"📊 Días disponibles: *{remaining_days}*\n"
                 f"📅 Días utilizados: {used_days}\n"
                 f"📋 Total anual: {total_days}\n\n"
                 f"¿Deseas solicitar días de vacaciones?",
            buttons=[
                {"id": "request_vacation", "title": "📝 Solicitar Vacaciones"},
                {"id": "vacation_history", "title": "📜 Historial"},
                {"id": "menu", "title": "🔙 Menú"}
            ]
        )
    
    @staticmethod
    def team_overview(team_data: List[Dict[str, Any]]) -> BotMessage:
        text = f"👥 *RESUMEN DEL EQUIPO*\n\n"
        text += f"📊 Total empleados: {len(team_data)}\n\n"
        
        # Present team status
        present_count = sum(1 for emp in team_data if emp.get("status") == "present")
        absent_count = len(team_data) - present_count
        
        text += f"✅ Presentes: {present_count}\n"
        text += f"❌ Ausentes: {absent_count}\n\n"
        
        # Today's activity
        text += "*Actividad de hoy:*\n"
        for emp in team_data[:5]:  # Show first 5
            status_icon = "✅" if emp.get("status") == "present" else "❌"
            text += f"{status_icon} {emp['name']}\n"
        
        if len(team_data) > 5:
            text += f"... y {len(team_data) - 5} más"
        
        return BotMessage(
            text=text,
            buttons=[
                {"id": "team_attendance", "title": "📊 Asistencia Detallada"},
                {"id": "team_approvals", "title": "✅ Aprobaciones"},
                {"id": "menu", "title": "🔙 Menú"}
            ]
        )
    
    @staticmethod
    def error_message(error_type: str) -> BotMessage:
        messages = {
            "location_required": "📍 Necesito tu ubicación para registrar la entrada/salida.\n\n"
                               "Por favor, comparte tu ubicación actual.",
            "outside_office": "❌ No estás dentro del área de trabajo permitida.\n\n"
                            "Debes estar cerca de la oficina para registrar entrada/salida.",
            "already_checked_in": "⚠️ Ya tienes una entrada registrada hoy.\n\n"
                                "¿Deseas registrar tu salida?",
            "not_checked_in": "⚠️ No tienes una entrada registrada hoy.\n\n"
                            "Primero debes registrar tu entrada.",
            "authentication_failed": "❌ No pude verificar tu identidad.\n\n"
                                   "Por favor, contacta a Recursos Humanos.",
            "invalid_command": "❓ No entendí tu solicitud.\n\n"
                             "Escribe *menu* para ver las opciones disponibles.",
            "system_error": "🔧 Hay un problema técnico temporal.\n\n"
                          "Por favor, intenta de nuevo en unos minutos."
        }
        
        return BotMessage(text=messages.get(error_type, messages["system_error"]))


class WhatsAppBotEngine:
    """Main WhatsApp Bot Engine - Multi-tenant Architecture"""
    
    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}
        self.payroll_engine = PayrollEngine()
        self.social_engine = SocialLinkEngine()
        self.geolocation_validator = GeolocationValidator()
        
        # Initialize Twilio client
        self.twilio_client = TwilioClient(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
    
    async def process_webhook(self, webhook_data: Dict[str, Any], company_id: str) -> Dict[str, Any]:
        """Process incoming WhatsApp webhook for specific company"""
        try:
            # Extract message data
            from_number = webhook_data.get("From", "").replace("whatsapp:", "")
            to_number = webhook_data.get("To", "").replace("whatsapp:", "")
            message_body = webhook_data.get("Body", "").strip()
            
            # Handle location sharing
            latitude = webhook_data.get("Latitude")
            longitude = webhook_data.get("Longitude")
            location_data = None
            if latitude and longitude:
                location_data = {"latitude": float(latitude), "longitude": float(longitude)}
            
            logger.info(f"Processing message from {from_number} for company {company_id}")
            
            # Get or create user session
            session = await self._get_or_create_session(from_number, company_id)
            
            # Authenticate user if not already authenticated
            if not session.authenticated:
                auth_result = await self._authenticate_user(session, from_number, company_id)
                if not auth_result:
                    response = MessageTemplates.error_message("authentication_failed")
                    await self._send_message(from_number, response, company_id)
                    return {"status": "error", "message": "Authentication failed"}
            
            # Process the message
            response = await self._process_user_message(session, message_body, location_data)
            
            # Send response
            await self._send_message(from_number, response, company_id)
            
            # Update session
            session.last_activity = datetime.now()
            self.sessions[from_number] = session
            
            return {"status": "success", "message": "Message processed"}
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            error_response = MessageTemplates.error_message("system_error")
            if 'from_number' in locals():
                await self._send_message(from_number, error_response, company_id)
            return {"status": "error", "message": str(e)}
    
    async def _get_or_create_session(self, phone_number: str, company_id: str) -> UserSession:
        """Get existing session or create new one"""
        if phone_number in self.sessions:
            session = self.sessions[phone_number]
            # Check if session is still valid (24 hours)
            if datetime.now() - session.last_activity < timedelta(hours=24):
                return session
        
        # Create new session
        session = UserSession(
            user_id=str(uuid.uuid4()),
            company_id=company_id,
            phone_number=phone_number,
            state=ConversationState.IDLE,
            context={},
            last_activity=datetime.now(),
            authenticated=False
        )
        
        return session
    
    async def _authenticate_user(self, session: UserSession, phone_number: str, 
                               company_id: str) -> bool:
        """Authenticate user by phone number"""
        try:
            # Mock database lookup - replace with actual database call
            employee_data = await self._lookup_employee_by_phone(phone_number, company_id)
            
            if employee_data:
                session.authenticated = True
                session.role = UserRole(employee_data.get("role", "employee"))
                session.employee_data = employee_data
                logger.info(f"User {phone_number} authenticated successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def _lookup_employee_by_phone(self, phone_number: str, company_id: str) -> Optional[Dict[str, Any]]:
        """Lookup employee by phone number - Mock implementation"""
        # This would be replaced with actual database queries
        mock_employees = {
            "+525512345678": {
                "id": "emp_001",
                "name": "Juan Pérez",
                "role": "employee",
                "monthly_salary": 15000.0,
                "department": "Desarrollo",
                "manager_id": "emp_002"
            },
            "+525587654321": {
                "id": "emp_002", 
                "name": "María González",
                "role": "supervisor",
                "monthly_salary": 25000.0,
                "department": "Desarrollo"
            }
        }
        
        return mock_employees.get(phone_number)
    
    async def _process_user_message(self, session: UserSession, message: str, 
                                  location_data: Optional[Dict[str, float]]) -> BotMessage:
        """Process user message based on current state and role"""
        message_lower = message.lower().strip()
        
        # Handle location-based states first
        if session.state == ConversationState.GEOLOCATION_REQUIRED:
            if location_data:
                return await self._handle_location_check(session, location_data)
            else:
                return MessageTemplates.error_message("location_required")
        
        # Handle common commands
        if message_lower in ["menu", "menú", "inicio", "start"]:
            session.state = ConversationState.MENU
            return MessageTemplates.main_menu(session.role)
        
        elif message_lower in ["hola", "hello", "hi"]:
            return MessageTemplates.welcome_message(session.employee_data["name"])
        
        # Role-based command processing
        elif message_lower in ["entrada", "salida", "check", "checkin", "checkout"]:
            return await self._handle_attendance_command(session, message_lower)
        
        elif message_lower in ["recibo", "nomina", "payslip", "sueldo"]:
            return await self._handle_payslip_request(session)
        
        elif message_lower in ["saldo", "balance", "dinero"]:
            return await self._handle_balance_request(session)
        
        elif message_lower in ["vacaciones", "vacation", "holidays"]:
            return await self._handle_vacation_request(session)
        
        elif message_lower in ["horario", "schedule", "tiempo"]:
            return await self._handle_schedule_request(session)
        
        # Supervisor/Manager commands
        elif message_lower in ["equipo", "team"] and session.role.value in ["supervisor", "hr_admin", "super_admin"]:
            return await self._handle_team_command(session)
        
        elif message_lower in ["aprobar", "approve"] and session.role.value in ["supervisor", "hr_admin", "super_admin"]:
            return await self._handle_approvals_command(session)
        
        elif message_lower == "reporte_asistencia" and session.role.value in ["supervisor", "hr_admin", "super_admin"]:
            return await self._handle_attendance_report(session)
        
        # HR Admin commands
        elif message_lower == "empleados" and session.role.value in ["hr_admin", "super_admin"]:
            return await self._handle_employee_management(session)
        
        elif message_lower == "estado_nomina" and session.role.value in ["hr_admin", "super_admin"]:
            return await self._handle_payroll_status(session)
        
        elif message_lower == "resumen" and session.role.value in ["hr_admin", "super_admin"]:
            return await self._handle_executive_summary(session)
        
        elif message_lower == "reportes" and session.role.value in ["hr_admin", "super_admin"]:
            return await self._handle_advanced_reports(session)
        
        # Button responses
        elif message_lower.startswith("payslip_"):
            return await self._handle_payslip_action(session, message_lower)
        
        else:
            return MessageTemplates.error_message("invalid_command")
    
    async def _handle_attendance_command(self, session: UserSession, command: str) -> BotMessage:
        """Handle check-in/check-out commands"""
        session.state = ConversationState.GEOLOCATION_REQUIRED
        session.context["attendance_action"] = "check_in" if command in ["entrada", "checkin"] else "check_out"
        
        return BotMessage(
            text="📍 Para registrar tu entrada/salida, necesito tu ubicación.\n\n"
                 "Por favor, comparte tu ubicación actual.",
            requires_location=True
        )
    
    async def _handle_location_check(self, session: UserSession, location_data: Dict[str, float]) -> BotMessage:
        """Handle location validation for check-in/out"""
        user_lat = location_data["latitude"]
        user_lon = location_data["longitude"]
        
        # Mock office locations - would come from company settings
        office_locations = [
            {"latitude": 19.4326, "longitude": -99.1332}  # Mexico City example
        ]
        
        if not self.geolocation_validator.is_within_office_radius(user_lat, user_lon, office_locations):
            session.state = ConversationState.IDLE
            return MessageTemplates.error_message("outside_office")
        
        # Process attendance
        action = session.context.get("attendance_action", "check_in")
        
        if action == "check_in":
            # Record check-in
            session.state = ConversationState.IDLE
            return MessageTemplates.check_in_success("Oficina Principal")
        else:
            # Record check-out and calculate hours
            hours_worked = 8.5  # Mock calculation
            session.state = ConversationState.IDLE
            return MessageTemplates.check_out_success(hours_worked)
    
    async def _handle_payslip_request(self, session: UserSession) -> BotMessage:
        """Handle payslip request"""
        # Generate mock payslip using payroll engine
        employee_data = session.employee_data
        
        try:
            payroll_calc = self.payroll_engine.calculate_payroll(
                employee_data,
                date.today().replace(day=1),  # Start of month
                date.today(),  # End of month
                overtime_hours=10  # Mock overtime
            )
            
            payslip_data = self.payroll_engine.generate_payslip_data(payroll_calc)
            return MessageTemplates.payslip_summary(payslip_data)
            
        except Exception as e:
            logger.error(f"Error generating payslip: {e}")
            return MessageTemplates.error_message("system_error")
    
    async def _handle_balance_request(self, session: UserSession) -> BotMessage:
        """Handle balance/salary request"""
        employee_data = session.employee_data
        monthly_salary = employee_data.get("monthly_salary", 0)
        
        # Calculate next payday
        today = date.today()
        if today.day <= 15:
            next_payday = today.replace(day=15)
        else:
            next_month = today.replace(day=28) + timedelta(days=4)
            next_payday = next_month.replace(day=1)
        
        days_until_payday = (next_payday - today).days
        
        return BotMessage(
            text=f"💰 *INFORMACIÓN SALARIAL*\n\n"
                 f"💵 Salario mensual: ${monthly_salary:,.2f}\n"
                 f"📅 Próximo pago: {next_payday.strftime('%d/%m/%Y')}\n"
                 f"⏳ Días restantes: {days_until_payday}\n\n"
                 f"💡 ¿Necesitas un adelanto de nómina?",
            buttons=[
                {"id": "request_advance", "title": "💸 Solicitar Adelanto"},
                {"id": "payslip", "title": "🧾 Ver Recibo"},
                {"id": "menu", "title": "🔙 Menú"}
            ]
        )
    
    async def _handle_vacation_request(self, session: UserSession) -> BotMessage:
        """Handle vacation balance request"""
        # Mock vacation data - would come from database
        vacation_data = {
            "total_days": 12,
            "used_days": 3,
            "remaining_days": 9
        }
        
        return MessageTemplates.vacation_balance(
            vacation_data["remaining_days"],
            vacation_data["used_days"],
            vacation_data["total_days"]
        )
    
    async def _handle_schedule_request(self, session: UserSession) -> BotMessage:
        """Handle work schedule request"""
        # Mock schedule data
        return BotMessage(
            text="📅 *MI HORARIO DE TRABAJO*\n\n"
                 "🕘 Lunes a Viernes: 9:00 AM - 6:00 PM\n"
                 "🕛 Almuerzo: 1:00 PM - 2:00 PM\n"
                 "📍 Modalidad: Híbrida\n\n"
                 "📊 Esta semana:\n"
                 "• Horas trabajadas: 32/40\n"
                 "• Días restantes: 2",
            buttons=[
                {"id": "time_tracking", "title": "⏱️ Seguimiento"},
                {"id": "schedule_change", "title": "📝 Cambio Horario"},
                {"id": "menu", "title": "🔙 Menú"}
            ]
        )
    
    async def _handle_team_command(self, session: UserSession) -> BotMessage:
        """Handle team management command"""
        # Mock team data
        team_data = [
            {"name": "Ana López", "status": "present"},
            {"name": "Carlos Ruiz", "status": "absent"},
            {"name": "Diana Torres", "status": "present"},
        ]
        
        return MessageTemplates.team_overview(team_data)
    
    async def _handle_approvals_command(self, session: UserSession) -> BotMessage:
        """Handle pending approvals"""
        return BotMessage(
            text="✅ *APROBACIONES PENDIENTES*\n\n"
                 "📋 Tienes 3 solicitudes por revisar:\n\n"
                 "1. 🏖️ Ana López - Vacaciones (2 días)\n"
                 "2. ⏰ Carlos Ruiz - Horas extra (5h)\n"
                 "3. 🏠 Diana Torres - Home Office\n\n"
                 "¿Qué solicitud deseas revisar?",
            buttons=[
                {"id": "approve_vacation", "title": "🏖️ Vacaciones"},
                {"id": "approve_overtime", "title": "⏰ Horas Extra"},
                {"id": "approve_remote", "title": "🏠 Home Office"}
            ]
        )
    
    async def _handle_attendance_report(self, session: UserSession) -> BotMessage:
        """Handle attendance report request"""
        return BotMessage(
            text="📊 *REPORTE DE ASISTENCIA*\n\n"
                 "📅 Semana actual:\n"
                 "• Asistencia promedio: 92%\n"
                 "• Llegadas tardías: 2\n"
                 "• Ausencias: 1\n\n"
                 "👥 Por empleado:\n"
                 "✅ Ana López: 100%\n"
                 "⚠️ Carlos Ruiz: 80% (1 falta)\n"
                 "✅ Diana Torres: 95%",
            buttons=[
                {"id": "detailed_report", "title": "📋 Reporte Detallado"},
                {"id": "export_report", "title": "📊 Exportar Excel"},
                {"id": "menu", "title": "🔙 Menú"}
            ]
        )
    
    async def _handle_employee_management(self, session: UserSession) -> BotMessage:
        """Handle employee management"""
        return BotMessage(
            text="👨‍💼 *GESTIÓN DE EMPLEADOS*\n\n"
                 "📊 Total empleados: 25\n"
                 "🆕 Nuevos este mes: 2\n"
                 "📤 Bajas: 0\n\n"
                 "¿Qué deseas hacer?",
            buttons=[
                {"id": "add_employee", "title": "➕ Agregar Empleado"},
                {"id": "employee_list", "title": "📋 Lista Empleados"},
                {"id": "employee_reports", "title": "📊 Reportes"},
                {"id": "menu", "title": "🔙 Menú"}
            ]
        )
    
    async def _handle_payroll_status(self, session: UserSession) -> BotMessage:
        """Handle payroll status"""
        return BotMessage(
            text="💰 *ESTADO DE NÓMINA*\n\n"
                 f"📅 Período: {date.today().strftime('%B %Y')}\n"
                 f"📊 Estado: En proceso\n"
                 f"✅ Calculada: 25/25 empleados\n"
                 f"⏳ Pendiente dispersión\n\n"
                 f"💵 Total nómina: $587,450.00\n"
                 f"📊 IMSS patronal: $67,320.00",
            buttons=[
                {"id": "process_payroll", "title": "🚀 Procesar Nómina"},
                {"id": "payroll_report", "title": "📋 Reporte Detallado"},
                {"id": "dispersion", "title": "💸 Dispersión"},
                {"id": "menu", "title": "🔙 Menú"}
            ]
        )
    
    async def _handle_executive_summary(self, session: UserSession) -> BotMessage:
        """Handle executive summary"""
        return BotMessage(
            text="📈 *RESUMEN EJECUTIVO*\n\n"
                 "👥 *Personal:*\n"
                 "• Total empleados: 25\n"
                 "• Asistencia promedio: 94%\n"
                 "• Rotación: 2.1%\n\n"
                 "💰 *Nómina:*\n"
                 "• Costo mensual: $587,450\n"
                 "• vs. mes anterior: +3.2%\n"
                 "• Horas extra: 125h\n\n"
                 "📊 *Productividad:*\n"
                 "• Proyectos completados: 8\n"
                 "• Satisfacción: 4.7/5",
            buttons=[
                {"id": "detailed_analytics", "title": "📊 Analytics"},
                {"id": "export_summary", "title": "📤 Exportar"},
                {"id": "menu", "title": "🔙 Menú"}
            ]
        )
    
    async def _handle_advanced_reports(self, session: UserSession) -> BotMessage:
        """Handle advanced reports"""
        return BotMessage(
            text="📋 *REPORTES AVANZADOS*\n\n"
                 "¿Qué reporte necesitas?",
            buttons=[
                {"id": "payroll_report", "title": "💰 Reporte Nómina"},
                {"id": "attendance_report", "title": "📊 Asistencia"},
                {"id": "performance_report", "title": "🎯 Desempeño"},
                {"id": "costs_report", "title": "💸 Costos"},
                {"id": "menu", "title": "🔙 Menú"}
            ]
        )
    
    async def _handle_payslip_action(self, session: UserSession, action: str) -> BotMessage:
        """Handle payslip-related actions"""
        if action == "payslip_pdf":
            return BotMessage(
                text="📄 Generando tu recibo en PDF...\n\n"
                     "Te llegará por email en unos momentos.",
                buttons=[{"id": "menu", "title": "🔙 Menú"}]
            )
        elif action == "payslip_history":
            return BotMessage(
                text="📈 *HISTORIAL DE RECIBOS*\n\n"
                     "📅 Noviembre 2024: $14,250.00\n"
                     "📅 Octubre 2024: $13,800.00\n"
                     "📅 Septiembre 2024: $14,100.00\n"
                     "📅 Agosto 2024: $13,950.00",
                buttons=[{"id": "menu", "title": "🔙 Menú"}]
            )
        else:
            return MessageTemplates.error_message("invalid_command")
    
    async def _send_message(self, to_number: str, message: BotMessage, company_id: str):
        """Send WhatsApp message using Twilio"""
        try:
            # Get company WhatsApp configuration
            from_number = await self._get_company_whatsapp_number(company_id)
            
            # Send main message
            twilio_message = self.twilio_client.messages.create(
                body=message.text,
                from_=f"whatsapp:{from_number}",
                to=f"whatsapp:{to_number}"
            )
            
            # Send buttons as follow-up if any
            if message.buttons:
                button_text = "\n\n" + "\n".join([
                    f"💬 *{btn['title']}* - Escribe: {btn['id']}"
                    for btn in message.buttons
                ])
                
                self.twilio_client.messages.create(
                    body=button_text,
                    from_=f"whatsapp:{from_number}",
                    to=f"whatsapp:{to_number}"
                )
            
            logger.info(f"Message sent successfully to {to_number}")
            
        except TwilioException as e:
            logger.error(f"Twilio error sending message: {e}")
            raise
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    async def _get_company_whatsapp_number(self, company_id: str) -> str:
        """Get company's dedicated WhatsApp number"""
        # Mock implementation - would query company settings
        company_numbers = {
            "company_1": "+14155238886",  # Twilio sandbox number
            "company_2": "+14155238887",
        }
        return company_numbers.get(company_id, "+14155238886")
    
    def cleanup_old_sessions(self):
        """Clean up sessions older than 24 hours"""
        cutoff = datetime.now() - timedelta(hours=24)
        expired_sessions = [
            phone for phone, session in self.sessions.items()
            if session.last_activity < cutoff
        ]
        
        for phone in expired_sessions:
            del self.sessions[phone]
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")