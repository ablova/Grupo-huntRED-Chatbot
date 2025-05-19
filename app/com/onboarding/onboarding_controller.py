"""
Controlador para manejar todas las interacciones del sistema de onboarding.

Este módulo proporciona funcionalidades para:
1. Iniciar procesos de onboarding
2. Gestionar encuestas de satisfacción
3. Generar reportes para clientes
4. Integrar con el sistema ML para predicciones
"""

import json
import logging
import base64
from datetime import datetime, timedelta
from pathlib import Path

from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.signing import Signer, BadSignature
from django.conf import settings
from django.db import transaction
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async
from PIL import Image

from app.models import OnboardingProcess, OnboardingTask, Person, Vacante
from app.com.onboarding.satisfaction_tracker import SatisfactionTracker
from app.ml.onboarding_processor import OnboardingMLProcessor

logger = logging.getLogger(__name__)

# Configuración para firma de tokens de seguridad
signer = Signer(salt='onboarding-satisfaction')

class OnboardingController:
    """
    Controlador principal para la gestión del sistema de onboarding.
    Maneja la creación de procesos, programación de encuestas, y generación de reportes.
    """
    
    @classmethod
    async def start_onboarding_process(cls, person_id, vacancy_id, hire_date=None):
        """
        Inicia un nuevo proceso de onboarding para un candidato.
        
        Args:
            person_id (int): ID del candidato
            vacancy_id (int): ID de la vacante
            hire_date (datetime, optional): Fecha de contratación. Si es None, usa la fecha actual.
            
        Returns:
            dict: Información sobre el proceso creado y las tareas programadas
        """
        try:
            # Validar datos
            if not person_id or not vacancy_id:
                raise ValidationError("Se requieren person_id y vacancy_id")
                
            # Si no se proporciona fecha, usar la actual
            if not hire_date:
                hire_date = timezone.now()
            
            # Crear proceso de onboarding de forma asíncrona
            @sync_to_async
            def create_process():
                person = Person.objects.get(id=person_id)
                vacancy = Vacante.objects.get(id=vacancy_id)
                
                # Verificar si ya existe un proceso para esta persona y vacante
                existing = OnboardingProcess.objects.filter(
                    person_id=person_id,
                    vacancy_id=vacancy_id
                ).first()
                
                if existing:
                    return existing, False
                
                # Crear nuevo proceso
                with transaction.atomic():
                    process = OnboardingProcess.objects.create(
                        person_id=person_id,
                        vacancy_id=vacancy_id,
                        hire_date=hire_date,
                        status='IN_PROGRESS'
                    )
                    
                    # Crear tareas estándar
                    OnboardingTask.objects.create(
                        onboarding=process,
                        title="Bienvenida y documentación inicial",
                        description="Enviar correo de bienvenida y solicitar documentación pendiente",
                        priority=10,
                        due_date=timezone.now() + timedelta(days=1)
                    )
                    
                    OnboardingTask.objects.create(
                        onboarding=process,
                        title="Configuración de accesos y herramientas",
                        description="Coordinar con IT la configuración de cuentas y accesos",
                        priority=9,
                        due_date=timezone.now() + timedelta(days=2)
                    )
                    
                    OnboardingTask.objects.create(
                        onboarding=process,
                        title="Reunión inicial con equipo",
                        description="Agendar presentación con el equipo y áreas relacionadas",
                        priority=8,
                        due_date=timezone.now() + timedelta(days=3)
                    )
                    
                    OnboardingTask.objects.create(
                        onboarding=process,
                        title="Sesión de capacitación inicial",
                        description="Coordinar entrenamiento sobre procesos y herramientas clave",
                        priority=7,
                        due_date=timezone.now() + timedelta(days=7)
                    )
                    
                return process, True
            
            process, is_new = await create_process()
            
            # Programar encuestas de satisfacción
            tracker = SatisfactionTracker()
            surveys_scheduled = await tracker.schedule_satisfaction_surveys(
                person_id=person_id,
                vacancy_id=vacancy_id,
                hire_date=hire_date
            )
            
            return {
                'success': True,
                'process_id': process.id,
                'person_id': person_id,
                'vacancy_id': vacancy_id,
                'hire_date': hire_date.isoformat(),
                'is_new': is_new,
                'surveys_scheduled': surveys_scheduled
            }
            
        except Exception as e:
            logger.error(f"Error iniciando proceso de onboarding: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    async def process_survey_response(cls, token, data):
        """
        Procesa las respuestas de una encuesta de satisfacción.
        
        Args:
            token (str): Token firmado que contiene onboarding_id y period
            data (dict): Datos de la encuesta
            
        Returns:
            dict: Resultado del procesamiento
        """
        try:
            # Validar y decodificar token
            try:
                token_data = json.loads(signer.unsign(token))
                onboarding_id = token_data.get('onboarding_id')
                period = token_data.get('period')
            except (BadSignature, json.JSONDecodeError) as e:
                logger.error(f"Token inválido: {str(e)}")
                return {'success': False, 'error': 'Token inválido'}
            
            if not onboarding_id or not period:
                return {'success': False, 'error': 'Token con datos incompletos'}
            
            # Guardar respuesta
            @sync_to_async
            def save_response():
                process = get_object_or_404(OnboardingProcess, id=onboarding_id)
                
                # Guardar respuestas
                process.record_survey_response(period, data)
                
                # Si satisfacción es baja, crear alerta
                if data.get('general_satisfaction') and int(data.get('general_satisfaction')) < 5:
                    # TODO: Implementar sistema de alertas para satisfacción baja
                    logger.warning(f"Alerta: Baja satisfacción en onboarding {onboarding_id}, periodo {period}")
                
                return process
            
            process = await save_response()
            
            # Procesar datos para ML si corresponde
            ml_processor = OnboardingMLProcessor()
            await ml_processor.process_survey_response(process.id, period, data)
            
            return {
                'success': True,
                'message': 'Respuesta procesada correctamente'
            }
            
        except Exception as e:
            logger.error(f"Error procesando respuesta de encuesta: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    async def generate_satisfaction_report(cls, onboarding_id, period=None):
        """
        Genera un reporte de satisfacción para un proceso de onboarding.
        
        Args:
            onboarding_id (int): ID del proceso de onboarding
            period (int, optional): Período específico para el reporte. Si es None, incluye todos.
            
        Returns:
            HttpResponse: Reporte en formato HTML o PDF
        """
        try:
            @sync_to_async
            def get_report_data():
                process = get_object_or_404(OnboardingProcess, id=onboarding_id)
                person = process.person
                vacancy = process.vacancy
                
                # Obtener período específico o el último disponible
                if period is not None:
                    # Usar período específico
                    report_period = period
                else:
                    # Buscar el último período con respuestas
                    available_periods = [
                        int(p) for p in process.survey_responses.keys()
                    ] if process.survey_responses else []
                    
                    report_period = max(available_periods) if available_periods else None
                
                # Preparar datos del reporte
                satisfaction_score = process.get_satisfaction_score(report_period)
                all_periods = process.get_all_periods_scores()
                
                # Calcular tendencia (si hay al menos 2 períodos con respuestas)
                trend = None
                trend_percent = None
                
                available_scores = [(p['days'], p['score']) for p in all_periods if p['score'] is not None]
                available_scores.sort(key=lambda x: x[0])
                
                if len(available_scores) >= 2:
                    # Comparar último score con el anterior
                    current_score = available_scores[-1][1]
                    previous_score = available_scores[-2][1]
                    
                    if current_score > previous_score:
                        trend = 'up'
                        trend_percent = ((current_score - previous_score) / previous_score) * 100
                    elif current_score < previous_score:
                        trend = 'down'
                        trend_percent = ((previous_score - current_score) / previous_score) * 100
                    else:
                        trend = 'stable'
                
                # Obtener logo para el reporte
                logo_path = Path(settings.BASE_DIR) / 'app' / 'static' / 'images' / 'logo.png'
                if logo_path.exists():
                    with open(logo_path, 'rb') as logo_file:
                        logo_base64 = base64.b64encode(logo_file.read()).decode('utf-8')
                else:
                    logo_base64 = None
                
                company = vacancy.empresa if hasattr(vacancy, 'empresa') else None
                
                # Preparar contexto para el template
                context = {
                    'onboarding': process,
                    'person': person,
                    'vacancy': vacancy,
                    'company': company,
                    'period': report_period,
                    'date': timezone.now().strftime('%d/%m/%Y'),
                    'report': {
                        'satisfaction_score': satisfaction_score,
                        'trend': trend,
                        'trend_percent': trend_percent,
                        'periods': all_periods,
                        'responses': process.survey_responses.get(str(report_period), {}) if report_period else {}
                    },
                    'logo_base64': logo_base64
                }
                
                return context
            
            # Obtener datos y renderizar reporte
            context = await get_report_data()
            html_content = render_to_string('onboarding/satisfaction_report.html', context)
            
            # Devolver como HTML (podría extenderse para generar PDF)
            return HttpResponse(html_content, content_type='text/html')
            
        except Exception as e:
            logger.error(f"Error generando reporte de satisfacción: {str(e)}")
            return HttpResponse(f"Error: {str(e)}", status=500)
    
    @classmethod
    async def generate_secure_survey_link(cls, onboarding_id, period):
        """
        Genera un enlace seguro para una encuesta de satisfacción.
        
        Args:
            onboarding_id (int): ID del proceso de onboarding
            period (int): Período de la encuesta (días)
            
        Returns:
            str: URL firmada para la encuesta
        """
        try:
            # Generar token con datos necesarios
            token_data = {
                'onboarding_id': onboarding_id,
                'period': period,
                'ts': timezone.now().timestamp()
            }
            
            # Firmar token
            signed_token = signer.sign(json.dumps(token_data))
            
            # Construir URL
            base_url = getattr(settings, 'SITE_URL', 'https://app.huntred.com')
            survey_url = f"{base_url}/onboarding/survey/?token={signed_token}"
            
            return survey_url
            
        except Exception as e:
            logger.error(f"Error generando enlace para encuesta: {str(e)}")
            return None
    
    @classmethod
    async def get_onboarding_status(cls, onboarding_id):
        """
        Obtiene el estado actual de un proceso de onboarding, incluyendo encuestas y tareas.
        
        Args:
            onboarding_id (int): ID del proceso de onboarding
            
        Returns:
            dict: Estado detallado del proceso
        """
        try:
            @sync_to_async
            def get_status():
                process = get_object_or_404(OnboardingProcess, id=onboarding_id)
                
                # Obtener tareas
                tasks = process.tasks.all()
                
                # Estado de las encuestas
                surveys_status = process.get_surveys_status()
                
                # Calcular progreso general
                completed_tasks = tasks.filter(status='COMPLETED').count()
                total_tasks = tasks.count()
                task_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                
                # Obtener satisfacción general
                satisfaction = process.get_satisfaction_score()
                
                return {
                    'process_id': process.id,
                    'person': {
                        'id': process.person.id,
                        'name': str(process.person)
                    },
                    'vacancy': {
                        'id': process.vacancy.id,
                        'title': process.vacancy.title
                    },
                    'hire_date': process.hire_date.isoformat(),
                    'status': process.status,
                    'satisfaction_score': satisfaction,
                    'task_progress': task_progress,
                    'tasks': [
                        {
                            'id': task.id,
                            'title': task.title,
                            'status': task.status,
                            'due_date': task.due_date.isoformat() if task.due_date else None,
                            'is_overdue': task.is_overdue(),
                            'days_remaining': task.get_days_remaining()
                        }
                        for task in tasks
                    ],
                    'surveys': surveys_status
                }
            
            return await get_status()
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de onboarding: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
