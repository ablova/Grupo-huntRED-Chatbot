from typing import List, Dict, Optional
from app.ats.utils.skills_utils import create_skill_processor
from app.ats.utils.cv_generator import CVGenerator
from app.ats.utils.signature import DigitalSignature
from app.ats.utils.scraping import JobScraper
from app.ats.utils.nlp import NLPProcessor
from app.ats.utils.cv_generator.cv_data import CVData
from app.ats.utils.signature.identity_validation import validate_identity
from app.ats.utils import logger_utils
import logging

logger = logging.getLogger(__name__)

class CandidateFlow:
    def __init__(self, business_unit: str):
        """
        Inicializa el flujo completo de candidatos.
        
        Args:
            business_unit: Unidad de negocio (huntRED, huntU, Amigro, etc.)
        """
        self.business_unit = business_unit
        self.logger = logger_utils.get_logger(f"{business_unit}_flow")
        
        # Inicializar componentes
        self.skill_processor = create_skill_processor(
            business_unit,
            mode='executive' if business_unit == 'huntRED Executive' else 'technical'
        )
        
        self.cv_generator = CVGenerator(template='blind')
        self.signature = DigitalSignature()
        self.job_scraper = JobScraper()
        self.nlp = NLPProcessor(
            business_unit=business_unit,
            mode="candidate",
            analysis_depth="deep"
        )
        
    async def process_new_opportunities(self) -> List[Dict]:
        """
        Procesa nuevas oportunidades y las integra con el sistema.
        
        Returns:
            Lista de oportunidades procesadas
        """
        try:
            # Scraping de nuevas oportunidades
            new_jobs = await self.job_scraper.scrape()
            
            # Análisis de requerimientos
            analyzed_jobs = []
            for job in new_jobs:
                analysis = await self.nlp.analyze(job['description'])
                job['skills'] = analysis['skills']
                job['competencies'] = analysis['competencies']
                analyzed_jobs.append(job)
                
            return analyzed_jobs
            
        except Exception as e:
            self.logger.error(f"Error procesando oportunidades: {str(e)}")
            return []
            
    async def match_candidates(self, opportunities: List[Dict]) -> Dict:
        """
        Empareja candidatos con oportunidades.
        
        Args:
            opportunities: Lista de oportunidades procesadas
            
        Returns:
            Dict con emparejamientos
        """
        try:
            # Obtener candidatos existentes
            candidates = await self._get_candidates()
            
            # Analizar y emparejar
            matches = {}
            for candidate in candidates:
                candidate_profile = await self._analyze_candidate(candidate)
                
                for job in opportunities:
                    score = await self._calculate_match_score(
                        candidate_profile,
                        job
                    )
                    
                    if score > 0.7:  # Umbral de emparejamiento
                        matches.setdefault(job['id'], []).append({
                            'candidate': candidate,
                            'score': score,
                            'reasons': self._get_match_reasons(candidate_profile, job)
                        })
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Error en emparejamiento: {str(e)}")
            return {}
            
    async def process_candidate(self, candidate_data: Dict) -> Dict:
        """
        Procesa un candidato completo: análisis, CV, firma, etc.
        
        Args:
            candidate_data: Datos del candidato
            
        Returns:
            Dict con resultado del procesamiento
        """
        try:
            # Validar identidad
            identity_valid, reason = validate_identity(
                candidate_data['name'],
                candidate_data['birthdate'],
                candidate_data.get('conscious', 'sí'),
                candidate_data.get('sober', 'no')
            )
            
            if not identity_valid:
                return {'status': 'error', 'reason': reason}
                
            # Analizar perfil
            profile = await self._analyze_candidate(candidate_data)
            
            # Generar CV ciego
            cv_data = CVData(**profile)
            cv_pdf = await self.cv_generator.generate(cv_data)
            
            # Obtener firma digital
            signature = await self.signature.get_signature(
                candidate_data['name'],
                cv_pdf
            )
            
            return {
                'status': 'success',
                'profile': profile,
                'cv': cv_pdf,
                'signature': signature,
                'blind_identifier': cv_data.get_blind_identifier()
            }
            
        except Exception as e:
            self.logger.error(f"Error procesando candidato: {str(e)}")
            return {'status': 'error', 'reason': str(e)}
            
    async def _analyze_candidate(self, candidate_data: Dict) -> Dict:
        """Analiza el perfil completo del candidato."""
        skills = await self.skill_processor.analyze_skills(candidate_data['skills'])
        competencies = await self.skill_processor.analyze_competencies(candidate_data['competencies'])
        
        return {
            'skills': skills,
            'competencies': competencies,
            'experience': candidate_data['experience'],
            'education': candidate_data['education'],
            'business_unit': self.business_unit
        }
        
    async def _calculate_match_score(self, candidate: Dict, job: Dict) -> float:
        """Calcula el score de emparejamiento."""
        skill_score = self._calculate_skill_match(candidate, job)
        competency_score = self._calculate_competency_match(candidate, job)
        experience_score = self._calculate_experience_match(candidate, job)
        
        return (skill_score + competency_score + experience_score) / 3
        
    def _get_match_reasons(self, candidate: Dict, job: Dict) -> List[str]:
        """Obtiene razones de emparejamiento."""
        reasons = []
        
        # Coincidencias de habilidades
        skill_matches = set(candidate['skills']) & set(job['skills'])
        if skill_matches:
            reasons.append(f"Coincidencias en habilidades: {', '.join(skill_matches)}")
            
        # Coincidencias de competencias
        competency_matches = set(candidate['competencies']) & set(job['competencies'])
        if competency_matches:
            reasons.append(f"Coincidencias en competencias: {', '.join(competency_matches)}")
            
        return reasons
