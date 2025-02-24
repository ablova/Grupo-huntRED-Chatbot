# Ubicación: /home/pablo/app/utilidades/vacantes.py

import requests
import logging
import numpy as np
import openai
from typing import List, Dict
from functools import lru_cache
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from geopy.distance import geodesic
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from asgiref.sync import sync_to_async
from app.models import Worker, Person, GptApi, ConfiguracionBU
#from app.chatbot.integrations.whatsapp import registro_amigro, nueva_posicion_amigro #Importaciones locales
from app.ml.ml_model import MatchmakingLearningSystem
from app.utilidades.scraping import get_session, consult, register, login, solicitud
from app.chatbot.utils import prioritize_interests, get_positions_by_skills
#import chainlit as cl
#from some_ml_model import match_candidate_to_job  # Tu modelo personalizado

# Configuración del logger
logger = logging.getLogger("app.utilidades.vacantes")

def main(message: str) -> None:
    """
    Función principal para procesar mensajes y sugerir vacantes.

    Args:
        message (str): Mensaje recibido del usuario.
    """
    candidate_profile = extract_candidate_profile(message)
    job_matches = match_candidate_to_job(candidate_profile)
    print(f"Encontré estas vacantes para ti: {job_matches}") 

def match_person_with_jobs(person, job_list):
    """
    Coincide un usuario con una lista de vacantes.
    """
    if not person:
        logger.warning("No hay candidatos registrados para hacer matching con vacantes.")
        return []
    
    person_location = (person.lat, person.lon) if person.lat and person.lon else None
    person_skills = set(person.skills.split(",")) if person.skills else set()

    matches = []
    for job in job_list:
        try:
            score = 0
            job_skills = set(job.requisitos.split(",")) if job.requisitos else set()
            skill_match = len(person_skills & job_skills)
            score += skill_match * 2

            if person_location and job.lat and job.lon:
                job_location = (job.lat, job.lon)
                distance = geodesic(person_location, job_location).km
                if distance <= 10:
                    score += 3
                elif distance <= 50:
                    score += 1

            if person.nivel_salarial and job.salario:
                if job.salario >= person.nivel_salarial:
                    score += 2

            if job.fecha_scraping and (datetime.now() - job.fecha_scraping).days <= 7:
                score += 1

            matches.append((job, score))
        except Exception as e:
            logger.error(f"Error al procesar coincidencia para el trabajo {job.id}: {e}")

    matches = sorted(matches, key=lambda x: x[1], reverse=True)
    return matches

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
        self.configuracion = ConfiguracionBU.objects.get(business_unit=self.job_data['business_unit'])
        self.api_url = self.configuracion.dominio_rest_api or "https://amigro.org/wp-json/wp/v2/job-listings"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.configuracion.jwt_token}',
            'User-Agent': 'VacanteManager/1.0'
        }
        self.client = None  # Cliente OpenAI

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
            return [tag.strip() for tag in tags if tag.strip()]
        except Exception as e:
            logger.warning(f"Error generando etiquetas con OpenAI: {e}")
            return self.generate_tags_backup(job_description)

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
        
    async def create_job_listing(self) -> Dict[str, str]:
        """
        Crea una vacante en WordPress y envía notificaciones.

        Returns:
            Dict[str, str]: Estado y mensaje del resultado.
        """
        from app.chatbot.integrations.services import send_email  # Importación local

        # Generar etiquetas
        job_tags = self.job_data.get("job_tags", await self.ensure_tags_exist(self.generate_tags(self.job_data["job_description"])))
        self.job_data["job_tags"] = job_tags

        # Estimar salario
        salario_min, salario_max = await self.estimate_salary()
        self.job_data["_salary_min"] = salario_min
        self.job_data["_salary_max"] = salario_max

        # Generar horarios
        unidad_trabajo = self.configuracion.business_unit.name.lower()
        duracion_sesion = 45 if unidad_trabajo in ["huntred", "huntu"] else 30
        fecha_inicio = datetime.now() + timedelta(days=15)
        horarios = self.generate_bookings(fecha_inicio, duracion_sesion)
        for i in range(1, 7):
            key = f"job_booking_{i}"
            self.job_data[key] = self.job_data.get(key) or (horarios[i - 1] if len(horarios) > i - 1 else "")

        # Payload para WordPress
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

        # Publicar
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=self.headers) as response:
                    response.raise_for_status()
                    logger.info(f"Vacante creada: {self.job_data['job_title']}")

                    # Notificar por email
                    correo_responsable = self.job_data.get("job_employee-email")
                    if correo_responsable:
                        subject = f"Vacante Creada: {self.job_data['job_title']}"
                        body = (
                            f"<h1>Vacante Creada</h1>"
                            f"<p>Hola {self.job_data.get('job_employee', 'Responsable')},</p>"
                            f"<p>La vacante '{self.job_data['job_title']}' para '{self.job_data['company_name']}' "
                            f"ha sido creada.</p>"
                            f"<ul>"
                            f"<li>Salario: ${salario_min} - ${salario_max} MXN</li>"
                            f"</ul>"
                        )
                        await send_email(self.configuracion.business_unit, subject, correo_responsable, body)

                    # Notificar por WhatsApp
                    await self.send_recap_position()
                    return {"status": "success", "message": "Vacante creada"}
        except aiohttp.ClientError as e:
            logger.error(f"Error al crear vacante: {e}")
            return {"status": "error", "message": str(e)}

    async def send_recap_position(self) -> None:
        """
        Envía un resumen de la vacante al responsable por WhatsApp.
        """
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
        Coincide un usuario con una lista de vacantes.
        """
        from app.chatbot.utils import get_positions_by_skills  # Importación dentro de la función

        matches = []
        person_location = (person.lat, person.lon) if person.lat and person.lon else None
        person_skills = set(person.skills.split(",")) if person.skills else set()

        for job in job_list:
            try:
                score = 0
                job_skills = set(job.requisitos.split(",")) if job.requisitos else set()
                skill_match = len(person_skills & job_skills)
                score += skill_match * 2

                if person_location and job.lat and job.lon:
                    job_location = (job.lat, job.lon)
                    distance = geodesic(person_location, job_location).km
                    if distance <= 10:
                        score += 3
                    elif distance <= 50:
                        score += 1

                if person.nivel_salarial and job.salario:
                    if job.salario >= person.nivel_salarial:
                        score += 2

                if job.fecha_scraping and (datetime.now() - job.fecha_scraping).days <= 7:
                    score += 1

                matches.append((job, score))
            except Exception as e:
                logger.error(f"Error al procesar coincidencia para el trabajo {job.id}: {e}")

        matches = sorted(matches, key=lambda x: x[1], reverse=True)
        return matches
    
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

    def fetch_latest_jobs(self, limit=5):
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
