#!/bin/bash

echo '🔄 Reiniciando frontend HuntRED...'

# Ir al directorio del frontend
cd /home/pablo/app/templates/front

# Detener procesos de desarrollo si están corriendo
pkill -f 'npm run dev' || true
pkill -f 'vite' || true

# Instalar dependencias si es necesario
echo '📦 Verificando dependencias...'
npm install

# Construir el frontend
echo '🔨 Construyendo frontend...'
npm run build

# Copiar archivos estáticos a Django si es necesario
echo '📁 Copiando archivos estáticos...'
cp -r dist/* /home/pablo/ai_huntred/staticfiles/ 2>/dev/null || true

# Recolectar archivos estáticos de Django
echo '🗂️ Recolectando archivos estáticos de Django...'
cd /home/pablo/ai_huntred
source /home/pablo/venv/bin/activate
DJANGO_SETTINGS_MODULE=ai_huntred.settings.production python manage.py collectstatic --noinput

# Reiniciar servicios
echo '🔄 Reiniciando servicios...'
sudo systemctl restart gunicorn
sudo systemctl reload nginx

echo '✅ Frontend reiniciado exitosamente!'
echo '🌐 Frontend disponible en: https://ai.huntred.com'
echo '🔧 Admin disponible en: https://ai.huntred.com/admin' 