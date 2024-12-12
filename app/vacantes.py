# Ubicación: /home/amigro/app/vacantes.py

import requests
import logging
import numpy as np
import openai
from functools import lru_cache
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from asgiref.sync import sync_to_async
from app.models import Worker, Person, GptApi, ConfiguracionBU
# from app.integrations.whatsapp import registro_amigro, nueva_posicion_amigro Importaciones locales
from app.ml_model import MatchMakingLearningSystem
from app.scraping import (
    get_session,
    consult,
    register,
    login,
    solicitud,
    login_to_wordpress
)
import chainlit as cl
#from some_ml_model import match_candidate_to_job  # Tu modelo personalizado

@cl.on_message
async def main(message):
    # Procesa el mensaje del usuario
    candidate_profile = extract_candidate_profile(message)
    job_matches = match_candidate_to_job(candidate_profile)
    await cl.Message(content=f"Encontré estas vacantes para ti: {job_matches}").send()
    
from geopy.distance import geodesic

def match_person_with_jobs(person, job_list):
    """
    Coincide un usuario con una lista de vacantes.
    :param person: Instancia de Person.
    :param job_list: Lista de vacantes (queryset o REST API).
    :return: Lista de vacantes ordenadas por puntaje.
    """
    matches = []
    person_location = (person.lat, person.lon) if person.lat and person.lon else None

    for job in job_list:
        score = 0
        # Comparar habilidades
        person_skills = set(person.skills.split(","))
        job_skills = set(job.requisitos.split(",")) if job.requisitos else set()
        skill_match = len(person_skills & job_skills)
        score += skill_match * 2

        # Comparar ubicación
        if person_location and job.lat and job.lon:
            job_location = (job.lat, job.lon)
            distance = geodesic(person_location, job_location).km
            if distance <= 10:  # Por ejemplo, prioridad a vacantes en 10 km
                score += 3
            elif distance <= 50:
                score += 1

        # Comparar salario
        if person.nivel_salarial and job.salario:
            if job.salario >= person.nivel_salarial:
                score += 2

        # Fecha de publicación
        if job.fecha_scraping and (timezone.now() - job.fecha_scraping).days <= 7:
            score += 1

        matches.append((job, score))

    # Ordenar vacantes por puntaje
    matches = sorted(matches, key=lambda x: x[1], reverse=True)
    return matches

# Configuración del logger
logger = logging.getLogger(__name__)

# Sesión persistente de requests
s = requests.session()

