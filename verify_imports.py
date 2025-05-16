import os
import re

def verify_imports():
    # Archivos principales a verificar
    main_files = [
        'app/admin.py',
        'app/admin_config.py',
        'app/forms.py',
        'app/utils.py',
        'app/urls.py',
        'app/tasks.py'
    ]
    
    # Patrones de importación obsoletos
    patterns = {
        'old_chatbot': r'from app.chatbot',
        'old_models': r'from app\.[a-zA-Z_]+\.models',
        'old_services': r'from app.services',
        'old_utils': r'from app.utils'
    }
    
    # Verificar cada archivo
    for file_path in main_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                
            for name, pattern in patterns.items():
                if re.search(pattern, content):
                    print(f"⚠️ {file_path} tiene importaciones obsoletas ({name})")
                    print("Contenido:")
                    print(content)
                    print("-" * 80)

if __name__ == "__main__":
    verify_imports()
