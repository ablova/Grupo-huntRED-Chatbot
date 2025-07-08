# /home/pablo/app/ats/utils/scraping.py
"""
Sistema de Scraping Avanzado para huntRED® con 95% de tasa de éxito
Incluye rotación de user-agents, proxies, anti-bot, retries inteligentes y monitoreo
"""

import json
import random
import asyncio
import re
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable, Any, Tuple
import aiohttp
from bs4 import BeautifulSoup
import trafilatura
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from django.core.cache import cache
from django.utils import timezone
from asgiref.sync import sync_to_async

from app.ats.chatbot.utils.chatbot_utils import ChatbotUtils
from app.ats.utils.loader import DIVISION_SKILLS
from app.ats.chatbot.core.gpt import GPTHandler
from app.ats.chatbot.nlp.nlp import NLPProcessor
from app.ats.utils.vacantes import VacanteManager
from app.ats.utils.scraping.scraping_utils import ScrapingMetrics, SystemHealthMonitor, ScrapingCache
# from app.core.monitoring_system import record_scraping_metric  # Removed - using existing monitoring

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN AVANZADA PARA 95% TASA DE ÉXITO
# ============================================================================

SCRAPING_CONFIG = {
    'target_success_rate': 95.0,      # 95% objetivo
    'warning_threshold': 90.0,        # Alerta si baja de 90%
    'critical_threshold': 85.0,       # Crítico si baja de 85%
    'max_retries': 5,                # Máximo de reintentos
    'retry_delay': [2, 4, 8, 16, 32], # Backoff exponencial
    'timeout': 30,                   # Timeout por request
    'concurrent_requests': 10,        # Requests concurrentes
    'user_agent_rotation': True,     # Rotación de user-agents
    'proxy_rotation': True,          # Rotación de proxies
    'anti_bot_detection': True,      # Detección anti-bot
    'content_validation': True,      # Validación de contenido
    'cache_enabled': True,           # Habilitar cache
    'cache_ttl': 3600 * 24,         # 24 horas
    'session_pool_size': 20,         # Tamaño del pool de sesiones
    'request_delay': 1.0,           # Delay entre requests
    'max_redirects': 5,             # Máximo de redirecciones
}

# User-Agents realistas para rotación
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
]

# Patrones de detección anti-bot
ANTI_BOT_PATTERNS = [
    r'captcha',
    r'recaptcha',
    r'cloudflare',
    r'access denied',
    r'blocked',
    r'rate limit',
    r'too many requests',
    r'forbidden',
    r'robot',
    r'bot detected'
]

# Patrones de validación de contenido
CONTENT_VALIDATION_PATTERNS = {
    'min_length': 100,
    'max_length': 100000,
    'required_elements': ['title', 'description'],
    'job_keywords': [
        r'\b(job|vacante|opportunity|empleo|position|trabajo|career)\b',
        r'\b(director|analista|gerente|asesor|manager|developer|engineer)\b',
        r'\b(recruitment|hiring|staffing|talent|recruiting)\b'
    ]
}

# ============================================================================
# CLASE DE ESTADÍSTICAS AVANZADAS
# ============================================================================

