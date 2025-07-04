import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, LoginCredentials, AuthContextType } from '../types/auth';
import { apiClient } from '../services/api';
import toast from 'react-hot-toast';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Check if user is authenticated on app load
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setLoading(false);
        return;
      }

      // Verify token and get user data
      const response = await apiClient.get('/auth/me/');
      setUser(response.data);
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      setLoading(true);
      
      const response = await apiClient.post('/auth/login/', credentials);
      const { access_token, refresh_token, user: userData } = response.data;

      // Store tokens
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      // Set user
      setUser(userData);

      toast.success('¡Bienvenido a huntRED® v2!');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Error al iniciar sesión';
      toast.error(message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      // Try to logout from server
      await apiClient.post('/auth/logout/');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Always clear local state
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      toast.success('Sesión cerrada correctamente');
    }
  };

  const refreshToken = async (): Promise<string | null> => {
    try {
      const refresh = localStorage.getItem('refresh_token');
      if (!refresh) {
        throw new Error('No refresh token available');
      }

      const response = await apiClient.post('/auth/refresh/', {
        refresh: refresh
      });

      const { access } = response.data;
      localStorage.setItem('access_token', access);
      
      return access;
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout(); // Force logout if refresh fails
      return null;
    }
  };

  const updateProfile = async (userData: Partial<User>): Promise<void> => {
    try {
      const response = await apiClient.patch('/auth/profile/', userData);
      setUser(response.data);
      toast.success('Perfil actualizado correctamente');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Error al actualizar perfil';
      toast.error(message);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    login,
    logout,
    refreshToken,
    updateProfile,
    checkAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};