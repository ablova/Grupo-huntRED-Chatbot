"""
Complete Chatbot Engine for Ghuntred-v2
Advanced conversational AI with multi-channel support and payroll intelligence
"""

import logging
import json
import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import asyncio
from dataclasses import dataclass
import hashlib

from ..models.base import MessageChannel, UserRole
from ..services.payroll_engine import PayrollEngine
from ..services.overtime_management import OvertimeManagementEngine

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Conversation state machine"""
    INITIAL = "initial"
    AUTHENTICATED = "authenticated"
    PAYROLL_INQUIRY = "payroll_inquiry"
    OVERTIME_REQUEST = "overtime_request"
    PROFILE_UPDATE = "profile_update"
    HELP_REQUEST = "help_request"
    ADMIN_MODE = "admin_mode"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"


class IntentType(Enum):
    """Intent classification types"""
    GREETING = "greeting"
    PAYROLL_QUERY = "payroll_query"
    OVERTIME_REQUEST = "overtime_request"
    PROFILE_QUERY = "profile_query"
    HELP = "help"
    GOODBYE = "goodbye"
    AUTHENTICATION = "authentication"
    ADMIN_COMMAND = "admin_command"
    UNKNOWN = "unknown"


class MessageType(Enum):
    """Message types for responses"""
    TEXT = "text"
    QUICK_REPLY = "quick_reply"
    BUTTON = "button"
    LIST = "list"
    TEMPLATE = "template"
    DOCUMENT = "document"
    IMAGE = "image"


@dataclass
class ConversationContext:
    """Context for maintaining conversation state"""
    user_id: str
    company_id: str
    channel: MessageChannel
    state: ConversationState = ConversationState.INITIAL
    intent: Optional[IntentType] = None
    entities: Dict[str, Any] = None
    session_data: Dict[str, Any] = None
    last_message: Optional[str] = None
    message_count: int = 0
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = {}
        if self.session_data is None:
            self.session_data = {}


@dataclass
class ChatbotResponse:
    """Structured chatbot response"""
    message: str
    message_type: MessageType = MessageType.TEXT
    quick_replies: List[str] = None
    buttons: List[Dict[str, str]] = None
    attachments: List[Dict[str, Any]] = None
    next_state: Optional[ConversationState] = None
    requires_auth: bool = False
    
    def __post_init__(self):
        if self.quick_replies is None:
            self.quick_replies = []
        if self.buttons is None:
            self.buttons = []
        if self.attachments is None:
            self.attachments = []


class IntentClassifier:
    """AI-powered intent classification"""
    
    def __init__(self):
        self.patterns = {
            IntentType.GREETING: [
                r'hola|hello|hi|buenos días|buenas tardes|buenas noches',
                r'empezar|comenzar|iniciar|start',
                r'ayuda|help|auxilio'
            ],
            IntentType.PAYROLL_QUERY: [
                r'nómina|nomina|sueldo|salario|pago|payroll',
                r'cuánto gano|cuanto cobro|mi salario',
                r'recibo de nómina|recibo de pago',
                r'deducciones|impuestos|isr|imss|infonavit',
                r'aguinaldo|prima vacacional|vacaciones'
            ],
            IntentType.OVERTIME_REQUEST: [
                r'horas extra|overtime|tiempo extra',
                r'trabajar más|quedarme tarde',
                r'solicitar horas|pedir horas extra',
                r'autorización|aprobar horas'
            ],
            IntentType.PROFILE_QUERY: [
                r'mi perfil|mis datos|información personal',
                r'actualizar datos|cambiar información',
                r'teléfono|dirección|email|correo'
            ],
            IntentType.ADMIN_COMMAND: [
                r'admin|administrador|reporte|report',
                r'dashboard|panel|estadísticas',
                r'empleados|users|usuarios'
            ],
            IntentType.GOODBYE: [
                r'adiós|bye|hasta luego|nos vemos',
                r'gracias|thank you|muchas gracias',
                r'terminar|salir|exit'
            ]
        }
    
    def classify_intent(self, message: str, user_role: str = "employee") -> IntentType:
        """Classify user intent using pattern matching and context"""
        message_lower = message.lower()
        
        # Check authentication patterns
        if re.search(r'mi número|mi id|employee.*\d+|empleado.*\d+', message_lower):
            return IntentType.AUTHENTICATION
        
        # Check each intent pattern
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        # Context-based classification
        if any(keyword in message_lower for keyword in ['cuánto', 'cuanto', 'dinero', 'pesos']):
            return IntentType.PAYROLL_QUERY
        
        if any(keyword in message_lower for keyword in ['solicitar', 'pedir', 'autorizar']):
            return IntentType.OVERTIME_REQUEST
        
        return IntentType.UNKNOWN
    
    def extract_entities(self, message: str, intent: IntentType) -> Dict[str, Any]:
        """Extract entities from message based on intent"""
        entities = {}
        message_lower = message.lower()
        
        if intent == IntentType.AUTHENTICATION:
            # Extract employee ID
            employee_id_match = re.search(r'(?:empleado|employee|id)?\s*(\d+)', message_lower)
            if employee_id_match:
                entities['employee_id'] = employee_id_match.group(1)
        
        elif intent == IntentType.OVERTIME_REQUEST:
            # Extract hours
            hours_match = re.search(r'(\d+(?:\.\d+)?)\s*horas?', message_lower)
            if hours_match:
                entities['hours'] = float(hours_match.group(1))
            
            # Extract date
            date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', message)
            if date_match:
                entities['date'] = date_match.group(1)
        
        elif intent == IntentType.PAYROLL_QUERY:
            # Extract period
            if 'mes' in message_lower or 'monthly' in message_lower:
                entities['period'] = 'monthly'
            elif 'quincenal' in message_lower or 'biweekly' in message_lower:
                entities['period'] = 'biweekly'
        
        return entities


class PayrollAssistant:
    """Specialized assistant for payroll queries"""
    
    def __init__(self, payroll_engine: PayrollEngine):
        self.payroll_engine = payroll_engine
    
    async def handle_payroll_query(self, context: ConversationContext) -> ChatbotResponse:
        """Handle payroll-related queries"""
        # Mock employee data (would come from database)
        employee_data = {
            "id": context.entities.get("employee_id", context.user_id),
            "name": "Juan Pérez",
            "monthly_salary": 25000.0,
            "payroll_frequency": "monthly"
        }
        
        # Calculate current period payroll
        today = date.today()
        period_start = today.replace(day=1)
        period_end = today
        
        calculation = self.payroll_engine.calculate_payroll(
            employee_data=employee_data,
            pay_period_start=period_start,
            pay_period_end=period_end
        )
        
        payslip_data = self.payroll_engine.generate_payslip_data(calculation)
        
        message = f"""💰 **Información de Nómina - {employee_data['name']}**

