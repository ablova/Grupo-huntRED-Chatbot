from django.urls import path, re_path
from app.ats.views.webhook_views import (
    WhatsAppWebhookView, TelegramWebhookView,
    MessengerWebhookView, InstagramWebhookView
)
from app.ats.views.verification_views import webhook_verification
from app.ats.views.publish_views import webhook_job_opportunity
from app.ats.views.webhook_views import WebhookView

urlpatterns = [
    # Webhooks de mensajería
    re_path(r'^whatsapp/(?P<phoneID>[\w-]+)/?$', 
            WhatsAppWebhookView.as_view(), 
            name='whatsapp_webhook'),
    re_path(r'^telegram/(?P<bot_name>.+)/?$', 
            TelegramWebhookView.as_view(), 
            name='telegram_webhook'),
    path('telegram/', 
         TelegramWebhookView.as_view(), 
         name='telegram_webhook_general'),
    re_path(r'^messenger/(?P<page_id>[\w-]+)/?$', 
            MessengerWebhookView.as_view(), 
            name='messenger_webhook'),
    re_path(r'^instagram/(?P<page_id>[\w-]+)/?$', 
            InstagramWebhookView.as_view(), 
            name='instagram_webhook'),
    
    # Webhooks de integración
    path('payment/', 
         WebhookView.as_view(), 
         name='payment_webhook'),
    path('verification/', 
         webhook_verification, 
         name='verification_webhook'),
    path('job_opportunity/', 
         webhook_job_opportunity, 
         name='job_opportunity_webhook'),
] 