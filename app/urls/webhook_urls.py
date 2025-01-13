# /home/pablollh/app/urls/webhook_urls.py

from django.urls import path
from app.models import WhatsAppAPI, TelegramAPI, MessengerAPI, InstagramAPI
from app.views.webhook_views import (
    WhatsAppWebhookView,
    TelegramWebhookView,
    MessengerWebhookView,
    InstagramWebhookView
)

urlpatterns = [
    path('whatsapp/<str:phoneID>/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    # path('whatsapp/048bd814-7716-4073-8acf-d491db68e9a1/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('telegram/<str:bot_name>/', TelegramWebhookView.as_view(), name='telegram_webhook'),  # Mi usuario es 871198362
    path('messenger/<str:page_id>/', MessengerWebhookView.as_view(), name='messenger_webhook'),  # Hacer dinámico con page_id
    path('instagram/<str:page_id>/', InstagramWebhookView.as_view(), name='instagram_webhook'),
]