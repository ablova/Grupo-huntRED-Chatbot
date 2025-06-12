# /home/pablo/app/ml/core/models/base.py
import os
import gc
import json
import logging
from pathlib import Path
from functools import lru_cache
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
import pandas as pd
import numpy as np
from joblib import dump, load
from celery import shared_task
from typing import Dict, List, Any, Optional, Tuple
from typing import Dict, List, Any, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from app.ml.core.utils.matchmaking import calculate_match_percentage, calculate_alignment_percentage
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime
from django.db import models

logger = logging.getLogger(__name__)

# Diccionario de jerarquía de unidades de negocio
BUSINESS_UNIT_HIERARCHY = {
    "amigro": 1,
    "huntu": 2,
    "huntred": 3,
    "huntred_executive": 4,
}

class BaseMLModel(ABC):
    """
    Clase base para modelos de Machine Learning en Grupo huntRED®.
    Implementa funcionalidades comunes y adaptables para diferentes niveles de perfiles.
    """
    
    def __init__(self, business_unit: Optional[str] = None):
        self.business_unit = business_unit
        self._cache = {}
        self._cache_ttl = 3600  # 1 hora por defecto
        self._initialize_models()
        
    @abstractmethod
    def _initialize_models(self) -> None:
        """Inicializa los modelos necesarios."""
        pass
        
    @abstractmethod
    def prepare_training_data(self) -> None:
        """Prepara los datos de entrenamiento."""
        pass
        
    @abstractmethod
    def train_model(self, df, test_size=0.2):
        """Entrena el modelo con los datos proporcionados."""
        pass
        
    def _check_api_limits(self) -> bool:
        """Verifica los límites de uso de APIs externas."""
        try:
            # Implementar verificación de límites
            return True
        except Exception as e:
            logger.error(f"Error verificando límites de API: {str(e)}")
            return False
            
    def _increment_api_usage(self, api_type: str):
        """Incrementa el contador de uso de APIs."""
        try:
            # Implementar incremento de uso
            pass
        except Exception as e:
            logger.error(f"Error incrementando uso de API: {str(e)}")
            
    async def calculate_match_score(self, person: Person, vacancy: Vacante) -> float:
        """
        Calcula el puntaje de matching considerando el nivel de información disponible.
        
        Args:
            person: Persona a evaluar
            vacancy: Vacante a evaluar
            
        Returns:
            float: Puntaje de matching (0-100)
        """
        try:
            # Obtener nivel de información del perfil
            profile_level = self._get_profile_level(person)
            
            # Obtener pesos según nivel de perfil y unidad de negocio
            weights = await self._get_weights(vacancy.business_unit, person)
            
            # Ajustar pesos según nivel de información disponible
            adjusted_weights = self._adjust_weights(weights, self._get_data_availability(person))
            
            # Calcular componentes del score
            skills_score = await self._calculate_skills_match(person, vacancy)
            experience_score = await self._calculate_experience_match(person, vacancy)
            culture_score = await self._calculate_culture_match(person, vacancy)
            
            # Calcular score final con pesos ajustados
            final_score = (
                skills_score * adjusted_weights['skills'] +
                experience_score * adjusted_weights['experience'] +
                culture_score * adjusted_weights['culture']
            )
            
            # Ajustar score según nivel de perfil
            if profile_level == 'basic':
                # Para perfiles básicos, dar más peso a la ubicación y disponibilidad
                location_score = await self._calculate_location_score(person, vacancy)
                final_score = (final_score * 0.7) + (location_score * 0.3)
            elif profile_level == 'complete':
                # Para perfiles completos, considerar más factores
                personality_score = await self._calculate_personality_match(person, vacancy)
                final_score = (final_score * 0.8) + (personality_score * 0.2)
            
            return min(100, max(0, final_score))
            
        except Exception as e:
            logger.error(f"Error calculando match score: {str(e)}")
            return 0.0
            
    def _get_profile_level(self, person: Person) -> str:
        """
        Determina el nivel de información del perfil.
        
        Returns:
            str: 'basic', 'intermediate', o 'complete'
        """
        try:
            # Contar campos completados
            completed_fields = 0
            total_fields = 0
            
            # Verificar información básica
            if person.name: completed_fields += 1
            total_fields += 1
            
            if person.email: completed_fields += 1
            total_fields += 1
            
            # Verificar información profesional
            if person.skills: completed_fields += 1
            total_fields += 1
            
            if person.experience: completed_fields += 1
            total_fields += 1
            
            # Verificar información adicional
            if person.education: completed_fields += 1
            total_fields += 1
            
            if person.location: completed_fields += 1
            total_fields += 1
            
            if person.salary_expectations: completed_fields += 1
            total_fields += 1
            
            # Calcular porcentaje de completitud
            completion_percentage = (completed_fields / total_fields) * 100
            
            # Determinar nivel
            if completion_percentage < 40:
                return 'basic'
            elif completion_percentage < 80:
                return 'intermediate'
            else:
                return 'complete'
                
        except Exception as e:
            logger.error(f"Error determinando nivel de perfil: {str(e)}")
            return 'basic'
            
    def _get_data_availability(self, person: Person) -> Dict[str, bool]:
        """
        Determina qué datos están disponibles para el perfil.
        
        Returns:
            Dict con flags de disponibilidad
        """
        return {
            'skills': bool(person.skills),
            'experience': bool(person.experience),
            'education': bool(person.education),
            'location': bool(person.location),
            'salary': bool(person.salary_expectations),
            'personality': bool(getattr(person, 'personality_traits', None)),
            'culture': bool(getattr(person, 'cultural_preferences', None))
        }
        
    def _adjust_weights(self, original_weights: Dict[str, float], data_availability: Dict[str, bool]) -> Dict[str, float]:
        """
        Ajusta los pesos según la disponibilidad de datos.
        
        Args:
            original_weights: Pesos originales
            data_availability: Disponibilidad de datos
            
        Returns:
            Dict con pesos ajustados
        """
        try:
            # Copiar pesos originales
            adjusted_weights = original_weights.copy()
            
            # Calcular total de datos disponibles
            available_data = sum(1 for available in data_availability.values() if available)
            if available_data == 0:
                return original_weights
                
            # Ajustar pesos según disponibilidad
            for key, available in data_availability.items():
                if not available and key in adjusted_weights:
                    # Redistribuir peso de datos no disponibles
                    weight_to_redistribute = adjusted_weights[key]
                    adjusted_weights[key] = 0
                    
                    # Distribuir peso entre datos disponibles
                    for other_key, other_available in data_availability.items():
                        if other_available and other_key in adjusted_weights:
                            adjusted_weights[other_key] += weight_to_redistribute / available_data
                            
            # Normalizar pesos
            total_weight = sum(adjusted_weights.values())
            if total_weight > 0:
                adjusted_weights = {k: v/total_weight for k, v in adjusted_weights.items()}
                
            return adjusted_weights
            
        except Exception as e:
            logger.error(f"Error ajustando pesos: {str(e)}")
            return original_weights
            
    async def _calculate_skills_match(self, person: Person, vacancy: Vacante) -> float:
        """
        Calcula el match de habilidades considerando el nivel de perfil.
        """
        try:
            if not person.skills:
                return 0.5  # Score base para perfiles sin habilidades
                
            # Obtener habilidades requeridas
            required_skills = vacancy.skills_required or []
            
            # Calcular match básico
            skill_match = calculate_match_percentage(
                candidate_skills=person.skills,
                required_skills=required_skills,
                business_unit_id=vacancy.business_unit.id
            )
            
            # Ajustar según nivel de perfil
            profile_level = self._get_profile_level(person)
            if profile_level == 'basic':
                # Para perfiles básicos, dar más peso a habilidades principales
                main_skills = [s for s in required_skills if s.get('importance', 0) > 0.7]
                if main_skills:
                    main_skills_match = calculate_match_percentage(
                        candidate_skills=person.skills,
                        required_skills=main_skills,
                        business_unit_id=vacancy.business_unit.id
                    )
                    skill_match = (skill_match * 0.3) + (main_skills_match * 0.7)
                    
            return skill_match
            
        except Exception as e:
            logger.error(f"Error calculando skills match: {str(e)}")
            return 0.0
            
    async def _calculate_experience_match(self, person: Person, vacancy: Vacante) -> float:
        """
        Calcula el match de experiencia considerando el nivel de perfil.
        """
        try:
            if not person.experience:
                return 0.5  # Score base para perfiles sin experiencia
                
            # Obtener años de experiencia requeridos
            required_exp = vacancy.metadata.get('required_experience', 0)
            person_exp = person.metadata.get('experience_years', 0)
            
            # Calcular match básico
            if not required_exp:
                return 1.0
                
            if person_exp >= required_exp:
                exp_match = 1.0
            elif person_exp >= required_exp * 0.8:
                exp_match = 0.8
            elif person_exp >= required_exp * 0.6:
                exp_match = 0.6
            elif person_exp >= required_exp * 0.4:
                exp_match = 0.4
            else:
                exp_match = 0.2
                
            # Ajustar según nivel de perfil
            profile_level = self._get_profile_level(person)
            if profile_level == 'basic':
                # Para perfiles básicos, dar más peso a experiencia relevante
                relevant_exp = sum(1 for exp in person.experience 
                                 if exp.get('industry') == vacancy.industry)
                if relevant_exp > 0:
                    exp_match = min(1.0, exp_match * 1.2)
                    
            return exp_match
            
        except Exception as e:
            logger.error(f"Error calculando experience match: {str(e)}")
            return 0.0
            
    async def _calculate_culture_match(self, person: Person, vacancy: Vacante) -> float:
        """
        Calcula el match cultural considerando el nivel de perfil.
        """
        try:
            if not getattr(person, 'cultural_preferences', None):
                return 0.5  # Score base para perfiles sin preferencias culturales
                
            # Obtener preferencias culturales
            person_culture = person.cultural_preferences
            vacancy_culture = vacancy.metadata.get('cultural_values', {})
            
            if not vacancy_culture:
                return 0.5
                
            # Calcular match básico
            culture_match = 0.0
            total_weights = 0
            
            for key, value in vacancy_culture.items():
                if key in person_culture:
                    weight = value.get('weight', 1.0)
                    culture_match += abs(person_culture[key] - value['value']) * weight
                    total_weights += weight
                    
            if total_weights > 0:
                culture_match = 1 - (culture_match / total_weights)
                
            # Ajustar según nivel de perfil
            profile_level = self._get_profile_level(person)
            if profile_level == 'basic':
                # Para perfiles básicos, dar más peso a valores fundamentales
                core_values = {k: v for k, v in vacancy_culture.items() 
                             if v.get('importance', 0) > 0.7}
                if core_values:
                    core_match = 0.0
                    core_weights = 0
                    
                    for key, value in core_values.items():
                        if key in person_culture:
                            weight = value.get('weight', 1.0)
                            core_match += abs(person_culture[key] - value['value']) * weight
                            core_weights += weight
                            
                    if core_weights > 0:
                        core_match = 1 - (core_match / core_weights)
                        culture_match = (culture_match * 0.3) + (core_match * 0.7)
                        
            return culture_match
            
        except Exception as e:
            logger.error(f"Error calculando culture match: {str(e)}")
            return 0.0
            
    async def _calculate_location_score(self, person: Person, vacancy: Vacante) -> float:
        """
        Calcula el score de ubicación considerando el nivel de perfil y la unidad de negocio.
        """
        try:
            if not person.location:
                return 0.5  # Score base para perfiles sin ubicación
                
            # Obtener preferencias de transporte según BU
            transport_prefs = self._get_transport_mode(person, vacancy)
            
            # Obtener zonas
            zones = self._get_zones()
            person_zone = self._get_zone(person.location, zones)
            vacancy_zone = self._get_zone(vacancy.location, zones)
            
            if not person_zone or not vacancy_zone:
                return 0.5
                
            # Calcular score base según BU
            base_score = self._calculate_zone_score(person_zone, vacancy_zone)
            
            # Obtener score aprendido de casos exitosos
            learned_score = await self._get_learned_location_score(person, vacancy)
            
            # Obtener nivel de perfil
            profile_level = self._get_profile_level(person)
            
            # Ajustar score según BU y nivel de perfil
            if vacancy.business_unit.name.lower() == 'huntred_executive':
                # Para huntRED Executive, menor peso a ubicación
                final_score = (base_score * 0.4 + learned_score * 0.2)
                if profile_level == 'complete':
                    # Para perfiles completos, considerar preferencias de transporte
                    transport_score = self._calculate_transport_score(person, vacancy, transport_prefs)
                    final_score = (final_score * 0.7) + (transport_score * 0.3)
                    
            elif vacancy.business_unit.name.lower() == 'huntu':
                # Para huntU, considerar ubicación de estudios
                if person.is_student and person.study_location:
                    study_score = await self._calculate_study_location_score(
                        person, vacancy, transport_prefs.get('max_distance', 30)
                    )
                    final_score = (base_score * 0.5 + learned_score * 0.2 + study_score * 0.3)
                else:
                    final_score = (base_score * 0.6 + learned_score * 0.4)
                    
            elif vacancy.business_unit.name.lower() == 'amigro':
                # Para Amigro, mayor peso a cercanía y transporte público
                if profile_level == 'basic':
                    # Para perfiles básicos, dar más peso a la cercanía
                    if self._are_adjacent_zones(person_zone, vacancy_zone):
                        base_score = min(1.0, base_score * 1.2)
                final_score = (base_score * 0.7 + learned_score * 0.3)
                
            else:  # huntRED general
                # Para huntRED general, balance entre todos los factores
                final_score = (base_score * 0.5 + learned_score * 0.3)
                if profile_level == 'complete':
                    # Para perfiles completos, considerar más factores
                    transport_score = self._calculate_transport_score(person, vacancy, transport_prefs)
                    final_score = (final_score * 0.7) + (transport_score * 0.3)
                    
            # Guardar nota de éxito si el score es alto
            if final_score > 0.7:
                await self._add_location_success_note(person, vacancy, final_score)
                
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculando location score: {str(e)}")
            return 0.0
            
    def _calculate_transport_score(self, person: Person, vacancy: Vacante, transport_prefs: Dict) -> float:
        """
        Calcula el score de transporte considerando preferencias y disponibilidad.
        """
        try:
            if not transport_prefs:
                return 0.5
                
            # Obtener modo de transporte preferido
            preferred_mode = transport_prefs.get('primary')
            if not preferred_mode:
                return 0.5
                
            # Verificar disponibilidad del modo preferido
            if preferred_mode == 'car' and not person.has_car:
                return 0.3
            elif preferred_mode == 'public_transport' and not person.has_public_transport:
                return 0.3
                
            # Calcular score base
            base_score = 0.7  # Score base para modo disponible
            
            # Ajustar según preferencias
            if person.preferred_transport_mode == preferred_mode:
                base_score *= 1.2
                
            return min(1.0, base_score)
            
        except Exception as e:
            logger.error(f"Error calculando transport score: {str(e)}")
            return 0.5
    
    async def _calculate_personality_match(self, person: Person, vacancy: Vacante) -> float:
        """
        Calcula el match de personalidad considerando el nivel de perfil.
        """
        try:
            if not getattr(person, 'personality_traits', None):
                return 0.5  # Score base para perfiles sin rasgos de personalidad
                
            # Obtener rasgos de personalidad
            person_traits = person.personality_traits
            vacancy_traits = vacancy.metadata.get('personality_traits', {})
            
            if not vacancy_traits:
                return 0.5
                
            # Calcular match básico
            personality_match = 0.0
            total_weights = 0
            
            for key, value in vacancy_traits.items():
                if key in person_traits:
                    weight = value.get('weight', 1.0)
                    personality_match += abs(person_traits[key] - value['value']) * weight
                    total_weights += weight
                    
            if total_weights > 0:
                personality_match = 1 - (personality_match / total_weights)
                
            return personality_match
            
        except Exception as e:
            logger.error(f"Error calculando personality match: {str(e)}")
            return 0.0

