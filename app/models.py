# Ubicación del archivo: /home/pablollh/app/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from urllib.parse import urlparse

import requests
import logging
import re
import uuid

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PLATFORM_CHOICES = [
    ("workday", "Workday"),
    ("phenom_people", "Phenom People"),
    ("oracle_hcm", "Oracle HCM"),
    ("sap_successfactors", "SAP SuccessFactors"),
    ("adp", "ADP"),
    ("peoplesoft", "PeopleSoft"),
    ("meta4", "Meta4"),
    ("cornerstone", "Cornerstone"),
    ("ukg", "UKG"),
    ("linkedin", "LinkedIn"),
    ("indeed", "Indeed"),
    ("greenhouse", "Greenhouse"),
    ("glassdoor", "Glassdoor"),
    ("computrabajo", "Computrabajo"),
    ("accenture", "Accenture"),
    ("santander", "Santander"),
    ("eightfold_ai", "EightFold AI"),
    ("default", "Default"),
    ("flexible", "Flexible"),
]

BUSINESS_UNIT_CHOICES = [
    ('huntRED', 'huntRED®'),
    ('huntRED_executive', 'huntRED® Executive'),
    ('huntu', 'huntU®'),
    ('amigro', 'Amigro®'),
]

COMUNICATION_CHOICES =[
    ("whatsapp", "WhatsApp"),
    ("telegram", "Telegram"),
    ("messenger", "Messenger"),
    ("instagram", "Instagram"),
    ("sms", "SMS"),
]

# User agents
USER_AGENTS = [
    # Chrome en Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",

    # Chrome en MacOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",

    # Chrome en Linux 
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    
    # Firefox en Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    
    # Firefox en MacOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/114.0",
    
    # Safari en MacOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",

    # Edge en Windows 
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.51",
]

class Configuracion(models.Model):
    secret_key = models.CharField(max_length=255, default='hfmrpTNRwmQ1F7gZI1DNKaQ9gNw3cgayKFB0HK_gt9BKJEnLy60v1v0PnkZtX3OkY48')
    sentry_dsn = models.CharField(max_length=255, blank=True, null=True, default='https://94c6575f877d16a00cc74bcaaab5ae79@o4508258791653376.ingest.us.sentry.io/4508258794471424')
    debug_mode = models.BooleanField(default=True)
    test_user = models.CharField(max_length=255, blank=True, null=True, default='Pablo Lelo de Larrea H.')
    test_phone_number = models.CharField(max_length=15, default='+525518490291', help_text='Número de teléfono para pruebas y reportes de ejecución')
    test_email = models.EmailField(max_length=50, default='pablo@huntred.com', help_text='Email para pruebas y reportes de ejecución')
    default_platform = models.CharField(max_length=20, default='whatsapp', choices=COMUNICATION_CHOICES, help_text='Plataforma de pruebas por defecto')
    notification_hour = models.TimeField(blank=True, null=True, help_text='Hora para enviar notificaciones diarias de pruebas')
    is_test_mode = models.BooleanField(default=True, help_text='Indicador de modo de pruebas')

    def __str__(self):
        return "Configuración General del Sistema"

