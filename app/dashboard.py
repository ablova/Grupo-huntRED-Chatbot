# Ubicación del archivo: /home/pablollh/app/dashboard.py
from admin_tools.dashboard import modules, Dashboard
from django.utils.timezone import now
from app.models import Application, Vacante

class CustomIndexDashboard(Dashboard):
    title = 'Panel de Control de Grupo huntRED®'

    def init_with_context(self, context):
        self.children.append(modules.ModelList(
            title='Administración',
            models=('app.models.Person', 'app.models.ChatState', 'app.models.Application', 'app.models.Vacante'),
        ))
        
        # Módulo de estadísticas
        self.children.append(modules.LinkList(
            title='Estadísticas',
            children=[
                {
                    'title': 'Vacantes Activas',
                    'url': '/admin/vacantes/activas',
                    'description': 'Monitorea todas las vacantes activas.',
                },
                {
                    'title': 'Postulaciones Recientes',
                    'url': '/admin/applications/recent',
                    'description': 'Consulta las postulaciones más recientes.',
                },
            ]
        ))

        self.children.append(modules.RecentActions(title='Acciones Recientes', limit=10))
        self.children.append(modules.ModelList(
            title='Unidades de Negocio y Configuración',
            models=('app.models.BusinessUnit', 'app.models.WhatsappAPI', 'app.models.TelegramAPI', 'app.models.MessengerAPI', 'app.models.InstagramAPI', 'app.models.MetaAPI', 'app.models.ConfiguracionBU'),
        ))

        self.children.append(modules.ModelList(
            title='Scraping y Vacantes',
            models=('app.models.DominioScraping', 'app.models.Vacante', 'app.models.RegistroScraping'),
        ))

        self.children.append(modules.ModelList(
            title='Otras Configuraciones',
            models=('app.models.GptApi', 'app.models.SmtpConfig', 'app.models.ApiConfig', 'app.models.Template'),
        ))

        self.children.append(modules.RecentActions(title='Acciones Recientes', limit=10))