class MatchmakingModel(BaseMLModel):
    """Modelo específico para matchmaking de candidatos."""
    
    def __init__(self, business_unit: Optional[str] = None):
        super().__init__(business_unit)
        self.model_file = os.path.join(
            settings.ML_MODELS_DIR,
            f"matchmaking_model_{business_unit or 'global'}.pkl"
        )
    
    def _initialize_models(self) -> None:
        self.model = RandomForestClassifier(n_estimators=100)
        self.scaler = StandardScaler()
        self.pipeline = Pipeline([
            ('scaler', self.scaler),
            ('classifier', self.model)
        ])
    
    def prepare_training_data(self):
        """Implementación específica para matchmaking."""
        # ... existing code ...
    
    def train_model(self, df, test_size=0.2):
        """Implementación específica para matchmaking."""
        # ... existing code ...

class TransitionModel(BaseMLModel):
    """Modelo específico para predicción de transiciones."""
    
    def __init__(self, business_unit: Optional[str] = None):
        super().__init__(business_unit)
        self.model_file = os.path.join(
            settings.ML_MODELS_DIR,
            f"transition_model_{business_unit or 'global'}.pkl"
        )
    
    def _initialize_models(self) -> None:
        self.model = RandomForestClassifier(n_estimators=100)
        self.scaler = StandardScaler()
        self.pipeline = Pipeline([
            ('scaler', self.scaler),
            ('classifier', self.model)
        ])
    
    def prepare_training_data(self):
        """Implementación específica para transiciones."""
        # ... existing code ...
    
    def train_model(self, df, test_size=0.2):
        """Implementación específica para transiciones."""
        # ... existing code ...

class MarketAnalysisModel(BaseMLModel):
    """Modelo específico para análisis de mercado."""
    
    def __init__(self, business_unit: Optional[str] = None):
        super().__init__(business_unit)
        self.model_file = os.path.join(
            settings.ML_MODELS_DIR,
            f"market_analysis_model_{business_unit or 'global'}.pkl"
        )
    
    def _initialize_models(self) -> None:
        self.model = RandomForestClassifier(n_estimators=100)
        self.scaler = StandardScaler()
        self.pipeline = Pipeline([
            ('scaler', self.scaler),
            ('classifier', self.model)
        ])
    
    def prepare_training_data(self):
        """Implementación específica para análisis de mercado."""
        # ... existing code ...
    
    def train_model(self, df, test_size=0.2):
        """Implementación específica para análisis de mercado."""
        # ... existing code ...

class LocationSuccessNote(models.Model):
    """Modelo para almacenar notas y casos de éxito de ubicación."""
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE)
    location_type = models.CharField(max_length=50)  # 'study', 'work', 'home'
    zone = models.CharField(max_length=50)
    transport_mode = models.CharField(max_length=50)
    success_score = models.FloatField()
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['business_unit', 'location_type']),
            models.Index(fields=['zone', 'transport_mode'])
        ]

class InteractionSuccessNote(models.Model):
    """Modelo para almacenar notas de éxito en interacciones y notificaciones."""
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=50)  # 'notification', 'match', 'response'
    channel = models.CharField(max_length=50)  # 'email', 'whatsapp', 'sms'
    time_of_day = models.IntegerField()  # Hora del día
    day_of_week = models.IntegerField()  # Día de la semana
    success_score = models.FloatField()
    response_time = models.IntegerField(null=True)  # Tiempo de respuesta en minutos
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['business_unit', 'interaction_type']),
            models.Index(fields=['channel', 'time_of_day'])
        ]