📅 **Período:** {period_start.strftime('%d/%m/%Y')} - {period_end.strftime('%d/%m/%Y')}

💵 **Ingresos:**
• Salario Base: ${payslip_data['base_salary']:,.2f}
• Horas Extra: ${payslip_data['overtime_amount']:,.2f}
• Bonos: ${payslip_data['bonuses']:,.2f}
• **Total Bruto:** ${payslip_data['gross_income']:,.2f}

📉 **Deducciones:**
• IMSS: ${payslip_data['imss_employee']:,.2f}
• ISR: ${payslip_data['isr_withheld']:,.2f}
• INFONAVIT: ${payslip_data['infonavit_employee']:,.2f}
• **Total Deducciones:** ${payslip_data['total_deductions']:,.2f}

💸 **Pago Neto:** ${payslip_data['net_pay']:,.2f}

¿Necesitas información adicional sobre algún concepto?"""
        
        quick_replies = [
            "Ver detalles IMSS",
            "Explicar ISR", 
            "Proyección anual",
            "Recibo completo",
            "Otra consulta"
        ]
        
        return ChatbotResponse(
            message=message,
            message_type=MessageType.QUICK_REPLY,
            quick_replies=quick_replies,
            next_state=ConversationState.PAYROLL_INQUIRY
        )
    
    async def handle_payroll_detail(self, context: ConversationContext, detail_type: str) -> ChatbotResponse:
        """Handle detailed payroll explanations"""
        if "imss" in detail_type.lower():
            message = """🏥 **Detalles IMSS 2024**

El IMSS (Instituto Mexicano del Seguro Social) incluye:

📊 **Cuota Fija:** 0.43% sobre 1 UMA
💰 **Excedente:** 0.625% sobre salario > 3 UMA
🏥 **Prestaciones en Dinero:** 0.25%
👴 **Pensionados:** 0.375%
♿ **Invalidez y Vida:** 0.625%
👨‍👩‍👧‍👦 **Cesantía y Vejez:** 1.125%

**UMA 2024:** $108.57 diario / $3,257.10 mensual

