import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { LoginFormData } from '../schemas/login.schema';

interface AuthContextType {
  user: any | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: LoginFormData) => Promise<void>;
  logout: () => void;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  // Verificar si hay una sesión activa al cargar la aplicación
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Aquí iría la lógica para verificar el token con el backend
        // Por ahora simulamos una verificación
        const token = localStorage.getItem('accessToken');
        if (token) {
          // Verificar token con el backend
          // const response = await fetch('/api/auth/verify-token/', { ... });
          // const userData = await response.json();
          // setUser(userData);
        }
      } catch (err) {
        console.error('Error al verificar la autenticación:', err);
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = useCallback(async (data: LoginFormData) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Simulamos una llamada a la API
      // const response = await fetch('/api/auth/login/', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(data),
      // });
      
      // if (!response.ok) {
      //   const errorData = await response.json();
      //   throw new Error(errorData.detail || 'Error al iniciar sesión');
      // }
      
      // const { access, refresh, user: userData } = await response.json();
      
      // Simulación de respuesta exitosa
      const mockResponse = {
        access: 'mock-access-token',
        refresh: 'mock-refresh-token',
        user: {
          id: 1,
          email: data.email,
          first_name: 'Usuario',
          last_name: 'Demo',
          is_staff: true,
        },
      };
      
      // Almacenar tokens
      localStorage.setItem('accessToken', mockResponse.access);
      localStorage.setItem('refreshToken', mockResponse.refresh);
      
      // Actualizar estado
      setUser(mockResponse.user);
      
      // Redirigir al dashboard
      navigate('/admin');
    } catch (err) {
      console.error('Error en login:', err);
      setError(
        err instanceof Error 
          ? err.message 
          : 'Error al iniciar sesión. Por favor, inténtalo de nuevo.'
      );
      throw err; // Re-lanzar para manejarlo en el componente
    } finally {
      setIsLoading(false);
    }
  }, [navigate]);

  const logout = useCallback(() => {
    // Limpiar almacenamiento local
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    
    // Actualizar estado
    setUser(null);
    
    // Redirigir al login
    navigate('/login', { replace: true });
  }, [navigate]);

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    error,
  };

  return (
    <AuthContext.Provider value={value}>
      {!isLoading && children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider');
  }
  return context;
}
