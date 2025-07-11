#!/bin/bash

# Script para desplegar el frontend en el servidor
echo "🚀 Iniciando despliegue del frontend..."

# Navegar al directorio del frontend
cd /home/pablo/app/templates/front

# Activar el entorno virtual
source /home/pablo/venv/bin/activate

# Instalar dependencias si es necesario
echo "📦 Instalando dependencias..."
npm install

# Limpiar build anterior
echo "🧹 Limpiando build anterior..."
rm -rf dist/

# Construir el proyecto
echo "🔨 Construyendo el proyecto..."
npm run build

# Verificar que el build se creó correctamente
if [ -d "dist" ]; then
    echo "✅ Build completado exitosamente"
    echo "📁 Contenido del directorio dist:"
    ls -la dist/
else
    echo "❌ Error: No se pudo crear el build"
    exit 1
fi

# Reiniciar servicios si es necesario
echo "🔄 Reiniciando servicios..."
sudo systemctl reload nginx

echo "🎉 Despliegue completado!" 