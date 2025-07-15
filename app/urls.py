# app/urls.py
#
# Configuración de URLs para el módulo. Define endpoints, vistas y patrones de URL.

import logging
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required

# IMPORTACIONES DE VISTAS
from app.views.main_views import (
    index, interacciones_por_unidad, finalize_candidates, 
    submit_application, home
)
from app.views.proposal_views import download_proposal_pdf
from app.views.auth_views import (
    login_view, logout_view, user_management,
    approve_user, profile, change_password,
    forgot_password, reset_password, document_verification
)
from app.views.offer_letter_views import (
    gestion_cartas_oferta, marcar_como_firmada, reenviar_carta, ver_carta, generar_preview
)
from app.views.preview_views import generar_preview
from app.views.dashboard_views import dashboard_view
from app.views.chatbot_views import ProcessMessageView, ChatbotView, WebhookView
from app.views.util_views import (
    SendTestMessageView, SendTestNotificationView, TriggerErrorView
)
from app.views.verification_views import (
    verification_list, initiate_verification, analyze_risk,
    verify_incode, webhook_verification
)
from app.views.candidatos_views import (
    candidato_dashboard, list_candidatos, add_application, 
    candidato_details, generate_challenges
)
from app.views.ml_views import train_ml_api, predict_matches
from app.views.ml_admin_views import MLDashboardView, vacancy_analysis_view, candidate_growth_plan_view, candidate_growth_plan_pdf_view, dashboard_charts_api_view
from app.views.analytics import advanced_analytics_dashboard, matching_analytics, performance_metrics, predictive_insights, automated_matching, analytics_api
from app.views.dashboard import (
    dashboard, interview_slots_dashboard, generate_slots, 
    slot_details, edit_slot, delete_slot, slot_analytics
)

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
from app.ats.sexsi.views import (
    sexsi_dashboard, create_agreement, sign_agreement, agreement_status,
    legal_compliance, process_payment, consent_form, mutual_agreement,
    agreement_detail, preference_selection
)
from django.urls import path
from app.views.publish_views import (
    job_opportunities_list,
    create_job_opportunity,
    publish_job_opportunity,
    update_job_opportunity_status,
    webhook_job_opportunity
)
# TODO: Temporal - comentar hasta resolver el problema de importación
# from app.ats.pricing.views import sync_pricing_view, sync_all_pricing_view

# Importación para Análisis Cultural
# Migrated to app.ats.chatbot.workflow.assessments.cultural



logger = logging.getLogger(__name__)

