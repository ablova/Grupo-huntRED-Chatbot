# /home/amigro/app/wordpress_integration.py

import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)
s = requests.session()

def get_session():
    """
    Obtiene un token de sesión desde el perfil de usuario en Amigro.
    """
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

def consult(page, url, business_unit):
    """
    Consulta las vacantes en WordPress según filtros específicos usando autenticación JWT.
    """
    configuracion = ConfiguracionBU.objects.get(business_unit=business_unit)
    jwt_token = configuracion.jwt_token
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {jwt_token}',
        'user-agent': 'Mozilla/5.0'
    }
    payload = (
        'lang=&search_keywords=&search_location=&filter_job_type%5B%5D=freelance&'
        'filter_job_type%5B%5D=full-time&filter_job_type%5B%5D=internship&'
        'filter_job_type%5B%5D=part-time&filter_job_type%5B%5D=temporary&'
        'per_page=6&orderby=title&order=DESC'
    )

    try:
        response = s.post(url, headers=headers, data=payload)
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
                    "whatsapp": li.get("data-whatsapp"),
                    "location": {
                        "address": li.get("data-address"),
                        "longitude": li.get("data-longitude"),
                        "latitude": li.get("data-latitude")
                    },
                    "agenda": {
                        "slot 1": li.get("job_booking_1"),
                        "slot 2": li.get("job_booking_2"),
                        "slot 3": li.get("job_booking_3"),
                        "slot 4": li.get("job_booking_4"),
                        "slot 5": li.get("job_booking_5"),
                        "slot 6": li.get("job_booking_6"),
                        "slot 7": li.get("job_booking_7"),
                        "slot 8": li.get("job_booking_8"),
                        "slot 9": li.get("job_booking_9"),
                        "slot 10": li.get("job_booking_10")
                    }
                })
        return vacantes
    except requests.RequestException as e:
        logger.error(f"Error consultando vacantes: {e}")
        return []

def register(username, email, password, name, lastname):
    """
    Realiza el registro de un usuario en WordPress.
    """
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

def login(username, password):
    """
    Realiza el inicio de sesión de un usuario en WordPress.
    """
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

def solicitud(vacante_url, name, email, message, job_id):
    """
    Envía la solicitud para una vacante específica en WordPress.
    """
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

def login_to_wordpress(username, password):
    """
    Realiza el login en WordPress para la administración de vacantes.
    """
    url = "https://amigro.org/wp-login.php"
    payload = {
        'log': username,
        'pwd': password,
        'wp-submit': 'Log In'
    }
    headers = {'user-agent': 'Mozilla/5.0'}
    
    try:
        response = s.post(url, headers=headers, data=payload)
        response.raise_for_status()
        
        if "dashboard" in response.url:  # Si redirige al dashboard, el login fue exitoso
            logger.info("Inicio de sesión exitoso en WordPress")
            return True
        else:
            logger.error("Error al iniciar sesión en WordPress")
            return False
    except requests.RequestException as e:
        logger.error(f"Error iniciando sesión: {e}")
        return False