class DominioScraping(models.Model):
    empresa = models.CharField(max_length=75, unique=True, blank=True, null=True)
    dominio = models.URLField(max_length=255, unique=True)
    plataforma = models.CharField(max_length=100, choices=PLATFORM_CHOICES, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=[("definido", "Definido"), ("libre", "Indefinido")], default="libre")
    verificado = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    cookies = models.JSONField(blank=True, null=True)
    frecuencia_scraping = models.IntegerField(default=24)
    mensaje_error = models.TextField(blank=True, null=True)
    ultima_verificacion = models.DateTimeField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    # Nuevos campos para scraping flexible
    selector_titulo = models.CharField(max_length=200, null=True, blank=True)
    selector_descripcion = models.CharField(max_length=200, null=True, blank=True)
    selector_ubicacion = models.CharField(max_length=200, null=True, blank=True)
    selector_salario = models.CharField(max_length=200, null=True, blank=True)
    # Tipo de selector (CSS, XPath)
    tipo_selector = models.CharField(
        max_length=20, 
        choices=[('css', 'CSS'), ('xpath', 'XPath')],
        default='css'
    )
    # Configuración JSON para mapeos más complejos
    mapeo_configuracion = models.JSONField(null=True, blank=True)

    def generar_correo_asignado(self):
        from app.models import ConfiguracionBU
        configuracion = ConfiguracionBU.objects.filter(scraping_domains__dominio=self.dominio).first()
        dominio_bu = configuracion.dominio_bu if configuracion else "huntred.com"
        return f"{self.empresa.lower()}@{dominio_bu}" if self.empresa else None

    def __str__(self):
        return f"{self.dominio} ({self.plataforma})"

    def validar_url(self):
        try:
            logger.info(f"Validando URL: {self.dominio}")
            response = requests.head(self.dominio, timeout=10, allow_redirects=True)
            if response.status_code != 200:
                logger.error(f"URL no válida: {self.dominio} - Estado: {response.status_code}")
                raise ValidationError("La URL proporcionada no es válida o no responde correctamente.")
        except requests.RequestException as e:
            logger.error(f"Error al validar la URL: {e}")
            raise ValidationError(f"Error al validar la URL: {e}")

    def detectar_plataforma(self):
        if self.plataforma:
            logger.info(f"Plataforma ya definida manualmente: {self.plataforma}")
            return

        url_lower = self.dominio.lower()
        patrones = {
            'workday': r'workday\.com',
            'oracle_hcm': r'oracle\.com',
            'sap_successfactors': r'sap\.com',
            'cornerstone': r'cornerstoneondemand\.com',
            'amigro': r'amigro\.org',
        }

        for plataforma, patron in patrones.items():
            if re.search(patron, url_lower):
                self.plataforma = plataforma
                self.verificado = True
                logger.info(f"Plataforma detectada automáticamente: {plataforma}")
                return

        self.plataforma = "otro"
        self.verificado = False
        logger.warning(f"No se detectó una plataforma conocida para: {self.dominio}")

    def clean(self):
        self.validar_url()
        self.detectar_plataforma()

    def save(self, *args, **kwargs):
        if not kwargs.pop("skip_clean", False):
            self.full_clean()
        super().save(*args, **kwargs)


class ConfiguracionScraping(models.Model):
    dominio = models.ForeignKey(DominioScraping, on_delete=models.CASCADE)
    campo = models.CharField(max_length=50)
    selector = models.CharField(max_length=200)
    tipo_selector = models.CharField(max_length=20, choices=[('css', 'CSS'), ('xpath', 'XPath')])
    transformacion = models.CharField(max_length=100, null=True, blank=True)

class BusinessUnit(models.Model):
    name = models.CharField(max_length=50, choices=BUSINESS_UNIT_CHOICES, unique=True)
    description = models.TextField(blank=True)
    # admin_email = models.EmailField(null=True, blank=True) # Removemos el campo admin_email ya que lo tenemos como property
    admin_phone = models.CharField(max_length=20, null=True, blank=True)  # Número de WhatsApp del administrador
    whatsapp_enabled = models.BooleanField(default=True)
    telegram_enabled = models.BooleanField(default=True)
    messenger_enabled = models.BooleanField(default=True)
    instagram_enabled = models.BooleanField(default=True)
    scrapping_enabled = models.BooleanField(default=True)
    scraping_domains = models.ManyToManyField(
        DominioScraping, related_name="business_units", blank=True
    )

    def __str__(self):
        return dict(BUSINESS_UNIT_CHOICES).get(self.name, self.name)
    
    def get_email_template_path(self):
        """
        Retorna la ruta de la plantilla de email basada en el nombre de la BusinessUnit.
        """
        sanitized_name = re.sub(r'\W+', '', self.name).lower()
        return f'emails/template_{sanitized_name}.html'

    @property
    def admin_email(self):
        """
        Genera automáticamente el correo electrónico del administrador basado en el dominio.
        Extrae el dominio base de la URL completa.
        """
        try:
            config = self.configuracionbu
            if config and config.dominio_bu:
                # Parsear la URL y obtener solo el dominio
                parsed_url = urlparse(config.dominio_bu)
                # Obtener el dominio limpio (sin www. si existe)
                domain = parsed_url.netloc or parsed_url.path
                domain = domain.replace('www.', '')
                return f'hola@{domain}'
        except ConfiguracionBU.DoesNotExist:
            pass
        return None

