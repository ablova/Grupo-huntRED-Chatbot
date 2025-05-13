# /home/pablo/app/com/utils/cv_generator/cv_generator.py
"""
CV Generator class.

This class provides functionality for generating PDF CVs from candidate data.
Includes capability to generate professional development plans.
"""

import os
import logging
from typing import Dict, List, Union, Optional, Tuple
from datetime import datetime
from weasyprint import HTML
from django.conf import settings
from django.template.loader import render_to_string

from .cv_template import CVTemplate
from .cv_utils import CVUtils
from .cv_data import CVData
from app.kanban.ml_integration import get_candidate_growth_data

logger = logging.getLogger(__name__)


class CVGenerator:
    """
    Generates PDF CVs from candidate data.
    """
    
    def __init__(self, template: str = 'modern', include_growth_plan: bool = False):
        """
        Initialize the CVGenerator.
        
        Args:
            template: The template to use for the CV
            include_growth_plan: Whether to include a professional development plan
        """
        self.template = CVTemplate(template)
        self.utils = CVUtils()
        self.include_growth_plan = include_growth_plan
    
    def _prepare_blind_data(self, cv_data: CVData) -> Dict:
        """
        Prepare data for blind CV generation.
        
        Args:
            cv_data: CVData object containing candidate information
            
        Returns:
            Dictionary with blind CV data
        """
        # Convert to dictionary
        data = cv_data.__dict__.copy()
        
        # Generate blind identifier
        data['blind_identifier'] = cv_data.get_blind_identifier()
        
        # Remove sensitive information
        data.pop('contact_info', None)
        data.pop('name', None)
        
        # Remove company names from experience
        if 'experience' in data:
            for exp in data['experience']:
                exp.pop('company', None)
                
        # Remove business unit information
        data.pop('business_unit', None)
        data.pop('business_unit_logo', None)
        
        return data
    
    def generate_cv(self, candidate_data: Union[Dict, CVData], language: str = 'es', blind: bool = False) -> bytes:
        """
        Generate a PDF CV from candidate data.
        
        Args:
            candidate_data: Dictionary or CVData object containing candidate information
            language: Language for the CV (es or en)
            blind: If True, generate a blind CV without personal information
            
        Returns:
            Bytes of the generated PDF
        """
        # Convert to CVData if it's a dictionary
        if isinstance(candidate_data, dict):
            candidate_data = CVData(**candidate_data)
        
        # Set language and dates
        candidate_data.language = language
        candidate_data.cv_creation_date = datetime.now()
        if not hasattr(candidate_data, 'ml_analysis_date') or not candidate_data.ml_analysis_date:
            candidate_data.ml_analysis_date = datetime.now()
        
        # Prepare data for template - use translated data if available
        if hasattr(candidate_data, 'get_translated_data'):
            template_data = candidate_data.get_translated_data()
        else:
            template_data = candidate_data.__dict__.copy()
            
        # If blind CV requested, prepare blind data
        if blind:
            template_data = self._prepare_blind_data(candidate_data)
        
        # Validate and clean data
        cleaned_data = self.utils.clean_candidate_data(template_data)
        
        # Add visual elements if available and not a blind CV
        if not blind:
            if hasattr(cleaned_data, 'get'):
                if cleaned_data.get('personality_test') and hasattr(cleaned_data['personality_test'], 'get_personality_chart'):
                    cleaned_data['personality_chart'] = cleaned_data['personality_test'].get_personality_chart()
                if cleaned_data.get('background_check') and hasattr(cleaned_data['background_check'], 'get_verification_seal'):
                    cleaned_data['verification_seal'] = cleaned_data['background_check'].get_verification_seal()
        
        # URLs provisionales para logos y sellos si no existen
        logo_urls = {
            'huntred_logo_url': 'https://huntred.com/logo.png',  # Logo principal
            'business_unit_logo': f'https://huntred.com/logos/{getattr(cleaned_data, "business_unit", "default")}.png',  # Logo de la BU
            'verification_seal_url': 'https://huntred.com/seals/verification.png',  # Sello de verificación
            'ml_seal_url': 'https://huntred.com/seals/ml.png',  # Sello de ML
            'personality_seal_url': 'https://huntred.com/seals/personality.png'  # Sello de personalidad
        }

        # Add additional data for template
        if hasattr(cleaned_data, '__dict__'):
            template_data = {
                **cleaned_data.__dict__,
                'language': language,
                **logo_urls,
                **self.utils.get_campaign_content()
            }
        else:
            template_data = {
                **cleaned_data,
                'language': language,
                **logo_urls,
                **self.utils.get_campaign_content()
            }
        
        # Generate HTML from template
        html_content = self.template.render(template_data)
        
        # Convert HTML to PDF
        pdf = HTML(string=html_content).write_pdf()
        
        return pdf
    
    def generate_multiple_cvs(self, candidates_data: List[Union[Dict, CVData]], language: str = 'es', blind: bool = False) -> List[bytes]:
        """
        Generate multiple PDF CVs from a list of candidates.
        
        Args:
            candidates_data: List of dictionaries or CVData objects containing candidate information
            language: Language for the CVs (es or en)
            blind: If True, generates blind CVs without contact information
            
        Returns:
            List of bytes for each generated PDF
        """
        return [self.generate_cv(data, language, blind) for data in candidates_data]
    
    def save_cv(self, candidate_data: Union[Dict, CVData], output_path: str, language: str = 'es', blind: bool = False, include_growth_plan: bool = None) -> str:
        """
        Generate and save a CV to a file. Optionally includes a development plan.
        
        Args:
            candidate_data: Dictionary or CVData object containing candidate information
            output_path: Path where to save the PDF
            language: Language for the CV (es or en)
            blind: If True, generates a blind CV without contact information
            include_growth_plan: Whether to include a development plan (overrides instance setting)
            
        Returns:
            Path to the saved PDF file
        """
        # Generate the CV bytes
        pdf = self.generate_cv(candidate_data, language, blind)
        
        # Save the CV to file
        with open(output_path, 'wb') as f:
            f.write(pdf)
        
        # Determine if we should include the growth plan
        should_include_plan = include_growth_plan if include_growth_plan is not None else self.include_growth_plan
        
        # If development plan is enabled and ML features are active, add it
        if should_include_plan and getattr(settings, 'ENABLE_ML_FEATURES', False):
            try:
                # Get candidate Person object from candidate_data
                person = None
                if isinstance(candidate_data, CVData) and hasattr(candidate_data, 'get_person_object'):
                    person = candidate_data.get_person_object()
                elif isinstance(candidate_data, dict) and 'id' in candidate_data:
                    from app.models import Person
                    try:
                        person = Person.objects.get(id=candidate_data['id'])
                    except Person.DoesNotExist:
                        pass
                
                if person:
                    # Generate development plan
                    plan_path = self._generate_development_plan(person, output_path)
                    if plan_path:
                        # Merge the PDFs (CV and development plan)
                        merged_path = self._merge_pdfs(output_path, plan_path, output_path)
                        return merged_path
            except Exception as e:
                logger.error(f"Error adding development plan to CV: {str(e)}")
        
        return output_path
    
    def _generate_development_plan(self, person, output_base_path: str) -> Optional[str]:
        """
        Generate a professional development plan PDF.
        
        Args:
            person: Person object for whom to generate the plan
            output_base_path: Base path for output file
            
        Returns:
            Path to the generated plan PDF, or None if generation failed
        """
        try:
            # Determine output path for the plan
            plan_filename = f"development_plan_{person.id}.pdf"
            plan_path = os.path.join(os.path.dirname(output_base_path), plan_filename)
            
            # Get development plan data for candidate audience
            growth_data = get_candidate_growth_data(person, audience_type='candidate')
            
            # Render template to HTML
            html_string = render_to_string('ml/candidate/growth_plan.html', {
                'candidate': growth_data,
                'for_pdf': True,
                'for_candidate': True,
                'timestamp': self.utils.get_current_date()
            })
            
            # Generate PDF
            HTML(string=html_string).write_pdf(plan_path)
            
            return plan_path
        except Exception as e:
            logger.error(f"Error generating development plan PDF: {str(e)}")
            return None
    
    def _merge_pdfs(self, cv_path: str, plan_path: str, output_base_path: str) -> str:
        """
        Merge CV and development plan PDFs.
        
        Args:
            cv_path: Path to CV PDF
            plan_path: Path to development plan PDF
            output_base_path: Base path for output file
            
        Returns:
            Path to merged PDF
        """
        try:
            from PyPDF2 import PdfMerger
            
            # Create merger object
            merger = PdfMerger()
            
            # Add the PDFs to the merger
            merger.append(cv_path)
            merger.append(plan_path)
            
            # Generate output path for merged file
            merged_filename = os.path.basename(output_base_path).replace('.pdf', '_with_plan.pdf')
            merged_path = os.path.join(os.path.dirname(output_base_path), merged_filename)
            
            # Write to output file
            with open(merged_path, 'wb') as output_file:
                merger.write(output_file)
            
            return merged_path
        except Exception as e:
            logger.error(f"Error merging PDFs: {str(e)}")
            # Return original CV path if merging fails
            return cv_path
