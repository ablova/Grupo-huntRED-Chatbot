"""
Analizador de Fit Cultural.

Este módulo analiza la compatibilidad cultural entre candidatos y empresas,
evaluando valores, propósito y prácticas organizacionales de Grupo huntRED®.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from django.conf import settings
from asgiref.sync import sync_to_async

from app.models import (
    Person, Company, BusinessUnit,
    PersonCulturalProfile, CulturalFitReport,
    OrganizationalCulture
)

from app.com.chatbot.workflow.assessments.cultural import CulturalAnalysis
from app.com.chatbot.workflow.assessments.personality import PersonalityAnalysis
from app.com.chatbot.workflow.assessments.generational import GenerationalAnalysis
from app.com.chatbot.core.values import ValuesPrinciples
from app.com.chatbot.core.principles import PrinciplesAnalyzer
from app.com.chatbot.core.purpose import PurposeAnalyzer

logger = logging.getLogger(__name__)

class CulturalFitAnalyzer:
    """
    Analizador de compatibilidad cultural entre candidatos y organizaciones.
    Optimizado para bajo consumo de CPU y respuestas rápidas.
    """
    
    def __init__(self, person: Person, company: Company):
        """
        Inicializa el analizador con la persona y compañía a evaluar.
        
        Args:
            person: Persona a evaluar
            company: Compañía para la evaluación
        """
        self.person = person
        self.company = company
        self.person_profile = None
        self.company_profile = None
        self._initialize_profiles()
    
    def _initialize_profiles(self):
        """Inicializa los perfiles culturales necesarios."""
        try:
            # Obtener perfil cultural de la persona
            self.person_profile = PersonCulturalProfile.objects.filter(
                person=self.person
            ).first()
            
            # Obtener perfil cultural de la organización
            self.company_profile = OrganizationalCulture.objects.filter(
                organization=self.company,
                is_current=True
            ).first()
            
        except Exception as e:
            logger.error(f"Error inicializando perfiles culturales: {str(e)}")
    
    @sync_to_async
    def analyze_fit(self) -> Dict[str, Any]:
        """
        Analiza la compatibilidad cultural entre la persona y la compañía.
        
        Returns:
            dict: Resultados del análisis de compatibilidad
        """
        try:
            if not self.person_profile or not self.company_profile:
                return {
                    'error': 'Perfiles culturales no disponibles',
                    'fit_score': 0.0
                }
            
            # Calcular puntuación general
            fit_score = self.person_profile.calculate_overall_fit(self.company_profile)
            
            # Crear o actualizar reporte de fit
            report, created = CulturalFitReport.objects.update_or_create(
                person=self.person,
                company=self.company,
                defaults={
                    'overall_fit_score': fit_score,
                    'dimension_scores': self.person_profile.get_cultural_dimensions(),
                    'values_alignment': self.person_profile.values_alignment
                }
            )
            
            return {
                'fit_score': fit_score,
                'fit_level': report.get_fit_level(),
                'dimensions': report.dimension_scores,
                'values': report.values_alignment,
                'strengths': report.strengths,
                'areas_for_improvement': report.areas_for_improvement,
                'recommendations': report.recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analizando fit cultural: {str(e)}")
            return {
                'error': str(e),
                'fit_score': 0.0
            }
