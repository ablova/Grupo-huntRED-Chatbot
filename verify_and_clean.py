import os
import shutil

def verify_and_clean():
    # Directorios a verificar
    obsolete_dirs = [
        'app/services',
        'app/com/chatbot/integrations',
        'app/com/chatbot/workflow',
        'app/com/chatbot/state'
    ]
    
    # Verificar y eliminar directorios vacíos
    for dir_path in obsolete_dirs:
        if os.path.exists(dir_path):
            try:
                # Verificar si está vacío
                if not os.listdir(dir_path):
                    print(f"✅ {dir_path} está vacío y será eliminado")
                    shutil.rmtree(dir_path)
                else:
                    print(f"⚠️ {dir_path} NO está vacío. Contiene:")
                    for item in os.listdir(dir_path):
                        print(f"  - {item}")
            except Exception as e:
                print(f"❌ Error al procesar {dir_path}: {str(e)}")

if __name__ == "__main__":
    verify_and_clean()
