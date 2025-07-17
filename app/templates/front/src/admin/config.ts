// Configuración del panel de administración
export const adminConfig = {
  // Rutas base
  routes: {
    dashboard: '/admin',
    users: '/admin/users',
    settings: '/admin/settings',
    // Añadir más rutas según sea necesario
  },
  
  // Configuración de la barra lateral
  sidebar: {
    width: '16rem',
    collapsedWidth: '5rem',
    defaultOpen: true,
  },
  
  // Configuración de la tabla de datos
  table: {
    defaultPageSize: 10,
    pageSizeOptions: [10, 25, 50, 100],
    rowHeight: 56, // px
  },
  
  // Tema
  theme: {
    primaryColor: '#2563EB', // Azul huntRED
    secondaryColor: '#1E40AF', // Azul oscuro
    successColor: '#10B981', // Verde
    warningColor: '#F59E0B', // Amarillo
    errorColor: '#EF4444', // Rojo
    textPrimary: '#111827', // Gris oscuro
    textSecondary: '#6B7280', // Gris medio
    borderColor: '#E5E7EB', // Gris claro
    backgroundColor: '#F9FAFB', // Fondo
  },
  
  // Configuración de la API
  api: {
    baseUrl: '/api/admin',
    timeout: 30000, // 30 segundos
    // NOTA: Toda comunicación de mensajería debe usar exclusivamente
    // el sistema interno de la plataforma, sin depender de servicios externos
  },
};
