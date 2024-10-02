# /home/amigro/app/models.py
from django.db import models
from datetime import datetime, timedelta

# Estado del Chat
class ChatState(models.Model):
    user_id = models.CharField(max_length=50)
    platform = models.CharField(max_length=20)  # 'telegram', 'whatsapp', 'messenger'
    current_question = models.ForeignKey('Pregunta', on_delete=models.CASCADE, null=True, blank=True)
    last_interaction = models.DateTimeField(auto_now=True)
    last_sub_pregunta_id = models.IntegerField(blank=True, null=True)
    context = models.JSONField(blank=True, null=True, default=dict)  # Para almacenar contexto adicional

    def __str__(self):
        return f"ChatState {self.user_id} - {self.platform}"

# Condiciones que se pueden usar para determinar la siguiente pregunta
class Condicion(models.Model):
    nombre = models.CharField(max_length=100)
    valor_esperado = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Condicion: {self.nombre} (espera: {self.valor_esperado})"

# Etapas del Chatbot
class Etapa(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Pregunta(models.Model):
    INPUT_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('email', 'Correo Electrónico'),
        ('date', 'Fecha'),
        ('phone', 'Teléfono'),
        ('sexo', 'Sexo'),
        ('number_interaction', 'Número de Interacción'),
        ('lastname', 'Apellido'),
        ('nationality', 'Nacionalidad'),
        ('family_traveling', 'Viaje Familiar'),
        ('policie', 'Política Aceptada'),
        ('passport', 'Pasaporte'),
        ('additional_official_documentation', 'Documentación Adicional'),
        ('int_work', 'Trabajo en la Industria'),
        ('menor', 'Menor de Edad'),
        ('refugio', 'Refugio'),
        ('perm_humanitario', 'Permiso Humanitario'),
        ('solicita_refugio', 'Solicita Refugio'),
        ('cita', 'Cita'),
        ('piensa_solicitar_refugio', 'Pensando en Solicitar Refugio'),
        ('industria_work', 'Industria de Trabajo'),
        ('licencia', 'Licencia de Conducir'),
        ('curp', 'CURP'),
        ('date_permit', 'Fecha de Permiso'),
        ('ubication', 'Ubicación Actual del Candidato/Migrante'),
        ('work_experience', 'Experiencia de Trabajo'),
        ('saludo', 'Saludo'),
        ('file', 'Carga de CV - Archivo'),
        ('per_trabajo', 'Permanente en Trabajo'),
    ]

    name = models.TextField(max_length=800)
    etapa = models.ForeignKey(Etapa, on_delete=models.CASCADE)  # Asociación directa a la etapa
    option = models.CharField(max_length=50)
    valid = models.BooleanField(null=True, blank=True)
    yes_or_not = models.BooleanField(null=True, blank=True)
    active = models.BooleanField()
    content = models.TextField(blank=True, null=True)
    sub_pregunta = models.ManyToManyField('SubPregunta', blank=True, related_name='pregunta_principal')
    decision = models.JSONField(blank=True, null=True, default=dict)  # {respuesta: id_pregunta_siguiente}
    condiciones = models.ManyToManyField(Condicion, blank=True)  # Condiciones para avanzar a la siguiente pregunta
    input_type = models.CharField(max_length=100, choices=INPUT_TYPE_CHOICES, blank=True, null=True)  # Tipo de entrada esperada
    requires_response = models.BooleanField(default=True)  # Nuevo campo

    def __str__(self):
        return str(self.name)

# SubPregunta dentro de una Pregunta
class SubPregunta(models.Model):
    INPUT_TYPE_CHOICES = Pregunta.INPUT_TYPE_CHOICES
    name = models.TextField(max_length=800)
    option = models.CharField(max_length=50)
    valid = models.BooleanField(null=True, blank=True)
    yes_or_not = models.BooleanField(null=True, blank=True)
    active = models.BooleanField()
    content = models.TextField(blank=True, null=True)
    parent_sub_pregunta = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)  # Para enlazar subpreguntas
    decision = models.JSONField(blank=True, null=True, default=dict)  # {respuesta: id_pregunta_siguiente}
    input_type = models.CharField(max_length=100, choices=INPUT_TYPE_CHOICES, blank=True, null=True)  # Tipo de entrada esperada
    requires_response = models.BooleanField(default=True)  # Nuevo campo

    def __str__(self):
        return str(self.name)

# Integración API de Telegram y Messenger
class TelegramAPI(models.Model):
    api_key = models.CharField(max_length=255, blank=False, null=False)
    bot_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.bot_name or "Telegram Bot"
    
class MetaAPI(models.Model):
    app_id = models.CharField(max_length=255 default='662158495636216')
    app_secret = models.CharField(max_length=255 default='7732534605ab6a7b96c8e8e81ce02e6b')   
    verify_token = models.CharField(max_length=255 default='amigro_secret_token')

    def __str__(self):
        return f"MetaAPI {self.app_id}"
        
# Integración API de WhatsApp
class WhatsAppAPI(models.Model):
    phoneID = models.CharField(max_length=100)
    api_token = models.CharField(max_length=500)  # Token de corto plazo
    WABID = models.CharField(max_length=100, default='104851739211207')
    v_api = models.CharField(max_length=100)
    
    def __str__(self):
        return f"WhatsApp API {self.phoneID}"

    def is_token_expiring_soon(self):
        """
        Verifica si el token expira en los próximos 5 días.
        """
        if self.token_expires_at:
            return (self.token_expires_at - datetime.now()).days <= 5
        return False

