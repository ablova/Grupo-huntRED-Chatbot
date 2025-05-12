"""
CV Generator module.

This module provides functionality for generating PDF CVs from candidate data.
"""
from .cv_generator import CVGenerator
from .cv_template import CVTemplate
from .cv_utils import CVUtils

__all__ = ['CVGenerator', 'CVTemplate', 'CVUtils']
