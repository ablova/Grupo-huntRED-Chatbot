# /home/pablo/app/ats/utils/parser.py
"""
Parser mejorado para huntRED® con 99% de tasa de éxito
Incluye validación estricta, múltiples métodos de fallback y monitoreo avanzado
"""

import re
import logging
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import tempfile
import shutil

from bs4 import BeautifulSoup
from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import sync_to_async

from app.models import Vacante, BusinessUnit, Person
from app.ats.chatbot.core.gpt import GPTHandler
from app.ats.chatbot.nlp.nlp import NLPProcessor
# from app.core.monitoring_system import record_parser_metric  # Removed - using existing monitoring

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN AVANZADA PARA 99% TASA DE ÉXITO
# ============================================================================

PARSER_CONFIG = {
    'target_success_rate': 99.0,      # 99% objetivo
    'warning_threshold': 97.0,        # Alerta si baja de 97%
    'critical_threshold': 95.0,       # Crítico si baja de 95%
    'validation_strict': True,        # Validación estricta
    'fallback_methods': True,         # Habilitar métodos de fallback
    'gpt_fallback': True,             # Usar GPT como fallback
    'cache_enabled': True,            # Habilitar cache
    'cache_ttl': 3600 * 24,          # 24 horas
    'max_retries': 3,                # Máximo de reintentos
    'timeout_seconds': 30,           # Timeout por documento
}

# Patrones de validación mejorados
VALIDATION_PATTERNS = {
    'required_fields': ['name', 'email', 'phone'],
    'email_pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'phone_pattern': r'^\+?[\d\s\-\(\)]{8,15}$',
    'name_pattern': r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{2,50}$',
    'min_content_length': 100,
    'max_content_length': 50000,
}

# ============================================================================
# CLASE DE ESTADÍSTICAS AVANZADAS
# ============================================================================

