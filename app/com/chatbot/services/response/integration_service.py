from django.conf import settings
from django.db import models
from django.utils import timezone
import json
from config import API_CONFIG
from models import Company, Person, BusinessUnit

class IntegrationService:
    def __init__(self):
        self.api_config = API_CONFIG

    def get_company_data(self, company_id):
        """Obtiene datos de diferentes fuentes"""
        data = {
            'aomni': self._get_aomni_data(company_id),
            'linkedin': self._get_linkedin_data(company_id),
            'chatbot': self._get_chatbot_data(company_id)
        }
        return data

    def _get_aomni_data(self, company_id):
        """Integración con AOMNI.ai"""
        if not self.api_config['AOMNI_AI']['ENABLED']:
            return None
        
        # Cuando tengamos el SDK, implementar la llamada a AOMNI.ai
        return {
            'strategies': [],
            'value_propositions': []
        }

    def _get_linkedin_data(self, company_id):
        """Integración con LinkedIn"""
        company = Company.objects.get(id=company_id)
        linkedin_data = {
            'profile_info': {
                'size': company.size,
                'industry': company.industry,
                'location': company.location
            },
            'connections': self._get_company_connections(company)
        }
        return linkedin_data

    def _get_chatbot_data(self, company_id):
        """Integración con datos del chatbot"""
        company = Company.objects.get(id=company_id)
        chatbot_data = {
            'interests': self._get_company_interests(company),
            'preferences': self._get_contact_preferences(company)
        }
        return chatbot_data

    def _get_company_connections(self, company):
        """Obtiene conexiones LinkedIn relevantes"""
        return list(company.key_contacts.values('linkedin_url', 'position'))

    def _get_company_interests(self, company):
        """Obtiene intereses expresados en el chatbot"""
        return list(company.opportunity_analyses.values('value_proposition'))

    def _get_contact_preferences(self, company):
        """Obtiene preferencias de contacto"""
        return list(company.key_contacts.values('preferred_language', 'communication_preferences'))
