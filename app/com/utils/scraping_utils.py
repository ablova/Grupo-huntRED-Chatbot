# /home/pablo/app/utilidades/scraping_utils.py
import random
import asyncio
import json
import logging
import gc
import os
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from django.core.cache import cache
from django.utils import timezone
from asgiref.sync import sync_to_async
from prometheus_client import Counter, Histogram, CollectorRegistry, start_http_server
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


logger = logging.getLogger(__name__)

class ScrapingMetrics:
    """Clase para gestionar métricas Prometheus de scraping."""
    def __init__(self, registry_name: str = "scraping"):
        self.registry = CollectorRegistry()
        self.jobs_scraped = Counter(
            f"{registry_name}_jobs_scraped_total", 
            "Total jobs scraped", 
            registry=self.registry
        )
        self.scraping_duration = Histogram(
            f"{registry_name}_scraping_duration_seconds", 
            "Time spent scraping", 
            registry=self.registry
        )
        self.errors_total = Counter(
            f"{registry_name}_scraping_errors_total", 
            "Total scraping errors", 
            registry=self.registry
        )
        self.emails_processed = Counter(
            f"{registry_name}_emails_processed_total", 
            "Total emails processed", 
            registry=self.registry
        )
        try:
            start_http_server(8001, registry=self.registry)
            logger.info("Prometheus server started on port 8001")
        except OSError as e:
            logger.warning(f"Failed to start Prometheus server on port 8001: {e}")
            for port in [8002, 8003, 8004, 8005]:  # Puertos alternativos
                try:
                    start_http_server(port, registry=self.registry)
                    logger.info(f"Prometheus server started on port {port}")
                    break
                except OSError:
                    logger.warning(f"Failed to start Prometheus server on port {port}")
            else:
                logger.error("Could not start Prometheus server on any port")

class SystemHealthMonitor:
    """Clase para monitorear la salud del sistema durante el scraping."""
    def __init__(self):
        self.start_time = time.time()
        self.last_check = self.start_time
        self.check_interval = 60  # Intervalo en segundos
        self.retry_delay = 5  # Retraso inicial en segundos
        self.stats = {
            "memory_usage": [], 
            "cpu_usage": [], 
            "error_rate": 0, 
            "success_rate": 0, 
            "connection_failures": 0
        }
        self.error_threshold = 0.3  # Umbral de tasa de error
        self.memory_threshold = 500  # Umbral de uso de memoria en MB
        self.cpu_threshold = 80  # Umbral de uso de CPU en porcentaje
        self.actions_taken = []

    async def check_health(self, processed: int, errors: int) -> Dict:
        """Verifica la salud del sistema y devuelve recomendaciones."""
        current_time = time.time()
        if current_time - self.last_check < self.check_interval:
            return {}
        self.last_check = current_time

        try:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / (1024 * 1024)
            cpu_percent = process.cpu_percent(interval=0.5)

            error_rate = errors / processed if processed > 0 else 0
            success_rate = (processed - errors) / processed if processed > 0 else 0

            self.stats["memory_usage"].append(memory_mb)
            self.stats["cpu_usage"].append(cpu_percent)
            self.stats["error_rate"] = error_rate
            self.stats["success_rate"] = success_rate

            recommendations = {}
            if memory_mb > self.memory_threshold:
                logger.warning(f"High memory usage: {memory_mb:.2f}MB")
                recommendations["run_gc"] = True
                self.actions_taken.append(f"High memory: {memory_mb:.2f}MB, running gc.collect()")
            if cpu_percent > self.cpu_threshold:
                logger.warning(f"High CPU usage: {cpu_percent:.2f}%")
                recommendations["reduce_batch"] = True
                self.actions_taken.append(f"High CPU: {cpu_percent:.2f}%, reducing batch_size")
            if error_rate > self.error_threshold:
                logger.warning(f"High error rate: {error_rate:.2%}")
                recommendations["increase_delay"] = True
                self.retry_delay = min(self.retry_delay * 2, 30)
                self.actions_taken.append(f"High error rate: {error_rate:.2%}, increased retry delay to {self.retry_delay}")
            return recommendations
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {}