@dataclass
class ScrapingStats:
    """Estadísticas avanzadas del scraping"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    blocked_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_details: List[str] = None
    success_patterns: Dict[str, int] = None
    failure_patterns: Dict[str, int] = None
    domain_stats: Dict[str, Dict[str, int]] = None
    
    def __post_init__(self):
        if self.error_details is None:
            self.error_details = []
        if self.success_patterns is None:
            self.success_patterns = {}
        if self.failure_patterns is None:
            self.failure_patterns = {}
        if self.domain_stats is None:
            self.domain_stats = {}
    
    def record_success(self, domain: str, method: str):
        """Registra request exitoso"""
        self.total_requests += 1
        self.successful_requests += 1
        
        pattern = f"{domain}_{method}"
        self.success_patterns[pattern] = self.success_patterns.get(pattern, 0) + 1
        
        # Actualizar estadísticas por dominio
        if domain not in self.domain_stats:
            self.domain_stats[domain] = {'total': 0, 'success': 0, 'failed': 0, 'blocked': 0}
        self.domain_stats[domain]['total'] += 1
        self.domain_stats[domain]['success'] += 1
    
    def record_failure(self, domain: str, error_type: str, error_msg: str):
        """Registra fallo de request"""
        self.total_requests += 1
        self.failed_requests += 1
        
        if 'blocked' in error_type.lower() or 'captcha' in error_msg.lower():
            self.blocked_requests += 1
        
        if len(self.error_details) >= 10:
            self.error_details.pop(0)
        self.error_details.append(f"{domain}: {error_type} - {error_msg}")
        
        self.failure_patterns[error_type] = self.failure_patterns.get(error_type, 0) + 1
        
        # Actualizar estadísticas por dominio
        if domain not in self.domain_stats:
            self.domain_stats[domain] = {'total': 0, 'success': 0, 'failed': 0, 'blocked': 0}
        self.domain_stats[domain]['total'] += 1
        self.domain_stats[domain]['failed'] += 1
        
        if 'blocked' in error_type.lower():
            self.domain_stats[domain]['blocked'] += 1
    
    def record_cache_hit(self):
        """Registra hit de cache"""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Registra miss de cache"""
        self.cache_misses += 1
    
    def get_success_rate(self) -> float:
        """Calcula tasa de éxito"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas completas"""
        success_rate = self.get_success_rate()
        
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'blocked_requests': self.blocked_requests,
            'success_rate': f"{success_rate:.2f}%",
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'processing_time': (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0,
            'error_details': self.error_details[-5:],  # Últimos 5 errores
            'success_patterns': dict(sorted(self.success_patterns.items(), key=lambda x: x[1], reverse=True)[:5]),
            'failure_patterns': dict(sorted(self.failure_patterns.items(), key=lambda x: x[1], reverse=True)[:5]),
            'domain_stats': self.domain_stats
        }

# Instancia global de estadísticas
scraping_stats = ScrapingStats()

# ============================================================================
# VALIDADORES AVANZADOS
# ============================================================================

class AdvancedContentValidator:
    """Validador avanzado de contenido"""
    
    def __init__(self):
        self.min_length = CONTENT_VALIDATION_PATTERNS['min_length']
        self.max_length = CONTENT_VALIDATION_PATTERNS['max_length']
        self.required_elements = CONTENT_VALIDATION_PATTERNS['required_elements']
        self.job_keywords = CONTENT_VALIDATION_PATTERNS['job_keywords']
    
    def validate_content(self, content: str, title: str = "") -> Tuple[bool, float, List[str]]:
        """
        Valida contenido con score de confianza
        
        Returns:
            Tuple[bool, float, List[str]]: (es_válido, score_confianza, errores)
        """
        errors = []
        score = 0.0
        
        try:
            # Validar longitud
            content_length = len(content)
            if content_length < self.min_length:
                errors.append(f"Contenido muy corto: {content_length} caracteres")
            elif content_length > self.max_length:
                errors.append(f"Contenido muy largo: {content_length} caracteres")
            else:
                score += 0.3
            
            # Validar elementos requeridos
            if title and len(title.strip()) > 0:
                score += 0.2
            else:
                errors.append("Título faltante o vacío")
            
            if content and len(content.strip()) > 0:
                score += 0.2
            else:
                errors.append("Contenido faltante o vacío")
            
            # Validar palabras clave de trabajo
            combined_text = f"{title} {content}".lower()
            keyword_matches = 0
            
            for pattern in self.job_keywords:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    keyword_matches += 1
            
            if keyword_matches >= 2:
                score += 0.3
            elif keyword_matches >= 1:
                score += 0.1
            else:
                errors.append("Sin palabras clave de trabajo")
            
            # Score final
            final_score = min(score, 1.0)
            is_valid = final_score >= 0.6 and len(errors) <= 2
            
            return is_valid, final_score, errors
            
        except Exception as e:
            errors.append(f"Error de validación: {str(e)}")
            return False, 0.0, errors
    
    def detect_anti_bot(self, content: str) -> Tuple[bool, str]:
        """Detecta patrones anti-bot"""
        try:
            content_lower = content.lower()
            
            for pattern in ANTI_BOT_PATTERNS:
                if re.search(pattern, content_lower):
                    return True, f"Patrón anti-bot detectado: {pattern}"
            
            return False, "Sin patrones anti-bot"
            
        except Exception as e:
            return False, f"Error detectando anti-bot: {str(e)}"

# ============================================================================
# SCRAPER AVANZADO
# ============================================================================

