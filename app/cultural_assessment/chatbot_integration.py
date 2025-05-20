"""
Integración del sistema de análisis cultural con el chatbot de Grupo huntRED®.

Este módulo proporciona las funciones necesarias para que el chatbot pueda
realizar evaluaciones culturales durante conversaciones con candidatos,
siguiendo las reglas globales de eficiencia y bajo uso de CPU.
"""

import logging
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.urls import reverse
from app.models import (
    CulturalAssessment, OrganizationalCulture, CulturalDimension, 
    CulturalValue, CulturalProfile, Person, BusinessUnit, Organization, Application, Vacante
)
from app.utils.cache import cache_result
from app.chatbot.conversation_state import ConversationState
from app.utils.common import generate_unique_token

logger = logging.getLogger(__name__)

class CulturalChatbotHandler:
    """
    Maneja la integración del análisis cultural con el chatbot.
    Optimizado para bajo consumo de CPU y respuestas rápidas.
    """

    def __init__(self, conversation_state: ConversationState):
        """
        Inicializa el manejador con el estado actual de conversación.
        
        Args:
            conversation_state: Estado actual de la conversación del chatbot
        """
        self.state = conversation_state
        self.person = None
        self.application = None
        self.organization = None
        self.assessment = None
        self._initialize_context()
    
    def _initialize_context(self):
        """Inicializa el contexto de la conversación recuperando los datos necesarios"""
        try:
            # Recuperar persona
            if self.state.person_id:
                self.person = Person.objects.get(id=self.state.person_id)
            
            # Recuperar aplicación si existe
            if self.state.application_id:
                self.application = Application.objects.select_related(
                    'vacante', 'vacante__organization', 'vacante__business_unit'
                ).get(id=self.state.application_id)
                
                if self.application and self.application.vacante:
                    self.organization = self.application.vacante.organization
        except Exception as e:
            logger.error(f"Error inicializando contexto cultural: {str(e)}")
    
    @cache_result(prefix="cultural_dimensions", timeout=3600)
    def get_available_dimensions(self, business_unit_id=None, limit=5):
        """
        Obtiene dimensiones culturales disponibles para evaluación.
        
        Args:
            business_unit_id: ID de la unidad de negocio
            limit: Número máximo de dimensiones a devolver
            
        Returns:
            list: Lista de dimensiones culturales
        """
        try:
            # Si no se especifica unidad de negocio pero hay aplicación, usar esa
            if not business_unit_id and self.application and self.application.vacante:
                business_unit_id = self.application.vacante.business_unit_id
            
            # Construir query base
            query = CulturalDimension.objects.filter(active=True)
            
            # Filtrar por unidad de negocio si está disponible
            if business_unit_id:
                query = query.filter(business_unit_id=business_unit_id)
            
            # Obtener dimensiones optimizando para bajo uso de CPU
            dimensions = query.order_by('category', 'name')[:limit]
            
            # Formatear resultados
            result = []
            for dim in dimensions:
                # Obtener algunos valores de ejemplo para cada dimensión
                values = CulturalValue.objects.filter(
                    dimension=dim, 
                    active=True
                ).order_by('?')[:2]  # Limitar y ordenar aleatoriamente
                
                result.append({
                    'id': dim.id,
                    'name': dim.name,
                    'category': dim.category,
                    'description': dim.description,
                    'sample_values': [
                        {
                            'id': val.id,
                            'name': val.name,
                            'statement': val.positive_statement
                        } for val in values
                    ]
                })
            
            return result
        except Exception as e:
            logger.error(f"Error obteniendo dimensiones culturales: {str(e)}")
            return []
    
    def start_cultural_assessment(self, business_unit_id=None):
        """
        Inicia una evaluación cultural como parte de una conversación de chatbot.
        
        Args:
            business_unit_id: ID de la unidad de negocio
            
        Returns:
            dict: Información para iniciar la evaluación
        """
        try:
            # Verificar si tenemos la información necesaria
            if not self.person:
                return {
                    'success': False,
                    'message': "No se encontró información de la persona"
                }
            
            # Determinar la organización y unidad de negocio
            organization = self.organization
            business_unit = None
            
            # Si hay una aplicación, usar esos datos
            if self.application and self.application.vacante:
                organization = self.application.vacante.organization
                business_unit = self.application.vacante.business_unit
            
            # Si se proporcionó business_unit_id, buscarla
            elif business_unit_id:
                try:
                    business_unit = BusinessUnit.objects.get(id=business_unit_id)
                    # Si no hay organización, usar una predeterminada asociada a la BU
                    if not organization:
                        organization = Organization.objects.filter(
                            business_unit=business_unit
                        ).first()
                except BusinessUnit.DoesNotExist:
                    logger.error(f"No se encontró unidad de negocio con ID {business_unit_id}")
            
            if not organization or not business_unit:
                return {
                    'success': False,
                    'message': "No se pudo determinar la organización o unidad de negocio"
                }
            
            # Buscar u obtener perfil cultural organizacional
            org_culture, _ = OrganizationalCulture.objects.get_or_create(
                organization=organization,
                business_unit=business_unit,
                is_current=True,
                defaults={
                    'status': 'in_progress',
                    'completion_percentage': 0
                }
            )
            
            # Crear o actualizar evaluación cultural
            with transaction.atomic():
                assessment, created = CulturalAssessment.objects.get_or_create(
                    person=self.person,
                    organization=organization,
                    organizational_culture=org_culture,
                    defaults={
                        'business_unit': business_unit,
                        'status': 'in_progress',
                        'completion_percentage': 0,
                        'started_at': timezone.now(),
                        'last_interaction': timezone.now(),
                        'expiration_date': timezone.now() + timedelta(days=7)
                    }
                )
                
                # Si ya existía pero no estaba en progreso, actualizarla
                if not created and assessment.status not in ['in_progress', 'completed']:
                    assessment.status = 'in_progress'
                    assessment.started_at = timezone.now()
                    assessment.last_interaction = timezone.now()
                    assessment.save()
                
                # Generar token si no existe
                if not assessment.invitation_token:
                    assessment.generate_invitation_token()
                
                # Guardar referencia en el estado de conversación
                self.assessment = assessment
                self.state.cultural_assessment_id = assessment.id
                self.state.save()
            
            # Obtener dimensiones para evaluar
            dimensions = self.get_available_dimensions(business_unit.id)
            
            return {
                'success': True,
                'assessment_id': assessment.id,
                'token': assessment.invitation_token,
                'dimensions': dimensions,
                'introduction': (
                    f"Ahora me gustaría conocer un poco más sobre tus valores y preferencias "
                    f"culturales para entender mejor cómo te alineas con "
                    f"{organization.name if self.application else 'nuestras organizaciones clientes'}."
                )
            }
        except Exception as e:
            logger.exception(f"Error iniciando evaluación cultural: {str(e)}")
            return {
                'success': False,
                'message': f"Error iniciando evaluación cultural: {str(e)}"
            }
    
    def process_dimension_response(self, dimension_id, response_value):
        """
        Procesa una respuesta del usuario a una dimensión cultural.
        
        Args:
            dimension_id: ID de la dimensión cultural
            response_value: Valor de respuesta (1-5)
            
        Returns:
            dict: Resultado del procesamiento
        """
        try:
            # Verificar que tengamos una evaluación activa
            if not self.assessment or not hasattr(self, 'assessment') or self.assessment.status != 'in_progress':
                return {
                    'success': False,
                    'message': "No hay una evaluación cultural activa"
                }
            
            # Validar valor de respuesta
            try:
                response_value = float(response_value)
                if response_value < 1 or response_value > 5:
                    raise ValueError("El valor debe estar entre 1 y 5")
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'message': "El valor de respuesta debe ser un número entre 1 y 5"
                }
            
            # Recuperar la dimensión
            try:
                dimension = CulturalDimension.objects.get(id=dimension_id)
            except CulturalDimension.DoesNotExist:
                return {
                    'success': False,
                    'message': f"Dimensión con ID {dimension_id} no encontrada"
                }
            
            # Actualizar los datos de evaluación
            assessment_data = self.assessment.assessment_data or {}
            dimensions_scores = self.assessment.dimensions_scores or {}
            
            # Inicializar si no existe
            if 'responses' not in assessment_data:
                assessment_data['responses'] = {}
            
            # Guardar respuesta
            assessment_data['responses'][str(dimension_id)] = {
                'value': response_value,
                'timestamp': timezone.now().isoformat(),
                'dimension_name': dimension.name,
                'dimension_category': dimension.category
            }
            
            # Actualizar puntaje de dimensión
            dimensions_scores[str(dimension_id)] = response_value
            
            # Calcular porcentaje de completitud
            total_dimensions = CulturalDimension.objects.filter(
                business_unit=self.assessment.business_unit, 
                active=True
            ).count()
            
            if total_dimensions > 0:
                completion_percentage = (len(dimensions_scores) / total_dimensions) * 100
                # Limitar al 100%
                completion_percentage = min(completion_percentage, 100)
            else:
                completion_percentage = 0
            
            # Actualizar la evaluación
            self.assessment.assessment_data = assessment_data
            self.assessment.dimensions_scores = dimensions_scores
            self.assessment.completion_percentage = completion_percentage
            self.assessment.last_interaction = timezone.now()
            
            # Si se completó la evaluación
            if completion_percentage >= 100:
                self.assessment.status = 'completed'
                self.assessment.completed_at = timezone.now()
                
                # Calcular factor de riesgo básico (ejemplo simplificado)
                # En un sistema real, esto usaría algoritmos más complejos
                risk_scores = []
                for dim_id, score in dimensions_scores.items():
                    # Mayor riesgo para valores extremos
                    deviation = abs(score - 3.0)  # Distancia desde el punto medio
                    risk = (deviation / 2.0) * 100  # Escalar a porcentaje
                    risk_scores.append(risk)
                
                # Promedio de factores de riesgo
                if risk_scores:
                    self.assessment.risk_factor = sum(risk_scores) / len(risk_scores)
                
                # Actualizar perfil cultural
                self.assessment.update_profile()
            
            self.assessment.save()
            
            # Si se completó, retornar mensaje de cierre
            if self.assessment.status == 'completed':
                return {
                    'success': True,
                    'completed': True,
                    'completion_percentage': completion_percentage,
                    'message': (
                        "¡Gracias por completar la evaluación cultural! "
                        "Estos datos nos ayudarán a entender mejor cómo te alineas con las "
                        "organizaciones y equipos con los que trabajamos."
                    )
                }
            
            # Si aún no se completa, buscar la siguiente dimensión no respondida
            next_dimension = CulturalDimension.objects.filter(
                business_unit=self.assessment.business_unit,
                active=True
            ).exclude(
                id__in=[int(d) for d in dimensions_scores.keys()]
            ).order_by('category', 'name').first()
            
            if next_dimension:
                # Obtener valores para la siguiente dimensión
                values = CulturalValue.objects.filter(
                    dimension=next_dimension, 
                    active=True
                ).order_by('?')[:2]
                
                return {
                    'success': True,
                    'completed': False,
                    'completion_percentage': completion_percentage,
                    'next_dimension': {
                        'id': next_dimension.id,
                        'name': next_dimension.name,
                        'category': next_dimension.category,
                        'description': next_dimension.description,
                        'sample_values': [
                            {
                                'id': val.id,
                                'name': val.name,
                                'statement': val.positive_statement
                            } for val in values
                        ]
                    }
                }
            else:
                # No hay más dimensiones por responder
                self.assessment.status = 'completed'
                self.assessment.completed_at = timezone.now()
                self.assessment.save()
                
                # Actualizar perfil cultural
                self.assessment.update_profile()
                
                return {
                    'success': True,
                    'completed': True,
                    'completion_percentage': 100,
                    'message': (
                        "¡Gracias por completar la evaluación cultural! "
                        "Estos datos nos ayudarán a entender mejor cómo te alineas con las "
                        "organizaciones y equipos con los que trabajamos."
                    )
                }
        except Exception as e:
            logger.exception(f"Error procesando respuesta cultural: {str(e)}")
            return {
                'success': False,
                'message': f"Error procesando respuesta: {str(e)}"
            }
    
    def get_assessment_progress(self):
        """
        Obtiene el progreso actual de la evaluación cultural.
        
        Returns:
            dict: Información de progreso
        """
        try:
            # Verificar si hay una evaluación activa
            if not self.assessment:
                if self.state.cultural_assessment_id:
                    try:
                        self.assessment = CulturalAssessment.objects.get(
                            id=self.state.cultural_assessment_id
                        )
                    except CulturalAssessment.DoesNotExist:
                        return {
                            'success': False,
                            'message': "No se encontró la evaluación cultural"
                        }
                else:
                    return {
                        'success': False,
                        'message': "No hay una evaluación cultural activa"
                    }
            
            return {
                'success': True,
                'assessment_id': self.assessment.id,
                'status': self.assessment.status,
                'completion_percentage': self.assessment.completion_percentage,
                'started_at': self.assessment.started_at,
                'completed_at': self.assessment.completed_at,
                'dimensions_answered': len(self.assessment.dimensions_scores or {})
            }
        except Exception as e:
            logger.exception(f"Error obteniendo progreso de evaluación: {str(e)}")
            return {
                'success': False,
                'message': f"Error obteniendo progreso: {str(e)}"
            }
    
    def get_cultural_profile_summary(self):
        """
        Obtiene un resumen del perfil cultural del candidato.
        
        Returns:
            dict: Resumen del perfil cultural
        """
        try:
            # Verificar si tenemos la información necesaria
            if not self.person:
                return {
                    'success': False,
                    'message': "No se encontró información de la persona"
                }
            
            try:
                # Buscar perfil cultural
                profile = CulturalProfile.objects.get(person=self.person)
            except CulturalProfile.DoesNotExist:
                return {
                    'success': False,
                    'message': "La persona no tiene un perfil cultural"
                }
            
            # Generar resumen
            summary = {
                'success': True,
                'person_name': f"{self.person.first_name} {self.person.last_name}",
                'scores': {
                    'values': profile.values_score,
                    'motivators': profile.motivators_score,
                    'interests': profile.interests_score,
                    'work_style': profile.work_style_score,
                    'social_impact': profile.social_impact_score,
                    'generational_values': profile.generational_values_score
                },
                'strengths': profile.strengths[:3] if hasattr(profile, 'strengths') and profile.strengths else [],
                'improvement_areas': profile.areas_of_improvement[:3] if hasattr(profile, 'areas_of_improvement') and profile.areas_of_improvement else [],
                'leadership_potential': profile.leadership_potential if hasattr(profile, 'leadership_potential') else None,
                'risk_factor': profile.risk_factor if hasattr(profile, 'risk_factor') else None
            }
            
            # Añadir compatibilidad con la organización actual si está disponible
            if self.application and self.application.vacante and self.application.vacante.organization:
                org = self.application.vacante.organization
                if profile.compatibility_data and str(org.id) in profile.compatibility_data:
                    summary['organization_compatibility'] = {
                        'organization_name': org.name,
                        'score': profile.compatibility_data[str(org.id)],
                        'level': profile.get_cultural_fit_level(org.id)
                    }
            
            return summary
        except Exception as e:
            logger.exception(f"Error obteniendo resumen cultural: {str(e)}")
            return {
                'success': False,
                'message': f"Error obteniendo resumen cultural: {str(e)}"
            }


