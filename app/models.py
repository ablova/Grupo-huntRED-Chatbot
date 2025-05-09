from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from urllib.parse import urlparse
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta
import re
import uuid
import logging
import requests
logger=logging.getLogger(__name__)
ROLE_CHOICES=[('SUPER_ADMIN','Super Administrador'),('BU_COMPLETE','Consultor BU Completo'),('BU_DIVISION','Consultor BU División')]
PERMISSION_CHOICES=[('ALL_ACCESS','Acceso Total'),('BU_ACCESS','Acceso a BU'),('DIVISION_ACCESS','Acceso a División')]
USER_STATUS_CHOICES=[('ACTIVE','Activo'),('INACTIVE','Inactivo'),('PENDING_APPROVAL','Pendiente de Aprobación')]
VERIFICATION_STATUS_CHOICES=[('PENDING','Pendiente'),('APPROVED','Aprobado'),('REJECTED','Rechazado')]
DOCUMENT_TYPE_CHOICES=[('ID','Identificación'),('CURP','CURP'),('RFC','RFC'),('PASSPORT','Pasaporte')]
USER_AGENTS=[
    "Mozilla/5.0 (Android 10; Mobile; rv:88.0) Gecko/88.0 Firefox/88.0",
    "Mozilla/5.0 (Linux; Android 10; SM-A505FN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13.6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14.6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15.7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15.7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15.7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15.7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.51",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (iPad; CPU OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
]
PLATFORM_CHOICES=[
    ("workday","Workday"),
    ("phenom_people","Phenom People"),
    ("oracle_hcm","Oracle HCM"),
    ("sap_successfactors","SAP SuccessFactors"),
    ("adp","ADP"),
    ("peoplesoft","PeopleSoft"),
    ("meta4","Meta4"),
    ("cornerstone","Cornerstone"),
    ("ukg","UKG"),
    ("linkedin","LinkedIn"),
    ("indeed","Indeed"),
    ("greenhouse","Greenhouse"),
    ("glassdoor","Glassdoor"),
    ("computrabajo","Computrabajo"),
    ("accenture","Accenture"),
    ("santander","Santander"),
    ("eightfold_ai","EightFold AI"),
    ("default","Default"),
    ("flexible","Flexible"),
]
OFERTA_STATUS_CHOICES=[
    ('pending','Pendiente'),
    ('sent','Enviada'),
    ('signed','Firmada'),
    ('rejected','Rechazada'),
    ('expired','Expirada'),
]
COMUNICATION_CHOICES=[
    ('whatsapp','WhatsApp'),
    ('telegram','Telegram'),
    ('messenger','Messenger'),
    ('instagram','Instagram'),
    ('slack','Slack'),
    ('email','Email'),
    ('incode','INCODE Verification'),
    ('blacktrust','BlackTrust Verification'),
    ('paypal','PayPal Payment Gateway'),
    ('stripe','Stripe Payment Gateway'),
    ('mercado_pago','MercadoPago Payment Gateway'),
    ('linkedin','LinkedIn Job Posting'),
]
API_CATEGORY_CHOICES=[
    ('VERIFICATION','Verificación de Identidad'),
    ('BACKGROUND_CHECK','Verificación de Antecedentes'),
    ('MESSAGING','Envío de Mensajes'),
    ('EMAIL','Envío de Email'),
    ('SOCIAL_MEDIA','Redes Sociales'),
    ('SCRAPING','Extracción de Datos'),
    ('AI','Inteligencia Artificial'),
    ('PAYMENT_GATEWAY','Pasarela de Pago'),
    ('REPORTING','Generación de Reportes'),
    ('ANALYTICS','Análisis de Datos'),
    ('STORAGE','Almacenamiento'),
    ('PAYMENT_GATEWAY','Pasarela de Pagos'),
    ('OTHER','Otro')
]
BUSINESS_UNIT_CHOICES=[
    ('huntRED','huntRED®'),
    ('huntRED_executive','huntRED® Executive'),
    ('huntu','huntU®'),
    ('amigro','Amigro®'),
    ('sexsi','SexSI'),
]
DIVISION_CHOICES=[
    ('RECRUITING','Recruiting'),
    ('TECH','Tecnología'),
    ('HR','Recursos Humanos'),
    ('FINANCE','Finanzas'),
    ('MARKETING','Marketing'),
    ('OPERATIONS','Operaciones'),
]
INTENT_TYPE_CHOICES=[
    ('SYSTEM','Sistema'),
    ('USER','Usuario'),
    ('BUSINESS','Negocio'),
    ('FALLBACK','Respuesta por defecto'),
]
STATE_TYPE_CHOICES=[
    ('INITIAL','Inicial'),
    ('PROFILE','Perfil'),
    ('SEARCH','Búsqueda'),
    ('APPLY','Aplicación'),
    ('INTERVIEW','Entrevista'),
    ('OFFER','Oferta'),
    ('HIRED','Contratado'),
    ('IDLE','Inactivo'),
]
TRANSITION_TYPE_CHOICES=[
    ('IMMEDIATE','Inmediato'),
    ('CONDITIONAL','Condicional'),
    ('TIME_BASED','Basado en tiempo'),
    ('EVENT_BASED','Basado en evento'),
]
CONDITION_TYPE_CHOICES=[
    ('PROFILE_COMPLETE','Perfil completo'),
    ('HAS_APPLIED','Ha aplicado'),
    ('HAS_INTERVIEW','Tiene entrevista'),
    ('HAS_OFFER','Tiene oferta'),
    ('HAS_PROFILE','Tiene perfil'),
    ('HAS_CV','Tiene CV'),
    ('HAS_TEST','Tiene prueba'),
]

class BusinessUnit(models.Model):
    name=models.CharField(max_length=50,choices=BUSINESS_UNIT_CHOICES,unique=True)
    description=models.TextField(blank=True)
    admin_phone=models.CharField(max_length=20,null=True,blank=True)
    whatsapp_enabled=models.BooleanField(default=True)
    telegram_enabled=models.BooleanField(default=True)
    messenger_enabled=models.BooleanField(default=True)
    instagram_enabled=models.BooleanField(default=True)
    scrapping_enabled=models.BooleanField(default=True)
    scraping_domains=models.ManyToManyField('DominioScraping',related_name="business_units",blank=True)
    ntfy_topic=models.CharField(max_length=100,blank=True,null=True,default=None,help_text="Tema de ntfy.sh específico para esta unidad de negocio. Si no se define, usa el tema general.")
    def __str__(self):
        return dict(BUSINESS_UNIT_CHOICES).get(self.name,self.name)
    def get_ntfy_topic(self):
        from django.conf import settings
        return self.ntfy_topic or Configuracion.objects.first().get_ntfy_topic() or settings.NTFY_DEFAULT_TOPIC
    def get_notification_recipients(self):
        recipients={}
        if self.admin_phone:
            recipients['phone']=self.admin_phone
        if self.admin_email:
            recipients['email']=self.admin_email
        return recipients
    def get_email_template_path(self):
        sanitized_name=re.sub(r'\W+','',self.name).lower()
        return f'emails/template_{sanitized_name}.html'
    @property
    def admin_email(self):
        try:
            config=self.configuracionbu
            if config and config.dominio_bu:
                parsed_url=urlparse(config.dominio_bu)
                domain=parsed_url.netloc or parsed_url.path
                domain=domain.replace('www.','')
                return f'hola@{domain}'
        except ConfiguracionBU.DoesNotExist:
            pass
        return None
    def save(self,*args,**kwargs):
        super().save(*args,**kwargs)
        if not hasattr(self,'configuracionbu'):
            ConfiguracionBU.objects.create(business_unit=self)
            logger.info(f"Creada ConfiguracionBU por defecto para {self.name}")

class Person(models.Model):
    number_interaction=models.IntegerField(default=0)
    ref_num=models.CharField(max_length=50,blank=True,null=True,help_text="Número de referencia para identificar origen del registro")
    nombre=models.CharField(max_length=100)
    apellido_paterno=models.CharField(max_length=200,blank=True,null=True)
    apellido_materno=models.CharField(max_length=200,blank=True,null=True)
    nacionalidad=models.CharField(max_length=100,blank=True,null=True)
    fecha_nacimiento=models.DateField(blank=True,null=True)
    sexo=models.CharField(max_length=20,choices=[('M','Masculino'),('F','Femenino'),('O','Otro')],blank=True,null=True)
    email=models.EmailField(blank=True,null=True)
    phone=models.CharField(max_length=40,blank=True,null=True)
    linkedin_url=models.URLField(max_length=200,blank=True,null=True,help_text="URL del perfil de LinkedIn")
    preferred_language=models.CharField(max_length=5,default='es_MX',help_text="Ej: es_MX, en_US")
    fecha_creacion=models.DateTimeField(auto_now_add=True)
    tos_accepted=models.BooleanField(default=False)
    JOB_SEARCH_STATUS_CHOICES=[
        ('activa','Activa'),
        ('pasiva','Pasiva'),
        ('local','Local'),
        ('remota','Remota'),
        ('no_busca','No en búsqueda'),
    ]
    job_search_status=models.CharField(max_length=20,choices=JOB_SEARCH_STATUS_CHOICES,blank=True,null=True,help_text="Estado actual de la búsqueda de empleo.")
    skills=models.TextField(blank=True,null=True,help_text="Listado libre de skills del candidato.")
    experience_years=models.IntegerField(blank=True,null=True,help_text="Años totales de experiencia.")
    desired_job_types=models.CharField(max_length=100,blank=True,null=True,help_text="Tipos de trabajo deseados, ej: tiempo completo, medio tiempo, freelance.")
    cv_file=models.FileField(upload_to='person_files/',blank=True,null=True,help_text="CV u otro documento del candidato.")
    cv_parsed=models.BooleanField(default=False,help_text="Indica si el CV ha sido analizado.")
    cv_analysis=models.JSONField(blank=True,null=True,help_text="Datos analizados del CV.")
    salary_data=models.JSONField(default=dict,blank=True,help_text="Información salarial, beneficios y expectativas.")
    personality_data=models.JSONField(default=dict,blank=True,help_text="Perfil de personalidad.")
    experience_data=models.JSONField(default=dict,blank=True,help_text="Experiencia profesional detallada.")
    metadata=models.JSONField(default=dict,blank=True,help_text="Información adicional del candidato.")
    hire_date=models.DateField(null=True,blank=True)
    points=models.IntegerField(default=0)
    badges=models.ManyToManyField('Badge',blank=True)
    current_stage=models.ForeignKey('WorkflowStage',on_delete=models.SET_NULL,null=True,blank=True,related_name='candidatos')
    openness=models.FloatField(default=0)
    conscientiousness=models.FloatField(default=0)
    extraversion=models.FloatField(default=0)
    agreeableness=models.FloatField(default=0)
    neuroticism=models.FloatField(default=0)
    def __str__(self):
        nombre_completo=f"{self.nombre} {self.apellido_paterno or ''} {self.apellido_materno or ''}".strip()
        return nombre_completo
    def is_profile_complete(self):
        required_fields=['nombre','apellido_paterno','email','phone','skills']
        missing_fields=[field for field in required_fields if not getattr(self,field,None)]
        return not missing_fields

class Worker(models.Model):
    name=models.CharField(max_length=100)
    whatsapp=models.CharField(max_length=20,blank=True,null=True)
    company=models.CharField(max_length=100,blank=True,null=True)
    img_company=models.CharField(max_length=500,blank=True,null=True)
    job_id=models.CharField(max_length=100,blank=True,null=True)
    url_name=models.CharField(max_length=100,blank=True,null=True)
    salary=models.CharField(max_length=100,blank=True,null=True)
    job_type=models.CharField(max_length=100,blank=True,null=True)
    address=models.CharField(max_length=200,blank=True,null=True)
    longitude=models.CharField(max_length=100,blank=True,null=True)
    latitude=models.CharField(max_length=100,blank=True,null=True)
    required_skills=models.TextField(blank=True,null=True)
    experience_required=models.IntegerField(blank=True,null=True)
    job_description=models.TextField(blank=True,null=True)
    metadata=models.JSONField(default=dict,blank=True,help_text="Información adicional del puesto: sectores, requerimientos, etc.")
    class Meta:
        indexes=[
            models.Index(fields=['name']),
            models.Index(fields=['job_id']),
            models.Index(fields=['company']),
        ]
    def __str__(self):
        return str(self.name)

class Vacante(models.Model):
    titulo = models.CharField(max_length=1000)
    empresa = models.ForeignKey(Worker, on_delete=models.CASCADE)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='vacantes', null=True, blank=True)
    salario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ubicacion = models.CharField(max_length=300, blank=True, null=True)
    modalidad = models.CharField(max_length=50, choices=[
        ('presencial', 'Presencial'),
        ('remoto', 'Remoto'),
        ('hibrido', 'Híbrido')
    ], null=True, blank=True)
    remote_friendly = models.BooleanField(default=False)
    descripcion = models.TextField(max_length=3000, blank=True)
    requisitos = models.TextField(blank=True, null=True)
    beneficios = models.TextField(blank=True, null=True)
    skills_required = models.JSONField(default=list)
    activa = models.BooleanField(default=True)
    fecha_publicacion = models.DateTimeField()
    fecha_scraping = models.DateTimeField(auto_now_add=True)
    current_stage = models.ForeignKey('WorkflowStage', on_delete=models.SET_NULL, null=True, blank=True, related_name='vacantes')
    numero_plazas = models.IntegerField(default=1, help_text="Número total de plazas disponibles")
    plazas_restantes = models.IntegerField(default=1, help_text="Número de plazas aún disponibles")
    procesamiento_count = models.IntegerField(default=0, help_text="Número de candidatos en proceso")
    publicar_en = models.JSONField(default=list, help_text="Plataformas donde se publicará la vacante")
    frecuencia_publicacion = models.IntegerField(default=1, help_text="Frecuencia de publicación en días")
    max_candidatos = models.IntegerField(default=100, help_text="Máximo número de candidatos a aceptar")
    dominio_origen = models.ForeignKey('DominioScraping', on_delete=models.SET_NULL, null=True)
    url_original = models.URLField(max_length=1000, blank=True, null=True)
    sentiment = models.CharField(max_length=20, blank=True, null=True)
    job_classification = models.CharField(max_length=100, blank=True, null=True)
    requiere_prueba_personalidad = models.BooleanField(default=False)
    # Campos de LinkedIn (temporalmente deshabilitados hasta obtener acceso a la API)
    linkedin_job_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="ID de la publicación en LinkedIn (temporalmente no disponible)"
    )
    linkedin_status = models.CharField(
        max_length=20,
        choices=[
            ('not_posted', 'No publicado'),
            ('manual', 'Publicado manualmente')
        ],
        default='not_posted',
        help_text="Estado de la publicación en LinkedIn (temporalmente solo manual)"
    )
    # Origen de la vacante
    ORIGEN_CHOICES = [
        ('manual', 'Creada manualmente'),
        ('scraping', 'Obtenida por scraping'),
        ('email', 'Obtenida por email'),
        ('wordpress', 'Sincronizada de WordPress')
    ]
    origen = models.CharField(
        max_length=20,
        choices=ORIGEN_CHOICES,
        default='manual',
        help_text="Origen de la vacante (manual, scraping, email o wordpress)"
    )
    unique_together = ['titulo', 'empresa', 'url_original']
    ordering = ['-fecha_publicacion']
    def __str__(self):
        return f"{self.titulo} - {self.empresa}"