class ScrapingCache:
    """Clase para gestionar caché de resultados de scraping."""
    TTL = 3600  # Tiempo de vida en segundos (1 hora)

    async def get(self, key: str) -> Optional[Dict]:
        """Obtiene un valor del caché."""
        try:
            serialized = await cache.get(key)
            return json.loads(serialized) if serialized else None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None

    async def set(self, key: str, value: Dict):
        """Establece un valor en el caché."""
        try:
            serialized = json.dumps(value)
            await cache.set(key, serialized, timeout=self.TTL)
            logger.info(f"Cached {key}")
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False

class PlaywrightAntiDeteccion:
    """Configuración para evitar detección en job boards usando Playwright."""
    COOKIES_CONFIG = {
        "linkedin": {
            "essential": ["li_at", "JSESSIONID"],
            "fingerprinting": ["bcookie", "bscookie", "_guid"],
            "session": ["lidc", "UserMatchHistory", "AnalyticsSyncHistory"],
            "preferences": ["lang", "li_theme", "timezone"],
            "headers": {
                "Referer": "https://www.linkedin.com/jobs/",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            }
        },
        "indeed": {
            "essential": ["CTK", "INDEED_CSRF_TOKEN"],
            "fingerprinting": ["SURF", "PPID", "JSESSIONID"],
            "session": ["indeed_rcc", "LC"],
            "preferences": ["PREF", "RQ"],
            "headers": {
                "Referer": "https://www.indeed.com/jobs",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            }
        },
        "glassdoor": {
            "essential": ["GSESSIONID", "datr", "gdId"],
            "fingerprinting": ["_ga", "_gid", "G_ENABLED_IDPS"],
            "session": ["trs", "fsr.r", "AWSALB"],
            "preferences": ["OptanonConsent", "OptanonAlertBoxClosed"],
            "headers": {
                "Referer": "https://www.glassdoor.com/Job/index.htm",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            }
        },
        "workday": {
            "essential": ["JSESSIONID", "wday_vps_cookie"],
            "fingerprinting": ["TS01292a30", "wd-browser-id"],
            "session": ["timezoneOffset", "iawSessionID"],
            "preferences": ["userLang", "calendarType"],
            "headers": {
                "Referer": "https://www.myworkday.com/",
                "X-Requested-With": "XMLHttpRequest",
            }
        },
        "default": {
            "essential": ["JSESSIONID", "csrf_token"],
            "fingerprinting": ["_ga", "_device_id"],
            "session": ["session_id", "visitor_id"],
            "preferences": ["lang", "timezone"],
            "headers": {
                "Referer": "",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            }
        }
    }

    @staticmethod
    async def generar_user_agent(tipo="desktop"):
        """Genera un user agent aleatorio para evitar detección."""
        desktop_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]
        mobile_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        ]
        return random.choice(desktop_agents if tipo == "desktop" else mobile_agents)

    @staticmethod
    async def generar_perfil_navegador(plataforma="default"):
        """Genera un perfil de navegador para simular comportamiento humano."""
        viewport_width = random.choice([1366, 1440, 1536, 1920])
        viewport_height = random.choice([768, 900, 1080, 1440])
        locale = random.choice(["es-ES", "es-MX", "es-AR", "es-CO", "en-US"])
        timezone_id = random.choice(["Europe/Madrid", "America/Mexico_City", "America/Bogota"])
        platform = "Windows" if random.random() > 0.3 else "macOS"
        user_agent = await PlaywrightAntiDeteccion.generar_user_agent("desktop")
        return {
            "user_agent": user_agent,
            "viewport": {"width": viewport_width, "height": viewport_height},
            "device_scale_factor": 1,
            "is_mobile": False,
            "has_touch": False,
            "locale": locale,
            "timezone_id": timezone_id,
            "color_scheme": "light",
            "reduced_motion": "no-preference",
            "platform": platform,
            "plataforma_specs": {"has_touch": False, "language": locale.split("-")[0]},
        }

    @staticmethod
    async def patron_navegacion_humana():
        """Define patrones de navegación para simular comportamiento humano."""
        return {
            "clicks_por_pagina": random.randint(3, 8),
            "tiempo_pagina": random.randint(30, 120),
            "patrones_scroll": [
                {"direccion": "down", "velocidad": random.uniform(100, 400), "distancia": random.randint(300, 1200)},
                {"direccion": "up", "velocidad": random.uniform(80, 300), "distancia": random.randint(100, 500)},
            ],
            "pausas_entre_acciones": [random.uniform(1.5, 4.5), random.uniform(0.8, 3.2)],
            "movimiento_mouse": {"patron": "humano", "velocidad": random.uniform(0.3, 0.8)},
        }

    @staticmethod
    async def obtener_cookies_formato_playwright(cookies_dict, dominio):
        """Convierte cookies a formato Playwright."""
        cookies_playwright = []
        dominio_base = dominio.split('/')[2] if '://' in dominio else dominio
        for name, value in cookies_dict.items():
            if value is not None:
                cookie = {
                    "name": name,
                    "value": str(value),
                    "domain": f".{dominio_base}",
                    "path": "/",
                    "expires": int((datetime.now() + timedelta(days=30)).timestamp()),
                    "httpOnly": False,
                    "secure": True,
                    "sameSite": "Lax",
                }
                cookies_playwright.append(cookie)
        return cookies_playwright

    @staticmethod
    async def simular_comportamiento_humano(page: Page):
        """Simula comportamiento humano en la página."""
        try:
            await page.wait_for_timeout(random.randint(1000, 3000))
            await page.mouse.move(random.randint(100, 700), random.randint(100, 500))
            if random.random() > 0.3:
                await page.mouse.wheel(0, random.randint(300, 800))
                await page.wait_for_timeout(random.randint(800, 2500))
                if random.random() > 0.6:
                    await page.mouse.wheel(0, random.randint(-400, -100))
                    await page.wait_for_timeout(random.randint(500, 1500))
            elementos = await page.query_selector_all('a, button')
            if elementos:
                elemento_aleatorio = random.choice(elementos)
                await elemento_aleatorio.hover()
                await page.wait_for_timeout(random.randint(300, 1200))
        except Exception as e:
            logger.debug(f"No se pudo simular comportamiento humano: {e}")

