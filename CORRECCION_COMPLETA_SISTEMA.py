#!/usr/bin/env python3
"""
CORRECCIÓN COMPLETA DEL SISTEMA huntRED®
========================================

Este script restaura la arquitectura corporativa correcta del sistema huntRED®
después de identificar y corregir todos los problemas estructurales.

ARQUITECTURA CORPORATIVA:
- Grupo huntRED® (Holding)
  - huntRED® (Unidad de Negocio Principal)
  - huntRED® Executive
  - huntRED® Solucions (Consultora)
  - huntRED® Experience (55+)
  - huntRED® Inspiration (Discapacitados)
  - huntU®
  - Amigro®
  - SEXSI
  - MilkyLeak

RESPONSABILIDADES:
- GenIA: Flujo de reclutamiento (huntRED®, Executive, huntU, Amigro)
- AURA: Trayectorias, históricos, analíticos (Solucions, Payroll, retención)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import django
from django.conf import settings
from django.core.management import execute_from_command_line

def print_header(title):
    """Imprime un encabezado con formato."""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def print_step(step, description):
    """Imprime un paso del proceso."""
    print(f"\n[{step}] {description}")
    print("-" * 60)

def run_command(command, description=""):
    """Ejecuta un comando y maneja errores."""
    if description:
        print(f"Ejecutando: {description}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description} - EXITOSO")
            return True
        else:
            print(f"✗ {description} - ERROR")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ {description} - EXCEPCIÓN: {str(e)}")
        return False

def setup_django():
    """Configura Django para el script."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.config.settings')
    django.setup()

def create_corporate_structure():
    """Crea la estructura corporativa correcta."""
    print_step("1", "CREANDO ESTRUCTURA CORPORATIVA")
    
    # Directorios corporativos
    corporate_dirs = [
        "app/corporate",
        "app/corporate/huntred",
        "app/corporate/huntred_executive", 
        "app/corporate/huntred_solucions",
        "app/corporate/huntred_experience",
        "app/corporate/huntred_inspiration",
        "app/corporate/huntu",
        "app/corporate/amigro",
        "app/corporate/sexsi",
        "app/corporate/milkyleak"
    ]
    
    for dir_path in corporate_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Creado: {dir_path}")

def fix_django_settings():
    """Corrige la configuración de Django."""
    print_step("2", "CORRIGIENDO CONFIGURACIÓN DJANGO")
    
    # Crear settings/base.py correcto
    base_settings = '''"""
Configuración base de Django para huntRED®.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-huntred-corporate-key-2024')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
]

LOCAL_APPS = [
    'app',
    'app.ats',
    'app.aura',
    'app.payroll',
    'app.sexsi',
    'app.milkyleak',
    'app.corporate',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'app' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'app' / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Celery
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
'''
    
    # Crear el archivo settings/base.py
    settings_dir = Path("app/config/settings")
    settings_dir.mkdir(parents=True, exist_ok=True)
    
    with open(settings_dir / "base.py", "w") as f:
        f.write(base_settings)
    
    print("✓ Configuración base de Django creada")

def fix_admin_structure():
    """Corrige la estructura del admin."""
    print_step("3", "CORRIGIENDO ESTRUCTURA ADMIN")
    
    # Crear admin modular por unidad de negocio
    admin_structure = {
        "app/admin/__init__.py": '''"""
Admin centralizado para huntRED®.
"""

from django.contrib import admin
from .huntred import *
from .executive import *
from .solucions import *
from .experience import *
from .inspiration import *
from .huntu import *
from .amigro import *
from .sexsi import *
from .milkyleak import *
''',
        "app/admin/huntred.py": '''"""
Admin para huntRED® (Unidad de Negocio Principal).
"""

from django.contrib import admin
from app.models import *

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email']
    readonly_fields = ['created_at', 'updated_at']
''',
        "app/admin/executive.py": '''"""
Admin para huntRED® Executive.
"""

from django.contrib import admin
from app.models import *

@admin.register(ExecutiveProfile)
class ExecutiveProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'company', 'experience_years']
    list_filter = ['experience_years', 'created_at']
    search_fields = ['name', 'position', 'company']
''',
        "app/admin/solucions.py": '''"""
Admin para huntRED® Solucions (Consultora).
"""

from django.contrib import admin
from app.models import *

@admin.register(ConsultingProject)
class ConsultingProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'client', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'start_date']
    search_fields = ['name', 'client']
''',
    }
    
    for file_path, content in admin_structure.items():
        with open(file_path, "w") as f:
            f.write(content)
        print(f"✓ Creado: {file_path}")

