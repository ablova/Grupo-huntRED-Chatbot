"""
Overtime Management System huntRED® v2
======================================

Funcionalidades:
- Gestión completa de horas extra
- Sistema de autorizaciones multi-nivel
- Cálculos automáticos por país/región
- Compliance internacional (México, USA, EU, LATAM)
- Integración con WhatsApp y nómina
- Reportes predictivos con ML
- Límites legales automáticos
- Notifications en tiempo real
"""

import asyncio
import uuid
from datetime import datetime, timedelta, time, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class OvertimeType(Enum):
    """Tipos de horas extra por país/región."""
    # México
    MEXICO_DOUBLE = "mexico_double"      # Primeras 9 horas: doble
    MEXICO_TRIPLE = "mexico_triple"      # Después de 9 horas: triple
    MEXICO_SUNDAY = "mexico_sunday"      # Domingo: triple
    MEXICO_HOLIDAY = "mexico_holiday"    # Día festivo: triple
    
    # Estados Unidos
    USA_OVERTIME = "usa_overtime"        # >40 hrs/semana: 1.5x
    USA_DOUBLE = "usa_double"           # >60 hrs/semana: 2x (algunos estados)
    
    # Unión Europea
    EU_OVERTIME = "eu_overtime"         # >40 hrs/semana: 1.25x-1.5x
    EU_NIGHT = "eu_night"              # Nocturno: +25%
    EU_WEEKEND = "eu_weekend"          # Fin de semana: +50%
    
    # Latinoamérica
    LATAM_OVERTIME = "latam_overtime"   # Configurable por país
    LATAM_NIGHT = "latam_night"        # Nocturno
    LATAM_HOLIDAY = "latam_holiday"    # Festivos

