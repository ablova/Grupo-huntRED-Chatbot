# Ubicación: /home/pablollh/app/utilidades/vacantes.py

import requests
import logging
import numpy as np
import openai
from typing import List, Dict
from functools import lru_cache
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from asgiref.sync import sync_to_async
from app.models import Worker, Person, GptApi, ConfiguracionBU
#from app.chatbot.integrations.whatsapp import registro_amigro, nueva_posicion_amigro #Importaciones locales
from app.ml.ml_model import MatchmakingLearningSystem
from app.utilidades.scraping import (
    get_session,
    consult,
    register,
    login,
    solicitud,
    login_to_wordpress
)
#import chainlit as cl
#from some_ml_model import match_candidate_to_job  # Tu modelo personalizado

#@cl.on_message
#async def main(message):
#    # Procesa el mensaje del usuario
#    candidate_profile = extract_candidate_profile(message)
#    job_matches = match_candidate_to_job(candidate_profile)
#    await cl.Message(content=f"Encontré estas vacantes para ti: {job_matches}").send()
def main(message):
    candidate_profile = extract_candidate_profile(message)
    job_matches = match_candidate_to_job(candidate_profile)
    print(f"Encontré estas vacantes para ti: {job_matches}")   
from geopy.distance import geodesic

def match_person_with_jobs(person, job_list):
    """
    Coincide un usuario con una lista de vacantes.
    """
    matches = []
    person_location = (person.lat, person.lon) if person.lat and person.lon else None
    person_skills = set(person.skills.split(",")) if person.skills else set()

    for job in job_list:
        try:
            score = 0
            # Comparar habilidades
            job_skills = set(job.requisitos.split(",")) if job.requisitos else set()
            skill_match = len(person_skills & job_skills)
            score += skill_match * 2

            # Comparar ubicación
            if person_location and job.lat and job.lon:
                job_location = (job.lat, job.lon)
                distance = geodesic(person_location, job_location).km
                if distance <= 10:
                    score += 3
                elif distance <= 50:
                    score += 1

            # Comparar salario
            if person.nivel_salarial and job.salario:
                if job.salario >= person.nivel_salarial:
                    score += 2

            # Fecha de publicación
            if job.fecha_scraping and (datetime.now() - job.fecha_scraping).days <= 7:
                score += 1

            matches.append((job, score))
        except Exception as e:
            logger.error(f"Error al procesar coincidencia para el trabajo {job.id}: {e}")

    matches = sorted(matches, key=lambda x: x[1], reverse=True)
    return matches

# Configuración del logger
logger = logging.getLogger(__name__)

# Sesión persistente de requests
s = requests.session()

