import os
import re
from pathlib import Path

# Mapeo de rutas antiguas a nuevas
PATH_MAPPING = {
    'app.ats.chatbot.integrations.services': 'app.ats.integrations.services',
    'app.ats.chatbot.integrations.whatsapp': 'app.ats.integrations.channels.whatsapp',
    'app.ats.chatbot.integrations.telegram': 'app.ats.integrations.channels.telegram',
    'app.ats.chatbot.integrations.slack': 'app.ats.integrations.channels.slack',
    'app.ats.chatbot.integrations.instagram': 'app.ats.integrations.channels.instagram',
    'app.ats.chatbot.integrations.messenger': 'app.ats.integrations.channels.messenger',
    'app.ats.chatbot.integrations.x': 'app.ats.integrations.channels.x',
    'app.ats.chatbot.integrations.email': 'app.ats.integrations.services.email',
    'app.ats.chatbot.integrations.verification': 'app.ats.integrations.services.verification',
    'app.ats.chatbot.integrations.invitaciones': 'app.ats.integrations.services.invitations',
    'app.ats.chatbot.integrations.enhanced_document_processor': 'app.ats.integrations.services.document',
    'app.ats.chatbot.integrations.message_sender': 'app.ats.integrations.services.message',
    'app.ats.chatbot.integrations.handlers': 'app.ats.integrations.handlers',
}

def update_file_imports(file_path):
    """Actualiza las importaciones en un archivo."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    for old_path, new_path in PATH_MAPPING.items():
        pattern = re.compile(f'from {old_path} import')
        if pattern.search(content):
            content = pattern.sub(f'from {new_path} import', content)
            modified = True
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated imports in {file_path}")

def process_directory(directory):
    """Procesa todos los archivos Python en un directorio."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                update_file_imports(file_path)

if __name__ == '__main__':
    # Directorios a procesar
    directories = [
        'app/ats/integrations',
        'app/ats/chatbot',
        'app/views',
        'app/tests',
        'app/sexsi',
        'app/ats/notifications',
        'app/ats/onboarding',
        'app/ats/kanban',
        'app/ats/utils',
        'app/ats/publish',
    ]
    
    for directory in directories:
        if os.path.exists(directory):
            process_directory(directory) 