"""
Conectores optimizados para integrar los nuevos sistemas NLP/GPT con el chatbot existente.
Este módulo proporciona adapatadores que mantienen compatibilidad total con la API
existente mientras aprovechan los nuevos sistemas optimizados.
"""

import asyncio
import logging
import json
import time
import os
from typing import Dict, List, Any, Optional, Union
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.cache import cache

# Intenta importar módulos de monitoreo (opcional)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Cache para minimizar importaciones repetidas
_cached_imports = {}

async def _import_module(module_path: str, default=None):
    """
    Importa un módulo dinámicamente, con caché para mejorar rendimiento
    """
    if module_path in _cached_imports:
        return _cached_imports[module_path]
    
    try:
        components = module_path.split('.')
        mod = __import__(components[0])
        
        for comp in components[1:]:
            mod = getattr(mod, comp)
            
        _cached_imports[module_path] = mod
        return mod
    except (ImportError, AttributeError) as e:
        logger.debug(f"No se pudo importar {module_path}: {str(e)}")
        return default


class OptimizedGPTConnector:
    """
    Conector optimizado para GPT que aprovecha el sistema de adaptadores
    manteniendo compatibilidad total con la API existente.
    """
    
    def __init__(self):
        """Inicialización con soporte para sistemas antiguos y nuevos"""
        self.handler = None
        self.adapters_available = False
        self.legacy_handler = None
        self.business_unit = None
        
        # Verificar si el nuevo sistema está disponible
        asyncio.create_task(self._initialize_adapters())
    
    async def _initialize_adapters(self):
        """Intenta inicializar el sistema de adaptadores asíncronamente"""
        try:
            # Importar sistema adaptador optimizado
            ai_adapters = await _import_module('app.utils.ai_adapters')
            if ai_adapters:
                self.adapters_available = True
                logger.info("Sistema optimizado de AI adaptadores disponible")
        except Exception as e:
            logger.debug(f"Sistema optimizado no disponible: {str(e)}")
            self.adapters_available = False
    
    async def get_legacy_handler(self):
        """Obtiene una instancia del manejador GPT legacy"""
        if self.legacy_handler:
            return self.legacy_handler
            
        try:
            # Ruta correcta al módulo GPT
            gpt_module = await _import_module('app.ats.utils.gpt')
            GPTHandler = getattr(gpt_module, 'GPTHandler', None)
            
            if GPTHandler:
                handler = GPTHandler()
                await handler.initialize()
                self.legacy_handler = handler
                return handler
            
            logger.error("GPTHandler no disponible en módulo gpt.py")
            return None
        except Exception as e:
            logger.error(f"Error inicializando legacy GPTHandler: {str(e)}")
            return None
    
    async def initialize(self, business_unit=None):
        """
        Inicializa el adaptador con una business unit específica
        
        Args:
            business_unit: Objeto BusinessUnit para configuración
        """
        self.business_unit = business_unit
        
        if not self.adapters_available:
            # Si el sistema optimizado no está disponible, usar legacy
            await self.get_legacy_handler()
            return True
            
        logger.info(f"GPTConnector optimizado inicializado para BU: {getattr(business_unit, 'name', None)}")
        return True
    
    async def generate_response(self, prompt: str, business_unit=None) -> str:
        """
        Genera una respuesta usando el sistema optimizado o legacy
        
        Args:
            prompt: Texto del prompt
            business_unit: BusinessUnit opcional (sobreescribe la configurada)
            
        Returns:
            Respuesta generada como string
        """
        # Usar BU proporcionada o la guardada en la instancia
        bu = business_unit or self.business_unit
        bu_id = getattr(bu, 'id', None) or getattr(bu, 'name', None)
        
        # Registrar contexto para logs
        context = {
            "business_unit": getattr(bu, 'name', str(bu)),
            "prompt_length": len(prompt)
        }
        logger.info(f"Generando respuesta GPT", extra=context)
        
        # Medir tiempo de ejecución
        start_time = time.time()
        
        if self.adapters_available:
            try:
                # Intentar usar sistema optimizado
                ai_adapters = await _import_module('app.utils.ai_adapters')
                
                # Obtener configuración específica para la BU
                system_prompt = None
                params = {}
                
                try:
                    from app.ats.utils.system_integrator import SystemIntegrator
                    bu_config = SystemIntegrator.get_business_unit_config(bu_id)
                    if bu_config and 'ai_settings' in bu_config:
                        params = bu_config['ai_settings']
                        system_prompt = bu_config.get('default_system_prompt')
                except ImportError:
                    # Buscar configuración en settings directamente
                    if hasattr(settings, 'get_business_unit_config'):
                        bu_config = settings.get_business_unit_config(bu_id, 'gpt')
                        if bu_config:
                            params = bu_config
                
                # Incluir system prompt si existe
                if system_prompt:
                    params['system_prompt'] = system_prompt
                
                # Generar respuesta con el adaptador optimizado
                if not params:
                    params = {}
                    
                # Determinar proveedor y modelo preferidos
                provider = 'openai'
                model = 'gpt-3.5-turbo'
                
                # Si hay GPT API configurado, usarlo
                try:
                    from app.models import GptApi
                    gpt_api = await sync_to_async(lambda: GptApi.objects.filter(
                        is_active=True
                    ).first())()
                    
                    if gpt_api:
                        provider = gpt_api.provider.name.lower()
                        if '(' in provider:
                            provider = provider.split('(')[0].strip().lower()
                        model = gpt_api.model
                except Exception as e:
                    logger.debug(f"No se pudo obtener GPT API: {str(e)}")
                
                # Generar respuesta
                response = await ai_adapters.generate_completion(
                    prompt=prompt,
                    business_unit_id=bu_id,
                    provider=provider,
                    model=model,
                    params=params
                )
                
                elapsed = time.time() - start_time
                logger.info(f"Respuesta generada en {elapsed:.2f}s", extra=context)
                return response
                    
            except Exception as e:
                # Si falla, usar el sistema legacy
                logger.warning(f"Error usando sistema optimizado: {str(e)}, usando legacy")
        
        # Si estamos en la ruta GPT del conector, actualizar su configuración
        try:
            # Optimizar uso de CPU según reglas de Grupo huntRED
            if PSUTIL_AVAILABLE:
                # Verificar carga actual
                cpu_percent = psutil.cpu_percent(interval=None)
                if cpu_percent > 85:
                    logger.warning(f"Carga de CPU alta: {cpu_percent}%, aplicando limitaciones")
                    # Si la CPU está saturada, usar modelo más ligero o reducir complejidad
                    if hasattr(self, 'config') and 'temperature' in self.config:
                        self.config['temperature'] = max(self.config.get('temperature', 0.7), 0.85)
                        logger.info(f"Temperatura ajustada a {self.config['temperature']} por carga alta")
                        
            # Obtener configuración para GPT handler
            async def process_gpt_response():
                try:
                    response = await self.generate_response(prompt, business_unit=bu)
                    elapsed = time.time() - start_time
                    logger.info(f"Respuesta generada en {elapsed:.2f}s", extra=context)
                    return response
                except Exception as e:
                    logger.error(f"Error generando respuesta: {str(e)}")
                    return "Error: No se pudo generar respuesta."
                    
            return await process_gpt_response()
        except Exception as e:
            logger.error(f"Error en generate_response: {str(e)}")
        
        # Fallback al sistema legacy
        try:
            handler = await self.get_legacy_handler()
            if handler:
                response = await handler.generate_response(prompt, business_unit=bu)
                elapsed = time.time() - start_time
                logger.info(f"Respuesta legacy generada en {elapsed:.2f}s", extra=context)
                return response
            
            return "Error: No se pudo generar respuesta."
        except Exception as e:
            logger.error(f"Error generando respuesta: {str(e)}")
            return f"Lo siento, ocurrió un error al procesar tu solicitud."
    
    def generate_response_sync(self, prompt: str, business_unit=None) -> str:
        """Versión sincrónica para compatibilidad"""
        try:
            return asyncio.run(self.generate_response(prompt, business_unit))
        except Exception as e:
            logger.error(f"Error en generate_response_sync: {str(e)}")
            return "Error generando respuesta."
    
    async def close(self):
        """Cierra conexiones y libera recursos"""
        if self.legacy_handler:
            await self.legacy_handler.close()
            
        # No necesitamos cerrar adaptadores, gestionan su propio ciclo de vida


