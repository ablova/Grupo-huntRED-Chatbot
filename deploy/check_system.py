#!/usr/bin/env python
"""
Script de verificación del sistema para la plataforma Grupo huntRED®

Este script verifica la integridad y configuración del sistema antes de enviar a la nube.
Realiza las siguientes verificaciones:
1. Estructura de directorios críticos
2. Modelos Django
3. Configuración de API y servicios
4. Dependencias Python
5. Archivos de configuración

Uso:
    python deploy/check_system.py
"""

import os
import sys
import importlib
import subprocess
import django
from pathlib import Path

# Color codes for console output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(title):
    """Imprime un encabezado con formato"""
    print(f"\n{BLUE}{BOLD}{'=' * 80}{RESET}")
    print(f"{BLUE}{BOLD} {title} {RESET}")
    print(f"{BLUE}{BOLD}{'=' * 80}{RESET}\n")

def print_success(message):
    """Imprime un mensaje de éxito"""
    print(f"{GREEN}✓ {message}{RESET}")

def print_warning(message):
    """Imprime un mensaje de advertencia"""
    print(f"{YELLOW}⚠ {message}{RESET}")

def print_error(message):
    """Imprime un mensaje de error"""
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    """Imprime un mensaje informativo"""
    print(f"{BLUE}ℹ {message}{RESET}")

def check_directories():
    """Verifica la estructura de directorios críticos"""
    print_header("Verificando estructura de directorios")

    critical_dirs = [
        "ai_huntred",
        "app",
        "app/com",
        "app/com/chatbot",
        "app/com/utils",
        "app/ml",
        "app/pagos",
        "app/publish",
        "app/sexsi",
        "app/utilidades",
        "app/templates",
        "static",
        "media",
        "deploy"
    ]

    issues = 0
    for directory in critical_dirs:
        dir_path = Path(directory)
        if dir_path.exists() and dir_path.is_dir():
            print_success(f"Directorio {directory} encontrado")
        else:
            print_error(f"Directorio {directory} no encontrado")
            issues += 1

    if issues == 0:
        print_success("Todos los directorios críticos existen")
    else:
        print_error(f"Faltan {issues} directorios críticos")
    
    return issues == 0

def check_config_files():
    """Verifica la existencia de archivos de configuración críticos"""
    print_header("Verificando archivos de configuración")

    critical_files = [
        "ai_huntred/settings.py",
        "ai_huntred/settings/production.py",
        "ai_huntred/urls.py",
        "ai_huntred/asgi.py",
        "ai_huntred/wsgi.py",
        "app/models.py",
        "manage.py",
        "requirements.txt",
        ".env-example",
        "Dockerfile",
        "docker-compose.yml",
        "deploy/entrypoint.sh",
        "deploy/nginx.conf"
    ]

    issues = 0
    for file_path in critical_files:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print_success(f"Archivo {file_path} encontrado")
        else:
            print_error(f"Archivo {file_path} no encontrado")
            issues += 1

    if issues == 0:
        print_success("Todos los archivos de configuración críticos existen")
    else:
        print_error(f"Faltan {issues} archivos de configuración críticos")
    
    return issues == 0

def check_django_models():
    """Verifica la integridad de los modelos Django"""
    print_header("Verificando modelos Django")
    
    # Añadir el directorio actual al path
    sys.path.append(os.getcwd())
    
    # Configurar Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_huntred.settings")
    try:
        django.setup()
    except Exception as e:
        print_error(f"Error al configurar Django: {e}")
        return False
    
    # Verificar modelos críticos
    from django.apps import apps
    
    critical_models = [
        "BusinessUnit",
        "Person",
        "SocialConnection",
        "Vacante",
        "ChatState",
        "ChatbotLog",
        "WhatsAppAPI",
        "TelegramAPI",
        "MLModel",
        "Opportunity",
        "PricingBaseline",
        "Addons",
        "Coupons",
        "PaymentMilestones",
        "OpportunityVerificationPackage",
        "CandidateVerification"
    ]
    
    issues = 0
    for model_name in critical_models:
        try:
            model = apps.get_model("app", model_name)
            fields_count = len(model._meta.fields)
            print_success(f"Modelo {model_name} encontrado con {fields_count} campos")
        except LookupError:
            print_error(f"Modelo {model_name} no encontrado")
            issues += 1
        except Exception as e:
            print_error(f"Error al verificar el modelo {model_name}: {e}")
            issues += 1
    
    if issues == 0:
        print_success("Todos los modelos críticos existen")
    else:
        print_error(f"Hay problemas con {issues} modelos críticos")
    
    return issues == 0

