# /home/pablo/app/ml/ml_scrape.py
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import spacy
from bs4 import BeautifulSoup
import pickle
import os
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse

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
        features = [f"{e['From']} {e['Subject']} {e.get('body', '')[:500]}" for e in emails]
        X = self.vectorizer.fit_transform(features)
        X_train, X_test, y_train, y_test = train_test_split(X, labels, test_size=0.2, random_state=42)
        
        self.email_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.email_classifier.fit(X_train, y_train)
        
        accuracy = self.email_classifier.score(X_test, y_test)
        logger.info(f"Precisión del clasificador de correos: {accuracy:.2f}")
        
        # Guardar modelos
        with open(f"{self.model_dir}/email_classifier.pkl", "wb") as f:
            pickle.dump(self.email_classifier, f)
        with open(f"{self.model_dir}/vectorizer.pkl", "wb") as f:
            pickle.dump(self.vectorizer, f)

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
        return "unknown"

    def _get_email_body(self, message: "email.message.Message") -> str:
        """Extrae el cuerpo del correo en texto plano o HTML."""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/html":
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
            if ent.label_ in ["ORG", "LOC", "JOB_TITLE"]:  # Etiquetas personalizadas o genéricas
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
        title = entity.text if entity.label_ == "JOB_TITLE" else None
        company = entity.text if entity.label_ == "ORG" else None
        location = entity.text if entity.label_ == "LOC" else "No especificada"
        
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
        # TODO: Implementar modelo de clasificación de páginas
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
            if ent.label_ == "JOB_TITLE":
                job_data["titulo"] = ent.text
            elif ent.label_ == "ORG":
                job_data["empresa"] = ent.text
            elif ent.label_ == "LOC":
                job_data["ubicacion"] = ent.text
        
        job_data["descripcion"] = text[:3000]
        return job_data

    async def retrain_models(self, new_data: List[Dict]):
        """Reentrena los modelos con nuevos datos."""
        # TODO: Implementar lógica de reentrenamiento con retroalimentación
        logger.info("Reentrenamiento de modelos pendiente de implementación")

# Example usage for integration with email_scraper.py and scraping.py
if __name__ == "__main__":
    ml_scraper = MLScraper()

    # Example training data (to be replaced with actual data)
    emails = ["Subject: Nueva vacante en LinkedIn", "Subject: Actualiza tu perfil"]
    email_labels = [1, 0]  # 1: job alert, 0: not job alert
    ml_scraper.train_email_classifier(emails, email_labels)

    urls = ["https://www.linkedin.com/jobs/view/123", "https://jobs.workday.com/job/456"]
    platforms = ["linkedin", "workday"]
    ml_scraper.train_platform_classifier(urls, platforms)

    error_data = [{"text": "Short text", "url": "http://example.com"}, {"text": "Long complex HTML" * 100, "url": "http://fail.com"}]
    error_outcomes = [0, 1]  # 0: success, 1: error
    ml_scraper.train_error_predictor(error_data, error_outcomes)