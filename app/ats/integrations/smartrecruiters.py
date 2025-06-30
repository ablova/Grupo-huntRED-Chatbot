import os
import asyncio
import httpx
from django.core.cache import cache
from asgiref.sync import sync_to_async
from app.models import Person, ChatState
from app.utilidades.parser import CVParser
# from app.chatbot.services import send_message  # Descomentar si existe
# from app.gamification.services import GamificationService  # Descomentar si existe
import time
from typing import List

SMARTRECRUITERS_API_URL = "https://api.smartrecruiters.com/v1"
CACHE_TIMEOUT = 86400  # 24 horas
PAGE_SIZE = 50
THROTTLE_SECONDS = 1.0

class SmartRecruitersImporter:
    def __init__(self):
        self.username = os.environ.get('SMARTRECRUITERS_USERNAME')
        self.password = os.environ.get('SMARTRECRUITERS_PASSWORD')
        self.api_token = os.environ.get('SMARTRECRUITERS_API_TOKEN')
        self.total_imported = 0
        self.logger = None  # Puede ser configurado externamente

    async def fetch_candidates(self, page: int = 1):
        cache_key = f"smartrecruiters:candidates:{page}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        url = f"{SMARTRECRUITERS_API_URL}/candidates?limit={PAGE_SIZE}&offset={(page-1)*PAGE_SIZE}"
        headers = {"X-SmartToken": self.api_token}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url, headers=headers, auth=(self.username, self.password))
                resp.raise_for_status()
                data = resp.json().get("content", [])
                cache.set(cache_key, data, CACHE_TIMEOUT)
                return data
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error obteniendo candidatos página {page}: {e}")
                return []

    async def fetch_candidate_cv(self, candidate_id: str):
        cache_key = f"smartrecruiters:cv:{candidate_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        url = f"{SMARTRECRUITERS_API_URL}/candidates/{candidate_id}/attachments"
        headers = {"X-SmartToken": self.api_token}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url, headers=headers, auth=(self.username, self.password))
                resp.raise_for_status()
                attachments = resp.json().get("content", [])
                for att in attachments:
                    if att.get("type") in ["RESUME", "CV"]:
                        cv_url = att.get("fileUrl")
                        cache.set(cache_key, cv_url, CACHE_TIMEOUT)
                        return cv_url
                return None
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error obteniendo CV para {candidate_id}: {e}")
                return None

    async def process_candidate(self, candidate: dict):
        candidate_id = candidate.get("id")
        email = candidate.get("email")
        phone = candidate.get("phone")
        name = candidate.get("firstName", "Usuario")
        last_name = candidate.get("lastName", "")
        # Deduplicación
        person, created = await sync_to_async(Person.objects.get_or_create)(
            phone=phone or f"smart_{candidate_id}",
            defaults={"nombre": name, "apellido_paterno": last_name, "email": email}
        )
        if not created:
            person.nombre = name
            person.apellido_paterno = last_name
            person.email = email
            await sync_to_async(person.save)()
        # ChatState
        chat_state, _ = await sync_to_async(ChatState.objects.get_or_create)(
            user_id=person.phone,
            defaults={"platform": "whatsapp", "state": "imported_historical", "context": {}}
        )
        # Procesar CV
        cv_url = await self.fetch_candidate_cv(candidate_id)
        if cv_url:
            parser = CVParser(cv_url)
            parsed_data = await sync_to_async(parser.parse)()
            person.cv_parsed = True
            person.cv_url = cv_url
            person.cv_parsed_data = parsed_data
            if "name" in parsed_data and not person.nombre:
                person.nombre = parsed_data["name"]
            if "email" in parsed_data and not person.email:
                person.email = parsed_data["email"]
            if "phone" in parsed_data and not person.phone:
                person.phone = parsed_data["phone"]
            if "skills" in parsed_data:
                person.skills = ", ".join(parsed_data["skills"]) if isinstance(parsed_data["skills"], list) else parsed_data["skills"]
            await sync_to_async(person.save)()
            # Mensaje personalizado (sin mencionar SmartRecruiters)
            bienvenida = (
                f"¡Bienvenido al nuevo huntRED®, {person.nombre}!\n"
                "Tu perfil ha sido importado de aplicaciones históricas de nuestra página www.huntred.com.\n"
                "Hemos ampliado nuestras capacidades tecnológicas con una plataforma de Inteligencia Artificial muy robusta pensada en brindarte las mejores oportunidades y agilizar tu experiencia. "
                "Por lo que te invitamos a conocer a detalle las nuevas funcionalidades, evaluaciones, pero sobre todo poder continuar asistiéndote en encontrar el mejor empleo, desde la comodidad de tu celular."
            )
            # Punto de integración: notificaciones/chatbot
            # send_message("whatsapp", person.phone, bienvenida)
            # Punto de integración: gamificación
            # GamificationService.bonus_for_imported(person)
            chat_state.state = "profile_in_progress"
            chat_state.context["parsed_data"] = parsed_data
            await sync_to_async(chat_state.save)()
        self.total_imported += 1
        await asyncio.sleep(THROTTLE_SECONDS)

    async def import_candidates(self):
        page = 1
        while True:
            candidates = await self.fetch_candidates(page)
            if not candidates:
                break
            for candidate in candidates:
                await self.process_candidate(candidate)
            page += 1
        # Apagado lógico: marcar estado en cache
        cache.set("smartrecruiters:import_status", "completed", None)
        return self.total_imported