class VacanteManager:
    def __init__(self, job_data):
        self.job_data = job_data
        self.configuracion = ConfiguracionBU.objects.get(business_unit=self.job_data['business_unit'])
        self.api_url = f"{self.configuracion.dominio_bu}/wp-json//wp/v2/job-listings"  # Usar el dominio REST API
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.configuracion.jwt_token}'  # Usar el JWT Token
        }
        self.wp_url = self.configuracion.dominio_conexion  # Usar el dominio de conexión

    @staticmethod
    @lru_cache(maxsize=1000)
    def get_gpt_api_config():
        try:
            gpt_api = GptApi.objects.first()
            if gpt_api:
                openai.api_key = gpt_api.api_token
                openai.organization = gpt_api.organization
                return gpt_api
            else:
                logger.warning("No se encontró la configuración de GptApi en la base de datos.")
                return None
        except Exception as e:
            logger.error(f"Error obteniendo configuración de GptApi: {e}")
            return None

    @lru_cache(maxsize=1000)
    def estimate_salary(self):
        gpt_api = self.get_gpt_api_config()
        if not gpt_api:
            logger.warning("Configuración de OpenAI faltante.")
            return "12000", "15000"

        prompt = (
            f"Calcula el rango salarial para el puesto '{self.job_data['job_title']}' en México.\n"
            f"Descripción: {self.job_data['job_description']}\n"
            f"Proporciona el salario mínimo y máximo estimados en pesos mexicanos."
        )

        try:
            response = openai.Completion.create(
                engine="gpt-4.0-mini",
                prompt=prompt,
                max_tokens=50,
                n=1,
                temperature=0.5
            )
            salario_min, salario_max = self.parse_salary_text(response.choices[0].text.strip())
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

    def generate_tags(self, job_description):
        gpt_api = self.get_gpt_api_config()
        if not gpt_api:
            logger.warning("Falta configuración de GptApi, no se puede usar OpenAI.")
            return self.generate_tags_backup(job_description)

        try:
            response = openai.Completion.create(
                engine=gpt_api.model,
                prompt=f"Genera etiquetas para esta descripción de trabajo:\n\n{job_description}\n\nEtiquetas:",
                max_tokens=50,
                n=1,
                temperature=0.5,
            )
            return [tag.strip() for tag in response.choices[0].text.strip().split(",")]
        except Exception as e:
            logger.warning(f"Error usando OpenAI para generar tags: {e}. Usando TF-IDF como respaldo.")
            return self.generate_tags_backup(job_description)

    def generate_tags_backup(self, job_description):
        vectorizer = TfidfVectorizer(max_features=5, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([job_description])
        return vectorizer.get_feature_names_out()

    def create_job_listing(self):
        """
        Crea una nueva vacante en WordPress y envía notificación por WhatsApp y correo electrónico.
        :return: Diccionario con el estado del proceso de creación.
        """
         # Importación dentro de la función para evitar importación circular con whatsapp.py
        from app.integrations.whatsapp import nueva_posicion_amigro
        from app.integrations.services import send_email #Para poder enviar por correo la confirmacion de la creacion

        business_unit_name = self.job_data.get("business_unit_name", "Grupo huntRED")

        job_tags = self.job_data.get("job_tags", [])
        if not job_tags:
            job_tags = self.generate_tags(self.job_data["job_description"])
        self.job_data["job_tags"] = self.ensure_tags_exist(job_tags)

        # Estimar el salario mínimo y máximo
        salario_min, salario_max = self.estimate_salary()
        self.job_data["_salary_min"] = salario_min
        self.job_data["_salary_max"] = salario_max

        payload = {
            "title": self.job_data["job_title"],
            "content": self.job_data["job_description"],
            "meta": {
                "_salary_min": salario_min,
                "_salary_max": salario_max,
                "_job_expires": self.job_data.get("_job_expires"),
                "_apply_link": self.job_data.get("_apply_link"),
                "_job_whatsapp": self.job_data.get("celular_responsable"),
                "_company_name": self.job_data.get("company_name"),
                    "_job_booking_1": self.job_data.get("job_booking_1"),
                    "_job_booking_2": self.job_data.get("job_booking_2"),
                    "_job_booking_3": self.job_data.get("job_booking_3"),
                    "_job_booking_4": self.job_data.get("job_booking_4"),
                    "_job_booking_5": self.job_data.get("job_booking_5"),
                    "_job_booking_6": self.job_data.get("job_booking_6")
            },
            "status": "publish",
            "job_region": self.job_data.get("job_listing_region"),
            "job_type": self.job_data.get("job_listing_type"),
            "remote_position": self.job_data.get("remote_position"),
            "tags": self.job_data["job_tags"]
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            response.raise_for_status()

            if response.status_code == 201:
                logger.info(f"Vacante creada exitosamente: {response.json()}")
                
                # Enviar notificación por WhatsApp
                celular_responsable = self.job_data.get("celular_responsable")
                mensaje_whatsapp = (
                    f"Hola, {self.job_data.get('job_employee')}, tu vacante '{self.job_data['job_title']}' ha sido creada "
                    f"exitosamente en {business_unit_name}®. Y por este medio te enviaré notificaciones y recordatorios de entrevista en su momento."
                )
                if celular_responsable:
                    nueva_posicion_amigro(celular_responsable, mensaje_whatsapp)

                # Enviar notificación por correo electrónico
                correo_responsable = self.job_data.get("job_employee-email")
                if correo_responsable:
                    subject = f"Vacante Creada: {self.job_data['job_title']}"
                    body = (
                        f"<h1>Vacante Creada Exitosamente</h1>"
                        f"<p>Hola {self.job_data.get('job_employee')},</p>"
                        f"<p>Tu vacante '<strong>{self.job_data['job_title']}</strong>' para la empresa '<strong>{self.job_data['company_name']}</strong>' "
                        f"ha sido creada exitosamente en el sistema de Amigro.org.</p>"
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

    def procesar_vacante(data):
        """
        Procesa los datos recibidos desde el chatbot y los prepara para enviarlos al API de WordPress,
        incluyendo la opción de recibir notificaciones vía WhatsApp.
        """
        # Importación dentro de la función para evitar importación circular con whatsapp.py
        from app.integrations.whatsapp import registro_amigro
        fecha_expiracion = (datetime.now() + timedelta(days=40)).strftime('%Y-%m-%d')
        job_data = {
            "company_name": data.get("TextInput_5315eb"),  # Nombre de la empresa
            "job_listing_category": data.get("Dropdown_612e94"),  # Sector de la empresa
            "job_employee": data.get("TextInput_de5bdf"),  # Responsable del proceso
            "job_employee-email": data.get("TextInput_e1c9ad"),  # Correo del responsable
            "celular_responsable": data.get("TextInput_4136cd"),  # Celular del responsable

            "job_title": data.get("TextInput_10ecd4"),  # Nombre de la posición
            "job_description": data.get("TextArea_5df661"),  # Descripción del puesto
            "job_listing_type": data.get("Dropdown_d27f07"),  # Tipo de posición (Presencial, Remota, etc.)
            "job_listing_region": "México",
            "job_location": data.get("TextInput_efcea3"),  # Ubicación
            "job_cond_migratorias": data.get("CheckboxGroup_be4dff"),

            "job_booking_1": data.get("DatePicker_478238"),  # Fechas de entrevistas
            "job_booking_2": data.get("DatePicker_0c62c5"),
            "job_booking_3": data.get("DatePicker_d6d6a6"),
            "job_booking_4": data.get("DatePicker_e2b1a8"),
            "job_booking_5": data.get("DatePicker_7ed362"),
            "job_booking_6": data.get("DatePicker_ca0813"),

            "status": "publish",
            "remote_position": data.get("remote_position", "1"),
            "job_tags": data.get("job_tags", ["Python", "Backend"]),
            "_job_expires": fecha_expiracion,
            "_salary_min": "12000",
            "_salary_max": "15000",
            "_company_tagline": "Hacemos posible el trabajo de tus sueños",
            "_remote_position": data.get("remote_position", "1"),
            "_hide_expiration": "0"
        }

        recibir_wa = data.get("RadioButtonsGroup_7b5b91") == "0_Si"
        celular_responsable = data.get("TextInput_4136cd")

        if recibir_wa and celular_responsable:
            mensaje_wa = (
                f"Hola, {data.get('TextInput_de5bdf')}, se han activado las notificaciones WA para el proceso de selección de {data.get('TextInput_10ecd4')} - {data.get('TextInput_5315eb')}."
            )
            registro_amigro(celular_responsable, mensaje_wa)

        vacante_manager = VacanteManager(job_data, use_jwt=True)
        return vacante_manager.create_job_listing()

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