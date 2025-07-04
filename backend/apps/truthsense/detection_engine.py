"""
TruthSense Detection Engine - huntRED® v2
Sistema avanzado de detección de inconsistencias, mentiras y análisis de veracidad con ML.
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import difflib
import requests
from collections import defaultdict

logger = logging.getLogger(__name__)


class VeracityLevel(Enum):
    """Niveles de veracidad."""
    TRUTHFUL = "truthful"
    QUESTIONABLE = "questionable"
    SUSPICIOUS = "suspicious"
    DECEPTIVE = "deceptive"
    FABRICATED = "fabricated"


class InconsistencyType(Enum):
    """Tipos de inconsistencias detectadas."""
    DATE_OVERLAP = "date_overlap"
    SALARY_INFLATION = "salary_inflation"
    TITLE_MISMATCH = "title_mismatch"
    COMPANY_VERIFICATION = "company_verification"
    EDUCATION_MISMATCH = "education_mismatch"
    SKILL_INFLATION = "skill_inflation"
    EXPERIENCE_GAP = "experience_gap"
    REFERENCE_MISMATCH = "reference_mismatch"
    LINGUISTIC_PATTERN = "linguistic_pattern"
    BEHAVIORAL_ANOMALY = "behavioral_anomaly"


class DataSource(Enum):
    """Fuentes de datos para verificación."""
    CV_DOCUMENT = "cv_document"
    LINKEDIN_PROFILE = "linkedin_profile"
    APPLICATION_FORM = "application_form"
    INTERVIEW_TRANSCRIPT = "interview_transcript"
    REFERENCE_CHECK = "reference_check"
    BACKGROUND_CHECK = "background_check"
    SOCIAL_MEDIA = "social_media"
    PUBLIC_RECORDS = "public_records"


@dataclass
class InconsistencyFinding:
    """Hallazgo de inconsistencia."""
    id: str
    inconsistency_type: InconsistencyType
    severity: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    description: str
    evidence: Dict[str, Any]
    sources: List[DataSource]
    recommendations: List[str]
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class VeracityProfile:
    """Perfil de veracidad de un candidato."""
    candidate_id: str
    overall_score: float  # 0.0 - 1.0
    veracity_level: VeracityLevel
    inconsistencies: List[InconsistencyFinding]
    verification_sources: List[DataSource]
    risk_factors: List[str]
    confidence_metrics: Dict[str, float]
    last_analysis: datetime = field(default_factory=datetime.now)


@dataclass
class CrossValidationResult:
    """Resultado de validación cruzada."""
    field_name: str
    sources: Dict[DataSource, Any]
    is_consistent: bool
    confidence: float
    discrepancies: List[str]


class LinguisticAnalyzer:
    """Analizador de patrones lingüísticos para detección de engaños."""
    
    def __init__(self):
        self.deception_indicators = {
            'hedge_words': ['maybe', 'perhaps', 'possibly', 'probably', 'might'],
            'distancing_words': ['that person', 'that company', 'those people'],
            'minimizing_words': ['just', 'only', 'simply', 'merely'],
            'qualifying_words': ['basically', 'generally', 'usually', 'mostly'],
            'evasive_patterns': [r'to be honest', r'to tell the truth', r'believe me'],
            'temporal_vagueness': [r'around \d+', r'approximately', r'roughly', r'about']
        }
    
    def analyze_text_patterns(self, text: str) -> Dict[str, Any]:
        """Analiza patrones lingüísticos indicativos de engaño."""
        if not text:
            return {'score': 0.0, 'indicators': []}
        
        text_lower = text.lower()
        indicators = []
        total_score = 0.0
        
        # Analizar palabras de cobertura
        hedge_count = sum(1 for word in self.deception_indicators['hedge_words'] 
                         if word in text_lower)
        if hedge_count > 0:
            score = min(hedge_count * 0.1, 0.3)
            total_score += score
            indicators.append(f"Hedge words detected: {hedge_count}")
        
        # Analizar distanciamiento
        distancing_count = sum(1 for word in self.deception_indicators['distancing_words'] 
                              if word in text_lower)
        if distancing_count > 0:
            score = min(distancing_count * 0.15, 0.4)
            total_score += score
            indicators.append(f"Distancing language: {distancing_count}")
        
        # Analizar patrones evasivos
        for pattern in self.deception_indicators['evasive_patterns']:
            if re.search(pattern, text_lower):
                total_score += 0.2
                indicators.append(f"Evasive pattern: {pattern}")
        
        # Analizar vaguedad temporal
        temporal_matches = []
        for pattern in self.deception_indicators['temporal_vagueness']:
            matches = re.findall(pattern, text_lower)
            temporal_matches.extend(matches)
        
        if temporal_matches:
            score = min(len(temporal_matches) * 0.1, 0.3)
            total_score += score
            indicators.append(f"Temporal vagueness: {len(temporal_matches)} instances")
        
        # Analizar longitud de respuestas (respuestas muy cortas pueden ser evasivas)
        word_count = len(text.split())
        if word_count < 10:
            total_score += 0.1
            indicators.append("Unusually short response")
        
        return {
            'score': min(total_score, 1.0),
            'indicators': indicators,
            'word_count': word_count,
            'hedge_ratio': hedge_count / max(word_count, 1),
            'distancing_ratio': distancing_count / max(word_count, 1)
        }


class DateConsistencyAnalyzer:
    """Analizador de consistencia de fechas."""
    
    def analyze_employment_timeline(self, experiences: List[Dict[str, Any]]) -> List[InconsistencyFinding]:
        """Analiza timeline de experiencia laboral para detectar inconsistencias."""
        findings = []
        
        if not experiences:
            return findings
        
        # Ordenar experiencias por fecha de inicio
        sorted_experiences = sorted(experiences, 
                                  key=lambda x: self._parse_date(x.get('start_date', '')))
        
        for i in range(len(sorted_experiences) - 1):
            current = sorted_experiences[i]
            next_exp = sorted_experiences[i + 1]
            
            current_start = self._parse_date(current.get('start_date', ''))
            current_end = self._parse_date(current.get('end_date', ''))
            next_start = self._parse_date(next_exp.get('start_date', ''))
            
            if not all([current_start, current_end, next_start]):
                continue
            
            # Verificar solapamiento
            if current_end > next_start:
                gap_days = (current_end - next_start).days
                
                finding = InconsistencyFinding(
                    id=str(uuid.uuid4()),
                    inconsistency_type=InconsistencyType.DATE_OVERLAP,
                    severity=min(gap_days / 30, 1.0),  # Severity based on overlap duration
                    confidence=0.9,
                    description=f"Employment overlap detected: {current.get('company')} and {next_exp.get('company')}",
                    evidence={
                        'overlap_days': gap_days,
                        'position1': current,
                        'position2': next_exp
                    },
                    sources=[DataSource.CV_DOCUMENT],
                    recommendations=[
                        "Verify employment dates with HR departments",
                        "Request official employment letters",
                        "Clarify if roles were part-time or consultant positions"
                    ]
                )
                findings.append(finding)
        
        return findings
    
    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parsea diferentes formatos de fecha."""
        if not date_string or date_string.lower() in ['present', 'current', 'now']:
            return datetime.now()
        
        # Formatos comunes
        formats = [
            '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', 
            '%Y-%m', '%m/%Y', '%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string.strip(), fmt)
            except ValueError:
                continue
        
        return None


class SalaryAnalyzer:
    """Analizador de consistencia salarial."""
    
    def __init__(self):
        # Datos de mercado salarial por país/industria (simplificado)
        self.salary_benchmarks = {
            'software_engineer': {
                'junior': (30000, 60000),
                'mid': (60000, 100000),
                'senior': (100000, 180000)
            },
            'data_scientist': {
                'junior': (40000, 70000),
                'mid': (70000, 120000),
                'senior': (120000, 200000)
            },
            'product_manager': {
                'junior': (50000, 80000),
                'mid': (80000, 130000),
                'senior': (130000, 220000)
            }
        }
    
    def analyze_salary_progression(self, experiences: List[Dict[str, Any]]) -> List[InconsistencyFinding]:
        """Analiza progresión salarial para detectar inflación."""
        findings = []
        
        sorted_experiences = sorted(experiences, 
                                  key=lambda x: self._parse_date(x.get('start_date', '')))
        
        for i in range(len(sorted_experiences) - 1):
            current = sorted_experiences[i]
            next_exp = sorted_experiences[i + 1]
            
            current_salary = self._extract_salary(current.get('salary', ''))
            next_salary = self._extract_salary(next_exp.get('salary', ''))
            
            if current_salary and next_salary:
                # Verificar incremento anormal
                increase_percentage = (next_salary - current_salary) / current_salary
                
                if increase_percentage > 0.5:  # Incremento > 50%
                    finding = InconsistencyFinding(
                        id=str(uuid.uuid4()),
                        inconsistency_type=InconsistencyType.SALARY_INFLATION,
                        severity=min(increase_percentage, 1.0),
                        confidence=0.7,
                        description=f"Unusual salary increase: {increase_percentage:.1%}",
                        evidence={
                            'previous_salary': current_salary,
                            'new_salary': next_salary,
                            'increase_percentage': increase_percentage,
                            'previous_company': current.get('company'),
                            'new_company': next_exp.get('company')
                        },
                        sources=[DataSource.CV_DOCUMENT],
                        recommendations=[
                            "Verify salary information with previous employers",
                            "Request salary certificates or tax documents",
                            "Check if currency or benefits are included"
                        ]
                    )
                    findings.append(finding)
        
        return findings
    
    def _extract_salary(self, salary_string: str) -> Optional[float]:
        """Extrae valor numérico del salario."""
        if not salary_string:
            return None
        
        # Remover monedas y formateo
        cleaned = re.sub(r'[^\d.]', '', salary_string)
        try:
            return float(cleaned)
        except ValueError:
            return None


class TruthSenseEngine:
    """
    Motor principal de TruthSense para detección de inconsistencias y análisis de veracidad.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Analizadores especializados
        self.linguistic_analyzer = LinguisticAnalyzer()
        self.date_analyzer = DateConsistencyAnalyzer()
        self.salary_analyzer = SalaryAnalyzer()
        
        # Perfiles de veracidad
        self.veracity_profiles: Dict[str, VeracityProfile] = {}
        
        # Base de datos de verificación
        self.verification_database = {}
        
        # Métricas del sistema
        self.metrics = {
            'total_analyses': 0,
            'inconsistencies_detected': 0,
            'accuracy_rate': 0.0,
            'false_positive_rate': 0.0
        }
    
    async def analyze_candidate_veracity(self, candidate_id: str, 
                                       data_sources: Dict[DataSource, Dict[str, Any]]) -> VeracityProfile:
        """Análisis completo de veracidad de un candidato."""
        try:
            logger.info(f"Starting TruthSense analysis for candidate {candidate_id}")
            
            inconsistencies = []
            confidence_metrics = {}
            
            # Análisis de consistencia de fechas
            if DataSource.CV_DOCUMENT in data_sources:
                cv_data = data_sources[DataSource.CV_DOCUMENT]
                experiences = cv_data.get('work_experience', [])
                
                date_inconsistencies = self.date_analyzer.analyze_employment_timeline(experiences)
                inconsistencies.extend(date_inconsistencies)
                
                salary_inconsistencies = self.salary_analyzer.analyze_salary_progression(experiences)
                inconsistencies.extend(salary_inconsistencies)
            
            # Análisis lingüístico en entrevistas
            if DataSource.INTERVIEW_TRANSCRIPT in data_sources:
                transcript = data_sources[DataSource.INTERVIEW_TRANSCRIPT]
                linguistic_analysis = await self._analyze_interview_linguistics(transcript)
                inconsistencies.extend(linguistic_analysis['inconsistencies'])
                confidence_metrics['linguistic_score'] = linguistic_analysis['score']
            
            # Validación cruzada entre fuentes
            cross_validation_results = await self._perform_cross_validation(data_sources)
            for result in cross_validation_results:
                if not result.is_consistent:
                    inconsistency = InconsistencyFinding(
                        id=str(uuid.uuid4()),
                        inconsistency_type=InconsistencyType.REFERENCE_MISMATCH,
                        severity=1.0 - result.confidence,
                        confidence=result.confidence,
                        description=f"Cross-validation failed for {result.field_name}",
                        evidence={
                            'field': result.field_name,
                            'sources': {source.value: value for source, value in result.sources.items()},
                            'discrepancies': result.discrepancies
                        },
                        sources=list(result.sources.keys()),
                        recommendations=[
                            "Verify information with original sources",
                            "Request additional documentation",
                            "Conduct follow-up interview"
                        ]
                    )
                    inconsistencies.append(inconsistency)
            
            # Verificación externa
            external_verification = await self._perform_external_verification(candidate_id, data_sources)
            inconsistencies.extend(external_verification)
            
            # Calcular score general de veracidad
            overall_score = self._calculate_veracity_score(inconsistencies, confidence_metrics)
            veracity_level = self._determine_veracity_level(overall_score)
            
            # Identificar factores de riesgo
            risk_factors = self._identify_risk_factors(inconsistencies)
            
            # Crear perfil de veracidad
            profile = VeracityProfile(
                candidate_id=candidate_id,
                overall_score=overall_score,
                veracity_level=veracity_level,
                inconsistencies=inconsistencies,
                verification_sources=list(data_sources.keys()),
                risk_factors=risk_factors,
                confidence_metrics=confidence_metrics
            )
            
            self.veracity_profiles[candidate_id] = profile
            self.metrics['total_analyses'] += 1
            self.metrics['inconsistencies_detected'] += len(inconsistencies)
            
            logger.info(f"TruthSense analysis completed for {candidate_id}: {veracity_level.value} ({overall_score:.2f})")
            return profile
            
        except Exception as e:
            logger.error(f"Error in TruthSense analysis: {str(e)}")
            raise
    
    async def _analyze_interview_linguistics(self, transcript: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza patrones lingüísticos en transcripciones de entrevistas."""
        inconsistencies = []
        total_deception_score = 0.0
        
        responses = transcript.get('responses', [])
        
        for response in responses:
            question = response.get('question', '')
            answer = response.get('answer', '')
            
            linguistic_analysis = self.linguistic_analyzer.analyze_text_patterns(answer)
            
            if linguistic_analysis['score'] > 0.5:  # Threshold para sospecha
                inconsistency = InconsistencyFinding(
                    id=str(uuid.uuid4()),
                    inconsistency_type=InconsistencyType.LINGUISTIC_PATTERN,
                    severity=linguistic_analysis['score'],
                    confidence=0.6,  # Linguistic analysis is less certain
                    description=f"Deceptive linguistic patterns detected in response to: {question[:100]}...",
                    evidence={
                        'question': question,
                        'answer': answer,
                        'indicators': linguistic_analysis['indicators'],
                        'deception_score': linguistic_analysis['score']
                    },
                    sources=[DataSource.INTERVIEW_TRANSCRIPT],
                    recommendations=[
                        "Follow up with specific probing questions",
                        "Request concrete examples and documentation",
                        "Consider behavioral interview techniques"
                    ]
                )
                inconsistencies.append(inconsistency)
            
            total_deception_score += linguistic_analysis['score']
        
        avg_score = total_deception_score / len(responses) if responses else 0.0
        
        return {
            'inconsistencies': inconsistencies,
            'score': avg_score,
            'total_responses': len(responses)
        }
    
    async def _perform_cross_validation(self, data_sources: Dict[DataSource, Dict[str, Any]]) -> List[CrossValidationResult]:
        """Realiza validación cruzada entre diferentes fuentes de datos."""
        results = []
        
        # Campos comunes para validar
        fields_to_validate = [
            'name', 'email', 'phone', 'current_title', 'current_company',
            'education', 'skills', 'certifications'
        ]
        
        for field in fields_to_validate:
            field_sources = {}
            
            # Extraer valor del campo de cada fuente
            for source, data in data_sources.items():
                value = self._extract_field_value(data, field)
                if value:
                    field_sources[source] = value
            
            if len(field_sources) >= 2:  # Al menos 2 fuentes para comparar
                is_consistent, confidence, discrepancies = self._compare_field_values(field_sources)
                
                result = CrossValidationResult(
                    field_name=field,
                    sources=field_sources,
                    is_consistent=is_consistent,
                    confidence=confidence,
                    discrepancies=discrepancies
                )
                results.append(result)
        
        return results
    
    def _extract_field_value(self, data: Dict[str, Any], field: str) -> Any:
        """Extrae valor de un campo específico de los datos."""
        # Mapeo de campos a rutas en los datos
        field_paths = {
            'name': ['name', 'full_name', 'candidate_name'],
            'email': ['email', 'email_address', 'contact_email'],
            'phone': ['phone', 'phone_number', 'mobile'],
            'current_title': ['current_position', 'title', 'job_title'],
            'current_company': ['current_company', 'company', 'employer'],
            'education': ['education', 'academic_background'],
            'skills': ['skills', 'technical_skills', 'competencies'],
            'certifications': ['certifications', 'certificates', 'credentials']
        }
        
        paths = field_paths.get(field, [field])
        
        for path in paths:
            if path in data:
                return data[path]
        
        return None
    
    def _compare_field_values(self, field_sources: Dict[DataSource, Any]) -> Tuple[bool, float, List[str]]:
        """Compara valores de un campo entre diferentes fuentes."""
        values = list(field_sources.values())
        sources = list(field_sources.keys())
        
        discrepancies = []
        
        # Para strings, usar similarity ratio
        if all(isinstance(v, str) for v in values):
            similarity_threshold = 0.8
            
            for i in range(len(values)):
                for j in range(i + 1, len(values)):
                    similarity = difflib.SequenceMatcher(None, values[i].lower(), values[j].lower()).ratio()
                    
                    if similarity < similarity_threshold:
                        discrepancies.append(
                            f"{sources[i].value}: '{values[i]}' vs {sources[j].value}: '{values[j]}' "
                            f"(similarity: {similarity:.2f})"
                        )
            
            is_consistent = len(discrepancies) == 0
            confidence = 1.0 - (len(discrepancies) / max(len(values) * (len(values) - 1) / 2, 1))
        
        # Para listas (skills, etc.)
        elif all(isinstance(v, list) for v in values):
            # Comparar intersección de listas
            all_items = set()
            for v in values:
                all_items.update(item.lower().strip() for item in v)
            
            common_items = set(values[0])
            for v in values[1:]:
                common_items.intersection_update(set(item.lower().strip() for item in v))
            
            if all_items:
                consistency_ratio = len(common_items) / len(all_items)
                is_consistent = consistency_ratio > 0.5
                confidence = consistency_ratio
                
                if not is_consistent:
                    unique_items = {}
                    for i, v in enumerate(values):
                        unique = set(v) - common_items
                        if unique:
                            unique_items[sources[i].value] = list(unique)
                    
                    discrepancies = [f"{source}: unique items {items}" 
                                   for source, items in unique_items.items()]
            else:
                is_consistent = True
                confidence = 1.0
        
        else:
            # Comparación directa para otros tipos
            unique_values = set(str(v) for v in values)
            is_consistent = len(unique_values) == 1
            confidence = 1.0 if is_consistent else 0.0
            
            if not is_consistent:
                discrepancies = [f"{source.value}: {value}" 
                               for source, value in field_sources.items()]
        
        return is_consistent, confidence, discrepancies
    
    async def _perform_external_verification(self, candidate_id: str, 
                                           data_sources: Dict[DataSource, Dict[str, Any]]) -> List[InconsistencyFinding]:
        """Realiza verificación externa con bases de datos públicas."""
        inconsistencies = []
        
        try:
            # Verificación de empresa (simplificado)
            if DataSource.CV_DOCUMENT in data_sources:
                cv_data = data_sources[DataSource.CV_DOCUMENT]
                experiences = cv_data.get('work_experience', [])
                
                for experience in experiences:
                    company = experience.get('company', '')
                    if company:
                        is_valid = await self._verify_company_existence(company)
                        if not is_valid:
                            inconsistency = InconsistencyFinding(
                                id=str(uuid.uuid4()),
                                inconsistency_type=InconsistencyType.COMPANY_VERIFICATION,
                                severity=0.8,
                                confidence=0.7,
                                description=f"Company verification failed: {company}",
                                evidence={
                                    'company_name': company,
                                    'verification_method': 'external_database'
                                },
                                sources=[DataSource.CV_DOCUMENT],
                                recommendations=[
                                    "Verify company name spelling and legal status",
                                    "Request employment verification letter",
                                    "Check if company has changed names or been acquired"
                                ]
                            )
                            inconsistencies.append(inconsistency)
            
            # Verificación educativa
            if DataSource.CV_DOCUMENT in data_sources:
                cv_data = data_sources[DataSource.CV_DOCUMENT]
                education = cv_data.get('education', [])
                
                for edu in education:
                    institution = edu.get('institution', '')
                    degree = edu.get('degree', '')
                    
                    if institution and degree:
                        is_valid = await self._verify_educational_credentials(institution, degree)
                        if not is_valid:
                            inconsistency = InconsistencyFinding(
                                id=str(uuid.uuid4()),
                                inconsistency_type=InconsistencyType.EDUCATION_MISMATCH,
                                severity=0.9,
                                confidence=0.8,
                                description=f"Educational credential verification failed: {degree} from {institution}",
                                evidence={
                                    'institution': institution,
                                    'degree': degree,
                                    'verification_method': 'educational_database'
                                },
                                sources=[DataSource.CV_DOCUMENT],
                                recommendations=[
                                    "Request official transcripts",
                                    "Verify institution accreditation",
                                    "Check degree title accuracy"
                                ]
                            )
                            inconsistencies.append(inconsistency)
        
        except Exception as e:
            logger.error(f"Error in external verification: {str(e)}")
        
        return inconsistencies
    
    async def _verify_company_existence(self, company_name: str) -> bool:
        """Verifica existencia de empresa en bases de datos externas."""
        try:
            # En producción, esto se integraría con APIs como:
            # - LinkedIn Company API
            # - Clearbit
            # - OpenCorporates
            # - Registros mercantiles
            
            # Simulación simplificada
            known_companies = [
                'google', 'microsoft', 'amazon', 'apple', 'facebook', 'meta',
                'netflix', 'uber', 'airbnb', 'spotify', 'tesla', 'nvidia'
            ]
            
            return any(known in company_name.lower() for known in known_companies)
            
        except Exception as e:
            logger.error(f"Error verifying company {company_name}: {str(e)}")
            return True  # Por defecto asumir válido si hay error
    
    async def _verify_educational_credentials(self, institution: str, degree: str) -> bool:
        """Verifica credenciales educativas."""
        try:
            # En producción, esto se integraría con:
            # - National Student Clearinghouse
            # - Bases de datos de universidades
            # - APIs de verificación académica
            
            # Simulación simplificada
            known_institutions = [
                'harvard', 'mit', 'stanford', 'berkeley', 'caltech',
                'princeton', 'yale', 'columbia', 'penn', 'chicago'
            ]
            
            return any(known in institution.lower() for known in known_institutions)
            
        except Exception as e:
            logger.error(f"Error verifying education {institution} - {degree}: {str(e)}")
            return True
    
    def _calculate_veracity_score(self, inconsistencies: List[InconsistencyFinding], 
                                 confidence_metrics: Dict[str, float]) -> float:
        """Calcula score general de veracidad."""
        if not inconsistencies:
            return 1.0
        
        # Penalty por cada inconsistencia, ponderado por severidad y confianza
        total_penalty = 0.0
        max_penalty = 0.0
        
        for inconsistency in inconsistencies:
            penalty = inconsistency.severity * inconsistency.confidence
            
            # Peso adicional por tipo de inconsistencia
            type_weights = {
                InconsistencyType.DATE_OVERLAP: 0.8,
                InconsistencyType.SALARY_INFLATION: 0.6,
                InconsistencyType.COMPANY_VERIFICATION: 0.9,
                InconsistencyType.EDUCATION_MISMATCH: 0.9,
                InconsistencyType.LINGUISTIC_PATTERN: 0.4,
                InconsistencyType.REFERENCE_MISMATCH: 0.7
            }
            
            weight = type_weights.get(inconsistency.inconsistency_type, 0.5)
            weighted_penalty = penalty * weight
            
            total_penalty += weighted_penalty
            max_penalty += weight
        
        # Normalizar penalty
        if max_penalty > 0:
            penalty_ratio = min(total_penalty / max_penalty, 1.0)
        else:
            penalty_ratio = 0.0
        
        # Score base menos penalty
        base_score = 1.0
        final_score = max(base_score - penalty_ratio, 0.0)
        
        return final_score
    
    def _determine_veracity_level(self, score: float) -> VeracityLevel:
        """Determina nivel de veracidad basado en score."""
        if score >= 0.9:
            return VeracityLevel.TRUTHFUL
        elif score >= 0.7:
            return VeracityLevel.QUESTIONABLE
        elif score >= 0.5:
            return VeracityLevel.SUSPICIOUS
        elif score >= 0.3:
            return VeracityLevel.DECEPTIVE
        else:
            return VeracityLevel.FABRICATED
    
    def _identify_risk_factors(self, inconsistencies: List[InconsistencyFinding]) -> List[str]:
        """Identifica factores de riesgo principales."""
        risk_factors = []
        
        # Agrupar por tipo de inconsistencia
        inconsistency_counts = defaultdict(int)
        for inconsistency in inconsistencies:
            inconsistency_counts[inconsistency.inconsistency_type] += 1
        
        # Evaluar riesgos
        if inconsistency_counts[InconsistencyType.DATE_OVERLAP] > 0:
            risk_factors.append("Employment timeline conflicts")
        
        if inconsistency_counts[InconsistencyType.SALARY_INFLATION] > 0:
            risk_factors.append("Potential salary misrepresentation")
        
        if inconsistency_counts[InconsistencyType.COMPANY_VERIFICATION] > 0:
            risk_factors.append("Unverified employment claims")
        
        if inconsistency_counts[InconsistencyType.EDUCATION_MISMATCH] > 0:
            risk_factors.append("Educational credential concerns")
        
        if inconsistency_counts[InconsistencyType.LINGUISTIC_PATTERN] > 1:
            risk_factors.append("Deceptive communication patterns")
        
        high_severity_inconsistencies = [i for i in inconsistencies if i.severity > 0.8]
        if len(high_severity_inconsistencies) > 2:
            risk_factors.append("Multiple high-severity inconsistencies")
        
        return risk_factors
    
    def get_veracity_profile(self, candidate_id: str) -> Optional[VeracityProfile]:
        """Obtiene perfil de veracidad de un candidato."""
        return self.veracity_profiles.get(candidate_id)
    
    def generate_veracity_report(self, candidate_id: str) -> Dict[str, Any]:
        """Genera reporte detallado de veracidad."""
        profile = self.veracity_profiles.get(candidate_id)
        if not profile:
            return {'error': 'Veracity profile not found'}
        
        # Agrupar inconsistencias por tipo
        inconsistencies_by_type = defaultdict(list)
        for inconsistency in profile.inconsistencies:
            inconsistencies_by_type[inconsistency.inconsistency_type.value].append({
                'id': inconsistency.id,
                'severity': inconsistency.severity,
                'confidence': inconsistency.confidence,
                'description': inconsistency.description,
                'recommendations': inconsistency.recommendations
            })
        
        return {
            'candidate_id': candidate_id,
            'overall_score': profile.overall_score,
            'veracity_level': profile.veracity_level.value,
            'risk_factors': profile.risk_factors,
            'inconsistencies_summary': {
                'total_count': len(profile.inconsistencies),
                'by_type': dict(inconsistencies_by_type),
                'high_severity_count': len([i for i in profile.inconsistencies if i.severity > 0.8])
            },
            'verification_sources': [source.value for source in profile.verification_sources],
            'confidence_metrics': profile.confidence_metrics,
            'analysis_date': profile.last_analysis.isoformat(),
            'recommendations': self._generate_verification_recommendations(profile)
        }
    
    def _generate_verification_recommendations(self, profile: VeracityProfile) -> List[str]:
        """Genera recomendaciones de verificación basadas en el perfil."""
        recommendations = []
        
        if profile.veracity_level in [VeracityLevel.SUSPICIOUS, VeracityLevel.DECEPTIVE, VeracityLevel.FABRICATED]:
            recommendations.append("Conduct thorough background check before proceeding")
            recommendations.append("Require additional documentation for all claims")
            recommendations.append("Consider involving legal team for verification")
        
        if profile.veracity_level == VeracityLevel.QUESTIONABLE:
            recommendations.append("Verify key information with additional sources")
            recommendations.append("Conduct follow-up interviews with specific probing questions")
        
        # Recomendaciones específicas por tipo de inconsistencia
        inconsistency_types = {i.inconsistency_type for i in profile.inconsistencies}
        
        if InconsistencyType.DATE_OVERLAP in inconsistency_types:
            recommendations.append("Request official employment letters with exact dates")
        
        if InconsistencyType.EDUCATION_MISMATCH in inconsistency_types:
            recommendations.append("Require official transcripts from educational institutions")
        
        if InconsistencyType.COMPANY_VERIFICATION in inconsistency_types:
            recommendations.append("Contact HR departments directly for employment verification")
        
        return recommendations
    
    async def batch_analyze_candidates(self, candidates_data: List[Dict[str, Any]]) -> Dict[str, VeracityProfile]:
        """Analiza múltiples candidatos en lote."""
        results = {}
        
        for candidate_data in candidates_data:
            candidate_id = candidate_data['candidate_id']
            data_sources = candidate_data['data_sources']
            
            try:
                profile = await self.analyze_candidate_veracity(candidate_id, data_sources)
                results[candidate_id] = profile
            except Exception as e:
                logger.error(f"Error analyzing candidate {candidate_id}: {str(e)}")
        
        return results
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema TruthSense."""
        return {
            **self.metrics,
            'total_profiles': len(self.veracity_profiles),
            'veracity_distribution': self._get_veracity_distribution(),
            'avg_inconsistencies_per_profile': (
                sum(len(p.inconsistencies) for p in self.veracity_profiles.values()) / 
                len(self.veracity_profiles) if self.veracity_profiles else 0
            )
        }
    
    def _get_veracity_distribution(self) -> Dict[str, int]:
        """Obtiene distribución de niveles de veracidad."""
        distribution = defaultdict(int)
        for profile in self.veracity_profiles.values():
            distribution[profile.veracity_level.value] += 1
        return dict(distribution)