class ConfiguracionBU(models.Model):
    business_unit = models.OneToOneField(BusinessUnit, on_delete=models.CASCADE)
    logo_url = models.URLField(default="https://huntred.com/logo.png")
    direccion_bu = models.CharField(max_length=255, default="Av. Santa Fe #428, Torre 3, Piso 15, CDMX")
    telefono_bu = models.CharField(max_length=20, default="+5255 59140089")
    correo_bu = models.CharField(max_length=20, default="hola@huntred.com")
    jwt_token = models.CharField(max_length=255, blank=True, null=True, default="...")
    dominio_bu = models.URLField(max_length=255, blank=True, null=True)
    dominio_rest_api = models.URLField(max_length=255, blank=True, null=True)
    scraping_domains = models.ManyToManyField(
        'DominioScraping',
        related_name='configuracion_business_units',
        blank=True,
        help_text="Selecciona los dominios de scraping asociados a esta unidad de negocio."
    )
    smtp_host = models.CharField(max_length=255, blank=True, null=True)
    smtp_port = models.IntegerField(blank=True, null=True, default=587)
    smtp_username = models.CharField(max_length=255, blank=True, null=True)
    smtp_password = models.CharField(max_length=255, blank=True, null=True)
    smtp_use_tls = models.BooleanField(default=True)
    smtp_use_ssl = models.BooleanField(default=False)

    weight_location = models.IntegerField(default=10)
    weight_hard_skills = models.IntegerField(default=45)
    weight_soft_skills = models.IntegerField(default=35)
    weight_contract = models.IntegerField(default=10)

    def __str__(self):
        return f"Configuración de {self.business_unit.name if self.business_unit else 'Unidad de Negocio'}"
    
    def get_smtp_config(self):
        """
        Devuelve la configuración SMTP/IMAP como un diccionario.
        """
        return {
            'host': self.smtp_host,
            'port': self.smtp_port,
            'username': self.smtp_username,
            'password': self.smtp_password,
            'use_tls': self.smtp_use_tls,
            'use_ssl': self.smtp_use_ssl
        }
    
class WeightingModel:
    def __init__(self, business_unit):
        self.business_unit = business_unit
        self.weights = self._load_weights()

    def _load_weights(self):
        """
        Carga los pesos dinámicos desde la configuración de la unidad de negocio.
        """
        try:
            config = ConfiguracionBU.objects.get(business_unit=self.business_unit)
            return {
                "ubicacion": config.weight_location or 10,
                "hard_skills": config.weight_hard_skills or 45,
                "soft_skills": config.weight_soft_skills or 35,
                "tipo_contrato": config.weight_contract or 10,
                "personalidad": config.weight_personality or 15,  # Nuevo peso para fit cultural
            }
        except ConfiguracionBU.DoesNotExist:
            # Valores por defecto
            return {
                "ubicacion": 5,
                "hard_skills": 45,
                "soft_skills": 35,
                "tipo_contrato": 5,
                "personalidad": 10,
            }

    def get_weights(self, position_level):
        """
        Ajusta los pesos según el nivel del puesto.
        """
        if position_level == "gerencia_media":
            return {**self.weights, "soft_skills": 40, "hard_skills": 40, "ubicacion": 10, "personalidad": 20}
        elif position_level == "alta_direccion":
            return {**self.weights, "soft_skills": 45, "hard_skills": 30, "ubicacion": 10, "personalidad": 25}
        elif position_level == "operativo":
            return {**self.weights, "ubicacion": 15, "hard_skills": 50, "soft_skills": 25, "personalidad": 10}
        return self.weights

class WorkflowStage(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='workflow_stages')
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.business_unit.name})"

class RegistroScraping(models.Model):
    dominio = models.ForeignKey(DominioScraping, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True)
    vacantes_encontradas = models.IntegerField(default=0)
    estado = models.CharField(max_length=50, choices=[
        ('exitoso', 'Exitoso'),
        ('fallido', 'Fallido'),
        ('parcial', 'Parcial'),
    ])
    error_log = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Registro {self.dominio.empresa} - {self.estado} - {self.fecha_inicio}"

class Vacante(models.Model):
    titulo = models.CharField(max_length=300)
    empresa = models.CharField(max_length=200)
    salario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ubicacion = models.CharField(max_length=300, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    requisitos = models.TextField(blank=True, null=True)
    beneficios = models.TextField(blank=True, null=True)
    skills_required = models.JSONField(blank=True, null=True)
    modalidad = models.CharField(max_length=20, choices=[
        ('presencial', 'Presencial'),
        ('remoto', 'Remoto'),
        ('hibrido', 'Híbrido')
    ], null=True, blank=True)
    remote_friendly = models.BooleanField(default=False)
    dominio_origen = models.ForeignKey(DominioScraping, on_delete=models.SET_NULL, null=True)
    url_original = models.URLField(max_length=500, blank=True, null=True)
    fecha_publicacion = models.DateTimeField(null=True, blank=True)
    fecha_scraping = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)
    business_unit = models.ForeignKey(
        BusinessUnit, on_delete=models.CASCADE, related_name='vacantes', null=True, blank=True
    )  # Relación con BusinessUnit
    current_stage = models.ForeignKey(
        WorkflowStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='vacantes')

    class Meta:
        unique_together = ['titulo', 'empresa', 'url_original']
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return f"{self.titulo} - {self.empresa}"

