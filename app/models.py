# /home/amigro/app/models.py

from django.db import models
from datetime import datetime
import graphviz  

#para evitar variables de entorno, no las quiero en lo más minimo, evitar tambien creación de archivos si no son explicitamente necesarios
class Configuracion(models.Model):
    secret_key = models.CharField(max_length=255, default='hfmrpTNRwmQ1F7gZI1DNKaQ9gNw3cgayKFB0HK_gt9BKJEnLy60v1v0PnkZtX3OkY48')
    sentry_dsn = models.CharField(max_length=255, blank=True, null=True, default='https://94c6575f877d16a00cc74bcaaab5ae79@o4508258791653376.ingest.us.sentry.io/4508258794471424')
    debug_mode = models.BooleanField(default=True)
    test_user = models.CharField(max_length=255, blank=True, null=True, default='Pablo Lelo de Larrea H.')
    test_phone_number = models.CharField(max_length=15, default='+525518490291', help_text='Número de teléfono para pruebas y reportes de ejecución')
    test_email = models.EmailField(max_length=50, default='pablo@huntred.com', help_text='Email para pruebas y reportes de ejecución')
    default_platform = models.CharField(max_length=20, default='whatsapp', help_text='Plataforma de pruebas por defecto (whatsapp, telegram, messenger)')
    notification_hour = models.TimeField(blank=True, null=True, help_text='Hora para enviar notificaciones diarias de pruebas')
    is_test_mode = models.BooleanField(default=True, help_text='Indicador de si el sistema está en modo de pruebas')
    default_flow_model = models.ForeignKey('FlowModel', on_delete=models.SET_NULL, blank=True, null=True, help_text='FlowModel de pruebas por defecto')

    # Otras configuraciones importantes

class BusinessUnit(models.Model):
    BUSINESS_UNIT_CHOICES = [
        ('huntRED', 'huntRED®'),
        ('huntRED_executive', 'huntRED® Executive'),
        ('huntu', 'huntU®'),
        ('amigro', 'Amigro®'),
        # Añadir más opciones si es necesario en el futuro
    ]

    name = models.CharField(max_length=50, choices=BUSINESS_UNIT_CHOICES, unique=True)
    description = models.TextField(blank=True)
    whatsapp_enabled = models.BooleanField(default=True)
    telegram_enabled = models.BooleanField(default=True)
    messenger_enabled = models.BooleanField(default=True)
    instagram_enabled = models.BooleanField(default=True)
    scrapping_enabled = models.BooleanField(default=True)
    scraping_domains = models.JSONField(default=list, help_text="Lista de dominios para el scraping")


    def __str__(self):
        # Mostrar el nombre completo de la unidad en lugar del código
        return dict(self.BUSINESS_UNIT_CHOICES).get(self.name, self.name)

class ConfiguracionBU(models.Model):
    business_unit = models.OneToOneField(BusinessUnit, on_delete=models.CASCADE)
    logo_url = models.URLField(default="https://amigro.org/logo.png")
    direccion_bu = models.CharField(max_length=255, default="Av. Santa Fe #428, Torre 3, Piso 15, CDMX")
    telefono_bu = models.CharField(max_length=20, default="+5255 59140089")
    correo_bu = models.CharField(max_length=20, default="hola@amigro.org")
    jwt_token = models.CharField(max_length=255, blank=True, null=True, default="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsIm5hbWUiOiJQYWJsbyIsImlhdCI6MTczMTAwNzY0OCwiZXhwIjoxODg4Njg3NjQ4fQ.BQezJzmVVpcaG2ZIbkMagezkt-ORoO5wyrG0odWZrlg")
    dominio_bu = models.URLField(max_length=255, blank=True, null=True)
    dominio_rest_api = models.URLField(max_length=255, blank=True, null=True)
    scraping_domains = models.JSONField(default=list)

        # Configuración SMTP específica por Business Unit
    smtp_host = models.CharField(max_length=255, blank=True, null=True)
    smtp_port = models.IntegerField(blank=True, null=True, default=587)
    smtp_username = models.CharField(max_length=255, blank=True, null=True)
    smtp_password = models.CharField(max_length=255, blank=True, null=True)
    smtp_use_tls = models.BooleanField(default=True)
    smtp_use_ssl = models.BooleanField(default=False)

    def __str__(self):
        return f"Configuración de {self.business_unit.name if self.business_unit else 'Unidad de Negocio'}"

