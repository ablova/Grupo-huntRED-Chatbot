import logging
import asyncio
import os
import json
from typing import Dict, List, Optional, Any, Union
import hashlib
from django.conf import settings
from app.models import BusinessUnit
from app.com.utils.cache import RedisCache
from environ import Env

env = Env()
logger = logging.getLogger(__name__)

class TabiyaConfig:
    """Configuración centralizada para Tabiya.
    
    Esta clase proporciona un punto único de configuración para todos los
    aspectos relacionados con la integración de Tabiya, incluyendo API keys,
    endpoints, timeouts y configuraciones específicas por BU.
    """
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Obtiene la configuración completa de Tabiya."""
        # Configuración general de NLP
        nlp_settings = {
            'USE_TABIYA': env.bool('NLP_USE_TABIYA', default=True),
            'FALLBACK_TO_SPACY': env.bool('NLP_FALLBACK_TO_SPACY', default=True),
            'MIN_TEXT_LENGTH': env.int('NLP_MIN_TEXT_LENGTH', default=100),
        }
        
        # Configuración de API
        api_config = TabiyaConfig.get_api_config()
        
        # Configuración por BU
        bu_configs = {
            'huntRED': TabiyaConfig.get_bu_config('huntRED'),
            'huntU': TabiyaConfig.get_bu_config('huntU'),
            'Amigro': TabiyaConfig.get_bu_config('Amigro'),
            'SEXSI': TabiyaConfig.get_bu_config('SEXSI')
        }
        
        return {
            'NLP': nlp_settings,
            'API': api_config,
            'BUSINESS_UNITS': bu_configs
        }
    
    @staticmethod
    def get_api_config() -> Dict[str, Any]:
        """Obtiene la configuración específica de la API de Tabiya."""
        return {
            'API_KEY': env.str('TABIYA_API_KEY', default=''),
            'API_URL': env.str('TABIYA_API_URL', default='https://api.tabiya.ai/v1'),
            'API_VERSION': env.str('TABIYA_API_VERSION', default='v1'),
            'TIMEOUT': env.int('TABIYA_TIMEOUT', default=30),
            'MAX_RETRIES': env.int('TABIYA_MAX_RETRIES', default=3),
            'BACKOFF_FACTOR': env.float('TABIYA_BACKOFF_FACTOR', default=0.3),
            'CACHE_TTL': env.int('TABIYA_CACHE_TTL', default=86400),  # 24 horas
            'ENDPOINTS': {
                'MATCH': '/match',
                'CLASSIFY': '/classify',
                'EXTRACT': '/extract',
                'ANALYZE': '/analyze'
            }
        }
    
    @staticmethod
    def get_bu_config(business_unit: str) -> Dict[str, Any]:
        """Obtiene la configuración específica por BU para Tabiya."""
        # Configuración base para cualquier BU
        base_config = {
            'ENABLED': True,
            'MODELS': {
                'SKILLS': 'skill-detector',
                'EXPERIENCE': 'experience-analyzer',
                'CULTURE': 'culture-analyzer',
                'PERSONALITY': 'personality-analyzer'
            },
            'WEIGHTS': {
                'SKILLS': 0.4,
                'EXPERIENCE': 0.3,
                'CULTURE': 0.2,
                'PERSONALITY': 0.1
            },
            'ESCO': {
                'ENABLED': True,
                'MIN_CONFIDENCE': 0.7,
                'TAXONOMY_FILE': os.path.join(settings.BASE_DIR, 'ESCO_occup_skills.json')
            }
        }
        
        # Configuraciones específicas por BU
        bu_specific = {
            'huntRED': {
                'WEIGHTS': {
                    'SKILLS': 0.3,
                    'EXPERIENCE': 0.4,
                    'CULTURE': 0.2,
                    'PERSONALITY': 0.1
                }
            },
            'huntU': {
                'WEIGHTS': {
                    'SKILLS': 0.5,
                    'EXPERIENCE': 0.2,
                    'CULTURE': 0.2,
                    'PERSONALITY': 0.1
                }
            },
            'Amigro': {
                'WEIGHTS': {
                    'SKILLS': 0.6,
                    'EXPERIENCE': 0.2,
                    'CULTURE': 0.1,
                    'PERSONALITY': 0.1
                }
            },
            'SEXSI': {
                'WEIGHTS': {
                    'SKILLS': 0.3,
                    'EXPERIENCE': 0.3,
                    'CULTURE': 0.3,
                    'PERSONALITY': 0.1
                }
            }
        }
        
        # Obtiene la configuración específica de la BU o usa base_config si no existe
        if business_unit in bu_specific:
            # Combina configuración base con específica
            for key, value in bu_specific[business_unit].items():
                if isinstance(value, dict) and key in base_config and isinstance(base_config[key], dict):
                    # Si ambos son diccionarios, combina en lugar de reemplazar
                    base_config[key].update(value)
                else:
                    # De lo contrario, simplemente reemplaza el valor
                    base_config[key] = value
                    
        return base_config
        
    @staticmethod
    def load_esco_taxonomy(business_unit: str = None) -> Dict[str, Any]:
        """Carga la taxonomía ESCO desde el archivo de configuración."""
        bu_config = TabiyaConfig.get_bu_config(business_unit) if business_unit else TabiyaConfig.get_bu_config('huntRED')
        taxonomy_file = bu_config['ESCO']['TAXONOMY_FILE']
        
        try:
            if os.path.exists(taxonomy_file):
                with open(taxonomy_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Archivo de taxonomía ESCO no encontrado: {taxonomy_file}")
                return {}
        except Exception as e:
            logger.error(f"Error cargando taxonomía ESCO: {str(e)}")
            return {}
    
    @staticmethod
    def is_tabiya_enabled() -> bool:
        """Verifica si Tabiya está habilitado en la configuración."""
        return env.bool('NLP_USE_TABIYA', default=True)

class TabiyaClient:
    """Cliente para integración con la API de Tabiya Technologies.
    
    Esta clase gestiona las conexiones con la API de Tabiya y proporciona
    acceso a los diferentes modelos disponibles.
    """
    def __init__(self, api_key: str = None, business_unit: str = None):
        """Inicializa un cliente de Tabiya con configuración específica.
        
        Args:
            api_key: Clave de API para Tabiya, sobrescribe la configuración
            business_unit: Unidad de negocio para configuración específica
        """
        self.config = TabiyaConfig.get_api_config()
        self.bu_config = TabiyaConfig.get_bu_config(business_unit) if business_unit else None
        self.api_key = api_key or self.config['API_KEY']
        self.base_url = self.config['API_URL']
        self.timeout = self.config['TIMEOUT']
        self.max_retries = self.config['MAX_RETRIES']
        self.endpoints = self.config['ENDPOINTS']
        self.cache = RedisCache()
        self.session = None
        
    async def __aenter__(self):
        """Inicializa la sesión asíncrona al usar un context manager."""
        import aiohttp
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cierra la sesión asíncrona al salir del context manager."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_model(self, model_name: str = None):
        """Obtiene un modelo específico de Tabiya.
        
        Args:
            model_name: Nombre del modelo a utilizar
            
        Returns:
            Una instancia de TabiyaModel configurada
        """
        return TabiyaModel(self, model_name)
    
    async def call_api(self, endpoint: str, data: Dict) -> Dict:
        """Realiza una llamada a la API de Tabiya.
        
        Args:
            endpoint: Ruta del endpoint relativa a la base_url
            data: Datos a enviar en la llamada
            
        Returns:
            Respuesta de la API como diccionario
            
        Raises:
            Exception: Si hay un error en la comunicación con la API
        """
        import aiohttp
        from urllib.parse import urljoin
        import backoff
        
        url = urljoin(self.base_url, endpoint)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'X-Tabiya-Client': 'huntRED-API-v2'
        }
        
        # Generar un hash único para esta solicitud para caché
        request_hash = hashlib.md5(f"{endpoint}:{json.dumps(data, sort_keys=True)}".encode()).hexdigest()
        cache_key = f"tabiya:api:{request_hash}"
        
        # Verificar caché primero
        cached_response = await self.cache.get(cache_key)
        if cached_response:
            logger.debug(f"Usando respuesta en caché para {endpoint}")
            return cached_response
        
        # Función para hacer la llamada HTTP con backoff
        @backoff.on_exception(backoff.expo, 
                             (aiohttp.ClientError, asyncio.TimeoutError),
                             max_tries=self.max_retries,
                             max_time=self.timeout*2)
        async def _make_request():
            close_session = False
            if not self.session:
                self.session = aiohttp.ClientSession()
                close_session = True
                
            try:
                async with self.session.post(url, json=data, headers=headers, timeout=self.timeout) as response:
                    response.raise_for_status()
                    result = await response.json()
                    # Guardar en caché para futuras solicitudes
                    await self.cache.set(cache_key, result, ttl=self.config['CACHE_TTL'])
                    return result
            finally:
                if close_session and self.session:
                    await self.session.close()
                    self.session = None
        
        try:
            return await _make_request()
        except Exception as e:
            logger.error(f"Error en llamada a API Tabiya {endpoint}: {str(e)}")
            raise

class TabiyaModel:
    """Representa un modelo específico de Tabiya Technologies.
    
    Esta clase implementa la funcionalidad para analizar texto usando
    diferentes modelos de procesamiento de lenguaje natural ofrecidos
    por Tabiya, con soporte para taxonomía ESCO y análisis de dominio
    específico.
    """
    def __init__(self, client: TabiyaClient, model_name: str):
        """Inicializa un modelo específico de Tabiya.
        
        Args:
            client: Cliente configurado para la API de Tabiya
            model_name: Nombre del modelo a utilizar
        """
        self.client = client
        self.model_name = model_name
        self.business_unit = client.bu_config['MODELS'][model_name] if client.bu_config else None
        self.esco_taxonomy = None
        self.is_esco_enabled = client.bu_config and client.bu_config.get('ESCO', {}).get('ENABLED', False) if client.bu_config else False
        
    async def analyze(self, text: str) -> Dict:
        """Analiza texto usando el modelo de Tabiya.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Diccionario con el resultado del análisis
            
        Raises:
            Exception: Si hay un error en el análisis y no hay fallback disponible
        """
        # Verificar si el texto tiene suficiente contenido para analizar
        if not text or len(text) < TabiyaConfig.get_config()['NLP']['MIN_TEXT_LENGTH']:
            logger.warning(f"Texto demasiado corto para análisis con Tabiya: {len(text)} caracteres")
            return self._get_empty_result()
            
        # Generar clave de caché basada en el texto y el modelo
        cache_key = f"tabiya:{self.model_name}:{hashlib.md5(text.encode()).hexdigest()}"
        cached = await self.client.cache.get(cache_key)
        
        if cached:
            logger.debug(f"Usando resultado en caché para modelo {self.model_name}")
            return cached
            
        try:
            # Realizar llamada a la API de Tabiya
            result = await self._call_tabiya_api(text)
            
            # Si estamos analizando habilidades y ESCO está habilitado, enriquecemos los resultados
            if self.model_name == 'SKILLS' and self.is_esco_enabled:
                result = await self._enrich_with_esco(result)
                
            # Guardar en caché para futuras solicitudes
            await self.client.cache.set(
                cache_key, 
                result, 
                ttl=self.client.config['CACHE_TTL']
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis de Tabiya {self.model_name}: {str(e)}")
            
            # Verificar si debemos usar spaCy como fallback
            if TabiyaConfig.get_config()['NLP']['FALLBACK_TO_SPACY']:
                logger.info(f"Usando spaCy como fallback para análisis de {self.model_name}")
                return await self._fallback_to_spacy(text)
            else:
                raise
            
    async def _call_tabiya_api(self, text: str) -> Dict:
        """Realiza una llamada a la API de Tabiya para análisis.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Resultado del análisis como diccionario
        """
        # Determinar el endpoint basado en el modelo
        endpoint = self.client.endpoints['ANALYZE']
        
        # Preparar los datos para la llamada a la API
        data = {
            "text": text,
            "model": self.model_name,
            "options": {
                "language": "es",  # Por defecto español para huntRED
                "return_context": True,
                "max_results": 50
            }
        }
        
        # Si hay configuración específica de BU, añadirla
        if self.client.bu_config:
            data["business_unit"] = self.client.bu_config
            
        # Realizar la llamada a la API y retornar resultados
        return await self.client.call_api(endpoint, data)
        
    async def _enrich_with_esco(self, result: Dict) -> Dict:
        """Enriquece los resultados con información de la taxonomía ESCO.
        
        Args:
            result: Resultado base del análisis
            
        Returns:
            Resultado enriquecido con información ESCO
        """
        # Cargar taxonomía ESCO si no está cargada
        if not self.esco_taxonomy:
            bu_name = self.client.bu_config['name'] if self.client.bu_config and 'name' in self.client.bu_config else None
            self.esco_taxonomy = TabiyaConfig.load_esco_taxonomy(bu_name)
            
        # Si no hay taxonomía, retornar el resultado original
        if not self.esco_taxonomy:
            return result
            
        # Procesar cada habilidad detectada y enriquecerla con información ESCO
        skills = result.get("skills", [])
        enriched_skills = []
        
        for skill in skills:
            skill_name = skill.get("name", "")
            if skill_name in self.esco_taxonomy.get("skills", {}):
                esco_info = self.esco_taxonomy["skills"][skill_name]
                skill["esco_id"] = esco_info.get("id")
                skill["esco_level"] = esco_info.get("level")
                skill["esco_description"] = esco_info.get("description")
                skill["esco_parent"] = esco_info.get("parent")
                
            enriched_skills.append(skill)
            
        result["skills"] = enriched_skills
        return result
        
    async def _fallback_to_spacy(self, text: str) -> Dict:
        """Realiza análisis con spaCy como fallback cuando Tabiya falla.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Resultado del análisis con spaCy en formato compatible con Tabiya
        """
        try:
            import spacy
            from app.com.utils.spacy_adapter import SpacyAdapter
            
            # Usar el adaptador de spaCy para obtener un formato similar
            spacy_adapter = SpacyAdapter()
            
            if self.model_name == 'SKILLS':
                return {"skills": await spacy_adapter.extract_skills(text)}
            elif self.model_name == 'EXPERIENCE':
                return {"experience": await spacy_adapter.extract_experience(text)}
            elif self.model_name == 'CULTURE':
                return {"culture": await spacy_adapter.extract_culture(text)}
            else:
                return self._get_empty_result()
                
        except Exception as e:
            logger.error(f"Error en fallback a spaCy: {str(e)}")
            return self._get_empty_result()
    
    def _get_empty_result(self) -> Dict:
        """Retorna un resultado vacío compatible con el formato esperado.
        
        Returns:
            Diccionario vacío para el tipo de modelo
        """
        if self.model_name == 'SKILLS':
            return {"skills": []}
        elif self.model_name == 'EXPERIENCE':
            return {"experience": {}}
        elif self.model_name == 'CULTURE':
            return {"culture": {}}
        elif self.model_name == 'PERSONALITY':
            return {"personality": {}}
        else:
            return {}
        
    def _analyze_skills(self, text: str) -> List[Dict]:
        """Analiza habilidades usando patrones de NLP avanzado.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Lista de habilidades detectadas con confianza y contexto
        """
        # Esta implementación es para simulación, en producción usa la API
        skills = []
        # Simular detección de habilidades comunes
        for skill in ["Python", "Django", "React", "SQL", "AWS"]:
            if skill.lower() in text.lower():
                skills.append({
                    "name": skill,
                    "confidence": 0.9,
                    "context": f"Se menciona {skill} en el texto"
                })
        return skills
        
    def _analyze_experience(self, text: str) -> Dict:
        """Analiza experiencia profesional usando patrones de NLP.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Diccionario con análisis de experiencia
        """
        # Implementación para simulación
        return {
            "years": 5,  # Años estimados de experiencia
            "domains": ["Tecnología", "Desarrollo web"],
            "positions": ["Desarrollador", "Líder técnico"],
            "confidence": 0.8,
        }
        
    def _analyze_culture(self, text: str) -> Dict:
        """Analiza fit cultural y valores organizacionales.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Diccionario con análisis de cultura organizacional
        """
        # Implementación para simulación
        return {
            "values": ["Innovación", "Trabajo en equipo", "Orientación a resultados"],
            "leadership_style": "Colaborativo",
            "work_environment": "Dinámico",
            "confidence": 0.7,
        }

class TabiyaNLPAdapter:
    """Adaptador para integrar NLP con Tabiya Technologies.
    
    Esta clase proporciona una interfaz unificada para interactuar con
    los diferentes modelos de Tabiya, facilitando el análisis de texto
    completo con múltiples modelos.
    """
    def __init__(self, business_unit: BusinessUnit = None):
        """Inicializa el adaptador NLP para Tabiya.
        
        Args:
            business_unit: Unidad de negocio para configuración específica
        """
        self.business_unit = business_unit
        self.bu_name = business_unit.name if business_unit else None
        
        # Verificar si Tabiya está habilitado en la configuración
        self.is_enabled = TabiyaConfig.is_tabiya_enabled()
        
        if not self.is_enabled:
            logger.warning("Tabiya está deshabilitado en la configuración")
            return
            
        # Inicializar cliente y modelos
        self.client = TabiyaClient(business_unit=self.bu_name)
        self.config = TabiyaConfig.get_bu_config(self.bu_name) if self.bu_name else TabiyaConfig.get_bu_config(None)
        
        # Inicializar modelos basándonos en la configuración
        self.models = {}
        self._init_models()
        
        # Cache para resultados de análisis
        self.cache = RedisCache()
        
    def _init_models(self):
        """Inicializa los modelos de Tabiya según la configuración."""
        if not self.is_enabled:
            return
            
        model_config = self.config.get('MODELS', {})
        
        # Inicializar cada modelo configurado
        for model_key, model_name in model_config.items():
            self.models[model_key.lower()] = self.client.get_model(model_name)
        
    async def analyze(self, text: str) -> Dict:
        """Analiza texto completo usando varios modelos de Tabiya.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Diccionario con los resultados de cada modelo
            
        Raises:
            Exception: Si ocurre un error y no hay fallback configurado
        """
        if not self.is_enabled:
            logger.warning("Intentando usar Tabiya cuando está deshabilitado")
            return self._get_empty_result()
            
        # Verificar si el texto cumple con los requisitos mínimos
        if not text or len(text) < TabiyaConfig.get_config()['NLP']['MIN_TEXT_LENGTH']:
            logger.warning(f"Texto demasiado corto para análisis con Tabiya: {len(text)} caracteres")
            return self._get_empty_result()
            
        # Generar clave de caché para el análisis completo
        cache_key = f"tabiya:full_analysis:{self.bu_name}:{hashlib.md5(text.encode()).hexdigest()}"
        cached = await self.cache.get(cache_key)
        
        if cached:
            logger.debug("Usando análisis completo de Tabiya desde caché")
            return cached
            
        try:
            # Iniciar análisis asíncrono con todos los modelos
            analysis_tasks = {}
            for model_key, model in self.models.items():
                analysis_tasks[model_key] = asyncio.create_task(model.analyze(text))
                
            # Esperar que todos los análisis se completen
            results = {}
            for model_key, task in analysis_tasks.items():
                try:
                    model_result = await task
                    results[model_key] = model_result
                except Exception as e:
                    logger.error(f"Error en modelo {model_key}: {str(e)}")
                    results[model_key] = {}  # Resultado vacío para el modelo que falló
            
            # Guardar en caché para futuras solicitudes
            await self.cache.set(cache_key, results, ttl=self.client.config['CACHE_TTL'])
            
            return results
            
        except Exception as e:
            logger.error(f"Error en análisis completo de Tabiya: {str(e)}")
            
            if TabiyaConfig.get_config()['NLP']['FALLBACK_TO_SPACY']:
                logger.info("Usando spaCy como fallback para análisis completo")
                return await self._fallback_to_spacy(text)
            else:
                raise
                
    async def _fallback_to_spacy(self, text: str) -> Dict:
        """Realiza un análisis completo con spaCy como fallback.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Resultados del análisis con spaCy en formato compatible
        """
        try:
            from app.com.utils.spacy_adapter import SpacyAdapter
            
            spacy_adapter = SpacyAdapter()
            return await spacy_adapter.analyze(text)
            
        except Exception as e:
            logger.error(f"Error en fallback a spaCy: {str(e)}")
            return self._get_empty_result()
            
    def _get_empty_result(self) -> Dict:
        """Retorna un resultado vacío compatible con el formato esperado."""
        return {
            "skills": {"skills": []},
            "experience": {"experience": {}},
            "culture": {"culture": {}},
            "personality": {"personality": {}}
        }

class TabiyaMatchingEngine:
    """Motor de matching que utiliza modelos de Tabiya.
    
    Esta clase implementa algoritmos avanzados de correspondencia (matching)
    entre perfiles de candidatos y vacantes, utilizando los análisis de Tabiya
    y ajustando las ponderaciones según la unidad de negocio y posición.
    """
    def __init__(self, business_unit: BusinessUnit = None):
        """Inicializa el motor de matching con configuración específica por BU.
        
        Args:
            business_unit: Unidad de negocio para configuración específica
        """
        self.business_unit = business_unit
        self.bu_name = business_unit.name if business_unit else None
        self.nlp = TabiyaNLPAdapter(business_unit)
        self.config = TabiyaConfig.get_bu_config(self.bu_name) if self.bu_name else TabiyaConfig.get_bu_config(None)
        self.weights = self.config.get('WEIGHTS', {})
        self.cache = RedisCache()
        
    async def calculate_match_score(self, candidate: Dict, vacancy: Dict) -> Dict:
        """Calcula score de matching usando Tabiya y ponderaciones dinámicas.
        
        Args:
            candidate: Datos del candidato incluyendo texto para análisis
            vacancy: Datos de la vacante incluyendo texto para análisis
            
        Returns:
            Diccionario con score total y scores por componente
            
        Raises:
            Exception: Si hay un error en el cálculo y no hay fallback
        """
        # Generar clave de caché para el matching
        candidate_hash = hashlib.md5(candidate.get('text', '').encode()).hexdigest()
        vacancy_hash = hashlib.md5(vacancy.get('text', '').encode()).hexdigest()
        cache_key = f"tabiya:match:{self.bu_name}:{candidate_hash}:{vacancy_hash}"
        
        # Verificar si tenemos resultado en caché
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.debug("Usando score de matching desde caché")
            return cached_result
        
        try:
            # Obtener análisis de ambos perfiles
            candidate_analysis = await self.nlp.analyze(candidate.get('text', ''))
            vacancy_analysis = await self.nlp.analyze(vacancy.get('text', ''))
            
            # Obtener ponderaciones dinámicas según posición
            position_level = vacancy.get('position_level', 'senior')
            position_weights = await self._get_position_weights(position_level)
            
            # Calcular score ponderado con los análisis y ponderaciones
            score_result = await self._calculate_weighted_score(
                candidate_analysis,
                vacancy_analysis,
                position_weights
            )
            
            # Guardar en caché para futuras consultas
            await self.cache.set(cache_key, score_result, ttl=86400)  # 24 horas
            
            return score_result
            
        except Exception as e:
            logger.error(f"Error calculando score de matching: {str(e)}")
            return {
                "total_score": 0.0,
                "component_scores": {
                    "skills": 0.0,
                    "experience": 0.0,
                    "culture": 0.0,
                    "personality": 0.0
                }
            }
    
    async def _get_position_weights(self, position_level: str) -> Dict:
        """Obtiene ponderaciones específicas para un nivel de posición.
        
        Args:
            position_level: Nivel de la posición (junior, senior, executive)
            
        Returns:
            Diccionario con ponderaciones para cada componente
        """
        # Ponderaciones base desde la configuración
        weights = dict(self.weights)
        
        # Ajustar ponderaciones según nivel de posición
        if position_level.lower() == 'junior':
            weights['SKILLS'] = weights.get('SKILLS', 0.4) * 1.3  # Más énfasis en habilidades
            weights['EXPERIENCE'] = weights.get('EXPERIENCE', 0.3) * 0.7  # Menos énfasis en experiencia
        elif position_level.lower() == 'executive':
            weights['EXPERIENCE'] = weights.get('EXPERIENCE', 0.3) * 1.2  # Más énfasis en experiencia
            weights['CULTURE'] = weights.get('CULTURE', 0.2) * 1.3  # Más énfasis en cultura
        
        # Normalizar para que la suma sea 1
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
            
        return weights
            
    async def _calculate_weighted_score(self, candidate: Dict, vacancy: Dict, weights: Dict) -> Dict:
        """Calcula score ponderado usando análisis de Tabiya.
        
        Args:
            candidate: Análisis del candidato
            vacancy: Análisis de la vacante
            weights: Ponderaciones por componente
            
        Returns:
            Diccionario con score total y scores por componente
        """
        # Comparar cada componente usando modelos de Tabiya
        component_scores = {}
        
        # Análisis de habilidades
        component_scores['skills'] = await self._compare_skills(
            candidate.get('skills', {}).get('skills', []),
            vacancy.get('skills', {}).get('skills', [])
        )
        
        # Análisis de experiencia
        component_scores['experience'] = await self._compare_experience(
            candidate.get('experience', {}).get('experience', {}),
            vacancy.get('experience', {}).get('experience', {})
        )
        
        # Análisis de cultura
        component_scores['culture'] = await self._compare_culture(
            candidate.get('culture', {}).get('culture', {}),
            vacancy.get('culture', {}).get('culture', {})
        )
        
        # Análisis de personalidad (si está disponible)
        component_scores['personality'] = await self._compare_personality(
            candidate.get('personality', {}).get('personality', {}),
            vacancy.get('personality', {}).get('personality', {})
        )
        
        # Aplicar ponderaciones para calcular score total
        total_score = 0.0
        for component, score in component_scores.items():
            weight_key = component.upper()
            if weight_key in weights:
                total_score += score * weights[weight_key]
        
        # Normalizar score total a un valor entre 0 y 1
        total_score = max(0.0, min(1.0, total_score))
        
        return {
            "total_score": total_score,
            "component_scores": component_scores
        }
        
    async def _compare_skills(self, candidate_skills: List[Dict], vacancy_skills: List[Dict]) -> float:
        """Compara habilidades del candidato con las requeridas por la vacante.
        
        Args:
            candidate_skills: Lista de habilidades del candidato
            vacancy_skills: Lista de habilidades requeridas
            
        Returns:
            Score de correspondencia entre 0 y 1
        """
        # Si no hay habilidades para comparar, retornar 0
        if not candidate_skills or not vacancy_skills:
            return 0.0
            
        # Extraer nombres de habilidades para comparación
        candidate_skill_names = {skill.get('name', '').lower() for skill in candidate_skills if skill.get('name')}
        vacancy_skill_names = {skill.get('name', '').lower() for skill in vacancy_skills if skill.get('name')}
        
        # Calcular score basado en las coincidencias y ponderaciones
        matching_skills = candidate_skill_names.intersection(vacancy_skill_names)
        required_skills_covered = len(matching_skills) / len(vacancy_skill_names) if vacancy_skill_names else 0
        
        # Si hay taxonomía ESCO, calcular también similitud semántica
        semantic_similarity = 0.0
        has_esco = any('esco_id' in skill for skill in candidate_skills) and any('esco_id' in skill for skill in vacancy_skills)
        
        if has_esco:
            # Calcular similitud usando IDs de ESCO
            candidate_esco_ids = {skill.get('esco_id') for skill in candidate_skills if skill.get('esco_id')}
            vacancy_esco_ids = {skill.get('esco_id') for skill in vacancy_skills if skill.get('esco_id')}
            
            matching_esco = candidate_esco_ids.intersection(vacancy_esco_ids)
            semantic_similarity = len(matching_esco) / len(vacancy_esco_ids) if vacancy_esco_ids else 0
            
            # Combinar scores dando más peso a ESCO
            skill_score = (required_skills_covered * 0.4) + (semantic_similarity * 0.6)
        else:
            skill_score = required_skills_covered
            
        return skill_score
        
    async def _compare_experience(self, candidate_exp: Dict, vacancy_exp: Dict) -> float:
        """Compara experiencia del candidato con la requerida por la vacante.
        
        Args:
            candidate_exp: Experiencia analizada del candidato
            vacancy_exp: Experiencia requerida por la vacante
            
        Returns:
            Score de correspondencia entre 0 y 1
        """
        # Si no hay datos de experiencia, retornar 0
        if not candidate_exp or not vacancy_exp:
            return 0.0
            
        # Comparar años de experiencia
        candidate_years = candidate_exp.get('years', 0)
        required_years = vacancy_exp.get('years', 0)
        
        # Score basado en años de experiencia (normalizado)
        years_ratio = min(1.0, candidate_years / required_years) if required_years > 0 else 0.0
        
        # Comparar dominios y posiciones
        candidate_domains = set(candidate_exp.get('domains', []))
        vacancy_domains = set(vacancy_exp.get('domains', []))
        domain_overlap = len(candidate_domains.intersection(vacancy_domains)) / len(vacancy_domains) if vacancy_domains else 0.0
        
        candidate_positions = set(candidate_exp.get('positions', []))
        vacancy_positions = set(vacancy_exp.get('positions', []))
        position_overlap = len(candidate_positions.intersection(vacancy_positions)) / len(vacancy_positions) if vacancy_positions else 0.0
        
        # Combinar scores con ponderaciones
        experience_score = (years_ratio * 0.5) + (domain_overlap * 0.3) + (position_overlap * 0.2)
        return experience_score
        
    async def _compare_culture(self, candidate_culture: Dict, vacancy_culture: Dict) -> float:
        """Compara fit cultural del candidato con la cultura organizacional.
        
        Args:
            candidate_culture: Cultura analizada del candidato
            vacancy_culture: Cultura requerida por la organización
            
        Returns:
            Score de fit cultural entre 0 y 1
        """
        # Si no hay datos de cultura, retornar 0
        if not candidate_culture or not vacancy_culture:
            return 0.0
            
        # Comparar valores culturales
        candidate_values = set(candidate_culture.get('values', []))
        vacancy_values = set(vacancy_culture.get('values', []))
        values_overlap = len(candidate_values.intersection(vacancy_values)) / len(vacancy_values) if vacancy_values else 0.0
        
        # Comparar estilo de liderazgo
        leadership_match = 1.0 if candidate_culture.get('leadership_style') == vacancy_culture.get('leadership_style') else 0.0
        
        # Comparar ambiente de trabajo
        environment_match = 1.0 if candidate_culture.get('work_environment') == vacancy_culture.get('work_environment') else 0.0
        
        # Combinar scores con ponderaciones
        culture_score = (values_overlap * 0.6) + (leadership_match * 0.2) + (environment_match * 0.2)
        return culture_score
        
    async def _compare_personality(self, candidate_personality: Dict, vacancy_personality: Dict) -> float:
        """Compara rasgos de personalidad del candidato con los deseados.
        
        Args:
            candidate_personality: Personalidad analizada del candidato
            vacancy_personality: Personalidad deseada para el rol
            
        Returns:
            Score de coincidencia de personalidad entre 0 y 1
        """
        # Si no hay datos de personalidad, retornar valor neutral
        if not candidate_personality or not vacancy_personality:
            return 0.5  # Valor neutral cuando no hay datos
            
        # Esta implementación es simplificada, en producción usaría algoritmos más avanzados
        # de comparación de perfiles de personalidad (OCEAN, DISC, etc.)
        return 0.5  # Implementación pendiente
