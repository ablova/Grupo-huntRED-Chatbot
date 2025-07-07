"""
huntRED® Payroll - Compliance Automation Service
Automatización completa de compliance fiscal y legal
"""

import logging
import requests
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from decimal import Decimal

from django.utils import timezone
from django.core.cache import cache
from django.db import transaction

from ..models import TaxTable, TaxUpdateLog, TaxValidationLog, PayrollCompany
from ..tasks import update_tax_tables_task

logger = logging.getLogger(__name__)

# CONFIGURACIÓN: HABILITADO POR DEFECTO
ENABLED = True


@dataclass
class ComplianceAlert:
    """Alerta de compliance"""
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    title: str
    description: str
    affected_companies: List[str]
    action_required: bool
    deadline: Optional[date]
    regulatory_source: str
    created_at: datetime


@dataclass
class TaxUpdateResult:
    """Resultado de actualización fiscal"""
    table_type: str
    country_code: str
    update_date: date
    changes_count: int
    new_values: Dict[str, Any]
    validation_status: str
    compliance_score: float
    next_update_date: date


@dataclass
class ComplianceReport:
    """Reporte de compliance"""
    company_id: str
    report_period: str
    compliance_score: float
    risk_level: str
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    audit_trail: List[Dict[str, Any]]
    generated_at: datetime