# -------------------------------
# 📌 RUTAS PRINCIPALES
# -------------------------------
urlpatterns = [
    # Rutas de autenticación
    path('auth/', include([
        path('login/', login_view, name='login'),
        path('logout/', logout_view, name='logout'),
        path('signup/', user_management, name='signup'),
        path('approve-user/<int:user_id>/', approve_user, name='approve_user'),
        path('profile/', login_required(profile), name='profile'),
        path('change-password/', login_required(change_password), name='change_password'),
        path('forgot-password/', forgot_password, name='forgot_password'),
        path('reset-password/<str:token>/', reset_password, name='reset_password'),
        path('document-verification/', login_required(document_verification), name='document_verification'),
    ])),
    
    # Rutas principales
    path('', home, name='home'),
    path('dashboard/', login_required(dashboard_view), name='dashboard'),
    
    # Incluir URLs de módulos
    path('chatbot/', include('app.views.chatbot.urls')),
    path('candidates/', include('app.views.candidates.urls')),
    #path('workflow/', include('app.views.workflow.urls')), Se convirtieron en las rutas de workflow de más adelante 218-222
    path('sexsi/', include('app.sexsi.urls')),

    path('pricing/', include('app.ats.pricing.urls', namespace='pricing')),
    path('publish/', include('app.ats.publish.urls')),
    path('ml/', include('app.views.ml.urls')),
    path('webhooks/', include('app.views.webhook.urls')),
    
    # 🌟 INTEGRACIÓN DE AURA - SISTEMA DE INTELIGENCIA RELACIONAL
    path('aura/', include('app.ml.aura.urls', namespace='aura')),
    
    # 🚀 ANALYTICS AVANZADOS Y MATCHING AUTOMÁTICO
    path('advanced-analytics/', advanced_analytics_dashboard, name='advanced_analytics_dashboard'),
    path('advanced-analytics/matching/', matching_analytics, name='matching_analytics'),
    path('advanced-analytics/performance/', performance_metrics, name='performance_metrics'),
    path('advanced-analytics/predictive/', predictive_insights, name='predictive_insights'),
    path('advanced-analytics/automated-matching/', automated_matching, name='automated_matching'),
    path('advanced-analytics/api/', analytics_api, name='analytics_api'),
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
    # Rutas principales del chatbot
    path('chatbot/<str:platform>/', ChatbotView.as_view(), name='chatbot_platform'),
    path('chatbot/process_message/', ProcessMessageView.as_view(), name='process_message'),
    
    # Rutas de webhooks
    path('webhook/whatsapp/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('webhook/telegram/', TelegramWebhookView.as_view(), name='telegram_webhook'),
    path('webhook/messenger/', MessengerWebhookView.as_view(), name='messenger_webhook'),
    path('webhook/instagram/', InstagramWebhookView.as_view(), name='instagram_webhook'),
    
    # Rutas de integración
    path('webhook/payment/', WebhookView.as_view(), name='payment_webhook'),
    path('webhook/verification/', webhook_verification, name='verification_webhook'),
    path('webhook/job_opportunity/', webhook_job_opportunity, name='job_opportunity_webhook'),
    
    # Rutas de prueba y utilidades
    path('chatbot/test/message/', SendTestMessageView.as_view(), name='test_message'),
    path('chatbot/test/notification/', SendTestNotificationView.as_view(), name='test_notification'),
    path('chatbot/test/error/', TriggerErrorView.as_view(), name='trigger_error')
]

# ------------------------
# 📌 RUTAS DE DASHBOARD
# ------------------------
urlpatterns += [
    path('dashboard/', dashboard, name='dashboard'),
    
    # 🎯 NUEVAS RUTAS PARA GESTIÓN DE SLOTS DE ENTREVISTA
    path('dashboard/slots/', login_required(interview_slots_dashboard), name='interview_slots_dashboard'),
    path('dashboard/slots/generate/', login_required(generate_slots), name='generate_slots'),
    path('dashboard/slots/<uuid:slot_id>/', login_required(slot_details), name='slot_details'),
    path('dashboard/slots/<uuid:slot_id>/edit/', login_required(edit_slot), name='edit_slot'),
    path('dashboard/slots/<uuid:slot_id>/delete/', login_required(delete_slot), name='delete_slot'),
    path('dashboard/slots/analytics/', login_required(slot_analytics), name='slot_analytics'),
]

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
    
    # Rutas de pagos
    path('pricing/', include('app.ats.pricing.urls', namespace='pricing')),
]

