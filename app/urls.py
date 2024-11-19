#/home/amigro/app/urls.py
#APP 713dd8c2-0801-4720-af2a-910da63c42d3   7732534605ab6a7b96c8e8e81ce02e6b

from django.urls import path, re_path, include
from django.conf.urls.static import static
from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponse
from app.views import (
    index,
    CreateFlowView,
    edit_flow,
    save_flow_structure,
    export_chatbot_flow,
    load_flow_data,
    create_pregunta,
    update_pregunta,
    delete_pregunta,
    update_position,
    send_test_message,
    send_test_notification
)
from app.integrations.telegram import telegram_webhook
from app.integrations.whatsapp import whatsapp_webhook
from app.integrations.messenger import messenger_webhook
from app.integrations.instagram import instagram_webhook
from app.milkyleak import milkyleak_view

# Vistas de error personalizadas
def custom_404_view(request, *args, **kwargs):
    return HttpResponseNotFound("Not Found - Error 404. Por favor, contacte al administrador.")

def trigger_error(request):
    division_by_zero = 1 / 0

def debug_view(request):
    return HttpResponse("Webhook encontrado")

# Definición de rutas
urlpatterns = [
    # Página principal
    path('', index, name="index"),

    # Webhooks para integraciones
    path('webhook/whatsapp/debug/', debug_view, name='debug_view'),
    path('webhook/whatsapp/048bd814-7716-4073-8acf-d491db68e9a1/', whatsapp_webhook, name='whatsapp_webhook'),
    path('webhook/whatsapp/048bd814-7716-4073-8acf-d491db68e9a1', whatsapp_webhook, name='whatsapp_webhook_no_slash'),
    path('webhook/telegram/871198362/', telegram_webhook, name='telegram_webhook'),
    path('webhook/messenger/109623338672452/', messenger_webhook, name='messenger_webhook'),
    path('webhook/instagram/109623338672452/', instagram_webhook, name='instagram_webhook'),

    # Rutas para CRUD de Preguntas
    path('preguntas/', create_pregunta, name='create_pregunta'),
    path('preguntas/<int:id>/', update_pregunta, name='update_pregunta'),
    path('preguntas/<int:id>/position/', update_position, name='update_position'),
    path('preguntas/<int:id>/delete/', delete_pregunta, name='delete_pregunta'),

    # Rutas para la gestión del flujo
    re_path(r'^create-flow/$', CreateFlowView.as_view(), name='create_flow'),
    path('flowmodel/<int:flowmodel_id>/edit-flow/', edit_flow, name='edit_flow'),
    path('save_flow_structure/', save_flow_structure, name='save_flow_structure'),
    path('export_chatbot_flow/', export_chatbot_flow, name='export_chatbot_flow'),
    path('load_flow_data/<int:flowmodel_id>/', load_flow_data, name='load_flow_data'),

    # Rutas de pruebas y utilidades
    path('send-test-message/', send_test_message, name='send_test_message'),
    path('send-test-notification/', send_test_notification, name='send_test_notification'),
    path('milkyleak/', milkyleak_view, name='milkyleak'),
    path('sentry-debug/', trigger_error),
]

# Añadir rutas para archivos estáticos en modo desarrollo
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)