# /home/pablo/app/utilidades/scraping_utils.py
import random
import asyncio
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from app.models import DominioScraping
from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger(__name__)

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
        await page.wait_for_timeout(random.randint(1000, 3000))
        await page.mouse.move(random.randint(100, 700), random.randint(100, 500))
        if random.random() > 0.3:
            await page.mouse.wheel(0, random.randint(300, 800))
            await page.wait_for_timeout(random.randint(800, 2500))
            if random.random() > 0.6:
                await page.mouse.wheel(0, random.randint(-400, -100))
                await page.wait_for_timeout(random.randint(500, 1500))
        try:
            elementos = await page.query_selector_all('a, button')
            if elementos:
                elemento_aleatorio = random.choice(elementos)
                await elemento_aleatorio.hover()
                await page.wait_for_timeout(random.randint(300, 1200))
        except Exception as e:
            logger.debug(f"No se pudo simular hover: {e}")

async def inicializar_contexto_playwright(domain: DominioScraping, browser: Browser) -> BrowserContext:
    """Inicializa un contexto de navegador Playwright con configuración anti-detección."""
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

async def visitar_pagina_humanizada(page: Page, url: str):
    """Visita una página con comportamiento humano."""
    await page.goto(url, wait_until="networkidle", timeout=60000)
    await PlaywrightAntiDeteccion.simular_comportamiento_humano(page)
    return page

async def extraer_y_guardar_cookies(domain: DominioScraping, context: BrowserContext):
    """Extrae cookies del contexto y las guarda en el modelo."""
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

async def scrape_with_playwright(domain: DominioScraping, url: str, headless=True, slow_mo=50):
    """Realiza scraping usando Playwright con configuración anti-detección."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, slow_mo=slow_mo)
        try:
            context = await inicializar_contexto_playwright(domain, browser)
            page = await context.new_page()
            await visitar_pagina_humanizada(page, url)
            content = await page.content()
            await extraer_y_guardar_cookies(domain, context)
            return content
        except Exception as e:
            logger.error(f"Error en scraping con Playwright para {url}: {e}")
            raise
        finally:
            await browser.close()