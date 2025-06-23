# 🚀 Sistema huntRED - Control Center & AURA Dashboard

## 📋 Descripción General

Este es el **sistema frontend completo** para el ecosistema huntRED, que incluye:

- **Control Center**: Panel de control unificado para todo el sistema
- **AURA Dashboard**: Dashboard especializado para el motor de IA AURA
- **Sistema de Navegación**: Navegación moderna y responsive
- **APIs Integradas**: Conexión con todos los módulos del backend

## 🏗️ Arquitectura

### Stack Tecnológico
- **React 18** + **TypeScript** + **Vite**
- **Shadcn/ui** + **Radix UI** (Componentes UI)
- **Tailwind CSS** (Estilos)
- **Recharts** (Gráficos)
- **React Router** (Navegación)
- **React Query** (Gestión de estado)

### Estructura de Archivos
```
src/
├── components/
│   ├── ui/           # Componentes Shadcn/ui
│   ├── Navigation.tsx # Navegación principal
│   └── ...           # Otros componentes
├── pages/
│   ├── Index.tsx           # Página principal
│   ├── ControlCenter.tsx   # Control Center
│   ├── AuraDashboard.tsx   # Dashboard AURA
│   └── NotFound.tsx        # 404
├── services/
│   └── auraAPI.ts          # Servicio para APIs de AURA
└── App.tsx                 # Aplicación principal
```

## 🎯 Funcionalidades Principales

### 1. Control Center
**Ruta**: `/control-center`

**Características**:
- ✅ **Vista General**: Resumen de todo el sistema
- ✅ **Gestión de Sistemas**: Monitoreo de servidores
- ✅ **Gestión de Módulos**: Control de ATS, AURA, AI, Infraestructura
- ✅ **Sistema de Alertas**: Notificaciones en tiempo real
- ✅ **Métricas Globales**: KPIs del sistema completo

**Módulos Gestionados**:
- **ATS**: Core, Reclutamiento, Onboarding, Feedback
- **AURA**: Core, Skill Gap, Networking, Analytics, Generative AI
- **AI**: ML Pipeline, NLP Engine, Predictive Analytics
- **Infraestructura**: API Gateway, Load Balancer, Redis, Monitoring

### 2. AURA Dashboard
**Ruta**: `/aura-dashboard`

**Características**:
- ✅ **Análisis de Brechas**: Visualización de skills gaps
- ✅ **Networking**: Métricas de conexiones y colaboraciones
- ✅ **Recomendaciones**: Efectividad de recomendaciones
- ✅ **Performance**: Rendimiento de módulos AURA
- ✅ **Filtros**: Por período y unidad de negocio

### 3. Sistema de Navegación
**Características**:
- ✅ **Responsive**: Funciona en móvil y desktop
- ✅ **Estado del Sistema**: Indicadores en tiempo real
- ✅ **Acciones Rápidas**: Acceso directo a funciones
- ✅ **Navegación Intuitiva**: Menú lateral moderno

## 🚀 Instalación y Configuración

### Prerrequisitos
```bash
# Node.js 18+ y npm
node --version
npm --version
```

### Instalación
```bash
# Clonar el repositorio
cd app/templates/front

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
```

### Variables de Entorno
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_AURA_API_URL=/api/aura

# Development
VITE_DEV_MODE=true
VITE_MOCK_DATA=true
```

### Desarrollo
```bash
# Iniciar servidor de desarrollo
npm run dev

# Build para producción
npm run build

# Preview de producción
npm run preview
```

## 🔌 Integración con APIs

### Endpoints de AURA
```typescript
// Ejemplo de uso
import { auraAPI } from '@/services/auraAPI';

// Obtener métricas del sistema
const metrics = await auraAPI.getSystemMetrics();

// Crear análisis de brechas
const analysis = await auraAPI.createSkillGapAnalysis('user123', 'huntRED Executive');

