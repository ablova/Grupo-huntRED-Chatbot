export interface LoginFormData {
  email: string;
  password: string;
  rememberMe: boolean;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    is_staff: boolean;
  };
}

export interface AuthState {
  user: AuthResponse['user'] | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}
