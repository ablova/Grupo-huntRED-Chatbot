"""
Servicio de Cálculo de Finiquito y Liquidación huntRED®
Cálculos precisos conforme a la LFT con desglose completo
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json

from django.utils import timezone
from django.core.exceptions import ValidationError

from ..models import PayrollEmployee, PayrollCalculation, AttendanceRecord
from .payroll_engine import PayrollEngine

logger = logging.getLogger(__name__)


class SeveranceCalculationService:
    """
    Servicio de cálculo de finiquito y liquidación
    """
    
    def __init__(self, employee: PayrollEmployee):
        self.employee = employee
        self.company = employee.company
        self.payroll_engine = PayrollEngine(self.company)
        
        # Configuración de beneficios
        self.benefits_config = self._get_benefits_config()
    
    def _get_benefits_config(self) -> Dict[str, Any]:
        """Obtiene configuración de beneficios de la empresa"""
        return self.company.premium_services.get('benefits', {
            'vacation_days_per_year': 12,
            'vacation_bonus_percentage': 25.0,  # 25% de prima vacacional
            'christmas_bonus_days': 15,
            'profit_sharing_percentage': 10.0,  # 10% de PTU
            'savings_fund_percentage': 13.0,    # 13% de fondo de ahorro
            'food_voucher_amount': 0,           # Vales de despensa
            'transport_voucher_amount': 0,      # Vales de transporte
            'housing_benefit_amount': 0,        # Beneficio de vivienda
            'other_benefits': {}
        })
    
    def calculate_severance(self, termination_date: date, termination_type: str = 'voluntary') -> Dict[str, Any]:
        """
        Calcula finiquito o liquidación según tipo de terminación
        
        Args:
            termination_date: Fecha de terminación
            termination_type: Tipo de terminación ('voluntary', 'involuntary', 'layoff')
            
        Returns:
            Cálculo completo de finiquito/liquidación
        """
        try:
            # Calcular antigüedad
            seniority = self._calculate_seniority(termination_date)
            
            # Obtener salario base
            base_salary = self.employee.monthly_salary
            
            # Calcular percepciones
            perceptions = self._calculate_perceptions(termination_date, seniority)
            
            # Calcular deducciones
            deductions = self._calculate_deductions(perceptions['gross_total'])
            
            # Calcular neto
            net_amount = perceptions['gross_total'] - deductions['total_deductions']
            
            # Calcular indemnización si aplica
            indemnization = self._calculate_indemnization(seniority, termination_type)
            
            # Calcular total a pagar
            total_to_pay = net_amount + indemnization['total']
            
            # Generar desglose
            breakdown = self._generate_breakdown(
                seniority, perceptions, deductions, 
                indemnization, total_to_pay, termination_type
            )
            
            return {
                'success': True,
                'employee_info': {
                    'name': self.employee.get_full_name(),
                    'employee_number': self.employee.employee_number,
                    'hire_date': self.employee.hire_date.isoformat(),
                    'termination_date': termination_date.isoformat(),
                    'seniority': seniority,
                    'base_salary': float(base_salary)
                },
                'seniority_breakdown': seniority,
                'perceptions': perceptions,
                'deductions': deductions,
                'indemnization': indemnization,
                'totals': {
                    'gross_total': float(perceptions['gross_total']),
                    'total_deductions': float(deductions['total_deductions']),
                    'net_amount': float(net_amount),
                    'indemnization_total': float(indemnization['total']),
                    'total_to_pay': float(total_to_pay)
                },
                'breakdown': breakdown,
                'calculation_date': timezone.now().isoformat(),
                'termination_type': termination_type
            }
            
        except Exception as e:
            logger.error(f"Error calculando finiquito para {self.employee.get_full_name()}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_seniority(self, termination_date: date) -> Dict[str, Any]:
        """Calcula antigüedad del empleado"""
        hire_date = self.employee.hire_date
        delta = termination_date - hire_date
        
        years = delta.days // 365
        remaining_days = delta.days % 365
        months = remaining_days // 30
        days = remaining_days % 30
        
        total_days = delta.days
        total_months = (years * 12) + months
        
        return {
            'years': years,
            'months': months,
            'days': days,
            'total_days': total_days,
            'total_months': total_months,
            'formatted': f"{years} años, {months} meses y {days} días"
        }
    
    def _calculate_perceptions(self, termination_date: date, seniority: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula percepciones del finiquito"""
        base_salary = self.employee.monthly_salary
        daily_salary = base_salary / 30.4  # Salario diario
        
        # 1. Salarios vencidos (si aplica)
        last_payroll_date = self._get_last_payroll_date()
        if last_payroll_date < termination_date:
            days_pending = (termination_date - last_payroll_date).days
            pending_salary = daily_salary * days_pending
        else:
            pending_salary = Decimal('0')
        
        # 2. Vacaciones no gozadas
        vacation_days = self._calculate_vacation_days(seniority)
        vacation_amount = daily_salary * vacation_days
        
        # 3. Prima vacacional
        vacation_bonus = vacation_amount * (Decimal(str(self.benefits_config['vacation_bonus_percentage'])) / 100)
        
        # 4. Aguinaldo proporcional
        christmas_bonus = self._calculate_christmas_bonus(termination_date)
        
        # 5. PTU proporcional (si aplica)
        ptu = self._calculate_ptu_proportional(termination_date)
        
        # 6. Fondo de ahorro proporcional
        savings_fund = self._calculate_savings_fund_proportional(termination_date)
        
        # 7. Otros beneficios
        other_benefits = self._calculate_other_benefits(termination_date)
        
        gross_total = (
            pending_salary + vacation_amount + vacation_bonus + 
            christmas_bonus + ptu + savings_fund + other_benefits
        )
        
        return {
            'pending_salary': float(pending_salary),
            'vacation_days': vacation_days,
            'vacation_amount': float(vacation_amount),
            'vacation_bonus': float(vacation_bonus),
            'christmas_bonus': float(christmas_bonus),
            'ptu': float(ptu),
            'savings_fund': float(savings_fund),
            'other_benefits': float(other_benefits),
            'gross_total': gross_total
        }
    
    def _calculate_deductions(self, gross_amount: Decimal) -> Dict[str, Any]:
        """Calcula deducciones del finiquito"""
        # Las deducciones en finiquito son mínimas, principalmente ISR
        isr = self.payroll_engine.calculate_isr(gross_amount)
        
        # No se descuentan IMSS ni INFONAVIT en finiquito
        total_deductions = isr
        
        return {
            'isr': float(isr),
            'imss': 0.0,  # No se descuenta en finiquito
            'infonavit': 0.0,  # No se descuenta en finiquito
            'other_deductions': 0.0,
            'total_deductions': total_deductions
        }
    
    def _calculate_indemnization(self, seniority: Dict[str, Any], termination_type: str) -> Dict[str, Any]:
        """Calcula indemnización según tipo de terminación"""
        if termination_type == 'voluntary':
            # Renuncia voluntaria - no hay indemnización
            return {
                'seniority_premium': 0.0,
                'constitutional_indemnization': 0.0,
                'total': Decimal('0')
            }
        
        elif termination_type == 'involuntary':
            # Despido injustificado - indemnización completa
            daily_salary = self.employee.monthly_salary / 30.4
            
            # Prima de antigüedad (12 días por año)
            seniority_premium = daily_salary * 12 * seniority['years']
            
            # Indemnización constitucional (3 meses + 20 días por año)
            constitutional_indemnization = (
                daily_salary * 90 +  # 3 meses
                daily_salary * 20 * seniority['years']  # 20 días por año
            )
            
            total = seniority_premium + constitutional_indemnization
            
            return {
                'seniority_premium': float(seniority_premium),
                'constitutional_indemnization': float(constitutional_indemnization),
                'total': total
            }
        
        elif termination_type == 'layoff':
            # Despido por causas de fuerza mayor - indemnización reducida
            daily_salary = self.employee.monthly_salary / 30.4
            
            # Solo prima de antigüedad
            seniority_premium = daily_salary * 12 * seniority['years']
            
            return {
                'seniority_premium': float(seniority_premium),
                'constitutional_indemnization': 0.0,
                'total': seniority_premium
            }
        
        else:
            return {
                'seniority_premium': 0.0,
                'constitutional_indemnization': 0.0,
                'total': Decimal('0')
            }
    
    def _calculate_vacation_days(self, seniority: Dict[str, Any]) -> int:
        """Calcula días de vacaciones no gozadas"""
        # Obtener días de vacaciones por año según antigüedad
        vacation_days_per_year = self._get_vacation_days_by_seniority(seniority['years'])
        
        # Calcular días proporcionales
        days_this_year = (seniority['total_days'] % 365)
        proportional_days = (vacation_days_per_year * days_this_year) / 365
        
        # Obtener días ya gozados este año
        used_vacation_days = self._get_used_vacation_days()
        
        # Días pendientes
        pending_days = proportional_days - used_vacation_days
        
        return max(0, int(pending_days))
    
    def _get_vacation_days_by_seniority(self, years: int) -> int:
        """Obtiene días de vacaciones según antigüedad (LFT)"""
        if years < 1:
            return 6
        elif years < 2:
            return 8
        elif years < 3:
            return 10
        elif years < 4:
            return 12
        elif years < 5:
            return 14
        elif years < 6:
            return 16
        elif years < 7:
            return 18
        elif years < 8:
            return 20
        elif years < 9:
            return 22
        elif years < 10:
            return 24
        elif years < 11:
            return 26
        elif years < 12:
            return 28
        elif years < 13:
            return 30
        elif years < 14:
            return 32
        else:
            return 34
    
    def _calculate_christmas_bonus(self, termination_date: date) -> Decimal:
        """Calcula aguinaldo proporcional"""
        daily_salary = self.employee.monthly_salary / 30.4
        christmas_bonus_days = self.benefits_config['christmas_bonus_days']
        
        # Calcular días trabajados en el año
        year_start = date(termination_date.year, 1, 1)
        days_worked = (termination_date - year_start).days
        
        # Aguinaldo proporcional
        proportional_bonus = (daily_salary * christmas_bonus_days * days_worked) / 365
        
        return proportional_bonus
    
    def _calculate_ptu_proportional(self, termination_date: date) -> Decimal:
        """Calcula PTU proporcional"""
        # Esto dependería de la PTU declarada por la empresa
        # Por ahora retornamos 0
        return Decimal('0')
    
    def _calculate_savings_fund_proportional(self, termination_date: date) -> Decimal:
        """Calcula fondo de ahorro proporcional"""
        daily_salary = self.employee.monthly_salary / 30.4
        savings_percentage = Decimal(str(self.benefits_config['savings_fund_percentage']))
        
        # Calcular días trabajados en el año
        year_start = date(termination_date.year, 1, 1)
        days_worked = (termination_date - year_start).days
        
        # Fondo de ahorro proporcional
        proportional_savings = (daily_salary * savings_percentage * days_worked) / (100 * 365)
        
        return proportional_savings
    
    def _calculate_other_benefits(self, termination_date: date) -> Decimal:
        """Calcula otros beneficios proporcionales"""
        # Vales de despensa, transporte, etc.
        food_voucher = Decimal(str(self.benefits_config['food_voucher_amount']))
        transport_voucher = Decimal(str(self.benefits_config['transport_voucher_amount']))
        
        # Calcular proporcional
        year_start = date(termination_date.year, 1, 1)
        days_worked = (termination_date - year_start).days
        
        proportional_benefits = ((food_voucher + transport_voucher) * days_worked) / 365
        
        return proportional_benefits
    
    def _get_last_payroll_date(self) -> date:
        """Obtiene fecha del último pago de nómina"""
        # Buscar último cálculo de nómina
        last_calculation = PayrollCalculation.objects.filter(
            employee=self.employee
        ).order_by('-calculation_date').first()
        
        if last_calculation:
            return last_calculation.period.end_date
        else:
            # Si no hay cálculos, usar fecha de contratación
            return self.employee.hire_date
    
    def _get_used_vacation_days(self) -> int:
        """Obtiene días de vacaciones ya utilizados este año"""
        current_year = timezone.now().year
        year_start = date(current_year, 1, 1)
        year_end = date(current_year, 12, 31)
        
        # Buscar solicitudes de vacaciones aprobadas este año
        vacation_requests = self.employee.requests.filter(
            request_type='vacation',
            status='approved',
            start_date__gte=year_start,
            end_date__lte=year_end
        )
        
        used_days = 0
        for request in vacation_requests:
            used_days += request.days_requested
        
        return used_days
    
    def _generate_breakdown(self, seniority: Dict[str, Any], perceptions: Dict[str, Any], 
                          deductions: Dict[str, Any], indemnization: Dict[str, Any], 
                          total_to_pay: Decimal, termination_type: str) -> Dict[str, Any]:
        """Genera desglose completo del finiquito"""
        
        breakdown = {
            'summary': {
                'employee_name': self.employee.get_full_name(),
                'employee_number': self.employee.employee_number,
                'hire_date': self.employee.hire_date.strftime('%d/%m/%Y'),
                'termination_date': timezone.now().strftime('%d/%m/%Y'),
                'seniority': seniority['formatted'],
                'termination_type': termination_type,
                'base_salary': f"${self.employee.monthly_salary:,.2f} MXN"
            },
            'perceptions_detail': {
                'pending_salary': {
                    'description': 'Salarios vencidos',
                    'amount': f"${perceptions['pending_salary']:,.2f}",
                    'calculation': 'Salario diario × días pendientes'
                },
                'vacation_days': {
                    'description': f'Vacaciones no gozadas ({perceptions["vacation_days"]} días)',
                    'amount': f"${perceptions['vacation_amount']:,.2f}",
                    'calculation': f'Salario diario × {perceptions["vacation_days"]} días'
                },
                'vacation_bonus': {
                    'description': 'Prima vacacional (25%)',
                    'amount': f"${perceptions['vacation_bonus']:,.2f}",
                    'calculation': 'Vacaciones × 25%'
                },
                'christmas_bonus': {
                    'description': 'Aguinaldo proporcional',
                    'amount': f"${perceptions['christmas_bonus']:,.2f}",
                    'calculation': '15 días × proporción del año'
                },
                'ptu': {
                    'description': 'PTU proporcional',
                    'amount': f"${perceptions['ptu']:,.2f}",
                    'calculation': 'PTU anual × proporción'
                },
                'savings_fund': {
                    'description': 'Fondo de ahorro proporcional',
                    'amount': f"${perceptions['savings_fund']:,.2f}",
                    'calculation': '13% × proporción del año'
                },
                'other_benefits': {
                    'description': 'Otros beneficios',
                    'amount': f"${perceptions['other_benefits']:,.2f}",
                    'calculation': 'Vales y beneficios × proporción'
                }
            },
            'deductions_detail': {
                'isr': {
                    'description': 'ISR',
                    'amount': f"${deductions['isr']:,.2f}",
                    'calculation': 'Según tabla ISR'
                },
                'imss': {
                    'description': 'IMSS',
                    'amount': f"${deductions['imss']:,.2f}",
                    'calculation': 'No aplica en finiquito'
                },
                'infonavit': {
                    'description': 'INFONAVIT',
                    'amount': f"${deductions['infonavit']:,.2f}",
                    'calculation': 'No aplica en finiquito'
                }
            },
            'indemnization_detail': {
                'seniority_premium': {
                    'description': 'Prima de antigüedad',
                    'amount': f"${indemnization['seniority_premium']:,.2f}",
                    'calculation': f'12 días × {seniority["years"]} años'
                },
                'constitutional_indemnization': {
                    'description': 'Indemnización constitucional',
                    'amount': f"${indemnization['constitutional_indemnization']:,.2f}",
                    'calculation': '3 meses + 20 días por año'
                }
            },
            'totals': {
                'gross_total': f"${perceptions['gross_total']:,.2f}",
                'total_deductions': f"${deductions['total_deductions']:,.2f}",
                'net_amount': f"${perceptions['gross_total'] - deductions['total_deductions']:,.2f}",
                'indemnization_total': f"${indemnization['total']:,.2f}",
                'total_to_pay': f"${total_to_pay:,.2f}"
            }
        }
        
        return breakdown
    
    def export_breakdown(self, calculation_result: Dict[str, Any], format: str = 'txt') -> str:
        """
        Exporta desglose en formato especificado
        
        Args:
            calculation_result: Resultado del cálculo
            format: Formato de exportación ('txt', 'json', 'html')
            
        Returns:
            Contenido exportado
        """
        breakdown = calculation_result['breakdown']
        
        if format == 'txt':
            return self._export_txt(breakdown)
        elif format == 'json':
            return json.dumps(breakdown, indent=2, ensure_ascii=False)
        elif format == 'html':
            return self._export_html(breakdown)
        else:
            raise ValueError(f"Formato no soportado: {format}")
    
    def _export_txt(self, breakdown: Dict[str, Any]) -> str:
        """Exporta desglose en formato texto"""
        content = []
        
        # Encabezado
        content.append("=" * 60)
        content.append("FINIQUITO / LIQUIDACIÓN")
        content.append("=" * 60)
        content.append("")
        
        # Información del empleado
        summary = breakdown['summary']
        content.append(f"EMPLEADO: {summary['employee_name']}")
        content.append(f"NÚMERO: {summary['employee_number']}")
        content.append(f"FECHA DE CONTRATACIÓN: {summary['hire_date']}")
        content.append(f"FECHA DE TERMINACIÓN: {summary['termination_date']}")
        content.append(f"ANTIGÜEDAD: {summary['seniority']}")
        content.append(f"TIPO DE TERMINACIÓN: {summary['termination_type']}")
        content.append(f"SALARIO BASE: {summary['base_salary']}")
        content.append("")
        
        # Percepciones
        content.append("PERCEPCIONES:")
        content.append("-" * 30)
        for key, detail in breakdown['perceptions_detail'].items():
            content.append(f"{detail['description']}: {detail['amount']}")
        content.append("")
        
        # Deducciones
        content.append("DEDUCCIONES:")
        content.append("-" * 30)
        for key, detail in breakdown['deductions_detail'].items():
            content.append(f"{detail['description']}: {detail['amount']}")
        content.append("")
        
        # Indemnización
        content.append("INDEMNIZACIÓN:")
        content.append("-" * 30)
        for key, detail in breakdown['indemnization_detail'].items():
            content.append(f"{detail['description']}: {detail['amount']}")
        content.append("")
        
        # Totales
        content.append("TOTALES:")
        content.append("-" * 30)
        totals = breakdown['totals']
        content.append(f"TOTAL BRUTO: {totals['gross_total']}")
        content.append(f"TOTAL DEDUCCIONES: {totals['total_deductions']}")
        content.append(f"NETO: {totals['net_amount']}")
        content.append(f"INDEMNIZACIÓN: {totals['indemnization_total']}")
        content.append("=" * 30)
        content.append(f"TOTAL A PAGAR: {totals['total_to_pay']}")
        content.append("=" * 30)
        content.append("")
        content.append(f"Fecha de cálculo: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        return "\n".join(content)
    
    def _export_html(self, breakdown: Dict[str, Any]) -> str:
        """Exporta desglose en formato HTML"""
        # Implementar exportación HTML con estilos
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Finiquito - {breakdown['summary']['employee_name']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }}
                .section {{ margin: 20px 0; }}
                .section h3 {{ color: #333; border-bottom: 1px solid #ccc; }}
                .item {{ display: flex; justify-content: space-between; margin: 5px 0; }}
                .total {{ font-weight: bold; border-top: 2px solid #333; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>FINIQUITO / LIQUIDACIÓN</h1>
            </div>
            
            <div class="section">
                <h3>Información del Empleado</h3>
                <div class="item">
                    <span>Nombre:</span>
                    <span>{breakdown['summary']['employee_name']}</span>
                </div>
                <div class="item">
                    <span>Número:</span>
                    <span>{breakdown['summary']['employee_number']}</span>
                </div>
                <div class="item">
                    <span>Antigüedad:</span>
                    <span>{breakdown['summary']['seniority']}</span>
                </div>
            </div>
            
            <div class="section">
                <h3>Percepciones</h3>
                {self._generate_html_items(breakdown['perceptions_detail'])}
            </div>
            
            <div class="section">
                <h3>Deducciones</h3>
                {self._generate_html_items(breakdown['deductions_detail'])}
            </div>
            
            <div class="section">
                <h3>Indemnización</h3>
                {self._generate_html_items(breakdown['indemnization_detail'])}
            </div>
            
            <div class="section total">
                <h3>Total a Pagar</h3>
                <div class="item">
                    <span>Total a Pagar:</span>
                    <span>{breakdown['totals']['total_to_pay']}</span>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_html_items(self, items: Dict[str, Any]) -> str:
        """Genera HTML para items de una sección"""
        html_items = []
        for key, detail in items.items():
            html_items.append(f"""
                <div class="item">
                    <span>{detail['description']}:</span>
                    <span>{detail['amount']}</span>
                </div>
            """)
        return "".join(html_items) 