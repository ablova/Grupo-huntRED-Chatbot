# /home/pablollh/app/urls/webhook_urls.py

from django.urls import path
from models import WhatsAppAPI
from app.views.webhook_views import (
    WhatsAppWebhookView,
    TelegramWebhookView,
    MessengerWebhookView,
    InstagramWebhookView
)

urlpatterns = [
    #path('whatsapp/<str:phoneID>/', whatsapp_webhook, name='whatsapp_webhook'),
    path('whatsapp/048bd814-7716-4073-8acf-d491db68e9a1/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('telegram/871198362/', TelegramWebhookView.as_view(), name='telegram_webhook'),
    path('messenger/109623338672452/', MessengerWebhookView.as_view(), name='messenger_webhook'),
    path('instagram/109623338672452/', InstagramWebhookView.as_view(), name='instagram_webhook'),
]