"""
Motor de Cálculo de Nómina huntRED®
Cálculos precisos con compliance México 2024
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, date, timedelta
from dataclasses import dataclass

from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.cache import cache

from ..models import PayrollEmployee, PayrollPeriod, PayrollCalculation, AttendanceRecord, UMARegistry, TaxTable
from .. import SUPPORTED_COUNTRIES

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTES MÉXICO 2024
# ============================================================================

# UMA 2024
UMA_DAILY_2024 = Decimal("108.57")
UMA_MONTHLY_2024 = Decimal("3257.10")
UMA_ANNUAL_2024 = UMA_DAILY_2024 * 365

# Tabla ISR Mensual 2024
ISR_TABLE_MONTHLY_2024 = [
    {"lower": Decimal("0.01"), "upper": Decimal("746.04"), "rate": Decimal("0.0192"), "fixed": Decimal("0.00")},
    {"lower": Decimal("746.05"), "upper": Decimal("6332.05"), "rate": Decimal("0.064"), "fixed": Decimal("14.32")},
    {"lower": Decimal("6332.06"), "upper": Decimal("11128.01"), "rate": Decimal("0.1088"), "fixed": Decimal("371.83")},
    {"lower": Decimal("11128.02"), "upper": Decimal("12935.82"), "rate": Decimal("0.16"), "fixed": Decimal("893.63")},
    {"lower": Decimal("12935.83"), "upper": Decimal("15487.71"), "rate": Decimal("0.2112"), "fixed": Decimal("1182.88")},
    {"lower": Decimal("15487.72"), "upper": Decimal("31236.49"), "rate": Decimal("0.23"), "fixed": Decimal("1721.36")},
    {"lower": Decimal("31236.50"), "upper": Decimal("49233.00"), "rate": Decimal("0.30"), "fixed": Decimal("5334.47")},
    {"lower": Decimal("49233.01"), "upper": Decimal("93993.90"), "rate": Decimal("0.32"), "fixed": Decimal("10733.67")},
    {"lower": Decimal("93993.91"), "upper": Decimal("125325.20"), "rate": Decimal("0.34"), "fixed": Decimal("25037.26")},
    {"lower": Decimal("125325.21"), "upper": None, "rate": Decimal("0.35"), "fixed": Decimal("35659.74")},
]

# Subsidio para el Empleo 2024
SUBSIDIO_EMPLEO_2024 = [
    {"lower": Decimal("0.01"), "upper": Decimal("1768.96"), "subsidio": Decimal("407.02")},
    {"lower": Decimal("1768.97"), "upper": Decimal("2653.38"), "subsidio": Decimal("406.83")},
    {"lower": Decimal("2653.39"), "upper": Decimal("3472.84"), "subsidio": Decimal("406.62")},
    {"lower": Decimal("3472.85"), "upper": Decimal("3537.87"), "subsidio": Decimal("392.77")},
    {"lower": Decimal("3537.88"), "upper": Decimal("4446.15"), "subsidio": Decimal("382.46")},
    {"lower": Decimal("4446.16"), "upper": Decimal("4717.18"), "subsidio": Decimal("354.23")},
    {"lower": Decimal("4717.19"), "upper": Decimal("5335.42"), "subsidio": Decimal("324.87")},
    {"lower": Decimal("5335.43"), "upper": Decimal("6224.67"), "subsidio": Decimal("294.63")},
    {"lower": Decimal("6224.68"), "upper": Decimal("7113.90"), "subsidio": Decimal("253.54")},
    {"lower": Decimal("7113.91"), "upper": Decimal("7382.33"), "subsidio": Decimal("217.61")},
    {"lower": Decimal("7382.34"), "upper": None, "subsidio": Decimal("0.00")},
]

# Límites IMSS 2024
IMSS_LOWER_LIMIT = UMA_DAILY_2024  # 1 UMA diario
IMSS_UPPER_LIMIT = UMA_DAILY_2024 * 25  # 25 UMA diario

# Tasas IMSS 2024
IMSS_RATES_2024 = {
    "enfermedad_maternidad_obrero": Decimal("0.0025"),  # 0.25%
    "invalidez_vida_obrero": Decimal("0.00625"),  # 0.625%
    "cesantia_vejez_obrero": Decimal("0.01125"),  # 1.125%
    "enfermedad_maternidad_patron": Decimal("0.007"),  # 0.70%
    "invalidez_vida_patron": Decimal("0.0175"),  # 1.75%
    "cesantia_vejez_patron": Decimal("0.0315"),  # 3.15%
    "infonavit_patron": Decimal("0.05"),  # 5.00%
    "retiro_patron": Decimal("0.02"),  # 2.00%
    "riesgo_trabajo": Decimal("0.005"),  # 0.50% (promedio)
}


@dataclass
class PayrollCalculationResult:
    """Resultado del cálculo de nómina"""
    employee_id: str
    period_id: str
    
    # Percepciones
    base_salary: Decimal
    overtime_hours: Decimal
    overtime_amount: Decimal
    bonuses: Decimal
    commissions: Decimal
    other_income: Decimal
    gross_income: Decimal
    
    # Deducciones
    isr_withheld: Decimal
    imss_employee: Decimal
    infonavit_employee: Decimal
    loan_deductions: Decimal
    advance_deductions: Decimal
    other_deductions: Decimal
    total_deductions: Decimal
    
    # Neto
    net_pay: Decimal
    
    # Aportaciones patronales
    imss_employer: Decimal
    infonavit_employer: Decimal
    total_employer_cost: Decimal
    
    # Metadatos
    calculation_date: datetime
    calculation_version: str = "1.0"


class ISRCalculator:
    """Calculadora de ISR México 2024"""
    
    @staticmethod
    def calculate_isr_monthly(gross_income: Decimal) -> Tuple[Decimal, Decimal]:
        """
        Calcula ISR mensual y subsidio para el empleo
        
        Args:
            gross_income: Ingreso bruto mensual
            
        Returns:
            Tuple[isr_calculated, subsidio_empleo]
        """
        # Calcular ISR
        isr_calculated = ISRCalculator._calculate_isr_from_table(gross_income)
        
        # Calcular subsidio para el empleo
        subsidio_empleo = ISRCalculator._calculate_subsidio_empleo(gross_income)
        
        # ISR final = ISR calculado - subsidio
        isr_final = max(Decimal("0"), isr_calculated - subsidio_empleo)
        
        return isr_final, subsidio_empleo
    
    @staticmethod
    def _calculate_isr_from_table(monthly_income: Decimal) -> Decimal:
        """Calcula ISR usando tabla progresiva"""
        for bracket in ISR_TABLE_MONTHLY_2024:
            if monthly_income <= bracket["upper"]:
                excess = monthly_income - bracket["lower"]
                variable_amount = excess * bracket["rate"]
                return bracket["fixed"] + variable_amount
        
        return Decimal("0")
    
    @staticmethod
    def _calculate_subsidio_empleo(monthly_income: Decimal) -> Decimal:
        """Calcula subsidio para el empleo"""
        for bracket in SUBSIDIO_EMPLEO_2024:
            if monthly_income <= bracket["upper"]:
                return bracket["subsidio"]
        
        return Decimal("0")


class IMSSCalculator:
    """Calculadora de IMSS México 2024"""
    
    @staticmethod
    def calculate_imss_base_salary(gross_salary: Decimal, frequency: str) -> Decimal:
        """Calcula salario base para IMSS con límites"""
        # Convertir a salario diario
        daily_salary = IMSSCalculator._convert_to_daily(gross_salary, frequency)
        
        # Aplicar límites IMSS
        if daily_salary < IMSS_LOWER_LIMIT:
            daily_salary = IMSS_LOWER_LIMIT
        elif daily_salary > IMSS_UPPER_LIMIT:
            daily_salary = IMSS_UPPER_LIMIT
        
        # Convertir de vuelta a frecuencia original
        return IMSSCalculator._convert_from_daily(daily_salary, frequency)
    
    @staticmethod
    def calculate_employee_imss(imss_base: Decimal, frequency: str) -> Decimal:
        """Calcula aportaciones IMSS del empleado"""
        daily_base = IMSSCalculator._convert_to_daily(imss_base, frequency)
        
        # Enfermedad y maternidad
        enfermedad_maternidad = daily_base * IMSS_RATES_2024["enfermedad_maternidad_obrero"]
        
        # Invalidez y vida
        invalidez_vida = daily_base * IMSS_RATES_2024["invalidez_vida_obrero"]
        
        # Cesantía y vejez
        cesantia_vejez = daily_base * IMSS_RATES_2024["cesantia_vejez_obrero"]
        
        total_daily = enfermedad_maternidad + invalidez_vida + cesantia_vejez
        
        return IMSSCalculator._convert_from_daily(total_daily, frequency)
    
    @staticmethod
    def calculate_employer_imss(imss_base: Decimal, frequency: str) -> Decimal:
        """Calcula aportaciones IMSS del patrón"""
        daily_base = IMSSCalculator._convert_to_daily(imss_base, frequency)
        
        # Enfermedad y maternidad
        enfermedad_maternidad = daily_base * IMSS_RATES_2024["enfermedad_maternidad_patron"]
        
        # Invalidez y vida
        invalidez_vida = daily_base * IMSS_RATES_2024["invalidez_vida_patron"]
        
        # Cesantía y vejez
        cesantia_vejez = daily_base * IMSS_RATES_2024["cesantia_vejez_patron"]
        
        # Riesgo de trabajo (promedio)
        riesgo_trabajo = daily_base * IMSS_RATES_2024["riesgo_trabajo"]
        
        total_daily = enfermedad_maternidad + invalidez_vida + cesantia_vejez + riesgo_trabajo
        
        return IMSSCalculator._convert_from_daily(total_daily, frequency)
    
    @staticmethod
    def calculate_infonavit_employer(imss_base: Decimal, frequency: str) -> Decimal:
        """Calcula aportación INFONAVIT del patrón (5%)"""
        daily_base = IMSSCalculator._convert_to_daily(imss_base, frequency)
        infonavit_daily = daily_base * IMSS_RATES_2024["infonavit_patron"]
        return IMSSCalculator._convert_from_daily(infonavit_daily, frequency)
    
    @staticmethod
    def _convert_to_daily(amount: Decimal, frequency: str) -> Decimal:
        """Convierte monto a salario diario"""
        if frequency == "monthly":
            return amount / Decimal("30")
        elif frequency == "biweekly":
            return amount / Decimal("14")
        elif frequency == "weekly":
            return amount / Decimal("7")
        else:
            return amount
    
    @staticmethod
    def _convert_from_daily(daily_amount: Decimal, frequency: str) -> Decimal:
        """Convierte salario diario a frecuencia original"""
        if frequency == "monthly":
            return daily_amount * Decimal("30")
        elif frequency == "biweekly":
            return daily_amount * Decimal("14")
        elif frequency == "weekly":
            return daily_amount * Decimal("7")
        else:
            return daily_amount


class OvertimeCalculator:
    """Calculadora de horas extra México"""
    
    @staticmethod
    def calculate_overtime_amount(
        base_hourly_rate: Decimal,
        overtime_hours: Decimal,
        overtime_type: str = "regular"
    ) -> Decimal:
        """
        Calcula monto de horas extra según LFT México
        
        Args:
            base_hourly_rate: Tarifa por hora base
            overtime_hours: Horas extra trabajadas
            overtime_type: Tipo de hora extra (regular, weekend, holiday)
            
        Returns:
            Monto total de horas extra
        """
        if overtime_type == "regular":
            # Primeras 9 horas: doble pago (200%)
            # Horas adicionales: triple pago (300%)
            if overtime_hours <= 9:
                return overtime_hours * base_hourly_rate * Decimal("2")
            else:
                double_time_amount = Decimal("9") * base_hourly_rate * Decimal("2")
                triple_time_hours = overtime_hours - Decimal("9")
                triple_time_amount = triple_time_hours * base_hourly_rate * Decimal("3")
                return double_time_amount + triple_time_amount
        
        elif overtime_type == "weekend":
            # Día de descanso: doble pago
            return overtime_hours * base_hourly_rate * Decimal("2")
        
        elif overtime_type == "holiday":
            # Día festivo: triple pago
            return overtime_hours * base_hourly_rate * Decimal("3")
        
        else:
            # Hora extra regular
            return overtime_hours * base_hourly_rate * Decimal("2")


class PayrollEngine:
    """Motor principal de cálculo de nómina"""
    
    def __init__(self, company_id: str):
        """
        Inicializa el motor de nómina
        
        Args:
            company_id: ID de la empresa
        """
        from ..models import PayrollCompany
        self.company = PayrollCompany.objects.get(id=company_id)
        self.country_config = SUPPORTED_COUNTRIES.get(self.company.country_code, {})
    
    def calculate_employee_payroll(
        self,
        employee: PayrollEmployee,
        period: PayrollPeriod,
        overtime_hours: Decimal = Decimal("0"),
        bonuses: Decimal = Decimal("0"),
        commissions: Decimal = Decimal("0"),
        other_income: Decimal = Decimal("0"),
        loan_deductions: Decimal = Decimal("0"),
        advance_deductions: Decimal = Decimal("0"),
        other_deductions: Decimal = Decimal("0")
    ) -> PayrollCalculationResult:
        """
        Calcula nómina completa de un empleado
        
        Args:
            employee: Empleado
            period: Período de nómina
            overtime_hours: Horas extra
            bonuses: Bonos
            commissions: Comisiones
            other_income: Otros ingresos
            loan_deductions: Deducciones por préstamos
            advance_deductions: Deducciones por adelantos
            other_deductions: Otras deducciones
            
        Returns:
            Resultado del cálculo
        """
        try:
            # 1. Calcular salario base del período
            base_salary = self._calculate_period_salary(employee, period)
            
            # 2. Calcular horas extra
            overtime_amount = self._calculate_overtime(employee, period, overtime_hours)
            
            # 3. Calcular ingreso bruto
            gross_income = base_salary + overtime_amount + bonuses + commissions + other_income
            
            # 4. Calcular ISR
            isr_withheld, subsidio_empleo = ISRCalculator.calculate_isr_monthly(gross_income)
            
            # 5. Calcular IMSS empleado
            imss_base = IMSSCalculator.calculate_imss_base_salary(gross_income, period.frequency)
            imss_employee = IMSSCalculator.calculate_employee_imss(imss_base, period.frequency)
            
            # 6. Calcular INFONAVIT empleado (no aplica para empleado)
            infonavit_employee = Decimal("0")
            
            # 7. Calcular total deducciones
            total_deductions = (
                isr_withheld + 
                imss_employee + 
                infonavit_employee + 
                loan_deductions + 
                advance_deductions + 
                other_deductions
            )
            
            # 8. Calcular neto a pagar
            net_pay = gross_income - total_deductions
            
            # 9. Calcular aportaciones patronales
            imss_employer = IMSSCalculator.calculate_employer_imss(imss_base, period.frequency)
            infonavit_employer = IMSSCalculator.calculate_infonavit_employer(imss_base, period.frequency)
            total_employer_cost = gross_income + imss_employer + infonavit_employer
            
            return PayrollCalculationResult(
                employee_id=str(employee.id),
                period_id=str(period.id),
                base_salary=base_salary,
                overtime_hours=overtime_hours,
                overtime_amount=overtime_amount,
                bonuses=bonuses,
                commissions=commissions,
                other_income=other_income,
                gross_income=gross_income,
                isr_withheld=isr_withheld,
                imss_employee=imss_employee,
                infonavit_employee=infonavit_employee,
                loan_deductions=loan_deductions,
                advance_deductions=advance_deductions,
                other_deductions=other_deductions,
                total_deductions=total_deductions,
                net_pay=net_pay,
                imss_employer=imss_employer,
                infonavit_employer=infonavit_employer,
                total_employer_cost=total_employer_cost,
                calculation_date=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculando nómina para empleado {employee.id}: {str(e)}")
            raise ValidationError(f"Error en cálculo de nómina: {str(e)}")
    
    def _calculate_period_salary(self, employee: PayrollEmployee, period: PayrollPeriod) -> Decimal:
        """Calcula salario base del período"""
        if period.frequency == "monthly":
            return employee.monthly_salary
        elif period.frequency == "biweekly":
            return employee.monthly_salary / Decimal("2")
        elif period.frequency == "weekly":
            return employee.monthly_salary / Decimal("4.33")  # Promedio semanas por mes
        else:
            # Calcular proporcional
            working_days = period.get_working_days()
            return (employee.monthly_salary / Decimal("30")) * Decimal(str(working_days))
    
    def _calculate_overtime(self, employee: PayrollEmployee, period: PayrollPeriod, overtime_hours: Decimal) -> Decimal:
        """Calcula monto de horas extra"""
        if overtime_hours <= 0:
            return Decimal("0")
        
        hourly_rate = employee.calculate_hourly_rate()
        return OvertimeCalculator.calculate_overtime_amount(hourly_rate, overtime_hours)
    
    def calculate_period_payroll(self, period: PayrollPeriod) -> Dict[str, Any]:
        """
        Calcula nómina completa del período
        
        Args:
            period: Período de nómina
            
        Returns:
            Resumen del cálculo
        """
        employees = self.company.employees.filter(is_active=True)
        calculations = []
        
        total_gross = Decimal("0")
        total_net = Decimal("0")
        total_taxes = Decimal("0")
        total_employer_cost = Decimal("0")
        
        for employee in employees:
            # Obtener horas extra del período
            overtime_hours = self._get_period_overtime(employee, period)
            
            # Calcular nómina individual
            result = self.calculate_employee_payroll(
                employee=employee,
                period=period,
                overtime_hours=overtime_hours
            )
            
            # Guardar cálculo
            calculation = PayrollCalculation.objects.create(
                period=period,
                employee=employee,
                base_salary=result.base_salary,
                overtime_hours=result.overtime_hours,
                overtime_amount=result.overtime_amount,
                bonuses=result.bonuses,
                commissions=result.commissions,
                other_income=result.other_income,
                gross_income=result.gross_income,
                isr_withheld=result.isr_withheld,
                imss_employee=result.imss_employee,
                infonavit_employee=result.infonavit_employee,
                loan_deductions=result.loan_deductions,
                advance_deductions=result.advance_deductions,
                other_deductions=result.other_deductions,
                total_deductions=result.total_deductions,
                net_pay=result.net_pay,
                imss_employer=result.imss_employer,
                infonavit_employer=result.infonavit_employer,
                total_employer_cost=result.total_employer_cost
            )
            
            calculations.append(calculation)
            
            # Acumular totales
            total_gross += result.gross_income
            total_net += result.net_pay
            total_taxes += result.total_deductions
            total_employer_cost += result.total_employer_cost
        
        # Actualizar período
        period.total_employees = len(calculations)
        period.total_gross = total_gross
        period.total_net = total_net
        period.total_taxes = total_taxes
        period.calculation_date = timezone.now()
        period.status = "calculated"
        period.save()
        
        return {
            "period_id": str(period.id),
            "total_employees": len(calculations),
            "total_gross": float(total_gross),
            "total_net": float(total_net),
            "total_taxes": float(total_taxes),
            "total_employer_cost": float(total_employer_cost),
            "calculations_count": len(calculations)
        }
    
    def _get_period_overtime(self, employee: PayrollEmployee, period: PayrollPeriod) -> Decimal:
        """Obtiene horas extra del período desde registros de asistencia"""
        attendance_records = AttendanceRecord.objects.filter(
            employee=employee,
            date__range=[period.start_date, period.end_date]
        )
        
        total_overtime = Decimal("0")
        for record in attendance_records:
            total_overtime += record.overtime_hours or Decimal("0")
        
        return total_overtime

    def get_uma_value(self, year: int = None) -> Decimal:
        """Obtiene valor UMA para el año especificado"""
        if year is None:
            year = date.today().year
        
        # Buscar en cache primero
        cache_key = f"uma_value_{self.company.country_code}_{year}"
        uma_value = cache.get(cache_key)
        
        if uma_value is None:
            # Buscar en base de datos
            uma_registry = UMARegistry.objects.filter(
                country_code=self.company.country_code,
                year=year,
                is_active=True
            ).first()
            
            if uma_registry:
                uma_value = uma_registry.uma_value
                # Guardar en cache por 24 horas
                cache.set(cache_key, uma_value, 86400)
            else:
                # Usar valor por defecto si no se encuentra
                uma_value = self._get_default_uma_value(year)
        
        return uma_value
    
    def get_tax_table(self, table_type: str, effective_date: date = None) -> List[Dict[str, Any]]:
        """Obtiene tabla fiscal específica"""
        if effective_date is None:
            effective_date = date.today()
        
        # Buscar en cache primero
        cache_key = f"tax_table_{table_type}_{effective_date.isoformat()}"
        tax_table = cache.get(cache_key)
        
        if tax_table is None:
            # Buscar en base de datos
            tax_entries = TaxTable.objects.filter(
                table_type=table_type,
                effective_date__lte=effective_date,
                is_active=True
            ).order_by('limit_inferior')
            
            tax_table = []
            for entry in tax_entries:
                tax_table.append({
                    'limit_inferior': entry.limit_inferior,
                    'limit_superior': entry.limit_superior,
                    'fixed_quota': entry.fixed_quota,
                    'percentage': entry.percentage,
                    'value': entry.value,
                    'concept': entry.concept
                })
            
            # Guardar en cache por 1 hora
            cache.set(cache_key, tax_table, 3600)
        
        return tax_table
    
    def calculate_isr(self, taxable_income: Decimal) -> Decimal:
        """Calcula ISR usando tablas dinámicas"""
        # Obtener tabla ISR mensual
        isr_table = self.get_tax_table('sat_isr_mensual')
        
        if not isr_table:
            # Fallback a cálculo manual si no hay tabla
            return self._calculate_isr_manual(taxable_income)
        
        # Buscar el rango correspondiente
        for row in isr_table:
            limit_inf = row['limit_inferior'] or 0
            limit_sup = row['limit_superior'] or float('inf')
            
            if limit_inf <= taxable_income <= limit_sup:
                # Calcular ISR
                excess = taxable_income - limit_inf
                isr = (row['fixed_quota'] or 0) + (excess * (row['percentage'] or 0) / 100)
                return isr
        
        # Si no se encuentra rango, usar el último
        if isr_table:
            last_row = isr_table[-1]
            excess = taxable_income - (last_row['limit_inferior'] or 0)
            isr = (last_row['fixed_quota'] or 0) + (excess * (last_row['percentage'] or 0) / 100)
            return isr
        
        return Decimal('0')
    
    def calculate_imss(self, base_salary: Decimal) -> Decimal:
        """Calcula cuotas IMSS usando tablas dinámicas"""
        # Obtener tabla de cuotas IMSS
        cuotas_table = self.get_tax_table('imss_cuotas')
        
        if not cuotas_table:
            # Fallback a valores por defecto
            return self._calculate_imss_manual(base_salary)
        
        total_imss = Decimal('0')
        
        for cuota in cuotas_table:
            if cuota['percentage']:
                total_imss += base_salary * (cuota['percentage'] / 100)
        
        return total_imss
    
    def calculate_infonavit(self, base_salary: Decimal) -> Decimal:
        """Calcula descuento INFONAVIT usando tablas dinámicas"""
        # Obtener tabla de descuentos INFONAVIT
        descuentos_table = self.get_tax_table('infonavit_descuentos')
        
        if not descuentos_table:
            # Fallback a valor por defecto (5%)
            return base_salary * Decimal('0.05')
        
        # Usar el primer descuento activo
        if descuentos_table:
            descuento = descuentos_table[0]
            if descuento['percentage']:
                return base_salary * (descuento['percentage'] / 100)
        
        return Decimal('0')
    
    def _get_default_uma_value(self, year: int) -> Decimal:
        """Obtiene valor UMA por defecto si no está en base de datos"""
        # Valores UMA por defecto (actualizar según sea necesario)
        default_values = {
            2024: Decimal('103.74'),
            2025: Decimal('108.57'),
            2026: Decimal('113.40'),
        }
        
        return default_values.get(year, Decimal('100.00'))
    
    def _calculate_isr_manual(self, taxable_income: Decimal) -> Decimal:
        """Cálculo manual de ISR como fallback"""
        # Tabla ISR 2024 (valores hardcodeados como fallback)
        isr_table = [
            {'limite_inferior': 0, 'limite_superior': 578.52, 'cuota_fija': 0, 'porcentaje': 1.92},
            {'limite_inferior': 578.53, 'limite_superior': 4910.18, 'cuota_fija': 11.11, 'porcentaje': 6.40},
            {'limite_inferior': 4910.19, 'limite_superior': 8629.20, 'cuota_fija': 288.33, 'porcentaje': 10.88},
            {'limite_inferior': 8629.21, 'limite_superior': 10031.33, 'cuota_fija': 692.96, 'porcentaje': 16.00},
            {'limite_inferior': 10031.34, 'limite_superior': 12009.94, 'cuota_fija': 917.26, 'porcentaje': 17.92},
            {'limite_inferior': 12009.95, 'limite_superior': 24222.31, 'cuota_fija': 1271.87, 'porcentaje': 21.36},
            {'limite_inferior': 24222.32, 'limite_superior': 38177.69, 'cuota_fija': 3880.44, 'porcentaje': 23.52},
            {'limite_inferior': 38177.70, 'limite_superior': 72887.50, 'cuota_fija': 7162.74, 'porcentaje': 30.00},
            {'limite_inferior': 72887.51, 'limite_superior': 97183.33, 'cuota_fija': 17575.69, 'porcentaje': 32.00},
            {'limite_inferior': 97183.34, 'limite_superior': 291550.00, 'cuota_fija': 25350.35, 'porcentaje': 34.00},
            {'limite_inferior': 291550.01, 'limite_superior': float('inf'), 'cuota_fija': 91435.02, 'porcentaje': 35.00}
        ]
        
        for row in isr_table:
            if row['limite_inferior'] <= taxable_income <= row['limite_superior']:
                excess = taxable_income - row['limite_inferior']
                isr = row['cuota_fija'] + (excess * row['porcentaje'] / 100)
                return isr
        
        return Decimal('0')
    
    def _calculate_imss_manual(self, base_salary: Decimal) -> Decimal:
        """Cálculo manual de IMSS como fallback"""
        # Cuotas IMSS por defecto (valores hardcodeados como fallback)
        cuotas = {
            'enfermedad_maternidad': Decimal('0.204'),
            'invalidez_vida': Decimal('0.625'),
            'retiro': Decimal('2.000'),
            'cesantia_vejez': Decimal('1.125'),
            'guarderia_prestaciones': Decimal('1.000')
        }
        
        total_imss = Decimal('0')
        for cuota in cuotas.values():
            total_imss += base_salary * (cuota / 100)
        
        return total_imss 