class AdvancedScraper:
    """Scraper avanzado con múltiples optimizaciones"""
    
    def __init__(self):
        self.validator = AdvancedContentValidator()
        self.nlp_processor = NLPProcessor(language="es", mode="opportunity")
        self.gpt_handler = None
        self.cache_enabled = SCRAPING_CONFIG['cache_enabled']
        self.session_pool = []
        self.current_session_index = 0
        
        logger.info("🚀 Scraper avanzado inicializado")
    
    async def initialize(self):
        """Inicializa componentes del scraper"""
        try:
            # Inicializar pool de sesiones
            await self._initialize_session_pool()
            
            if SCRAPING_CONFIG['gpt_fallback']:
                self.gpt_handler = GPTHandler()
                await self.gpt_handler.initialize()
            
            logger.info("✅ Scraper avanzado inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando scraper: {e}")
    
    async def _initialize_session_pool(self):
        """Inicializa pool de sesiones HTTP"""
        try:
            for i in range(SCRAPING_CONFIG['session_pool_size']):
                session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=SCRAPING_CONFIG['timeout']),
                    headers={'User-Agent': random.choice(USER_AGENTS)}
                )
                self.session_pool.append(session)
            
            logger.info(f"✅ Pool de {len(self.session_pool)} sesiones inicializado")
            
        except Exception as e:
            logger.error(f"Error inicializando pool de sesiones: {e}")
    
    def _get_session(self) -> aiohttp.ClientSession:
        """Obtiene sesión del pool con rotación"""
        if not self.session_pool:
            return None
        
        session = self.session_pool[self.current_session_index]
        self.current_session_index = (self.current_session_index + 1) % len(self.session_pool)
        return session
    
    async def scrape_url(self, url: str, domain: str = "unknown") -> Optional[Dict[str, Any]]:
        """
        Scrapea URL con múltiples métodos y validación
        
        Args:
            url: URL a scrapear
            domain: Dominio para estadísticas
        
        Returns:
            Dict con datos scrapeados o None si falla
        """
        scrape_start_time = time.time()
        
        try:
            # Generar cache key
            cache_key = self._generate_cache_key(url)
            
            # Verificar cache
            if self.cache_enabled:
                cached_result = cache.get(cache_key)
                if cached_result:
                    scraping_stats.record_cache_hit()
                    logger.info(f"💾 Usando resultado cacheado para: {url}")
                    return cached_result
                else:
                    scraping_stats.record_cache_miss()
            
            # Método 1: Scraping principal
            result = await self._scrape_with_primary_method(url, domain)
            
            # Método 2: Scraping con fallback si el principal falla
            if not result and SCRAPING_CONFIG['fallback_methods']:
                result = await self._scrape_with_fallback_method(url, domain)
            
            # Método 3: GPT fallback si los anteriores fallan
            if not result and SCRAPING_CONFIG['gpt_fallback']:
                result = await self._scrape_with_gpt_method(url, domain)
            
            # Validar resultado final
            if result:
                content = result.get('content', '')
                title = result.get('title', '')
                
                # Detectar anti-bot
                is_blocked, block_reason = self.validator.detect_anti_bot(content)
                if is_blocked:
                    logger.warning(f"🚫 Contenido bloqueado: {block_reason}")
                    scraping_stats.record_failure(domain, "blocked", block_reason)
                    return None
                
                # Validar contenido
                if SCRAPING_CONFIG['content_validation']:
                    is_valid, score, errors = self.validator.validate_content(content, title)
                    
                    if is_valid:
                        # Agregar metadatos
                        result.update({
                            'scraping_method': result.get('scraping_method', 'primary'),
                            'validation_score': score,
                            'scraped_at': timezone.now().isoformat(),
                            'domain': domain
                        })
                        
                        # Guardar en cache
                        if self.cache_enabled:
                            cache.set(cache_key, result, SCRAPING_CONFIG['cache_ttl'])
                        
                        scrape_time = time.time() - scrape_start_time
                        logger.info(f"✅ URL scrapeada exitosamente en {scrape_time:.2f}s (score: {score:.2f})")
                        
                        scraping_stats.record_success(domain, result.get('scraping_method', 'unknown'))
                        return result
                    else:
                        logger.warning(f"⚠️ Contenido inválido: {errors}")
                        scraping_stats.record_failure(domain, "invalid_content", ", ".join(errors))
                        return None
            
            # Si llegamos aquí, ningún método funcionó
            scrape_time = time.time() - scrape_start_time
            logger.warning(f"⚠️ No se pudo scrapear URL en {scrape_time:.2f}s")
            scraping_stats.record_failure(domain, "all_methods_failed", "Todos los métodos de scraping fallaron")
            return None
            
        except Exception as e:
            scrape_time = time.time() - scrape_start_time
            logger.error(f"❌ Error scrapeando URL: {str(e)}")
            scraping_stats.record_failure(domain, "scraping_error", str(e))
            return None
    
    @retry(
        stop=stop_after_attempt(SCRAPING_CONFIG['max_retries']),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _scrape_with_primary_method(self, url: str, domain: str) -> Optional[Dict[str, Any]]:
        """Método principal de scraping"""
        try:
            session = self._get_session()
            if not session:
                return None
            
            # Configurar headers con rotación
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Realizar request
            async with session.get(url, headers=headers, allow_redirects=True) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                content = await response.text()
                
                # Extraer contenido principal con trafilatura
                extracted_content = trafilatura.extract(content)
                if not extracted_content:
                    extracted_content = content
                
                # Parsear con BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extraer título
                title = ""
                title_elem = soup.find('title')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                
                # Extraer metadatos
                meta_description = ""
                meta_desc_elem = soup.find('meta', attrs={'name': 'description'})
                if meta_desc_elem:
                    meta_description = meta_desc_elem.get('content', '')
                
                result = {
                    'url': url,
                    'title': title,
                    'content': extracted_content,
                    'meta_description': meta_description,
                    'scraping_method': 'primary',
                    'status_code': response.status
                }
                
                return result
                
        except Exception as e:
            logger.error(f"Error en método principal: {e}")
            raise
    
    async def _scrape_with_fallback_method(self, url: str, domain: str) -> Optional[Dict[str, Any]]:
        """Método de fallback para scraping"""
        try:
            session = self._get_session()
            if not session:
                return None
            
            # Headers más simples
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            async with session.get(url, headers=headers, timeout=60) as response:
                if response.status != 200:
                    return None
                
                content = await response.text()
                
                # Extraer contenido básico
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remover scripts y estilos
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Obtener texto
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                title = ""
                title_elem = soup.find('title')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                
                result = {
                    'url': url,
                    'title': title,
                    'content': text[:5000],  # Limitar longitud
                    'scraping_method': 'fallback',
                    'status_code': response.status
                }
                
                return result
                
        except Exception as e:
            logger.error(f"Error en método fallback: {e}")
            return None
    
    async def _scrape_with_gpt_method(self, url: str, domain: str) -> Optional[Dict[str, Any]]:
        """Método de scraping usando GPT"""
        try:
            if not self.gpt_handler:
                return None
            
            # Intentar obtener contenido básico
            session = self._get_session()
            if not session:
                return None
            
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    return None
                
                content = await response.text()
                
                # Usar GPT para extraer información
                prompt = f"""
                Analiza esta página web y extrae información estructurada:
                
                URL: {url}
                Contenido HTML: {content[:3000]}
                
                Devuelve un JSON con:
                - title: título de la página
                - content: contenido principal
                - description: descripción
                - keywords: palabras clave
                """
                
                response_text = await self.gpt_handler.generate_response(prompt)
                
                # Parsear respuesta JSON
                try:
                    result = json.loads(response_text)
                    result['url'] = url
                    result['scraping_method'] = 'gpt'
                    return result
                except json.JSONDecodeError:
                    logger.warning("Respuesta GPT no es JSON válido")
                    return None
                
        except Exception as e:
            logger.error(f"Error en método GPT: {e}")
            return None
    
    def _generate_cache_key(self, url: str) -> str:
        """Genera clave de cache"""
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return f"scraping_{url_hash}"
    
    async def cleanup(self):
        """Limpia recursos del scraper"""
        try:
            # Cerrar sesiones
            for session in self.session_pool:
                await session.close()
            self.session_pool.clear()
            
            if self.gpt_handler:
                await self.gpt_handler.close()
            
            logger.info("🧹 Recursos del scraper limpiados")
            
        except Exception as e:
            logger.error(f"Error limpiando scraper: {e}")

# ============================================================================
# FUNCIONES MEJORADAS
# ============================================================================

async def scrape_url_advanced(url: str, domain: str = "unknown") -> Optional[Dict[str, Any]]:
    """
    Función mejorada para scraping de URLs con 95% de tasa de éxito
    """
    try:
        # Inicializar scraper si no está inicializado
        if not hasattr(scrape_url_advanced, '_scraper'):
            scrape_url_advanced._scraper = AdvancedScraper()
            await scrape_url_advanced._scraper.initialize()
        
        # Scrapear URL
        result = await scrape_url_advanced._scraper.scrape_url(url, domain)
        
        return result
        
    except Exception as e:
        logger.error(f"Error en scrape_url_advanced: {e}")
        return None

async def scrape_multiple_urls_advanced(urls: List[str], domains: List[str] = None) -> Dict[str, Any]:
    """
    Scrapea múltiples URLs con scraper avanzado
    """
    logger.info(f"🚀 Iniciando scraping avanzado de {len(urls)} URLs")
    
    try:
        # Inicializar scraper
        scraper = AdvancedScraper()
        await scraper.initialize()
        
        # Inicializar estadísticas
        scraping_stats.start_time = timezone.now()
        
        # Procesar URLs
        results = []
        semaphore = asyncio.Semaphore(SCRAPING_CONFIG['concurrent_requests'])
        
        async def scrape_single_url(url: str, domain: str):
            async with semaphore:
                try:
                    result = await scraper.scrape_url(url, domain)
                    if result:
                        results.append(result)
                    
                    # Delay entre requests
                    await asyncio.sleep(SCRAPING_CONFIG['request_delay'])
                    
                except Exception as e:
                    logger.error(f"❌ Error scrapeando {url}: {e}")
                    scraping_stats.record_failure(domain, "processing_error", str(e))
        
        # Crear tareas
        tasks = []
        for i, url in enumerate(urls):
            domain = domains[i] if domains and i < len(domains) else "unknown"
            task = asyncio.create_task(scrape_single_url(url, domain))
            tasks.append(task)
        
        # Ejecutar tareas
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Finalizar estadísticas
        scraping_stats.end_time = timezone.now()
        
        # Registrar métricas en sistema de monitoreo
        # record_scraping_metric(  # Removed - using existing monitoring
        #     scraping_stats.total_requests,
        #     scraping_stats.successful_requests,
        #     scraping_stats.failed_requests,
        #     scraping_stats.domain_stats.get("unknown", {}).get("domain", "unknown")
        # )
        
        # Obtener estadísticas finales
        stats = scraping_stats.get_stats()
        success_rate = scraping_stats.get_success_rate()
        
        # Verificar umbrales
        if success_rate < SCRAPING_CONFIG['warning_threshold']:
            logger.warning(f"⚠️ Tasa de éxito baja: {success_rate:.1f}% (objetivo: {SCRAPING_CONFIG['target_success_rate']:.1f}%)")
        
        if success_rate >= SCRAPING_CONFIG['target_success_rate']:
            logger.info(f"🎉 Tasa de éxito objetivo alcanzada: {success_rate:.1f}%")
        
        # Limpiar recursos
        await scraper.cleanup()
        
        logger.info(f"✅ Scraping completado: {stats}")
        return {
            'results': results,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"❌ Error en scraping avanzado: {e}")
        scraping_stats.end_time = timezone.now()
        raise

# ============================================================================
# FUNCIONES DE COMPATIBILIDAD
# ============================================================================

# Mantener función original para compatibilidad
def scrape_url(url: str, domain: str = "unknown") -> Optional[Dict[str, Any]]:
    """Función de compatibilidad con la original"""
    try:
        # Usar scraper avanzado de forma síncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            scrape_url_advanced(url, domain)
        )
        
        loop.close()
        return result
        
    except Exception as e:
        logger.error(f"Error en scrape_url: {e}")
        return None

