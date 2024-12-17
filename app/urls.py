# /home/amigro/app/urls.py

from django.urls import path
from app.views.main_views import (
    index, interacciones_por_unidad, load_flow, create_pregunta,
    update_pregunta, delete_pregunta, update_position, load_flow_data,
    edit_flow, save_flow_structure, export_chatbot_flow, load_flow_questions_data,
    finalize_candidates, login_view, submit_application
)
from app.views.chatbot_views import (
    ProcessMessageView, send_test_message
)
from app.views.webhook_views import (
    WhatsAppWebhookView, TelegramWebhookView,
    MessengerWebhookView, InstagramWebhookView
)
from app.views.utils_views import (
    SendTestMessageView, SendTestNotificationView
)
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    # Home y Dashboard
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),

    # Vistas administrativas
    path('admin/estadisticas/interacciones/', interacciones_por_unidad, name='interacciones_por_unidad'),
    path('admin/chatbot_flow/<int:flowmodel_id>/', edit_flow, name='edit_flow'),

    # Chatbot
    path('chatbot/process_message/', process_message, name='process_message'),
    path('chatbot/settings/', chatbot_settings, name='chatbot_settings'),

    # Candidatos
    path('generate_challenges/<int:user_id>/', generate_challenges, name='generate_challenges'),

    # Scraping
    path('scraping/status/', scraping_status, name='scraping_status'),
    path('scraping/initiate/', initiate_scraping, name='initiate_scraping'),

    # Machine Learning
    path('ml/predict_matches/<int:user_id>/', predict_matches, name='predict_matches'),
    path('ml/train_model/', train_model, name='train_model'),

    # Webhooks para integraciones
    path('webhook/whatsapp/debug/', DebugView.as_view(), name='debug_view'),
    path('webhook/whatsapp/048bd814-7716-4073-8acf-d491db68e9a1/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('webhook/telegram/871198362/', TelegramWebhookView.as_view(), name='telegram_webhook'),
    path('webhook/messenger/109623338672452/', MessengerWebhookView.as_view(), name='messenger_webhook'),
    path('webhook/instagram/109623338672452/', InstagramWebhookView.as_view(), name='instagram_webhook'),

    # Rutas de pruebas y utilidades
    path('send-test-message/', SendTestMessageView.as_view(), name='send_test_message'),
    path('send-test-notification/', SendTestNotificationView.as_view(), name='send_test_notification'),
    path('sentry-debug/', TriggerErrorView.as_view(), name='trigger_error'),


    # Aplicaciones y finalización
    path('apply/<int:job_id>/', submit_application, name='submit_application'),
    path('finalize_candidates/<int:business_unit_id>/', finalize_candidates, name='finalize_candidates'),

    # Autenticación
    path('login/', login_view, name='login'),

]

# Añadir rutas para archivos estáticos en modo desarrollo
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Manejo de errores personalizados
handler404 = 'app.views.main_views.Custom404View.as_view'