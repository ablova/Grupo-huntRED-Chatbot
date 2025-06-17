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
from typing import Dict, Any, Optional

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

from app.models import OnboardingProcess, OnboardingTask, Person, Vacante, BusinessUnit
from app.ats.onboarding.satisfaction_tracker import SatisfactionTracker
from app.ml.onboarding_processor import OnboardingMLProcessor
from app.ats.integrations.notifications.process.onboarding_notifications import OnboardingNotificationService
from app.ats.analytics.services.satisfaction_analyzer import SatisfactionAnalyzer

logger = logging.getLogger(__name__)

# Configuración para firma de tokens de seguridad
signer = Signer(salt='onboarding-satisfaction')

class OnboardingController:
    """
    Controlador principal para la gestión del sistema de onboarding.
    Maneja la creación de procesos, programación de encuestas, y generación de reportes.
    """
    
    def __init__(self):
        self.notification_service = OnboardingNotificationService()
        self.satisfaction_tracker = SatisfactionTracker()
        self.satisfaction_analyzer = SatisfactionAnalyzer()
    
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
            
            # Notificar inicio del proceso
            notification_service = OnboardingNotificationService()
            await notification_service.notify_onboarding_started(process.id)
            
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
                    notification_service = OnboardingNotificationService()
                    asyncio.run(notification_service.notify_low_satisfaction(
                        onboarding_id=onboarding_id,
                        period=period,
                        score=int(data.get('general_satisfaction'))
                    ))
                
                return process
            
            process = await save_response()
            
            # Procesar datos para ML
            ml_processor = OnboardingMLProcessor()
            await ml_processor.process_survey_response(process.id, period, data)
            
            # Analizar tendencias
            satisfaction_analyzer = SatisfactionAnalyzer()
            await satisfaction_analyzer.analyze_satisfaction_trends(process.business_unit)
            
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
            period (int, optional): Período específico para el reporte
            
        Returns:
            dict: Datos del reporte generado
        """
        try:
            @sync_to_async
            def get_report_data():
                process = get_object_or_404(OnboardingProcess, id=onboarding_id)
                
                # Obtener datos del proceso
                person = process.person
                vacancy = process.vacancy
                company = vacancy.company
                
                # Obtener respuestas de encuestas
                responses = process.get_responses()
                
                # Si se especifica período, filtrar solo ese período
                if period:
                    responses = {str(period): responses.get(str(period), {})}
                
                # Calcular métricas
                total_surveys = len(responses)
                completed_surveys = sum(1 for r in responses.values() if r)
                satisfaction_scores = [
                    int(r.get('general_satisfaction', 0))
                    for r in responses.values()
                    if r and r.get('general_satisfaction')
                ]
                
                avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
                
                return {
                    'process_id': onboarding_id,
                    'person': {
                        'id': person.id,
                        'name': f"{person.first_name} {person.last_name}",
                        'email': person.email
                    },
                    'vacancy': {
                        'id': vacancy.id,
                        'title': vacancy.title,
                        'company': company.name
                    },
                    'hire_date': process.hire_date.isoformat(),
                    'total_surveys': total_surveys,
                    'completed_surveys': completed_surveys,
                    'average_satisfaction': round(avg_satisfaction, 2),
                    'responses': responses
                }
            
            report_data = await get_report_data()
            
            # Generar PDF
            pdf_file = await cls._generate_pdf_report(report_data)
            
            return {
                'success': True,
                'report_data': report_data,
                'pdf_file': pdf_file
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte de satisfacción: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    async def _generate_pdf_report(cls, report_data):
        """Genera archivo PDF del reporte."""
        try:
            # Renderizar template HTML
            html_content = render_to_string(
                'onboarding/satisfaction_report.html',
                report_data
            )
            
            # Convertir a PDF
            from weasyprint import HTML
            pdf = HTML(string=html_content).write_pdf()
            
            return pdf
            
        except Exception as e:
            logger.error(f"Error generando PDF: {str(e)}")
            return None
    
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