class OptimizedNLPConnector:
    """
    Conector optimizado para NLP que aprovecha el nuevo procesador
    manteniendo compatibilidad total con la API existente.
    """
    
    def __init__(self, mode: str = "candidate", language: str = "es", analysis_depth: str = "quick"):
        """
        Inicializa el conector NLP con configuración por defecto
        
        Args:
            mode: Modo de análisis (candidate, opportunity)
            language: Idioma principal
            analysis_depth: Profundidad de análisis (quick, deep)
        """
        self.mode = mode
        self.language = language
        self.analysis_depth = analysis_depth
        self.business_unit = None
        self.optimized_available = False
        self.legacy_processor = None
        
        # Verificar si el sistema optimizado está disponible
        asyncio.create_task(self._initialize_processor())
    
    async def _initialize_processor(self):
        """Intenta inicializar el procesador NLP optimizado asíncronamente"""
        try:
            # Importar sistema optimizado
            nlp_processor = await _import_module('app.utils.nlp_processor')
            if nlp_processor:
                self.optimized_available = True
                logger.info("Sistema optimizado de NLP disponible")
        except Exception as e:
            logger.debug(f"Procesador NLP optimizado no disponible: {str(e)}")
            self.optimized_available = False
    
    async def get_legacy_processor(self):
        """Obtiene una instancia del procesador NLP legacy"""
        if self.legacy_processor:
            return self.legacy_processor
        
        try:
            # Ruta correcta al módulo NLP
            nlp_module = await _import_module('app.ats.utils.nlp')
            NLPProcessor = getattr(nlp_module, 'NLPProcessor', None)
            
            if NLPProcessor:
                self.legacy_processor = NLPProcessor(
                    mode=self.mode,
                    language=self.language,
                    analysis_depth=self.analysis_depth
                )
                return self.legacy_processor
            
            logger.error("NLPProcessor no disponible en módulo nlp.py")
            return None
        except Exception as e:
            logger.error(f"Error inicializando legacy NLPProcessor: {str(e)}")
            return None
    
    async def initialize(self, business_unit=None):
        """
        Inicializa el procesador con una business unit específica
        
        Args:
            business_unit: Objeto BusinessUnit para configuración
        """
        self.business_unit = business_unit
        
        if not self.optimized_available:
            # Si el sistema optimizado no está disponible, usar legacy
            await self.get_legacy_processor()
        
        bu_name = getattr(business_unit, 'name', str(business_unit)) if business_unit else None
        logger.info(f"NLPConnector inicializado para BU: {bu_name}")
        return True
    
    async def analyze(self, text: str) -> Dict:
        """
        Analiza un texto usando el sistema optimizado o legacy
        
        Args:
            text: Texto a analizar
            
        Returns:
            Dict con resultados de análisis
        """
        if not text:
            return {
                "skills": {"technical": [], "soft": [], "tools": [], "certifications": []},
                "sentiment": "neutral",
                "metadata": {
                    "original_text": "",
                    "translated_text": "",
                    "detected_language": self.language,
                    "analysis_depth": self.analysis_depth
                }
            }
        
        # Obtener ID de business unit
        bu = self.business_unit
        bu_id = getattr(bu, 'id', None) or getattr(bu, 'name', None)
        
        # Registrar contexto para logs
        context = {
            "business_unit": getattr(bu, 'name', str(bu)) if bu else None,
            "text_length": len(text)
        }
        logger.info(f"Analizando texto NLP", extra=context)
        
        # Medir tiempo de ejecución
        start_time = time.time()
        
        if self.optimized_available:
            try:
                # Intentar usar sistema optimizado
                nlp_processor = await _import_module('app.utils.nlp_processor')
                
                # Analizar texto
                result = await nlp_processor.analyze_text(
                    text=text,
                    business_unit_id=bu_id,
                    language=self.language
                )
                
                elapsed = time.time() - start_time
                logger.info(f"Análisis NLP completado en {elapsed:.2f}s", extra=context)
                return result
                
            except Exception as e:
                # Si falla, usar el sistema legacy
                logger.warning(f"Error usando NLP optimizado: {str(e)}, usando legacy")
        
        # Fallback al sistema legacy
        try:
            processor = await self.get_legacy_processor()
            if processor:
                result = await processor.analyze(text)
                elapsed = time.time() - start_time
                logger.info(f"Análisis NLP legacy completado en {elapsed:.2f}s", extra=context)
                return result
            
            # Si no hay procesador, devolver resultado vacío
            return {
                "skills": {"technical": [], "soft": [], "tools": [], "certifications": []},
                "sentiment": "neutral",
                "metadata": {
                    "original_text": text,
                    "translated_text": text,
                    "detected_language": self.language,
                    "analysis_depth": self.analysis_depth,
                    "error": "Procesador NLP no disponible"
                }
            }
            
        except Exception as e:
            logger.error(f"Error en análisis NLP: {str(e)}")
            return {
                "skills": {"technical": [], "soft": [], "tools": [], "certifications": []},
                "sentiment": "neutral",
                "metadata": {
                    "original_text": text,
                    "translated_text": text,
                    "detected_language": self.language,
                    "analysis_depth": self.analysis_depth,
                    "error": str(e)
                }
            }
    
    def analyze_sync(self, text: str) -> Dict:
        """Versión sincrónica para compatibilidad"""
        try:
            return asyncio.run(self.analyze(text))
        except Exception as e:
            logger.error(f"Error en analyze_sync: {str(e)}")
            return {
                "skills": {"technical": [], "soft": [], "tools": [], "certifications": []},
                "sentiment": "neutral",
                "metadata": {
                    "original_text": text,
                    "translated_text": text,
                    "detected_language": self.language,
                    "analysis_depth": self.analysis_depth,
                    "error": str(e)
                }
            }
    
    async def close(self):
        """Cierra conexiones y libera recursos"""
        if self.legacy_processor:
            # Si el procesador legacy tiene método close, llamarlo
            if hasattr(self.legacy_processor, 'close'):
                await self.legacy_processor.close()


