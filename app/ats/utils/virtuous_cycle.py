from typing import Dict, List
from app.ats.utils.candidate_flow import CandidateFlow
from app.ats.utils.cv_generator import CVGenerator
from app.ats.utils.signature import DigitalSignature
from app.ats.utils import logger_utils
import logging
import asyncio

logger = logging.getLogger(__name__)

class VirtuousCycle:
    def __init__(self, business_units: List[str]):
        """
        Inicializa el ciclo virtuoso.
        
        Args:
            business_units: Lista de unidades de negocio a manejar
        """
        self.business_units = business_units
        self.flows = {}
        self.logger = logger_utils.get_logger("virtuous_cycle")
        
        # Inicializar flujo para cada BU
        for bu in business_units:
            self.flows[bu] = CandidateFlow(bu)
            
    async def run_cycle(self):
        """
        Ejecuta el ciclo virtuoso completo:
        1. Buscar y procesar nuevas oportunidades
        2. Emparejar candidatos
        3. Procesar nuevos candidatos
        4. Generar CVs y firmas
        """
        try:
            # 1. Procesar nuevas oportunidades
            new_opportunities = await self._process_opportunities()
            
            # 2. Emparejar candidatos existentes
            matches = await self._match_candidates(new_opportunities)
            
            # 3. Procesar nuevos candidatos
            new_candidates = await self._process_new_candidates()
            
            # 4. Generar CVs y firmas
            await self._generate_documents(new_candidates)
            
            return {
                'opportunities': len(new_opportunities),
                'matches': len(matches),
                'new_candidates': len(new_candidates)
            }
            
        except Exception as e:
            self.logger.error(f"Error en ciclo virtuoso: {str(e)}")
            return {'status': 'error', 'reason': str(e)}
            
    async def _process_opportunities(self) -> Dict:
        """Procesa nuevas oportunidades para todas las BUs."""
        opportunities = {}
        for bu, flow in self.flows.items():
            self.logger.info(f"Procesando oportunidades para {bu}")
            bu_opportunities = await flow.process_new_opportunities()
            opportunities[bu] = bu_opportunities
            
        return opportunities
        
    async def _match_candidates(self, opportunities: Dict) -> Dict:
        """Empareja candidatos con oportunidades."""
        matches = {}
        for bu, flow in self.flows.items():
            self.logger.info(f"Emparejando candidatos para {bu}")
            bu_matches = await flow.match_candidates(opportunities.get(bu, []))
            matches[bu] = bu_matches
            
        return matches
        
    async def _process_new_candidates(self) -> List[Dict]:
        """Procesa nuevos candidatos para todas las BUs."""
        new_candidates = []
        for bu, flow in self.flows.items():
            self.logger.info(f"Procesando nuevos candidatos para {bu}")
            candidates = await self._get_new_candidates(bu)
            for candidate in candidates:
                result = await flow.process_candidate(candidate)
                if result.get('status') == 'success':
                    new_candidates.append(result)
                    
        return new_candidates
        
    async def _generate_documents(self, candidates: List[Dict]):
        """Genera documentos para nuevos candidatos."""
        for candidate in candidates:
            self.logger.info(f"Generando documentos para {candidate['profile']['name']}")
            
            # Generar CV ciego
            cv_generator = CVGenerator(template='blind')
            cv_pdf = await cv_generator.generate(candidate['profile'])
            
            # Obtener firma digital
            signature = await DigitalSignature().get_signature(
                candidate['profile']['name'],
                cv_pdf
            )
            
            # Almacenar documentos
            await self._store_documents(candidate, cv_pdf, signature)
            
    async def _get_new_candidates(self, business_unit: str) -> List[Dict]:
        """Obtiene nuevos candidatos para una BU específica."""
        # TODO: Implementar lógica específica por BU
        return []
        
    async def _store_documents(self, candidate: Dict, cv: bytes, signature: str):
        """Almacena documentos del candidato."""
        # TODO: Implementar almacenamiento
        pass
