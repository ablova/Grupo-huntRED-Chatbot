"""
Módulo de soporte para permitir migraciones en entornos locales.
Este módulo "monkeypatches" Django para evitar que intente cargar adaptadores PostgreSQL
durante la inicialización cuando sólo se está usando SQLite.

Uso:
    python local_sqlite_hack.py makemigrations
    python local_sqlite_hack.py migrate
"""
import sys
import warnings
import importlib.util
import os
import django
from importlib import import_module
from types import ModuleType

class DummyPostgresModule(ModuleType):
    """Módulo dummy para simular PostgreSQL."""
    def __getattr__(self, name):
        return None

def patch_postgres_imports():
    """
    Aplica monkey patch para evitar errores de importación de PostgreSQL
    cuando se está utilizando SQLite para desarrollo.
    """
    # Crear módulos dummy para psycopg y psycopg2
    sys.modules['psycopg'] = DummyPostgresModule('psycopg')
    sys.modules['psycopg2'] = DummyPostgresModule('psycopg2')
    
    # Suprime advertencias específicas
    warnings.filterwarnings("ignore", message=".*psycopg.*")
    
    # Forzar configuración de SQLite
    os.environ['FORCE_SQLITE'] = 'true'
    os.environ['LOCAL_DEV'] = 'true'
    os.environ['DEBUG'] = 'true'
    os.environ['PRODUCTION'] = 'false'
    
    print("🔧 Aplicado patch para usar SQLite en entorno local")
    print("🪄 Ignorando dependencias de PostgreSQL")

def main():
    # Aplicar el monkey patch
    patch_postgres_imports()
    
    # Importar manage.py y ejecutar comandos
    try:
        # Ejecutar el comando original
        django_command = ' '.join(sys.argv[1:])
        print(f"🚀 Ejecutando: {django_command}")
        
        # Ejecutar el comando usando manage.py
        from manage import main as manage_main
        manage_main()
        
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Error: Debe proporcionar un comando de Django")
        print("Uso: python local_sqlite_hack.py [comando]")
        print("Ejemplo: python local_sqlite_hack.py makemigrations")
        sys.exit(1)
    main()