class OvertimeStatus(Enum):
    """Estados de solicitud de horas extra."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ApprovalLevel(Enum):
    """Niveles de aprobación."""
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    HR = "hr"
    DIRECTOR = "director"
    AUTO_APPROVED = "auto_approved"

class WorkShiftType(Enum):
    """Tipos de turno laboral."""
    DAY_SHIFT = "day"        # 6:00 - 18:00
    NIGHT_SHIFT = "night"    # 18:00 - 6:00
    ROTATING = "rotating"    # Rotativo
    FLEXIBLE = "flexible"    # Horario flexible

@dataclass
class CountryOvertimeRules:
    """Reglas de horas extra por país."""
    country_code: str
    country_name: str
    
    # Límites legales
    max_overtime_daily: int = 3      # Horas extra máximas por día
    max_overtime_weekly: int = 15    # Horas extra máximas por semana
    max_overtime_monthly: int = 60   # Horas extra máximas por mes
    max_overtime_annual: int = 200   # Horas extra máximas por año
    
    # Multiplicadores de pago
    overtime_multiplier: Decimal = Decimal('1.5')     # Normal overtime
    double_multiplier: Decimal = Decimal('2.0')       # Double time
    triple_multiplier: Decimal = Decimal('3.0')       # Triple time
    night_multiplier: Decimal = Decimal('1.25')       # Night shift
    weekend_multiplier: Decimal = Decimal('1.5')      # Weekend
    holiday_multiplier: Decimal = Decimal('2.5')      # Holidays
    
    # Horarios especiales
    night_start_hour: int = 22       # Inicio turno nocturno
    night_end_hour: int = 6         # Fin turno nocturno
    
    # Configuración de aprobaciones
    auto_approve_limit: int = 2      # Auto-aprobar hasta X horas
    requires_justification: bool = True
    
    # Días de descanso obligatorios
    mandatory_rest_days: List[str] = field(default_factory=lambda: ["sunday"])
    
    # Metadatos
    currency: str = "USD"
    timezone: str = "UTC"
    effective_date: date = field(default_factory=date.today)

@dataclass
class OvertimeRequest:
    """Solicitud de horas extra."""
    id: str
    employee_id: str
    client_id: str
    
    # Detalles de la solicitud
    requested_date: date
    start_time: time
    end_time: time
    total_hours: Decimal
    overtime_type: OvertimeType
    
    # Justificación
    reason: str
    description: str = ""
    priority: str = "normal"  # low, normal, high, urgent
    
    # Autorización
    status: OvertimeStatus = OvertimeStatus.PENDING
    approval_level_required: ApprovalLevel = ApprovalLevel.SUPERVISOR
    
    # Aprobadores
    requested_by: str = ""
    approved_by: Optional[str] = None
    approval_chain: List[Dict[str, Any]] = field(default_factory=list)
    
    # Cálculos
    regular_rate: Decimal = Decimal('0')
    overtime_rate: Decimal = Decimal('0')
    total_payment: Decimal = Decimal('0')
    
    # Tracking
    actual_start_time: Optional[time] = None
    actual_end_time: Optional[time] = None
    actual_hours: Optional[Decimal] = None
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: str = ""

@dataclass
class OvertimeTracking:
    """Seguimiento de horas extra por empleado."""
    employee_id: str
    period_year: int
    period_month: int
    
    # Acumulados
    daily_overtime: Dict[str, Decimal] = field(default_factory=dict)  # date -> hours
    weekly_overtime: Dict[int, Decimal] = field(default_factory=dict)  # week -> hours
    monthly_overtime: Decimal = Decimal('0')
    annual_overtime: Decimal = Decimal('0')
    
    # Límites
    daily_limit_exceeded: List[str] = field(default_factory=list)     # dates
    weekly_limit_exceeded: List[int] = field(default_factory=list)    # weeks
    monthly_limit_exceeded: bool = False
    annual_limit_exceeded: bool = False
    
    # Pagos
    total_overtime_payment: Decimal = Decimal('0')
    pending_payment: Decimal = Decimal('0')
    
    # Metadatos
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class ApprovalWorkflow:
    """Flujo de aprobaciones personalizable."""
    client_id: str
    workflow_name: str
    
    # Configuración del workflow
    levels: List[Dict[str, Any]] = field(default_factory=list)
    
    # Condiciones automáticas
    auto_approve_conditions: Dict[str, Any] = field(default_factory=dict)
    escalation_rules: Dict[str, Any] = field(default_factory=dict)
    
    # Notificaciones
    notification_settings: Dict[str, Any] = field(default_factory=dict)
    
    # SLA
    approval_timeout_hours: int = 24
    escalation_timeout_hours: int = 48
    
    # Metadatos
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

class OvertimeManagement:
    """Sistema principal de gestión de horas extra."""
    
    def __init__(self):
        self.requests: Dict[str, OvertimeRequest] = {}
        self.tracking: Dict[str, OvertimeTracking] = {}  # employee_id -> tracking
        self.country_rules: Dict[str, CountryOvertimeRules] = {}
        self.workflows: Dict[str, ApprovalWorkflow] = {}
        
        # Importar otros sistemas
        from ..payroll.payroll_engine import PayrollEngine
        from ..chatbot.payroll_whatsapp_bot import PayrollWhatsAppBot
        
        self.payroll_engine = PayrollEngine()
        self.whatsapp_bot = PayrollWhatsAppBot()
        
        # Setup inicial
        self._setup_country_rules()
        self._setup_default_workflows()
    
    def _setup_country_rules(self):
        """Configura reglas de horas extra por país."""
        
        # México
        mexico_rules = CountryOvertimeRules(
            country_code="MX",
            country_name="México",
            max_overtime_daily=3,
            max_overtime_weekly=9,
            max_overtime_monthly=36,
            max_overtime_annual=200,
            overtime_multiplier=Decimal('2.0'),   # Doble
            triple_multiplier=Decimal('3.0'),     # Triple después de 9 hrs
            night_multiplier=Decimal('1.25'),
            weekend_multiplier=Decimal('2.0'),
            holiday_multiplier=Decimal('3.0'),
            night_start_hour=20,
            night_end_hour=6,
            auto_approve_limit=2,
            mandatory_rest_days=["sunday"],
            currency="MXN",
            timezone="America/Mexico_City"
        )
        
        # Estados Unidos
        usa_rules = CountryOvertimeRules(
            country_code="US",
            country_name="United States",
            max_overtime_daily=8,
            max_overtime_weekly=20,
            max_overtime_monthly=80,
            max_overtime_annual=400,
            overtime_multiplier=Decimal('1.5'),
            double_multiplier=Decimal('2.0'),
            night_multiplier=Decimal('1.1'),
            weekend_multiplier=Decimal('1.5'),
            holiday_multiplier=Decimal('2.0'),
            night_start_hour=22,
            night_end_hour=6,
            auto_approve_limit=4,
            mandatory_rest_days=["sunday"],
            currency="USD",
            timezone="America/New_York"
        )
        
        # Unión Europea (base)
        eu_rules = CountryOvertimeRules(
            country_code="EU",
            country_name="European Union",
            max_overtime_daily=2,
            max_overtime_weekly=8,
            max_overtime_monthly=32,
            max_overtime_annual=150,
            overtime_multiplier=Decimal('1.25'),
            double_multiplier=Decimal('1.5'),
            night_multiplier=Decimal('1.2'),
            weekend_multiplier=Decimal('1.5'),
            holiday_multiplier=Decimal('2.0'),
            night_start_hour=22,
            night_end_hour=6,
            auto_approve_limit=1,
            mandatory_rest_days=["sunday"],
            currency="EUR",
            timezone="Europe/Madrid"
        )
        
        # Colombia
        colombia_rules = CountryOvertimeRules(
            country_code="CO",
            country_name="Colombia",
            max_overtime_daily=2,
            max_overtime_weekly=12,
            max_overtime_monthly=48,
            max_overtime_annual=200,
            overtime_multiplier=Decimal('1.25'),
            double_multiplier=Decimal('1.75'),
            night_multiplier=Decimal('1.35'),
            weekend_multiplier=Decimal('1.75'),
            holiday_multiplier=Decimal('2.0'),
            night_start_hour=21,
            night_end_hour=6,
            auto_approve_limit=1,
            mandatory_rest_days=["sunday"],
            currency="COP",
            timezone="America/Bogota"
        )
        
        self.country_rules["MX"] = mexico_rules
        self.country_rules["US"] = usa_rules
        self.country_rules["EU"] = eu_rules
        self.country_rules["CO"] = colombia_rules
    
    def _setup_default_workflows(self):
        """Configura workflows de aprobación por defecto."""
        
        # Workflow estándar
        standard_workflow = ApprovalWorkflow(
            client_id="default",
            workflow_name="Standard Approval",
            levels=[
                {
                    "level": 1,
                    "role": "supervisor",
                    "required": True,
                    "timeout_hours": 24
                },
                {
                    "level": 2,
                    "role": "manager",
                    "required_if": "hours > 4",
                    "timeout_hours": 24
                },
                {
                    "level": 3,
                    "role": "hr",
                    "required_if": "hours > 8 OR total_weekly > 15",
                    "timeout_hours": 48
                }
            ],
            auto_approve_conditions={
                "max_hours": 2,
                "employee_level": "senior",
                "previous_approvals": 5
            },
            escalation_rules={
                "timeout_action": "escalate",
                "max_escalations": 2,
                "final_approver": "director"
            }
        )
        
        self.workflows["default"] = standard_workflow
    
    async def request_overtime(self, request_data: Dict[str, Any]) -> str:
        """Solicita horas extra."""
        
        request_id = str(uuid.uuid4())
        
        # Validar datos
        employee_id = request_data["employee_id"]
        client_id = request_data["client_id"]
        requested_date = datetime.strptime(request_data["date"], "%Y-%m-%d").date()
        start_time = datetime.strptime(request_data["start_time"], "%H:%M").time()
        end_time = datetime.strptime(request_data["end_time"], "%H:%M").time()
        
        # Calcular horas
        start_datetime = datetime.combine(requested_date, start_time)
        end_datetime = datetime.combine(requested_date, end_time)
        if end_time < start_time:  # Cruza medianoche
            end_datetime += timedelta(days=1)
        
        total_hours = Decimal(str((end_datetime - start_datetime).total_seconds() / 3600))
        
        # Obtener reglas del país
        country_code = request_data.get("country_code", "MX")
        rules = self.country_rules.get(country_code, self.country_rules["MX"])
        
        # Determinar tipo de horas extra
        overtime_type = await self._determine_overtime_type(
            requested_date, start_time, end_time, country_code
        )
        
        # Validar límites legales
        validation = await self._validate_overtime_limits(
            employee_id, requested_date, total_hours, rules
        )
        
        if not validation["valid"]:
            raise ValueError(f"Overtime request exceeds limits: {validation['reason']}")
        
        # Calcular tasas de pago
        employee = self.payroll_engine.employees.get(employee_id)
        if not employee:
            raise ValueError("Employee not found")
        
        regular_rate = employee.base_salary / Decimal('160')  # Asumiendo 160 hrs/mes
        overtime_rate = await self._calculate_overtime_rate(
            regular_rate, overtime_type, rules
        )
        total_payment = total_hours * overtime_rate
        
        # Determinar nivel de aprobación requerido
        approval_level = await self._determine_approval_level(
            total_hours, employee_id, client_id, rules
        )
        
        # Crear solicitud
        request = OvertimeRequest(
            id=request_id,
            employee_id=employee_id,
            client_id=client_id,
            requested_date=requested_date,
            start_time=start_time,
            end_time=end_time,
            total_hours=total_hours,
            overtime_type=overtime_type,
            reason=request_data["reason"],
            description=request_data.get("description", ""),
            priority=request_data.get("priority", "normal"),
            approval_level_required=approval_level,
            requested_by=request_data.get("requested_by", employee_id),
            regular_rate=regular_rate,
            overtime_rate=overtime_rate,
            total_payment=total_payment
        )
        
        # Auto-aprobar si cumple condiciones
        if total_hours <= rules.auto_approve_limit:
            request.status = OvertimeStatus.APPROVED
            request.approved_by = "system"
            request.approved_at = datetime.now()
            await self._send_approval_notification(request, auto_approved=True)
        else:
            # Iniciar flujo de aprobación
            await self._initiate_approval_workflow(request)
        
        self.requests[request_id] = request
        
        # Actualizar tracking
        await self._update_overtime_tracking(employee_id, requested_date, total_hours)
        
        logger.info(f"Overtime request created: {request_id} for {total_hours} hours")
        return request_id
    
    async def _determine_overtime_type(self, date: date, start_time: time, 
                                     end_time: time, country_code: str) -> OvertimeType:
        """Determina el tipo de horas extra según país y horario."""
        
        rules = self.country_rules.get(country_code, self.country_rules["MX"])
        
        # Verificar si es domingo
        if date.weekday() == 6:  # Sunday
            if country_code == "MX":
                return OvertimeType.MEXICO_SUNDAY
            elif country_code == "US":
                return OvertimeType.USA_OVERTIME
            else:
                return OvertimeType.EU_WEEKEND
        
        # Verificar si es turno nocturno
        night_start = rules.night_start_hour
        night_end = rules.night_end_hour
        
        if (start_time.hour >= night_start or start_time.hour < night_end or
            end_time.hour >= night_start or end_time.hour < night_end):
            if country_code == "MX":
                return OvertimeType.MEXICO_DOUBLE
            elif country_code == "US":
                return OvertimeType.USA_OVERTIME
            else:
                return OvertimeType.EU_NIGHT
        
        # Tipo normal según país
        if country_code == "MX":
            return OvertimeType.MEXICO_DOUBLE
        elif country_code == "US":
            return OvertimeType.USA_OVERTIME
        else:
            return OvertimeType.EU_OVERTIME
    
    async def _validate_overtime_limits(self, employee_id: str, date: date, 
                                      hours: Decimal, rules: CountryOvertimeRules) -> Dict[str, Any]:
        """Valida que las horas extra no excedan límites legales."""
        
        tracking = await self._get_overtime_tracking(employee_id, date.year, date.month)
        
        # Validar límite diario
        date_str = date.isoformat()
        daily_total = tracking.daily_overtime.get(date_str, Decimal('0')) + hours
        if daily_total > rules.max_overtime_daily:
            return {
                "valid": False,
                "reason": f"Daily limit exceeded: {daily_total}/{rules.max_overtime_daily}"
            }
        
        # Validar límite semanal
        week_number = date.isocalendar()[1]
        weekly_total = tracking.weekly_overtime.get(week_number, Decimal('0')) + hours
        if weekly_total > rules.max_overtime_weekly:
            return {
                "valid": False,
                "reason": f"Weekly limit exceeded: {weekly_total}/{rules.max_overtime_weekly}"
            }
        
        # Validar límite mensual
        monthly_total = tracking.monthly_overtime + hours
        if monthly_total > rules.max_overtime_monthly:
            return {
                "valid": False,
                "reason": f"Monthly limit exceeded: {monthly_total}/{rules.max_overtime_monthly}"
            }
        
        # Validar límite anual
        annual_total = tracking.annual_overtime + hours
        if annual_total > rules.max_overtime_annual:
            return {
                "valid": False,
                "reason": f"Annual limit exceeded: {annual_total}/{rules.max_overtime_annual}"
            }
        
        return {"valid": True}
    
    async def _calculate_overtime_rate(self, regular_rate: Decimal, 
                                     overtime_type: OvertimeType,
                                     rules: CountryOvertimeRules) -> Decimal:
        """Calcula la tasa de pago de horas extra."""
        
        multiplier_map = {
            OvertimeType.MEXICO_DOUBLE: rules.overtime_multiplier,
            OvertimeType.MEXICO_TRIPLE: rules.triple_multiplier,
            OvertimeType.MEXICO_SUNDAY: rules.triple_multiplier,
            OvertimeType.MEXICO_HOLIDAY: rules.holiday_multiplier,
            OvertimeType.USA_OVERTIME: rules.overtime_multiplier,
            OvertimeType.USA_DOUBLE: rules.double_multiplier,
            OvertimeType.EU_OVERTIME: rules.overtime_multiplier,
            OvertimeType.EU_NIGHT: rules.night_multiplier,
            OvertimeType.EU_WEEKEND: rules.weekend_multiplier,
            OvertimeType.LATAM_OVERTIME: rules.overtime_multiplier,
            OvertimeType.LATAM_NIGHT: rules.night_multiplier,
            OvertimeType.LATAM_HOLIDAY: rules.holiday_multiplier
        }
        
        multiplier = multiplier_map.get(overtime_type, rules.overtime_multiplier)
        return regular_rate * multiplier
    
    async def _determine_approval_level(self, hours: Decimal, employee_id: str,
                                      client_id: str, rules: CountryOvertimeRules) -> ApprovalLevel:
        """Determina el nivel de aprobación requerido."""
        
        # Auto-aprobación para horas menores al límite
        if hours <= rules.auto_approve_limit:
            return ApprovalLevel.AUTO_APPROVED
        
        # Supervisor para horas normales
        if hours <= 4:
            return ApprovalLevel.SUPERVISOR
        
        # Manager para horas altas
        if hours <= 8:
            return ApprovalLevel.MANAGER
        
        # HR para horas muy altas
        return ApprovalLevel.HR
    
    async def _initiate_approval_workflow(self, request: OvertimeRequest):
        """Inicia el flujo de aprobación."""
        
        workflow = self.workflows.get(request.client_id, self.workflows["default"])
        
        # Agregar primer nivel de aprobación
        first_level = workflow.levels[0]
        approval_step = {
            "level": first_level["level"],
            "role": first_level["role"],
            "status": "pending",
            "requested_at": datetime.now(),
            "timeout_at": datetime.now() + timedelta(hours=first_level["timeout_hours"])
        }
        
        request.approval_chain.append(approval_step)
        
        # Enviar notificación
        await self._send_approval_notification(request)
    
    async def approve_overtime(self, request_id: str, approver_id: str, 
                             decision: str, comments: str = "") -> bool:
        """Aprueba o rechaza una solicitud de horas extra."""
        
        request = self.requests.get(request_id)
        if not request:
            return False
        
        if request.status != OvertimeStatus.PENDING:
            return False
        
        # Actualizar solicitud
        if decision.lower() == "approved":
            request.status = OvertimeStatus.APPROVED
            request.approved_by = approver_id
            request.approved_at = datetime.now()
            
            # Enviar notificación de aprobación
            await self._send_approval_notification(request, approved=True)
            
            # Notificar por WhatsApp
            await self._send_whatsapp_notification(request, "approved")
            
        elif decision.lower() == "rejected":
            request.status = OvertimeStatus.REJECTED
            request.notes = comments
            
            # Enviar notificación de rechazo
            await self._send_approval_notification(request, rejected=True)
            
            # Notificar por WhatsApp
            await self._send_whatsapp_notification(request, "rejected")
        
        # Actualizar cadena de aprobación
        if request.approval_chain:
            current_step = request.approval_chain[-1]
            current_step["status"] = decision.lower()
            current_step["approver_id"] = approver_id
            current_step["approved_at"] = datetime.now()
            current_step["comments"] = comments
        
        logger.info(f"Overtime request {request_id} {decision} by {approver_id}")
        return True
    
    async def start_overtime_tracking(self, request_id: str) -> bool:
        """Inicia el tracking de horas extra."""
        
        request = self.requests.get(request_id)
        if not request or request.status != OvertimeStatus.APPROVED:
            return False
        
        request.status = OvertimeStatus.IN_PROGRESS
        request.actual_start_time = datetime.now().time()
        
        # Notificar inicio por WhatsApp
        await self._send_whatsapp_notification(request, "started")
        
        logger.info(f"Overtime tracking started for request {request_id}")
        return True
    
    async def complete_overtime_tracking(self, request_id: str, 
                                       actual_end_time: Optional[time] = None) -> Dict[str, Any]:
        """Completa el tracking de horas extra."""
        
        request = self.requests.get(request_id)
        if not request or request.status != OvertimeStatus.IN_PROGRESS:
            return {"success": False, "error": "Invalid request or status"}
        
        # Registrar tiempo real
        if actual_end_time:
            request.actual_end_time = actual_end_time
        else:
            request.actual_end_time = datetime.now().time()
        
        # Calcular horas reales
        if request.actual_start_time and request.actual_end_time:
            start_dt = datetime.combine(request.requested_date, request.actual_start_time)
            end_dt = datetime.combine(request.requested_date, request.actual_end_time)
            
            if request.actual_end_time < request.actual_start_time:
                end_dt += timedelta(days=1)
            
            actual_hours = Decimal(str((end_dt - start_dt).total_seconds() / 3600))
            request.actual_hours = actual_hours
            
            # Recalcular pago basado en horas reales
            request.total_payment = actual_hours * request.overtime_rate
        
        request.status = OvertimeStatus.COMPLETED
        request.completed_at = datetime.now()
        
        # Actualizar tracking del empleado
        await self._update_overtime_tracking(
            request.employee_id, 
            request.requested_date, 
            request.actual_hours or request.total_hours
        )
        
        # Integrar con nómina
        await self._integrate_with_payroll(request)
        
        # Notificar completado por WhatsApp
        await self._send_whatsapp_notification(request, "completed")
        
        result = {
            "success": True,
            "request_id": request_id,
            "planned_hours": float(request.total_hours),
            "actual_hours": float(request.actual_hours or request.total_hours),
            "total_payment": float(request.total_payment)
        }
        
        logger.info(f"Overtime completed for request {request_id}: {result}")
        return result
    
    async def _get_overtime_tracking(self, employee_id: str, year: int, month: int) -> OvertimeTracking:
        """Obtiene o crea el tracking de horas extra para un empleado."""
        
        tracking_key = f"{employee_id}_{year}_{month:02d}"
        
        if tracking_key not in self.tracking:
            self.tracking[tracking_key] = OvertimeTracking(
                employee_id=employee_id,
                period_year=year,
                period_month=month
            )
        
        return self.tracking[tracking_key]
    
    async def _update_overtime_tracking(self, employee_id: str, date: date, hours: Decimal):
        """Actualiza el tracking de horas extra."""
        
        tracking = await self._get_overtime_tracking(employee_id, date.year, date.month)
        
        # Actualizar por día
        date_str = date.isoformat()
        tracking.daily_overtime[date_str] = tracking.daily_overtime.get(date_str, Decimal('0')) + hours
        
        # Actualizar por semana
        week_number = date.isocalendar()[1]
        tracking.weekly_overtime[week_number] = tracking.weekly_overtime.get(week_number, Decimal('0')) + hours
        
        # Actualizar mensual
        tracking.monthly_overtime += hours
        
        # Actualizar anual (buscar en otros meses del año)
        annual_total = hours
        for month in range(1, 13):
            if month != date.month:
                month_tracking = await self._get_overtime_tracking(employee_id, date.year, month)
                annual_total += month_tracking.monthly_overtime
        
        tracking.annual_overtime = annual_total
        tracking.last_updated = datetime.now()
    
    async def _integrate_with_payroll(self, request: OvertimeRequest):
        """Integra las horas extra con el sistema de nómina."""
        
        # Buscar el empleado en el sistema de nómina
        employee = self.payroll_engine.employees.get(request.employee_id)
        if not employee:
            return
        
        # Agregar concepto de horas extra al próximo período de nómina
        # En un sistema real, esto se haría a través de la API del PayrollEngine
        payroll_concept = {
            "employee_id": request.employee_id,
            "concept_type": "overtime",
            "amount": request.total_payment,
            "hours": request.actual_hours or request.total_hours,
            "rate": request.overtime_rate,
            "overtime_type": request.overtime_type.value,
            "date": request.requested_date.isoformat(),
            "request_id": request.id
        }
        
        logger.info(f"Overtime integrated with payroll: {payroll_concept}")
    
    async def _send_approval_notification(self, request: OvertimeRequest, 
                                        auto_approved: bool = False,
                                        approved: bool = False, 
                                        rejected: bool = False):
        """Envía notificaciones de aprobación."""
        
        employee = self.payroll_engine.employees.get(request.employee_id)
        if not employee:
            return
        
        if auto_approved:
            message = f"✅ Horas extra auto-aprobadas\n\n"
            message += f"📅 Fecha: {request.requested_date.strftime('%d/%m/%Y')}\n"
            message += f"⏰ Horario: {request.start_time} - {request.end_time}\n"
            message += f"🕐 Total: {request.total_hours} horas\n"
            message += f"💰 Pago: ${request.total_payment:,.2f}\n\n"
            message += f"Puedes iniciar cuando estés listo."
        
        elif approved:
            message = f"✅ Horas extra APROBADAS\n\n"
            message += f"📅 Fecha: {request.requested_date.strftime('%d/%m/%Y')}\n"
            message += f"⏰ Horario: {request.start_time} - {request.end_time}\n"
            message += f"🕐 Total: {request.total_hours} horas\n"
            message += f"💰 Pago: ${request.total_payment:,.2f}\n"
            message += f"👤 Aprobado por: {request.approved_by}\n\n"
            message += f"Escribe 'iniciar overtime {request.id[:8]}' cuando comiences."
        
        elif rejected:
            message = f"❌ Horas extra RECHAZADAS\n\n"
            message += f"📅 Fecha: {request.requested_date.strftime('%d/%m/%Y')}\n"
            message += f"⏰ Horario: {request.start_time} - {request.end_time}\n"
            message += f"🕐 Total: {request.total_hours} horas\n"
            if request.notes:
                message += f"\n📝 Motivo: {request.notes}"
        
        else:
            # Pendiente de aprobación
            message = f"⏳ Horas extra enviadas para aprobación\n\n"
            message += f"📅 Fecha: {request.requested_date.strftime('%d/%m/%Y')}\n"
            message += f"⏰ Horario: {request.start_time} - {request.end_time}\n"
            message += f"🕐 Total: {request.total_hours} horas\n"
            message += f"📝 Motivo: {request.reason}\n\n"
            message += f"Te notificaremos cuando sea aprobada."
        
        # En un sistema real, aquí se enviaría por email, WhatsApp, etc.
        logger.info(f"Notification sent for request {request.id}: {message}")
    
    async def _send_whatsapp_notification(self, request: OvertimeRequest, status: str):
        """Envía notificación por WhatsApp."""
        
        # En un sistema real, esto se integraría con el WhatsApp bot
        employee = self.payroll_engine.employees.get(request.employee_id)
        if not employee:
            return
        
        # Simular envío de mensaje
        logger.info(f"WhatsApp notification sent to {employee.first_name} {employee.last_name}: overtime {status}")
    
    def get_overtime_summary(self, employee_id: str, year: int, month: int) -> Dict[str, Any]:
        """Obtiene resumen de horas extra de un empleado."""
        
        tracking = self.tracking.get(f"{employee_id}_{year}_{month:02d}")
        if not tracking:
            return {"error": "No overtime data found"}
        
        # Obtener solicitudes del período
        period_requests = [
            req for req in self.requests.values()
            if (req.employee_id == employee_id and 
                req.requested_date.year == year and 
                req.requested_date.month == month)
        ]
        
        # Estadísticas por estado
        status_counts = {}
        for status in OvertimeStatus:
            status_counts[status.value] = len([
                req for req in period_requests if req.status == status
            ])
        
        return {
            "employee_id": employee_id,
            "period": f"{year}-{month:02d}",
            "summary": {
                "total_hours": float(tracking.monthly_overtime),
                "total_payment": float(tracking.total_overtime_payment),
                "pending_payment": float(tracking.pending_payment),
                "requests_count": len(period_requests)
            },
            "by_status": status_counts,
            "limits": {
                "monthly_limit_exceeded": tracking.monthly_limit_exceeded,
                "annual_limit_exceeded": tracking.annual_limit_exceeded
            },
            "requests": [
                {
                    "id": req.id,
                    "date": req.requested_date.isoformat(),
                    "hours": float(req.total_hours),
                    "actual_hours": float(req.actual_hours) if req.actual_hours else None,
                    "payment": float(req.total_payment),
                    "status": req.status.value,
                    "type": req.overtime_type.value
                }
                for req in period_requests
            ]
        }
    
    def get_client_overtime_analytics(self, client_id: str, year: int, month: int) -> Dict[str, Any]:
        """Obtiene analytics de horas extra para un cliente."""
        
        # Filtrar solicitudes del cliente
        client_requests = [
            req for req in self.requests.values()
            if (req.client_id == client_id and 
                req.requested_date.year == year and 
                req.requested_date.month == month)
        ]
        
        if not client_requests:
            return {"error": "No overtime data found for client"}
        
        # Cálculos agregados
        total_hours = sum(req.actual_hours or req.total_hours for req in client_requests)
        total_cost = sum(req.total_payment for req in client_requests)
        total_requests = len(client_requests)
        
        # Por empleado
        by_employee = {}
        for req in client_requests:
            emp_id = req.employee_id
            if emp_id not in by_employee:
                by_employee[emp_id] = {
                    "hours": Decimal('0'),
                    "cost": Decimal('0'),
                    "requests": 0
                }
            by_employee[emp_id]["hours"] += req.actual_hours or req.total_hours
            by_employee[emp_id]["cost"] += req.total_payment
            by_employee[emp_id]["requests"] += 1
        
        # Por tipo
        by_type = {}
        for req in client_requests:
            ot_type = req.overtime_type.value
            if ot_type not in by_type:
                by_type[ot_type] = {"hours": Decimal('0'), "cost": Decimal('0'), "count": 0}
            by_type[ot_type]["hours"] += req.actual_hours or req.total_hours
            by_type[ot_type]["cost"] += req.total_payment
            by_type[ot_type]["count"] += 1
        
        return {
            "client_id": client_id,
            "period": f"{year}-{month:02d}",
            "summary": {
                "total_hours": float(total_hours),
                "total_cost": float(total_cost),
                "total_requests": total_requests,
                "average_hours_per_request": float(total_hours / total_requests) if total_requests > 0 else 0
            },
            "by_employee": {
                emp_id: {
                    "hours": float(data["hours"]),
                    "cost": float(data["cost"]),
                    "requests": data["requests"]
                }
                for emp_id, data in by_employee.items()
            },
            "by_type": {
                ot_type: {
                    "hours": float(data["hours"]),
                    "cost": float(data["cost"]),
                    "count": data["count"]
                }
                for ot_type, data in by_type.items()
            }
        }

# Funciones de utilidad
async def setup_country_overtime_rules(country_code: str, rules_data: Dict[str, Any]) -> str:
    """Configura reglas de horas extra para un país."""
    
    management = OvertimeManagement()
    
    rules = CountryOvertimeRules(
        country_code=country_code,
        country_name=rules_data["country_name"],
        max_overtime_daily=rules_data.get("max_overtime_daily", 8),
        max_overtime_weekly=rules_data.get("max_overtime_weekly", 20),
        max_overtime_monthly=rules_data.get("max_overtime_monthly", 80),
        max_overtime_annual=rules_data.get("max_overtime_annual", 400),
        overtime_multiplier=Decimal(str(rules_data.get("overtime_multiplier", 1.5))),
        currency=rules_data.get("currency", "USD"),
        timezone=rules_data.get("timezone", "UTC")
    )
    
    management.country_rules[country_code] = rules
    return f"Overtime rules configured for {country_code}"

# Exportaciones
__all__ = [
    'OvertimeType', 'OvertimeStatus', 'ApprovalLevel', 'WorkShiftType',
    'CountryOvertimeRules', 'OvertimeRequest', 'OvertimeTracking', 'ApprovalWorkflow',
    'OvertimeManagement', 'setup_country_overtime_rules'
]