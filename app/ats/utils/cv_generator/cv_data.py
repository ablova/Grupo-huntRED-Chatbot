# /home/pablo/app/com/utils/cv_generator/cv_data.py
#
# Estructura de datos y utilidades para CV.

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ContactInfo:
    """Contact information for the candidate."""
    email: str
    phone: str
    linkedin: Optional[str] = None
    whatsapp: Optional[str] = None


@dataclass
class Experience:
    """Work experience entry."""
    company: str
    position: str
    start_date: str
    description: str
    end_date: Optional[str] = None
    achievements: Optional[List[str]] = None
    ml_analysis: Optional[Dict] = None  # Análisis ML de la experiencia


@dataclass
class Education:
    """Education entry."""
    institution: str
    degree: str
    field_of_study: str
    start_date: str
    end_date: Optional[str] = None
    description: Optional[str] = None
    grade: Optional[str] = None
    ml_analysis: Optional[Dict] = None  # Análisis ML de la educación


@dataclass
class Language:
    """Language proficiency."""
    language: str
    level: str
    certificate: Optional[str] = None
    ml_analysis: Optional[Dict] = None  # Análisis ML del idioma


@dataclass
class Skill:
    """Professional skill."""
    name: str
    proficiency: str
    years_experience: Optional[int] = None
    certification: Optional[str] = None
    ml_analysis: Optional[Dict] = None  # Análisis ML de la habilidad
    ml_relevance: Optional[float] = None  # Relevancia según ML
    ml_growth_potential: Optional[float] = None  # Potencial de crecimiento


@dataclass
class SkillAssessment:
    """Evaluación de una habilidad específica."""
    skill: str
    score: float
    assessment_date: datetime
    assessor: Optional[str] = None
    is_verified: bool = False
    comments: Optional[str] = None


@dataclass
class PersonalityTest:
    """Personality test results."""
    test_name: str
    date: datetime
    results: Dict[str, float]
    interpretation: str
    ml_insights: Optional[Dict] = None  # Insights adicionales del ML


@dataclass
class BackgroundCheck:
    """Background check results."""
    check_type: str
    date: datetime
    status: str
    findings: Dict[str, str]
    ml_risk_assessment: Optional[Dict] = None  # Evaluación de riesgo ML


@dataclass
class CVData:
    """Complete CV data structure."""
    name: str
    title: str
    contact_info: ContactInfo
    summary: str
    experience: List[Experience]
    education: List[Education]
    skills: List[Skill]
    languages: List[Language]
    skill_assessments: List[SkillAssessment]  # Nueva lista de evaluaciones
    business_unit: str
    business_unit_logo: str
    personality_test: Optional[PersonalityTest] = None
    background_check: Optional[BackgroundCheck] = None
    language: str = 'es'
    birth_year: Optional[int] = None
    reference_code: Optional[str] = None
    ml_profile_analysis: Optional[Dict] = None  # Análisis completo del perfil
    ml_market_fit: Optional[float] = None  # Ajuste al mercado
    ml_growth_potential: Optional[float] = None  # Potencial de crecimiento
    ml_recommendations: Optional[List[str]] = None  # Recomendaciones ML
    ml_analysis_date: Optional[datetime] = None  # Fecha del análisis ML
    cv_creation_date: Optional[datetime] = None  # Fecha de creación del CV
    ml_disclaimer: str = ("Este análisis es meramente informativo y se basa en datos históricos y tendencias actuales."
                         "Los valores son estimativos y pueden variar según el contexto del mercado.")

    def get_translated_data(self) -> Dict:
        """
        Get the CV data translated to the specified language.
        
        Returns:
            Dictionary with translated data
        """
        translations = {
            'es': {
                'title': 'Resumen Profesional',
                'experience': 'Experiencia Laboral',
                'education': 'Educación',
                'skills': 'Habilidades',
                'languages': 'Idiomas',
                'certifications': 'Certificaciones',
                'achievements': 'Logros',
                'grade': 'Calificación',
                'personality': 'Análisis de Personalidad',
                'background': 'Verificación de Antecedentes'
            },
            'en': {
                'title': 'Professional Summary',
                'experience': 'Work Experience',
                'education': 'Education',
                'skills': 'Skills',
                'languages': 'Languages',
                'certifications': 'Certifications',
                'achievements': 'Achievements',
                'grade': 'Grade',
                'personality': 'Personality Analysis',
                'background': 'Background Check'
            }
        }
        
        data = self.__dict__.copy()
        data['translations'] = translations[self.language]
        return data

    def get_blind_identifier(self) -> str:
        """
        Generate a blind identifier for the candidate.
        
        Returns:
            String in format: "Nombre - Ref: XXXXSX - Iniciales Apellidos"
        """
        # Get initials from last names
        last_names = self.name.split()[1:]  # Get all words except first name
        initials = ''.join([name[0] for name in last_names])
        
        # Generate reference code if not provided
        if not self.reference_code:
            import random
            import string
            self.reference_code = ''.join(random.choices(string.ascii_uppercase, k=4)) + str(random.randint(1000, 9999))
        
        return f"{self.name.split()[0]} - Ref: {self.reference_code} - {initials} ({self.birth_year})"

    def get_personality_chart(self) -> str:
        """
        Generate a visual chart for personality test results.
        
        Returns:
            HTML string with the personality chart
        """
        if not self.personality_test:
            return ""
            
        metrics = self.personality_test.results
        max_value = max(metrics.values())
        
        chart = "<div class='personality-chart'>"
        
        for metric, value in metrics.items():
            percentage = (value / max_value) * 100
            chart += f"""
            <div class='metric-bar'>
                <div class='metric-label'>{metric}</div>
                <div class='metric-value'>{value}%</div>
                <div class='bar-container'>
                    <div class='bar' style='width: {percentage}%'>
                        <div class='bar-label'>{value}%</div>
                    </div>
                </div>
            </div>
            """
            
        chart += "</div>"
        return chart

    def get_verification_seal(self) -> str:
        """
        Get the verification seal for background check.
        
        Returns:
            HTML string with the verification seal
        """
        if not self.background_check:
            return ""
            
        provider_logos = {
            'BlackTrust': 'https://blacktrust.com/logo.png',
            'VeriCheck': 'https://vericheck.com/logo.png',
            'SafeCheck': 'https://safecheck.com/logo.png'
        }
        
        provider = self.background_check.check_type
        logo_url = provider_logos.get(provider, '')
        
        return f"""
        <div class='verification-seal'>
            <img src='{logo_url}' alt='{provider} Verification' class='seal-logo'>
            <div class='seal-status'>
                <div class='status-label'>Estado:</div>
                <div class='status-value {self.background_check.status.lower()}'>
                    {self.background_check.status}
                </div>
            </div>
            <div class='seal-date'>
                Verificado el: {self.background_check.date.strftime('%d/%m/%Y')}
            </div>
        </div>
        """
