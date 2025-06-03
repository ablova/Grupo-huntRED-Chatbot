# /home/pablo/app/com/chatbot/integrations/verification.py
#
# Módulo para manejar la verificación de identidad y análisis de riesgo.
# Integra servicios como INCODE y BlackTrust para verificar datos de candidatos.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

from django.conf import settings
from django.utils import timezone
from app.models import ApiConfig, BusinessUnit
import httpx
import json
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

COMUNICATION_CHOICES = [
    ('whatsapp', 'WhatsApp'),
    ('telegram', 'Telegram'),
    ('messenger', 'Messenger'),
    ('instagram', 'Instagram'),
    ('slack', 'Slack'),
    ('email', 'Email'),
    ('incode', 'INCODE Verification'),
    ('blacktrust', 'BlackTrust Verification'),
]

class VerificationService:
    def __init__(self, business_unit: str):
        self.business_unit = business_unit
        self.configs = self._load_configs()
        
    def _load_configs(self) -> Dict[str, ApiConfig]:
        """Carga las configuraciones de API para la unidad de negocio"""
        # Primero intenta cargar configuraciones específicas para la unidad de negocio
        specific_configs = {
            config.api_type: config
            for config in ApiConfig.objects.filter(
                business_unit__name=self.business_unit,
                enabled=True
            )
        }
        
        # Si no hay configuración específica, usa las globales
        if not specific_configs:
            global_configs = {
                config.api_type: config
                for config in ApiConfig.objects.filter(
                    business_unit__isnull=True,
                    enabled=True
                )
            }
            return global_configs
        
        return specific_configs
        
    async def verify_identity(self, user_id: str, verification_type: str) -> Dict:
        """Realiza la verificación de identidad usando el tipo especificado"""
        config = self.configs.get(verification_type)
        if not config:
            raise ValueError(f"No se encontró configuración para {verification_type}")
            
        if verification_type == 'incode':
            return await self._verify_with_incode(config, user_id)
        elif verification_type == 'blacktrust':
            return await self._verify_with_blacktrust(config, user_id)
        else:
            raise ValueError(f"Tipo de verificación no soportado: {verification_type}")
            
    async def _verify_with_incode(self, config: ApiConfig, user_id: str) -> Dict:
        """Realiza verificación con INCODE"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{config.additional_settings.get('base_url', 'https://api.incode.com')}/verify",
                    headers={
                        "Authorization": f"Bearer {config.api_key}",
                        "X-API-SECRET": config.api_secret
                    },
                    json={
                        "user_id": user_id,
                        "verification_types": config.additional_settings.get('verification_types', ['INE', 'ID', 'passport'])
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Validación adicional de resultados
                if not result.get('success'):
                    raise ValueError(f"Verificación fallida: {result.get('error', 'Error desconocido')}")
                
                return result
        except Exception as e:
            logger.error(f"Error en verificación INCODE: {str(e)}")
            raise
            
    async def _verify_with_blacktrust(self, config: ApiConfig, user_id: str) -> Dict:
        """Realiza verificación de antecedentes con BlackTrust"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{config.additional_settings.get('base_url', 'https://api.blacktrust.com')}/background-check",
                    headers={
                        "Authorization": f"Bearer {config.api_key}",
                        "X-API-SECRET": config.api_secret
                    },
                    json={
                        "user_id": user_id,
                        "check_types": config.additional_settings.get('background_check_types', ['criminal', 'credit', 'employment']),
                        "regions": config.additional_settings.get('regions', ['global', 'latam', 'usa'])
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Validación adicional de resultados
                if not result.get('success'):
                    raise ValueError(f"Verificación fallida: {result.get('error', 'Error desconocido')}")
                
                return result
        except Exception as e:
            logger.error(f"Error en verificación BlackTrust: {str(e)}")
            raise
            
    async def perform_verification(self, candidate_data: dict) -> Dict:
        """Realiza la verificación completa del candidato"""
        # 1. Análisis interno de riesgo
        risk_analysis = await self.perform_internal_analysis(candidate_data)
        
        # 2. Verificación de identidad con INCODE
        incode_result = None
        if risk_analysis['risk_score'] < 40:  # Solo si el riesgo es bajo
            incode_result = await self._verify_with_incode(
                config=self.configs['incode'],
                user_id=candidate_data['phone']
            )
        
        # 3. Verificación de antecedentes con BlackTrust
        blacktrust_result = None
        if risk_analysis['risk_score'] < 40 and incode_result and incode_result.get('success'):
            blacktrust_result = await self._verify_with_blacktrust(
                config=self.configs['blacktrust'],
                user_id=candidate_data['phone']
            )
        
        # 4. Consolidar resultados
        results = {
            'risk_analysis': risk_analysis,
            'incode_verification': incode_result,
            'blacktrust_verification': blacktrust_result,
            'overall_status': 'pending',
            'flags': [],
            'recommendations': []
        }
        
        # Determinar estado final
        if risk_analysis['risk_score'] >= 70:
            results['overall_status'] = 'high_risk'
            results['flags'].extend(risk_analysis['flags'])
            results['recommendations'].extend(risk_analysis['recommendations'])
        elif risk_analysis['risk_score'] >= 40:
            results['overall_status'] = 'medium_risk'
            results['flags'].extend(risk_analysis['flags'])
            results['recommendations'].extend(risk_analysis['recommendations'])
        else:
            if incode_result and incode_result.get('success'):
                if blacktrust_result and blacktrust_result.get('success'):
                    results['overall_status'] = 'approved'
                else:
                    results['overall_status'] = 'pending_blacktrust'
            else:
                results['overall_status'] = 'pending_incode'
                
        return results
        
    async def perform_internal_analysis(self, candidate_data: dict) -> Dict:
        """Realiza un análisis interno de riesgo basado en los datos del candidato"""
        analysis = {
            'risk_score': 0,
            'flags': [],
            'details': {}
        }
        
        # 1. Análisis de consistencia
        consistency = self._analyze_consistency(candidate_data)
        if not consistency['valid']:
            analysis['risk_score'] += consistency['score']
            analysis['flags'].extend(consistency['flags'])
            
        # 2. Análisis de patrones sospechosos
        patterns = self._detect_suspicious_patterns(candidate_data)
        if patterns:
            analysis['risk_score'] += len(patterns) * 5
            analysis['flags'].extend(patterns)
            
        # 3. Análisis de riesgo por unidad de negocio
        business_risk = self._analyze_business_risk(candidate_data)
        analysis['risk_score'] += business_risk['score']
        analysis['flags'].extend(business_risk['flags'])
        
        # 4. Análisis de comportamiento
        behavior = self._analyze_behavior(candidate_data)
        analysis['risk_score'] += behavior['score']
        analysis['flags'].extend(behavior['flags'])
        
        # 5. Recomendaciones específicas
        analysis['recommendations'] = self._get_recommendations(analysis['risk_score'])
        
        return analysis
        
    def _analyze_consistency(self, data: dict) -> Dict:
        """Analiza la consistencia en los datos del candidato"""
        result = {
            'valid': True,
            'score': 0,
            'flags': []
        }
        
        # Validación de nombres
        if not self._validate_names(data):
            result['valid'] = False
            result['score'] += 10
            result['flags'].append('Inconsistencia en nombres')
            
        # Validación de fecha de nacimiento
        if not self._validate_birth_date(data):
            result['valid'] = False
            result['score'] += 15
            result['flags'].append('Fecha de nacimiento inválida')
            
        # Validación de email
        if not self._validate_email(data):
            result['valid'] = False
            result['score'] += 10
            result['flags'].append('Email inválido')
            
        # Validación de teléfono
        if not self._validate_phone(data):
            result['valid'] = False
            result['score'] += 15
            result['flags'].append('Teléfono inválido')
            
        return result
        
    def _validate_names(self, data: dict) -> bool:
        """Valida la consistencia en nombres"""
        if not data.get('nombre') or not data.get('apellido_paterno'):
            return False
            
        return all(
            re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$', name)
            for name in [data['nombre'], data['apellido_paterno']]
        )
        
    def _validate_birth_date(self, data: dict) -> bool:
        """Valida la fecha de nacimiento"""
        try:
            birth_date = datetime.strptime(data['fecha_nacimiento'], "%d/%m/%Y").date()
            age = (datetime.now().date() - birth_date).days / 365
            return 18 <= age <= 70
        except (ValueError, TypeError):
            return False
            
    def _validate_email(self, data: dict) -> bool:
        """Valida el formato del email"""
        if not data.get('email'):
            return False
            
        return bool(re.match(r"[^@]+@[^@]+\.[^@]+", data['email']))
        
    def _validate_phone(self, data: dict) -> bool:
        """Valida el formato del teléfono"""
        if not data.get('phone'):
            return False
            
        return bool(re.match(r'^\+\d{10,15}$', data['phone']))
        
    def _detect_suspicious_patterns(self, data: dict) -> list:
        """Detecta patrones sospechosos en los datos"""
        patterns = []
        
        # Patrones en teléfono
        if data.get('phone'):
            if re.match(r'^\+111', data['phone']) or re.match(r'^\+999', data['phone']):
                patterns.append('Patrón de teléfono sospechoso')
            
        # Patrones en email
        if data.get('email'):
            if re.match(r'^.*@gmail\.com$', data['email']) and data.get('nacionalidad') == 'Estadounidense':
                patterns.append('Email potencialmente sospechoso')
            
        # Patrones en nombre
        if data.get('nombre') and data.get('apellido_paterno'):
            if len(data['nombre'].split()) > 3:
                patterns.append('Nombre sospechosamente largo')
            
        return patterns
        
    def _analyze_business_risk(self, data: dict) -> dict:
        """Analiza el riesgo específico por unidad de negocio"""
        analysis = {
            'score': 0,
            'flags': []
        }
        
        # Reglas específicas por unidad de negocio
        if self.business_unit == 'consumer':
            if data.get('extraversion', 0) < 3:
                analysis['score'] += 15
                analysis['flags'].append('Baja capacidad de venta')
            if data.get('amabilidad', 0) < 3:
                analysis['score'] += 10
                analysis['flags'].append('Bajo nivel de servicio')
                
        elif self.business_unit == 'pharma':
            if data.get('conciencia', 0) < 4:
                analysis['score'] += 20
                analysis['flags'].append('Bajo nivel de profesionalismo')
            if data.get('apertura', 0) < 3:
                analysis['score'] += 15
                analysis['flags'].append('Baja capacidad de aprendizaje')
                
        elif self.business_unit == 'service':
            if data.get('amabilidad', 0) < 3:
                analysis['score'] += 15
                analysis['flags'].append('Bajo nivel de servicio')
            if data.get('estabilidad', 0) < 3:
                analysis['score'] += 10
                analysis['flags'].append('Bajo manejo de estrés')
                
        return analysis
        
    def _analyze_behavior(self, data: dict) -> dict:
        """Analiza el comportamiento basado en los datos del candidato"""
        analysis = {
            'score': 0,
            'flags': []
        }
        
        # Análisis de personalidad
        if data.get('extraversion', 0) < 2:
            analysis['score'] += 10
            analysis['flags'].append('Bajo nivel de sociabilidad')
            
        if data.get('neuroticismo', 0) > 4:
            analysis['score'] += 15
            analysis['flags'].append('Alto nivel de estrés')
            
        # Análisis de patrones de comunicación
        if data.get('email'):
            if '@gmail.com' in data['email'] and data.get('nacionalidad') == 'Estadounidense':
                analysis['score'] += 5
                analysis['flags'].append('Posible uso de email temporal')
                
        return analysis
        
    def _get_recommendations(self, risk_score: int) -> list:
        """Obtiene recomendaciones basadas en el puntaje de riesgo"""
        recommendations = []
        
        if risk_score >= 70:
            recommendations.extend([
                'Realizar verificación manual adicional',
                'Revisar documentos físicos',
                'Contactar referencias',
                'Validar información con fuentes alternativas'
            ])
        elif risk_score >= 40:
            recommendations.extend([
                'Validar información con fuentes alternativas',
                'Revisar antecedentes laborales',
                'Realizar entrevista adicional'
            ])
        else:
            recommendations.extend([
                'Proceso estándar de verificación',
                'Seguimiento periódico'
            ])
            
        return recommendations

    @classmethod
    def get_global_config(cls, api_type: str) -> Optional[ApiConfig]:
        """Obtiene la configuración global para un tipo de API"""
        try:
            return ApiConfig.objects.get(
                business_unit__isnull=True,
                api_type=api_type,
                enabled=True
            )
        except ApiConfig.DoesNotExist:
            return None

    @classmethod
    def get_all_configs_by_category(cls, category: str) -> list:
        """Obtiene todas las configuraciones de una categoría"""
        return list(ApiConfig.objects.filter(
            category=category,
            enabled=True
        ).order_by('business_unit__name'))

    @classmethod
    def get_config_for_business_unit(cls, business_unit: str, api_type: str) -> Optional[ApiConfig]:
        """Obtiene la configuración para una unidad de negocio específica"""
        try:
            return ApiConfig.objects.get(
                business_unit__name=business_unit,
                api_type=api_type,
                enabled=True
            )
        except ApiConfig.DoesNotExist:
            return None

    @classmethod
    def get_api_by_category(cls, category: str, business_unit: str = None) -> Optional[ApiConfig]:
        """Obtiene una API por categoría, preferentemente para la unidad de negocio especificada"""
        try:
            # Primero intenta obtener una configuración específica para la unidad de negocio
            if business_unit:
                return ApiConfig.objects.get(
                    business_unit__name=business_unit,
                    category=category,
                    enabled=True
                )
            
            # Si no hay configuración específica, usa la global
            return ApiConfig.objects.get(
                business_unit__isnull=True,
                category=category,
                enabled=True
            )
        except ApiConfig.DoesNotExist:
            return None

    @classmethod
    def get_all_apis_by_category(cls, category: str) -> list:
        """Obtiene todas las APIs de una categoría, incluyendo globales y específicas"""
        return list(ApiConfig.objects.filter(
            category=category,
            enabled=True
        ).order_by('business_unit__name'))

    @classmethod
    def verify_with_api(cls, category: str, user_id: str, business_unit: str = None) -> Dict:
        """Realiza una verificación usando una API por categoría"""
        config = cls.get_api_by_category(category, business_unit)
        if not config:
            raise ValueError(f"No se encontró una API configurada para la categoría {category}")
            
        if config.api_type == 'incode':
            return cls._verify_with_incode(config, user_id)
        elif config.api_type == 'blacktrust':
            return cls._verify_with_blacktrust(config, user_id)
        else:
            raise ValueError(f"Tipo de API no soportado: {config.api_type}")

    @classmethod
    async def _verify_with_incode(cls, config: ApiConfig, user_id: str) -> Dict:
        """Realiza verificación con INCODE"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{config.additional_settings.get('base_url', 'https://api.incode.com')}/verify",
                    headers={
                        "Authorization": f"Bearer {config.api_key}",
                        "X-API-SECRET": config.api_secret
                    },
                    json={
                        "user_id": user_id,
                        "verification_types": config.additional_settings.get('verification_types', ['INE', 'ID', 'passport'])
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error en verificación INCODE: {str(e)}")
            raise

    @classmethod
    async def _verify_with_blacktrust(cls, config: ApiConfig, user_id: str) -> Dict:
        """Realiza verificación de antecedentes con BlackTrust"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{config.additional_settings.get('base_url', 'https://api.blacktrust.com')}/background-check",
                    headers={
                        "Authorization": f"Bearer {config.api_key}",
                        "X-API-SECRET": config.api_secret
                    },
                    json={
                        "user_id": user_id,
                        "check_types": config.additional_settings.get('background_check_types', ['criminal', 'credit', 'employment']),
                        "regions": config.additional_settings.get('regions', ['global', 'latam', 'usa'])
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error en verificación BlackTrust: {str(e)}")
            raise

class InCodeClient:
    def __init__(self, api_key: str, api_secret: str, settings: dict):
        self.base_url = settings.get('base_url', 'https://api.incode.com')
        self.api_key = api_key
        self.api_secret = api_secret
        self.settings = settings or {}
        
    async def verify(self, user_id: str) -> Dict:
        """Realiza verificación de identidad con INCODE"""
        try:
            async with httpx.AsyncClient(timeout=self.settings.get('timeout', 30)) as client:
                response = await client.post(
                    f"{self.base_url}/verify",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "X-API-SECRET": self.api_secret
                    },
                    json={
                        "user_id": user_id,
                        "verification_types": self.settings.get('verification_types', ['INE', 'ID', 'passport'])
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error en verificación INCODE: {str(e)}")
            raise

class BlackTrustClient:
    def __init__(self, api_key: str, api_secret: str, settings: dict):
        self.base_url = settings.get('base_url', 'https://api.blacktrust.com')
        self.api_key = api_key
        self.api_secret = api_secret
        self.settings = settings or {}
        
    async def verify(self, user_id: str) -> Dict:
        """Realiza verificación de antecedentes con BlackTrust"""
        try:
            async with httpx.AsyncClient(timeout=self.settings.get('timeout', 30)) as client:
                response = await client.post(
                    f"{self.base_url}/background-check",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "X-API-SECRET": self.api_secret
                    },
                    json={
                        "user_id": user_id,
                        "check_types": self.settings.get('background_check_types', ['criminal', 'credit', 'employment']),
                        "regions": self.settings.get('regions', ['global', 'latam', 'usa'])
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error en verificación BlackTrust: {str(e)}")
            raise