# Funciones auxiliares para ser utilizadas en el chatbot

def start_cultural_evaluation(conversation_state):
    """
    Inicia una evaluación cultural durante una conversación.
    
    Args:
        conversation_state: Estado de la conversación
        
    Returns:
        dict: Información para iniciar la evaluación
    """
    handler = CulturalChatbotHandler(conversation_state)
    return handler.start_cultural_assessment()

def process_cultural_answer(conversation_state, dimension_id, answer_value):
    """
    Procesa una respuesta de evaluación cultural.
    
    Args:
        conversation_state: Estado de la conversación
        dimension_id: ID de la dimensión cultural
        answer_value: Valor de respuesta (1-5)
        
    Returns:
        dict: Resultado del procesamiento
    """
    handler = CulturalChatbotHandler(conversation_state)
    return handler.process_dimension_response(dimension_id, answer_value)

def get_cultural_profile(conversation_state):
    """
    Obtiene el perfil cultural de un candidato.
    
    Args:
        conversation_state: Estado de la conversación
        
    Returns:
        dict: Resumen del perfil cultural
    """
    handler = CulturalChatbotHandler(conversation_state)
    return handler.get_cultural_profile_summary()

def format_cultural_question(dimension):
    """
    Formatea una pregunta de evaluación cultural para el chatbot.
    
    Args:
        dimension: Diccionario con información de la dimensión
        
    Returns:
        str: Texto formateado para el chatbot
    """
    if not dimension:
        return None
    
    sample_statements = ""
    if 'sample_values' in dimension and dimension['sample_values']:
        for value in dimension['sample_values']:
            sample_statements += f"• {value['statement']}\n"
    
    return (
        f"Con respecto a la dimensión '{dimension['name']}' ({dimension['category']}):\n\n"
        f"{dimension['description']}\n\n"
        f"Ejemplos de valores en esta dimensión:\n{sample_statements}\n"
        f"En una escala del 1 al 5, donde 1 es 'Nada importante' y 5 es 'Extremadamente importante', "
        f"¿qué tan importante es esta dimensión para ti en un ambiente laboral?"
    )
