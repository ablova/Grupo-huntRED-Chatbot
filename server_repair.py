#!/usr/bin/env python3
"""
Script de reparación y optimización del servidor para Grupo huntRED®.
Responsable de verificar y configurar todos los componentes necesarios.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import shutil
import json
import django
from django.core.management import call_command
import psutil
import platform
import socket
import requests
from datetime import datetime
import yaml
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server_repair.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ServerRepair:
    def __init__(self):
        self.base_dir = Path(os.getcwd())
        self.app_dir = self.base_dir / 'app'
        self.venv_dir = self.base_dir / 'venv'
        self.requirements_file = self.base_dir / 'requirements.txt'
        self.backup_dir = self.base_dir / 'backups'
        self.log_dir = self.base_dir / 'logs'
        self.config_file = self.base_dir / 'config.yaml'
        
    def run(self):
        """Ejecuta todas las tareas de reparación"""
        try:
            logger.info("Iniciando proceso de reparación del servidor...")
            
            # 1. Verificar sistema
            self.check_system()
            
            # 2. Crear directorios necesarios
            self.create_required_dirs()
            
            # 3. Verificar estructura de directorios
            self.check_directory_structure()
            
            # 4. Verificar y actualizar dependencias
            self.check_dependencies()
            
            # 5. Verificar configuración de Django
            self.check_django_config()
            
            # 6. Verificar base de datos
            self.check_database()
            
            # 7. Limpiar archivos temporales y backups
            self.cleanup_files()
            
            # 8. Verificar permisos
            self.check_permissions()
            
            # 9. Verificar servicios
            self.check_services()
            
            # 10. Crear backup
            self.create_backup()
            
            # 11. Verificar configuración
            self.check_configuration()
            
            logger.info("Proceso de reparación completado exitosamente")
            
        except Exception as e:
            logger.error(f"Error durante la reparación: {str(e)}")
            sys.exit(1)

    def check_system(self):
        """Verifica el estado del sistema"""
        logger.info("Verificando estado del sistema...")
        
        # Información del sistema
        system_info = {
            'platform': platform.platform(),
            'python_version': sys.version,
            'hostname': socket.gethostname(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'disk_usage': psutil.disk_usage('/').percent,
            'python_path': sys.executable,
            'environment': os.environ.get('DJANGO_SETTINGS_MODULE', 'No configurado')
        }
        
        logger.info(f"Información del sistema: {json.dumps(system_info, indent=2)}")
        
        # Verificar memoria disponible
        if psutil.virtual_memory().available < 1024 * 1024 * 100:  # Menos de 100MB
            logger.warning("Memoria disponible baja")
            
        # Verificar espacio en disco
        if psutil.disk_usage('/').percent > 90:
            logger.warning("Espacio en disco bajo")
            
        # Verificar conexión a internet
        try:
            requests.get('https://www.google.com', timeout=5)
            logger.info("Conexión a internet verificada")
        except requests.RequestException:
            logger.warning("No hay conexión a internet")

    def create_required_dirs(self):
        """Crea directorios necesarios para el funcionamiento"""
        logger.info("Creando directorios necesarios...")
        
        required_dirs = [
            self.backup_dir,
            self.log_dir,
            self.base_dir / 'static',
            self.base_dir / 'media',
            self.base_dir / 'temp',
            self.base_dir / 'logs/nginx',
            self.base_dir / 'logs/gunicorn',
            self.base_dir / 'logs/celery'
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                logger.info(f"Creando directorio: {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)

    def check_directory_structure(self):
        """Verifica la estructura de directorios necesaria"""
        logger.info("Verificando estructura de directorios...")
        
        required_dirs = [
            'app/com/chatbot',
            'app/com/chatbot/core',
            'app/com/chatbot/nlp',
            'app/com/chatbot/components',
            'app/com/chatbot/models',
            'app/com/chatbot/views',
            'app/com/chatbot/urls',
            'app/com/chatbot/validation',
            'app/com/chatbot/values',
            'app/com/chatbot/middleware',
            'app/com/chatbot/flow',
            'app/com/chatbot/core/intents',
            'app/com/chatbot/ml',
            'app/com/chatbot/services',
            'app/com/chatbot/workflow',
            'app/com/chatbot/utils',
            'app/com/chatbot/integrations',
            'app/com/chatbot/handlers'
        ]
        
        for dir_path in required_dirs:
            full_path = self.base_dir / dir_path
            if not full_path.exists():
                logger.info(f"Creando directorio: {dir_path}")
                full_path.mkdir(parents=True, exist_ok=True)
                
            # Verificar __init__.py
            init_file = full_path / '__init__.py'
            if not init_file.exists():
                logger.info(f"Creando __init__.py en: {dir_path}")
                with open(init_file, 'w') as f:
                    f.write(f'"""\nMódulo {dir_path.split("/")[-1]} del chatbot para Grupo huntRED®.\n"""')

    def check_dependencies(self):
        """Verifica y actualiza las dependencias del proyecto"""
        logger.info("Verificando dependencias...")
        
        # Activar entorno virtual si existe
        if self.venv_dir.exists():
            activate_script = self.venv_dir / 'bin' / 'activate'
            if sys.platform == 'win32':
                activate_script = self.venv_dir / 'Scripts' / 'activate.bat'
            
            if activate_script.exists():
                logger.info("Activando entorno virtual...")
                if sys.platform == 'win32':
                    os.system(f'call {activate_script}')
                else:
                    os.system(f'source {activate_script}')
        else:
            logger.info("Creando entorno virtual...")
            subprocess.run([sys.executable, '-m', 'venv', str(self.venv_dir)])
        
        # Actualizar pip
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        
        # Instalar/actualizar dependencias
        if self.requirements_file.exists():
            logger.info("Instalando/actualizando dependencias...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(self.requirements_file)])
            
            # Verificar dependencias vulnerables
            try:
                subprocess.run([sys.executable, '-m', 'safety', 'check', '-r', str(self.requirements_file)])
            except Exception as e:
                logger.warning(f"No se pudo verificar vulnerabilidades: {str(e)}")
        else:
            logger.warning("No se encontró requirements.txt")

    def check_django_config(self):
        """Verifica la configuración de Django"""
        logger.info("Verificando configuración de Django...")
        
        try:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
            django.setup()
            
            # Verificar settings
            from django.conf import settings
            
            # Verificar configuración de seguridad
            if settings.DEBUG:
                logger.warning("DEBUG está activado en producción")
            
            # Verificar configuración de base de datos
            if not settings.DATABASES:
                logger.error("No hay configuración de base de datos")
                raise Exception("Configuración de base de datos faltante")
                
            # Verificar configuración de seguridad
            if not settings.SECRET_KEY:
                logger.error("SECRET_KEY no está configurada")
                raise Exception("SECRET_KEY faltante")
                
            # Verificar configuración de CORS
            if 'corsheaders' not in settings.INSTALLED_APPS:
                logger.warning("django-cors-headers no está instalado")
                
            logger.info("Configuración de Django cargada correctamente")
            
        except Exception as e:
            logger.error(f"Error en la configuración de Django: {str(e)}")
            raise

    def check_database(self):
        """Verifica y repara la base de datos"""
        logger.info("Verificando base de datos...")
        
        try:
            # Ejecutar migraciones
            call_command('makemigrations')
            call_command('migrate')
            
            # Verificar conexión
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                logger.info("Conexión a la base de datos verificada")
                
            # Verificar tablas
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = cursor.fetchall()
                logger.info(f"Tablas encontradas: {len(tables)}")
                
            # Verificar índices
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT schemaname, tablename, indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                """)
                indexes = cursor.fetchall()
                logger.info(f"Índices encontrados: {len(indexes)}")
                
        except Exception as e:
            logger.error(f"Error en la base de datos: {str(e)}")
            raise

    def cleanup_files(self):
        """Limpia archivos temporales y backups innecesarios"""
        logger.info("Limpiando archivos temporales...")
        
        # Eliminar archivos .pyc
        for pyc_file in self.base_dir.rglob('*.pyc'):
            pyc_file.unlink()
            
        # Eliminar archivos .py.bak innecesarios
        for bak_file in self.base_dir.rglob('*.py.bak'):
            # Verificar si el archivo original existe y está actualizado
            original_file = bak_file.with_suffix('')
            if original_file.exists():
                bak_file.unlink()
                logger.info(f"Eliminado backup innecesario: {bak_file}")
                
        # Limpiar directorio temp
        temp_dir = self.base_dir / 'temp'
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            temp_dir.mkdir()
            
        # Limpiar logs antiguos
        log_files = list(self.log_dir.rglob('*.log'))
        for log_file in log_files:
            if log_file.stat().st_mtime < (datetime.now().timestamp() - 30 * 24 * 60 * 60):  # 30 días
                log_file.unlink()
                logger.info(f"Eliminado log antiguo: {log_file}")

    def check_permissions(self):
        """Verifica y corrige permisos de archivos y directorios"""
        logger.info("Verificando permisos...")
        
        # Establecer permisos para directorios
        for dir_path in self.base_dir.rglob('*'):
            if dir_path.is_dir():
                os.chmod(dir_path, 0o755)
                
        # Establecer permisos para archivos Python
        for py_file in self.base_dir.rglob('*.py'):
            os.chmod(py_file, 0o644)
            
        # Establecer permisos para archivos de configuración
        for config_file in self.base_dir.rglob('*.env'):
            os.chmod(config_file, 0o600)
            
        # Establecer permisos para archivos de log
        for log_file in self.log_dir.rglob('*.log'):
            os.chmod(log_file, 0o644)

    def check_services(self):
        """Verifica el estado de los servicios necesarios"""
        logger.info("Verificando servicios...")
        
        # Verificar puertos necesarios
        required_ports = [8000, 5432, 6379]  # Django, PostgreSQL, Redis
        for port in required_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            if result == 0:
                logger.info(f"Puerto {port} está abierto")
            else:
                logger.warning(f"Puerto {port} está cerrado")
            sock.close()
            
        # Verificar servicios del sistema
        required_services = ['nginx', 'postgresql', 'redis-server']
        for service in required_services:
            try:
                subprocess.run(['systemctl', 'is-active', service], check=True)
                logger.info(f"Servicio {service} está activo")
            except subprocess.CalledProcessError:
                logger.warning(f"Servicio {service} no está activo")

    def create_backup(self):
        """Crea un backup del sistema"""
        logger.info("Creando backup del sistema...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f'backup_{timestamp}'
        
        # Crear directorio de backup
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Copiar archivos importantes
        important_files = [
            'requirements.txt',
            'manage.py',
            'app/settings.py',
            'app/urls.py',
            '.env',
            'config.yaml'
        ]
        
        for file in important_files:
            src = self.base_dir / file
            if src.exists():
                dst = backup_path / file
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                
        # Backup de la base de datos
        try:
            from django.conf import settings
            db_name = settings.DATABASES['default']['NAME']
            backup_file = backup_path / f'db_backup_{timestamp}.sql'
            
            subprocess.run([
                'pg_dump',
                '-U', settings.DATABASES['default']['USER'],
                '-h', settings.DATABASES['default']['HOST'],
                db_name,
                '-f', str(backup_file)
            ])
            
            logger.info(f"Backup creado en: {backup_path}")
            
        except Exception as e:
            logger.error(f"Error al crear backup de la base de datos: {str(e)}")
            
    def check_configuration(self):
        """Verifica la configuración del sistema"""
        logger.info("Verificando configuración del sistema...")
        
        # Verificar archivo de configuración
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info("Archivo de configuración cargado correctamente")
            except Exception as e:
                logger.error(f"Error al cargar archivo de configuración: {str(e)}")
        else:
            logger.warning("No se encontró archivo de configuración")
            
        # Verificar variables de entorno
        required_env_vars = [
            'DJANGO_SETTINGS_MODULE',
            'SECRET_KEY',
            'DATABASE_URL',
            'REDIS_URL'
        ]
        
        for var in required_env_vars:
            if not os.getenv(var):
                logger.warning(f"Variable de entorno {var} no está configurada")

def main():
    repair = ServerRepair()
    repair.run()

if __name__ == '__main__':
    main()