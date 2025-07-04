"""
🚀 GhuntRED-v2 Frontend URLs
Catch-all URLs for React Router SPA
"""

from django.urls import path, re_path
from django.views.generic import TemplateView

urlpatterns = [
    # Catch-all pattern for React Router
    re_path(r'^.*$', TemplateView.as_view(template_name='frontend/index.html'), name='frontend'),
]