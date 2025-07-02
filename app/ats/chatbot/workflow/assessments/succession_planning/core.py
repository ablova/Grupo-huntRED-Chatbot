"""
Módulo principal para la gestión de planes de sucesión.

Este módulo proporciona la funcionalidad central para evaluar candidatos
para planes de sucesión, identificar brechas de habilidades y generar
planes de desarrollo personalizados.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import logging
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from app.ats.chatbot.models import Employee, Position, Assessment, SuccessionPlan, SuccessionCandidate
from app.ats.chatbot.services.ml_service import MLService
from app.ats.chatbot.exceptions import InvalidAssessmentData, EmployeeNotFound, PositionNotFound

logger = logging.getLogger(__name__)

@dataclass
class SuccessionReadiness:
    """Resultado del análisis de preparación para sucesión."""
    readiness_score: float  # 0-100
    readiness_level: str     # 'Ready Now', '1-2 Years', '3-5 Years', 'Not Feasible'
    critical_gaps: List[str]
    development_areas: Dict[str, str]  # area: recomendación
    predicted_performance: Optional[float] = None  # Predicción de rendimiento 0-1
    risk_factors: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class SuccessionPlanningEngine:
    """Motor principal para la gestión de planes de sucesión."""
    
    def __init__(self, ml_service: MLService = None):
        """
        Inicializa el motor de planificación de sucesión.
        
        Args:
            ml_service: Servicio de ML para análisis predictivo
        """
        self.ml_service = ml_service or MLService()
    
    async def evaluate_candidate(
        self,
        candidate_id: str,
        position_id: str,
        assessment_data: Dict,
        org_context: Optional[Dict] = None
    ) -> Dict:
        """
        Evalúa un candidato para un plan de sucesión.
        
        Args:
            candidate_id: ID del empleado candidato
            position_id: ID del puesto objetivo
            assessment_data: Datos del assessment
            org_context: Contexto organizacional opcional
            
        Returns:
            Dict con los resultados de la evaluación
            
        Raises:
            EmployeeNotFound: Si el empleado no existe
            PositionNotFound: Si el puesto no existe
            InvalidAssessmentData: Si los datos del assessment no son válidos
        """
        try:
            # Obtener datos del candidato y el puesto
            candidate = await self._get_employee(candidate_id)
            position = await self._get_position(position_id)
            
            # Validar datos del assessment
            self._validate_assessment_data(assessment_data)
            
            # Crear o actualizar assessment
            assessment = await self._get_or_create_assessment(
                candidate, 
                position, 
                assessment_data
            )
            
            # Analizar preparación
            readiness_analysis = await self._analyze_readiness(
                candidate, 
                position, 
                assessment,
                org_context or {}
            )
            
            # Generar plan de desarrollo
            development_plan = await self._generate_development_plan(
                candidate, 
                position, 
                readiness_analysis,
                org_context or {}
            )
            
            # Evaluar riesgos
            risk_assessment = self._assess_succession_risk(
                readiness_analysis,
                org_context or {}
            )
            
            # Guardar resultados
            await self._save_succession_analysis(
                candidate,
                position,
                readiness_analysis,
                development_plan,
                risk_assessment
            )
            
            return {
                "readiness_analysis": readiness_analysis.to_dict(),
                "development_plan": development_plan,
                "risk_assessment": risk_assessment,
                "assessment_id": str(assessment.id) if assessment else None
            }
            
        except Exception as e:
            logger.error(f"Error en evaluación de sucesión: {str(e)}", exc_info=True)
            raise
    
    # Métodos auxiliares
    
    async def _get_employee(self, employee_id: str) -> Employee:
        """Obtiene un empleado por ID."""
        try:
            return await Employee.objects.aget(id=employee_id)
        except Employee.DoesNotExist:
            raise EmployeeNotFound(f"Empleado con ID {employee_id} no encontrado")
    
    async def _get_position(self, position_id: str) -> Position:
        """Obtiene un puesto por ID."""
        try:
            return await Position.objects.aget(id=position_id)
        except Position.DoesNotExist:
            raise PositionNotFound(f"Puesto con ID {position_id} no encontrado")
    
    def _validate_assessment_data(self, assessment_data: Dict):
        """Valida los datos del assessment."""
        if not assessment_data or not isinstance(assessment_data, dict):
            raise InvalidAssessmentData("Datos de assessment no válidos")
        # Aquí se pueden agregar más validaciones según sea necesario
    
    async def _get_or_create_assessment(
        self, 
        employee: Employee, 
        position: Position, 
        assessment_data: Dict
    ) -> Assessment:
        """Obtiene o crea un registro de assessment."""
        # Lógica para obtener o crear el assessment
        # Esto es un placeholder - implementar según el modelo Assessment existente
        return await Assessment.objects.acreate(
            employee=employee,
            position=position,
            data=assessment_data,
            assessment_type="succession_planning"
        )
    
    async def _analyze_readiness(
        self,
        candidate: Employee,
        position: Position,
        assessment: Assessment,
        org_context: Dict
    ) -> SuccessionReadiness:
        """Analiza la preparación del candidato para el puesto objetivo."""
        try:
            # Usar el servicio de ML para analizar la preparación
            analysis_result = await self.ml_service.analyze_succession_readiness(
                candidate_id=str(candidate.id),
                position_id=str(position.id),
                assessment_data=assessment.data,
                org_context=org_context
            )
            
            return SuccessionReadiness(
                readiness_score=analysis_result.get('readiness_score', 0),
                readiness_level=analysis_result.get('readiness_level', 'Not Feasible'),
                critical_gaps=analysis_result.get('critical_gaps', []),
                development_areas=analysis_result.get('development_areas', {}),
                predicted_performance=analysis_result.get('predicted_performance'),
                risk_factors=analysis_result.get('risk_factors', [])
            )
            
        except Exception as e:
            logger.error(f"Error en análisis de preparación: {str(e)}", exc_info=True)
            # Retornar un objeto con valores por defecto en caso de error
            return SuccessionReadiness(
                readiness_score=0,
                readiness_level='Not Feasible',
                critical_gaps=["Error en el análisis"],
                development_areas={"error": "No se pudo completar el análisis"},
                risk_factors=["Error técnico"]
            )
    
    async def _generate_development_plan(
        self,
        candidate: Employee,
        position: Position,
        readiness: SuccessionReadiness,
        org_context: Dict
    ) -> Dict:
        """Genera un plan de desarrollo personalizado."""
        # Lógica para generar un plan de desarrollo basado en las brechas identificadas
        # Esto es un ejemplo básico - se debe adaptar según los requisitos específicos
        
        development_plan = {
            "candidate_id": str(candidate.id),
            "position_id": str(position.id),
            "development_areas": [],
            "recommended_actions": [],
            "timeline_months": 12,  # Plazo por defecto de 12 meses
            "priority": "high" if readiness.readiness_level == 'Ready Now' else "medium"
        }
        
        # Agregar áreas de desarrollo basadas en las brechas críticas
        for gap in readiness.critical_gaps:
            development_plan["development_areas"].append({
                "area": gap,
                "current_level": "N/A",  # Se debería obtener del perfil del candidato
                "target_level": "N/A",   # Se debería obtener de los requisitos del puesto
                "actions": self._get_recommended_actions(gap, org_context)
            })
        
        return development_plan
    
    def _get_recommended_actions(self, gap: str, org_context: Dict) -> List[Dict]:
        """Obtiene acciones recomendadas para una brecha específica."""
        # Mapeo de brechas a acciones recomendadas
        # Esto es un ejemplo básico - se debe expandir según sea necesario
        actions_map = {
            "liderazgo": [
                {"action": "Curso de Liderazgo Estratégico", "type": "training"},
                {"action": "Mentoría con líder senior", "type": "mentoring"},
                {"action": "Asignación a proyecto de liderazgo", "type": "experience"}
            ],
            "gestión de equipos": [
                {"action": "Taller de Gestión de Equipos", "type": "training"},
                {"action": "Liderar un equipo pequeño", "type": "experience"}
            ],
            "conocimiento técnico": [
                {"action": "Certificación en área técnica relevante", "type": "certification"},
                {"action": "Proyecto en área técnica", "type": "experience"}
            ]
        }
        
        # Buscar acciones para la brecha específica
        for key, actions in actions_map.items():
            if key.lower() in gap.lower():
                return actions
        
        # Acciones por defecto si no se encuentra una coincidencia
        return [{"action": f"Desarrollar habilidades en {gap}", "type": "other"}]
    
    def _assess_succession_risk(
        self,
        readiness: SuccessionReadiness,
        org_context: Dict
    ) -> Dict:
        """Evalúa los riesgos asociados con el plan de sucesión."""
        risk_level = "low"
        risk_factors = []
        
        # Evaluar nivel de preparación
        if readiness.readiness_level == 'Not Feasible':
            risk_level = "high"
            risk_factors.append("El candidato no es viable para la posición actualmente")
        elif readiness.readiness_level == '3-5 Years':
            risk_level = "medium-high"
            risk_factors.append("Tiempo prolongado de preparación requerido")
        
        # Evaluar brechas críticas
        if readiness.critical_gaps:
            risk_level = "medium" if risk_level == "low" else risk_level
            risk_factors.append(f"{len(readiness.critical_gaps)} brechas críticas identificadas")
        
        # Evaluar rendimiento predicho
        if readiness.predicted_performance and readiness.predicted_performance < 0.7:
            risk_level = "high" if risk_level != "high" else risk_level
            risk_factors.append(f"Rendimiento predicho por debajo del umbral: {readiness.predicted_performance*100:.1f}%")
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "mitigation_strategies": self._get_mitigation_strategies(risk_level, risk_factors)
        }
    
    def _get_mitigation_strategies(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """Obtiene estrategias de mitigación basadas en el nivel de riesgo."""
        if risk_level == "high":
            return [
                "Identificar candidatos adicionales para este rol",
                "Desarrollar un plan de desarrollo intensivo",
                "Considerar contratación externa si es necesario"
            ]
        elif risk_level == "medium-high":
            return [
                "Acelerar el plan de desarrollo",
                "Asignar un mentor experimentado",
                "Monitorear el progreso mensualmente"
            ]
        elif risk_level == "medium":
            return [
                "Implementar el plan de desarrollo según lo planeado",
                "Revisar el progreso trimestralmente",
                "Ajustar el plan según sea necesario"
            ]
        else:
            return ["Continuar con el plan de desarrollo actual"]
    
    async def _save_succession_analysis(
        self,
        candidate: Employee,
        position: Position,
        readiness: SuccessionReadiness,
        development_plan: Dict,
        risk_assessment: Dict
    ) -> None:
        """Guarda el análisis de sucesión en la base de datos."""
        try:
            # Obtener o crear el plan de sucesión para el puesto
            succession_plan, created = await SuccessionPlan.objects.aget_or_create(
                position=position,
                defaults={
                    'critical_position': True,  # O determinar según lógica de negocio
                    'risk_level': risk_assessment.get('risk_level', 'medium'),
                    'last_updated': timezone.now()
                }
            )
            
            # Crear o actualizar el candidato en el plan de sucesión
            await SuccessionCandidate.objects.aupdate_or_create(
                plan=succession_plan,
                employee=candidate,
                defaults={
                    'readiness_level': readiness.readiness_level,
                    'potential_rating': int(readiness.readiness_score / 20),  # Convertir a escala 1-5
                    'development_needs': '\n'.join(readiness.critical_gaps),
                    'timeline_months': development_plan.get('timeline_months', 12),
                    'last_assessment_date': timezone.now()
                }
            )
            
            logger.info(f"Análisis de sucesión guardado para {candidate} en {position}")
            
        except Exception as e:
            logger.error(f"Error al guardar el análisis de sucesión: {str(e)}", exc_info=True)
            # No lanzamos la excepción para no interrumpir el flujo principal
            pass
