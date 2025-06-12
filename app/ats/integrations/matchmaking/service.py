"""
Servicio de matchmaking mejorado.
Coordina el proceso de matching entre candidatos y vacantes.
"""
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from .analyzer import EnhancedMatchmakingAnalyzer
from app.ats.models import Person, Job, Match
from app.ats.utils.cache import cache_manager

logger = logging.getLogger(__name__)

class EnhancedMatchmakingService:
    """Servicio mejorado de matchmaking."""
    
    def __init__(self):
        self.analyzer = EnhancedMatchmakingAnalyzer()
        self.cache = cache_manager
        
    async def find_matches(
        self,
        candidate_id: str,
        job_ids: Optional[List[str]] = None,
        business_unit: Optional[str] = None,
        min_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Encuentra matches para un candidato.
        
        Args:
            candidate_id: ID del candidato
            job_ids: Lista de IDs de vacantes (opcional)
            business_unit: Unidad de negocio (opcional)
            min_score: Score mínimo de match (default: 0.7)
            
        Returns:
            Lista de matches encontrados
        """
        try:
            # 1. Obtener datos del candidato
            candidate_data = await self._get_candidate_data(candidate_id)
            
            # 2. Obtener vacantes relevantes
            jobs = await self._get_relevant_jobs(job_ids, business_unit)
            
            # 3. Analizar matches
            matches = []
            for job in jobs:
                # Usar la business unit de la vacante si no se especificó una
                job_business_unit = business_unit or job.get('business_unit')
                
                # Solo incluir datos grupales para Amigro
                if job_business_unit != 'amigro':
                    candidate_data.pop('group_data', None)
                
                match_result = await self.analyzer.analyze_match(
                    candidate_data,
                    job,
                    job_business_unit
                )
                
                if match_result['match_score'] >= min_score:
                    matches.append({
                        'job_id': job['id'],
                        'match_score': match_result['match_score'],
                        'report': match_result['report'],
                        'insights': match_result['insights'],
                        'timestamp': match_result['timestamp']
                    })
                    
            # 4. Ordenar por score
            matches.sort(key=lambda x: x['match_score'], reverse=True)
            
            # 5. Guardar resultados
            await self._save_matches(candidate_id, matches)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error en búsqueda de matches: {str(e)}")
            raise
            
    async def find_candidates(
        self,
        job_id: str,
        max_candidates: int = 10,
        min_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Encuentra candidatos para una vacante.
        
        Args:
            job_id: ID de la vacante
            max_candidates: Máximo número de candidatos
            min_score: Score mínimo de match
            
        Returns:
            Lista de candidatos encontrados
        """
        try:
            # 1. Obtener datos de la vacante
            job_data = await self._get_job_data(job_id)
            
            # 2. Obtener candidatos relevantes
            candidates = await self._get_relevant_candidates(job_data)
            
            # 3. Analizar matches
            matches = []
            for candidate in candidates:
                match_result = await self.analyzer.analyze_match(
                    candidate,
                    job_data,
                    job_data.get('business_unit')
                )
                
                if match_result['match_score'] >= min_score:
                    matches.append({
                        'candidate_id': candidate['id'],
                        'match_score': match_result['match_score'],
                        'report': match_result['report'],
                        'insights': match_result['insights'],
                        'timestamp': match_result['timestamp']
                    })
                    
            # 4. Ordenar y limitar resultados
            matches.sort(key=lambda x: x['match_score'], reverse=True)
            matches = matches[:max_candidates]
            
            # 5. Guardar resultados
            await self._save_matches_for_job(job_id, matches)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error en búsqueda de candidatos: {str(e)}")
            raise
            
    async def _get_candidate_data(self, candidate_id: str) -> Dict:
        """Obtiene datos completos del candidato."""
        try:
            candidate = await Person.objects.aget(id=candidate_id)
            
            # Datos básicos
            data = {
                'id': candidate.id,
                'name': candidate.get_full_name(),
                'skills': candidate.skills,
                'experience': candidate.experience_data,
                'personality': candidate.personality_data,
                'metadata': candidate.metadata
            }
            
            # Datos grupales y familiares
            data['group_data'] = {
                'family_members': [
                    {
                        'id': member.id,
                        'name': member.get_full_name(),
                        'relationship': relationship.relationship_type
                    }
                    for member, relationship in candidate.family_members.through.objects.filter(
                        person=candidate
                    ).select_related('related_person')
                ],
                'group_work_history': candidate.group_work_history,
                'group_success_rate': candidate.group_success_rate,
                'group_stability': candidate.group_stability,
                'community_integration': candidate.community_integration
            }
            
            # Datos de red social
            data['social_network'] = {
                'connections': [
                    {
                        'id': conn.related_person.id,
                        'name': conn.related_person.get_full_name(),
                        'relationship': conn.relationship_type,
                        'strength': conn.strength
                    }
                    for conn in candidate.social_connections.all()
                ]
            }
            
            return data
            
        except Person.DoesNotExist:
            logger.error(f"Candidato no encontrado: {candidate_id}")
            raise
        except Exception as e:
            logger.error(f"Error al obtener datos del candidato: {str(e)}")
            raise
        
    async def _get_job_data(self, job_id: str) -> Dict:
        """Obtiene datos completos de la vacante."""
        # Implementar obtención de datos
        return {}
        
    async def _get_relevant_jobs(
        self,
        job_ids: Optional[List[str]],
        business_unit: Optional[str]
    ) -> List[Dict]:
        """Obtiene vacantes relevantes."""
        # Implementar filtrado de vacantes
        return []
        
    async def _get_relevant_candidates(self, job_data: Dict) -> List[Dict]:
        """Obtiene candidatos relevantes."""
        # Implementar filtrado de candidatos
        return []
        
    async def _save_matches(self, candidate_id: str, matches: List[Dict]):
        """Guarda resultados de matches."""
        # Implementar guardado de matches
        pass
        
    async def _save_matches_for_job(self, job_id: str, matches: List[Dict]):
        """Guarda resultados de matches para una vacante."""
        # Implementar guardado de matches
        pass 