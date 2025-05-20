#!/usr/bin/env python
"""
Script simplificado para ejecutar migraciones de Django en entorno local 
usando SQLite en lugar de PostgreSQL.

Este script es una solución temporal para entornos donde PostgreSQL
no está disponible o hay problemas de compatibilidad (macOS ARM).
"""
import os
import sys
import importlib.util
import sqlite3
import subprocess
from pathlib import Path

# Configurar entorno para forzar SQLite
os.environ['DJANGO_SETTINGS_MODULE'] = 'ai_huntred.settings'
os.environ['DEBUG'] = 'True'
os.environ['FORCE_SQLITE'] = 'True'
os.environ['LOCAL_DEV'] = 'True'
os.environ['PRODUCTION'] = 'False'

# Verificar que la base SQLite exista o crearla
db_path = Path(__file__).parent / 'db.sqlite3'
if not db_path.exists():
    print(f"Creando base de datos SQLite en: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.close()
else:
    print(f"Base de datos SQLite encontrada en: {db_path}")

# Definir función para ejecutar comandos con variables de entorno adecuadas
def run_django_command(command):
    """Ejecuta un comando de Django con variables de entorno adecuadas."""
    # Configurar el comando a ejecutar
    full_command = f"{sys.executable} manage.py {command}"
    
    # Usar subprocess para mantener la salida en tiempo real
    print(f"\n----- Ejecutando: {full_command} -----\n")
    process = subprocess.Popen(
        full_command,
        shell=True,
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Mostrar salida en tiempo real
    for line in process.stdout:
        sys.stdout.write(line)
    
    # Esperar a que termine el proceso
    exit_code = process.wait()
    if exit_code != 0:
        print(f"\n⚠️ Comando terminó con código de salida: {exit_code}")
    else:
        print("\n✅ Comando completado correctamente")
    
    return exit_code

# Función principal
def main():
    """Función principal del script."""
    if len(sys.argv) < 2:
        print("Uso: python simple_sqlite_migration.py [comando_django]")
        print("Ejemplos:")
        print("  python simple_sqlite_migration.py makemigrations")
        print("  python simple_sqlite_migration.py migrate")
        return 1
    
    command = ' '.join(sys.argv[1:])
    return run_django_command(command)

if __name__ == "__main__":
    sys.exit(main())