class MessengerAPI(models.Model):
    page_access_token = models.CharField(max_length=255, blank=False, null=False)

    def __str__(self):
        return "Messenger Configuration"
    
class InstagramAPI(models.Model):
    app_id = models.CharField(max_length=255, default ='1615393869401916') # Amigro-IG amigro_org 17841457231476550
    access_token = models.CharField(max_length=255  default = '5d8740cb80ae42d8b5cafb47e6c461d5') #IGQWROZA1BQNXB2UElFQms3SlhzT0M4bUJzZA2ZAQNFpISTNsZAHVOb1pYeXNkVExWMGhzNjdjYlQ2MnQzQ1RqQ043Slh5SzFmVXFmOGdxX0l5aTZAvWjhkcUlKRzl6ajE1dElrdmVUbDE3d0ozTm0yU0ZANaDVvU0dJcmMZD
    instagram_account_id = models.CharField(max_length=255 default = '17841457231476550')
    def __str__(self):
        return f"InstagramAPI {self.app_id}"

# GPT API para el chatbot
class GptApi(models.Model):
    api_token = models.CharField(max_length=500)
    organization = models.CharField(max_length=100, blank=True, null=True)
    project = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100)
    form_pregunta = models.CharField(max_length=500)
    work_pregunta = models.CharField(max_length=500)

    def __str__(self):
        return f"Model: {self.model} | Organization: {self.organization} | Project: {self.project}"

# Modelo para guardar chat
class Chat(models.Model):
    body = models.TextField(max_length=1000)
    SmsStatus = models.CharField(max_length=15, null=True, blank=True)
    From = models.CharField(max_length=15)
    To = models.CharField(max_length=15)
    ProfileName = models.CharField(max_length=50)
    ChannelPrefix = models.CharField(max_length=50)
    MessageSid = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return str(self.body)

class Worker(models.Model):
    name = models.CharField(max_length=100)
    job_id = models.CharField(max_length=100, blank=True, null=True)
    url_name = models.CharField(max_length=100, blank=True, null=True)
    salary = models.CharField(max_length=100, blank=True, null=True)
    job_type = models.CharField(max_length=100, blank=True, null=True)
    img_company = models.CharField(max_length=500, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    longitude = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.CharField(max_length=100, blank=True, null=True)
    required_skills = models.TextField(blank=True, null=True)  # Habilidades requeridas, separadas por comas
    experience_required = models.IntegerField(blank=True, null=True)  # Años de experiencia requeridos
    job_description = models.TextField(blank=True, null=True)
    job_type = models.CharField(max_length=100, blank=True, null=True)
    interview_slots = models.JSONField(blank=True, null=True)  # Formato de los slots: [{"date": "2023-09-30", "time": "15:00", "available": True}, ...]

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['job_id']),
            models.Index(fields=['company']),
        ]

    def __str__(self) -> str:
        return str(self.name)

# Personas que interactúan con el chatbot, usuarios, migrantes - a la base de datos
class Person(models.Model):
    #user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    number_interaction = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100, blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    nacimiento = models.DateField(blank=True, null=True)
    sexo = models.CharField(max_length=20, choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')])
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=40, blank=True, null=True)
    family_traveling = models.BooleanField(default=False)
    policie = models.BooleanField(default=False)
    group_aditionality = models.BooleanField(default=False)
    passport = models.CharField(max_length=50, blank=True, null=True)
    additional_official_documentation = models.CharField(max_length=50, blank=True, null=True)
    int_work = models.BooleanField(default=False)
    menor = models.BooleanField(default=False)
    refugio = models.BooleanField(default=False)
    perm_humanitario = models.BooleanField(default=False)
    solicita_refugio = models.BooleanField(default=False)
    cita = models.DateTimeField(blank=True, null=True)
    piensa_solicitar_refugio = models.BooleanField(default=False)
    industria_work = models.BooleanField(default=False)
    licencia = models.BooleanField(default=False)
    curp = models.CharField(max_length=50, blank=True, null=True)
    date_permit = models.DateField(blank=True, null=True)
    ubication = models.CharField(max_length=100, blank=True, null=True)
    work_experience = models.TextField(blank=True, null=True)
    saludo = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='person_files/', blank=True, null=True)
    per_trabajo = models.TextField(blank=True, null=True)
    preferred_language = models.CharField(max_length=5, default='es_MX')  # Puede ser 'es_MX', 'en_US', 'fr_FR', etc.
    skills = models.TextField(blank=True, null=True)  # Habilidades del usuario, separadas por comas
    experience_years = models.IntegerField(blank=True, null=True)  # Años de experiencia
    desired_job_types = models.CharField(max_length=100, blank=True, null=True) 
    
    def __str__(self):
        return f"{self.name} {self.lastname}"

# Configuración SMTP
class SmtpConfig(models.Model):
    host = models.CharField(max_length=255)
    port = models.IntegerField()
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.host}:{self.port}"

# Botones para preguntas
class Buttons(models.Model):
    name = models.TextField(max_length=800)
    active = models.BooleanField()
    pregunta = models.ManyToManyField(Pregunta, blank=True)
    sub_pregunta = models.ManyToManyField(SubPregunta, blank=True)

    def __str__(self):
        return str(self.name)

# Modelo para flujos de preguntas
class FlowModel(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    flow_data_json = models.TextField(blank=True, null=True)  # Aquí se almacena el flujo en formato JSON

    def __str__(self):
        return self.name