class Application(models.Model):
    user=models.ForeignKey(Person,on_delete=models.CASCADE,related_name='applications')
    vacancy=models.ForeignKey(Vacante,on_delete=models.CASCADE,related_name='applications')
    status=models.CharField(max_length=20,choices=[('applied','Applied'),('interview','Interview'),('rejected','Rejected'),('hired','Hired')],default='applied')
    applied_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    additional_notes=models.TextField(blank=True,null=True)
    def __str__(self):
        return f"{self.user} - {self.vacancy} - {self.status}"

class EntrevistaTipo(models.Model):
    TIPO_CHOICES=[('presencial','Presencial'),('virtual','Virtual'),('panel','Panel'),('otro','Otro')]
    nombre=models.CharField(max_length=50,choices=TIPO_CHOICES)
    descripcion=models.TextField(blank=True,null=True)
    def __str__(self):
        return self.nombre

class Entrevista(models.Model):
    candidato=models.ForeignKey(Person,on_delete=models.CASCADE,related_name='entrevistas')
    vacante=models.ForeignKey(Vacante,on_delete=models.CASCADE,related_name='entrevistas')
    tipo=models.ForeignKey(EntrevistaTipo,on_delete=models.SET_NULL,null=True)
    fecha=models.DateTimeField()
    resultado=models.CharField(max_length=50,choices=[('pendiente','Pendiente'),('aprobado','Aprobado'),('rechazado','Rechazado')],default='pendiente')
    comentarios=models.TextField(blank=True,null=True)
    def __str__(self):
        return f"Entrevista de {self.candidato.nombre} para {self.vacante.titulo}"

