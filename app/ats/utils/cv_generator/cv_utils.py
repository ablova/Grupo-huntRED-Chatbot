# /home/pablo/app/com/utils/cv_generator/cv_utils.py
"""
CV Utilities module.

This module provides utility functions for CV generation.
"""

from typing import Dict, List
import re
from datetime import datetime


from django.utils import timezone
from app.ats.publish.models import Campaign

class CVUtils:
    """
    Provides utility functions for CV generation.
    """
    
    def __init__(self):
        self.active_campaign = self._get_active_campaign()
        
    def _get_active_campaign(self):
        """
        Obtiene la campaña activa actual
        """
        try:
            return Campaign.objects.filter(
                status='active',
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            ).order_by('-created_at').first()
        except Campaign.DoesNotExist:
            return None
    
    def get_campaign_content(self):
        """
        Obtiene el contenido dinámico de la campaña activa
        """
        if not self.active_campaign:
            return {
                'market_study_url': 'https://huntred.com/estudio-mercado',
                'pricing_url': 'https://huntred.com/precios',
                'contact_url': 'https://huntred.com/contacto',
                'linkedin_url': 'https://linkedin.com/company/huntred',
                'campaign_name': 'Grupo huntRED',
                'campaign_description': 'Campaña estándar',
                'last_updated': timezone.now()
            }
            
        return {
            'market_study_url': self.active_campaign.blind_content.get('market_study_url', 'https://huntred.com/estudio-mercado'),
            'pricing_url': self.active_campaign.blind_content.get('pricing_url', 'https://huntred.com/precios'),
            'contact_url': self.active_campaign.blind_content.get('contact_url', 'https://huntred.com/contacto'),
            'linkedin_url': self.active_campaign.blind_content.get('linkedin_url', 'https://linkedin.com/company/huntred'),
            'campaign_name': self.active_campaign.name,
            'campaign_description': self.active_campaign.description,
            'last_updated': self.active_campaign.last_updated or timezone.now()
        }
    
    def clean_candidate_data(self, data: Dict) -> Dict:
        """
        Clean and validate candidate data.
        
        Args:
            data: Dictionary containing candidate information
            
        Returns:
            Cleaned and validated data
        """
        cleaned_data = {}
        
        # Clean name
        cleaned_data['name'] = self._clean_name(data.get('name', ''))
        
        # Clean contact information
        cleaned_data['email'] = self._clean_email(data.get('email', ''))
        cleaned_data['phone'] = self._clean_phone(data.get('phone', ''))
        
        # Clean dates
        cleaned_data['birth_date'] = self._clean_date(data.get('birth_date'))
        
        # Clean experience
        cleaned_data['experience'] = self._clean_experience(data.get('experience', []))
        
        # Clean education
        cleaned_data['education'] = self._clean_education(data.get('education', []))
        
        # Add URLs for blind CV
        cleaned_data['market_study_url'] = self.urls['market_study']
        cleaned_data['pricing_url'] = self.urls['pricing']
        cleaned_data['contact_url'] = self.urls['contact']
        cleaned_data['linkedin_url'] = self.urls['linkedin']
        
        return cleaned_data
    
    def _clean_name(self, name: str) -> str:
        """
        Clean and validate a name.
        """
        return re.sub(r'[^a-zA-Z\s]', '', name).strip()
    
    def _clean_email(self, email: str) -> str:
        """
        Clean and validate an email address.
        """
        email = email.strip().lower()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return ''
        return email
    
    def _clean_phone(self, phone: str) -> str:
        """
        Clean and validate a phone number.
        """
        return re.sub(r'[^0-9]', '', phone)
    
    def _clean_date(self, date_str: str) -> str:
        """
        Clean and validate a date string.
        """
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %Y')
        except (ValueError, TypeError):
            return ''
    
    def _clean_experience(self, experience: List[Dict]) -> List[Dict]:
        """
        Clean and validate work experience entries.
        """
        cleaned = []
        for exp in experience:
            if all(key in exp for key in ['company', 'position', 'start_date']):
                cleaned.append({
                    'company': self._clean_name(exp['company']),
                    'position': self._clean_name(exp['position']),
                    'start_date': self._clean_date(exp['start_date']),
                    'end_date': self._clean_date(exp.get('end_date', '')),
                    'description': exp.get('description', '')
                })
        return cleaned
    
    def _clean_education(self, education: List[Dict]) -> List[Dict]:
        """
        Clean and validate education entries.
        """
        cleaned = []
        for edu in education:
            if all(key in edu for key in ['institution', 'degree', 'start_date']):
                cleaned.append({
                    'institution': self._clean_name(edu['institution']),
                    'degree': self._clean_name(edu['degree']),
                    'start_date': self._clean_date(edu['start_date']),
                    'end_date': self._clean_date(edu.get('end_date', '')),
                    'description': edu.get('description', '')
                })
        return cleaned