# ---
# Modo alternativo: Extracción por Web Scraping si no hay API Key
# --------------------------------------------------------------
# Este modo usa Selenium o Playwright para automatizar el login y la navegación
# por el portal web de SmartRecruiters, permitiendo extraer datos de candidatos
# y descargar CVs de manera masiva. Úsalo solo si no tienes acceso a la API Key.
#
# Limitaciones:
# - Puede romperse si SmartRecruiters cambia el diseño de la web.
# - Puede estar limitado por captchas, autenticación 2FA o políticas de uso.
# - Requiere mantener credenciales de usuario y cookies de sesión.
# - Úsalo bajo tu propio riesgo y revisa los Términos de Servicio.
#
# Requiere: playwright (o selenium), playwright install, y credenciales válidas.

class SmartRecruitersWebScraper:
    def __init__(self, username: str, password: str, headless: bool = True):
        self.username = username
        self.password = password
        self.headless = headless
        self.browser = None
        self.page = None
        self.logger = None

    async def initialize(self):
        from playwright.async_api import async_playwright
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        if self.logger:
            self.logger.info("Playwright browser session initialized for SmartRecruiters scraping")

    async def login(self):
        await self.page.goto("https://www.smartrecruiters.com/login/")
        await self.page.fill('input[name="email"]', self.username)
        await self.page.fill('input[name="password"]', self.password)
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state('networkidle')
        if self.logger:
            self.logger.info(f"Logged in as {self.username}")

    async def scrape_candidates(self, max_pages: int = 100):
        """
        Extrae candidatos y CVs navegando por el portal web.
        max_pages: número máximo de páginas a recorrer (ajustar según volumen)
        """
        candidates = []
        await self.page.goto("https://www.smartrecruiters.com/people/candidates/")
        for page_num in range(1, max_pages+1):
            await self.page.wait_for_selector('.candidate-list')
            rows = await self.page.query_selector_all('.candidate-list .candidate-row')
            for row in rows:
                name = await row.query_selector_eval('.candidate-name', 'el => el.textContent')
                email = await row.query_selector_eval('.candidate-email', 'el => el.textContent')
                phone = await row.query_selector_eval('.candidate-phone', 'el => el.textContent')
                candidate_id = await row.get_attribute('data-candidate-id')
                # Ir al detalle para descargar CV
                await row.click()
                await self.page.wait_for_selector('.attachments-list')
                attachments = await self.page.query_selector_all('.attachments-list .attachment-row')
                cv_url = None
                for att in attachments:
                    att_type = await att.query_selector_eval('.attachment-type', 'el => el.textContent')
                    if 'CV' in att_type or 'Resume' in att_type:
                        cv_url = await att.query_selector_eval('a', 'el => el.href')
                        break
                candidates.append({
                    'id': candidate_id,
                    'name': name.strip() if name else '',
                    'email': email.strip() if email else '',
                    'phone': phone.strip() if phone else '',
                    'cv_url': cv_url
                })
                # Aquí puedes llamar al parser y almacenar el candidato
                # parsed_data = CVParser(cv_url).parse() if cv_url else None
                # ... guardar en base de datos ...
                if self.logger:
                    self.logger.info(f"Scraped candidate {name} ({email})")
                await self.page.go_back()
                await asyncio.sleep(0.5)
            # Ir a la siguiente página
            next_btn = await self.page.query_selector('.pagination-next')
            if next_btn and await next_btn.is_enabled():
                await next_btn.click()
                await self.page.wait_for_load_state('networkidle')
            else:
                break
        return candidates

    async def close(self):
        if self.browser:
            await self.browser.close()

