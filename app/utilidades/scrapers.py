# /home/pablollh/app/scrapers.py

# Módulos estándar de Python
import json
import asyncio
import logging
import random
import requests
import aiohttp
from django.db import transaction
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Librerías de terceros

from abc import ABC, abstractmethod
from aiohttp import ClientTimeout
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from prometheus_client import Counter, Histogram, start_http_server
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options

# Funcionalidad de Django
from asgiref.sync import sync_to_async
from django.utils.timezone import now

# Modelos y componentes de la aplicación
from app.models import (
    DominioScraping, Vacante, RegistroScraping, ConfiguracionBU,
    BusinessUnit, PLATFORM_CHOICES
)
from app.utilidades.loader import DIVISION_SKILLS, DIVISIONES, BUSINESS_UNITS
from app.chatbot.utils import clean_text
from app.chatbot import ChatBotHandler  # Solo si se usa en scraping

# ========================
# Scrapers Específicos
# ========================
# Aquí incluyes clases como WorkdayScraper, OracleScraper, FlexibleScraper, etc.
# Usa la estructura modular propuesta en tu código original.

class FlexibleScraper(BaseScraper):
    def __init__(self, url, config=None, cookies=None):
        self.url = url
        self.config = config or ScraperConfig()
        self.cookies = cookies

    async def parse_jobs(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []
        
        job_containers = soup.find_all("div", class_="job-card")
        
        for container in job_containers:
            job = {}
            for field, params in self.config.items():
                element = container.select_one(params['selector'])
                if element:
                    job[field] = element.get_text(strip=True) if params['method'] == 'text' else element.decode_contents()
            
            jobs.append(job)
        
        return jobs
# Implementaciones específicas de scrapers
class WorkdayScraper:
    def __init__(self, url, cookies=None):
        self.url = url
        self.cookies = cookies or {}

    async def scrape(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)

        try:
            logger.info(f"Iniciando scraping con Selenium para: {self.url}")
            driver.get(self.url)
            driver.implicitly_wait(12) # Esperar a que el contenido dinámico se cargue

            # Extraer contenido renderizado
            soup = BeautifulSoup(driver.page_source, "html.parser")
            job_elements = soup.find_all("a", {"data-automation-id": "jobTitle"})

            vacantes = []
            for job in job_elements:
                title = job.text.strip()
                link = job["href"]
                full_link = f"{self.url.split('/job-search')[0]}{link}"
                vacantes.append({
                    "title": title,
                    "url": full_link,
                    "location": "No disponible",  # Puedes mejorar con más scraping
                })

            logger.info(f"Total de vacantes extraídas: {len(vacantes)}")
            return vacantes  # Lista sincronizada

        except Exception as e:
            logger.error(f"Error durante el scraping: {e}")
            return []

        finally:
            driver.quit()

class PhenomPeopleScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        logger.info(f"Iniciando PhenomPeopleScraper para dominio: {self.dominio}")
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}?page={page}"
                try:
                    response = await self.fetch(session, url)
                    if not response:
                        logger.warning(f"No se obtuvo respuesta en {url}. Finalizando scraping.")
                        break
                    soup = BeautifulSoup(response, "html.parser")
                    jobs = await self.parse_jobs(soup)
                    if not jobs:
                        logger.info(f"No se encontraron más vacantes en {url}.")
                        break
                    vacantes.extend(jobs)
                    logger.debug(f"Página {page}: {len(jobs)} vacantes extraídas.")
                    page += 1
                except Exception as e:
                    logger.error(f"Error en PhenomPeopleScraper (página {page}): {e}")
                    break
        return vacantes

    async def parse_jobs(self, soup):
        jobs = []
        job_cards = soup.find_all("div", class_="job-card")  # Ajustar el selector
        for card in job_cards:
            try:
                title = card.find("h3").get_text(strip=True)
                location = card.find("span", class_="job-location").get_text(strip=True)
                link = card.find("a", href=True)["href"]
                jobs.append({"title": title, "location": location, "link": link})
            except AttributeError as e:
                logger.warning(f"Error procesando una tarjeta de trabajo: {e}")
                continue
        return jobs
    
class OracleScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}/jobs?page={page}"
                try:
                    response = await self.fetch(session, url)
                    if not response:
                        break

                    # Verifica si la respuesta es un string o JSON
                    if isinstance(response, str):
                        logger.error(f"Respuesta inesperada: texto plano en lugar de JSON")
                        break

                    jobs = await self.parse_jobs(response)
                    if not jobs:
                        break
                    vacantes.extend(jobs)
                    page += 1
                except Exception as e:
                    logger.error(f"Error en OracleScraper: {e}")
                    break
        return vacantes

    async def parse_jobs(self, data):
        vacantes = []
        for job in data.get('jobList', []):
            vacantes.append({
                "title": job.get("title", "No especificado"),
                "location": job.get("location", {}).get("city", "No especificado"),
                "link": job.get("detailUrl"),
                "details": await self.get_job_details(job.get("detailUrl"))
            })
        return vacantes

    async def get_job_details(self, job_url):
        async with aiohttp.ClientSession() as session:
            try:
                response = await self.fetch(session, f"{self.dominio}{job_url}")
                soup = BeautifulSoup(response, "html.parser")

                return {
                    "description": soup.find("div", class_="job-description").get_text(strip=True) if soup.find("div", class_="job-description") else "No disponible",
                    "requirements": soup.find("div", class_="job-requirements").get_text(strip=True) if soup.find("div", class_="job-requirements") else "No disponible",
                    "benefits": soup.find("div", class_="job-benefits").get_text(strip=True) if soup.find("div", class_="job-benefits") else "No disponible",
                }
            except Exception as e:
                logger.error(f"Error obteniendo detalles del trabajo: {e}")
                return {}

class SAPScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}/jobs?page={page}"
                try:
                    response = await self.fetch(session, url)
                    jobs = await self.parse_jobs(response)
                    if not jobs:
                        break
                    vacantes.extend(jobs)
                    page += 1
                except Exception as e:
                    logger.error(f"Error en SAPScraper: {e}")
                    break
        return vacantes

    async def parse_jobs(self, data):
        vacantes = []
        for job in data.get('jobs', []):
            vacantes.append({
                "title": clean_text(job.get("title", "No especificado")),
                "location": clean_text(job.get("location", {}).get("city", "No especificado")),
                "link": job.get("detailUrl"),
                "details": await self.get_job_details(job.get("detailUrl"))
            })
        return vacantes

    async def get_job_details(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                response = await self.fetch(session, f"{self.dominio}{url}")
                soup = BeautifulSoup(response, 'html.parser')
                return {
                    "description": soup.find("div", class_="job-description").get_text(strip=True) if soup.find("div", class_="job-description") else "No disponible",
                    "requirements": soup.find("div", class_="job-requirements").get_text(strip=True) if soup.find("div", class_="job-requirements") else "No disponible",
                    "benefits": soup.find("div", class_="job-benefits").get_text(strip=True) if soup.find("div", class_="job-benefits") else "No disponible"
                }
        except Exception as e:
            logger.error(f"Error obteniendo detalles del trabajo en SAP: {e}")
            return {}
        
class LinkedInScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 0
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}?start={page * 25}"
                try:
                    response = await self.fetch(session, url)
                    soup = BeautifulSoup(response, 'html.parser')
                    jobs = await self.parse_jobs(soup)
                    if not jobs:
                        break
                    vacantes.extend(jobs)
                    page += 1
                except Exception as e:
                    logger.error(f"Error en LinkedInScraper: {e}")
                    break
        return vacantes

    async def parse_jobs(self, soup):
        jobs = []
        job_cards = soup.find_all("div", class_="result-card__contents")
        for card in job_cards:
            title = card.find("h3", class_="job-card-list__titlee").get_text(strip=True)
            company = card.find("h4", class_="job-card-container__company-name").get_text(strip=True)
            location = card.find("span", class_="job-card-container__metadata-item").get_text(strip=True)
            link = card.find("a", class_="job-card-container__link")['href']
            jobs.append({"title": title, "company": company, "location": location, "link": link})
        return jobs
    
class IndeedScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 0
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}?start={page * 10}"
                try:
                    response = await self.fetch(session, url)
                    soup = BeautifulSoup(response, 'html.parser')
                    jobs = await self.parse_jobs(soup)
                    if not jobs:
                        break
                    vacantes.extend(jobs)
                    page += 1
                except Exception as e:
                    logger.error(f"Error en IndeedScraper: {e}")
                    break
        return vacantes

    async def parse_jobs(self, soup):
        jobs = []
        job_cards = soup.find_all("div", class_="job_seen_beacon")
        for card in job_cards:
            title = card.find("h2", class_="jobTitle").get_text(strip=True)
            company = card.find("span", class_="companyName").get_text(strip=True)
            location = card.find("div", class_="companyLocation").get_text(strip=True)
            link = card.find("a", class_="jcs-JobTitle")['href']
            jobs.append({"title": title, "company": company, "location": location, "link": link})
        return jobs

class ADPScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}/search?page={page}"
                try:
                    response = await self.fetch(session, url)
                    data = json.loads(response)
                    jobs = await self.parse_jobs(data)
                    if not jobs:
                        break
                    vacantes.extend(jobs)
                    page += 1
                except Exception as e:
                    logger.error(f"Error en ADPScraper: {e}")
                    break
        return vacantes

    async def parse_jobs(self, data):
        return [
            {
                "title": job.get("jobTitle", "No especificado"),
                "location": job.get("jobLocation", "No especificado"),
                "link": job.get("jobUrl", "No disponible"),
            }
            for job in data.get("jobs", [])
        ]

class PeopleSoftScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        async with aiohttp.ClientSession() as session:
            url = f"{self.dominio}/joblist"
            try:
                response = await self.fetch(session, url)
                soup = BeautifulSoup(response, 'html.parser')
                vacantes = await self.parse_jobs(soup)
            except Exception as e:
                logger.error(f"Error en PeopleSoftScraper: {e}")
        return vacantes

    async def parse_jobs(self, soup):
        jobs = []
        for job_card in soup.find_all("div", class_="job-card"):
            title = job_card.find("h3").get_text(strip=True)
            location = job_card.find("span", class_="location").get_text(strip=True)
            link = job_card.find("a", href=True)["href"]
            jobs.append({"title": title, "location": location, "link": link})
        return jobs

class Meta4Scraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        async with aiohttp.ClientSession() as session:
            url = f"{self.dominio}/opportunities"
            try:
                response = await self.fetch(session, url)
                soup = BeautifulSoup(response, 'html.parser')
                vacantes = await self.parse_jobs(soup)
            except Exception as e:
                logger.error(f"Error en Meta4Scraper: {e}")
        return vacantes

    async def parse_jobs(self, soup):
        return [
            {
                "title": job.find("h3").get_text(strip=True),
                "location": job.find("span", class_="location").get_text(strip=True),
                "link": job.find("a", href=True)["href"],
            }
            for job in soup.find_all("div", class_="job-item")
        ]

class CornerstoneScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}/joblist?page={page}"
                try:
                    response = await self.fetch(session, url)
                    jobs = await self.parse_jobs(response)
                    if not jobs:
                        break
                    vacantes.extend(jobs)
                    page += 1
                except Exception as e:
                    logger.error(f"Error en CornerstoneScraper: {e}")
                    break
        return vacantes

    async def parse_jobs(self, data):
        return [
            {
                "title": job.get("title", "No especificado"),
                "location": job.get("location", "No especificado"),
                "link": job.get("url", "No disponible"),
            }
            for job in data.get("jobs", [])
        ]

class UKGScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}/search?page={page}"
                try:
                    response = await self.fetch(session, url)
                    data = json.loads(response)
                    jobs = await self.parse_jobs(data)
                    if not jobs:
                        break
                    vacantes.extend(jobs)
                    page += 1
                except Exception as e:
                    logger.error(f"Error en UKGScraper: {e}")
                    break
        return vacantes

    async def parse_jobs(self, data):
        return [
            {
                "title": job.get("title", "No especificado"),
                "location": job.get("location", "No especificado"),
                "link": job.get("url", "No disponible"),
            }
            for job in data.get("results", [])
        ]

class GreenhouseScraper(BaseScraper):
    async def scrape(self):
        vacantes = []
        page = 1
        logger.info(f"Iniciando Greenhouse para dominio: {self.dominio}")
        
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.dominio}?page={page}"
                try:
                    response = await self.fetch(session, url)
                    if not response:
                        logger.warning(f"Sin respuesta en {url}. Finalizando scraping.")
                        break

                    jobs = await self.parse_jobs(response)
                    if not jobs:
                        logger.info(f"No se encontraron más vacantes en {url}.")
                        break

                    vacantes.extend(jobs)
                    logger.debug(f"Página {page}: {len(jobs)} vacantes extraídas.")
                    page += 1
                except Exception as e:
                    logger.error(f"Error en scraping Workday (página {page}): {e}", exc_info=True)
                    break

        logger.info(f"Greenhouse finalizado. Total de vacantes: {len(vacantes)}")
        return vacantes

    async def parse_jobs(self, response):
        try:
            soup = BeautifulSoup(response, "html.parser")
            job_cards = soup.find_all("div", class_="opening")
            return [
                {
                    "title": job.find("a").get_text(strip=True),
                    "location": job.find("span", class_="location").get_text(strip=True),
                    "link": job.find("a")["href"]
                }
                for job in job_cards
            ]
        except Exception as e:
            logger.error(f"Error procesando trabajos: {e}")
            return []
    def get_job_details(self, link):
        """
        Obtiene detalles adicionales de una vacante desde su página específica.
        """
        try:
            full_url = f"{self.dominio}{link}"
            response = self.get(full_url)
            if not response:
                return {"description": "No disponible"}
            soup = BeautifulSoup(response, "html.parser")
            description = soup.find("div", class_="section-wrapper").get_text(strip=True)
            return {"description": description}
        except Exception as e:
            logger.error(f"Error obteniendo detalles del trabajo: {e}")
            return {"description": "Error al obtener detalles"}

