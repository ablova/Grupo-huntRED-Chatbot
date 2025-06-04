"""
Utilidades para el manejo de referencias.
"""

from typing import Dict, List, Optional
from django.utils import timezone
from app.models import Reference, Person
from app.ats.chatbot.nlp.nlp import NLPProcessor
from app.ats.utils.cv_generator.cv_generator import CVGenerator

class ReferenceUtils:
    """Clase con utilidades para el manejo de referencias."""
    
    def __init__(self):
        self.nlp = NLPProcessor()
        self.cv_generator = CVGenerator()
    
    def calculate_reference_score(self, feedback: Dict) -> float:
        """
        Calcula el puntaje de calidad de una referencia basado en su feedback.
        
        Args:
            feedback: Dict - Feedback proporcionado
            
        Returns:
            float - Puntaje calculado (0-5)
        """
        try:
            # Extraer puntajes numéricos
            scores = []
            for key, value in feedback.items():
                if isinstance(value, (int, float)):
                    scores.append(value)
                elif isinstance(value, str):
                    # Analizar sentimiento de comentarios textuales
                    sentiment = self.nlp.analyze_sentiment(value)
                    scores.append(sentiment['score'])
            
            # Calcular promedio
            if not scores:
                return 0.0
                
            return sum(scores) / len(scores)
            
        except Exception as e:
            print(f"Error calculando score de referencia: {e}")
            return 0.0
    
    def update_candidate_cv_with_feedback(self, reference: Reference) -> bool:
        """
        Actualiza el CV del candidato con el feedback de la referencia.
        
        Args:
            reference: Reference - Referencia con feedback
            
        Returns:
            bool - True si se actualizó correctamente
        """
        try:
            candidate = reference.candidate
            
            # Extraer insights del feedback
            insights = self._extract_feedback_insights(reference)
            
            # Actualizar metadata del candidato
            if not candidate.metadata:
                candidate.metadata = {}
                
            if 'reference_feedback' not in candidate.metadata:
                candidate.metadata['reference_feedback'] = []
                
            candidate.metadata['reference_feedback'].append({
                'reference_id': reference.id,
                'relationship': reference.relationship,
                'insights': insights,
                'score': reference.score,
                'date': timezone.now().isoformat()
            })
            
            candidate.save()
            
            # Regenerar CV
            self.cv_generator.generate_cv(candidate)
            
            return True
            
        except Exception as e:
            print(f"Error actualizando CV con feedback: {e}")
            return False
    
    def _extract_feedback_insights(self, reference: Reference) -> Dict:
        """
        Extrae insights relevantes del feedback de una referencia.
        
        Args:
            reference: Reference - Referencia con feedback
            
        Returns:
            Dict - Insights extraídos
        """
        try:
            insights = {
                'strengths': [],
                'areas_for_improvement': [],
                'key_achievements': [],
                'work_style': {},
                'leadership_style': {},
                'technical_skills': {}
            }
            
            # Procesar feedback textual
            for key, value in reference.feedback.items():
                if isinstance(value, str):
                    # Analizar sentimiento y entidades
                    sentiment = self.nlp.analyze_sentiment(value)
                    entities = self.nlp.extract_entities(value)
                    
                    # Clasificar en categorías
                    if sentiment['score'] > 0.6:  # Positivo
                        insights['strengths'].append({
                            'text': value,
                            'sentiment': sentiment,
                            'entities': entities
                        })
                    elif sentiment['score'] < 0.4:  # Negativo
                        insights['areas_for_improvement'].append({
                            'text': value,
                            'sentiment': sentiment,
                            'entities': entities
                        })
                    
                    # Extraer logros
                    if 'achievement' in key.lower() or 'accomplishment' in key.lower():
                        insights['key_achievements'].append({
                            'text': value,
                            'entities': entities
                        })
                    
                    # Analizar estilo de trabajo
                    if 'work_style' in key.lower():
                        insights['work_style'] = self.nlp.analyze_work_style(value)
                    
                    # Analizar estilo de liderazgo
                    if 'leadership' in key.lower():
                        insights['leadership_style'] = self.nlp.analyze_leadership_style(value)
                    
                    # Analizar habilidades técnicas
                    if 'technical' in key.lower() or 'skills' in key.lower():
                        insights['technical_skills'] = self.nlp.extract_technical_skills(value)
            
            return insights
            
        except Exception as e:
            print(f"Error extrayendo insights del feedback: {e}")
            return {}
    
    def validate_reference_data(self, data: Dict) -> List[str]:
        """
        Valida los datos de una referencia.
        
        Args:
            data: Dict - Datos a validar
            
        Returns:
            List[str] - Lista de errores encontrados
        """
        errors = []
        
        # Validar campos requeridos
        required_fields = ['name', 'relationship', 'company', 'title', 'email']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"El campo {field} es requerido")
        
        # Validar email
        if data.get('email') and not self._is_valid_email(data['email']):
            errors.append("El email no es válido")
        
        # Validar teléfono si se proporciona
        if data.get('phone') and not self._is_valid_phone(data['phone']):
            errors.append("El teléfono no es válido")
        
        return errors
    
    def _is_valid_email(self, email: str) -> bool:
        """Valida formato de email."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Valida formato de teléfono."""
        import re
        # Eliminar caracteres no numéricos
        phone = re.sub(r'\D', '', phone)
        # Verificar longitud mínima
        return len(phone) >= 10 