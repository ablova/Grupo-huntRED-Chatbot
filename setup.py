#!/usr/bin/env python3
"""
Script de configuración para el proyecto Grupo huntRED.
Detecta automáticamente el entorno y usa el archivo de requisitos correcto.
"""

import os
import platform
import subprocess
import sys

def detect_environment():
    """Detecta el entorno de ejecución."""
    system = platform.system()
    if system == "Darwin":  # macOS
        return "macos"
    elif system == "Linux":
        return "server"
    else:
        return "base"

def install_requirements():
    """Instala las dependencias según el entorno detectado."""
    env = detect_environment()
    requirements_file = f"requirements-{env}.txt"
    
    print(f"🔍 Detectado entorno: {env}")
    print(f"📦 Instalando dependencias desde {requirements_file}")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
        print("✅ Dependencias instaladas correctamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_requirements() 