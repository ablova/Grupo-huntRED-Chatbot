import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AdminLayout from './layouts/AdminLayout';
import DashboardPage from './pages/DashboardPage';

// Páginas de ejemplo (reemplazar con páginas reales)
const UsersPage = () => <div className="p-6">Gestión de Usuarios</div>;
const SettingsPage = () => <div className="p-6">Configuración</div>;

const AdminRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<AdminLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="settings" element={<SettingsPage />} />
        
        {/* Ruta por defecto para rutas no encontradas */}
        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Route>
    </Routes>
  );
};

export default AdminRoutes;
