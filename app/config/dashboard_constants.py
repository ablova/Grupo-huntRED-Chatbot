"""
Módulo de constantes para el dashboard.

Este módulo contiene todas las constantes y configuraciones utilizadas en el dashboard.

Constantes:
    DASHBOARD_COLORS: Colores para el dashboard
    ALERT_THRESHOLDS: Umbral para alertas
    STATS_TIMEFRAMES: Tiempos para estadísticas
    APPLICATION_STATUS: Estados de aplicación
    VACANCY_STATUS: Estados de vacante
    TASK_PRIORITIES: Prioridades para tareas
    INTEGRATION_STATUS: Estados de integración
    ALERT_TYPES: Tipos de alerta
    SALARY_RANGES: Rangos de salario
    EDUCATION_LEVELS: Niveles educativos
    SKILL_CATEGORIES: Categorías de habilidades
    GAMIFICATION_STATES: Estados de gamificación
    ACHIEVEMENT_TYPES: Tipos de logro
    SUCCESS_METRICS: Métricas de éxito
    PROCESS_STATES: Estados de proceso
    NOTIFICATION_TYPES: Tipos de notificación
"""

from datetime import timedelta

# Colores para el dashboard
"""
Colores utilizados en el dashboard para diferentes estados y elementos.
"""
DASHBOARD_COLORS = {
    'primary': '#2563eb',      # Azul principal más vibrante
    'success': '#10b981',      # Verde para éxitos
    'warning': '#f59e0b',      # Amarillo para advertencias
    'danger': '#ef4444',       # Rojo para errores
    'info': '#3b82f6',         # Azul más claro para información
    'light': '#f8fafc',        # Gris claro para elementos secundarios
    'dark': '#1e293b'          # Gris oscuro para texto
}

# Umbral para alertas
"""
Umbral para diferentes métricas del sistema.
"""
def calculate_alert_thresholds(total_applications: int) -> dict:
    """
    Calcula umbrales dinámicos basados en el tamaño de la organización.
    
    Args:
        total_applications: Número total de aplicaciones
        
    Returns:
        dict: Diccionario con umbrales ajustados
    """
    base = 1000
    scale = total_applications / base
    
    return {
        'conversion_rate': {
            'low': max(20, 50 - (scale * 5)),
            'high': min(60, 50 + (scale * 5))
        },
        'avg_days': {
            'low': max(10, 15 - (scale * 2)),
            'high': min(40, 30 + (scale * 2))
        },
        'engagement_rate': {
            'low': max(30, 40 - (scale * 5)),
            'high': min(80, 70 + (scale * 5))
        }
    }

ALERT_THRESHOLDS = calculate_alert_thresholds(1000)  # Valor inicial, se actualizará dinámicamente

# Tiempos para estadísticas
"""
Periodos de tiempo utilizados para diferentes estadísticas.
"""
STATS_TIMEFRAMES = {
    'daily': timedelta(days=1),    # Estadísticas diarias
    'weekly': timedelta(days=7),   # Estadísticas semanales
    'monthly': timedelta(days=30), # Estadísticas mensuales
    'yearly': timedelta(days=365)  # Estadísticas anuales
}

# Estados de aplicación
"""
Estados posibles para una aplicación.
"""
APPLICATION_STATUS = {
    'applied': 'Solicitado',       # Estado inicial
    'in_review': 'En revisión',    # En proceso de revisión
    'interview': 'Entrevista',     # En proceso de entrevista
    'hired': 'Contratado',         # Contratado exitosamente
    'rejected': 'Rechazado'        # Rechazado
}

# Estados de vacante
"""
Estados posibles para una vacante.
"""
VACANCY_STATUS = {
    'active': 'Activa',           # Vacante activa
    'in_progress': 'En proceso',  # En proceso de contratación
    'closed': 'Cerrada',          # Vacante cerrada
    'draft': 'Borrador'           # Vacante en borrador
}

# Prioridades para tareas
"""
Niveles de prioridad para las tareas.
"""
TASK_PRIORITIES = {
    'high': 'Alta',              # Prioridad alta
    'medium': 'Media',           # Prioridad media
    'low': 'Baja'               # Prioridad baja
}

