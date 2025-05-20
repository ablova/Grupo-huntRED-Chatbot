"""
Módulo Kanban para la gestión de candidatos.
Este módulo implementa una interfaz tipo Kanban para el seguimiento 
y gestión del estado de los candidatos en el proceso de reclutamiento.

Proporciona las siguientes funcionalidades:
- Tableros Kanban personalizables para diferentes unidades de negocio
- Gestión de columnas y tarjetas para seguimiento de candidatos
- Historial de cambios y notificaciones
- Comentarios y archivos adjuntos para cada candidato
"""

__version__ = "1.0.0"

# No es necesario registrar módulos manualmente, ModuleRegistry se encarga automáticamente
# ModuleRegistry en app/module_registry.py registra todos los módulos durante el inicio de Django

# Imports para compatibilidad
from app.models import (
    KanbanBoard, KanbanColumn, KanbanCard, KanbanCardHistory,
    KanbanComment, KanbanAttachment, KanbanNotification
)