class JobTracker(models.Model):
    OPERATION_STATUS_CHOICES = [
        ('not_started', 'No Iniciado'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('on_hold', 'En Espera'),
    ]

    opportunity = models.OneToOneField(Vacante, on_delete=models.CASCADE, related_name='job_tracker')
    status = models.CharField(max_length=20, choices=OPERATION_STATUS_CHOICES, default='not_started')
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)  # Fecha límite para completar el proceso

    def __str__(self):
        return f"Job Tracker para {self.opportunity.titulo}"
    
#    @receiver(post_save, sender=JobTracker)
    def handle_job_tracker_status_change(sender, instance, **kwargs):
        if instance.status == 'completed':
            # Enviar notificación o actualizar otra tabla
            print(f"El JobTracker para {instance.opportunity} ha sido completado.")

class ApiConfig(models.Model):
    business_unit = models.ForeignKey(
        BusinessUnit,
        related_name='api_configs',
        on_delete=models.CASCADE
    )
    api_type = models.CharField(
        max_length=50,
        choices=COMUNICATION_CHOICES
    )
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255, blank=True, null=True)
    additional_settings = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.business_unit.name} - {self.api_type}"

class Person(models.Model):
    number_interaction = models.IntegerField(default=0)  # Changed from CharField to IntegerField #number_interaction = models.CharField(max_length=40, unique=True)

    # Datos personales básicos
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=200, blank=True, null=True)
    apellido_materno = models.CharField(max_length=200, blank=True, null=True)
    nacionalidad = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    sexo = models.CharField(
        max_length=20,
        choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')],
        blank=True,
        null=True
    )
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=40, blank=True, null=True)
    preferred_language = models.CharField(max_length=5, default='es_MX', help_text="Ej: es_MX, en_US")

    # Estado de búsqueda de empleo (ejemplo de opciones: activa, pasiva, local, remota, etc.)
    JOB_SEARCH_STATUS_CHOICES = [
        ('activa', 'Activa'),
        ('pasiva', 'Pasiva'),
        ('local', 'Local'),
        ('remota', 'Remota'),
        ('no_busca', 'No en búsqueda'),
    ]
    job_search_status = models.CharField(
        max_length=20,
        choices=JOB_SEARCH_STATUS_CHOICES,
        blank=True,
        null=True,
        help_text="Estado actual de la búsqueda de empleo."
    )

    # Habilidades y experiencia
    skills = models.TextField(blank=True, null=True, help_text="Listado libre de skills del candidato.")
    experience_years = models.IntegerField(blank=True, null=True, help_text="Años totales de experiencia.")
    desired_job_types = models.CharField(max_length=100, blank=True, null=True, help_text="Tipos de trabajo deseados, ej: tiempo completo, medio tiempo, freelance.")
    cv_file = models.FileField(upload_to='person_files/', blank=True, null=True, help_text="CV u otro documento del candidato.")
    cv_parsed = models.BooleanField(default=False, help_text="Indica si el CV ha sido analizado.")
    cv_analysis = models.JSONField(blank=True, null=True, help_text="Datos analizados del CV.")

    # Información salarial en formato JSON (ej: {"current_salary": 50000, "expected_salary": 60000, "benefits": ["SGMM", "Fondo de ahorro"]})
    salary_data = models.JSONField(default=dict, blank=True, help_text="Información salarial, beneficios y expectativas.")

    # Datos de personalidad (MBTI, Big Five, etc.)
    personality_data = models.JSONField(default=dict, blank=True, help_text="Perfil de personalidad.")

    # Datos de experiencia detallada (ej: [{"empresa": "X", "años": 2, "puesto": "Analista"}])
    experience_data = models.JSONField(default=dict, blank=True, help_text="Experiencia profesional detallada.")

    # Metadatos adicionales: Aquí podemos almacenar información migratoria (Amigro), preferencias culturales, certificaciones, etc.
    # Ejemplo:
    # {
    #   "soft_skills": ["liderazgo", "comunicación"],
    #   "certifications": ["PMP", "AWS Certified"],
    #   "education": ["Licenciatura en Economía", "Maestría en TI"],
    #   "preferred_sectors": ["financiero", "tecnología"],
    #   "desired_companies": ["Google", "Amazon"],
    #   "desired_locations": ["CDMX", "Monterrey"],
    #   "migratory_status": {
    #       "refugio": false,
    #       "permiso_trabajo": true,
    #       "detalles": "Información relevante..."
    #   }
    # }
    metadata = models.JSONField(default=dict, blank=True, help_text="Información adicional del candidato.")
    hire_date = models.DateField(null=True, blank=True)  # Nuevo campo
    points = models.IntegerField(default=0)
    badges = models.ManyToManyField('Badge', blank=True)
    current_stage = models.ForeignKey(
        WorkflowStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='candidatos')

    def __str__(self):
        nombre_completo = f"{self.nombre} {self.apellido_paterno or ''} {self.apellido_materno or ''}".strip()
        return nombre_completo

    def is_profile_complete(self):
        """
        Verifica si todos los campos necesarios están completos en el perfil del usuario.
        Campos requeridos sugeridos:
        - nombre
        - apellido_paterno
        - email
        - phone
        - skills
        """
        required_fields = ['nombre', 'apellido_paterno', 'email', 'phone', 'skills']
        missing_fields = [field for field in required_fields if not getattr(self, field, None)]
        return not missing_fields

