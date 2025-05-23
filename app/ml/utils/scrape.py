# /home/pablo/app/ml/utils/scrape.py
import json
import logging
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from django.utils import timezone
from asgiref.sync import sync_to_async
from app.com.chatbot.utils import ChatbotUtils
from app.models import DominioScraping
import aiohttp
import re
import email  # Importación agregada para manejar email.message.Message

logger = logging.getLogger(__name__)

# Cargar el modelo de embeddings Universal Sentence Encoder
try:
    embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
except Exception as e:
    logger.error(f"Error cargando Universal Sentence Encoder: {e}")
    embed = None

class MLScraper:
    def __init__(self):
        self.model = None  # Placeholder para modelo de clasificación entrenado
        self.training_data_path = "/home/pablo/app/ml/training_data/web.jsonl"
        self.feedback_path = "/home/pablo/app/ml/feedback.jsonl"
        self.platform_patterns = {
            "linkedin": r"linkedin\.com",
            "workday": r"workday\.com",
            "indeed": r"indeed\.com",
            "glassdoor": r"glassdoor\.com",
            "greenhouse": r"greenhouse\.io",
            "accenture": r"accenture\.com",
            "eightfold_ai": r"eightfold\.ai",
            "phenom_people": r"phenompeople\.com",
            "oracle_hcm": r"oracle\.com",
            "sap_successfactors": r"sap\.com",
            "adp": r"adp\.com",
            "peoplesoft": r"peoplesoft\.com",
            "cornerstone": r"cornerstoneondemand\.com",
            "ukg": r"ukg\.com",
            "computrabajo": r"computrabajo\.com",
        }
        logger.info("Inicializando MLScraper")

    async def classify_email(self, message: email.message.Message) -> str:
        """Clasifica la plataforma de un correo electrónico."""
        try:
            text_content = ""
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    text_content += part.get_payload(decode=True).decode(errors='ignore')
                elif part.get_content_type() == "text/html":
                    html = part.get_payload(decode=True).decode(errors='ignore')
                    soup = BeautifulSoup(html, "html.parser")
                    text_content += soup.get_text()

            text_content = ChatbotUtils.clean_text(text_content).lower()
            if not text_content:
                logger.warning("Correo sin contenido legible")
                return "unknown"

            # Buscar patrones de plataformas en el contenido
            for platform, pattern in self.platform_patterns.items():
                if re.search(pattern, text_content):
                    logger.info(f"Plataforma detectada en correo: {platform}")
                    return platform

            # Usar embeddings si no se detecta una plataforma clara
            if embed:
                embedding = embed([text_content]).numpy()[0]
                # Placeholder: Implementar modelo de clasificación entrenado
                # Por ahora, usar heurística basada en palabras clave
                keywords = ["job", "vacante", "opportunity", "empleo", "position"]
                if any(keyword in text_content for keyword in keywords):
                    logger.info("Correo clasificado como job-related por keywords")
                    return "default"  # Plataforma genérica para correos relacionados con empleo
                else:
                    logger.info("Correo no relacionado con vacantes")
                    return "unknown"
            else:
                logger.warning("Embeddings no disponibles, clasificación fallida")
                return "unknown"
        except Exception as e:
            logger.error(f"Error clasificando correo: {e}")
            return "unknown"

    async def classify_page(self, url: str, content: str) -> str:
        """Clasifica la plataforma de una página web."""
        try:
            url_lower = url.lower()
            content_clean = ChatbotUtils.clean_text(content).lower()

            # Buscar patrones de plataformas en la URL
            for platform, pattern in self.platform_patterns.items():
                if re.search(pattern, url_lower):
                    logger.info(f"Plataforma detectada en URL: {platform}")
                    return platform

            # Usar embeddings si no se detecta una plataforma clara
            if embed:
                embedding = embed([content_clean]).numpy()[0]
                # Placeholder: Implementar modelo de clasificación entrenado
                # Por ahora, usar heurística basada en contenido
                job_indicators = ["job", "vacante", "career", "employment", "apply", "position"]
                if any(indicator in content_clean for indicator in job_indicators):
                    logger.info("Página clasificada como job-related por contenido")
                    return "default"
                else:
                    logger.info("Página no relacionada con vacantes")
                    return "unknown"
            else:
                logger.warning("Embeddings no disponibles, clasificación fallida")
                return "unknown"
        except Exception as e:
            logger.error(f"Error clasificando página {url}: {e}")
            return "unknown"

    async def extract_vacancies_from_email(self, message: email.message.Message) -> List[Dict]:
        """Extrae vacantes desde un correo electrónico."""
        try:
            text_content = ""
            html_content = ""
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    text_content += part.get_payload(decode=True).decode(errors='ignore')
                elif part.get_content_type() == "text/html":
                    html_content += part.get_payload(decode=True).decode(errors='ignore')

            # Extraer URLs del contenido
            urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text_content + html_content)
            job_listings = []
            soup = BeautifulSoup(html_content, "html.parser") if html_content else None

            for url in urls:
                # Normalizar URL
                url = url.replace("https://https://", "https://")
                job_data = {
                    "titulo": "Vacante desde correo",
                    "url_original": url,
                    "descripcion": "Extraído de correo",
                    "skills_required": [],
                    "fecha_publicacion": timezone.now(),
                    "ubicacion": "No especificada",
                    "empresa": None,
                    "modalidad": None,
                    "requisitos": "",
                    "beneficios": ""
                }

                # Intentar extraer título desde HTML si está disponible
                if soup:
                    link = soup.find("a", href=re.compile(re.escape(url), re.I))
                    if link:
                        title = link.get_text(strip=True)
                        if title and len(title) > 5:
                            job_data["titulo"] = title[:500]

                job_listings.append(job_data)

            # Extraer información adicional desde HTML si está disponible
            if soup:
                job_rows = soup.find_all("tr") or soup.find_all("div", class_=re.compile("job|vacancy|listing", re.I))
                for row in job_rows:
                    link = row.find("a", href=re.compile(r"https?://"))
                    if link:
                        url = link["href"]
                        title = link.get_text(strip=True)[:500]
                        if title and len(title) > 5:
                            location = row.find(string=re.compile(r"(?:ciudad|área|remote|remoto|híbrido|presencial)", re.I))
                            company = row.find(string=re.compile(r"^[A-Za-z0-9\s&.,-]+$", re.I))
                            job_data = {
                                "titulo": title,
                                "url_original": url,
                                "descripcion": "Extraído de correo",
                                "skills_required": [],
                                "fecha_publicacion": timezone.now(),
                                "ubicacion": location.strip()[:300] if location else "No especificada",
                                "empresa": company.strip() if company else None,
                                "modalidad": (
                                    "Remoto" if location and "remoto" in location.lower() else
                                    "Híbrido" if location and "híbrido" in location.lower() else
                                    "Presencial" if location and "presencial" in location.lower() else None
                                ),
                                "requisitos": "",
                                "beneficios": ""
                            }
                            job_listings.append(job_data)

            logger.info(f"Extraídas {len(job_listings)} vacantes desde correo")
            return job_listings
        except Exception as e:
            logger.error(f"Error extrayendo vacantes desde correo: {e}")
            return []

    async def extract_job_details(self, content: str, platform: str) -> Dict:
        """Extrae detalles de una vacante desde el contenido HTML."""
        try:
            soup = BeautifulSoup(content, "html.parser")
            selectors = {
                "title": ["h1", "h2", ".job-title", "h3"],
                "description": [".job-description", "div.description", "div.job-details", "#jobDescriptionText"],
                "location": [".location", "span.location", ".job-location", "div.companyLocation"],
                "company": [".company", "span.company", ".company-name", "span.companyName"],
                "posted_date": ["span.posted-date", "time", "span.date"],
                "skills": [".skills", "ul.skills", "div.requirements"],
                "requirements": [".requirements", "div.requirements", ".job-requirements"],
                "benefits": [".benefits", "div.benefits", ".job-benefits"]
            }

            job_details = {
                "title": "No especificado",
                "description": "No disponible",
                "location": "Unknown",
                "company": "Unknown",
                "skills": [],
                "posted_date": timezone.now(),
                "modality": "Híbrido",
                "requirements": "",
                "benefits": "",
                "original_url": ""
            }

            # Extraer campos usando selectores
            for field, sel_list in selectors.items():
                for sel in sel_list:
                    elem = soup.select_one(sel)
                    if elem:
                        if field == "skills":
                            job_details[field] = [item.get_text(strip=True) for item in elem.find_all(["li", "span"])]
                        elif field in ["title", "description", "location", "company", "requirements", "benefits"]:
                            job_details[field] = elem.get_text(strip=True)
                        elif field == "posted_date":
                            try:
                                job_details[field] = datetime.strptime(elem.get_text(strip=True), "%Y-%m-%d")
                            except:
                                job_details[field] = timezone.now()
                        break

            # Usar embeddings para extraer habilidades si no se encuentran con selectores
            if not job_details["skills"] and embed:
                job_details["skills"] = self.extract_skills(content)

            # Normalizar datos
            job_details["title"] = job_details["title"][:500]
            job_details["description"] = job_details["description"][:3000]
            job_details["location"] = job_details["location"][:300]
            job_details["requirements"] = job_details["requirements"][:1000]
            job_details["benefits"] = job_details["benefits"][:1000]

            logger.info(f"Detalles extraídos para plataforma {platform}: {job_details['title']}")
            return job_details
        except Exception as e:
            logger.error(f"Error extrayendo detalles de vacante para plataforma {platform}: {e}")
            return {
                "title": "No especificado",
                "description": "No disponible",
                "location": "Unknown",
                "company": "Unknown",
                "skills": [],
                "posted_date": timezone.now(),
                "modality": "Híbrido",
                "requirements": "",
                "benefits": "",
                "original_url": ""
            }

    async def identify_selectors(self, url: str, platform: str) -> Dict:
        """Identifica selectores dinámicamente para una página web."""
        try:
            content = await self.fetch_content(url)
            if not content:
                logger.warning(f"No se pudo obtener contenido para {url}")
                return {}

            soup = BeautifulSoup(content, "html.parser")
            selectors = {
                "job_cards": "",
                "title": "",
                "url": "",
                "description": "",
                "location": "",
                "company": "",
                "posted_date": ""
            }

            # Buscar elementos comunes para job cards
            for tag in ["div", "li", "article"]:
                elements = soup.find_all(tag, class_=re.compile("job|vacancy|listing|card", re.I))
                if elements and len(elements) > 1:  # Asegurar que hay múltiples resultados
                    selectors["job_cards"] = f"{tag}[class*='job'],{tag}[class*='vacancy'],{tag}[class*='listing'],{tag}[class*='card']"
                    break

            # Buscar título
            for tag in ["h1", "h2", "h3"]:
                title = soup.find(tag, string=re.compile("job|vacancy|position", re.I))
                if title:
                    selectors["title"] = tag
                    break

            # Buscar URLs
            links = soup.find_all("a", href=re.compile(r"https?://|job|apply", re.I))
            if links:
                selectors["url"] = "a[href*='job'],a[href*='apply']"

            # Buscar descripción
            for tag in ["div", "section"]:
                desc = soup.find(tag, class_=re.compile("description|details", re.I))
                if desc:
                    selectors["description"] = f"{tag}[class*='description'],{tag}[class*='details']"
                    break

            # Buscar ubicación
            for tag in ["span", "div"]:
                loc = soup.find(tag, string=re.compile("location|city|remote", re.I))
                if loc:
                    selectors["location"] = f"{tag}[class*='location'],{tag}[class*='city']"
                    break

            # Buscar empresa
            for tag in ["span", "div"]:
                comp = soup.find(tag, class_=re.compile("company|employer", re.I))
                if comp:
                    selectors["company"] = f"{tag}[class*='company'],{tag}[class*='employer']"
                    break

            # Buscar fecha de publicación
            for tag in ["span", "time"]:
                date = soup.find(tag, string=re.compile(r"\d{4}-\d{2}-\d{2}|posted|published", re.I))
                if date:
                    selectors["posted_date"] = tag
                    break

            # Usar embeddings para refinar si es necesario
            if embed and not all(selectors.values()):
                embedding = embed([ChatbotUtils.clean_text(content)]).numpy()[0]
                # Placeholder: Usar modelo para identificar patrones de selectores
                logger.info("Usando embeddings para refinar selectores")

            logger.info(f"Selectores identificados para {url}: {selectors}")
            return selectors
        except Exception as e:
            logger.error(f"Error identificando selectores para {url}: {e}")
            return {}

    def extract_skills(self, text: str) -> List[str]:
        """Extrae habilidades desde el texto usando embeddings."""
        try:
            if not embed:
                logger.warning("Embeddings no disponibles para extracción de habilidades")
                return []

            text_clean = ChatbotUtils.clean_text(text).lower()
            # Lista de habilidades comunes para comparar
            common_skills = [
                "python", "sql", "javascript", "java", "aws", "docker", "kubernetes",
                "leadership", "communication", "project management", "data analysis"
            ]
            skills = []
            embedding_text = embed([text_clean]).numpy()[0]

            for skill in common_skills:
                embedding_skill = embed([skill]).numpy()[0]
                similarity = np.dot(embedding_text, embedding_skill) / (
                    np.linalg.norm(embedding_text) * np.linalg.norm(embedding_skill)
                )
                if similarity > 0.7:  # Umbral de similitud
                    skills.append(skill)

            # Buscar habilidades explícitas en el texto
            for skill in common_skills:
                if skill in text_clean and skill not in skills:
                    skills.append(skill)

            logger.info(f"Habilidades extraídas: {skills}")
            return skills
        except Exception as e:
            logger.error(f"Error extrayendo habilidades: {e}")
            return []

    async def save_training_data(self, domain: DominioScraping, jobs: List[Dict], status: str, error: str = None):
        """Guarda datos enriquecidos para reentrenamiento."""
        try:
            training_data = {
                "url": domain.dominio,
                "platform": domain.plataforma,
                "vacancies_found": len(jobs),
                "status": status,
                "error": error,
                "jobs": [
                    {
                        "title": job["title"],
                        "description_embedding": (
                            embed([job["description"]]).numpy().tolist() 
                            if job["description"] and embed else []
                        ),
                        "skills": job.get("skills", []),
                        "selectors_used": domain.mapeo_configuracion.get("selectors", {}) 
                        if domain.mapeo_configuracion else {},
                        "location": job.get("location", "Unknown"),
                        "company": job.get("company", "Unknown")
                    } for job in jobs
                ],
                "timestamp": datetime.now().isoformat()
            }
            with open(self.training_data_path, "a") as f:
                f.write(json.dumps(training_data) + "\n")
            logger.info(f"Datos de entrenamiento guardados para {domain.dominio}")
        except Exception as e:
            logger.error(f"Error guardando datos de entrenamiento: {e}")

    async def log_feedback(self, vacante_id: int, success: bool, corrections: Dict = None):
        """Registra retroalimentación para mejorar el modelo."""
        try:
            feedback_data = {
                "vacante_id": vacante_id,
                "success": success,
                "corrections": corrections or {},
                "timestamp": datetime.now().isoformat()
            }
            with open(self.feedback_path, "a") as f:
                f.write(json.dumps(feedback_data) + "\n")
            logger.info(f"Retroalimentación registrada para vacante {vacante_id}")
        except Exception as e:
            logger.error(f"Error registrando retroalimentación: {e}")

    def retrain(self, training_data: List[Dict]):
        """Reentrena el modelo con nuevos datos."""
        try:
            # Placeholder: Implementar lógica de reentrenamiento
            # Ejemplo: Usar TensorFlow para entrenar un modelo de clasificación
            logger.info(f"Reentrenando modelo con {len(training_data)} ejemplos")
            
            # Preparar datos para entrenamiento
            X = []
            y = []
            for data in training_data:
                if data["status"] == "success" and data["jobs"]:
                    for job in data["jobs"]:
                        if job["description_embedding"]:
                            X.append(job["description_embedding"])
                            y.append(data["platform"])
            
            if not X or not y:
                logger.warning("Datos insuficientes para reentrenamiento")
                return

            # Convertir a arrays de NumPy
            X = np.array(X)
            y = np.array(y)

            # Crear y entrenar un modelo simple (ejemplo)
            model = tf.keras.Sequential([
                tf.keras.layers.Dense(128, activation='relu', input_shape=(X.shape[1],)),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(len(set(y)), activation='softmax')
            ])

            model.compile(
                optimizer='adam',
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy']
            )

            # Codificar etiquetas
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            y_encoded = le.fit_transform(y)

            # Entrenar modelo
            model.fit(X, y_encoded, epochs=10, batch_size=32, validation_split=0.2)

            # Guardar modelo
            model.save("/home/pablo/app/ml/models/classifier.h5")
            self.model = model
            logger.info("Modelo reentrenado y guardado con éxito")
        except Exception as e:
            logger.error(f"Error reentrenando modelo: {e}")

    async def fetch_content(self, url: str) -> Optional[str]:
        """Obtiene el contenido de una URL."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        return await response.text()
                    logger.warning(f"Error HTTP {response.status} para {url}")
                    return None
            except Exception as e:
                logger.error(f"Error obteniendo contenido de {url}: {e}")
                return None