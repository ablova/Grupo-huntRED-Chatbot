"""
LinkedIn Advanced Scraper - huntRED® v2
Scraping inteligente de perfiles de LinkedIn con anti-detección y proxies rotativos.
"""

import asyncio
import random
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent
import logging
from urllib.parse import urljoin, urlparse
import json
import re
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class LinkedInProfile:
    """Estructura de datos para perfiles de LinkedIn."""
    linkedin_id: str
    full_name: str
    headline: str
    location: str
    industry: str
    current_company: Optional[str]
    current_position: Optional[str]
    experience: List[Dict]
    education: List[Dict]
    skills: List[str]
    languages: List[str]
    connections_count: Optional[int]
    profile_url: str
    profile_image_url: Optional[str]
    summary: Optional[str]
    certifications: List[Dict]
    recommendations: List[Dict]
    activity_posts: List[Dict]
    contact_info: Dict
    scraped_at: datetime
    confidence_score: float


class LinkedInScraper:
    """
    Scraper avanzado de LinkedIn con múltiples estrategias anti-detección.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ua = UserAgent()
        self.session = requests.Session()
        self.driver = None
        self.proxies = config.get('proxies', [])
        self.current_proxy_index = 0
        self.accounts = config.get('linkedin_accounts', [])
        self.current_account_index = 0
        self.rate_limits = {
            'requests_per_minute': config.get('rate_limit_rpm', 30),
            'requests_per_hour': config.get('rate_limit_rph', 500),
            'daily_limit': config.get('daily_limit', 2000)
        }
        self.request_times = []
        
    def _setup_driver(self, headless: bool = True) -> webdriver.Chrome:
        """Configura el driver de Chrome con opciones anti-detección."""
        options = Options()
        
        if headless:
            options.add_argument('--headless')
        
        # Anti-detección básica
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User Agent rotativo
        options.add_argument(f'--user-agent={self.ua.random}')
        
        # Proxy rotativo
        if self.proxies:
            proxy = self._get_next_proxy()
            options.add_argument(f'--proxy-server={proxy}')
        
        # Otras opciones para parecer más humano
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins-discovery')
        options.add_argument('--start-maximized')
        
        driver = webdriver.Chrome(options=options)
        
        # Ejecutar script para ocultar webdriver
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def _get_next_proxy(self) -> str:
        """Obtiene el siguiente proxy de la lista rotativamente."""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy
    
    def _get_next_account(self) -> Dict[str, str]:
        """Obtiene la siguiente cuenta de LinkedIn rotativamente."""
        if not self.accounts:
            raise ValueError("No LinkedIn accounts configured")
        
        account = self.accounts[self.current_account_index]
        self.current_account_index = (self.current_account_index + 1) % len(self.accounts)
        return account
    
    def _check_rate_limits(self) -> bool:
        """Verifica si estamos dentro de los límites de velocidad."""
        now = datetime.now()
        
        # Limpiar requests antiguos
        self.request_times = [t for t in self.request_times if now - t < timedelta(hours=1)]
        
        # Verificar límites
        requests_last_minute = sum(1 for t in self.request_times if now - t < timedelta(minutes=1))
        requests_last_hour = len(self.request_times)
        
        if requests_last_minute >= self.rate_limits['requests_per_minute']:
            logger.warning("Rate limit per minute exceeded")
            return False
        
        if requests_last_hour >= self.rate_limits['requests_per_hour']:
            logger.warning("Rate limit per hour exceeded")
            return False
        
        return True
    
    def _wait_with_jitter(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Espera con jitter aleatorio para simular comportamiento humano."""
        wait_time = random.uniform(min_seconds, max_seconds)
        time.sleep(wait_time)
    
    def _login_to_linkedin(self) -> bool:
        """Inicia sesión en LinkedIn usando una cuenta rotatoria."""
        try:
            account = self._get_next_account()
            self.driver.get("https://www.linkedin.com/login")
            
            # Esperar a que cargue la página
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Simular escritura humana
            username_field = self.driver.find_element(By.ID, "username")
            self._human_type(username_field, account['email'])
            
            password_field = self.driver.find_element(By.ID, "password")
            self._human_type(password_field, account['password'])
            
            # Click en login
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Esperar a que se complete el login
            self._wait_with_jitter(3, 5)
            
            # Verificar si el login fue exitoso
            if "feed" in self.driver.current_url or "in/" in self.driver.current_url:
                logger.info(f"Successfully logged in with account: {account['email']}")
                return True
            else:
                logger.error(f"Login failed for account: {account['email']}")
                return False
                
        except Exception as e:
            logger.error(f"Error during LinkedIn login: {str(e)}")
            return False
    
    def _human_type(self, element, text: str):
        """Simula escritura humana con delays aleatorios."""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def _extract_profile_data(self, profile_url: str) -> Optional[LinkedInProfile]:
        """Extrae datos completos de un perfil de LinkedIn."""
        try:
            if not self._check_rate_limits():
                logger.warning("Rate limit exceeded, waiting...")
                time.sleep(60)
            
            self.driver.get(profile_url)
            self.request_times.append(datetime.now())
            
            # Esperar a que cargue el perfil
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".pv-text-details__left-panel"))
            )
            
            # Scroll para cargar contenido dinámico
            self._scroll_profile()
            
            # Extraer datos básicos
            basic_info = self._extract_basic_info()
            experience = self._extract_experience()
            education = self._extract_education()
            skills = self._extract_skills()
            contact_info = self._extract_contact_info()
            activity = self._extract_recent_activity()
            
            # Crear objeto de perfil
            profile = LinkedInProfile(
                linkedin_id=self._extract_linkedin_id(profile_url),
                full_name=basic_info.get('name', ''),
                headline=basic_info.get('headline', ''),
                location=basic_info.get('location', ''),
                industry=basic_info.get('industry', ''),
                current_company=basic_info.get('current_company'),
                current_position=basic_info.get('current_position'),
                experience=experience,
                education=education,
                skills=skills,
                languages=self._extract_languages(),
                connections_count=basic_info.get('connections_count'),
                profile_url=profile_url,
                profile_image_url=basic_info.get('profile_image'),
                summary=self._extract_summary(),
                certifications=self._extract_certifications(),
                recommendations=self._extract_recommendations(),
                activity_posts=activity,
                contact_info=contact_info,
                scraped_at=datetime.now(),
                confidence_score=self._calculate_confidence_score(basic_info, experience, education)
            )
            
            logger.info(f"Successfully extracted profile: {profile.full_name}")
            return profile
            
        except TimeoutException:
            logger.error(f"Timeout while loading profile: {profile_url}")
            return None
        except Exception as e:
            logger.error(f"Error extracting profile {profile_url}: {str(e)}")
            return None
    
    def _scroll_profile(self):
        """Hace scroll en el perfil para cargar contenido dinámico."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll hacia abajo
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Esperar a que cargue el contenido
            self._wait_with_jitter(2, 4)
            
            # Calcular nueva altura
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                break
            last_height = new_height
            
            # Límite de scrolls para evitar loops infinitos
            if new_height > 20000:
                break
    
    def _extract_basic_info(self) -> Dict[str, Any]:
        """Extrae información básica del perfil."""
        try:
            info = {}
            
            # Nombre
            try:
                name_element = self.driver.find_element(By.CSS_SELECTOR, ".text-heading-xlarge")
                info['name'] = name_element.text.strip()
            except NoSuchElementException:
                info['name'] = ""
            
            # Headline
            try:
                headline_element = self.driver.find_element(By.CSS_SELECTOR, ".text-body-medium.break-words")
                info['headline'] = headline_element.text.strip()
            except NoSuchElementException:
                info['headline'] = ""
            
            # Ubicación
            try:
                location_element = self.driver.find_element(By.CSS_SELECTOR, ".text-body-small.inline.t-black--light.break-words")
                info['location'] = location_element.text.strip()
            except NoSuchElementException:
                info['location'] = ""
            
            # Conexiones
            try:
                connections_element = self.driver.find_element(By.CSS_SELECTOR, ".t-black--light.t-normal")
                connections_text = connections_element.text
                connections_match = re.search(r'(\d+)', connections_text.replace(',', ''))
                if connections_match:
                    info['connections_count'] = int(connections_match.group(1))
            except (NoSuchElementException, ValueError):
                info['connections_count'] = None
            
            # Imagen de perfil
            try:
                img_element = self.driver.find_element(By.CSS_SELECTOR, ".pv-top-card-profile-picture__image")
                info['profile_image'] = img_element.get_attribute('src')
            except NoSuchElementException:
                info['profile_image'] = None
            
            return info
            
        except Exception as e:
            logger.error(f"Error extracting basic info: {str(e)}")
            return {}
    
    def _extract_experience(self) -> List[Dict]:
        """Extrae experiencia laboral."""
        try:
            experiences = []
            
            # Buscar sección de experiencia
            try:
                experience_section = self.driver.find_element(By.ID, "experience")
                experience_items = experience_section.find_elements(
                    By.CSS_SELECTOR, 
                    ".artdeco-list__item .pvs-entity"
                )
                
                for item in experience_items:
                    exp = {}
                    
                    # Título del puesto
                    try:
                        title_element = item.find_element(By.CSS_SELECTOR, ".mr1.t-bold")
                        exp['title'] = title_element.text.strip()
                    except NoSuchElementException:
                        continue
                    
                    # Empresa
                    try:
                        company_element = item.find_element(By.CSS_SELECTOR, ".t-14.t-normal")
                        exp['company'] = company_element.text.strip()
                    except NoSuchElementException:
                        exp['company'] = ""
                    
                    # Fechas
                    try:
                        dates_element = item.find_element(By.CSS_SELECTOR, ".t-14.t-black--light")
                        exp['duration'] = dates_element.text.strip()
                        exp['start_date'], exp['end_date'] = self._parse_dates(exp['duration'])
                    except NoSuchElementException:
                        exp['duration'] = ""
                        exp['start_date'] = None
                        exp['end_date'] = None
                    
                    # Ubicación
                    try:
                        location_elements = item.find_elements(By.CSS_SELECTOR, ".t-14.t-black--light")
                        if len(location_elements) > 1:
                            exp['location'] = location_elements[1].text.strip()
                    except:
                        exp['location'] = ""
                    
                    # Descripción
                    try:
                        desc_element = item.find_element(By.CSS_SELECTOR, ".pvs-list__outer-container")
                        exp['description'] = desc_element.text.strip()
                    except NoSuchElementException:
                        exp['description'] = ""
                    
                    experiences.append(exp)
                    
            except NoSuchElementException:
                logger.warning("Experience section not found")
            
            return experiences
            
        except Exception as e:
            logger.error(f"Error extracting experience: {str(e)}")
            return []
    
    def _extract_education(self) -> List[Dict]:
        """Extrae información educativa."""
        try:
            education = []
            
            try:
                education_section = self.driver.find_element(By.ID, "education")
                education_items = education_section.find_elements(
                    By.CSS_SELECTOR,
                    ".artdeco-list__item .pvs-entity"
                )
                
                for item in education_items:
                    edu = {}
                    
                    # Institución
                    try:
                        school_element = item.find_element(By.CSS_SELECTOR, ".mr1.t-bold")
                        edu['school'] = school_element.text.strip()
                    except NoSuchElementException:
                        continue
                    
                    # Grado/Título
                    try:
                        degree_elements = item.find_elements(By.CSS_SELECTOR, ".t-14.t-normal")
                        if degree_elements:
                            edu['degree'] = degree_elements[0].text.strip()
                    except:
                        edu['degree'] = ""
                    
                    # Fechas
                    try:
                        dates_element = item.find_element(By.CSS_SELECTOR, ".t-14.t-black--light")
                        edu['duration'] = dates_element.text.strip()
                        edu['start_date'], edu['end_date'] = self._parse_dates(edu['duration'])
                    except NoSuchElementException:
                        edu['duration'] = ""
                        edu['start_date'] = None
                        edu['end_date'] = None
                    
                    education.append(edu)
                    
            except NoSuchElementException:
                logger.warning("Education section not found")
            
            return education
            
        except Exception as e:
            logger.error(f"Error extracting education: {str(e)}")
            return []
    
    def _extract_skills(self) -> List[str]:
        """Extrae habilidades."""
        try:
            skills = []
            
            try:
                skills_section = self.driver.find_element(By.CSS_SELECTOR, "[data-section='skills']")
                skill_elements = skills_section.find_elements(
                    By.CSS_SELECTOR,
                    ".mr1.t-bold span[aria-hidden='true']"
                )
                
                for element in skill_elements:
                    skill = element.text.strip()
                    if skill and skill not in skills:
                        skills.append(skill)
                        
            except NoSuchElementException:
                logger.warning("Skills section not found")
            
            return skills[:50]  # Limitar a 50 skills
            
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            return []
    
    def _extract_summary(self) -> Optional[str]:
        """Extrae el resumen/about del perfil."""
        try:
            summary_section = self.driver.find_element(By.ID, "about")
            summary_element = summary_section.find_element(
                By.CSS_SELECTOR,
                ".full-width.t-14.t-normal.t-black.display-flex.align-items-center"
            )
            return summary_element.text.strip()
        except NoSuchElementException:
            return None
        except Exception as e:
            logger.error(f"Error extracting summary: {str(e)}")
            return None
    
    def _extract_languages(self) -> List[str]:
        """Extrae idiomas."""
        try:
            languages = []
            
            try:
                # Buscar sección de idiomas
                lang_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "[data-section='languages'] .mr1.t-bold span"
                )
                
                for element in lang_elements:
                    lang = element.text.strip()
                    if lang and lang not in languages:
                        languages.append(lang)
                        
            except NoSuchElementException:
                pass
            
            return languages
            
        except Exception as e:
            logger.error(f"Error extracting languages: {str(e)}")
            return []
    
    def _extract_certifications(self) -> List[Dict]:
        """Extrae certificaciones."""
        try:
            certifications = []
            
            try:
                cert_section = self.driver.find_element(By.CSS_SELECTOR, "[data-section='certifications']")
                cert_items = cert_section.find_elements(By.CSS_SELECTOR, ".artdeco-list__item")
                
                for item in cert_items:
                    cert = {}
                    
                    # Nombre de la certificación
                    try:
                        name_element = item.find_element(By.CSS_SELECTOR, ".mr1.t-bold")
                        cert['name'] = name_element.text.strip()
                    except NoSuchElementException:
                        continue
                    
                    # Organización
                    try:
                        org_element = item.find_element(By.CSS_SELECTOR, ".t-14.t-normal")
                        cert['organization'] = org_element.text.strip()
                    except NoSuchElementException:
                        cert['organization'] = ""
                    
                    # Fecha
                    try:
                        date_element = item.find_element(By.CSS_SELECTOR, ".t-14.t-black--light")
                        cert['date'] = date_element.text.strip()
                    except NoSuchElementException:
                        cert['date'] = ""
                    
                    certifications.append(cert)
                    
            except NoSuchElementException:
                pass
            
            return certifications
            
        except Exception as e:
            logger.error(f"Error extracting certifications: {str(e)}")
            return []
    
    def _extract_recommendations(self) -> List[Dict]:
        """Extrae recomendaciones."""
        try:
            recommendations = []
            
            try:
                rec_section = self.driver.find_element(By.CSS_SELECTOR, "[data-section='recommendations']")
                rec_items = rec_section.find_elements(By.CSS_SELECTOR, ".artdeco-list__item")
                
                for item in rec_items:
                    rec = {}
                    
                    # Texto de la recomendación
                    try:
                        text_element = item.find_element(By.CSS_SELECTOR, ".t-14.t-normal")
                        rec['text'] = text_element.text.strip()
                    except NoSuchElementException:
                        continue
                    
                    # Nombre del recomendador
                    try:
                        author_element = item.find_element(By.CSS_SELECTOR, ".mr1.t-bold")
                        rec['author'] = author_element.text.strip()
                    except NoSuchElementException:
                        rec['author'] = ""
                    
                    recommendations.append(rec)
                    
            except NoSuchElementException:
                pass
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error extracting recommendations: {str(e)}")
            return []
    
    def _extract_contact_info(self) -> Dict[str, Any]:
        """Extrae información de contacto."""
        try:
            contact_info = {}
            
            # Hacer clic en el botón de contacto
            try:
                contact_button = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "[data-control-name='contact_see_more']"
                )
                contact_button.click()
                self._wait_with_jitter(1, 2)
                
                # Extraer información del modal
                modal = self.driver.find_element(By.CSS_SELECTOR, ".artdeco-modal")
                
                # Email
                try:
                    email_element = modal.find_element(By.CSS_SELECTOR, "[href^='mailto:']")
                    contact_info['email'] = email_element.get_attribute('href').replace('mailto:', '')
                except NoSuchElementException:
                    pass
                
                # Teléfono
                try:
                    phone_elements = modal.find_elements(By.CSS_SELECTOR, ".t-14.t-black")
                    for element in phone_elements:
                        text = element.text.strip()
                        if re.match(r'[\+\d\s\-\(\)]+', text) and len(text) > 7:
                            contact_info['phone'] = text
                            break
                except:
                    pass
                
                # Cerrar modal
                close_button = modal.find_element(By.CSS_SELECTOR, ".artdeco-modal__dismiss")
                close_button.click()
                
            except NoSuchElementException:
                pass
            
            return contact_info
            
        except Exception as e:
            logger.error(f"Error extracting contact info: {str(e)}")
            return {}
    
    def _extract_recent_activity(self) -> List[Dict]:
        """Extrae actividad reciente."""
        try:
            activity = []
            
            try:
                activity_section = self.driver.find_element(By.CSS_SELECTOR, "[data-section='activity']")
                activity_items = activity_section.find_elements(By.CSS_SELECTOR, ".artdeco-list__item")
                
                for item in activity_items[:10]:  # Limitar a 10 posts recientes
                    post = {}
                    
                    # Texto del post
                    try:
                        text_element = item.find_element(By.CSS_SELECTOR, ".feed-shared-text")
                        post['text'] = text_element.text.strip()
                    except NoSuchElementException:
                        continue
                    
                    # Fecha
                    try:
                        date_element = item.find_element(By.CSS_SELECTOR, ".t-12.t-black--light")
                        post['date'] = date_element.text.strip()
                    except NoSuchElementException:
                        post['date'] = ""
                    
                    # Tipo de actividad
                    try:
                        type_element = item.find_element(By.CSS_SELECTOR, ".feed-shared-actor__meta")
                        post['type'] = type_element.text.strip()
                    except NoSuchElementException:
                        post['type'] = ""
                    
                    activity.append(post)
                    
            except NoSuchElementException:
                pass
            
            return activity
            
        except Exception as e:
            logger.error(f"Error extracting activity: {str(e)}")
            return []
    
    def _parse_dates(self, date_string: str) -> tuple:
        """Parsea cadenas de fecha de LinkedIn."""
        try:
            # Patrones comunes de fechas en LinkedIn
            patterns = [
                r'(\w+\s\d{4})\s*–\s*(\w+\s\d{4})',
                r'(\w+\s\d{4})\s*–\s*(Present|Presente)',
                r'(\d{4})\s*–\s*(\d{4})',
                r'(\d{4})\s*–\s*(Present|Presente)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_string)
                if match:
                    start_date = match.group(1)
                    end_date = match.group(2) if match.group(2) not in ['Present', 'Presente'] else None
                    return start_date, end_date
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error parsing dates: {str(e)}")
            return None, None
    
    def _extract_linkedin_id(self, profile_url: str) -> str:
        """Extrae el ID de LinkedIn de la URL."""
        try:
            # Buscar patrón /in/username/
            match = re.search(r'/in/([^/]+)/', profile_url)
            if match:
                return match.group(1)
            
            # Fallback: usar hash de la URL
            return hashlib.md5(profile_url.encode()).hexdigest()
            
        except Exception:
            return hashlib.md5(profile_url.encode()).hexdigest()
    
    def _calculate_confidence_score(self, basic_info: Dict, experience: List, education: List) -> float:
        """Calcula un score de confianza basado en la completitud de los datos."""
        score = 0.0
        max_score = 10.0
        
        # Información básica (30%)
        if basic_info.get('name'):
            score += 1.0
        if basic_info.get('headline'):
            score += 1.0
        if basic_info.get('location'):
            score += 1.0
        
        # Experiencia (40%)
        if experience:
            score += 2.0
            if len(experience) >= 3:
                score += 1.0
            if any(exp.get('description') for exp in experience):
                score += 1.0
        
        # Educación (20%)
        if education:
            score += 1.0
            if len(education) >= 2:
                score += 1.0
        
        # Información adicional (10%)
        if basic_info.get('profile_image'):
            score += 0.5
        if basic_info.get('connections_count'):
            score += 0.5
        
        return min(score / max_score, 1.0)
    
    async def search_profiles(self, search_query: str, filters: Dict = None) -> List[str]:
        """Busca perfiles de LinkedIn basado en criterios."""
        try:
            if not self.driver:
                self.driver = self._setup_driver()
                if not self._login_to_linkedin():
                    raise Exception("Failed to login to LinkedIn")
            
            # Construir URL de búsqueda
            base_url = "https://www.linkedin.com/search/results/people/"
            params = {
                'keywords': search_query,
                'origin': 'SWITCH_SEARCH_VERTICAL'
            }
            
            # Añadir filtros
            if filters:
                if filters.get('location'):
                    params['geoUrn'] = f"[{filters['location']}]"
                if filters.get('current_company'):
                    params['currentCompany'] = f"[{filters['current_company']}]"
                if filters.get('industry'):
                    params['industry'] = f"[{filters['industry']}]"
            
            # Construir URL completa
            search_url = base_url + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
            
            profile_urls = []
            page = 1
            max_pages = filters.get('max_pages', 5) if filters else 5
            
            while page <= max_pages:
                try:
                    # Navegar a la página de resultados
                    page_url = f"{search_url}&page={page}"
                    self.driver.get(page_url)
                    self._wait_with_jitter(3, 5)
                    
                    # Extraer URLs de perfil
                    profile_links = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        ".entity-result__title-text a[href*='/in/']"
                    )
                    
                    if not profile_links:
                        logger.info(f"No more profiles found on page {page}")
                        break
                    
                    for link in profile_links:
                        url = link.get_attribute('href')
                        if url and '/in/' in url:
                            clean_url = url.split('?')[0]  # Remover parámetros
                            if clean_url not in profile_urls:
                                profile_urls.append(clean_url)
                    
                    logger.info(f"Found {len(profile_links)} profiles on page {page}")
                    page += 1
                    
                    # Delay entre páginas
                    self._wait_with_jitter(5, 10)
                    
                except Exception as e:
                    logger.error(f"Error on search page {page}: {str(e)}")
                    break
            
            logger.info(f"Total profiles found: {len(profile_urls)}")
            return profile_urls
            
        except Exception as e:
            logger.error(f"Error searching profiles: {str(e)}")
            return []
    
    async def scrape_profiles_batch(self, profile_urls: List[str]) -> List[LinkedInProfile]:
        """Scrape múltiples perfiles en lotes."""
        profiles = []
        
        try:
            if not self.driver:
                self.driver = self._setup_driver()
                if not self._login_to_linkedin():
                    raise Exception("Failed to login to LinkedIn")
            
            for i, url in enumerate(profile_urls):
                try:
                    logger.info(f"Scraping profile {i+1}/{len(profile_urls)}: {url}")
                    
                    profile = self._extract_profile_data(url)
                    if profile:
                        profiles.append(profile)
                    
                    # Delay entre perfiles para evitar detección
                    if i < len(profile_urls) - 1:
                        self._wait_with_jitter(10, 20)
                    
                    # Rotar cuenta cada cierto número de perfiles
                    if (i + 1) % 50 == 0:
                        logger.info("Rotating account...")
                        self.driver.quit()
                        self.driver = self._setup_driver()
                        if not self._login_to_linkedin():
                            logger.error("Failed to login with new account")
                            break
                    
                except Exception as e:
                    logger.error(f"Error scraping profile {url}: {str(e)}")
                    continue
            
            return profiles
            
        except Exception as e:
            logger.error(f"Error in batch scraping: {str(e)}")
            return profiles
        finally:
            if self.driver:
                self.driver.quit()
    
    def __del__(self):
        """Cleanup del driver al destruir el objeto."""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass