"""
CV Generator class.

This class provides functionality for generating PDF CVs from candidate data.
"""

from typing import Dict, List, Union, Optional
from weasyprint import HTML
from .cv_template import CVTemplate
from .cv_utils import CVUtils
from .cv_data import CVData


class CVGenerator:
    """
    Generates PDF CVs from candidate data.
    """
    
    def __init__(self, template: str = 'modern'):
        """
        Initialize the CVGenerator.
        
        Args:
            template: The template to use for the CV
        """
        self.template = CVTemplate(template)
        self.utils = CVUtils()
        
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
            Bytes of the generated PDF file
        """
        # If input is a dictionary, convert to CVData
        if isinstance(candidate_data, dict):
            candidate_data = CVData(**candidate_data)
        
        # Set language
        candidate_data.language = language
        
        # Set dates
        candidate_data.cv_creation_date = datetime.now()
        if not candidate_data.ml_analysis_date:
            candidate_data.ml_analysis_date = datetime.now()
        
        # Prepare data for template
        template_data = candidate_data.get_translated_data()
        
        # If blind CV, prepare blind data
        if blind:
            template_data = self._prepare_blind_data(candidate_data)
        
        # Validate and clean data
        cleaned_data = self.utils.clean_candidate_data(template_data)
        
        # Add visual elements
        if not blind:
            if cleaned_data.get('personality_test'):
                cleaned_data['personality_chart'] = cleaned_data['personality_test'].get_personality_chart()
            if cleaned_data.get('background_check'):
                cleaned_data['verification_seal'] = cleaned_data['background_check'].get_verification_seal()
        
        # Generate HTML from template
        html_content = self.template.render(cleaned_data, template)
        
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

    def save_cv(self, candidate_data: Union[Dict, CVData], output_path: str, language: str = 'es', blind: bool = False) -> None:
        """
        Generate and save a CV to a file.
        
        Args:
            candidate_data: Dictionary or CVData object containing candidate information
            output_path: Path where to save the PDF
            language: Language for the CV (es or en)
            blind: If True, generates a blind CV without contact information
        """
        pdf = self.generate_cv(candidate_data, language, blind)
        with open(output_path, 'wb') as f:
            f.write(pdf)


class CVGenerator:
    """
    Generates PDF CVs from candidate data.
    """
    
    def __init__(self, template: str = 'modern'):
        """
        Initialize the CVGenerator.
        
        Args:
            template: The template to use for the CV
        """
        self.template = CVTemplate(template)
        self.utils = CVUtils()
        
    def generate_cv(self, candidate_data: Union[Dict, CVData], language: str = 'es') -> bytes:
        """
        Generate a PDF CV from candidate data.
        
        Args:
            candidate_data: Dictionary or CVData object containing candidate information
            language: Language for the CV (es or en)
            
        Returns:
            Bytes of the generated PDF
        """
        # Convert to CVData if it's a dictionary
        if isinstance(candidate_data, dict):
            candidate_data = CVData(**candidate_data)
            
        # Validate and clean data
        cleaned_data = self.utils.clean_candidate_data(candidate_data)
        
        # URLs provisionales para logos y sellos
        logo_urls = {
            'huntred_logo_url': 'https://huntred.com/logo.png',  # Logo principal
            'business_unit_logo': f'https://huntred.com/logos/{cleaned_data.business_unit}.png',  # Logo de la BU
            'verification_seal_url': 'https://huntred.com/seals/verification.png',  # Sello de verificación
            'ml_seal_url': 'https://huntred.com/seals/ml.png',  # Sello de ML
            'personality_seal_url': 'https://huntred.com/seals/personality.png'  # Sello de personalidad
        }

        # Add additional data for template
        template_data = {
            **cleaned_data,
            'language': language,
            **logo_urls,
            **self.utils.get_campaign_content()
        }
        
        # Generate HTML from template
        html_content = self.template.render(template_data)
        
        # Convert HTML to PDF
        if blind:
            # Add script to convert to blind CV
            html_content = f"""
            <script>
                convertToBlindCV();
            </script>
            {html_content}
            """
        
        pdf = HTML(string=html_content).write_pdf()
        
        return pdf

    def generate_multiple_cvs(self, candidates_data: List[Union[Dict, CVData]], language: str = 'es') -> List[bytes]:
        """
        Generate multiple PDF CVs from a list of candidates.
        
        Args:
            candidates_data: List of dictionaries or CVData objects containing candidate information
            language: Language for the CVs (es or en)
            
        Returns:
            List of bytes for each generated PDF
        """
        return [self.generate_cv(data, language) for data in candidates_data]

    def save_cv(self, candidate_data: Union[Dict, CVData], output_path: str, language: str = 'es') -> None:
        """
        Generate and save a CV to a file.
        
        Args:
            candidate_data: Dictionary or CVData object containing candidate information
            output_path: Path where to save the PDF
            language: Language for the CV (es or en)
        """
        pdf = self.generate_cv(candidate_data, language)
        with open(output_path, 'wb') as f:
            f.write(pdf)
