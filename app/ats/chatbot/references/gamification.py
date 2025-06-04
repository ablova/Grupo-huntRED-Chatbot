# /home/pablo/app/ats/chatbot/references/gamification.py
"""
Sistema de gamificación para referencias integrado con el sistema global.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from django.db.models import Count, Q
from app.models import Reference, BusinessUnit, Person
from app.ats.chatbot.workflow.business_units.reference_config import get_reference_config
from app.ats.integrations.services.gamification import ActivityType, gamification_service

class ReferenceGamification:
    """Sistema de gamificación para referencias."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.config = get_reference_config(business_unit.code)
    
    async def process_reference_completion(self, reference: Reference) -> Dict:
        """
        Procesa la completitud de una referencia y otorga puntos.
        
        Args:
            reference: Reference - Referencia completada
            
        Returns:
            Dict con información sobre puntos otorgados
        """
        try:
            # Calcular puntos base
            points = await self._calculate_reference_points(reference)
            
            # Registrar actividad en el sistema global
            result = await gamification_service.record_activity(
                user=reference.reference,
                activity_type=ActivityType.FEEDBACK_PROVIDED,
                xp_amount=points,
                metadata={
                    'reference_id': reference.id,
                    'candidate_name': reference.candidate.get_full_name(),
                    'quality_score': reference.metadata.get('analysis', {}).get('metrics', {}).get('score', 0),
                    'completeness': reference.metadata.get('analysis', {}).get('metrics', {}).get('completeness', 0)
                }
            )
            
            # Actualizar metadata de la referencia
            reference.metadata['gamification'] = {
                'points_awarded': points,
                'achievements': result.get('badges_earned', []),
                'processed_at': datetime.now().isoformat()
            }
            await reference.save()
            
            return result
            
        except Exception as e:
            print(f"Error procesando gamificación de referencia: {e}")
            return {}
    
    async def _calculate_reference_points(self, reference: Reference) -> int:
        """Calcula puntos para una referencia."""
        try:
            points = 0
            
            # Puntos base por completar
            if reference.status == 'completed':
                points += 100
            
            # Puntos por calidad
            if 'analysis' in reference.metadata:
                metrics = reference.metadata['analysis'].get('metrics', {})
                
                # Puntos por completitud
                completeness = metrics.get('completeness', 0)
                points += int(completeness * 50)
                
                # Puntos por nivel de detalle
                detail_level = metrics.get('detail_level', 0)
                points += int(detail_level * 30)
                
                # Puntos por sentimiento positivo
                sentiment = metrics.get('sentiment', 0)
                if sentiment > 0.7:
                    points += 20
            
            # Puntos por velocidad de respuesta
            if reference.status == 'completed':
                response_time = (reference.updated_at - reference.created_at).days
                if response_time <= 3:
                    points += 30
                elif response_time <= 7:
                    points += 20
                elif response_time <= 14:
                    points += 10
            
            # Puntos por conversión
            if reference.status == 'converted':
                points += 200
            
            return points
            
        except Exception as e:
            print(f"Error calculando puntos: {e}")
            return 0
    
    async def get_reference_stats(self, reference: Reference) -> Dict:
        """
        Obtiene estadísticas de una referencia.
        
        Args:
            reference: Reference - Referencia a analizar
            
        Returns:
            Dict - Estadísticas
        """
        try:
            # Obtener perfil de gamificación
            profile = await gamification_service.get_user_progress(reference.reference)
            
            # Obtener puntos específicos de la referencia
            points = reference.metadata.get('gamification', {}).get('points_awarded', 0)
            achievements = reference.metadata.get('gamification', {}).get('achievements', [])
            
            return {
                'points': points,
                'achievements': achievements,
                'total_xp': profile.get('xp_total', 0),
                'current_level': profile.get('current_level', 1),
                'xp_to_next_level': profile.get('xp_to_next_level', 100)
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {}
    
    async def get_leaderboard(self, days: int = 30) -> List[Dict]:
        """
        Obtiene ranking de referencias.
        
        Args:
            days: int - Días a considerar
            
        Returns:
            List[Dict] - Ranking de referencias
        """
        try:
            # Obtener ranking del sistema global
            leaderboard = await gamification_service.get_leaderboard(
                category='feedback',
                limit=10
            )
            
            # Enriquecer con datos de referencias
            enriched_leaderboard = []
            for entry in leaderboard:
                reference = Reference.objects.filter(
                    reference=entry['user'],
                    created_at__gte=datetime.now() - timedelta(days=days)
                ).first()
                
                if reference:
                    enriched_leaderboard.append({
                        'user': entry['user'],
                        'points': entry['points'],
                        'reference': reference,
                        'achievements': entry.get('achievements', [])
                    })
            
            return enriched_leaderboard
            
        except Exception as e:
            print(f"Error obteniendo ranking: {e}")
            return []
    
    def get_achievements(self, reference: Reference) -> List[str]:
        """
        Obtiene logros desbloqueados.
        
        Args:
            reference: Reference - Referencia a evaluar
            
        Returns:
            List[str] - Logros desbloqueados
        """
        try:
            achievements = []
            points = self.calculate_points(reference)
            
            # Logros por puntos
            if points >= 300:
                achievements.append("Maestro de Referencias")
            elif points >= 200:
                achievements.append("Experto en Referencias")
            elif points >= 100:
                achievements.append("Referenciador Avanzado")
            elif points >= 50:
                achievements.append("Referenciador Iniciado")
            
            # Logros por velocidad
            if reference.status == 'completed':
                response_time = (reference.updated_at - reference.created_at).days
                if response_time <= 3:
                    achievements.append("Respuesta Rápida")
                elif response_time <= 7:
                    achievements.append("Respuesta Eficiente")
            
            # Logros por calidad
            if 'analysis' in reference.metadata:
                metrics = reference.metadata['analysis'].get('metrics', {})
                if metrics.get('completeness', 0) >= 0.9:
                    achievements.append("Referencia Completa")
                if metrics.get('detail_level', 0) >= 0.8:
                    achievements.append("Referencia Detallada")
                if metrics.get('sentiment', 0) >= 0.8:
                    achievements.append("Referencia Positiva")
            
            # Logros por conversión
            if reference.status == 'converted':
                achievements.append("Conversión Exitosa")
            
            return achievements
            
        except Exception as e:
            print(f"Error obteniendo logros: {e}")
            return []
    
    def calculate_points(self, reference: Reference) -> int:
        """
        Calcula puntos para una referencia.
        
        Args:
            reference: Reference - Referencia a evaluar
            
        Returns:
            int - Puntos obtenidos
        """
        try:
            points = 0
            
            # Puntos base por completar
            if reference.status == 'completed':
                points += 100
            
            # Puntos por calidad
            if 'analysis' in reference.metadata:
                metrics = reference.metadata['analysis'].get('metrics', {})
                
                # Puntos por completitud
                completeness = metrics.get('completeness', 0)
                points += int(completeness * 50)
                
                # Puntos por nivel de detalle
                detail_level = metrics.get('detail_level', 0)
                points += int(detail_level * 30)
                
                # Puntos por sentimiento positivo
                sentiment = metrics.get('sentiment', 0)
                if sentiment > 0.7:
                    points += 20
            
            # Puntos por velocidad de respuesta
            if reference.status == 'completed':
                response_time = (reference.updated_at - reference.created_at).days
                if response_time <= 3:
                    points += 30
                elif response_time <= 7:
                    points += 20
                elif response_time <= 14:
                    points += 10
            
            # Puntos por conversión
            if reference.status == 'converted':
                points += 200
            
            return points
            
        except Exception as e:
            print(f"Error calculando puntos: {e}")
            return 0
    
    def _get_next_achievement(self, points: int) -> Optional[str]:
        """Obtiene próximo logro a desbloquear."""
        if points < 50:
            return "Referenciador Iniciado (50 puntos)"
        elif points < 100:
            return "Referenciador Avanzado (100 puntos)"
        elif points < 200:
            return "Experto en Referencias (200 puntos)"
        elif points < 300:
            return "Maestro de Referencias (300 puntos)"
        return None 