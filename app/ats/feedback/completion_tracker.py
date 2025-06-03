# /home/pablo/app/com/feedback/completion_tracker.py
"""
Sistema de seguimiento y retroalimentación para servicios concluidos.

Este módulo permite:
1. Enviar encuestas automáticas al concluir los servicios
2. Recolectar evaluaciones finales de los clientes sobre el servicio prestado
3. Obtener testimoniales para uso en marketing
4. Identificar oportunidades de cross-selling y upselling
5. Medir la satisfacción general y el NPS (Net Promoter Score)
"""
from typing import Dict, List, Optional, Union
import asyncio
from datetime import datetime, timedelta
import json
import logging
import secrets
import uuid

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
import redis
import requests

from app.models import Opportunity, ServiceContract, Company, Contact
from app.ats.feedback.feedback_models import ServiceFeedback, CompletedServiceFeedback, ServiceImprovementSuggestion

logger = logging.getLogger(__name__)

class ServiceCompletionTracker:
    """
    Gestiona el seguimiento y retroalimentación de servicios concluidos.
    
    Envía encuestas al finalizar los servicios para evaluar la satisfacción general,
    obtener testimoniales y detectar oportunidades de venta cruzada.
    """
    
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.redis_prefix = "completion_tracker:"
        
        # Calendario.com API para Pablo (configurable desde settings)
        self.calendly_url = getattr(settings, "MANAGING_DIRECTOR_CALENDAR_URL", 
                                  "https://huntred.com/agenda-pllh/")
        
        # Preguntas predefinidas - enfocadas en evaluación final
        self.completion_questions = [
            {
                "id": "objectives_met",
                "question": "¿En qué medida se cumplieron los objetivos del servicio?",
                "options": ["5 - Completamente", "4 - En gran parte", "3 - Parcialmente", "2 - Mínimamente", "1 - No se cumplieron"],
                "type": "scale"
            },
            {
                "id": "value_perception",
                "question": "¿Cómo percibe la relación calidad-precio del servicio?",
                "options": [
                    "excellent - Excelente relación calidad-precio",
                    "good - Buena relación calidad-precio",
                    "fair - Relación calidad-precio aceptable",
                    "poor - Relación calidad-precio deficiente",
                    "overpriced - Precio excesivo para el valor recibido"
                ],
                "type": "radio"
            },
            {
                "id": "recommendation_likelihood",
                "question": "¿Qué tan probable es que recomiende Grupo huntRED® a un colega o amigo?",
                "options": ["0 - Nada probable", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10 - Extremadamente probable"],
                "type": "nps"
            },
            {
                "id": "consultant_evaluation",
                "question": "¿Cómo evaluaría al consultor/equipo que gestionó su servicio?",
                "options": ["5 - Excelente", "4 - Bueno", "3 - Aceptable", "2 - Deficiente", "1 - Muy deficiente"],
                "type": "scale"
            },
            {
                "id": "best_aspects",
                "question": "¿Cuáles fueron los aspectos más destacados del servicio?",
                "type": "text"
            },
            {
                "id": "areas_for_improvement",
                "question": "¿Qué aspectos podríamos mejorar?",
                "type": "text"
            },
            {
                "id": "interested_in_other_services",
                "question": "¿Estaría interesado en conocer otros servicios de Grupo huntRED®?",
                "options": ["Sí", "No"],
                "type": "radio"
            },
            {
                "id": "services_of_interest",
                "question": "¿Qué otros servicios le interesaría conocer?",
                "options": [
                    "Análisis de Talento 360°",
                    "Reclutamiento Especializado",
                    "Búsqueda de Ejecutivos",
                    "Consultoría de HR",
                    "Outplacement",
                    "Capacitación"
                ],
                "allow_multiple": True,
                "type": "checkbox"
            },
            {
                "id": "new_services_suggestion",
                "question": "¿Qué servicios adicionales le gustaría que Grupo huntRED® ofreciera?",
                "type": "text"
            },
            {
                "id": "testimonial",
                "question": "¿Le gustaría proporcionar un breve testimonial sobre su experiencia con Grupo huntRED®?",
                "type": "text",
                "placeholder": "Su opinión es muy valiosa para nosotros y para futuros clientes."
            },
            {
                "id": "allow_public_testimonial",
                "question": "¿Nos autoriza a utilizar su testimonio en nuestro sitio web y materiales promocionales?",
                "options": ["Sí", "No"],
                "type": "radio"
            },
            {
                "id": "meeting_request",
                "question": "¿Desea hablar directamente con nuestro Managing Director?",
                "description": "Reserve una reunión personal con Pablo Lelo de Larrea H. - Sr. Managing Partner Grupo huntRED® para discutir cualquier aspecto del servicio o explorar futuras colaboraciones.",
                "button_text": "Agendar Reunión",
                "type": "meeting_request"
            }
        ]
    
    def generate_feedback_token(self, opportunity_id: int) -> str:
        """Genera un token único para identificar respuestas de retroalimentación."""
        token = secrets.token_urlsafe(32)
        # Guardar relación token-oportunidad en Redis por 90 días
        token_key = f"{self.redis_prefix}token:{token}"
        self.redis.set(token_key, str(opportunity_id), ex=60*60*24*90)  # 90 días
        return token
    
    async def schedule_completion_feedback(self, opportunity_id: int, delay_days: int = 3, 
                                         contact_email: str = None):
        """
        Programa una solicitud de retroalimentación para ser enviada después de
        un número específico de días tras la conclusión del servicio.
        """
        try:
            # Obtener datos de la oportunidad
            opportunity = Opportunity.objects.get(id=opportunity_id)
            
            # Verificar si el servicio ha concluido
            contract = getattr(opportunity, 'service_contract', None)
            
            if not contract or not hasattr(contract, 'status') or contract.status != 'completed':
                logger.warning(f"No se puede programar evaluación final: Servicio {opportunity_id} no concluido")
                return False
            
            # Obtener información de contacto
            company = opportunity.company
            contact_email = contact_email or (opportunity.contact.email if opportunity.contact else None)
            
            if not contact_email:
                logger.warning(f"No se puede programar evaluación final: Oportunidad {opportunity_id} sin email de contacto")
                return False
            
            # Generar token único para esta solicitud
            token = self.generate_feedback_token(opportunity_id)
            
            # Guardar programación en Redis
            schedule_key = f"{self.redis_prefix}scheduled:{opportunity_id}"
            schedule_data = {
                "opportunity_id": opportunity_id,
                "token": token,
                "company_name": company.name,
                "contact_email": contact_email,
                "service_type": opportunity.service_type,
                "send_after": (timezone.now() + timedelta(days=delay_days)).isoformat(),
                "status": "scheduled"
            }
            
            self.redis.set(schedule_key, json.dumps(schedule_data), ex=60*60*24*90)  # 90 días
            
            logger.info(f"Retroalimentación de conclusión programada para servicio ID:{opportunity_id}")
            return True
            
        except Opportunity.DoesNotExist:
            logger.error(f"No se encontró la oportunidad con ID {opportunity_id}")
            return False
        except Exception as e:
            logger.error(f"Error al programar evaluación final: {str(e)}")
            return False
    
    async def send_completion_feedback_requests(self):
        """
        Busca evaluaciones finales programadas que deban enviarse hoy y las envía.
        Esta función debería ejecutarse diariamente mediante una tarea programada.
        """
        now = timezone.now()
        pattern = f"{self.redis_prefix}scheduled:*"
        
        # Buscar todas las programaciones en Redis
        for key in self.redis.scan_iter(match=pattern):
            try:
                data = json.loads(self.redis.get(key))
                
                # Verificar si ya es hora de enviar
                send_after = datetime.fromisoformat(data["send_after"])
                if now < send_after or data["status"] != "scheduled":
                    continue
                
                # Enviar solicitud de retroalimentación
                success = await self._send_feedback_email(data)
                
                # Actualizar estado
                if success:
                    data["status"] = "sent"
                    data["sent_at"] = now.isoformat()
                    self.redis.set(key, json.dumps(data), ex=60*60*24*90)  # 90 días más
                    logger.info(f"Enviada evaluación final para servicio {data['opportunity_id']}")
            except Exception as e:
                logger.error(f"Error procesando clave de Redis {key}: {str(e)}")
    
    async def _send_feedback_email(self, data: Dict) -> bool:
        """Envía email de solicitud de evaluación final."""
        try:
            opportunity_id = data["opportunity_id"]
            token = data["token"]
            company_name = data["company_name"]
            contact_email = data["contact_email"]
            service_type = data.get("service_type", "")
            
            # Obtener nombre del servicio para el asunto
            service_name = "nuestro servicio"
            if service_type == "talent_analysis":
                service_name = "Análisis de Talento 360°"
            elif service_type == "recruitment":
                service_name = "Reclutamiento Especializado"
            elif service_type == "executive_search":
                service_name = "Búsqueda de Ejecutivos"
            
            # Generar URL única para retroalimentación
            feedback_url = f"{settings.SITE_URL}{reverse('feedback:completion_feedback', args=[token])}"
            
            # Preparar email
            context = {
                "opportunity_id": opportunity_id,
                "token": token,
                "company_name": company_name, 
                "service_name": service_name,
                "feedback_url": feedback_url,
                "feedback_questions": self.completion_questions,
                "managing_director_calendar": self.calendly_url
            }
            
            subject = f"Evaluación final de {service_name} - Grupo huntRED®"
            html_message = render_to_string("emails/completion_feedback_request.html", context)
            text_message = render_to_string("emails/completion_feedback_request.txt", context)
            
            # Enviar email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contact_email],
                html_message=html_message,
                fail_silently=False
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar evaluación final: {str(e)}")
            return False
    
    async def process_feedback(self, token: str, feedback_data: Dict) -> Optional[ServiceFeedback]:
        """
        Procesa la evaluación final recibida de un cliente y la almacena 
        para análisis posterior.
        """
        # Validar token
        token_key = f"{self.redis_prefix}token:{token}"
        opportunity_id = self.redis.get(token_key)
        
        if not opportunity_id:
            logger.warning(f"Token inválido o expirado: {token}")
            return None
        
        try:
            opportunity_id = int(opportunity_id)
            opportunity = Opportunity.objects.get(id=opportunity_id)
            
            # Determinar si ya existe un feedback para esta oportunidad
            try:
                existing_feedback = ServiceFeedback.objects.get(
                    opportunity=opportunity,
                    stage='completed',
                    token=token
                )
                # Actualizar existente
                base_feedback = existing_feedback
                base_feedback.rating = feedback_data.get("rating", feedback_data.get("objectives_met"))
                base_feedback.comments = feedback_data.get("comments", feedback_data.get("best_aspects"))
                base_feedback.suggested_services = feedback_data.get("new_services_suggestion")
                base_feedback.meeting_requested = feedback_data.get("meeting_requested", False)
                base_feedback.save()
                
                # Actualizar la parte específica
                completed_feedback = base_feedback.completed_feedback
                
            except ServiceFeedback.DoesNotExist:
                # Crear nuevo feedback base
                base_feedback = ServiceFeedback(
                    opportunity=opportunity,
                    company=opportunity.company,
                    stage='completed',
                    service_type=opportunity.service_type,
                    token=token,
                    contact_name=opportunity.contact.name if opportunity.contact else "Cliente",
                    contact_email=opportunity.contact.email if opportunity.contact else "",
                    company_name=opportunity.company.name,
                    rating=feedback_data.get("rating", feedback_data.get("objectives_met")),
                    comments=feedback_data.get("comments", feedback_data.get("best_aspects")),
                    suggested_services=feedback_data.get("new_services_suggestion"),
                    meeting_requested=feedback_data.get("meeting_requested", False)
                )
                base_feedback.save()
                
                # Crear la parte específica
                completed_feedback = CompletedServiceFeedback(
                    base_feedback=base_feedback
                )
            
            # Actualizar datos específicos de evaluación final
            completed_feedback.objectives_met = feedback_data.get("objectives_met")
            completed_feedback.value_perception = feedback_data.get("value_perception")
            completed_feedback.recommendation_likelihood = feedback_data.get("recommendation_likelihood")
            completed_feedback.consultant_evaluation = feedback_data.get("consultant_evaluation")
            completed_feedback.best_aspects = feedback_data.get("best_aspects")
            completed_feedback.areas_for_improvement = feedback_data.get("areas_for_improvement")
            
            # Interés en otros servicios
            completed_feedback.interested_in_other_services = feedback_data.get("interested_in_other_services") == "Sí"
            completed_feedback.services_of_interest = ", ".join(feedback_data.get("services_of_interest", []))
            
            # Testimonial
            testimonial = feedback_data.get("testimonial")
            if testimonial and len(testimonial.strip()) > 10:
                completed_feedback.testimonial_provided = True
                completed_feedback.testimonial_text = testimonial
                completed_feedback.allow_public_testimonial = feedback_data.get("allow_public_testimonial") == "Sí"
            
            completed_feedback.save()
            
            # Si se solicitó una reunión, crear la solicitud
            if base_feedback.meeting_requested:
                self._create_meeting_request(base_feedback, feedback_data)
            
            # Si hay sugerencias de nuevos servicios, registrarlas
            new_services = feedback_data.get("new_services_suggestion")
            if new_services and len(new_services.strip()) > 10:
                self._register_service_suggestion(base_feedback, new_services)
            
            # Si proporcionó un testimonial, agradecerlo
            if completed_feedback.testimonial_provided:
                self._send_testimonial_thank_you(base_feedback)
            
            # Si mostró interés en otros servicios, notificar al equipo comercial
            if completed_feedback.interested_in_other_services:
                self._notify_sales_opportunity(base_feedback, completed_feedback.services_of_interest)
            
            logger.info(f"Procesada evaluación final para servicio {opportunity_id}")
            return base_feedback
            
        except Exception as e:
            logger.error(f"Error al procesar evaluación final: {str(e)}")
            return None
    
    def _create_meeting_request(self, feedback: ServiceFeedback, feedback_data: Dict):
        """Crea una solicitud de reunión con el Managing Director."""
        # Esta función se implementó anteriormente en el sistema de feedback de propuestas
        pass
    
    def _register_service_suggestion(self, feedback: ServiceFeedback, suggestion_text: str):
        """Registra una sugerencia de nuevo servicio para análisis posterior."""
        try:
            # Crear registro de sugerencia
            suggestion = ServiceImprovementSuggestion(
                feedback=feedback,
                suggestion_type='new_service',
                title=f"Sugerencia de nuevo servicio - {feedback.company_name}",
                description=suggestion_text,
                status='new'
            )
            suggestion.save()
            
            logger.info(f"Registrada sugerencia de nuevo servicio desde feedback {feedback.id}")
            
        except Exception as e:
            logger.error(f"Error al registrar sugerencia de nuevo servicio: {str(e)}")
    
    def _send_testimonial_thank_you(self, feedback: ServiceFeedback):
        """Envía un agradecimiento por proporcionar un testimonial."""
        try:
            # Preparar email de agradecimiento
            subject = "Gracias por su testimonial - Grupo huntRED®"
            message = (
                f"Estimado/a {feedback.contact_name},\n\n"
                f"Queremos agradecerle sinceramente por tomarse el tiempo de compartir su experiencia con Grupo huntRED®.\n\n"
                f"Los testimonios como el suyo son extremadamente valiosos para nosotros y nos ayudan a mejorar constantemente nuestros servicios.\n\n"
                f"Ha sido un placer trabajar con {feedback.company_name} y esperamos tener la oportunidad de colaborar nuevamente en el futuro.\n\n"
                f"Si en algún momento necesita cualquier otro servicio de recursos humanos, no dude en contactarnos.\n\n"
                f"Atentamente,\n\n"
                f"Pablo Lelo de Larrea H.\n"
                f"Sr. Managing Partner\n"
                f"Grupo huntRED®"
            )
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[feedback.contact_email],
                fail_silently=False
            )
            
            logger.info(f"Email de agradecimiento por testimonial enviado para feedback {feedback.id}")
            
        except Exception as e:
            logger.error(f"Error al enviar agradecimiento por testimonial: {str(e)}")
    
    def _notify_sales_opportunity(self, feedback: ServiceFeedback, services_of_interest: str):
        """Notifica al equipo comercial sobre una oportunidad de venta cruzada."""
        try:
            # Determinar responsable comercial
            sales_email = None
            if hasattr(feedback.opportunity, 'assigned_to') and feedback.opportunity.assigned_to:
                sales_email = feedback.opportunity.assigned_to.email
            
            # Si no hay responsable asignado, enviar al Director Comercial o MD
            if not sales_email:
                sales_email = getattr(settings, "SALES_DIRECTOR_EMAIL", 
                                   getattr(settings, "MANAGING_DIRECTOR_EMAIL", "pablo@huntred.com"))
            
            # Enviar notificación
            subject = f"✅ Oportunidad de venta cruzada - {feedback.company_name}"
            message = (
                f"Se ha detectado una oportunidad de venta cruzada para {feedback.company_name}.\n\n"
                f"El cliente ha expresado interés en los siguientes servicios:\n{services_of_interest}\n\n"
                f"Detalles del cliente:\n"
                f"Contacto: {feedback.contact_name}\n"
                f"Email: {feedback.contact_email}\n"
                f"Servicio actual: {feedback.get_service_type_display()}\n\n"
                f"Se recomienda contactar al cliente en los próximos días para presentarle los servicios de su interés.\n\n"
                f"Puede ver todos los detalles de esta retroalimentación en el panel de administración."
            )
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[sales_email],
                fail_silently=False
            )
            
            logger.info(f"Notificación de oportunidad de venta cruzada enviada para feedback {feedback.id}")
            
        except Exception as e:
            logger.error(f"Error al enviar notificación de oportunidad de venta cruzada: {str(e)}")
    
    async def trigger_completion_feedback(self, opportunity_id: int, delay_days: int = 3):
        """
        Dispara una solicitud de evaluación final para un servicio concluido.
        
        Esta función puede ser llamada cuando se marca un servicio como completado
        en el sistema, ya sea manualmente o automáticamente.
        """
        return await self.schedule_completion_feedback(
            opportunity_id=opportunity_id,
            delay_days=delay_days
        )
    
    async def generate_insights_report(self, start_date: datetime, end_date: datetime, 
                                     service_type: str = None) -> Dict:
        """
        Genera un informe de insights basado en las evaluaciones finales
        en un periodo específico.
        """
        # Filtrar feedback
        query = ServiceFeedback.objects.filter(
            stage='completed',
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        if service_type:
            query = query.filter(service_type=service_type)
        
        feedbacks = query.select_related('completed_feedback')
        
        if not feedbacks.exists():
            return {"error": "No hay datos para el período seleccionado"}
        
        # Estadísticas básicas
        total = feedbacks.count()
        
        # Métricas principales
        avg_ratings = {
            "objectives_met": 0,
            "consultant_evaluation": 0
        }
        
        # NPS
        promoters = 0
        passives = 0
        detractors = 0
        
        # Testimoniales
        testimonials_count = 0
        public_testimonials = 0
        featured_testimonials = []
        
        # Oportunidades de venta cruzada
        cross_sell_opportunities = 0
        interested_services = {}
        
        for feedback in feedbacks:
            completed = getattr(feedback, 'completed_feedback', None)
            if not completed:
                continue
                
            # Calificaciones
            if completed.objectives_met:
                avg_ratings["objectives_met"] += completed.objectives_met
            if completed.consultant_evaluation:
                avg_ratings["consultant_evaluation"] += completed.consultant_evaluation
            
            # NPS
            if completed.recommendation_likelihood is not None:
                if completed.recommendation_likelihood >= 9:
                    promoters += 1
                elif completed.recommendation_likelihood >= 7:
                    passives += 1
                else:
                    detractors += 1
            
            # Testimoniales
            if completed.testimonial_provided:
                testimonials_count += 1
                if completed.allow_public_testimonial:
                    public_testimonials += 1
                    
                    # Añadir a destacados si tiene buen NPS y es público
                    if completed.recommendation_likelihood and completed.recommendation_likelihood >= 9:
                        featured_testimonials.append({
                            "company": feedback.company_name,
                            "text": completed.testimonial_text[:200] + "..." if len(completed.testimonial_text) > 200 else completed.testimonial_text,
                            "rating": completed.recommendation_likelihood
                        })
            
            # Oportunidades de venta cruzada
            if completed.interested_in_other_services:
                cross_sell_opportunities += 1
                
                # Contar servicios de interés
                if completed.services_of_interest:
                    for service in completed.services_of_interest.split(','):
                        service = service.strip()
                        if service:
                            interested_services[service] = interested_services.get(service, 0) + 1
        
        # Calcular promedios
        for key in avg_ratings:
            avg_ratings[key] = round(avg_ratings[key] / total, 1) if total > 0 else 0
        
        # Calcular NPS
        nps_score = 0
        if (promoters + passives + detractors) > 0:
            nps_score = int(((promoters - detractors) / (promoters + passives + detractors)) * 100)
        
        # Ordenar servicios de interés
        top_services = sorted(interested_services.items(), key=lambda x: x[1], reverse=True)
        
        # Recomendaciones basadas en datos
        recommendations = []
        if avg_ratings["objectives_met"] < 4.0:
            recommendations.append("El cumplimiento de objetivos está por debajo del nivel deseado. Revisar procesos de definición y seguimiento de objetivos con clientes.")
        
        if nps_score < 30:
            recommendations.append("El NPS es bajo. Implementar un programa de mejora de experiencia del cliente para aumentar el número de promotores.")
        
        return {
            "period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            },
            "total_feedbacks": total,
            "average_ratings": avg_ratings,
            "nps": {
                "score": nps_score,
                "promoters": promoters,
                "promoters_percentage": (promoters / total) * 100 if total > 0 else 0,
                "passives": passives,
                "passives_percentage": (passives / total) * 100 if total > 0 else 0,
                "detractors": detractors,
                "detractors_percentage": (detractors / total) * 100 if total > 0 else 0
            },
            "testimonials": {
                "total": testimonials_count,
                "percentage": (testimonials_count / total) * 100 if total > 0 else 0,
                "public": public_testimonials,
                "featured": featured_testimonials[:3]  # Top 3 testimonios
            },
            "cross_selling": {
                "opportunities": cross_sell_opportunities,
                "percentage": (cross_sell_opportunities / total) * 100 if total > 0 else 0,
                "top_services": [{"name": s[0], "count": s[1]} for s in top_services[:5]]  # Top 5 servicios
            },
            "recommendations": recommendations
        }


# Función para inicializar el tracker
def get_service_completion_tracker():
    """Obtiene una instancia del ServiceCompletionTracker."""
    return ServiceCompletionTracker()
