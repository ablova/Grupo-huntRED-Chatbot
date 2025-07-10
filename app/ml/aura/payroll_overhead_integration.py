# app/ml/aura/payroll_overhead_integration.py
"""
Sistema de Integración AURA-Payroll Overhead
==========================================
Conecta el sistema de ML/AURA con el cálculo de overhead en Payroll
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from datetime import datetime
import asyncio
import logging
from django.db import transaction
from django.core.cache import cache

from app.payroll.models import (
    PayrollEmployee as Employee, PayrollCompany as Company, OverheadCategory, 
    EmployeeOverheadCalculation, TeamOverheadAnalysis,
    OverheadMLModel
)
from app.payroll.services.overhead_calculator import OverheadCalculatorService
from app.payroll.services.ml_overhead_optimizer import MLOverheadOptimizer

from .aura import AuraEngine, AuraAnalysisType
from .compatibility_engine import CompatibilityEngine
from .recommendation_engine import RecommendationEngine
from .energy_analyzer import EnergyAnalyzer
from .vibrational_matcher import VibrationalMatcher
from .holistic_assessor import HolisticAssessor
from .aura_metrics import AuraMetrics

logger = logging.getLogger(__name__)

class AuraPayrollOverheadIntegration:
    """
    Integración profunda entre AURA y el sistema de Overhead de Payroll
    Potencia el cálculo de overhead con inteligencia de AURA
    """
    
    def __init__(self, company: Optional[Company] = None):
        self.company = company
        self.aura_engine = AuraEngine()
        self.overhead_calculator = OverheadCalculatorService()
        self.ml_optimizer = MLOverheadOptimizer()
        self.cache_ttl = 3600
        
    async def calculate_aura_enhanced_overhead(
        self, 
        employee: Employee,
        include_predictions: bool = True
    ) -> Dict[str, Any]:
        """
        Calcula overhead mejorado con AURA
        """
        try:
            # 1. Cálculo base de overhead
            base_overhead = self.overhead_calculator.calculate_individual_overhead(
                employee, include_ml=False
            )
            
            # 2. Análisis AURA del empleado
            person = employee.person if hasattr(employee, 'person') else None
            if not person:
                logger.warning(f"Empleado {employee.id} sin persona asociada para AURA")
                return base_overhead
                
            aura_analysis = await self.aura_engine.analyze_person_aura(
                person,
                analysis_types=[
                    AuraAnalysisType.GROWTH_POTENTIAL,
                    AuraAnalysisType.TEAM_SYNERGY,
                    AuraAnalysisType.CULTURAL_FIT,
                    AuraAnalysisType.ENERGY_MATCH
                ]
            )
            
            # 3. Calcular mejoras AURA al overhead
            aura_enhancements = await self._calculate_aura_enhancements(
                employee, aura_analysis, base_overhead
            )
            
            # 4. Predicciones ML con contexto AURA
            ml_predictions = None
            if include_predictions:
                ml_predictions = await self._get_ml_predictions_with_aura(
                    employee, aura_analysis
                )
            
            # 5. Integrar todo
            result = {
                'base_overhead': base_overhead,
                'aura_enhancements': aura_enhancements,
                'ml_predictions': ml_predictions,
                'total_overhead': self._calculate_total_enhanced_overhead(
                    base_overhead, aura_enhancements
                ),
                'aura_insights': await self._generate_aura_insights(
                    employee, aura_analysis
                ),
                'recommendations': await self._generate_recommendations(
                    employee, aura_analysis, base_overhead
                )
            }
            
            # 6. Guardar en BD
            await self._save_calculation(employee, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error en cálculo AURA-enhanced overhead: {str(e)}")
            return base_overhead

    async def analyze_team_overhead_with_aura(
        self,
        team_members: List[Employee]
    ) -> Dict[str, Any]:
        """
        Análisis de overhead de equipo con sinergia AURA
        """
        try:
            # 1. Cálculo base del equipo
            base_team_analysis = self.overhead_calculator.calculate_team_overhead(
                team_members
            )
            
            # 2. Análisis AURA de sinergia
            team_synergy = await self._analyze_team_synergy_aura(team_members)
            
            # 3. Análisis de compatibilidad del equipo
            compatibility_matrix = await self._build_compatibility_matrix(team_members)
            
            # 4. Optimización ML del equipo
            ml_optimization = await self._optimize_team_with_ml(
                team_members, team_synergy, compatibility_matrix
            )
            
            # 5. Integrar resultados
            result = {
                'base_analysis': base_team_analysis,
                'team_synergy': team_synergy,
                'compatibility_matrix': compatibility_matrix,
                'ml_optimization': ml_optimization,
                'enhanced_team_overhead': self._calculate_enhanced_team_overhead(
                    base_team_analysis, team_synergy
                ),
                'team_insights': await self._generate_team_insights(
                    team_members, team_synergy, compatibility_matrix
                ),
                'recommendations': await self._generate_team_recommendations(
                    team_members, team_synergy, ml_optimization
                )
            }
            
            # 6. Guardar análisis
            await self._save_team_analysis(team_members, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis de equipo AURA: {str(e)}")

    async def _calculate_aura_enhancements(
        self,
        employee: Employee,
        aura_analysis: Dict[AuraAnalysisType, Any],
        base_overhead: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calcula mejoras AURA específicas al overhead
        """
        enhancements = {
            'categories': {},
            'total_enhancement': 0.0,
            'aura_multiplier': 1.0
        }
        
        # Growth Potential impacta capacitación e innovación
        growth_score = aura_analysis.get(AuraAnalysisType.GROWTH_POTENTIAL, {}).score or 0
        if growth_score > 80:
            enhancements['categories']['training'] = 0.02  # +2% en capacitación
            enhancements['categories']['innovation'] = 0.03  # +3% en innovación
            
        # Team Synergy impacta bienestar y productividad
        synergy_score = aura_analysis.get(AuraAnalysisType.TEAM_SYNERGY, {}).score or 0
        if synergy_score > 75:
            enhancements['categories']['wellbeing'] = 0.025  # +2.5% en bienestar
            
        # Cultural Fit reduce costos administrativos
        cultural_score = aura_analysis.get(AuraAnalysisType.CULTURAL_FIT, {}).score or 0
        if cultural_score > 85:
            enhancements['categories']['administrative'] = -0.02  # -2% admin (más eficiente)
            
        # Energy Match mejora sustentabilidad
        energy_score = aura_analysis.get(AuraAnalysisType.ENERGY_MATCH, {}).score or 0
        if energy_score > 70:
            enhancements['categories']['sustainability'] = 0.015  # +1.5% sustentabilidad
            
        # Calcular multiplicador AURA total
        avg_aura_score = np.mean([
            growth_score, synergy_score, cultural_score, energy_score
        ])
        enhancements['aura_multiplier'] = 1 + (avg_aura_score / 1000)  # Max +10%
        
        # Total enhancement
        enhancements['total_enhancement'] = sum(enhancements['categories'].values())
        
        return enhancements

    async def _get_ml_predictions_with_aura(
        self,
        employee: Employee,
        aura_analysis: Dict[AuraAnalysisType, Any]
    ) -> Dict[str, Any]:
        """
        Obtiene predicciones ML enriquecidas con datos AURA
        """
        # Preparar features incluyendo AURA
        features = self._prepare_ml_features(employee)
        aura_features = self._extract_aura_features(aura_analysis)
        combined_features = {**features, **aura_features}
        
        # Obtener predicción
        prediction = self.ml_optimizer.predict_optimal_overhead(
            employee,
            additional_features=combined_features
        )
        
        # Enriquecer con contexto AURA
        prediction['aura_confidence_boost'] = self._calculate_aura_confidence_boost(
            aura_analysis
        )
        prediction['aura_adjusted_prediction'] = (
            prediction['optimal_overhead'] * 
            (1 + prediction['aura_confidence_boost'])
        )
        
        return prediction

    async def _analyze_team_synergy_aura(
        self,
        team_members: List[Employee]
    ) -> Dict[str, Any]:
        """
        Analiza la sinergia AURA del equipo
        """
        synergy_scores = []
        energy_patterns = []
        
        for member in team_members:
            if hasattr(member, 'person') and member.person:
                # Análisis individual
                aura_result = await self.aura_engine.analyze_person_aura(
                    member.person,
                    [AuraAnalysisType.TEAM_SYNERGY, AuraAnalysisType.ENERGY_MATCH]
                )
                
                synergy_scores.append(
                    aura_result.get(AuraAnalysisType.TEAM_SYNERGY, {}).score or 0
                )
                energy_patterns.append(
                    aura_result.get(AuraAnalysisType.ENERGY_MATCH, {})
                )
        
        # Calcular métricas del equipo
        team_synergy = {
            'average_synergy': np.mean(synergy_scores) if synergy_scores else 0,
            'synergy_variance': np.var(synergy_scores) if synergy_scores else 0,
            'energy_alignment': self._calculate_energy_alignment(energy_patterns),
            'collaboration_potential': self._estimate_collaboration_potential(
                synergy_scores, energy_patterns
            ),
            'team_coherence': self._calculate_team_coherence(synergy_scores)
        }
        
        return team_synergy

    async def _build_compatibility_matrix(
        self,
        team_members: List[Employee]
    ) -> np.ndarray:
        """
        Construye matriz de compatibilidad AURA entre miembros
        """
        n = len(team_members)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i+1, n):
                if (hasattr(team_members[i], 'person') and 
                    hasattr(team_members[j], 'person')):
                    
                    # Calcular compatibilidad bidireccional
                    compatibility = await self._calculate_pairwise_compatibility(
                        team_members[i].person,
                        team_members[j].person
                    )
                    
                    matrix[i][j] = compatibility
                    matrix[j][i] = compatibility
                    
        return matrix

    def _calculate_total_enhanced_overhead(
        self,
        base_overhead: Dict[str, Any],
        aura_enhancements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calcula el overhead total con mejoras AURA
        """
        enhanced_overhead = {
            'total_percentage': base_overhead['total_percentage'],
            'monthly_amount': base_overhead['monthly_amount'],
            'categories': {}
        }
        
        # Aplicar mejoras por categoría
        for category, base_value in base_overhead['categories'].items():
            enhancement = aura_enhancements['categories'].get(category, 0)
            enhanced_value = base_value * (1 + enhancement)
            enhanced_overhead['categories'][category] = enhanced_value
            
        # Aplicar multiplicador AURA
        enhanced_overhead['total_percentage'] *= aura_enhancements['aura_multiplier']
        enhanced_overhead['monthly_amount'] *= aura_enhancements['aura_multiplier']
        
        # Agregar nuevas categorías AURA si aplican
        if aura_enhancements['total_enhancement'] > 0.05:  # Si hay mejora significativa
            enhanced_overhead['aura_bonus'] = aura_enhancements['total_enhancement']
            
        return enhanced_overhead

    async def _save_calculation(
        self,
        employee: Employee,
        result: Dict[str, Any]
    ) -> None:
        """
        Guarda el cálculo en la base de datos
        """
        try:
            with transaction.atomic():
                calculation = EmployeeOverheadCalculation.objects.create(
                    employee=employee,
                    calculation_date=datetime.now(),
                    total_overhead_percentage=result['total_overhead']['total_percentage'],
                    categories=result['total_overhead']['categories'],
                    ml_prediction=result.get('ml_predictions'),
                    aura_score=result['aura_enhancements']['aura_multiplier'],
                    recommendations=result.get('recommendations', [])
                )
                
                # Cache para acceso rápido
                cache_key = f"aura_overhead_{employee.id}"
                cache.set(cache_key, result, self.cache_ttl)
                
        except Exception as e:
            logger.error(f"Error guardando cálculo AURA: {str(e)}")