class OfertaEstado(models.Model):
    nombre=models.CharField(max_length=50)
    descripcion=models.TextField(blank=True,null=True)
    def __str__(self):
        return self.nombre

class CartaOfertaManager(models.Manager):
    def crear_carta_oferta(self,user,vacancy,salary,benefits,start_date,end_date=None):
        if not user.is_complete_profile():
            raise ValueError("El perfil del usuario debe estar completo para crear una carta de oferta.")
        estado_pendiente,_=OfertaEstado.objects.get_or_create(nombre='pendiente',defaults={'descripcion':'Oferta pendiente de aceptación'})
        carta=self.create(user=user,vacancy=vacancy,salary=salary,benefits=benefits,start_date=start_date,end_date=end_date or (start_date+timedelta(days=365)),status=estado_pendiente)
        return carta

class CartaOferta(models.Model):
    user=models.ForeignKey(Person,on_delete=models.CASCADE,related_name='cartas_oferta')
    vacancy=models.ForeignKey(Vacante,on_delete=models.CASCADE,related_name='cartas_oferta')
    salary=models.DecimalField(max_digits=10,decimal_places=2)
    benefits=models.TextField()
    start_date=models.DateField()
    end_date=models.DateField()
    status=models.CharField(max_length=20,choices=OFERTA_STATUS_CHOICES,default='pending')
    canal_envio=models.CharField(max_length=20,choices=COMUNICATION_CHOICES,null=True,blank=True)
    fecha_envio=models.DateTimeField(null=True,blank=True)
    fecha_firma=models.DateTimeField(null=True,blank=True)
    pdf_file=models.FileField(upload_to='cartas_oferta/',null=True,blank=True)
    entrevista=models.ForeignKey(Entrevista,on_delete=models.SET_NULL,null=True,blank=True,related_name='cartas_oferta')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    objects=CartaOfertaManager()
    class Meta:
        ordering=['-created_at']
        unique_together=['user','vacancy']
    def marcar_como_firmada(self):
        try:
            self.status='signed'
            self.fecha_firma=timezone.now()
            self.save()
            application=Application.objects.filter(user=self.user,vacancy=self.vacancy).first()
            if application:
                application.status='hired'
                application.save()
            chat_state=ChatState.objects.filter(person=self.user,business_unit=self.vacancy.business_unit).first()
            if chat_state:
                chat_state.state='HIRED'
                chat_state.last_transition=timezone.now()
                chat_state.save()
        except Exception as e:
            logger.error(f"Error marcando carta como firmada: {str(e)}")
            raise
    def rechazar(self):
        try:
            self.status='rejected'
            self.save()
            application=Application.objects.filter(user=self.user,vacancy=self.vacancy).first()
            if application:
                application.status='rejected'
                application.save()
        except Exception as e:
            logger.error(f"Error rechazando carta: {str(e)}")
            raise
    def get_status_badge(self):
        badge_colors={'pending':'warning','sent':'info','signed':'success','rejected':'danger','expired':'secondary'}
        return badge_colors.get(self.status,'secondary')
    def get_status_display(self):
        for value,display in OFERTA_STATUS_CHOICES:
            if value==self.status:
                return display
        return self.status
    def __str__(self):
        return f"Carta de Oferta para {self.user.nombre} - {self.vacancy.titulo} ({self.status})"

class JobTracker(models.Model):
    OPERATION_STATUS_CHOICES=[('not_started','No Iniciado'),('in_progress','En Progreso'),('completed','Completado'),('on_hold','En Espera')]
    opportunity=models.OneToOneField(Vacante,on_delete=models.CASCADE,related_name='job_tracker')
    status=models.CharField(max_length=20,choices=OPERATION_STATUS_CHOICES,default='not_started')
    start_date=models.DateField(auto_now_add=True)
    end_date=models.DateField(null=True,blank=True)
    def __str__(self):
        return f"Job Tracker para {self.opportunity.titulo}"
    def handle_job_tracker_status_change(sender,instance,**kwargs):
        if instance.status=='completed':
            print(f"El JobTracker para {instance.opportunity} ha sido completado.")



class Interview(models.Model):
    INTERVIEW_TYPE_CHOICES=[('presencial','Presencial'),('virtual','Virtual'),('panel','Panel')]
    person=models.ForeignKey(Person,on_delete=models.CASCADE)
    interviewer=models.ForeignKey(Person,on_delete=models.CASCADE,related_name='conducted_interviews',blank=True,null=True)
    job=models.ForeignKey(Worker,on_delete=models.CASCADE)
    interview_date=models.DateTimeField()
    application_date=models.DateTimeField(auto_now_add=True)
    slot=models.CharField(max_length=50)
    candidate_latitude=models.CharField(max_length=100,blank=True,null=True)
    candidate_longitude=models.CharField(max_length=100,blank=True,null=True)
    location_verified=models.BooleanField(default=False)
    interview_type=models.CharField(max_length=20,choices=INTERVIEW_TYPE_CHOICES,default='presencial')
    candidate_confirmed=models.BooleanField(default=False)
    def days_until_interview(self):
        return (self.interview_date-timezone.now()).days

class Configuracion(models.Model):
    secret_key=models.CharField(max_length=255,default='hfmrpTNRwmQ1F7gZI1DNKaQ9gNw3cgayKFB0HK_gt9BKJEnLy60v1v0PnkZtX3OkY48')
    sentry_dsn=models.CharField(max_length=255,blank=True,null=True,default='https://94c6575f877d16a00cc74bcaaab5ae79@o4508258791653376.ingest.us.sentry.io/4508258794471424')
    debug_mode=models.BooleanField(default=True)
    test_user=models.CharField(max_length=255,blank=True,null=True,default='Pablo Lelo de Larrea H.')
    test_phone_number=models.CharField(max_length=15,default='+525518490291',help_text='Número de teléfono para pruebas y reportes de ejecución')
    test_email=models.EmailField(max_length=50,default='pablo@huntred.com',help_text='Email para pruebas y reportes de ejecución')
    default_platform=models.CharField(max_length=20,default='whatsapp',choices=COMUNICATION_CHOICES,help_text='Plataforma de pruebas por defecto')
    ntfy_topic=models.CharField(max_length=100,blank=True,null=True,default=None,help_text="Tema de ntfy.sh para notificaciones generales. Si no se define, usa NTFY_DEFAULT_TOPIC de settings.")
    notification_hour=models.TimeField(blank=True,null=True,help_text='Hora para enviar notificaciones diarias de pruebas')
    is_test_mode=models.BooleanField(default=True,help_text='Indicador de modo de pruebas')
    def get_ntfy_topic(self):
        from django.conf import settings
        return self.ntfy_topic or settings.NTFY_DEFAULT_TOPIC
    def __str__(self):
        return "Configuración General del Sistema"

