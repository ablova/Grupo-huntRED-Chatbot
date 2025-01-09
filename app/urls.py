# Ubicacion /home/pablollh/app/urls.py

from django.urls import path
from app.views.main_views import (
    index, interacciones_por_unidad,
    finalize_candidates, login_view, submit_application, home
)
from app.views.chatbot_views import (
    ProcessMessageView, send_test_message
)
from app.views.webhook_views import (
    WhatsAppWebhookView, TelegramWebhookView,
    MessengerWebhookView, InstagramWebhookView
)
from app.views.util_views import (
    SendTestMessageView, SendTestNotificationView,
    TriggerErrorView
)
from django.conf.urls.static import static
from django.conf import settings
from app.views.candidatos_views import (
    candidato_dashboard, list_candidatos, add_application, candidato_details, generate_challenges
)
from app.views.dashboard_views import dashboard_view
from app.views.ml_views import (
    train_ml_api,
    predict_matches
)

urlpatterns = [
    # Home y Dashboard
    path('', home, name='home'),
    path('dashboard/', dashboard_view, name='dashboard'),

    # Vistas administrativas
    path('admin/estadisticas/interacciones/', interacciones_por_unidad, name='interacciones_por_unidad'),
    #path('admin/chatbot_flow/<int:flowmodel_id>/', edit_flow, name='edit_flow'),

    # Chatbot
    path('chatbot/process_message/', ProcessMessageView.as_view(), name='process_message'),
#    path('chatbot/settings/', chatbot_settings, name='chatbot_settings'),

    # Candidatos
    path('candidatos/', candidato_dashboard, name='candidato_dashboard'),
    path('candidatos/list/', list_candidatos, name='list_candidatos'),
    path('candidatos/add/', add_application, name='add_application'),
    path('candidatos/<int:candidato_id>/', candidato_details, name='candidato_details'),
    path('generate_challenges/<int:user_id>/', generate_challenges, name='generate_challenges'),

    # Scraping
#    path('scraping/status/', scraping_status, name='scraping_status'),
#    path('scraping/initiate/', initiate_scraping, name='initiate_scraping'),

    # Machine Learning
    path('ml/predict_matches/<int:user_id>/', predict_matches, name='predict_matches'),
    path('ml/train_model/', train_ml_api, name='train_model'),


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