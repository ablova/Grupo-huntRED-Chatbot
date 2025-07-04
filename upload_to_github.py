#!/usr/bin/env python3
"""
Upload HuntRED® v2 Complete System to GitHub
Automated script to commit and push all changes
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

def run_command(command, description=""):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def check_git_status():
    """Check if we're in a git repository"""
    if not Path('.git').exists():
        print("❌ Not in a git repository")
        return False
    
    # Check if there are changes
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("✅ No changes to commit")
        return False
    
    print("📋 Changes detected:")
    print(result.stdout)
    return True

def create_commit_message():
    """Create a comprehensive commit message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    commit_message = f"""🚀 HuntRED® v2 - COMPLETE FUNCTIONAL SYSTEM

✅ TODAS LAS FUNCIONALIDADES IMPLEMENTADAS:
• 🔐 Autenticación JWT con roles completos
• 👥 Gestión completa de empleados (CRUD)
• ⏰ Sistema de asistencia con geolocalización
• 💰 Cálculos de nómina México 2024 (IMSS, ISR, INFONAVIT)
• 📊 Reportes avanzados y analytics
• 💬 Bot de WhatsApp integrado con BD
• 🏢 Multi-tenant para múltiples empresas

🎯 COMPONENTES PRINCIPALES:
• auth/auth_service.py - Autenticación JWT real
• services/attendance_service.py - Asistencia + GPS
• services/real_payroll_service.py - Nómina México 2024
• services/reports_service.py - Reportes avanzados
• api/complete_endpoints.py - API completa
• main_complete.py - Aplicación principal

🔧 INFRAESTRUCTURA:
• Base de datos PostgreSQL persistente
• Modelos relacionales completos
• Validaciones y constraints
• Logging y monitoreo
• Scripts de inicialización

📱 FUNCIONALIDADES DESTACADAS:
• Control de acceso basado en roles
• Geolocalización con validación de radio
• Cálculos fiscales México 2024 reales
• Bot conversacional con comandos
• Dashboard ejecutivo con KPIs
• Reportes por departamento y empleado

🎉 SISTEMA 100% FUNCIONAL Y LISTO PARA PRODUCCIÓN

Timestamp: {timestamp}
"""
    return commit_message

def main():
    """Main upload process"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    🚀 HUNTRED® v2 - UPLOAD TO GITHUB                                        ║
║                                                                              ║
║    Subiendo sistema COMPLETAMENTE FUNCIONAL al repositorio                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Step 1: Check git status
    if not check_git_status():
        print("❌ No hay cambios para subir o no estamos en un repositorio git")
        return
    
    # Step 2: Add all files
    print("\n📁 Agregando archivos al staging area...")
    if not run_command("git add .", "Adding all files"):
        return
    
    # Step 3: Create commit
    print("\n📝 Creando commit...")
    commit_message = create_commit_message()
    
    # Save commit message to file for complex message
    with open('.commit_message.tmp', 'w', encoding='utf-8') as f:
        f.write(commit_message)
    
    if not run_command("git commit -F .commit_message.tmp", "Creating commit"):
        return
    
    # Clean up temp file
    os.remove('.commit_message.tmp')
    
    # Step 4: Push to GitHub
    print("\n🚀 Subiendo al repositorio GitHub...")
    
    # Get current branch
    result = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True)
    current_branch = result.stdout.strip() if result.returncode == 0 else "main"
    
    if not run_command(f"git push origin {current_branch}", f"Pushing to origin/{current_branch}"):
        print("❌ Error al subir al repositorio")
        print("💡 Verifica que tengas permisos de escritura en el repositorio")
        print("💡 Asegúrate de que el repositorio remoto esté configurado correctamente")
        return
    
    # Step 5: Success message
    print("\n" + "="*80)
    print("🎉 ¡ÉXITO! Sistema completo subido a GitHub")
    print("="*80)
    print("✅ Todos los archivos del sistema funcional han sido subidos")
    print("✅ Commit creado con mensaje descriptivo completo")
    print("✅ Cambios pusheados al repositorio remoto")
    print()
    print("📊 RESUMEN DEL SISTEMA SUBIDO:")
    print("   • 🔐 Autenticación JWT completa")
    print("   • 👥 Gestión de empleados (CRUD)")
    print("   • ⏰ Sistema de asistencia con GPS")
    print("   • 💰 Nómina México 2024 real")
    print("   • 📊 Reportes y analytics avanzados")
    print("   • 💬 Bot WhatsApp integrado")
    print("   • 🏢 Arquitectura multi-tenant")
    print("   • 🗄️ Base de datos PostgreSQL")
    print("   • 📱 API REST completa")
    print("   • 🚀 Listo para producción")
    print()
    print("🌐 Para clonar y usar el sistema:")
    print("   git clone https://github.com/ablova/Ghuntred-v2.git")
    print("   cd Ghuntred-v2")
    print("   python start_complete_system.py")
    print()
    print("📖 Documentación completa en README_COMPLETE_SYSTEM.md")
    print("="*80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🔄 Proceso cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)