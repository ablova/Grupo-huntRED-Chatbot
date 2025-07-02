"""
AURA - SocialVerify™ Social Verifier
Verificador principal de autenticidad social para SocialVerify™.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
import re
import json

logger = logging.getLogger(__name__)

class SocialPlatform(Enum):
    """Plataformas sociales soportadas"""
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    GITHUB = "github"
    MEDIUM = "medium"
    YOUTUBE = "youtube"

class AuthenticityLevel(Enum):
    """Niveles de autenticidad"""
    VERIFIED = "verified"
    LIKELY_AUTHENTIC = "likely_authentic"
    UNCERTAIN = "uncertain"
    SUSPICIOUS = "suspicious"
    FAKE = "fake"

@dataclass
class SocialProfile:
    """Perfil social verificado"""
    platform: SocialPlatform
    username: str
    authenticity_score: float
    authenticity_level: AuthenticityLevel
    verification_date: datetime
    profile_metrics: Dict[str, Any]
    activity_indicators: Dict[str, Any]
    risk_factors: List[str]

@dataclass
class SocialVerification:
    """Resultado de verificación social"""
    overall_authenticity_score: float
    authenticity_level: AuthenticityLevel
    confidence: float
    verified_profiles: List[SocialProfile]
    network_health: float
    influence_score: float
    risk_assessment: Dict[str, Any]
    recommendations: List[str]

class SocialVerifier:
    """
    Verificador principal de autenticidad social para SocialVerify™.
    
    Características:
    - Verificación multi-plataforma
    - Análisis de autenticidad
    - Evaluación de actividad
    - Detección de perfiles falsos
    - Análisis de métricas sociales
    """
    
    def __init__(self):
        """Inicializa el verificador social"""
        self.platform_verifiers = {
            SocialPlatform.LINKEDIN: self._verify_linkedin_profile,
            SocialPlatform.TWITTER: self._verify_twitter_profile,
            SocialPlatform.FACEBOOK: self._verify_facebook_profile,
            SocialPlatform.INSTAGRAM: self._verify_instagram_profile,
            SocialPlatform.GITHUB: self._verify_github_profile,
            SocialPlatform.MEDIUM: self._verify_medium_profile,
            SocialPlatform.YOUTUBE: self._verify_youtube_profile
        }
        
        # Patrones de detección de perfiles falsos
        self.fake_profile_indicators = {
            "recent_creation": 0.3,  # Peso para perfiles recientes
            "low_activity": 0.4,     # Peso para baja actividad
            "generic_content": 0.2,  # Peso para contenido genérico
            "suspicious_connections": 0.3,  # Peso para conexiones sospechosas
            "inconsistent_info": 0.4  # Peso para información inconsistente
        }
        
        logger.info("SocialVerify™ Social Verifier inicializado")
    
    async def verify_social_presence_comprehensive(
        self,
        person_data: Dict[str, Any],
        target_platforms: Optional[List[SocialPlatform]] = None,
        business_context: Optional[Dict[str, Any]] = None
    ) -> SocialVerification:
        """
        Verificación comprehensiva de presencia social.
        
        Args:
            person_data: Datos de la persona
            target_platforms: Plataformas específicas a verificar
            business_context: Contexto de negocio
            
        Returns:
            SocialVerification con análisis completo
        """
        try:
            verified_profiles = []
            all_risk_factors = []
            
            # Determinar plataformas a verificar
            platforms_to_verify = target_platforms or list(SocialPlatform)
            
            # Verificar cada plataforma
            for platform in platforms_to_verify:
                try:
                    profile = await self.platform_verifiers[platform](
                        person_data, business_context
                    )
                    if profile:
                        verified_profiles.append(profile)
                        all_risk_factors.extend(profile.risk_factors)
                except Exception as e:
                    logger.error(f"Error verificando {platform.value}: {str(e)}")
            
            # Calcular score general de autenticidad
            overall_score = self._calculate_overall_authenticity_score(verified_profiles)
            
            # Determinar nivel de autenticidad
            authenticity_level = self._determine_authenticity_level(overall_score)
            
            # Calcular confianza
            confidence = self._calculate_verification_confidence(verified_profiles)
            
            # Calcular salud de red
            network_health = self._calculate_network_health(verified_profiles)
            
            # Calcular score de influencia
            influence_score = self._calculate_influence_score(verified_profiles)
            
            # Evaluar riesgos
            risk_assessment = self._assess_social_risks(verified_profiles, all_risk_factors)
            
            # Generar recomendaciones
            recommendations = self._generate_social_recommendations(
                verified_profiles, overall_score, risk_assessment
            )
            
            return SocialVerification(
                overall_authenticity_score=overall_score,
                authenticity_level=authenticity_level,
                confidence=confidence,
                verified_profiles=verified_profiles,
                network_health=network_health,
                influence_score=influence_score,
                risk_assessment=risk_assessment,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error en verificación social: {str(e)}")
            raise
    
    async def _verify_linkedin_profile(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Optional[SocialProfile]:
        """Verifica perfil de LinkedIn"""
        try:
            # Simular verificación de LinkedIn
            authenticity_score = np.random.uniform(0.7, 0.95)
            risk_factors = []
            
            # Verificar consistencia con datos personales
            if "name" in person_data and "linkedin" in person_data:
                linkedin_data = person_data["linkedin"]
                if isinstance(linkedin_data, dict):
                    # Verificar nombre
                    if "name" in linkedin_data:
                        name_consistency = self._check_name_consistency(
                            person_data["name"], linkedin_data["name"]
                        )
                        if not name_consistency:
                            risk_factors.append("Inconsistencia en nombre")
                            authenticity_score -= 0.1
                    
                    # Verificar experiencia
                    if "experience" in linkedin_data and "experience" in person_data:
                        exp_consistency = self._check_experience_consistency(
                            person_data["experience"], linkedin_data.get("experience", [])
                        )
                        if not exp_consistency:
                            risk_factors.append("Inconsistencia en experiencia")
                            authenticity_score -= 0.15
            
            # Calcular métricas del perfil
            profile_metrics = {
                "connections": np.random.randint(100, 2000),
                "endorsements": np.random.randint(10, 500),
                "posts": np.random.randint(5, 100),
                "profile_completeness": np.random.uniform(0.7, 1.0)
            }
            
            # Indicadores de actividad
            activity_indicators = {
                "last_activity": datetime.now() - timedelta(days=np.random.randint(1, 30)),
                "posting_frequency": np.random.uniform(0.1, 2.0),  # posts por semana
                "engagement_rate": np.random.uniform(0.01, 0.1)
            }
            
            # Detectar factores de riesgo
            if profile_metrics["connections"] < 200:
                risk_factors.append("Pocas conexiones")
            
            if profile_metrics["profile_completeness"] < 0.8:
                risk_factors.append("Perfil incompleto")
            
            if activity_indicators["posting_frequency"] < 0.2:
                risk_factors.append("Baja actividad")
            
            return SocialProfile(
                platform=SocialPlatform.LINKEDIN,
                username=person_data.get("linkedin", {}).get("username", "unknown"),
                authenticity_score=max(0.0, authenticity_score),
                authenticity_level=self._determine_authenticity_level(authenticity_score),
                verification_date=datetime.now(),
                profile_metrics=profile_metrics,
                activity_indicators=activity_indicators,
                risk_factors=risk_factors
            )
            
        except Exception as e:
            logger.error(f"Error verificando LinkedIn: {str(e)}")
            return None
    
    async def _verify_twitter_profile(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Optional[SocialProfile]:
        """Verifica perfil de Twitter"""
        try:
            # Simular verificación de Twitter
            authenticity_score = np.random.uniform(0.6, 0.9)
            risk_factors = []
            
            # Métricas del perfil
            profile_metrics = {
                "followers": np.random.randint(50, 5000),
                "following": np.random.randint(20, 1000),
                "tweets": np.random.randint(10, 500),
                "verified": np.random.choice([True, False], p=[0.1, 0.9])
            }
            
            # Indicadores de actividad
            activity_indicators = {
                "last_tweet": datetime.now() - timedelta(days=np.random.randint(1, 60)),
                "tweet_frequency": np.random.uniform(0.1, 5.0),  # tweets por día
                "engagement_rate": np.random.uniform(0.001, 0.05)
            }
            
            # Detectar factores de riesgo
            if profile_metrics["followers"] < 100:
                risk_factors.append("Pocos seguidores")
            
            if activity_indicators["tweet_frequency"] < 0.5:
                risk_factors.append("Baja actividad")
            
            if not profile_metrics["verified"]:
                risk_factors.append("Cuenta no verificada")
            
            return SocialProfile(
                platform=SocialPlatform.TWITTER,
                username=person_data.get("twitter", {}).get("username", "unknown"),
                authenticity_score=max(0.0, authenticity_score),
                authenticity_level=self._determine_authenticity_level(authenticity_score),
                verification_date=datetime.now(),
                profile_metrics=profile_metrics,
                activity_indicators=activity_indicators,
                risk_factors=risk_factors
            )
            
        except Exception as e:
            logger.error(f"Error verificando Twitter: {str(e)}")
            return None
    
    async def _verify_facebook_profile(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Optional[SocialProfile]:
        """Verifica perfil de Facebook"""
        try:
            # Simular verificación de Facebook
            authenticity_score = np.random.uniform(0.5, 0.85)
            risk_factors = []
            
            # Métricas del perfil
            profile_metrics = {
                "friends": np.random.randint(100, 2000),
                "posts": np.random.randint(5, 200),
                "photos": np.random.randint(10, 500),
                "account_age": np.random.randint(365, 3650)  # días
            }
            
            # Indicadores de actividad
            activity_indicators = {
                "last_post": datetime.now() - timedelta(days=np.random.randint(1, 90)),
                "posting_frequency": np.random.uniform(0.05, 1.0),
                "privacy_level": np.random.choice(["public", "friends", "private"])
            }
            
            # Detectar factores de riesgo
            if profile_metrics["friends"] < 150:
                risk_factors.append("Pocos amigos")
            
            if activity_indicators["privacy_level"] == "private":
                risk_factors.append("Perfil privado")
            
            return SocialProfile(
                platform=SocialPlatform.FACEBOOK,
                username=person_data.get("facebook", {}).get("username", "unknown"),
                authenticity_score=max(0.0, authenticity_score),
                authenticity_level=self._determine_authenticity_level(authenticity_score),
                verification_date=datetime.now(),
                profile_metrics=profile_metrics,
                activity_indicators=activity_indicators,
                risk_factors=risk_factors
            )
            
        except Exception as e:
            logger.error(f"Error verificando Facebook: {str(e)}")
            return None
    
    async def _verify_instagram_profile(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Optional[SocialProfile]:
        """Verifica perfil de Instagram"""
        try:
            # Simular verificación de Instagram
            authenticity_score = np.random.uniform(0.6, 0.9)
            risk_factors = []
            
            # Métricas del perfil
            profile_metrics = {
                "followers": np.random.randint(50, 3000),
                "following": np.random.randint(20, 800),
                "posts": np.random.randint(5, 200),
                "verified": np.random.choice([True, False], p=[0.05, 0.95])
            }
            
            # Indicadores de actividad
            activity_indicators = {
                "last_post": datetime.now() - timedelta(days=np.random.randint(1, 45)),
                "posting_frequency": np.random.uniform(0.1, 2.0),
                "engagement_rate": np.random.uniform(0.01, 0.08)
            }
            
            # Detectar factores de riesgo
            if profile_metrics["followers"] < 100:
                risk_factors.append("Pocos seguidores")
            
            if not profile_metrics["verified"]:
                risk_factors.append("Cuenta no verificada")
            
            return SocialProfile(
                platform=SocialPlatform.INSTAGRAM,
                username=person_data.get("instagram", {}).get("username", "unknown"),
                authenticity_score=max(0.0, authenticity_score),
                authenticity_level=self._determine_authenticity_level(authenticity_score),
                verification_date=datetime.now(),
                profile_metrics=profile_metrics,
                activity_indicators=activity_indicators,
                risk_factors=risk_factors
            )
            
        except Exception as e:
            logger.error(f"Error verificando Instagram: {str(e)}")
            return None
    
    async def _verify_github_profile(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Optional[SocialProfile]:
        """Verifica perfil de GitHub"""
        try:
            # Simular verificación de GitHub
            authenticity_score = np.random.uniform(0.7, 0.95)
            risk_factors = []
            
            # Métricas del perfil
            profile_metrics = {
                "repositories": np.random.randint(1, 50),
                "followers": np.random.randint(5, 500),
                "following": np.random.randint(5, 200),
                "stars": np.random.randint(0, 100),
                "contributions": np.random.randint(10, 1000)
            }
            
            # Indicadores de actividad
            activity_indicators = {
                "last_commit": datetime.now() - timedelta(days=np.random.randint(1, 30)),
                "commit_frequency": np.random.uniform(0.1, 3.0),
                "languages": np.random.randint(1, 8)
            }
            
            # Detectar factores de riesgo
            if profile_metrics["repositories"] < 3:
                risk_factors.append("Pocos repositorios")
            
            if profile_metrics["contributions"] < 50:
                risk_factors.append("Pocas contribuciones")
            
            return SocialProfile(
                platform=SocialPlatform.GITHUB,
                username=person_data.get("github", {}).get("username", "unknown"),
                authenticity_score=max(0.0, authenticity_score),
                authenticity_level=self._determine_authenticity_level(authenticity_score),
                verification_date=datetime.now(),
                profile_metrics=profile_metrics,
                activity_indicators=activity_indicators,
                risk_factors=risk_factors
            )
            
        except Exception as e:
            logger.error(f"Error verificando GitHub: {str(e)}")
            return None
    
    async def _verify_medium_profile(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Optional[SocialProfile]:
        """Verifica perfil de Medium"""
        try:
            # Simular verificación de Medium
            authenticity_score = np.random.uniform(0.6, 0.9)
            risk_factors = []
            
            # Métricas del perfil
            profile_metrics = {
                "articles": np.random.randint(1, 30),
                "followers": np.random.randint(10, 1000),
                "following": np.random.randint(5, 200),
                "claps": np.random.randint(10, 5000)
            }
            
            # Indicadores de actividad
            activity_indicators = {
                "last_article": datetime.now() - timedelta(days=np.random.randint(1, 90)),
                "writing_frequency": np.random.uniform(0.05, 1.0),
                "avg_claps": np.random.uniform(10, 200)
            }
            
            # Detectar factores de riesgo
            if profile_metrics["articles"] < 2:
                risk_factors.append("Pocos artículos")
            
            if activity_indicators["avg_claps"] < 20:
                risk_factors.append("Bajo engagement")
            
            return SocialProfile(
                platform=SocialPlatform.MEDIUM,
                username=person_data.get("medium", {}).get("username", "unknown"),
                authenticity_score=max(0.0, authenticity_score),
                authenticity_level=self._determine_authenticity_level(authenticity_score),
                verification_date=datetime.now(),
                profile_metrics=profile_metrics,
                activity_indicators=activity_indicators,
                risk_factors=risk_factors
            )
            
        except Exception as e:
            logger.error(f"Error verificando Medium: {str(e)}")
            return None
    
    async def _verify_youtube_profile(
        self,
        person_data: Dict[str, Any],
        business_context: Optional[Dict[str, Any]]
    ) -> Optional[SocialProfile]:
        """Verifica perfil de YouTube"""
        try:
            # Simular verificación de YouTube
            authenticity_score = np.random.uniform(0.5, 0.85)
            risk_factors = []
            
            # Métricas del perfil
            profile_metrics = {
                "subscribers": np.random.randint(10, 10000),
                "videos": np.random.randint(1, 100),
                "views": np.random.randint(100, 100000),
                "verified": np.random.choice([True, False], p=[0.05, 0.95])
            }
            
            # Indicadores de actividad
            activity_indicators = {
                "last_video": datetime.now() - timedelta(days=np.random.randint(1, 120)),
                "upload_frequency": np.random.uniform(0.01, 0.5),
                "avg_views": np.random.uniform(100, 5000)
            }
            
            # Detectar factores de riesgo
            if profile_metrics["subscribers"] < 100:
                risk_factors.append("Pocos suscriptores")
            
            if not profile_metrics["verified"]:
                risk_factors.append("Canal no verificado")
            
            return SocialProfile(
                platform=SocialPlatform.YOUTUBE,
                username=person_data.get("youtube", {}).get("username", "unknown"),
                authenticity_score=max(0.0, authenticity_score),
                authenticity_level=self._determine_authenticity_level(authenticity_score),
                verification_date=datetime.now(),
                profile_metrics=profile_metrics,
                activity_indicators=activity_indicators,
                risk_factors=risk_factors
            )
            
        except Exception as e:
            logger.error(f"Error verificando YouTube: {str(e)}")
            return None
    
    def _check_name_consistency(self, name1: str, name2: str) -> bool:
        """Verifica consistencia de nombres"""
        try:
            # Normalizar nombres
            name1_norm = re.sub(r'[^\w\s]', '', name1.lower()).strip()
            name2_norm = re.sub(r'[^\w\s]', '', name2.lower()).strip()
            
            # Verificar similitud
            return name1_norm == name2_norm or name1_norm in name2_norm or name2_norm in name1_norm
            
        except Exception as e:
            logger.error(f"Error verificando consistencia de nombres: {str(e)}")
            return False
    
    def _check_experience_consistency(
        self,
        experience1: List[Dict[str, Any]],
        experience2: List[Dict[str, Any]]
    ) -> bool:
        """Verifica consistencia de experiencia"""
        try:
            if not experience1 or not experience2:
                return True  # No hay datos para comparar
            
            # Extraer títulos de trabajo
            titles1 = [exp.get("title", "").lower() for exp in experience1]
            titles2 = [exp.get("title", "").lower() for exp in experience2]
            
            # Verificar si hay títulos comunes
            common_titles = set(titles1) & set(titles2)
            
            return len(common_titles) > 0
            
        except Exception as e:
            logger.error(f"Error verificando consistencia de experiencia: {str(e)}")
            return False
    
    def _calculate_overall_authenticity_score(self, profiles: List[SocialProfile]) -> float:
        """Calcula score general de autenticidad"""
        try:
            if not profiles:
                return 0.0
            
            # Ponderar por plataforma
            platform_weights = {
                SocialPlatform.LINKEDIN: 0.3,
                SocialPlatform.TWITTER: 0.2,
                SocialPlatform.FACEBOOK: 0.15,
                SocialPlatform.INSTAGRAM: 0.15,
                SocialPlatform.GITHUB: 0.1,
                SocialPlatform.MEDIUM: 0.05,
                SocialPlatform.YOUTUBE: 0.05
            }
            
            weighted_sum = 0.0
            total_weight = 0.0
            
            for profile in profiles:
                weight = platform_weights.get(profile.platform, 0.1)
                weighted_sum += profile.authenticity_score * weight
                total_weight += weight
            
            return weighted_sum / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculando score de autenticidad: {str(e)}")
            return 0.0
    
    def _determine_authenticity_level(self, score: float) -> AuthenticityLevel:
        """Determina nivel de autenticidad"""
        if score >= 0.85:
            return AuthenticityLevel.VERIFIED
        elif score >= 0.7:
            return AuthenticityLevel.LIKELY_AUTHENTIC
        elif score >= 0.5:
            return AuthenticityLevel.UNCERTAIN
        elif score >= 0.3:
            return AuthenticityLevel.SUSPICIOUS
        else:
            return AuthenticityLevel.FAKE
    
    def _calculate_verification_confidence(self, profiles: List[SocialProfile]) -> float:
        """Calcula confianza en la verificación"""
        try:
            if not profiles:
                return 0.0
            
            # Basado en número de perfiles verificados
            verified_count = len([p for p in profiles if p.authenticity_level in [
                AuthenticityLevel.VERIFIED, AuthenticityLevel.LIKELY_AUTHENTIC
            ]])
            
            confidence = verified_count / len(profiles)
            
            # Ajustar por calidad de perfiles
            avg_authenticity = np.mean([p.authenticity_score for p in profiles])
            confidence = (confidence + avg_authenticity) / 2
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"Error calculando confianza: {str(e)}")
            return 0.5
    
    def _calculate_network_health(self, profiles: List[SocialProfile]) -> float:
        """Calcula salud de la red social"""
        try:
            if not profiles:
                return 0.0
            
            health_scores = []
            
            for profile in profiles:
                # Calcular salud por perfil
                activity_score = min(1.0, profile.activity_indicators.get("posting_frequency", 0) / 2.0)
                engagement_score = min(1.0, profile.profile_metrics.get("followers", 0) / 1000.0)
                completeness_score = profile.profile_metrics.get("profile_completeness", 0.5)
                
                profile_health = (activity_score + engagement_score + completeness_score) / 3
                health_scores.append(profile_health)
            
            return np.mean(health_scores)
            
        except Exception as e:
            logger.error(f"Error calculando salud de red: {str(e)}")
            return 0.0
    
    def _calculate_influence_score(self, profiles: List[SocialProfile]) -> float:
        """Calcula score de influencia"""
        try:
            if not profiles:
                return 0.0
            
            influence_scores = []
            
            for profile in profiles:
                # Calcular influencia por plataforma
                if profile.platform == SocialPlatform.LINKEDIN:
                    influence = profile.profile_metrics.get("connections", 0) / 1000.0
                elif profile.platform == SocialPlatform.TWITTER:
                    influence = profile.profile_metrics.get("followers", 0) / 5000.0
                elif profile.platform == SocialPlatform.INSTAGRAM:
                    influence = profile.profile_metrics.get("followers", 0) / 3000.0
                else:
                    influence = 0.1  # Influencia base para otras plataformas
                
                influence_scores.append(min(1.0, influence))
            
            return np.mean(influence_scores)
            
        except Exception as e:
            logger.error(f"Error calculando score de influencia: {str(e)}")
            return 0.0
    
    def _assess_social_risks(
        self,
        profiles: List[SocialProfile],
        risk_factors: List[str]
    ) -> Dict[str, Any]:
        """Evalúa riesgos sociales"""
        try:
            risk_assessment = {
                "overall_risk_level": "low",
                "risk_factors": risk_factors,
                "suspicious_profiles": 0,
                "fake_profile_probability": 0.0,
                "reputation_risk": 0.0
            }
            
            # Contar perfiles sospechosos
            suspicious_count = len([p for p in profiles if p.authenticity_level in [
                AuthenticityLevel.SUSPICIOUS, AuthenticityLevel.FAKE
            ]])
            
            risk_assessment["suspicious_profiles"] = suspicious_count
            
            # Calcular probabilidad de perfil falso
            fake_probability = suspicious_count / len(profiles) if profiles else 0.0
            risk_assessment["fake_profile_probability"] = fake_probability
            
            # Evaluar riesgo de reputación
            if fake_probability > 0.5:
                risk_assessment["reputation_risk"] = 0.8
                risk_assessment["overall_risk_level"] = "high"
            elif fake_probability > 0.2:
                risk_assessment["reputation_risk"] = 0.5
                risk_assessment["overall_risk_level"] = "medium"
            else:
                risk_assessment["reputation_risk"] = 0.2
                risk_assessment["overall_risk_level"] = "low"
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Error evaluando riesgos sociales: {str(e)}")
            return {"error": str(e)}
    
    def _generate_social_recommendations(
        self,
        profiles: List[SocialProfile],
        overall_score: float,
        risk_assessment: Dict[str, Any]
    ) -> List[str]:
        """Genera recomendaciones sociales"""
        recommendations = []
        
        # Recomendaciones basadas en score general
        if overall_score < 0.6:
            recommendations.append("Verificar autenticidad de perfiles sociales")
        
        # Recomendaciones basadas en riesgos
        if risk_assessment.get("overall_risk_level") == "high":
            recommendations.append("Realizar verificación exhaustiva de identidad")
        
        if risk_assessment.get("suspicious_profiles", 0) > 2:
            recommendations.append("Investigar perfiles sospechosos")
        
        # Recomendaciones específicas por plataforma
        linkedin_profiles = [p for p in profiles if p.platform == SocialPlatform.LINKEDIN]
        if not linkedin_profiles:
            recommendations.append("Solicitar perfil de LinkedIn")
        
        # Recomendaciones de mejora
        if overall_score < 0.8:
            recommendations.append("Considerar verificación adicional de identidad")
        
        if not recommendations:
            recommendations.append("Presencia social verificada satisfactoriamente")
        
        return recommendations[:5]  # Máximo 5 recomendaciones

# Instancia global
social_verifier = SocialVerifier()
