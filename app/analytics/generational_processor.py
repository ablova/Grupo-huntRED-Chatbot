# app/analytics/generational_processor.py
from typing import Dict, List, Optional
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from .models import GenerationalProfile, MotivationalProfile, CareerAspiration, WorkStylePreference, CulturalAlignment
from app.models import Person, EnhancedMLProfile

class GenerationalAnalytics:
    """Procesador para análisis generacional y motivacional"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=4, random_state=42)
        self.generations = {
            'BB': {'range': (1946, 1964), 'name': 'Baby Boomers'},
            'X': {'range': (1965, 1980), 'name': 'Generación X'},
            'Y': {'range': (1981, 1996), 'name': 'Millennials'},
            'Z': {'range': (1997, 2012), 'name': 'Generación Z'}
        }
        
    def process_person_data(self, person: Person) -> Dict:
        """Procesa los datos de una persona para análisis generacional"""
        if not person.date_of_birth:
            return None
            
        # Obtener perfil generacional
        generational_profile = person.get_generational_profile()
        if not generational_profile:
            return None
            
        # Obtener perfil motivacional
        motivational_profile = person.get_motivational_profile()
        
        # Obtener preferencias de trabajo
        work_preferences = person.get_work_style_preferences()
        
        # Generar insights
        insights = {
            'generational': {
                'generation': generational_profile,
                'generation_name': self.generations[generational_profile]['name'],
                'work_preferences': work_preferences,
                'values': {
                    'career_growth': person.calculate_career_growth_importance(),
                    'social_impact': person.calculate_social_impact_importance(),
                    'financial_security': person.calculate_financial_security_importance()
                }
            },
            'motivational': motivational_profile,
            'work_style': work_preferences
        }
        
        # Actualizar perfil ML
        ml_profile = EnhancedMLProfile.objects.filter(user=person).first()
        if ml_profile:
            ml_profile.update_generational_insights(insights)
        
        return insights
    
    def analyze_team_composition(self, team_members: List[Person]) -> Dict:
        """Analiza la composición generacional de un equipo"""
        if not team_members:
            return None
            
        generational_distribution = {}
        motivational_patterns = {
            'intrinsic': {'autonomy': 0, 'mastery': 0, 'purpose': 0},
            'extrinsic': {'recognition': 0, 'compensation': 0, 'status': 0}
        }
        
        for member in team_members:
            # Distribución generacional
            generation = member.get_generational_profile()
            if generation:
                generational_distribution[generation] = generational_distribution.get(generation, 0) + 1
            
            # Patrones motivacionales
            motivational = member.get_motivational_profile()
            if motivational:
                for category in ['intrinsic', 'extrinsic']:
                    for factor in motivational[category]:
                        motivational_patterns[category][factor] += motivational[category][factor]
        
        # Normalizar patrones motivacionales
        team_size = len(team_members)
        for category in motivational_patterns:
            for factor in motivational_patterns[category]:
                motivational_patterns[category][factor] /= team_size
        
        return {
            'generational_distribution': generational_distribution,
            'motivational_patterns': motivational_patterns,
            'team_size': team_size
        }
    
    def generate_team_recommendations(self, team_analysis: Dict) -> List[Dict]:
        """Genera recomendaciones basadas en el análisis del equipo"""
        if not team_analysis:
            return []
            
        recommendations = []
        
        # Recomendaciones basadas en distribución generacional
        distribution = team_analysis['generational_distribution']
        if len(distribution) < 2:
            recommendations.append({
                'type': 'diversity',
                'title': 'Diversidad Generacional',
                'description': 'Considerar incorporar miembros de otras generaciones para enriquecer la perspectiva del equipo',
                'priority': 'high'
            })
        
        # Recomendaciones basadas en patrones motivacionales
        patterns = team_analysis['motivational_patterns']
        if patterns['intrinsic']['purpose'] < 0.5:
            recommendations.append({
                'type': 'motivation',
                'title': 'Propósito Compartido',
                'description': 'Fortalecer el sentido de propósito y misión del equipo',
                'priority': 'medium'
            })
        
        return recommendations
    
    def generate_visualization_data(self, person: Person) -> Dict:
        """Genera datos para visualizaciones del análisis generacional"""
        insights = self.process_person_data(person)
        if not insights:
            return None
            
        return {
            'generational_profile': {
                'generation': insights['generational']['generation'],
                'generation_name': insights['generational']['generation_name'],
                'values': insights['generational']['values']
            },
            'motivational_radar': {
                'intrinsic': insights['motivational']['intrinsic'],
                'extrinsic': insights['motivational']['extrinsic']
            },
            'work_style': insights['work_style']
        }
    
    def process_generational_data(self, user_data):
        """Procesa los datos generacionales y retorna insights"""
        profile = GenerationalProfile.objects.get(user=user_data)
        motivational = MotivationalProfile.objects.get(user=user_data)
        career = CareerAspiration.objects.get(user=user_data)
        work_style = WorkStylePreference.objects.get(user=user_data)
        cultural = CulturalAlignment.objects.get(user=user_data)
        
        # Análisis de Perfil Generacional
        generational_insights = {
            'generation': profile.generation,
            'work_preferences': {
                'work_life_balance': profile.work_life_balance_importance,
                'tech_adoption': profile.tech_adoption_level,
                'remote_work': profile.remote_work_preference
            },
            'values': {
                'career_growth': profile.career_growth_importance,
                'social_impact': profile.social_impact_importance,
                'financial_security': profile.financial_security_importance
            }
        }
        
        # Análisis Motivacional
        motivational_insights = {
            'intrinsic': {
                'autonomy': motivational.autonomy_need,
                'mastery': motivational.mastery_need,
                'purpose': motivational.purpose_need
            },
            'extrinsic': {
                'recognition': motivational.recognition_importance,
                'compensation': motivational.compensation_importance,
                'status': motivational.status_importance
            }
        }
        
        # Análisis de Carrera
        career_insights = {
            'goals': {
                'short_term': career.short_term_goal,
                'long_term': career.long_term_goal
            },
            'preferences': career.preferred_learning_methods,
            'desired_skills': career.desired_skills
        }
        
        # Análisis de Estilo de Trabajo
        work_style_insights = {
            'collaboration': work_style.collaboration_preference,
            'independence': work_style.independence_preference,
            'structure': work_style.structure_preference
        }
        
        # Análisis Cultural
        cultural_insights = {
            'values_alignment': cultural.company_values_alignment,
            'flexibility': cultural.cultural_flexibility,
            'adaptability': cultural.change_adaptability
        }
        
        return {
            'generational': generational_insights,
            'motivational': motivational_insights,
            'career': career_insights,
            'work_style': work_style_insights,
            'cultural': cultural_insights
        }
    
    def generate_recommendations(self, insights):
        """Genera recomendaciones basadas en los insights"""
        recommendations = []
        
        # Recomendaciones Generacionales
        if insights['generational']['work_preferences']['remote_work'] > 70:
            recommendations.append({
                'type': 'work_style',
                'title': 'Flexibilidad Laboral',
                'description': 'Considerar opciones de trabajo remoto o híbrido',
                'impact': 'Alto'
            })
        
        # Recomendaciones Motivacionales
        if insights['motivational']['intrinsic']['purpose'] > 80:
            recommendations.append({
                'type': 'engagement',
                'title': 'Propósito Organizacional',
                'description': 'Enfatizar el impacto y propósito del trabajo',
                'impact': 'Alto'
            })
        
        # Recomendaciones de Desarrollo
        if insights['career']['preferences'].get('formal_education'):
            recommendations.append({
                'type': 'development',
                'title': 'Desarrollo Académico',
                'description': 'Considerar programas de educación formal',
                'impact': 'Medio'
            })
        
        return recommendations
    
    def calculate_generational_compatibility(self, user_data, team_data):
        """Calcula la compatibilidad generacional con el equipo"""
        user_insights = self.process_generational_data(user_data)
        team_insights = [self.process_generational_data(member) for member in team_data]
        
        compatibility_scores = []
        for member in team_insights:
            score = self._calculate_compatibility_score(user_insights, member)
            compatibility_scores.append(score)
        
        return {
            'average_compatibility': np.mean(compatibility_scores),
            'compatibility_details': compatibility_scores
        }
    
    def _calculate_compatibility_score(self, user_insights, team_member_insights):
        """Calcula el score de compatibilidad entre dos perfiles"""
        # Implementar lógica de cálculo de compatibilidad
        # Considerar diferentes aspectos: valores, estilos de trabajo, etc.
        return 0.0  # Placeholder
    
    def generate_team_insights(self, team_data):
        """Genera insights a nivel de equipo"""
        team_insights = [self.process_generational_data(member) for member in team_data]
        
        # Análisis de diversidad generacional
        generational_diversity = self._analyze_generational_diversity(team_insights)
        
        # Análisis de compatibilidad
        compatibility_matrix = self._generate_compatibility_matrix(team_insights)
        
        # Identificación de patrones
        patterns = self._identify_team_patterns(team_insights)
        
        return {
            'diversity': generational_diversity,
            'compatibility': compatibility_matrix,
            'patterns': patterns
        }
    
    def _analyze_generational_diversity(self, team_insights):
        """Analiza la diversidad generacional del equipo"""
        # Implementar análisis de diversidad
        return {}
    
    def _generate_compatibility_matrix(self, team_insights):
        """Genera matriz de compatibilidad del equipo"""
        # Implementar generación de matriz
        return {}
    
    def _identify_team_patterns(self, team_insights):
        """Identifica patrones en el equipo"""
        # Implementar identificación de patrones
        return {} 