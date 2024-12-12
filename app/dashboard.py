# Ubicación del archivo: /home/amigro/app/dashboard.py
from admin_tools.dashboard import modules, Dashboard

class CustomIndexDashboard(Dashboard):
    title = 'Panel de Control de Grupo huntRED®'

    def init_with_context(self, context):
        self.children.append(modules.ModelList(
            title='Administración',
            models=('app.models.Person', 'app.models.ChatState', 'app.models.Person', 'app.models.Application', 'app.models.Vacante'),
        ))
        
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