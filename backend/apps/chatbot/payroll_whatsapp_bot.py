"""
WhatsApp Payroll Bot huntRED® v2
=================================

Funcionalidades:
- Bot WhatsApp dedicado por cliente
- Multi-tenant architecture
- Comandos completos de nómina
- Check-in/out con geolocalización
- Self-service empleados
- Consultas de recibos y pagos
- Notificaciones automáticas
- Reportes por WhatsApp
- Integración completa con Payroll Engine
"""

import asyncio
import uuid
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import re
from geopy.distance import geodesic
import qrcode
import io
import base64

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Tipos de mensajes WhatsApp."""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    LOCATION = "location"
    AUDIO = "audio"
    VIDEO = "video"
    BUTTON = "button"
    LIST = "list"

class CommandType(Enum):
    """Tipos de comandos disponibles."""
    # Empleados
    CHECKIN = "checkin"
    CHECKOUT = "checkout"
    PAYSLIP = "recibo"
    BALANCE = "saldo"
    VACATION_BALANCE = "vacaciones"
    SCHEDULE = "horario"
    
    # Administradores
    PAYROLL_STATUS = "nomina_estado"
    EMPLOYEE_LIST = "empleados"
    PAYROLL_SUMMARY = "resumen_nomina"
    APPROVE_PAYROLL = "aprobar_nomina"
    REPORTS = "reportes"
    
    # Generales
    HELP = "ayuda"
    MENU = "menu"
    REGISTER = "registro"

class UserRole(Enum):
    """Roles de usuario en el sistema."""
    EMPLOYEE = "employee"
    SUPERVISOR = "supervisor"
    HR_ADMIN = "hr_admin"
    SUPER_ADMIN = "super_admin"

@dataclass
class WhatsAppUser:
    """Usuario de WhatsApp en el sistema."""
    phone_number: str
    client_id: str
    
    # Información del usuario
    name: str = ""
    role: UserRole = UserRole.EMPLOYEE
    employee_id: Optional[str] = None
    
    # Configuración
    language: str = "es"
    timezone: str = "America/Mexico_City"
    notifications_enabled: bool = True
    
    # Estado de conversación
    current_flow: Optional[str] = None
    flow_step: int = 0
    temp_data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadatos
    registered_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    total_interactions: int = 0

@dataclass
class CheckInOut:
    """Registro de entrada/salida."""
    id: str
    employee_id: str
    client_id: str
    
    # Información del registro
    action_type: str  # "checkin" o "checkout"
    timestamp: datetime
    
    # Geolocalización
    latitude: float
    longitude: float
    location_address: str = ""
    
    # Validación
    is_valid_location: bool = True
    distance_from_office: float = 0.0  # metros
    
    # Metadatos
    device_info: str = ""
    ip_address: str = ""
    notes: str = ""

@dataclass
class ClientConfiguration:
    """Configuración específica del cliente."""
    client_id: str
    company_name: str
    
    # Configuración WhatsApp
    whatsapp_number: str
    whatsapp_token: str
    webhook_url: str
    
    # Configuración de ubicación
    office_locations: List[Dict[str, Any]] = field(default_factory=list)
    max_distance_meters: float = 100.0  # Radio permitido
    
    # Configuración de horarios
    work_schedule: Dict[str, Any] = field(default_factory=dict)
    timezone: str = "America/Mexico_City"
    
    # Configuración de notificaciones
    payroll_notifications: bool = True
    attendance_reminders: bool = True
    
    # Personalización
    welcome_message: str = ""
    company_logo_url: str = ""
    
    # Administradores
    admin_phones: List[str] = field(default_factory=list)
    hr_phones: List[str] = field(default_factory=list)

class PayrollWhatsAppBot:
    """Bot principal de WhatsApp para nómina."""
    
    def __init__(self):
        self.users: Dict[str, WhatsAppUser] = {}  # phone -> user
        self.client_configs: Dict[str, ClientConfiguration] = {}
        self.checkins: Dict[str, List[CheckInOut]] = {}  # employee_id -> checkins
        self.active_flows: Dict[str, str] = {}  # phone -> flow_name
        
        # Importar PayrollEngine
        from ..payroll.payroll_engine import PayrollEngine
        self.payroll_engine = PayrollEngine()
        
        # Comandos disponibles
        self.commands = {
            # Comandos de empleados
            "entrada": CommandType.CHECKIN,
            "checkin": CommandType.CHECKIN,
            "salida": CommandType.CHECKOUT,
            "checkout": CommandType.CHECKOUT,
            "recibo": CommandType.PAYSLIP,
            "nomina": CommandType.PAYSLIP,
            "saldo": CommandType.BALANCE,
            "vacaciones": CommandType.VACATION_BALANCE,
            "horario": CommandType.SCHEDULE,
            
            # Comandos administrativos
            "estado_nomina": CommandType.PAYROLL_STATUS,
            "empleados": CommandType.EMPLOYEE_LIST,
            "resumen": CommandType.PAYROLL_SUMMARY,
            "aprobar": CommandType.APPROVE_PAYROLL,
            "reportes": CommandType.REPORTS,
            
            # Comandos generales
            "ayuda": CommandType.HELP,
            "help": CommandType.HELP,
            "menu": CommandType.MENU,
            "inicio": CommandType.MENU,
            "registro": CommandType.REGISTER
        }
        
        # Setup inicial
        self._setup_sample_client()
    
    def _setup_sample_client(self):
        """Configura cliente de ejemplo."""
        
        sample_config = ClientConfiguration(
            client_id="client_tech_001",
            company_name="TechCorp México",
            whatsapp_number="+525512345678",
            whatsapp_token="sample_token_123",
            webhook_url="https://api.huntred.com/webhook/whatsapp/client_tech_001",
            office_locations=[
                {
                    "name": "Oficina Principal",
                    "address": "Av. Reforma 123, CDMX",
                    "latitude": 19.4326,
                    "longitude": -99.1332,
                    "radius_meters": 100
                }
            ],
            max_distance_meters=100.0,
            work_schedule={
                "monday": {"start": "09:00", "end": "18:00"},
                "tuesday": {"start": "09:00", "end": "18:00"},
                "wednesday": {"start": "09:00", "end": "18:00"},
                "thursday": {"start": "09:00", "end": "18:00"},
                "friday": {"start": "09:00", "end": "18:00"}
            },
            welcome_message="¡Bienvenido al sistema de nómina de TechCorp! 🏢\n\nEscribe 'menu' para ver las opciones disponibles.",
            admin_phones=["+525551234567"],
            hr_phones=["+525551234568"]
        )
        
        self.client_configs["client_tech_001"] = sample_config
    
    async def process_message(self, phone_number: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un mensaje entrante de WhatsApp."""
        
        # Determinar cliente basado en el número de WhatsApp receptor
        client_id = await self._get_client_from_whatsapp_number(message_data.get("to", ""))
        if not client_id:
            return await self._send_error_message("Cliente no encontrado")
        
        # Obtener o crear usuario
        user = await self._get_or_create_user(phone_number, client_id)
        user.last_activity = datetime.now()
        user.total_interactions += 1
        
        # Procesar según tipo de mensaje
        message_type = MessageType(message_data.get("type", "text"))
        
        if message_type == MessageType.TEXT:
            return await self._process_text_message(user, message_data["text"])
        elif message_type == MessageType.LOCATION:
            return await self._process_location_message(user, message_data["location"])
        elif message_type == MessageType.BUTTON:
            return await self._process_button_message(user, message_data["button"])
        elif message_type == MessageType.LIST:
            return await self._process_list_message(user, message_data["list"])
        else:
            return await self._send_help_message(user)
    
    async def _get_client_from_whatsapp_number(self, whatsapp_number: str) -> Optional[str]:
        """Obtiene el ID del cliente basado en el número de WhatsApp."""
        
        for client_id, config in self.client_configs.items():
            if config.whatsapp_number == whatsapp_number:
                return client_id
        
        return None
    
    async def _get_or_create_user(self, phone_number: str, client_id: str) -> WhatsAppUser:
        """Obtiene o crea un usuario de WhatsApp."""
        
        user_key = f"{client_id}_{phone_number}"
        
        if user_key not in self.users:
            # Verificar si es administrador
            config = self.client_configs[client_id]
            role = UserRole.EMPLOYEE
            
            if phone_number in config.admin_phones:
                role = UserRole.SUPER_ADMIN
            elif phone_number in config.hr_phones:
                role = UserRole.HR_ADMIN
            
            # Buscar empleado asociado
            employee_id = await self._find_employee_by_phone(phone_number, client_id)
            
            user = WhatsAppUser(
                phone_number=phone_number,
                client_id=client_id,
                role=role,
                employee_id=employee_id
            )
            
            self.users[user_key] = user
            
            # Enviar mensaje de bienvenida si es nuevo usuario
            if not employee_id and role == UserRole.EMPLOYEE:
                await self._start_registration_flow(user)
        
        return self.users[user_key]
    
    async def _find_employee_by_phone(self, phone_number: str, client_id: str) -> Optional[str]:
        """Busca un empleado por número de teléfono."""
        
        # En un sistema real, esto buscaría en la base de datos
        # Por ahora, simular búsqueda
        for emp_id, employee in self.payroll_engine.employees.items():
            if employee.client_id == client_id:
                # Simular que el teléfono está en algún campo del empleado
                # En producción esto sería una búsqueda real
                if phone_number.endswith("1234567"):  # Ejemplo
                    return emp_id
        
        return None
    
    async def _process_text_message(self, user: WhatsAppUser, text: str) -> Dict[str, Any]:
        """Procesa un mensaje de texto."""
        
        text_lower = text.lower().strip()
        
        # Si está en un flujo activo, procesarlo
        if user.current_flow:
            return await self._process_flow_step(user, text)
        
        # Procesar comandos
        command = self._parse_command(text_lower)
        
        if command:
            return await self._execute_command(user, command, text)
        else:
            # Mensaje no reconocido, mostrar ayuda
            return await self._send_help_message(user)
    
    def _parse_command(self, text: str) -> Optional[CommandType]:
        """Parsea el texto para identificar comandos."""
        
        # Limpiar texto
        text = re.sub(r'[^\w\s]', '', text).strip()
        
        # Buscar comando exacto
        if text in self.commands:
            return self.commands[text]
        
        # Buscar comandos que contengan el texto
        for cmd_text, cmd_type in self.commands.items():
            if cmd_text in text or text in cmd_text:
                return cmd_type
        
        return None
    
    async def _execute_command(self, user: WhatsAppUser, command: CommandType, original_text: str) -> Dict[str, Any]:
        """Ejecuta un comando específico."""
        
        if command == CommandType.MENU:
            return await self._send_main_menu(user)
        
        elif command == CommandType.HELP:
            return await self._send_help_message(user)
        
        elif command == CommandType.REGISTER:
            return await self._start_registration_flow(user)
        
        elif command == CommandType.CHECKIN:
            return await self._request_checkin_location(user)
        
        elif command == CommandType.CHECKOUT:
            return await self._request_checkout_location(user)
        
        elif command == CommandType.PAYSLIP:
            return await self._send_payslip_options(user)
        
        elif command == CommandType.BALANCE:
            return await self._send_balance_info(user)
        
        elif command == CommandType.VACATION_BALANCE:
            return await self._send_vacation_balance(user)
        
        elif command == CommandType.SCHEDULE:
            return await self._send_work_schedule(user)
        
        # Comandos administrativos
        elif command == CommandType.PAYROLL_STATUS:
            if user.role in [UserRole.HR_ADMIN, UserRole.SUPER_ADMIN]:
                return await self._send_payroll_status(user)
            else:
                return await self._send_permission_error(user)
        
        elif command == CommandType.EMPLOYEE_LIST:
            if user.role in [UserRole.HR_ADMIN, UserRole.SUPER_ADMIN]:
                return await self._send_employee_list(user)
            else:
                return await self._send_permission_error(user)
        
        elif command == CommandType.PAYROLL_SUMMARY:
            if user.role in [UserRole.HR_ADMIN, UserRole.SUPER_ADMIN]:
                return await self._send_payroll_summary(user)
            else:
                return await self._send_permission_error(user)
        
        elif command == CommandType.APPROVE_PAYROLL:
            if user.role in [UserRole.HR_ADMIN, UserRole.SUPER_ADMIN]:
                return await self._start_payroll_approval_flow(user)
            else:
                return await self._send_permission_error(user)
        
        elif command == CommandType.REPORTS:
            if user.role in [UserRole.HR_ADMIN, UserRole.SUPER_ADMIN]:
                return await self._send_reports_menu(user)
            else:
                return await self._send_permission_error(user)
        
        else:
            return await self._send_help_message(user)
    
    async def _send_main_menu(self, user: WhatsAppUser) -> Dict[str, Any]:
        """Envía el menú principal."""
        
        config = self.client_configs[user.client_id]
        
        if user.role == UserRole.EMPLOYEE:
            menu_text = f"🏢 *{config.company_name}*\n\n"
            menu_text += "📱 *Menú Principal - Empleado*\n\n"
            menu_text += "⏰ *Asistencia:*\n"
            menu_text += "• `entrada` - Registrar entrada\n"
            menu_text += "• `salida` - Registrar salida\n\n"
            menu_text += "💰 *Nómina:*\n"
            menu_text += "• `recibo` - Ver recibo de pago\n"
            menu_text += "• `saldo` - Consultar saldo\n"
            menu_text += "• `vacaciones` - Balance de vacaciones\n\n"
            menu_text += "ℹ️ *Información:*\n"
            menu_text += "• `horario` - Ver horario de trabajo\n"
            menu_text += "• `ayuda` - Mostrar ayuda\n\n"
            menu_text += "_Escribe cualquier comando para comenzar_ ✨"
        
        else:  # Admin o HR
            menu_text = f"🏢 *{config.company_name}*\n\n"
            menu_text += "👨‍💼 *Panel Administrativo*\n\n"
            menu_text += "👥 *Empleados:*\n"
            menu_text += "• `empleados` - Lista de empleados\n"
            menu_text += "• `reportes` - Reportes de asistencia\n\n"
            menu_text += "💰 *Nómina:*\n"
            menu_text += "• `estado_nomina` - Estado actual\n"
            menu_text += "• `resumen` - Resumen de nómina\n"
            menu_text += "• `aprobar` - Aprobar nómina\n\n"
            menu_text += "ℹ️ *General:*\n"
            menu_text += "• `ayuda` - Mostrar ayuda completa\n\n"
            menu_text += "_Panel de administración activo_ 🔐"
        
        return {
            "type": "text",
            "text": menu_text
        }
    
    async def _send_help_message(self, user: WhatsAppUser) -> Dict[str, Any]:
        """Envía mensaje de ayuda."""
        
        help_text = "🤖 *Asistente de Nómina huntRED®*\n\n"
        help_text += "Comandos disponibles:\n\n"
        
        if user.role == UserRole.EMPLOYEE:
            help_text += "⏰ *Asistencia:*\n"
            help_text += "• entrada, checkin\n"
            help_text += "• salida, checkout\n\n"
            help_text += "💰 *Nómina:*\n"
            help_text += "• recibo, nomina\n"
            help_text += "• saldo\n"
            help_text += "• vacaciones\n\n"
        else:
            help_text += "👨‍💼 *Administración:*\n"
            help_text += "• empleados\n"
            help_text += "• estado_nomina\n"
            help_text += "• resumen\n"
            help_text += "• aprobar\n"
            help_text += "• reportes\n\n"
        
        help_text += "ℹ️ *General:*\n"
        help_text += "• menu, inicio\n"
        help_text += "• ayuda, help\n\n"
        help_text += "_Escribe 'menu' para ver todas las opciones_ 📋"
        
        return {
            "type": "text",
            "text": help_text
        }
    
    async def _request_checkin_location(self, user: WhatsAppUser) -> Dict[str, Any]:
        """Solicita ubicación para check-in."""
        
        if not user.employee_id:
            return {
                "type": "text",
                "text": "❌ No estás registrado como empleado. Contacta a RH para más información."
            }
        
        # Verificar si ya hizo check-in hoy
        today_checkins = await self._get_today_checkins(user.employee_id)
        if any(c.action_type == "checkin" for c in today_checkins):
            last_checkin = max((c for c in today_checkins if c.action_type == "checkin"), 
                             key=lambda x: x.timestamp)
            return {
                "type": "text",
                "text": f"✅ Ya registraste tu entrada hoy a las {last_checkin.timestamp.strftime('%H:%M')}\n\n"
                       f"Si necesitas hacer una corrección, contacta a RH."
            }
        
        user.current_flow = "checkin"
        user.flow_step = 1
        
        return {
            "type": "text",
            "text": "📍 *Registro de Entrada*\n\n"
                   "Para registrar tu entrada, comparte tu ubicación actual.\n\n"
                   "👆 Toca el botón de adjuntar (📎) y selecciona 'Ubicación' 📍\n\n"
                   "_Necesario para validar que estés en la oficina_ 🏢"
        }
    
    async def _request_checkout_location(self, user: WhatsAppUser) -> Dict[str, Any]:
        """Solicita ubicación para check-out."""
        
        if not user.employee_id:
            return {
                "type": "text",
                "text": "❌ No estás registrado como empleado. Contacta a RH para más información."
            }
        
        # Verificar si hizo check-in hoy
        today_checkins = await self._get_today_checkins(user.employee_id)
        checkin_today = any(c.action_type == "checkin" for c in today_checkins)
        
        if not checkin_today:
            return {
                "type": "text",
                "text": "❌ No has registrado tu entrada hoy.\n\n"
                       "Primero registra tu entrada con el comando `entrada`"
            }
        
        # Verificar si ya hizo check-out
        if any(c.action_type == "checkout" for c in today_checkins):
            last_checkout = max((c for c in today_checkins if c.action_type == "checkout"), 
                              key=lambda x: x.timestamp)
            return {
                "type": "text",
                "text": f"✅ Ya registraste tu salida hoy a las {last_checkout.timestamp.strftime('%H:%M')}\n\n"
                       f"Si necesitas hacer una corrección, contacta a RH."
            }
        
        user.current_flow = "checkout"
        user.flow_step = 1
        
        return {
            "type": "text",
            "text": "📍 *Registro de Salida*\n\n"
                   "Para registrar tu salida, comparte tu ubicación actual.\n\n"
                   "👆 Toca el botón de adjuntar (📎) y selecciona 'Ubicación' 📍\n\n"
                   "_Necesario para validar que estés saliendo de la oficina_ 🏢"
        }
    
    async def _process_location_message(self, user: WhatsAppUser, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un mensaje de ubicación."""
        
        if user.current_flow in ["checkin", "checkout"]:
            return await self._process_checkin_checkout_location(user, location_data)
        else:
            return {
                "type": "text",
                "text": "📍 Ubicación recibida, pero no estoy esperando una ubicación en este momento.\n\n"
                       "Escribe `entrada` o `salida` para registrar asistencia."
            }
    
    async def _process_checkin_checkout_location(self, user: WhatsAppUser, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa ubicación para check-in/checkout."""
        
        latitude = location_data.get("latitude")
        longitude = location_data.get("longitude")
        
        if not latitude or not longitude:
            return {
                "type": "text",
                "text": "❌ No se pudo obtener tu ubicación. Intenta de nuevo."
            }
        
        # Validar ubicación
        config = self.client_configs[user.client_id]
        is_valid, distance, office_name = await self._validate_location(
            latitude, longitude, config
        )
        
        # Crear registro
        checkin_id = str(uuid.uuid4())
        checkin = CheckInOut(
            id=checkin_id,
            employee_id=user.employee_id,
            client_id=user.client_id,
            action_type=user.current_flow,
            timestamp=datetime.now(),
            latitude=latitude,
            longitude=longitude,
            is_valid_location=is_valid,
            distance_from_office=distance
        )
        
        # Guardar registro
        if user.employee_id not in self.checkins:
            self.checkins[user.employee_id] = []
        self.checkins[user.employee_id].append(checkin)
        
        # Limpiar flujo
        user.current_flow = None
        user.flow_step = 0
        
        # Generar respuesta
        action_name = "entrada" if checkin.action_type == "checkin" else "salida"
        time_str = checkin.timestamp.strftime("%H:%M")
        
        if is_valid:
            response = f"✅ *{action_name.title()} registrada exitosamente*\n\n"
            response += f"🕐 Hora: {time_str}\n"
            response += f"📍 Ubicación: {office_name}\n"
            response += f"📏 Distancia: {distance:.0f}m de la oficina\n\n"
            response += "¡Que tengas un excelente día! 😊"
        else:
            response = f"⚠️ *{action_name.title()} registrada con observación*\n\n"
            response += f"🕐 Hora: {time_str}\n"
            response += f"📍 Distancia: {distance:.0f}m de la oficina\n"
            response += f"🚨 Fuera del rango permitido ({config.max_distance_meters}m)\n\n"
            response += "Tu registro ha sido marcado para revisión por RH."
        
        return {
            "type": "text",
            "text": response
        }
    
    async def _validate_location(self, latitude: float, longitude: float, 
                               config: ClientConfiguration) -> Tuple[bool, float, str]:
        """Valida si la ubicación está dentro del rango permitido."""
        
        user_location = (latitude, longitude)
        min_distance = float('inf')
        closest_office = "Ubicación desconocida"
        
        for office in config.office_locations:
            office_location = (office["latitude"], office["longitude"])
            distance = geodesic(user_location, office_location).meters
            
            if distance < min_distance:
                min_distance = distance
                closest_office = office["name"]
        
        is_valid = min_distance <= config.max_distance_meters
        
        return is_valid, min_distance, closest_office
    
    async def _get_today_checkins(self, employee_id: str) -> List[CheckInOut]:
        """Obtiene los check-ins del día actual."""
        
        today = date.today()
        employee_checkins = self.checkins.get(employee_id, [])
        
        return [
            checkin for checkin in employee_checkins
            if checkin.timestamp.date() == today
        ]
    
    async def _send_payslip_options(self, user: WhatsAppUser) -> Dict[str, Any]:
        """Envía opciones de recibos de nómina."""
        
        if not user.employee_id:
            return {
                "type": "text",
                "text": "❌ No estás registrado como empleado. Contacta a RH."
            }
        
        # Obtener recibos disponibles (últimos 6 meses)
        current_date = date.today()
        available_periods = []
        
        for i in range(6):
            period_date = current_date.replace(day=1) - timedelta(days=i*30)
            period_id = f"{user.client_id}_{period_date.year}_{period_date.month:02d}"
            
            # Verificar si existe el período
            if period_id in self.payroll_engine.periods:
                period_name = period_date.strftime("%B %Y")
                available_periods.append({
                    "id": period_id,
                    "name": period_name
                })
        
        if not available_periods:
            return {
                "type": "text",
                "text": "📄 No hay recibos de nómina disponibles.\n\n"
                       "Contacta a RH si necesitas información sobre tus pagos."
            }
        
        # Crear lista interactiva
        sections = [{
            "title": "Selecciona el período",
            "rows": [
                {
                    "id": f"payslip_{period['id']}",
                    "title": period['name'],
                    "description": "Ver recibo de nómina"
                }
                for period in available_periods[:5]  # Max 5 opciones
            ]
        }]
        
        return {
            "type": "list",
            "header": "📄 Recibos de Nómina",
            "body": "Selecciona el período del cual quieres ver tu recibo:",
            "footer": "huntRED® Payroll",
            "button": "Ver Períodos",
            "sections": sections
        }
    
    async def _send_balance_info(self, user: WhatsAppUser) -> Dict[str, Any]:
        """Envía información del saldo/balance del empleado."""
        
        if not user.employee_id:
            return {
                "type": "text",
                "text": "❌ No estás registrado como empleado."
            }
        
        employee = self.payroll_engine.employees.get(user.employee_id)
        if not employee:
            return {
                "type": "text",
                "text": "❌ No se encontró información del empleado."
            }
        
        # Buscar último recibo
        latest_batch = None
        for batch_id, batch in self.payroll_engine.batches.items():
            if (batch.client_id == user.client_id and 
                user.employee_id in batch.payroll_concepts):
                if not latest_batch or batch.processed_at > latest_batch.processed_at:
                    latest_batch = batch
        
        if not latest_batch:
            return {
                "type": "text",
                "text": "📊 *Información del Empleado*\n\n"
                       f"👤 Nombre: {employee.first_name} {employee.last_name}\n"
                       f"🆔 No. Empleado: {employee.employee_number}\n"
                       f"💰 Salario Base: ${employee.base_salary:,.2f}\n"
                       f"📅 Fecha de Ingreso: {employee.hire_date.strftime('%d/%m/%Y')}\n\n"
                       "💳 No hay información de nómina disponible aún."
            }
        
        concepts = latest_batch.payroll_concepts[user.employee_id]
        period = self.payroll_engine.periods.get(latest_batch.period_id)
        
        balance_text = "💰 *Balance Actual*\n\n"
        balance_text += f"👤 {employee.first_name} {employee.last_name}\n"
        balance_text += f"🆔 No. Empleado: {employee.employee_number}\n\n"
        
        if period:
            balance_text += f"📅 Último período: {period.start_date.strftime('%B %Y')}\n"
        
        balance_text += f"💵 Percepciones: ${concepts.total_perceptions:,.2f}\n"
        balance_text += f"➖ Deducciones: ${concepts.total_deductions:,.2f}\n"
        balance_text += f"💳 *Neto: ${concepts.net_pay:,.2f}*\n\n"
        balance_text += f"📊 Días trabajados: {concepts.worked_days}\n"
        
        if concepts.absent_days > 0:
            balance_text += f"⚠️ Faltas: {concepts.absent_days} días\n"
        
        balance_text += f"\n_Información actualizada al {concepts.calculated_at.strftime('%d/%m/%Y')}_"
        
        return {
            "type": "text",
            "text": balance_text
        }
    
    async def _send_vacation_balance(self, user: WhatsAppUser) -> Dict[str, Any]:
        """Envía balance de vacaciones."""
        
        if not user.employee_id:
            return {
                "type": "text",
                "text": "❌ No estás registrado como empleado."
            }
        
        employee = self.payroll_engine.employees.get(user.employee_id)
        if not employee:
            return {
                "type": "text",
                "text": "❌ No se encontró información del empleado."
            }
        
        # Calcular antigüedad
        today = date.today()
        years_worked = (today - employee.hire_date).days / 365.25
        
        # Calcular días de vacaciones según ley mexicana
        if years_worked < 1:
            vacation_days = int(12 * (years_worked))
        elif years_worked < 2:
            vacation_days = 12
        elif years_worked < 3:
            vacation_days = 14
        elif years_worked < 4:
            vacation_days = 16
        elif years_worked < 5:
            vacation_days = 18
        elif years_worked < 10:
            vacation_days = 20
        else:
            vacation_days = min(22, 20 + int((years_worked - 5) / 5) * 2)
        
        # Simular días usados (en un sistema real esto vendría de la BD)
        import random
        used_days = random.randint(0, vacation_days)
        available_days = vacation_days - used_days
        
        vacation_text = "🏖️ *Balance de Vacaciones*\n\n"
        vacation_text += f"👤 {employee.first_name} {employee.last_name}\n"
        vacation_text += f"📅 Antigüedad: {years_worked:.1f} años\n\n"
        vacation_text += f"📊 *Período actual ({today.year}):*\n"
        vacation_text += f"✅ Días ganados: {vacation_days}\n"
        vacation_text += f"🏖️ Días usados: {used_days}\n"
        vacation_text += f"⭐ *Disponibles: {available_days} días*\n\n"
        
        if available_days > 0:
            vacation_text += "💡 Puedes solicitar vacaciones contactando a RH.\n\n"
        else:
            vacation_text += "⚠️ No tienes días de vacaciones disponibles.\n\n"
        
        vacation_text += f"_Prima vacacional: 25% adicional sobre días tomados_"
        
        return {
            "type": "text",
            "text": vacation_text
        }
    
    async def _send_work_schedule(self, user: WhatsAppUser) -> Dict[str, Any]:
        """Envía horario de trabajo."""
        
        config = self.client_configs[user.client_id]
        schedule = config.work_schedule
        
        schedule_text = "🕐 *Horario de Trabajo*\n\n"
        schedule_text += f"🏢 {config.company_name}\n\n"
        
        days_es = {
            "monday": "Lunes",
            "tuesday": "Martes", 
            "wednesday": "Miércoles",
            "thursday": "Jueves",
            "friday": "Viernes",
            "saturday": "Sábado",
            "sunday": "Domingo"
        }
        
        for day_en, day_es in days_es.items():
            if day_en in schedule:
                day_schedule = schedule[day_en]
                schedule_text += f"📅 {day_es}: {day_schedule['start']} - {day_schedule['end']}\n"
            else:
                schedule_text += f"📅 {day_es}: Descanso\n"
        
        schedule_text += f"\n⏰ Zona horaria: {config.timezone}\n"
        schedule_text += f"📍 Registro requerido desde oficina\n"
        schedule_text += f"📏 Radio permitido: {config.max_distance_meters}m\n\n"
        schedule_text += "_Usa 'entrada' y 'salida' para registrar asistencia_"
        
        return {
            "type": "text",
            "text": schedule_text
        }
    
    async def _send_payroll_status(self, user: WhatsAppUser) -> Dict[str, Any]:
        """Envía estado de nómina (solo admins)."""
        
        # Buscar nóminas del cliente
        client_batches = [
            batch for batch in self.payroll_engine.batches.values()
            if batch.client_id == user.client_id
        ]
        
        if not client_batches:
            return {
                "type": "text",
                "text": "📊 No hay nóminas procesadas para este período."
            }
        
        # Obtener última nómina
        latest_batch = max(client_batches, key=lambda b: b.processed_at or datetime.min)
        period = self.payroll_engine.periods.get(latest_batch.period_id)
        
        status_text = "📊 *Estado de Nómina*\n\n"
        
        if period:
            status_text += f"📅 Período: {period.start_date.strftime('%B %Y')}\n"
            status_text += f"💳 Fecha de pago: {period.pay_date.strftime('%d/%m/%Y')}\n"
        
        status_text += f"👥 Empleados: {latest_batch.total_employees}\n"
        status_text += f"💰 Total neto: ${latest_batch.total_net_pay:,.2f}\n"
        status_text += f"🏢 Costo patronal: ${latest_batch.total_employer_cost:,.2f}\n\n"
        
        status_emoji = {
            "draft": "📝",
            "calculated": "🧮", 
            "approved": "✅",
            "paid": "💳",
            "rejected": "❌"
        }
        
        status_text += f"{status_emoji.get(latest_batch.status.value, '❓')} "
        status_text += f"Estado: {latest_batch.status.value.title()}\n\n"
        
        if latest_batch.status.value == "calculated":
            status_text += "⏳ _Pendiente de aprobación_\n"
            status_text += "Usa 'aprobar' para aprobar la nómina"
        elif latest_batch.status.value == "approved":
            status_text += "✅ _Lista para dispersión bancaria_"
        
        return {
            "type": "text", 
            "text": status_text
        }
    
    async def _send_permission_error(self, user: WhatsAppUser) -> Dict[str, Any]:
        """Envía mensaje de error de permisos."""
        
        return {
            "type": "text",
            "text": "🔒 No tienes permisos para ejecutar este comando.\n\n"
                   "Contacta al administrador si necesitas acceso."
        }
    
    async def _send_error_message(self, message: str) -> Dict[str, Any]:
        """Envía mensaje de error genérico."""
        
        return {
            "type": "text",
            "text": f"❌ Error: {message}"
        }
    
    # ... [Continuaré con más métodos en la siguiente función]
    
    async def _start_registration_flow(self, user: WhatsAppUser) -> Dict[str, Any]:
        """Inicia flujo de registro de empleado."""
        
        user.current_flow = "registration"
        user.flow_step = 1
        
        return {
            "type": "text",
            "text": "📝 *Registro de Empleado*\n\n"
                   "Para usar el sistema de nómina, necesito registrarte.\n\n"
                   "¿Cuál es tu número de empleado?\n\n"
                   "_Si no lo sabes, contacta a RH_"
        }

# Funciones de utilidad
async def setup_client_whatsapp(client_id: str, whatsapp_config: Dict[str, Any]) -> str:
    """Configura WhatsApp para un cliente específico."""
    
    bot = PayrollWhatsAppBot()
    
    config = ClientConfiguration(
        client_id=client_id,
        company_name=whatsapp_config["company_name"],
        whatsapp_number=whatsapp_config["whatsapp_number"],
        whatsapp_token=whatsapp_config["whatsapp_token"],
        webhook_url=whatsapp_config["webhook_url"],
        office_locations=whatsapp_config.get("office_locations", []),
        max_distance_meters=whatsapp_config.get("max_distance_meters", 100),
        work_schedule=whatsapp_config.get("work_schedule", {}),
        admin_phones=whatsapp_config.get("admin_phones", []),
        hr_phones=whatsapp_config.get("hr_phones", [])
    )
    
    bot.client_configs[client_id] = config
    return f"WhatsApp configured for client: {client_id}"

# Exportaciones
__all__ = [
    'MessageType', 'CommandType', 'UserRole', 
    'WhatsAppUser', 'CheckInOut', 'ClientConfiguration',
    'PayrollWhatsAppBot', 'setup_client_whatsapp'
]