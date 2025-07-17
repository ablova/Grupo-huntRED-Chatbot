import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Providers
import { AuthProvider } from '@/features/auth/hooks/useAuth';

// Componentes de UI
import { LoadingSpinner } from '@/components/ui/loading-spinner';

// Layouts
import { MainLayout } from '@/layouts/MainLayout';

// Páginas públicas
import Index from '../pages/Index';
import AIServicesPage from '../pages/ai/AIServicesPage';
import GenIAPage from '../pages/ai/GenIAPage';
import AURAPage from '../pages/ai/AURAPage';
import PlataformaPage from '../pages/PlataformaPage';
import LaboratorioPage from '../pages/LaboratorioPage';
import CalculadoraPage from '../pages/CalculadoraPage';

// Páginas de autenticación
const LoginPage = lazy(() => import('@/features/auth/pages/LoginPage'));
const ForgotPasswordPage = lazy(() => import('@/features/auth/pages/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('@/features/auth/pages/ResetPasswordPage'));

// Panel de administración (carga perezosa)
const AdminRoutes = lazy(() => import('@/admin/routes'));

// Componente de carga
const Loading = () => (
  <div className="flex items-center justify-center min-h-screen">
    <LoadingSpinner className="w-12 h-12 text-blue-600" />
  </div>
);

/**
 * Componente principal de rutas de la aplicación
 * Estructura multi-página organizada según líneas de negocio
 */
const AppRoutes: React.FC = () => {
  return (
    <AuthProvider>
      <Routes>
        {/* Rutas públicas */}
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Index />} />
          <Route path="ai-services" element={<AIServicesPage />} />
          <Route path="ai-services/genia" element={<GenIAPage />} />
          <Route path="ai-services/aura" element={<AURAPage />} />
          <Route path="plataforma" element={<PlataformaPage />} />
          <Route path="laboratorio" element={<LaboratorioPage />} />
          <Route path="calculadora" element={<CalculadoraPage />} />
          
          {/* Rutas de autenticación */}
          <Route path="login" element={
            <Suspense fallback={<Loading />}>
              <LoginPage />
            </Suspense>
          } />
          
          <Route path="forgot-password" element={
            <Suspense fallback={<Loading />}>
              <ForgotPasswordPage />
            </Suspense>
          } />
          
          <Route path="reset-password/:uid/:token" element={
            <Suspense fallback={<Loading />}>
              <ResetPasswordPage />
            </Suspense>
          } />
        </Route>
        
        {/* Rutas protegidas */}
        <Route path="/admin/*" element={
          <Suspense fallback={<Loading />}>
            <ProtectedRoute>
              <AdminRoutes />
            </ProtectedRoute>
          </Suspense>
        } />
        
        {/* Ruta para páginas no encontradas */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
};

// Componente para proteger rutas
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <Loading />;
  }

  if (!isAuthenticated) {
    // Redirigir al login, guardando la ubicación actual
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

export default AppRoutes;
