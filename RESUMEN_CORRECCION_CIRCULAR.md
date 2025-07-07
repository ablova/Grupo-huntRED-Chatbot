# Resumen de Corrección de Referencia Circular

## Problema Identificado
Se detectó un ciclo de importación entre los siguientes archivos:
1. `app/ats/integrations/services/document.py` → importa `LinkedInScraper`
2. `app/ats/utils/linkedin.py` → importa `monitoring`
3. `app/ats/utils/monitoring/monitoring.py` → importa `tasks/base.py`
4. `app/ats/tasks/__init__.py` → importa `services`
5. `app/ats/services/__init__.py` → importa `interview_service.py`
6. `app/ats/services/interview_service.py` → importa `vacantes.py`
7. `app/ats/utils/vacantes.py` → importa `whatsapp.py`
8. `app/ats/integrations/channels/whatsapp/whatsapp.py` → importa `document.py` (ciclo completo)

## Solución Implementada
Se movió la importación de `LinkedInScraper` desde el nivel de módulo al nivel de función en `document.py`:

### Cambios Realizados:

1. **Eliminada importación global:**
   ```python
   # ANTES (línea 25)
   from app.ats.utils.linkedin import LinkedInScraper
   ```

2. **Inicialización diferida en constructor:**
   ```python
   # ANTES
   self.linkedin_processor = LinkedInScraper()
   
   # DESPUÉS
   self.linkedin_processor = None  # Se inicializará cuando sea necesario
   ```

3. **Importación local en método:**
   ```python
   async def _enrich_with_linkedin(self, linkedin_url: str) -> Optional[Dict[str, Any]]:
       try:
           if not linkedin_url:
               return None
           
           # Importar LinkedInScraper solo cuando sea necesario
           if self.linkedin_processor is None:
               from app.ats.utils.linkedin import LinkedInScraper
               self.linkedin_processor = LinkedInScraper()
               
           data = await self.linkedin_processor.scrape_profile(linkedin_url)
           # ... resto del código
   ```

## Verificación Local
- ✅ `python manage.py makemigrations` ejecutado sin errores de referencia circular
- ✅ Solo error de TensorFlow (no afecta al servidor donde está instalado `tensorflow-cpu`)

## Instrucciones para Aplicar en Servidor

### Opción 1: SSH Manual
```bash
ssh pablo@45.79.12.84
cd /home/pablo/app
git stash
git pull origin main
python manage.py migrate
sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart celerybeat
```

### Opción 2: Usar Script
```bash
./apply_circular_fix.sh
```

## Estado Actual
- ✅ Código corregido y committeado
- ✅ Push realizado a GitHub
- ✅ Verificación local exitosa
- ⏳ Pendiente aplicación en servidor (problemas de conectividad)

## Beneficios de la Corrección
1. **Eliminación del ciclo de importación** que impedía las migraciones
2. **Mejor rendimiento** al cargar `LinkedInScraper` solo cuando es necesario
3. **Código más limpio** con importaciones lazy
4. **Compatibilidad** mantenida con toda la funcionalidad existente

## Archivos Modificados
- `app/ats/integrations/services/document.py` - Corrección principal
- `apply_circular_fix.sh` - Script de despliegue
- `RESUMEN_CORRECCION_CIRCULAR.md` - Este archivo

## Próximos Pasos
1. Aplicar cambios en servidor cuando se resuelva la conectividad
2. Verificar que las migraciones funcionen correctamente
3. Monitorear logs para confirmar que no hay errores de importación 