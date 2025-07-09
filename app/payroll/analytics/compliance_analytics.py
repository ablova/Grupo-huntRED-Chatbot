"""
Módulo para análisis avanzado de cumplimiento normativo en nómina
Proporciona herramientas para análisis predictivo, detección de riesgos
y optimización de procesos relacionados con nómina y evaluaciones.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json

from django.utils import timezone
from django.db.models import Q, F, Count, Case, When, Value, IntegerField, Avg, Sum
from django.db import transaction, connection

from ..models import PayrollCompany, PayrollEmployee
from app.ats.chatbot.workflow.assessments.nom35.models import AssessmentNOM35, AssessmentNOM35Result
from app.models import Person, BusinessUnit

logger = logging.getLogger(__name__)

class ComplianceAnalyticsService:
    """
    Servicio para análisis avanzado de cumplimiento normativo y optimización
    de procesos relacionados con nómina y evaluaciones obligatorias.
    """
    
    def __init__(self, company: PayrollCompany = None):
        """
        Inicializa el servicio con la empresa especificada o para todas las empresas
        
        Args:
            company: Instancia de PayrollCompany (opcional, si None analiza todas)
        """
        self.company = company
        self.business_unit = company.business_unit if company else None
        
    def get_nom35_risk_analysis(self, company: Optional[PayrollCompany] = None) -> Dict[str, Any]:
        """
        Genera análisis de riesgos psicosociales basado en resultados de NOM 35
        
        Args:
            company: Empresa específica para análisis (opcional)
            
        Returns:
            Análisis detallado de riesgos por categoría
        """
        target_company = company or self.company
        
        # En implementación real, aquí analizaríamos los resultados reales de NOM 35
        # para identificar patrones y áreas de riesgo
        
        # Simular datos de análisis para demostración
        risk_categories = {
            "ambiente_trabajo": {
                "nivel": "bajo",
                "porcentaje": 22.5,
                "tendencia": "estable",
                "recomendaciones": [
                    "Mantener las políticas actuales de ambiente laboral",
                    "Continuar con evaluaciones periódicas"
                ]
            },
            "factores_organizacionales": {
                "nivel": "medio",
                "porcentaje": 45.8,
                "tendencia": "mejora",
                "recomendaciones": [
                    "Revisar cargas de trabajo",
                    "Implementar pausas activas programadas"
                ]
            },
            "liderazgo": {
                "nivel": "bajo",
                "porcentaje": 28.3,
                "tendencia": "mejora",
                "recomendaciones": [
                    "Mantener programas de desarrollo de liderazgo",
                    "Continuar con retroalimentación periódica"
                ]
            },
            "jornada_trabajo": {
                "nivel": "medio",
                "porcentaje": 39.7,
                "tendencia": "deterioro",
                "recomendaciones": [
                    "Revisar y optimizar horarios de trabajo",
                    "Implementar política de desconexión digital",
                    "Analizar horas extras recurrentes"
                ]
            },
            "violencia_acoso": {
                "nivel": "muy bajo",
                "porcentaje": 5.2,
                "tendencia": "estable",
                "recomendaciones": [
                    "Mantener canales de denuncia anónimos",
                    "Continuar con campañas de sensibilización"
                ]
            }
        }
        
        # Análisis global
        general_risk_level = self._calculate_general_risk_level(risk_categories)
        
        return {
            "company_name": target_company.name if target_company else "Todas las empresas",
            "risk_categories": risk_categories,
            "general_risk_level": general_risk_level,
            "as_of_date": timezone.now().date()
        }
    
    def _calculate_general_risk_level(self, risk_categories: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula nivel de riesgo general ponderado basado en categorías
        
        Args:
            risk_categories: Categorías de riesgo con sus niveles
            
        Returns:
            Nivel de riesgo general y recomendaciones prioritarias
        """
        risk_mapping = {
            "muy bajo": 1,
            "bajo": 2,
            "medio": 3,
            "alto": 4,
            "muy alto": 5
        }
        
        # Pesos para cada categoría (en implementación real, estos serían calibrados)
        weights = {
            "ambiente_trabajo": 0.2,
            "factores_organizacionales": 0.25,
            "liderazgo": 0.15,
            "jornada_trabajo": 0.2,
            "violencia_acoso": 0.2
        }
        
        # Calcular riesgo ponderado
        weighted_sum = 0
        for category, data in risk_categories.items():
            risk_value = risk_mapping.get(data["nivel"], 0)
            weighted_sum += risk_value * weights.get(category, 0)
        
        # Determinar nivel general
        if weighted_sum < 1.5:
            general_level = "muy bajo"
        elif weighted_sum < 2.5:
            general_level = "bajo"
        elif weighted_sum < 3.5:
            general_level = "medio"
        elif weighted_sum < 4.5:
            general_level = "alto"
        else:
            general_level = "muy alto"
        
        # Recomendaciones prioritarias (categorías con mayor riesgo)
        sorted_categories = sorted(
            risk_categories.items(), 
            key=lambda x: risk_mapping.get(x[1]["nivel"], 0),
            reverse=True
        )
        
        priority_recommendations = []
        for category, data in sorted_categories[:2]:
            for rec in data["recomendaciones"]:
                priority_recommendations.append(rec)
                
        return {
            "nivel": general_level,
            "valor_ponderado": round(weighted_sum, 2),
            "recomendaciones_prioritarias": priority_recommendations[:3]
        }
    
    def generate_compliance_forecast(self, months_ahead: int = 3) -> Dict[str, Any]:
        """
        Genera pronóstico de cumplimiento normativo para los próximos meses
        
        Args:
            months_ahead: Número de meses a pronosticar
            
        Returns:
            Pronóstico de cumplimiento con tendencias
        """
        target_company = self.company
        
        # En implementación real, utilizaríamos datos históricos para proyectar
        # tendencias futuras de cumplimiento
        
        # Simular datos de pronóstico para demostración
        current_date = timezone.now().date()
        forecast_data = []
        
        # Datos actuales (simulados)
        current_compliance = 78.5
        monthly_growth = 2.8
        seasonal_factors = [1.0, 0.9, 1.1, 1.05, 0.95, 1.0, 0.9, 0.85, 1.1, 1.15, 1.05, 0.95]
        
        # Generar pronóstico para los próximos meses
        for i in range(months_ahead):
            forecast_month = (current_date.month + i) % 12
            if forecast_month == 0:
                forecast_month = 12
                
            seasonal_factor = seasonal_factors[forecast_month - 1]
            
            # Calcular fecha del pronóstico
            forecast_date = current_date.replace(day=1)
            forecast_date = forecast_date + timedelta(days=32 * (i + 1))
            forecast_date = forecast_date.replace(day=1) - timedelta(days=1)
            
            # Calcular cumplimiento pronosticado
            forecasted_compliance = min(100, current_compliance + (monthly_growth * (i + 1) * seasonal_factor))
            
            forecast_data.append({
                "fecha": forecast_date,
                "mes": forecast_date.strftime("%B %Y"),
                "cumplimiento_pronosticado": round(forecasted_compliance, 1),
                "factor_estacional": round(seasonal_factor, 2)
            })
        
        return {
            "company_name": target_company.name if target_company else "Todas las empresas",
            "current_compliance": current_compliance,
            "forecast": forecast_data,
            "as_of_date": current_date
        }
    
    def identify_compliance_gaps(self) -> Dict[str, Any]:
        """
        Identifica brechas de cumplimiento normativo y oportunidades de mejora
        
        Returns:
            Brechas identificadas y recomendaciones
        """
        target_company = self.company
        
        # En implementación real, analizaríamos datos reales para identificar
        # las brechas de cumplimiento más significativas
        
        # Simular datos para demostración
        compliance_gaps = [
            {
                "categoria": "NOM 35",
                "cumplimiento_actual": 78.5,
                "objetivo": 95.0,
                "brecha": 16.5,
                "impacto": "alto",
                "recomendaciones": [
                    "Implementar recordatorios escalonados para evaluaciones pendientes",
                    "Ofrecer incentivos por completar evaluaciones a tiempo",
                    "Realizar sesiones breves de concientización"
                ]
            },
            {
                "categoria": "Capacitación obligatoria",
                "cumplimiento_actual": 82.3,
                "objetivo": 90.0,
                "brecha": 7.7,
                "impacto": "medio",
                "recomendaciones": [
                    "Integrar recordatorios de capacitación en el sistema de nómina",
                    "Enviar notificaciones automatizadas para cursos pendientes"
                ]
            },
            {
                "categoria": "Documentación legal",
                "cumplimiento_actual": 91.8,
                "objetivo": 100.0,
                "brecha": 8.2,
                "impacto": "alto",
                "recomendaciones": [
                    "Implementar verificación automática de documentos faltantes",
                    "Establecer flujo de trabajo para actualización periódica"
                ]
            }
        ]
        
        # Priorizar brechas por impacto y tamaño
        sorted_gaps = sorted(
            compliance_gaps,
            key=lambda x: (
                {"alto": 3, "medio": 2, "bajo": 1}.get(x["impacto"], 0),
                x["brecha"]
            ),
            reverse=True
        )
        
        return {
            "company_name": target_company.name if target_company else "Todas las empresas",
            "compliance_gaps": sorted_gaps,
            "as_of_date": timezone.now().date()
        }
    
    def optimize_assessment_scheduling(self) -> Dict[str, Any]:
        """
        Optimiza la programación de evaluaciones basado en análisis de patrones
        
        Returns:
            Recomendaciones optimizadas de programación
        """
        target_company = self.company
        
        # En implementación real, analizaríamos patrones históricos de respuesta
        # para determinar los mejores momentos para programar evaluaciones
        
        # Simular datos de análisis para demostración
        optimal_days = ["Martes", "Miércoles", "Jueves"]
        optimal_hours = ["9:00-11:00", "14:00-16:00"]
        
        compliance_by_day = {
            "Lunes": 65.3,
            "Martes": 82.7,
            "Miércoles": 85.2,
            "Jueves": 78.9,
            "Viernes": 58.4,
            "Sábado": 45.1,
            "Domingo": 32.5
        }
        
        compliance_by_hour = {
            "8:00-10:00": 72.5,
            "10:00-12:00": 68.3,
            "12:00-14:00": 45.2,
            "14:00-16:00": 76.8,
            "16:00-18:00": 65.7,
            "18:00-20:00": 52.1
        }
        
        # Generar recomendaciones específicas basadas en departamentos
        department_recommendations = {
            "Operaciones": {
                "dias_optimos": ["Martes", "Miércoles"],
                "horas_optimas": ["9:00-11:00"]
            },
            "Administración": {
                "dias_optimos": ["Miércoles", "Jueves"],
                "horas_optimas": ["14:00-16:00"]
            },
            "Ventas": {
                "dias_optimos": ["Martes", "Viernes"],
                "horas_optimas": ["16:00-18:00"]
            },
            "TI": {
                "dias_optimos": ["Lunes", "Jueves"],
                "horas_optimas": ["10:00-12:00"]
            }
        }
        
        return {
            "company_name": target_company.name if target_company else "Todas las empresas",
            "optimal_days": optimal_days,
            "optimal_hours": optimal_hours,
            "compliance_by_day": compliance_by_day,
            "compliance_by_hour": compliance_by_hour,
            "department_recommendations": department_recommendations,
            "as_of_date": timezone.now().date()
        }
    
    def export_compliance_dashboard_data(self, format: str = "json") -> str:
        """
        Exporta datos consolidados para dashboard de cumplimiento
        
        Args:
            format: Formato de exportación ("json" por defecto)
            
        Returns:
            Datos consolidados en formato especificado
        """
        # Recopilar todos los datos de análisis
        dashboard_data = {
            "risk_analysis": self.get_nom35_risk_analysis(),
            "compliance_forecast": self.generate_compliance_forecast(),
            "compliance_gaps": self.identify_compliance_gaps(),
            "optimization_recommendations": self.optimize_assessment_scheduling(),
            "generated_at": timezone.now().isoformat()
        }
        
        if format.lower() == "json":
            return json.dumps(dashboard_data, default=str, indent=2)
        else:
            # Implementar otros formatos si es necesario
            return json.dumps(dashboard_data, default=str)
