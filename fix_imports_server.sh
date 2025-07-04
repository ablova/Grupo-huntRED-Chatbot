#!/bin/bash

# Script para corregir importaciones en el servidor
echo "🔄 Aplicando correcciones de importación..."

# Navegar al directorio del proyecto
cd /home/pablo

# Hacer pull de los cambios más recientes
echo "📥 Obteniendo cambios del repositorio..."
git pull origin main

# Verificar que los cambios se aplicaron
echo "✅ Verificando cambios aplicados..."

# Verificar que amigro.py tiene la importación correcta
if grep -q "send_options, send_menu" app/ats/chatbot/workflow/business_units/amigro/amigro.py; then
    echo "✅ amigro.py - Importación corregida"
else
    echo "❌ amigro.py - Importación incorrecta"
fi

# Verificar que __init__.py de services expone las funciones correctas
if grep -q "send_message" app/ats/integrations/services/__init__.py; then
    echo "✅ services/__init__.py - send_message expuesta"
else
    echo "❌ services/__init__.py - send_message no expuesta"
fi

# Probar la migración
echo "🚀 Probando migración..."
source venv/bin/activate
python manage.py makemigrations --dry-run

echo "🎉 Proceso completado!" 