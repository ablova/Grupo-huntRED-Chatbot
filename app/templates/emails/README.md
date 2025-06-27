# Plantillas de Emails

Este directorio contiene las plantillas base de emails del sistema huntRED.

## Estructura recomendada
- `base_email.html`: Plantilla base para todos los correos.
- `notificacion_nom35.html`: Notificación de NOM 35 agendada o completada.
- `upsell_assessment.html`: Plantilla para sugerir otros assessments o servicios.
- `components/`: Fragmentos reutilizables (header, footer, branding).

## Personalización
- Las plantillas pueden ser sobreescritas desde el admin por superadmin o consultores seniors.
- Si existe una versión personalizada en la base de datos, se usa esa; si no, se usa la de archivo.

## Variables dinámicas
Puedes usar variables como `{{nombre_cliente}}`, `{{logo_url}}`, `{{reporte_url}}`, etc.

## Recursos
- Logos y branding en `static/images/logos/`
- CSS específico en `static/css/emails/`

## Edición
- Editor visual y vista previa disponible en el admin para usuarios autorizados. 