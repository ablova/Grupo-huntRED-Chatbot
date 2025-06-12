# Frontend Assets

Este directorio contiene los archivos de frontend para el proyecto Grupo huntRED.

## Estructura

```
static/
├── src/           # Código fuente de estilos (SCSS/CSS)
├── css/          # CSS compilado
└── js/           # Archivos JavaScript
```

## Configuración del Entorno de Desarrollo

1. Asegúrate de tener Node.js instalado (v14+)

2. Instala las dependencias:
   ```bash
   cd /ruta/al/proyecto/app
   npm install
   ```

3. Para desarrollo (modo observador):
   ```bash
   npm run dev
   ```

4. Para producción:
   ```bash
   npm run build
   ```

## Flujo de Trabajo

1. Modifica los archivos en `static/src/`
2. Los cambios se compilan automáticamente en desarrollo
3. Para producción, ejecuta `npm run build`

## Dependencias

- Tailwind CSS
- PostCSS
- Autoprefixer
