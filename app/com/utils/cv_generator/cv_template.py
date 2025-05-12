"""
CV Template class.

This class provides functionality for rendering CV templates.
"""

from typing import Dict, Optional
from jinja2 import Environment, FileSystemLoader
import os
from pathlib import Path


class CVTemplate:
    """
    Renders CV templates using Jinja2.
    """
    
    def __init__(self):
        """
        Initialize the CVTemplate.
        """
        self.env = Environment(
            loader=FileSystemLoader(self._get_template_dir()),
            autoescape=True
        )
        
    def _get_template_dir(self) -> str:
        """
        Get the directory containing CV templates.
        """
        return str(Path(__file__).parent / 'templates')
        
    def render(self, data: Dict, template_name: Optional[str] = None) -> str:
        """
        Render a CV template with the given data.
        
        Args:
            data: Dictionary containing CV data
            template_name: Name of the template to use (optional)
            
        Returns:
            Rendered HTML as string
        """
        template_name = template_name or data.get('template', 'modern')
        template = self.env.get_template(f'{template_name}.html')
        return template.render(data)