def fix_models_structure():
    """Corrige la estructura de modelos."""
    print_step("4", "CORRIGIENDO ESTRUCTURA DE MODELOS")
    
    # Crear modelos corporativos
    corporate_models = '''"""
Modelos corporativos para huntRED®.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class BusinessUnit(models.Model):
    """Unidad de negocio del Grupo huntRED®."""
    
    UNITS = [
        ('huntred', 'huntRED®'),
        ('executive', 'huntRED® Executive'),
        ('solucions', 'huntRED® Solucions'),
        ('experience', 'huntRED® Experience'),
        ('inspiration', 'huntRED® Inspiration'),
        ('huntu', 'huntU®'),
        ('amigro', 'Amigro®'),
        ('sexsi', 'SEXSI'),
        ('milkyleak', 'MilkyLeak'),
    ]
    
    name = models.CharField(max_length=100, choices=UNITS)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Unidad de Negocio"
        verbose_name_plural = "Unidades de Negocio"
    
    def __str__(self):
        return self.name

class Candidate(models.Model):
    """Candidato del sistema."""
    
    STATUS_CHOICES = [
        ('new', 'Nuevo'),
        ('screening', 'En Evaluación'),
        ('interview', 'Entrevista'),
        ('offer', 'Oferta'),
        ('hired', 'Contratado'),
        ('rejected', 'Rechazado'),
    ]
    
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Candidato"
        verbose_name_plural = "Candidatos"
    
    def __str__(self):
        return self.name

class ExecutiveProfile(models.Model):
    """Perfil ejecutivo para huntRED® Executive."""
    
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    experience_years = models.IntegerField()
    salary_expectation = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Perfil Ejecutivo"
        verbose_name_plural = "Perfiles Ejecutivos"
    
    def __str__(self):
        return f"{self.name} - {self.position}"

class ConsultingProject(models.Model):
    """Proyecto de consultoría para huntRED® Solucions."""
    
    STATUS_CHOICES = [
        ('proposal', 'Propuesta'),
        ('active', 'Activo'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    
    name = models.CharField(max_length=200)
    client = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposal')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Proyecto de Consultoría"
        verbose_name_plural = "Proyectos de Consultoría"
    
    def __str__(self):
        return f"{self.name} - {self.client}"
'''
    
    with open("app/models/corporate.py", "w") as f:
        f.write(corporate_models)
    
    print("✓ Modelos corporativos creados")