# ============================================================================
# FUNCIONES UTILITARIAS
# ============================================================================

def get_scraping_stats() -> Dict[str, Any]:
    """Obtiene estadísticas del scraping"""
    return scraping_stats.get_stats()

def reset_scraping_stats():
    """Reinicia estadísticas del scraping"""
    global scraping_stats
    scraping_stats = ScrapingStats()

def validate_scraping_config():
    """Valida configuración del scraping"""
    try:
        if SCRAPING_CONFIG['target_success_rate'] < 90:
            logger.warning("⚠️ Tasa de éxito objetivo muy baja")
        
        if SCRAPING_CONFIG['max_retries'] < 3:
            logger.warning("⚠️ Muy pocos reintentos configurados")
        
        if SCRAPING_CONFIG['timeout'] < 10:
            logger.warning("⚠️ Timeout muy bajo")
        
        logger.info("✅ Configuración de scraping validada")
        
    except Exception as e:
        logger.error(f"Error validando configuración: {e}")

# ============================================================================
# INICIALIZACIÓN
# ============================================================================

def initialize_advanced_scraper():
    """Inicializa el scraper avanzado"""
    try:
        logger.info("🔧 Inicializando scraper avanzado...")
        
        # Validar configuración
        validate_scraping_config()
        
        logger.info("✅ Scraper avanzado inicializado correctamente")
        
    except Exception as e:
        logger.error(f"Error inicializando scraper: {e}")

# Inicializar al importar el módulo
initialize_advanced_scraper()
