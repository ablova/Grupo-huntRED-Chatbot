"""
Integración optimizada con WhatsApp Business API.
"""

import logging
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import base64
import os

logger = logging.getLogger(__name__)

class WhatsAppBusinessAPI:
    """
    Integración avanzada con WhatsApp Business API.
    """
    
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN')
        
        # Configuración de templates
        self.templates = {
            'candidate_welcome': {
                'name': 'candidate_welcome',
                'language': 'es_MX',
                'components': [
                    {
                        'type': 'header',
                        'text': '¡Bienvenido a huntRED!'
                    },
                    {
                        'type': 'body',
                        'text': 'Hola {{1}}, gracias por tu interés en {{2}}. Te contactaremos pronto.'
                    }
                ]
            },
            'interview_scheduled': {
                'name': 'interview_scheduled',
                'language': 'es_MX',
                'components': [
                    {
                        'type': 'header',
                        'text': 'Entrevista Programada'
                    },
                    {
                        'type': 'body',
                        'text': 'Hola {{1}}, tu entrevista para {{2}} está programada para {{3}} con {{4}}.'
                    }
                ]
            },
            'offer_sent': {
                'name': 'offer_sent',
                'language': 'es_MX',
                'components': [
                    {
                        'type': 'header',
                        'text': 'Propuesta Enviada'
                    },
                    {
                        'type': 'body',
                        'text': 'Hola {{1}}, hemos enviado una propuesta para {{2}}. Revisa tu email.'
                    }
                ]
            },
            'follow_up': {
                'name': 'follow_up',
                'language': 'es_MX',
                'components': [
                    {
                        'type': 'header',
                        'text': 'Seguimiento'
                    },
                    {
                        'type': 'body',
                        'text': 'Hola {{1}}, ¿cómo va todo con tu proceso para {{2}}?'
                    }
                ]
            }
        }
    
    def send_template_message(self, phone_number: str, template_name: str, 
                            parameters: List[str], language: str = 'es_MX') -> Dict:
        """
        Envía mensaje usando template pre-aprobado.
        """
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Preparar componentes del template
            components = []
            if parameters:
                components.append({
                    'type': 'body',
                    'parameters': [
                        {'type': 'text', 'text': param} for param in parameters
                    ]
                })
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': phone_number,
                'type': 'template',
                'template': {
                    'name': template_name,
                    'language': {
                        'code': language
                    },
                    'components': components
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Registrar el envío
            self._log_message_sent(phone_number, template_name, parameters, result)
            
            return {
                'success': True,
                'message_id': result.get('messages', [{}])[0].get('id'),
                'response': result
            }
            
        except Exception as e:
            logger.error(f"Error enviando template message: {str(e)}")
            return {'error': str(e)}
    
    def send_text_message(self, phone_number: str, message: str) -> Dict:
        """
        Envía mensaje de texto simple.
        """
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': phone_number,
                'type': 'text',
                'text': {
                    'body': message
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Registrar el envío
            self._log_message_sent(phone_number, 'text', [message], result)
            
            return {
                'success': True,
                'message_id': result.get('messages', [{}])[0].get('id'),
                'response': result
            }
            
        except Exception as e:
            logger.error(f"Error enviando text message: {str(e)}")
            return {'error': str(e)}
    
    def send_media_message(self, phone_number: str, media_url: str, 
                          media_type: str = 'document', caption: str = None) -> Dict:
        """
        Envía mensaje con archivo adjunto.
        """
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': phone_number,
                'type': media_type,
                media_type: {
                    'link': media_url
                }
            }
            
            if caption:
                payload[media_type]['caption'] = caption
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Registrar el envío
            self._log_message_sent(phone_number, f'{media_type}_media', [media_url], result)
            
            return {
                'success': True,
                'message_id': result.get('messages', [{}])[0].get('id'),
                'response': result
            }
            
        except Exception as e:
            logger.error(f"Error enviando media message: {str(e)}")
            return {'error': str(e)}
    
    def send_interactive_message(self, phone_number: str, message: str, 
                               buttons: List[Dict]) -> Dict:
        """
        Envía mensaje interactivo con botones.
        """
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Preparar botones
            action_buttons = []
            for i, button in enumerate(buttons[:3]):  # Máximo 3 botones
                action_buttons.append({
                    'type': 'reply',
                    'reply': {
                        'id': f'button_{i}',
                        'title': button['title']
                    }
                })
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': phone_number,
                'type': 'interactive',
                'interactive': {
                    'type': 'button',
                    'body': {
                        'text': message
                    },
                    'action': {
                        'buttons': action_buttons
                    }
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Registrar el envío
            self._log_message_sent(phone_number, 'interactive', [message], result)
            
            return {
                'success': True,
                'message_id': result.get('messages', [{}])[0].get('id'),
                'response': result
            }
            
        except Exception as e:
            logger.error(f"Error enviando interactive message: {str(e)}")
            return {'error': str(e)}
    
    def send_candidate_welcome(self, candidate_data: Dict) -> Dict:
        """
        Envía mensaje de bienvenida a candidato.
        """
        try:
            phone_number = candidate_data.get('phone_number')
            candidate_name = candidate_data.get('name', 'Candidato')
            position_title = candidate_data.get('position_title', 'la posición')
            
            return self.send_template_message(
                phone_number=phone_number,
                template_name='candidate_welcome',
                parameters=[candidate_name, position_title]
            )
            
        except Exception as e:
            logger.error(f"Error enviando welcome message: {str(e)}")
            return {'error': str(e)}
    
    def send_interview_scheduled(self, candidate_data: Dict, interview_data: Dict) -> Dict:
        """
        Envía confirmación de entrevista programada.
        """
        try:
            phone_number = candidate_data.get('phone_number')
            candidate_name = candidate_data.get('name', 'Candidato')
            position_title = candidate_data.get('position_title', 'la posición')
            interview_date = interview_data.get('date', 'fecha por confirmar')
            interviewer = interview_data.get('interviewer', 'nuestro equipo')
            
            return self.send_template_message(
                phone_number=phone_number,
                template_name='interview_scheduled',
                parameters=[candidate_name, position_title, interview_date, interviewer]
            )
            
        except Exception as e:
            logger.error(f"Error enviando interview scheduled: {str(e)}")
            return {'error': str(e)}
    
    def send_offer_notification(self, candidate_data: Dict, offer_data: Dict) -> Dict:
        """
        Envía notificación de propuesta enviada.
        """
        try:
            phone_number = candidate_data.get('phone_number')
            candidate_name = candidate_data.get('name', 'Candidato')
            position_title = candidate_data.get('position_title', 'la posición')
            
            return self.send_template_message(
                phone_number=phone_number,
                template_name='offer_sent',
                parameters=[candidate_name, position_title]
            )
            
        except Exception as e:
            logger.error(f"Error enviando offer notification: {str(e)}")
            return {'error': str(e)}
    
    def send_follow_up(self, candidate_data: Dict, days_since_last_contact: int) -> Dict:
        """
        Envía mensaje de seguimiento.
        """
        try:
            phone_number = candidate_data.get('phone_number')
            candidate_name = candidate_data.get('name', 'Candidato')
            position_title = candidate_data.get('position_title', 'tu proceso')
            
            return self.send_template_message(
                phone_number=phone_number,
                template_name='follow_up',
                parameters=[candidate_name, position_title]
            )
            
        except Exception as e:
            logger.error(f"Error enviando follow up: {str(e)}")
            return {'error': str(e)}
    
    def send_cv_to_client(self, client_data: Dict, candidate_data: Dict, cv_url: str) -> Dict:
        """
        Envía CV de candidato al cliente.
        """
        try:
            phone_number = client_data.get('phone_number')
            candidate_name = candidate_data.get('name', 'Candidato')
            position_title = candidate_data.get('position_title', 'la posición')
            
            caption = f"CV de {candidate_name} para {position_title}"
            
            return self.send_media_message(
                phone_number=phone_number,
                media_url=cv_url,
                media_type='document',
                caption=caption
            )
            
        except Exception as e:
            logger.error(f"Error enviando CV: {str(e)}")
            return {'error': str(e)}
    
    def send_quick_actions(self, phone_number: str, message: str, actions: List[str]) -> Dict:
        """
        Envía mensaje con acciones rápidas.
        """
        try:
            buttons = []
            for action in actions:
                buttons.append({'title': action})
            
            return self.send_interactive_message(
                phone_number=phone_number,
                message=message,
                buttons=buttons
            )
            
        except Exception as e:
            logger.error(f"Error enviando quick actions: {str(e)}")
            return {'error': str(e)}
    
    def get_message_status(self, message_id: str) -> Dict:
        """
        Obtiene el estado de un mensaje enviado.
        """
        try:
            url = f"{self.base_url}/{message_id}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error obteniendo status: {str(e)}")
            return {'error': str(e)}
    
    def get_phone_number_info(self) -> Dict:
        """
        Obtiene información del número de teléfono de WhatsApp Business.
        """
        try:
            url = f"{self.base_url}/{self.phone_number_id}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error obteniendo phone info: {str(e)}")
            return {'error': str(e)}
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> str:
        """
        Verifica webhook de WhatsApp Business API.
        """
        try:
            if mode == 'subscribe' and token == self.verify_token:
                logger.info("Webhook verificado exitosamente")
                return challenge
            else:
                logger.error("Verificación de webhook fallida")
                return "Verification failed"
                
        except Exception as e:
            logger.error(f"Error verificando webhook: {str(e)}")
            return "Error"
    
    def process_webhook_message(self, webhook_data: Dict) -> Dict:
        """
        Procesa mensajes recibidos via webhook.
        """
        try:
            if 'entry' not in webhook_data:
                return {'error': 'Invalid webhook data'}
            
            for entry in webhook_data['entry']:
                for change in entry.get('changes', []):
                    if change.get('value', {}).get('messages'):
                        for message in change['value']['messages']:
                            return self._process_incoming_message(message)
            
            return {'success': True, 'message': 'Webhook processed'}
            
        except Exception as e:
            logger.error(f"Error procesando webhook: {str(e)}")
            return {'error': str(e)}
    
    def _process_incoming_message(self, message: Dict) -> Dict:
        """
        Procesa mensaje entrante individual.
        """
        try:
            message_type = message.get('type')
            from_number = message.get('from')
            timestamp = message.get('timestamp')
            
            if message_type == 'text':
                text = message['text']['body']
                return self._handle_text_message(from_number, text, timestamp)
            
            elif message_type == 'interactive':
                interactive = message['interactive']
                if interactive['type'] == 'button_reply':
                    button_id = interactive['button_reply']['id']
                    return self._handle_button_click(from_number, button_id, timestamp)
            
            return {'success': True, 'message': 'Message processed'}
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return {'error': str(e)}
    
    def _handle_text_message(self, from_number: str, text: str, timestamp: int) -> Dict:
        """
        Maneja mensaje de texto entrante.
        """
        try:
            # Aquí puedes implementar lógica de chatbot o routing
            if 'hola' in text.lower():
                return self.send_text_message(
                    from_number, 
                    "¡Hola! Soy el asistente de huntRED. ¿En qué puedo ayudarte?"
                )
            
            elif 'entrevista' in text.lower():
                return self.send_text_message(
                    from_number,
                    "Para programar una entrevista, por favor contacta a tu consultor asignado."
                )
            
            else:
                return self.send_text_message(
                    from_number,
                    "Gracias por tu mensaje. Un consultor te contactará pronto."
                )
                
        except Exception as e:
            logger.error(f"Error manejando texto: {str(e)}")
            return {'error': str(e)}
    
    def _handle_button_click(self, from_number: str, button_id: str, timestamp: int) -> Dict:
        """
        Maneja clic en botón interactivo.
        """
        try:
            if button_id == 'button_0':
                return self.send_text_message(
                    from_number,
                    "Has seleccionado la primera opción. Te contactaremos pronto."
                )
            
            elif button_id == 'button_1':
                return self.send_text_message(
                    from_number,
                    "Has seleccionado la segunda opción. Te contactaremos pronto."
                )
            
            else:
                return self.send_text_message(
                    from_number,
                    "Opción no reconocida. Te contactaremos pronto."
                )
                
        except Exception as e:
            logger.error(f"Error manejando botón: {str(e)}")
            return {'error': str(e)}
    
    def _log_message_sent(self, phone_number: str, message_type: str, 
                         parameters: List, response: Dict):
        """
        Registra mensaje enviado para analytics.
        """
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'phone_number': phone_number,
                'message_type': message_type,
                'parameters': parameters,
                'response': response,
                'success': 'error' not in response
            }
            
            # Aquí puedes guardar en base de datos o archivo
            logger.info(f"Message sent: {log_entry}")
            
        except Exception as e:
            logger.error(f"Error logging message: {str(e)}")
    
    def get_usage_statistics(self, start_date: datetime = None, end_date: datetime = None) -> Dict:
        """
        Obtiene estadísticas de uso de WhatsApp Business API.
        """
        try:
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # En producción, esto vendría de la base de datos
            # Aquí simulamos estadísticas
            stats = {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'messages_sent': 1250,
                'messages_delivered': 1180,
                'messages_read': 950,
                'delivery_rate': 94.4,
                'read_rate': 76.0,
                'templates_used': {
                    'candidate_welcome': 450,
                    'interview_scheduled': 300,
                    'offer_sent': 200,
                    'follow_up': 300
                },
                'cost_estimate': 25.0  # USD estimado
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {'error': str(e)} 