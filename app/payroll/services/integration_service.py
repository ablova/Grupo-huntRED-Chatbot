"""
Servicio de Integración huntRED®
Integración completa con ATS, banking gateways y sistemas externos
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from ..models import PayrollEmployee, PayrollCompany, PayrollCalculation
from .authority_integration_service import AuthorityIntegrationService
from .severance_calculation_service import SeveranceCalculationService
from .workplace_climate_service import WorkplaceClimateService

logger = logging.getLogger(__name__)


class IntegrationService:
    """
    Servicio de integración con sistemas externos
    """
    
    def __init__(self, company: PayrollCompany):
        self.company = company
        self.authority_service = AuthorityIntegrationService(company)
        self.climate_service = WorkplaceClimateService(company)
    
    def sync_ats_data(self) -> Dict[str, Any]:
        """
        Sincroniza datos con el sistema ATS
        
        Returns:
            Resultado de la sincronización
        """
        try:
            # Buscar candidatos en ATS que puedan ser empleados
            ats_candidates = self._get_ats_candidates()
            
            # Buscar empleados que puedan ser candidatos (dados de baja)
            terminated_employees = self._get_terminated_employees()
            
            # Crear empleados desde candidatos
            created_employees = []
            for candidate in ats_candidates:
                if self._should_create_employee(candidate):
                    employee = self._create_employee_from_candidate(candidate)
                    if employee:
                        created_employees.append(employee)
            
            # Crear candidatos desde empleados terminados
            created_candidates = []
            for employee in terminated_employees:
                if self._should_create_candidate(employee):
                    candidate = self._create_candidate_from_employee(employee)
                    if candidate:
                        created_candidates.append(candidate)
            
            return {
                'success': True,
                'ats_candidates_found': len(ats_candidates),
                'terminated_employees_found': len(terminated_employees),
                'employees_created': len(created_employees),
                'candidates_created': len(created_candidates),
                'sync_date': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sincronizando con ATS: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def detect_position_needs(self) -> Dict[str, Any]:
        """
        Detecta inteligentemente cuando se necesitan nuevas posiciones
        
        Returns:
            Análisis de necesidades de posiciones
        """
        try:
            needs = []
            
            # Analizar carga de trabajo por departamento
            departments = self._analyze_workload_by_department()
            
            for dept, data in departments.items():
                if data['workload_ratio'] > 1.2:  # 20% sobrecarga
                    needs.append({
                        'type': 'workload_overflow',
                        'department': dept,
                        'current_employees': data['employee_count'],
                        'recommended_employees': data['recommended_employees'],
                        'workload_ratio': data['workload_ratio'],
                        'priority': 'high' if data['workload_ratio'] > 1.5 else 'medium',
                        'description': f'Departamento {dept} con {data["workload_ratio"]:.1%} de sobrecarga'
                    })
            
            # Analizar rotación por posición
            turnover_analysis = self._analyze_turnover_by_position()
            
            for position, data in turnover_analysis.items():
                if data['turnover_rate'] > 0.3:  # 30% rotación
                    needs.append({
                        'type': 'high_turnover',
                        'position': position,
                        'turnover_rate': data['turnover_rate'],
                        'priority': 'high',
                        'description': f'Posición {position} con {data["turnover_rate"]:.1%} de rotación'
                    })
            
            # Analizar crecimiento del negocio
            growth_needs = self._analyze_business_growth_needs()
            needs.extend(growth_needs)
            
            return {
                'success': True,
                'total_needs': len(needs),
                'high_priority': len([n for n in needs if n['priority'] == 'high']),
                'medium_priority': len([n for n in needs if n['priority'] == 'medium']),
                'needs': needs,
                'analysis_date': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error detectando necesidades de posiciones: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_employee_termination(self, employee: PayrollEmployee, 
                                   termination_date: date, 
                                   termination_type: str = 'voluntary',
                                   create_candidate: bool = True) -> Dict[str, Any]:
        """
        Procesa terminación de empleado con integración completa
        
        Args:
            employee: Empleado a terminar
            termination_date: Fecha de terminación
            termination_type: Tipo de terminación
            create_candidate: Si crear candidato en ATS
            
        Returns:
            Resultado del procesamiento
        """
        try:
            with transaction.atomic():
                # 1. Calcular finiquito/liquidación
                severance_service = SeveranceCalculationService(employee)
                severance_calculation = severance_service.calculate_severance(
                    termination_date, termination_type
                )
                
                if not severance_calculation['success']:
                    raise ValidationError(f"Error calculando finiquito: {severance_calculation['error']}")
                
                # 2. Dar de baja en autoridades
                authority_results = self.authority_service.unregister_employee(
                    employee, termination_date
                )
                
                # 3. Actualizar estado del empleado
                employee.termination_date = termination_date
                employee.termination_type = termination_type
                employee.is_active = False
                employee.save()
                
                # 4. Crear candidato en ATS si se solicita
                candidate_created = None
                if create_candidate:
                    candidate_created = self._create_candidate_from_employee(employee)
                
                # 5. Generar reportes
                reports = self._generate_termination_reports(employee, severance_calculation)
                
                return {
                    'success': True,
                    'employee_name': employee.get_full_name(),
                    'termination_date': termination_date.isoformat(),
                    'termination_type': termination_type,
                    'severance_calculation': severance_calculation,
                    'authority_results': authority_results,
                    'candidate_created': candidate_created is not None,
                    'reports_generated': len(reports),
                    'total_to_pay': severance_calculation['totals']['total_to_pay'],
                    'processing_date': timezone.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error procesando terminación de {employee.get_full_name()}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def integrate_banking_gateways(self, payroll_calculation: PayrollCalculation) -> Dict[str, Any]:
        """
        Integra con gateways bancarios para pago de nómina
        
        Args:
            payroll_calculation: Cálculo de nómina a pagar
            
        Returns:
            Resultado de la integración bancaria
        """
        try:
            # Obtener configuración bancaria de la empresa
            banking_config = self.company.banking_integration
            
            if not banking_config or not banking_config.get('enabled', False):
                return {
                    'success': False,
                    'error': 'Integración bancaria no configurada'
                }
            
            # Preparar datos para transferencia
            transfer_data = self._prepare_bank_transfer_data(payroll_calculation)
            
            # Ejecutar transferencia según gateway
            gateway = banking_config.get('gateway', 'bbva')
            
            if gateway == 'bbva':
                result = self._execute_bbva_transfer(transfer_data)
            elif gateway == 'santander':
                result = self._execute_santander_transfer(transfer_data)
            elif gateway == 'banamex':
                result = self._execute_banamex_transfer(transfer_data)
            elif gateway == 'banorte':
                result = self._execute_banorte_transfer(transfer_data)
            else:
                return {
                    'success': False,
                    'error': f'Gateway bancario {gateway} no soportado'
                }
            
            # Actualizar estado del cálculo
            if result['success']:
                payroll_calculation.payment_status = 'paid'
                payroll_calculation.payment_date = timezone.now()
                payroll_calculation.bank_reference = result.get('reference', '')
                payroll_calculation.save()
            
            return result
            
        except Exception as e:
            logger.error(f"Error integrando con gateway bancario: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_comprehensive_reports(self, report_type: str = 'monthly') -> Dict[str, Any]:
        """
        Genera reportes integrales del sistema
        
        Args:
            report_type: Tipo de reporte ('monthly', 'quarterly', 'annual')
            
        Returns:
            Reportes generados
        """
        try:
            reports = {}
            
            # Reporte de nómina
            payroll_report = self._generate_payroll_report(report_type)
            reports['payroll'] = payroll_report
            
            # Reporte de clima laboral
            climate_report = self._generate_climate_report(report_type)
            reports['workplace_climate'] = climate_report
            
            # Reporte de autoridades
            authority_report = self._generate_authority_report(report_type)
            reports['authority_integration'] = authority_report
            
            # Reporte de integración ATS
            ats_report = self._generate_ats_integration_report(report_type)
            reports['ats_integration'] = ats_report
            
            # Reporte financiero
            financial_report = self._generate_financial_report(report_type)
            reports['financial'] = financial_report
            
            return {
                'success': True,
                'report_type': report_type,
                'reports': reports,
                'generation_date': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generando reportes: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_ats_candidates(self) -> List[Dict[str, Any]]:
        """Obtiene candidatos del sistema ATS"""
        # Aquí se implementaría la integración real con el ATS
        # Por ahora simulamos datos
        
        return [
            {
                'id': 'candidate_001',
                'name': 'Juan Pérez',
                'email': 'juan.perez@email.com',
                'phone': '+525512345678',
                'position': 'Desarrollador Senior',
                'status': 'hired',
                'hire_date': date.today().isoformat(),
                'salary_expectation': 25000
            },
            {
                'id': 'candidate_002',
                'name': 'María García',
                'email': 'maria.garcia@email.com',
                'phone': '+525598765432',
                'position': 'Analista de RH',
                'status': 'hired',
                'hire_date': date.today().isoformat(),
                'salary_expectation': 18000
            }
        ]
    
    def _get_terminated_employees(self) -> List[PayrollEmployee]:
        """Obtiene empleados terminados recientemente"""
        return PayrollEmployee.objects.filter(
            company=self.company,
            is_active=False,
            termination_date__gte=date.today() - timedelta(days=30)
        )
    
    def _should_create_employee(self, candidate: Dict[str, Any]) -> bool:
        """Determina si un candidato debe convertirse en empleado"""
        return candidate.get('status') == 'hired'
    
    def _should_create_candidate(self, employee: PayrollEmployee) -> bool:
        """Determina si un empleado terminado debe convertirse en candidato"""
        # Solo si no fue por causa grave
        return employee.termination_type not in ['serious_misconduct', 'criminal']
    
    def _create_employee_from_candidate(self, candidate: Dict[str, Any]) -> Optional[PayrollEmployee]:
        """Crea empleado desde candidato del ATS"""
        try:
            employee = PayrollEmployee.objects.create(
                company=self.company,
                first_name=candidate['name'].split()[0],
                last_name=' '.join(candidate['name'].split()[1:]),
                email=candidate['email'],
                phone=candidate['phone'],
                position=candidate['position'],
                monthly_salary=candidate['salary_expectation'],
                hire_date=date.fromisoformat(candidate['hire_date']),
                employee_type='full_time',
                department=self._map_position_to_department(candidate['position'])
            )
            
            logger.info(f"Empleado creado desde candidato ATS: {employee.get_full_name()}")
            return employee
            
        except Exception as e:
            logger.error(f"Error creando empleado desde candidato: {str(e)}")
            return None
    
    def _create_candidate_from_employee(self, employee: PayrollEmployee) -> Optional[Dict[str, Any]]:
        """Crea candidato en ATS desde empleado terminado"""
        try:
            # Aquí se implementaría la creación real en el ATS
            candidate_data = {
                'id': f'candidate_{employee.id}',
                'name': employee.get_full_name(),
                'email': employee.email,
                'phone': employee.phone,
                'position': employee.position,
                'status': 'available',
                'previous_company': self.company.name,
                'previous_salary': float(employee.monthly_salary),
                'termination_date': employee.termination_date.isoformat(),
                'skills': self._extract_employee_skills(employee)
            }
            
            logger.info(f"Candidato creado en ATS desde empleado: {employee.get_full_name()}")
            return candidate_data
            
        except Exception as e:
            logger.error(f"Error creando candidato desde empleado: {str(e)}")
            return None
    
    def _map_position_to_department(self, position: str) -> str:
        """Mapea posición a departamento"""
        position_lower = position.lower()
        
        if any(word in position_lower for word in ['desarrollador', 'programador', 'ingeniero']):
            return 'IT'
        elif any(word in position_lower for word in ['analista', 'rh', 'recursos']):
            return 'HR'
        elif any(word in position_lower for word in ['contador', 'financiero', 'contabilidad']):
            return 'Finance'
        elif any(word in position_lower for word in ['vendedor', 'ventas', 'comercial']):
            return 'Sales'
        else:
            return 'General'
    
    def _extract_employee_skills(self, employee: PayrollEmployee) -> List[str]:
        """Extrae habilidades del empleado"""
        # Implementar extracción de habilidades desde el perfil del empleado
        return ['Leadership', 'Communication', 'Problem Solving']
    
    def _analyze_workload_by_department(self) -> Dict[str, Any]:
        """Analiza carga de trabajo por departamento"""
        departments = {}
        
        # Obtener empleados por departamento
        for employee in self.company.employees.filter(is_active=True):
            dept = employee.department
            if dept not in departments:
                departments[dept] = {
                    'employee_count': 0,
                    'total_salary': 0,
                    'workload_score': 0
                }
            
            departments[dept]['employee_count'] += 1
            departments[dept]['total_salary'] += float(employee.monthly_salary)
        
        # Calcular ratios de carga de trabajo
        for dept, data in departments.items():
            # Simular cálculo de carga de trabajo
            data['workload_ratio'] = 1.0 + (data['employee_count'] * 0.1)
            data['recommended_employees'] = max(1, int(data['employee_count'] * 1.2))
        
        return departments
    
    def _analyze_turnover_by_position(self) -> Dict[str, Any]:
        """Analiza rotación por posición"""
        positions = {}
        
        # Obtener empleados terminados por posición
        terminated_employees = PayrollEmployee.objects.filter(
            company=self.company,
            is_active=False,
            termination_date__gte=date.today() - timedelta(days=365)
        )
        
        for employee in terminated_employees:
            position = employee.position
            if position not in positions:
                positions[position] = {
                    'terminated_count': 0,
                    'total_count': 0
                }
            
            positions[position]['terminated_count'] += 1
        
        # Calcular tasas de rotación
        for position, data in positions.items():
            current_employees = self.company.employees.filter(
                position=position,
                is_active=True
            ).count()
            
            data['total_count'] = data['terminated_count'] + current_employees
            data['turnover_rate'] = data['terminated_count'] / data['total_count'] if data['total_count'] > 0 else 0
        
        return positions
    
    def _analyze_business_growth_needs(self) -> List[Dict[str, Any]]:
        """Analiza necesidades por crecimiento del negocio"""
        needs = []
        
        # Simular análisis de crecimiento
        # En implementación real, se analizarían métricas de negocio
        
        return needs
    
    def _prepare_bank_transfer_data(self, payroll_calculation: PayrollCalculation) -> Dict[str, Any]:
        """Prepara datos para transferencia bancaria"""
        employees_data = []
        
        for employee_calculation in payroll_calculation.employee_calculations.all():
            employees_data.append({
                'employee_name': employee_calculation.employee.get_full_name(),
                'account_number': employee_calculation.employee.bank_account,
                'amount': float(employee_calculation.net_amount),
                'description': f'Nómina {payroll_calculation.period.name}'
            })
        
        return {
            'company_account': self.company.banking_integration.get('account_number'),
            'total_amount': float(payroll_calculation.total_amount),
            'employees': employees_data,
            'reference': f'PAYROLL_{payroll_calculation.period.name}_{timezone.now().strftime("%Y%m%d")}'
        }
    
    def _execute_bbva_transfer(self, transfer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta transferencia a través de BBVA"""
        # Implementar integración real con BBVA
        return {
            'success': True,
            'reference': f'BBVA_{timezone.now().strftime("%Y%m%d%H%M%S")}',
            'message': 'Transferencia ejecutada exitosamente'
        }
    
    def _execute_santander_transfer(self, transfer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta transferencia a través de Santander"""
        # Implementar integración real con Santander
        return {
            'success': True,
            'reference': f'SANT_{timezone.now().strftime("%Y%m%d%H%M%S")}',
            'message': 'Transferencia ejecutada exitosamente'
        }
    
    def _execute_banamex_transfer(self, transfer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta transferencia a través de Banamex"""
        # Implementar integración real con Banamex
        return {
            'success': True,
            'reference': f'BNAM_{timezone.now().strftime("%Y%m%d%H%M%S")}',
            'message': 'Transferencia ejecutada exitosamente'
        }
    
    def _execute_banorte_transfer(self, transfer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta transferencia a través de Banorte"""
        # Implementar integración real con Banorte
        return {
            'success': True,
            'reference': f'BANORTE_{timezone.now().strftime("%Y%m%d%H%M%S")}',
            'message': 'Transferencia ejecutada exitosamente'
        }
    
    def _generate_termination_reports(self, employee: PayrollEmployee, 
                                    severance_calculation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera reportes de terminación"""
        reports = []
        
        # Reporte de finiquito
        severance_report = {
            'type': 'severance_calculation',
            'employee_name': employee.get_full_name(),
            'content': severance_calculation,
            'format': 'json'
        }
        reports.append(severance_report)
        
        # Reporte de autoridad
        authority_report = {
            'type': 'authority_notification',
            'employee_name': employee.get_full_name(),
            'content': f'Empleado dado de baja en autoridades fiscales',
            'format': 'txt'
        }
        reports.append(authority_report)
        
        return reports
    
    def _generate_payroll_report(self, report_type: str) -> Dict[str, Any]:
        """Genera reporte de nómina"""
        # Implementar generación de reporte de nómina
        return {
            'type': 'payroll',
            'period': report_type,
            'total_employees': self.company.employees.filter(is_active=True).count(),
            'total_payroll': 0,  # Calcular total real
            'generated_date': timezone.now().isoformat()
        }
    
    def _generate_climate_report(self, report_type: str) -> Dict[str, Any]:
        """Genera reporte de clima laboral"""
        climate_analysis = self.climate_service.analyze_workplace_climate()
        
        return {
            'type': 'workplace_climate',
            'period': report_type,
            'overall_score': climate_analysis.get('overall_score', 0),
            'risks_detected': climate_analysis.get('risk_analysis', {}).get('total_risks', 0),
            'generated_date': timezone.now().isoformat()
        }
    
    def _generate_authority_report(self, report_type: str) -> Dict[str, Any]:
        """Genera reporte de integración con autoridades"""
        # Implementar reporte de autoridades
        return {
            'type': 'authority_integration',
            'period': report_type,
            'operations_count': 0,  # Calcular operaciones reales
            'success_rate': 1.0,
            'generated_date': timezone.now().isoformat()
        }
    
    def _generate_ats_integration_report(self, report_type: str) -> Dict[str, Any]:
        """Genera reporte de integración ATS"""
        # Implementar reporte de ATS
        return {
            'type': 'ats_integration',
            'period': report_type,
            'candidates_created': 0,
            'employees_created': 0,
            'generated_date': timezone.now().isoformat()
        }
    
    def _generate_financial_report(self, report_type: str) -> Dict[str, Any]:
        """Genera reporte financiero"""
        # Implementar reporte financiero
        return {
            'type': 'financial',
            'period': report_type,
            'total_payroll_cost': 0,
            'benefits_cost': 0,
            'taxes_paid': 0,
            'generated_date': timezone.now().isoformat()
        } 