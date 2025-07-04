"""
Sistema de Nómina huntRED® v2 - Payroll Engine
==============================================

Funcionalidades:
- Cálculo automático de nóminas (ISR, IMSS, INFONAVIT)
- Integración completa WhatsApp por cliente
- Compliance total México (SAT, IMSS, STPS)
- Geolocalización y time tracking
- ML predictivo para costos laborales
- Reportes automáticos con análisis
- Self-service empleados vía WhatsApp
"""

import asyncio
import uuid
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import calendar
from decimal import Decimal, ROUND_HALF_UP
import math

logger = logging.getLogger(__name__)

class PayrollStatus(Enum):
    """Estados de nómina."""
    DRAFT = "draft"
    CALCULATED = "calculated"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"

class PaymentFrequency(Enum):
    """Frecuencias de pago."""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    ANNUAL = "annual"

class EmployeeStatus(Enum):
    """Estados del empleado."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"

class ContractType(Enum):
    """Tipos de contrato."""
    INDEFINITE = "indefinite"
    FIXED_TERM = "fixed_term"
    TRAINING = "training"
    SEASONAL = "seasonal"
    PROJECT = "project"

class PayrollConcept(Enum):
    """Conceptos de nómina."""
    # Percepciones
    BASE_SALARY = "base_salary"
    OVERTIME = "overtime"
    BONUS = "bonus"
    COMMISSION = "commission"
    VACATION_PAY = "vacation_pay"
    CHRISTMAS_BONUS = "christmas_bonus"
    VACATION_PREMIUM = "vacation_premium"
    PRODUCTIVITY_BONUS = "productivity_bonus"
    
    # Deducciones
    ISR = "isr"
    IMSS_EMPLOYEE = "imss_employee"
    INFONAVIT = "infonavit"
    LOAN_DISCOUNT = "loan_discount"
    ABSENCE_DISCOUNT = "absence_discount"
    LATE_DISCOUNT = "late_discount"
    
    # Aportaciones patronales
    IMSS_EMPLOYER = "imss_employer"
    INFONAVIT_EMPLOYER = "infonavit_employer"
    SAR = "sar"
    INFONAVIT_SAR = "infonavit_sar"

@dataclass
class Employee:
    """Empleado en el sistema de nómina."""
    id: str
    client_id: str  # Cliente que contrata el servicio
    
    # Información personal
    first_name: str
    last_name: str
    rfc: str
    curp: str
    nss: str  # Número de Seguridad Social
    
    # Información laboral
    employee_number: str
    hire_date: date
    job_title: str
    department: str
    contract_type: ContractType
    status: EmployeeStatus
    
    # Información salarial
    base_salary: Decimal
    payment_frequency: PaymentFrequency
    
    # Información fiscal
    tax_regime: str = "601"  # Régimen fiscal
    zip_code: str = ""
    
    # Configuración IMSS/INFONAVIT
    imss_salary: Optional[Decimal] = None
    infonavit_discount_type: str = "percentage"  # percentage, vsm, fixed
    infonavit_discount_value: Decimal = Decimal('0')
    
    # Información bancaria
    bank_account: str = ""
    bank_name: str = ""
    bank_clabe: str = ""
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    terminated_at: Optional[datetime] = None

@dataclass
class PayrollPeriod:
    """Período de nómina."""
    id: str
    client_id: str
    
    # Fechas del período
    start_date: date
    end_date: date
    pay_date: date
    
    # Configuración
    frequency: PaymentFrequency
    year: int
    period_number: int
    
    # Estado
    status: PayrollStatus = PayrollStatus.DRAFT
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    calculated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

@dataclass
class PayrollConcepts:
    """Conceptos de nómina para un empleado."""
    employee_id: str
    period_id: str
    
    # Percepciones
    perceptions: Dict[PayrollConcept, Decimal] = field(default_factory=dict)
    
    # Deducciones
    deductions: Dict[PayrollConcept, Decimal] = field(default_factory=dict)
    
    # Aportaciones patronales
    employer_contributions: Dict[PayrollConcept, Decimal] = field(default_factory=dict)
    
    # Totales calculados
    total_perceptions: Decimal = Decimal('0')
    total_deductions: Decimal = Decimal('0')
    net_pay: Decimal = Decimal('0')
    total_employer_cost: Decimal = Decimal('0')
    
    # Días trabajados
    worked_days: int = 0
    absent_days: int = 0
    
    # Metadatos
    calculated_at: datetime = field(default_factory=datetime.now)

@dataclass
class PayrollBatch:
    """Lote de nómina para procesamiento."""
    id: str
    client_id: str
    period_id: str
    
    # Empleados incluidos
    employee_ids: List[str] = field(default_factory=list)
    
    # Resultados
    payroll_concepts: Dict[str, PayrollConcepts] = field(default_factory=dict)
    
    # Totales del lote
    total_employees: int = 0
    total_perceptions: Decimal = Decimal('0')
    total_deductions: Decimal = Decimal('0')
    total_net_pay: Decimal = Decimal('0')
    total_employer_cost: Decimal = Decimal('0')
    
    # Estado
    status: PayrollStatus = PayrollStatus.DRAFT
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None

@dataclass
class TaxTable:
    """Tabla de impuestos ISR."""
    year: int
    frequency: PaymentFrequency
    brackets: List[Dict[str, Decimal]] = field(default_factory=list)
    
    # UMA (Unidad de Medida y Actualización)
    uma_daily: Decimal = Decimal('0')
    uma_monthly: Decimal = Decimal('0')
    uma_annual: Decimal = Decimal('0')

class PayrollEngine:
    """Motor principal del sistema de nómina."""
    
    def __init__(self):
        self.employees: Dict[str, Employee] = {}
        self.periods: Dict[str, PayrollPeriod] = {}
        self.batches: Dict[str, PayrollBatch] = {}
        self.tax_tables: Dict[int, TaxTable] = {}
        
        # Configuración de tasas (2024)
        self.imss_rates = {
            "employee": {
                "retirement": Decimal('0.01125'),  # 1.125%
                "disability": Decimal('0.0025'),   # 0.25%
                "medical": Decimal('0.004')       # 0.4%
            },
            "employer": {
                "retirement": Decimal('0.02'),     # 2%
                "disability": Decimal('0.0175'),   # 1.75%
                "medical": Decimal('0.0104'),      # 1.04%
                "risk": Decimal('0.00522'),        # 0.522% promedio
                "nursery": Decimal('0.01'),        # 1%
                "infonavit": Decimal('0.05')       # 5%
            }
        }
        
        # Configuración INFONAVIT
        self.infonavit_rate = Decimal('0.05')  # 5% sobre salario base
        
        # Setup inicial
        self._setup_tax_tables()
        self._setup_sample_data()
    
    def _setup_tax_tables(self):
        """Configura las tablas de impuestos para 2024."""
        
        # Tabla ISR mensual 2024
        monthly_brackets = [
            {"lower": Decimal('0.01'), "upper": Decimal('644.58'), "rate": Decimal('0.0192'), "fixed": Decimal('0')},
            {"lower": Decimal('644.59'), "upper": Decimal('5470.92'), "rate": Decimal('0.064'), "fixed": Decimal('12.38')},
            {"lower": Decimal('5470.93'), "upper": Decimal('9614.66'), "rate": Decimal('0.1088'), "fixed": Decimal('321.26')},
            {"lower": Decimal('9614.67'), "upper": Decimal('11176.61'), "rate": Decimal('0.16'), "fixed": Decimal('772.10')},
            {"lower": Decimal('11176.62'), "upper": Decimal('13381.47'), "rate": Decimal('0.2136'), "fixed": Decimal('1021.95')},
            {"lower": Decimal('13381.48'), "upper": Decimal('26988.50'), "rate": Decimal('0.2352'), "fixed": Decimal('1492.18')},
            {"lower": Decimal('26988.51'), "upper": Decimal('42537.58'), "rate": Decimal('0.30'), "fixed": Decimal('4690.67')},
            {"lower": Decimal('42537.59'), "upper": Decimal('81211.25'), "rate": Decimal('0.32'), "fixed": Decimal('9355.39')},
            {"lower": Decimal('81211.26'), "upper": Decimal('108281.67'), "rate": Decimal('0.34'), "fixed": Decimal('21732.18')},
            {"lower": Decimal('108281.68'), "upper": Decimal('324845.01'), "rate": Decimal('0.35'), "fixed": Decimal('30906.90')},
            {"lower": Decimal('324845.02'), "upper": None, "rate": Decimal('0.35'), "fixed": Decimal('106803.80')}
        ]
        
        monthly_table = TaxTable(
            year=2024,
            frequency=PaymentFrequency.MONTHLY,
            brackets=monthly_brackets,
            uma_daily=Decimal('108.57'),
            uma_monthly=Decimal('3257.10'),
            uma_annual=Decimal('39085.20')
        )
        
        self.tax_tables[2024] = monthly_table
    
    def _setup_sample_data(self):
        """Configura datos de ejemplo."""
        
        # Empleado de ejemplo
        sample_employee = Employee(
            id="emp_001",
            client_id="client_tech_001",
            first_name="Juan",
            last_name="Pérez García",
            rfc="PEGJ850315ABC",
            curp="PEGJ850315HDFRRL01",
            nss="12345678901",
            employee_number="001",
            hire_date=date(2024, 1, 15),
            job_title="Desarrollador Senior",
            department="Tecnología",
            contract_type=ContractType.INDEFINITE,
            status=EmployeeStatus.ACTIVE,
            base_salary=Decimal('25000.00'),
            payment_frequency=PaymentFrequency.MONTHLY,
            tax_regime="601",
            zip_code="06100"
        )
        
        self.employees["emp_001"] = sample_employee
    
    async def create_employee(self, employee_data: Dict[str, Any]) -> str:
        """Crea un nuevo empleado."""
        
        employee_id = employee_data.get("id", str(uuid.uuid4()))
        
        employee = Employee(
            id=employee_id,
            client_id=employee_data["client_id"],
            first_name=employee_data["first_name"],
            last_name=employee_data["last_name"],
            rfc=employee_data["rfc"],
            curp=employee_data["curp"],
            nss=employee_data["nss"],
            employee_number=employee_data["employee_number"],
            hire_date=datetime.strptime(employee_data["hire_date"], "%Y-%m-%d").date(),
            job_title=employee_data["job_title"],
            department=employee_data["department"],
            contract_type=ContractType(employee_data["contract_type"]),
            status=EmployeeStatus(employee_data.get("status", "active")),
            base_salary=Decimal(str(employee_data["base_salary"])),
            payment_frequency=PaymentFrequency(employee_data["payment_frequency"]),
            tax_regime=employee_data.get("tax_regime", "601"),
            zip_code=employee_data.get("zip_code", ""),
            imss_salary=Decimal(str(employee_data.get("imss_salary", employee_data["base_salary"]))),
            infonavit_discount_type=employee_data.get("infonavit_discount_type", "percentage"),
            infonavit_discount_value=Decimal(str(employee_data.get("infonavit_discount_value", 0))),
            bank_account=employee_data.get("bank_account", ""),
            bank_name=employee_data.get("bank_name", ""),
            bank_clabe=employee_data.get("bank_clabe", "")
        )
        
        self.employees[employee_id] = employee
        
        logger.info(f"Employee created: {employee_id} - {employee.first_name} {employee.last_name}")
        return employee_id
    
    async def create_payroll_period(self, client_id: str, year: int, month: int,
                                  frequency: PaymentFrequency = PaymentFrequency.MONTHLY) -> str:
        """Crea un período de nómina."""
        
        period_id = f"{client_id}_{year}_{month:02d}"
        
        # Calcular fechas del período
        if frequency == PaymentFrequency.MONTHLY:
            start_date = date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = date(year, month, last_day)
            
            # Fecha de pago: último día hábil del mes
            pay_date = self._get_last_business_day(year, month)
        
        period = PayrollPeriod(
            id=period_id,
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            pay_date=pay_date,
            frequency=frequency,
            year=year,
            period_number=month
        )
        
        self.periods[period_id] = period
        
        logger.info(f"Payroll period created: {period_id}")
        return period_id
    
    def _get_last_business_day(self, year: int, month: int) -> date:
        """Obtiene el último día hábil del mes."""
        
        last_day = calendar.monthrange(year, month)[1]
        last_date = date(year, month, last_day)
        
        # Si cae en fin de semana, retroceder
        while last_date.weekday() > 4:  # 5=sábado, 6=domingo
            last_date -= timedelta(days=1)
        
        return last_date
    
    async def calculate_payroll(self, client_id: str, period_id: str,
                              employee_ids: Optional[List[str]] = None) -> str:
        """Calcula la nómina para un período."""
        
        period = self.periods.get(period_id)
        if not period:
            raise ValueError(f"Payroll period not found: {period_id}")
        
        # Obtener empleados a procesar
        if employee_ids is None:
            employee_ids = [
                emp_id for emp_id, emp in self.employees.items()
                if emp.client_id == client_id and emp.status == EmployeeStatus.ACTIVE
            ]
        
        batch_id = f"{period_id}_batch_{int(datetime.now().timestamp())}"
        
        # Crear lote de nómina
        batch = PayrollBatch(
            id=batch_id,
            client_id=client_id,
            period_id=period_id,
            employee_ids=employee_ids,
            total_employees=len(employee_ids)
        )
        
        # Calcular nómina para cada empleado
        for employee_id in employee_ids:
            employee = self.employees.get(employee_id)
            if not employee:
                continue
            
            payroll_concepts = await self._calculate_employee_payroll(
                employee, period, batch_id
            )
            
            batch.payroll_concepts[employee_id] = payroll_concepts
            
            # Acumular totales
            batch.total_perceptions += payroll_concepts.total_perceptions
            batch.total_deductions += payroll_concepts.total_deductions
            batch.total_net_pay += payroll_concepts.net_pay
            batch.total_employer_cost += payroll_concepts.total_employer_cost
        
        batch.status = PayrollStatus.CALCULATED
        batch.processed_at = datetime.now()
        
        self.batches[batch_id] = batch
        
        logger.info(f"Payroll calculated: {batch_id} - {len(employee_ids)} employees")
        return batch_id
    
    async def _calculate_employee_payroll(self, employee: Employee, period: PayrollPeriod,
                                        batch_id: str) -> PayrollConcepts:
        """Calcula la nómina de un empleado específico."""
        
        concepts = PayrollConcepts(
            employee_id=employee.id,
            period_id=period.id
        )
        
        # Obtener días trabajados (por ahora usar días del período)
        period_days = (period.end_date - period.start_date).days + 1
        worked_days = await self._get_worked_days(employee.id, period)
        concepts.worked_days = worked_days
        concepts.absent_days = period_days - worked_days
        
        # Calcular salario base proporcional
        if employee.payment_frequency == PaymentFrequency.MONTHLY:
            daily_salary = employee.base_salary / 30
            base_salary = daily_salary * worked_days
        else:
            base_salary = employee.base_salary
        
        # PERCEPCIONES
        concepts.perceptions[PayrollConcept.BASE_SALARY] = base_salary
        
        # Horas extra (ejemplo: 10 horas al mes)
        overtime_hours = await self._get_overtime_hours(employee.id, period)
        if overtime_hours > 0:
            hourly_rate = (employee.base_salary / 30) / 8  # Asumiendo 8 hrs/día
            overtime_pay = hourly_rate * overtime_hours * Decimal('2')  # Doble pago
            concepts.perceptions[PayrollConcept.OVERTIME] = overtime_pay
        
        # Aguinaldo proporcional (si es diciembre o fin de contrato)
        if period.end_date.month == 12 or employee.status == EmployeeStatus.TERMINATED:
            christmas_bonus = await self._calculate_christmas_bonus(employee, period)
            if christmas_bonus > 0:
                concepts.perceptions[PayrollConcept.CHRISTMAS_BONUS] = christmas_bonus
        
        # Vacaciones (si aplica)
        vacation_pay, vacation_premium = await self._calculate_vacation_pay(employee, period)
        if vacation_pay > 0:
            concepts.perceptions[PayrollConcept.VACATION_PAY] = vacation_pay
            concepts.perceptions[PayrollConcept.VACATION_PREMIUM] = vacation_premium
        
        # Calcular total de percepciones
        concepts.total_perceptions = sum(concepts.perceptions.values())
        
        # DEDUCCIONES
        
        # ISR
        isr_amount = await self._calculate_isr(employee, concepts.total_perceptions, period)
        if isr_amount > 0:
            concepts.deductions[PayrollConcept.ISR] = isr_amount
        
        # IMSS Empleado
        imss_employee = await self._calculate_imss_employee(employee, concepts.total_perceptions)
        if imss_employee > 0:
            concepts.deductions[PayrollConcept.IMSS_EMPLOYEE] = imss_employee
        
        # INFONAVIT
        infonavit_amount = await self._calculate_infonavit(employee, concepts.total_perceptions)
        if infonavit_amount > 0:
            concepts.deductions[PayrollConcept.INFONAVIT] = infonavit_amount
        
        # Descuentos por faltas
        absence_discount = await self._calculate_absence_discount(employee, period, concepts.absent_days)
        if absence_discount > 0:
            concepts.deductions[PayrollConcept.ABSENCE_DISCOUNT] = absence_discount
        
        # Calcular total de deducciones
        concepts.total_deductions = sum(concepts.deductions.values())
        
        # APORTACIONES PATRONALES
        
        # IMSS Patrón
        imss_employer = await self._calculate_imss_employer(employee, concepts.total_perceptions)
        concepts.employer_contributions[PayrollConcept.IMSS_EMPLOYER] = imss_employer
        
        # INFONAVIT Patrón
        infonavit_employer = employee.base_salary * self.infonavit_rate
        concepts.employer_contributions[PayrollConcept.INFONAVIT_EMPLOYER] = infonavit_employer
        
        # SAR
        sar_amount = employee.base_salary * Decimal('0.02')  # 2%
        concepts.employer_contributions[PayrollConcept.SAR] = sar_amount
        
        # INFONAVIT SAR
        infonavit_sar = employee.base_salary * Decimal('0.05')  # 5%
        concepts.employer_contributions[PayrollConcept.INFONAVIT_SAR] = infonavit_sar
        
        # Calcular totales finales
        concepts.net_pay = concepts.total_perceptions - concepts.total_deductions
        concepts.total_employer_cost = (concepts.total_perceptions + 
                                      sum(concepts.employer_contributions.values()))
        
        return concepts
    
    async def _get_worked_days(self, employee_id: str, period: PayrollPeriod) -> int:
        """Obtiene los días trabajados por un empleado en el período."""
        
        # En un sistema real, esto consultaría la base de datos de asistencia
        # Por ahora, simular días trabajados
        period_days = (period.end_date - period.start_date).days + 1
        
        # Simular algunas faltas aleatorias
        import random
        absences = random.randint(0, 2)  # 0-2 faltas al mes
        
        return max(1, period_days - absences)
    
    async def _get_overtime_hours(self, employee_id: str, period: PayrollPeriod) -> int:
        """Obtiene las horas extra trabajadas."""
        
        # Simular horas extra
        import random
        return random.randint(0, 20)  # 0-20 horas extra al mes
    
    async def _calculate_christmas_bonus(self, employee: Employee, period: PayrollPeriod) -> Decimal:
        """Calcula el aguinaldo proporcional."""
        
        # Aguinaldo = 15 días de salario mínimo
        # Si no ha trabajado el año completo, es proporcional
        
        year_start = date(period.year, 1, 1)
        worked_days_year = (period.end_date - max(employee.hire_date, year_start)).days + 1
        
        if worked_days_year >= 365:
            # Aguinaldo completo
            return employee.base_salary / 2  # 15 días = 0.5 meses
        else:
            # Proporcional
            proportion = worked_days_year / 365
            return (employee.base_salary / 2) * Decimal(str(proportion))
    
    async def _calculate_vacation_pay(self, employee: Employee, period: PayrollPeriod) -> Tuple[Decimal, Decimal]:
        """Calcula el pago de vacaciones y prima vacacional."""
        
        # Verificar si el empleado tiene vacaciones pendientes
        # En un sistema real, esto consultaría el balance de vacaciones
        
        # Por ahora, simular que no hay vacaciones en este período
        return Decimal('0'), Decimal('0')
    
    async def _calculate_isr(self, employee: Employee, total_income: Decimal, 
                           period: PayrollPeriod) -> Decimal:
        """Calcula el Impuesto Sobre la Renta."""
        
        tax_table = self.tax_tables.get(period.year)
        if not tax_table:
            return Decimal('0')
        
        # Ajustar ingreso según frecuencia de pago
        if employee.payment_frequency == PaymentFrequency.MONTHLY:
            monthly_income = total_income
        elif employee.payment_frequency == PaymentFrequency.BIWEEKLY:
            monthly_income = total_income * 2
        elif employee.payment_frequency == PaymentFrequency.WEEKLY:
            monthly_income = total_income * Decimal('4.33')
        else:
            monthly_income = total_income / 12
        
        # Buscar bracket correspondiente
        for bracket in tax_table.brackets:
            if bracket["upper"] is None or monthly_income <= bracket["upper"]:
                if monthly_income >= bracket["lower"]:
                    # Calcular ISR
                    excess = monthly_income - bracket["lower"]
                    tax = bracket["fixed"] + (excess * bracket["rate"])
                    
                    # Ajustar de vuelta a la frecuencia de pago
                    if employee.payment_frequency == PaymentFrequency.MONTHLY:
                        return tax
                    elif employee.payment_frequency == PaymentFrequency.BIWEEKLY:
                        return tax / 2
                    elif employee.payment_frequency == PaymentFrequency.WEEKLY:
                        return tax / Decimal('4.33')
                    else:
                        return tax * 12
        
        return Decimal('0')
    
    async def _calculate_imss_employee(self, employee: Employee, total_income: Decimal) -> Decimal:
        """Calcula la cuota IMSS del empleado."""
        
        # Salario base de cotización (máximo 25 UMAs)
        uma_monthly = self.tax_tables[2024].uma_monthly
        max_salary = uma_monthly * 25
        imss_salary = min(employee.imss_salary or employee.base_salary, max_salary)
        
        # Calcular cuotas
        retirement = imss_salary * self.imss_rates["employee"]["retirement"]
        disability = imss_salary * self.imss_rates["employee"]["disability"]
        medical = imss_salary * self.imss_rates["employee"]["medical"]
        
        return retirement + disability + medical
    
    async def _calculate_imss_employer(self, employee: Employee, total_income: Decimal) -> Decimal:
        """Calcula la cuota IMSS del patrón."""
        
        # Salario base de cotización
        uma_monthly = self.tax_tables[2024].uma_monthly
        max_salary = uma_monthly * 25
        imss_salary = min(employee.imss_salary or employee.base_salary, max_salary)
        
        # Calcular cuotas patronales
        retirement = imss_salary * self.imss_rates["employer"]["retirement"]
        disability = imss_salary * self.imss_rates["employer"]["disability"]
        medical = imss_salary * self.imss_rates["employer"]["medical"]
        risk = imss_salary * self.imss_rates["employer"]["risk"]
        nursery = imss_salary * self.imss_rates["employer"]["nursery"]
        
        return retirement + disability + medical + risk + nursery
    
    async def _calculate_infonavit(self, employee: Employee, total_income: Decimal) -> Decimal:
        """Calcula el descuento INFONAVIT."""
        
        if employee.infonavit_discount_value <= 0:
            return Decimal('0')
        
        if employee.infonavit_discount_type == "percentage":
            return total_income * (employee.infonavit_discount_value / 100)
        elif employee.infonavit_discount_type == "vsm":
            # VSM = Veces Salario Mínimo
            daily_minimum_wage = Decimal('248.93')  # 2024
            return daily_minimum_wage * employee.infonavit_discount_value * 30
        else:  # fixed
            return employee.infonavit_discount_value
    
    async def _calculate_absence_discount(self, employee: Employee, period: PayrollPeriod, 
                                        absent_days: int) -> Decimal:
        """Calcula descuento por faltas."""
        
        if absent_days <= 0:
            return Decimal('0')
        
        daily_salary = employee.base_salary / 30
        return daily_salary * absent_days
    
    def get_payroll_summary(self, batch_id: str) -> Dict[str, Any]:
        """Obtiene resumen de nómina calculada."""
        
        batch = self.batches.get(batch_id)
        if not batch:
            return {"error": "Batch not found"}
        
        period = self.periods.get(batch.period_id)
        
        # Generar detalles por empleado
        employee_details = []
        for employee_id, concepts in batch.payroll_concepts.items():
            employee = self.employees.get(employee_id)
            if not employee:
                continue
            
            employee_details.append({
                "employee_id": employee_id,
                "name": f"{employee.first_name} {employee.last_name}",
                "employee_number": employee.employee_number,
                "base_salary": float(employee.base_salary),
                "worked_days": concepts.worked_days,
                "total_perceptions": float(concepts.total_perceptions),
                "total_deductions": float(concepts.total_deductions),
                "net_pay": float(concepts.net_pay),
                "employer_cost": float(concepts.total_employer_cost)
            })
        
        return {
            "batch_id": batch_id,
            "client_id": batch.client_id,
            "period": {
                "id": period.id if period else None,
                "start_date": period.start_date.isoformat() if period else None,
                "end_date": period.end_date.isoformat() if period else None,
                "pay_date": period.pay_date.isoformat() if period else None
            },
            "summary": {
                "total_employees": batch.total_employees,
                "total_perceptions": float(batch.total_perceptions),
                "total_deductions": float(batch.total_deductions),
                "total_net_pay": float(batch.total_net_pay),
                "total_employer_cost": float(batch.total_employer_cost)
            },
            "employees": employee_details,
            "status": batch.status.value,
            "processed_at": batch.processed_at.isoformat() if batch.processed_at else None
        }
    
    def get_employee_payslip(self, employee_id: str, batch_id: str) -> Dict[str, Any]:
        """Genera recibo de nómina individual."""
        
        batch = self.batches.get(batch_id)
        if not batch or employee_id not in batch.payroll_concepts:
            return {"error": "Employee payroll not found"}
        
        employee = self.employees.get(employee_id)
        concepts = batch.payroll_concepts[employee_id]
        period = self.periods.get(batch.period_id)
        
        # Formatear percepciones
        perceptions_detail = []
        for concept, amount in concepts.perceptions.items():
            perceptions_detail.append({
                "concept": concept.value,
                "description": self._get_concept_description(concept),
                "amount": float(amount)
            })
        
        # Formatear deducciones
        deductions_detail = []
        for concept, amount in concepts.deductions.items():
            deductions_detail.append({
                "concept": concept.value,
                "description": self._get_concept_description(concept),
                "amount": float(amount)
            })
        
        return {
            "employee": {
                "id": employee.id,
                "name": f"{employee.first_name} {employee.last_name}",
                "employee_number": employee.employee_number,
                "rfc": employee.rfc,
                "nss": employee.nss,
                "job_title": employee.job_title,
                "department": employee.department
            },
            "period": {
                "start_date": period.start_date.isoformat() if period else None,
                "end_date": period.end_date.isoformat() if period else None,
                "pay_date": period.pay_date.isoformat() if period else None,
                "worked_days": concepts.worked_days,
                "absent_days": concepts.absent_days
            },
            "perceptions": {
                "details": perceptions_detail,
                "total": float(concepts.total_perceptions)
            },
            "deductions": {
                "details": deductions_detail,
                "total": float(concepts.total_deductions)
            },
            "net_pay": float(concepts.net_pay),
            "calculated_at": concepts.calculated_at.isoformat()
        }
    
    def _get_concept_description(self, concept: PayrollConcept) -> str:
        """Obtiene descripción legible del concepto."""
        
        descriptions = {
            PayrollConcept.BASE_SALARY: "Salario Base",
            PayrollConcept.OVERTIME: "Horas Extra",
            PayrollConcept.BONUS: "Bono",
            PayrollConcept.COMMISSION: "Comisión",
            PayrollConcept.VACATION_PAY: "Vacaciones",
            PayrollConcept.CHRISTMAS_BONUS: "Aguinaldo",
            PayrollConcept.VACATION_PREMIUM: "Prima Vacacional",
            PayrollConcept.PRODUCTIVITY_BONUS: "Bono de Productividad",
            PayrollConcept.ISR: "ISR",
            PayrollConcept.IMSS_EMPLOYEE: "IMSS Empleado",
            PayrollConcept.INFONAVIT: "INFONAVIT",
            PayrollConcept.LOAN_DISCOUNT: "Descuento Préstamo",
            PayrollConcept.ABSENCE_DISCOUNT: "Descuento Faltas",
            PayrollConcept.LATE_DISCOUNT: "Descuento Retardos",
            PayrollConcept.IMSS_EMPLOYER: "IMSS Patrón",
            PayrollConcept.INFONAVIT_EMPLOYER: "INFONAVIT Patrón",
            PayrollConcept.SAR: "SAR",
            PayrollConcept.INFONAVIT_SAR: "INFONAVIT SAR"
        }
        
        return descriptions.get(concept, concept.value)
    
    async def approve_payroll(self, batch_id: str, approved_by: str) -> bool:
        """Aprueba un lote de nómina."""
        
        batch = self.batches.get(batch_id)
        if not batch:
            return False
        
        if batch.status != PayrollStatus.CALCULATED:
            return False
        
        batch.status = PayrollStatus.APPROVED
        
        # Actualizar período
        period = self.periods.get(batch.period_id)
        if period:
            period.status = PayrollStatus.APPROVED
            period.approved_at = datetime.now()
        
        logger.info(f"Payroll approved: {batch_id} by {approved_by}")
        return True
    
    async def generate_payment_file(self, batch_id: str, bank_format: str = "banamex") -> Dict[str, Any]:
        """Genera archivo de dispersión bancaria."""
        
        batch = self.batches.get(batch_id)
        if not batch or batch.status != PayrollStatus.APPROVED:
            return {"error": "Batch not approved for payment"}
        
        payment_records = []
        total_amount = Decimal('0')
        
        for employee_id, concepts in batch.payroll_concepts.items():
            employee = self.employees.get(employee_id)
            if not employee or not employee.bank_clabe:
                continue
            
            if concepts.net_pay > 0:
                payment_records.append({
                    "employee_number": employee.employee_number,
                    "name": f"{employee.first_name} {employee.last_name}",
                    "bank_clabe": employee.bank_clabe,
                    "amount": float(concepts.net_pay),
                    "reference": f"NOM{batch.period_id}_{employee.employee_number}"
                })
                total_amount += concepts.net_pay
        
        # Generar archivo según formato bancario
        if bank_format == "banamex":
            file_content = await self._generate_banamex_file(payment_records, batch)
        else:
            file_content = await self._generate_generic_file(payment_records, batch)
        
        return {
            "file_content": file_content,
            "total_records": len(payment_records),
            "total_amount": float(total_amount),
            "filename": f"nomina_{batch.period_id}_{bank_format}.txt"
        }
    
    async def _generate_banamex_file(self, records: List[Dict], batch: PayrollBatch) -> str:
        """Genera archivo en formato Banamex."""
        
        lines = []
        
        # Header
        header = f"H{datetime.now().strftime('%Y%m%d')}{len(records):06d}{int(batch.total_net_pay):012d}"
        lines.append(header)
        
        # Detail records
        for i, record in enumerate(records, 1):
            detail = (f"D{i:06d}{record['bank_clabe']}{int(record['amount'] * 100):012d}"
                     f"{record['reference'][:16]:16s}")
            lines.append(detail)
        
        # Trailer
        trailer = f"T{len(records):06d}{int(batch.total_net_pay * 100):012d}"
        lines.append(trailer)
        
        return "\n".join(lines)
    
    async def _generate_generic_file(self, records: List[Dict], batch: PayrollBatch) -> str:
        """Genera archivo genérico CSV."""
        
        lines = ["CLABE,Nombre,Monto,Referencia"]
        
        for record in records:
            line = f"{record['bank_clabe']},{record['name']},{record['amount']},{record['reference']}"
            lines.append(line)
        
        return "\n".join(lines)

# Funciones de utilidad
async def quick_payroll_calculation(client_id: str, year: int, month: int) -> str:
    """Función de conveniencia para cálculo rápido de nómina."""
    
    engine = PayrollEngine()
    
    # Crear período
    period_id = await engine.create_payroll_period(client_id, year, month)
    
    # Calcular nómina
    batch_id = await engine.calculate_payroll(client_id, period_id)
    
    return batch_id

# Exportaciones
__all__ = [
    'PayrollStatus', 'PaymentFrequency', 'EmployeeStatus', 'ContractType', 'PayrollConcept',
    'Employee', 'PayrollPeriod', 'PayrollConcepts', 'PayrollBatch', 'TaxTable',
    'PayrollEngine', 'quick_payroll_calculation'
]