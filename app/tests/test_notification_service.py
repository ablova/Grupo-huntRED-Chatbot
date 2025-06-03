import os
import sys
import pytest
import django
import asyncio
from unittest.mock import patch, MagicMock

# Configuración de entorno de prueba
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')
django.setup()

from app.models import Person, Notification, NotificationChannel, NotificationConfig, MetaAPI, WhatsAppConfig
from app.ats.utils.notification_service import NotificationService
from app.ats.utils.whatsapp import WhatsAppApi

# Datos de prueba
TEST_PHONE = '+525518490291'
TEST_EMAIL = 'pablo@huntred.com'
TEST_TELEGRAM_ID = '871198362'
TEST_NAME = 'Pablo'

class TestNotificationService:
    """
    Tests para el servicio de notificaciones.
    """
    
    @pytest.fixture(scope="class")
    def test_person(self):
        """Fixture para crear persona de prueba."""
        # Usar get_or_create para evitar duplicados
        person, created = Person.objects.get_or_create(
            phone=TEST_PHONE,
            defaults={
                'nombre': TEST_NAME,
                'email': TEST_EMAIL,
                'telegram_id': TEST_TELEGRAM_ID,
                'whatsapp_enabled': True
            }
        )
        return person
        
    @pytest.fixture(scope="class")
    def notification_service(self):
        """Fixture para crear servicio de notificaciones."""
        return NotificationService()
        
    @pytest.mark.asyncio
    async def test_send_notification_whatsapp(self, test_person, notification_service):
        """Test de envío de notificación por WhatsApp."""
        with patch.object(WhatsAppApi, 'send_message', return_value=True):
            notification = await notification_service.send_notification(
                recipient=test_person,
                notification_type='TEST',
                content='Mensaje de prueba - WhatsApp',
                metadata={'test': True}
            )
            
            assert notification is not None
            assert notification.recipient == test_person
            assert notification.notification_type == 'TEST'
            assert notification.status == 'SENT'
            
    @pytest.mark.asyncio
    async def test_send_notification_email(self, test_person, notification_service):
        """Test de envío de notificación por Email."""
        # Deshabilitar WhatsApp temporalmente
        test_person.whatsapp_enabled = False
        await test_person.asave()
        
        with patch('asyncio.to_thread', return_value=1):
            notification = await notification_service.send_notification(
                recipient=test_person,
                notification_type='TEST',
                content='Mensaje de prueba - Email',
                metadata={'test': True}
            )
            
            assert notification is not None
            assert notification.recipient == test_person
            assert notification.notification_type == 'TEST'
            assert notification.status == 'SENT'
            
        # Restaurar configuración
        test_person.whatsapp_enabled = True
        await test_person.asave()
        
    @pytest.mark.asyncio
    async def test_mark_as_read(self, test_person, notification_service):
        """Test de marcar notificación como leída."""
        notification = await Notification.objects.acreate(
            recipient=test_person,
            notification_type='TEST',
            content='Prueba marcar como leída',
            status='SENT'
        )
        
        result = await notification_service.mark_as_read(notification.id)
        
        assert result is True
        updated = await Notification.objects.aget(id=notification.id)
        assert updated.status == 'READ'
        
    @pytest.mark.asyncio
    async def test_get_unread_notifications(self, test_person, notification_service):
        """Test de obtener notificaciones no leídas."""
        # Crear notificaciones de prueba
        await Notification.objects.acreate(
            recipient=test_person,
            notification_type='TEST',
            content='Notificación 1',
            status='SENT'
        )
        
        await Notification.objects.acreate(
            recipient=test_person,
            notification_type='TEST',
            content='Notificación 2',
            status='DELIVERED'
        )
        
        # Marcar una como leída
        notification = await Notification.objects.acreate(
            recipient=test_person,
            notification_type='TEST',
            content='Notificación 3',
            status='SENT'
        )
        notification.status = 'READ'
        await notification.asave()
        
        # Obtener no leídas
        unread = await notification_service.get_unread_notifications(test_person)
        
        assert len(unread) >= 2
        statuses = [n.status for n in unread]
        assert all(s in ['SENT', 'DELIVERED'] for s in statuses)
        
if __name__ == "__main__":
    pytest.main()
