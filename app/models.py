# /home/amigro/app/models.py

from django.db import models
from datetime import datetime

#para evitar variables de entorno, no las quiero en lo más minimo, evitar tambien creación de archivos si no son explicitamente necesarios
class Configuracion(models.Model):
    secret_key = models.CharField(max_length=255)
    sentry_dsn = models.CharField(max_length=255, blank=True, null=True)
    debug_mode = models.BooleanField(default=True)
    # Otras configuraciones importantes

# Estado del Chat
class ChatState(models.Model):
    user_id = models.CharField(max_length=50)
    platform = models.CharField(max_length=20)  # 'telegram', 'whatsapp', 'messenger'
    current_question = models.ForeignKey('Pregunta', on_delete=models.CASCADE, null=True, blank=True)
    last_interaction = models.DateTimeField(auto_now=True)
    context = models.JSONField(blank=True, null=True, default=dict)

    def __str__(self):
        return f"ChatState {self.user_id} - {self.platform}"

class Condicion(models.Model):
    nombre = models.CharField(max_length=100)
    valor_esperado = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Condicion: {self.nombre} (espera: {self.valor_esperado})"

class Etapa(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Pregunta(models.Model):
    INPUT_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('name', 'Nombre'),
        ('apellido_paterno', 'Apellido Paterno'),
        ('apellido_materno', 'Apellido Materno'),
        ('nationality', 'Nacionalidad'),
        ('fecha_nacimiento', 'Fecha de Nacimiento'),
        ('sexo', 'Sexo'),
        ('email', 'Email'),
        ('phone', 'Celular'),
        ('family_traveling', 'Viaja con Familia'),
        ('policie', 'Politica Migratoria'),
        ('group_aditionality', 'Viaja en Grupo'),
        ('passport', 'Pasaporte'),
        ('additional_official_documentation', 'Documentación Adicional'),
        ('int_work', 'Intención de Trabajo'),
        ('menor', 'Menores'),
        ('refugio', 'Refugio'),
        ('perm_humanitario', 'Permiso Humanitario'),
        ('solicita_refugio', 'Solicitud de Refugio'),
        ('cita', 'Fecha de Cita'),
        ('piensa_solicitar_refugio', 'Contempla Solicitud de Refugio'),
        ('industria_work', 'Industria de Trabajo'),
        ('licencia', 'Licencia para Trabajar'),
        ('curp', 'CURP'),
        ('date_permit', 'Fecha del Permiso'),
        ('ubication', 'Ubicación'),
        ('work_experience', 'Experiencia Laboral'),
        ('saludo', 'Saludo'),
        ('file', 'Archivo / CV'),
        ('per_trabajo', 'Permiso de Trabajo'),
        ('preferred_language', 'Idioma Preferido'),
        ('skills', 'Habilidades'),
        ('experience_years', 'Años de Experiencia'),
        ('desired_job_types', 'Tipo de Trabajo Deseado'),
        ('nivel_salarial', 'Nivel Salarial Deseado'),
    ]

    ACTION_TYPE_CHOICES = [
        ('none', 'Ninguna acción'),
        ('mostrar_vacantes', 'Mostrar Vacantes'),
        ('enviar_whatsapp_plantilla', 'Enviar Plantilla WhatsApp'),
        ('enviar_imagen', 'Enviar Imagen'),
        ('enviar_url', 'Enviar URL'),
        ('recap', 'Hacer Recapitulación'),
        # Otras acciones personalizadas que necesites
    ]

    name = models.TextField(max_length=800)
    etapa = models.ForeignKey('Etapa', on_delete=models.CASCADE, default=1)
    option = models.CharField(max_length=50)
    valid = models.BooleanField(null=True, blank=True)
    active = models.BooleanField(default=True)
    content = models.TextField(blank=True, null=True)
    sub_pregunta = models.ManyToManyField('SubPregunta', blank=True, related_name='pregunta_principal')
    decision = models.JSONField(blank=True, null=True, default=dict)  # {respuesta: id_pregunta_siguiente}
    condiciones = models.ManyToManyField(Condicion, blank=True)
    input_type = models.CharField(max_length=100, choices=INPUT_TYPE_CHOICES, blank=True, null=True)
    requires_response = models.BooleanField(default=True)
    field_person = models.CharField(max_length=50, blank=True, null=True)  # Relaciona la pregunta con el campo de Person
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES, default='none')  # Acciones personalizadas

    def __str__(self):
        return str(self.name)


class SubPregunta(models.Model):
    INPUT_TYPE_CHOICES = Pregunta.INPUT_TYPE_CHOICES
    ACTION_TYPE_CHOICES = Pregunta.ACTION_TYPE_CHOICES  # Mismas opciones que Pregunta

    name = models.CharField(max_length=800)
    option = models.CharField(max_length=50)
    valid = models.BooleanField(null=True, blank=True)
    active = models.BooleanField(default=True)
    content = models.TextField(blank=True, null=True)
    parent_sub_pregunta = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    decision = models.JSONField(blank=True, null=True, default=dict)
    input_type = models.CharField(max_length=100, choices=INPUT_TYPE_CHOICES, blank=True, null=True)
    requires_response = models.BooleanField(default=True)
    field_person = models.CharField(max_length=50, blank=True, null=True)  # Relaciona la subpregunta con el campo de Person
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES, default='none')  # Acciones personalizadas

    def __str__(self):
        return str(self.name)

