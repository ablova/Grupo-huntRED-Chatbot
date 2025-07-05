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
from ..services.advanced_feedback_service import AdvancedFeedbackService, FeedbackType

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
    FEEDBACK_RESPONSE = "feedback_response"
    FEEDBACK_QUICK_RATING = "feedback_quick_rating"


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
            "📅 *horario* - Mi horario de trabajo",
            "📝 *feedback* - Responder feedback pendiente"
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
    
    @staticmethod
    def feedback_notification(feedback_type: str, context: Dict[str, Any]) -> BotMessage:
        """Generate feedback notification message"""
        
        if feedback_type == "client_interview":
            candidate_name = context.get("candidate_name", "el candidato")
            job_title = context.get("job_title", "la posición")
            
            return BotMessage(
                text=f"📝 *FEEDBACK SOLICITADO*\n\n"
                     f"Se solicita tu feedback sobre la entrevista:\n\n"
                     f"👤 Candidato: {candidate_name}\n"
                     f"💼 Posición: {job_title}\n\n"
                     f"*Responde rápidamente:*",
                quick_replies=[
                    "⭐ Excelente (9-10)",
                    "👍 Bueno (7-8)", 
                    "👌 Regular (5-6)",
                    "👎 Malo (1-4)",
                    "📝 Feedback detallado"
                ]
            )
        
        elif feedback_type == "candidate_process":
            job_title = context.get("job_title", "la posición")
            company_name = context.get("company_name", "la empresa")
            
            return BotMessage(
                text=f"📝 *FEEDBACK SOLICITADO*\n\n"
                     f"¿Cómo fue tu experiencia en el proceso?\n\n"
                     f"💼 Posición: {job_title}\n"
                     f"🏢 Empresa: {company_name}\n\n"
                     f"*Responde rápidamente:*",
                quick_replies=[
                    "😊 Muy satisfecho",
                    "🙂 Satisfecho",
                    "😐 Neutral",
                    "😞 Insatisfecho",
                    "📝 Feedback detallado"
                ]
            )
        
        elif feedback_type == "consultant_performance":
            recruiter_name = context.get("recruiter_name", "el recruiter")
            
            return BotMessage(
                text=f"📝 *EVALUACIÓN DE PERFORMANCE*\n\n"
                     f"Evalúa el desempeño de:\n"
                     f"👨‍💼 {recruiter_name}\n\n"
                     f"*Responde rápidamente:*",
                quick_replies=[
                    "🌟 Excelente",
                    "👍 Muy bueno",
                    "👌 Bueno",
                    "👎 Necesita mejorar",
                    "📝 Evaluación detallada"
                ]
            )
        
        elif feedback_type == "super_admin_system":
            return BotMessage(
                text=f"📝 *EVALUACIÓN DEL SISTEMA*\n\n"
                     f"Evalúa el rendimiento general del sistema:\n\n"
                     f"*Responde rápidamente:*",
                quick_replies=[
                    "🚀 Excelente",
                    "✅ Muy bueno",
                    "👌 Bueno",
                    "⚠️ Necesita mejoras",
                    "📝 Evaluación detallada"
                ]
            )
        
        elif feedback_type == "recruiter_client":
            client_name = context.get("client_name", "el cliente")
            
            return BotMessage(
                text=f"📝 *FEEDBACK SOBRE CLIENTE*\n\n"
                     f"¿Cómo fue la colaboración con:\n"
                     f"🏢 {client_name}\n\n"
                     f"*Responde rápidamente:*",
                quick_replies=[
                    "🤝 Excelente",
                    "👍 Muy buena",
                    "👌 Buena",
                    "👎 Regular",
                    "📝 Feedback detallado"
                ]
            )
        
        return BotMessage(text="📝 Se ha solicitado tu feedback. Por favor responde.")
    
    @staticmethod
    def feedback_quick_response_form(feedback_type: str, quick_rating: str) -> BotMessage:
        """Generate quick response form based on rating"""
        
        if feedback_type == "client_interview":
            if quick_rating in ["⭐ Excelente (9-10)", "👍 Bueno (7-8)"]:
                return BotMessage(
                    text=f"✅ *Calificación: {quick_rating}*\n\n"
                         f"*Responde rápidamente:*\n\n"
                         f"1️⃣ ¿Principales fortalezas del candidato?",
                    quick_replies=[
                        "💻 Técnicamente sólido",
                        "🗣️ Excelente comunicación",
                        "🎯 Experiencia relevante",
                        "🤝 Buen fit cultural",
                        "📝 Escribir respuesta"
                    ]
                )
            else:
                return BotMessage(
                    text=f"⚠️ *Calificación: {quick_rating}*\n\n"
                         f"*Responde rápidamente:*\n\n"
                         f"1️⃣ ¿Principales áreas de preocupación?",
                    quick_replies=[
                        "💻 Habilidades técnicas",
                        "🗣️ Comunicación",
                        "📚 Falta experiencia",
                        "🤝 No fit cultural",
                        "📝 Escribir respuesta"
                    ]
                )
        
        elif feedback_type == "candidate_process":
            return BotMessage(
                text=f"✅ *Experiencia: {quick_rating}*\n\n"
                     f"*¿Qué mejorarías del proceso?*",
                quick_replies=[
                    "⏰ Tiempos de respuesta",
                    "📞 Comunicación",
                    "📋 Claridad del proceso",
                    "🤝 Trato del recruiter",
                    "📝 Escribir sugerencia"
                ]
            )
        
        return BotMessage(
            text=f"✅ *Calificación registrada: {quick_rating}*\n\n"
                 f"¿Deseas agregar comentarios adicionales?",
            quick_replies=[
                "✅ Enviar así",
                "📝 Agregar comentarios",
                "🔙 Menú principal"
            ]
        )
    
    @staticmethod
    def feedback_completion_success(feedback_type: str) -> BotMessage:
        """Feedback completion confirmation"""
        type_names = {
            "client_interview": "entrevista",
            "candidate_process": "proceso",
            "consultant_performance": "performance",
            "super_admin_system": "sistema",
            "recruiter_client": "colaboración"
        }
        
        type_name = type_names.get(feedback_type, "feedback")
        
        return BotMessage(
            text=f"✅ *FEEDBACK ENVIADO*\n\n"
                 f"Gracias por tu feedback sobre {type_name}.\n\n"
                 f"Tu respuesta ha sido registrada y será analizada para mejorar nuestros servicios.\n\n"
                 f"🎯 *Próximos pasos automáticos generados*",
            buttons=[
                {"id": "menu", "title": "🔙 Menú Principal"},
                {"id": "feedback_history", "title": "📜 Historial"}
            ]
        )
    
    @staticmethod
    def pending_feedback_reminder(pending_count: int) -> BotMessage:
        """Reminder for pending feedback"""
        return BotMessage(
            text=f"📝 *RECORDATORIO*\n\n"
                 f"Tienes {pending_count} feedback(s) pendiente(s) de responder.\n\n"
                 f"¿Deseas responderlos ahora?",
            buttons=[
                {"id": "respond_feedback", "title": "📝 Responder Ahora"},
                {"id": "remind_later", "title": "⏰ Recordar Después"},
                {"id": "menu", "title": "🔙 Menú"}
            ]
        )