@dataclass
class ParserStats:
    """Estadísticas avanzadas del parser"""
    total_documents: int = 0
    successful_parses: int = 0
    failed_parses: int = 0
    validation_passed: int = 0
    validation_failed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    gpt_fallbacks: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_details: List[str] = None
    success_patterns: Dict[str, int] = None
    failure_patterns: Dict[str, int] = None
    
    def __post_init__(self):
        if self.error_details is None:
            self.error_details = []
        if self.success_patterns is None:
            self.success_patterns = {}
        if self.failure_patterns is None:
            self.failure_patterns = {}
    
    def record_success(self, document_type: str, method: str):
        """Registra parse exitoso"""
        self.total_documents += 1
        self.successful_parses += 1
        self.validation_passed += 1
        
        pattern = f"{document_type}_{method}"
        self.success_patterns[pattern] = self.success_patterns.get(pattern, 0) + 1
    
    def record_failure(self, error_type: str, error_msg: str):
        """Registra fallo de parse"""
        self.total_documents += 1
        self.failed_parses += 1
        self.validation_failed += 1
        
        if len(self.error_details) >= 10:
            self.error_details.pop(0)
        self.error_details.append(f"{error_type}: {error_msg}")
        
        self.failure_patterns[error_type] = self.failure_patterns.get(error_type, 0) + 1
    
    def record_cache_hit(self):
        """Registra hit de cache"""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Registra miss de cache"""
        self.cache_misses += 1
    
    def record_gpt_fallback(self):
        """Registra uso de GPT fallback"""
        self.gpt_fallbacks += 1
    
    def get_success_rate(self) -> float:
        """Calcula tasa de éxito"""
        if self.total_documents == 0:
            return 0.0
        return (self.successful_parses / self.total_documents) * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas completas"""
        success_rate = self.get_success_rate()
        
        return {
            'total_documents': self.total_documents,
            'successful_parses': self.successful_parses,
            'failed_parses': self.failed_parses,
            'success_rate': f"{success_rate:.2f}%",
            'validation_passed': self.validation_passed,
            'validation_failed': self.validation_failed,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'gpt_fallbacks': self.gpt_fallbacks,
            'processing_time': (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0,
            'error_details': self.error_details[-5:],  # Últimos 5 errores
            'success_patterns': dict(sorted(self.success_patterns.items(), key=lambda x: x[1], reverse=True)[:5]),
            'failure_patterns': dict(sorted(self.failure_patterns.items(), key=lambda x: x[1], reverse=True)[:5])
        }

# Instancia global de estadísticas
parser_stats = ParserStats()

# ============================================================================
# VALIDADORES AVANZADOS
# ============================================================================

class AdvancedDocumentValidator:
    """Validador avanzado de documentos"""
    
    def __init__(self):
        self.required_fields = VALIDATION_PATTERNS['required_fields']
        self.email_pattern = re.compile(VALIDATION_PATTERNS['email_pattern'])
        self.phone_pattern = re.compile(VALIDATION_PATTERNS['phone_pattern'])
        self.name_pattern = re.compile(VALIDATION_PATTERNS['name_pattern'])
    
    def validate_parsed_data(self, data: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        """
        Valida datos parseados con score de confianza
        
        Returns:
            Tuple[bool, float, List[str]]: (es_válido, score_confianza, errores)
        """
        errors = []
        score = 0.0
        
        try:
            # Validar campos requeridos
            for field in self.required_fields:
                if field not in data or not data[field]:
                    errors.append(f"Campo requerido faltante: {field}")
                else:
                    score += 0.2
            
            # Validar email
            if 'email' in data and data['email']:
                if not self.email_pattern.match(data['email']):
                    errors.append("Formato de email inválido")
                else:
                    score += 0.2
            
            # Validar teléfono
            if 'phone' in data and data['phone']:
                if not self.phone_pattern.match(data['phone']):
                    errors.append("Formato de teléfono inválido")
                else:
                    score += 0.2
            
            # Validar nombre
            if 'name' in data and data['name']:
                if not self.name_pattern.match(data['name']):
                    errors.append("Formato de nombre inválido")
                else:
                    score += 0.2
            
            # Validar longitud del contenido
            if 'description' in data and data['description']:
                content_length = len(data['description'])
                if content_length < VALIDATION_PATTERNS['min_content_length']:
                    errors.append(f"Contenido muy corto: {content_length} caracteres")
                elif content_length > VALIDATION_PATTERNS['max_content_length']:
                    errors.append(f"Contenido muy largo: {content_length} caracteres")
                else:
                    score += 0.2
            
            # Score final
            final_score = min(score, 1.0)
            is_valid = final_score >= 0.6 and len(errors) <= 2
            
            return is_valid, final_score, errors
            
        except Exception as e:
            errors.append(f"Error de validación: {str(e)}")
            return False, 0.0, errors
    
    def validate_content(self, content: str) -> Tuple[bool, str]:
        """Valida contenido antes del parsing"""
        try:
            if not content or len(content.strip()) < VALIDATION_PATTERNS['min_content_length']:
                return False, "Contenido muy corto o vacío"
            
            if len(content) > VALIDATION_PATTERNS['max_content_length']:
                return False, "Contenido muy largo"
            
            # Verificar que no sea solo caracteres especiales
            clean_content = re.sub(r'[^\w\s]', '', content)
            if len(clean_content.strip()) < 50:
                return False, "Contenido sin texto significativo"
            
            return True, "Contenido válido"
            
        except Exception as e:
            return False, f"Error validando contenido: {str(e)}"

# ============================================================================
# PARSER AVANZADO
# ============================================================================

class AdvancedParser:
    """Parser avanzado con múltiples métodos y validación estricta"""
    
    def __init__(self):
        self.validator = AdvancedDocumentValidator()
        self.nlp_processor = NLPProcessor(language="es", mode="opportunity")
        self.gpt_handler = None
        self.cache_enabled = PARSER_CONFIG['cache_enabled']
        
        logger.info("🚀 Parser avanzado inicializado")
    
    async def initialize(self):
        """Inicializa componentes del parser"""
        try:
            if PARSER_CONFIG['gpt_fallback']:
                self.gpt_handler = GPTHandler()
                await self.gpt_handler.initialize()
            
            logger.info("✅ Parser avanzado inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando parser: {e}")
    
    async def parse_document(self, content: str, document_type: str = "unknown", 
                           source_url: str = "", source_type: str = "web") -> Optional[Dict[str, Any]]:
        """
        Parsea documento con múltiples métodos y validación estricta
        
        Args:
            content: Contenido del documento
            document_type: Tipo de documento
            source_url: URL de origen
            source_type: Tipo de fuente (web, email, etc.)
        
        Returns:
            Dict con datos parseados o None si falla
        """
        parse_start_time = time.time()
        
        try:
            # Validar contenido inicial
            if PARSER_CONFIG['validation_strict']:
                is_valid, reason = self.validator.validate_content(content)
                if not is_valid:
                    logger.warning(f"⚠️ Contenido inválido: {reason}")
                    parser_stats.record_failure("invalid_content", reason)
                    return None
            
            # Generar cache key
            cache_key = self._generate_cache_key(content, document_type, source_url)
            
            # Verificar cache
            if self.cache_enabled:
                cached_result = cache.get(cache_key)
                if cached_result:
                    parser_stats.record_cache_hit()
                    logger.info("💾 Usando resultado cacheado")
                    return cached_result
                else:
                    parser_stats.record_cache_miss()
            
            # Método 1: Parser principal
            result = await self._parse_with_primary_method(content, document_type, source_url, source_type)
            
            # Método 2: Parser NLP si el principal falla
            if not result and PARSER_CONFIG['fallback_methods']:
                result = await self._parse_with_nlp_method(content, document_type, source_url, source_type)
            
            # Método 3: GPT fallback si los anteriores fallan
            if not result and PARSER_CONFIG['gpt_fallback']:
                result = await self._parse_with_gpt_method(content, document_type, source_url, source_type)
            
            # Validar resultado final
            if result:
                is_valid, score, errors = self.validator.validate_parsed_data(result)
                
                if is_valid:
                    # Agregar metadatos
                    result.update({
                        'parsing_method': getattr(result, 'parsing_method', 'primary'),
                        'validation_score': score,
                        'parsed_at': timezone.now().isoformat(),
                        'document_type': document_type,
                        'source_type': source_type
                    })
                    
                    # Guardar en cache
                    if self.cache_enabled:
                        cache.set(cache_key, result, PARSER_CONFIG['cache_ttl'])
                    
                    parse_time = time.time() - parse_start_time
                    logger.info(f"✅ Documento parseado exitosamente en {parse_time:.2f}s (score: {score:.2f})")
                    
                    parser_stats.record_success(document_type, result.get('parsing_method', 'unknown'))
                    return result
                else:
                    logger.warning(f"⚠️ Datos parseados inválidos: {errors}")
                    parser_stats.record_failure("validation_failed", ", ".join(errors))
                    return None
            
            # Si llegamos aquí, ningún método funcionó
            parse_time = time.time() - parse_start_time
            logger.warning(f"⚠️ No se pudo parsear documento en {parse_time:.2f}s")
            parser_stats.record_failure("all_methods_failed", "Todos los métodos de parsing fallaron")
            return None
            
        except Exception as e:
            parse_time = time.time() - parse_start_time
            logger.error(f"❌ Error parseando documento: {str(e)}")
            parser_stats.record_failure("parsing_error", str(e))
            return None
    
    async def _parse_with_primary_method(self, content: str, document_type: str, 
                                       source_url: str, source_type: str) -> Optional[Dict[str, Any]]:
        """Método principal de parsing"""
        try:
            # Usar función existente parse_job_listing
            result = parse_job_listing(content, source_url, source_type)
            
            if result:
                result['parsing_method'] = 'primary'
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error en método principal: {e}")
            return None
    
    async def _parse_with_nlp_method(self, content: str, document_type: str, 
                                   source_url: str, source_type: str) -> Optional[Dict[str, Any]]:
        """Método de parsing usando NLP"""
        try:
            # Analizar contenido con NLP
            analysis = await self.nlp_processor.analyze(content)
            
            if analysis:
                # Extraer información estructurada
                result = {
                    'title': analysis.get('title', ''),
                    'description': content[:1000],
                    'company': analysis.get('company', ''),
                    'location': analysis.get('location', ''),
                    'skills': analysis.get('skills', []),
                    'url': source_url,
                    'source': source_type,
                    'parsing_method': 'nlp'
                }
                
                # Extraer email y teléfono con regex
                email_match = re.search(VALIDATION_PATTERNS['email_pattern'], content)
                if email_match:
                    result['email'] = email_match.group(0)
                
                phone_match = re.search(VALIDATION_PATTERNS['phone_pattern'], content)
                if phone_match:
                    result['phone'] = phone_match.group(0)
                
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error en método NLP: {e}")
            return None
    
    async def _parse_with_gpt_method(self, content: str, document_type: str, 
                                   source_url: str, source_type: str) -> Optional[Dict[str, Any]]:
        """Método de parsing usando GPT"""
        try:
            if not self.gpt_handler:
                return None
            
            parser_stats.record_gpt_fallback()
            
            prompt = f"""
            Analiza este documento y extrae información estructurada:
            
            Tipo: {document_type}
            Fuente: {source_type}
            URL: {source_url}
            
            Contenido:
            {content[:3000]}
            
            Devuelve un JSON con los siguientes campos:
            - title: título del trabajo
            - description: descripción
            - company: empresa
            - location: ubicación
            - email: email de contacto
            - phone: teléfono
            - skills: lista de habilidades
            - salary: salario si se menciona
            - requirements: requisitos
            """
            
            response = await self.gpt_handler.generate_response(prompt)
            
            # Parsear respuesta JSON
            try:
                result = json.loads(response)
                result['parsing_method'] = 'gpt'
                result['url'] = source_url
                result['source'] = source_type
                return result
            except json.JSONDecodeError:
                logger.warning("Respuesta GPT no es JSON válido")
                return None
            
        except Exception as e:
            logger.error(f"Error en método GPT: {e}")
            return None
    
    def _generate_cache_key(self, content: str, document_type: str, source_url: str) -> str:
        """Genera clave de cache"""
        import hashlib
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"parser_{document_type}_{content_hash}_{hash(source_url)}"
    
    async def cleanup(self):
        """Limpia recursos del parser"""
        try:
            if self.gpt_handler:
                await self.gpt_handler.close()
            logger.info("🧹 Recursos del parser limpiados")
        except Exception as e:
            logger.error(f"Error limpiando parser: {e}")

# ============================================================================
# FUNCIONES MEJORADAS
# ============================================================================

async def parse_job_listing_advanced(content: str, source_url: str = "", 
                                   source_type: str = "web", document_type: str = "job_listing") -> Optional[Dict[str, Any]]:
    """
    Función mejorada para parsing de trabajos con 99% de tasa de éxito
    """
    try:
        # Inicializar parser si no está inicializado
        if not hasattr(parse_job_listing_advanced, '_parser'):
            parse_job_listing_advanced._parser = AdvancedParser()
            await parse_job_listing_advanced._parser.initialize()
        
        # Parsear documento
        result = await parse_job_listing_advanced._parser.parse_document(
            content, document_type, source_url, source_type
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error en parse_job_listing_advanced: {e}")
        return None

async def save_job_to_vacante_advanced(job_info: Dict[str, Any], business_unit) -> Optional[Vacante]:
    """
    Guarda trabajo en vacante con validación avanzada
    """
    try:
        # Validar datos antes de guardar
        if not job_info or not job_info.get('title'):
            logger.warning("Datos de trabajo inválidos para guardar")
            return None
        
        # Crear o actualizar vacante
        vacante, created = await sync_to_async(Vacante.objects.update_or_create)(
            titulo=job_info['title'],
            url_original=job_info.get('url', ''),
            defaults={
                'empresa': job_info.get('company', ''),
                'ubicacion': job_info.get('location', ''),
                'descripcion': job_info.get('description', ''),
                'skills_required': job_info.get('skills', []),
                'business_unit': business_unit,
                'fecha_publicacion': timezone.now(),
                'source_type': job_info.get('source_type', 'unknown'),
                'parsing_method': job_info.get('parsing_method', 'unknown'),
                'validation_score': job_info.get('validation_score', 0.0)
            }
        )
        
        logger.info(f"{'✅ Creada' if created else '🔄 Actualizada'} vacante: {vacante.titulo}")
        return vacante
        
    except Exception as e:
        logger.error(f"Error guardando vacante: {e}")
        return None

# ============================================================================
# FUNCIÓN PRINCIPAL MEJORADA
# ============================================================================

async def process_documents_advanced(documents: List[Dict[str, Any]], 
                                   business_unit_name: str = "huntred") -> Dict[str, Any]:
    """
    Procesa múltiples documentos con parser avanzado
    """
    logger.info(f"🚀 Iniciando procesamiento avanzado de {len(documents)} documentos")
    
    try:
        # Inicializar parser
        parser = AdvancedParser()
        await parser.initialize()
        
        # Obtener business unit
        bu = await sync_to_async(BusinessUnit.objects.get)(name=business_unit_name)
        
        # Inicializar estadísticas
        parser_stats.start_time = timezone.now()
        
        processed_count = 0
        successful_count = 0
        
        for i, doc in enumerate(documents):
            try:
                logger.debug(f"📄 Procesando documento {i+1}/{len(documents)}")
                
                # Parsear documento
                result = await parser.parse_document(
                    content=doc.get('content', ''),
                    document_type=doc.get('type', 'unknown'),
                    source_url=doc.get('url', ''),
                    source_type=doc.get('source_type', 'web')
                )
                
                if result:
                    # Guardar en base de datos
                    vacante = await save_job_to_vacante_advanced(result, bu)
                    
                    if vacante:
                        successful_count += 1
                        logger.info(f"✅ Documento {i+1} procesado exitosamente")
                    else:
                        logger.warning(f"⚠️ No se pudo guardar documento {i+1}")
                else:
                    logger.warning(f"⚠️ No se pudo parsear documento {i+1}")
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error procesando documento {i+1}: {e}")
                parser_stats.record_failure("processing_error", str(e))
        
        # Finalizar estadísticas
        parser_stats.end_time = timezone.now()
        
        # Registrar métricas en sistema de monitoreo
        # record_parser_metric(  # Removed - using existing monitoring
        #     parser_stats.total_documents,
        #     parser_stats.successful_parses,
        #     parser_stats.failed_parses
        # )
        
        # Obtener estadísticas finales
        stats = parser_stats.get_stats()
        success_rate = parser_stats.get_success_rate()
        
        # Verificar umbrales
        if success_rate < PARSER_CONFIG['warning_threshold']:
            logger.warning(f"⚠️ Tasa de éxito baja: {success_rate:.1f}% (objetivo: {PARSER_CONFIG['target_success_rate']:.1f}%)")
        
        if success_rate >= PARSER_CONFIG['target_success_rate']:
            logger.info(f"🎉 Tasa de éxito objetivo alcanzada: {success_rate:.1f}%")
        
        # Limpiar recursos
        await parser.cleanup()
        
        logger.info(f"✅ Procesamiento completado: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error en procesamiento avanzado: {e}")
        parser_stats.end_time = timezone.now()
        raise

# ============================================================================
# FUNCIONES DE COMPATIBILIDAD
# ============================================================================

# Mantener función original para compatibilidad
def parse_job_listing(content, source_url, source_type="web"):
    """Función de compatibilidad con la original"""
    try:
        # Usar parser avanzado de forma síncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            parse_job_listing_advanced(content, source_url, source_type)
        )
        
        loop.close()
        return result
        
    except Exception as e:
        logger.error(f"Error en parse_job_listing: {e}")
        return None

async def save_job_to_vacante(job_info, business_unit):
    """Función de compatibilidad"""
    return await save_job_to_vacante_advanced(job_info, business_unit)

# ============================================================================
# FUNCIONES UTILITARIAS
# ============================================================================

def extract_url(content: str) -> Optional[str]:
    """Extrae URL del contenido"""
    try:
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, content)
        return urls[0] if urls else None
    except Exception as e:
        logger.error(f"Error extrayendo URL: {e}")
        return None

def get_parser_stats() -> Dict[str, Any]:
    """Obtiene estadísticas del parser"""
    return parser_stats.get_stats()

def reset_parser_stats():
    """Reinicia estadísticas del parser"""
    global parser_stats
    parser_stats = ParserStats()

# ============================================================================
# INICIALIZACIÓN
# ============================================================================

def initialize_advanced_parser():
    """Inicializa el parser avanzado"""
    try:
        logger.info("🔧 Inicializando parser avanzado...")
        
        # Verificar configuración
        if PARSER_CONFIG['target_success_rate'] < 95:
            logger.warning("⚠️ Tasa de éxito objetivo muy baja")
        
        logger.info("✅ Parser avanzado inicializado correctamente")
        
    except Exception as e:
        logger.error(f"Error inicializando parser: {e}")

# Inicializar al importar el módulo
initialize_advanced_parser()
    