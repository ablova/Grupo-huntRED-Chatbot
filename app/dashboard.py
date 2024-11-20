# /home/amigro/app/dashboard.py

from admin_tools.dashboard import modules, Dashboard
from django.utils.translation import ugettext_lazy as _
from app.models import BusinessUnit, ChatState

class CustomIndexDashboard(Dashboard):
    title = 'Panel de Control de Grupo huntRED'

    def init_with_context(self, context):
        self.children.append(modules.ModelList(
            title='Administración de Chatbots',
            models=('app.models.Person', 'app.models.ChatState', 'app.models.Pregunta'),
        ))

        self.children.append(modules.Group(
            title='Unidades de Negocio',
            display='tabs',
            children=[
                modules.ModelList(
                    title='Unidades de Negocio',
                    models=('app.models.BusinessUnit', 'app.models.FlowModel'),
                ),
                modules.ModelList(
                    title='APIs',
                    models=('app.models.WhatsAppAPI', 'app.models.TelegramAPI', 'app.models.MetaAPI'),
                ),
            ]
        ))

        # Agregar un módulo de estadísticas
        self.children.append(modules.LinkList(
            title='Estadísticas',
            children=[
                {
                    'title': 'Interacciones por Unidad de Negocio',
                    'url': '/admin/estadisticas/interacciones/',
                    'external': False,
                },
                # Puedes agregar más enlaces o módulos de gráficos aquí
            ]
        ))

        self.children.append(modules.RecentActions(
            title='Acciones Recientes',
            limit=10,
        ))