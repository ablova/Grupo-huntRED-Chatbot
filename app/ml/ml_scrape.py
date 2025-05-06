# /home/pablo/app/ml/ml_scrape.py

import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Deshabilita GPU
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import spacy
from bs4 import BeautifulSoup
import pickle
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse
import re
import asyncio
import json
from app.utilidades.scraping import ScrapingPipeline

logger = logging.getLogger(__name__)

class MLScraper:
    def __init__(self, model_dir: str = "/home/pablo/app/ml/models"):
        """Inicializa el scraper de ML con modelos preentrenados."""
        self.model_dir = model_dir
        self.email_classifier = None
        self.vectorizer = None
        self.nlp = spacy.load("es_core_news_md")  # Modelo en español para NER
        self.pipeline = ScrapingPipeline()
        self.load_models()

    def load_models(self):
        """Carga los modelos entrenados desde disco."""
        try:
            with open(f"{self.model_dir}/email_classifier.pkl", "rb") as f:
                self.email_classifier = pickle.load(f)
            with open(f"{self.model_dir}/vectorizer.pkl", "rb") as f:
                self.vectorizer = pickle.load(f)
            logger.info("Modelos de ML cargados exitosamente")
        except FileNotFoundError as e:
            logger.warning(f"Modelos no encontrados: {e}. Entrenar modelos primero.")
        except Exception as e:
            logger.error(f"Error cargando modelos: {e}")

    async def train_email_classifier(self, emails: List[Dict], labels: List[str]):
        """Entrena el clasificador de correos con datos etiquetados."""
        if not emails or not labels:
            logger.error("No se proporcionaron datos para entrenamiento")
            raise ValueError("Emails y labels no pueden estar vacíos")
        
        if len(emails) != len(labels):
            logger.error(f"Longitudes no coinciden: {len(emails)} emails, {len(labels)} labels")
            raise ValueError("Longitudes de emails y labels deben coincidir")

        features = [f"{e['From']} {e['Subject']} {e.get('body', '')[:500]}" for e in emails]
        self.vectorizer = TfidfVectorizer(max_features=5000)
        X = self.vectorizer.fit_transform(features)
        X_train, X_test, y_train, y_test = train_test_split(X, labels, test_size=0.2, random_state=42)
        
        self.email_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.email_classifier.fit(X_train, y_train)
        
        # Evaluar el modelo
        y_pred = self.email_classifier.predict(X_test)
        logger.info(f"Reporte de clasificación:\n{classification_report(y_test, y_pred)}")
        accuracy = self.email_classifier.score(X_test, y_test)
        logger.info(f"Precisión del clasificador de correos: {accuracy:.2f}")
        
        # Guardar modelos
        os.makedirs(self.model_dir, exist_ok=True)
        with open(f"{self.model_dir}/email_classifier.pkl", "wb") as f:
            pickle.dump(self.email_classifier, f)
        with open(f"{self.model_dir}/vectorizer.pkl", "wb") as f:
            pickle.dump(self.vectorizer, f)
        logger.info("Modelos guardados exitosamente")

    async def classify_email(self, message: "email.message.Message") -> str:
        """Clasifica la plataforma de origen de un correo electrónico."""
        if not self.email_classifier or not self.vectorizer:
            logger.warning("Modelos no cargados, usando clasificación básica")
            return self._basic_email_classification(message)
        
        sender = message.get("From", "").lower()
        subject = message.get("Subject", "").lower()
        body = self._get_email_body(message)[:500]
        text = f"{sender} {subject} {body}"
        
        X = self.vectorizer.transform([text])
        prediction = self.email_classifier.predict(X)[0]
        logger.debug(f"Correo clasificado como: {prediction}")
        return prediction

    def _basic_email_classification(self, message: "email.message.Message") -> str:
        """Clasificación básica si el modelo no está disponible."""
        sender = message.get("From", "").lower()
        subject = message.get("Subject", "").lower()
        if "linkedin" in sender or "linkedin" in subject:
            return "linkedin"
        elif "indeed" in sender or "indeed" in subject:
            return "indeed"
        elif "computrabajo" in sender or "computrabajo" in subject:
            return "computrabajo"
        elif "workday" in sender or "workday" in subject:
            return "workday"
        elif "glassdoor" in sender or "glassdoor" in subject:
            return "glassdoor"
        return "unknown"

    def _get_email_body(self, message: "email.message.Message") -> str:
        """Extrae el cuerpo del correo en texto plano o HTML."""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/html":
                    return part.get_payload(decode=True).decode("utf-8", errors="ignore")
                elif part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode("utf-8", errors="ignore")
        return message.get_payload(decode=True).decode("utf-8", errors="ignore")

    async def extract_vacancies_from_email(self, message: "email.message.Message") -> List[Dict]:
        """Extrae vacantes de un correo usando NER y reglas adaptativas."""
        body = self._get_email_body(message)
        soup = BeautifulSoup(body, "html.parser")
        text = soup.get_text()
        
        # Usar spaCy para NER
        doc = self.nlp(text)
        job_listings = []
        
        # Identificar entidades relevantes
        for ent in doc.ents:
            if ent.label_ in ["ORG", "LOC", "PER"]:  # Ajustado para spaCy estándar
                job_data = self._extract_job_context(doc, ent)
                if job_data:
                    job_listings.append(job_data)
        
        # Extraer URLs y enriquecer
        urls = [a["href"] for a in soup.find_all("a", href=True)]
        enriched_jobs = await asyncio.gather(
            *(self._enrich_job_from_url(job, url) for job, url in zip(job_listings, urls)),
            return_exceptions=True
        )
        
        valid_jobs = [job for job in enriched_jobs if isinstance(job, dict)]
        logger.info(f"Extraídas {len(valid_jobs)} vacantes del correo")
        return valid_jobs

    def _extract_job_context(self, doc, entity) -> Optional[Dict]:
        """Extrae contexto de una entidad para formar una vacante."""
        context = doc[max(0, entity.start - 20):min(len(doc), entity.end + 20)].text
        title = None
        company = entity.text if entity.label_ == "ORG" else None
        location = entity.text if entity.label_ == "LOC" else "No especificada"
        
        # Intentar extraer título del contexto
        title_match = re.search(r"(?:job|vacante|puesto|position)\s*:\s*([^\n<]+)", context, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
        
        if title or company:
            return {
                "titulo": title or "Sin título",
                "empresa": company,
                "ubicacion": location,
                "descripcion": context[:1000],
                "url_original": "",
                "skills_required": [],
                "fecha_publicacion": None,
                "modalidad": None
            }
        return None

    async def _enrich_job_from_url(self, job: Dict, url: str) -> Dict:
        """Enriquece una vacante scrapeando detalles desde una URL."""
        job["url_original"] = url
        details = await self.pipeline.process([job])
        return details[0] if details else job

    async def classify_page(self, url: str, html_content: str) -> str:
        """Clasifica la plataforma de una página web."""
        domain = re.sub(r"https?://(www\.)?", "", url).split("/")[0]
        if "linkedin" in domain:
            return "linkedin"
        elif "workday" in domain:
            return "workday"
        elif "indeed" in domain:
            return "indeed"
        elif "computrabajo" in domain:
            return "computrabajo"
        return "unknown"

    async def extract_job_details(self, html_content: str, platform: str) -> Dict:
        """Extrae detalles de una vacante desde contenido HTML."""
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text()
        doc = self.nlp(text)
        
        job_data = {
            "titulo": "Sin título",
            "ubicacion": "No especificada",
            "descripcion": "No disponible",
            "empresa": None,
            "skills_required": [],
            "fecha_publicacion": None,
            "modalidad": None,
            "url_original": ""
        }
        
        for ent in doc.ents:
            if ent.label_ == "PER":  # Usamos PER como proxy para títulos
                job_data["titulo"] = ent.text
            elif ent.label_ == "ORG":
                job_data["empresa"] = ent.text
            elif ent.label_ == "LOC":
                job_data["ubicacion"] = ent.text
        
        job_data["descripcion"] = text[:3000]
        return job_data