// Obtener recomendaciones
const recommendations = await auraAPI.getRecommendations('user123', 'huntRED Executive');
```

### Endpoints Disponibles
- `GET /api/aura/skill-gap-analyses` - Listar análisis
- `POST /api/aura/skill-gap-analyses` - Crear análisis
- `GET /api/aura/networking-connections` - Conexiones
- `GET /api/aura/analytics-dashboard` - Dashboard
- `GET /api/aura/recommendations` - Recomendaciones
- `GET /api/aura/system-metrics` - Métricas del sistema
- `GET /api/aura/alerts` - Alertas del sistema

## 🎨 Sistema de Diseño

### Colores Tech
```css
--tech-blue: #3b82f6
--tech-purple: #8b5cf6
--tech-cyan: #06b6d4
```

### Componentes UI
- **Cards**: Para mostrar información
- **Progress**: Para métricas y estados
- **Badges**: Para etiquetas y estados
- **Tabs**: Para navegación entre secciones
- **Charts**: Para visualizaciones de datos

### Animaciones
- `fade-in`: Entrada suave
- `slide-in-right`: Deslizamiento
- `float`: Efecto flotante
- `pulse-slow`: Pulso lento

## 📊 Métricas y KPIs

### Control Center
- **Usuarios Totales**: 156
- **Sesiones Activas**: 89
- **Requests Totales**: 1,247
- **Tiempo de Respuesta**: 245ms
- **Uptime**: 99.8%
- **Último Incidente**: 10/01/2024

### AURA Dashboard
- **Análisis de Brechas**: 156 (+12%)
- **Conexiones**: 2,847 (+8%)
- **Recomendaciones**: 1,234 (+15%)
- **Satisfacción**: 4.6/5 (+0.3)

## 🔧 Configuración Avanzada

### Proxy para Desarrollo
```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
```

### Build para Producción
```bash
# Build optimizado
npm run build

# Los archivos se generan en:
# ../../../static/frontend/
```

### Integración con Django
```python
# settings.py
STATICFILES_DIRS = [
    BASE_DIR / "static" / "frontend",
]

# urls.py
urlpatterns = [
    path('static/frontend/', serve, {'document_root': settings.STATICFILES_DIRS[0]}),
]
```

## 🚨 Sistema de Alertas

### Tipos de Alertas
- **Info**: Información general
- **Warning**: Advertencias
- **Error**: Errores críticos
- **Success**: Operaciones exitosas

### Prioridades
- **Low**: Baja prioridad
- **Medium**: Prioridad media
- **High**: Alta prioridad
- **Critical**: Crítica

## 🔐 Seguridad

### Autenticación
- JWT tokens para APIs
- Session-based para Django
- CSRF protection

### Autorización
- Roles y permisos por unidad de negocio
- Acceso granular a módulos
- Auditoría de acciones

## 📱 Responsive Design

### Breakpoints
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Características Mobile
- Menú hamburguesa
- Navegación táctil
- Gráficos adaptativos
- Cards optimizadas

## 🧪 Testing

### Pruebas Unitarias
```bash
# Ejecutar tests
npm run test

# Coverage
npm run test:coverage
```

### Pruebas E2E
```bash
# Playwright
npm run test:e2e
```

## 📈 Monitoreo y Analytics

### Métricas de Performance
- **LCP**: Largest Contentful Paint
- **FID**: First Input Delay
- **CLS**: Cumulative Layout Shift

### Error Tracking
- Sentry integration
- Error boundaries
- Logging automático

## 🔄 CI/CD

### Pipeline
1. **Build**: Compilación y optimización
2. **Test**: Pruebas automáticas
3. **Deploy**: Despliegue automático
4. **Monitor**: Monitoreo post-deploy

### Environments
- **Development**: `dev.huntred.com`
- **Staging**: `staging.huntred.com`
- **Production**: `ai.huntred.com`

## 📚 Documentación Adicional

### APIs
- [AURA API Documentation](./docs/aura-api.md)
- [Control Center API](./docs/control-center-api.md)

### Componentes
- [UI Components](./docs/ui-components.md)
- [Custom Components](./docs/custom-components.md)

### Guías
- [Getting Started](./docs/getting-started.md)
- [Best Practices](./docs/best-practices.md)
- [Troubleshooting](./docs/troubleshooting.md)

## 🤝 Contribución

### Flujo de Trabajo
1. Fork del repositorio
2. Crear feature branch
3. Desarrollar funcionalidad
4. Tests y linting
5. Pull request
6. Code review
7. Merge

### Estándares de Código
- **TypeScript**: Tipado estricto
- **ESLint**: Linting automático
- **Prettier**: Formateo de código
- **Conventional Commits**: Mensajes de commit

## 📞 Soporte

### Contacto
- **Email**: tech@huntred.com
- **Slack**: #tech-support
- **Documentación**: docs.huntred.com

### Issues
- **GitHub Issues**: Para bugs y features
- **Jira**: Para tracking de proyectos
- **Sentry**: Para errores en producción

---

## 🎉 ¡Sistema Listo!

El **Control Center** y **AURA Dashboard** están completamente implementados y listos para usar. El sistema proporciona:

✅ **Control total** del ecosistema huntRED  
✅ **Monitoreo en tiempo real** de todos los módulos  
✅ **Interfaz moderna** y responsive  
✅ **Integración completa** con las APIs de AURA  
✅ **Sistema de alertas** inteligente  
✅ **Métricas avanzadas** y visualizaciones  

¡El futuro del control de sistemas está aquí! 🚀 