class Division(models.Model):
    name = models.CharField(max_length=100, unique=True)
    skills = models.ManyToManyField('Skill', blank=True)

    def __str__(self):
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.ImageField(upload_to='badges/', null=True, blank=True)

    def __str__(self):
        return self.name

class Application(models.Model):
    user = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='applications')
    vacancy = models.ForeignKey(Vacante, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(
        max_length=20,
        choices=[
            ('applied', 'Applied'),
            ('interview', 'Interview'),
            ('rejected', 'Rejected'),
            ('hired', 'Hired'),
        ],
        default='applied'
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    additional_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.vacancy} - {self.status}"

class Invitacion(models.Model):
    referrer = models.ForeignKey(Person, related_name='invitaciones_enviadas', on_delete=models.CASCADE)
    invitado = models.ForeignKey(Person, related_name='invitaciones_recibidas', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class MetaAPI(models.Model):
    business_unit = models.OneToOneField(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='meta_api_config',
    )
    app_id = models.CharField(max_length=255, default='662158495636216')
    app_secret = models.CharField(max_length=255, default='...')
    verify_token = models.CharField(max_length=255, default='amigro_secret_token')

    def __str__(self):
        return f"MetaAPI {self.business_unit.name} ({self.app_id})"

class WhatsAppAPI(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='whatsapp_apis', null=True, blank=True)
    name = models.CharField(max_length=50)
    phoneID = models.CharField(max_length=20, default='114521714899382')
    api_token = models.CharField(max_length=500, default='...')
    WABID = models.CharField(max_length=20, default='104851739211207')
    v_api = models.CharField(max_length=10, default='v21.0')
    meta_api = models.ForeignKey('MetaAPI', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.business_unit.name if self.business_unit else ''} - WhatsApp API {self.phoneID}"

class Template(models.Model):
    TEMPLATE_TYPES = [
        ('FLOW', 'Flow'),
        ('BUTTON', 'Button'),
        ('URL', 'URL'),
        ('IMAGE', 'Image'),
    ]
    whatsapp_api = models.ForeignKey(WhatsAppAPI, on_delete=models.CASCADE, related_name='templates')
    name = models.CharField(max_length=100)
    is_flow = models.BooleanField(default=False)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    image_url = models.URLField(blank=True, null=True)
    language_code = models.CharField(max_length=10, default='es_MX')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('whatsapp_api', 'name', 'language_code')
    def __str__(self):
        return f"{self.name} ({self.language_code}) - {self.whatsapp_api.business_unit.name if self.whatsapp_api.business_unit else 'Sin BU'}"

class MessengerAPI(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='messenger_apis', null=True, blank=True)
    page_id = models.CharField(max_length=255, unique=True)  # <--- Nuevo Campo
    page_access_token = models.CharField(max_length=255)
    meta_api = models.ForeignKey('MetaAPI', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.business_unit.name if self.business_unit else ''} - Messenger API"

class InstagramAPI(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='instagram_apis', null=True, blank=True)
    app_id = models.CharField(max_length=255, default='1615393869401916')
    access_token = models.CharField(max_length=255, default='...')
    instagram_account_id = models.CharField(max_length=255, default='17841457231476550')
    meta_api = models.ForeignKey('MetaAPI', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.business_unit.name if self.business_unit else ''} - Instagram API"

class TelegramAPI(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='telegram_apis', null=True, blank=True)
    api_key = models.CharField(max_length=255)
    bot_name = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.business_unit.name if self.business_unit else ''} - Telegram Bot"

class GptApi(models.Model):
    api_token = models.CharField(max_length=500)
    organization = models.CharField(max_length=100, blank=True, null=True)
    project = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100)
    form_pregunta = models.CharField(max_length=500)
    work_pregunta = models.CharField(max_length=500)
    max_tokens = models.IntegerField(default=150)  # Nuevo campo
    temperature = models.FloatField(default=0.7)  # Nuevo campo
    top_p = models.FloatField(default=1.0, blank=True, null=True)  # Otro parámetro común
    
    def __str__(self):
        return f"Model: {self.model} | Org: {self.organization} | Project: {self.project}"

