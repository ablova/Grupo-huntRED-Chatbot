"""
Comando para generar insights y recomendaciones para consultores

Este comando analiza el rendimiento de los consultores y genera
recomendaciones personalizadas para mejorar su productividad.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F
from datetime import datetime, timedelta
import logging

from app.models import Person, Application, Vacante, BusinessUnit, Event, Interview
from app.ats.dashboard.consultant_advanced_dashboard import ConsultantAdvancedDashboard

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Genera insights y recomendaciones personalizadas para consultores'

    def add_arguments(self, parser):
        parser.add_argument(
            '--consultant-id',
            type=str,
            help='ID específico del consultor a analizar'
        )
        parser.add_argument(
            '--business-unit',
            type=str,
            help='Unidad de negocio específica'
        )
        parser.add_argument(
            '--period',
            type=str,
            default='30d',
            choices=['7d', '30d', '90d'],
            help='Período de análisis (7d, 30d, 90d)'
        )
        parser.add_argument(
            '--generate-recommendations',
            action='store_true',
            help='Generar recomendaciones específicas'
        )
        parser.add_argument(
            '--export-data',
            action='store_true',
            help='Exportar datos a archivo'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin hacer cambios'
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(
                self.style.SUCCESS('🚀 Iniciando generación de insights para consultores...')
            )
            
            # Configurar período de análisis
            period_days = self._get_period_days(options['period'])
            start_date = timezone.now() - timedelta(days=period_days)
            
            # Obtener consultores a analizar
            consultants = self._get_consultants_to_analyze(options)
            
            if not consultants:
                self.stdout.write(
                    self.style.WARNING('⚠️ No se encontraron consultores para analizar')
                )
                return
            
            self.stdout.write(
                f'📊 Analizando {len(consultants)} consultores para el período de {options["period"]}'
            )
            
            # Analizar cada consultor
            insights_data = []
            for consultant in consultants:
                self.stdout.write(f'🔍 Analizando consultor: {consultant.name}')
                
                consultant_insights = self._analyze_consultant(
                    consultant, start_date, options
                )
                insights_data.append(consultant_insights)
                
                # Mostrar resumen
                self._display_consultant_summary(consultant_insights)
            
            # Generar recomendaciones si se solicita
            if options['generate_recommendations']:
                self._generate_recommendations(insights_data, options)
            
            # Exportar datos si se solicita
            if options['export_data']:
                self._export_insights_data(insights_data, options)
            
            # Mostrar resumen general
            self._display_general_summary(insights_data)
            
            self.stdout.write(
                self.style.SUCCESS('✅ Análisis completado exitosamente')
            )
            
        except Exception as e:
            logger.error(f"Error en comando generate_consultant_insights: {str(e)}")
            raise CommandError(f'Error ejecutando comando: {str(e)}')

    def _get_period_days(self, period: str) -> int:
        """Convierte el período a días."""
        period_mapping = {
            '7d': 7,
            '30d': 30,
            '90d': 90
        }
        return period_mapping.get(period, 30)

    def _get_consultants_to_analyze(self, options: dict) -> list:
        """Obtiene la lista de consultores a analizar."""
        consultants = Person.objects.filter(is_consultant=True, is_active=True)
        
        # Filtrar por ID específico
        if options['consultant_id']:
            consultants = consultants.filter(id=options['consultant_id'])
        
        # Filtrar por unidad de negocio
        if options['business_unit']:
            consultants = consultants.filter(business_unit__name=options['business_unit'])
        
        return list(consultants)

    def _analyze_consultant(self, consultant: Person, start_date: datetime, options: dict) -> dict:
        """Analiza un consultor específico."""
        try:
            # Inicializar dashboard del consultor
            dashboard = ConsultantAdvancedDashboard(
                consultant_id=str(consultant.id),
                business_unit=consultant.business_unit
            )
            
            # Obtener métricas básicas
            performance_metrics = self._get_performance_metrics(consultant, start_date)
            productivity_metrics = self._get_productivity_metrics(consultant, start_date)
            engagement_metrics = self._get_engagement_metrics(consultant, start_date)
            
            # Calcular scores
            performance_score = self._calculate_performance_score(performance_metrics)
            productivity_score = self._calculate_productivity_score(productivity_metrics)
            engagement_score = self._calculate_engagement_score(engagement_metrics)
            
            # Identificar áreas de mejora
            improvement_areas = self._identify_improvement_areas(
                performance_metrics, productivity_metrics, engagement_metrics
            )
            
            # Generar insights específicos
            insights = self._generate_consultant_insights(
                consultant, performance_metrics, productivity_metrics, engagement_metrics
            )
            
            return {
                'consultant': {
                    'id': consultant.id,
                    'name': consultant.name,
                    'email': consultant.email,
                    'business_unit': consultant.business_unit.name if consultant.business_unit else 'N/A'
                },
                'period': {
                    'start_date': start_date,
                    'end_date': timezone.now(),
                    'days': (timezone.now() - start_date).days
                },
                'metrics': {
                    'performance': performance_metrics,
                    'productivity': productivity_metrics,
                    'engagement': engagement_metrics
                },
                'scores': {
                    'performance': performance_score,
                    'productivity': productivity_score,
                    'engagement': engagement_score,
                    'overall': (performance_score + productivity_score + engagement_score) / 3
                },
                'improvement_areas': improvement_areas,
                'insights': insights,
                'recommendations': []  # Se llenará si se solicitan
            }
            
        except Exception as e:
            logger.error(f"Error analizando consultor {consultant.id}: {str(e)}")
            return {
                'consultant': {
                    'id': consultant.id,
                    'name': consultant.name,
                    'email': consultant.email
                },
                'error': str(e)
            }

    def _get_performance_metrics(self, consultant: Person, start_date: datetime) -> dict:
        """Obtiene métricas de rendimiento del consultor."""
        # Aplicaciones del período
        applications = Application.objects.filter(
            consultant=consultant,
            created_at__gte=start_date
        )
        
        total_applications = applications.count()
        successful_placements = applications.filter(status='hired').count()
        conversion_rate = (successful_placements / total_applications * 100) if total_applications > 0 else 0
        
        # Tiempo promedio de contratación
        hired_applications = applications.filter(status='hired')
        avg_time_to_hire = hired_applications.aggregate(
            avg_days=Avg(F('updated_at') - F('created_at'))
        )['avg_days'] or timedelta(days=0)
        
        # Ingresos generados
        revenue_generated = applications.filter(
            status='hired'
        ).aggregate(
            total_revenue=Sum('vacancy__salary_max')
        )['total_revenue'] or 0
        
        return {
            'total_applications': total_applications,
            'successful_placements': successful_placements,
            'conversion_rate': round(conversion_rate, 2),
            'avg_time_to_hire_days': avg_time_to_hire.days,
            'revenue_generated': revenue_generated,
            'applications_per_day': round(total_applications / max((timezone.now() - start_date).days, 1), 2)
        }

    def _get_productivity_metrics(self, consultant: Person, start_date: datetime) -> dict:
        """Obtiene métricas de productividad del consultor."""
        # Entrevistas realizadas
        interviews = Interview.objects.filter(
            consultant=consultant,
            scheduled_at__gte=start_date
        )
        
        total_interviews = interviews.count()
        completed_interviews = interviews.filter(status='completed').count()
        interview_completion_rate = (completed_interviews / total_interviews * 100) if total_interviews > 0 else 0
        
        # Tiempo de respuesta (simulado)
        avg_response_time = 18.5  # horas - esto debería calcularse de datos reales
        
        # Tareas completadas
        events = Event.objects.filter(
            metadata__consultant_id=consultant.id,
            created_at__gte=start_date
        )
        
        total_events = events.count()
        completed_events = events.filter(status='CONFIRMADO').count()
        completion_rate = (completed_events / total_events * 100) if total_events > 0 else 0
        
        return {
            'total_interviews': total_interviews,
            'completed_interviews': completed_interviews,
            'interview_completion_rate': round(interview_completion_rate, 2),
            'avg_response_time_hours': avg_response_time,
            'total_events': total_events,
            'completed_events': completed_events,
            'completion_rate': round(completion_rate, 2)
        }

    def _get_engagement_metrics(self, consultant: Person, start_date: datetime) -> dict:
        """Obtiene métricas de engagement del consultor."""
        # Actividad reciente
        recent_activity = Application.objects.filter(
            consultant=consultant,
            created_at__gte=start_date
        ).count()
        
        # Interacciones con candidatos
        candidate_interactions = EventParticipant.objects.filter(
            event__metadata__consultant_id=consultant.id,
            event__created_at__gte=start_date
        ).count()
        
        # Feedback recibido (simulado)
        satisfaction_score = 4.6  # Esto debería venir de datos reales
        
        return {
            'recent_activity_count': recent_activity,
            'candidate_interactions': candidate_interactions,
            'satisfaction_score': satisfaction_score,
            'activity_level': 'high' if recent_activity > 10 else 'medium' if recent_activity > 5 else 'low'
        }

    def _calculate_performance_score(self, metrics: dict) -> float:
        """Calcula score de rendimiento."""
        conversion_score = min(metrics['conversion_rate'] / 20, 1.0) * 40
        time_score = max(0, (30 - metrics['avg_time_to_hire_days']) / 30) * 30
        revenue_score = min(metrics['revenue_generated'] / 50000, 1.0) * 30
        
        return round(conversion_score + time_score + revenue_score, 1)

    def _calculate_productivity_score(self, metrics: dict) -> float:
        """Calcula score de productividad."""
        interview_score = (metrics['interview_completion_rate'] / 100) * 30
        response_score = max(0, (24 - metrics['avg_response_time_hours']) / 24) * 30
        completion_score = (metrics['completion_rate'] / 100) * 40
        
        return round(interview_score + response_score + completion_score, 1)

    def _calculate_engagement_score(self, metrics: dict) -> float:
        """Calcula score de engagement."""
        activity_score = min(metrics['recent_activity_count'] / 20, 1.0) * 40
        interaction_score = min(metrics['candidate_interactions'] / 50, 1.0) * 30
        satisfaction_score = (metrics['satisfaction_score'] / 5) * 30
        
        return round(activity_score + interaction_score + satisfaction_score, 1)

    def _identify_improvement_areas(self, performance: dict, productivity: dict, engagement: dict) -> list:
        """Identifica áreas de mejora."""
        areas = []
        
        # Análisis de rendimiento
        if performance['conversion_rate'] < 15:
            areas.append({
                'category': 'performance',
                'area': 'conversion_rate',
                'current_value': performance['conversion_rate'],
                'target_value': 20,
                'priority': 'high',
                'description': 'Tasa de conversión por debajo del objetivo'
            })
        
        if performance['avg_time_to_hire_days'] > 20:
            areas.append({
                'category': 'performance',
                'area': 'time_to_hire',
                'current_value': performance['avg_time_to_hire_days'],
                'target_value': 15,
                'priority': 'medium',
                'description': 'Tiempo de contratación superior al promedio'
            })
        
        # Análisis de productividad
        if productivity['avg_response_time_hours'] > 24:
            areas.append({
                'category': 'productivity',
                'area': 'response_time',
                'current_value': productivity['avg_response_time_hours'],
                'target_value': 12,
                'priority': 'high',
                'description': 'Tiempo de respuesta superior a 24 horas'
            })
        
        if productivity['interview_completion_rate'] < 80:
            areas.append({
                'category': 'productivity',
                'area': 'interview_completion',
                'current_value': productivity['interview_completion_rate'],
                'target_value': 90,
                'priority': 'medium',
                'description': 'Tasa de finalización de entrevistas baja'
            })
        
        # Análisis de engagement
        if engagement['recent_activity_count'] < 5:
            areas.append({
                'category': 'engagement',
                'area': 'activity_level',
                'current_value': engagement['recent_activity_count'],
                'target_value': 10,
                'priority': 'medium',
                'description': 'Nivel de actividad reciente bajo'
            })
        
        return areas

    def _generate_consultant_insights(self, consultant: Person, performance: dict, productivity: dict, engagement: dict) -> list:
        """Genera insights específicos para el consultor."""
        insights = []
        
        # Insights de rendimiento
        if performance['conversion_rate'] > 25:
            insights.append({
                'type': 'positive',
                'category': 'performance',
                'title': 'Excelente tasa de conversión',
                'description': f'Tu tasa de conversión del {performance["conversion_rate"]}% está muy por encima del promedio del equipo.',
                'impact': 'high'
            })
        
        if performance['avg_time_to_hire_days'] < 10:
            insights.append({
                'type': 'positive',
                'category': 'performance',
                'title': 'Contrataciones rápidas',
                'description': f'Promedio de {performance["avg_time_to_hire_days"]} días para contratar, muy eficiente.',
                'impact': 'high'
            })
        
        # Insights de productividad
        if productivity['avg_response_time_hours'] < 12:
            insights.append({
                'type': 'positive',
                'category': 'productivity',
                'title': 'Respuestas rápidas',
                'description': f'Tiempo promedio de respuesta de {productivity["avg_response_time_hours"]} horas, excelente.',
                'impact': 'medium'
            })
        
        # Insights de engagement
        if engagement['satisfaction_score'] > 4.5:
            insights.append({
                'type': 'positive',
                'category': 'engagement',
                'title': 'Alta satisfacción',
                'description': f'Puntuación de satisfacción de {engagement["satisfaction_score"]}/5, muy buena.',
                'impact': 'medium'
            })
        
        return insights

    def _generate_recommendations(self, insights_data: list, options: dict):
        """Genera recomendaciones basadas en los insights."""
        self.stdout.write('🎯 Generando recomendaciones personalizadas...')
        
        for consultant_data in insights_data:
            if 'error' in consultant_data:
                continue
            
            recommendations = []
            improvement_areas = consultant_data['improvement_areas']
            
            for area in improvement_areas:
                recommendation = self._create_recommendation(area, consultant_data)
                if recommendation:
                    recommendations.append(recommendation)
            
            consultant_data['recommendations'] = recommendations
            
            if not options['dry_run']:
                # Guardar recomendaciones en la base de datos
                self._save_recommendations(consultant_data)
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Generadas {sum(len(d.get("recommendations", [])) for d in insights_data)} recomendaciones')
        )

    def _create_recommendation(self, improvement_area: dict, consultant_data: dict) -> dict:
        """Crea una recomendación específica basada en un área de mejora."""
        recommendations_mapping = {
            'conversion_rate': {
                'title': 'Mejorar proceso de screening',
                'description': 'Implementa criterios más estrictos en la evaluación inicial de candidatos.',
                'action': 'Revisar y actualizar criterios de evaluación',
                'effort': 'medium',
                'expected_impact': 'Aumentar tasa de conversión en 5-10%'
            },
            'time_to_hire': {
                'title': 'Optimizar proceso de contratación',
                'description': 'Reduce el tiempo entre la aplicación y la contratación final.',
                'action': 'Implementar proceso acelerado para candidatos top',
                'effort': 'high',
                'expected_impact': 'Reducir tiempo de contratación en 30%'
            },
            'response_time': {
                'title': 'Automatizar respuestas iniciales',
                'description': 'Configura respuestas automáticas para mejorar el tiempo de respuesta.',
                'action': 'Configurar templates de respuesta automática',
                'effort': 'low',
                'expected_impact': 'Reducir tiempo de respuesta a 4-6 horas'
            },
            'interview_completion': {
                'title': 'Mejorar seguimiento de entrevistas',
                'description': 'Implementa recordatorios y seguimiento para reducir cancelaciones.',
                'action': 'Configurar sistema de recordatorios automáticos',
                'effort': 'medium',
                'expected_impact': 'Aumentar tasa de finalización a 90%'
            },
            'activity_level': {
                'title': 'Aumentar actividad de sourcing',
                'description': 'Incrementa la búsqueda activa de candidatos.',
                'action': 'Dedicar 2 horas diarias a sourcing activo',
                'effort': 'medium',
                'expected_impact': 'Aumentar aplicaciones en 25%'
            }
        }
        
        area_key = improvement_area['area']
        if area_key in recommendations_mapping:
            base_rec = recommendations_mapping[area_key]
            return {
                'type': improvement_area['category'],
                'priority': improvement_area['priority'],
                'title': base_rec['title'],
                'description': base_rec['description'],
                'action': base_rec['action'],
                'effort': base_rec['effort'],
                'expected_impact': base_rec['expected_impact'],
                'improvement_area': improvement_area
            }
        
        return None

    def _save_recommendations(self, consultant_data: dict):
        """Guarda las recomendaciones en la base de datos."""
        try:
            # Aquí implementarías la lógica para guardar las recomendaciones
            # en tu modelo de base de datos
            pass
        except Exception as e:
            logger.error(f"Error guardando recomendaciones: {str(e)}")

    def _export_insights_data(self, insights_data: list, options: dict):
        """Exporta los datos de insights a un archivo."""
        try:
            import json
            from django.conf import settings
            import os
            
            # Crear directorio si no existe
            export_dir = os.path.join(settings.BASE_DIR, 'exports', 'consultant_insights')
            os.makedirs(export_dir, exist_ok=True)
            
            # Generar nombre de archivo
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f'consultant_insights_{timestamp}.json'
            filepath = os.path.join(export_dir, filename)
            
            # Guardar datos
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(insights_data, f, indent=2, default=str)
            
            self.stdout.write(
                self.style.SUCCESS(f'📁 Datos exportados a: {filepath}')
            )
            
        except Exception as e:
            logger.error(f"Error exportando datos: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'❌ Error exportando datos: {str(e)}')
            )

    def _display_consultant_summary(self, consultant_data: dict):
        """Muestra un resumen del análisis del consultor."""
        if 'error' in consultant_data:
            self.stdout.write(
                self.style.ERROR(f'❌ Error analizando {consultant_data["consultant"]["name"]}: {consultant_data["error"]}')
            )
            return
        
        consultant = consultant_data['consultant']
        scores = consultant_data['scores']
        
        self.stdout.write(f'\n📊 {consultant["name"]} ({consultant["business_unit"]})')
        self.stdout.write(f'   Performance: {scores["performance"]}/100')
        self.stdout.write(f'   Productividad: {scores["productivity"]}/100')
        self.stdout.write(f'   Engagement: {scores["engagement"]}/100')
        self.stdout.write(f'   Overall: {scores["overall"]:.1f}/100')
        
        if consultant_data['improvement_areas']:
            self.stdout.write(f'   🔧 Áreas de mejora: {len(consultant_data["improvement_areas"])}')
        
        if consultant_data['insights']:
            self.stdout.write(f'   💡 Insights: {len(consultant_data["insights"])}')

    def _display_general_summary(self, insights_data: list):
        """Muestra un resumen general del análisis."""
        valid_data = [d for d in insights_data if 'error' not in d]
        
        if not valid_data:
            return
        
        avg_overall = sum(d['scores']['overall'] for d in valid_data) / len(valid_data)
        total_improvement_areas = sum(len(d['improvement_areas']) for d in valid_data)
        total_insights = sum(len(d['insights']) for d in valid_data)
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('📈 RESUMEN GENERAL')
        self.stdout.write('='*50)
        self.stdout.write(f'Consultores analizados: {len(valid_data)}')
        self.stdout.write(f'Score promedio: {avg_overall:.1f}/100')
        self.stdout.write(f'Áreas de mejora identificadas: {total_improvement_areas}')
        self.stdout.write(f'Insights generados: {total_insights}')
        
        # Top performers
        top_performers = sorted(valid_data, key=lambda x: x['scores']['overall'], reverse=True)[:3]
        self.stdout.write('\n🏆 TOP PERFORMERS:')
        for i, performer in enumerate(top_performers, 1):
            self.stdout.write(f'{i}. {performer["consultant"]["name"]} - {performer["scores"]["overall"]:.1f}/100') 