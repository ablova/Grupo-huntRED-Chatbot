# /home/pablo/app/admin/config.py
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Configuración de filtros y columnas para el admin
ADMIN_CONFIG = {
    'Vacante': {
        'list_display': (
            'titulo', 'empresa', 'ubicacion', 'modalidad', 'activa', 
            'business_unit', 'fecha_publicacion', 'url_original',
            'vacantes_restantes', 'procesamiento_count'
        ),
        'list_filter': (
            'activa', 'modalidad', 'dominio_origen', 'business_unit',
            'fecha_publicacion', 'procesamiento_count'
        ),
        'search_fields': ('titulo', 'empresa', 'ubicacion', 'descripcion'),
        'date_hierarchy': 'fecha_publicacion',
        'list_select_related': ('empresa', 'business_unit'),
    },
    'Application': {
        'list_display': (
            'user', 'vacancy', 'status', 'applied_at', 'updated_at',
            'business_unit', 'job_title'
        ),
        'list_filter': (
            'status', 'vacancy__business_unit', 'applied_at',
            'vacancy__titulo'
        ),
        'search_fields': (
            'user__nombre', 'vacancy__titulo', 'vacancy__empresa__nombre'
        ),
        'list_select_related': ('user', 'vacancy', 'vacancy__empresa'),
    },
    'Person': {
        'list_display': (
            'nombre', 'apellido_paterno', 'email', 'phone',
            'job_search_status', 'fecha_creacion', 'points'
        ),
        'list_filter': (
            'job_search_status', 'preferred_language', 'fecha_creacion',
            'points'
        ),
        'search_fields': (
            'nombre', 'apellido_paterno', 'email', 'phone'
        ),
        'list_select_related': ('current_stage',),
    },
    'ChatState': {
        'list_display': (
            'user_id', 'platform', 'applied', 'interviewed',
            'last_interaction_at', 'current_stage'
        ),
        'list_filter': (
            'platform', 'applied', 'interviewed', 'last_interaction_at'
        ),
        'search_fields': ('user_id', 'platform'),
        'list_select_related': ('current_stage',),
    },
    'UserInteractionLog': {
        'list_display': (
            'user_id', 'platform', 'business_unit', 'timestamp',
            'message_direction', 'interaction_type'
        ),
        'list_filter': (
            'platform', 'business_unit', 'timestamp',
            'message_direction', 'interaction_type'
        ),
        'search_fields': ('user_id', 'message'),
        'date_hierarchy': 'timestamp',
    },
}

# Funciones de ayuda para el admin
def get_date_ranges():
    """Devuelve rangos de fechas para filtros"""
    today = datetime.now()
    return {
        'today': (today, today),
        'this_week': (today - timedelta(days=7), today),
        'this_month': (today.replace(day=1), today),
        'last_month': (
            (today.replace(day=1) - timedelta(days=1)).replace(day=1),
            today.replace(day=1) - timedelta(days=1)
        )
    }
