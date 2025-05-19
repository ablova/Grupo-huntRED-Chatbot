# /home/pablo/app/notifications/urls.py
#
# Configuración de URLs para el módulo. Define endpoints, vistas y patrones de URL.

from django.urls import path
from app.notifications import views

app_name = 'notifications'

urlpatterns = [
    path('send/', views.send_notification, name='send'),
    path('bulk/', views.send_bulk_notifications, name='bulk'),
    path('status/<int:notification_id>/', views.get_notification_status, name='status'),
    path('templates/', views.list_templates, name='templates'),
    path('channels/', views.list_channels, name='channels'),
    path('recipients/', views.list_recipients, name='recipients'),
]
