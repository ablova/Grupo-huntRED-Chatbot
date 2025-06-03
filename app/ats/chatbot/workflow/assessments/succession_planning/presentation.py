"""
Módulo de presentación para planes de sucesión.

Este módulo se encarga de generar informes y visualizaciones
para los planes de sucesión.
"""

from typing import Dict, List, Optional, Any, Union, BinaryIO
from datetime import datetime
import io
import logging

from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from ....models import SuccessionPlan, Employee, Position
from .analysis import SuccessionAnalysis

logger = logging.getLogger(__name__)

class SuccessionReportGenerator:
    """Generador de informes para planes de sucesión."""
    
    def __init__(self, org_id: Optional[str] = None):
        """
        Inicializa el generador de informes.
        
        Args:
            org_id: ID de la organización (opcional)
        """
        self.org_id = org_id
        self.analyzer = SuccessionAnalysis(org_id=org_id)
    
    async def generate_succession_report(
        self,
        report_type: str = 'overview',
        department: Optional[str] = None,
        position_id: Optional[str] = None,
        format: str = 'html'
    ) -> Union[Dict, bytes]:
        """
        Genera un informe de sucesión.
        
        Args:
            report_type: Tipo de informe ('overview', 'detailed', 'development')
            department: Departamento (opcional)
            position_id: ID del puesto (opcional)
            format: Formato de salida ('html', 'pdf')
            
        Returns:
            Dict o bytes con el informe generado
        """
        try:
            # Obtener datos según el tipo de informe
            if report_type == 'overview':
                data = await self._get_overview_data(department)
                template = 'succession/reports/overview.html'
            elif report_type == 'detailed':
                data = await self._get_detailed_data(position_id, department)
                template = 'succession/reports/detailed.html'
            elif report_type == 'development':
                data = await self._get_development_data(department)
                template = 'succession/reports/development.html'
            else:
                raise ValueError(f"Tipo de informe no válido: {report_type}")
            
            # Renderizar plantilla
            html_content = render_to_string(template, {
                'data': data,
                'report_date': timezone.now().strftime('%Y-%m-%d'),
                'org_id': self.org_id,
                'department': department,
                'position_id': position_id
            })
            
            # Devolver en el formato solicitado
            if format.lower() == 'pdf':
                return self._convert_to_pdf(html_content)
            else:
                return {'content': html_content, 'format': 'html'}
                
        except Exception as e:
            logger.error(f"Error al generar informe de sucesión: {str(e)}", exc_info=True)
            return {
                'error': f'No se pudo generar el informe: {str(e)}',
                'report_type': report_type,
                'department': department,
                'position_id': position_id
            }
    
    async def _get_overview_data(self, department: Optional[str] = None) -> Dict:
        """Obtiene datos para el informe de resumen."""
        # Obtener datos del dashboard de riesgo
        dashboard_data = await self.analyzer.get_succession_risk_dashboard(department)
        
        # Obtener datos de preparación
        readiness_data = await self.analyzer.get_readiness_breakdown(department)
        
        # Obtener necesidades de desarrollo principales
        dev_needs = await self.analyzer.get_development_needs_summary(department, min_frequency=5)
        
        return {
            'dashboard': dashboard_data,
            'readiness': readiness_data,
            'development_needs': dev_needs.get('needs', [])[:5] if 'needs' in dev_needs else []
        }
    
    async def _get_detailed_data(
        self, 
        position_id: Optional[str] = None, 
        department: Optional[str] = None
    ) -> Dict:
        """Obtiene datos para el informe detallado."""
        # Obtener datos de fortaleza del banco de talentos
        bench_strength = await self.analyzer.get_bench_strength(
            position_id=position_id,
            department=department
        )
        
        # Si se especificó un puesto, obtener detalles adicionales
        position_details = None
        if position_id:
            try:
                position = await Position.objects.aget(id=position_id)
                position_details = {
                    'id': str(position.id),
                    'title': position.title,
                    'department': position.department,
                    'description': position.description
                }
                
                # Obtener candidatos para este puesto
                candidates = []
                async for candidate in SuccessionCandidate.objects.filter(
                    plan__position_id=position_id
                ).select_related('employee'):
                    candidates.append({
                        'id': str(candidate.employee.id),
                        'name': f"{candidate.employee.first_name} {candidate.employee.last_name}",
                        'readiness_level': candidate.readiness_level,
                        'potential_rating': candidate.potential_rating,
                        'timeline_months': candidate.timeline_months,
                        'development_needs': candidate.development_needs.split('\n') if candidate.development_needs else []
                    })
                
                position_details['candidates'] = candidates
                
            except Position.DoesNotExist:
                position_details = {'error': 'Puesto no encontrado'}
        
        return {
            'bench_strength': bench_strength,
            'position': position_details,
            'department': department
        }
    
    async def _get_development_data(self, department: Optional[str] = None) -> Dict:
        """Obtiene datos para el informe de desarrollo."""
        # Obtener necesidades de desarrollo
        dev_needs = await self.analyzer.get_development_needs_summary(
            department=department,
            min_frequency=3
        )
        
        # Obtener datos de preparación por área
        readiness_by_area = {}
        if department:
            departments = [department]
        else:
            # Obtener todos los departamentos únicos con puestos críticos
            departments = await SuccessionPlan.objects.filter(
                critical_position=True
            ).values_list('position__department', flat=True).distinct().alist()
        
        for dept in departments:
            readiness = await self.analyzer.get_readiness_breakdown(department=dept)
            if 'summary' in readiness:
                readiness_by_area[dept or 'Sin departamento'] = readiness['summary']
        
        return {
            'development_needs': dev_needs,
            'readiness_by_area': readiness_by_area,
            'department': department
        }
    
    def _convert_to_pdf(self, html_content: str) -> bytes:
        """
        Convierte el contenido HTML a PDF.
        
        Args:
            html_content: Contenido HTML a convertir
            
        Returns:
            bytes con el PDF generado
        """
        try:
            # Convertir HTML a PDF usando WeasyPrint
            html = HTML(string=html_content, base_url='/')
            pdf_bytes = html.write_pdf()
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error al convertir HTML a PDF: {str(e)}", exc_info=True)
            raise ValueError(f"No se pudo generar el PDF: {str(e)}")
    
    async def generate_employee_development_plan(
        self,
        employee_id: str,
        position_id: str,
        format: str = 'pdf'
    ) -> Union[Dict, bytes]:
        """
        Genera un plan de desarrollo individual para un empleado.
        
        Args:
            employee_id: ID del empleado
            position_id: ID del puesto objetivo
            format: Formato de salida ('html', 'pdf')
            
        Returns:
            Dict o bytes con el plan de desarrollo
        """
        try:
            # Obtener datos del empleado y el puesto
            try:
                employee = await Employee.objects.aget(id=employee_id)
                position = await Position.objects.aget(id=position_id)
            except (Employee.DoesNotExist, Position.DoesNotExist) as e:
                raise ValueError("Empleado o puesto no encontrado")
            
            # Obtener datos de sucesión para este empleado y puesto
            succession_data = await self.analyzer.get_employee_succession_data(
                employee_id=employee_id,
                position_id=position_id
            )
            
            # Renderizar plantilla
            html_content = render_to_string('succession/reports/development_plan.html', {
                'employee': employee,
                'position': position,
                'succession_data': succession_data,
                'report_date': timezone.now().strftime('%Y-%m-%d')
            })
            
            # Devolver en el formato solicitado
            if format.lower() == 'pdf':
                return self._convert_to_pdf(html_content)
            else:
                return {'content': html_content, 'format': 'html'}
                
        except Exception as e:
            logger.error(f"Error al generar plan de desarrollo: {str(e)}", exc_info=True)
            return {
                'error': f'No se pudo generar el plan de desarrollo: {str(e)}',
                'employee_id': employee_id,
                'position_id': position_id
            }
    
    async def generate_succession_org_chart(
        self,
        department: Optional[str] = None,
        format: str = 'svg'
    ) -> Union[Dict, bytes]:
        """
        Genera un organigrama de sucesión.
        
        Args:
            department: Departamento (opcional)
            format: Formato de salida ('svg', 'png', 'pdf')
            
        Returns:
            Dict o bytes con el organigrama
        """
        try:
            # Obtener datos de puestos críticos y candidatos
            query = SuccessionPlan.objects.filter(critical_position=True)
            
            if department:
                query = query.filter(position__department=department)
                
            if self.org_id:
                query = query.filter(position__organization_id=self.org_id)
            
            # Obtener puestos y candidatos
            positions = []
            async for plan in query.select_related('position').prefetch_related('candidates'):
                position_data = {
                    'id': str(plan.position.id),
                    'title': plan.position.title,
                    'department': plan.position.department,
                    'candidates': []
                }
                
                async for candidate in plan.candidates.select_related('employee'):
                    position_data['candidates'].append({
                        'id': str(candidate.employee.id),
                        'name': f"{candidate.employee.first_name} {candidate.employee.last_name}",
                        'readiness_level': candidate.readiness_level,
                        'potential_rating': candidate.potential_rating
                    })
                
                positions.append(position_data)
            
            # Generar datos para el organigrama
            org_chart_data = self._prepare_org_chart_data(positions)
            
            # Renderizar plantilla
            html_content = render_to_string('succession/reports/org_chart.html', {
                'org_chart_data': org_chart_data,
                'department': department or 'Toda la organización',
                'report_date': timezone.now().strftime('%Y-%m-%d')
            })
            
            # Devolver en el formato solicitado
            if format.lower() in ('pdf', 'png'):
                return self._convert_to_pdf(html_content)
            else:
                return {'content': html_content, 'format': 'html'}
                
        except Exception as e:
            logger.error(f"Error al generar organigrama de sucesión: {str(e)}", exc_info=True)
            return {
                'error': f'No se pudo generar el organigrama: {str(e)}',
                'department': department
            }
    
    def _prepare_org_chart_data(self, positions: List[Dict]) -> Dict:
        """
        Prepara los datos para el organigrama.
        
        Args:
            positions: Lista de puestos con candidatos
            
        Returns:
            Dict con los datos formateados para el organigrama
        """
        # Esta es una implementación simplificada
        # En una implementación real, se usaría una biblioteca como mermaid.js o similar
        
        nodes = []
        links = []
        
        # Agregar nodos para puestos
        for i, position in enumerate(positions):
            node_id = f"p{i}"
            nodes.append({
                'id': node_id,
                'name': position['title'],
                'type': 'position',
                'department': position['department']
            })
            
            # Agregar nodos para candidatos
            for j, candidate in enumerate(position['candidates']):
                candidate_id = f"c{i}_{j}"
                nodes.append({
                    'id': candidate_id,
                    'name': candidate['name'],
                    'type': 'candidate',
                    'readiness_level': candidate['readiness_level'],
                    'potential_rating': candidate['potential_rating']
                })
                
                # Agregar enlace entre puesto y candidato
                links.append({
                    'source': node_id,
                    'target': candidate_id,
                    'type': 'succession'
                })
        
        return {
            'nodes': nodes,
            'links': links
        }