# Estados de integración
"""
Estados posibles para las integraciones.
"""
INTEGRATION_STATUS = {
    'success': 'Activo',         # Integración activa
    'warning': 'Advertencia',    # Integración con advertencia
    'error': 'Error'             # Integración con error
}

# Tipos de alerta
"""
Tipos de alertas que pueden generarse en el sistema.
"""
ALERT_TYPES = {
    'success': 'Éxito',          # Alerta de éxito
    'warning': 'Advertencia',    # Alerta de advertencia
    'error': 'Error',            # Alerta de error
    'info': 'Información'        # Alerta informativa
}

# Rangos de salario
"""
Rangos de salario utilizados para clasificación.
"""
def get_salary_ranges(region: str = 'MX') -> dict:
    """
    Obtiene rangos de salario ajustados por región.
    
    Args:
        region: Código de región (MX, US, EU, etc.)
        
    Returns:
        dict: Diccionario con rangos de salario ajustados
    """
    base_ranges = {
        'low': (0, 20000),
        'medium': (20001, 50000),
        'high': (50001, 100000),
        'very_high': (100001, float('inf'))
    }
    
    # Ajustes por región
    region_adjustments = {
        'MX': 1.0,    # México
        'US': 3.0,    # Estados Unidos
        'EU': 2.5,    # Europa
    }
    
    adjustment = region_adjustments.get(region, 1.0)
    
    return {
        k: (int(v[0] * adjustment), int(v[1] * adjustment) if v[1] != float('inf') else float('inf'))
        for k, v in base_ranges.items()
    }

SALARY_RANGES = get_salary_ranges('MX')  # Valor inicial, se actualizará según la región

# Niveles educativos
"""
Niveles educativos utilizados para clasificación.
"""
EDUCATION_LEVELS = {
    'high_school': 'Bachillerato',  # Bachillerato
    'technical': 'Técnico',         # Técnico
    'bachelor': 'Licenciatura',    # Licenciatura
    'master': 'Maestría',          # Maestría
    'doctorate': 'Doctorado'       # Doctorado
}

# Categorías de habilidades
"""
Categorías de habilidades utilizadas para clasificación.
"""
SKILL_CATEGORIES = {
    'technical': 'Técnicas',       # Habilidades técnicas
    'soft': 'Blandas',            # Habilidades blandas
    'languages': 'Idiomas',       # Idiomas
    'tools': 'Herramientas'       # Herramientas
}

# Estados de gamificación
"""
Estados posibles para el sistema de gamificación.
"""
GAMIFICATION_STATES = {
    'new': 'Nuevo',              # Estado inicial
    'active': 'Activo',          # Activo
    'inactive': 'Inactivo'       # Inactivo
}

# Tipos de logro
"""
Tipos de logros que pueden obtenerse en el sistema.
"""
ACHIEVEMENT_TYPES = {
    'profile': 'Perfil',          # Logros relacionados con el perfil
    'application': 'Aplicación', # Logros relacionados con aplicaciones
    'success': 'Éxito',          # Logros de éxito
    'engagement': 'Engagement'   # Logros de engagement
}

# Métricas de éxito
"""
Métricas de éxito utilizadas para medir el rendimiento del sistema.
"""
SUCCESS_METRICS = {
    'conversion_rate': 'Tasa de conversión',  # Tasa de conversión
    'avg_days': 'Días promedio',             # Días promedio
    'engagement_rate': 'Tasa de engagement'  # Tasa de engagement
}

# Estados de proceso
"""
Estados posibles para un proceso.
"""
PROCESS_STATES = {
    'initial': 'Inicial',         # Estado inicial
    'in_progress': 'En proceso',  # En proceso
    'completed': 'Completado',    # Completado
    'failed': 'Fallido'           # Fallido
}

# Tipos de notificación
"""
Tipos de notificaciones que pueden generarse en el sistema.
"""
NOTIFICATION_TYPES = {
    'application': 'Aplicación',  # Notificación de aplicación
    'status': 'Estado',           # Notificación de estado
    'system': 'Sistema',          # Notificación del sistema
    'engagement': 'Engagement'    # Notificación de engagement
}
