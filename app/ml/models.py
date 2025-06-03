from typing import Dict, Any, List, Optional
import logging
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger('ml')

class MatchmakingLearningSystem:
    """
    Sistema de aprendizaje automático para matchmaking y análisis de perfiles.
    """
    
    def __init__(self):
        """Inicializa el sistema de aprendizaje automático."""
        self.personality_model = RandomForestClassifier(n_estimators=100)
        self.professional_model = RandomForestClassifier(n_estimators=100)
        self.scaler = StandardScaler()
        self._initialize_models()
        
    def _initialize_models(self) -> None:
        """Inicializa los modelos con datos de entrenamiento."""
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
            
    def generate_recommendations(self, traits: Dict[str, float]) -> List[str]:
        """
        Genera recomendaciones basadas en los rasgos.
        
        Args:
            traits: Diccionario con rasgos de personalidad
            
        Returns:
            Lista de recomendaciones
        """
        try:
            # Implementación básica que puede ser expandida
            recommendations = []
            
            # Analizar rasgos y generar recomendaciones
            for trait, score in traits.items():
                if score < 0.3:
                    recommendations.append(f"Desarrollar {trait.replace('_', ' ')}")
                elif score > 0.7:
                    recommendations.append(f"Aprovechar fortaleza en {trait.replace('_', ' ')}")
                    
            return recommendations[:5]  # Limitar a 5 recomendaciones
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            return []
            
    def calculate_score(self, traits: Dict[str, float]) -> float:
        """
        Calcula un score general basado en los rasgos.
        
        Args:
            traits: Diccionario con rasgos de personalidad
            
        Returns:
            float: Score general
        """
        try:
            # Implementación básica que puede ser expandida
            scores = list(traits.values())
            return sum(scores) / len(scores) if scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculando score: {str(e)}")
            return 0.0
            
    def generate_professional_recommendations(self, skills: Dict[str, float],
                                           experience: Dict[str, Any]) -> List[str]:
        """
        Genera recomendaciones profesionales basadas en habilidades y experiencia.
        
        Args:
            skills: Diccionario con habilidades
            experience: Diccionario con experiencia
            
        Returns:
            Lista de recomendaciones profesionales
        """
        try:
            recommendations = []
            
            # Analizar habilidades
            for skill, level in skills.items():
                if level < 0.3:
                    recommendations.append(f"Fortalecer {skill.replace('_', ' ')}")
                elif level > 0.7:
                    recommendations.append(f"Liderar iniciativas en {skill.replace('_', ' ')}")
                    
            # Analizar experiencia
            years = experience.get('years', 0)
            if years < 2:
                recommendations.append("Buscar oportunidades de crecimiento en roles junior")
            elif years < 5:
                recommendations.append("Considerar roles de liderazgo de equipo")
            else:
                recommendations.append("Explorar roles estratégicos y de gestión")
                
            return recommendations[:5]  # Limitar a 5 recomendaciones
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones profesionales: {str(e)}")
            return []
            
    def calculate_professional_score(self, skills: Dict[str, float],
                                   experience: Dict[str, Any]) -> float:
        """
        Calcula un score profesional basado en habilidades y experiencia.
        
        Args:
            skills: Diccionario con habilidades
            experience: Diccionario con experiencia
            
        Returns:
            float: Score profesional
        """
        try:
            # Calcular score de habilidades
            skill_scores = list(skills.values())
            skill_score = sum(skill_scores) / len(skill_scores) if skill_scores else 0.0
            
            # Calcular score de experiencia
            years = experience.get('years', 0)
            experience_score = min(1.0, years / 10)  # Normalizar a 10 años
            
            # Combinar scores
            return 0.7 * skill_score + 0.3 * experience_score
            
        except Exception as e:
            logger.error(f"Error calculando score profesional: {str(e)}")
            return 0.0
            
    def calculate_trait_skill_compatibility(self, traits: Dict[str, float],
                                          skills: Dict[str, float]) -> Dict[str, float]:
        """
        Calcula la compatibilidad entre rasgos de personalidad y habilidades.
        
        Args:
            traits: Diccionario con rasgos de personalidad
            skills: Diccionario con habilidades
            
        Returns:
            Dict con puntuaciones de compatibilidad
        """
        try:
            compatibility = {}
            
            # Mapeo de rasgos a habilidades
            trait_skill_mapping = {
                'openness': ['innovation', 'creativity', 'adaptability'],
                'conscientiousness': ['organization', 'planning', 'reliability'],
                'extraversion': ['communication', 'leadership', 'networking'],
                'agreeableness': ['teamwork', 'collaboration', 'empathy'],
                'neuroticism': ['stress_management', 'emotional_stability']
            }
            
            # Calcular compatibilidad para cada rasgo
            for trait, trait_score in traits.items():
                if trait in trait_skill_mapping:
                    related_skills = trait_skill_mapping[trait]
                    skill_scores = [skills.get(skill, 0.0) for skill in related_skills]
                    compatibility[trait] = sum(skill_scores) / len(skill_scores) if skill_scores else 0.0
                    
            return compatibility
            
        except Exception as e:
            logger.error(f"Error calculando compatibilidad: {str(e)}")
            return {}
            
    def identify_integrated_strengths(self, traits: Dict[str, float],
                                    skills: Dict[str, float]) -> List[str]:
        """
        Identifica fortalezas integradas basadas en rasgos y habilidades.
        
        Args:
            traits: Diccionario con rasgos de personalidad
            skills: Diccionario con habilidades
            
        Returns:
            Lista de fortalezas identificadas
        """
        try:
            strengths = []
            
            # Identificar fortalezas en rasgos
            for trait, score in traits.items():
                if score > 0.7:
                    strengths.append(f"Alto {trait.replace('_', ' ')}")
                    
            # Identificar fortalezas en habilidades
            for skill, level in skills.items():
                if level > 0.7:
                    strengths.append(f"Experto en {skill.replace('_', ' ')}")
                    
            return strengths[:5]  # Limitar a 5 fortalezas
            
        except Exception as e:
            logger.error(f"Error identificando fortalezas: {str(e)}")
            return []
            
    def identify_integrated_improvements(self, traits: Dict[str, float],
                                      skills: Dict[str, float]) -> List[str]:
        """
        Identifica áreas de mejora integradas basadas en rasgos y habilidades.
        
        Args:
            traits: Diccionario con rasgos de personalidad
            skills: Diccionario con habilidades
            
        Returns:
            Lista de áreas de mejora identificadas
        """
        try:
            improvements = []
            
            # Identificar mejoras en rasgos
            for trait, score in traits.items():
                if score < 0.3:
                    improvements.append(f"Desarrollar {trait.replace('_', ' ')}")
                    
            # Identificar mejoras en habilidades
            for skill, level in skills.items():
                if level < 0.3:
                    improvements.append(f"Fortalecer {skill.replace('_', ' ')}")
                    
            return improvements[:5]  # Limitar a 5 mejoras
            
        except Exception as e:
            logger.error(f"Error identificando mejoras: {str(e)}")
            return []
            
    def determine_personality_type(self, traits: Dict[str, float]) -> str:
        """
        Determina el tipo de personalidad basado en los rasgos.
        
        Args:
            traits: Diccionario con rasgos de personalidad
            
        Returns:
            str: Tipo de personalidad
        """
        try:
            # Implementación básica que puede ser expandida
            if traits.get('openness', 0) > 0.7 and traits.get('extraversion', 0) > 0.7:
                return 'Explorador'
            elif traits.get('conscientiousness', 0) > 0.7 and traits.get('agreeableness', 0) > 0.7:
                return 'Organizador'
            elif traits.get('extraversion', 0) > 0.7 and traits.get('agreeableness', 0) > 0.7:
                return 'Social'
            elif traits.get('openness', 0) > 0.7 and traits.get('conscientiousness', 0) > 0.7:
                return 'Analítico'
            else:
                return 'Balanceado'
                
        except Exception as e:
            logger.error(f"Error determinando tipo de personalidad: {str(e)}")
            return 'Unknown'
            
    def generate_integrated_recommendations(self, personality_results: Dict[str, Any],
                                         professional_results: Dict[str, Any],
                                         business_unit: Optional[str] = None) -> List[str]:
        """
        Genera recomendaciones integradas basadas en ambos análisis.
        
        Args:
            personality_results: Resultados del análisis de personalidad
            professional_results: Resultados del análisis profesional
            business_unit: Unidad de negocio (opcional)
            
        Returns:
            Lista de recomendaciones integradas
        """
        try:
            recommendations = []
            
            # Recomendaciones basadas en personalidad
            personality_traits = personality_results.get('traits', {})
            for trait, score in personality_traits.items():
                if score < 0.3:
                    recommendations.append(f"Desarrollar {trait.replace('_', ' ')}")
                    
            # Recomendaciones basadas en perfil profesional
            professional_skills = professional_results.get('skills', {})
            for skill, level in professional_skills.items():
                if level < 0.3:
                    recommendations.append(f"Fortalecer {skill.replace('_', ' ')}")
                    
            # Recomendaciones específicas por unidad de negocio
            if business_unit:
                bu_recommendations = {
                    'huntRED': "Considerar roles ejecutivos y estratégicos",
                    'huntU': "Explorar oportunidades en desarrollo tecnológico",
                    'Amigro': "Buscar roles en gestión social y comunitaria",
                    'SEXSI': "Considerar posiciones en consultoría especializada"
                }
                if business_unit in bu_recommendations:
                    recommendations.append(bu_recommendations[business_unit])
                    
            return recommendations[:5]  # Limitar a 5 recomendaciones
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones integradas: {str(e)}")
            return []
            
    def calculate_integrated_score(self, personality_results: Dict[str, Any],
                                 professional_results: Dict[str, Any]) -> float:
        """
        Calcula un score general integrado.
        
        Args:
            personality_results: Resultados del análisis de personalidad
            professional_results: Resultados del análisis profesional
            
        Returns:
            float: Score integrado
        """
        try:
            # Calcular scores individuales
            personality_score = personality_results.get('score', 0.0)
            professional_score = professional_results.get('score', 0.0)
            
            # Combinar scores con pesos
            return 0.4 * personality_score + 0.6 * professional_score
            
        except Exception as e:
            logger.error(f"Error calculando score integrado: {str(e)}")
            return 0.0
            
    def _dict_to_vector(self, data: Dict[str, float]) -> np.ndarray:
        """
        Convierte un diccionario a vector numpy.
        
        Args:
            data: Diccionario con valores numéricos
            
        Returns:
            np.ndarray: Vector numpy
        """
        return np.array(list(data.values())) 