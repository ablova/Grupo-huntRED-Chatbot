# /home/pablo/app/ml/analyzers/reference_analyzer.py
"""
Analizador de referencias utilizando técnicas de ML.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q
from app.models import Reference, BusinessUnit
from app.ats.chatbot.nlp.nlp import NLPProcessor
from app.ats.chatbot.workflow.business_units.reference_config import get_reference_config

class ReferenceAnalyzer:
    """Analizador de referencias con ML."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.nlp = NLPProcessor()
        self.config = get_reference_config(business_unit.code)
    
    def analyze_reference_quality(self, reference: Reference) -> Dict:
        """
        Analiza la calidad de una referencia.
        
        Args:
            reference: Reference - Referencia a analizar
            
        Returns:
            Dict con métricas de calidad
        """
        try:
            # Extraer respuestas
            responses = reference.metadata.get('responses', {})
            if not responses:
                return {
                    'score': 0,
                    'completeness': 0,
                    'detail_level': 0,
                    'sentiment': 0,
                    'competencies': []
                }
            
            # Calcular métricas
            metrics = {
                'score': self._calculate_overall_score(responses),
                'completeness': self._calculate_completeness(responses),
                'detail_level': self._calculate_detail_level(responses),
                'sentiment': self._analyze_sentiment(responses),
                'competencies': self._extract_competencies(responses)
            }
            
            # Actualizar metadata
            reference.metadata['analysis'] = {
                'metrics': metrics,
                'analyzed_at': datetime.now().isoformat()
            }
            reference.save()
            
            return metrics
            
        except Exception as e:
            print(f"Error analizando referencia: {e}")
            return {}
    
    def generate_reference_report(self, reference: Reference) -> Dict:
        """
        Genera un reporte detallado de la referencia.
        
        Args:
            reference: Reference - Referencia a analizar
            
        Returns:
            Dict con reporte detallado
        """
        try:
            # Obtener métricas básicas
            metrics = self.analyze_reference_quality(reference)
            
            # Generar insights
            insights = {
                'strengths': self._extract_strengths(reference),
                'areas_for_improvement': self._extract_improvement_areas(reference),
                'key_achievements': self._extract_achievements(reference),
                'work_style': self._analyze_work_style(reference),
                'leadership_style': self._analyze_leadership_style(reference),
                'technical_skills': self._analyze_technical_skills(reference)
            }
            
            # Generar recomendaciones
            recommendations = self._generate_recommendations(metrics, insights)
            
            return {
                'metrics': metrics,
                'insights': insights,
                'recommendations': recommendations,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error generando reporte: {e}")
            return {}
    
    def analyze_reference_trends(self, days: int = 30) -> Dict:
        """
        Analiza tendencias de referencias.
        
        Args:
            days: int - Días a analizar
            
        Returns:
            Dict con tendencias
        """
        try:
            # Obtener referencias del período
            start_date = datetime.now() - timedelta(days=days)
            references = Reference.objects.filter(
                business_unit=self.business_unit,
                created_at__gte=start_date
            )
            
            # Calcular métricas
            total_references = references.count()
            completed_references = references.filter(status='completed').count()
            expired_references = references.filter(status='expired').count()
            converted_references = references.filter(status='converted').count()
            
            # Calcular tasas
            completion_rate = (completed_references / total_references) if total_references > 0 else 0
            expiration_rate = (expired_references / total_references) if total_references > 0 else 0
            conversion_rate = (converted_references / total_references) if total_references > 0 else 0
            
            # Calcular promedios
            avg_score = references.filter(status='completed').aggregate(
                avg_score=Avg('metadata__analysis__metrics__score')
            )['avg_score'] or 0
            
            avg_response_time = references.filter(status='completed').aggregate(
                avg_time=Avg('metadata__analysis__response_time')
            )['avg_time'] or 0
            
            return {
                'total_references': total_references,
                'completion_rate': completion_rate,
                'expiration_rate': expiration_rate,
                'conversion_rate': conversion_rate,
                'avg_score': avg_score,
                'avg_response_time': avg_response_time,
                'period': {
                    'start': start_date.isoformat(),
                    'end': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"Error analizando tendencias: {e}")
            return {}
    
    def _calculate_overall_score(self, responses: Dict) -> float:
        """Calcula puntuación general."""
        try:
            total_score = 0
            total_weight = 0
            
            for question in self.config['questions']:
                if question['id'] in responses:
                    response = responses[question['id']]
                    weight = question.get('weight', 1.0)
                    
                    if question['type'] == 'rating':
                        score = float(response) / question['scale']
                    elif question['type'] == 'multiple_choice':
                        score = len(response) / len(question['options'])
                    elif question['type'] == 'boolean':
                        score = 1.0 if response else 0.0
                    else:  # text
                        score = min(1.0, len(response) / 500)  # Normalizar por longitud
                    
                    total_score += score * weight
                    total_weight += weight
            
            return (total_score / total_weight) if total_weight > 0 else 0
            
        except Exception as e:
            print(f"Error calculando puntuación: {e}")
            return 0
    
    def _calculate_completeness(self, responses: Dict) -> float:
        """Calcula nivel de completitud."""
        try:
            total_questions = len(self.config['questions'])
            answered_questions = len(responses)
            return answered_questions / total_questions if total_questions > 0 else 0
            
        except Exception as e:
            print(f"Error calculando completitud: {e}")
            return 0
    
    def _calculate_detail_level(self, responses: Dict) -> float:
        """Calcula nivel de detalle."""
        try:
            total_length = 0
            text_questions = 0
            
            for question in self.config['questions']:
                if question['type'] == 'text' and question['id'] in responses:
                    total_length += len(responses[question['id']])
                    text_questions += 1
            
            return (total_length / (text_questions * 500)) if text_questions > 0 else 0
            
        except Exception as e:
            print(f"Error calculando nivel de detalle: {e}")
            return 0
    
    def _analyze_sentiment(self, responses: Dict) -> Dict:
        """Analiza sentimiento de las respuestas."""
        try:
            sentiments = {}
            
            for question in self.config['questions']:
                if question['id'] in responses and question['type'] == 'text':
                    response = responses[question['id']]
                    sentiment = self.nlp.analyze_sentiment(response)
                    sentiments[question['id']] = sentiment
            
            return sentiments
            
        except Exception as e:
            print(f"Error analizando sentimiento: {e}")
            return {}
    
    def _extract_competencies(self, responses: Dict) -> List[Dict]:
        """Extrae competencias mencionadas."""
        try:
            competencies = []
            
            for question in self.config['questions']:
                if question['id'] in responses and question['type'] == 'text':
                    response = responses[question['id']]
                    extracted = self.nlp.extract_competencies(response)
                    competencies.extend(extracted)
            
            return competencies
            
        except Exception as e:
            print(f"Error extrayendo competencias: {e}")
            return []
    
    def _extract_strengths(self, reference: Reference) -> List[str]:
        """Extrae fortalezas mencionadas."""
        try:
            strengths = []
            responses = reference.metadata.get('responses', {})
            
            if 'strengths' in responses:
                strengths.extend(responses['strengths'])
            
            return strengths
            
        except Exception as e:
            print(f"Error extrayendo fortalezas: {e}")
            return []
    
    def _extract_improvement_areas(self, reference: Reference) -> List[str]:
        """Extrae áreas de mejora."""
        try:
            areas = []
            responses = reference.metadata.get('responses', {})
            
            if 'recommendation' in responses and not responses['recommendation']:
                if 'recommendation_feedback' in responses:
                    areas.append(responses['recommendation_feedback'])
            
            return areas
            
        except Exception as e:
            print(f"Error extrayendo áreas de mejora: {e}")
            return []
    
    def _extract_achievements(self, reference: Reference) -> List[str]:
        """Extrae logros mencionados."""
        try:
            achievements = []
            responses = reference.metadata.get('responses', {})
            
            if 'achievements' in responses:
                achievements.append(responses['achievements'])
            
            return achievements
            
        except Exception as e:
            print(f"Error extrayendo logros: {e}")
            return []
    
    def _analyze_work_style(self, reference: Reference) -> Dict:
        """Analiza estilo de trabajo."""
        try:
            style = {}
            responses = reference.metadata.get('responses', {})
            
            if 'work_style' in responses:
                style['type'] = responses['work_style']
            
            return style
            
        except Exception as e:
            print(f"Error analizando estilo de trabajo: {e}")
            return {}
    
    def _analyze_leadership_style(self, reference: Reference) -> Dict:
        """Analiza estilo de liderazgo."""
        try:
            style = {}
            responses = reference.metadata.get('responses', {})
            
            if 'leadership' in responses:
                style['types'] = responses['leadership']
            
            return style
            
        except Exception as e:
            print(f"Error analizando estilo de liderazgo: {e}")
            return {}
    
    def _analyze_technical_skills(self, reference: Reference) -> Dict:
        """Analiza habilidades técnicas."""
        try:
            skills = {}
            responses = reference.metadata.get('responses', {})
            
            if 'technical' in responses:
                skills['level'] = responses['technical']
            if 'skills' in responses:
                skills['areas'] = responses['skills']
            
            return skills
            
        except Exception as e:
            print(f"Error analizando habilidades técnicas: {e}")
            return {}
    
    def _generate_recommendations(self, metrics: Dict, insights: Dict) -> List[str]:
        """Genera recomendaciones basadas en el análisis."""
        try:
            recommendations = []
            
            # Recomendaciones basadas en métricas
            if metrics['completeness'] < 0.8:
                recommendations.append({
                    'type': 'completeness',
                    'priority': 'high',
                    'message': "Solicitar información adicional para completar la referencia",
                    'suggested_questions': self._get_suggested_questions(metrics)
                })
            
            if metrics['detail_level'] < 0.6:
                recommendations.append({
                    'type': 'detail',
                    'priority': 'medium',
                    'message': "Solicitar más detalles en las respuestas abiertas",
                    'suggested_questions': self._get_detail_questions(metrics)
                })
            
            if metrics['sentiment'] < 0.5:
                recommendations.append({
                    'type': 'sentiment',
                    'priority': 'high',
                    'message': "Investigar más a fondo las áreas de mejora mencionadas",
                    'suggested_questions': self._get_sentiment_questions(metrics)
                })
            
            # Recomendaciones basadas en insights
            if not insights['strengths']:
                recommendations.append({
                    'type': 'strengths',
                    'priority': 'medium',
                    'message': "Solicitar ejemplos específicos de fortalezas",
                    'suggested_questions': self._get_strength_questions()
                })
            
            if insights['areas_for_improvement']:
                recommendations.append({
                    'type': 'improvement',
                    'priority': 'high',
                    'message': "Desarrollar plan de mejora para las áreas identificadas",
                    'suggested_questions': self._get_improvement_questions(insights)
                })
            
            if not insights['key_achievements']:
                recommendations.append({
                    'type': 'achievements',
                    'priority': 'medium',
                    'message': "Solicitar ejemplos de logros y contribuciones",
                    'suggested_questions': self._get_achievement_questions()
                })
            
            # Ordenar por prioridad
            recommendations.sort(key=lambda x: {
                'high': 0,
                'medium': 1,
                'low': 2
            }[x['priority']])
            
            return recommendations
            
        except Exception as e:
            print(f"Error generando recomendaciones: {e}")
            return []
    
    def _get_suggested_questions(self, metrics: Dict) -> List[str]:
        """Obtiene preguntas sugeridas basadas en métricas."""
        questions = []
        
        # Preguntas basadas en completitud
        if metrics['completeness'] < 0.5:
            questions.extend([
                "¿Podrías proporcionar más detalles sobre el rol y responsabilidades?",
                "¿Cuáles fueron los principales desafíos que enfrentó?",
                "¿Cómo manejó situaciones difíciles?"
            ])
        elif metrics['completeness'] < 0.8:
            questions.extend([
                "¿Podrías compartir ejemplos específicos de su desempeño?",
                "¿Cómo contribuyó al éxito del equipo?"
            ])
        
        return questions
    
    def _get_detail_questions(self, metrics: Dict) -> List[str]:
        """Obtiene preguntas para mejorar el detalle."""
        return [
            "¿Podrías proporcionar ejemplos concretos?",
            "¿Qué resultados específicos logró?",
            "¿Cómo se comparaba con otros en roles similares?"
        ]
    
    def _get_sentiment_questions(self, metrics: Dict) -> List[str]:
        """Obtiene preguntas para investigar sentimiento negativo."""
        return [
            "¿Qué áreas específicas necesitan mejora?",
            "¿Qué sugerencias tienes para su desarrollo?",
            "¿Cómo podría haber manejado mejor las situaciones?"
        ]
    
    def _get_strength_questions(self) -> List[str]:
        """Obtiene preguntas sobre fortalezas."""
        return [
            "¿Cuáles son sus mayores fortalezas técnicas?",
            "¿Qué habilidades blandas destaca?",
            "¿En qué áreas sobresale por encima de otros?"
        ]
    
    def _get_improvement_questions(self, insights: Dict) -> List[str]:
        """Obtiene preguntas sobre áreas de mejora."""
        questions = [
            "¿Qué recursos o apoyo necesitaría para mejorar?",
            "¿Qué tipo de mentoría sería más efectiva?",
            "¿Qué expectativas tienes sobre su desarrollo?"
        ]
        
        # Agregar preguntas específicas basadas en áreas identificadas
        for area in insights['areas_for_improvement']:
            questions.append(f"¿Cómo podría mejorar específicamente en {area}?")
        
        return questions
    
    def _get_achievement_questions(self) -> List[str]:
        """Obtiene preguntas sobre logros."""
        return [
            "¿Cuáles fueron sus mayores contribuciones?",
            "¿Qué proyectos o iniciativas lideró?",
            "¿Qué impacto tuvo en el negocio?"
        ] 