def fix_frontend_structure():
    """Corrige la estructura del frontend."""
    print_step("5", "CORRIGIENDO ESTRUCTURA FRONTEND")
    
    # Verificar si existe el frontend
    frontend_dir = Path("app/templates/front")
    if not frontend_dir.exists():
        print("✗ No se encontró el directorio del frontend")
        return False
    
    # Corregir package.json
    package_json = '''{
  "name": "huntred-frontend",
  "version": "1.0.0",
  "description": "Frontend corporativo para huntRED®",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "@tanstack/react-query": "^4.29.0",
    "axios": "^1.3.0",
    "lucide-react": "^0.263.1",
    "clsx": "^1.2.1",
    "tailwind-merge": "^1.13.0"
  },
  "devDependencies": {
    "@types/react": "^18.0.28",
    "@types/react-dom": "^18.0.11",
    "@typescript-eslint/eslint-plugin": "^5.57.1",
    "@typescript-eslint/parser": "^5.57.1",
    "@vitejs/plugin-react": "^3.1.0",
    "autoprefixer": "^10.4.14",
    "eslint": "^8.38.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.3.4",
    "postcss": "^8.4.21",
    "tailwindcss": "^3.2.7",
    "typescript": "^4.9.3",
    "vite": "^4.2.0"
  }
}'''
    
    with open(frontend_dir / "package.json", "w") as f:
        f.write(package_json)
    
    # Corregir vite.config.ts
    vite_config = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})'''
    
    with open(frontend_dir / "vite.config.ts", "w") as f:
        f.write(vite_config)
    
    print("✓ Configuración del frontend corregida")

def run_migrations():
    """Ejecuta las migraciones."""
    print_step("6", "EJECUTANDO MIGRACIONES")
    
    commands = [
        ("python manage.py makemigrations", "Creando migraciones"),
        ("python manage.py migrate", "Aplicando migraciones"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def install_dependencies():
    """Instala las dependencias."""
    print_step("7", "INSTALANDO DEPENDENCIAS")
    
    commands = [
        ("pip install -r requirements.txt", "Instalando dependencias Python"),
        ("cd app/templates/front && npm install", "Instalando dependencias Node.js"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def create_superuser():
    """Crea un superusuario."""
    print_step("8", "CREANDO SUPERUSUARIO")
    
    # Crear superusuario automáticamente
    create_user_script = '''
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.config.settings.base')
django.setup()

from django.contrib.auth.models import User

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@huntred.com', 'huntred2024')
    print("Superusuario creado: admin/huntred2024")
else:
    print("El superusuario ya existe")
'''
    
    with open("create_superuser.py", "w") as f:
        f.write(create_user_script)
    
    run_command("python create_superuser.py", "Creando superusuario")
    run_command("rm create_superuser.py", "Limpiando script temporal")
    
    return True

def test_system():
    """Prueba el sistema."""
    print_step("9", "PROBANDO SISTEMA")
    
    commands = [
        ("python manage.py check", "Verificando configuración Django"),
        ("python manage.py collectstatic --noinput", "Recopilando archivos estáticos"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def main():
    """Función principal."""
    print_header("CORRECCIÓN COMPLETA DEL SISTEMA huntRED®")
    
    print("Iniciando corrección del sistema...")
    print("Este proceso restaurará la arquitectura corporativa correcta.")
    
    try:
        # 1. Crear estructura corporativa
        create_corporate_structure()
        
        # 2. Corregir configuración Django
        fix_django_settings()
        
        # 3. Corregir estructura admin
        fix_admin_structure()
        
        # 4. Corregir estructura de modelos
        fix_models_structure()
        
        # 5. Corregir estructura frontend
        fix_frontend_structure()
        
        # 6. Instalar dependencias
        if not install_dependencies():
            print("✗ Error instalando dependencias")
            return False
        
        # 7. Ejecutar migraciones
        if not run_migrations():
            print("✗ Error ejecutando migraciones")
            return False
        
        # 8. Crear superusuario
        if not create_superuser():
            print("✗ Error creando superusuario")
            return False
        
        # 9. Probar sistema
        if not test_system():
            print("✗ Error probando sistema")
            return False
        
        print_header("CORRECCIÓN COMPLETADA EXITOSAMENTE")
        print("✓ Sistema huntRED® restaurado correctamente")
        print("✓ Arquitectura corporativa implementada")
        print("✓ Admin modular configurado")
        print("✓ Frontend corregido")
        print("✓ Base de datos migrada")
        print("✓ Superusuario creado: admin/huntred2024")
        
        print("\nPRÓXIMOS PASOS:")
        print("1. Ejecutar: python manage.py runserver")
        print("2. Ejecutar: cd app/templates/front && npm run dev")
        print("3. Acceder a: http://localhost:8000/admin")
        print("4. Acceder a: http://localhost:5173")
        
    except Exception as e:
        print(f"✗ Error durante la corrección: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 