class SmartRecruitersUnifiedImporter:
    """
    Importador unificado para SmartRecruiters.
    Permite alternar entre modo 'web' (scraping) y 'api' (API oficial) según el parámetro 'mode'.
    Por defecto usa web scraping. Si se pasa mode='api' y api_key, usa la API.

    Ejemplo de uso:
    # Web scraping (default)
    importer = SmartRecruitersUnifiedImporter(username='pablo@huntred.com', password='Latituded800!')
    total = asyncio.run(importer.import_candidates(max_pages=1000))

    # API (si tienes API Key)
    importer = SmartRecruitersUnifiedImporter(api_key='DCRA1-xxxxxxxxxxxxxxxxxxxxxxxxxxxx', mode='api')
    total = asyncio.run(importer.import_candidates())
    """
    def __init__(self, username=None, password=None, api_key=None, mode='web', headless=True):
        self.username = username or os.environ.get('SMARTRECRUITERS_USERNAME')
        self.password = password or os.environ.get('SMARTRECRUITERS_PASSWORD')
        self.api_key = api_key or os.environ.get('SMARTRECRUITERS_API_TOKEN')
        self.mode = mode
        self.headless = headless
        self.logger = None
        self.total_imported = 0
        # Web scraping
        self.browser = None
        self.page = None

    async def import_candidates(self, max_pages=100):
        if self.mode == 'api' and self.api_key:
            return await self._import_candidates_api()
        else:
            return await self._import_candidates_web(max_pages=max_pages)

    # --- API MODE ---
    async def _fetch_candidates_api(self, page: int = 1):
        cache_key = f"smartrecruiters:candidates:{page}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        url = f"{SMARTRECRUITERS_API_URL}/candidates?limit={PAGE_SIZE}&offset={(page-1)*PAGE_SIZE}"
        headers = {"X-SmartToken": self.api_key}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json().get("content", [])
                cache.set(cache_key, data, CACHE_TIMEOUT)
                return data
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error obteniendo candidatos página {page}: {e}")
                return []

    async def _fetch_candidate_cv_api(self, candidate_id: str):
        cache_key = f"smartrecruiters:cv:{candidate_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        url = f"{SMARTRECRUITERS_API_URL}/candidates/{candidate_id}/attachments"
        headers = {"X-SmartToken": self.api_key}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                attachments = resp.json().get("content", [])
                for att in attachments:
                    if att.get("type") in ["RESUME", "CV"]:
                        cv_url = att.get("fileUrl")
                        cache.set(cache_key, cv_url, CACHE_TIMEOUT)
                        return cv_url
                return None
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error obteniendo CV para {candidate_id}: {e}")
                return None

    async def _import_candidates_api(self):
        page = 1
        while True:
            candidates = await self._fetch_candidates_api(page)
            if not candidates:
                break
            for candidate in candidates:
                await self._process_candidate_api(candidate)
            page += 1
        cache.set("smartrecruiters:import_status", "completed", None)
        return self.total_imported

    async def _process_candidate_api(self, candidate: dict):
        candidate_id = candidate.get("id")
        email = candidate.get("email")
        phone = candidate.get("phone")
        name = candidate.get("firstName", "Usuario")
        last_name = candidate.get("lastName", "")
        person, created = await sync_to_async(Person.objects.get_or_create)(
            phone=phone or f"smart_{candidate_id}",
            defaults={"nombre": name, "apellido_paterno": last_name, "email": email}
        )
        if not created:
            person.nombre = name
            person.apellido_paterno = last_name
            person.email = email
            await sync_to_async(person.save)()
        chat_state, _ = await sync_to_async(ChatState.objects.get_or_create)(
            user_id=person.phone,
            defaults={"platform": "whatsapp", "state": "imported_historical", "context": {}}
        )
        cv_url = await self._fetch_candidate_cv_api(candidate_id)
        if cv_url and cv_url.endswith(('.pdf', '.doc', '.docx')):
            parser = CVParser(cv_url)
            parsed_data = await sync_to_async(parser.parse)()
            person.cv_parsed = True
            person.cv_url = cv_url
            person.cv_parsed_data = parsed_data
            if "name" in parsed_data and not person.nombre:
                person.nombre = parsed_data["name"]
            if "email" in parsed_data and not person.email:
                person.email = parsed_data["email"]
            if "phone" in parsed_data and not person.phone:
                person.phone = parsed_data["phone"]
            if "skills" in parsed_data:
                person.skills = ", ".join(parsed_data["skills"]) if isinstance(parsed_data["skills"], list) else parsed_data["skills"]
            await sync_to_async(person.save)()
            bienvenida = (
                f"¡Bienvenido al nuevo huntRED®, {person.nombre}!\n"
                "Tu perfil ha sido importado de aplicaciones históricas.\n"
                "Hemos ampliado nuestras capacidades tecnológicas con una plataforma de Inteligencia Artificial muy robusta pensada en brindarte las mejores oportunidades y agilizar tu experiencia. "
                "Por lo que te invitamos a conocer a detalle las nuevas funcionalidades."
            )
            # send_message("whatsapp", person.phone, bienvenida)
            # GamificationService.bonus_for_imported(person)
            chat_state.state = "profile_in_progress"
            chat_state.context["parsed_data"] = parsed_data
            await sync_to_async(chat_state.save)()
        self.total_imported += 1
        await asyncio.sleep(THROTTLE_SECONDS)

    # --- WEB SCRAPING MODE ---
    async def _initialize_web(self):
        from playwright.async_api import async_playwright
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        if self.logger:
            self.logger.info("Playwright browser session initialized for SmartRecruiters scraping")

    async def _login_web(self):
        await self.page.goto("https://www.smartrecruiters.com/login/")
        await self.page.fill('input[name="email"]', self.username)
        await self.page.fill('input[name="password"]', self.password)
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state('networkidle')
        if self.logger:
            self.logger.info(f"Logged in as {self.username}")

    async def _import_candidates_web(self, max_pages: int = 100):
        await self._initialize_web()
        await self._login_web()
        candidates = []
        await self.page.goto("https://www.smartrecruiters.com/people/candidates/")
        for page_num in range(1, max_pages+1):
            await self.page.wait_for_selector('.candidate-list')
            rows = await self.page.query_selector_all('.candidate-list .candidate-row')
            for row in rows:
                name = await row.query_selector_eval('.candidate-name', 'el => el.textContent')
                email = await row.query_selector_eval('.candidate-email', 'el => el.textContent')
                phone = await row.query_selector_eval('.candidate-phone', 'el => el.textContent')
                candidate_id = await row.get_attribute('data-candidate-id')
                await row.click()
                await self.page.wait_for_selector('.attachments-list')
                attachments = await self.page.query_selector_all('.attachments-list .attachment-row')
                cv_url = None
                for att in attachments:
                    att_type = await att.query_selector_eval('.attachment-type', 'el => el.textContent')
                    if 'CV' in att_type or 'Resume' in att_type:
                        cv_url = await att.query_selector_eval('a', 'el => el.href')
                        break
                candidates.append({
                    'id': candidate_id,
                    'name': name.strip() if name else '',
                    'email': email.strip() if email else '',
                    'phone': phone.strip() if phone else '',
                    'cv_url': cv_url
                })
                # parsed_data = CVParser(cv_url).parse() if cv_url else None
                # ... guardar en base de datos ...
                if self.logger:
                    self.logger.info(f"Scraped candidate {name} ({email})")
                await self.page.go_back()
                await asyncio.sleep(0.5)
            next_btn = await self.page.query_selector('.pagination-next')
            if next_btn and await next_btn.is_enabled():
                await next_btn.click()
                await self.page.wait_for_load_state('networkidle')
            else:
                break
        await self.browser.close()
        self.total_imported = len(candidates)
        cache.set("smartrecruiters:import_status", "completed", None)
        return self.total_imported

# Ejemplo de uso:
# importer = SmartRecruitersUnifiedImporter(mode='web')  # Web scraping por defecto
# importer = SmartRecruitersUnifiedImporter(mode='api')   # Usar API si hay API Key
# total = asyncio.run(importer.import_candidates(max_pages=1000)) 