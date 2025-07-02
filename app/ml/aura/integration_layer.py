# app/ml/aura/integration_layer.py
"""
Capa de Integración de AURA con el Sistema Principal

Este módulo conecta AURA con el sistema huntRED existente,
permitiendo acceso a datos enriquecidos y sincronización bidireccional.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import asyncio

from app.models import Person, BusinessUnit
from app.ats.models import Person as Candidate, Vacancy as Job, Application
from app.ml.aura.aura import AuraEngine
from app.ml.aura.connectors.linkedin_connector import LinkedInConnector

logger = logging.getLogger(__name__)

class AuraIntegrationLayer:
    """
    Capa de integración que conecta AURA con el sistema Grupo huntRED AI - GenIA.
    
    Permite a AURA acceder a todos los datos enriquecidos del sistema
    principal y sincronizar insights de vuelta al sistema.
    """
    
    def __init__(self):
        """Inicializa la capa de integración."""
        self.aura_engine = AuraEngine()
        self.linkedin_connector = LinkedInConnector()
        
        # Cache para optimizar consultas
        self.person_cache = {}
        self.candidate_cache = {}
        self.job_cache = {}
        
        logger.info("Capa de integración AURA inicializada")
    
    async def get_enriched_person_data(self, person_id: int) -> Dict[str, Any]:
        """
        Obtiene datos enriquecidos de una persona del sistema principal.
        
        Args:
            person_id: ID de la persona en el sistema huntRED
            
        Returns:
            Datos enriquecidos de la persona
        """
        try:
            # Obtener datos base del sistema principal
            person = await self._get_person_from_system(person_id)
            
            if not person:
                return {}
            
            # Enriquecer con datos de LinkedIn
            linkedin_data = await self.linkedin_connector.enrich_person_data(person)
            
            # Obtener datos de candidatos si aplica
            candidate_data = await self._get_candidate_data(person)
            
            # Obtener datos de aplicaciones
            application_data = await self._get_application_data(person)
            
            # Construir perfil enriquecido
            enriched_profile = {
                'person_id': person_id,
                'name': person.name,
                'email': getattr(person, 'email', None),
                'current_role': getattr(person, 'current_role', None),
                'current_company': getattr(person, 'current_company', None),
                'location': getattr(person, 'location', None),
                'skills': getattr(person, 'skills', []),
                'experience_years': getattr(person, 'experience_years', 0),
                'education': getattr(person, 'education', []),
                'linkedin_data': linkedin_data,
                'candidate_data': candidate_data,
                'application_data': application_data,
                'aura_metrics': await self._calculate_aura_metrics(person),
                'last_updated': datetime.now().isoformat()
            }
            
            # Cachear resultado
            self.person_cache[person_id] = enriched_profile
            
            return enriched_profile
            
        except Exception as e:
            logger.error(f"Error obteniendo datos enriquecidos de persona {person_id}: {str(e)}")
            return {}
    
    async def analyze_candidate_aura(
        self,
        candidate_id: int,
        job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analiza la aura de un candidato usando datos del sistema principal.
        
        Args:
            candidate_id: ID del candidato
            job_id: ID del trabajo específico (opcional)
            
        Returns:
            Análisis completo de aura del candidato
        """
        try:
            # Obtener candidato del sistema principal
            candidate = await self._get_candidate_from_system(candidate_id)
            
            if not candidate:
                return {'error': 'Candidato no encontrado'}
            
            # Obtener datos enriquecidos de la persona
            person_data = await self.get_enriched_person_data(candidate.person.id)
            
            # Si se especifica un trabajo, obtener datos del trabajo
            job_data = None
            if job_id:
                job_data = await self._get_job_from_system(job_id)
            
            # Analizar aura usando el motor de AURA
            aura_analysis = await self.aura_engine.analyze_candidate_aura(
                candidate_data=candidate,
                person_data=person_data,
                job_data=job_data
            )
            
            # Sincronizar insights al sistema principal
            await self._sync_aura_insights_to_system(candidate_id, aura_analysis)
            
            return aura_analysis
            
        except Exception as e:
            logger.error(f"Error analizando aura de candidato {candidate_id}: {str(e)}")
            return {'error': str(e)}
    
    async def find_aura_matches(
        self,
        job_id: int,
        max_candidates: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Encuentra candidatos con mejor aura para un trabajo específico.
        
        Args:
            job_id: ID del trabajo
            max_candidates: Máximo número de candidatos a retornar
            
        Returns:
            Lista de candidatos ordenados por score de aura
        """
        try:
            # Obtener trabajo del sistema principal
            job = await self._get_job_from_system(job_id)
            
            if not job:
                return []
            
            # Obtener candidatos activos
            candidates = await self._get_active_candidates()
            
            # Analizar aura de cada candidato
            aura_matches = []
            
            for candidate in candidates[:50]:  # Limitar para performance
                try:
                    aura_analysis = await self.analyze_candidate_aura(
                        candidate.id, job_id
                    )
                    
                    if 'aura_score' in aura_analysis:
                        aura_matches.append({
                            'candidate_id': candidate.id,
                            'candidate_name': candidate.person.name,
                            'aura_score': aura_analysis['aura_score'],
                            'compatibility_factors': aura_analysis.get('compatibility_factors', {}),
                            'recommendations': aura_analysis.get('recommendations', []),
                            'risk_factors': aura_analysis.get('risk_factors', [])
                        })
                        
                except Exception as e:
                    logger.warning(f"Error analizando candidato {candidate.id}: {str(e)}")
                    continue
            
            # Ordenar por score de aura
            aura_matches.sort(key=lambda x: x['aura_score'], reverse=True)
            
            return aura_matches[:max_candidates]
            
        except Exception as e:
            logger.error(f"Error encontrando matches de aura para trabajo {job_id}: {str(e)}")
            return []
    
    async def generate_network_insights(self, person_id: int) -> Dict[str, Any]:
        """
        Genera insights de red profesional usando datos del sistema.
        
        Args:
            person_id: ID de la persona
            
        Returns:
            Insights de red profesional
        """
        try:
            # Obtener datos enriquecidos
            person_data = await self.get_enriched_person_data(person_id)
            
            # Obtener conexiones de LinkedIn
            person = await self._get_person_from_system(person_id)
            linkedin_connections = await self.linkedin_connector.find_professional_connections(person)
            
            # Detectar hubs de red
            network_hubs = await self.linkedin_connector.detect_network_hubs(person)
            
            # Obtener candidatos relacionados
            related_candidates = await self._find_related_candidates(person_id)
            
            # Generar insights usando el motor de AURA
            network_insights = await self.aura_engine.generate_network_insights(
                person_data=person_data,
                linkedin_connections=linkedin_connections,
                network_hubs=network_hubs,
                related_candidates=related_candidates
            )
            
            return network_insights
            
        except Exception as e:
            logger.error(f"Error generando insights de red para persona {person_id}: {str(e)}")
            return {'error': str(e)}
    
    async def validate_experience_cross_reference(
        self,
        person_id: int,
        company: str,
        position: str,
        start_date: date,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Valida experiencia usando referencias cruzadas del sistema.
        
        Args:
            person_id: ID de la persona
            company: Empresa
            position: Posición
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Resultado de validación cruzada
        """
        try:
            # Obtener persona del sistema
            person = await self._get_person_from_system(person_id)
            
            if not person:
                return {'error': 'Persona no encontrada'}
            
            # Validar con LinkedIn
            linkedin_validation = await self.linkedin_connector.validate_experience(
                person, company, position, start_date, end_date
            )
            
            # Buscar referencias cruzadas
            cross_references = await self.linkedin_connector.find_cross_references(
                person, company, position
            )
            
            # Buscar en el sistema interno
            internal_references = await self._find_internal_references(
                person_id, company, position
            )
            
            # Combinar resultados
            validation_result = {
                'person_id': person_id,
                'company': company,
                'position': position,
                'linkedin_validation': linkedin_validation,
                'cross_references': cross_references,
                'internal_references': internal_references,
                'overall_confidence': self._calculate_overall_confidence(
                    linkedin_validation, cross_references, internal_references
                ),
                'validation_date': datetime.now().isoformat()
            }
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validando experiencia: {str(e)}")
            return {'error': str(e)}
    
    async def sync_aura_insights_to_dashboard(self, person_id: int) -> Dict[str, Any]:
        """
        Sincroniza insights de AURA al dashboard del sistema principal.
        
        Args:
            person_id: ID de la persona
            
        Returns:
            Resultado de sincronización
        """
        try:
            # Generar insights completos
            network_insights = await self.generate_network_insights(person_id)
            person_data = await self.get_enriched_person_data(person_id)
            
            # Preparar datos para el dashboard
            dashboard_data = {
                'person_id': person_id,
                'aura_score': person_data.get('aura_metrics', {}).get('overall_score', 0),
                'network_strength': network_insights.get('network_strength', 0),
                'professional_reputation': network_insights.get('reputation_score', 0),
                'key_connections': network_insights.get('key_connections', []),
                'recommendations': network_insights.get('recommendations', []),
                'risk_factors': network_insights.get('risk_factors', []),
                'last_updated': datetime.now().isoformat()
            }
            
            # En una implementación real, esto actualizaría el dashboard
            # Por ahora, solo registramos la sincronización
            logger.info(f"Sincronizando insights de AURA al dashboard para persona {person_id}")
            
            return {
                'success': True,
                'dashboard_data': dashboard_data,
                'sync_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sincronizando insights al dashboard: {str(e)}")
            return {'error': str(e)}
    
    # Métodos auxiliares para integración con el sistema principal
    
    async def _get_person_from_system(self, person_id: int) -> Optional[Person]:
        """Obtiene persona del sistema principal."""
        try:
            # En una implementación real, esto consultaría la base de datos
            # Por ahora, simulamos la consulta
            return Person.objects.get(id=person_id)
        except Person.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo persona {person_id}: {str(e)}")
            return None
    
    async def _get_candidate_from_system(self, candidate_id: int) -> Optional[Candidate]:
        """Obtiene candidato del sistema principal."""
        try:
            return Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo candidato {candidate_id}: {str(e)}")
            return None
    
    async def _get_job_from_system(self, job_id: int) -> Optional[Job]:
        """Obtiene trabajo del sistema principal."""
        try:
            return Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo trabajo {job_id}: {str(e)}")
            return None
    
    async def _get_candidate_data(self, person: Person) -> Dict[str, Any]:
        """Obtiene datos de candidato asociados a una persona."""
        try:
            candidates = Candidate.objects.filter(person=person)
            if candidates.exists():
                candidate = candidates.first()
                return {
                    'candidate_id': candidate.id,
                    'status': candidate.status,
                    'skills': getattr(candidate, 'skills', []),
                    'experience': getattr(candidate, 'experience', {}),
                    'preferences': getattr(candidate, 'preferences', {})
                }
            return {}
        except Exception as e:
            logger.error(f"Error obteniendo datos de candidato: {str(e)}")
            return {}
    
    async def _get_application_data(self, person: Person) -> List[Dict[str, Any]]:
        """Obtiene datos de aplicaciones de una persona."""
        try:
            applications = Application.objects.filter(candidate__person=person)
            return [
                {
                    'application_id': app.id,
                    'job_id': app.job.id,
                    'job_title': app.job.title,
                    'status': app.status,
                    'applied_date': app.created_at.isoformat(),
                    'score': getattr(app, 'score', 0)
                }
                for app in applications
            ]
        except Exception as e:
            logger.error(f"Error obteniendo datos de aplicaciones: {str(e)}")
            return []
    
    async def _get_active_candidates(self) -> List[Candidate]:
        """Obtiene candidatos activos del sistema."""
        try:
            return list(Candidate.objects.filter(status='active')[:100])
        except Exception as e:
            logger.error(f"Error obteniendo candidatos activos: {str(e)}")
            return []
    
    async def _find_related_candidates(self, person_id: int) -> List[Dict[str, Any]]:
        """Encuentra candidatos relacionados en el sistema."""
        try:
            # Buscar candidatos con habilidades similares
            person = await self._get_person_from_system(person_id)
            if not person:
                return []
            
            # En una implementación real, esto buscaría candidatos similares
            # Por ahora, retornamos una lista vacía
            return []
            
        except Exception as e:
            logger.error(f"Error encontrando candidatos relacionados: {str(e)}")
            return []
    
    async def _find_internal_references(
        self,
        person_id: int,
        company: str,
        position: str
    ) -> List[Dict[str, Any]]:
        """Encuentra referencias internas en el sistema."""
        try:
            # Buscar personas en el sistema que trabajaron en la misma empresa
            # En una implementación real, esto consultaría la base de datos
            return []
            
        except Exception as e:
            logger.error(f"Error encontrando referencias internas: {str(e)}")
            return []
    
    async def _calculate_aura_metrics(self, person: Person) -> Dict[str, float]:
        """Calcula métricas de aura para una persona."""
        try:
            # Métricas básicas basadas en datos del sistema
            metrics = {
                'professional_score': 0.7,  # Simulado
                'network_score': 0.6,       # Simulado
                'reputation_score': 0.8,    # Simulado
                'overall_score': 0.7        # Promedio
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculando métricas de aura: {str(e)}")
            return {}
    
    async def _sync_aura_insights_to_system(
        self,
        candidate_id: int,
        aura_analysis: Dict[str, Any]
    ) -> None:
        """Sincroniza insights de AURA al sistema principal."""
        try:
            # En una implementación real, esto actualizaría la base de datos
            # con los insights de AURA
            logger.info(f"Sincronizando insights de AURA para candidato {candidate_id}")
            
        except Exception as e:
            logger.error(f"Error sincronizando insights al sistema: {str(e)}")
    
    def _calculate_overall_confidence(
        self,
        linkedin_validation: Dict[str, Any],
        cross_references: List[Dict[str, Any]],
        internal_references: List[Dict[str, Any]]
    ) -> float:
        """Calcula la confianza general de la validación."""
        try:
            confidence = 0.0
            
            # Factor 1: Validación de LinkedIn
            if linkedin_validation.get('validated', False):
                confidence += linkedin_validation.get('confidence', 0.0) * 0.4
            
            # Factor 2: Referencias cruzadas
            if cross_references:
                max_ref_confidence = max(
                    [ref.get('validation_potential', 0.0) for ref in cross_references]
                )
                confidence += max_ref_confidence * 0.4
            
            # Factor 3: Referencias internas
            if internal_references:
                confidence += 0.2
            
            return min(1.0, confidence)
            
        except Exception as e:
            logger.error(f"Error calculando confianza general: {str(e)}")
            return 0.0 