def check_dependencies():
    """Verifica las dependencias Python"""
    print_header("Verificando dependencias Python")
    
    # Lista de dependencias críticas
    critical_dependencies = [
        "django",
        "celery",
        "redis",
        "psycopg2",
        "djangorestframework",
        "whitenoise",
        "gunicorn",
        "tensorflow",
        "sentry_sdk",
        "django_redis",
        "stripe",
        "requests",
        "uvicorn"
    ]
    
    issues = 0
    for dependency in critical_dependencies:
        try:
            importlib.import_module(dependency.replace("-", "_"))
            print_success(f"Dependencia {dependency} instalada")
        except ImportError:
            print_error(f"Dependencia {dependency} no instalada")
            issues += 1
    
    if issues == 0:
        print_success("Todas las dependencias críticas están instaladas")
    else:
        print_error(f"Faltan {issues} dependencias críticas")
        print_info("Ejecuta: pip install -r requirements.txt")
    
    return issues == 0

def check_environment_variables():
    """Verifica la existencia de un archivo .env o variables de entorno"""
    print_header("Verificando variables de entorno")
    
    if os.path.exists(".env"):
        print_success("Archivo .env encontrado")
        # Contar número de variables en el archivo .env
        with open(".env", "r") as env_file:
            env_vars = [line for line in env_file.readlines() if "=" in line and not line.startswith("#")]
            print_info(f"El archivo .env contiene {len(env_vars)} variables definidas")
    else:
        print_warning("Archivo .env no encontrado, revisando .env-example")
        if os.path.exists(".env-example"):
            print_info("Archivo .env-example encontrado. Debes crear un archivo .env basado en este ejemplo antes de desplegar")
        else:
            print_error("No se encontró ningún archivo de variables de entorno")
            return False
    
    return True

def check_database_connection():
    """Verifica la conexión a la base de datos"""
    print_header("Verificando conexión a la base de datos")
    
    try:
        # Configurar Django si no se ha hecho antes
        if not apps.ready:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_huntred.settings")
            django.setup()
        
        from django.db import connections
        connection = connections['default']
        connection.ensure_connection()
        print_success("Conexión a la base de datos establecida correctamente")
        
        # Verificar tablas críticas
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations;")
            migrations_count = cursor.fetchone()[0]
            print_info(f"Hay {migrations_count} migraciones aplicadas")
            
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            tables_count = cursor.fetchone()[0]
            print_info(f"Hay {tables_count} tablas en la base de datos")
        
        return True
    except Exception as e:
        print_error(f"Error al conectar con la base de datos: {e}")
        print_info("Asegúrate de que la base de datos esté configurada correctamente en settings.py o en variables de entorno")
        return False

def check_docker_setup():
    """Verifica la configuración de Docker"""
    print_header("Verificando configuración de Docker")
    
    docker_files = ["Dockerfile", "docker-compose.yml", ".dockerignore"]
    issues = 0
    
    for file in docker_files:
        if os.path.exists(file):
            print_success(f"Archivo {file} encontrado")
        else:
            print_error(f"Archivo {file} no encontrado")
            issues += 1
    
    # Verificar si Docker está instalado
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Docker instalado: {result.stdout.strip()}")
        else:
            print_error("Docker no está instalado o no está en el PATH")
            issues += 1
    except Exception:
        print_error("Docker no está instalado o no está en el PATH")
        issues += 1
    
    # Verificar si Docker Compose está instalado
    try:
        result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Docker Compose instalado: {result.stdout.strip()}")
        else:
            print_error("Docker Compose no está instalado o no está en el PATH")
            issues += 1
    except Exception:
        print_error("Docker Compose no está instalado o no está en el PATH")
        issues += 1
    
    if issues == 0:
        print_success("Configuración de Docker completa")
    else:
        print_warning(f"Hay {issues} problemas con la configuración de Docker")
    
    return issues == 0

