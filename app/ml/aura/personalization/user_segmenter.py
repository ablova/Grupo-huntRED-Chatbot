"""
AURA - User Segmenter
Segmentación avanzada de usuarios basada en perfil, comportamiento y contexto de red.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class UserSegmenter:
    """
    Segmentador avanzado de usuarios para AURA:
    - Análisis de perfil profesional y personal
    - Segmentación por comportamiento y preferencias
    - Integración con GNN para contexto de red
    - Segmentación dinámica y adaptativa
    """
    
    def __init__(self):
        self.segments = {
            'executive': {
                'description': 'Ejecutivos y líderes senior',
                'criteria': ['senior_level', 'management_experience', 'strategic_role'],
                'weight': 0.9
            },
            'junior': {
                'description': 'Profesionales junior y en desarrollo',
                'criteria': ['early_career', 'learning_focused', 'growth_minded'],
                'weight': 0.7
            },
            'recruiter': {
                'description': 'Reclutadores y headhunters',
                'criteria': ['recruitment_role', 'talent_acquisition', 'hiring_focused'],
                'weight': 0.8
            },
            'student': {
                'description': 'Estudiantes y recién graduados',
                'criteria': ['student_status', 'internship_seeking', 'career_exploration'],
                'weight': 0.6
            },
            'entrepreneur': {
                'description': 'Emprendedores y fundadores',
                'criteria': ['founder_role', 'startup_experience', 'business_owner'],
                'weight': 0.85
            },
            'tech': {
                'description': 'Profesionales de tecnología',
                'criteria': ['tech_skills', 'software_development', 'innovation_focused'],
                'weight': 0.8
            },
            'hr': {
                'description': 'Profesionales de RRHH',
                'criteria': ['hr_role', 'people_management', 'organizational_development'],
                'weight': 0.75
            },
            'sales': {
                'description': 'Profesionales de ventas',
                'criteria': ['sales_role', 'client_relationship', 'revenue_focused'],
                'weight': 0.7
            }
        }
        
    def segment_user(self, user_profile: Dict[str, Any], behavior_data: Optional[Dict[str, Any]] = None, 
                    network_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Segmenta un usuario basado en múltiples criterios.
        
        Args:
            user_profile: Perfil del usuario
            behavior_data: Datos de comportamiento (opcional)
            network_context: Contexto de red desde GNN (opcional)
            
        Returns:
            Dict con segmento principal y secundarios, scores y metadata
        """
        scores = {}
        
        # Calcular scores para cada segmento
        for segment_name, segment_config in self.segments.items():
            score = self._calculate_segment_score(
                user_profile, behavior_data, network_context, segment_config
            )
            scores[segment_name] = score * segment_config['weight']
        
        # Determinar segmento principal
        primary_segment = max(scores, key=scores.get)
        primary_score = scores[primary_segment]
        
        # Determinar segmentos secundarios (scores > 0.5)
        secondary_segments = {
            seg: score for seg, score in scores.items() 
            if score > 0.5 and seg != primary_segment
        }
        
        return {
            'primary_segment': primary_segment,
            'primary_score': primary_score,
            'secondary_segments': secondary_segments,
            'all_scores': scores,
            'confidence': self._calculate_confidence(scores),
            'timestamp': datetime.now().isoformat(),
            'metadata': {
                'total_criteria_evaluated': len(self.segments),
                'network_context_used': network_context is not None,
                'behavior_data_used': behavior_data is not None
            }
        }
    
    def _calculate_segment_score(self, user_profile: Dict[str, Any], 
                               behavior_data: Optional[Dict[str, Any]], 
                               network_context: Optional[Dict[str, Any]], 
                               segment_config: Dict[str, Any]) -> float:
        """Calcula el score para un segmento específico."""
        score = 0.0
        criteria_matches = 0
        
        # Evaluar criterios del perfil
        for criterion in segment_config['criteria']:
            if self._matches_criterion(user_profile, criterion):
                score += 1.0
                criteria_matches += 1
        
        # Normalizar por número de criterios
        if segment_config['criteria']:
            score = score / len(segment_config['criteria'])
        
        # Ajustar por comportamiento si está disponible
        if behavior_data:
            behavior_adjustment = self._calculate_behavior_adjustment(
                behavior_data, segment_config
            )
            score = (score + behavior_adjustment) / 2
        
        # Ajustar por contexto de red si está disponible
        if network_context:
            network_adjustment = self._calculate_network_adjustment(
                network_context, segment_config
            )
            score = (score + network_adjustment) / 2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _matches_criterion(self, user_profile: Dict[str, Any], criterion: str) -> bool:
        """Verifica si el perfil del usuario coincide con un criterio específico."""
        # Mapeo de criterios a campos del perfil
        criterion_mapping = {
            'senior_level': ['senior', 'director', 'vp', 'c-level', 'executive'],
            'management_experience': ['manager', 'lead', 'supervisor', 'director'],
            'strategic_role': ['strategy', 'planning', 'executive', 'leadership'],
            'early_career': ['junior', 'entry', 'associate', 'trainee'],
            'learning_focused': ['student', 'learning', 'certification', 'course'],
            'growth_minded': ['growth', 'development', 'advancement', 'career'],
            'recruitment_role': ['recruiter', 'talent', 'hiring', 'acquisition'],
            'talent_acquisition': ['recruiter', 'talent', 'hiring', 'sourcing'],
            'hiring_focused': ['hiring', 'recruitment', 'selection', 'interview'],
            'student_status': ['student', 'university', 'college', 'academic'],
            'internship_seeking': ['internship', 'practicum', 'training'],
            'career_exploration': ['exploration', 'discovery', 'orientation'],
            'founder_role': ['founder', 'co-founder', 'entrepreneur', 'startup'],
            'startup_experience': ['startup', 'entrepreneur', 'founder', 'business'],
            'business_owner': ['owner', 'founder', 'entrepreneur', 'business'],
            'tech_skills': ['programming', 'software', 'technology', 'development'],
            'software_development': ['developer', 'programmer', 'engineer', 'coding'],
            'innovation_focused': ['innovation', 'technology', 'research', 'development'],
            'hr_role': ['hr', 'human_resources', 'people', 'personnel'],
            'people_management': ['people', 'team', 'personnel', 'workforce'],
            'organizational_development': ['organization', 'development', 'culture', 'change'],
            'sales_role': ['sales', 'business_development', 'account', 'revenue'],
            'client_relationship': ['client', 'customer', 'relationship', 'account'],
            'revenue_focused': ['revenue', 'sales', 'business', 'growth']
        }
        
        if criterion not in criterion_mapping:
            return False
        
        # Buscar en campos relevantes del perfil
        search_fields = ['title', 'role', 'department', 'skills', 'experience', 'interests']
        profile_text = ' '.join([
            str(user_profile.get(field, '')).lower() 
            for field in search_fields
        ])
        
        return any(keyword in profile_text for keyword in criterion_mapping[criterion])
    
    def _calculate_behavior_adjustment(self, behavior_data: Dict[str, Any], 
                                     segment_config: Dict[str, Any]) -> float:
        """Calcula ajuste basado en comportamiento del usuario."""
        # Implementar lógica de ajuste por comportamiento
        # Por ahora, retorna un valor neutral
        return 0.5
    
    def _calculate_network_adjustment(self, network_context: Dict[str, Any], 
                                    segment_config: Dict[str, Any]) -> float:
        """Calcula ajuste basado en contexto de red."""
        # Implementar lógica de ajuste por red
        # Por ahora, retorna un valor neutral
        return 0.5
    
    def _calculate_confidence(self, scores: Dict[str, float]) -> float:
        """Calcula la confianza en la segmentación."""
        if not scores:
            return 0.0
        
        # Confianza basada en la diferencia entre el mejor y segundo mejor score
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) >= 2:
            confidence = (sorted_scores[0] - sorted_scores[1]) / sorted_scores[0]
        else:
            confidence = sorted_scores[0]
        
        return min(confidence, 1.0)
    
    def get_segment_info(self, segment_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene información detallada de un segmento."""
        if segment_name in self.segments:
            return {
                'name': segment_name,
                **self.segments[segment_name]
            }
        return None
    
    def list_segments(self) -> List[Dict[str, Any]]:
        """Lista todos los segmentos disponibles."""
        return [
            {'name': name, **config} 
            for name, config in self.segments.items()
        ]
    
    def add_custom_segment(self, name: str, description: str, criteria: List[str], weight: float = 0.7):
        """Añade un segmento personalizado."""
        self.segments[name] = {
            'description': description,
            'criteria': criteria,
            'weight': weight
        }
        logger.info(f"Custom segment '{name}' added to UserSegmenter")
    
    def update_segment_weight(self, segment_name: str, new_weight: float):
        """Actualiza el peso de un segmento existente."""
        if segment_name in self.segments:
            self.segments[segment_name]['weight'] = new_weight
            logger.info(f"Updated weight for segment '{segment_name}' to {new_weight}")
        else:
            logger.warning(f"Segment '{segment_name}' not found for weight update")

# Instancia global
user_segmenter = UserSegmenter() 