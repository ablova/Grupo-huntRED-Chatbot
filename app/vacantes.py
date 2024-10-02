# /home/amigro/app/vacantes.py

import requests
from bs4 import BeautifulSoup
from app.models import Worker, Person
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Mantener la sesión abierta
s = requests.session()

# Configuración del logger
logger = logging.getLogger(__name__)

def get_session():
    headers = {'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)'}
    try:
        response = requests.get("https://amigro.org/my-profile/", headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        data = soup.find("input", {"id": "login_security"}).get("value")
        return data
    except requests.RequestException as e:
        logger.error(f"Error obteniendo sesión: {e}")
        return None

# Consultar vacantes disponibles
def consult(page, url):
    payload = (
        'lang=&search_keywords=&search_location=&filter_job_type%5B%5D=freelance&'
        'filter_job_type%5B%5D=full-time&filter_job_type%5B%5D=internship&'
        'filter_job_type%5B%5D=part-time&filter_job_type%5B%5D=temporary&'
        'per_page=6&orderby=title&order=DESC'
    )
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'user-agent': 'Mozilla/5.0'}
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        html = response.json()
        soup = BeautifulSoup(html["html"], "html.parser")
        vacantes = []

        for li in soup.find_all("li"):
            if "data-title" in str(li):
                vacantes.append({
                    "id": li.get("data-job_id"),
                    "title": li.get("data-title"),
                    "salary": li.get("data-salary"),
                    "job_type": li.get("data-job_type_class"),
                    "company": li.get("data-company"),
                    "location": {
                        "address": li.get("data-address"),
                        "longitude": li.get("data-longitude"),
                        "latitude": li.get("data-latitude"),
                    },
                })
        return vacantes
    except requests.RequestException as e:
        logger.error(f"Error consultando vacantes: {e}")
        return []

# Función para registrar un usuario
def register(username, email, password, name, lastname):
    data_session = get_session()
    if not data_session:
        return "Error obteniendo la sesión para registro."

    url = "https://amigro.org/wp-admin/admin-ajax.php"
    payload = (
        f'action=workscoutajaxregister&role=candidate&username={username}&email={email}'
        f'&password={password}&first-name={name}&last-name={lastname}&privacy_policy=on'
        f'&register_security={data_session}'
    )
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'user-agent': 'Mozilla/5.0'}
    try:
        response = s.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Error registrando usuario: {e}")
        return None

# Función para iniciar sesión
def login(username, password):
    data_session = get_session()
    if not data_session:
        return "Error obteniendo la sesión para login."

    url = "https://amigro.org/wp-login.php"
    payload = f'_wp_http_referer=%2Fmy-profile%2F&log={username}&pwd={password}&login_security={data_session}'
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'user-agent': 'Mozilla/5.0'}
    try:
        response = s.post(url, headers=headers, data=payload)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.find('div', {'class': 'user-avatar-title'})
    except requests.RequestException as e:
        logger.error(f"Error iniciando sesión: {e}")
        return None

# Enviar solicitud para una vacante
def solicitud(vacante_url, name, email, message, job_id):
    payload = f'candidate_email={email}&application_message={message}&job_id={job_id}&candidate_name={name}'
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'user-agent': 'Mozilla/5.0'}
    try:
        response = s.post(vacante_url, headers=headers, data=payload, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        texto = soup.find("p", class_="job-manager-message").text
        return texto
    except requests.RequestException as e:
        logger.error(f"Error enviando solicitud: {e}")
        return None

# Función para encontrar trabajos que coincidan con la persona
def match_person_with_jobs(person):
    """
    Función para encontrar trabajos que coincidan con las habilidades, experiencia
    y otros datos del candidato (persona) en base a su perfil.
    """
    logger.info(f"Buscando coincidencias de trabajo para {person.name}")

    # Obtener todas las vacantes
    all_jobs = Worker.objects.all()

    # Preprocesar las habilidades del usuario
    user_skills = person.skills.lower().split(',') if person.skills else []
    user_skills_text = ' '.join(user_skills)

    # Crear una lista de documentos (descripciones de trabajos)
    job_descriptions = []
    job_list = []
    for job in all_jobs:
        job_skills = job.required_skills.lower().split(','
