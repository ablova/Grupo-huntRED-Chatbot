"""
Vistas para el dashboard de pagos y analíticas financieras.
Este módulo implementa las vistas relacionadas con visualizaciones y métricas de pagos.
"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Avg, Q, F, ExpressionWrapper, fields
from django.db.models.functions import TruncMonth, TruncWeek, ExtractMonth
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from app.models import Pago, Empleador, BusinessUnit
from app.ats.utils.rbac import RBAC

logger = logging.getLogger(__name__)

class PaymentDashboardView(LoginRequiredMixin, TemplateView):
    """
    Vista principal del dashboard de pagos.
    Muestra resumen de pagos, tendencias y métricas clave.
    """
    template_name = 'pagos/dashboard.html'
    
    def get_context_data(self, **kwargs):
        """
        Obtiene y calcula las métricas para el dashboard.
        Implementa caché para mejorar rendimiento.
        """
        context = super().get_context_data(**kwargs)
        
        # Obtener parámetros de filtrado
        bu_id = self.request.GET.get('bu_id')
        date_from = self.request.GET.get('from')
        date_to = self.request.GET.get('to')
        period = self.request.GET.get('period', 'month')  # Periodos: week, month, quarter, year
        
        # Construir key para caché basada en parámetros
        cache_key = f"payment_dashboard:{bu_id}:{date_from}:{date_to}:{period}:{self.request.user.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            context.update(cached_data)
            context['from_cache'] = True
            return context
        
        # Preparar queryset base con los filtros
        base_queryset = self.get_filtered_queryset(bu_id, date_from, date_to)
        
        # Obtener BUs disponibles para el usuario
        context['business_units'] = self.get_user_business_units()
        
        # Métricas generales
        payment_metrics = self.calculate_payment_metrics(base_queryset)
        context.update(payment_metrics)
        
        # Datos de gráficos según el periodo
        chart_data = self.generate_chart_data(base_queryset, period)
        context.update(chart_data)
        
        # Lista de pagos recientes
        context['recent_payments'] = base_queryset.order_by('-fecha_creacion')[:10]
        
        # Pagos por estado
        context['payments_by_status'] = self.get_payments_by_status(base_queryset)
        
        # Guardar en caché por 15 minutos
        cache.set(cache_key, {k: v for k, v in context.items() 
                             if k not in ['view', 'recent_payments']}, 900)
        
        return context
    
    def get_filtered_queryset(self, bu_id=None, date_from=None, date_to=None):
        """
        Aplica filtros al queryset de pagos según los parámetros.
        
        Args:
            bu_id: ID de la business unit a filtrar
            date_from: Fecha inicial (formato YYYY-MM-DD)
            date_to: Fecha final (formato YYYY-MM-DD)
            
        Returns:
            QuerySet: Pagos filtrados
        """
        queryset = Pago.objects.all()
        
        # Optimizar consultas con select_related
        queryset = queryset.select_related('empleador', 'bu')
        
        # Filtrar por BU
        if bu_id:
            queryset = queryset.filter(bu_id=bu_id)
        elif not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            # Si no es superadmin, limitar a sus BUs asignadas
            user_bus = self.request.user.profile.business_units.values_list('id', flat=True)
            queryset = queryset.filter(bu_id__in=user_bus)
        
        # Filtrar por fechas
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_creacion__gte=date_from)
            except ValueError:
                logger.warning(f"Invalid date_from format: {date_from}")
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_creacion__lte=date_to)
            except ValueError:
                logger.warning(f"Invalid date_to format: {date_to}")
        
        return queryset
    
    def get_user_business_units(self):
        """
        Obtiene la lista de BUs a las que tiene acceso el usuario.
        
        Returns:
            QuerySet: Business Units disponibles
        """
        if self.request.user.is_superuser:
            return BusinessUnit.objects.all()
        
        if hasattr(self.request.user, 'profile'):
            return self.request.user.profile.business_units.all()
            
        return BusinessUnit.objects.none()
    
    def calculate_payment_metrics(self, queryset):
        """
        Calcula métricas generales de pagos.
        
        Args:
            queryset: QuerySet de pagos filtrado
            
        Returns:
            dict: Métricas calculadas
        """
        # Total de pagos y montos
        total_payments = queryset.count()
        total_amount = queryset.aggregate(total=Sum('monto'))['total'] or Decimal('0')
        
        # Pagos pendientes y vencidos
        pending_payments = queryset.filter(estado='pendiente').count()
        overdue_payments = queryset.filter(
            estado='pendiente',
            fecha_vencimiento__lt=timezone.now().date()
        ).count()
        
        # Promedio de días para pago
        payment_days = queryset.filter(
            fecha_pago__isnull=False
        ).annotate(
            days_to_pay=ExpressionWrapper(
                F('fecha_pago') - F('fecha_creacion'),
                output_field=fields.DurationField()
            )
        ).aggregate(
            avg_days=Avg('days_to_pay')
        )
        
        avg_payment_days = 0
        if payment_days['avg_days']:
            avg_payment_days = payment_days['avg_days'].days
        
        # Tendencias (comparación con periodo anterior)
        # Calcular período actual
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)  # Último mes por defecto
        
        # Período anterior de igual duración
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=30)
        
        # Pagos en período actual
        current_payments = queryset.filter(
            fecha_creacion__gte=start_date,
            fecha_creacion__lte=end_date
        ).count()
        
        # Pagos en período anterior
        previous_payments = queryset.filter(
            fecha_creacion__gte=prev_start_date,
            fecha_creacion__lte=prev_end_date
        ).count()
        
        # Calcular tendencia en porcentaje
        payment_trend = 0
        if previous_payments > 0:
            payment_trend = ((current_payments - previous_payments) / previous_payments) * 100
        
        return {
            'total_payments': total_payments,
            'total_amount': total_amount,
            'pending_payments': pending_payments,
            'overdue_payments': overdue_payments,
            'avg_payment_days': avg_payment_days,
            'current_payments': current_payments,
            'payment_trend': payment_trend
        }
    
    def generate_chart_data(self, queryset, period='month'):
        """
        Genera datos para gráficos según el periodo especificado.
        
        Args:
            queryset: QuerySet de pagos filtrado
            period: Periodo de agrupación (week, month, quarter, year)
            
        Returns:
            dict: Datos para gráficos
        """
        # Determinar función de truncamiento según periodo
        if period == 'week':
            trunc_func = TruncWeek('fecha_creacion')
            date_format = '%d %b'
        elif period == 'month':
            trunc_func = TruncMonth('fecha_creacion')
            date_format = '%b %Y'
        elif period == 'quarter':
            # Para trimestres usamos meses y luego agrupamos
            trunc_func = TruncMonth('fecha_creacion')
            date_format = '%b %Y'
        else:  # year
            # Para años usamos meses y agrupamos después
            trunc_func = TruncMonth('fecha_creacion')
            date_format = '%b %Y'
        
        # Obtener datos agregados por periodo
        payments_by_period = queryset.annotate(
            period=trunc_func
        ).values(
            'period'
        ).annotate(
            count=Count('id'),
            total=Sum('monto')
        ).order_by('period')
        
        # Preparar datos para gráficos
        periods = []
        payment_counts = []
        payment_amounts = []
        
        for item in payments_by_period:
            if item['period']:
                period_str = item['period'].strftime(date_format)
                periods.append(period_str)
                payment_counts.append(item['count'])
                payment_amounts.append(float(item['total'] if item['total'] else 0))
        
        # Datos por método de pago
        payments_by_method = queryset.values('metodo_pago').annotate(
            count=Count('id'),
            total=Sum('monto')
        ).order_by('-total')
        
        payment_methods = []
        method_amounts = []
        
        for item in payments_by_method:
            method = item['metodo_pago'] or 'No especificado'
            payment_methods.append(method)
            method_amounts.append(float(item['total'] if item['total'] else 0))
        
        return {
            'chart_periods': json.dumps(periods),
            'chart_payment_counts': json.dumps(payment_counts),
            'chart_payment_amounts': json.dumps(payment_amounts),
            'chart_payment_methods': json.dumps(payment_methods),
            'chart_method_amounts': json.dumps(method_amounts)
        }
    
    def get_payments_by_status(self, queryset):
        """
        Obtiene distribución de pagos por estado.
        
        Args:
            queryset: QuerySet de pagos filtrado
            
        Returns:
            dict: Conteo de pagos por estado
        """
        status_counts = queryset.values('estado').annotate(
            count=Count('id'),
            total=Sum('monto')
        ).order_by('estado')
        
        # Convertir a diccionario con estados como keys
        result = {}
        for item in status_counts:
            status = item['estado'] or 'desconocido'
            result[status] = {
                'count': item['count'],
                'total': item['total'] or Decimal('0')
            }
            
        return result


class PaymentAnalyticsView(LoginRequiredMixin, TemplateView):
    """
    Vista de analíticas avanzadas de pagos.
    Incluye predicciones, tendencias y análisis detallado.
    """
    template_name = 'pagos/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener parámetros
        bu_id = self.request.GET.get('bu_id')
        year = self.request.GET.get('year', str(timezone.now().year))
        
        # Construir cache key
        cache_key = f"payment_analytics:{bu_id}:{year}:{self.request.user.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            context.update(cached_data)
            context['from_cache'] = True
            return context
        
        # Filtrar datos
        queryset = self.get_filtered_queryset(bu_id, year)
        
        # Análisis por empleador
        context['employer_analysis'] = self.analyze_by_employer(queryset)
        
        # Análisis por mes
        context['monthly_analysis'] = self.analyze_by_month(queryset, year)
        
        # Análisis de puntualidad
        context['punctuality_analysis'] = self.analyze_payment_punctuality(queryset)
        
        # Proyecciones
        context['projections'] = self.generate_projections(queryset, year)
        
        # BUs disponibles
        context['business_units'] = BusinessUnit.objects.all()
        context['selected_bu'] = bu_id
        context['selected_year'] = year
        context['available_years'] = range(2020, timezone.now().year + 2)
        
        # Guardar en caché
        cache.set(cache_key, {k: v for k, v in context.items() 
                             if k not in ['view', 'business_units', 'available_years']}, 1800)
        
        return context
    
    def get_filtered_queryset(self, bu_id=None, year=None):
        """
        Obtiene queryset filtrado por BU y año.
        
        Args:
            bu_id: ID de la Business Unit
            year: Año a analizar
            
        Returns:
            QuerySet: Pagos filtrados
        """
        queryset = Pago.objects.all().select_related('empleador', 'bu')
        
        # Filtrar por BU
        if bu_id:
            queryset = queryset.filter(bu_id=bu_id)
        elif not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            user_bus = self.request.user.profile.business_units.values_list('id', flat=True)
            queryset = queryset.filter(bu_id__in=user_bus)
            
        # Filtrar por año
        if year and year.isdigit():
            queryset = queryset.filter(fecha_creacion__year=int(year))
            
        return queryset
    
    def analyze_by_employer(self, queryset):
        """
        Analiza pagos agrupados por empleador.
        
        Args:
            queryset: QuerySet de pagos
            
        Returns:
            list: Análisis por empleador
        """
        employer_analysis = queryset.values(
            'empleador__id', 'empleador__nombre'
        ).annotate(
            payment_count=Count('id'),
            total_amount=Sum('monto'),
            avg_amount=Avg('monto'),
            overdue_count=Count('id', filter=Q(
                estado='pendiente',
                fecha_vencimiento__lt=timezone.now().date()
            ))
        ).order_by('-total_amount')[:10]
        
        return list(employer_analysis)
    
    def analyze_by_month(self, queryset, year):
        """
        Analiza pagos por mes para un año específico.
        
        Args:
            queryset: QuerySet de pagos
            year: Año a analizar
            
        Returns:
            dict: Análisis mensual
        """
        # Extraer mes y agrupar
        monthly_data = queryset.annotate(
            month=ExtractMonth('fecha_creacion')
        ).values('month').annotate(
            payment_count=Count('id'),
            total_amount=Sum('monto'),
            approved_amount=Sum('monto', filter=Q(estado='aprobado'))
        ).order_by('month')
        
        # Convertir a formato para gráficos
        months = []
        counts = []
        totals = []
        approved = []
        
        # Inicializar arrays con ceros para todos los meses
        for i in range(1, 13):
            months.append(datetime(2000, i, 1).strftime('%b'))
            counts.append(0)
            totals.append(0)
            approved.append(0)
        
        # Llenar con datos reales
        for item in monthly_data:
            if item['month'] and 1 <= item['month'] <= 12:
                month_idx = item['month'] - 1
                counts[month_idx] = item['payment_count']
                totals[month_idx] = float(item['total_amount'] if item['total_amount'] else 0)
                approved[month_idx] = float(item['approved_amount'] if item['approved_amount'] else 0)
        
        return {
            'months': json.dumps(months),
            'counts': json.dumps(counts),
            'totals': json.dumps(totals),
            'approved': json.dumps(approved)
        }
    
    def analyze_payment_punctuality(self, queryset):
        """
        Analiza la puntualidad en los pagos.
        
        Args:
            queryset: QuerySet de pagos
            
        Returns:
            dict: Análisis de puntualidad
        """
        # Solo pagos con fecha de vencimiento y pago
        punctuality_qs = queryset.filter(
            fecha_vencimiento__isnull=False,
            fecha_pago__isnull=False
        )
        
        # Calcular días de diferencia
        punctuality_data = punctuality_qs.annotate(
            days_diff=ExpressionWrapper(
                F('fecha_pago') - F('fecha_vencimiento'),
                output_field=fields.DurationField()
            )
        )
        
        # Categorizar
        on_time = punctuality_data.filter(days_diff__lte=timedelta(days=0)).count()
        late_1_7 = punctuality_data.filter(days_diff__gt=timedelta(days=0), days_diff__lte=timedelta(days=7)).count()
        late_8_15 = punctuality_data.filter(days_diff__gt=timedelta(days=7), days_diff__lte=timedelta(days=15)).count()
        late_16_30 = punctuality_data.filter(days_diff__gt=timedelta(days=15), days_diff__lte=timedelta(days=30)).count()
        late_30_plus = punctuality_data.filter(days_diff__gt=timedelta(days=30)).count()
        
        return {
            'categories': json.dumps(['A tiempo', '1-7 días', '8-15 días', '16-30 días', '30+ días']),
            'counts': json.dumps([on_time, late_1_7, late_8_15, late_16_30, late_30_plus])
        }
    
    def generate_projections(self, queryset, year):
        """
        Genera proyecciones de pagos para los próximos meses.
        
        Args:
            queryset: QuerySet de pagos
            year: Año actual
            
        Returns:
            dict: Proyecciones
        """
        # Obtener mes actual
        current_month = timezone.now().month
        
        # Solo hacer proyecciones si tenemos al menos 3 meses de datos
        if current_month < 4:
            return {
                'insufficient_data': True
            }
        
        # Obtener datos históricos para proyección
        historical_data = queryset.annotate(
            month=ExtractMonth('fecha_creacion')
        ).values('month').annotate(
            total_amount=Sum('monto')
        ).order_by('month')
        
        # Convertir a listas para cálculos
        months = []
        amounts = []
        
        for i in range(1, 13):
            months.append(i)
            amounts.append(0)
        
        for item in historical_data:
            if item['month'] and 1 <= item['month'] <= 12:
                amounts[item['month'] - 1] = float(item['total_amount'] if item['total_amount'] else 0)
        
        # Calcular proyección simple (promedio de los últimos 3 meses)
        projection_base = sum(amounts[max(0, current_month-3):current_month]) / min(3, current_month)
        
        # Proyectar para meses restantes
        projections = []
        for i in range(current_month, 13):
            # Ajustar proyección con factores estacionales basados en datos históricos
            month_name = datetime(2000, i, 1).strftime('%b')
            projected_amount = projection_base
            
            # Aplicar pequeñas variaciones para los meses restantes
            # En un sistema real, esto usaría análisis más sofisticado
            if i in [11, 12]:  # Noviembre, Diciembre 
                projected_amount *= 1.2  # Incremento por temporada alta
            
            projections.append({
                'month': month_name,
                'amount': round(projected_amount, 2)
            })
        
        return {
            'projections': projections,
            'total_projected': round(sum(p['amount'] for p in projections), 2)
        }
