"""
URL configuration for the chatbot app.

This module includes all URL patterns for the chatbot application.
"""

from django.urls import path, include

# Import all URL modules
from . import assessment_urls

# URL patterns
urlpatterns = [
    # Include assessment URLs
    path('', include(assessment_urls)),
]
