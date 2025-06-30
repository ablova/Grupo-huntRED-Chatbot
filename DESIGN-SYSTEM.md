# HuntRED Design System

## Arquitectura UI/UX Unificada

Este documento describe la arquitectura y principios del sistema de diseño unificado implementado para HuntRED, que proporciona una experiencia de usuario consistente y de alta calidad en todas las interfaces de la aplicación.

### Principios fundamentales

- **Coherencia**: Una experiencia visual y funcional consistente en todas las interfaces
- **Mantenibilidad**: Una única fuente de verdad para todos los componentes UI/UX
- **Rendimiento**: Optimización de carga y recursos mediante la centralización
- **Flexibilidad**: Adaptable a múltiples contextos de usuario manteniendo coherencia

## Estructura técnica

```
/src/
  ├── styles/               # Estilos centralizados
  │   ├── core/             # Fundamentos de diseño (variables, temas)
  │   ├── components/       # Estilos de componentes 
  │   └── main.css          # Punto de entrada principal para CSS
  │
  ├── js/                   # JavaScript centralizado
  │   ├── core/             # Funcionalidades base
  │   ├── components/       # Componentes reutilizables
  │   └── utils/            # Utilidades
  │
  └── components/           # Componentes React
      ├── shared/           # Componentes usados en todos los roles
      ├── dashboards/       # Componentes específicos para dashboards
      └── forms/            # Componentes específicos para formularios
```

## Arquitectura híbrida React+Vite y Django

Esta aplicación utiliza una arquitectura híbrida:

- **React+Vite**: Componentes interactivos avanzados, visualizaciones y elementos de alta interactividad
- **Django Templates**: Framework base de la aplicación y renderizado de HTML

Esta combinación nos permite:
1. Mantener la robustez del backend Django
2. Aprovechar React donde agrega más valor (gráficos, Kanban, etc.)
3. Compartir un sistema de diseño unificado entre ambas partes

## Sistema de temas y roles

### Temas (Claro/Oscuro)

El sistema implementa un cambio de tema basado en el atributo `data-theme`:

```html
<html data-theme="dark">
```

Los temas se aplican mediante variables CSS que cambian según el tema:

```css
:root {
  --background: #ffffff;
  --text-color: #1a202c;
}

[data-theme="dark"] {
  --background: #1a202c;
  --text-color: #f7fafc;
}
```

### Roles de usuario

Todos los roles de usuario (cliente, consultor, admin, superadmin) comparten la **misma base técnica y funcional** del sistema de diseño. Las diferencias son mínimas y puramente visuales:

```html
<html data-theme="dark" data-role="consultant">
```

El atributo `data-role` permite:

1. Pequeños indicadores visuales (principalmente color de acento) para ayudar al usuario a identificar su contexto
2. Mantener una experiencia coherente en toda la aplicación

```css
/* Ejemplos de acentos por rol - sutil pero reconocible */
[data-role="client"] .accent-border {
  border-color: var(--client-accent);
}

[data-role="consultant"] .accent-border {
  border-color: var(--consultant-accent);
}
```

## Uso en la aplicación

### Para Django Templates

```html
{% extends 'base.html' %}

{% block content %}
<div class="dashboard-container">
  <h1 class="text-2xl font-bold mb-4">Dashboard</h1>
  <!-- Los componentes heredan automáticamente el tema y rol -->
</div>
{% endblock %}
```

### Para componentes React

```jsx
function DashboardCard({ title, children }) {
  // Los estilos responderán automáticamente al tema y rol del documento
  return (
    <div className="bg-card p-4 rounded-lg shadow">
      <h2 className="text-lg font-medium mb-2">{title}</h2>
      {children}
    </div>
  );
}
```

## Beneficios del sistema unificado

- **Consistencia**: Experiencia coherente en todas las interfaces
- **Eficiencia**: Desarrollo más rápido al reutilizar componentes
- **Mantenibilidad**: Cambios en un solo lugar afectan a toda la aplicación
- **Escalabilidad**: Nuevos roles o interfaces heredan automáticamente el sistema de diseño
- **Rendimiento**: Carga óptima de recursos y menor duplicación

## Mejores prácticas para desarrolladores

1. **Siempre** use las variables CSS definidas en vez de colores literales
2. **Evite** agregar estilos específicos por rol a menos que sea estrictamente necesario
3. **Mantenga** todos los componentes adaptables a ambos temas (claro/oscuro)
4. **Utilice** los componentes compartidos en lugar de crear nuevos cuando sea posible
5. **Pruebe** siempre en todos los temas y roles relevantes
