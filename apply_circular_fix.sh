#!/bin/bash

echo "🔧 Aplicando corrección de referencia circular en el servidor..."

# Conectar al servidor y aplicar cambios
ssh pablo@45.79.12.84 << 'EOF'
    cd /home/pablo/app
    echo "📥 Actualizando código desde GitHub..."
    git stash
    git pull origin main
    
    echo "🔍 Verificando que no hay errores de importación..."
    python manage.py check --deploy
    
    echo "📊 Ejecutando migraciones..."
    python manage.py migrate
    
    echo "✅ Corrección aplicada exitosamente"
    echo "🔄 Reiniciando servicios..."
    sudo systemctl restart gunicorn
    sudo systemctl restart celery
    sudo systemctl restart celerybeat
    
    echo "🎉 Servidor actualizado y reiniciado"
EOF

echo "✅ Script completado" 