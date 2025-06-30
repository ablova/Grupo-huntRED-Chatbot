"""
SISTEMA DE SCRAPING ROBUSTO - Grupo huntRED®
Sistema a prueba de fallos para LinkedIn, Workday, Indeed y otras plataformas
"""

import asyncio
import time
import random
import logging
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
from pathlib import Path

import aiohttp
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

# Importar USER_AGENTS existentes
from app.models import USER_AGENTS

logger = logging.getLogger(__name__)

@dataclass
class ScrapingConfig:
    """Configuración de scraping por plataforma"""
    platform: str
    max_retries: int = 3
    timeout: int = 30
    delay_between_requests: float = 2.0
    max_concurrent: int = 2
    use_proxy: bool = False
    rotate_user_agents: bool = True
    enable_anti_detection: bool = True
    cache_duration: int = 3600  # 1 hora
    rate_limit_requests: int = 20
    rate_limit_period: int = 60  # segundos

@dataclass
class ScrapingResult:
    """Resultado de scraping"""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    platform: Optional[str] = None
    url: Optional[str] = None
    timestamp: datetime = field(default_factory=timezone.now)
    retry_count: int = 0
    response_time: float = 0.0

class RobustScrapingSystem:
    """
    Sistema de scraping robusto con múltiples fallbacks y anti-detección
    """
    
    def __init__(self):
        self.configs = self._initialize_configs()
        self.session_cache = {}
        self.proxy_pool = self._load_proxy_pool()
        self.user_agents = USER_AGENTS  # Usar USER_AGENTS existentes
        self.rate_limiters = {}
        self.browser_pool = {}
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'blocked_requests': 0,
            'cache_hits': 0
        }
        
    def _initialize_configs(self) -> Dict[str, ScrapingConfig]:
        """Inicializa configuración de assets centralizados"""
        return {
            'linkedin': ScrapingConfig(
                platform='linkedin',
                max_retries=5,
                timeout=45,
                delay_between_requests=3.0,
                max_concurrent=1,  # LinkedIn es muy sensible
                use_proxy=True,
                rotate_user_agents=True,
                enable_anti_detection=True,
                rate_limit_requests=15,
                rate_limit_period=60
            ),
            'workday': ScrapingConfig(
                platform='workday',
                max_retries=3,
                timeout=30,
                delay_between_requests=2.0,
                max_concurrent=2,
                use_proxy=False,
                rotate_user_agents=True,
                enable_anti_detection=True,
                rate_limit_requests=20,
                rate_limit_period=60
            ),
            'indeed': ScrapingConfig(
                platform='indeed',
                max_retries=3,
                timeout=30,
                delay_between_requests=1.5,
                max_concurrent=3,
                use_proxy=False,
                rotate_user_agents=True,
                enable_anti_detection=True,
                rate_limit_requests=25,
                rate_limit_period=60
            ),
            'glassdoor': ScrapingConfig(
                platform='glassdoor',
                max_retries=3,
                timeout=30,
                delay_between_requests=2.0,
                max_concurrent=2,
                use_proxy=False,
                rotate_user_agents=True,
                enable_anti_detection=True,
                rate_limit_requests=20,
                rate_limit_period=60
            ),
            'default': ScrapingConfig(
                platform='default',
                max_retries=3,
                timeout=30,
                delay_between_requests=2.0,
                max_concurrent=2,
                use_proxy=False,
                rotate_user_agents=True,
                enable_anti_detection=True,
                rate_limit_requests=20,
                rate_limit_period=60
            )
        }
    
    def _load_proxy_pool(self) -> List[str]:
        """Carga pool de proxies"""
        try:
            proxy_file = Path(settings.BASE_DIR) / 'config' / 'proxies.txt'
            if proxy_file.exists():
                with open(proxy_file, 'r') as f:
                    return [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.warning(f"No se pudo cargar pool de proxies: {e}")
        
        return []
    
    def _get_platform_from_url(self, url: str) -> str:
        """Determina la plataforma desde la URL"""
        domain = urlparse(url).netloc.lower()
        
        if 'linkedin.com' in domain:
            return 'linkedin'
        elif 'workday.com' in domain or 'myworkdayjobs.com' in domain:
            return 'workday'
        elif 'indeed.com' in domain:
            return 'indeed'
        elif 'glassdoor.com' in domain:
            return 'glassdoor'
        else:
            return 'default'
    
    def _get_cache_key(self, url: str, platform: str) -> str:
        """Genera clave de cache"""
        return f"scraping:{platform}:{hashlib.md5(url.encode()).hexdigest()}"
    
    def _get_from_cache(self, url: str, platform: str) -> Optional[Dict]:
        """Obtiene datos del cache"""
        cache_key = self._get_cache_key(url, platform)
        cached_data = cache.get(cache_key)
        
        if cached_data:
            self.stats['cache_hits'] += 1
            logger.info(f"Cache hit para {url}")
            return cached_data
        
        return None
    
    def _save_to_cache(self, url: str, platform: str, data: Dict) -> None:
        """Guarda datos en cache"""
        cache_key = self._get_cache_key(url, platform)
        config = self.configs[platform]
        cache.set(cache_key, data, config.cache_duration)
    
    async def _rate_limit_acquire(self, platform: str) -> None:
        """Adquiere permiso de rate limiting"""
        if platform not in self.rate_limiters:
            config = self.configs[platform]
            self.rate_limiters[platform] = {
                'requests': [],
                'limit': config.rate_limit_requests,
                'period': config.rate_limit_period
            }
        
        limiter = self.rate_limiters[platform]
        now = time.time()
        
        # Limpiar requests antiguos
        limiter['requests'] = [req_time for req_time in limiter['requests'] 
                             if now - req_time < limiter['period']]
        
        # Si excede el límite, esperar
        if len(limiter['requests']) >= limiter['limit']:
            oldest_request = limiter['requests'][0]
            wait_time = limiter['period'] - (now - oldest_request)
            if wait_time > 0:
                logger.info(f"Rate limit alcanzado para {platform}, esperando {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                # Limpiar después de esperar
                limiter['requests'] = [req_time for req_time in limiter['requests'] 
                                     if now - req_time < limiter['period']]
        
        limiter['requests'].append(now)
    
    async def _get_browser_session(self, platform: str) -> Tuple[Browser, BrowserContext, Page]:
        """Obtiene sesión de browser con configuración anti-detección"""
        if platform in self.browser_pool:
            return self.browser_pool[platform]
        
        config = self.configs[platform]
        
        # Inicializar Playwright
        playwright = await async_playwright().start()
        
        # Configuración del browser
        browser_options = {
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Cargar sin imágenes para velocidad
                '--disable-javascript',  # Opcional: deshabilitar JS si no es necesario
                '--disable-gpu',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-field-trial-config',
                '--disable-ipc-flooding-protection'
            ]
        }
        
        if config.use_proxy and self.proxy_pool:
            proxy = random.choice(self.proxy_pool)
            browser_options['proxy'] = {
                'server': proxy,
                'username': settings.PROXY_USERNAME if hasattr(settings, 'PROXY_USERNAME') else None,
                'password': settings.PROXY_PASSWORD if hasattr(settings, 'PROXY_PASSWORD') else None
            }
        
        browser = await playwright.chromium.launch(**browser_options)
        
        # Configuración del contexto
        context_options = {
            'user_agent': random.choice(self.user_agents) if config.rotate_user_agents else self.user_agents[0],
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'es-ES',
            'timezone_id': 'America/Mexico_City',
            'permissions': ['geolocation'],  # Simular permisos reales
            'extra_http_headers': {
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
        }
        
        context = await browser.new_context(**context_options)
        
        # Configurar anti-detección
        if config.enable_anti_detection:
            await self._setup_anti_detection(context)
        
        page = await context.new_page()
        
        # Configurar timeouts
        page.set_default_timeout(config.timeout * 1000)
        
        session = (browser, context, page)
        self.browser_pool[platform] = session
        
        return session
    
    async def _setup_anti_detection(self, context: BrowserContext) -> None:
        """Configura anti-detección avanzado"""
        # Inyectar script para ocultar webdriver y automation
        await context.add_init_script("""
            // Ocultar webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Simular plugins reales
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Simular permisos
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: async () => ({ state: 'granted' })
                }),
            });
            
            // Ocultar automation
            Object.defineProperty(navigator, 'languages', {
                get: () => ['es-ES', 'es', 'en-US', 'en'],
            });
            
            // Simular hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
            });
            
            // Simular device memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
            });
            
            // Ocultar chrome
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Simular permisos de notificaciones
            if ('Notification' in window) {
                Object.defineProperty(Notification, 'permission', {
                    get: () => 'granted',
                });
            }
            
            // Ocultar automation en window
            Object.defineProperty(window, 'navigator', {
                get: () => ({
                    ...navigator,
                    webdriver: undefined,
                    plugins: [1, 2, 3, 4, 5],
                    languages: ['es-ES', 'es', 'en-US', 'en'],
                    hardwareConcurrency: 8,
                    deviceMemory: 8
                }),
            });
        """)
    
    async def _simulate_human_behavior(self, page: Page) -> None:
        """Simula comportamiento humano avanzado"""
        try:
            # Scroll aleatorio más natural
            await page.evaluate("""
                () => {
                    const scrollHeight = document.body.scrollHeight;
                    const viewportHeight = window.innerHeight;
                    const scrollSteps = Math.floor(scrollHeight / viewportHeight);
                    
                    // Scroll con pausas naturales
                    for (let i = 0; i < scrollSteps; i++) {
                        setTimeout(() => {
                            const targetY = i * viewportHeight + Math.random() * 200;
                            window.scrollTo({
                                top: targetY,
                                behavior: 'smooth'
                            });
                        }, i * 150 + Math.random() * 100);
                    }
                }
            """)
            
            # Esperar tiempo aleatorio
            await asyncio.sleep(random.uniform(2, 4))
            
            # Mover mouse de forma natural
            await page.mouse.move(
                random.randint(100, 800),
                random.randint(100, 600)
            )
            
            # Simular clicks aleatorios (opcional)
            if random.random() < 0.3:  # 30% de probabilidad
                await page.mouse.click(
                    random.randint(200, 700),
                    random.randint(200, 500)
                )
            
            # Simular teclas (opcional)
            if random.random() < 0.2:  # 20% de probabilidad
                await page.keyboard.press('PageDown')
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await page.keyboard.press('PageUp')
            
        except Exception as e:
            logger.warning(f"Error en simulación de comportamiento humano: {e}")
    
    async def scrape_with_playwright(self, url: str, platform: str) -> ScrapingResult:
        """Scraping usando Playwright con optimizaciones"""
        start_time = time.time()
        config = self.configs[platform]
        
        try:
            # Rate limiting
            await self._rate_limit_acquire(platform)
            
            # Obtener sesión de browser
            browser, context, page = await self._get_browser_session(platform)
            
            # Navegar a la URL
            logger.info(f"Scraping {url} con Playwright")
            
            # Configurar headers adicionales
            await page.set_extra_http_headers({
                'Referer': 'https://www.google.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            })
            
            response = await page.goto(url, wait_until='domcontentloaded')
            
            if not response or response.status >= 400:
                raise Exception(f"HTTP {response.status if response else 'No response'}")
            
            # Simular comportamiento humano
            await self._simulate_human_behavior(page)
            
            # Extraer contenido
            content = await page.content()
            
            # Parsear contenido
            data = await self._parse_content(content, url, platform)
            
            response_time = time.time() - start_time
            
            # Guardar en cache
            self._save_to_cache(url, platform, data)
            
            self.stats['successful_requests'] += 1
            
            return ScrapingResult(
                success=True,
                data=data,
                platform=platform,
                url=url,
                response_time=response_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.stats['failed_requests'] += 1
            
            logger.error(f"Error scraping {url} con Playwright: {e}")
            
            return ScrapingResult(
                success=False,
                error=str(e),
                platform=platform,
                url=url,
                response_time=response_time
            )
    
    async def scrape_with_selenium(self, url: str, platform: str) -> ScrapingResult:
        """Scraping usando Selenium como fallback optimizado"""
        start_time = time.time()
        config = self.configs[platform]
        
        driver = None
        try:
            # Rate limiting
            await self._rate_limit_acquire(platform)
            
            # Configurar Chrome con optimizaciones
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument(f'--user-agent={random.choice(self.user_agents)}')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-field-trial-config')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            
            # Configurar preferencias
            chrome_options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 2
            })
            
            if config.use_proxy and self.proxy_pool:
                proxy = random.choice(self.proxy_pool)
                chrome_options.add_argument(f'--proxy-server={proxy}')
            
            # Inicializar driver
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(config.timeout)
            
            # Configurar window size
            driver.set_window_size(1920, 1080)
            
            # Navegar a la URL
            logger.info(f"Scraping {url} con Selenium")
            driver.get(url)
            
            # Esperar a que cargue
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Simular scroll natural
            driver.execute_script("""
                const scrollHeight = document.body.scrollHeight;
                const viewportHeight = window.innerHeight;
                const scrollSteps = Math.floor(scrollHeight / viewportHeight);
                
                for (let i = 0; i < scrollSteps; i++) {
                    setTimeout(() => {
                        const targetY = i * viewportHeight + Math.random() * 200;
                        window.scrollTo({
                            top: targetY,
                            behavior: 'smooth'
                        });
                    }, i * 150 + Math.random() * 100);
                }
            """)
            
            time.sleep(random.uniform(2, 4))
            
            # Obtener contenido
            content = driver.page_source
            
            # Parsear contenido
            data = await self._parse_content(content, url, platform)
            
            response_time = time.time() - start_time
            
            # Guardar en cache
            self._save_to_cache(url, platform, data)
            
            self.stats['successful_requests'] += 1
            
            return ScrapingResult(
                success=True,
                data=data,
                platform=platform,
                url=url,
                response_time=response_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.stats['failed_requests'] += 1
            
            logger.error(f"Error scraping {url} con Selenium: {e}")
            
            return ScrapingResult(
                success=False,
                error=str(e),
                platform=platform,
                url=url,
                response_time=response_time
            )
            
        finally:
            if driver:
                driver.quit()
    
    async def scrape_with_requests(self, url: str, platform: str) -> ScrapingResult:
        """Scraping usando requests como último fallback optimizado"""
        start_time = time.time()
        config = self.configs[platform]
        
        try:
            # Rate limiting
            await self._rate_limit_acquire(platform)
            
            # Configurar headers realistas
            headers = {
                'User-Agent': random.choice(self.user_agents) if config.rotate_user_agents else self.user_agents[0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'Referer': 'https://www.google.com/'
            }
            
            # Configurar proxies
            proxies = None
            if config.use_proxy and self.proxy_pool:
                proxy = random.choice(self.proxy_pool)
                proxies = {
                    'http': f'http://{proxy}',
                    'https': f'http://{proxy}'
                }
            
            # Configurar session con retry
            session = requests.Session()
            session.headers.update(headers)
            
            # Configurar adapters para retry
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Hacer request
            logger.info(f"Scraping {url} con Requests")
            
            response = session.get(
                url, 
                proxies=proxies,
                timeout=config.timeout,
                allow_redirects=True
            )
            
            if response.status_code >= 400:
                raise Exception(f"HTTP {response.status_code}")
            
            content = response.text
            
            # Parsear contenido
            data = await self._parse_content(content, url, platform)
            
            response_time = time.time() - start_time
            
            # Guardar en cache
            self._save_to_cache(url, platform, data)
            
            self.stats['successful_requests'] += 1
            
            return ScrapingResult(
                success=True,
                data=data,
                platform=platform,
                url=url,
                response_time=response_time
            )
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.stats['failed_requests'] += 1
            
            logger.error(f"Error scraping {url} con Requests: {e}")
            
            return ScrapingResult(
                success=False,
                error=str(e),
                platform=platform,
                url=url,
                response_time=response_time
            )
    
    async def _parse_content(self, content: str, url: str, platform: str) -> Dict:
        """Parsea el contenido HTML según la plataforma"""
        soup = BeautifulSoup(content, "html.parser")
        
        # Detectar si estamos bloqueados
        if self._is_blocked(soup, platform):
            raise Exception(f"Contenido bloqueado por {platform}")
        
        # Parsear según plataforma
        if platform == 'linkedin':
            return self._parse_linkedin(soup, url)
        elif platform == 'workday':
            return self._parse_workday(soup, url)
        elif platform == 'indeed':
            return self._parse_indeed(soup, url)
        elif platform == 'glassdoor':
            return self._parse_glassdoor(soup, url)
        else:
            return self._parse_generic(soup, url)
    
    def _is_blocked(self, soup: BeautifulSoup, platform: str) -> bool:
        """Detecta si el contenido está bloqueado"""
        blocked_indicators = [
            'access denied',
            'blocked',
            'captcha',
            'robot',
            'automation',
            'suspicious activity',
            'too many requests',
            'rate limit',
            'please verify you are human',
            'security check',
            'unusual traffic',
            'temporary block'
        ]
        
        text = soup.get_text().lower()
        return any(indicator in text for indicator in blocked_indicators)
    
    def _parse_linkedin(self, soup: BeautifulSoup, url: str) -> Dict:
        """Parsea contenido de LinkedIn optimizado"""
        data = {
            'platform': 'linkedin',
            'url': url,
            'scraped_at': timezone.now().isoformat(),
            'title': None,
            'company': None,
            'location': None,
            'description': None,
            'requirements': [],
            'benefits': [],
            'salary': None,
            'job_type': None,
            'experience_level': None
        }
        
        # Selectores optimizados para LinkedIn
        title_selectors = [
            'h1.topcard__title',
            'h1.job-details-jobs-unified-top-card__job-title',
            'h1[data-test-job-title]',
            'h1.job-title',
            'h1'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                data['title'] = title_elem.get_text(strip=True)
                break
        
        # Empresa
        company_selectors = [
            'a.topcard__org-name-link',
            'span.topcard__org-name-text',
            'div.job-details-jobs-unified-top-card__company-name',
            'span.company-name'
        ]
        
        for selector in company_selectors:
            company_elem = soup.select_one(selector)
            if company_elem:
                data['company'] = company_elem.get_text(strip=True)
                break
        
        # Ubicación
        location_selectors = [
            'span.topcard__flavor--bullet',
            'div.job-details-jobs-unified-top-card__bullet',
            'span.location'
        ]
        
        for selector in location_selectors:
            location_elem = soup.select_one(selector)
            if location_elem:
                data['location'] = location_elem.get_text(strip=True)
                break
        
        # Descripción
        desc_selectors = [
            'div.description__text',
            'div.job-details-jobs-unified-top-card__job-description',
            'div[data-test-job-description]',
            'div.job-description'
        ]
        
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                data['description'] = desc_elem.get_text(strip=True)
                break
        
        return data
    
    def _parse_workday(self, soup: BeautifulSoup, url: str) -> Dict:
        """Parsea contenido de Workday optimizado"""
        data = {
            'platform': 'workday',
            'url': url,
            'scraped_at': timezone.now().isoformat(),
            'title': None,
            'company': None,
            'location': None,
            'description': None,
            'requirements': [],
            'benefits': [],
            'salary': None,
            'job_type': None
        }
        
        # Workday usa data-automation-id
        title_elem = soup.select_one('[data-automation-id="jobTitle"]')
        if title_elem:
            data['title'] = title_elem.get_text(strip=True)
        
        company_elem = soup.select_one('[data-automation-id="company"]')
        if company_elem:
            data['company'] = company_elem.get_text(strip=True)
        
        location_elem = soup.select_one('[data-automation-id="location"]')
        if location_elem:
            data['location'] = location_elem.get_text(strip=True)
        
        desc_elem = soup.select_one('[data-automation-id="jobPostingDescription"]')
        if desc_elem:
            data['description'] = desc_elem.get_text(strip=True)
        
        return data
    
    def _parse_indeed(self, soup: BeautifulSoup, url: str) -> Dict:
        """Parsea contenido de Indeed optimizado"""
        data = {
            'platform': 'indeed',
            'url': url,
            'scraped_at': timezone.now().isoformat(),
            'title': None,
            'company': None,
            'location': None,
            'description': None,
            'requirements': [],
            'benefits': [],
            'salary': None,
            'job_type': None
        }
        
        # Indeed selectors optimizados
        title_elem = soup.select_one('h1.jobTitle')
        if title_elem:
            data['title'] = title_elem.get_text(strip=True)
        
        company_elem = soup.select_one('span.companyName')
        if company_elem:
            data['company'] = company_elem.get_text(strip=True)
        
        location_elem = soup.select_one('div.companyLocation')
        if location_elem:
            data['location'] = location_elem.get_text(strip=True)
        
        desc_elem = soup.select_one('#jobDescriptionText')
        if desc_elem:
            data['description'] = desc_elem.get_text(strip=True)
        
        return data
    
    def _parse_glassdoor(self, soup: BeautifulSoup, url: str) -> Dict:
        """Parsea contenido de Glassdoor optimizado"""
        data = {
            'platform': 'glassdoor',
            'url': url,
            'scraped_at': timezone.now().isoformat(),
            'title': None,
            'company': None,
            'location': None,
            'description': None,
            'requirements': [],
            'benefits': [],
            'salary': None,
            'job_type': None
        }
        
        # Glassdoor selectors optimizados
        title_elem = soup.select_one('h1.job-title')
        if title_elem:
            data['title'] = title_elem.get_text(strip=True)
        
        company_elem = soup.select_one('div.job-company')
        if company_elem:
            data['company'] = company_elem.get_text(strip=True)
        
        location_elem = soup.select_one('span.job-location')
        if location_elem:
            data['location'] = location_elem.get_text(strip=True)
        
        desc_elem = soup.select_one('div.job-description')
        if desc_elem:
            data['description'] = desc_elem.get_text(strip=True)
        
        return data
    
    def _parse_generic(self, soup: BeautifulSoup, url: str) -> Dict:
        """Parsea contenido genérico optimizado"""
        data = {
            'platform': 'generic',
            'url': url,
            'scraped_at': timezone.now().isoformat(),
            'title': None,
            'company': None,
            'location': None,
            'description': None,
            'requirements': [],
            'benefits': [],
            'salary': None,
            'job_type': None
        }
        
        # Intentar extraer título con múltiples selectores
        title_selectors = ['h1', 'h2', '.title', '.job-title', '[class*="title"]']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                data['title'] = title_elem.get_text(strip=True)
                break
        
        # Intentar extraer empresa
        company_selectors = ['.company', '.employer', '[class*="company"]']
        for selector in company_selectors:
            company_elem = soup.select_one(selector)
            if company_elem:
                data['company'] = company_elem.get_text(strip=True)
                break
        
        # Intentar extraer descripción
        desc_selectors = ['.description', '.content', '[class*="desc"]']
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                data['description'] = desc_elem.get_text(strip=True)
                break
        
        return data
    
    async def scrape_url(self, url: str, max_retries: int = None) -> ScrapingResult:
        """
        Método principal de scraping con múltiples fallbacks
        """
        self.stats['total_requests'] += 1
        
        # Determinar plataforma
        platform = self._get_platform_from_url(url)
        config = self.configs[platform]
        
        # Verificar cache
        cached_data = self._get_from_cache(url, platform)
        if cached_data:
            return ScrapingResult(
                success=True,
                data=cached_data,
                platform=platform,
                url=url
            )
        
        # Configurar retries
        max_retries = max_retries or config.max_retries
        
        # Métodos de scraping en orden de preferencia
        scraping_methods = [
            self.scrape_with_playwright,
            self.scrape_with_selenium,
            self.scrape_with_requests
        ]
        
        last_error = None
        
        for method in scraping_methods:
            for attempt in range(max_retries):
                try:
                    # Delay entre intentos
                    if attempt > 0:
                        delay = config.delay_between_requests * (2 ** attempt)
                        await asyncio.sleep(delay)
                    
                    result = await method(url, platform)
                    
                    if result.success:
                        return result
                    else:
                        last_error = result.error
                        
                        # Si es bloqueo, cambiar método
                        if 'blocked' in result.error.lower() or 'rate limit' in result.error.lower():
                            self.stats['blocked_requests'] += 1
                            break
                        
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Intento {attempt + 1} falló para {url}: {e}")
        
        # Si todos los métodos fallaron
        return ScrapingResult(
            success=False,
            error=f"Todos los métodos de scraping fallaron: {last_error}",
            platform=platform,
            url=url,
            retry_count=max_retries
        )
    
    async def scrape_multiple_urls(self, urls: List[str], max_concurrent: int = None) -> List[ScrapingResult]:
        """Scraping de múltiples URLs con control de concurrencia"""
        if not urls:
            return []
        
        # Determinar concurrencia por plataforma
        platform = self._get_platform_from_url(urls[0])
        config = self.configs[platform]
        max_concurrent = max_concurrent or config.max_concurrent
        
        # Agrupar URLs por plataforma para respetar rate limits
        urls_by_platform = {}
        for url in urls:
            platform = self._get_platform_from_url(url)
            if platform not in urls_by_platform:
                urls_by_platform[platform] = []
            urls_by_platform[platform].append(url)
        
        all_results = []
        
        # Procesar cada plataforma con su propia concurrencia
        for platform, platform_urls in urls_by_platform.items():
            config = self.configs[platform]
            platform_concurrent = min(max_concurrent, config.max_concurrent)
            
            # Crear semáforo para limitar concurrencia
            semaphore = asyncio.Semaphore(platform_concurrent)
            
            async def scrape_with_semaphore(url):
                async with semaphore:
                    return await self.scrape_url(url)
            
            # Ejecutar scraping concurrente
            tasks = [scrape_with_semaphore(url) for url in platform_urls]
            platform_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados
            for result in platform_results:
                if isinstance(result, Exception):
                    all_results.append(ScrapingResult(
                        success=False,
                        error=str(result),
                        platform=platform
                    ))
                else:
                    all_results.append(result)
        
        return all_results
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del sistema"""
        return {
            **self.stats,
            'success_rate': (self.stats['successful_requests'] / max(self.stats['total_requests'], 1)) * 100,
            'cache_hit_rate': (self.stats['cache_hits'] / max(self.stats['total_requests'], 1)) * 100,
            'blocked_rate': (self.stats['blocked_requests'] / max(self.stats['total_requests'], 1)) * 100
        }
    
    async def cleanup(self):
        """Limpia recursos del sistema"""
        # Cerrar browsers
        for platform, (browser, context, page) in self.browser_pool.items():
            try:
                await page.close()
                await context.close()
                await browser.close()
            except Exception as e:
                logger.error(f"Error cerrando browser para {platform}: {e}")
        
        self.browser_pool.clear()

# Instancia global del sistema
robust_scraping_system = RobustScrapingSystem() 