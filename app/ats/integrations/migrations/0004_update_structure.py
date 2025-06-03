from django.db import migrations
import os
import shutil
from pathlib import Path

def update_structure(apps, schema_editor):
    """
    Actualiza la estructura de los archivos de integración.
    """
    # Directorios base
    base_dir = Path('app/ats/integrations')
    channels_dir = base_dir / 'channels'
    
    # Crear directorios necesarios
    channels_dir.mkdir(exist_ok=True)
    (channels_dir / 'whatsapp').mkdir(exist_ok=True)
    (channels_dir / 'telegram').mkdir(exist_ok=True)
    (channels_dir / 'instagram').mkdir(exist_ok=True)
    (channels_dir / 'slack').mkdir(exist_ok=True)
    (channels_dir / 'messenger').mkdir(exist_ok=True)
    
    # Mover archivos de handlers
    handlers = {
        'whatsapp': {
            'source': 'app/ats/chatbot/integrations/whatsapp.py',
            'dest': 'app/ats/integrations/channels/whatsapp/handler.py'
        },
        'telegram': {
            'source': 'app/ats/chatbot/integrations/telegram.py',
            'dest': 'app/ats/integrations/channels/telegram/handler.py'
        },
        'instagram': {
            'source': 'app/ats/chatbot/integrations/instagram.py',
            'dest': 'app/ats/integrations/channels/instagram/handler.py'
        },
        'slack': {
            'source': 'app/ats/chatbot/integrations/slack.py',
            'dest': 'app/ats/integrations/channels/slack/handler.py'
        },
        'messenger': {
            'source': 'app/ats/chatbot/integrations/messenger.py',
            'dest': 'app/ats/integrations/channels/messenger/handler.py'
        }
    }
    
    for channel, paths in handlers.items():
        try:
            if os.path.exists(paths['source']):
                # Crear directorio de destino si no existe
                os.makedirs(os.path.dirname(paths['dest']), exist_ok=True)
                
                # Copiar archivo
                shutil.copy2(paths['source'], paths['dest'])
                
                # Crear archivo __init__.py en el directorio del canal
                init_file = os.path.join(os.path.dirname(paths['dest']), '__init__.py')
                if not os.path.exists(init_file):
                    with open(init_file, 'w') as f:
                        f.write(f'from .handler import {channel.capitalize()}Handler\n')
                        
        except Exception as e:
            print(f"Error procesando {channel}: {str(e)}")
    
    # Crear archivo __init__.py en el directorio channels
    channels_init = os.path.join(channels_dir, '__init__.py')
    if not os.path.exists(channels_init):
        with open(channels_init, 'w') as f:
            f.write('from .whatsapp.handler import WhatsAppHandler\n')
            f.write('from .telegram.handler import TelegramHandler\n')
            f.write('from .instagram.handler import InstagramHandler\n')
            f.write('from .slack.handler import SlackHandler\n')
            f.write('from .messenger.handler import MessengerHandler\n')

def reverse_structure(apps, schema_editor):
    """
    Revierte los cambios en la estructura de archivos.
    """
    # Directorios a eliminar
    channels_dir = Path('app/ats/integrations/channels')
    
    if channels_dir.exists():
        shutil.rmtree(channels_dir)

class Migration(migrations.Migration):
    dependencies = [
        ('integrations', '0003_update_remaining_references'),
    ]

    operations = [
        migrations.RunPython(update_structure, reverse_structure),
    ] 