Estos descuentos te dan derecho a:
✅ Atención médica
✅ Incapacidades pagadas
✅ Pensión por vejez
✅ Seguro de vida"""
        
        elif "isr" in detail_type.lower():
            message = """💼 **Impuesto Sobre la Renta (ISR) 2024**

El ISR se calcula con tabla progresiva:

📈 **Tarifas 2024:**
• $0 - $746: 1.92%
• $746 - $6,332: 6.4%
• $6,332 - $11,128: 10.88%
• Y así sucesivamente...

💰 **Subsidio para el Empleo:**
Se aplica automáticamente para reducir el ISR.

🧮 **Tu cálculo:**
ISR = (Ingresos - Deducciones) × Tarifa
ISR Final = ISR - Subsidio"""
        
        elif "proyección" in detail_type.lower() or "anual" in detail_type.lower():
            # Mock annual projection
            message = """📊 **Proyección Anual 2024**

💵 **Ingresos Anuales:**
• Salario: $300,000.00
• Aguinaldo: $25,000.00
• Prima Vacacional: $3,750.00
• **Total Bruto:** $328,750.00

📉 **Deducciones Anuales:**
• IMSS: $18,562.50
• ISR: $24,375.00
• INFONAVIT: $15,000.00
• **Total Deducciones:** $57,937.50

💸 **Neto Anual:** $270,812.50
💳 **Neto Mensual Promedio:** $22,567.71

📈 **Comparativa:**
• Incremento vs 2023: +8.5%
• Ahorro fiscal: $3,250.00"""
        
        else:
            message = "Por favor especifica qué detalle te interesa: IMSS, ISR, o proyección anual."
        
        return ChatbotResponse(
            message=message,
            quick_replies=["Volver a nómina", "Nueva consulta", "Ayuda"]
        )


class OvertimeAssistant:
    """Specialized assistant for overtime requests"""
    
    def __init__(self, overtime_engine: OvertimeManagementEngine):
        self.overtime_engine = overtime_engine
    
    async def handle_overtime_request(self, context: ConversationContext) -> ChatbotResponse:
        """Handle overtime request process"""
        if not context.entities.get("hours") or not context.entities.get("date"):
            return ChatbotResponse(
                message="""⏰ **Solicitud de Horas Extra**

Para procesar tu solicitud necesito:

📅 **Fecha:** ¿Qué día trabajaste horas extra?
⏱️ **Horas:** ¿Cuántas horas extra trabajaste?
📝 **Motivo:** ¿Por qué fue necesario?

Ejemplo: "Trabajé 3 horas extra el 15/12/2024 por entrega urgente de proyecto"

Por favor proporciona esta información.""",
                next_state=ConversationState.WAITING_INPUT
            )
        
        # Process overtime request
        hours = context.entities.get("hours")
        work_date = context.entities.get("date")
        reason = context.entities.get("reason", "No especificado")
        
        # Mock overtime calculation
        base_hourly_rate = 120.00  # $120/hour
        overtime_amount = hours * base_hourly_rate * 2  # Double time
        
        overtime_data = {
            "work_date": work_date,
            "start_time": "18:00",
            "end_time": f"{18 + int(hours)}:00",
            "hours_requested": hours,
            "overtime_type": "regular",
            "reason": reason
        }
        
        # Create request (mock)
        request_id = f"OT-{datetime.now().strftime('%Y%m%d')}-{hash(context.user_id) % 1000:03d}"
        
        message = f"""✅ **Solicitud de Horas Extra Creada**

🆔 **ID Solicitud:** {request_id}
📅 **Fecha:** {work_date}
⏰ **Horas:** {hours} horas
💰 **Monto:** ${overtime_amount:,.2f}
📝 **Motivo:** {reason}

📋 **Estado:** Pendiente de aprobación
👤 **Aprobador:** Tu supervisor directo

⏳ **Tiempo estimado de respuesta:** 24-48 horas