class DominioScraping(models.Model):
    empresa=models.CharField(max_length=75,unique=True,blank=True,null=True)
    dominio=models.URLField(max_length=255,unique=True)
    company_name=models.CharField(max_length=255,blank=True)
    email_scraping_enabled=models.BooleanField(default=False)
    valid_senders=models.JSONField(default=list)
    plataforma=models.CharField(max_length=100,choices=PLATFORM_CHOICES,blank=True,null=True)
    estado=models.CharField(max_length=20,choices=[("definido","Definido"),("libre","Indefinido")],default="libre")
    verificado=models.BooleanField(default=False)
    activo=models.BooleanField(default=True)
    cookies=models.JSONField(blank=True,null=True)
    frecuencia_scraping=models.IntegerField(default=24)
    mensaje_error=models.TextField(blank=True,null=True)
    ultima_verificacion=models.DateTimeField(blank=True,null=True)
    creado_en=models.DateTimeField(auto_now_add=True)
    actualizado_en=models.DateTimeField(auto_now=True)
    selector_titulo=models.CharField(max_length=200,null=True,blank=True)
    selector_descripcion=models.CharField(max_length=200,null=True,blank=True)
    selector_ubicacion=models.CharField(max_length=200,null=True,blank=True)
    selector_salario=models.CharField(max_length=200,null=True,blank=True)
    tipo_selector=models.CharField(max_length=20,choices=[('css','CSS'),('xpath','XPath')],default='css')
    mapeo_configuracion=models.JSONField(null=True,blank=True,help_text="Configuración personalizada (selectores, paginación, etc.)")
    def generar_correo_asignado(self):
        configuracion=ConfiguracionBU.objects.filter(scraping_domains__dominio=self.dominio).first()
        dominio_bu=configuracion.dominio_bu if configuracion else "huntred.com"
        return f"{self.empresa.lower()}@{dominio_bu}" if self.empresa else None
    def __str__(self):
        return f"{self.dominio} ({self.plataforma})"
    def detectar_plataforma(self):
        if self.plataforma:
            logger.info(f"Plataforma ya definida manualmente: {self.plataforma}")
            return
        url_lower=self.dominio.lower()
        patrones={
            'workday':r'workday\.com',
            'oracle_hcm':r'oracle\.com',
            'sap_successfactors':r'sap\.com',
            'cornerstone':r'cornerstoneondemand\.com',
            'amigro':r'amigro\.org',
        }
        for plataforma,patron in patrones.items():
            if re.search(patron,url_lower):
                self.plataforma=plataforma
                self.verificado=True
                logger.info(f"Plataforma detectada automáticamente: {plataforma}")
                return
        self.plataforma="otro"
        self.verificado=False
        logger.warning(f"No se detectó una plataforma conocida para: {self.dominio}")
    def clean(self):
        self.detectar_plataforma()
    def save(self,*args,**kwargs):
        self.clean()
        super().save(*args,**kwargs)
    class Meta:
        indexes=[models.Index(fields=['dominio'])]

class ConfiguracionScraping(models.Model):
    dominio=models.ForeignKey(DominioScraping,on_delete=models.CASCADE)
    campo=models.CharField(max_length=50)
    selector=models.CharField(max_length=200)
    tipo_selector=models.CharField(max_length=20,choices=[('css','CSS'),('xpath','XPath')])
    transformacion=models.CharField(max_length=100,null=True,blank=True)

class ConfiguracionBU(models.Model):
    business_unit=models.OneToOneField(BusinessUnit,on_delete=models.CASCADE)
    logo_url=models.URLField(default="https://huntred.com/logo.png")
    direccion_bu=models.CharField(max_length=255,default="Av. Santa Fe #428, Torre 3, Piso 15, CDMX")
    telefono_bu=models.CharField(max_length=20,default="+5255 59140089")
    correo_bu=models.CharField(max_length=20,default="hola@huntred.com")
    jwt_token=models.CharField(max_length=255,blank=True,null=True,default="...")
    dominio_bu=models.URLField(max_length=255,blank=True,null=True)
    dominio_rest_api=models.URLField(max_length=255,blank=True,null=True)
    scraping_domains=models.ManyToManyField('DominioScraping',related_name='configuracion_business_units',blank=True,help_text="Selecciona los dominios de scraping asociados a esta unidad de negocio.")
    smtp_host=models.CharField(max_length=255,blank=True,null=True)
    smtp_port=models.IntegerField(blank=True,null=True,default=587)
    smtp_username=models.CharField(max_length=255,blank=True,null=True)
    smtp_password=models.CharField(max_length=255,blank=True,null=True)
    smtp_use_tls=models.BooleanField(default=True)
    smtp_use_ssl=models.BooleanField(default=False)
    weight_location=models.IntegerField(default=10)
    weight_hard_skills=models.IntegerField(default=45)
    weight_soft_skills=models.IntegerField(default=35)
    weight_contract=models.IntegerField(default=10)
    def __str__(self):
        return f"Configuración de {self.business_unit.name if self.business_unit else 'Unidad de Negocio'}"
    def get_smtp_config(self):
        return {
            'host':self.smtp_host,
            'port':self.smtp_port,
            'username':self.smtp_username,
            'password':self.smtp_password,
            'use_tls':self.smtp_use_tls,
            'use_ssl':self.smtp_use_ssl
        }
    def calculate_tier(self,candidate_score:float):
        if candidate_score>=85:
            return "Tier 1 (Excelente)"
        elif candidate_score>=70:
            return "Tier 2 (Muy Bueno)"
        elif candidate_score>=55:
            return "Tier 3 (Bueno)"
        elif candidate_score>=40:
            return "Tier 4 (Regular)"
        else:
            return "Tier 5 (Necesita Mejora)"
    def _load_weights(self):
        try:
            config=ConfiguracionBU.objects.get(business_unit=self.business_unit)
            return {
                "ubicacion":config.weight_location or 10,
                "hard_skills":config.weight_hard_skills or 45,
                "soft_skills":config.weight_soft_skills or 35,
                "tipo_contrato":config.weight_contract or 10,
                "personalidad":config.weight_personality or 15,
            }
        except ConfiguracionBU.DoesNotExist:
            return {
                "ubicacion":5,
                "hard_skills":45,
                "soft_skills":35,
                "tipo_contrato":5,
                "personalidad":10,
            }
    def get_weights(self,position_level):
        if position_level=="gerencia_media":
            return {**self.weights,"soft_skills":40,"hard_skills":40,"ubicacion":10,"personalidad":20}
        elif position_level=="alta_direccion":
            return {**self.weights,"soft_skills":45,"hard_skills":30,"ubicacion":10,"personalidad":25}
        elif position_level=="operativo":
            return {**self.weights,"ubicacion":15,"hard_skills":50,"soft_skills":25,"personalidad":10}
        return self.weights

