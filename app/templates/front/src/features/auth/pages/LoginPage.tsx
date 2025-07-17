import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { LoginForm } from '../components/LoginForm';
import { LoginFormData } from '../schemas/login.schema';
import { useAuth } from '../hooks/useAuth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Icons } from '@/components/icons';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle2 } from 'lucide-react';

interface LocationState {
  from?: { pathname: string };
  message?: string;
}

export function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  // Check for success message in location state (e.g., after password reset)
  useEffect(() => {
    const state = location.state as LocationState;
    if (state?.message) {
      setSuccessMessage(state.message);
      // Clear the state to prevent showing the message again on refresh
      window.history.replaceState({}, '');
    }
  }, [location.state]);

  const handleSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setError(null);
    
    try {
      await login(data);
      // Redirigir al dashboard después del login exitoso
      navigate('/admin');
    } catch (err) {
      console.error('Error en el login:', err);
      setError(
        err instanceof Error 
          ? err.message 
          : 'Ocurrió un error al iniciar sesión. Por favor, inténtalo de nuevo.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <Icons.logo className="h-12 w-auto text-blue-600" />
          <h1 className="text-2xl font-bold mt-4 text-gray-900">huntRED</h1>
          <p className="text-sm text-gray-500">Panel de administración</p>
        </div>
        
        <Card className="w-full">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold">Iniciar sesión</CardTitle>
            <CardDescription>
              Ingresa tus credenciales para acceder al panel de administración
            </CardDescription>
          </CardHeader>
          
          {successMessage && (
            <div className="px-6 pb-2">
              <Alert variant="success">
                <CheckCircle2 className="h-4 w-4" />
                <AlertDescription>
                  {successMessage}
                </AlertDescription>
              </Alert>
            </div>
          )}
          <CardContent>
            <LoginForm 
              onSubmit={handleSubmit} 
              isLoading={isLoading} 
              error={error} 
            />
          </CardContent>
        </Card>
        
        <div className="mt-4 text-center text-sm">
          <p className="text-gray-600">
            ¿No tienes una cuenta?{' '}
            <a href="#" className="font-medium text-blue-600 hover:text-blue-500">
              Contacta al administrador
            </a>
          </p>
        </div>
        
        <div className="mt-8 text-center text-xs text-gray-500">
          <p>© {new Date().getFullYear()} huntRED. Todos los derechos reservados.</p>
        </div>
      </div>
    </div>
  );
}