class Chat(models.Model):
    body = models.TextField(max_length=1000)
    SmsStatus = models.CharField(max_length=15, null=True, blank=True)
    From = models.CharField(max_length=15)
    To = models.CharField(max_length=15)
    ProfileName = models.CharField(max_length=50)
    ChannelPrefix = models.CharField(max_length=50)
    MessageSid = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    message_count = models.IntegerField(default=0)

    def __str__(self):
        return str(self.body)

class Worker(models.Model):
    name = models.CharField(max_length=100)
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    img_company = models.CharField(max_length=500, blank=True, null=True)
    job_id = models.CharField(max_length=100, blank=True, null=True)
    url_name = models.CharField(max_length=100, blank=True, null=True)
    salary = models.CharField(max_length=100, blank=True, null=True)
    job_type = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    longitude = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.CharField(max_length=100, blank=True, null=True)
    required_skills = models.TextField(blank=True, null=True)
    experience_required = models.IntegerField(blank=True, null=True)
    job_description = models.TextField(blank=True, null=True)

    # Información adicional en JSON
    metadata = models.JSONField(default=dict, blank=True, help_text="Información adicional del puesto: sectores, requerimientos, etc.")

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['job_id']),
            models.Index(fields=['company']),
        ]

    def __str__(self) -> str:
        return str(self.name)

class Interview(models.Model):
    INTERVIEW_TYPE_CHOICES = [
        ('presencial', 'Presencial'),
        ('virtual', 'Virtual'),
    ]
    person = models.ForeignKey('Person', on_delete=models.CASCADE)
    interviewer = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='conducted_interviews', blank=True, null=True)
    job = models.ForeignKey(Worker, on_delete=models.CASCADE)
    interview_date = models.DateTimeField()
    application_date = models.DateTimeField(auto_now_add=True)
    slot = models.CharField(max_length=50)
    candidate_latitude = models.CharField(max_length=100, blank=True, null=True)
    candidate_longitude = models.CharField(max_length=100, blank=True, null=True)
    location_verified = models.BooleanField(default=False)
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPE_CHOICES, default='presencial')
    candidate_confirmed = models.BooleanField(default=False)

    def days_until_interview(self):
        return (self.interview_date - timezone.now()).days

class SmtpConfig(models.Model):
    host = models.CharField(max_length=255)
    port = models.IntegerField()
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255, blank=True, null=True)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.host}:{self.port}"

class ChatState(models.Model):
    user_id = models.CharField(max_length=100, db_index=True)
    platform = models.CharField(max_length=50, blank=True, null=True, choices=COMUNICATION_CHOICES)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.SET_NULL, null=True, blank=True)
    conversation_history = models.JSONField(default=list, blank=True, help_text="Historial de la conversación con el candidato.")
    applied = models.BooleanField(default=False)
    interviewed = models.BooleanField(default=False)
    last_interaction_at = models.DateTimeField(auto_now=True)
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True,
                               help_text="Perfil del candidato asociado.")  # Cambiado a ForeignKey
    class Meta:
        unique_together = ('user_id', 'business_unit')  # Permitir múltiples ChatState por persona y BU


    def __str__(self):
        return f"ChatState user={self.user_id} platform={self.platform}"