class WhatsAppBotEngine:
    """Main WhatsApp Bot Engine - Multi-tenant Architecture"""
    
    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}
        self.payroll_engine = PayrollEngine()
        self.social_engine = SocialLinkEngine()
        self.geolocation_validator = GeolocationValidator()
        self.feedback_service = AdvancedFeedbackService()
        
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
        
        # Feedback commands
        elif message_lower in ["feedback", "responder_feedback", "respond_feedback"]:
            return await self._handle_feedback_command(session)
        
        elif message_lower in ["feedback_pendientes", "pending_feedback"]:
            return await self._handle_pending_feedback(session)
        
        # Button responses
        elif message_lower.startswith("payslip_"):
            return await self._handle_payslip_action(session, message_lower)
        
        # Feedback quick responses
        elif session.state == ConversationState.FEEDBACK_RESPONSE:
            return await self._handle_feedback_response(session, message)
        
        elif session.state == ConversationState.FEEDBACK_QUICK_RATING:
            return await self._handle_feedback_quick_rating(session, message)
        
        # Check for feedback quick replies
        elif any(keyword in message for keyword in ["⭐", "👍", "👌", "👎", "😊", "🙂", "😐", "😞", "🌟", "🚀", "✅", "⚠️", "🤝"]):
            return await self._handle_feedback_quick_reply(session, message)
        
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
    
    async def _handle_feedback_command(self, session: UserSession) -> BotMessage:
        """Handle feedback command - show pending feedback"""
        try:
            await self.feedback_service.initialize_service()
            
            # Get pending feedback for user
            pending_feedback = await self._get_pending_feedback_for_user(session)
            
            if not pending_feedback:
                return BotMessage(
                    text="✅ *NO HAY FEEDBACK PENDIENTE*\n\n"
                         "No tienes solicitudes de feedback pendientes en este momento.\n\n"
                         "¡Gracias por mantener tus evaluaciones al día! 👍",
                    buttons=[
                        {"id": "menu", "title": "🔙 Menú Principal"}
                    ]
                )
            
            # Show first pending feedback
            first_feedback = pending_feedback[0]
            session.context["current_feedback"] = first_feedback
            session.state = ConversationState.FEEDBACK_RESPONSE
            
            return MessageTemplates.feedback_notification(
                first_feedback["type"], 
                first_feedback["context"]
            )
            
        except Exception as e:
            logger.error(f"Error handling feedback command: {e}")
            return MessageTemplates.error_message("system_error")
    
    async def _handle_pending_feedback(self, session: UserSession) -> BotMessage:
        """Show list of pending feedback"""
        try:
            pending_feedback = await self._get_pending_feedback_for_user(session)
            
            if not pending_feedback:
                return BotMessage(
                    text="✅ No tienes feedback pendiente.",
                    buttons=[{"id": "menu", "title": "🔙 Menú"}]
                )
            
            text = f"📝 *FEEDBACK PENDIENTE*\n\n"
            text += f"Tienes {len(pending_feedback)} solicitud(es) pendiente(s):\n\n"
            
            for i, feedback in enumerate(pending_feedback[:5], 1):
                type_name = self._get_feedback_type_name(feedback["type"])
                text += f"{i}️⃣ {type_name}\n"
            
            if len(pending_feedback) > 5:
                text += f"... y {len(pending_feedback) - 5} más"
            
            return BotMessage(
                text=text,
                buttons=[
                    {"id": "respond_feedback", "title": "📝 Responder Ahora"},
                    {"id": "menu", "title": "🔙 Menú"}
                ]
            )
            
        except Exception as e:
            logger.error(f"Error getting pending feedback: {e}")
            return MessageTemplates.error_message("system_error")
    
    async def _handle_feedback_response(self, session: UserSession, message: str) -> BotMessage:
        """Handle feedback response"""
        current_feedback = session.context.get("current_feedback")
        if not current_feedback:
            session.state = ConversationState.IDLE
            return MessageTemplates.error_message("system_error")
        
        # Store the response
        if "responses" not in session.context:
            session.context["responses"] = {}
        
        session.context["responses"]["main_response"] = message
        
        # Move to completion
        return await self._complete_feedback_submission(session)
    
    async def _handle_feedback_quick_reply(self, session: UserSession, message: str) -> BotMessage:
        """Handle quick reply feedback responses"""
        current_feedback = session.context.get("current_feedback")
        if not current_feedback:
            # Check if this is a new feedback notification response
            return await self._handle_potential_feedback_start(session, message)
        
        feedback_type = current_feedback["type"]
        
        # Convert quick reply to structured response
        quick_response = self._convert_quick_reply_to_response(message, feedback_type)
        
        if "responses" not in session.context:
            session.context["responses"] = {}
        
        session.context["responses"].update(quick_response)
        
        # Check if we need more information
        if message == "📝 Feedback detallado" or message == "📝 Evaluación detallada":
            session.state = ConversationState.FEEDBACK_RESPONSE
            return BotMessage(
                text="📝 *FEEDBACK DETALLADO*\n\n"
                     "Por favor, escribe tu feedback detallado:"
            )
        
        # Show quick follow-up form
        session.state = ConversationState.FEEDBACK_QUICK_RATING
        return MessageTemplates.feedback_quick_response_form(feedback_type, message)
    
    async def _handle_feedback_quick_rating(self, session: UserSession, message: str) -> BotMessage:
        """Handle quick rating follow-up responses"""
        current_feedback = session.context.get("current_feedback")
        if not current_feedback:
            session.state = ConversationState.IDLE
            return MessageTemplates.error_message("system_error")
        
        if message == "✅ Enviar así":
            return await self._complete_feedback_submission(session)
        
        elif message == "📝 Agregar comentarios":
            session.state = ConversationState.FEEDBACK_RESPONSE
            return BotMessage(
                text="📝 *COMENTARIOS ADICIONALES*\n\n"
                     "Escribe tus comentarios adicionales:"
            )
        
        elif message == "🔙 Menú principal":
            session.state = ConversationState.IDLE
            return MessageTemplates.main_menu(session.role)
        
        else:
            # Store additional response
            if "responses" not in session.context:
                session.context["responses"] = {}
            
            # Convert quick reply to structured response
            feedback_type = current_feedback["type"]
            additional_response = self._convert_quick_reply_to_response(message, feedback_type)
            session.context["responses"].update(additional_response)
            
            return await self._complete_feedback_submission(session)
    
    async def _complete_feedback_submission(self, session: UserSession) -> BotMessage:
        """Complete and submit feedback"""
        try:
            current_feedback = session.context.get("current_feedback")
            responses = session.context.get("responses", {})
            
            if not current_feedback:
                return MessageTemplates.error_message("system_error")
            
            # Submit feedback to service
            result = await self.feedback_service.submit_feedback(
                feedback_request_id=current_feedback["id"],
                responses=responses,
                respondent_notes=responses.get("main_response", "")
            )
            
            if result["success"]:
                # Clear feedback context
                session.context.pop("current_feedback", None)
                session.context.pop("responses", None)
                session.state = ConversationState.IDLE
                
                return MessageTemplates.feedback_completion_success(current_feedback["type"])
            else:
                return MessageTemplates.error_message("system_error")
                
        except Exception as e:
            logger.error(f"Error completing feedback submission: {e}")
            return MessageTemplates.error_message("system_error")
    
    async def _get_pending_feedback_for_user(self, session: UserSession) -> List[Dict[str, Any]]:
        """Get pending feedback requests for user"""
        # Mock implementation - would query actual feedback service
        user_id = session.employee_data.get("id")
        user_role = session.role.value
        
        # Simulate pending feedback based on role
        pending_feedback = []
        
        if user_role in ["hr_admin", "super_admin"]:
            pending_feedback.append({
                "id": "FB_SYSTEM_001",
                "type": "super_admin_system",
                "context": {
                    "period_start": "2024-11-01",
                    "period_end": "2024-12-15"
                }
            })
        
        if user_role in ["supervisor", "hr_admin", "super_admin"]:
            pending_feedback.append({
                "id": "FB_CONSULTANT_001", 
                "type": "consultant_performance",
                "context": {
                    "recruiter_name": "María González",
                    "period_start": "2024-11-01"
                }
            })
        
        # Simulate client feedback
        pending_feedback.append({
            "id": "FB_CLIENT_001",
            "type": "client_interview", 
            "context": {
                "candidate_name": "Juan Pérez",
                "job_title": "Senior Developer"
            }
        })
        
        return pending_feedback
    
    def _get_feedback_type_name(self, feedback_type: str) -> str:
        """Get human-readable feedback type name"""
        type_names = {
            "client_interview": "📝 Feedback de Entrevista",
            "candidate_process": "📝 Feedback de Proceso", 
            "consultant_performance": "📝 Evaluación de Performance",
            "super_admin_system": "📝 Evaluación de Sistema",
            "recruiter_client": "📝 Feedback de Cliente"
        }
        return type_names.get(feedback_type, "📝 Feedback")
    
    def _convert_quick_reply_to_response(self, message: str, feedback_type: str) -> Dict[str, Any]:
        """Convert quick reply to structured response"""
        
        if feedback_type == "client_interview":
            if "⭐ Excelente" in message:
                return {"technical_fit": 9, "cultural_fit": 9, "overall_rating": "excellent"}
            elif "👍 Bueno" in message:
                return {"technical_fit": 7, "cultural_fit": 7, "overall_rating": "good"}
            elif "👌 Regular" in message:
                return {"technical_fit": 5, "cultural_fit": 5, "overall_rating": "regular"}
            elif "👎 Malo" in message:
                return {"technical_fit": 3, "cultural_fit": 3, "overall_rating": "poor"}
            elif "💻 Técnicamente sólido" in message:
                return {"strengths_observed": "Técnicamente sólido"}
            elif "🗣️ Excelente comunicación" in message:
                return {"strengths_observed": "Excelente comunicación"}
            elif "🎯 Experiencia relevante" in message:
                return {"strengths_observed": "Experiencia relevante"}
            elif "🤝 Buen fit cultural" in message:
                return {"strengths_observed": "Buen fit cultural"}
        
        elif feedback_type == "candidate_process":
            if "😊 Muy satisfecho" in message:
                return {"overall_satisfaction": 9, "process_clarity": 9}
            elif "🙂 Satisfecho" in message:
                return {"overall_satisfaction": 7, "process_clarity": 7}
            elif "😐 Neutral" in message:
                return {"overall_satisfaction": 5, "process_clarity": 5}
            elif "😞 Insatisfecho" in message:
                return {"overall_satisfaction": 3, "process_clarity": 3}
            elif "⏰ Tiempos de respuesta" in message:
                return {"improvement_suggestions": "Mejorar tiempos de respuesta"}
            elif "📞 Comunicación" in message:
                return {"improvement_suggestions": "Mejorar comunicación"}
        
        elif feedback_type == "consultant_performance":
            if "🌟 Excelente" in message:
                return {"recruiter_evaluation": 9, "overall_assessment": "Altamente recomendado"}
            elif "👍 Muy bueno" in message:
                return {"recruiter_evaluation": 8, "overall_assessment": "Recomendado"}
            elif "👌 Bueno" in message:
                return {"recruiter_evaluation": 6, "overall_assessment": "Aceptable"}
            elif "👎 Necesita mejorar" in message:
                return {"recruiter_evaluation": 4, "overall_assessment": "Necesita mejoras"}
        
        return {"quick_response": message}
    
    async def _handle_potential_feedback_start(self, session: UserSession, message: str) -> BotMessage:
        """Handle potential start of feedback from notification"""
        # Check if user has pending feedback and this looks like a response
        pending_feedback = await self._get_pending_feedback_for_user(session)
        
        if pending_feedback and any(keyword in message for keyword in ["⭐", "👍", "👌", "👎", "😊", "🙂", "😐", "😞"]):
            # Start feedback process with first pending
            first_feedback = pending_feedback[0]
            session.context["current_feedback"] = first_feedback
            session.state = ConversationState.FEEDBACK_RESPONSE
            
            return await self._handle_feedback_quick_reply(session, message)
        
        return MessageTemplates.error_message("invalid_command")
    
    async def send_feedback_notification(self, phone_number: str, company_id: str, 
                                       feedback_type: str, context: Dict[str, Any]):
        """Send feedback notification to user"""
        try:
            message = MessageTemplates.feedback_notification(feedback_type, context)
            await self._send_message(phone_number, message, company_id)
            logger.info(f"Feedback notification sent to {phone_number}")
            
        except Exception as e:
            logger.error(f"Error sending feedback notification: {e}")
    
    async def send_feedback_reminder(self, phone_number: str, company_id: str, pending_count: int):
        """Send feedback reminder to user"""
        try:
            message = MessageTemplates.pending_feedback_reminder(pending_count)
            await self._send_message(phone_number, message, company_id)
            logger.info(f"Feedback reminder sent to {phone_number}")
            
        except Exception as e:
            logger.error(f"Error sending feedback reminder: {e}")