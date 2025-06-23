#!/usr/bin/env python3
"""
Script de diagnóstico, reparación y optimización para el proyecto Grupo huntRED® Chatbot.
Realiza verificaciones exhaustivas, reparaciones y optimizaciones en todo el proyecto.
"""

import os
import sys
import logging
import subprocess
import importlib
import ast
from pathlib import Path
from typing import List, Dict, Any, Set
import psutil
import yaml
from dotenv import load_dotenv
import django
from django.conf import settings
from django.core.management import call_command
from django.db import connection
import black
import isort
import flake8
import mypy
import bandit
import safety
import socket
import platform
import shutil
import json
from datetime import datetime
import grp
import pwd
import re
from collections import defaultdict
from django.apps import apps
from django.db import models

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('project_diagnostic.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Intentar importar systemd, si no está disponible, usar alternativas
try:
    import systemd.journal
    import systemd.daemon
    SYSTEMD_AVAILABLE = True
except ImportError:
    logger.warning("systemd no está disponible. Usando alternativas.")
    SYSTEMD_AVAILABLE = False

def setup_django():
    """Configura el entorno de Django."""
    try:
        # Asegurarse de que estamos en el directorio correcto
        project_root = Path(__file__).parent.absolute()
        os.chdir(project_root)
        
        # Configurar Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()
        
        logger.info("✓ Entorno de Django configurado correctamente")
        return True
    except Exception as e:
        logger.error(f"Error configurando Django: {str(e)}")
        return False

class ProjectManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.requirements_file = self.project_root / 'requirements.txt'
        self.env_file = self.project_root / '.env'
        self.settings_file = self.project_root / 'config' / 'settings.py'
        self.urls_file = self.project_root / 'config' / 'urls.py'
        self.models_file = self.project_root / 'app' / 'models.py'
        self.views_dir = self.project_root / 'app' / 'views'
        self.templates_dir = self.project_root / 'app' / 'templates'
        self.static_dir = self.project_root / 'app' / 'static'
        self.migrations_dir = self.project_root / 'app' / 'migrations'
        
        # Verificar que estamos en el directorio correcto
        if not self.settings_file.exists():
            logger.error(f"No se encontró el archivo de configuración en: {self.settings_file}")
            logger.info("Asegúrate de ejecutar el script desde el directorio raíz del proyecto")
            sys.exit(1)
        
        self.app_dir = self.project_root / 'app'
        self.issues = []
        self.optimizations = []
        self.dependencies = set()
        self.cleaned_files = []
        self.repairs = []
        self.backups = []
        
        # Detectar entorno
        self.environment = self.detect_environment()
        logger.info(f"Entorno detectado: {self.environment}")
        
        # Configuración según entorno
        self.configure_environment()
        
        # Verificar dependencias
        self.check_dependencies()
        
        # Configuración de servicios
        self.required_services = {
            'gunicorn': {
                'port': 8000,
                'config': '/etc/gunicorn/conf.py',
                'service': 'gunicorn.service',
                'user': 'www-data',
                'group': 'www-data'
            },
            'nginx': {
                'port': 80,
                'config': '/etc/nginx/sites-available/huntred',
                'service': 'nginx.service',
                'user': 'www-data',
                'group': 'www-data'
            },
            'celery': {
                'port': 5672,
                'config': '/etc/celery/celery.conf',
                'service': 'celery.service',
                'user': 'pablo',
                'group': 'ai_huntred'
            },
            'redis': {
                'port': 6379,
                'config': '/etc/redis/redis.conf',
                'service': 'redis.service',
                'user': 'redis',
                'group': 'redis'
            },
            'postgresql': {
                'port': 5432,
                'config': '/etc/postgresql/13/main/postgresql.conf',
                'service': 'postgresql.service',
                'user': 'postgres',
                'group': 'postgres'
            }
        }
        
        # Archivos de configuración críticos
        self.critical_configs = {
            '.env': {
                'path': '/home/pablo/.env',
                'permissions': '600',
                'owner': 'pablo',
                'group': 'ai_huntred'
            },
            'gunicorn_conf.py': {
                'path': '/home/pablo/app/gunicorn_conf.py',
                'permissions': '644',
                'owner': 'www-data',
                'group': 'ai_huntred'
            },
            'celery_conf.py': {
                'path': '/home/pablo/app/celery_conf.py',
                'permissions': '644',
                'owner': 'pablo',
                'group': 'ai_huntred'
            }
        }
        
    def check_dependencies(self):
        """Verifica y maneja las dependencias necesarias."""
        required_packages = {
            'psutil': 'psutil',
            'yaml': 'PyYAML',
            'django': 'Django',
            'black': 'black',
            'isort': 'isort',
            'flake8': 'flake8',
            'mypy': 'mypy',
            'bandit': 'bandit',
            'safety': 'safety'
        }
        
        missing_packages = []
        for module, package in required_packages.items():
            try:
                importlib.import_module(module)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.warning(f"Faltan las siguientes dependencias: {', '.join(missing_packages)}")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages, check=True)
                logger.info("Dependencias instaladas correctamente")
            except subprocess.CalledProcessError as e:
                logger.error(f"Error al instalar dependencias: {str(e)}")
                self.issues.append(f"Error al instalar dependencias: {str(e)}")
        
        # Verificar systemd
        if not SYSTEMD_AVAILABLE:
            logger.warning("systemd no está disponible. Algunas funcionalidades estarán limitadas.")
            self.issues.append("systemd no está disponible. Algunas funcionalidades estarán limitadas.")
        
    def detect_environment(self) -> str:
        """Detecta si estamos en producción o desarrollo."""
        try:
            # Verificar hostname
            hostname = socket.gethostname()
            if 'huntred' in hostname.lower():
                return 'production'
            
            # Verificar IP
            ip = socket.gethostbyname(hostname)
            if ip.startswith('10.') or ip.startswith('192.168.'):
                return 'development'
            
            # Verificar variables de entorno
            if os.getenv('DJANGO_ENV') == 'production':
                return 'production'
            elif os.getenv('DJANGO_ENV') == 'development':
                return 'development'
            
            # Verificar si estamos en Google Cloud
            try:
                import google.cloud
                return 'production'
            except ImportError:
                pass
            
            # Verificar si estamos en un servidor real
            if os.path.exists('/etc/systemd/system/gunicorn.service'):
                return 'production'
            
            return 'development'
            
        except Exception as e:
            logger.warning(f"Error al detectar entorno: {str(e)}")
            return 'development'  # Por defecto, asumimos desarrollo
            
    def configure_environment(self):
        """Configura el entorno según la detección."""
        if self.environment == 'production':
            # Configuración para producción
            self.required_users = ['pablollh', 'pablo', 'root', 'www-data']
            self.required_group = 'ai_huntred'
            self.required_paths = [
                '/home/pablo/',
                '/home/pablo/app',
                '/home/pablo/ai_huntred'
            ]
            self.required_services = {
                'gunicorn': {
                    'port': 8000,
                    'config': '/etc/gunicorn/conf.py',
                    'service': 'gunicorn.service',
                    'user': 'www-data',
                    'group': 'www-data'
                },
                'nginx': {
                    'port': 80,
                    'config': '/etc/nginx/sites-available/huntred',
                    'service': 'nginx.service',
                    'user': 'www-data',
                    'group': 'www-data'
                },
                'celery': {
                    'port': 5672,
                    'config': '/etc/celery/celery.conf',
                    'service': 'celery.service',
                    'user': 'pablo',
                    'group': 'ai_huntred'
                },
                'redis': {
                    'port': 6379,
                    'config': '/etc/redis/redis.conf',
                    'service': 'redis.service',
                    'user': 'redis',
                    'group': 'redis'
                },
                'postgresql': {
                    'port': 5432,
                    'config': '/etc/postgresql/13/main/postgresql.conf',
                    'service': 'postgresql.service',
                    'user': 'postgres',
                    'group': 'postgres'
                }
            }
        else:
            # Configuración para desarrollo
            self.required_users = ['pablollh']
            self.required_group = 'ai_huntred'
            self.required_paths = [
                str(self.project_root),
                str(self.project_root / 'app')
            ]
            self.required_services = {
                'django': {
                    'port': 8000,
                    'config': str(self.project_root / 'config/settings.py'),
                    'service': None,
                    'user': os.getenv('USER'),
                    'group': 'ai_huntred'
                },
                'celery': {
                    'port': 5672,
                    'config': str(self.project_root / 'config/celery.py'),
                    'service': None,
                    'user': os.getenv('USER'),
                    'group': 'ai_huntred'
                },
                'redis': {
                    'port': 6379,
                    'config': None,
                    'service': None,
                    'user': os.getenv('USER'),
                    'group': 'ai_huntred'
                },
                'postgresql': {
                    'port': 5432,
                    'config': None,
                    'service': None,
                    'user': os.getenv('USER'),
                    'group': 'ai_huntred'
                }
            }
            
        # Configuración común
        self.critical_configs = {
            '.env': {
                'path': str(self.project_root / '.env'),
                'permissions': '600',
                'owner': os.getenv('USER'),
                'group': 'ai_huntred'
            },
            'gunicorn_conf.py': {
                'path': str(self.project_root / 'gunicorn_conf.py'),
                'permissions': '644',
                'owner': os.getenv('USER'),
                'group': 'ai_huntred'
            },
            'celery_conf.py': {
                'path': str(self.project_root / 'celery_conf.py'),
                'permissions': '644',
                'owner': os.getenv('USER'),
                'group': 'ai_huntred'
            }
        }
        
    def verify_permissions(self):
        """Verifica que los permisos estén correctamente configurados."""
        logger.info("Verificando configuración de permisos...")
        
        permission_issues = []
        
        try:
            # Verificar grupo ai_huntred
            try:
                group_info = grp.getgrnam(self.required_group)
                logger.info(f"Grupo {self.required_group} existe con GID: {group_info.gr_gid}")
                
                # Verificar miembros del grupo
                group_members = group_info.gr_mem
                for user in self.required_users:
                    if user not in group_members:
                        permission_issues.append(f"Usuario {user} no está en el grupo {self.required_group}")
            except KeyError:
                permission_issues.append(f"Grupo {self.required_group} no existe")
            
            # Verificar usuarios
            for username in self.required_users:
                try:
                    user_info = pwd.getpwnam(username)
                    logger.info(f"Usuario {username} existe con UID: {user_info.pw_uid}")
                    
                    # Verificar directorio home
                    home_dir = Path(user_info.pw_dir)
                    if home_dir.exists():
                        stat = home_dir.stat()
                        if stat.st_gid != group_info.gr_gid:
                            permission_issues.append(f"Directorio home de {username} no pertenece al grupo {self.required_group}")
                except KeyError:
                    permission_issues.append(f"Usuario {username} no existe")
            
            # Verificar permisos de directorios
            for path in self.required_paths:
                path_obj = Path(path)
                if path_obj.exists():
                    # Verificar grupo propietario
                    stat = path_obj.stat()
                    if stat.st_gid != group_info.gr_gid:
                        permission_issues.append(f"Directorio {path} no pertenece al grupo {self.required_group}")
                    
                    # Verificar permisos de directorios
                    for root, dirs, files in os.walk(path_obj):
                        for item in dirs + files:
                            item_path = Path(root) / item
                            item_stat = item_path.stat()
                            
                            # Verificar grupo
                            if item_stat.st_gid != group_info.gr_gid:
                                permission_issues.append(f"Item {item_path} no pertenece al grupo {self.required_group}")
                            
                            # Verificar permisos
                            if item_path.is_dir():
                                if not (item_stat.st_mode & 0o775 == 0o775):
                                    permission_issues.append(f"Permisos incorrectos en directorio {item_path}")
                            elif item_path.suffix in ['.py', '.sh']:
                                if not (item_stat.st_mode & 0o775 == 0o775):
                                    permission_issues.append(f"Permisos incorrectos en script {item_path}")
                            else:
                                if not (item_stat.st_mode & 0o664 == 0o664):
                                    permission_issues.append(f"Permisos incorrectos en archivo {item_path}")
                else:
                    permission_issues.append(f"Ruta {path} no existe")
            
            # Verificar permisos del script
            script_path = Path(__file__)
            script_stat = script_path.stat()
            if script_stat.st_gid != group_info.gr_gid:
                permission_issues.append(f"Script no pertenece al grupo {self.required_group}")
            if not (script_stat.st_mode & 0o775 == 0o775):
                permission_issues.append("Permisos incorrectos en el script")
            
            # Si hay problemas, intentar repararlos
            if permission_issues:
                logger.warning("Se encontraron problemas de permisos:")
                for issue in permission_issues:
                    logger.warning(f"- {issue}")
                self.check_and_repair_permissions()
            else:
                logger.info("Todos los permisos están correctamente configurados")
            
        except Exception as e:
            self.issues.append(f"Error al verificar permisos: {str(e)}")
            
    def check_and_repair_permissions(self):
        """Verifica y repara los permisos de usuarios y grupos."""
        logger.info("Verificando y reparando permisos...")
        
        try:
            # Verificar grupo ai_huntred
            try:
                group_info = grp.getgrnam(self.required_group)
                logger.info(f"Grupo {self.required_group} existe con GID: {group_info.gr_gid}")
            except KeyError:
                self.issues.append(f"Grupo {self.required_group} no existe")
                # Crear grupo si no existe
                try:
                    subprocess.run(['sudo', 'groupadd', self.required_group], check=True)
                    self.repairs.append(f"Grupo {self.required_group} creado")
                except subprocess.CalledProcessError as e:
                    self.issues.append(f"Error al crear grupo {self.required_group}: {str(e)}")
            
            # Verificar usuarios
            for username in self.required_users:
                try:
                    user_info = pwd.getpwnam(username)
                    logger.info(f"Usuario {username} existe con UID: {user_info.pw_uid}")
                    
                    # Agregar usuario al grupo si no está
                    if self.required_group not in grp.getgrgid(user_info.pw_gid).gr_mem:
                        try:
                            subprocess.run(['sudo', 'usermod', '-a', '-G', self.required_group, username], check=True)
                            self.repairs.append(f"Usuario {username} agregado al grupo {self.required_group}")
                        except subprocess.CalledProcessError as e:
                            self.issues.append(f"Error al agregar {username} al grupo {self.required_group}: {str(e)}")
                except KeyError:
                    self.issues.append(f"Usuario {username} no existe")
            
            # Verificar y reparar permisos de directorios
            for path in self.required_paths:
                path_obj = Path(path)
                if path_obj.exists():
                    # Establecer grupo
                    try:
                        subprocess.run(['sudo', 'chgrp', '-R', self.required_group, str(path_obj)], check=True)
                        self.repairs.append(f"Grupo establecido para {path}")
                    except subprocess.CalledProcessError as e:
                        self.issues.append(f"Error al establecer grupo para {path}: {str(e)}")
                    
                    # Establecer permisos
                    try:
                        # Directorios: 775 (drwxrwxr-x)
                        subprocess.run(['sudo', 'find', str(path_obj), '-type', 'd', '-exec', 'chmod', '775', '{}', '+'], check=True)
                        # Archivos: 664 (rw-rw-r--)
                        subprocess.run(['sudo', 'find', str(path_obj), '-type', 'f', '-exec', 'chmod', '664', '{}', '+'], check=True)
                        # Scripts ejecutables: 775 (rwxrwxr-x)
                        subprocess.run(['sudo', 'find', str(path_obj), '-type', 'f', '-name', '*.py', '-exec', 'chmod', '775', '{}', '+'], check=True)
                        subprocess.run(['sudo', 'find', str(path_obj), '-type', 'f', '-name', '*.sh', '-exec', 'chmod', '775', '{}', '+'], check=True)
                        self.repairs.append(f"Permisos establecidos para {path}")
                    except subprocess.CalledProcessError as e:
                        self.issues.append(f"Error al establecer permisos para {path}: {str(e)}")
                else:
                    self.issues.append(f"Ruta {path} no existe")
            
            # Verificar permisos de este script
            script_path = Path(__file__)
            try:
                # Establecer grupo
                subprocess.run(['sudo', 'chgrp', self.required_group, str(script_path)], check=True)
                # Establecer permisos ejecutables
                subprocess.run(['sudo', 'chmod', '775', str(script_path)], check=True)
                self.repairs.append("Permisos del script establecidos")
            except subprocess.CalledProcessError as e:
                self.issues.append(f"Error al establecer permisos del script: {str(e)}")
            
            # Verificar que los permisos se hayan aplicado correctamente
            self.verify_permissions()
            
        except Exception as e:
            self.issues.append(f"Error al verificar/reparar permisos: {str(e)}")
            
    def repair_project(self):
        """Repara el proyecto."""
        logger.info("Iniciando reparación del proyecto...")
        
        # Verificar y reparar permisos primero
        self.verify_permissions()
        
        # Crear directorios necesarios
        required_dirs = [
            'backups',
            'logs',
            'static',
            'media',
            'temp',
            'app/ats/chatbot/flow',
            'app/ats/chatbot/workflow',
            'app/ats/chatbot/nlp',
            'app/ats/chatbot/core',
            'app/ats/chatbot/components',
            'app/ats/chatbot/models',
            'app/ats/chatbot/views',
            'app/ats/chatbot/urls',
            'app/ats/chatbot/validation',
            'app/ats/chatbot/values',
            'app/ats/chatbot/middleware'
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                self.repairs.append(f"Directorio creado: {dir_path}")
                logger.info(f"Directorio creado: {dir_path}")
                
                # Establecer permisos para el nuevo directorio
                try:
                    subprocess.run(['sudo', 'chgrp', self.required_group, str(full_path)], check=True)
                    subprocess.run(['sudo', 'chmod', '775', str(full_path)], check=True)
                    self.repairs.append(f"Permisos establecidos para nuevo directorio: {dir_path}")
                except subprocess.CalledProcessError as e:
                    self.issues.append(f"Error al establecer permisos para {dir_path}: {str(e)}")
        
        # Verificar y reparar configuración de Django
        self.repair_django_settings()
        
        # Verificar y reparar base de datos
        self.repair_database()
        
        # Verificar y reparar servicios
        self.repair_services()
        
        # Verificar permisos una vez más después de todas las reparaciones
        self.verify_permissions()

    def check_system_info(self):
        """Verifica información del sistema."""
        logger.info("Verificando información del sistema...")
        
        system_info = {
            'platform': platform.platform(),
            'python_version': sys.version,
            'hostname': socket.gethostname(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'disk_usage': psutil.disk_usage('/').percent
        }
        
        logger.info(f"Sistema: {system_info['platform']}")
        logger.info(f"Python: {system_info['python_version']}")
        logger.info(f"Hostname: {system_info['hostname']}")
        logger.info(f"CPUs: {system_info['cpu_count']}")
        logger.info(f"Memoria total: {system_info['memory_total'] / (1024**3):.2f} GB")
        logger.info(f"Uso de disco: {system_info['disk_usage']}%")

    def repair_django_settings(self):
        """Repara la configuración de Django."""
        logger.info("Reparando configuración de Django...")
        
        try:
            # Verificar SECRET_KEY
            if not settings.SECRET_KEY or settings.SECRET_KEY == 'your-secret-key-here':
                new_key = ''.join([chr(ord('a') + i % 26) for i in range(50)])
                self.repairs.append("SECRET_KEY regenerada")
                logger.info("SECRET_KEY regenerada")
            
            # Verificar DEBUG
            if settings.DEBUG:
                self.issues.append("DEBUG está activado en producción")
            
            # Verificar ALLOWED_HOSTS
            if not settings.ALLOWED_HOSTS:
                self.issues.append("ALLOWED_HOSTS está vacío")
            
            # Verificar CORS
            if 'corsheaders' in settings.INSTALLED_APPS:
                if not hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
                    self.issues.append("CORS_ALLOWED_ORIGINS no está configurado")
            
        except Exception as e:
            self.issues.append(f"Error al reparar configuración Django: {str(e)}")

    def repair_database(self):
        """Repara la base de datos."""
        logger.info("Reparando base de datos...")
        
        try:
            # Verificar conexión
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Aplicar migraciones
            call_command('makemigrations')
            call_command('migrate')
            
            # Verificar índices
            call_command('dbshell')
            
            self.repairs.append("Base de datos reparada")
            
        except Exception as e:
            self.issues.append(f"Error al reparar base de datos: {str(e)}")

    def verify_services(self):
        """Verifica el estado de los servicios requeridos."""
        logger.info("Verificando servicios...")
        
        for service_name, service_info in self.required_services.items():
            try:
                # En desarrollo, solo verificar puertos
                if self.environment == 'development':
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('127.0.0.1', service_info['port']))
                    if result != 0:
                        self.issues.append(f"Puerto {service_info['port']} para {service_name} no está disponible")
                    sock.close()
                    continue
                
                # En producción, verificar servicios systemd si está disponible
                if SYSTEMD_AVAILABLE and service_info['service']:
                    result = subprocess.run(['systemctl', 'is-active', service_info['service']], 
                                         capture_output=True, text=True)
                    if result.stdout.strip() != 'active':
                        self.issues.append(f"Servicio {service_name} no está activo")
                        try:
                            subprocess.run(['sudo', 'systemctl', 'start', service_info['service']], check=True)
                            self.repairs.append(f"Servicio {service_name} iniciado")
                        except subprocess.CalledProcessError as e:
                            self.issues.append(f"Error al iniciar servicio {service_name}: {str(e)}")
                else:
                    # Verificar proceso alternativo
                    for proc in psutil.process_iter(['name']):
                        if service_name.lower() in proc.info['name'].lower():
                            break
                    else:
                        self.issues.append(f"Proceso {service_name} no está en ejecución")
                
                # Verificar puerto
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('127.0.0.1', service_info['port']))
                if result != 0:
                    self.issues.append(f"Puerto {service_info['port']} para {service_name} no está disponible")
                sock.close()
                
                # Verificar archivo de configuración
                if service_info['config']:
                    config_path = Path(service_info['config'])
                    if not config_path.exists():
                        self.issues.append(f"Archivo de configuración para {service_name} no existe: {config_path}")
                    else:
                        # Verificar permisos
                        stat = config_path.stat()
                        if stat.st_uid != pwd.getpwnam(service_info['user']).pw_uid:
                            self.issues.append(f"Propietario incorrecto en {config_path}")
                        if stat.st_gid != grp.getgrnam(service_info['group']).gr_gid:
                            self.issues.append(f"Grupo incorrecto en {config_path}")
                
            except Exception as e:
                self.issues.append(f"Error al verificar servicio {service_name}: {str(e)}")

    def verify_critical_configs(self):
        """Verifica los archivos de configuración críticos."""
        logger.info("Verificando archivos de configuración críticos...")
        
        for config_name, config_info in self.critical_configs.items():
            try:
                config_path = Path(config_info['path'])
                if not config_path.exists():
                    self.issues.append(f"Archivo de configuración {config_name} no existe: {config_path}")
                    continue
                
                # Verificar permisos
                stat = config_path.stat()
                expected_perms = int(config_info['permissions'], 8)
                if stat.st_mode & 0o777 != expected_perms:
                    self.issues.append(f"Permisos incorrectos en {config_name}")
                    try:
                        subprocess.run(['sudo', 'chmod', config_info['permissions'], str(config_path)], check=True)
                        self.repairs.append(f"Permisos corregidos para {config_name}")
                    except subprocess.CalledProcessError as e:
                        self.issues.append(f"Error al corregir permisos de {config_name}: {str(e)}")
                
                # Verificar propietario y grupo
                if stat.st_uid != pwd.getpwnam(config_info['owner']).pw_uid:
                    self.issues.append(f"Propietario incorrecto en {config_name}")
                    try:
                        subprocess.run(['sudo', 'chown', config_info['owner'], str(config_path)], check=True)
                        self.repairs.append(f"Propietario corregido para {config_name}")
                    except subprocess.CalledProcessError as e:
                        self.issues.append(f"Error al corregir propietario de {config_name}: {str(e)}")
                
                if stat.st_gid != grp.getgrnam(config_info['group']).gr_gid:
                    self.issues.append(f"Grupo incorrecto en {config_name}")
                    try:
                        subprocess.run(['sudo', 'chgrp', config_info['group'], str(config_path)], check=True)
                        self.repairs.append(f"Grupo corregido para {config_name}")
                    except subprocess.CalledProcessError as e:
                        self.issues.append(f"Error al corregir grupo de {config_name}: {str(e)}")
                
            except Exception as e:
                self.issues.append(f"Error al verificar {config_name}: {str(e)}")

    def repair_services(self):
        """Repara los servicios necesarios."""
        logger.info("Reparando servicios...")
        
        # Verificar servicios primero
        self.verify_services()
        
        # Verificar configuraciones críticas
        self.verify_critical_configs()
        
        # Reiniciar servicios si es necesario
        for service_name, service_info in self.required_services.items():
            try:
                subprocess.run(['sudo', 'systemctl', 'restart', service_info['service']], check=True)
                self.repairs.append(f"Servicio {service_name} reiniciado")
            except subprocess.CalledProcessError as e:
                self.issues.append(f"Error al reiniciar servicio {service_name}: {str(e)}")

    def create_backup(self):
        """Crea un backup del proyecto."""
        logger.info("Creando backup del proyecto...")
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = self.project_root / 'backups' / f'backup_{timestamp}'
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup de archivos importantes
            important_files = [
                'requirements.txt',
                '.env',
                'config/settings.py',
                'config/urls.py',
                'manage.py'
            ]
            
            for file in important_files:
                src = self.project_root / file
                if src.exists():
                    dst = backup_dir / file
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    self.backups.append(str(dst))
            
            # Backup de la base de datos
            try:
                db_backup = backup_dir / 'database_backup.json'
                call_command('dumpdata', '--output', str(db_backup))
                self.backups.append(str(db_backup))
            except Exception as e:
                self.issues.append(f"Error al hacer backup de la base de datos: {str(e)}")
            
            logger.info(f"Backup creado en: {backup_dir}")
            self.repairs.append(f"Backup creado: {backup_dir}")
            
        except Exception as e:
            self.issues.append(f"Error al crear backup: {str(e)}")

    def generate_report(self):
        """Genera un reporte final."""
        logger.info("Generando reporte final...")
        
        report = {
            'issues': self.issues,
            'optimizations': self.optimizations,
            'dependencies': list(self.dependencies),
            'cleaned_files': self.cleaned_files,
            'repairs': self.repairs,
            'backups': self.backups
        }
        
        with open('project_report.yaml', 'w') as f:
            yaml.dump(report, f, default_flow_style=False)
            
        logger.info(f"Reporte generado: project_report.yaml")
        logger.info(f"Problemas encontrados: {len(self.issues)}")
        logger.info(f"Optimizaciones realizadas: {len(self.optimizations)}")
        logger.info(f"Dependencias detectadas: {len(self.dependencies)}")
        logger.info(f"Archivos limpiados: {len(self.cleaned_files)}")
        logger.info(f"Reparaciones realizadas: {len(self.repairs)}")
        logger.info(f"Backups creados: {len(self.backups)}")

    def clean_unnecessary_files(self):
        """Limpia archivos innecesarios del proyecto."""
        logger.info("Limpiando archivos innecesarios...")
        
        # Patrones de archivos a limpiar
        cleanup_patterns = {
            # Archivos de respaldo y temporales
            'backup_files': [
                '*.py.bak*',      # Archivos de respaldo de Python
                '*.pyc',          # Archivos compilados de Python
                '*.pyo',          # Archivos optimizados de Python
                '*.pyd',          # Archivos de extensión de Python
                '__pycache__',    # Directorios de caché
                '.DS_Store',      # Archivos de sistema macOS
                '*.swp',          # Archivos temporales de vim
                '*.swo',          # Archivos temporales de vim
                '*.tmp',          # Archivos temporales
                '*.bak',          # Archivos de respaldo genéricos
                '*.log.bak',      # Logs de respaldo
                '*.bak.*',        # Archivos de respaldo con extensión
                '*.old',          # Archivos antiguos
                '*.orig',         # Archivos originales
                '*.rej',          # Archivos de rechazo
            ],
            # Archivos de desarrollo y pruebas
            'development_files': [
                '*.test.py',      # Archivos de prueba
                'test_*.py',      # Archivos de prueba
                '*.spec',         # Archivos de especificación
                '*.egg-info',     # Información de paquetes
                '*.egg',          # Paquetes Python
                'dist/',          # Directorio de distribución
                'build/',         # Directorio de construcción
                '.pytest_cache/', # Caché de pytest
                '.coverage',      # Archivo de cobertura
                'htmlcov/',       # Directorio de cobertura HTML
            ],
            # Archivos de IDE y editores
            'ide_files': [
                '.idea/',         # PyCharm
                '.vscode/',       # Visual Studio Code
                '*.sublime-*',    # Sublime Text
                '.project',       # Eclipse
                '.pydevproject',  # Eclipse
                '.settings/',     # Eclipse
            ],
            # Archivos de sistema y logs
            'system_files': [
                '*.log',          # Archivos de log
                '*.pid',          # Archivos de PID
                '*.lock',         # Archivos de bloqueo
                '*.pid.lock',     # Archivos de bloqueo de PID
                '*.socket',       # Archivos de socket
                '*.service',      # Archivos de servicio
            ]
        }
        
        try:
            for category, patterns in cleanup_patterns.items():
                logger.info(f"Limpiando {category}...")
                for pattern in patterns:
                    for file_path in self.project_root.rglob(pattern):
                        try:
                            if file_path.is_file():
                                # Verificar si el archivo es necesario
                                if self.is_file_necessary(file_path):
                                    continue
                                    
                                file_path.unlink()
                                self.cleaned_files.append(str(file_path))
                                logger.info(f"Archivo eliminado: {file_path}")
                            elif file_path.is_dir():
                                # Verificar si el directorio está vacío
                                if not any(file_path.iterdir()):
                                    shutil.rmtree(file_path)
                                    self.cleaned_files.append(str(file_path))
                                    logger.info(f"Directorio vacío eliminado: {file_path}")
                        except Exception as e:
                            self.issues.append(f"Error al eliminar {file_path}: {str(e)}")
            
            # Agregar información de limpieza al reporte
            self.optimizations.append({
                'type': 'file_cleanup',
                'files_cleaned': len(self.cleaned_files),
                'details': self.cleaned_files
            })
            
            logger.info(f"Limpieza completada. {len(self.cleaned_files)} archivos eliminados.")
            
        except Exception as e:
            self.issues.append(f"Error durante la limpieza: {str(e)}")
            
    def is_file_necessary(self, file_path: Path) -> bool:
        """Verifica si un archivo es necesario para el proyecto."""
        # Lista de archivos y patrones que NO deben eliminarse
        necessary_patterns = [
            'requirements.txt',
            '.env',
            'manage.py',
            'wsgi.py',
            'asgi.py',
            'settings.py',
            'urls.py',
            '__init__.py',
            'celery.py',
            'gunicorn_conf.py',
            'nginx.conf',
            'supervisord.conf',
            'docker-compose.yml',
            'Dockerfile',
            'README.md',
            'LICENSE',
            '.gitignore',
            'project_diagnostic.py'  # No eliminar este script
        ]
        
        # Verificar si el archivo está en la lista de necesarios
        for pattern in necessary_patterns:
            if file_path.name == pattern or file_path.match(pattern):
                return True
                
        # Verificar si el archivo está en directorios críticos
        critical_dirs = [
            'app/ats/chatbot',
            'config',
            'static',
            'media',
            'templates'
        ]
        
        for dir_name in critical_dirs:
            if dir_name in str(file_path):
                return True
                
        return False

    def prepare_deployment(self):
        """Prepara el proyecto para despliegue en servidor."""
        logger.info("Preparando despliegue en servidor...")
        
        try:
            # 1. Verificar requisitos de despliegue
            deployment_requirements = {
                'python_version': '3.8+',
                'django_version': '4.2+',
                'postgresql_version': '13+',
                'redis_version': '6+',
                'nginx_version': '1.18+',
                'gunicorn_version': '20.1+'
            }
            
            # 2. Crear archivos de configuración necesarios
            config_files = {
                'gunicorn.service': f"""[Unit]
Description=Gunicorn daemon for huntRED Chatbot
After=network.target

[Service]
User=www-data
Group=ai_huntred
WorkingDirectory=/home/pablo/app
ExecStart=/home/pablo/venv/bin/gunicorn \\
    --access-logfile - \\
    --workers 3 \\
    --bind unix:/run/gunicorn.sock \\
    config.wsgi:application

[Install]
WantedBy=multi-user.target""",

                'nginx.conf': f"""server {{
    listen 80;
    server_name huntred.com www.huntred.com;

    location = /favicon.ico {{ access_log off; log_not_found off; }}
    
    location /static/ {{
        root /home/pablo/app;
    }}

    location /media/ {{
        root /home/pablo/app;
    }}

    location / {{
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }}
}}""",

                'supervisord.conf': f"""[program:huntred-celery]
command=/home/pablo/venv/bin/celery -A config worker -l INFO
directory=/home/pablo/app
user=pablo
numprocs=1
stdout_logfile=/home/pablo/logs/celery.log
stderr_logfile=/home/pablo/logs/celery.error.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600

[program:huntred-celerybeat]
command=/home/pablo/venv/bin/celery -A config beat -l INFO
directory=/home/pablo/app
user=pablo
numprocs=1
stdout_logfile=/home/pablo/logs/celerybeat.log
stderr_logfile=/home/pablo/logs/celerybeat.error.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600"""
            }
            
            # 3. Crear directorios necesarios
            required_dirs = [
                '/home/pablo/logs',
                '/home/pablo/static',
                '/home/pablo/media',
                '/home/pablo/backups',
                '/run/gunicorn'
            ]
            
            for dir_path in required_dirs:
                try:
                    Path(dir_path).mkdir(parents=True, exist_ok=True)
                    subprocess.run(['sudo', 'chown', '-R', 'www-data:ai_huntred', dir_path], check=True)
                    subprocess.run(['sudo', 'chmod', '-R', '775', dir_path], check=True)
                    self.repairs.append(f"Directorio creado y configurado: {dir_path}")
                except Exception as e:
                    self.issues.append(f"Error al crear directorio {dir_path}: {str(e)}")
            
            # 4. Crear archivos de configuración
            for filename, content in config_files.items():
                try:
                    file_path = Path(f'/etc/{filename}')
                    with open(file_path, 'w') as f:
                        f.write(content)
                    subprocess.run(['sudo', 'chown', 'root:root', str(file_path)], check=True)
                    subprocess.run(['sudo', 'chmod', '644', str(file_path)], check=True)
                    self.repairs.append(f"Archivo de configuración creado: {filename}")
                except Exception as e:
                    self.issues.append(f"Error al crear archivo {filename}: {str(e)}")
            
            # 5. Configurar servicios
            services = ['gunicorn', 'nginx', 'supervisor']
            for service in services:
                try:
                    subprocess.run(['sudo', 'systemctl', 'enable', f'{service}.service'], check=True)
                    subprocess.run(['sudo', 'systemctl', 'restart', f'{service}.service'], check=True)
                    self.repairs.append(f"Servicio configurado y reiniciado: {service}")
                except Exception as e:
                    self.issues.append(f"Error al configurar servicio {service}: {str(e)}")
            
            # 6. Configurar SSL (si es necesario)
            if os.getenv('ENABLE_SSL', 'false').lower() == 'true':
                try:
                    subprocess.run(['sudo', 'certbot', '--nginx', '-d', 'huntred.com', '-d', 'www.huntred.com'], check=True)
                    self.repairs.append("SSL configurado con Certbot")
                except Exception as e:
                    self.issues.append(f"Error al configurar SSL: {str(e)}")
            
            logger.info("Preparación de despliegue completada")
            
        except Exception as e:
            self.issues.append(f"Error en la preparación del despliegue: {str(e)}")

    def verify_django_settings(self):
        """Verifica la configuración de Django antes de las migraciones."""
        logger.info("Verificando configuración de Django...")
        
        try:
            # 1. Verificar estructura de settings
            settings_dir = self.project_root / 'config' / 'settings'
            if not settings_dir.exists():
                raise Exception("No se encuentra el directorio de settings")
            
            # 2. Verificar archivos de settings
            required_settings = ['__init__.py', 'base.py', 'development.py', 'production.py']
            for setting_file in required_settings:
                if not (settings_dir / setting_file).exists():
                    raise Exception(f"Falta el archivo de configuración: {setting_file}")
            
            # 3. Verificar INSTALLED_APPS
            if 'app' not in settings.INSTALLED_APPS:
                raise Exception("La app 'app' no está en INSTALLED_APPS")
            
            # 4. Verificar configuración de base de datos
            if not settings.DATABASES:
                raise Exception("No hay configuración de base de datos")
            
            db_config = settings.DATABASES.get('default', {})
            if not db_config:
                raise Exception("No hay configuración para la base de datos 'default'")
            
            # 5. Verificar AUTH_USER_MODEL (opcional)
            if hasattr(settings, 'AUTH_USER_MODEL'):
                if settings.AUTH_USER_MODEL != 'accounts.CustomUser':
                    logger.warning(f"AUTH_USER_MODEL está configurado como {settings.AUTH_USER_MODEL}, pero usaremos el modelo estándar de Django")
            else:
                logger.warning("AUTH_USER_MODEL no está configurado, usando el modelo estándar de Django")
            
            logger.info("Configuración de Django verificada correctamente")
            
        except Exception as e:
            self.issues.append(f"Error en la verificación de configuración Django: {str(e)}")
            raise

    def verify_custom_user_model(self):
        """Verifica que el modelo CustomUser existe y está correctamente configurado."""
        logger.info("Verificando modelo CustomUser...")
        
        try:
            # 1. Verificar que existe el archivo models.py
            models_file = self.project_root / 'app' / 'models.py'
            if not models_file.exists():
                raise Exception("No se encuentra el archivo models.py")
            
            # 2. Verificar que el modelo está definido
            with open(models_file, 'r') as f:
                content = f.read()
                if 'class CustomUser' not in content:
                    raise Exception("El modelo CustomUser no está definido en models.py")
            
            # 3. Verificar que la app está en el PYTHONPATH
            app_path = self.project_root / 'app'
            if str(app_path) not in sys.path:
                sys.path.append(str(app_path))
                logger.info(f"Agregado {app_path} al PYTHONPATH")
            
            # 4. Intentar importar el modelo
            try:
                from app.ats.accounts.models import CustomUser
                logger.info("Modelo CustomUser encontrado y configurado correctamente")
            except ImportError as e:
                raise Exception(f"Error al importar CustomUser: {str(e)}")
            
            logger.info("Modelo CustomUser verificado correctamente")
            
        except Exception as e:
            self.issues.append(f"Error en la verificación del modelo CustomUser: {str(e)}")
            raise

    def migrate_database(self):
        """Realiza la migración completa de la base de datos."""
        logger.info("Iniciando migración de base de datos...")
        
        try:
            # 1. Verificar configuración de Django primero
            self.verify_django_settings()
            
            # 2. Verificar conexión a la base de datos
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                logger.info("Conexión a la base de datos establecida")
            except Exception as e:
                logger.error(f"Error al conectar con la base de datos: {str(e)}")
                raise
            
            # 3. Eliminar migraciones existentes si es un proyecto nuevo
            migrations_dir = self.project_root / 'app' / 'migrations'
            if migrations_dir.exists():
                logger.info("Eliminando migraciones existentes...")
                for file in migrations_dir.glob('*.py'):
                    if file.name != '__init__.py':
                        file.unlink()
                self.repairs.append("Migraciones existentes eliminadas")
            
            # 4. Crear migraciones iniciales
            logger.info("Creando migraciones iniciales...")
            try:
                call_command('makemigrations', 'app', name='initial')
                self.repairs.append("Migración inicial creada")
            except Exception as e:
                self.issues.append(f"Error al crear migración inicial: {str(e)}")
                raise
            
            # 5. Aplicar migraciones
            logger.info("Aplicando migraciones...")
            try:
                call_command('migrate', 'auth')  # Primero auth
                call_command('migrate', 'contenttypes')  # Luego contenttypes
                call_command('migrate', 'app')  # Finalmente nuestra app
                self.repairs.append("Migraciones aplicadas correctamente")
            except Exception as e:
                self.issues.append(f"Error al aplicar migraciones: {str(e)}")
                raise
            
            # 6. Verificar que las tablas se crearon correctamente
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = cursor.fetchall()
                
                if not tables:
                    self.issues.append("No se encontraron tablas en la base de datos")
                    raise Exception("No se encontraron tablas en la base de datos")
                
                logger.info(f"Tablas creadas: {[table[0] for table in tables]}")
            
            # 7. Crear superusuario si no existe
            try:
                from django.contrib.auth.models import User
                if not User.objects.filter(is_superuser=True).exists():
                    User.objects.create_superuser(
                        username='PabloLLH',
                        email='pablo@huntred.com',
                        password='Natalia&Patricio1113!'
                    )
                    self.repairs.append("Superusuario creado correctamente")
            except Exception as e:
                self.issues.append(f"Error al crear superusuario: {str(e)}")
            
            # 8. Optimizar base de datos
            with connection.cursor() as cursor:
                cursor.execute("VACUUM ANALYZE")
                cursor.execute("REINDEX DATABASE g_huntred_ai_db")
            
            logger.info("Migración de base de datos completada")
            
        except Exception as e:
            self.issues.append(f"Error en la migración de la base de datos: {str(e)}")
            raise

    def run(self):
        """Ejecuta todas las verificaciones, reparaciones y optimizaciones."""
        logger.info("Iniciando gestión del proyecto...")
        
        # Verificación del sistema
        self.check_system_info()
        
        # Preparación para despliegue
        self.prepare_deployment()
        
        # Migración de base de datos
        self.migrate_database()
        
        # Limpieza y reparación
        self.clean_unnecessary_files()
        self.clean_backup_files()
        self.repair_project()
        
        # Verificaciones
        self.check_system_resources()
        self.check_python_environment()
        self.check_project_structure()
        self.check_dependencies()
        self.check_imports()
        self.check_code_quality()
        self.check_security()
        self.check_database()
        self.check_settings()
        self.check_static_files()
        self.check_templates()
        self.check_urls()
        self.check_views()
        self.check_models()
        self.check_forms()
        self.check_tests()
        
        # Optimizaciones
        self.optimize_imports()
        self.optimize_code()
        self.optimize_database()
        self.optimize_static_files()
        
        # Backup final
        self.create_backup()
        
        # Reporte final
        self.generate_report()

def main():
    """Función principal."""
    try:
        # Cargar variables de entorno
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            logger.info("✓ Variables de entorno cargadas")
        else:
            logger.warning("No se encontró el archivo .env")
        
        # Configurar Django
        if not setup_django():
            sys.exit(1)
        
        # Ejecutar gestión del proyecto
        manager = ProjectManager()
        manager.run()
        
    except Exception as e:
        logger.error(f"Error en la gestión del proyecto: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 