class UserInteractionLog(models.Model):
    user_id = models.CharField(max_length=100, db_index=True)
    platform = models.CharField(max_length=50, blank=True, null=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    message_direction = models.CharField(max_length=10, choices=[('in', 'Inbound'), ('out', 'Outbound')], default='in')

    def __str__(self):
        return f"{self.user_id} - {self.platform} - {self.timestamp}"


#________________________________________________________________________________________________
# Esto es para la aplicación de Milkyleak, independiente del chatbot de amigro, solo se utiliza el servidor.
#class MilkyLeak(models.Model):
    # Configuraciones de la API de Twitter
#    twitter_api_key = models.CharField(max_length=255)  # YVIxTWtkZ0NheGRiamNlem5UbkQ6MTpjaQ Client ID / 2fIV8CDPV13tZ18VpCzzK7Yu2 Api Key
#    twitter_api_secret_key = models.CharField(max_length=255)  # cSuwv9VXrxZI4yr1oaVrkCj6p6feuu4dy1QoaID1lQe7lbjXdb / 85KIRnuNGdWhJOiglSg8ramGBT4OzCqMts17uxkUIBm1tR8avu API secret
#    twitter_access_token = models.CharField(max_length=255)  # 235862444-UWHrUObIvUoNcMVSL0S5kPx0geKu88M9nawe43YM
#    twitter_access_token_secret = models.CharField(max_length=255)  # tUCYmHzpWI0YwCQ8AedFfEMHaa9pNHAt2r0AKQUdIWT78

    # Configuraciones de Mega.nz
#    mega_email = models.EmailField()  # milkyleak@gmail.com
#    mega_password = models.CharField(max_length=255, blank=True, null=True)  # PLLH_huntred2009!

    # Configuraciones adicionales
#    folder_location = models.CharField(max_length=255, help_text="Nombre del folder en Mega.nz")
#    image_prefix = models.CharField(max_length=50, help_text='ML_')
#    local_directory = models.CharField(max_length=255, default='/home/pablollh/media', help_text="Directorio local temporal para imágenes")

    # Contador de imágenes
#    image_counter = models.PositiveIntegerField(default=1)
    # Rango de tiempo aleatorio para publicaciones (en minutos)
#    min_interval = models.PositiveIntegerField(default=10, help_text="Tiempo mínimo de espera entre publicaciones (minutos)")
#    max_interval = models.PositiveIntegerField(default=20, help_text="Tiempo máximo de espera entre publicaciones (minutos)")

    # Configuración de Dropbox (App Key brg4mvkdjisvo67 / App Secret szbinvambk7anvv)
#    dropbox_access_token = models.CharField(max_length=255, blank=True, null=True)  # Token para Dropbox sl.B-gJAWUpS-lHTLRkq64AC_rz2xSwijP_fITCv9iZtmfSfywYyZYU6qUliXFi1EEy1KmPU7XLZzPcFzFR4_HBuMg9PpK6hgF96tmMeaPabPNmcfXjfIOL7jLG7EmOf-SkePCKBC5m63mf
#    dropbox_refresh_token = models.CharField(max_length=255, blank=True, null=True)  # Añadir refresh token
#    dropbox_token_expires_at = models.DateTimeField(blank=True, null=True)
#    storage_service = models.CharField(
#        max_length=10, 
#        choices=[('mega', 'Mega.nz'), ('dropbox', 'Dropbox')],
#        default='dropbox'
#    )  # Selector entre Mega y Dropbox

#    def __str__(self):
#        return f"MilkyLeak Config ({self.twitter_api_key})"

#    def increment_image_counter(self):
#        """
#        Incrementa el contador de imágenes y guarda el modelo.
#        """
#        self.image_counter += 1
#        self.save()


##  ____________  PARA LOS MODELOS DE ENTRENAMIENTO Y MACHINE LEARNING

class ReporteScraping(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    fecha = models.DateField(default=timezone.now)
    vacantes_creadas = models.IntegerField(default=0)
    exitosos = models.IntegerField(default=0)
    fallidos = models.IntegerField(default=0)
    parciales = models.IntegerField(default=0)

    def __str__(self):
        return f"Reporte de Scraping - {self.business_unit.name} - {self.fecha}"

class EnhancedMLProfile(models.Model):
    # Core User Relationship
    user = models.OneToOneField('Person', on_delete=models.CASCADE, related_name='ml_profile')
    
    # Performance Tracking
    performance_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=0.0
    )
    
    # ML Model Metadata
    model_version = models.CharField(max_length=50, default='v1.0')
    last_prediction_timestamp = models.DateTimeField(null=True, blank=True)
    
    learning_potential = models.FloatField(default=0.5)
    
    # Feedback and Improvement Tracking
    feedback_count = models.IntegerField(default=0)
    improvement_suggestions = models.JSONField(null=True, blank=True)
    
    def update_performance_metrics(self, ml_insights):
        """Update profile based on ML model predictions"""
        self.performance_score = ml_insights.get('score', 0.0)
        self.skill_adaptability_index = ml_insights.get('adaptability', 0.5)
        self.improvement_suggestions = ml_insights.get('recommendations', [])
        self.last_prediction_timestamp = timezone.now()
        self.save()
        logger.info(f"Actualizadas métricas de ML para {self.user}")

    def log_model_feedback(self, feedback_data):
        """Track model prediction feedback"""
        self.feedback_count += 1
        self.last_prediction_timestamp = timezone.now()
        # Aquí puedes agregar lógica adicional para manejar el feedback
        self.save()
        logger.info(f"Feedback registrado para {self.user}: {feedback_data}")

    def __str__(self):
        return f"EnhancedMLProfile for {self.user.nombre} {self.user.apellido_paterno}"    

class ModelTrainingLog(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    accuracy = models.FloatField()
    trained_at = models.DateTimeField(auto_now_add=True)
    model_version = models.CharField(max_length=50)

class QuarterlyInsight(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    insights_data = JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

class MigrantSupportPlatform(models.Model):
    user = models.OneToOneField(Person, on_delete=models.CASCADE)
    preferred_locations = JSONField(default=list)
    work_authorization_status = models.CharField(max_length=50)
    language_proficiencies = JSONField(default=dict)
    family_members_seeking_work = models.IntegerField(default=0)
    network_connections = models.ManyToManyField('self', blank=True)
    cultural_training_completed = models.BooleanField(default=False)
    legal_support_needed = models.BooleanField(default=False)
    potential_business_units = models.ManyToManyField(BusinessUnit)

    def match_cross_unit_opportunities(self):
        matching_opportunities = []
        for unit in self.potential_business_units.all():
            opportunities = self._find_opportunities_in_unit(unit)
            matching_opportunities.extend(opportunities)
        return matching_opportunities

class EnhancedNetworkGamificationProfile(models.Model):
    user = models.OneToOneField(Person, on_delete=models.CASCADE)
    professional_points = models.IntegerField(default=0)
    skill_endorsements = models.IntegerField(default=0)
    network_expansion_level = models.IntegerField(default=1)

    def award_points(self, activity_type):
        point_system = {
            'profile_update': 10,
            'skill_endorsement': 15,
            'successful_referral': 50,
            'completed_challenge': 25,
            'connection_made': 5
        }
        points = point_system.get(activity_type, 0)
        self.professional_points += points
        self._update_network_level()
        self.save()

    def _update_network_level(self):
        level_thresholds = [
            (100, 2),
            (250, 3),
            (500, 4),
            (1000, 5)
        ]
        for threshold, level in level_thresholds:
            if self.professional_points >= threshold:
                self.network_expansion_level = level

    def generate_networking_challenges(self):
        challenges = [
            {
                'title': 'Expand Your Network',
                'description': 'Connect with 5 professionals in your industry',
                'points_reward': 25,
                'deadline': timezone.now() + timezone.timedelta(days=30)
            },
            {
                'title': 'Skill Showcase',
                'description': 'Get 3 endorsements for a new skill',
                'points_reward': 30,
                'deadline': timezone.now() + timezone.timedelta(days=45)
            }
        ]
        return challenges
    
class VerificationCode(models.Model):
    PURPOSE_CHOICES = [
        ('update_whatsapp', 'Actualizar WhatsApp'),
        # Añade otros propósitos aquí si es necesario
    ]

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    purpose = models.CharField(max_length=50, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.person.first_name} {self.person.last_name} - {self.purpose} - {'Usado' if self.is_used else 'No usado'}"

class Interaction(models.Model):
    """
    Modelo para registrar las interacciones de los candidatos.
    """
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='interactions')
    timestamp = models.DateTimeField(auto_now_add=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.SET_NULL, null=True, blank=True)
    chat_state = models.CharField(max_length=100, null=True, blank=True)  # Puede almacenar el estado del chat o información relevante

    def __str__(self):
        return f"Interacción de {self.person} en {self.timestamp}"