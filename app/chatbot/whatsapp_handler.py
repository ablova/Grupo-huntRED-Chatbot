from typing import Dict, Any, Optional, List
from django.conf import settings
from django.utils import timezone
from app.models import (
    Person, BusinessUnit, Application, Interview,
    WhatsAppAPI, MetaAPI, ConfiguracionBU
)
from app.chatbot.chat_state_manager import ChatStateManager
from app.chatbot.intents_handler import IntentProcessor
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class WhatsAppHandler:
    """Manejador de interacciones de WhatsApp para el chatbot."""
    
    def __init__(self, phone_number: str, business_unit: BusinessUnit):
        self.phone_number = phone_number
        self.business_unit = business_unit
        self.user: Optional[Person] = None
        self.chat_manager: Optional[ChatStateManager] = None
        self.intent_processor: Optional[IntentProcessor] = None
        
    async def initialize(self):
        """Inicializa el manejador de WhatsApp."""
        try:
            # Obtener o crear el usuario
            self.user = await self._get_or_create_user()
            
            # Inicializar el manejador de estados de chat
            self.chat_manager = ChatStateManager(self.user, self.business_unit)
            await self.chat_manager.initialize()
            
            # Inicializar el procesador de intents
            self.intent_processor = IntentProcessor(self.user)
            
            return True
        except Exception as e:
            logger.error(f"Error inicializando WhatsAppHandler: {str(e)}")
            raise
    
    async def handle_message(self, message: str) -> Dict[str, Any]:
        """Procesa un mensaje de WhatsApp y genera una respuesta."""
        try:
            # Verificar si es spam
            if await self._is_spam_message(message):
                return {
                    'response': "Por favor, no envíes mensajes repetidos o spam."
                }
            
            # Procesar el mensaje y obtener el intent
            result = await self.chat_manager.process_message(message)
            
            # Obtener la respuesta basada en el intent
            response = await self._get_response(result)
            
            # Generar respuesta para WhatsApp
            whatsapp_response = await self._generate_whatsapp_response(response)
            
            return whatsapp_response
        except Exception as e:
            logger.error(f"Error procesando mensaje de WhatsApp: {str(e)}")
            return {
                'response': "Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta nuevamente."
            }
    
    async def _get_or_create_user(self) -> Person:
        """Obtiene o crea un usuario basado en el número de teléfono."""
        try:
            user = await Person.objects.aget_or_create(
                phone=self.phone_number,
                defaults={
                    'nombre': 'Usuario de WhatsApp',
                    'preferred_language': 'es_MX'
                }
            )
            
            return user
        except Exception as e:
            logger.error(f"Error obteniendo/creando usuario: {str(e)}")
            raise
    
    async def _is_spam_message(self, message: str) -> bool:
        """Verifica si un mensaje es considerado spam."""
        try:
            # Verificar mensaje repetido
            if await self.chat_manager._check_message_history(message):
                return True
                
            # Verificar frecuencia de mensajes
            if await self.chat_manager._check_message_frequency():
                return True
                
            return False
        except Exception as e:
            logger.error(f"Error verificando spam: {str(e)}")
            return False
    
    async def _get_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene la respuesta basada en el intent y el estado."""
        try:
            intent = result.get('intent')
            state = result.get('state')
            context = result.get('context')
            
            # Procesar el intent
            response = await self.intent_processor.process_intent(
                intent=intent,
                message=result.get('analysis', {}).get('text', '')
            )
            
            # Personalizar la respuesta según el estado
            response = await self._customize_response(
                response=response,
                state=state,
                context=context
            )
            
            return response
        except Exception as e:
            logger.error(f"Error obteniendo respuesta: {str(e)}")
            return {
                'response': "Lo siento, no pude procesar tu solicitud. Por favor, intenta nuevamente."
            }
    
    async def _customize_response(self, response: Dict[str, Any], state: str, context: Dict) -> Dict[str, Any]:
        """Personaliza la respuesta según el estado y contexto."""
        try:
            # Añadir botones inteligentes según el estado
            smart_options = await self._get_smart_options(state, context)
            response['smart_options'] = smart_options
            
            # Añadir plantillas de mensaje según el estado
            template_messages = await self._get_template_messages(state, context)
            response['template_messages'] = template_messages
            
            # Personalizar el texto según el contexto
            response['response'] = await self._personalize_text(
                response['response'],
                context
            )
            
            return response
        except Exception as e:
            logger.error(f"Error personalizando respuesta: {str(e)}")
            return response
    
    async def _get_smart_options(self, state: str, context: Dict) -> List[Dict]:
        """Obtiene las opciones inteligentes según el estado y contexto."""
        try:
            options = []
            
            if state == 'PROFILE':
                options.extend([
                    {
                        'text': 'Actualizar experiencia',
                        'data': {'action': 'update_experience'}
                    },
                    {
                        'text': 'Actualizar habilidades',
                        'data': {'action': 'update_skills'}
                    }
                ])
            elif state == 'SEARCH':
                options.extend([
                    {
                        'text': 'Ver detalles de la vacante',
                        'data': {'action': 'view_vacancy'}
                    },
                    {
                        'text': 'Postularme',
                        'data': {'action': 'apply'}
                    }
                ])
            elif state == 'APPLY':
                options.extend([
                    {
                        'text': 'Ver estado de mi aplicación',
                        'data': {'action': 'view_status'}
                    },
                    {
                        'text': 'Actualizar perfil',
                        'data': {'action': 'update_profile'}
                    }
                ])
            
            return options
        except Exception as e:
            logger.error(f"Error obteniendo opciones inteligentes: {str(e)}")
            return []
    
    async def _get_template_messages(self, state: str, context: Dict) -> List[Dict]:
        """Obtiene las plantillas de mensaje según el estado y contexto."""
        try:
            templates = []
            
            if state == 'SEARCH':
                # Obtener recomendaciones de vacantes
                recommendations = await self._get_vacancy_recommendations(context)
                for rec in recommendations:
                    templates.append({
                        'title': rec.title,
                        'description': rec.description[:100],
                        'footer': f"{rec.location} • {rec.required_experience} años exp",
                        'buttons': [
                            {
                                'type': 'quick_reply',
                                'text': 'Postular',
                                'payload': json.dumps({
                                    'action': 'apply',
                                    'vacancy_id': rec.id
                                })
                            }
                        ]
                    })
            
            return templates
        except Exception as e:
            logger.error(f"Error obteniendo plantillas: {str(e)}")
            return []
    
    async def _personalize_text(self, text: str, context: Dict) -> str:
        """Personaliza el texto de la respuesta según el contexto."""
        try:
            # Reemplazar variables de contexto
            for key, value in context.items():
                if isinstance(value, str):
                    text = text.replace(f"{{{{{key}}}}}", value)
            
            # Añadir información relevante
            if 'vacancy' in context:
                text = text.replace("{vacancy_title}", context['vacancy'].title)
                text = text.replace("{vacancy_location}", context['vacancy'].location)
            
            return text
        except Exception as e:
            logger.error(f"Error personalizando texto: {str(e)}")
            return text
    
    async def _generate_whatsapp_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Genera la respuesta en formato WhatsApp."""
        try:
            # Preparar el mensaje principal
            whatsapp_response = {
                'type': 'text',
                'text': response['response']
            }
            
            # Añadir botones inteligentes
            if response.get('smart_options'):
                whatsapp_response['buttons'] = [
                    {
                        'type': 'quick_reply',
                        'text': option['text'],
                        'payload': json.dumps(option['data'])
                    } for option in response['smart_options']
                ]
            
            # Añadir plantillas de mensaje
            if response.get('template_messages'):
                whatsapp_response['templates'] = response['template_messages']
            
            return whatsapp_response
        except Exception as e:
            logger.error(f"Error generando respuesta de WhatsApp: {str(e)}")
            return {
                'type': 'text',
                'text': "Lo siento, hubo un error al generar la respuesta."
            }
    
    async def _get_vacancy_recommendations(self, context: Dict) -> List[Dict]:
        """Obtiene recomendaciones de vacantes basadas en el contexto."""
        try:
            # Obtener habilidades del contexto
            skills = context.get('entities', {}).get('skills', [])
            
            # Obtener ubicación del contexto
            location = context.get('entities', {}).get('location')
            
            # Obtener experiencia del contexto
            experience = context.get('entities', {}).get('experience')
            
            # Obtener vacantes recomendadas
            recommendations = await self._get_recommended_vacancies(
                skills=skills,
                location=location,
                experience=experience
            )
            
            return recommendations
        except Exception as e:
            logger.error(f"Error obteniendo recomendaciones: {str(e)}")
            return []
    
    async def _get_recommended_vacancies(self, skills: List[str], location: str, experience: str) -> List[Dict]:
        """Obtiene vacantes recomendadas basadas en habilidades, ubicación y experiencia."""
        try:
            # Obtener vacantes activas
            vacancies = await Vacante.objects.filter(
                activa=True,
                business_unit=self.business_unit
            ).aall()
            
            # Filtrar por ubicación
            if location:
                vacancies = [v for v in vacancies if v.ubicacion == location]
            
            # Filtrar por experiencia
            if experience:
                vacancies = [v for v in vacancies if v.experience_years <= experience]
            
            # Calcular puntuación para cada vacante
            scored_vacancies = []
            for vacancy in vacancies:
                score = 0
                
                # Puntuar por habilidades
                if skills:
                    common_skills = set(skills) & set(vacancy.skills_required)
                    score += len(common_skills) * 0.6
                
                # Puntuar por ubicación
                if location and location == vacancy.ubicacion:
                    score += 0.3
                
                # Puntuar por experiencia
                if experience and experience <= vacancy.experience_years:
                    score += 0.1
                
                scored_vacancies.append((vacancy, score))
            
            # Ordenar por puntuación y tomar las mejores
            scored_vacancies.sort(key=lambda x: x[1], reverse=True)
            return [v[0] for v in scored_vacancies[:3]]
        except Exception as e:
            logger.error(f"Error obteniendo vacantes recomendadas: {str(e)}")
            return []