class VacanteManager:
    def __init__(self, job_data):
        required_fields = ["business_unit", "job_title", "job_description", "company_name"]
        missing_fields = [field for field in required_fields if field not in job_data]
        if missing_fields:
            raise ValueError(f"Faltan los siguientes campos requeridos en job_data: {', '.join(missing_fields)}")

        self.job_data = job_data
        self.configuracion = ConfiguracionBU.objects.get(business_unit=self.job_data['business_unit'])
        self.api_url = self.configuracion.dominio_rest_api
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.configuracion.jwt_token}'
        }
        self.wp_url = self.configuracion.dominio_bu

    def _init_openai_client(self):
        """Initialize OpenAI client if not already done"""
        if self.client is None:
            gpt_api = self.get_gpt_api_config()
            if gpt_api:
                self.client = OpenAI(
                    api_key=gpt_api.api_token,
                    organization=gpt_api.organization
                )
        return self.client is not None
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def get_gpt_api_config():
        try:
            gpt_api = GptApi.objects.first()
            if gpt_api:
                return gpt_api
            else:
                logger.warning("No se encontró la configuración de GptApi en la base de datos.")
                return None
        except Exception as e:
            logger.error(f"Error obteniendo configuración de GptApi: {e}")
            return None

    def fetch_latest_jobs(self, limit=5):
        """
        Obtiene las últimas vacantes publicadas con campos específicos.
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.configuracion.jwt_token}",
                "Accept": "application/json",
                "User-Agent": "VacanteManager/1.0"
            }
            params = {"_fields": "id,title", "per_page": limit}
            response = requests.get(self.api_url, headers=headers, params=params)
            response.raise_for_status()
            jobs = response.json()
            logger.info(f"Se obtuvieron {len(jobs)} vacantes.")
            return jobs
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP {e.response.status_code}: {e.response.text}")
        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión al API de WordPress")
        except requests.exceptions.Timeout:
            logger.error("Tiempo de espera agotado al conectar con el API")
        except Exception as e:
            logger.error(f"Error desconocido: {e}")
        return []

    def generate_bookings(start_date, session_duration):
        """
        Genera horarios de entrevistas desde una fecha inicial, con una duración específica por sesión.
        :param start_date: Fecha inicial (datetime) para comenzar los horarios.
        :param session_duration: Duración de cada sesión en minutos.
        :return: Lista de horarios en formato '%Y-%m-%d %H:%M'.
        """
        horarios = []
        hora_actual = datetime.combine(start_date.date(), datetime.min.time()).replace(hour=9)
        while hora_actual.time() <= datetime.min.time().replace(hour=14):
            horarios.append(hora_actual.strftime('%Y-%m-%d %H:%M'))
            hora_actual += timedelta(minutes=session_duration)
        return horarios

    def estimate_salary(self):
        """
        Estima el rango salarial usando el nuevo cliente de OpenAI.
        """
        if not self._init_openai_client():
            logger.warning("No se pudo inicializar el cliente de OpenAI.")
            return "12000", "15000"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un experto en compensaciones y salarios en México."},
                    {"role": "user", "content": f"Calcula el rango salarial para el puesto '{self.job_data['job_title']}' "
                                                f"en México.\nDescripción: {self.job_data['job_description']}\n"
                                                f"Proporciona el salario mínimo y máximo estimados en pesos mexicanos."}
                ],
                max_tokens=50,
                temperature=0.5
            )
            salario_min, salario_max = self.parse_salary_text(response.choices[0].message.content.strip())
            return salario_min, salario_max
        except Exception as e:
            logger.error(f"Error al estimar salario con OpenAI: {e}")
            return "12000", "15000"

    def parse_salary_text(self, text):
        try:
            # Asumiendo que el texto tiene el formato "Salario mínimo: $XXXX, Salario máximo: $YYYY"
            salarios = [s for s in text.split() if s.startswith('$')]
            return salarios[0].replace("$", ""), salarios[1].replace("$", "")
        except Exception:
            logger.warning("Error al parsear salario, valores predeterminados utilizados.")
            return "10000", "15000"

    def ensure_tags_exist(self, tags):
        tag_ids = []
        for tag in tags:
            try:
                response = requests.get(f"{self.api_url}/tags", headers=self.headers, params={"search": tag})
                if response.status_code == 200 and response.json():
                    tag_ids.append(response.json()[0]["id"])
                else:
                    create_tag_response = requests.post(
                        f"{self.api_url}/tags", headers=self.headers, json={"name": tag}
                    )
                    if create_tag_response.status_code == 201:
                        tag_ids.append(create_tag_response.json()["id"])
                    else:
                        logger.error(f"Error creando tag '{tag}': {create_tag_response.text}")
            except Exception as e:
                logger.error(f"Error al asegurar existencia de tag '{tag}': {e}")
        return tag_ids

    @staticmethod
    def generate_tags(job_description):
        """
        Genera etiquetas usando el nuevo cliente de OpenAI.
        """
        if not job_description:
            logger.warning("La descripción del trabajo está vacía.")
            return []

        try:
            gpt_api = VacanteManager.get_gpt_api_config()
            if not gpt_api:
                return VacanteManager.generate_tags_backup(job_description)

            client = OpenAI(
                api_key=gpt_api.api_token,
                organization=gpt_api.organization
            )

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Genera etiquetas relevantes para trabajos, separadas por comas."},
                    {"role": "user", "content": f"Genera etiquetas para esta descripción:\n{job_description}"}
                ],
                max_tokens=50,
                temperature=0.5
            )
            
            tags = response.choices[0].message.content.strip().split(",")
            return [tag.strip() for tag in tags if tag.strip()]
        except Exception as e:
            logger.warning(f"Error al generar etiquetas con OpenAI: {e}")
            return VacanteManager.generate_tags_backup(job_description)

    @staticmethod
    def generate_tags_backup(job_description):
        """
        Método de respaldo para generar etiquetas usando TF-IDF.
        """
        vectorizer = TfidfVectorizer(max_features=5, stop_words='english')
        try:
            tfidf_matrix = vectorizer.fit_transform([job_description])
            return vectorizer.get_feature_names_out().tolist()
        except Exception as e:
            logger.error(f"Error en generate_tags_backup: {e}")
            return ["general"]

    def create_job_listing(self):
        """
        Crea una nueva vacante en WordPress y envía notificación por WhatsApp y correo electrónico.
        :return: Diccionario con el estado del proceso de creación.
        """
        from app.chatbot.integrations.services import send_email  # Importación para envío de correos

        business_unit_name = self.job_data.get("business_unit_name", "Grupo huntRED")

        # Generar etiquetas si no existen
        job_tags = self.job_data.get("job_tags", [])
        if not job_tags:
            job_tags = self.generate_tags(self.job_data["job_description"])
        self.job_data["job_tags"] = self.ensure_tags_exist(job_tags)

        # Estimar el salario mínimo y máximo
        salario_min, salario_max = self.estimate_salary()
        self.job_data["_salary_min"] = salario_min
        self.job_data["_salary_max"] = salario_max

        # Generar horarios si no existen
        unidad_trabajo = self.configuracion.business_unit.name.lower()
        duracion_sesion = 45 if unidad_trabajo in ["huntred", "huntu"] else 30
        fecha_inicio = datetime.now() + timedelta(days=15)
        horarios = generate_bookings(fecha_inicio, duracion_sesion)
        for i in range(1, 7):
            key = f"job_booking_{i}"
            if key not in self.job_data or not self.job_data[key]:
                self.job_data[key] = horarios[i - 1] if len(horarios) > i - 1 else ""

        # Crear el payload
        payload = {
            "title": self.job_data["job_title"],
            "content": self.job_data["job_description"],
            "meta": {
                "_salary_min": self.job_data.get("_salary_min", "12000"),
                "_salary_max": self.job_data.get("_salary_max", "15000"),
                "_job_expires": self.job_data.get("_job_expires", ""),
                "_apply_link": self.job_data.get("_apply_link", ""),
                "_job_whatsapp": self.job_data.get("celular_responsable", ""),
                "_company_name": self.job_data.get("company_name", ""),
                **{f"_job_booking_{i}": self.job_data.get(f"job_booking_{i}", "") for i in range(1, 7)}
            },
            "status": "publish",
            "job_region": self.job_data.get("job_listing_region", ""),
            "job_type": self.job_data.get("job_listing_type", ""),
            "remote_position": self.job_data.get("remote_position", "0"),
            "tags": self.job_data.get("job_tags", ["Python", "Backend"]),
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            response.raise_for_status()

            if response.status_code == 201:
                logger.info(f"Vacante creada exitosamente: {response.json()}")
                # Notificar al responsable por correo electrónico
                correo_responsable = self.job_data.get("job_employee-email")
                if correo_responsable:
                    subject = f"Vacante Creada: {self.job_data['job_title']}"
                    body = (
                        f"<h1>Vacante Creada Exitosamente</h1>"
                        f"<p>Hola {self.job_data.get('job_employee')},</p>"
                        f"<p>Tu vacante '<strong>{self.job_data['job_title']}</strong>' para la empresa '<strong>{self.job_data['company_name']}</strong>' "
                        f"ha sido creada exitosamente en el sistema de huntred.com.</p>"
                        f"<ul>"
                        f"<li><strong>Salario Estimado:</strong> ${salario_min} - ${salario_max} MXN</li>"
                        f"<li><strong>Tipo de Trabajo:</strong> {self.job_data.get('job_listing_type')}</li>"
                        f"<li><strong>Región:</strong> {self.job_data.get('job_listing_region')}</li>"
                        f"</ul>"
                        f"<p>Te mantendremos informado sobre los recordatorios de entrevistas y aplicaciones recibidas.</p>"
                    )
                    send_email(self.job_data.get("business_unit"), subject, correo_responsable, body)
                return {"status": "success", "message": "Vacante creada exitosamente"}

            else:
                logger.error(f"Error al crear vacante: {response.status_code}, {response.text}")
                return {"status": "error", "message": f"Error al crear vacante: {response.status_code}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en la solicitud al API: {str(e)}")
            return {"status": "error", "message": "Error en la solicitud al API"}

    def send_recap_position(self):
        """
        Envía un resumen de la posición creada al responsable de la vacante.
        """
        # Importación dentro de la función para evitar importación circular con whatsapp.py
        from app.integrations.whatsapp import nueva_posicion_amigro
        mensaje = (
            f"Resumen de la posición creada:\n"
            f"Posición: {self.job_data['job_title']}\n"
            f"Empresa: {self.job_data['company_name']}\n"
            f"Descripción: {self.job_data['job_description']}\n"
            f"Salario estimado: ${self.job_data['_salary_min']} - ${self.job_data['_salary_max']} MXN\n\n"
            f"Este salario se generó con base en indicadores nacionales y recomendaciones "
            f"internacionales usando algoritmos de IA procesados específicamente para este proceso."
        )
        celular_responsable = self.job_data.get("celular_responsable")
        if celular_responsable:
            nueva_posicion_amigro(celular_responsable, mensaje)

    def generate_tags(job_description):
        """
        Genera etiquetas utilizando GPT de OpenAI para una descripción de trabajo específica.
        """
        response = openai.Completion.create(
            engine="gpt-4.0-mini",
            prompt=f"Genera etiquetas para esta descripción de trabajo:\n\n{job_description}\n\nEtiquetas:",
            max_tokens=50,
            n=1,
            temperature=0.5,
        )
        tags = response.choices[0].text.strip().split(", ")
        return tags

    @staticmethod
    def match_person_with_jobs(person):
        """
        Encuentra coincidencias de vacantes con base en habilidades del candidato.
        """
        logger.info(f"Buscando coincidencias de trabajo para {person.name}")
        all_jobs = get_wordpress_jobs()

        if not all_jobs:
            logger.info("No se encontraron vacantes disponibles.")
            return []

        user_skills = person.skills.lower().split(',') if person.skills else []
        user_skills_text = ' '.join(user_skills)

        job_descriptions = []
        job_list = []

        for job in all_jobs:
            job_skills = job.required_skills.lower().split(',') if job.required_skills else []
            job_descriptions.append(' '.join(job_skills))
            job_list.append(job)

        if not job_descriptions:
            return []

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(job_descriptions + [user_skills_text])
        cosine_similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
        similarity_scores = cosine_similarities[0]

        top_jobs = sorted(zip(job_list, similarity_scores), key=lambda x: x[1], reverse=True)
        return top_jobs[:5]
    
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

def procesar_vacante(data):
        """
        Procesa los datos recibidos desde el chatbot y los prepara para enviarlos al API de WordPress,
        incluyendo la opción de generar horarios automáticamente y notificaciones vía WhatsApp.
        """
        from app.chatbot.integrations.whatsapp import registro_amigro

        # Validar campos requeridos
        campos_requeridos = [
            "TextInput_5315eb",  # Nombre de la empresa
            "TextInput_de5bdf",  # Responsable del proceso
            "TextInput_e1c9ad",  # Correo del responsable
            "TextInput_4136cd",  # Celular del responsable
            "TextInput_10ecd4",  # Nombre de la posición
            "TextArea_5df661",   # Descripción del puesto
        ]
        faltantes = [campo for campo in campos_requeridos if not data.get(campo)]
        if faltantes:
            return {
                "status": "error",
                "message": f"Faltan los siguientes campos obligatorios: {', '.join(faltantes)}"
            }

        # Configurar datos de la vacante
        fecha_expiracion = (datetime.now() + timedelta(days=40)).strftime('%Y-%m-%d')
        job_data = {
            "company_name": data.get("TextInput_5315eb"),
            "job_listing_category": data.get("Dropdown_612e94", "General"),
            "job_employee": data.get("TextInput_de5bdf"),
            "job_employee-email": data.get("TextInput_e1c9ad"),
            "celular_responsable": data.get("TextInput_4136cd"),
            "job_title": data.get("TextInput_10ecd4"),
            "job_description": data.get("TextArea_5df661"),
            "job_listing_type": data.get("Dropdown_d27f07", "Remoto"),
            "job_listing_region": "México",
            "job_location": data.get("TextInput_efcea3", "Remoto"),
            "job_cond_migratorias": data.get("CheckboxGroup_be4dff", ""),
            "job_booking_1": data.get("DatePicker_478238", ""),
            "job_booking_2": data.get("DatePicker_0c62c5", ""),
            "job_booking_3": data.get("DatePicker_d6d6a6", ""),
            "job_booking_4": data.get("DatePicker_e2b1a8", ""),
            "job_booking_5": data.get("DatePicker_7ed362", ""),
            "job_booking_6": data.get("DatePicker_ca0813", ""),
            "status": "publish",
            "remote_position": data.get("remote_position", "1"),
            "job_tags": data.get("job_tags", ["Python", "Backend"]),
            "_job_expires": fecha_expiracion,
            "_salary_min": "12000",
            "_salary_max": "15000",
            "_company_tagline": "Hacemos posible el trabajo de tus sueños",
            "_hide_expiration": "0",
        }

        # Generar horarios automáticamente si no están definidos
        unidad_trabajo = data.get("business_unit", "").lower()
        duracion_sesion = 45 if unidad_trabajo in ["huntred", "huntu"] else 30
        fecha_inicio = datetime.now() + timedelta(days=15)
        horarios = generate_bookings(fecha_inicio, duracion_sesion)

        for i in range(1, 7):
            key = f"job_booking_{i}"
            if not job_data.get(key):
                job_data[key] = horarios[i - 1] if len(horarios) > i - 1 else ""

        # Enviar notificación por WhatsApp si se requiere
        recibir_wa = data.get("RadioButtonsGroup_7b5b91") == "0_Si"
        if recibir_wa and job_data["celular_responsable"]:
            mensaje_wa = (
                f"Hola, {job_data['job_employee']}, se han activado las notificaciones WA para el proceso de selección "
                f"de la vacante '{job_data['job_title']}' en la empresa {job_data['company_name']}."
            )
            registro_amigro(job_data["celular_responsable"], mensaje_wa)

        # Crear la vacante mediante el gestor VacanteManager
        try:
            vacante_manager = VacanteManager(job_data)
            resultado = vacante_manager.create_job_listing()
            return resultado
        except Exception as e:
            logger.error(f"Error al procesar la vacante: {e}")
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