class ApiConfig(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, related_name='api_configs', on_delete=models.CASCADE)
    api_type = models.CharField(max_length=50)  # e.g., 'WhatsApp', 'Telegram', etc.
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255, blank=True, null=True)
    additional_settings = models.JSONField(blank=True, null=True)  # Para configuraciones adicionales como tokens, etc.

    def __str__(self):
        return f"{self.business_unit.name} - {self.api_type}"
# Estado del Chat
class ChatState(models.Model):
    user_id = models.CharField(max_length=50, db_index=True)  # Index para optimizar búsqueda por usuario
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

class FlowModel(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    preguntas = models.ManyToManyField('Pregunta', related_name='flowmodels')
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='flows', null=True, blank=True)
    flow_data_json = models.JSONField(blank=True, null=True)  # Añadir este campo

    def generate_flow_diagram(self):
        dot = graphviz.Digraph()
        # Generar nodos y conexiones basadas en las preguntas del flujo
        for pregunta in self.preguntas.all():
            dot.node(str(pregunta.id), pregunta.name)  # Nombre de la pregunta como nodo
            if pregunta.next_si:
                dot.edge(str(pregunta.id), str(pregunta.next_si.id), label='Sí')
            if pregunta.next_no:
                dot.edge(str(pregunta.id), str(pregunta.next_no.id), label='No')
        
        # Guarda el diagrama
        dot.render(f'/home/amigro/media/flow_diagram_{self.id}', format='png')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.generate_flow_diagram()  # Genera el diagrama al guardar
    def __str__(self):
        return self.name

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
        ('enviar_logo', 'Enviar Logo de Amigro'),
        ('enviar_imagen', 'Enviar Imagen'),
        ('enviar_url', 'Enviar URL'),
        ('recap', 'Hacer Recapitulación'),
        ('decision_si_no', 'Decisión - Sí/No'),  # Nuevo tipo de acción para decisiones
        ('botones', 'Botones'),  # Nuevo tipo de acción para botones personalizados
        # Otras acciones personalizadas que necesites
    ]

    flow = models.ForeignKey('FlowModel', on_delete=models.CASCADE, default=1)
    etapa = models.ForeignKey('Etapa', on_delete=models.CASCADE, default=1)
    name = models.TextField(max_length=800)
    content = models.TextField(blank=True, null=True)
    option = models.CharField(max_length=50)
    buttons = models.ManyToManyField('Buttons', related_name='preguntas', blank=True)
    valid = models.BooleanField(null=True, blank=True)
    active = models.BooleanField(default=True)
    requires_response = models.BooleanField(default=True)
    multi_select = models.BooleanField(default=False)  # Indica si es selección múltiple
    next_si = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='pregunta_si')  # Pregunta siguiente si es "Sí"
    next_no = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='pregunta_no')  # Pregunta siguiente si es "No"
    input_type = models.CharField(max_length=100, choices=INPUT_TYPE_CHOICES, blank=True, null=True)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES, default='none')  # Acciones personalizadas
    #NO se si se estan utilizando ya en el chatbot, pero las dejo para no romper el app
    field_person = models.CharField(max_length=50, blank=True, null=True)  # Relaciona la pregunta con el campo de Person
    condiciones = models.ManyToManyField(Condicion, blank=True)
    decision = models.JSONField(blank=True, null=True, default=dict)  # {respuesta: id_pregunta_siguiente}

    def __str__(self):
        return f"{self.id} - {self.flow.name} - {self.name}"
    def save(self, *args, **kwargs):
        # Puedes agregar lógica para establecer valores por defecto o validaciones aquí.
        if not self.name:
            self.name = "Nombre por defecto"  # Asignar un valor por defecto si no se proporciona.
        super().save(*args, **kwargs)