# ----------------------------------------
# 📌 RUTAS DE MENSAJERÍA (WEBHOOKS GLOBALES)
# ----------------------------------------
urlpatterns += [
    re_path(r'^webhook/whatsapp/(?P<phoneID>[\w-]+)/?$', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    re_path(r'^webhook/telegram/(?P<bot_name>.+)/?$', TelegramWebhookView.as_view(), name='telegram_webhook'),
    path('webhook/telegram/', TelegramWebhookView.as_view(), name='telegram_webhook_general'),
    re_path(r'^webhook/messenger/(?P<page_id>[\w-]+)/?$', MessengerWebhookView.as_view(), name='messenger_webhook'),
    re_path(r'^webhook/instagram/(?P<page_id>[\w-]+)/?$', InstagramWebhookView.as_view(), name='instagram_webhook'),
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
    path('sexsi/', sexsi_dashboard, name='sexsi_dashboard'),
    path('sexsi/create/', create_agreement, name='create_agreement'),
    path('sexsi/sign/', sign_agreement, name='sign_agreement'),
    path('sexsi/status/', agreement_status, name='agreement_status'),
    path('sexsi/compliance/', legal_compliance, name='legal_compliance'),
    path('sexsi/payment/', process_payment, name='process_payment'),
    path('sexsi/consent/', consent_form, name='consent_form'),
    path('sexsi/mutual/', mutual_agreement, name='mutual_agreement'),
    path('sexsi/agreement/<int:agreement_id>/', agreement_detail, name='agreement_detail'),
    path('sexsi/preferences/', preference_selection, name='preference_selection'),
]

# ------------------------
# 📌 RUTAS DE CARTAS DE OFERTA Y PROPUESTAS
# ------------------------
urlpatterns += [
    path('admin/cartas_oferta/', gestion_cartas_oferta, name='gestion_cartas_oferta'),
    path('admin/cartas_oferta/<int:carta_id>/firmar/', marcar_como_firmada, name='marcar_como_firmada'),
    path('admin/cartas_oferta/<int:carta_id>/reenviar/', reenviar_carta, name='reenviar_carta'),
    path('admin/cartas_oferta/<int:carta_id>/ver/', ver_carta, name='ver_carta'),
    path('admin/cartas_oferta/preview/', generar_preview, name='generar_preview'),
    path('proposal/pdf/<int:proposal_id>/', download_proposal_pdf, name='download_proposal_pdf'),
]

# ------------------------
# 📌 RUTAS DE PUBLICACIÓN
# ------------------------
urlpatterns += [
    path('publish/jobs/', job_opportunities_list, name='job_opportunities_list'),
    path('publish/jobs/create/', create_job_opportunity, name='create_job_opportunity'),
    path('publish/jobs/<int:opportunity_id>/publish/', publish_job_opportunity, name='publish_job_opportunity'),
    path('publish/jobs/<int:opportunity_id>/status/', update_job_opportunity_status, name='update_job_opportunity_status'),
    path('webhook/job_opportunity/', webhook_job_opportunity, name='webhook_job_opportunity'),
]

# ---------------------------------------
# 📌 RUTAS DEL SISTEMA DE RETROALIMENTACIÓN
# ---------------------------------------
urlpatterns += [
    path('feedback/', include('app.ats.feedback.urls', namespace='feedback')),
    # Ruta de compatibilidad para mantener URLs existentes
    path('pricing/feedback/', include('app.ats.feedback.urls', namespace='pricing_feedback')),
]

# ------------------------
# 📌 RUTAS DE VERIFICACIÓN
# ------------------------
urlpatterns += [
    path('verification/', verification_list, name='verification_list'),
    path('verification/initiate/<int:candidate_id>/', initiate_verification, name='initiate_verification'),
    path('verification/<int:verification_id>/risk/', analyze_risk, name='analyze_risk'),
    path('verification/<int:verification_id>/incode/', verify_incode, name='verify_incode'),
    path('webhook/verification/', webhook_verification, name='webhook_verification'),
]
# ----------------------------------------
# 📌 RUTAS DE KANBAN (GESTIÓN DE CANDIDATOS)
# ----------------------------------------
urlpatterns += [
    path('kanban/', include('app.ats.kanban.urls', namespace='kanban')),
]

# ----------------------------------------
# 📌 RUTAS DE ANÁLISIS CULTURAL (CULTURAL FIT)
# ----------------------------------------
urlpatterns += [
    # Migrated to app.ats.chatbot.workflow.assessments.cultural
]

# ------------------------
# 📌 RUTAS DE ML (ANÁLISIS PREDICTIVO)
# ------------------------
urlpatterns += [
    # Dashboard y análisis ML
    path('ml/dashboard/', MLDashboardView.as_view(), name='ml_dashboard'),
    path('ml/vacancy/<int:vacancy_id>/', vacancy_analysis_view, name='ml_vacancy_analysis'),
    path('ml/candidate/<int:candidate_id>/growth/', candidate_growth_plan_view, name='ml_candidate_growth_plan'),
    path('ml/candidate/<int:candidate_id>/growth/pdf/', candidate_growth_plan_pdf_view, name='ml_candidate_growth_plan_pdf'),
    
    # API para los gráficos y datos del dashboard
    path('ml/api/dashboard-charts/', dashboard_charts_api_view, name='ml_api_dashboard_charts'),
    
    # Rutas existentes de ML
    path('ml/train/', train_ml_api, name='train_ml_api'),
    path('ml/predict/', predict_matches, name='predict_matches'),
]

# -------------------------------
# 📌 MANEJO DE ARCHIVOS ESTÁTICOS
# -------------------------------
# ------------------------
# 📌 RUTAS DE ONBOARDING
# ------------------------
urlpatterns += [
    path('onboarding/', include('app.ats.onboarding.urls')),
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# -------------------------------
# 📌 MANEJO DE ERRORES
# -------------------------------
# handler404 = 'app.views.main_views.Custom404View.as_view'


from app.views.talent import talent_views

urlpatterns += [
    path('api/talent/team-synergy', talent_views.analyze_team_synergy, name='analyze_team_synergy'),
    path('api/talent/career-trajectory/<int:person_id>', talent_views.analyze_career_trajectory, name='analyze_career_trajectory'),
    path('api/talent/cultural-fit', talent_views.analyze_cultural_fit, name='analyze_cultural_fit'),
    path('api/talent/learning-plan/<int:person_id>', talent_views.generate_learning_plan, name='generate_learning_plan'),
    path('api/talent/mentor-match/<int:person_id>', talent_views.find_mentors, name='find_mentors'),
    path('api/talent/retention-risk/<int:person_id>', talent_views.analyze_retention_risk, name='analyze_retention_risk'),
    path('api/talent/intervention-plan/<int:person_id>', talent_views.generate_intervention_plan, name='generate_intervention_plan'),
]

# ----------------------------------------
# 📌 RUTAS DE FEEDBACK API
# ----------------------------------------
from app.views.feedback_api_views import *
from app.views.linkedin import message_templates, schedules
from app.views.proposals import update_client_info, update_company_contacts, add_invitee, remove_invitee

urlpatterns += [
    # Feedback URLs
    path('api/feedback/submit/', submit_feedback, name='submit_feedback'),
    path('api/feedback/stats/<str:skill_id>/', get_feedback_stats, name='get_feedback_stats'),
    path('api/feedback/list/', list_feedback, name='list_feedback'),
    path('api/feedback/<int:feedback_id>/', get_feedback_details, name='get_feedback_details'),
    path('api/feedback/retrain/<str:skill_id>/', trigger_retraining, name='trigger_retraining'),

    # URLs para validación de skills (existen en app.views.feedback_api_views)
    path('skill-assessment/<int:assessment_id>/', get_skill_assessment_details, name='skill_assessment_details'),
    path('skill-assessment/<int:assessment_id>/validate/', validate_skill_assessment, name='validate_skill_assessment'),

    # LinkedIn Templates (existen en app.views.linkedin.message_templates)
    path('linkedin/templates/', message_templates.template_list, name='linkedin:template_list'),
    path('linkedin/templates/create/', message_templates.template_create, name='linkedin:template_create'),
    path('linkedin/templates/<int:pk>/edit/', message_templates.template_edit, name='linkedin:template_edit'),
    path('linkedin/templates/<int:pk>/toggle/', message_templates.template_toggle, name='linkedin:template_toggle'),
    path('linkedin/templates/<int:pk>/delete/', message_templates.template_delete, name='linkedin:template_delete'),

    # LinkedIn Schedules (existen en app.views.linkedin.schedules)
    path('linkedin/schedules/', schedules.schedule_list, name='linkedin:schedule_list'),
    path('linkedin/schedules/create/', schedules.schedule_create, name='linkedin:schedule_create'),
    path('linkedin/schedules/<int:pk>/edit/', schedules.schedule_edit, name='linkedin:schedule_edit'),
    path('linkedin/schedules/<int:pk>/toggle/', schedules.schedule_toggle, name='linkedin:schedule_toggle'),
    path('linkedin/schedules/<int:pk>/delete/', schedules.schedule_delete, name='linkedin:schedule_delete'),

    # Rutas de edición inline (existen en app.views.proposals.views)
    path('proposals/client/<int:client_id>/update-info/', update_client_info, name='update_client_info'),
    path('proposals/company/<int:company_id>/update-contacts/', update_company_contacts, name='update_company_contacts'),
    path('proposals/company/<int:company_id>/add-invitee/', add_invitee, name='add_invitee'),
    path('proposals/company/<int:company_id>/remove-invitee/', remove_invitee, name='remove_invitee'),
]

# ----------------------------------------
# 📌 RUTAS DE AURA (EXECUTIVE DASHBOARD)
# ----------------------------------------
from app.views.aura.dashboard import AURADashboardView
from app.views.aura.recommendations import AuraRecommendationsView
from app.views.aura.networking import AuraNetworkingView
from app.views.aura.organizational import AuraOrganizationalView
from app.views.aura.gpt_assistant import AuraGPTAssistantView

urlpatterns += [
    # AURA Routes (existen en app.views.aura.*)
    path('aura/dashboard/', AURADashboardView.as_view(), name='aura_dashboard'),
    path('aura/recommendations/', AuraRecommendationsView.as_view(), name='aura_recommendations'),
    path('aura/networking/', AuraNetworkingView.as_view(), name='aura_networking'),
    path('aura/organizational/', AuraOrganizationalView.as_view(), name='aura_organizational'),
    path('aura/gpt/', AuraGPTAssistantView.as_view(), name='aura_gpt_assistant'),
]