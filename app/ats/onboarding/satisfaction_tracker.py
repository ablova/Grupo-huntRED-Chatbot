# /home/pablo/app/com/onboarding/satisfaction_tracker.py
"""
Sistema de seguimiento de satisfacción para candidatos en onboarding.
Realiza encuestas periódicas, recolecta respuestas y genera insights.
"""
from typing import Dict, List, Optional, Union
import asyncio
from datetime import datetime, timedelta
import json
import logging

from django.conf import settings
import redis
from django.utils import timezone

from app.models import Person, Vacante, Company, OnboardingProcess
from app.ats.chatbot.message_service import MessageService
from app.tasks import send_satisfaction_survey

logger = logging.getLogger(__name__)

class SatisfactionTracker:
    """Gestiona encuestas periódicas de satisfacción durante el onboarding"""
    
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.redis_prefix = "satisfaction_tracker:"
        self.message_service = MessageService()
        
        # Preguntas predefinidas de satisfacción - cortas y directas
        self.satisfaction_questions = [
            {
                "id": "feeling",
                "question": "¿Cómo te sientes hoy en tu nuevo trabajo?",
                "options": ["😀 Muy bien", "🙂 Bien", "😐 Neutral", "😕 No muy bien", "😟 Mal"],
                "type": "emoji_scale"
            },
            {
                "id": "expectations",
                "question": "¿El trabajo cumple con tus expectativas?",
                "options": ["Completamente", "En su mayoría", "Parcialmente", "Poco", "No cumple"],
                "type": "likert_scale"
            },
            {
                "id": "integration",
                "question": "¿Te sientes integrado con tu equipo?",
                "options": ["Totalmente", "Bastante", "Algo", "Poco", "Nada"],
                "type": "likert_scale"
            },
            {
                "id": "support",
                "question": "¿Has recibido el apoyo necesario?",
                "options": ["Sí, todo el apoyo", "Bastante apoyo", "Apoyo limitado", "Poco apoyo", "Sin apoyo"],
                "type": "likert_scale"
            }
        ]
        
        # Períodos de seguimiento (en días desde contratación)
        self.follow_up_periods = [3, 7, 15, 30, 60, 90, 180, 365]
    
    async def schedule_satisfaction_surveys(self, 
                                          person_id: int, 
                                          vacancy_id: int,
                                          hire_date: datetime) -> bool:
        """Programa encuestas de satisfacción para períodos clave"""
        try:
            # Obtener datos necesarios
            person = Person.objects.get(id=person_id)
            vacancy = Vacante.objects.get(id=vacancy_id)
            
            # Crear o recuperar proceso de onboarding
            onboarding, created = OnboardingProcess.objects.get_or_create(
                person=person,
                vacancy=vacancy,
                defaults={
                    'hire_date': hire_date,
                    'status': 'active',
                    'completed_surveys': 0
                }
            )
            
            # Programar encuestas para cada período
            for days in self.follow_up_periods:
                survey_date = hire_date + timedelta(days=days)
                
                # Solo programar encuestas futuras si es un proceso existente
                if created or survey_date > timezone.now():
                    await self._schedule_survey(onboarding.id, survey_date, days)
            
            logger.info(f"Encuestas programadas para {person.first_name} ({vacancy.title})")
            return True
            
        except (Person.DoesNotExist, Vacante.DoesNotExist) as e:
            logger.error(f"Error programando encuestas: {e}")
            return False
    
    async def _schedule_survey(self, onboarding_id: int, survey_date: datetime, period_days: int):
        """Programa una encuesta específica en Celery"""
        
        # Programar tarea asíncrona
        send_satisfaction_survey.apply_async(
            args=[onboarding_id, period_days],
            eta=survey_date
        )
        
        # Almacenar en Redis para referencia
        key = f"{self.redis_prefix}scheduled:{onboarding_id}:{period_days}"
        self.redis.set(
            key, 
            json.dumps({
                "scheduled_at": datetime.now().isoformat(),
                "survey_date": survey_date.isoformat(),
                "period_days": period_days
            }),
            ex=86400*366  # 1 año + 1 día TTL
        )
    
    async def send_satisfaction_survey(self, onboarding_id: int, period_days: int) -> bool:
        """Envía encuesta de satisfacción a un candidato"""
        try:
            onboarding = OnboardingProcess.objects.get(id=onboarding_id)
            person = onboarding.person
            vacancy = onboarding.vacancy
            
            # Verificar si la encuesta ya fue enviada
            key = f"{self.redis_prefix}sent:{onboarding_id}:{period_days}"
            if self.redis.get(key):
                logger.info(f"Encuesta para {person.first_name} ({period_days} días) ya enviada")
                return False  # Ya enviada
                
            # Preparar mensaje personalizado según período
            if period_days <= 7:
                intro_message = f"¡Hola {person.first_name}! Esperamos que estés adaptándote bien a tu nuevo rol como {vacancy.title}. Nos gustaría saber cómo te sientes."
            elif period_days <= 30:
                intro_message = f"¡Hola {person.first_name}! Han pasado {period_days} días desde que comenzaste como {vacancy.title}. Queremos saber cómo va todo."
            else:
                intro_message = f"¡Hola {person.first_name}! Ya llevas {period_days} días en {vacancy.company.name}. Tu feedback es muy importante para nosotros."
            
            # Determinar canal preferido
            preferred_channel = getattr(person, 'preferred_channel', None) or 'whatsapp'
            
            # Enviar introducción
            await self.message_service.send_message(
                person.id,
                intro_message,
                preferred_channel
            )
            
            # Esperar un poco para no saturar al usuario
            await asyncio.sleep(1)
            
            # Enviar preguntas de la encuesta
            survey_id = f"{onboarding_id}:{period_days}"
            
            for question in self.satisfaction_questions:
                # Crear mensaje con opciones
                await self.message_service.send_options(
                    person.id,
                    question["question"],
                    question["options"],
                    preferred_channel,
                    metadata={
                        "question_id": question["id"], 
                        "survey_id": survey_id,
                        "type": "satisfaction_survey"
                    }
                )
                
                # En un sistema real, esperaríamos la respuesta aquí
                # Para este ejemplo, simulamos un tiempo entre preguntas
                await asyncio.sleep(1)
            
            # Enviar mensaje de cierre
            await self.message_service.send_message(
                person.id,
                f"Gracias por tu tiempo. Tus respuestas nos ayudan a mejorar la experiencia de integración.",
                preferred_channel
            )
            
            # Marcar como enviada
            self.redis.setex(key, 86400*30, "sent")  # 30 días TTL
            
            # Actualizar registro de onboarding
            onboarding.last_survey_date = timezone.now()
            onboarding.completed_surveys += 1
            onboarding.save(update_fields=['last_survey_date', 'completed_surveys'])
            
            logger.info(f"Encuesta enviada a {person.first_name} ({period_days} días)")
            return True
            
        except OnboardingProcess.DoesNotExist:
            logger.error(f"Proceso de onboarding {onboarding_id} no encontrado")
            return False
        except Exception as e:
            logger.error(f"Error enviando encuesta: {e}")
            return False
    
    async def process_survey_response(self, 
                                   person_id: int, 
                                   response: str,
                                   question_id: str,
                                   survey_id: str) -> Dict:
        """Procesa la respuesta de una encuesta de satisfacción"""
        try:
            # Obtener IDs del survey_id
            onboarding_id, period_days = map(int, survey_id.split(':'))
            
            # Guardar respuesta
            try:
                onboarding = OnboardingProcess.objects.get(id=onboarding_id)
                
                # Guardar respuesta en modelo
                onboarding.add_response(period_days, question_id, response)
                onboarding.save(update_fields=['survey_responses'])
                
                # También guardar en Redis para acceso rápido
                key = f"{self.redis_prefix}response:{onboarding_id}:{period_days}:{question_id}"
                self.redis.set(
                    key,
                    json.dumps({
                        "value": response,
                        "timestamp": datetime.now().isoformat()
                    }),
                    ex=86400*366  # 1 año + 1 día TTL
                )
                
                # Si es la última pregunta, generar informe y verificar problemas
                if question_id == self.satisfaction_questions[-1]["id"]:
                    await self._check_satisfaction_issues(onboarding_id, period_days)
                    await self._generate_client_report(onboarding_id, period_days)
                    
                return {
                    "success": True, 
                    "message": "Respuesta registrada correctamente"
                }
                
            except OnboardingProcess.DoesNotExist:
                logger.error(f"Proceso de onboarding no encontrado: {onboarding_id}")
                return {"success": False, "error": "Proceso de onboarding no encontrado"}
                
        except Exception as e:
            logger.error(f"Error procesando respuesta: {e}")
            return {"success": False, "error": str(e)}
    
    async def _check_satisfaction_issues(self, onboarding_id: int, period_days: int):
        """Verifica problemas de satisfacción y envía alertas si es necesario"""
        try:
            onboarding = OnboardingProcess.objects.get(id=onboarding_id)
            responses = onboarding.get_responses()
            
            if str(period_days) not in responses:
                return
                
            current_responses = responses[str(period_days)]
            
            # Detectar respuestas negativas
            negative_count = 0
            for q in self.satisfaction_questions:
                q_id = q["id"]
                if q_id in current_responses:
                    response_value = current_responses[q_id]["value"]
                    options = q["options"]
                    
                    # Si la respuesta está en las últimas 2 opciones (negativas)
                    try:
                        option_index = options.index(response_value)
                        if option_index >= len(options) - 2:  # En las últimas 2 opciones
                            negative_count += 1
                    except ValueError:
                        pass
            
            # Si hay suficientes respuestas negativas, enviar alerta
            if negative_count >= 2:
                vacancy = onboarding.vacancy
                
                # Enviar alerta a consultor responsable
                if hasattr(vacancy, 'consultant') and vacancy.consultant:
                    consultant_message = (
                        f"⚠️ ALERTA: El candidato {onboarding.person.first_name} {onboarding.person.last_name} " +
                        f"ha expresado insatisfacción en su encuesta de {period_days} días para " +
                        f"{vacancy.title} en {vacancy.company.name}."
                    )
                    
                    # Enviar por el canal apropiado
                    consultant_channel = getattr(vacancy.consultant, 'preferred_channel', 'email')
                    await self.message_service.send_message(
                        vacancy.consultant.id,
                        consultant_message,
                        consultant_channel
                    )
                    
                    # Almacenar alerta en Redis
                    alert_key = f"{self.redis_prefix}alert:{onboarding_id}:{period_days}"
                    self.redis.set(
                        alert_key,
                        json.dumps({
                            "type": "satisfaction_issue",
                            "negative_count": negative_count,
                            "timestamp": datetime.now().isoformat(),
                            "period_days": period_days
                        }),
                        ex=86400*30  # 30 días TTL
                    )
                    
                    logger.warning(f"Alerta de satisfacción para {onboarding.person.first_name} ({period_days} días)")
                
        except Exception as e:
            logger.error(f"Error verificando problemas de satisfacción: {e}")
    
    async def _generate_client_report(self, onboarding_id: int, period_days: int):
        """Genera reporte para cliente basado en respuestas de encuesta"""
        # Solo generar reporte para períodos clave
        if period_days not in [30, 90, 180, 365]:
            return
            
        try:
            onboarding = OnboardingProcess.objects.get(id=onboarding_id)
            vacancy = onboarding.vacancy
            company = vacancy.company
            
            # Obtener contacto del cliente
            client_email = None
            if hasattr(company, 'client_contact_email') and company.client_contact_email:
                client_email = company.client_contact_email
            elif hasattr(vacancy, 'company_contact_email') and vacancy.company_contact_email:
                client_email = vacancy.company_contact_email
                
            if not client_email:
                logger.warning(f"No hay email de contacto para enviar reporte ({company.name})")
                return
                
            # Generar datos del reporte
            report_data = await self._format_satisfaction_data(onboarding_id)
            
            # Enviar reporte por email
            from app.ats.utils.email_sender import EmailSender
            email_sender = EmailSender()
            
            subject = f"Reporte de satisfacción a {period_days} días - {onboarding.person.first_name} {onboarding.person.last_name}"
            
            # Generar PDF usando template existente
            from app.ats.utils.pdf_generator import generate_pdf
            pdf_file = await generate_pdf(
                'onboarding/satisfaction_report.html',
                {
                    'company': company,
                    'vacancy': vacancy,
                    'person': onboarding.person,
                    'report': report_data,
                    'period': period_days,
                    'date': datetime.now().strftime('%d/%m/%Y')
                }
            )
            
            # Enviar email con reporte
            await email_sender.send_email(
                recipients=[client_email],
                subject=subject,
                template='onboarding/satisfaction_report_email.html',
                context={
                    'company': company,
                    'vacancy': vacancy,
                    'person': onboarding.person,
                    'report': report_data,
                    'period': period_days
                },
                attachments=[
                    {'filename': f'reporte_satisfaccion_{period_days}_dias.pdf', 'content': pdf_file}
                ]
            )
            
            logger.info(f"Reporte enviado a {client_email} para {onboarding.person.first_name} ({period_days} días)")
            
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
    
    async def _format_satisfaction_data(self, onboarding_id: int) -> Dict:
        """Formatea datos de satisfacción para reporte"""
        try:
            onboarding = OnboardingProcess.objects.get(id=onboarding_id)
            responses = onboarding.get_responses()
            
            if not responses:
                return {"satisfaction_score": None, "responses": {}, "no_data": True}
            
            # Obtener todas las respuestas y ordenarlas por período
            periods = sorted([int(p) for p in responses.keys()])
            
            # Preparar datos formateados
            formatted_data = {
                "satisfaction_score": onboarding.get_satisfaction_score(),
                "periods": [],
                "trend": None,
                "responses": {}
            }
            
            # Obtener datos por período
            prev_score = None
            scores = []
            
            for period in periods:
                period_key = str(period)
                period_data = responses[period_key]
                period_score = onboarding.get_satisfaction_score(period)
                
                if period_score is not None:
                    scores.append(period_score)
                
                formatted_data["periods"].append({
                    "days": period,
                    "responses": period_data,
                    "score": period_score
                })
            
            # Calcular tendencia si hay suficientes datos
            if len(scores) >= 2:
                if scores[-1] > scores[-2]:
                    formatted_data["trend"] = "up"
                elif scores[-1] < scores[-2]:
                    formatted_data["trend"] = "down"
                else:
                    formatted_data["trend"] = "stable"
                    
                # Calcular cambio porcentual
                if scores[-2] > 0:
                    change_percent = ((scores[-1] - scores[-2]) / scores[-2]) * 100
                    formatted_data["trend_percent"] = round(change_percent, 1)
            
            # Formatear respuestas para visualización
            question_map = {q["id"]: q for q in self.satisfaction_questions}
            
            for period in periods:
                period_key = str(period)
                if period_key in responses:
                    for question_id, response_data in responses[period_key].items():
                        if question_id in question_map:
                            question = question_map[question_id]["question"]
                            value = response_data["value"]
                            
                            if question_id not in formatted_data["responses"]:
                                formatted_data["responses"][question_id] = {
                                    "question": question,
                                    "values": []
                                }
                            
                            formatted_data["responses"][question_id]["values"].append({
                                "period": period,
                                "value": value
                            })
            
            return formatted_data
            
        except OnboardingProcess.DoesNotExist:
            return {"satisfaction_score": None, "responses": {}, "error": "Proceso no encontrado"}
        except Exception as e:
            logger.error(f"Error formateando datos: {e}")
            return {"satisfaction_score": None, "responses": {}, "error": str(e)}
    
    async def get_satisfaction_trends(self, company_id: int, period: str = '6_months') -> Dict:
        """Obtiene tendencias de satisfacción para una empresa"""
        try:
            # Calcular fecha de inicio según período solicitado
            end_date = timezone.now()
            if period == '1_month':
                start_date = end_date - timedelta(days=30)
            elif period == '3_months':
                start_date = end_date - timedelta(days=90)
            elif period == '6_months':
                start_date = end_date - timedelta(days=180)
            elif period == '1_year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=180)  # Default 6 meses
            
            # Buscar procesos de onboarding para esta empresa en el período
            processes = OnboardingProcess.objects.filter(
                vacancy__company_id=company_id,
                hire_date__gte=start_date,
                hire_date__lte=end_date
            )
            
            # Preparar estructura de datos
            trends = {
                "company_id": company_id,
                "period": period,
                "total_processes": processes.count(),
                "average_score": None,
                "by_period": {},
                "by_position": {}
            }
            
            # Si no hay datos, retornar estructura vacía
            if not processes.exists():
                return trends
            
            # Calcular promedios por período y posición
            positions = {}
            period_data = {}
            all_scores = []
            
            for process in processes:
                # Obtener puntuación global
                score = process.get_satisfaction_score()
                if score is not None:
                    all_scores.append(score)
                    
                    # Agrupar por posición
                    position = process.vacancy.title
                    if position not in positions:
                        positions[position] = []
                    positions[position].append(score)
                    
                    # Agrupar por período
                    responses = process.get_responses()
                    for period_key, period_responses in responses.items():
                        days = int(period_key)
                        if days not in period_data:
                            period_data[days] = []
                        
                        period_score = process.get_satisfaction_score(days)
                        if period_score is not None:
                            period_data[days].append(period_score)
            
            # Calcular promedio general
            if all_scores:
                trends["average_score"] = sum(all_scores) / len(all_scores)
                
            # Calcular promedios por posición
            position_avgs = {}
            for position, scores in positions.items():
                if scores:
                    position_avgs[position] = sum(scores) / len(scores)
            trends["by_position"] = position_avgs
            
            # Calcular promedios por período
            period_avgs = {}
            for days, scores in period_data.items():
                if scores:
                    period_avgs[days] = sum(scores) / len(scores)
            trends["by_period"] = period_avgs
            
            return trends
            
        except Exception as e:
            logger.error(f"Error obteniendo tendencias: {e}")
            return {
                "company_id": company_id,
                "period": period,
                "error": str(e),
                "total_processes": 0
            }