class MetaAPI(models.Model):
    business_unit = models.OneToOneField(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='meta_api_config',  # Cambiar el related_name
    )
    app_id = models.CharField(max_length=255, default='662158495636216')
    app_secret = models.CharField(max_length=255, default='7732534605ab6a7b96c8e8e81ce02e6b')
    verify_token = models.CharField(max_length=255, default='amigro_secret_token')

    def __str__(self):
        return f"MetaAPI {self.business_unit.name} ({self.app_id})"

class WhatsAppAPI(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='whatsapp_apis', null=True, blank=True)
    name = models.CharField(max_length=50)
    phoneID = models.CharField(max_length=20)
    api_token = models.CharField(max_length=500)
    WABID = models.CharField(max_length=20, default='104851739211207')
    v_api = models.CharField(max_length=10)
    meta_api = models.ForeignKey('MetaAPI', on_delete=models.CASCADE)
    associated_flow = models.ForeignKey('FlowModel', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)  # Campo para activar o desactivar el canal

    def __str__(self):
        return f"{self.business_unit.name} - WhatsApp API {self.phoneID} - {self.associated_flow}"

class MessengerAPI(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='messenger_apis', null=True, blank=True)
    page_access_token = models.CharField(max_length=255)
    meta_api = models.ForeignKey('MetaAPI', on_delete=models.CASCADE)
    associated_flow = models.ForeignKey('FlowModel', on_delete=models.CASCADE, related_name='messenger_flows', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.business_unit.name} - Messenger API - {self.associated_flow.name}"

class InstagramAPI(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='instagram_apis', null=True, blank=True)
    app_id = models.CharField(max_length=255, default='1615393869401916')
    access_token = models.CharField(max_length=255, default='5d8740cb80ae42d8b5cafb47e6c461d5')
    instagram_account_id = models.CharField(max_length=255, default='17841457231476550')
    meta_api = models.ForeignKey('MetaAPI', on_delete=models.CASCADE)
    associated_flow = models.ForeignKey('FlowModel', on_delete=models.CASCADE, related_name='instagram_flows', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.business_unit.name} - Instagram API - {self.associated_flow.name}"
    
class TelegramAPI(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='telegram_apis', null=True, blank=True)
    api_key = models.CharField(max_length=255)
    bot_name = models.CharField(max_length=255, blank=True, null=True)
    associated_flow = models.ForeignKey('FlowModel', on_delete=models.CASCADE, related_name='telegram_flows', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.business_unit.name} - Telegram Bot - {self.associated_flow.name}"

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
    name = models.CharField(max_length=100) #nombre del responsable
    whatsapp = models.CharField(max_length=20, blank=True, null=True)  # Campo para almacenar WhatsApp del empleador
    company = models.CharField(max_length=100, blank=True, null=True) #nombre de la empresa
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
    
    interview_slots = models.JSONField(blank=True, null=True)

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
    person = models.ForeignKey('app.Person', on_delete=models.CASCADE)  # Referencia al modelo Person mediante una cadena
    job = models.ForeignKey(Worker, on_delete=models.CASCADE)
    interview_date = models.DateTimeField()  # Fecha de la entrevista
    application_date = models.DateTimeField(auto_now_add=True)  # Fecha de aplicación
    slot = models.CharField(max_length=50)  # Slot de entrevista reservado
    candidate_latitude = models.CharField(max_length=100, blank=True, null=True)
    candidate_longitude = models.CharField(max_length=100, blank=True, null=True)
    location_verified = models.BooleanField(default=False)
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPE_CHOICES, default='presencial')
    candidate_confirmed = models.BooleanField(default=False)  # Nuevo campo para confirmar asistencia

    def days_until_interview(self):
        return (self.interview_date - timezone.now()).days

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
    permiso_trabajo = models.BooleanField(default=False)
    curp = models.CharField(max_length=50, blank=True, null=True)
    date_permit = models.DateField(blank=True, null=True)
    ubicacion = models.CharField(max_length=100, blank=True, null=True)
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
        return f"{self.name} {self.apellido_paterno} {self.apellido_materno}"
    def is_profile_complete(self):
        """
        Verifica si todos los campos necesarios están completos en el perfil del usuario.
        """
        required_fields = ['name', 'apellido_paterno', 'email', 'phone', 'skills']
        missing_fields = [field for field in required_fields if not getattr(self, field)]
        return not missing_fields  # Retorna True si está completo, False si falta algo

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
    name = models.CharField(max_length=20)
    active = models.BooleanField()
    pregunta = models.ManyToManyField(Pregunta, related_name='botones_pregunta', blank=True)
    subpregunta = models.ManyToManyField(SubPregunta, related_name='botones_subpregunta', blank=True)

    def __str__(self):
        return str(self.name)


