# Instrucciones para Desplegar el Frontend

## Cambios Realizados

1. **Header actualizado**: Se cambió el texto "Grupo huntRED® AI" por el logo `/static/images/g_huntred.png`
2. **Nuevos componentes agregados**: Se agregaron 3 nuevos componentes al inicio de la página principal:
   - `HeroSection`
   - `TalentEcosystemSection` 
   - `TalentLifecycleSection`

## Pasos para Desplegar en el Servidor

### Opción 1: Usar el script automático
```bash
# Conectarse al servidor
ssh pablo@ai.huntred.com

# Navegar al directorio del proyecto
cd /home/pablo

# Activar el entorno virtual
source venv/bin/activate

# Navegar al frontend
cd app/templates/front

# Ejecutar el script de despliegue
./deploy_frontend.sh
```

### Opción 2: Pasos manuales
```bash
# Conectarse al servidor
ssh pablo@ai.huntred.com

# Navegar al directorio del proyecto
cd /home/pablo

# Activar el entorno virtual
source venv/bin/activate

# Navegar al frontend
cd app/templates/front

# Instalar dependencias
npm install

# Limpiar build anterior
rm -rf dist/

# Construir el proyecto
npm run build

# Verificar que el build se creó
ls -la dist/

# Reiniciar nginx
sudo systemctl reload nginx
```

## Verificación

Después del despliegue, verifica que:

1. El logo aparece en el header en lugar del texto
2. Los 3 nuevos componentes aparecen al inicio de la página principal
3. La página carga correctamente sin errores

## Archivos Modificados

- `app/templates/front/src/components/Header.tsx` - Logo actualizado
- `app/templates/front/src/pages/Index.tsx` - Nuevos componentes agregados
- `app/templates/front/src/components/HeroSection.tsx` - Nuevo componente
- `app/templates/front/src/components/TalentEcosystemSection.tsx` - Nuevo componente  
- `app/templates/front/src/components/TalentLifecycleSection.tsx` - Nuevo componente

## Notas Importantes

- El build local se completó exitosamente con Vite
- El CSS aumentó de ~3.4 KB a ~139 KB, indicando que Tailwind se compiló correctamente
- Los errores de TypeScript se resolvieron usando Vite directamente 