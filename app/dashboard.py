# Ubicación del archivo: /home/pablo/app/dashboard.py
from admin_tools.dashboard import modules, Dashboard
from django.utils.timezone import now
from django.db.models import Count, Q
from app.models import (
    Application, Vacante, Person, BusinessUnit,
    EnhancedNetworkGamificationProfile, ChatState
)
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

class CustomIndexDashboard(Dashboard):
    title = 'Panel de Control de Grupo huntRED®'

    def init_with_context(self, context):
        # Estadísticas en tiempo real
        stats = self._get_dashboard_stats()
        
        # Widget de estadísticas
        self.children.append(modules.DashboardModule(
            title='Estadísticas en Tiempo Real',
            template='dashboard/stats.html',
            pre_content='''
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total de Candidatos</h3>
                    <p class="stat-value">{total_candidates}</p>
                </div>
                <div class="stat-card">
                    <h3>Vacantes Activas</h3>
                    <p class="stat-value">{active_jobs}</p>
                </div>
                <div class="stat-card">
                    <h3>Aplicaciones Nuevas</h3>
                    <p class="stat-value">{new_applications}</p>
                </div>
                <div class="stat-card">
                    <h3>Contrataciones Último Mes</h3>
                    <p class="stat-value">{hires_last_month}</p>
                </div>
            </div>
            '''.format(**stats)
        ))

        # Widget de KPIs
        self.children.append(modules.DashboardModule(
            title='KPIs del Sistema',
            template='dashboard/kpis.html',
            pre_content='''
            <div class="kpis-grid">
                <div class="kpi-card">
                    <h3>Tasa de Conversión</h3>
                    <p class="kpi-value">{conversion_rate}%</p>
                </div>
                <div class="kpi-card">
                    <h3>Tiempo Promedio de Contratación</h3>
                    <p class="kpi-value">{avg_days} días</p>
                </div>
                <div class="kpi-card">
                    <h3>Engagement de Candidatos</h3>
                    <p class="kpi-value">{engagement_rate}%</p>
                </div>
            </div>
            '''.format(**stats)
        ))

        # Widget de gráficos
        self.children.append(modules.DashboardModule(
            title='Gráficos de Tendencias',
            template='dashboard/charts.html',
            pre_content='''
            <div class="charts-grid">
                <div id="applications-chart"></div>
                <div id="conversion-chart"></div>
            </div>
            ''',
            extra_js='''
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <script>
                // Código para generar gráficos
                // ...
            </script>
            '''
        ))

        # Widget de alertas
        self.children.append(modules.DashboardModule(
            title='Alertas y Notificaciones',
            template='dashboard/alerts.html',
            pre_content='''
            <div class="alerts-grid">
                {% for alert in alerts %}
                <div class="alert-card {{ alert.type }}">
                    <h4>{{ alert.title }}</h4>
                    <p>{{ alert.message }}</p>
                    <span class="timestamp">{{ alert.timestamp }}</span>
                </div>
                {% endfor %}
            </div>
            '''
        ))

        # Widget de tareas pendientes
        self.children.append(modules.DashboardModule(
            title='Tareas Pendientes',
            template='dashboard/tasks.html',
            pre_content='''
            <div class="tasks-grid">
                {% for task in tasks %}
                <div class="task-card">
                    <h4>{{ task.title }}</h4>
                    <p>{{ task.description }}</p>
                    <span class="priority">{{ task.priority }}</span>
                    <span class="deadline">{{ task.deadline }}</span>
                </div>
                {% endfor %}
            </div>
            '''
        ))

        # Widget de integraciones
        self.children.append(modules.DashboardModule(
            title='Estado de Integraciones',
            template='dashboard/integrations.html',
            pre_content='''
            <div class="integrations-grid">
                {% for integration in integrations %}
                <div class="integration-card {{ integration.status }}">
                    <h4>{{ integration.name }}</h4>
                    <p>{{ integration.status }}</p>
                    <span class="last-update">{{ integration.last_update }}</span>
                </div>
                {% endfor %}
            </div>
            '''
        ))

    def _get_dashboard_stats(self):
        """Obtiene estadísticas para el dashboard."""
        now = timezone.now()
        one_month_ago = now - timedelta(days=30)

        total_candidates = Person.objects.count()
        active_jobs = Vacante.objects.filter(
            Q(status='active') | Q(status='in_progress')
        ).count()
        new_applications = Application.objects.filter(
            created_at__gte=one_month_ago
        ).count()
        hires_last_month = Application.objects.filter(
            status='hired',
            created_at__gte=one_month_ago
        ).count()

        # Cálculo de KPIs
        total_applications = Application.objects.count()
        total_hires = Application.objects.filter(status='hired').count()
        conversion_rate = (total_hires / total_applications * 100) if total_applications else 0

        avg_days = Application.objects.filter(
            status='hired'
        ).annotate(
            days=ExtractDay(F('created_at') - F('updated_at'))
        ).aggregate(avg=Avg('days'))['avg'] or 0

        engagement_rate = (new_applications / total_candidates * 100) if total_candidates else 0

        return {
            'total_candidates': total_candidates,
            'active_jobs': active_jobs,
            'new_applications': new_applications,
            'hires_last_month': hires_last_month,
            'conversion_rate': round(conversion_rate, 2),
            'avg_days': round(avg_days, 1),
            'engagement_rate': round(engagement_rate, 2)
        }

        self.children.append(modules.RecentActions(title='Acciones Recientes', limit=10))