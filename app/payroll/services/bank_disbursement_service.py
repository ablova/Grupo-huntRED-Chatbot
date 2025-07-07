"""
Servicio de Dispersión Bancaria huntRED® Payroll
Integración con gateways bancarios existentes para dispersión de nómina
"""
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, date

from django.core.exceptions import ValidationError
from django.utils import timezone

from app.ats.pricing.gateways.banks import BBVAGateway, SantanderGateway, BanamexGateway, BanorteGateway
from app.ats.models import PaymentGateway, BankAccount
from ..models import PayrollCompany, PayrollPeriod, PayrollCalculation
from .. import PREMIUM_SERVICES

logger = logging.getLogger(__name__)


class BankDisbursementService:
    """
    Servicio de dispersión bancaria para nómina
    """
    
    def __init__(self, company: PayrollCompany):
        self.company = company
        self.business_unit = company.business_unit
        
        # Obtener gateway bancario configurado
        self.bank_gateway = self._get_bank_gateway()
        
        # Configuración de servicios premium
        self.premium_config = PREMIUM_SERVICES.get('bank_disbursement', {})
    
    def _get_bank_gateway(self) -> Optional[Any]:
        """Obtiene gateway bancario configurado para la empresa"""
        try:
            # Buscar gateway bancario activo
            payment_gateway = PaymentGateway.objects.filter(
                business_unit=self.business_unit,
                gateway_type__in=['bbva', 'santander', 'banamex', 'banorte'],
                status='active'
            ).first()
            
            if not payment_gateway:
                logger.warning(f"No se encontró gateway bancario para empresa {self.company.name}")
                return None
            
            # Crear instancia del gateway específico
            if payment_gateway.gateway_type == 'bbva':
                return BBVAGateway(self.business_unit, payment_gateway)
            elif payment_gateway.gateway_type == 'santander':
                return SantanderGateway(self.business_unit, payment_gateway)
            elif payment_gateway.gateway_type == 'banamex':
                return BanamexGateway(self.business_unit, payment_gateway)
            elif payment_gateway.gateway_type == 'banorte':
                return BanorteGateway(self.business_unit, payment_gateway)
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo gateway bancario: {str(e)}")
            return None
    
    def create_payroll_disbursement(
        self,
        period: PayrollPeriod,
        source_account: BankAccount,
        execution_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Crea dispersión bancaria para un período de nómina
        
        Args:
            period: Período de nómina
            source_account: Cuenta bancaria de origen
            execution_date: Fecha de ejecución (opcional)
            
        Returns:
            Resultado de la dispersión
        """
        try:
            if not self.bank_gateway:
                raise ValidationError("No hay gateway bancario configurado")
            
            # Validar que el período esté aprobado
            if period.status != 'approved':
                raise ValidationError("El período debe estar aprobado para dispersión")
            
            # Obtener cálculos de nómina
            calculations = period.calculations.all()
            if not calculations:
                raise ValidationError("No hay cálculos de nómina para dispersar")
            
            # Validar monto mínimo
            total_amount = sum(calc.net_pay for calc in calculations)
            min_amount = Decimal(str(self.premium_config.get('min_amount', 500000)))
            
            if total_amount < min_amount:
                raise ValidationError(f"Monto mínimo no alcanzado: ${total_amount:,.2f} < ${min_amount:,.2f}")
            
            # Crear órdenes de pago individuales
            payment_orders = []
            successful_payments = 0
            failed_payments = 0
            total_disbursed = Decimal("0")
            
            for calculation in calculations:
                employee = calculation.employee
                
                # Validar información bancaria
                if not employee.clabe:
                    logger.warning(f"Empleado {employee.id} sin CLABE configurada")
                    failed_payments += 1
                    continue
                
                # Crear orden de pago
                payment_result = self.bank_gateway.create_payment_order(
                    beneficiary_account=employee.clabe,
                    beneficiary_name=employee.get_full_name(),
                    amount=calculation.net_pay,
                    description=f"Nómina {period.period_name}",
                    reference=f"PAYROLL-{period.id}-{employee.employee_number}",
                    execution_date=execution_date
                )
                
                if payment_result.get('success'):
                    payment_orders.append({
                        'employee_id': str(employee.id),
                        'employee_name': employee.get_full_name(),
                        'amount': float(calculation.net_pay),
                        'payment_id': payment_result.get('payment_id'),
                        'status': 'created'
                    })
                    successful_payments += 1
                    total_disbursed += calculation.net_pay
                else:
                    logger.error(f"Error creando pago para {employee.get_full_name()}: {payment_result.get('error')}")
                    failed_payments += 1
            
            # Calcular comisión
            fee_percentage = Decimal(str(self.premium_config.get('fee_percentage', 0.8)))
            fee_amount = total_disbursed * (fee_percentage / Decimal("100"))
            
            # Actualizar período
            if successful_payments > 0:
                period.status = 'disbursed'
                period.disbursement_date = timezone.now()
                period.save()
            
            return {
                "success": True,
                "period_id": str(period.id),
                "total_employees": len(calculations),
                "successful_payments": successful_payments,
                "failed_payments": failed_payments,
                "total_amount": float(total_amount),
                "total_disbursed": float(total_disbursed),
                "fee_amount": float(fee_amount),
                "payment_orders": payment_orders,
                "execution_date": execution_date.isoformat() if execution_date else None
            }
            
        except Exception as e:
            logger.error(f"Error en dispersión bancaria: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "period_id": str(period.id) if period else None
            }
    
    def get_disbursement_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Obtiene estado de una dispersión
        
        Args:
            payment_id: ID del pago
            
        Returns:
            Estado del pago
        """
        try:
            if not self.bank_gateway:
                raise ValidationError("No hay gateway bancario configurado")
            
            status_result = self.bank_gateway.get_payment_status(payment_id)
            
            return {
                "success": True,
                "payment_id": payment_id,
                "status": status_result.get('status'),
                "amount": status_result.get('amount'),
                "execution_date": status_result.get('execution_date'),
                "confirmation_date": status_result.get('confirmation_date')
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de pago {payment_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "payment_id": payment_id
            }
    
    def generate_disbursement_file(
        self,
        period: PayrollPeriod,
        bank_format: str = "banamex"
    ) -> Dict[str, Any]:
        """
        Genera archivo de dispersión en formato bancario
        
        Args:
            period: Período de nómina
            bank_format: Formato bancario (banamex, bbva, santander, banorte)
            
        Returns:
            Archivo de dispersión
        """
        try:
            calculations = period.calculations.all()
            
            if not calculations:
                raise ValidationError("No hay cálculos de nómina para generar archivo")
            
            # Generar contenido según formato
            if bank_format == "banamex":
                content = self._generate_banamex_format(calculations, period)
            elif bank_format == "bbva":
                content = self._generate_bbva_format(calculations, period)
            elif bank_format == "santander":
                content = self._generate_santander_format(calculations, period)
            elif bank_format == "banorte":
                content = self._generate_banorte_format(calculations, period)
            else:
                content = self._generate_csv_format(calculations, period)
            
            filename = f"dispersión_nómina_{period.period_name}_{bank_format}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            return {
                "success": True,
                "filename": filename,
                "content": content,
                "total_records": len(calculations),
                "total_amount": float(sum(calc.net_pay for calc in calculations)),
                "format": bank_format
            }
            
        except Exception as e:
            logger.error(f"Error generando archivo de dispersión: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_banamex_format(self, calculations: List[PayrollCalculation], period: PayrollPeriod) -> str:
        """Genera formato Banamex (142 caracteres por registro)"""
        content = []
        
        for calculation in calculations:
            employee = calculation.employee
            
            # Formato: 142 caracteres
            # 1-20: Nombre beneficiario (izquierda, espacios)
            # 21-40: CLABE (derecha, ceros)
            # 41-60: Monto (derecha, ceros, centavos)
            # 61-80: Referencia (izquierda, espacios)
            # 81-142: Espacios en blanco
            
            name = employee.get_full_name()[:20].ljust(20)
            clabe = employee.clabe.zfill(18) if employee.clabe else "0" * 18
            amount = f"{int(calculation.net_pay * 100):018d}"  # Centavos
            reference = f"PAYROLL-{period.id}-{employee.employee_number}"[:20].ljust(20)
            
            record = f"{name}{clabe}{amount}{reference}{' ' * 62}"
            content.append(record)
        
        return "\n".join(content)
    
    def _generate_bbva_format(self, calculations: List[PayrollCalculation], period: PayrollPeriod) -> str:
        """Genera formato BBVA"""
        content = []
        
        for calculation in calculations:
            employee = calculation.employee
            
            # Formato BBVA específico
            record = {
                "beneficiary_name": employee.get_full_name(),
                "clabe": employee.clabe,
                "amount": float(calculation.net_pay),
                "reference": f"PAYROLL-{period.id}-{employee.employee_number}",
                "description": f"Nómina {period.period_name}"
            }
            
            content.append(record)
        
        return json.dumps(content, indent=2)
    
    def _generate_santander_format(self, calculations: List[PayrollCalculation], period: PayrollPeriod) -> str:
        """Genera formato Santander"""
        content = []
        
        for calculation in calculations:
            employee = calculation.employee
            
            # Formato Santander específico
            record = f"{employee.get_full_name()},{employee.clabe},{calculation.net_pay},{period.period_name}"
            content.append(record)
        
        return "\n".join(content)
    
    def _generate_banorte_format(self, calculations: List[PayrollCalculation], period: PayrollPeriod) -> str:
        """Genera formato Banorte"""
        content = []
        
        for calculation in calculations:
            employee = calculation.employee
            
            # Formato Banorte específico
            record = f"{employee.get_full_name()}|{employee.clabe}|{calculation.net_pay}|{period.period_name}"
            content.append(record)
        
        return "\n".join(content)
    
    def _generate_csv_format(self, calculations: List[PayrollCalculation], period: PayrollPeriod) -> str:
        """Genera formato CSV genérico"""
        content = ["Nombre,CLABE,Monto,Referencia,Descripción"]
        
        for calculation in calculations:
            employee = calculation.employee
            
            record = [
                employee.get_full_name(),
                employee.clabe or "",
                str(calculation.net_pay),
                f"PAYROLL-{period.id}-{employee.employee_number}",
                f"Nómina {period.period_name}"
            ]
            
            content.append(",".join(record))
        
        return "\n".join(content)
    
    def validate_bank_accounts(self, period: PayrollPeriod) -> Dict[str, Any]:
        """
        Valida cuentas bancarias de empleados
        
        Args:
            period: Período de nómina
            
        Returns:
            Resultado de validación
        """
        try:
            calculations = period.calculations.all()
            
            valid_accounts = 0
            invalid_accounts = 0
            missing_accounts = 0
            issues = []
            
            for calculation in calculations:
                employee = calculation.employee
                
                if not employee.clabe:
                    missing_accounts += 1
                    issues.append({
                        "employee_id": str(employee.id),
                        "employee_name": employee.get_full_name(),
                        "issue": "Sin CLABE configurada"
                    })
                elif not self._validate_clabe(employee.clabe):
                    invalid_accounts += 1
                    issues.append({
                        "employee_id": str(employee.id),
                        "employee_name": employee.get_full_name(),
                        "issue": "CLABE inválida",
                        "clabe": employee.clabe
                    })
                else:
                    valid_accounts += 1
            
            return {
                "success": True,
                "total_employees": len(calculations),
                "valid_accounts": valid_accounts,
                "invalid_accounts": invalid_accounts,
                "missing_accounts": missing_accounts,
                "issues": issues,
                "can_disburse": invalid_accounts == 0 and missing_accounts == 0
            }
            
        except Exception as e:
            logger.error(f"Error validando cuentas bancarias: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_clabe(self, clabe: str) -> bool:
        """Valida formato de CLABE"""
        import re
        
        # CLABE debe tener 18 dígitos
        if not re.match(r'^\d{18}$', clabe):
            return False
        
        # Aquí se podría agregar validación de dígito verificador
        # Por ahora solo validamos formato
        
        return True 