"""
Advanced Risk Analysis Engine - huntRED® v2
Sistema completo de análisis de riesgos con ML predictivo, scoring dinámico y verificación automatizada.
"""

import asyncio
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import statistics
import requests
from collections import defaultdict

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Niveles de riesgo."""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(Enum):
    """Categorías de riesgo."""
    EMPLOYMENT = "employment"
    CRIMINAL = "criminal"
    FINANCIAL = "financial"
    REGULATORY = "regulatory"
    REPUTATIONAL = "reputational"
    TECHNICAL = "technical"
    CULTURAL = "cultural"
    LEGAL = "legal"
    OPERATIONAL = "operational"


class BackgroundCheckType(Enum):
    """Tipos de verificación de antecedentes."""
    CRIMINAL_RECORD = "criminal_record"
    EMPLOYMENT_HISTORY = "employment_history"
    EDUCATION_VERIFICATION = "education_verification"
    CREDIT_CHECK = "credit_check"
    REFERENCE_CHECK = "reference_check"
    SOCIAL_MEDIA_SCREENING = "social_media_screening"
    PROFESSIONAL_LICENSE = "professional_license"
    DRUG_SCREENING = "drug_screening"
    IDENTITY_VERIFICATION = "identity_verification"


@dataclass
class RiskFactor:
    """Factor de riesgo individual."""
    id: str
    category: RiskCategory
    name: str
    description: str
    severity: float  # 0.0 - 1.0
    probability: float  # 0.0 - 1.0
    impact: float  # 0.0 - 1.0
    evidence: Dict[str, Any]
    mitigation_strategies: List[str]
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class BackgroundCheckResult:
    """Resultado de verificación de antecedentes."""
    check_type: BackgroundCheckType
    status: str  # clear, pending, flagged, failed
    details: Dict[str, Any]
    confidence: float
    completed_at: datetime = field(default_factory=datetime.now)
    provider: Optional[str] = None
    cost: Optional[float] = None


@dataclass
class RiskProfile:
    """Perfil completo de riesgo de un candidato."""
    candidate_id: str
    overall_risk_score: float  # 0.0 - 1.0
    risk_level: RiskLevel
    risk_factors: List[RiskFactor]
    background_checks: List[BackgroundCheckResult]
    predictive_indicators: Dict[str, float]
    mitigation_plan: List[str]
    last_updated: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class RiskAlert:
    """Alerta de riesgo."""
    id: str
    candidate_id: str
    risk_category: RiskCategory
    severity: RiskLevel
    message: str
    details: Dict[str, Any]
    action_required: bool
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False


class PredictiveRiskModel:
    """Modelo predictivo de riesgos usando ML."""
    
    def __init__(self):
        # Pesos del modelo (en producción serían entrenados con ML)
        self.feature_weights = {
            'employment_gaps': 0.3,
            'job_hopping': 0.25,
            'salary_inconsistencies': 0.2,
            'reference_quality': 0.15,
            'education_verification': 0.1,
            'social_media_flags': 0.2,
            'criminal_history': 0.8,
            'financial_stability': 0.3,
            'professional_licenses': 0.15
        }
        
        # Thresholds para diferentes factores
        self.risk_thresholds = {
            'employment_gap_months': 6,
            'job_changes_per_year': 1.5,
            'salary_variance_threshold': 0.3,
            'reference_score_minimum': 0.7
        }
    
    def predict_risk_score(self, candidate_data: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """Predice score de riesgo basado en datos del candidato."""
        feature_scores = {}
        
        # Analizar gaps de empleo
        employment_gaps = self._analyze_employment_gaps(
            candidate_data.get('work_experience', [])
        )
        feature_scores['employment_gaps'] = employment_gaps
        
        # Analizar job hopping
        job_hopping = self._analyze_job_hopping(
            candidate_data.get('work_experience', [])
        )
        feature_scores['job_hopping'] = job_hopping
        
        # Analizar inconsistencias salariales
        salary_issues = self._analyze_salary_consistency(
            candidate_data.get('work_experience', [])
        )
        feature_scores['salary_inconsistencies'] = salary_issues
        
        # Calidad de referencias
        reference_quality = self._analyze_reference_quality(
            candidate_data.get('references', [])
        )
        feature_scores['reference_quality'] = 1.0 - reference_quality  # Invertir para riesgo
        
        # Verificación educativa
        education_risk = self._analyze_education_risk(
            candidate_data.get('education', [])
        )
        feature_scores['education_verification'] = education_risk
        
        # Flags de redes sociales
        social_media_risk = self._analyze_social_media_risk(
            candidate_data.get('social_media_screening', {})
        )
        feature_scores['social_media_flags'] = social_media_risk
        
        # Calcular score ponderado
        weighted_score = 0.0
        total_weight = 0.0
        
        for feature, score in feature_scores.items():
            if feature in self.feature_weights:
                weight = self.feature_weights[feature]
                weighted_score += score * weight
                total_weight += weight
        
        final_score = weighted_score / total_weight if total_weight > 0 else 0.0
        
        return min(final_score, 1.0), feature_scores
    
    def _analyze_employment_gaps(self, work_experience: List[Dict[str, Any]]) -> float:
        """Analiza gaps en el historial laboral."""
        if not work_experience or len(work_experience) < 2:
            return 0.0
        
        # Ordenar por fecha
        sorted_exp = sorted(work_experience, 
                           key=lambda x: self._parse_date(x.get('start_date', '')))
        
        total_gap_months = 0
        for i in range(len(sorted_exp) - 1):
            current_end = self._parse_date(sorted_exp[i].get('end_date', ''))
            next_start = self._parse_date(sorted_exp[i + 1].get('start_date', ''))
            
            if current_end and next_start and next_start > current_end:
                gap_months = (next_start - current_end).days / 30.44
                total_gap_months += gap_months
        
        # Normalizar basado en threshold
        risk_score = min(total_gap_months / self.risk_thresholds['employment_gap_months'], 1.0)
        return risk_score
    
    def _analyze_job_hopping(self, work_experience: List[Dict[str, Any]]) -> float:
        """Analiza tendencia de cambio frecuente de trabajo."""
        if not work_experience:
            return 0.0
        
        if len(work_experience) < 2:
            return 0.0
        
        # Calcular años totales de experiencia
        sorted_exp = sorted(work_experience, 
                           key=lambda x: self._parse_date(x.get('start_date', '')))
        
        first_job = self._parse_date(sorted_exp[0].get('start_date', ''))
        last_job = self._parse_date(sorted_exp[-1].get('end_date', '')) or datetime.now()
        
        if not first_job:
            return 0.0
        
        total_years = (last_job - first_job).days / 365.25
        if total_years == 0:
            return 0.0
        
        job_changes_per_year = len(work_experience) / total_years
        
        # Normalizar basado en threshold
        risk_score = min(job_changes_per_year / self.risk_thresholds['job_changes_per_year'], 1.0)
        return risk_score
    
    def _analyze_salary_consistency(self, work_experience: List[Dict[str, Any]]) -> float:
        """Analiza consistencia en progresión salarial."""
        salaries = []
        for exp in work_experience:
            salary_str = exp.get('salary', '')
            if salary_str:
                try:
                    # Extraer número del salary string
                    import re
                    salary_num = re.sub(r'[^\d.]', '', salary_str)
                    if salary_num:
                        salaries.append(float(salary_num))
                except ValueError:
                    continue
        
        if len(salaries) < 2:
            return 0.0
        
        # Calcular varianza normalizada
        mean_salary = statistics.mean(salaries)
        variance = statistics.variance(salaries)
        
        if mean_salary == 0:
            return 0.0
        
        coefficient_of_variation = (variance ** 0.5) / mean_salary
        
        # Si la variación es muy alta, es riesgoso
        risk_score = min(coefficient_of_variation / self.risk_thresholds['salary_variance_threshold'], 1.0)
        return risk_score
    
    def _analyze_reference_quality(self, references: List[Dict[str, Any]]) -> float:
        """Analiza calidad de las referencias."""
        if not references:
            return 0.0  # Sin referencias es score bajo
        
        quality_scores = []
        for ref in references:
            score = 0.0
            
            # Verificar completitud de información
            if ref.get('name'):
                score += 0.2
            if ref.get('company'):
                score += 0.2
            if ref.get('position'):
                score += 0.2
            if ref.get('relationship'):
                score += 0.2
            if ref.get('contact_info'):
                score += 0.2
            
            # Bonus por referencias directas vs HR
            if 'manager' in ref.get('relationship', '').lower():
                score += 0.1
            
            quality_scores.append(min(score, 1.0))
        
        avg_quality = statistics.mean(quality_scores)
        return avg_quality
    
    def _analyze_education_risk(self, education: List[Dict[str, Any]]) -> float:
        """Analiza riesgos en verificación educativa."""
        if not education:
            return 0.3  # Sin educación reportada es moderadamente riesgoso
        
        risk_factors = 0.0
        
        for edu in education:
            institution = edu.get('institution', '')
            degree = edu.get('degree', '')
            
            # Flags de riesgo
            if not institution:
                risk_factors += 0.3
            if not degree:
                risk_factors += 0.2
            
            # Verificar si parece institución legítima (simplificado)
            suspicious_keywords = ['online', 'diploma mill', 'certificate']
            if any(keyword in institution.lower() for keyword in suspicious_keywords):
                risk_factors += 0.4
        
        return min(risk_factors / len(education), 1.0)
    
    def _analyze_social_media_risk(self, social_media_data: Dict[str, Any]) -> float:
        """Analiza riesgos en redes sociales."""
        if not social_media_data:
            return 0.0
        
        risk_score = 0.0
        
        # Flags de contenido inapropiado
        inappropriate_content = social_media_data.get('inappropriate_content', 0)
        risk_score += min(inappropriate_content * 0.2, 0.6)
        
        # Actividad discriminatoria
        discriminatory_content = social_media_data.get('discriminatory_content', 0)
        risk_score += min(discriminatory_content * 0.3, 0.8)
        
        # Inconsistencias con CV
        profile_inconsistencies = social_media_data.get('profile_inconsistencies', 0)
        risk_score += min(profile_inconsistencies * 0.1, 0.3)
        
        return min(risk_score, 1.0)
    
    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parsea string de fecha."""
        if not date_string or date_string.lower() in ['present', 'current']:
            return datetime.now()
        
        formats = ['%Y-%m-%d', '%Y-%m', '%Y', '%m/%Y', '%d/%m/%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_string.strip(), fmt)
            except ValueError:
                continue
        return None


class BackgroundCheckService:
    """Servicio de verificación de antecedentes."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers = {
            'criminal': config.get('criminal_check_provider'),
            'employment': config.get('employment_check_provider'),
            'education': config.get('education_check_provider'),
            'credit': config.get('credit_check_provider')
        }
    
    async def perform_background_check(self, candidate_id: str, 
                                     check_types: List[BackgroundCheckType],
                                     candidate_data: Dict[str, Any]) -> List[BackgroundCheckResult]:
        """Realiza verificaciones de antecedentes."""
        results = []
        
        for check_type in check_types:
            try:
                result = await self._perform_specific_check(check_type, candidate_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in {check_type.value} check: {str(e)}")
                # Crear resultado de error
                error_result = BackgroundCheckResult(
                    check_type=check_type,
                    status='failed',
                    details={'error': str(e)},
                    confidence=0.0
                )
                results.append(error_result)
        
        return results
    
    async def _perform_specific_check(self, check_type: BackgroundCheckType,
                                    candidate_data: Dict[str, Any]) -> BackgroundCheckResult:
        """Realiza verificación específica."""
        
        if check_type == BackgroundCheckType.CRIMINAL_RECORD:
            return await self._criminal_record_check(candidate_data)
        elif check_type == BackgroundCheckType.EMPLOYMENT_HISTORY:
            return await self._employment_history_check(candidate_data)
        elif check_type == BackgroundCheckType.EDUCATION_VERIFICATION:
            return await self._education_verification_check(candidate_data)
        elif check_type == BackgroundCheckType.CREDIT_CHECK:
            return await self._credit_check(candidate_data)
        elif check_type == BackgroundCheckType.SOCIAL_MEDIA_SCREENING:
            return await self._social_media_screening(candidate_data)
        elif check_type == BackgroundCheckType.IDENTITY_VERIFICATION:
            return await self._identity_verification(candidate_data)
        else:
            # Default para otros tipos
            return BackgroundCheckResult(
                check_type=check_type,
                status='pending',
                details={'message': 'Check type not implemented'},
                confidence=0.0
            )
    
    async def _criminal_record_check(self, candidate_data: Dict[str, Any]) -> BackgroundCheckResult:
        """Verificación de antecedentes penales."""
        # En producción, esto se integraría con servicios como:
        # - National Crime Information Center (NCIC)
        # - State criminal databases
        # - International criminal databases
        
        name = candidate_data.get('name', '')
        ssn = candidate_data.get('ssn', '')
        
        # Simulación de verificación
        await asyncio.sleep(1)  # Simular tiempo de procesamiento
        
        # Verificación simulada basada en nombre
        high_risk_indicators = ['test criminal', 'fraud', 'convicted']
        has_record = any(indicator in name.lower() for indicator in high_risk_indicators)
        
        if has_record:
            status = 'flagged'
            details = {
                'records_found': 1,
                'severity': 'moderate',
                'charges': ['Financial fraud'],
                'dates': ['2018-03-15'],
                'disposition': 'Convicted'
            }
            confidence = 0.85
        else:
            status = 'clear'
            details = {
                'records_found': 0,
                'search_scope': 'National and state databases',
                'coverage_years': 7
            }
            confidence = 0.95
        
        return BackgroundCheckResult(
            check_type=BackgroundCheckType.CRIMINAL_RECORD,
            status=status,
            details=details,
            confidence=confidence,
            provider='CriminalCheckPro'
        )
    
    async def _employment_history_check(self, candidate_data: Dict[str, Any]) -> BackgroundCheckResult:
        """Verificación de historial laboral."""
        work_experience = candidate_data.get('work_experience', [])
        
        verified_count = 0
        unverified_count = 0
        discrepancies = []
        
        for exp in work_experience:
            company = exp.get('company', '')
            position = exp.get('position', '')
            
            # Simulación de verificación
            if 'google' in company.lower() or 'microsoft' in company.lower():
                verified_count += 1
            else:
                unverified_count += 1
                if 'fake' in company.lower():
                    discrepancies.append(f"Could not verify employment at {company}")
        
        total_positions = len(work_experience)
        verification_rate = verified_count / total_positions if total_positions > 0 else 0
        
        if verification_rate >= 0.8:
            status = 'clear'
        elif verification_rate >= 0.6:
            status = 'pending'
        else:
            status = 'flagged'
        
        return BackgroundCheckResult(
            check_type=BackgroundCheckType.EMPLOYMENT_HISTORY,
            status=status,
            details={
                'total_positions': total_positions,
                'verified_positions': verified_count,
                'unverified_positions': unverified_count,
                'verification_rate': verification_rate,
                'discrepancies': discrepancies
            },
            confidence=0.8,
            provider='EmploymentVerify'
        )
    
    async def _education_verification_check(self, candidate_data: Dict[str, Any]) -> BackgroundCheckResult:
        """Verificación de credenciales educativas."""
        education = candidate_data.get('education', [])
        
        verified_count = 0
        total_credentials = len(education)
        issues = []
        
        for edu in education:
            institution = edu.get('institution', '')
            degree = edu.get('degree', '')
            
            # Simulación de verificación
            reputable_institutions = ['harvard', 'mit', 'stanford', 'berkeley']
            if any(inst in institution.lower() for inst in reputable_institutions):
                verified_count += 1
            elif 'fake' in institution.lower() or 'mill' in institution.lower():
                issues.append(f"Suspicious institution: {institution}")
        
        verification_rate = verified_count / total_credentials if total_credentials > 0 else 1.0
        
        if verification_rate >= 0.9 and not issues:
            status = 'clear'
        elif issues:
            status = 'flagged'
        else:
            status = 'pending'
        
        return BackgroundCheckResult(
            check_type=BackgroundCheckType.EDUCATION_VERIFICATION,
            status=status,
            details={
                'total_credentials': total_credentials,
                'verified_credentials': verified_count,
                'verification_rate': verification_rate,
                'issues': issues
            },
            confidence=0.85,
            provider='EduVerify'
        )
    
    async def _credit_check(self, candidate_data: Dict[str, Any]) -> BackgroundCheckResult:
        """Verificación crediticia."""
        # Simulación de credit check
        await asyncio.sleep(0.5)
        
        # Score simulado basado en datos
        base_score = 650
        name = candidate_data.get('name', '')
        
        if 'good' in name.lower():
            credit_score = 750
        elif 'bad' in name.lower():
            credit_score = 450
        else:
            credit_score = base_score
        
        if credit_score >= 700:
            status = 'clear'
            risk_level = 'low'
        elif credit_score >= 600:
            status = 'pending'
            risk_level = 'moderate'
        else:
            status = 'flagged'
            risk_level = 'high'
        
        return BackgroundCheckResult(
            check_type=BackgroundCheckType.CREDIT_CHECK,
            status=status,
            details={
                'credit_score': credit_score,
                'risk_level': risk_level,
                'delinquencies': 0 if credit_score > 600 else 2,
                'bankruptcies': 0 if credit_score > 500 else 1
            },
            confidence=0.9,
            provider='CreditBureau'
        )
    
    async def _social_media_screening(self, candidate_data: Dict[str, Any]) -> BackgroundCheckResult:
        """Screening de redes sociales."""
        # Simulación de análisis de redes sociales
        name = candidate_data.get('name', '')
        
        flags = []
        risk_score = 0.0
        
        # Simulación de flags basada en nombre
        if 'inappropriate' in name.lower():
            flags.append('Inappropriate content found')
            risk_score += 0.3
        
        if 'discriminatory' in name.lower():
            flags.append('Discriminatory language detected')
            risk_score += 0.5
        
        if risk_score == 0:
            status = 'clear'
        elif risk_score < 0.4:
            status = 'pending'
        else:
            status = 'flagged'
        
        return BackgroundCheckResult(
            check_type=BackgroundCheckType.SOCIAL_MEDIA_SCREENING,
            status=status,
            details={
                'platforms_screened': ['LinkedIn', 'Facebook', 'Twitter'],
                'flags': flags,
                'risk_score': risk_score,
                'content_categories': {
                    'professional': 0.8,
                    'personal': 0.2,
                    'inappropriate': risk_score
                }
            },
            confidence=0.7,
            provider='SocialScreener'
        )
    
    async def _identity_verification(self, candidate_data: Dict[str, Any]) -> BackgroundCheckResult:
        """Verificación de identidad."""
        # Simulación de verificación de identidad
        required_fields = ['name', 'ssn', 'date_of_birth', 'address']
        provided_fields = [field for field in required_fields if candidate_data.get(field)]
        
        completeness = len(provided_fields) / len(required_fields)
        
        if completeness >= 0.9:
            status = 'clear'
            identity_confidence = 0.95
        elif completeness >= 0.7:
            status = 'pending'
            identity_confidence = 0.8
        else:
            status = 'flagged'
            identity_confidence = 0.5
        
        return BackgroundCheckResult(
            check_type=BackgroundCheckType.IDENTITY_VERIFICATION,
            status=status,
            details={
                'completeness': completeness,
                'provided_fields': provided_fields,
                'missing_fields': [f for f in required_fields if f not in provided_fields],
                'identity_confidence': identity_confidence
            },
            confidence=identity_confidence,
            provider='IDVerify'
        )


class AdvancedRiskEngine:
    """
    Motor avanzado de análisis de riesgos con:
    - ML predictivo para scoring de riesgos
    - Background checks automatizados
    - Detección de red flags en tiempo real
    - Alertas inteligentes
    - Mitigación de riesgos automatizada
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Servicios especializados
        self.predictive_model = PredictiveRiskModel()
        self.background_check_service = BackgroundCheckService(config)
        
        # Perfiles de riesgo
        self.risk_profiles: Dict[str, RiskProfile] = {}
        self.risk_alerts: Dict[str, RiskAlert] = {}
        
        # Configuración de thresholds
        self.risk_thresholds = {
            'automatic_reject': 0.9,
            'require_approval': 0.7,
            'enhanced_screening': 0.5,
            'standard_process': 0.3
        }
        
        # Métricas del sistema
        self.metrics = {
            'total_assessments': 0,
            'high_risk_candidates': 0,
            'background_checks_performed': 0,
            'alerts_generated': 0
        }
    
    async def assess_candidate_risk(self, candidate_id: str, candidate_data: Dict[str, Any],
                                  include_background_checks: bool = True) -> RiskProfile:
        """Evaluación completa de riesgo de un candidato."""
        try:
            logger.info(f"Starting risk assessment for candidate {candidate_id}")
            
            # 1. Análisis predictivo con ML
            predicted_score, feature_scores = self.predictive_model.predict_risk_score(candidate_data)
            
            # 2. Identificar factores de riesgo específicos
            risk_factors = await self._identify_risk_factors(candidate_data, feature_scores)
            
            # 3. Realizar background checks si es necesario
            background_checks = []
            if include_background_checks and predicted_score > self.risk_thresholds['enhanced_screening']:
                check_types = self._determine_required_checks(predicted_score, risk_factors)
                background_checks = await self.background_check_service.perform_background_check(
                    candidate_id, check_types, candidate_data
                )
            
            # 4. Ajustar score basado en background checks
            final_score = self._adjust_score_with_background_checks(predicted_score, background_checks)
            
            # 5. Determinar nivel de riesgo
            risk_level = self._determine_risk_level(final_score)
            
            # 6. Generar plan de mitigación
            mitigation_plan = self._generate_mitigation_plan(risk_factors, background_checks, risk_level)
            
            # 7. Crear perfil de riesgo
            profile = RiskProfile(
                candidate_id=candidate_id,
                overall_risk_score=final_score,
                risk_level=risk_level,
                risk_factors=risk_factors,
                background_checks=background_checks,
                predictive_indicators=feature_scores,
                mitigation_plan=mitigation_plan,
                expires_at=datetime.now() + timedelta(days=90)  # Los análisis de riesgo expiran
            )
            
            # 8. Generar alertas si es necesario
            await self._generate_risk_alerts(candidate_id, profile)
            
            # 9. Guardar perfil
            self.risk_profiles[candidate_id] = profile
            
            # 10. Actualizar métricas
            self.metrics['total_assessments'] += 1
            if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                self.metrics['high_risk_candidates'] += 1
            self.metrics['background_checks_performed'] += len(background_checks)
            
            logger.info(f"Risk assessment completed for {candidate_id}: {risk_level.value} ({final_score:.2f})")
            return profile
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {str(e)}")
            raise
    
    async def _identify_risk_factors(self, candidate_data: Dict[str, Any], 
                                   feature_scores: Dict[str, float]) -> List[RiskFactor]:
        """Identifica factores de riesgo específicos."""
        risk_factors = []
        
        # Factor: Employment gaps
        if feature_scores.get('employment_gaps', 0) > 0.5:
            risk_factors.append(RiskFactor(
                id=str(uuid.uuid4()),
                category=RiskCategory.EMPLOYMENT,
                name="Employment Gaps",
                description="Significant gaps in employment history detected",
                severity=feature_scores['employment_gaps'],
                probability=0.8,
                impact=0.6,
                evidence={'gap_score': feature_scores['employment_gaps']},
                mitigation_strategies=[
                    "Request explanation for employment gaps",
                    "Verify reasons with previous employers",
                    "Consider alternative activities during gaps"
                ]
            ))
        
        # Factor: Job hopping
        if feature_scores.get('job_hopping', 0) > 0.6:
            risk_factors.append(RiskFactor(
                id=str(uuid.uuid4()),
                category=RiskCategory.EMPLOYMENT,
                name="Job Hopping Pattern",
                description="Frequent job changes indicating potential instability",
                severity=feature_scores['job_hopping'],
                probability=0.7,
                impact=0.5,
                evidence={'hopping_score': feature_scores['job_hopping']},
                mitigation_strategies=[
                    "Discuss career progression goals",
                    "Evaluate commitment to long-term employment",
                    "Consider probationary period"
                ]
            ))
        
        # Factor: Reference quality
        if feature_scores.get('reference_quality', 0) > 0.4:
            risk_factors.append(RiskFactor(
                id=str(uuid.uuid4()),
                category=RiskCategory.REPUTATIONAL,
                name="Poor Reference Quality",
                description="References provided are incomplete or inadequate",
                severity=feature_scores['reference_quality'],
                probability=0.6,
                impact=0.7,
                evidence={'reference_score': 1.0 - feature_scores['reference_quality']},
                mitigation_strategies=[
                    "Request additional references",
                    "Conduct thorough reference checks",
                    "Verify reference authenticity"
                ]
            ))
        
        # Factor: Education verification issues
        if feature_scores.get('education_verification', 0) > 0.3:
            risk_factors.append(RiskFactor(
                id=str(uuid.uuid4()),
                category=RiskCategory.REGULATORY,
                name="Education Verification Risk",
                description="Potential issues with educational credentials",
                severity=feature_scores['education_verification'],
                probability=0.7,
                impact=0.8,
                evidence={'education_risk_score': feature_scores['education_verification']},
                mitigation_strategies=[
                    "Request official transcripts",
                    "Verify institution accreditation",
                    "Contact educational institutions directly"
                ]
            ))
        
        # Factor: Social media red flags
        if feature_scores.get('social_media_flags', 0) > 0.3:
            risk_factors.append(RiskFactor(
                id=str(uuid.uuid4()),
                category=RiskCategory.REPUTATIONAL,
                name="Social Media Red Flags",
                description="Inappropriate content found in social media screening",
                severity=feature_scores['social_media_flags'],
                probability=0.8,
                impact=0.6,
                evidence={'social_media_score': feature_scores['social_media_flags']},
                mitigation_strategies=[
                    "Discuss social media policy",
                    "Consider cultural fit assessment",
                    "Implement social media training"
                ]
            ))
        
        return risk_factors
    
    def _determine_required_checks(self, risk_score: float, 
                                 risk_factors: List[RiskFactor]) -> List[BackgroundCheckType]:
        """Determina qué verificaciones son necesarias basado en el riesgo."""
        required_checks = []
        
        # Checks básicos para todos los candidatos de riesgo medio-alto
        if risk_score > self.risk_thresholds['enhanced_screening']:
            required_checks.extend([
                BackgroundCheckType.IDENTITY_VERIFICATION,
                BackgroundCheckType.EMPLOYMENT_HISTORY,
                BackgroundCheckType.EDUCATION_VERIFICATION
            ])
        
        # Checks adicionales para riesgo alto
        if risk_score > self.risk_thresholds['require_approval']:
            required_checks.extend([
                BackgroundCheckType.CRIMINAL_RECORD,
                BackgroundCheckType.REFERENCE_CHECK,
                BackgroundCheckType.SOCIAL_MEDIA_SCREENING
            ])
        
        # Checks exhaustivos para riesgo crítico
        if risk_score > self.risk_thresholds['automatic_reject']:
            required_checks.extend([
                BackgroundCheckType.CREDIT_CHECK,
                BackgroundCheckType.PROFESSIONAL_LICENSE
            ])
        
        # Checks específicos basados en factores de riesgo
        risk_categories = {rf.category for rf in risk_factors}
        
        if RiskCategory.FINANCIAL in risk_categories:
            required_checks.append(BackgroundCheckType.CREDIT_CHECK)
        
        if RiskCategory.REPUTATIONAL in risk_categories:
            required_checks.append(BackgroundCheckType.SOCIAL_MEDIA_SCREENING)
        
        if RiskCategory.REGULATORY in risk_categories:
            required_checks.append(BackgroundCheckType.PROFESSIONAL_LICENSE)
        
        # Remover duplicados
        return list(set(required_checks))
    
    def _adjust_score_with_background_checks(self, base_score: float, 
                                           background_checks: List[BackgroundCheckResult]) -> float:
        """Ajusta el score de riesgo basado en resultados de background checks."""
        adjustment = 0.0
        
        for check in background_checks:
            if check.status == 'flagged':
                # Incrementar riesgo para checks flagged
                adjustment += 0.15 * check.confidence
            elif check.status == 'clear':
                # Reducir riesgo para checks clear
                adjustment -= 0.05 * check.confidence
            # 'pending' no ajusta el score
        
        # Ajustes específicos por tipo de check
        for check in background_checks:
            if check.check_type == BackgroundCheckType.CRIMINAL_RECORD and check.status == 'flagged':
                adjustment += 0.3  # Criminal history es muy serio
            elif check.check_type == BackgroundCheckType.EDUCATION_VERIFICATION and check.status == 'flagged':
                adjustment += 0.2  # Credenciales falsas son serias
        
        final_score = base_score + adjustment
        return max(0.0, min(final_score, 1.0))  # Mantener en rango 0-1
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determina nivel de riesgo basado en score."""
        if risk_score >= self.risk_thresholds['automatic_reject']:
            return RiskLevel.CRITICAL
        elif risk_score >= self.risk_thresholds['require_approval']:
            return RiskLevel.HIGH
        elif risk_score >= self.risk_thresholds['enhanced_screening']:
            return RiskLevel.MODERATE
        elif risk_score >= self.risk_thresholds['standard_process']:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL
    
    def _generate_mitigation_plan(self, risk_factors: List[RiskFactor], 
                                background_checks: List[BackgroundCheckResult],
                                risk_level: RiskLevel) -> List[str]:
        """Genera plan de mitigación de riesgos."""
        mitigation_strategies = []
        
        # Estrategias basadas en factores de riesgo
        for factor in risk_factors:
            mitigation_strategies.extend(factor.mitigation_strategies)
        
        # Estrategias basadas en background checks
        for check in background_checks:
            if check.status == 'flagged':
                if check.check_type == BackgroundCheckType.CRIMINAL_RECORD:
                    mitigation_strategies.extend([
                        "Conduct detailed interview about criminal history",
                        "Evaluate rehabilitation evidence",
                        "Consider role-specific risk implications",
                        "Implement enhanced supervision"
                    ])
                elif check.check_type == BackgroundCheckType.EMPLOYMENT_HISTORY:
                    mitigation_strategies.extend([
                        "Obtain additional employment references",
                        "Verify employment details with HR departments",
                        "Consider probationary employment period"
                    ])
        
        # Estrategias basadas en nivel de riesgo
        if risk_level == RiskLevel.CRITICAL:
            mitigation_strategies.extend([
                "Require executive approval for hiring decision",
                "Implement comprehensive monitoring plan",
                "Consider alternative role with lower risk exposure",
                "Require additional insurance coverage"
            ])
        elif risk_level == RiskLevel.HIGH:
            mitigation_strategies.extend([
                "Require manager approval for hiring",
                "Implement enhanced onboarding process",
                "Schedule regular check-ins during probation"
            ])
        
        # Remover duplicados y retornar
        return list(set(mitigation_strategies))
    
    async def _generate_risk_alerts(self, candidate_id: str, profile: RiskProfile):
        """Genera alertas de riesgo si es necesario."""
        alerts = []
        
        # Alerta para riesgo crítico
        if profile.risk_level == RiskLevel.CRITICAL:
            alert = RiskAlert(
                id=str(uuid.uuid4()),
                candidate_id=candidate_id,
                risk_category=RiskCategory.OPERATIONAL,
                severity=RiskLevel.CRITICAL,
                message=f"CRITICAL RISK: Candidate {candidate_id} has critical risk factors",
                details={
                    'risk_score': profile.overall_risk_score,
                    'factor_count': len(profile.risk_factors),
                    'flagged_checks': len([c for c in profile.background_checks if c.status == 'flagged'])
                },
                action_required=True
            )
            alerts.append(alert)
        
        # Alertas por factores específicos
        high_severity_factors = [f for f in profile.risk_factors if f.severity > 0.8]
        for factor in high_severity_factors:
            alert = RiskAlert(
                id=str(uuid.uuid4()),
                candidate_id=candidate_id,
                risk_category=factor.category,
                severity=RiskLevel.HIGH,
                message=f"High-severity risk factor: {factor.name}",
                details={
                    'factor_id': factor.id,
                    'severity': factor.severity,
                    'description': factor.description
                },
                action_required=True
            )
            alerts.append(alert)
        
        # Guardar alertas
        for alert in alerts:
            self.risk_alerts[alert.id] = alert
            self.metrics['alerts_generated'] += 1
    
    def get_risk_profile(self, candidate_id: str) -> Optional[RiskProfile]:
        """Obtiene perfil de riesgo de un candidato."""
        return self.risk_profiles.get(candidate_id)
    
    def get_risk_recommendations(self, candidate_id: str) -> Dict[str, Any]:
        """Obtiene recomendaciones de riesgo para un candidato."""
        profile = self.risk_profiles.get(candidate_id)
        if not profile:
            return {'error': 'Risk profile not found'}
        
        # Determinar acción recomendada
        if profile.risk_level == RiskLevel.CRITICAL:
            recommended_action = "REJECT"
            reasoning = "Critical risk factors identified"
        elif profile.risk_level == RiskLevel.HIGH:
            recommended_action = "REQUIRE_APPROVAL"
            reasoning = "High risk requires additional oversight"
        elif profile.risk_level == RiskLevel.MODERATE:
            recommended_action = "ENHANCED_SCREENING"
            reasoning = "Moderate risk requires additional verification"
        else:
            recommended_action = "PROCEED"
            reasoning = "Low risk profile acceptable"
        
        return {
            'candidate_id': candidate_id,
            'risk_level': profile.risk_level.value,
            'risk_score': profile.overall_risk_score,
            'recommended_action': recommended_action,
            'reasoning': reasoning,
            'mitigation_plan': profile.mitigation_plan,
            'key_risk_factors': [
                {
                    'name': factor.name,
                    'category': factor.category.value,
                    'severity': factor.severity
                }
                for factor in sorted(profile.risk_factors, key=lambda x: x.severity, reverse=True)[:3]
            ],
            'background_check_summary': {
                'total_checks': len(profile.background_checks),
                'clear_checks': len([c for c in profile.background_checks if c.status == 'clear']),
                'flagged_checks': len([c for c in profile.background_checks if c.status == 'flagged']),
                'pending_checks': len([c for c in profile.background_checks if c.status == 'pending'])
            }
        }
    
    def get_active_alerts(self, acknowledged: bool = False) -> List[Dict[str, Any]]:
        """Obtiene alertas activas del sistema."""
        filtered_alerts = [
            alert for alert in self.risk_alerts.values()
            if alert.acknowledged == acknowledged
        ]
        
        return [
            {
                'id': alert.id,
                'candidate_id': alert.candidate_id,
                'category': alert.risk_category.value,
                'severity': alert.severity.value,
                'message': alert.message,
                'created_at': alert.created_at.isoformat(),
                'action_required': alert.action_required
            }
            for alert in sorted(filtered_alerts, key=lambda x: x.created_at, reverse=True)
        ]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Marca una alerta como reconocida."""
        alert = self.risk_alerts.get(alert_id)
        if alert:
            alert.acknowledged = True
            return True
        return False
    
    async def batch_assess_candidates(self, candidates_data: List[Dict[str, Any]]) -> Dict[str, RiskProfile]:
        """Evalúa múltiples candidatos en lote."""
        results = {}
        
        for candidate_data in candidates_data:
            candidate_id = candidate_data['candidate_id']
            
            try:
                profile = await self.assess_candidate_risk(candidate_id, candidate_data)
                results[candidate_id] = profile
            except Exception as e:
                logger.error(f"Error assessing candidate {candidate_id}: {str(e)}")
        
        return results
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema de análisis de riesgos."""
        # Distribución de niveles de riesgo
        risk_distribution = defaultdict(int)
        for profile in self.risk_profiles.values():
            risk_distribution[profile.risk_level.value] += 1
        
        return {
            **self.metrics,
            'total_profiles': len(self.risk_profiles),
            'active_alerts': len([a for a in self.risk_alerts.values() if not a.acknowledged]),
            'risk_distribution': dict(risk_distribution),
            'average_risk_score': (
                sum(p.overall_risk_score for p in self.risk_profiles.values()) / 
                len(self.risk_profiles) if self.risk_profiles else 0.0
            )
        }