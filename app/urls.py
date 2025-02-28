# Ubicación: /home/pablo/app/urls.py
# Descripción: Archivo principal de rutas centralizadas para toda la aplicación.
import logging
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# IMPORTACIONES DE VISTAS
from app.views.main_views import (
    index, interacciones_por_unidad, finalize_candidates, 
    login_view, submit_application, home
)
from app.views.dashboard_views import dashboard_view
from app.views.chatbot_views import ProcessMessageView
from app.views.util_views import (
    SendTestMessageView, SendTestNotificationView, TriggerErrorView
)
from app.views.candidatos_views import (
    candidato_dashboard, list_candidatos, add_application, 
    candidato_details, generate_challenges
)
from app.views.ml_views import train_ml_api, predict_matches

# IMPORTACIONES DE WEBHOOKS (MENSAJERÍA)
from app.views.webhook_views import (
    WhatsAppWebhookView, TelegramWebhookView, 
    MessengerWebhookView, InstagramWebhookView
)

# IMPORTACIONES DE WORKFLOW (GESTIÓN DE ETAPAS)
from app.views.workflow_views import (
    WorkflowStageListView, WorkflowStageCreateView, 
    WorkflowStageUpdateView, WorkflowStageDeleteView
)

# IMPORTACIONES DE SEXSI (GESTIÓN DE ACUERDOS)
from app.sexsi.views import (
    create_agreement, agreement_detail, sign_agreement,
    download_pdf, upload_signature_and_selfie, finalize_agreement,
    request_revision, revoke_agreement, paypal_webhook
)

logger = logging.getLogger(__name__)
logger.info("Inicio de la aplicación.")
# -------------------------------
# 📌 RUTAS PRINCIPALES Y DASHBOARD
# -------------------------------
urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard_view, name='dashboard'),
]

# ---------------------------------
# 📌 RUTAS ADMINISTRATIVAS Y LOGS
# ---------------------------------
urlpatterns += [
    path('admin/estadisticas/interacciones/', interacciones_por_unidad, name='interacciones_por_unidad'),
]

# ------------------------
# 📌 RUTAS DEL CHATBOT
# ------------------------
urlpatterns += [
    path('chatbot/process_message/', ProcessMessageView.as_view(), name='process_message'),
]

# ------------------------
# 📌 RUTAS DE CANDIDATOS
# ------------------------
urlpatterns += [
    path('candidatos/', candidato_dashboard, name='candidato_dashboard'),
    path('candidatos/list/', list_candidatos, name='list_candidatos'),
    path('candidatos/add/', add_application, name='add_application'),
    path('candidatos/<int:candidato_id>/', candidato_details, name='candidato_details'),
    path('generate_challenges/<int:user_id>/', generate_challenges, name='generate_challenges'),
]

# ------------------------
# 📌 RUTAS DE MACHINE LEARNING
# ------------------------
urlpatterns += [
    path('ml/predict_matches/<int:user_id>/', predict_matches, name='predict_matches'),
    path('ml/train_model/', train_ml_api, name='train_model'),
]

# ------------------------
# 📌 RUTAS DE PRUEBAS Y UTILIDADES
# ------------------------
urlpatterns += [
    path('send-test-message/', SendTestMessageView.as_view(), name='send_test_message'),
    path('send-test-notification/', SendTestNotificationView.as_view(), name='send_test_notification'),
    path('sentry-debug/', TriggerErrorView.as_view(), name='trigger_error'),
]

# ------------------------
# 📌 RUTAS DE AUTENTICACIÓN
# ------------------------
urlpatterns += [
    path('login/', login_view, name='login'),
]

# ----------------------------------------
# 📌 RUTAS DE MENSAJERÍA (WEBHOOKS GLOBALES)
# ----------------------------------------
urlpatterns += [
    path('webhook/whatsapp/<str:phoneID>/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('webhook/telegram/<str:bot_name>/', TelegramWebhookView.as_view(), name='telegram_webhook'),
    path('webhook/telegram/', TelegramWebhookView.as_view(), name='telegram_webhook_general'),
    path('webhook/messenger/<str:page_id>/', MessengerWebhookView.as_view(), name='messenger_webhook'),
    path('webhook/instagram/<str:page_id>/', InstagramWebhookView.as_view(), name='instagram_webhook'),
]

# ----------------------------------------
# 📌 RUTAS DE WORKFLOW (GESTIÓN DE ETAPAS)
# ----------------------------------------
urlpatterns += [
    path('<int:business_unit_id>/stages/', WorkflowStageListView.as_view(), name='workflow_stage_list'),
    path('<int:business_unit_id>/stages/create/', WorkflowStageCreateView.as_view(), name='workflow_stage_create'),
    path('<int:business_unit_id>/stages/<int:stage_id>/update/', WorkflowStageUpdateView.as_view(), name='workflow_stage_update'),
    path('<int:business_unit_id>/stages/<int:stage_id>/delete/', WorkflowStageDeleteView.as_view(), name='workflow_stage_delete'),
]

# ----------------------------------------
# 📌 RUTAS DE SEXSI (GESTIÓN DE ACUERDOS)
# ----------------------------------------
urlpatterns += [
    path('sexsi/create/', create_agreement, name='create_agreement'),
    path('sexsi/agreement/<int:agreement_id>/', agreement_detail, name='agreement_detail'),
    path('sexsi/sign/<int:agreement_id>/<str:signer>/<uuid:token>/', sign_agreement, name='sign_agreement'),
    path('sexsi/download/<int:agreement_id>/', download_pdf, name='download_pdf'),
    path('sexsi/sign/save/<int:agreement_id>/', upload_signature_and_selfie, name='save_signature'),
    path('sexsi/sign/finalize/<int:agreement_id>/<str:signer>/<uuid:token>/', finalize_agreement, name='finalize_agreement'),
    path('sexsi/sign/revision/<int:agreement_id>/', request_revision, name='request_revision'),
    path('sexsi/sign/revoke/<int:agreement_id>/', revoke_agreement, name='revoke_agreement'),
    path('sexsi/webhook/paypal/', paypal_webhook, name='paypal_webhook'),
]

# -------------------------------
# 📌 MANEJO DE ARCHIVOS ESTÁTICOS
# -------------------------------
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# -------------------------------
# 📌 MANEJO DE ERRORES
# -------------------------------
handler404 = 'app.views.main_views.Custom404View.as_view'