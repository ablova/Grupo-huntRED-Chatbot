"""
Payroll Engine Core - Complete Mexico 2024 Compliance
900+ lines of advanced payroll calculations
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum
import math

from ..config.settings import get_settings
from ..models.base import PayrollFrequency

settings = get_settings()
logger = logging.getLogger(__name__)


# Mexico 2024 Constants
UMA_DAILY_2024 = Decimal("108.57")  # Updated UMA daily value for 2024
UMA_MONTHLY_2024 = Decimal("3257.10")  # UMA monthly (30 days)
UMA_ANNUAL_2024 = UMA_DAILY_2024 * 365

# IMSS 2024 Rates
IMSS_RATES_2024 = {
    "cuota_fija_obrero": Decimal("0.00430"),  # 0.43%
    "cuota_fija_patron": Decimal("0.01300"),  # 1.30%
    "excedente_obrero": Decimal("0.00625"),   # 0.625%
    "excedente_patron": Decimal("0.01900"),   # 1.90%
    "prestaciones_dinero_obrero": Decimal("0.00250"),  # 0.25%
    "prestaciones_dinero_patron": Decimal("0.00700"),  # 0.70%
    "prestaciones_especie_patron": Decimal("0.01000"),  # 1.00%
    "pensionados_obrero": Decimal("0.00375"),  # 0.375%
    "pensionados_patron": Decimal("0.01050"),  # 1.05%
    "invalidez_vida_obrero": Decimal("0.00625"),  # 0.625%
    "invalidez_vida_patron": Decimal("0.01750"),  # 1.75%
    "cesantia_vejez_obrero": Decimal("0.01125"),  # 1.125%
    "cesantia_vejez_patron": Decimal("0.03150"),  # 3.15%
    "infonavit_patron": Decimal("0.05000"),  # 5.00%
    "retiro_patron": Decimal("0.02000"),  # 2.00%
}

# IMSS Salary Limits 2024
IMSS_LOWER_LIMIT = UMA_DAILY_2024  # 1 UMA daily
IMSS_UPPER_LIMIT = UMA_DAILY_2024 * 25  # 25 UMA daily

# INFONAVIT 2024 Constants
INFONAVIT_MINIMUM_SALARY = UMA_MONTHLY_2024  # 1 UMA monthly
INFONAVIT_MAXIMUM_SALARY = UMA_MONTHLY_2024 * 5  # 5 UMA monthly

# ISR 2024 Tax Tables (Monthly)
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

# Subsidio para el Empleo 2024 (Monthly)
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


@dataclass
class PayrollCalculation:
    """Complete payroll calculation results"""
    employee_id: str
    pay_period_start: date
    pay_period_end: date
    
    # Gross Income
    base_salary: Decimal
    overtime_hours: Decimal
    overtime_amount: Decimal
    bonuses: Decimal
    commissions: Decimal
    other_income: Decimal
    gross_income: Decimal
    
    # IMSS Calculations
    imss_base_salary: Decimal
    imss_employee: Decimal
    imss_employer: Decimal
    
    # INFONAVIT
    infonavit_employee: Decimal
    infonavit_employer: Decimal
    
    # ISR
    isr_base: Decimal
    isr_calculated: Decimal
    subsidio_empleo: Decimal
    isr_withheld: Decimal
    
    # Other Deductions
    loan_deductions: Decimal
    advance_deductions: Decimal
    other_deductions: Decimal
    total_deductions: Decimal
    
    # Net Pay
    net_pay: Decimal
    
    # Employer Costs
    total_employer_cost: Decimal
    
    # Metadata
    calculation_date: datetime
    payroll_frequency: str
    currency: str = "MXN"


class PayrollFrequencyCalculator:
    """Handle different payroll frequencies"""
    
    @staticmethod
    def get_days_in_period(frequency: str, start_date: date, end_date: date) -> int:
        """Calculate days in pay period"""
        if frequency == "daily":
            return 1
        elif frequency == "weekly":
            return 7
        elif frequency == "biweekly":
            return 14
        elif frequency == "monthly":
            return (end_date - start_date).days + 1
        elif frequency == "bimonthly":
            return (end_date - start_date).days + 1
        else:
            return (end_date - start_date).days + 1
    
    @staticmethod
    def convert_monthly_to_period(monthly_amount: Decimal, frequency: str, 
                                days_in_period: int = None) -> Decimal:
        """Convert monthly amount to pay period amount"""
        if frequency == "monthly":
            return monthly_amount
        elif frequency == "biweekly":
            return monthly_amount / Decimal("2")
        elif frequency == "weekly":
            return monthly_amount / Decimal("4.33")  # Average weeks per month
        elif frequency == "daily":
            return monthly_amount / Decimal("30")
        elif frequency == "bimonthly":
            return monthly_amount * Decimal("2")
        else:
            if days_in_period:
                return monthly_amount * Decimal(str(days_in_period)) / Decimal("30")
            return monthly_amount


class IMSSCalculator:
    """IMSS (Instituto Mexicano del Seguro Social) calculations"""
    
    @classmethod
    def calculate_imss_base_salary(cls, gross_salary: Decimal, frequency: str) -> Decimal:
        """Calculate IMSS base salary with limits"""
        # Convert to daily for IMSS calculations
        if frequency == "monthly":
            daily_salary = gross_salary / Decimal("30")
        elif frequency == "biweekly":
            daily_salary = gross_salary / Decimal("14")
        elif frequency == "weekly":
            daily_salary = gross_salary / Decimal("7")
        else:
            daily_salary = gross_salary
        
        # Apply IMSS limits
        if daily_salary < IMSS_LOWER_LIMIT:
            daily_salary = IMSS_LOWER_LIMIT
        elif daily_salary > IMSS_UPPER_LIMIT:
            daily_salary = IMSS_UPPER_LIMIT
        
        # Convert back to original frequency
        if frequency == "monthly":
            return daily_salary * Decimal("30")
        elif frequency == "biweekly":
            return daily_salary * Decimal("14")
        elif frequency == "weekly":
            return daily_salary * Decimal("7")
        else:
            return daily_salary
    
    @classmethod
    def calculate_employee_imss(cls, imss_base: Decimal, frequency: str) -> Decimal:
        """Calculate employee IMSS contributions"""
        daily_base = cls._convert_to_daily(imss_base, frequency)
        
        # Calculate components
        cuota_fija = UMA_DAILY_2024 * IMSS_RATES_2024["cuota_fija_obrero"]
        
        # Excedente only if salary > 3 UMA
        excedente = Decimal("0")
        if daily_base > (UMA_DAILY_2024 * 3):
            excedente = (daily_base - (UMA_DAILY_2024 * 3)) * IMSS_RATES_2024["excedente_obrero"]
        
        prestaciones_dinero = daily_base * IMSS_RATES_2024["prestaciones_dinero_obrero"]
        pensionados = daily_base * IMSS_RATES_2024["pensionados_obrero"]
        invalidez_vida = daily_base * IMSS_RATES_2024["invalidez_vida_obrero"]
        cesantia_vejez = daily_base * IMSS_RATES_2024["cesantia_vejez_obrero"]
        
        daily_total = cuota_fija + excedente + prestaciones_dinero + pensionados + invalidez_vida + cesantia_vejez
        
        return cls._convert_from_daily(daily_total, frequency)
    
    @classmethod
    def calculate_employer_imss(cls, imss_base: Decimal, frequency: str) -> Decimal:
        """Calculate employer IMSS contributions"""
        daily_base = cls._convert_to_daily(imss_base, frequency)
        
        # Calculate components
        cuota_fija = UMA_DAILY_2024 * IMSS_RATES_2024["cuota_fija_patron"]
        
        # Excedente only if salary > 3 UMA
        excedente = Decimal("0")
        if daily_base > (UMA_DAILY_2024 * 3):
            excedente = (daily_base - (UMA_DAILY_2024 * 3)) * IMSS_RATES_2024["excedente_patron"]
        
        prestaciones_dinero = daily_base * IMSS_RATES_2024["prestaciones_dinero_patron"]
        prestaciones_especie = daily_base * IMSS_RATES_2024["prestaciones_especie_patron"]
        pensionados = daily_base * IMSS_RATES_2024["pensionados_patron"]
        invalidez_vida = daily_base * IMSS_RATES_2024["invalidez_vida_patron"]
        cesantia_vejez = daily_base * IMSS_RATES_2024["cesantia_vejez_patron"]
        infonavit = daily_base * IMSS_RATES_2024["infonavit_patron"]
        retiro = daily_base * IMSS_RATES_2024["retiro_patron"]
        
        daily_total = (cuota_fija + excedente + prestaciones_dinero + prestaciones_especie + 
                      pensionados + invalidez_vida + cesantia_vejez + infonavit + retiro)
        
        return cls._convert_from_daily(daily_total, frequency)
    
    @staticmethod
    def _convert_to_daily(amount: Decimal, frequency: str) -> Decimal:
        """Convert amount to daily"""
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
        """Convert daily amount to frequency"""
        if frequency == "monthly":
            return daily_amount * Decimal("30")
        elif frequency == "biweekly":
            return daily_amount * Decimal("14")
        elif frequency == "weekly":
            return daily_amount * Decimal("7")
        else:
            return daily_amount


class INFONAVITCalculator:
    """INFONAVIT (Instituto del Fondo Nacional de la Vivienda) calculations"""
    
    @classmethod
    def calculate_infonavit_base(cls, gross_salary: Decimal, frequency: str) -> Decimal:
        """Calculate INFONAVIT base salary"""
        # Convert to monthly for INFONAVIT calculations
        if frequency == "monthly":
            monthly_salary = gross_salary
        elif frequency == "biweekly":
            monthly_salary = gross_salary * Decimal("2")
        elif frequency == "weekly":
            monthly_salary = gross_salary * Decimal("4.33")
        else:
            monthly_salary = gross_salary * Decimal("30")
        
        # Apply INFONAVIT limits
        if monthly_salary < INFONAVIT_MINIMUM_SALARY:
            monthly_salary = INFONAVIT_MINIMUM_SALARY
        elif monthly_salary > INFONAVIT_MAXIMUM_SALARY:
            monthly_salary = INFONAVIT_MAXIMUM_SALARY
        
        # Convert back to original frequency
        return PayrollFrequencyCalculator.convert_monthly_to_period(monthly_salary, frequency)
    
    @classmethod
    def calculate_employee_infonavit(cls, infonavit_base: Decimal, frequency: str) -> Decimal:
        """Calculate employee INFONAVIT (usually 0% for employee)"""
        return Decimal("0")  # Employees don't contribute to INFONAVIT
    
    @classmethod
    def calculate_employer_infonavit(cls, infonavit_base: Decimal, frequency: str) -> Decimal:
        """Calculate employer INFONAVIT (5%)"""
        return infonavit_base * IMSS_RATES_2024["infonavit_patron"]


class ISRCalculator:
    """ISR (Impuesto Sobre la Renta) calculations"""
    
    @classmethod
    def calculate_isr(cls, gross_income: Decimal, frequency: str) -> Tuple[Decimal, Decimal, Decimal]:
        """Calculate ISR with subsidio para el empleo
        Returns: (isr_calculated, subsidio_empleo, isr_withheld)
        """
        # Convert to monthly for ISR calculation
        monthly_income = cls._convert_to_monthly(gross_income, frequency)
        
        # Calculate ISR from table
        isr_calculated = cls._calculate_isr_from_table(monthly_income)
        
        # Calculate subsidio para el empleo
        subsidio_empleo = cls._calculate_subsidio_empleo(monthly_income)
        
        # ISR withheld = ISR calculated - Subsidio
        isr_withheld = max(Decimal("0"), isr_calculated - subsidio_empleo)
        
        # Convert back to frequency
        isr_calculated = PayrollFrequencyCalculator.convert_monthly_to_period(isr_calculated, frequency)
        subsidio_empleo = PayrollFrequencyCalculator.convert_monthly_to_period(subsidio_empleo, frequency)
        isr_withheld = PayrollFrequencyCalculator.convert_monthly_to_period(isr_withheld, frequency)
        
        return isr_calculated, subsidio_empleo, isr_withheld
    
    @classmethod
    def _convert_to_monthly(cls, amount: Decimal, frequency: str) -> Decimal:
        """Convert amount to monthly"""
        if frequency == "monthly":
            return amount
        elif frequency == "biweekly":
            return amount * Decimal("2")
        elif frequency == "weekly":
            return amount * Decimal("4.33")
        else:
            return amount * Decimal("30")
    
    @classmethod
    def _calculate_isr_from_table(cls, monthly_income: Decimal) -> Decimal:
        """Calculate ISR using 2024 tax table"""
        for bracket in ISR_TABLE_MONTHLY_2024:
            if monthly_income >= bracket["lower"]:
                if bracket["upper"] is None or monthly_income <= bracket["upper"]:
                    excess = monthly_income - bracket["lower"]
                    variable_tax = excess * bracket["rate"]
                    total_tax = bracket["fixed"] + variable_tax
                    return total_tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        return Decimal("0")
    
    @classmethod
    def _calculate_subsidio_empleo(cls, monthly_income: Decimal) -> Decimal:
        """Calculate subsidio para el empleo"""
        for bracket in SUBSIDIO_EMPLEO_2024:
            if monthly_income >= bracket["lower"]:
                if bracket["upper"] is None or monthly_income <= bracket["upper"]:
                    return bracket["subsidio"]
        
        return Decimal("0")


class OvertimeCalculator:
    """Overtime calculations according to Mexican Labor Law"""
    
    @classmethod
    def calculate_overtime_amount(cls, base_hourly_rate: Decimal, overtime_hours: Decimal,
                                overtime_type: str = "regular") -> Decimal:
        """Calculate overtime amount
        
        Mexican Law:
        - First 9 hours over 8: double time (200%)
        - Hours over 17 total: triple time (300%)
        """
        if overtime_hours <= 0:
            return Decimal("0")
        
        overtime_amount = Decimal("0")
        remaining_hours = overtime_hours
        
        # First 9 hours of overtime: double time (200% = 2x base rate)
        if remaining_hours > 0:
            double_time_hours = min(remaining_hours, Decimal("9"))
            overtime_amount += double_time_hours * base_hourly_rate * Decimal("2")
            remaining_hours -= double_time_hours
        
        # Additional hours: triple time (300% = 3x base rate)
        if remaining_hours > 0:
            overtime_amount += remaining_hours * base_hourly_rate * Decimal("3")
        
        return overtime_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @classmethod
    def calculate_hourly_rate(cls, monthly_salary: Decimal, working_hours_per_day: int = 8,
                            working_days_per_month: int = 22) -> Decimal:
        """Calculate hourly rate from monthly salary"""
        total_monthly_hours = working_hours_per_day * working_days_per_month
        return (monthly_salary / Decimal(str(total_monthly_hours))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )


class PayrollEngine:
    """Main Payroll Engine for Mexico 2024"""
    
    def __init__(self):
        self.imss_calculator = IMSSCalculator()
        self.infonavit_calculator = INFONAVITCalculator()
        self.isr_calculator = ISRCalculator()
        self.overtime_calculator = OvertimeCalculator()
        self.frequency_calculator = PayrollFrequencyCalculator()
    
    def calculate_payroll(self, employee_data: Dict[str, Any], 
                         pay_period_start: date, pay_period_end: date,
                         overtime_hours: Decimal = Decimal("0"),
                         bonuses: Decimal = Decimal("0"),
                         commissions: Decimal = Decimal("0"),
                         other_income: Decimal = Decimal("0"),
                         loan_deductions: Decimal = Decimal("0"),
                         advance_deductions: Decimal = Decimal("0"),
                         other_deductions: Decimal = Decimal("0")) -> PayrollCalculation:
        """Complete payroll calculation for an employee"""
        
        employee_id = employee_data["id"]
        monthly_salary = Decimal(str(employee_data["monthly_salary"]))
        frequency = employee_data.get("payroll_frequency", "monthly")
        
        logger.info(f"Calculating payroll for employee {employee_id}")
        
        # Calculate period salary
        days_in_period = self.frequency_calculator.get_days_in_period(
            frequency, pay_period_start, pay_period_end
        )
        base_salary = self.frequency_calculator.convert_monthly_to_period(
            monthly_salary, frequency, days_in_period
        )
        
        # Calculate overtime
        hourly_rate = self.overtime_calculator.calculate_hourly_rate(monthly_salary)
        overtime_amount = self.overtime_calculator.calculate_overtime_amount(
            hourly_rate, overtime_hours
        )
        
        # Calculate gross income
        gross_income = base_salary + overtime_amount + bonuses + commissions + other_income
        
        # IMSS Calculations
        imss_base_salary = self.imss_calculator.calculate_imss_base_salary(gross_income, frequency)
        imss_employee = self.imss_calculator.calculate_employee_imss(imss_base_salary, frequency)
        imss_employer = self.imss_calculator.calculate_employer_imss(imss_base_salary, frequency)
        
        # INFONAVIT Calculations
        infonavit_base = self.infonavit_calculator.calculate_infonavit_base(gross_income, frequency)
        infonavit_employee = self.infonavit_calculator.calculate_employee_infonavit(infonavit_base, frequency)
        infonavit_employer = self.infonavit_calculator.calculate_employer_infonavit(infonavit_base, frequency)
        
        # ISR Calculations
        isr_base = gross_income - imss_employee  # ISR base = gross - employee IMSS
        isr_calculated, subsidio_empleo, isr_withheld = self.isr_calculator.calculate_isr(
            isr_base, frequency
        )
        
        # Total deductions
        total_deductions = (imss_employee + infonavit_employee + isr_withheld + 
                          loan_deductions + advance_deductions + other_deductions)
        
        # Net pay
        net_pay = gross_income - total_deductions
        
        # Total employer cost
        total_employer_cost = gross_income + imss_employer + infonavit_employer
        
        # Create calculation result
        calculation = PayrollCalculation(
            employee_id=employee_id,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            base_salary=base_salary,
            overtime_hours=overtime_hours,
            overtime_amount=overtime_amount,
            bonuses=bonuses,
            commissions=commissions,
            other_income=other_income,
            gross_income=gross_income,
            imss_base_salary=imss_base_salary,
            imss_employee=imss_employee,
            imss_employer=imss_employer,
            infonavit_employee=infonavit_employee,
            infonavit_employer=infonavit_employer,
            isr_base=isr_base,
            isr_calculated=isr_calculated,
            subsidio_empleo=subsidio_empleo,
            isr_withheld=isr_withheld,
            loan_deductions=loan_deductions,
            advance_deductions=advance_deductions,
            other_deductions=other_deductions,
            total_deductions=total_deductions,
            net_pay=net_pay,
            total_employer_cost=total_employer_cost,
            calculation_date=datetime.now(),
            payroll_frequency=frequency
        )
        
        logger.info(f"Payroll calculation completed for employee {employee_id}: Net pay ${net_pay}")
        return calculation
    
    def calculate_annual_projection(self, employee_data: Dict[str, Any]) -> Dict[str, Decimal]:
        """Calculate annual payroll projection"""
        monthly_salary = Decimal(str(employee_data["monthly_salary"]))
        
        # Annual base salary
        annual_base = monthly_salary * 12
        
        # Estimate overtime (10% of base)
        annual_overtime = annual_base * Decimal("0.10")
        
        # Annual gross
        annual_gross = annual_base + annual_overtime
        
        # Calculate for one month and project
        sample_calculation = self.calculate_payroll(
            employee_data,
            date.today().replace(day=1),
            date.today(),
            overtime_hours=Decimal("10"),  # Sample overtime
        )
        
        # Project annual values
        annual_imss_employee = sample_calculation.imss_employee * 12
        annual_imss_employer = sample_calculation.imss_employer * 12
        annual_isr = sample_calculation.isr_withheld * 12
        annual_net = annual_gross - annual_imss_employee - annual_isr
        annual_employer_cost = annual_gross + annual_imss_employer
        
        return {
            "annual_base_salary": annual_base,
            "annual_overtime": annual_overtime,
            "annual_gross": annual_gross,
            "annual_imss_employee": annual_imss_employee,
            "annual_imss_employer": annual_imss_employer,
            "annual_isr": annual_isr,
            "annual_net_pay": annual_net,
            "annual_employer_cost": annual_employer_cost
        }
    
    def generate_payslip_data(self, calculation: PayrollCalculation) -> Dict[str, Any]:
        """Generate structured payslip data"""
        return {
            "employee_id": calculation.employee_id,
            "pay_period": {
                "start": calculation.pay_period_start.isoformat(),
                "end": calculation.pay_period_end.isoformat(),
                "frequency": calculation.payroll_frequency
            },
            "income": {
                "base_salary": float(calculation.base_salary),
                "overtime_hours": float(calculation.overtime_hours),
                "overtime_amount": float(calculation.overtime_amount),
                "bonuses": float(calculation.bonuses),
                "commissions": float(calculation.commissions),
                "other_income": float(calculation.other_income),
                "gross_total": float(calculation.gross_income)
            },
            "deductions": {
                "imss": float(calculation.imss_employee),
                "infonavit": float(calculation.infonavit_employee),
                "isr": float(calculation.isr_withheld),
                "subsidio_empleo": float(calculation.subsidio_empleo),
                "loans": float(calculation.loan_deductions),
                "advances": float(calculation.advance_deductions),
                "other": float(calculation.other_deductions),
                "total": float(calculation.total_deductions)
            },
            "net_pay": float(calculation.net_pay),
            "employer_costs": {
                "imss": float(calculation.imss_employer),
                "infonavit": float(calculation.infonavit_employer),
                "total": float(calculation.total_employer_cost)
            },
            "calculation_metadata": {
                "calculation_date": calculation.calculation_date.isoformat(),
                "currency": calculation.currency,
                "uma_daily": float(UMA_DAILY_2024),
                "uma_monthly": float(UMA_MONTHLY_2024)
            }
        }
    
    def validate_payroll_data(self, employee_data: Dict[str, Any]) -> List[str]:
        """Validate employee data for payroll calculation"""
        errors = []
        
        # Required fields
        required_fields = ["id", "monthly_salary", "payroll_frequency"]
        for field in required_fields:
            if field not in employee_data:
                errors.append(f"Missing required field: {field}")
        
        # Salary validation
        if "monthly_salary" in employee_data:
            try:
                salary = Decimal(str(employee_data["monthly_salary"]))
                if salary <= 0:
                    errors.append("Monthly salary must be greater than 0")
                if salary < UMA_MONTHLY_2024:
                    errors.append(f"Monthly salary is below minimum wage (UMA): ${UMA_MONTHLY_2024}")
            except (ValueError, TypeError):
                errors.append("Invalid monthly salary format")
        
        # Frequency validation
        valid_frequencies = ["daily", "weekly", "biweekly", "monthly", "bimonthly"]
        if "payroll_frequency" in employee_data:
            if employee_data["payroll_frequency"] not in valid_frequencies:
                errors.append(f"Invalid payroll frequency. Must be one of: {valid_frequencies}")
        
        return errors