class InternalDocumentSignature(models.Model):
    """
    Modelo para manejar firmas digitales internas de documentos.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('signed_by_creator', 'Firmado por Creador'),
        ('signed_by_reviewer', 'Firmado por Revisor'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado')
    ]

    creator = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='created_signatures')
    reviewer = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='reviewed_signatures', null=True, blank=True)
    document_name = models.CharField(max_length=200)
    document_description = models.TextField()
    document_file = models.FileField(upload_to='internal_documents/')
    signature_method = models.CharField(
        max_length=20, 
        choices=(
            ("digital", "Firma Digital"), 
            ("electronic", "Firma Electrónica")
        ),
        default="digital"
    )
    
    # Firma y validaciones
    is_signed_by_creator = models.BooleanField(default=False)
    is_signed_by_reviewer = models.BooleanField(default=False)
    creator_signature = models.ImageField(upload_to='internal_signatures/', null=True, blank=True)
    reviewer_signature = models.ImageField(upload_to='internal_signatures/', null=True, blank=True)
    
    # Seguridad y control
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    token_expiry = models.DateTimeField()
    
    # Estado y timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Relación con Business Unit
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='internal_signatures')
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['creator', 'document_file']

    def __str__(self):
        return f"Firma #{self.id} - {self.document_name}"

    def save(self, *args, **kwargs):
        if not self.token_expiry:
            self.token_expiry = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_token_valid(self):
        return timezone.now() < self.token_expiry

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, 'Desconocido')

    def mark_as_signed_by_creator(self):
        self.is_signed_by_creator = True
        self.status = 'signed_by_creator'
        self.save()

    def mark_as_signed_by_reviewer(self):
        self.is_signed_by_reviewer = True
        self.status = 'completed'
        self.save()

    def cancel(self):
        self.status = 'cancelled'
        self.save()

    def get_absolute_url(self):
        return reverse('internal_signature_detail', kwargs={'pk': self.pk})

class WorkflowStage(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField(blank=True,null=True)
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='workflow_stages')
    order=models.PositiveIntegerField()
    class Meta:
        ordering=['order']
    def __str__(self):
        return f"{self.name} ({self.business_unit.name})"

class RegistroScraping(models.Model):
    dominio=models.ForeignKey(DominioScraping,on_delete=models.CASCADE)
    fecha_inicio=models.DateTimeField(auto_now_add=True)
    fecha_fin=models.DateTimeField(null=True)
    vacantes_encontradas=models.IntegerField(default=0)
    estado=models.CharField(max_length=50,choices=[('exitoso','Exitoso'),('fallido','Fallido'),('parcial','Parcial')])
    error_log=models.TextField(blank=True,null=True)
    def __str__(self):
        return f"Registro {self.dominio.empresa} - {self.estado} - {self.fecha_inicio}"

class IntentPattern(models.Model):
    name=models.CharField(max_length=100,unique=True)
    description=models.TextField(blank=True,null=True)
    patterns=models.TextField(help_text="Patrones de regex separados por nueva línea")
    responses=models.JSONField(default=dict,help_text="Respuestas por canal y unidad de negocio")
    priority=models.IntegerField(default=50)
    enabled=models.BooleanField(default=True)
    type=models.CharField(max_length=20,choices=INTENT_TYPE_CHOICES,default='USER')
    business_units=models.ManyToManyField(BusinessUnit,related_name='intent_patterns')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=('-priority','name')
    def __str__(self):
        return f"{self.name} ({self.type})"
    def get_patterns_list(self):
        return self.patterns.split('\n') if self.patterns else []

class StateTransition(models.Model):
    current_state=models.CharField(max_length=50,choices=STATE_TYPE_CHOICES)
    next_state=models.CharField(max_length=50,choices=STATE_TYPE_CHOICES)
    conditions=models.JSONField(default=list,help_text="Condiciones para la transición")
    type=models.CharField(max_length=20,choices=TRANSITION_TYPE_CHOICES,default='IMMEDIATE')
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='state_transitions')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('current_state','next_state','business_unit')
    def __str__(self):
        return f"{self.business_unit.name}: {self.current_state} -> {self.next_state}"

class IntentTransition(models.Model):
    current_intent=models.ForeignKey(IntentPattern,on_delete=models.CASCADE,related_name='transitions_from')
    next_intent=models.ForeignKey(IntentPattern,on_delete=models.CASCADE,related_name='transitions_to')
    conditions=models.JSONField(default=list,help_text="Condiciones para la transición")
    type=models.CharField(max_length=20,choices=TRANSITION_TYPE_CHOICES,default='IMMEDIATE')
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='intent_transitions')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('current_intent','next_intent','business_unit')
    def __str__(self):
        return f"{self.business_unit.name}: {self.current_intent.name} -> {self.next_intent.name}"

class ContextCondition(models.Model):
    name=models.CharField(max_length=100)
    type=models.CharField(max_length=50,choices=CONDITION_TYPE_CHOICES)
    value=models.TextField()
    description=models.TextField(blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.name} ({self.type})"

class ChatState(models.Model):
    person=models.ForeignKey(Person,on_delete=models.CASCADE,related_name='chat_states')
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='chat_states')
    state=models.CharField(max_length=50,choices=STATE_TYPE_CHOICES,default='INITIAL')
    last_intent=models.ForeignKey(IntentPattern,on_delete=models.SET_NULL,null=True,blank=True,related_name='chat_states')
    conversation_history=models.JSONField(default=list)
    last_transition=models.DateTimeField(auto_now=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('person','business_unit')
    def __str__(self):
        return f"{self.person.nombre} - {self.business_unit.name} ({self.state})"
    def get_available_intents(self):
        current_state=self.state
        bu=self.business_unit
        transitions=StateTransition.objects.filter(current_state=current_state,business_unit=bu)
        available_intents=IntentPattern.objects.filter(business_units=bu,enabled=True)
        filtered_intents=[intent for intent in available_intents if IntentTransition.objects.filter(current_intent=intent,business_unit=bu).exists()]
        return filtered_intents
    def validate_transition(self,new_state):
        try:
            StateTransition.objects.get(current_state=self.state,next_state=new_state,business_unit=self.business_unit)
            return True
        except StateTransition.DoesNotExist:
            return False
    def transition_to(self,new_state):
        if self.validate_transition(new_state):
            self.state=new_state
            self.last_transition=timezone.now()
            self.save()
            return True
        return False
@receiver(post_save,sender=Person)
def create_chat_states(sender,instance,created,**kwargs):
    """
    Crea estados de chat iniciales para una nueva persona.
    """
    if created:
        for bu in BusinessUnit.objects.all():
            ChatState.objects.create(person=instance,business_unit=bu)
@receiver(post_save,sender=Application)
def update_chat_state_on_application(sender,instance,created,**kwargs):
    if created:
        chat_state=ChatState.objects.get(person=instance.user,business_unit=instance.vacancy.business_unit)
        chat_state.transition_to('APPLY')
@receiver(post_save,sender=Interview)
def update_chat_state_on_interview(sender,instance,created,**kwargs):
    if created:
        chat_state=ChatState.objects.get(person=instance.person,business_unit=instance.job.business_unit)
        chat_state.transition_to('INTERVIEW')
@receiver(post_save,sender=Application)
def update_chat_state_on_offer_accepted(sender,instance,**kwargs):
    if instance.status=='hired':
        chat_state=ChatState.objects.filter(person=instance.user,business_unit=instance.vacancy.business_unit).first()
        if chat_state:
            chat_state.state='HIRED'
            chat_state.last_transition=timezone.now()
            chat_state.save()

class CustomUserManager(BaseUserManager):
    def create_user(self,email,password=None,**extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email=self.normalize_email(email)
        user=self.model(email=email,**extra_fields)
        user.set_password(password)
        user.save()
        return user
    def create_superuser(self,email,password,**extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        extra_fields.setdefault('role','SUPER_ADMIN')
        extra_fields.setdefault('status','ACTIVE')
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email,password,**extra_fields)

class CustomUser(AbstractUser):
    username=None
    email=models.EmailField(_('email address'),unique=True)
    role=models.CharField(max_length=20,choices=ROLE_CHOICES,default='BU_DIVISION')
    status=models.CharField(max_length=20,choices=USER_STATUS_CHOICES,default='PENDING_APPROVAL')
    verification_status=models.CharField(max_length=20,choices=VERIFICATION_STATUS_CHOICES,default='PENDING')
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.SET_NULL,null=True,blank=True)
    division=models.CharField(max_length=50,choices=DIVISION_CHOICES,blank=True,null=True)
    phone_number=models.CharField(max_length=20,blank=True,null=True)
    emergency_contact=models.CharField(max_length=20,blank=True,null=True)
    emergency_contact_name=models.CharField(max_length=100,blank=True,null=True)
    address=models.TextField(blank=True,null=True)
    date_of_birth=models.DateField(blank=True,null=True)
    USERNAME_FIELD='email'
    REQUIRED_FIELDS=['first_name','last_name']
    objects=CustomUserManager()
    class Meta:
        ordering=['-date_joined']
        verbose_name='Usuario'
        verbose_name_plural='Usuarios'
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    def has_bu_access(self,bu_name):
        if self.role=='SUPER_ADMIN':
            return True
        if self.business_unit and self.business_unit.name==bu_name:
            return True
        return False
    def has_division_access(self,division_name):
        if self.role=='SUPER_ADMIN':
            return True
        if self.division==division_name:
            return True
        return False
    def has_permission(self,permission):
        return self.userpermission_set.filter(permission=permission).exists()
    def clean(self):
        if not self.email:
            raise ValidationError(_('El email no puede estar vacío.'))
    def save(self,*args,**kwargs):
        self.full_clean()
        super().save(*args,**kwargs)

class UserPermission(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='permissions')
    permission=models.CharField(max_length=50,choices=PERMISSION_CHOICES)
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,null=True,blank=True)
    division=models.CharField(max_length=50,choices=DIVISION_CHOICES,blank=True,null=True)
    class Meta:
        unique_together=('user','permission','business_unit','division')
        verbose_name='Permiso de Usuario'
        verbose_name_plural='Permisos de Usuarios'
    def __str__(self):
        return f"{self.user.email} - {self.permission}"

class FailedLoginAttempt(models.Model):
    email=models.EmailField()
    ip_address=models.GenericIPAddressField()
    user_agent=models.TextField()
    attempt_time=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.email} - {self.attempt_time}"
    def clean(self):
        if not self.user_agent:
            raise ValidationError(_('El user_agent no puede estar vacío.'))
    def save(self,*args,**kwargs):
        self.full_clean()
        super().save(*args,**kwargs)

class UserActivityLog(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='activity_logs')
    action=models.CharField(max_length=100)
    description=models.TextField()
    ip_address=models.GenericIPAddressField()
    user_agent=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name='Registro de Actividad'
        verbose_name_plural='Registros de Actividad'
        ordering=['-created_at']
    def __str__(self):
        return f"{self.user.email} - {self.action} ({self.created_at})"
    def save(self,*args,**kwargs):
        if not self.user_agent:
            raise ValidationError(_('El user_agent no puede estar vacío.'))
        super().save(*args,**kwargs)
@receiver(post_save,sender=CustomUser)
@sync_to_async
def create_user_activity(sender,instance,created,**kwargs):
    if created:
        UserActivityLog.objects.create(
            user=instance,
            action='USER_CREATED',
            description=f'Nueva cuenta de usuario creada: {instance.email}',
            ip_address='127.0.0.1',
            user_agent='System'
        )
@receiver(post_save,sender=FailedLoginAttempt)
@sync_to_async
def log_failed_login(sender,instance,created,**kwargs):
    if created:
        UserActivityLog.objects.create(
            user=None,
            action='FAILED_LOGIN',
            description=f'Intento fallido de login desde {instance.ip_address}',
            ip_address=instance.ip_address,
            user_agent=instance.user_agent
        )
@receiver(post_save,sender=UserPermission)
@sync_to_async
def log_permission_change(sender,instance,created,**kwargs):
    action='PERMISSION_GRANTED' if created else 'PERMISSION_UPDATED'
    UserActivityLog.objects.create(
        user=instance.user,
        action=action,
        description=f'Permiso {instance.permission} actualizado',
        ip_address='127.0.0.1',
        user_agent='System'
    )

class Invitacion(models.Model):
    referrer=models.ForeignKey(Person,related_name='invitaciones_enviadas',on_delete=models.CASCADE)
    invitado=models.ForeignKey(Person,related_name='invitaciones_recibidas',on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)

class Division(models.Model):
    name=models.CharField(max_length=100,unique=True)
    skills=models.ManyToManyField('Skill',blank=True)
    def __str__(self):
        return self.name

class Skill(models.Model):
    name=models.CharField(max_length=100,unique=True)
    def __str__(self):
        return self.name

class Badge(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField()
    icon=models.ImageField(upload_to='badges/',null=True,blank=True)
    def __str__(self):
        return self.name

class DivisionTransition(models.Model):
    person=models.ForeignKey(Person,on_delete=models.CASCADE)
    from_division=models.CharField(max_length=50)
    to_division=models.CharField(max_length=50)
    success=models.BooleanField(default=True)
    date=models.DateTimeField(auto_now_add=True)

class ApiConfig(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,related_name='api_configs',on_delete=models.CASCADE,null=True,blank=True,help_text="Si está vacío, la configuración es global para todas las unidades de negocio")
    api_type=models.CharField(max_length=50,choices=COMUNICATION_CHOICES)
    category=models.CharField(max_length=50,choices=API_CATEGORY_CHOICES,help_text="Categoría de la API para identificar su propósito principal")
    api_key=models.CharField(max_length=255,blank=True,null=True)
    api_secret=models.CharField(max_length=255,blank=True,null=True)
    additional_settings=models.JSONField(default=dict,blank=True,null=True)
    description=models.TextField(blank=True,null=True)
    enabled=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    
    @classmethod
    def get_config(cls, api_type, business_unit=None):
        """
        Obtiene la configuración de API más apropiada para el tipo y unidad de negocio especificados.
        Si no existe una configuración específica, retorna None.
        """
        try:
            if business_unit:
                return cls.objects.get(
                    api_type=api_type,
                    business_unit=business_unit,
                    enabled=True
                )
            else:
                return cls.objects.get(
                    api_type=api_type,
                    business_unit__isnull=True,
                    enabled=True
                )
        except cls.DoesNotExist:
            return None
    def __str__(self):
        return f"{self.business_unit.name if self.business_unit else 'Global'} - {self.api_type} - {self.description[:50]}"
    class Meta:
        verbose_name="API Configuration"
        verbose_name_plural="API Configurations"
        unique_together=['business_unit','api_type']
    def get_verification_settings(self):
        if self.api_type in ['incode','blacktrust']:
            return {
                'base_url':self.additional_settings.get('base_url',{
                    'incode':'https://api.incode.com',
                    'blacktrust':'https://api.blacktrust.com'
                }.get(self.api_type)),
                'timeout':self.additional_settings.get('timeout',30),
                'retry_count':self.additional_settings.get('retry_count',3),
                'verification_types':self.additional_settings.get('verification_types',{
                    'incode':['INE','ID','passport'],
                    'blacktrust':['criminal','credit','employment']
                }.get(self.api_type))
            }
        return self.additional_settings
    def get_payment_settings(self):
        if self.api_type in ['paypal','stripe','mercado_pago']:
            settings = {
                'base_url': self.additional_settings.get('base_url', {
                    'paypal': 'https://api.paypal.com',
                    'stripe': 'https://api.stripe.com',
                    'mercado_pago': 'https://api.mercadopago.com'
                }.get(self.api_type)),
                'timeout': self.additional_settings.get('timeout', 30),
                'retry_count': self.additional_settings.get('retry_count', 3),
                'webhook_url': self.additional_settings.get('webhook_url'),
                'currency': self.additional_settings.get('currency', 'MXN'),
                'environment': self.additional_settings.get('environment', 'production')
            }
            if self.api_type == 'stripe':
                settings['version'] = self.additional_settings.get('version', '2023-10-16')
            elif self.api_type == 'mercado_pago':
                settings['public_key'] = self.additional_settings.get('public_key')
            return settings
        return self.additional_settings
    def get_business_units(self):
        if self.business_unit:
            return [self.business_unit]
        return BusinessUnit.objects.all()

class MetaAPI(models.Model):
    business_unit=models.OneToOneField(BusinessUnit,on_delete=models.CASCADE,related_name='meta_api_config')
    app_id=models.CharField(max_length=255,default='662158495636216')
    app_secret=models.CharField(max_length=255,default='...')
    verify_token=models.CharField(max_length=255,default='amigro_secret_token')
    def __str__(self):
        return f"MetaAPI {self.business_unit.name} ({self.app_id})"

class WhatsAppAPI(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='whatsapp_apis',null=True,blank=True)
    name=models.CharField(max_length=50)
    phoneID=models.CharField(max_length=20,default='114521714899382')
    api_token=models.CharField(max_length=500,default='...')
    WABID=models.CharField(max_length=20,default='104851739211207')
    v_api=models.CharField(max_length=10,default='v22.0')
    meta_api=models.ForeignKey(MetaAPI,on_delete=models.CASCADE)
    is_active=models.BooleanField(default=True)
    def __str__(self):
        return f"{self.business_unit.name if self.business_unit else ''} - WhatsApp API {self.phoneID}"

class Template(models.Model):
    TEMPLATE_TYPES=[('FLOW','Flow'),('BUTTON','Button'),('URL','URL'),('IMAGE','Image')]
    whatsapp_api=models.ForeignKey(WhatsAppAPI,on_delete=models.CASCADE,related_name='templates')
    name=models.CharField(max_length=100)
    is_flow=models.BooleanField(default=False)
    template_type=models.CharField(max_length=20,choices=TEMPLATE_TYPES)
    image_url=models.URLField(blank=True,null=True)
    language_code=models.CharField(max_length=10,default='es_MX')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        unique_together=('whatsapp_api','name','language_code')
    def __str__(self):
        return f"{self.name} ({self.language_code}) - {self.whatsapp_api.business_unit.name if self.whatsapp_api.business_unit else 'Sin BU'}"

class MessengerAPI(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='messenger_apis',null=True,blank=True)
    page_id=models.CharField(max_length=255,unique=True)
    page_access_token=models.CharField(max_length=255)
    meta_api=models.ForeignKey(MetaAPI,on_delete=models.CASCADE)
    is_active=models.BooleanField(default=True)
    def __str__(self):
        return f"{self.business_unit.name if self.business_unit else ''} - Messenger API"

class InstagramAPI(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='instagram_apis',null=True,blank=True)
    app_id=models.CharField(max_length=255,default='1615393869401916')
    access_token=models.CharField(max_length=255,default='...')
    instagram_account_id=models.CharField(max_length=255,default='17841457231476550')
    meta_api=models.ForeignKey(MetaAPI,on_delete=models.CASCADE)
    is_active=models.BooleanField(default=True)
    def __str__(self):
        return f"{self.business_unit.name if self.business_unit else ''} - Instagram API"

class TelegramAPI(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='telegram_apis',null=True,blank=True)
    api_key=models.CharField(max_length=255)
    bot_name=models.CharField(max_length=255,blank=True,null=True)
    is_active=models.BooleanField(default=True)
    def __str__(self):
        return f"{self.business_unit.name if self.business_unit else ''} - Telegram Bot"

class SlackAPI(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE)
    bot_token=models.CharField(max_length=255)
    is_active=models.BooleanField(default=True)

class Provider(models.Model):
    name=models.CharField(max_length=50,unique=True,verbose_name="Nombre del proveedor")
    api_endpoint=models.URLField(verbose_name="Endpoint de la API",help_text="URL base para interactuar con la API")
    models_endpoint=models.URLField(blank=True,null=True,verbose_name="Endpoint de modelos",help_text="URL para obtener modelos disponibles")
    class Meta:
        verbose_name="Proveedor de IA"
        verbose_name_plural="Proveedores de IA"
    def __str__(self):
        return self.name
    def fetch_models(self,api_token=None):
        if not self.models_endpoint or not api_token:
            return []
        try:
            headers={"Authorization":f"Bearer {api_token}"}
            response=requests.get(self.models_endpoint,headers=headers)
            response.raise_for_status()
            data=response.json()
            if self.name=="OpenAI":
                return [model["id"] for model in data["data"]]
            elif self.name=="Grok (X AI)":
                return data.get("models",[])
            elif self.name=="Google (Gemini)":
                return [model["name"] for model in data.get("models",[])]
            return []
        except Exception as e:
            logger.error(f"Error al obtener modelos de {self.name}: {e}")
            return []

class GptApi(models.Model):
    provider=models.ForeignKey(Provider,on_delete=models.CASCADE,verbose_name="Proveedor")
    model=models.CharField(max_length=100,verbose_name="Modelo específico",help_text="Ejemplo: gpt-4o, gemini-1.5-flash-001")
    is_active=models.BooleanField(default=False,verbose_name="Activo")
    api_token=models.CharField(max_length=255,blank=True,null=True,verbose_name="Token API")
    organization=models.CharField(max_length=100,blank=True,null=True,verbose_name="Organización")
    project=models.CharField(max_length=100,blank=True,null=True,verbose_name="Proyecto")
    max_tokens=models.IntegerField(default=1000,verbose_name="Máximo de tokens")
    temperature=models.FloatField(default=0.7,verbose_name="Temperatura")
    top_p=models.FloatField(default=1.0,verbose_name="Top P")
    prompts=models.JSONField(default=dict,blank=True,verbose_name="Prompts personalizados")
    tabiya_enabled=models.BooleanField(default=False,verbose_name="Tabiya habilitado")
    class Meta:
        verbose_name="Configuración de API GPT"
        verbose_name_plural="Configuraciones de API GPT"
    def __str__(self):
        return f"{self.model} ({self.provider.name}) - {'Activo' if self.is_active else 'Inactivo'}"
    def get_prompt(self,key,default=None):
        return self.prompts.get(key,default)
    def save(self,*args,**kwargs):
        if self.is_active:
            GptApi.objects.filter(is_active=True).exclude(id=self.id).update(is_active=False)
        super().save(*args,**kwargs)
    def available_models(self):
        return self.provider.fetch_models(self.api_token)

class Chat(models.Model):
    body=models.TextField(max_length=1000)
    SmsStatus=models.CharField(max_length=15,null=True,blank=True)
    From=models.CharField(max_length=15)
    To=models.CharField(max_length=15)
    ProfileName=models.CharField(max_length=50)
    ChannelPrefix=models.CharField(max_length=50)
    MessageSid=models.CharField(max_length=100,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    message_count=models.IntegerField(default=0)
    def __str__(self):
        return str(self.body)

class JobOpportunity(models.Model):
    title=models.CharField(max_length=255)
    description=models.TextField()
    requirements=models.TextField()
    location=models.CharField(max_length=255)
    salary=models.CharField(max_length=100,blank=True,null=True)
    status=models.CharField(max_length=20,choices=[
        ('DRAFT', 'Borrador'),
        ('ACTIVE', 'Activa'),
        ('PAUSED', 'En Pausa'),
        ('CLOSED', 'Cerrada')
    ], default='DRAFT')
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE,related_name='job_opportunities')
    
    # Información de plazas
    numero_plazas=models.IntegerField(default=1, help_text="Número total de plazas disponibles")
    plazas_restantes=models.IntegerField(default=1, help_text="Número de plazas aún disponibles")
    
    # Información de contratación
    contrataciones_exitosas=models.IntegerField(default=0, help_text="Número de contrataciones exitosas")
    candidatos_aplicados=models.ManyToManyField('Person', through='JobApplication', related_name='opportunities_applied')
    
    # Información de publicación
    fecha_publicacion=models.DateTimeField(null=True, blank=True, help_text="Fecha de primera publicación")
    fecha_cierre=models.DateTimeField(null=True, blank=True, help_text="Fecha de cierre de la oportunidad")
    
    # Configuración de publicación
    publicar_en=models.JSONField(default=list, help_text="Plataformas donde se publicará la oportunidad")
    frecuencia_publicacion=models.IntegerField(default=1, help_text="Frecuencia de publicación en días")
    max_candidatos=models.IntegerField(default=100, help_text="Máximo número de candidatos a aceptar")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    def get_publish_channels(self):
        from app.publish.models import Channel
        return Channel.objects.filter(business_unit=self.business_unit,is_active=True)
    def get_channel_config(self,channel_type):
        if channel_type=='WHATSAPP':
            return WhatsAppAPI.objects.filter(business_unit=self.business_unit,is_active=True).first()
        elif channel_type=='TELEGRAM':
            return TelegramAPI.objects.filter(business_unit=self.business_unit,is_active=True).first()
        return None

class SmtpConfig(models.Model):
    host=models.CharField(max_length=255)
    port=models.IntegerField()
    username=models.CharField(max_length=255)
    password=models.CharField(max_length=255,blank=True,null=True)
    use_tls=models.BooleanField(default=True)
    use_ssl=models.BooleanField(default=False)
    def __str__(self):
        return f"{self.host}:{self.port}"

class UserInteractionLog(models.Model):
    user_id=models.CharField(max_length=100,db_index=True)
    platform=models.CharField(max_length=50,blank=True,null=True)
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.SET_NULL,null=True,blank=True)
    timestamp=models.DateTimeField(auto_now_add=True)
    message_direction=models.CharField(max_length=10,choices=[('in','Inbound'),('out','Outbound')],default='in')
    def __str__(self):
        return f"{self.user_id} - {self.platform} - {self.timestamp}"

class ReporteScraping(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE)
    fecha=models.DateField(default=timezone.now)
    vacantes_creadas=models.IntegerField(default=0)
    exitosos=models.IntegerField(default=0)
    fallidos=models.IntegerField(default=0)
    parciales=models.IntegerField(default=0)
    def __str__(self):
        return f"Reporte de Scraping - {self.business_unit.name} - {self.fecha}"

class EnhancedMLProfile(models.Model):
    user=models.OneToOneField(Person,on_delete=models.CASCADE,related_name='ml_profile')
    points=models.IntegerField(default=0)
    level=models.IntegerField(default=1)
    performance_score=models.FloatField(validators=[MinValueValidator(0.0),MaxValueValidator(100.0)],default=0.0)
    model_version=models.CharField(max_length=50,default='v1.0')
    last_prediction_timestamp=models.DateTimeField(null=True,blank=True)
    learning_potential=models.FloatField(default=0.5)
    feedback_count=models.IntegerField(default=0)
    improvement_suggestions=models.JSONField(null=True,blank=True)
    def update_performance_metrics(self,ml_insights):
        self.performance_score=ml_insights.get('score',0.0)
        self.skill_adaptability_index=ml_insights.get('adaptability',0.5)
        self.improvement_suggestions=ml_insights.get('recommendations',[])
        self.last_prediction_timestamp=timezone.now()
        self.save()
        logger.info(f"Actualizadas métricas de ML para {self.user}")
    def log_model_feedback(self,feedback_data):
        self.feedback_count+=1
        self.last_prediction_timestamp=timezone.now()
        self.save()
        logger.info(f"Feedback registrado para {self.user}: {feedback_data}")
    def __str__(self):
        return f"EnhancedMLProfile for {self.user.nombre} {self.user.apellido_paterno}"

class ModelTrainingLog(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE)
    accuracy=models.FloatField()
    trained_at=models.DateTimeField(auto_now_add=True)
    model_version=models.CharField(max_length=50)

class QuarterlyInsight(models.Model):
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.CASCADE)
    insights_data=models.JSONField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

class MigrantSupportPlatform(models.Model):
    user=models.OneToOneField(Person,on_delete=models.CASCADE)
    preferred_locations=JSONField(default=list)
    work_authorization_status=models.CharField(max_length=50)
    language_proficiencies=JSONField(default=dict)
    family_members_seeking_work=models.IntegerField(default=0)
    network_connections=models.ManyToManyField('self',blank=True)
    cultural_training_completed=models.BooleanField(default=False)
    legal_support_needed=models.BooleanField(default=False)
    potential_business_units=models.ManyToManyField(BusinessUnit)
    def match_cross_unit_opportunities(self):
        matching_opportunities=[]
        for unit in self.potential_business_units.all():
            opportunities=self._find_opportunities_in_unit(unit)
            matching_opportunities.extend(opportunities)
        return matching_opportunities

class EnhancedNetworkGamificationProfile(models.Model):
    user=models.OneToOneField(Person,on_delete=models.CASCADE)
    professional_points=models.IntegerField(default=0)
    skill_endorsements=models.IntegerField(default=0)
    network_expansion_level=models.IntegerField(default=1)
    def award_points(self,activity_type):
        point_system={
            'profile_update':10,
            'skill_endorsement':15,
            'successful_referral':50,
            'completed_challenge':25,
            'connection_made':5
        }
        points=point_system.get(activity_type,0)
        self.professional_points+=points
        self._update_network_level()
        self.save()
    def _update_network_level(self):
        level_thresholds=[(100,2),(250,3),(500,4),(1000,5)]
        for threshold,level in level_thresholds:
            if self.professional_points>=threshold:
                self.network_expansion_level=level
    def generate_networking_challenges(self):
        challenges=[
            {
                'title':'Expand Your Network',
                'description':'Connect with 5 professionals in your industry',
                'points_reward':25,
                'deadline':timezone.now()+timezone.timedelta(days=30)
            },
            {
                'title':'Skill Showcase',
                'description':'Get 3 endorsements for a new skill',
                'points_reward':30,
                'deadline':timezone.now()+timezone.timedelta(days=45)
            }
        ]
        return challenges

class VerificationCode(models.Model):
    PURPOSE_CHOICES=[('update_whatsapp','Actualizar WhatsApp')]
    person=models.ForeignKey(Person,on_delete=models.CASCADE)
    key=models.UUIDField(default=uuid.uuid4,editable=False,unique=True)
    purpose=models.CharField(max_length=50,choices=PURPOSE_CHOICES)
    created_at=models.DateTimeField(auto_now_add=True)
    is_used=models.BooleanField(default=False)
    def __str__(self):
        return f"{self.person.first_name} {self.person.last_name} - {self.purpose} - {'Usado' if self.is_used else 'No usado'}"

class Interaction(models.Model):
    person=models.ForeignKey(Person,on_delete=models.CASCADE,related_name='interactions')
    timestamp=models.DateTimeField(auto_now_add=True)
    business_unit=models.ForeignKey(BusinessUnit,on_delete=models.SET_NULL,null=True,blank=True)
    chat_state=models.CharField(max_length=100,null=True,blank=True)
    def __str__(self):
        return f"Interacción de {self.person} en {self.timestamp}"