def check_business_units():
    """Verifica las unidades de negocio configuradas"""
    print_header("Verificando unidades de negocio")
    
    try:
        # Configurar Django si no se ha hecho antes
        if 'django' not in sys.modules:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_huntred.settings")
            django.setup()
        
        from django.apps import apps
        BusinessUnit = apps.get_model("app", "BusinessUnit")
        
        units = BusinessUnit.objects.all()
        if units.exists():
            print_success(f"Se encontraron {units.count()} unidades de negocio")
            for unit in units:
                print_info(f"- {unit.name}")
        else:
            print_warning("No se encontraron unidades de negocio configuradas")
            print_info("Deberás crear las unidades de negocio después del despliegue")
        
        return True
    except Exception as e:
        print_error(f"Error al verificar unidades de negocio: {e}")
        return False

def check_permissions():
    """Verifica los permisos de archivos críticos"""
    print_header("Verificando permisos de archivos")
    
    executable_files = [
        "manage.py",
        "deploy/entrypoint.sh"
    ]
    
    issues = 0
    for file_path in executable_files:
        if os.path.exists(file_path):
            if os.access(file_path, os.X_OK):
                print_success(f"Archivo {file_path} tiene permisos de ejecución")
            else:
                print_warning(f"Archivo {file_path} no tiene permisos de ejecución")
                print_info(f"Ejecuta: chmod +x {file_path}")
                issues += 1
        else:
            print_error(f"Archivo {file_path} no encontrado")
            issues += 1
    
    if issues == 0:
        print_success("Todos los archivos tienen los permisos correctos")
    else:
        print_warning(f"Hay {issues} problemas con los permisos de archivos")
    
    return issues == 0

def main():
    """Función principal que ejecuta todas las verificaciones"""
    print_header("VERIFICACIÓN DEL SISTEMA GRUPO HUNTRED®")
    print(f"{BOLD}Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print("\nEste script verificará la integridad del sistema antes del despliegue en la nube.\n")
    
    checks = [
        ("Estructura de directorios", check_directories),
        ("Archivos de configuración", check_config_files),
        ("Modelos Django", check_django_models),
        ("Dependencias Python", check_dependencies),
        ("Variables de entorno", check_environment_variables),
        ("Configuración de Docker", check_docker_setup),
        ("Permisos de archivos", check_permissions)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Error durante la verificación de {name}: {e}")
            results.append((name, False))
    
    print_header("RESUMEN DE VERIFICACIÓN")
    
    passed = 0
    for name, result in results:
        if result:
            print_success(f"{name}: VERIFICADO")
            passed += 1
        else:
            print_error(f"{name}: FALLÓ")
    
    success_rate = (passed / len(results)) * 100
    print(f"\n{BOLD}Resultado: {passed}/{len(results)} verificaciones exitosas ({success_rate:.1f}%){RESET}")
    
    if success_rate == 100:
        print(f"\n{GREEN}{BOLD}¡SISTEMA LISTO PARA DESPLIEGUE!{RESET}")
        print(f"\n{BLUE}Para desplegar, ejecuta:{RESET}")
        print(f"{BOLD}  docker-compose up -d{RESET}")
    elif success_rate >= 80:
        print(f"\n{YELLOW}{BOLD}SISTEMA CASI LISTO - CORRIGE LOS PROBLEMAS MENORES{RESET}")
        print(f"\n{BLUE}Revisa los errores arriba y corrígelos antes de desplegar.{RESET}")
    else:
        print(f"\n{RED}{BOLD}SISTEMA NO LISTO - SE REQUIEREN CORRECCIONES IMPORTANTES{RESET}")
        print(f"\n{BLUE}Corrige los problemas indicados antes de intentar el despliegue.{RESET}")

if __name__ == "__main__":
    import datetime
    main()