async def inicializar_contexto_playwright(domain, browser: Browser) -> BrowserContext:
    """Inicializa el contexto de Playwright con configuración anti-detección."""
    from app.models import DominioScraping  # Importación local
    if not isinstance(domain, DominioScraping):
        raise ValueError("El dominio debe ser una instancia de DominioScraping")
    try:
        plataforma = domain.plataforma or "default"
        perfil = await PlaywrightAntiDeteccion.generar_perfil_navegador(plataforma)
        context = await browser.new_context(
            viewport=perfil["viewport"],
            user_agent=perfil["user_agent"],
            locale=perfil["locale"],
            timezone_id=perfil["timezone_id"],
            color_scheme=perfil["color_scheme"],
            reduced_motion=perfil["reduced_motion"],
            is_mobile=perfil["is_mobile"],
            has_touch=perfil["has_touch"],
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', {
                get: () => ({
                    length: 5,
                    item: () => ({}),
                    namedItem: () => ({}),
                    refresh: () => {},
                    [Symbol.iterator]: function* () {
                        yield { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' };
                        yield { name: 'Chrome PDF Viewer', filename: 'chrome-pdf-viewer' };
                        yield { name: 'Native Client', filename: 'internal-nacl-plugin' };
                    }
                })
            });
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                ['notifications', 'geolocation', 'midi', 'camera', 'microphone'].includes(parameters.name)
                ? Promise.resolve({ state: 'prompt' })
                : originalQuery(parameters)
            );
            Object.defineProperty(navigator, 'languages', { get: () => ['es-ES', 'es', 'en-US', 'en'] });
            Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
        """)
        if domain.cookies and domain.cookies.get(plataforma):
            cookies_dict = domain.cookies.get(plataforma, {})
            cookies_playwright = await PlaywrightAntiDeteccion.obtener_cookies_formato_playwright(cookies_dict, domain.dominio)
            if cookies_playwright:
                await context.add_cookies(cookies_playwright)
                logger.info(f"Cookies cargadas para {domain.dominio} ({plataforma})")
        return context
    except Exception as e:
        logger.error(f"Error inicializando contexto Playwright para {domain.dominio}: {e}")
        raise

async def visitar_pagina_humanizada(page: Page, url: str):
    """Simula comportamiento humano al visitar una página."""
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await PlaywrightAntiDeteccion.simular_comportamiento_humano(page)
        return page
    except Exception as e:
        logger.error(f"Error visitando página {url}: {e}")
        raise

async def extraer_y_guardar_cookies(domain, context: BrowserContext):
    """Extrae y guarda las cookies del contexto de Playwright."""
    from app.models import DominioScraping
    if not isinstance(domain, DominioScraping):
        raise ValueError("El dominio debe ser una instancia de DominioScraping")
    try:
        cookies_playwright = await context.cookies()
        plataforma = domain.plataforma or "default"
        cookies_dict = {}
        config_cookies = PlaywrightAntiDeteccion.COOKIES_CONFIG.get(plataforma, PlaywrightAntiDeteccion.COOKIES_CONFIG["default"])
        todas_cookies_relevantes = (
            config_cookies.get("essential", []) + 
            config_cookies.get("fingerprinting", []) + 
            config_cookies.get("session", []) + 
            config_cookies.get("preferences", [])
        )
        cookies_relevantes = {cookie.lower(): cookie for cookie in todas_cookies_relevantes}
        for cookie in cookies_playwright:
            nombre_cookie = cookie["name"]
            if nombre_cookie.lower() in cookies_relevantes:
                cookies_dict[cookies_relevantes[nombre_cookie.lower()]] = cookie["value"]
        if not domain.cookies:
            domain.cookies = {}
        domain.cookies[plataforma] = cookies_dict
        domain.cookies["_last_updated"] = datetime.now().isoformat()
        domain.cookies["_user_agent"] = await context.pages[0].evaluate("() => navigator.userAgent")
        domain.cookies["_comportamiento"] = await PlaywrightAntiDeteccion.patron_navegacion_humana()
        await sync_to_async(domain.save)(skip_clean=True)
        logger.info(f"Cookies actualizadas para {domain.dominio} ({plataforma})")
        return domain.cookies
    except Exception as e:
        logger.error(f"Error extrayendo y guardando cookies para {domain.dominio}: {e}")
        return {}

async def generate_summary_report(stats: Dict, actions_taken: List[str]) -> str:
    """Genera un reporte resumen de las acciones tomadas."""
    try:
        return (
            f"Scraping Summary:\n"
            f"Processed: {stats.get('correos_procesados', 0) or stats.get('vacantes_procesadas', 0)}\n"
            f"Successful: {stats.get('correos_exitosos', 0) or stats.get('vacantes_guardadas', 0)}\n"
            f"Errors: {stats.get('correos_error', 0) or stats.get('errors_total', 0)}\n"
            f"Vacancies Extracted: {stats.get('vacantes_extraidas', 0)}\n"
            f"Vacancies Saved: {stats.get('vacantes_guardadas', 0)}\n\n"
            f"Actions Taken:\n{chr(10).join(actions_taken) if actions_taken else 'No corrective actions taken.'}"
        )
    except Exception as e:
        logger.error(f"Error generating summary report: {e}")
        return "Error generating summary report"