class GlassdoorScraper(BaseScraper):
    async def extract_jobs(self, url):
        # Implementar scraping específico de Glassdoor
        return []

class ComputrabajoScraper(BaseScraper):
    async def extract_jobs(self, url):
        # Implementar scraping específico de Computrabajo
        return []
# Implementación específica para Accenture
class AccentureScraper(BaseScraper):
    async def scrape(self) -> List[JobListing]:
        vacantes = []
        page = 1
        logger.info(f"Iniciando AccentureScraper para dominio: {self.domain}")

        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.domain}/mx-es/careers/jobsearch?pg={page}"
                logger.info(f"Procesando página: {page}")

                try:
                    response = await self.fetch_with_retry(session, url)
                    if not response:
                        logger.warning(f"Sin respuesta en {url}. Finalizando scraping.")
                        break

                    jobs = self.parse_jobs(response)
                    if not jobs:
                        logger.info(f"No se encontraron más vacantes en {url}.")
                        break

                    vacantes.extend(jobs)
                    logger.debug(f"Página {page}: {len(jobs)} vacantes extraídas.")
                    page += 1
                except Exception as e:
                    logger.error(f"Error procesando página {page}: {e}", exc_info=True)
                    break

        logger.info(f"AccentureScraper finalizado. Total de vacantes: {len(vacantes)}")
        return vacantes

    async def parse_jobs(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        job_cards = soup.find_all("div", class_="cmp-teaser card")
        if not job_cards:
            logger.warning("No se encontraron tarjetas de empleo en la página.")
            return []

        vacantes = []
        for card in job_cards:
            try:
                title = card.find("h3", class_="cmp-teaser__title").get_text(strip=True) if card.find("h3", class_="cmp-teaser__title") else "No especificado"
                detail_link = card.find("a", class_="cmp-teaser__title-link")
                detail_url = f"https://www.accenture.com{detail_link['href']}" if detail_link and 'href' in detail_link.attrs else None
                location = f"{card.find('div', class_='cmp-teaser-region').get_text(strip=True) if card.find('div', class_='cmp-teaser-region') else 'No especificado'}, {card.find('div', class_='cmp-teaser-city').get_text(strip=True) if card.find('div', class_='cmp-teaser-city') else 'No especificado'}"
                skill = card.find("span", class_="cmp-teaser__job-listing-semibold skill").get_text(strip=True) if card.find("span", class_="cmp-teaser__job-listing-semibold skill") else "No especificado"
                posted_date = card.find("p", class_="cmp-teaser__job-listing-posted-date").get_text(strip=True) if card.find("p", class_="cmp-teaser__job-listing-posted-date") else "No especificado"

                details = await self.get_job_details(detail_url) if detail_url else {}
                vacante = {
                    "title": title,
                    "location": location,
                    "skill": skill,
                    "posted_date": posted_date,
                    "detail_url": detail_url,
                    "description": details.get("description", "No disponible")
                }
                vacantes.append(vacante)
            except Exception as e:
                logger.error(f"Error al procesar tarjeta de empleo: {e}", exc_info=True)
                continue
        return vacantes

    async def get_job_details(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                response = await self.fetch(session, url)
                soup = BeautifulSoup(response, 'html.parser')
                description = soup.find("div", class_="job-description").get_text(strip=True) if soup.find("div", class_="job-description") else "No disponible"
                return {"description": description}
        except Exception as e:
            logger.error(f"Error obteniendo detalles del trabajo en {url}: {e}")
            return {"description": "No disponible"}

class EightFoldScraper(BaseScraper):
    def __init__(self, url, config=None, cookies=None):
        super().__init__(url, config=config, cookies=cookies)
        self.base_url = url  # Asegúrate de que este atributo esté inicializado

    async def fetch_with_retry(self, session, url, max_retries=3):
        """Realiza solicitudes con reintentos"""
        for attempt in range(max_retries):
            try:
                async with session.get(url, timeout=30) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                logger.warning(f"Intento {attempt + 1} fallido: {e}")
                if attempt == max_retries - 1:
                    raise

    async def scrape(self) -> List[JobListing]:
        """Scraper principal para EightFold AI"""
        vacantes = []
        page = 1
        
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.base_url}?location={self.location}&page={page}&sort_by=relevance"
                logger.info(f"Procesando página: {page} - {url}")

                try:
                    response = await self.fetch_with_retry(session, url)
                    
                    # Procesar JSON de trabajos
                    jobs = response.get('jobs', [])
                    if not jobs:
                        break

                    # Obtener detalles de cada trabajo
                    job_details = await asyncio.gather(
                        *[self.get_job_details(session, job) for job in jobs],
                        return_exceptions=True
                    )

                    for job, details in zip(jobs, job_details):
                        if isinstance(details, Exception):
                            logger.error(f"Error procesando trabajo: {job.get('title', 'Sin título')}")
                            continue

                        vacante = JobListing(
                            title=job.get('title', 'Sin título'),
                            company=job.get('company_name', 'Sin empresa'),
                            location=job.get('locations', [{}])[0].get('name', 'Sin ubicación'),
                            url=job.get('url', ''),
                            description=details.get('description', 'No description'),
                            requirements=details.get('requirements', 'No requirements')
                        )
                        vacantes.append(vacante)

                    logger.info(f"Página {page}: {len(jobs)} vacantes procesadas")
                    page += 1

                except Exception as e:
                    logger.error(f"Error procesando página {page}: {e}", exc_info=True)
                    break

        logger.info(f"Finalizado EightFold AI Scraper. Total vacantes: {len(vacantes)}")
        return vacantes

    async def get_job_details(self, session, job):
        """Obtiene detalles específicos de un trabajo"""
        async with self.semaphore:
            try:
                job_url = job.get('url')
                if not job_url:
                    return {}

                async with session.get(job_url) as response:
                    response.raise_for_status()
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Extracción de descripción y requisitos
                    description_elem = soup.find('div', class_='job-description')
                    requirements_elem = soup.find('div', class_='job-requirements')

                    return {
                        'description': description_elem.get_text(strip=True) if description_elem else 'No description',
                        'requirements': requirements_elem.get_text(strip=True) if requirements_elem else 'No requirements'
                    }
            except Exception as e:
                logger.error(f"Error obteniendo detalles del trabajo: {e}")
                return {}

class FlexibleScraper(BaseScraper):
    def __init__(self, dominio_scraping):
        super().__init__(dominio_scraping.dominio)
        self.configuracion = dominio_scraping

    async def scrape(self):
        async with aiohttp.ClientSession(cookies=self.configuracion.cookies or {}) as session:
            response = await self.fetch(session, self.configuracion.dominio)
            soup = BeautifulSoup(response, 'html.parser')

            vacantes = []
            job_cards = self.get_elements(soup, self.configuracion.selector_job_cards)

            for card in job_cards:
                vacante = {
                    'titulo': self.extract_dato(card, self.configuracion.selector_titulo),
                    'descripcion': self.extract_dato(card, self.configuracion.selector_descripcion),
                    'ubicacion': self.extract_dato(card, self.configuracion.selector_ubicacion),
                    'salario': self.extract_dato(card, self.configuracion.selector_salario),
                }
                vacantes.append(vacante)

            return vacantes

    def get_elements(self, soup, selector):
        """Obtiene los elementos con el selector configurado."""
        if not selector:
            return []
        try:
            return soup.select(selector)
        except Exception as e:
            logger.warning(f"Error al obtener elementos con selector {selector}: {e}")
            return []

    def extract_dato(self, elemento, selector):
        """Extrae datos usando el selector configurado."""
        if not selector:
            return None
        try:
            return elemento.select_one(selector).get_text(strip=True)
        except Exception as e:
            logger.warning(f"No se pudo extraer dato con selector {selector}: {e}")
            return None

# ========================
# Mapeo de Scrapers
# ========================

SCRAPER_MAP = {
    "workday": WorkdayScraper,
    "phenom_people": PhenomPeopleScraper,
    "oracle_hcm": OracleScraper,
    "sap_successfactors": SAPScraper,
    "adp": ADPScraper,
    "peoplesoft": PeopleSoftScraper,
    "meta4": Meta4Scraper,
    "cornerstone": CornerstoneScraper,
    "ukg": UKGScraper,
    "linkedin": LinkedInScraper,
    "indeed": IndeedScraper,
    "greenhouse": GreenhouseScraper,
    "glassdoor": GlassdoorScraper,
    "computrabajo": ComputrabajoScraper,
    "accenture": AccentureScraper,
    "eightfold_ai": EightFoldScraper,
    "default": BaseScraper,  # Genérico por defecto
    "flexible": FlexibleScraper,
}

