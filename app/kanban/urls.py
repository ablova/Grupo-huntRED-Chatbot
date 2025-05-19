"""
Configuración de URLs para el módulo Kanban.
Define las rutas para las vistas y APIs del sistema Kanban de gestión de candidatos.
"""

from django.urls import path
from app.kanban import views

app_name = 'kanban'

urlpatterns = [
    # Vistas principales
    path('', views.index, name='index'),
    path('board/<int:board_id>/', views.board_view, name='board_view'),
    path('card/<int:card_id>/', views.card_detail_view, name='card_detail'),
    
    # APIs para interacción con tarjetas
    path('api/move-card/', views.move_card, name='move_card'),
    path('api/update-card/', views.update_card, name='update_card'),
    path('api/add-comment/', views.add_comment, name='add_comment'),
    path('api/archive-card/', views.archive_card, name='archive_card'),
    path('api/upload-attachment/', views.upload_attachment, name='upload_attachment'),
    path('api/notification/mark-read/', views.mark_notification_read, name='mark_notification_read'),
]