#________________________________________________________________________________________________
#Esto es para la aplicación de Milkyleak, independiente del chatbot de amigro, solo se utiliza el servidor.
class MilkyLeak(models.Model):
    # Configuraciones de la API de Twitter
    twitter_api_key = models.CharField(max_length=255) #YVIxTWtkZ0NheGRiamNlem5UbkQ6MTpjaQ Client ID   / 2fIV8CDPV13tZ18VpCzzK7Yu2 Api Key
    twitter_api_secret_key = models.CharField(max_length=255) #cSuwv9VXrxZI4yr1oaVrkCj6p6feuu4dy1QoaID1lQe7lbjXdb   / 85KIRnuNGdWhJOiglSg8ramGBT4OzCqMts17uxkUIBm1tR8avu API secret
    twitter_access_token = models.CharField(max_length=255) # 235862444-UWHrUObIvUoNcMVSL0S5kPx0geKu88M9nawe43YM
    twitter_access_token_secret = models.CharField(max_length=255) # tUCYmHzpWI0YwCQ8AedFfEMHaa9pNHAt2r0AKQUdIWT78

    # Configuraciones de Mega.nz
    mega_email = models.EmailField() #milkyleak@gmail.com
    mega_password = models.CharField(max_length=255) #PLLH_huntred2009!

    # Configuraciones adicionales
    folder_location = models.CharField(max_length=255, help_text="Nombre del folder en Mega.nz")
    image_prefix = models.CharField(max_length=50, help_text='ML_')
    local_directory = models.CharField(max_length=255, default='/home/amigro/media', help_text="Directorio local temporal para imágenes")

    # Contador de imágenes
    image_counter = models.PositiveIntegerField(default=1)
    # Rango de tiempo aleatorio para publicaciones (en minutos)
    min_interval = models.PositiveIntegerField(default=10, help_text="Tiempo mínimo de espera entre publicaciones (minutos)")
    max_interval = models.PositiveIntegerField(default=20, help_text="Tiempo máximo de espera entre publicaciones (minutos)")

    #Configuración de Dropbos  (App Key brg4mvkdjisvo67  /  App Secret  szbinvambk7anvv)
    dropbox_access_token = models.CharField(max_length=255, blank=True, null=True)  # Token para Dropbox sl.B-gJAWUpS-lHTLRkq64AC_rz2xSwijP_fITCv9iZtmfSfywYyZYU6qUliXFi1EEy1KmPU7XLZzPcFzFR4_HBuMg9PpK6hgF96tmMeaPabPNmcfXjfIOL7jLG7EmOf-SkePCKBC5m63mf
    dropbox_refresh_token = models.CharField(max_length=255, blank=True, null=True)  # Añadir refresh token
    dropbox_token_expires_at = models.DateTimeField(blank=True, null=True)
    storage_service = models.CharField(
        max_length=10, 
        choices=[('mega', 'Mega.nz'), ('dropbox', 'Dropbox')],
        default='dropbox'
    )  # Selector entre Mega y Dropbox

    def __str__(self):
        return f"MilkyLeak Config ({self.twitter_api_key})"
    def increment_image_counter(self):
        """
        Incrementa el contador de imágenes y guarda el modelo.
        """
        self.image_counter += 1
        self.save()