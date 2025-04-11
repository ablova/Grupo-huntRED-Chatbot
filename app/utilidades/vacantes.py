# Ubicación: /home/pablo/app/utilidades/vacantes.py

import requests
import sys
import logging
import aiohttp
import numpy as np
import openai
from openai import OpenAI
from typing import List, Dict, Optional
from functools import lru_cache
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import tensorflow as tf
import tensorflow_hub as hub
from geopy.distance import geodesic
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from asgiref.sync import sync_to_async
from app.models import Worker, Person, GptApi, ConfiguracionBU, BusinessUnit, Vacante
#from app.chatbot.integrations.whatsapp import registro_amigro, nueva_posicion_amigro #Importaciones locales
from app.chatbot.integrations.services import send_email, send_message
from app.ml.ml_model import MatchmakingLearningSystem
from app.chatbot.utils import prioritize_interests, get_positions_by_skills
#import chainlit as cl
#from some_ml_model import match_candidate_to_job  # Tu modelo personalizado


# Configuración del logger En el módulo utilidades
logger = logging.getLogger(__name__)
# Verificación para saltar carga pesada durante migraciones
SKIP_HEAVY_INIT = 'makemigrations' in sys.argv or 'migrate' in sys.argv

# Carga del modelo solo si no estamos en migración
if not SKIP_HEAVY_INIT:
    embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
else:
    embed = None  # O un objeto dummy si es necesario en otras partes del código
def main(message: str) -> None:
    """
    Función principal para procesar mensajes y sugerir vacantes.

    Args:
        message (str): Mensaje recibido del usuario.
    """
    candidate_profile = extract_candidate_profile(message)
    job_matches = match_candidate_to_job(candidate_profile)
    print(f"Encontré estas vacantes para ti: {job_matches}") 

def extract_candidate_profile(message: str) -> Dict:
    """
    Extrae el perfil del candidato desde un mensaje (placeholder).

    Args:
        message (str): Mensaje recibido del candidato.
    Returns:
        Dict: Perfil básico del candidato (simulado).
    """
    # Placeholder: Implementar lógica real según tu sistema
    return {"skills": ["python", "sql"], "location": "CDMX"}

def match_candidate_to_job(profile: Dict) -> List[str]:
    """
    Coincide un perfil de candidato con trabajos (placeholder).

    Args:
        profile (Dict): Perfil del candidato.
    Returns:
        List[str]: Lista de vacantes coincidentes (simulada).
    """
    # Placeholder: Implementar con ML real
    return ["Developer Job 1", "Developer Job 2"]


# Sesión persistente de requests
s = requests.session()