# Función para registrar los conectores optimizados en el sistema de importación
def register_optimized_connectors():
    """
    Registra los conectores optimizados para que sean usados por el sistema
    de importación dinámico get_xxx_handler() en app/import_config.py
    """
    try:
        # Primero verificamos si existe el archivo de importación
        import importlib
        import sys
        
        # Intentar importar el módulo de configuración
        try:
            import_config = importlib.import_module('app.import_config')
            
            # Registrar nuestros conectores
            if hasattr(import_config, 'register_handler'):
                # GPT optimizado
                import_config.register_handler('gpt_handler', 'app.ats.chatbot.optimized_connectors', 'OptimizedGPTConnector')
                logger.info("GPT optimizado registrado")
                
                # NLP optimizado
                import_config.register_handler('nlp_processor', 'app.ats.chatbot.optimized_connectors', 'OptimizedNLPConnector')
                logger.info("NLP optimizado registrado")
                
                return True
        except ImportError:
            logger.debug("Módulo import_config no encontrado")
        
        # Si no existe, monkeypatch del sistema de importación
        import app
        if hasattr(app, 'import_config'):
            # Monkeypatch para get_gpt_handler
            original_get_gpt = getattr(app.import_config, 'get_gpt_handler', None)
            
            def optimized_get_gpt_handler():
                return OptimizedGPTConnector
            
            if original_get_gpt:
                setattr(app.import_config, 'get_gpt_handler', optimized_get_gpt_handler)
                logger.info("Monkeypatch de get_gpt_handler realizado")
            
            # Monkeypatch para get_nlp_processor
            original_get_nlp = getattr(app.import_config, 'get_nlp_processor', None)
            
            def optimized_get_nlp_processor():
                return OptimizedNLPConnector
            
            if original_get_nlp:
                setattr(app.import_config, 'get_nlp_processor', optimized_get_nlp_processor)
                logger.info("Monkeypatch de get_nlp_processor realizado")
                
            return True
            
        return False
    except Exception as e:
        logger.error(f"Error registrando conectores optimizados: {str(e)}")
        return False


# Registrar conectores al importar el módulo
register_optimized_connectors()