class MatchmakingLearningSystem:
    """
    Sistema de aprendizaje automático para matchmaking y análisis de perfiles.
    Optimizado para eficiencia y bajo costo operativo.
    """
    
    def __init__(self):
        """Initialize the matchmaking system with required models."""
        super().__init__()
        self.location_analyzer = None
        self._cache = {}
        self._cache_ttl = 3600  # 1 hora por defecto
    
    async def calculate_match_score(self, person: Person, vacancy: Vacante) -> float:
        """
        Calcula el puntaje de matching considerando patrones del candidato.
        """
        try:
            # Obtener score base
            base_score = await super().calculate_match_score(person, vacancy)
            
            # Analizar patrones del candidato
            patterns = await self._analyze_candidate_patterns(person)
            
            # Ajustar score según patrones
            if patterns:
                # Ajustar por zona preferida
                if vacancy.location in patterns.get('preferred_zones', {}):
                    base_score *= 1.1
                
                # Ajustar por horario preferido
                current_hour = datetime.now().hour
                if 6 <= current_hour < 12 and patterns['preferred_schedules']['morning'] > 0:
                    base_score *= 1.05
                
                # Ajustar por roles exitosos
                if vacancy.role in [role for role, _ in patterns.get('successful_matches', {}).get('preferred_roles', [])]:
                    base_score *= 1.15
            
            return min(100, base_score)
            
        except Exception as e:
            logger.error(f"Error calculando match score con patrones: {str(e)}")
            return await super().calculate_match_score(person, vacancy)
    
    def _get_cached_score(self, key: str) -> Optional[float]:
        """Obtiene un score desde el caché."""
        if key in self._cache:
            timestamp, score = self._cache[key]
            if datetime.now().timestamp() - timestamp < self._cache_ttl:
                return score
            del self._cache[key]
        return None
    
    def _cache_score(self, key: str, score: float):
        """Guarda un score en el caché."""
        self._cache[key] = (datetime.now().timestamp(), score)
    
    async def _get_weights(self, business_unit: BusinessUnit, person: Person) -> Dict:
        """Obtiene los pesos de matching según la unidad de negocio y nivel de posición."""
        try:
            # Verificar caché
            cache_key = f"weights:{business_unit.id}:{person.id}"
            cached_weights = self._get_cached_score(cache_key)
            if cached_weights is not None:
                return cached_weights
            
            # Obtener configuración de la BU
            config = ConfiguracionBU.objects.get(business_unit=business_unit)
            
            # Determinar nivel de posición
            position_level = self._get_position_level(person)
            
            # Obtener pesos según nivel
            weights = config.get_weights(position_level)
            
            result = {
                'skills': weights['hard_skills'] / 100,
                'location': weights['ubicacion'] / 100,
                'culture': weights['soft_skills'] / 100,
                'experience': weights['personalidad'] / 100
            }
            
            # Guardar en caché
            self._cache_score(cache_key, result)
            
            return result
            
        except ConfiguracionBU.DoesNotExist:
            logger.warning(f"No se encontró configuración para {business_unit}")
            return {
                'skills': 0.4,
                'location': 0.2,
                'culture': 0.2,
                'experience': 0.2
            }
    
    def _get_position_level(self, person: Person) -> str:
        """Determina el nivel de posición basado en la experiencia."""
        experience_years = person.metadata.get('experience_years', 0)
        
        if experience_years >= 15:
            return 'alta_direccion'
        elif experience_years >= 8:
            return 'gerencia_media'
        elif experience_years >= 2:
            return 'operativo'
        return 'entry_level'
    
    async def _calculate_skills_match(self, person: Person, vacancy: Vacante) -> float:
        """Calcula el score de matching de habilidades."""
        try:
            # Verificar caché
            cache_key = f"skills_match:{person.id}:{vacancy.id}"
            cached_score = self._get_cached_score(cache_key)
            if cached_score is not None:
                return cached_score
            
            # Obtener habilidades del candidato
            person_skills = set(person.skills.split(','))
            
            # Obtener habilidades requeridas
            required_skills = set(vacancy.palabras_clave)
            
            # Calcular match
            if not required_skills:
                return 0.0
                
            matching_skills = person_skills.intersection(required_skills)
            score = len(matching_skills) / len(required_skills)
            
            # Guardar en caché
            self._cache_score(cache_key, score)
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculando skills match: {str(e)}")
            return 0.0
    
    async def _calculate_location_score(self, person: Person, vacancy: Vacante) -> float:
        """
        Calcula el score de ubicación considerando el modo de transporte, preferencias por BU
        y aprendizaje automático de casos de éxito.
        """
        try:
            # Obtener preferencias de transporte
            transport_prefs = self._get_transport_mode(person, vacancy)
            
            # Obtener zonas
            zones = self._get_zones()
            person_zone = self._get_zone(person.location, zones)
            vacancy_zone = self._get_zone(vacancy.location, zones)
            
            if not person_zone or not vacancy_zone:
                return 0.0
            
            # Calcular score base
            base_score = await self._calculate_zone_score(person_zone, vacancy_zone)
            
            # Obtener score aprendido
            learned_score = await self._get_learned_location_score(person, vacancy)
            
            # Combinar scores (70% base, 30% aprendido)
            final_score = (base_score * 0.7 + learned_score * 0.3)
            
            # Guardar nota de éxito si el score es alto
            if final_score > 0.7:
                await self._add_location_success_note(person, vacancy, final_score)
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculando location score: {str(e)}")
            return 0.0

    async def _calculate_study_location_score(self, person: Person, vacancy: Vacante, max_distance: int) -> float:
        """
        Calcula el score de ubicación considerando la ubicación de estudios para huntU.
        """
        try:
            if not person.study_location:
                return 0.0
                
            # Calcular distancia a lugar de estudios
            study_distance = await self._calculate_public_transport_time(
                person.location,
                person.study_location
            )
            
            # Calcular distancia al trabajo
            work_distance = await self._calculate_public_transport_time(
                person.location,
                vacancy.location
            )
            
            # Si la distancia total es menor al máximo permitido
            if (study_distance + work_distance) <= max_distance:
                return 1.0
            elif (study_distance + work_distance) <= max_distance * 1.5:
                return 0.7
            else:
                return 0.3
                
        except Exception as e:
            logger.error(f"Error calculando study location score: {str(e)}")
            return 0.0

    async def _calculate_public_transport_score(self, origin: str, destination: str) -> float:
        """
        Calcula el score basado en la calidad del transporte público.
        """
        try:
            # Obtener rutas de transporte público
            routes = await self._get_public_transport_routes(origin, destination)
            if not routes:
                return 0.0
                
            # Calcular score basado en:
            # - Número de transbordos
            # - Frecuencia de servicio
            # - Tiempo total de viaje
            # - Horarios de servicio
            scores = []
            for route in routes:
                route_score = (
                    (1.0 - (route['transfers'] * 0.2)) * 0.3 +  # Menos transbordos es mejor
                    (route['frequency'] / 10) * 0.3 +           # Mayor frecuencia es mejor
                    (1.0 - (route['duration'] / 120)) * 0.4     # Menor duración es mejor
                )
                scores.append(route_score)
                
            return max(scores) if scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculando public transport score: {str(e)}")
            return 0.0

    async def _calculate_public_transport_time(self, origin: str, destination: str) -> int:
        """
        Calcula el tiempo de viaje en transporte público en minutos.
        """
        try:
            routes = await self._get_public_transport_routes(origin, destination)
            if not routes:
                return 999  # Valor alto para indicar que no hay ruta
            return min(route['duration'] for route in routes)
        except Exception as e:
            logger.error(f"Error calculando tiempo de transporte público: {str(e)}")
            return 999

    def _calculate_zone_score(self, zone1: str, zone2: str) -> float:
        """
        Calcula el score base según las zonas.
        """
        if zone1 == zone2:
            return 1.0
        elif self._are_adjacent_zones(zone1, zone2):
            return 0.8
        elif self._are_nearby_zones(zone1, zone2):
            return 0.6
        return 0.3

    def _get_transport_mode(self, person: Person, vacancy: Vacante) -> Dict:
        """
        Determina el modo de transporte preferido según la unidad de negocio y el perfil.
        """
        try:
            bu_config = ConfiguracionBU.objects.get(business_unit=vacancy.business_unit)
            transport_preferences = {
                'amigro': {
                    'primary': 'public_transport',
                    'secondary': 'walking',
                    'weight': 0.8  # Mayor peso al transporte público
                },
                'huntu': {
                    'primary': 'public_transport',
                    'secondary': 'walking',
                    'weight': 0.7,
                    'consider_study_location': True
                },
                'huntred': {
                    'primary': 'car',
                    'secondary': 'public_transport',
                    'weight': 0.6
                },
                'huntred_executive': {
                    'primary': 'car',
                    'secondary': None,
                    'weight': 0.4  # Menor peso a la ubicación
                }
            }
            
            # Obtener preferencias base según BU
            preferences = transport_preferences.get(vacancy.business_unit.name.lower(), {})
            
            # Ajustes específicos para huntU
            if vacancy.business_unit.name.lower() == 'huntu':
                if person.is_student:
                    preferences['consider_study_location'] = True
                    preferences['max_distance'] = 30  # minutos en transporte público
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error determinando modo de transporte: {str(e)}")
            return {'primary': 'public_transport', 'weight': 0.5}

    def _get_zones(self) -> Dict:
        """Obtiene las zonas predefinidas."""
        return {
            'centro': ['Centro Histórico', 'Roma', 'Condesa', 'Polanco'],
            'norte': ['Satélite', 'Interlomas', 'Lomas Verdes'],
            'sur': ['Coyoacán', 'San Ángel', 'Pedregal'],
            'oriente': ['Iztapalapa', 'Tláhuac', 'Xochimilco'],
            'poniente': ['Santa Fe', 'Lomas de Chapultepec', 'Las Águilas']
        }
    
    def _get_zone(self, location: str, zones: Dict) -> Optional[str]:
        """Determina la zona de una ubicación."""
        for zone, areas in zones.items():
            if any(area.lower() in location.lower() for area in areas):
                return zone
        return None
    
    def _are_adjacent_zones(self, zone1: str, zone2: str) -> bool:
        """Determina si dos zonas son adyacentes."""
        adjacent_zones = {
            'centro': ['norte', 'sur', 'oriente', 'poniente'],
            'norte': ['centro', 'poniente'],
            'sur': ['centro', 'oriente'],
            'oriente': ['centro', 'sur'],
            'poniente': ['centro', 'norte']
        }
        return zone2 in adjacent_zones.get(zone1, [])
    
    def _are_nearby_zones(self, zone1: str, zone2: str) -> bool:
        """Determina si dos zonas están relativamente cerca."""
        return not self._are_adjacent_zones(zone1, zone2) and zone1 != zone2
    
    async def _get_historical_traffic_score(self, origin: str, destination: str) -> float:
        """Obtiene score de tráfico basado en datos históricos."""
        try:
            # Usar datos históricos almacenados
            historical_data = await self._get_historical_data(origin, destination)
            
            if not historical_data:
                return 0.5
            
            # Calcular score basado en patrones históricos
            return self._calculate_historical_score(historical_data)
            
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos: {str(e)}")
            return 0.5
    
    async def _calculate_cultural_fit(self, person: Person, vacancy: Vacante) -> float:
        """Calcula el score de fit cultural."""
        try:
            # Verificar caché
            cache_key = f"cultural_fit:{person.id}:{vacancy.id}"
            cached_score = self._get_cached_score(cache_key)
            if cached_score is not None:
                return cached_score
            
            # Obtener datos de personalidad
            person_personality = person.metadata.get('personality_data', {})
            vacancy_personality = vacancy.metadata.get('desired_personality', {})
            
            if not person_personality or not vacancy_personality:
                return 0.0
            
            # Calcular match de personalidad
            matching_traits = 0
            total_traits = 0
            
            for trait, value in vacancy_personality.items():
                if trait in person_personality:
                    total_traits += 1
                    if abs(person_personality[trait] - value) <= 0.2:
                        matching_traits += 1
            
            score = matching_traits / total_traits if total_traits > 0 else 0.0
            
            # Guardar en caché
            self._cache_score(cache_key, score)
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculando cultural fit: {str(e)}")
            return 0.0
    
    async def _calculate_experience_match(self, person: Person, vacancy: Vacante) -> float:
        """Calcula el score de matching de experiencia."""
        try:
            # Verificar caché
            cache_key = f"experience_match:{person.id}:{vacancy.id}"
            cached_score = self._get_cached_score(cache_key)
            if cached_score is not None:
                return cached_score
            
            # Obtener años de experiencia
            person_exp = person.metadata.get('experience_years', 0)
            required_exp = vacancy.metadata.get('required_experience', 0)
            
            if not required_exp:
                return 1.0
            
            # Calcular match
            if person_exp >= required_exp:
                score = 1.0
            elif person_exp >= required_exp * 0.8:
                score = 0.8
            elif person_exp >= required_exp * 0.6:
                score = 0.6
            elif person_exp >= required_exp * 0.4:
                score = 0.4
            else:
                score = 0.2
            
            # Guardar en caché
            self._cache_score(cache_key, score)
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculando experience match: {str(e)}")
            return 0.0
    
    def load_tensorflow(self):
        try:
            import tensorflow as tf
            tf.config.set_visible_devices([], 'GPU')
            tf.config.threading.set_intra_op_parallelism_threads(1)
            tf.config.threading.set_inter_op_parallelism_threads(1)
            logger.info("✅ TensorFlow cargado bajo demanda.")
            return tf
        except ImportError:
            logger.warning("⚠ TensorFlow no está instalado. Usando solo scikit-learn.")
            return None

    def load_model(self):
        if not self._loaded_model and os.path.exists(self.model_file):
            self._loaded_model = load(self.model_file)
            logger.info(f"Modelo cargado desde {self.model_file}")
        elif not os.path.exists(self.model_file):
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import Pipeline
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.scaler = StandardScaler()
            self.pipeline = Pipeline([
                ('scaler', self.scaler),
                ('classifier', self.model)
            ])
            logger.info("Modelo RandomForest inicializado (no entrenado).")
    
    def load_transition_model(self):
        """Carga o inicializa el modelo de predicción de transiciones."""
        if not self._loaded_transition_model and os.path.exists(self.transition_model_file):
            self._loaded_transition_model = load(self.transition_model_file)
            logger.info(f"Modelo de transición cargado desde {self.transition_model_file}")
        elif not os.path.exists(self.transition_model_file):
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import Pipeline
            self.transition_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.transition_scaler = StandardScaler()
            self.transition_pipeline = Pipeline([
                ('scaler', self.transition_scaler),
                ('classifier', self.transition_model)
            ])
            logger.info("Modelo de transición RandomForest inicializado (no entrenado).")

    def _get_applications(self):
        from app.models import Application
        if self.business_unit:
            apps = Application.objects.filter(
                vacancy__business_unit=self.business_unit,
                status__in=['contratado', 'rechazado']
            )
        else:
            apps = Application.objects.filter(status__in=['contratado', 'rechazado'])
        logger.info(f"Aplicaciones recuperadas: {apps.count()}")
        return apps

    @shared_task(name='ml.prepare_batch_data', retry_backoff=True, retry_jitter=True, max_retries=3)
    def process_batch(self, batch_ids):
        """Process a batch of applications to extract features."""
        from app.models import Application
        from app.ml.ml_utils import calculate_match_percentage, calculate_alignment_percentage
        batch_apps = Application.objects.filter(id__in=batch_ids)
        batch_data = []
        for app in batch_apps:
            try:
                hard_skills_score = calculate_match_percentage(app.person.skills, app.vacancy.required_skills)
                soft_skills_score = calculate_match_percentage(app.person.personality, app.vacancy.culture_fit)
                salary_alignment = self._calculate_salary_alignment(app)
                age = self._calculate_age(app.person)
                success = 1 if app.status == 'contratado' else 0
                batch_data.append({
                    'person_id': app.person.id,
                    'vacancy_id': app.vacancy.id,
                    'hard_skills_score': hard_skills_score,
                    'soft_skills_score': soft_skills_score,
                    'salary_alignment': salary_alignment,
                    'age': age,
                    'success': success
                })
                logger.info(f"Processed application {app.id} in batch")
            except Exception as e:
                logger.error(f"Error processing application {app.id}: {str(e)}")
        return batch_data

    def prepare_training_data(self):
        """Prepare training data with batch processing to optimize memory usage."""
        from app.models import Application
        if self.business_unit:
            apps = Application.objects.filter(
                vacancy__business_unit=self.business_unit,
                status__in=['contratado', 'rechazado']
            )
        else:
            apps = Application.objects.filter(status__in=['contratado', 'rechazado'])
        logger.info(f"Total applications to process: {apps.count()}")
        
        # Process in batches to avoid memory issues
        batch_size = 1000
        app_ids = list(apps.values_list('id', flat=True))
        data = []
        for i in range(0, len(app_ids), batch_size):
            batch_ids = app_ids[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1} with {len(batch_ids)} applications")
            batch_result = self.process_batch.delay(batch_ids)
            batch_data = batch_result.get()  # Wait for the batch to complete
            data.extend(batch_data)
            logger.info(f"Batch {i // batch_size + 1} completed, {len(batch_data)} records processed")
        
        return data

    def train_model(self, df, test_size=0.2):
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.ensemble import RandomForestClassifier
        from joblib import dump

        if os.path.exists(self.model_file):
            logger.info("Modelo ya entrenado, omitiendo entrenamiento.")
            return

        # Definir el pipeline si no está ya definido
        if not hasattr(self, 'pipeline'):
            self.pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', RandomForestClassifier(random_state=42))
            ])

        X = df.drop(columns=["success"])
        y = df["success"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

        self.pipeline.fit(X_train, y_train)
        dump(self.pipeline, self.model_file)
        logger.info(f"✅ Modelo RandomForest entrenado y guardado en {self.model_file}")

        y_pred = self.pipeline.predict(X_test)
        report = classification_report(y_test, y_pred)
        logger.info(f"Reporte de clasificación:\n{report}")

    def predict_candidate_success(self, person, vacancy):
        from app.ml.ml_utils import calculate_match_percentage, calculate_alignment_percentage
        self.load_model()
        if not self.pipeline:
            raise FileNotFoundError("El modelo no está entrenado.")

        features = {
            'experience_years': person.experience_years or 0,
            'hard_skills_match': calculate_match_percentage(person.skills, vacancy.skills_required),
            'soft_skills_match': calculate_match_percentage(
                person.metadata.get("soft_skills", []),
                vacancy.metadata.get("soft_skills", [])
            ),
            'salary_alignment': calculate_alignment_percentage(
                person.salary_data.get("current_salary", 0),
                vacancy.salario or 0
            ),
            'age': (timezone.now().date() - person.fecha_nacimiento).days / 365
                if person.fecha_nacimiento else 0,
            'openness': person.openness,
            'conscientiousness': person.conscientiousness,
            'extraversion': person.extraversion,
            'agreeableness': person.agreeableness,
            'neuroticism': person.neuroticism
        }

        X = pd.DataFrame([features])
        proba = self.pipeline.predict_proba(X)[0][1]  # Probabilidad de éxito (clase 'hired')
        logger.info(f"Probabilidad de éxito para {person} en '{vacancy.titulo}': {proba:.2f}")
        return proba

    @shared_task(name='ml.predict_batch_matches', retry_backoff=True, retry_jitter=True, max_retries=3)
    def predict_batch(self, person_id, batch_vacancy_ids):
        """Predict matches for a batch of vacancies."""
        from app.models import Person, Vacante
        from app.ml.ml_utils import calculate_match_percentage, calculate_alignment_percentage
        person = Person.objects.get(id=person_id)
        batch_vacancies = Vacante.objects.filter(id__in=batch_vacancy_ids, status='activa')
        batch_predictions = []
        for vacancy in batch_vacancies:
            try:
                score = self.predict_candidate_success(person, vacancy)
                batch_predictions.append({
                    'vacancy_id': vacancy.id,
                    'score': score
                })
                logger.info(f"Predicted match for person {person_id} and vacancy {vacancy.id}: {score}")
            except Exception as e:
                logger.error(f"Error predicting match for person {person_id} and vacancy {vacancy.id}: {str(e)}")
        return batch_predictions

    def predict_all_active_matches(self, person, batch_size=50):
        """Predict matches for a person across all active vacancies with batch processing."""
        self.load_model()
        if not self.pipeline:
            raise FileNotFoundError("El modelo no está entrenado.")
        
        if self.business_unit:
            vacancies = Vacante.objects.filter(business_unit=self.business_unit, status='activa')
        else:
            vacancies = Vacante.objects.filter(status='activa')
        logger.info(f"Predicting matches for person {person.id} across {vacancies.count()} active vacancies")
        
        vacancy_ids = list(vacancies.values_list('id', flat=True))
        predictions = []
        for i in range(0, len(vacancy_ids), batch_size):
            batch_vacancy_ids = vacancy_ids[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1} with {len(batch_vacancy_ids)} vacancies")
            batch_result = self.predict_batch.delay(person.id, batch_vacancy_ids)
            batch_predictions = batch_result.get()  # Wait for the batch to complete
            predictions.extend(batch_predictions)
            logger.info(f"Batch {i // batch_size + 1} completed, {len(batch_predictions)} predictions made")
        
        sorted_predictions = sorted(predictions, key=lambda x: x['score'], reverse=True)
        return sorted_predictions[:10]  # Return top 10 matches

    # Métodos internos (sin cambios, están bien)
    def _calculate_hard_skills_match(self, application):
        from app.ml.ml_utils import calculate_match_percentage
        person_skills = (application.person.skills or "").split(',')
        job_skills = application.vacancy.skills_required or []
        return calculate_match_percentage(person_skills, job_skills)

    def _calculate_soft_skills_match(self, application):
        person_soft_skills = set(application.person.metadata.get('soft_skills', []))
        job_soft_skills = set(application.vacancy.metadata.get('soft_skills', []))
        if not job_soft_skills:
            return 0.0
        return (len(person_soft_skills.intersection(job_soft_skills)) / len(job_soft_skills)) * 100

    def _calculate_salary_alignment(self, application):
        from app.ml.ml_utils import calculate_alignment_percentage
        current_salary = application.person.salary_data.get('current_salary', 0)
        offered_salary = application.vacancy.salario or 0
        return calculate_alignment_percentage(current_salary, offered_salary)

    def _calculate_age(self, person):
        if not person.fecha_nacimiento:
            return 0
        return (timezone.now().date() - person.fecha_nacimiento).days / 365

    def _calculate_hard_skills_match_mock(self, person, vacancy):
        from app.ml.ml_utils import calculate_match_percentage
        person_skills = (person.skills or "").split(',')
        job_skills = vacancy.skills_required or []
        return calculate_match_percentage(person_skills, job_skills)

    def _calculate_soft_skills_match_mock(self, person, vacancy):
        p_soft = set(person.metadata.get("soft_skills", []))
        v_soft = set(vacancy.metadata.get("soft_skills", []))
        if not v_soft:
            return 0.0
        return (len(p_soft.intersection(v_soft)) / len(v_soft)) * 100

    def _calculate_salary_alignment_mock(self, person, vacancy):
        from app.ml.ml_utils import calculate_alignment_percentage
        cur_sal = person.salary_data.get('current_salary', 0)
        off_sal = vacancy.salario or 0
        return calculate_alignment_percentage(cur_sal, off_sal)
    
    def calculate_personality_similarity(self, person, vacancy):
        # Obtener rasgos del candidato (suponiendo que están en person.personality_traits como dict)
        candidate_traits = person.personality_traits or {}
        # Generar rasgos deseados si no están definidos
        desired_traits = vacancy.rasgos_deseados or generate_desired_traits(vacancy.skills_required or [])
        
        if not desired_traits:
            return 0.0
        
        similarity = 0.0
        trait_count = 0
        for trait, desired_value in desired_traits.items():
            candidate_value = candidate_traits.get(trait, 0)
            # Normalizar la diferencia (asumiendo escala de 0 a 5)
            similarity += 1 - abs(candidate_value - desired_value) / 5
            trait_count += 1
        
        return similarity / trait_count if trait_count > 0 else 0.0

    def recommend_skill_improvements(self, person):
        skill_gaps = self._identify_skill_gaps()
        person_skills = set(skill.strip().lower() for skill in (person.skills or "").split(','))
        recommendations = []
        for skill, importance in skill_gaps.items():
            if skill.lower() not in person_skills:
                recommendations.append({
                    'skill': skill,
                    'importance': importance,
                    'recommendation': f"Deberías desarrollar más la habilidad '{skill}'"
                })
        logger.info(f"Recomendaciones para {person}: {recommendations}")
        return recommendations

    def generate_quarterly_insights(self):
        insights = {
            'top_performing_skills': self._analyze_top_skills(),
            'success_rate_by_experience': self._analyze_experience_impact(),
            'salary_correlation': self._analyze_salary_impact()
        }
        logger.info(f"Insights trimestrales: {insights}")
        return insights

    def explain_prediction(self, person, vacancy):
        if not Path(self.model_file).exists():
            logger.error("Modelo no encontrado para explicar la predicción.")
            raise FileNotFoundError("Modelo no entrenado.")

        self.load_model()
        if not self._loaded_model:
            raise FileNotFoundError("El modelo no está cargado.")

        import shap
        explainer = shap.TreeExplainer(self._loaded_model['classifier'])
        features = [
            person.experience_years or 0,
            self._calculate_hard_skills_match_mock(person, vacancy),
            self._calculate_soft_skills_match_mock(person, vacancy),
            self._calculate_salary_alignment_mock(person, vacancy),
            self._calculate_age(person)
        ]
        shap_values = explainer.shap_values([features])
        logger.info(f"SHAP Values: {shap_values}")
        return shap_values

    def _identify_skill_gaps(self):
        return {
            'Python': 0.9,
            'Gestión de proyectos': 0.8,
            'Análisis de datos': 0.7
        }

    def _analyze_top_skills(self):
        from app.models import Application
        successful_apps = Application.objects.filter(status='contratado')
        skill_counts = {}
        for app in successful_apps:
            if not app.person.skills:
                continue
            skills = [s.strip().lower() for s in app.person.skills.split(',')]
            for skill in skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_skills[:10]

    def _analyze_experience_impact(self):
        from app.models import Application
        s_apps = Application.objects.filter(status='contratado')
        r_apps = Application.objects.filter(status='rechazado')
        exp_success = [app.person.experience_years or 0 for app in s_apps]
        exp_reject = [app.person.experience_years or 0 for app in r_apps]
        avg_succ = sum(exp_success) / len(exp_success) if exp_success else 0
        avg_reje = sum(exp_reject) / len(exp_reject) if exp_reject else 0
        return {
            "avg_experience_contratados": round(avg_succ, 2),
            "avg_experience_rechazados": round(avg_reje, 2),
            "difference": round(avg_succ - avg_reje, 2)
        }

    def _analyze_salary_impact(self):
        from app.models import Application, Vacante
        s_apps = Application.objects.filter(status='contratado')
        salary_diffs = []
        for app in s_apps:
            expected_salary = app.person.salary_data.get('expected_salary', 0)
            offered_salary = app.vacancy.salario if app.vacancy else 0
            if offered_salary:
                diff = abs(expected_salary - offered_salary) / offered_salary * 100
                salary_diffs.append(diff)
        avg_diff = sum(salary_diffs) / len(salary_diffs) if salary_diffs else 0
        aligned_count = sum(1 for d in salary_diffs if d < 10)
        return {
            "avg_salary_difference": round(avg_diff, 2),
            "aligned_candidates": aligned_count,
            "total_candidates": len(salary_diffs)
        }
    
    def load_transition_model(self):
        """Carga o inicializa el modelo de predicción de transiciones."""
        if not self._loaded_transition_model and os.path.exists(self.transition_model_file):
            self._loaded_transition_model = load(self.transition_model_file)
            logger.info(f"Modelo de transición cargado desde {self.transition_model_file}")
        elif not os.path.exists(self.transition_model_file):
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import Pipeline
            self.transition_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.transition_scaler = StandardScaler()
            self.transition_pipeline = Pipeline([
                ('scaler', self.transition_scaler),
                ('classifier', self.transition_model)
            ])
            logger.info("Modelo de transición RandomForest inicializado (no entrenado).")

    def prepare_transition_training_data(self):
        """Prepara datos para entrenar el modelo de transiciones entre BusinessUnits."""
        from app.models import Person, BusinessUnit, DivisionTransition
        # Datos de candidatos que han transicionado
        transitions = DivisionTransition.objects.select_related('person', 'from_business_unit', 'to_business_unit')
        data = []
        for transition in transitions:
            person = transition.person
            education_level = {
                'licenciatura': 1,
                'maestría': 2,
                'doctorado': 3
            }.get(person.metadata.get('education', [''])[0].lower(), 0)
            data.append({
                'experience_years': person.experience_years or 0,
                'skills_count': len(person.skills.split(',')) if person.skills else 0,
                'certifications_count': len(person.metadata.get('certifications', [])),
                'education_level': education_level,
                'openness': person.openness,
                'conscientiousness': person.conscientiousness,
                'extraversion': person.extraversion,
                'agreeableness': person.agreeableness,
                'neuroticism': person.neuroticism,
                'transition_label': 1 if transition.success else 0
            })
        # Datos de candidatos sin transiciones
        non_transitions = Person.objects.filter(divisiontransition__isnull=True)
        for person in non_transitions:
            education_level = {
                'licenciatura': 1,
                'maestría': 2,
                'doctorado': 3
            }.get(person.metadata.get('education', [''])[0].lower(), 0)
            data.append({
                'experience_years': person.experience_years or 0,
                'skills_count': len(person.skills.split(',')) if person.skills else 0,
                'certifications_count': len(person.metadata.get('certifications', [])),
                'education_level': education_level,
                'openness': person.openness,
                'conscientiousness': person.conscientiousness,
                'extraversion': person.extraversion,
                'agreeableness': person.agreeableness,
                'neuroticism': person.neuroticism,
                'transition_label': 0
            })
        df = pd.DataFrame(data)
        logger.info(f"Datos de transición preparados: {len(df)} registros.")
        return df

    def train_transition_model(self, df, test_size=0.2):
        """Entrena el modelo de transiciones con los datos preparados."""
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report
        X = df.drop(columns=["transition_label"])
        y = df["transition_label"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
        self.transition_pipeline.fit(X_train, y_train)
        dump(self.transition_pipeline, self.transition_model_file)
        logger.info(f"✅ Modelo de transición entrenado y guardado en {self.transition_model_file}")
        y_pred = self.transition_pipeline.predict(X_test)
        report = classification_report(y_test, y_pred)
        logger.info(f"Reporte de clasificación para transición:\n{report}")

    def predict_transition(self, person):
        """Predice la probabilidad de que un candidato esté listo para transicionar."""
        self.load_transition_model()
        if not self.transition_pipeline:
            raise FileNotFoundError("El modelo de transición no está entrenado.")
        education_level = {
            'licenciatura': 1,
            'maestría': 2,
            'doctorado': 3
        }.get(person.metadata.get('education', [''])[0].lower(), 0)
        features = {
            'experience_years': person.experience_years or 0,
            'skills_count': len(person.skills.split(',')) if person.skills else 0,
            'certifications_count': len(person.metadata.get('certifications', [])),
            'education_level': education_level,
            'openness': person.openness,
            'conscientiousness': person.conscientiousness,
            'extraversion': person.extraversion,
            'agreeableness': person.agreeableness,
            'neuroticism': person.neuroticism
        }
        X = pd.DataFrame([features])
        proba = self.transition_pipeline.predict_proba(X)[0][1]  # Probabilidad de transición
        logger.info(f"Probabilidad de transición para {person}: {proba:.2f}")
        return proba

    def get_possible_transitions(self, current_bu_name):
        """Obtiene las transiciones posibles desde la unidad de negocio actual."""
        current_level = BUSINESS_UNIT_HIERARCHY.get(current_bu_name.lower(), 0)
        possible_transitions = []
        for bu, level in BUSINESS_UNIT_HIERARCHY.items():
            if level > current_level:
                possible_transitions.append(bu)
        return possible_transitions
    
    async def calculate_market_alignment(self, features: Dict) -> Dict:
        """Calcula la alineación del candidato con el mercado laboral."""
        try:
            # Obtenemos datos del mercado
            market_data = await self._get_market_data()
            
            # Calculamos alineación por categoría
            alignment = {
                "skills": self._calculate_skills_alignment(features["skills"], market_data["skills"]),
                "experience": self._calculate_experience_alignment(features["experience"], market_data["experience"]),
                "salary": self._calculate_salary_alignment(features["salary_expectations"], market_data["salary"]),
                "personality": self._calculate_personality_alignment(features["personality_traits"], market_data["personality"])
            }
            
            # Calculamos score general
            alignment["overall_score"] = sum(alignment.values()) / len(alignment)
            
            return alignment
        except Exception as e:
            logger.error(f"Error calculando alineación con el mercado: {str(e)}", exc_info=True)
            return {}
    
    async def _get_market_data(self) -> Dict:
        """Obtiene datos actualizados del mercado laboral."""
        try:
            # Intentamos obtener de caché primero
            market_data = cache.get("market_data")
            if market_data:
                return market_data
            
            # Si no está en caché, lo generamos
            market_data = {
                "skills": await self._analyze_market_skills(),
                "experience": await self._analyze_market_experience(),
                "salary": await self._analyze_market_salaries(),
                "personality": await self._analyze_market_personality()
            }
            
            # Guardamos en caché por 24 horas
            cache.set("market_data", market_data, 86400)
            
            return market_data
        except Exception as e:
            logger.error(f"Error obteniendo datos del mercado: {str(e)}", exc_info=True)
            return {}
    
    async def _analyze_market_skills(self) -> Dict:
        """Analiza las habilidades más demandadas en el mercado."""
        try:
            from app.models import Vacancy, Skill
            
            # Obtenemos todas las vacantes activas
            vacancies = Vacancy.objects.filter(status="active")
            
            # Analizamos habilidades requeridas
            skills_analysis = {}
            for vacancy in vacancies:
                for skill in vacancy.required_skills.all():
                    skills_analysis[skill.name] = skills_analysis.get(skill.name, 0) + 1
            
            # Normalizamos y ordenamos
            total_vacancies = vacancies.count()
            return {
                skill: count/total_vacancies 
                for skill, count in sorted(
                    skills_analysis.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
            }
        except Exception as e:
            logger.error(f"Error analizando habilidades del mercado: {str(e)}", exc_info=True)
            return {}
    
    async def _analyze_market_experience(self) -> Dict:
        """Analiza los requisitos de experiencia en el mercado."""
        try:
            from app.models import Vacancy
            
            # Obtenemos todas las vacantes activas
            vacancies = Vacancy.objects.filter(status="active")
            
            # Analizamos rangos de experiencia
            experience_ranges = {
                "0-2": 0,
                "2-5": 0,
                "5-10": 0,
                "10+": 0
            }
            
            for vacancy in vacancies:
                exp_years = vacancy.experience_years or 0
                if exp_years <= 2:
                    experience_ranges["0-2"] += 1
                elif exp_years <= 5:
                    experience_ranges["2-5"] += 1
                elif exp_years <= 10:
                    experience_ranges["5-10"] += 1
                else:
                    experience_ranges["10+"] += 1
            
            # Normalizamos
            total_vacancies = vacancies.count()
            return {
                range_name: count/total_vacancies 
                for range_name, count in experience_ranges.items()
            }
        except Exception as e:
            logger.error(f"Error analizando experiencia del mercado: {str(e)}", exc_info=True)
            return {}
    
    async def _analyze_market_salaries(self) -> Dict:
        """Analiza los rangos salariales en el mercado."""
        try:
            from app.models import Vacancy
            
            # Obtenemos todas las vacantes activas
            vacancies = Vacancy.objects.filter(status="active")
            
            # Analizamos rangos salariales
            salary_ranges = {
                "0-30000": 0,
                "30000-60000": 0,
                "60000-90000": 0,
                "90000+": 0
            }
            
            for vacancy in vacancies:
                salary = vacancy.salario or 0
                if salary <= 30000:
                    salary_ranges["0-30000"] += 1
                elif salary <= 60000:
                    salary_ranges["30000-60000"] += 1
                elif salary <= 90000:
                    salary_ranges["60000-90000"] += 1
                else:
                    salary_ranges["90000+"] += 1
            
            # Normalizamos
            total_vacancies = vacancies.count()
            return {
                range_name: count/total_vacancies 
                for range_name, count in salary_ranges.items()
            }
        except Exception as e:
            logger.error(f"Error analizando salarios del mercado: {str(e)}", exc_info=True)
            return {}
    
    async def _analyze_market_personality(self) -> Dict:
        """Analiza los rasgos de personalidad más valorados en el mercado."""
        try:
            from app.models import Vacancy
            
            # Obtenemos todas las vacantes activas
            vacancies = Vacancy.objects.filter(status="active")
            
            # Analizamos rasgos de personalidad
            personality_traits = {}
            for vacancy in vacancies:
                for trait in vacancy.metadata.get("personality_traits", []):
                    personality_traits[trait] = personality_traits.get(trait, 0) + 1
            
            # Normalizamos y ordenamos
            total_vacancies = vacancies.count()
            return {
                trait: count/total_vacancies 
                for trait, count in sorted(
                    personality_traits.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
            }
        except Exception as e:
            logger.error(f"Error analizando personalidad del mercado: {str(e)}", exc_info=True)
            return {}
    
    def _calculate_skills_alignment(self, candidate_skills: List[str], market_skills: Dict) -> float:
        """Calcula la alineación de habilidades del candidato con el mercado."""
        try:
            if not candidate_skills or not market_skills:
                return 0.0
            
            # Calculamos score para cada habilidad
            total_score = 0.0
            for skill in candidate_skills:
                total_score += market_skills.get(skill, 0)
            
            # Normalizamos
            return total_score / len(candidate_skills)
        except Exception as e:
            logger.error(f"Error calculando alineación de habilidades: {str(e)}", exc_info=True)
            return 0.0
    
    def _calculate_experience_alignment(self, candidate_experience: List[Dict], market_experience: Dict) -> float:
        """Calcula la alineación de experiencia del candidato con el mercado."""
        try:
            if not candidate_experience or not market_experience:
                return 0.0
            
            # Calculamos años totales de experiencia
            total_years = sum(exp.get("years", 0) for exp in candidate_experience)
            
            # Determinamos el rango
            if total_years <= 2:
                range_key = "0-2"
            elif total_years <= 5:
                range_key = "2-5"
            elif total_years <= 10:
                range_key = "5-10"
            else:
                range_key = "10+"
            
            return market_experience.get(range_key, 0)
        except Exception as e:
            logger.error(f"Error calculando alineación de experiencia: {str(e)}", exc_info=True)
            return 0.0
    
    def _calculate_salary_alignment(self, candidate_salary: Dict, market_salary: Dict) -> float:
        """Calcula la alineación salarial del candidato con el mercado."""
        try:
            if not candidate_salary or not market_salary:
                return 0.0
            
            expected_salary = candidate_salary.get("expected", 0)
            
            # Determinamos el rango
            if expected_salary <= 30000:
                range_key = "0-30000"
            elif expected_salary <= 60000:
                range_key = "30000-60000"
            elif expected_salary <= 90000:
                range_key = "60000-90000"
            else:
                range_key = "90000+"
            
            return market_salary.get(range_key, 0)
        except Exception as e:
            logger.error(f"Error calculando alineación salarial: {str(e)}", exc_info=True)
            return 0.0
    
    def _calculate_personality_alignment(self, candidate_traits: Dict, market_traits: Dict) -> float:
        """Calcula la alineación de personalidad del candidato con el mercado."""
        try:
            if not candidate_traits or not market_traits:
                return 0.0
            
            # Calculamos score para cada rasgo
            total_score = 0.0
            for trait, value in candidate_traits.items():
                total_score += market_traits.get(trait, 0) * value
            
            # Normalizamos
            return total_score / len(candidate_traits)
        except Exception as e:
            logger.error(f"Error calculando alineación de personalidad: {str(e)}", exc_info=True)
            return 0.0
    
    def _initialize_models(self) -> None:
        """
        Inicializa los modelos con datos de entrenamiento.
        
        Este método carga los datos de entrenamiento y entrena los modelos
        específicos para personalidad y profesional.
        """
        try:
            # Aquí se cargarían los datos de entrenamiento y se entrenarían los modelos
            # Por ahora, los modelos se inicializan vacíos
            pass
        except Exception as e:
            logger.error(f"Error inicializando modelos: {str(e)}")

    def predict_compatibility(self, traits: Dict[str, float]) -> Dict[str, float]:
        """
        Predice la compatibilidad con diferentes perfiles.
        
        Args:
            traits: Diccionario con rasgos de personalidad
            
        Returns:
            Dict con puntuaciones de compatibilidad
        """
        try:
            # Convertir rasgos a vector
            trait_vector = self._dict_to_vector(traits)
            
            # Normalizar vector
            normalized_vector = self.scaler.transform([trait_vector])[0]
            
            # Predecir compatibilidad
            compatibility_scores = self.personality_model.predict_proba([normalized_vector])[0]
            
            # Mapear scores a perfiles
            profiles = ['Analítico', 'Creativo', 'Social', 'Estructurado']
            return dict(zip(profiles, compatibility_scores))
            
        except Exception as e:
            logger.error(f"Error prediciendo compatibilidad: {str(e)}")
            return {}

    def _dict_to_vector(self, data: Dict[str, float]) -> np.ndarray:
        """
        Convierte un diccionario de características en un vector numérico.
        """
        # Codificar variables categóricas
        transport_mode_map = {'car': 0, 'public_transport': 1, 'walking': 2}
        location_type_map = {'work': 0, 'study': 1, 'home': 2}
        zone_map = {zone: idx for idx, zone in enumerate(self._get_zones().keys())}
        
        return np.array([
            transport_mode_map.get(data['transport_mode'], 0),
            zone_map.get(data['zone'], 0),
            location_type_map.get(data['location_type'], 0),
            data['time_of_day'] / 24.0  # Normalizar hora del día
        ])

    async def _add_location_success_note(self, person: Person, vacancy: Vacante, success_score: float):
        """
        Agrega una nota de éxito de ubicación para aprendizaje futuro.
        """
        try:
            zones = self._get_zones()
            person_zone = self._get_zone(person.location, zones)
            transport_prefs = self._get_transport_mode(person, vacancy)
            
            note = LocationSuccessNote(
                business_unit=vacancy.business_unit,
                location_type='work',
                zone=person_zone,
                transport_mode=transport_prefs['primary'],
                success_score=success_score,
                notes=f"Candidato: {person.id}, Vacante: {vacancy.id}, Score: {success_score}"
            )
            
            if person.is_student:
                note.location_type = 'study'
                note.notes += f", Ubicación estudios: {person.study_location}"
            
            note.save()
            
            # Actualizar modelo de aprendizaje
            await self._update_location_learning_model(note)
            
        except Exception as e:
            logger.error(f"Error agregando nota de éxito: {str(e)}")
    
    async def _update_location_learning_model(self, note: LocationSuccessNote):
        """
        Actualiza el modelo de aprendizaje con nuevos casos de éxito.
        """
        try:
            # Obtener datos históricos
            historical_notes = LocationSuccessNote.objects.filter(
                business_unit=note.business_unit,
                location_type=note.location_type,
                zone=note.zone
            ).order_by('-created_at')[:100]
            
            if not historical_notes:
                return
            
            # Preparar datos para aprendizaje
            X = []
            y = []
            
            for hist_note in historical_notes:
                features = {
                    'transport_mode': hist_note.transport_mode,
                    'zone': hist_note.zone,
                    'location_type': hist_note.location_type,
                    'time_of_day': hist_note.created_at.hour
                }
                X.append(self._dict_to_vector(features))
                y.append(hist_note.success_score)
            
            # Actualizar modelo
            if not hasattr(self, '_location_model'):
                self._location_model = RandomForestRegressor(n_estimators=100)
            
            self._location_model.fit(X, y)
            
        except Exception as e:
            logger.error(f"Error actualizando modelo de aprendizaje: {str(e)}")
    
    async def _get_learned_location_score(self, person: Person, vacancy: Vacante) -> float:
        """
        Obtiene un score de ubicación basado en el aprendizaje automático.
        """
        try:
            if not hasattr(self, '_location_model'):
                return 0.5
            
            zones = self._get_zones()
            person_zone = self._get_zone(person.location, zones)
            transport_prefs = self._get_transport_mode(person, vacancy)
            
            features = {
                'transport_mode': transport_prefs['primary'],
                'zone': person_zone,
                'location_type': 'study' if person.is_student else 'work',
                'time_of_day': datetime.now().hour
            }
            
            X = self._dict_to_vector(features)
            score = self._location_model.predict([X])[0]
            
            return min(1.0, max(0.0, score))
            
        except Exception as e:
            logger.error(f"Error obteniendo score aprendido: {str(e)}")
            return 0.5

    async def _add_interaction_success_note(self, 
                                          business_unit: BusinessUnit,
                                          interaction_type: str,
                                          channel: str,
                                          success_score: float,
                                          response_time: Optional[int] = None,
                                          notes: str = ""):
        """
        Agrega una nota de éxito de interacción para aprendizaje futuro.
        """
        try:
            note = InteractionSuccessNote(
                business_unit=business_unit,
                interaction_type=interaction_type,
                channel=channel,
                time_of_day=datetime.now().hour,
                day_of_week=datetime.now().weekday(),
                success_score=success_score,
                response_time=response_time,
                notes=notes
            )
            note.save()
            
            # Actualizar modelo de aprendizaje
            await self._update_interaction_learning_model(note)
            
        except Exception as e:
            logger.error(f"Error agregando nota de interacción: {str(e)}")
    
    async def _update_interaction_learning_model(self, note: InteractionSuccessNote):
        """
        Actualiza el modelo de aprendizaje de interacciones.
        """
        try:
            # Obtener datos históricos
            historical_notes = InteractionSuccessNote.objects.filter(
                business_unit=note.business_unit,
                interaction_type=note.interaction_type
            ).order_by('-created_at')[:1000]
            
            if not historical_notes:
                return
            
            # Preparar datos para aprendizaje
            X = []
            y = []
            
            for hist_note in historical_notes:
                features = {
                    'channel': hist_note.channel,
                    'time_of_day': hist_note.time_of_day,
                    'day_of_week': hist_note.day_of_week
                }
                X.append(self._dict_to_interaction_vector(features))
                y.append(hist_note.success_score)
            
            # Actualizar modelo
            if not hasattr(self, '_interaction_model'):
                self._interaction_model = RandomForestRegressor(n_estimators=100)
            
            self._interaction_model.fit(X, y)
            
        except Exception as e:
            logger.error(f"Error actualizando modelo de interacciones: {str(e)}")
    
    async def get_optimal_notification_time(self, 
                                          business_unit: BusinessUnit,
                                          channel: str) -> Dict[str, Any]:
        """
        Determina el mejor momento para enviar notificaciones.
        """
        try:
            if not hasattr(self, '_interaction_model'):
                return {'time_of_day': 10, 'day_of_week': 1}  # Valores por defecto
            
            # Generar todas las combinaciones posibles
            best_score = 0
            best_time = None
            
            for hour in range(24):
                for day in range(7):
                    features = {
                        'channel': channel,
                        'time_of_day': hour,
                        'day_of_week': day
                    }
                    X = self._dict_to_interaction_vector(features)
                    score = self._interaction_model.predict([X])[0]
                    
                    if score > best_score:
                        best_score = score
                        best_time = {'time_of_day': hour, 'day_of_week': day}
            
            return best_time or {'time_of_day': 10, 'day_of_week': 1}
            
        except Exception as e:
            logger.error(f"Error obteniendo tiempo óptimo: {str(e)}")
            return {'time_of_day': 10, 'day_of_week': 1}
    
    def _dict_to_interaction_vector(self, data: Dict[str, Any]) -> np.ndarray:
        """
        Convierte características de interacción a vector numérico.
        """
        channel_map = {'email': 0, 'whatsapp': 1, 'sms': 2}
        
        return np.array([
            channel_map.get(data['channel'], 0),
            data['time_of_day'] / 24.0,  # Normalizar hora
            data['day_of_week'] / 7.0    # Normalizar día
        ])

    async def _analyze_candidate_patterns(self, person: Person) -> Dict[str, Any]:
        """
        Analiza patrones del candidato para mejorar el matching.
        """
        try:
            # Obtener historial de aplicaciones
            applications = await self._get_candidate_applications(person)
            
            patterns = {
                'preferred_zones': self._analyze_preferred_zones(applications),
                'preferred_schedules': self._analyze_preferred_schedules(applications),
                'successful_matches': self._analyze_successful_matches(applications),
                'response_times': self._analyze_response_times(applications),
                'skill_evolution': self._analyze_skill_evolution(person)
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analizando patrones: {str(e)}")
            return {}
    
    def _analyze_preferred_zones(self, applications: List[Dict]) -> Dict[str, float]:
        """
        Analiza las zonas preferidas del candidato.
        """
        try:
            zone_counts = {}
            total = len(applications)
            
            for app in applications:
                zone = self._get_zone(app['location'], self._get_zones())
                if zone:
                    zone_counts[zone] = zone_counts.get(zone, 0) + 1
            
            return {zone: count/total for zone, count in zone_counts.items()}
            
        except Exception as e:
            logger.error(f"Error analizando zonas preferidas: {str(e)}")
            return {}
    
    def _analyze_preferred_schedules(self, applications: List[Dict]) -> Dict[str, Any]:
        """
        Analiza los horarios preferidos del candidato.
        """
        try:
            schedule_counts = {
                'morning': 0,
                'afternoon': 0,
                'evening': 0,
                'night': 0
            }
            
            for app in applications:
                hour = app['created_at'].hour
                if 6 <= hour < 12:
                    schedule_counts['morning'] += 1
                elif 12 <= hour < 17:
                    schedule_counts['afternoon'] += 1
                elif 17 <= hour < 22:
                    schedule_counts['evening'] += 1
                else:
                    schedule_counts['night'] += 1
            
            return schedule_counts
            
        except Exception as e:
            logger.error(f"Error analizando horarios preferidos: {str(e)}")
            return {}
    
    def _analyze_successful_matches(self, applications: List[Dict]) -> Dict[str, Any]:
        """
        Analiza los matches exitosos del candidato.
        """
        try:
            successful = [app for app in applications if app['status'] == 'hired']
            
            return {
                'total_matches': len(successful),
                'avg_match_score': sum(app['match_score'] for app in successful) / len(successful) if successful else 0,
                'common_skills': self._get_common_skills(successful),
                'preferred_roles': self._get_preferred_roles(successful)
            }
            
        except Exception as e:
            logger.error(f"Error analizando matches exitosos: {str(e)}")
            return {}
    
    def _analyze_response_times(self, applications: List[Dict]) -> Dict[str, Any]:
        """
        Analiza los tiempos de respuesta del candidato.
        """
        try:
            response_times = []
            for app in applications:
                if app['response_time']:
                    response_times.append(app['response_time'])
            
            if not response_times:
                return {}
            
            return {
                'avg_response_time': sum(response_times) / len(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'response_rate': len(response_times) / len(applications)
            }
            
        except Exception as e:
            logger.error(f"Error analizando tiempos de respuesta: {str(e)}")
            return {}
    
    def _analyze_skill_evolution(self, person: Person) -> Dict[str, Any]:
        """
        Analiza la evolución de habilidades del candidato.
        """
        try:
            skill_history = person.skill_history if hasattr(person, 'skill_history') else []
            
            if not skill_history:
                return {}
            
            current_skills = set(person.skills)
            skill_evolution = {}
            
            for skill in current_skills:
                skill_evolution[skill] = {
                    'first_seen': None,
                    'improvement_rate': 0,
                    'current_level': 0
                }
                
                for record in skill_history:
                    if skill in record['skills']:
                        if not skill_evolution[skill]['first_seen']:
                            skill_evolution[skill]['first_seen'] = record['date']
                        skill_evolution[skill]['current_level'] = record['skills'][skill]
            
            return skill_evolution
            
        except Exception as e:
            logger.error(f"Error analizando evolución de habilidades: {str(e)}")
            return {}
    
    async def _get_candidate_applications(self, person: Person) -> List[Dict]:
        """
        Obtiene el historial de aplicaciones del candidato.
        """
        try:
            # Implementar obtención de aplicaciones
            return []
        except Exception as e:
            logger.error(f"Error obteniendo aplicaciones: {str(e)}")
            return []
    
    def _get_common_skills(self, applications: List[Dict]) -> List[str]:
        """
        Obtiene las habilidades más comunes en matches exitosos.
        """
        try:
            skill_counts = {}
            for app in applications:
                for skill in app['skills']:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
            
            return sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            logger.error(f"Error obteniendo habilidades comunes: {str(e)}")
            return []
    
    def _get_preferred_roles(self, applications: List[Dict]) -> List[str]:
        """
        Obtiene los roles preferidos del candidato.
        """
        try:
            role_counts = {}
            for app in applications:
                role = app['role']
                role_counts[role] = role_counts.get(role, 0) + 1
            
            return sorted(role_counts.items(), key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            logger.error(f"Error obteniendo roles preferidos: {str(e)}")
            return []

    async def analyze_profile_gaps(self, person: Person, vacancy: Vacante) -> Dict[str, Any]:
        """
        Analiza las brechas en el perfil y genera recomendaciones para mejorar.
        
        Args:
            person: Persona a analizar
            vacancy: Vacante de referencia
            
        Returns:
            Dict con análisis de brechas y recomendaciones
        """
        try:
            # Obtener nivel de perfil actual
            profile_level = self._get_profile_level(person)
            
            # Analizar brechas por categoría
            gaps = {
                'skills': await self._analyze_skills_gaps(person, vacancy),
                'experience': await self._analyze_experience_gaps(person, vacancy),
                'location': await self._analyze_location_gaps(person, vacancy),
                'culture': await self._analyze_culture_gaps(person, vacancy),
                'education': await self._analyze_education_gaps(person, vacancy)
            }
            
            # Generar recomendaciones específicas
            recommendations = self._generate_profile_recommendations(gaps, profile_level, vacancy.business_unit)
            
            # Calcular impacto potencial
            potential_impact = self._calculate_potential_impact(gaps, vacancy.business_unit)
            
            return {
                'profile_level': profile_level,
                'gaps': gaps,
                'recommendations': recommendations,
                'potential_impact': potential_impact,
                'next_steps': self._get_next_steps(gaps, profile_level)
            }
            
        except Exception as e:
            logger.error(f"Error analizando brechas de perfil: {str(e)}")
            return {}
            
    async def _analyze_skills_gaps(self, person: Person, vacancy: Vacante) -> Dict[str, Any]:
        """Analiza brechas en habilidades."""
        try:
            gaps = {
                'missing_skills': [],
                'skill_level_gaps': [],
                'recommended_skills': []
            }
            
            # Obtener habilidades requeridas
            required_skills = vacancy.skills_required or []
            
            # Analizar habilidades faltantes
            if person.skills:
                person_skills = set(person.skills)
                for skill in required_skills:
                    if skill['name'] not in person_skills:
                        gaps['missing_skills'].append({
                            'skill': skill['name'],
                            'importance': skill.get('importance', 0.5),
                            'priority': 'high' if skill.get('importance', 0) > 0.7 else 'medium'
                        })
            
            # Analizar nivel de habilidades
            if person.skill_levels:
                for skill in required_skills:
                    if skill['name'] in person.skill_levels:
                        current_level = person.skill_levels[skill['name']]
                        required_level = skill.get('level', 3)
                        if current_level < required_level:
                            gaps['skill_level_gaps'].append({
                                'skill': skill['name'],
                                'current_level': current_level,
                                'required_level': required_level,
                                'gap': required_level - current_level
                            })
            
            # Generar recomendaciones de habilidades
            gaps['recommended_skills'] = self._get_recommended_skills(
                gaps['missing_skills'],
                gaps['skill_level_gaps'],
                vacancy.business_unit
            )
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error analizando brechas de habilidades: {str(e)}")
            return {}
            
    async def _analyze_experience_gaps(self, person: Person, vacancy: Vacante) -> Dict[str, Any]:
        """Analiza brechas en experiencia."""
        try:
            gaps = {
                'years_gap': 0,
                'industry_gap': False,
                'role_gap': False,
                'recommendations': []
            }
            
            # Analizar años de experiencia
            required_exp = vacancy.metadata.get('required_experience', 0)
            person_exp = person.metadata.get('experience_years', 0)
            if person_exp < required_exp:
                gaps['years_gap'] = required_exp - person_exp
            
            # Analizar experiencia en industria
            if vacancy.industry and person.experience:
                has_industry_exp = any(
                    exp.get('industry') == vacancy.industry 
                    for exp in person.experience
                )
                gaps['industry_gap'] = not has_industry_exp
            
            # Analizar experiencia en rol
            if vacancy.role and person.experience:
                has_role_exp = any(
                    exp.get('role') == vacancy.role 
                    for exp in person.experience
                )
                gaps['role_gap'] = not has_role_exp
            
            # Generar recomendaciones
            gaps['recommendations'] = self._get_experience_recommendations(
                gaps,
                vacancy.business_unit
            )
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error analizando brechas de experiencia: {str(e)}")
            return {}
            
    async def _analyze_location_gaps(self, person: Person, vacancy: Vacante) -> Dict[str, Any]:
        """Analiza brechas en ubicación."""
        try:
            gaps = {
                'distance_gap': 0,
                'transport_gap': False,
                'zone_gap': False,
                'recommendations': []
            }
            
            # Analizar distancia
            if person.location and vacancy.location:
                distance = await self._calculate_distance(
                    person.location,
                    vacancy.location
                )
                max_distance = self._get_max_distance(vacancy.business_unit)
                if distance > max_distance:
                    gaps['distance_gap'] = distance - max_distance
            
            # Analizar transporte
            transport_prefs = self._get_transport_mode(person, vacancy)
            if transport_prefs['primary'] == 'car' and not person.has_car:
                gaps['transport_gap'] = True
            
            # Analizar zona
            zones = self._get_zones()
            person_zone = self._get_zone(person.location, zones)
            vacancy_zone = self._get_zone(vacancy.location, zones)
            if not self._are_adjacent_zones(person_zone, vacancy_zone):
                gaps['zone_gap'] = True
            
            # Generar recomendaciones
            gaps['recommendations'] = self._get_location_recommendations(
                gaps,
                vacancy.business_unit
            )
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error analizando brechas de ubicación: {str(e)}")
            return {}
            
    def _generate_profile_recommendations(self, gaps: Dict[str, Any], profile_level: str, business_unit: BusinessUnit) -> List[Dict[str, Any]]:
        """Genera recomendaciones específicas para mejorar el perfil."""
        try:
            recommendations = []
            
            # Recomendaciones por nivel de perfil
            if profile_level == 'basic':
                # Enfocarse en información fundamental
                if gaps['skills']['missing_skills']:
                    recommendations.append({
                        'type': 'skill',
                        'priority': 'high',
                        'message': 'Completa tu perfil con las habilidades básicas requeridas',
                        'skills': [s['skill'] for s in gaps['skills']['missing_skills'] if s['priority'] == 'high']
                    })
                
                if gaps['location']['distance_gap'] > 0:
                    recommendations.append({
                        'type': 'location',
                        'priority': 'high',
                        'message': 'Considera oportunidades más cercanas a tu ubicación actual'
                    })
                    
            elif profile_level == 'intermediate':
                # Enfocarse en desarrollo profesional
                if gaps['experience']['years_gap'] > 0:
                    recommendations.append({
                        'type': 'experience',
                        'priority': 'medium',
                        'message': f'Busca oportunidades para ganar {gaps["experience"]["years_gap"]} años más de experiencia'
                    })
                
                if gaps['skills']['skill_level_gaps']:
                    recommendations.append({
                        'type': 'skill_development',
                        'priority': 'medium',
                        'message': 'Mejora el nivel de tus habilidades actuales',
                        'skills': gaps['skills']['skill_level_gaps']
                    })
                    
            else:  # complete
                # Enfocarse en especialización y liderazgo
                if gaps['culture']['missing_traits']:
                    recommendations.append({
                        'type': 'culture',
                        'priority': 'low',
                        'message': 'Desarrolla rasgos culturales adicionales',
                        'traits': gaps['culture']['missing_traits']
                    })
                
                if gaps['education']['missing_certifications']:
                    recommendations.append({
                        'type': 'education',
                        'priority': 'low',
                        'message': 'Considera obtener certificaciones adicionales',
                        'certifications': gaps['education']['missing_certifications']
                    })
            
            # Ajustar recomendaciones según unidad de negocio
            if business_unit.name.lower() == 'huntred_executive':
                recommendations.extend(self._get_executive_recommendations(gaps))
            elif business_unit.name.lower() == 'huntu':
                recommendations.extend(self._get_student_recommendations(gaps))
            elif business_unit.name.lower() == 'amigro':
                recommendations.extend(self._get_amigro_recommendations(gaps))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            return []
            
    def _get_next_steps(self, gaps: Dict[str, Any], profile_level: str) -> List[Dict[str, Any]]:
        """Genera pasos específicos para mejorar el perfil."""
        try:
            next_steps = []
            
            # Pasos inmediatos
            if profile_level == 'basic':
                next_steps.append({
                    'step': 'complete_basic_info',
                    'priority': 'high',
                    'description': 'Completa tu información básica en el perfil',
                    'estimated_time': '5 minutos'
                })
                
                if gaps['skills']['missing_skills']:
                    next_steps.append({
                        'step': 'add_skills',
                        'priority': 'high',
                        'description': 'Agrega tus habilidades principales',
                        'estimated_time': '10 minutos'
                    })
                    
            # Pasos a medio plazo
            if profile_level in ['intermediate', 'complete']:
                if gaps['experience']['years_gap'] > 0:
                    next_steps.append({
                        'step': 'gain_experience',
                        'priority': 'medium',
                        'description': f'Busca oportunidades para ganar {gaps["experience"]["years_gap"]} años de experiencia',
                        'estimated_time': '6-12 meses'
                    })
                
                if gaps['skills']['skill_level_gaps']:
                    next_steps.append({
                        'step': 'improve_skills',
                        'priority': 'medium',
                        'description': 'Mejora el nivel de tus habilidades actuales',
                        'estimated_time': '3-6 meses'
                    })
            
            return next_steps
            
        except Exception as e:
            logger.error(f"Error generando pasos siguientes: {str(e)}")
            return []
            
    def _calculate_potential_impact(self, gaps: Dict[str, Any], business_unit: BusinessUnit) -> Dict[str, Any]:
        """Calcula el impacto potencial de mejorar el perfil."""
        try:
            impact = {
                'score_improvement': 0.0,
                'opportunity_increase': 0.0,
                'salary_potential': 0.0
            }
            
            # Calcular mejora en score
            if gaps['skills']['missing_skills']:
                impact['score_improvement'] += 0.2
            if gaps['experience']['years_gap'] > 0:
                impact['score_improvement'] += 0.15
            if gaps['location']['distance_gap'] > 0:
                impact['score_improvement'] += 0.1
                
            # Calcular aumento en oportunidades
            if business_unit.name.lower() == 'huntred_executive':
                impact['opportunity_increase'] = 0.3
                impact['salary_potential'] = 0.4
            elif business_unit.name.lower() == 'huntu':
                impact['opportunity_increase'] = 0.2
                impact['salary_potential'] = 0.2
            elif business_unit.name.lower() == 'amigro':
                impact['opportunity_increase'] = 0.15
                impact['salary_potential'] = 0.1
                
            return impact
            
        except Exception as e:
            logger.error(f"Error calculando impacto potencial: {str(e)}")
            return {}

    async def get_preselection_candidates(self, vacancy: Vacante, num_candidates: int = 8) -> Dict[str, Any]:
        """
        Obtiene una lista ampliada de candidatos para pre-selección por el Managing Partner.
        
        Args:
            vacancy: La vacante para la cual buscar candidatos
            num_candidates: Número de candidatos a pre-seleccionar (default: 8)
            
        Returns:
            Dict con candidatos pre-seleccionados y sus scores
        """
        try:
            # Obtener candidatos con scores
            candidates = await self._get_candidates_with_scores(vacancy)
            
            # Ordenar por score
            sorted_candidates = sorted(
                candidates,
                key=lambda x: x['match_score'],
                reverse=True
            )
            
            # Tomar los primeros num_candidates
            preselection = sorted_candidates[:num_candidates]
            
            # Preparar datos para feedback
            feedback_data = {
                'vacancy_id': vacancy.id,
                'vacancy_title': vacancy.titulo,
                'candidates': [
                    {
                        'id': c['candidate'].id,
                        'name': c['candidate'].nombre,
                        'match_score': c['match_score'],
                        'skills_match': c['skills_match'],
                        'experience_match': c['experience_match'],
                        'location_match': c['location_match'],
                        'cultural_fit': c['cultural_fit'],
                        'key_strengths': self._get_key_strengths(c['candidate'], vacancy),
                        'potential_concerns': self._get_potential_concerns(c['candidate'], vacancy)
                    }
                    for c in preselection
                ],
                'created_at': timezone.now(),
                'status': 'pending_review'
            }
            
            # Guardar pre-selección para revisión
            await self._save_preselection(feedback_data)
            
            return feedback_data
            
        except Exception as e:
            logger.error(f"Error en pre-selección de candidatos: {str(e)}")
            return {}

    async def process_mp_feedback(self, preselection_id: int, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa el feedback del Managing Partner sobre los candidatos pre-seleccionados.
        
        Args:
            preselection_id: ID de la pre-selección
            feedback: Dict con el feedback del MP
                {
                    'selected_candidates': [id1, id2, ...],
                    'rejected_candidates': [id1, id2, ...],
                    'feedback_notes': {
                        'id1': 'notas sobre el candidato 1',
                        'id2': 'notas sobre el candidato 2',
                        ...
                    },
                    'additional_requirements': ['req1', 'req2', ...]
                }
        """
        try:
            # Obtener pre-selección
            preselection = await self._get_preselection(preselection_id)
            if not preselection:
                raise ValueError("Pre-selección no encontrada")
            
            # Actualizar estado
            preselection['status'] = 'mp_reviewed'
            preselection['mp_feedback'] = feedback
            preselection['reviewed_at'] = timezone.now()
            
            # Guardar feedback
            await self._save_preselection(preselection)
            
            # Aprender del feedback
            await self._learn_from_mp_feedback(preselection, feedback)
            
            # Preparar candidatos finales
            final_candidates = [
                c for c in preselection['candidates']
                if c['id'] in feedback['selected_candidates']
            ]
            
            return {
                'success': True,
                'final_candidates': final_candidates,
                'learning_points': await self._get_learning_points(feedback)
            }
            
        except Exception as e:
            logger.error(f"Error procesando feedback del MP: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _learn_from_mp_feedback(self, preselection: Dict, feedback: Dict) -> None:
        """
        Aprende del feedback del Managing Partner para mejorar futuras selecciones.
        """
        try:
            # Analizar patrones en candidatos seleccionados
            selected_patterns = await self._analyze_selected_patterns(
                [c for c in preselection['candidates'] 
                 if c['id'] in feedback['selected_candidates']]
            )
            
            # Analizar patrones en candidatos rechazados
            rejected_patterns = await self._analyze_rejected_patterns(
                [c for c in preselection['candidates']
                 if c['id'] in feedback['rejected_candidates']]
            )
            
            # Actualizar pesos del modelo
            await self._update_model_weights(selected_patterns, rejected_patterns)
            
            # Guardar insights
            await self._save_learning_insights({
                'selected_patterns': selected_patterns,
                'rejected_patterns': rejected_patterns,
                'feedback_notes': feedback['feedback_notes'],
                'additional_requirements': feedback.get('additional_requirements', [])
            })
            
        except Exception as e:
            logger.error(f"Error aprendiendo del feedback: {str(e)}")

    async def _get_key_strengths(self, candidate: Person, vacancy: Vacante) -> List[str]:
        """
        Identifica las fortalezas clave del candidato para la vacante.
        """
        strengths = []
        
        # Analizar habilidades
        if candidate.skills:
            candidate_skills = set(skill.strip().lower() for skill in candidate.skills.split(','))
            required_skills = set(skill.strip().lower() for skill in vacancy.palabras_clave)
            matching_skills = candidate_skills.intersection(required_skills)
            if matching_skills:
                strengths.append(f"Habilidades técnicas destacadas: {', '.join(matching_skills)}")
        
        # Analizar experiencia
        if candidate.experience_years and vacancy.metadata.get('required_experience'):
            if candidate.experience_years >= vacancy.metadata['required_experience']:
                strengths.append(f"Experiencia superior a la requerida ({candidate.experience_years} años)")
        
        # Analizar ubicación
        if candidate.location and vacancy.location:
            if self._calculate_zone_score(candidate.location, vacancy.location) > 0.8:
                strengths.append("Ubicación ideal para la posición")
        
        return strengths

    async def _get_potential_concerns(self, candidate: Person, vacancy: Vacante) -> List[str]:
        """
        Identifica posibles preocupaciones sobre el candidato para la vacante.
        """
        concerns = []
        
        # Analizar habilidades faltantes
        if candidate.skills and vacancy.palabras_clave:
            candidate_skills = set(skill.strip().lower() for skill in candidate.skills.split(','))
            required_skills = set(skill.strip().lower() for skill in vacancy.palabras_clave)
            missing_skills = required_skills - candidate_skills
            if missing_skills:
                concerns.append(f"Habilidades requeridas faltantes: {', '.join(missing_skills)}")
        
        # Analizar experiencia
        if candidate.experience_years and vacancy.metadata.get('required_experience'):
            if candidate.experience_years < vacancy.metadata['required_experience'] * 0.8:
                concerns.append(f"Experiencia por debajo del requerido ({candidate.experience_years} años)")
        
        # Analizar ubicación
        if candidate.location and vacancy.location:
            if self._calculate_zone_score(candidate.location, vacancy.location) < 0.5:
                concerns.append("Ubicación lejana a la posición")
        
        return concerns

def main():
    pipeline = MatchmakingModel(business_unit='huntRED®')
    data = pipeline.prepare_training_data()
    X_train, X_test, y_train, y_test = pipeline.preprocess_data(data)
    pipeline.train_model(X_train, y_train, X_test, y_test)
    from app.models import Person
    person = Person.objects.first()
    if person:
        matches = pipeline.predict_all_active_matches(person)
        logger.info(f"Coincidencias para {person.nombre}: {matches}")

if __name__ == "__main__":
    main()