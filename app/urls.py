# /home/amigro/app/urls.py
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views
from .views import index
from app.integrations.telegram import telegram_webhook
from app.integrations.whatsapp import whatsapp_webhook
from app.integrations.messenger import messenger_webhook
from app.integrations.instagram import instagram_webhook

urlpatterns = [
    path('', index, name="index"),
    path('webhook/whatsapp/048bd814-7716-4073-8acf-d491db68e9a1', whatsapp_webhook, name='whatsapp_webhook'),
    path('webhook/telegram/871198362', telegram_webhook, name='telegram_webhook'),
    path('webhook/messenger/109623338672452', messenger_webhook, name='messenger_webhook'),
    path('webhook/instagram/109623338672452', instagram_webhook, name='instagram_webhook'), #amigro_secret_token
    
    # Rutas para administrar preguntas
    path('preguntas/', views.create_pregunta, name='create_pregunta'),
    path('preguntas/<int:id>/', views.update_pregunta, name='update_pregunta'),
    path('preguntas/<int:id>/position/', views.update_position, name='update_position'),
    path('preguntas/<int:id>/delete/', views.delete_pregunta, name='delete_pregunta'),

    # Rutas para la administración del flujo del chatbot
    path('admin/app/flowmodel/<int:flowmodel_id>/edit-flow/', views.edit_flow, name='edit_flow'),
    path('admin/app/save_flow_structure/', views.save_flow_structure, name='save_flow_structure'),
    path('admin/app/export_chatbot_flow/', views.export_chatbot_flow, name='export_chatbot_flow'),
    path('admin/app/load_flow_data/', views.load_flow_data, name='load_flow_data'),
    path('send-message/', views.send_message, name='send_message'),
    path('send-test-message/', views.send_test_message, name='send_test_message'),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#APP 713dd8c2-0801-4720-af2a-910da63c42d3   7732534605ab6a7b96c8e8e81ce02e6b