class VacanteManager:
    def __init__(self, job_data: Dict):
        """
        Inicializa el gestor de vacantes con datos de la vacante.

        Args:
            job_data (Dict): Datos de la vacante (business_unit, job_title, etc.).
        Raises:
            ValueError: Si faltan campos requeridos.
        """
        required_fields = ["business_unit", "job_title", "job_description", "company_name"]
        missing_fields = [field for field in required_fields if field not in job_data]
        if missing_fields:
            raise ValueError(f"Faltan campos requeridos: {', '.join(missing_fields)}")
        
        self.job_data = job_data
        self.configuracion = None  # Se inicializará en un método asíncrono
        self.api_url = None
        self.headers = None
        self.client = None

    async def initialize(self):
        """Método asíncrono para inicializar configuraciones."""
        self.configuracion = await sync_to_async(ConfiguracionBU.objects.get)(business_unit=self.job_data['business_unit'])
        self.api_url = self.configuracion.dominio_rest_api or "https://amigro.org/wp-json/wp/v2/job-listings"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.configuracion.jwt_token}',
            'User-Agent': 'VacanteManager/1.0'
        }
        logger.info("Inicializando VacanteManager")
        print("🚀 Inicializando VacanteManager...")

    def _init_openai_client(self) -> bool:
        """
        Inicializa el cliente de OpenAI si no está configurado.

        Returns:
            bool: True si el cliente se inicializó, False si no.
        """
        if self.client is None:
            gpt_api = self.get_gpt_api_config()
            if gpt_api:
                self.client = OpenAI(api_key=gpt_api.api_token, organization=gpt_api.organization)
        return self.client is not None
    
    async def create_job_listing(self) -> Dict[str, str]:
        """
        Crea una vacante en el sistema, dividiendo el proceso en preparación, publicación y notificación.
        """
        logger.info("Iniciando creación de vacante")
        print("📝 Iniciando creación de vacante...")

        try:
            # 1. Verificación y generación de datos
            prepared_data = await self._prepare_job_data()
            if not prepared_data:
                logger.warning("No se pudieron preparar los datos de la vacante")
                print("⚠️ No se pudieron preparar los datos de la vacante")
                return {"status": "error", "message": "Falló la preparación de datos"}

            # 2. Publicación (local y WordPress)
            publish_result = await self._publish_job(prepared_data)
            if publish_result["status"] != "success":
                logger.warning(f"Problema en la publicación: {publish_result['message']}")
                print(f"⚠️ Problema en la publicación: {publish_result['message']}")
            else:
                logger.info("Publicación completada con éxito")
                print("✅ Publicación completada con éxito")

            # 3. Notificaciones
            await self._send_notifications(prepared_data)
            logger.info("Proceso de creación de vacante finalizado")
            print("🎉 Proceso de creación de vacante finalizado")

            return {"status": "success", "message": "Vacante creada y notificaciones enviadas"}
        except Exception as e:
            logger.error(f"Error general en create_job_listing: {e}")
            print(f"❌ Error general en create_job_listing: {e}")
            return {"status": "error", "message": f"Error inesperado: {str(e)}"}

    async def _prepare_job_data(self) -> Optional[Dict]:
        """
        Verifica los datos de entrada, genera etiquetas y prepara el payload para la vacante.
        """
        logger.info("Preparando datos de la vacante")
        print("🔧 Preparando datos de la vacante...")

        try:
            # Verificación inicial: ¿existe la vacante?
            job_link = self.job_data.get("job_link")
            if job_link:
                from .models import Vacante  # Asegúrate de importar tu modelo
                existing_vacante = await sync_to_async(Vacante.objects.filter(url_original=job_link).first)()
                if existing_vacante:
                    logger.info(f"Vacante ya existe: {existing_vacante.titulo}")
                    print(f"ℹ️ Vacante ya existe: {existing_vacante.titulo}")
                    return None

            # Generación de etiquetas
            logger.debug("Generando etiquetas para la vacante")
            print("🏷️ Generando etiquetas...")
            job_tags = self.job_data.get("job_tags") or await self.ensure_tags_exist(
                self.generate_tags(self.job_data["job_description"])
            )
            self.job_data["job_tags"] = job_tags
            logger.debug(f"Etiquetas generadas: {job_tags}")
            print(f"✅ Etiquetas generadas: {job_tags}")

            # Estimación de salario
            logger.debug("Estimando salario")
            print("💰 Estimando salario...")
            salario_min, salario_max = await self.estimate_salary()
            self.job_data["_salary_min"] = salario_min
            self.job_data["_salary_max"] = salario_max
            logger.debug(f"Salario estimado: {salario_min} - {salario_max}")
            print(f"✅ Salario estimado: {salario_min} - {salario_max}")

            # Generación de horarios
            logger.debug("Generando horarios")
            print("⏰ Generando horarios...")
            unidad_trabajo = self.configuracion.business_unit.name.lower()
            duracion_sesion = 45 if unidad_trabajo in ["huntred", "huntu"] else 30
            fecha_inicio = datetime.now() + timedelta(days=15)
            horarios = self.generate_bookings(fecha_inicio, duracion_sesion)
            for i in range(1, 7):
                key = f"job_booking_{i}"
                self.job_data[key] = self.job_data.get(key) or (horarios[i - 1] if len(horarios) > i - 1 else "")
            logger.debug(f"Horarios generados: {horarios}")
            print(f"✅ Horarios generados")

            # Preparar payload
            payload = {
                "title": self.job_data["job_title"],
                "content": self.job_data["job_description"],
                "meta": {
                    "_salary_min": self.job_data["_salary_min"],
                    "_salary_max": self.job_data["_salary_max"],
                    "_job_expires": self.job_data.get("_job_expires", (datetime.now() + timedelta(days=40)).strftime('%Y-%m-%d')),
                    "_apply_link": self.job_data.get("_apply_link", ""),
                    "_job_whatsapp": self.job_data.get("celular_responsable", ""),
                    "_company_name": self.job_data["company_name"],
                    **{f"_job_booking_{i}": self.job_data[f"job_booking_{i}"] for i in range(1, 7)}
                },
                "status": "publish",
                "job_region": self.job_data.get("job_listing_region", "México"),
                "job_type": self.job_data.get("job_listing_type", "Remoto"),
                "remote_position": self.job_data.get("remote_position", "0"),
                "tags": self.job_data["job_tags"],
            }

            logger.info("Datos de la vacante preparados exitosamente")
            print("✅ Datos de la vacante preparados")
            return payload
        except Exception as e:
            logger.error(f"Error preparando datos: {e}")
            print(f"❌ Error preparando datos: {e}")
            return None

    async def _publish_job(self, payload: Dict) -> Dict[str, str]:
        """
        Publica la vacante localmente y en WordPress. Si WordPress falla, sigue con la creación local.
        """
        logger.info("Iniciando publicación de la vacante")
        print("📤 Iniciando publicación de la vacante...")

        try:
            # Publicación local
            logger.debug("Creando vacante en la base de datos local")
            print("💾 Creando vacante localmente...")
            from .models import Vacante  # Asegúrate de importar tu modelo
            vacante = await sync_to_async(Vacante.objects.create)(
                titulo=payload["title"],
                empresa=payload["meta"]["_company_name"],
                descripcion=payload["content"],
                # Otros campos según tu modelo
            )
            logger.info(f"Vacante creada localmente: {vacante.titulo}")
            print(f"✅ Vacante creada localmente: {vacante.titulo}")

            # Publicación en WordPress (no interrumpe si falla)
            logger.debug("Publicando en WordPress")
            print("🌐 Publicando en WordPress...")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.api_url, json=payload, headers=self.headers) as response:
                        if response.status == 201:
                            logger.info(f"Vacante publicada en WordPress: {payload['title']}")
                            print(f"✅ Vacante publicada en WordPress: {payload['title']}")
                        else:
                            logger.warning(f"Fallo al publicar en WordPress: {response.status} - {await response.text()}")
                            print(f"⚠️ Fallo al publicar en WordPress: {response.status}")
            except Exception as e:
                logger.error(f"Error publicando en WordPress: {e}")
                print(f"❌ Error publicando en WordPress: {e} (continúa proceso local)")

            return {"status": "success", "message": "Vacante publicada localmente"}
        except Exception as e:
            logger.error(f"Error publicando la vacante localmente: {e}")
            print(f"❌ Error publicando la vacante localmente: {e}")
            return {"status": "error", "message": f"Error en publicación local: {str(e)}"}

    async def _send_notifications(self, payload: Dict):
        """
        Envía notificaciones por email y WhatsApp a los responsables.
        """
        logger.info("Enviando notificaciones")
        print("📢 Enviando notificaciones...")

        try:
            # Notificación por email
            correo_responsable = self.job_data.get("job_employee-email")
            if correo_responsable:
                logger.debug(f"Preparando email para {correo_responsable}")
                print(f"📧 Preparando email para {correo_responsable}...")
                subject = f"Vacante Creada: {payload['title']}"
                body = (
                    f"<h1>Vacante Creada</h1>"
                    f"<p>Hola {self.job_data.get('job_employee', 'Responsable')},</p>"
                    f"<p>La vacante '{payload['title']}' para '{payload['meta']['_company_name']}' "
                    f"ha sido creada.</p>"
                    f"<ul>"
                    f"<li>Salario: ${payload['meta']['_salary_min']} - ${payload['meta']['_salary_max']} MXN</li>"
                    f"</ul>"
                )
                await self.send_email(self.configuracion.business_unit, subject, correo_responsable, body)
                logger.info(f"Email enviado a {correo_responsable}")
                print(f"✅ Email enviado a {correo_responsable}")

            # Notificación por WhatsApp
            logger.debug("Enviando notificación por WhatsApp")
            print("📱 Enviando notificación por WhatsApp...")
            await self.send_recap_position()
            logger.info("Notificación por WhatsApp enviada")
            print("✅ Notificación por WhatsApp enviada")
        except Exception as e:
            logger.error(f"Error enviando notificaciones: {e}")
            print(f"❌ Error enviando notificaciones: {e}")

    @staticmethod
    @lru_cache(maxsize=1000)
    def get_gpt_api_config() -> Optional[GptApi]:
        """
        Obtiene la configuración de la API de OpenAI desde la base de datos con caché.

        Returns:
            Optional[GptApi]: Configuración de GptApi o None si falla.
        """
        try:
            gpt_api = GptApi.objects.first()
            if not gpt_api:
                logger.warning("No se encontró configuración de GptApi.")
            return gpt_api
        except Exception as e:
            logger.error(f"Error al obtener GptApi: {e}")
            return None

    async def fetch_latest_jobs(self, limit: int = 5) -> List[Dict]:
        """
        Obtiene las últimas vacantes publicadas desde WordPress.

        Args:
            limit (int): Número máximo de vacantes a retornar (default: 5).
        Returns:
            List[Dict]: Lista de vacantes con id y título.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_url,
                    headers=self.headers,
                    params={"_fields": "id,title", "per_page": limit}
                ) as response:
                    response.raise_for_status()
                    jobs = await response.json()
                    logger.info(f"Se obtuvieron {len(jobs)} vacantes.")
                    return jobs
        except aiohttp.ClientError as e:
            logger.error(f"Error al obtener vacantes: {e}")
            return []
        
    @staticmethod
    def generate_bookings(start_date: datetime, session_duration: int) -> List[str]:
        """
        Genera horarios de entrevistas desde una fecha inicial.

        Args:
            start_date (datetime): Fecha inicial para los horarios.
            session_duration (int): Duración de cada sesión en minutos.
        Returns:
            List[str]: Horarios en formato 'YYYY-MM-DD HH:MM'.
        """
        horarios = []
        hora_actual = datetime.combine(start_date.date(), datetime.min.time()).replace(hour=9)
        while hora_actual.time() <= datetime.min.time().replace(hour=14):
            horarios.append(hora_actual.strftime('%Y-%m-%d %H:%M'))
            hora_actual += timedelta(minutes=session_duration)
        logger.debug("Generando horarios de reserva")
        return horarios

    async def estimate_salary(self) -> tuple[str, str]:
        """
        Estima el rango salarial usando OpenAI.

        Returns:
            tuple[str, str]: Salario mínimo y máximo en MXN.
        """
        if not self._init_openai_client():
            logger.warning("No se inicializó OpenAI, usando valores por defecto.")
            return "12000", "15000"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres experto en salarios en México."},
                    {"role": "user", "content": f"Calcula el rango salarial para '{self.job_data['job_title']}' en México.\n"
                                                f"Descripción: {self.job_data['job_description']}\n"
                                                f"Formato: min: $XXXX, max: $YYYY"}
                ],
                max_tokens=50,
                temperature=0.5
            )
            text = response.choices[0].message.content.strip()
            return self.parse_salary_text(text)
        except Exception as e:
            logger.error(f"Error al estimar salario: {e}")
            return "12000", "15000"
        
    def parse_salary_text(self, text: str) -> tuple[str, str]:
        """
        Parsea el texto de salario devuelto por OpenAI.

        Args:
            text (str): Texto en formato "min: $XXXX, max: $YYYY".
        Returns:
            tuple[str, str]: Salario mínimos y máximo.
        """
        try:
            parts = text.split(", ")
            min_salary = parts[0].split("$")[1]
            max_salary = parts[1].split("$")[1]
            return min_salary, max_salary
        except Exception:
            logger.warning("Error al parsear salario, usando valores por defecto.")
            return "12000", "15000"

    async def ensure_tags_exist(self, tags: List[str]) -> List[int]:
        """
        Asegura que las etiquetas existan en WordPress, creando las faltantes.

        Args:
            tags (List[str]): Lista de etiquetas a verificar/crear.
        Returns:
            List[int]: IDs de las etiquetas en WordPress.
        """
        tag_ids = []
        async with aiohttp.ClientSession() as session:
            for tag in tags:
                try:
                    async with session.get(f"{self.api_url}/tags", headers=self.headers, params={"search": tag}) as resp:
                        if resp.status == 200 and (data := await resp.json()):
                            tag_ids.append(data[0]["id"])
                        else:
                            async with session.post(f"{self.api_url}/tags", headers=self.headers, json={"name": tag}) as create_resp:
                                if create_resp.status == 201:
                                    tag_ids.append((await create_resp.json())["id"])
                                else:
                                    logger.error(f"Error creando tag '{tag}': {await create_resp.text()}")
                except Exception as e:
                    logger.error(f"Error con tag '{tag}': {e}")
        logger.debug("Asegurando existencia de etiquetas")
        return tag_ids
    
    def generate_tags(self, job_description: str) -> List[str]:
        """
        Genera etiquetas para la vacante usando OpenAI o respaldo.

        Args:
            job_description (str): Descripción del trabajo.
        Returns:
            List[str]: Etiquetas generadas.
        """
        if not job_description:
            logger.warning("Descripción vacía, no se generan etiquetas.")
            return []

        if not self._init_openai_client():
            return self.generate_tags_backup(job_description)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Genera etiquetas relevantes separadas por comas."},
                    {"role": "user", "content": f"Genera etiquetas para:\n{job_description}"}
                ],
                max_tokens=50,
                temperature=0.5
            )
            tags = response.choices[0].message.content.strip().split(",")
            logger.debug("Generando etiquetas a partir de la descripción")
            return [tag.strip() for tag in tags if tag.strip()]
        except Exception as e:
            logger.warning("OpenAI falló, usando spaCy")
            import spacy
            nlp = spacy.load("es_core_news_sm")
            doc = nlp(job_description)
            tags = list(set([ent.text for ent in doc.ents]))
        return tags

    @staticmethod
    def generate_tags_backup(job_description: str) -> List[str]:
        """
        Genera etiquetas usando TF-IDF como respaldo.

        Args:
            job_description (str): Descripción del trabajo.
        Returns:
            List[str]: Etiquetas generadas.
        """
        vectorizer = TfidfVectorizer(max_features=5, stop_words='english')
        try:
            tfidf_matrix = vectorizer.fit_transform([job_description])
            return vectorizer.get_feature_names_out().tolist()
        except Exception as e:
            logger.error(f"Error en generate_tags_backup: {e}")
            return ["general"]
        
    async def send_recap_position(self) -> None:
        """
        Envía un resumen de la vacante al responsable por WhatsApp.
        """
        logger.debug("Enviando recap por WhatsApp")
        print("Simulando envío por WhatsApp")
        mensaje = (
            f"Resumen:\n"
            f"Posición: {self.job_data['job_title']}\n"
            f"Empresa: {self.job_data['company_name']}\n"
            f"Descripción: {self.job_data['job_description']}\n"
            f"Salario: ${self.job_data['_salary_min']} - ${self.job_data['_salary_max']} MXN\n"
        )
        celular_responsable = self.job_data.get("celular_responsable")
        if celular_responsable:
            await send_message("whatsapp", celular_responsable, mensaje, self.configuracion.business_unit.name)

    @staticmethod
    def match_person_with_jobs(person, job_list):
        """
        Coincide un usuario con una lista de vacantes considerando habilidades, distancia y salario.

        Args:
            person (Person): Objeto del candidato.
            job_list (List[Job]): Lista de vacantes disponibles.

        Returns:
            List[Tuple[Job, int]]: Lista de trabajos con su puntaje de coincidencia ordenada de mayor a menor.
        """
        if not person:
            logger.warning("No hay candidato para hacer matching.")
            return []
        
        if not job_list:
            logger.warning("No hay vacantes disponibles para hacer matching.")
            return []

        person_location = (person.lat, person.lon) if person.lat and person.lon else None
        person_skills = set(person.skills.split(",")) if person.skills else set()

        matches = []
        # Generar embedding para las habilidades del candidato
        person_emb = embed([', '.join(person_skills)]).numpy()[0] if person_skills else None

        for job in job_list:
            try:
                score = 0
                job_skills = set(job.requisitos.split(",")) if job.requisitos else set()

                # 🔹 Match de habilidades (cada coincidencia suma 2 puntos)
                skill_match = len(person_skills & job_skills)
                score += skill_match * 2

                # 🔹 Similitud semántica (si hay habilidades)
                if person_emb is not None and job_skills:
                    job_emb = embed([', '.join(job_skills)]).numpy()[0]
                    similarity = cosine_similarity([person_emb], [job_emb])[0][0]
                    score += similarity * 10  # Peso ajustable

                # 🔹 Distancia geográfica (mayor cercanía = más puntos)
                if person_location and job.lat and job.lon:
                    job_location = (job.lat, job.lon)
                    distance = geodesic(person_location, job_location).km
                    if distance <= 4:
                        score += 3  # Cercano
                    elif distance <= 10:
                        score += 1  # Moderadamente lejos

                # 🔹 Comparación de salario (si el puesto paga igual o más, suma puntos)
                if person.nivel_salarial and job.salario:
                    if job.salario >= person.nivel_salarial:
                        score += 2

                # 🔹 Antigüedad del puesto (vacantes recientes tienen mayor peso)
                if job.fecha_scraping and (datetime.now() - job.fecha_scraping).days <= 7:
                    score += 1

                matches.append((job, score))

            except Exception as e:
                logger.error(f"Error al procesar coincidencia para el trabajo {job.id}: {e}", exc_info=True)

        # 🔹 Ordenar por puntaje de coincidencia (descendente)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    async def match_person_with_jobs(self, person, limit=5):
        local_jobs = await sync_to_async(list)(Vacante.objects.filter(business_unit=person.chat_state.business_unit))
        api_jobs = await self.fetch_latest_jobs(limit)
        
        combined_jobs = local_jobs + [
            Vacante(titulo=j["title"]["rendered"], descripcion=j["content"]["rendered"], business_unit=person.chat_state.business_unit)
            for j in api_jobs
        ]
        
        person_skills = person.skills.split(",") if person.skills else []
        person_emb = embed([", ".join(person_skills)]).numpy()[0] if person_skills else None
        matches = []

        for job in combined_jobs:
            job_skills = job.requisitos.split(",") if job.requisitos else []
            job_emb = embed([", ".join(job_skills)]).numpy()[0] if job_skills else None
            
            skill_score = cosine_similarity([person_emb], [job_emb])[0][0] * 50 if person_emb and job_emb else 0
            location_score = 20 if job.ubicacion in person.metadata.get("desired_locations", []) else 0
            salary_score = 30 if job.salario >= person.salary_data.get("expected_salary", 0) else 0
            
            total_score = skill_score + location_score + salary_score
            matches.append({"job": job, "score": total_score})
        
        return sorted(matches, key=lambda x: x["score"], reverse=True)[:limit]

    def calculate_match_score(person, vacante, weights):
        """
        Calcula el puntaje de coincidencia dinámicamente según los pesos proporcionados.
        """
        score = 0

        # Hard Skills
        if set(person.skills.split(",")).intersection(set(vacante.palabras_clave)):
            score += weights["hard_skills"]

        # Soft Skills
        soft_skills = person.metadata.get("soft_skills", [])
        if soft_skills and vacante.soft_skills:
            matching_soft_skills = set(soft_skills).intersection(set(vacante.soft_skills))
            if matching_soft_skills:
                score += len(matching_soft_skills) / len(vacante.soft_skills) * weights["soft_skills"]

        # Fit Cultural (personalidad)
        personality_match = fit_personality(person.personality_data, vacante.metadata.get("desired_personality", {}))
        score += personality_match * weights["personalidad"]

        # Ubicación
        if person.metadata.get("desired_locations") and vacante.ubicacion in person.metadata.get("desired_locations"):
            score += weights["ubicacion"]

        # Tipo de contrato
        if person.desired_job_types and vacante.tipo_contrato in person.desired_job_types.split(","):
            score += weights["tipo_contrato"]

        return score

    def fit_personality(personality_data, desired_personality):
        """
        Evalúa el ajuste de personalidad entre el candidato y la vacante.
        """
        if not personality_data or not desired_personality:
            return 0  # Sin datos suficientes para evaluar

        match_score = 0
        for key, value in desired_personality.items():
            if key in personality_data and personality_data[key] == value:
                match_score += 1

        return match_score / len(desired_personality)  # Normalizado

    def suggest_positions(self, extracted_skills, interests):
        """ Sugiere posiciones basadas en habilidades detectadas e intereses expresados. """
        prioritized_skills, skill_weights = prioritize_interests(extracted_skills, interests)
        positions = get_positions_by_skills(prioritized_skills)
        return {
            "positions": positions,
            "prioritized_skills": prioritized_skills,
            "skill_weights": skill_weights
        }

    async def process_candidate(self, person):
        """ Procesa a un candidato y sugiere vacantes con base en habilidades e intereses. """
        extracted_skills = person.metadata.get("skills", [])
        interests = person.metadata.get("interests", {})
        suggestions = self.suggest_positions(extracted_skills, interests)

        # Aplicar ranking con machine learning
        matched_jobs = await sync_to_async(self.rank_vacancies)(person, suggestions["positions"])

        logger.info(f"✅ Recomendaciones de vacantes para {person.name}: {matched_jobs}")
        return matched_jobs
    
    def rank_vacancies(self, person, vacancies):
        """ Ordena las vacantes según coincidencia con habilidades e intereses. """
        ml_system = MatchmakingLearningSystem(person.business_unit)
        ranked_jobs = ml_system.rank_candidates(vacancies)
        return ranked_jobs

    def fetch_latest_jobs_sync(self, limit=5):
        """ Obtiene las últimas vacantes publicadas. """
        try:
            response = requests.get(self.api_url, headers=self.headers, params={"_fields": "id,title", "per_page": limit})
            response.raise_for_status()
            jobs = response.json()
            logger.info(f"Se obtuvieron {len(jobs)} vacantes.")
            return jobs
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener vacantes: {e}")
            return []
        
def create_or_update_job_on_wordpress(job_data):
    """
    Crea o actualiza una vacante en WordPress y envía una notificación al empleador si es necesario.
    """
    # Aquí iría la lógica para crear o actualizar la vacante en WordPress.
    worker = Worker.objects.get_or_create(
        job_id=job_data['id'],
        defaults={
            'name': job_data['name'],
            'whatsapp': job_data['whatsapp'],
            'company': job_data['company'],
            'address': job_data['location']['address'],
            'salary': job_data['salary'],
            'job_type': job_data['job_type'],
            'required_skills': ', '.join(job_data['required_skills']),
            'job_description': job_data['job_description'],
            'interview_slots': job_data['agenda'],
        }
    )[0]

    # Notificar al empleador si es necesario
    if worker.whatsapp:
        message = f"Hola {worker.name}, tu vacante {job_data['title']} ha sido actualizada y cargada en el sistema de agenda de Amigro con éxito. Yo seré quien te envíe los recordatorios de entrevista en su momento."
        notify_employer(worker, message)

async def suggest_jobs(self, event):
    """
    Sugiere vacantes al usuario basado en su perfil.
    """
    person = await sync_to_async(Person.objects.get)(phone=event.user_id)
    job_list = await sync_to_async(Vacante.objects.filter)(business_unit=event.business_unit)

    # Obtener coincidencias
    matches = await sync_to_async(match_person_with_jobs)(person, job_list)

    if matches:
        response = "Aquí tienes algunas vacantes recomendadas para ti:\n"
        for idx, (job, score) in enumerate(matches[:5]):  # Top 5
            response += f"{idx+1}. {job.titulo} en {job.empresa} - Puntaje: {score}\n"
        response += "Por favor, ingresa el número de la vacante que te interesa."
    else:
        response = "Lo siento, no encontré vacantes que coincidan con tu perfil."
    
    await self.send_response(event.platform, event.user_id, response)

def calculate_match_score(person, vacante, weights):
    """
    Calcula el puntaje de coincidencia dinámicamente según los pesos proporcionados.
    """
    score = 0

    # Hard Skills
    if set(person.skills.split(",")).intersection(set(vacante.palabras_clave)):
        score += weights["hard_skills"]

    # Soft Skills
    soft_skills = person.metadata.get("soft_skills", [])
    if soft_skills and vacante.soft_skills:
        matching_soft_skills = set(soft_skills).intersection(set(vacante.soft_skills))
        if matching_soft_skills:
            score += len(matching_soft_skills) / len(vacante.soft_skills) * weights["soft_skills"]

    # Fit Cultural (personalidad)
    personality_match = fit_personality(person.personality_data, vacante.metadata.get("desired_personality", {}))
    score += personality_match * weights["personalidad"]

    # Ubicación
    if person.metadata.get("desired_locations") and vacante.ubicacion in person.metadata.get("desired_locations"):
        score += weights["ubicacion"]

    # Tipo de contrato
    if person.desired_job_types and vacante.tipo_contrato in person.desired_job_types.split(","):
        score += weights["tipo_contrato"]

    return score

def fit_personality(personality_data, desired_personality):
    """
    Evalúa el ajuste de personalidad entre el candidato y la vacante.
    """
    if not personality_data or not desired_personality:
        return 0  # Sin datos suficientes para evaluar

    match_score = 0
    for key, value in desired_personality.items():
        if key in personality_data and personality_data[key] == value:
            match_score += 1

    return match_score / len(desired_personality)  # Normalizado

async def procesar_vacante(data: Dict) -> Dict[str, str]:
    """
    Procesa datos del chatbot para crear una vacante en WordPress.

    Args:
        data (Dict): Datos recibidos del chatbot.
    Returns:
        Dict[str, str]: Estado y mensaje del resultado.
    """
    from app.chatbot.integrations.whatsapp import registro_amigro

    required_fields = ["TextInput_5315eb", "TextInput_de5bdf", "TextInput_e1c9ad", "TextInput_4136cd", "TextInput_10ecd4", "TextArea_5df661"]
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return {"status": "error", "message": f"Faltan campos: {', '.join(missing)}"}

    job_data = {
        "business_unit": data.get("business_unit", 4),
        "company_name": data.get("TextInput_5315eb"),
        "job_employee": data.get("TextInput_de5bdf"),
        "job_employee-email": data.get("TextInput_e1c9ad"),
        "celular_responsable": data.get("TextInput_4136cd"),
        "job_title": data.get("TextInput_10ecd4"),
        "job_description": data.get("TextArea_5df661"),
        "job_listing_type": data.get("Dropdown_d27f07", "Remoto"),
        "job_listing_region": "México",
    }

    try:
        manager = VacanteManager(job_data)
        return await manager.create_job_listing()
    except Exception as e:
        logger.error(f"Error procesando vacante: {e}")
        return {"status": "error", "message": str(e)}

async def process_vacante_matching(vacante):
    """
    Procesa las coincidencias para una vacante específica.
    """
    business_unit = vacante.business_unit
    position_level = vacante.nivel_puesto

    # Cargar los pesos dinámicos
    weights_model = WeightingModel(business_unit)
    weights = weights_model.get_weights(position_level)

    # Filtrar personas activas en búsqueda de empleo
    candidates = await sync_to_async(list)(
        Person.objects.filter(job_search_status__in=["activa", "pasiva"])
    )
    matches = []

    for person in candidates:
        relevancia = calculate_match_score(person, vacante, weights)
        if relevancia >= 70:  # Mínimo requerido
            matches.append(CandidatoVacanteMatch(
                vacante=vacante,
                person=person,
                relevancia=relevancia,
            ))

            # Notificar al candidato
            await notify_candidate(person, vacante)

    CandidatoVacanteMatch.objects.bulk_create(matches)

def recommend_candidates(vacancy):
    """
    Recomienda candidatos para una vacante específica.
    """
    system = MatchmakingLearningSystem(vacancy.business_unit)
    predictions = system.rank_candidates(vacancy)
    return predictions

# Ejemplo de uso
if __name__ == "__main__":
    try:
        # Inicialización de VacanteManager con datos completos
        manager = VacanteManager(job_data={
            "business_unit": 4,
            "job_title": "Front & Backend Developer",
            "job_description": "Desarrollar aplicaciones web en Python, ML & debugging.",
            "company_name": "Amigro Technologies",
            "celular_responsable": "525512345678",
            "job_employee-email": "responsable@amigro.org"
        })

        # Obtener las últimas vacantes
        latest_jobs = manager.fetch_latest_jobs()
        print("Últimas vacantes:", latest_jobs)

        # Crear una nueva vacante
        result = manager.create_job_listing()
        print(result)

    except ValueError as ve:
        print(f"Error: {ve}")
    except RuntimeError as re:
        print(f"Error crítico: {re}")
# ========================
# Sección de Conexiones WordPress / JWT (Conservada para Parte 3)
# ========================
# Nota: Estas funciones se integrarán en la Parte 3 para publicación al sistema interno.

async def get_session():
    """Obtiene un token de sesión desde el perfil de usuario en HuntRED de manera asíncrona."""
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)'}
    url = "https://huntred.com/my-profile/"
    try:
        async with ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                response.raise_for_status()
                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")
                input_tag = soup.find("input", {"id": "login_security"})
                if input_tag and input_tag.get("value"):
                    return input_tag.get("value")
                logger.error("No 'login_security' input found in response.")
                return None
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return None

async def register(username: str, email: str, password: str, name: str, lastname: str) -> Optional[str]:
    """Registra un usuario en WordPress."""
    data_session = await get_session()
    if not data_session:
        return "Error obteniendo la sesión para registro."
    url = "https://huntred.com/wp-admin/admin-ajax.php"
    payload = {
        "action": "workscoutajaxregister",
        "role": "candidate",
        "username": username,
        "email": email,
        "password": password,
        "first-name": name,
        "last-name": lastname,
        "privacy_policy": "on",
        "register_security": data_session
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"}
    async with ClientSession() as session:
        try:
            async with session.post(url, data=payload, headers=headers) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return None

async def login(username: str, password: str) -> Optional[str]:
    """Inicia sesión en WordPress."""
    data_session = await get_session()
    if not data_session:
        return "Error obteniendo la sesión para login."
    url = "https://huntred.com/wp-login.php"
    payload = {
        "_wp_http_referer": "/my-profile/",
        "log": username,
        "pwd": password,
        "login_security": data_session
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"}
    async with ClientSession() as session:
        try:
            async with session.post(url, data=payload, headers=headers) as response:
                response.raise_for_status()
                soup = BeautifulSoup(await response.text(), "html.parser")
                return soup.find("div", {"class": "user-avatar-title"})
        except Exception as e:
            logger.error(f"Error logging in: {e}")
            return None

async def solicitud(vacante_url: str, name: str, email: str, message: str, job_id: str) -> Optional[str]:
    """Envía una solicitud para una vacante en WordPress."""
    payload = {
        "candidate_email": email,
        "application_message": message,
        "job_id": job_id,
        "candidate_name": name
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"}
    async with ClientSession() as session:
        try:
            async with session.post(vacante_url, data=payload, headers=headers, allow_redirects=True) as response:
                response.raise_for_status()
                soup = BeautifulSoup(await response.text(), "html.parser")
                return soup.find("p", class_="job-manager-message").text
        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            return None

async def login_to_wordpress(username: str, password: str) -> bool:
    """Realiza login en WordPress para administración de vacantes."""
    url = "https://huntred.com/wp-login.php"
    payload = {"log": username, "pwd": password, "wp-submit": "Log In"}
    headers = {"User-Agent": "Mozilla/5.0"}
    async with ClientSession() as session:
        try:
            async with session.post(url, data=payload, headers=headers) as response:
                response.raise_for_status()
                if "dashboard" in str(response.url):
                    logger.info("WordPress login successful")
                    return True
                logger.error("WordPress login failed")
                return False
        except Exception as e:
            logger.error(f"Error logging into WordPress: {e}")
            return False

async def exportar_vacantes_a_wordpress(business_unit: BusinessUnit, vacantes: List[Vacante]) -> bool:
    """Exporta vacantes a WordPress."""
    try:
        configuracion = await sync_to_async(ConfiguracionBU.objects.get)(business_unit=business_unit)
    except ConfiguracionBU.DoesNotExist:
        logger.error(f"No configuration found for Business Unit {business_unit}")
        return False

    if not await login_to_wordpress(configuracion.usuario_wp, configuracion.password_wp):
        logger.error("WordPress login failed")
        return False

    for vacante in vacantes:
        logger.debug(f"Processing vacante: {vacante}")
        payload = {
            "job_title": vacante.titulo,
            "company": vacante.empresa,
            "description": vacante.descripcion,
            "location": vacante.ubicacion,
        }
        try:
            result = await solicitud(configuracion.api_url, configuracion.usuario_wp, payload["company"], payload["description"], vacante.id)
            logger.info(f"Vacante publicada: {vacante.titulo}")
        except Exception as e:
            logger.error(f"Error publishing vacante {vacante.titulo}: {e}")

    return True