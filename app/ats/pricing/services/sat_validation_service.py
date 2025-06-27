"""
Servicio de validación SAT para proveedores y RFCs.
"""
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET

from app.models import Person, BusinessUnit

logger = logging.getLogger(__name__)

class SATValidationService:
    """Servicio para validar RFCs y proveedores con el SAT."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.sat_api_url = "https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc"
    
    def validate_rfc(
        self,
        rfc: str,
        include_blacklist_check: bool = True
    ) -> Dict[str, Any]:
        """
        Valida un RFC con el SAT.
        
        Args:
            rfc: RFC a validar
            include_blacklist_check: Incluir verificación de lista negra
            
        Returns:
            Dict con resultado de validación
        """
        try:
            # Validar formato RFC
            if not self._is_valid_rfc_format(rfc):
                return {
                    'success': False,
                    'error': 'Formato de RFC inválido',
                    'rfc': rfc,
                    'validation_date': datetime.now().isoformat()
                }
            
            # Verificar estado en SAT
            sat_status = self._check_sat_status(rfc)
            
            # Verificar lista negra (si está habilitado)
            blacklist_status = None
            if include_blacklist_check:
                blacklist_status = self._check_blacklist(rfc)
            
            # Determinar si el RFC es válido para operaciones
            is_valid_for_operations = (
                sat_status.get('status') == 'active' and
                (blacklist_status is None or blacklist_status.get('is_blacklisted') == False)
            )
            
            return {
                'success': True,
                'rfc': rfc,
                'sat_status': sat_status,
                'blacklist_status': blacklist_status,
                'is_valid_for_operations': is_valid_for_operations,
                'validation_date': datetime.now().isoformat(),
                'recommendations': self._generate_validation_recommendations(
                    sat_status, blacklist_status
                )
            }
            
        except Exception as e:
            logger.error(f"Error validando RFC {rfc}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'rfc': rfc,
                'validation_date': datetime.now().isoformat()
            }
    
    def validate_provider(
        self,
        provider: Person,
        validate_rfc: bool = True,
        validate_fiscal_data: bool = True
    ) -> Dict[str, Any]:
        """
        Valida un proveedor completo.
        
        Args:
            provider: Proveedor a validar
            validate_rfc: Validar RFC
            validate_fiscal_data: Validar datos fiscales
            
        Returns:
            Dict con resultado de validación
        """
        try:
            validation_results = {
                'provider_id': provider.id,
                'provider_name': provider.name,
                'validation_date': datetime.now().isoformat(),
                'overall_status': 'pending',
                'details': {}
            }
            
            # Validar RFC
            if validate_rfc and provider.rfc:
                rfc_validation = self.validate_rfc(provider.rfc)
                validation_results['details']['rfc_validation'] = rfc_validation
                
                if not rfc_validation.get('success') or not rfc_validation.get('is_valid_for_operations'):
                    validation_results['overall_status'] = 'failed'
                    validation_results['blocking_issues'] = ['RFC inválido o en lista negra']
            
            # Validar datos fiscales
            if validate_fiscal_data:
                fiscal_validation = self._validate_fiscal_data(provider)
                validation_results['details']['fiscal_validation'] = fiscal_validation
                
                if not fiscal_validation.get('is_complete'):
                    validation_results['overall_status'] = 'warning'
                    if 'blocking_issues' not in validation_results:
                        validation_results['blocking_issues'] = []
                    validation_results['blocking_issues'].append('Datos fiscales incompletos')
            
            # Determinar estado final
            if validation_results['overall_status'] == 'pending':
                validation_results['overall_status'] = 'passed'
            
            # Generar recomendaciones
            validation_results['recommendations'] = self._generate_provider_recommendations(
                validation_results
            )
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validando proveedor {provider.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider_id': provider.id,
                'validation_date': datetime.now().isoformat()
            }
    
    def check_payment_eligibility(
        self,
        provider: Person,
        payment_amount: float
    ) -> Dict[str, Any]:
        """
        Verifica si un proveedor es elegible para recibir pagos.
        
        Args:
            provider: Proveedor a verificar
            payment_amount: Monto del pago
            
        Returns:
            Dict con resultado de elegibilidad
        """
        try:
            # Validar proveedor
            provider_validation = self.validate_provider(provider)
            
            if provider_validation['overall_status'] != 'passed':
                return {
                    'success': False,
                    'eligible': False,
                    'reason': 'Proveedor no validado correctamente',
                    'validation_details': provider_validation
                }
            
            # Verificar límites de pago
            payment_limits = self._check_payment_limits(provider, payment_amount)
            
            # Verificar frecuencia de pagos
            payment_frequency = self._check_payment_frequency(provider)
            
            # Determinar elegibilidad
            is_eligible = (
                payment_limits['within_limits'] and
                payment_frequency['allowed']
            )
            
            return {
                'success': True,
                'eligible': is_eligible,
                'provider_validation': provider_validation,
                'payment_limits': payment_limits,
                'payment_frequency': payment_frequency,
                'recommendations': self._generate_payment_recommendations(
                    provider_validation, payment_limits, payment_frequency
                )
            }
            
        except Exception as e:
            logger.error(f"Error verificando elegibilidad de pago: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _is_valid_rfc_format(self, rfc: str) -> bool:
        """Valida el formato del RFC."""
        if not rfc:
            return False
        
        # RFC para personas físicas: 4 letras + 6 números + 3 alfanuméricos
        # RFC para personas morales: 3 letras + 6 números + 3 alfanuméricos
        import re
        
        rfc_pattern = r'^[A-Z&Ñ]{3,4}[0-9]{6}[A-Z0-9]{3}$'
        return bool(re.match(rfc_pattern, rfc.upper()))
    
    def _check_sat_status(self, rfc: str) -> Dict[str, Any]:
        """Verifica el estado del RFC en el SAT."""
        try:
            # Aquí implementarías la consulta real al SAT
            # Por ahora simulamos la respuesta
            
            # Simular diferentes estados
            if rfc.endswith('000'):
                return {
                    'status': 'inactive',
                    'reason': 'RFC genérico',
                    'last_updated': datetime.now().isoformat()
                }
            elif rfc.startswith('XAXX'):
                return {
                    'status': 'inactive',
                    'reason': 'RFC público',
                    'last_updated': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'active',
                    'reason': 'RFC válido',
                    'last_updated': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error consultando estado SAT: {str(e)}")
            return {
                'status': 'unknown',
                'reason': 'Error en consulta',
                'last_updated': datetime.now().isoformat()
            }
    
    def _check_blacklist(self, rfc: str) -> Dict[str, Any]:
        """Verifica si el RFC está en lista negra."""
        try:
            # Aquí implementarías la consulta a la lista negra del SAT
            # Por ahora simulamos la respuesta
            
            # Simular algunos RFCs en lista negra
            blacklisted_rfcs = [
                'ABC123456789',
                'DEF987654321'
            ]
            
            is_blacklisted = rfc.upper() in blacklisted_rfcs
            
            return {
                'is_blacklisted': is_blacklisted,
                'blacklist_reason': 'RFC con problemas fiscales' if is_blacklisted else None,
                'check_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error verificando lista negra: {str(e)}")
            return {
                'is_blacklisted': False,
                'error': str(e),
                'check_date': datetime.now().isoformat()
            }
    
    def _validate_fiscal_data(self, provider: Person) -> Dict[str, Any]:
        """Valida los datos fiscales del proveedor."""
        required_fields = [
            'rfc', 'fiscal_name', 'fiscal_address', 'fiscal_regime'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(provider, field, None):
                missing_fields.append(field)
        
        return {
            'is_complete': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'completeness_percentage': ((len(required_fields) - len(missing_fields)) / len(required_fields)) * 100
        }
    
    def _check_payment_limits(self, provider: Person, payment_amount: float) -> Dict[str, Any]:
        """Verifica límites de pago para el proveedor."""
        # Obtener límites del proveedor
        provider_limits = getattr(provider, 'payment_limits', {}) or {}
        
        max_single_payment = provider_limits.get('max_single_payment', 100000)
        max_monthly_payment = provider_limits.get('max_monthly_payment', 500000)
        
        # Verificar límite de pago único
        within_single_limit = payment_amount <= max_single_payment
        
        # Verificar límite mensual (simulado)
        current_monthly_total = 0  # Aquí obtendrías el total del mes
        within_monthly_limit = (current_monthly_total + payment_amount) <= max_monthly_payment
        
        return {
            'within_limits': within_single_limit and within_monthly_limit,
            'max_single_payment': max_single_payment,
            'max_monthly_payment': max_monthly_payment,
            'current_monthly_total': current_monthly_total,
            'payment_amount': payment_amount,
            'single_limit_exceeded': not within_single_limit,
            'monthly_limit_exceeded': not within_monthly_limit
        }
    
    def _check_payment_frequency(self, provider: Person) -> Dict[str, Any]:
        """Verifica frecuencia de pagos al proveedor."""
        # Obtener configuración de frecuencia
        frequency_config = getattr(provider, 'payment_frequency_config', {}) or {}
        
        max_payments_per_month = frequency_config.get('max_payments_per_month', 10)
        min_days_between_payments = frequency_config.get('min_days_between_payments', 1)
        
        # Simular verificación de frecuencia
        payments_this_month = 0  # Aquí obtendrías el conteo real
        days_since_last_payment = 30  # Aquí obtendrías los días reales
        
        return {
            'allowed': (
                payments_this_month < max_payments_per_month and
                days_since_last_payment >= min_days_between_payments
            ),
            'max_payments_per_month': max_payments_per_month,
            'min_days_between_payments': min_days_between_payments,
            'payments_this_month': payments_this_month,
            'days_since_last_payment': days_since_last_payment
        }
    
    def _generate_validation_recommendations(
        self,
        sat_status: Dict[str, Any],
        blacklist_status: Optional[Dict[str, Any]]
    ) -> list:
        """Genera recomendaciones basadas en la validación."""
        recommendations = []
        
        if sat_status.get('status') != 'active':
            recommendations.append('RFC inactivo en SAT - verificar estado fiscal')
        
        if blacklist_status and blacklist_status.get('is_blacklisted'):
            recommendations.append('RFC en lista negra - NO realizar operaciones')
        
        if not recommendations:
            recommendations.append('RFC válido para operaciones')
        
        return recommendations
    
    def _generate_provider_recommendations(self, validation_results: Dict[str, Any]) -> list:
        """Genera recomendaciones para el proveedor."""
        recommendations = []
        
        if validation_results['overall_status'] == 'failed':
            recommendations.append('NO realizar operaciones hasta resolver problemas')
        
        if validation_results['overall_status'] == 'warning':
            recommendations.append('Completar datos fiscales faltantes')
        
        fiscal_validation = validation_results['details'].get('fiscal_validation', {})
        if fiscal_validation.get('missing_fields'):
            recommendations.append(f"Completar campos: {', '.join(fiscal_validation['missing_fields'])}")
        
        return recommendations
    
    def _generate_payment_recommendations(
        self,
        provider_validation: Dict[str, Any],
        payment_limits: Dict[str, Any],
        payment_frequency: Dict[str, Any]
    ) -> list:
        """Genera recomendaciones para pagos."""
        recommendations = []
        
        if not provider_validation.get('eligible', True):
            recommendations.append('Proveedor no elegible para pagos')
        
        if payment_limits.get('single_limit_exceeded'):
            recommendations.append('Dividir pago en múltiples transacciones')
        
        if payment_limits.get('monthly_limit_exceeded'):
            recommendations.append('Esperar al siguiente mes para realizar pago')
        
        if not payment_frequency.get('allowed'):
            recommendations.append('Esperar días mínimos entre pagos')
        
        return recommendations
    
    def get_validation_history(self, provider: Person) -> Dict[str, Any]:
        """
        Obtiene historial de validaciones del proveedor.
        
        Args:
            provider: Proveedor
            
        Returns:
            Dict con historial de validaciones
        """
        try:
            # Aquí implementarías la lógica para obtener historial
            # Por ahora retornamos datos simulados
            
            return {
                'success': True,
                'provider_id': provider.id,
                'validation_history': [
                    {
                        'date': datetime.now().isoformat(),
                        'status': 'passed',
                        'validated_by': 'system',
                        'details': 'Validación automática'
                    }
                ],
                'total_validations': 1,
                'last_validation_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de validaciones: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            } 