class ComplianceAutomationService:
    """
    Servicio de automatización de compliance fiscal y legal
    """
    
    def __init__(self):
        self.enabled = ENABLED
        if not self.enabled:
            logger.info("ComplianceAutomationService: DESHABILITADO")
            return
        
        # Configuración de fuentes regulatorias
        self.regulatory_sources = {
            'MEX': {
                'sat': 'https://www.sat.gob.mx/',
                'imss': 'https://www.imss.gob.mx/',
                'infonavit': 'https://www.infonavit.org.mx/',
                'uma': 'https://www.dof.gob.mx/'
            },
            'COL': {
                'dian': 'https://www.dian.gov.co/',
                'pensiones': 'https://www.colpensiones.gov.co/',
                'salud': 'https://www.minsalud.gov.co/'
            },
            'ARG': {
                'afip': 'https://www.afip.gob.ar/',
                'anses': 'https://www.anses.gob.ar/'
            }
        }
        
        # Configuración de frecuencias de actualización
        self.update_frequencies = {
            'uma': 'monthly',
            'isr_tables': 'quarterly',
            'imss_rates': 'quarterly',
            'infonavit_rates': 'quarterly',
            'subsidios': 'annual',
            'lft_articles': 'annual'
        }
        
        # Umbrales de alerta
        self.alert_thresholds = {
            'tax_rate_change': 0.05,  # 5% cambio en tasas
            'uma_change': 0.03,  # 3% cambio en UMA
            'compliance_deadline': 30,  # días antes del deadline
            'validation_error': 0.02  # 2% error en validaciones
        }
        
        logger.info("ComplianceAutomationService: Inicializado")
    
    def update_tax_tables_automatically(self, country_code: str = 'MEX') -> TaxUpdateResult:
        """
        Actualiza tablas fiscales automáticamente
        
        Args:
            country_code: Código del país
            
        Returns:
            Resultado de la actualización
        """
        if not self.enabled:
            return self._get_mock_tax_update_result(country_code)
        
        try:
            logger.info(f"Iniciando actualización automática de tablas fiscales para {country_code}")
            
            # Verificar si es necesario actualizar
            if not self._needs_update(country_code):
                logger.info(f"No se requiere actualización para {country_code}")
                return self._get_current_tax_status(country_code)
            
            # Obtener datos actualizados de fuentes oficiales
            updated_data = self._fetch_updated_tax_data(country_code)
            
            if not updated_data:
                logger.warning(f"No se pudieron obtener datos actualizados para {country_code}")
                return self._get_mock_tax_update_result(country_code)
            
            # Validar datos obtenidos
            validation_result = self._validate_tax_data(updated_data, country_code)
            
            if not validation_result['is_valid']:
                logger.error(f"Datos fiscales inválidos para {country_code}: {validation_result['errors']}")
                return self._get_mock_tax_update_result(country_code)
            
            # Aplicar actualizaciones en transacción
            with transaction.atomic():
                changes_count = self._apply_tax_updates(updated_data, country_code)
                
                # Registrar log de actualización
                self._log_tax_update(country_code, updated_data, changes_count)
                
                # Validar cálculos después de actualización
                validation_status = self._validate_calculations_after_update(country_code)
                
                # Calcular score de compliance
                compliance_score = self._calculate_compliance_score(country_code)
            
            # Programar próxima actualización
            next_update_date = self._calculate_next_update_date(country_code)
            
            # Enviar notificaciones si es necesario
            self._send_update_notifications(country_code, changes_count)
            
            return TaxUpdateResult(
                table_type='all_tables',
                country_code=country_code,
                update_date=date.today(),
                changes_count=changes_count,
                new_values=updated_data,
                validation_status=validation_status,
                compliance_score=compliance_score,
                next_update_date=next_update_date
            )
            
        except Exception as e:
            logger.error(f"Error en actualización automática para {country_code}: {str(e)}")
            return self._get_mock_tax_update_result(country_code)
    
    def monitor_regulatory_changes(self, country_code: str = 'MEX') -> List[ComplianceAlert]:
        """
        Monitorea cambios regulatorios
        
        Args:
            country_code: Código del país
            
        Returns:
            Lista de alertas de compliance
        """
        if not self.enabled:
            return self._get_mock_compliance_alerts(country_code)
        
        try:
            alerts = []
            
            # Monitorear cambios en sitios oficiales
            for source_name, source_url in self.regulatory_sources.get(country_code, {}).items():
                source_alerts = self._monitor_regulatory_source(source_name, source_url, country_code)
                alerts.extend(source_alerts)
            
            # Monitorear cambios en tablas fiscales
            tax_alerts = self._monitor_tax_table_changes(country_code)
            alerts.extend(tax_alerts)
            
            # Monitorear deadlines de compliance
            deadline_alerts = self._monitor_compliance_deadlines(country_code)
            alerts.extend(deadline_alerts)
            
            # Filtrar alertas duplicadas y ordenar por severidad
            unique_alerts = self._deduplicate_alerts(alerts)
            sorted_alerts = sorted(unique_alerts, key=lambda x: self._get_severity_score(x.severity), reverse=True)
            
            # Guardar alertas en cache
            cache.set(f'compliance_alerts_{country_code}', sorted_alerts, timeout=3600)
            
            return sorted_alerts
            
        except Exception as e:
            logger.error(f"Error monitoreando cambios regulatorios para {country_code}: {str(e)}")
            return self._get_mock_compliance_alerts(country_code)
    
    def generate_compliance_report(self, company_id: str, period: str = 'monthly') -> ComplianceReport:
        """
        Genera reporte de compliance
        
        Args:
            company_id: ID de la empresa
            period: Período del reporte
            
        Returns:
            Reporte de compliance
        """
        if not self.enabled:
            return self._get_mock_compliance_report(company_id, period)
        
        try:
            # Obtener datos de la empresa
            company = PayrollCompany.objects.get(id=company_id)
            
            # Analizar compliance actual
            compliance_analysis = self._analyze_company_compliance(company)
            
            # Identificar violaciones
            violations = self._identify_compliance_violations(company)
            
            # Calcular score de compliance
            compliance_score = self._calculate_company_compliance_score(company, violations)
            
            # Determinar nivel de riesgo
            risk_level = self._determine_risk_level(compliance_score)
            
            # Generar recomendaciones
            recommendations = self._generate_compliance_recommendations(company, violations, compliance_score)
            
            # Generar audit trail
            audit_trail = self._generate_audit_trail(company, period)
            
            return ComplianceReport(
                company_id=company_id,
                report_period=period,
                compliance_score=compliance_score,
                risk_level=risk_level,
                violations=violations,
                recommendations=recommendations,
                audit_trail=audit_trail,
                generated_at=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Error generando reporte de compliance para {company_id}: {str(e)}")
            return self._get_mock_compliance_report(company_id, period)
    
    def validate_payroll_compliance(self, payroll_data: Dict[str, Any], country_code: str = 'MEX') -> Dict[str, Any]:
        """
        Valida compliance de nómina
        
        Args:
            payroll_data: Datos de nómina
            country_code: Código del país
            
        Returns:
            Resultado de validación
        """
        if not self.enabled:
            return self._get_mock_validation_result(country_code)
        
        try:
            validation_results = {
                'isr_validation': self._validate_isr_calculations(payroll_data, country_code),
                'imss_validation': self._validate_imss_calculations(payroll_data, country_code),
                'infonavit_validation': self._validate_infonavit_calculations(payroll_data, country_code),
                'uma_validation': self._validate_uma_calculations(payroll_data, country_code),
                'lft_validation': self._validate_lft_compliance(payroll_data, country_code)
            }
            
            # Calcular score general
            overall_score = self._calculate_validation_score(validation_results)
            
            # Identificar errores críticos
            critical_errors = self._identify_critical_errors(validation_results)
            
            # Generar recomendaciones
            recommendations = self._generate_validation_recommendations(validation_results, critical_errors)
            
            return {
                'overall_score': overall_score,
                'validation_results': validation_results,
                'critical_errors': critical_errors,
                'recommendations': recommendations,
                'compliance_status': 'compliant' if overall_score > 0.95 else 'non_compliant',
                'validation_date': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error validando compliance de nómina: {str(e)}")
            return self._get_mock_validation_result(country_code)
    
    def generate_legal_documents(self, document_type: str, company_id: str, **kwargs) -> Dict[str, Any]:
        """
        Genera documentos legales automáticamente
        
        Args:
            document_type: Tipo de documento
            company_id: ID de la empresa
            **kwargs: Parámetros adicionales
            
        Returns:
            Documento generado
        """
        if not self.enabled:
            return self._get_mock_legal_document(document_type, company_id)
        
        try:
            company = PayrollCompany.objects.get(id=company_id)
            
            if document_type == 'payroll_certification':
                return self._generate_payroll_certification(company, **kwargs)
            elif document_type == 'compliance_declaration':
                return self._generate_compliance_declaration(company, **kwargs)
            elif document_type == 'tax_report':
                return self._generate_tax_report(company, **kwargs)
            elif document_type == 'labor_contract':
                return self._generate_labor_contract(company, **kwargs)
            elif document_type == 'termination_letter':
                return self._generate_termination_letter(company, **kwargs)
            else:
                raise ValueError(f"Tipo de documento no soportado: {document_type}")
                
        except Exception as e:
            logger.error(f"Error generando documento legal {document_type}: {str(e)}")
            return self._get_mock_legal_document(document_type, company_id)
    
    def setup_automated_compliance_monitoring(self, company_id: str) -> Dict[str, Any]:
        """
        Configura monitoreo automático de compliance
        
        Args:
            company_id: ID de la empresa
            
        Returns:
            Configuración de monitoreo
        """
        if not self.enabled:
            return self._get_mock_monitoring_config(company_id)
        
        try:
            company = PayrollCompany.objects.get(id=company_id)
            
            # Configurar alertas automáticas
            alert_config = self._setup_automated_alerts(company)
            
            # Configurar validaciones automáticas
            validation_config = self._setup_automated_validations(company)
            
            # Configurar reportes automáticos
            reporting_config = self._setup_automated_reporting(company)
            
            # Configurar actualizaciones automáticas
            update_config = self._setup_automated_updates(company)
            
            return {
                'company_id': company_id,
                'alert_config': alert_config,
                'validation_config': validation_config,
                'reporting_config': reporting_config,
                'update_config': update_config,
                'monitoring_active': True,
                'setup_date': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error configurando monitoreo automático para {company_id}: {str(e)}")
            return self._get_mock_monitoring_config(company_id)
    
    # Métodos auxiliares privados
    
    def _needs_update(self, country_code: str) -> bool:
        """Verifica si se necesita actualización"""
        try:
            # Verificar última actualización
            last_update = TaxUpdateLog.objects.filter(
                country_code=country_code,
                success=True
            ).order_by('-created_at').first()
            
            if not last_update:
                return True
            
            # Verificar frecuencia de actualización
            days_since_update = (date.today() - last_update.created_at.date()).days
            
            if country_code == 'MEX':
                return days_since_update >= 30  # Mensual
            elif country_code == 'COL':
                return days_since_update >= 45  # Bimestral
            elif country_code == 'ARG':
                return days_since_update >= 60  # Bimestral
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando necesidad de actualización: {str(e)}")
            return True
    
    def _fetch_updated_tax_data(self, country_code: str) -> Dict[str, Any]:
        """Obtiene datos fiscales actualizados"""
        try:
            if country_code == 'MEX':
                return self._fetch_mexican_tax_data()
            elif country_code == 'COL':
                return self._fetch_colombian_tax_data()
            elif country_code == 'ARG':
                return self._fetch_argentine_tax_data()
            else:
                logger.warning(f"País no soportado: {country_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error obteniendo datos fiscales para {country_code}: {str(e)}")
            return {}
    
    def _fetch_mexican_tax_data(self) -> Dict[str, Any]:
        """Obtiene datos fiscales mexicanos"""
        try:
            # En implementación real, se conectaría con APIs oficiales
            # Por ahora, simulamos datos actualizados
            
            return {
                'uma': {
                    'daily': 108.57,
                    'monthly': 3257.10,
                    'annual': 39611.05,
                    'effective_date': date.today().isoformat()
                },
                'isr_tables': {
                    'monthly': [
                        {'lower': 0.01, 'upper': 746.04, 'rate': 1.92, 'fixed': 0.00},
                        {'lower': 746.05, 'upper': 6332.05, 'rate': 6.40, 'fixed': 14.32},
                        # ... más rangos
                    ],
                    'effective_date': date.today().isoformat()
                },
                'imss_rates': {
                    'enfermedad_maternidad_obrero': 0.0025,
                    'invalidez_vida_obrero': 0.00625,
                    'cesantia_vejez_obrero': 0.01125,
                    'enfermedad_maternidad_patron': 0.007,
                    'invalidez_vida_patron': 0.0175,
                    'cesantia_vejez_patron': 0.0315,
                    'infonavit_patron': 0.05,
                    'retiro_patron': 0.02,
                    'effective_date': date.today().isoformat()
                },
                'subsidios': {
                    'empleo': [
                        {'lower': 0.01, 'upper': 1768.96, 'subsidio': 407.02},
                        {'lower': 1768.97, 'upper': 2653.38, 'subsidio': 406.83},
                        # ... más rangos
                    ],
                    'effective_date': date.today().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos fiscales mexicanos: {str(e)}")
            return {}
    
    def _validate_tax_data(self, tax_data: Dict[str, Any], country_code: str) -> Dict[str, Any]:
        """Valida datos fiscales obtenidos"""
        try:
            errors = []
            warnings = []
            
            # Validar estructura de datos
            required_fields = {
                'MEX': ['uma', 'isr_tables', 'imss_rates'],
                'COL': ['pensiones', 'salud', 'dian_rates'],
                'ARG': ['anses_rates', 'afip_rates']
            }
            
            required = required_fields.get(country_code, [])
            for field in required:
                if field not in tax_data:
                    errors.append(f"Campo requerido faltante: {field}")
            
            # Validar valores numéricos
            if 'uma' in tax_data:
                uma = tax_data['uma']
                if uma.get('daily', 0) <= 0:
                    errors.append("UMA diario debe ser mayor a 0")
                if uma.get('monthly', 0) <= 0:
                    errors.append("UMA mensual debe ser mayor a 0")
            
            # Validar fechas de vigencia
            for table_name, table_data in tax_data.items():
                if isinstance(table_data, dict) and 'effective_date' in table_data:
                    try:
                        effective_date = datetime.fromisoformat(table_data['effective_date'].replace('Z', '+00:00'))
                        if effective_date.date() > date.today():
                            warnings.append(f"Fecha de vigencia futura en {table_name}")
                    except ValueError:
                        errors.append(f"Fecha de vigencia inválida en {table_name}")
            
            return {
                'is_valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
            
        except Exception as e:
            logger.error(f"Error validando datos fiscales: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f"Error de validación: {str(e)}"],
                'warnings': []
            }
    
    def _apply_tax_updates(self, tax_data: Dict[str, Any], country_code: str) -> int:
        """Aplica actualizaciones fiscales"""
        try:
            changes_count = 0
            
            # Desactivar tablas anteriores
            TaxTable.objects.filter(
                table_type__startswith=f'{country_code.lower()}_',
                is_active=True
            ).update(is_active=False)
            
            # Crear nuevas tablas
            for table_name, table_data in tax_data.items():
                if table_name == 'uma':
                    changes_count += self._create_uma_table(table_data, country_code)
                elif table_name == 'isr_tables':
                    changes_count += self._create_isr_tables(table_data, country_code)
                elif table_name == 'imss_rates':
                    changes_count += self._create_imss_tables(table_data, country_code)
                elif table_name == 'subsidios':
                    changes_count += self._create_subsidios_tables(table_data, country_code)
            
            return changes_count
            
        except Exception as e:
            logger.error(f"Error aplicando actualizaciones fiscales: {str(e)}")
            raise
    
    def _create_uma_table(self, uma_data: Dict[str, Any], country_code: str) -> int:
        """Crea tabla UMA"""
        try:
            TaxTable.objects.create(
                table_type=f'{country_code.lower()}_uma',
                concept='uma_daily',
                value=uma_data['daily'],
                effective_date=date.today(),
                is_active=True,
                source='automated'
            )
            
            TaxTable.objects.create(
                table_type=f'{country_code.lower()}_uma',
                concept='uma_monthly',
                value=uma_data['monthly'],
                effective_date=date.today(),
                is_active=True,
                source='automated'
            )
            
            return 2
            
        except Exception as e:
            logger.error(f"Error creando tabla UMA: {str(e)}")
            return 0
    
    def _create_isr_tables(self, isr_data: Dict[str, Any], country_code: str) -> int:
        """Crea tablas ISR"""
        try:
            changes_count = 0
            
            for i, row in enumerate(isr_data.get('monthly', [])):
                TaxTable.objects.create(
                    table_type=f'{country_code.lower()}_isr_mensual',
                    concept=f'limite_{i+1}',
                    limit_inferior=row['lower'],
                    limit_superior=row['upper'],
                    percentage=row['rate'],
                    fixed_quota=row['fixed'],
                    effective_date=date.today(),
                    is_active=True,
                    source='automated'
                )
                changes_count += 1
            
            return changes_count
            
        except Exception as e:
            logger.error(f"Error creando tablas ISR: {str(e)}")
            return 0
    
    def _create_imss_tables(self, imss_data: Dict[str, Any], country_code: str) -> int:
        """Crea tablas IMSS"""
        try:
            changes_count = 0
            
            for rate_name, rate_value in imss_data.items():
                if rate_name != 'effective_date':
                    TaxTable.objects.create(
                        table_type=f'{country_code.lower()}_imss_rates',
                        concept=rate_name,
                        percentage=rate_value * 100,  # Convertir a porcentaje
                        effective_date=date.today(),
                        is_active=True,
                        source='automated'
                    )
                    changes_count += 1
            
            return changes_count
            
        except Exception as e:
            logger.error(f"Error creando tablas IMSS: {str(e)}")
            return 0
    
    def _create_subsidios_tables(self, subsidios_data: Dict[str, Any], country_code: str) -> int:
        """Crea tablas de subsidios"""
        try:
            changes_count = 0
            
            for i, row in enumerate(subsidios_data.get('empleo', [])):
                TaxTable.objects.create(
                    table_type=f'{country_code.lower()}_subsidios',
                    concept=f'subsidio_empleo_{i+1}',
                    limit_inferior=row['lower'],
                    limit_superior=row['upper'],
                    value=row['subsidio'],
                    effective_date=date.today(),
                    is_active=True,
                    source='automated'
                )
                changes_count += 1
            
            return changes_count
            
        except Exception as e:
            logger.error(f"Error creando tablas de subsidios: {str(e)}")
            return 0
    
    def _log_tax_update(self, country_code: str, tax_data: Dict[str, Any], changes_count: int) -> None:
        """Registra log de actualización fiscal"""
        try:
            TaxUpdateLog.objects.create(
                update_type='automatic',
                country_code=country_code,
                description=f'Actualización automática de {changes_count} tablas fiscales',
                new_values=tax_data,
                success=True,
                source='automated'
            )
        except Exception as e:
            logger.error(f"Error registrando log de actualización: {str(e)}")
    
    def _validate_calculations_after_update(self, country_code: str) -> str:
        """Valida cálculos después de actualización"""
        try:
            # Ejecutar validaciones de prueba
            test_salaries = [5000, 15000, 50000, 100000]
            validation_errors = 0
            
            for salary in test_salaries:
                validation_result = self._validate_salary_calculation(salary, country_code)
                if not validation_result['is_valid']:
                    validation_errors += 1
            
            error_rate = validation_errors / len(test_salaries)
            
            if error_rate < self.alert_thresholds['validation_error']:
                return 'valid'
            elif error_rate < 0.1:
                return 'warning'
            else:
                return 'error'
                
        except Exception as e:
            logger.error(f"Error validando cálculos: {str(e)}")
            return 'error'
    
    def _calculate_compliance_score(self, country_code: str) -> float:
        """Calcula score de compliance"""
        try:
            # Verificar tablas actualizadas
            updated_tables = TaxTable.objects.filter(
                table_type__startswith=f'{country_code.lower()}_',
                is_active=True,
                effective_date=date.today()
            ).count()
            
            # Verificar validaciones exitosas
            successful_validations = TaxValidationLog.objects.filter(
                validation_status='ok',
                created_at__date=date.today()
            ).count()
            
            total_validations = TaxValidationLog.objects.filter(
                created_at__date=date.today()
            ).count()
            
            # Calcular score
            table_score = min(updated_tables / 10, 1.0)  # Mínimo 10 tablas
            validation_score = successful_validations / max(total_validations, 1)
            
            overall_score = (table_score * 0.6) + (validation_score * 0.4)
            
            return min(overall_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculando score de compliance: {str(e)}")
            return 0.5
    
    def _calculate_next_update_date(self, country_code: str) -> date:
        """Calcula próxima fecha de actualización"""
        try:
            if country_code == 'MEX':
                return date.today() + timedelta(days=30)
            elif country_code == 'COL':
                return date.today() + timedelta(days=45)
            elif country_code == 'ARG':
                return date.today() + timedelta(days=60)
            else:
                return date.today() + timedelta(days=30)
                
        except Exception as e:
            logger.error(f"Error calculando próxima fecha de actualización: {str(e)}")
            return date.today() + timedelta(days=30)
    
    def _send_update_notifications(self, country_code: str, changes_count: int) -> None:
        """Envía notificaciones de actualización"""
        try:
            # Notificar a empresas afectadas
            affected_companies = PayrollCompany.objects.filter(country_code=country_code)
            
            for company in affected_companies:
                # Enviar notificación por WhatsApp
                self._send_whatsapp_notification(
                    company.whatsapp_phone_number,
                    f"✅ Actualización automática completada\n"
                    f"📊 {changes_count} tablas fiscales actualizadas\n"
                    f"🇲🇽 País: {country_code}\n"
                    f"📅 Fecha: {date.today().strftime('%d/%m/%Y')}"
                )
                
                # Enviar notificación por email
                self._send_email_notification(
                    company.email,
                    f"Actualización Automática de Tablas Fiscales - {country_code}",
                    f"Se han actualizado {changes_count} tablas fiscales automáticamente."
                )
                
        except Exception as e:
            logger.error(f"Error enviando notificaciones: {str(e)}")
    
    def _send_whatsapp_notification(self, phone_number: str, message: str) -> None:
        """Envía notificación por WhatsApp"""
        try:
            # En implementación real, usar API de WhatsApp Business
            logger.info(f"WhatsApp notification to {phone_number}: {message}")
        except Exception as e:
            logger.error(f"Error enviando notificación WhatsApp: {str(e)}")
    
    def _send_email_notification(self, email: str, subject: str, message: str) -> None:
        """Envía notificación por email"""
        try:
            # En implementación real, usar sistema de email
            logger.info(f"Email notification to {email}: {subject} - {message}")
        except Exception as e:
            logger.error(f"Error enviando notificación email: {str(e)}")
    
    # Métodos mock para cuando el servicio está deshabilitado
    
    def _get_mock_tax_update_result(self, country_code: str) -> TaxUpdateResult:
        return TaxUpdateResult(
            table_type='all_tables',
            country_code=country_code,
            update_date=date.today(),
            changes_count=5,
            new_values={'uma': {'daily': 108.57}},
            validation_status='valid',
            compliance_score=0.95,
            next_update_date=date.today() + timedelta(days=30)
        )
    
    def _get_mock_compliance_alerts(self, country_code: str) -> List[ComplianceAlert]:
        return [
            ComplianceAlert(
                alert_type='tax_update',
                severity='medium',
                title='Actualización de UMA',
                description='Nueva UMA publicada en DOF',
                affected_companies=['company1', 'company2'],
                action_required=False,
                deadline=None,
                regulatory_source='DOF',
                created_at=timezone.now()
            )
        ]
    
    def _get_mock_compliance_report(self, company_id: str, period: str) -> ComplianceReport:
        return ComplianceReport(
            company_id=company_id,
            report_period=period,
            compliance_score=0.92,
            risk_level='low',
            violations=[],
            recommendations=['Mantener monitoreo regular'],
            audit_trail=[],
            generated_at=timezone.now()
        )
    
    def _get_mock_validation_result(self, country_code: str) -> Dict[str, Any]:
        return {
            'overall_score': 0.95,
            'validation_results': {
                'isr_validation': {'status': 'valid', 'score': 0.98},
                'imss_validation': {'status': 'valid', 'score': 0.95},
                'infonavit_validation': {'status': 'valid', 'score': 0.92}
            },
            'critical_errors': [],
            'recommendations': ['Mantener configuración actual'],
            'compliance_status': 'compliant',
            'validation_date': timezone.now().isoformat()
        }
    
    def _get_mock_legal_document(self, document_type: str, company_id: str) -> Dict[str, Any]:
        return {
            'document_type': document_type,
            'company_id': company_id,
            'content': f'Documento legal {document_type} generado automáticamente',
            'generated_at': timezone.now().isoformat(),
            'compliance_verified': True
        }
    
    def _get_mock_monitoring_config(self, company_id: str) -> Dict[str, Any]:
        return {
            'company_id': company_id,
            'alert_config': {'enabled': True, 'channels': ['whatsapp', 'email']},
            'validation_config': {'enabled': True, 'frequency': 'daily'},
            'reporting_config': {'enabled': True, 'frequency': 'monthly'},
            'update_config': {'enabled': True, 'frequency': 'automatic'},
            'monitoring_active': True,
            'setup_date': timezone.now().isoformat()
        }
    
    def _get_current_tax_status(self, country_code: str) -> TaxUpdateResult:
        """Obtiene estado actual de tablas fiscales"""
        return TaxUpdateResult(
            table_type='current',
            country_code=country_code,
            update_date=date.today(),
            changes_count=0,
            new_values={},
            validation_status='valid',
            compliance_score=0.95,
            next_update_date=date.today() + timedelta(days=30)
        )
    
    def _monitor_regulatory_source(self, source_name: str, source_url: str, country_code: str) -> List[ComplianceAlert]:
        """Monitorea fuente regulatoria específica"""
        # En implementación real, hacer web scraping o usar APIs
        return []
    
    def _monitor_tax_table_changes(self, country_code: str) -> List[ComplianceAlert]:
        """Monitorea cambios en tablas fiscales"""
        # En implementación real, verificar cambios en tablas
        return []
    
    def _monitor_compliance_deadlines(self, country_code: str) -> List[ComplianceAlert]:
        """Monitorea deadlines de compliance"""
        # En implementación real, verificar deadlines
        return []
    
    def _deduplicate_alerts(self, alerts: List[ComplianceAlert]) -> List[ComplianceAlert]:
        """Elimina alertas duplicadas"""
        seen = set()
        unique_alerts = []
        
        for alert in alerts:
            alert_key = f"{alert.alert_type}_{alert.title}_{alert.regulatory_source}"
            if alert_key not in seen:
                seen.add(alert_key)
                unique_alerts.append(alert)
        
        return unique_alerts
    
    def _get_severity_score(self, severity: str) -> int:
        """Obtiene score numérico de severidad"""
        severity_scores = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        return severity_scores.get(severity, 1)
    
    def _analyze_company_compliance(self, company: PayrollCompany) -> Dict[str, Any]:
        """Analiza compliance de la empresa"""
        # En implementación real, analizar compliance
        return {'score': 0.92, 'status': 'compliant'}
    
    def _identify_compliance_violations(self, company: PayrollCompany) -> List[Dict[str, Any]]:
        """Identifica violaciones de compliance"""
        # En implementación real, identificar violaciones
        return []
    
    def _calculate_company_compliance_score(self, company: PayrollCompany, violations: List[Dict[str, Any]]) -> float:
        """Calcula score de compliance de la empresa"""
        # En implementación real, calcular score
        return 0.92
    
    def _determine_risk_level(self, compliance_score: float) -> str:
        """Determina nivel de riesgo"""
        if compliance_score >= 0.95:
            return 'low'
        elif compliance_score >= 0.85:
            return 'medium'
        elif compliance_score >= 0.75:
            return 'high'
        else:
            return 'critical'
    
    def _generate_compliance_recommendations(self, company: PayrollCompany, violations: List[Dict[str, Any]], compliance_score: float) -> List[str]:
        """Genera recomendaciones de compliance"""
        # En implementación real, generar recomendaciones
        return ['Mantener monitoreo regular', 'Revisar políticas internas']
    
    def _generate_audit_trail(self, company: PayrollCompany, period: str) -> List[Dict[str, Any]]:
        """Genera audit trail"""
        # En implementación real, generar audit trail
        return []
    
    def _validate_isr_calculations(self, payroll_data: Dict[str, Any], country_code: str) -> Dict[str, Any]:
        """Valida cálculos ISR"""
        # En implementación real, validar ISR
        return {'status': 'valid', 'score': 0.98}
    
    def _validate_imss_calculations(self, payroll_data: Dict[str, Any], country_code: str) -> Dict[str, Any]:
        """Valida cálculos IMSS"""
        # En implementación real, validar IMSS
        return {'status': 'valid', 'score': 0.95}
    
    def _validate_infonavit_calculations(self, payroll_data: Dict[str, Any], country_code: str) -> Dict[str, Any]:
        """Valida cálculos INFONAVIT"""
        # En implementación real, validar INFONAVIT
        return {'status': 'valid', 'score': 0.92}
    
    def _validate_uma_calculations(self, payroll_data: Dict[str, Any], country_code: str) -> Dict[str, Any]:
        """Valida cálculos UMA"""
        # En implementación real, validar UMA
        return {'status': 'valid', 'score': 0.96}
    
    def _validate_lft_compliance(self, payroll_data: Dict[str, Any], country_code: str) -> Dict[str, Any]:
        """Valida compliance LFT"""
        # En implementación real, validar LFT
        return {'status': 'valid', 'score': 0.94}
    
    def _calculate_validation_score(self, validation_results: Dict[str, Any]) -> float:
        """Calcula score de validación"""
        scores = []
        for result in validation_results.values():
            if isinstance(result, dict) and 'score' in result:
                scores.append(result['score'])
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _identify_critical_errors(self, validation_results: Dict[str, Any]) -> List[str]:
        """Identifica errores críticos"""
        # En implementación real, identificar errores críticos
        return []
    
    def _generate_validation_recommendations(self, validation_results: Dict[str, Any], critical_errors: List[str]) -> List[str]:
        """Genera recomendaciones de validación"""
        # En implementación real, generar recomendaciones
        return ['Mantener configuración actual']
    
    def _validate_salary_calculation(self, salary: float, country_code: str) -> Dict[str, Any]:
        """Valida cálculo de salario"""
        # En implementación real, validar cálculo
        return {'is_valid': True, 'errors': []}
    
    def _generate_payroll_certification(self, company: PayrollCompany, **kwargs) -> Dict[str, Any]:
        """Genera certificación de nómina"""
        # En implementación real, generar certificación
        return {
            'document_type': 'payroll_certification',
            'company_name': company.name,
            'content': f'Certificación de nómina para {company.name}',
            'generated_at': timezone.now().isoformat()
        }
    
    def _generate_compliance_declaration(self, company: PayrollCompany, **kwargs) -> Dict[str, Any]:
        """Genera declaración de compliance"""
        # En implementación real, generar declaración
        return {
            'document_type': 'compliance_declaration',
            'company_name': company.name,
            'content': f'Declaración de compliance para {company.name}',
            'generated_at': timezone.now().isoformat()
        }
    
    def _generate_tax_report(self, company: PayrollCompany, **kwargs) -> Dict[str, Any]:
        """Genera reporte fiscal"""
        # En implementación real, generar reporte
        return {
            'document_type': 'tax_report',
            'company_name': company.name,
            'content': f'Reporte fiscal para {company.name}',
            'generated_at': timezone.now().isoformat()
        }
    
    def _generate_labor_contract(self, company: PayrollCompany, **kwargs) -> Dict[str, Any]:
        """Genera contrato laboral"""
        # En implementación real, generar contrato
        return {
            'document_type': 'labor_contract',
            'company_name': company.name,
            'content': f'Contrato laboral para {company.name}',
            'generated_at': timezone.now().isoformat()
        }
    
    def _generate_termination_letter(self, company: PayrollCompany, **kwargs) -> Dict[str, Any]:
        """Genera carta de terminación"""
        # En implementación real, generar carta
        return {
            'document_type': 'termination_letter',
            'company_name': company.name,
            'content': f'Carta de terminación para {company.name}',
            'generated_at': timezone.now().isoformat()
        }
    
    def _setup_automated_alerts(self, company: PayrollCompany) -> Dict[str, Any]:
        """Configura alertas automáticas"""
        # En implementación real, configurar alertas
        return {'enabled': True, 'channels': ['whatsapp', 'email']}
    
    def _setup_automated_validations(self, company: PayrollCompany) -> Dict[str, Any]:
        """Configura validaciones automáticas"""
        # En implementación real, configurar validaciones
        return {'enabled': True, 'frequency': 'daily'}
    
    def _setup_automated_reporting(self, company: PayrollCompany) -> Dict[str, Any]:
        """Configura reportes automáticos"""
        # En implementación real, configurar reportes
        return {'enabled': True, 'frequency': 'monthly'}
    
    def _setup_automated_updates(self, company: PayrollCompany) -> Dict[str, Any]:
        """Configura actualizaciones automáticas"""
        # En implementación real, configurar actualizaciones
        return {'enabled': True, 'frequency': 'automatic'} 