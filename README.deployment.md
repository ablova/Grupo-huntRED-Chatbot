# Guía de Despliegue para Grupo huntRED®

Este documento proporciona instrucciones para desplegar correctamente los cambios realizados en el sistema de Grupo huntRED®, siguiendo las reglas globales para optimización de rendimiento y mantenimiento de código.

## Cambios Implementados

1. **Mejora de inicialización de Django**
   - Implementación de lazy loading para evitar dependencias circulares
   - Soporte para entornos duales (desarrollo local con SQLite, producción con PostgreSQL)
   - Middleware personalizado para adaptación de base de datos

2. **Migraciones de Base de Datos**
   - Nuevos campos WordPress añadidos al modelo BusinessUnit
   - Compatibilidad entre entornos de desarrollo y producción

## Instrucciones para Desplegar en Servidor

### 1. Archivos a Subir
Asegúrate de subir los siguientes archivos al servidor:

- `app/migrations/0001_add_wordpress_fields_to_business_unit.py` - La migración
- `app/middleware/database_adapter.py` y `app/middleware/__init__.py` - Middleware de adaptación
- `ai_huntred/settings.py` - Configuración actualizada
- `app/models.py` - Modelos con lazy loading

### 2. Verificación de Dependencias
Si ya existen migraciones en el servidor, edita manualmente `0001_add_wordpress_fields_to_business_unit.py` 
para actualizar su lista `dependencies` con la referencia a la migración anterior.

### 3. Ejecución de Migraciones
En el servidor, ejecuta:
```bash
python manage.py migrate
```

### 4. Verificación
Verifica que el modelo BusinessUnit ahora incluye los campos:
- `wordpress_base_url`
- `wordpress_auth_token`

## Desarrollo Local

Para desarrollo local en entornos con problemas de compatibilidad de PostgreSQL (como macOS con Apple Silicon):

1. Ejecuta el script `fix_migrations_for_server.py` para generar migraciones
2. Usa la configuración adaptada con SQLite para pruebas locales

## Mantenimiento Futuro

Al realizar cambios futuros en modelos, sigue estas prácticas:

1. Usa lazy loading para referencias entre modelos
2. Mantén la separación entre entornos local y producción
3. Evita dependencias circulares durante la inicialización

---

Documento generado: Mayo 2025
Contacto: Equipo de Desarrollo de Grupo huntRED®