¿Deseas hacer otra solicitud o consultar el estado de solicitudes anteriores?"""
        
        quick_replies = [
            "Ver mis solicitudes",
            "Nueva solicitud",
            "Política de horas extra",
            "Contactar supervisor"
        ]
        
        return ChatbotResponse(
            message=message,
            message_type=MessageType.QUICK_REPLY,
            quick_replies=quick_replies,
            next_state=ConversationState.COMPLETED
        )
    
    async def get_overtime_status(self, context: ConversationContext) -> ChatbotResponse:
        """Get overtime requests status"""
        # Mock overtime requests
        requests = [
            {
                "id": "OT-20241215-001",
                "date": "15/12/2024",
                "hours": 3.0,
                "amount": 720.00,
                "status": "approved",
                "approver": "María García"
            },
            {
                "id": "OT-20241210-002", 
                "date": "10/12/2024",
                "hours": 2.5,
                "amount": 600.00,
                "status": "pending",
                "approver": "María García"
            }
        ]
        
        message = "📋 **Mis Solicitudes de Horas Extra**\n\n"
        
        for req in requests:
            status_emoji = "✅" if req["status"] == "approved" else "⏳" if req["status"] == "pending" else "❌"
            message += f"""{status_emoji} **{req['id']}**
📅 Fecha: {req['date']}
⏰ Horas: {req['hours']}
💰 Monto: ${req['amount']:,.2f}
📊 Estado: {req['status'].title()}
👤 Aprobador: {req['approver']}

