from django.db import migrations
import re

def update_imports(apps, schema_editor):
    """
    Actualiza las referencias a los módulos de integración en los archivos del proyecto.
    """
    # Patrones de búsqueda y reemplazo
    patterns = [
        # Servicios
        (r'from app\.ats\.chatbot\.integrations\.services import (.*)',
         r'from app.ats.integrations.services import \1'),
        
        # Handlers específicos
        (r'from app\.ats\.chatbot\.integrations\.(whatsapp|telegram|instagram|slack|messenger) import (.*)',
         r'from app.ats.integrations.\1 import \2'),
        
        # Procesadores de documentos
        (r'from app\.ats\.chatbot\.integrations\.enhanced_document_processor import (.*)',
         r'from app.ats.integrations.document_processor import \1'),
        
        # Mensajes
        (r'from app\.ats\.chatbot\.integrations\.message_sender import (.*)',
         r'from app.ats.integrations.message_sender import \1'),
        
        # Email
        (r'from app\.ats\.chatbot\.integrations\.email import (.*)',
         r'from app.ats.integrations.email import \1'),
        
        # Handlers
        (r'from app\.ats\.chatbot\.integrations\.handlers import (.*)',
         r'from app.ats.integrations.handlers import \1'),
    ]
    
    # Archivos a actualizar
    files_to_update = [
        'app/views/webhook_views.py',
        'app/ats/onboarding/client_feedback_controller.py',
        'app/views/proposals/views.py',
        'app/views/main_views.py',
        'app/ats/notifications/handlers.py',
        'app/ats/kanban/views.py',
        'app/ats/publish/integrations/whatsapp.py',
        'app/views/chatbot_views.py',
        'app/ats/utils/vacantes.py',
        'app/ats/utils/scraping.py',
        'app/ats/utils/notification_service.py',
        'app/ats/utils/parser.py',
        'app/views/util_views.py',
        'app/ats/chatbot/core/intents_handler.py',
        'app/ats/chatbot/core/gpt.py',
        'app/ats/chatbot/core/chatbot.py',
        'app/ats/chatbot/workflow/common/jobs/jobs.py',
        'app/ats/chatbot/workflow/business_units/huntu/huntu.py',
        'app/ats/chatbot/workflow/business_units/sexsi/sexsi.py',
        'app/ats/chatbot/workflow/common/common.py',
        'app/ats/chatbot/workflow/business_units/huntred_executive.py',
        'app/ats/chatbot/workflow/business_units/huntred/huntred.py',
        'app/ats/chatbot/workflow/business_units/amigro/amigro.py',
        'app/ats/chatbot/nlp/generate_embeddings.py',
        'app/ats/chatbot/components/chat_state_manager.py',
    ]
    
    for file_path in files_to_update:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Aplicar cada patrón de reemplazo
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            
            # Guardar los cambios
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except FileNotFoundError:
            print(f"Archivo no encontrado: {file_path}")
        except Exception as e:
            print(f"Error al procesar {file_path}: {str(e)}")

def reverse_imports(apps, schema_editor):
    """
    Revierte los cambios en las importaciones.
    """
    # Patrones de búsqueda y reemplazo (en orden inverso)
    patterns = [
        # Handlers
        (r'from app\.ats\.integrations\.handlers import (.*)',
         r'from app.ats.integrations.handlers import \1'),
        
        # Email
        (r'from app\.ats\.integrations\.email import (.*)',
         r'from app.ats.integrations.services.email import \1'),
        
        # Mensajes
        (r'from app\.ats\.integrations\.message_sender import (.*)',
         r'from app.ats.integrations.services.message import \1'),
        
        # Procesadores de documentos
        (r'from app\.ats\.integrations\.document_processor import (.*)',
         r'from app.ats.integrations.services.document import \1'),
        
        # Handlers específicos
        (r'from app\.ats\.integrations\.(whatsapp|telegram|instagram|slack|messenger) import (.*)',
         r'from app.ats.chatbot.integrations.\1 import \2'),
        
        # Servicios
        (r'from app\.ats\.integrations\.services import (.*)',
         r'from app.ats.integrations.services import \1'),
    ]
    
    # Archivos a actualizar
    files_to_update = [
        'app/views/webhook_views.py',
        'app/ats/onboarding/client_feedback_controller.py',
        'app/views/proposals/views.py',
        'app/views/main_views.py',
        'app/ats/notifications/handlers.py',
        'app/ats/kanban/views.py',
        'app/ats/publish/integrations/whatsapp.py',
        'app/views/chatbot_views.py',
        'app/ats/utils/vacantes.py',
        'app/ats/utils/scraping.py',
        'app/ats/utils/notification_service.py',
        'app/ats/utils/parser.py',
        'app/views/util_views.py',
        'app/ats/chatbot/core/intents_handler.py',
        'app/ats/chatbot/core/gpt.py',
        'app/ats/chatbot/core/chatbot.py',
        'app/ats/chatbot/workflow/common/jobs/jobs.py',
        'app/ats/chatbot/workflow/business_units/huntu/huntu.py',
        'app/ats/chatbot/workflow/business_units/sexsi/sexsi.py',
        'app/ats/chatbot/workflow/common/common.py',
        'app/ats/chatbot/workflow/business_units/huntred_executive.py',
        'app/ats/chatbot/workflow/business_units/huntred/huntred.py',
        'app/ats/chatbot/workflow/business_units/amigro/amigro.py',
        'app/ats/chatbot/nlp/generate_embeddings.py',
        'app/ats/chatbot/components/chat_state_manager.py',
    ]
    
    for file_path in files_to_update:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Aplicar cada patrón de reemplazo
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            
            # Guardar los cambios
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except FileNotFoundError:
            print(f"Archivo no encontrado: {file_path}")
        except Exception as e:
            print(f"Error al procesar {file_path}: {str(e)}")

class Migration(migrations.Migration):
    dependencies = [
        ('integrations', '0002_update_imports'),
    ]

    operations = [
        migrations.RunPython(update_imports, reverse_imports),
    ] 