class TelegramAPI(models.Model):
    api_key = models.CharField(max_length=255)
    bot_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.bot_name or "Telegram Bot"

class MetaAPI(models.Model):
    app_id = models.CharField(max_length=255, default='662158495636216')
    app_secret = models.CharField(max_length=255, default='7732534605ab6a7b96c8e8e81ce02e6b')
    verify_token = models.CharField(max_length=255, default='amigro_secret_token')

    def __str__(self):
        return f"MetaAPI {self.app_id}"

class WhatsAppAPI(models.Model):
    phoneID = models.CharField(max_length=100)
    api_token = models.CharField(max_length=500)
    WABID = models.CharField(max_length=100, default='104851739211207')
    v_api = models.CharField(max_length=100)

    def __str__(self):
        return f"WhatsApp API {self.phoneID}"

class MessengerAPI(models.Model):
    page_access_token = models.CharField(max_length=255)

    def __str__(self):
        return "Messenger Configuration"

class InstagramAPI(models.Model):
    app_id = models.CharField(max_length=255, default='1615393869401916')
    access_token = models.CharField(max_length=255, default='5d8740cb80ae42d8b5cafb47e6c461d5')
    instagram_account_id = models.CharField(max_length=255, default='17841457231476550')

    def __str__(self):
        return f"InstagramAPI {self.app_id}"

class GptApi(models.Model):
    api_token = models.CharField(max_length=500)
    organization = models.CharField(max_length=100, blank=True, null=True)
    project = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100)
    form_pregunta = models.CharField(max_length=500)
    work_pregunta = models.CharField(max_length=500)

    def __str__(self):
        return f"Model: {self.model} | Organization: {self.organization} | Project: {self.project}"

class Chat(models.Model):
    body = models.TextField(max_length=1000)
    SmsStatus = models.CharField(max_length=15, null=True, blank=True)
    From = models.CharField(max_length=15)
    To = models.CharField(max_length=15)
    ProfileName = models.CharField(max_length=50)
    ChannelPrefix = models.CharField(max_length=50)
    MessageSid = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True) #Agregando campo de fecha de creación
    updated_at = models.DateTimeField(auto_now_add=True) #Agregando campo de fecha de creación
    message_count = models.IntegerField(default=0)

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
    required_skills = models.TextField(blank=True, null=True)
    experience_required = models.IntegerField(blank=True, null=True)
    job_description = models.TextField(blank=True, null=True)
    interview_slots = models.JSONField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['job_id']),
            models.Index(fields=['company']),
        ]

    def __str__(self) -> str:
        return str(self.name)

class Person(models.Model):
    number_interaction = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=200, blank=True, null=True)
    apellido_materno = models.CharField(max_length=200, blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
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
    preferred_language = models.CharField(max_length=5, default='es_MX')
    skills = models.TextField(blank=True, null=True)
    experience_years = models.IntegerField(blank=True, null=True)
    desired_job_types = models.CharField(max_length=100, blank=True, null=True)
    nivel_salarial = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} {self.lastname}"

class Invitacion(models.Model):
    referrer = models.ForeignKey(Person, related_name='invitaciones_enviadas', on_delete=models.CASCADE)
    invitado = models.ForeignKey(Person, related_name='invitaciones_recibidas', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class SmtpConfig(models.Model):
    host = models.CharField(max_length=255)
    port = models.IntegerField()
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.host}:{self.port}"

class Buttons(models.Model):
    name = models.CharField(max_length=800)
    active = models.BooleanField()
    pregunta = models.ManyToManyField(Pregunta, blank=True)
    sub_pregunta = models.ManyToManyField(SubPregunta, blank=True)

    def __str__(self):
        return str(self.name)

class FlowModel(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    preguntas = models.ManyToManyField(Pregunta, related_name='flowmodels')
    flow_data_json = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    

#________________________________________________________________________________________________
#Esto es para la aplicación de Milkyleak, independiente del chatbot de amigro, solo se utiliza el servidor.
class MilkyLeak(models.Model):
    # Configuraciones de la API de Twitter
    twitter_api_key = models.CharField(max_length=255)
    twitter_api_secret_key = models.CharField(max_length=255)
    twitter_access_token = models.CharField(max_length=255)
    twitter_access_token_secret = models.CharField(max_length=255)

    # Configuraciones de Mega.nz
    mega_email = models.EmailField()
    mega_password = models.CharField(max_length=255)

    # Configuraciones adicionales
    folder_location = models.CharField(max_length=255, help_text="Nombre del folder en Mega.nz")
    image_prefix = models.CharField(max_length=50, default='ML_')
    local_directory = models.CharField(max_length=255, default='/tmp/', help_text="Directorio local temporal para imágenes")

    # Contador de imágenes
    image_counter = models.PositiveIntegerField(default=1)
    # Rango de tiempo aleatorio para publicaciones (en minutos)
    min_interval = models.PositiveIntegerField(default=10, help_text="Tiempo mínimo de espera entre publicaciones (minutos)")
    max_interval = models.PositiveIntegerField(default=20, help_text="Tiempo máximo de espera entre publicaciones (minutos)")


    def __str__(self):
        return f"MilkyLeak Config ({self.twitter_api_key})"

    