"""
        
        return ChatbotResponse(
            message=message,
            quick_replies=["Nueva solicitud", "Política horas extra", "Volver al menú"]
        )


class ChatbotEngine:
    """Main chatbot engine with AI capabilities"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.payroll_engine = PayrollEngine()
        self.overtime_engine = OvertimeManagementEngine()
        self.payroll_assistant = PayrollAssistant(self.payroll_engine)
        self.overtime_assistant = OvertimeAssistant(self.overtime_engine)
        
        # In-memory context storage (would use Redis in production)
        self.contexts: Dict[str, ConversationContext] = {}
        
        # Response templates
        self.templates = {
            "greeting": """¡Hola! 👋 Soy el Asistente de huntRED®

Puedo ayudarte con:
💰 Consultas de nómina
⏰ Solicitudes de horas extra  
👤 Información de perfil
📊 Reportes (solo administradores)

¿En qué puedo ayudarte hoy?""",
            
            "authentication_required": """🔐 **Autenticación Requerida**

Para acceder a tu información personal, necesito verificar tu identidad.

Por favor proporciona tu **número de empleado** o **ID de usuario**.

Ejemplo: "Mi número de empleado es 12345" """,
            
            "help": """🆘 **Centro de Ayuda - huntRED®**

**Comandos disponibles:**
• "Mi nómina" - Ver información de pago
• "Horas extra" - Solicitar o consultar horas extra
• "Mi perfil" - Ver/actualizar información personal
• "Ayuda" - Mostrar este menú

**Ejemplos de preguntas:**
• "¿Cuánto gané este mes?"
• "Quiero solicitar 3 horas extra del 15/12"
• "¿Cuándo es mi próximo pago?"
• "Actualizar mi teléfono"

**Soporte técnico:** soporte@huntred.com
**Horario:** Lunes a Viernes 9:00-18:00""",
            
            "unknown": """❓ No entendí tu solicitud.

Puedes preguntarme sobre:
• 💰 Nómina y pagos
• ⏰ Horas extra
• 👤 Tu perfil
• 📊 Reportes

O escribe "ayuda" para ver todas las opciones disponibles.""",
            
            "goodbye": """👋 ¡Hasta luego!

Gracias por usar el Asistente de huntRED®. 

Si necesitas ayuda adicional, no dudes en escribirme nuevamente.

**huntRED® - Tecnología que conecta talento** 🌟"""
        }
    
    def _get_context_key(self, user_id: str, company_id: str, channel: MessageChannel) -> str:
        """Generate unique context key"""
        return f"{company_id}:{user_id}:{channel.value}"
    
    def _get_or_create_context(self, user_id: str, company_id: str, channel: MessageChannel) -> ConversationContext:
        """Get or create conversation context"""
        key = self._get_context_key(user_id, company_id, channel)
        
        if key not in self.contexts:
            self.contexts[key] = ConversationContext(
                user_id=user_id,
                company_id=company_id,
                channel=channel
            )
        
        return self.contexts[key]
    
    async def process_message(self, user_id: str, company_id: str, message: str, 
                            channel: MessageChannel, user_role: str = "employee") -> ChatbotResponse:
        """Process incoming message and generate response"""
        try:
            # Get conversation context
            context = self._get_or_create_context(user_id, company_id, channel)
            context.last_message = message
            context.message_count += 1
            context.updated_at = datetime.now()
            
            # Classify intent
            intent = self.intent_classifier.classify_intent(message, user_role)
            context.intent = intent
            
            # Extract entities
            entities = self.intent_classifier.extract_entities(message, intent)
            context.entities.update(entities)
            
            # Route to appropriate handler
            response = await self._route_message(context, message, user_role)
            
            # Update context state
            if response.next_state:
                context.state = response.next_state
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return ChatbotResponse(
                message="❌ Ocurrió un error procesando tu mensaje. Por favor intenta nuevamente.",
                next_state=ConversationState.INITIAL
            )
    
    async def _route_message(self, context: ConversationContext, message: str, user_role: str) -> ChatbotResponse:
        """Route message to appropriate handler based on intent and state"""
        
        # Handle authentication flow
        if context.intent == IntentType.AUTHENTICATION or context.state == ConversationState.WAITING_INPUT:
            return await self._handle_authentication(context, message)
        
        # Handle greeting
        if context.intent == IntentType.GREETING:
            return ChatbotResponse(
                message=self.templates["greeting"],
                message_type=MessageType.QUICK_REPLY,
                quick_replies=["Mi nómina", "Horas extra", "Mi perfil", "Ayuda"],
                next_state=ConversationState.AUTHENTICATED
            )
        
        # Handle payroll queries
        if context.intent == IntentType.PAYROLL_QUERY:
            if not self._is_authenticated(context):
                return ChatbotResponse(
                    message=self.templates["authentication_required"],
                    requires_auth=True,
                    next_state=ConversationState.WAITING_INPUT
                )
            return await self.payroll_assistant.handle_payroll_query(context)
        
        # Handle overtime requests
        if context.intent == IntentType.OVERTIME_REQUEST:
            if not self._is_authenticated(context):
                return ChatbotResponse(
                    message=self.templates["authentication_required"],
                    requires_auth=True,
                    next_state=ConversationState.WAITING_INPUT
                )
            return await self.overtime_assistant.handle_overtime_request(context)
        
        # Handle help requests
        if context.intent == IntentType.HELP:
            return ChatbotResponse(
                message=self.templates["help"],
                quick_replies=["Mi nómina", "Horas extra", "Mi perfil", "Volver"]
            )
        
        # Handle admin commands
        if context.intent == IntentType.ADMIN_COMMAND:
            return await self._handle_admin_command(context, message, user_role)
        
        # Handle goodbye
        if context.intent == IntentType.GOODBYE:
            # Reset context
            context.state = ConversationState.INITIAL
            context.entities.clear()
            return ChatbotResponse(
                message=self.templates["goodbye"],
                next_state=ConversationState.INITIAL
            )
        
        # Handle context-specific responses
        if context.state == ConversationState.PAYROLL_INQUIRY:
            return await self.payroll_assistant.handle_payroll_detail(context, message)
        
        # Handle quick replies and button responses
        if message.lower() in ["ver mis solicitudes", "mis solicitudes"]:
            return await self.overtime_assistant.get_overtime_status(context)
        
        # Default unknown response
        return ChatbotResponse(
            message=self.templates["unknown"],
            quick_replies=["Mi nómina", "Horas extra", "Ayuda"]
        )
    
    async def _handle_authentication(self, context: ConversationContext, message: str) -> ChatbotResponse:
        """Handle user authentication"""
        # Extract employee ID from message
        employee_id_match = re.search(r'(\d+)', message)
        
        if employee_id_match:
            employee_id = employee_id_match.group(1)
            
            # Mock authentication (would verify against database)
            if len(employee_id) >= 3:  # Simple validation
                context.entities["employee_id"] = employee_id
                context.entities["authenticated"] = True
                context.state = ConversationState.AUTHENTICATED
                
                return ChatbotResponse(
                    message=f"""✅ **Autenticación Exitosa**

Bienvenido, empleado #{employee_id}

Ahora puedes acceder a:
💰 Tu información de nómina
⏰ Solicitudes de horas extra
👤 Tu perfil personal

¿Qué te gustaría consultar?""",
                    message_type=MessageType.QUICK_REPLY,
                    quick_replies=["Mi nómina", "Horas extra", "Mi perfil", "Ayuda"],
                    next_state=ConversationState.AUTHENTICATED
                )
            else:
                return ChatbotResponse(
                    message="❌ Número de empleado inválido. Debe tener al menos 3 dígitos. Intenta nuevamente.",
                    next_state=ConversationState.WAITING_INPUT
                )
        else:
            return ChatbotResponse(
                message="❌ No pude identificar tu número de empleado. Por favor escribe solo el número. Ejemplo: 12345",
                next_state=ConversationState.WAITING_INPUT
            )
    
    async def _handle_admin_command(self, context: ConversationContext, message: str, user_role: str) -> ChatbotResponse:
        """Handle admin-specific commands"""
        if user_role not in ["hr_admin", "super_admin", "manager"]:
            return ChatbotResponse(
                message="❌ No tienes permisos para ejecutar comandos administrativos."
            )
        
        if "dashboard" in message.lower() or "panel" in message.lower():
            # Mock admin dashboard
            return ChatbotResponse(
                message="""📊 **Dashboard Administrativo**

👥 **Empleados:**
• Total: 125 empleados
• Activos: 122
• En vacaciones: 3

💰 **Nómina Actual:**
• Total bruto: $3,125,000
• Total neto: $2,437,500
• Pendientes: 3 empleados

⏰ **Horas Extra:**
• Solicitudes pendientes: 8
• Aprobadas hoy: 12
• Total mes: $45,600

📈 **Métricas:**
• Asistencia promedio: 96.5%
• Satisfacción: 4.2/5.0
• Rotación mensual: 1.8%""",
                quick_replies=["Ver empleados", "Aprobar horas extra", "Reportes", "Volver"]
            )
        
        elif "empleados" in message.lower():
            return ChatbotResponse(
                message="""👥 **Gestión de Empleados**

**Acciones disponibles:**
• Ver lista de empleados
• Buscar empleado específico
• Ver empleados por departamento
• Empleados con cumpleaños
• Reportes de asistencia

Escribe el nombre del empleado o departamento que quieres consultar.""",
                quick_replies=["Todos los empleados", "Por departamento", "Cumpleaños", "Volver"]
            )
        
        return ChatbotResponse(
            message="Comando administrativo no reconocido. Disponibles: dashboard, empleados, reportes."
        )
    
    def _is_authenticated(self, context: ConversationContext) -> bool:
        """Check if user is authenticated"""
        return context.entities.get("authenticated", False)
    
    async def get_conversation_history(self, user_id: str, company_id: str, channel: MessageChannel) -> List[Dict[str, Any]]:
        """Get conversation history for user"""
        key = self._get_context_key(user_id, company_id, channel)
        context = self.contexts.get(key)
        
        if not context:
            return []
        
        # Mock conversation history
        return [
            {
                "timestamp": context.created_at.isoformat(),
                "message": context.last_message or "Conversación iniciada",
                "intent": context.intent.value if context.intent else "unknown",
                "state": context.state.value,
                "message_count": context.message_count
            }
        ]
    
    async def reset_conversation(self, user_id: str, company_id: str, channel: MessageChannel):
        """Reset conversation context"""
        key = self._get_context_key(user_id, company_id, channel)
        if key in self.contexts:
            del self.contexts[key]
    
    async def get_analytics(self, company_id: Optional[str] = None) -> Dict[str, Any]:
        """Get chatbot analytics"""
        # Filter contexts by company if specified
        relevant_contexts = []
        for context in self.contexts.values():
            if not company_id or context.company_id == company_id:
                relevant_contexts.append(context)
        
        if not relevant_contexts:
            return {
                "total_conversations": 0,
                "active_conversations": 0,
                "total_messages": 0,
                "intent_distribution": {},
                "channel_distribution": {},
                "avg_messages_per_conversation": 0
            }
        
        # Calculate analytics
        total_conversations = len(relevant_contexts)
        active_conversations = len([c for c in relevant_contexts if c.state != ConversationState.COMPLETED])
        total_messages = sum(c.message_count for c in relevant_contexts)
        
        # Intent distribution
        intent_counts = {}
        for context in relevant_contexts:
            if context.intent:
                intent_counts[context.intent.value] = intent_counts.get(context.intent.value, 0) + 1
        
        # Channel distribution
        channel_counts = {}
        for context in relevant_contexts:
            channel_counts[context.channel.value] = channel_counts.get(context.channel.value, 0) + 1
        
        return {
            "total_conversations": total_conversations,
            "active_conversations": active_conversations,
            "total_messages": total_messages,
            "intent_distribution": intent_counts,
            "channel_distribution": channel_counts,
            "avg_messages_per_conversation": total_messages / total_conversations if total_conversations > 0 else 0,
            "most_common_intent": max(intent_counts.items(), key=lambda x: x[1])[0] if intent_counts else "unknown",
            "most_used_channel": max(channel_counts.items(), key=lambda x: x[1])[0] if channel_counts else "unknown"
        }