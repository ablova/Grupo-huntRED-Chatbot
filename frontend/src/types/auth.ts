export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  avatar?: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  date_joined: string;
  last_login?: string;
  
  // Business Unit Info
  business_unit?: {
    id: string;
    name: string;
    company_name: string;
    logo?: string;
  };
  
  // Role Info
  role: {
    id: string;
    name: string;
    display_name: string;
    permissions: string[];
  };
  
  // Preferences
  preferences: {
    theme: 'light' | 'dark' | 'system';
    language: string;
    timezone: string;
    notifications: {
      email: boolean;
      push: boolean;
      sms: boolean;
    };
  };
  
  // Profile Info
  profile: {
    phone?: string;
    position?: string;
    department?: string;
    bio?: string;
    linkedin_url?: string;
    twitter_url?: string;
  };
}

export interface LoginCredentials {
  username: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  business_unit_id?: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  new_password: string;
}

export interface ChangePassword {
  old_password: string;
  new_password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<string | null>;
  updateProfile: (userData: Partial<User>) => Promise<void>;
  checkAuth: () => Promise<void>;
}

// Permission types
export interface Permission {
  id: string;
  name: string;
  codename: string;
  content_type: string;
}

export interface Role {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  permissions: Permission[];
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// API Error types
export interface ApiError {
  detail?: string;
  code?: string;
  field_errors?: Record<string, string[]>;
  non_field_errors?: string[];
}

export interface ApiResponse<T = any> {
  data: T;
  status: number;
  message?: string;
  errors?: ApiError;
}

// Login session info
export interface LoginSession {
  id: string;
  user_agent: string;
  ip_address: string;
  location?: string;
  device_type: string;
  last_activity: string;
  is_current: boolean;
  created_at: string;
}

// Two-factor authentication
export interface TwoFactorAuth {
  is_enabled: boolean;
  backup_codes_remaining?: number;
  last_used?: string;
}

export interface EnableTwoFactorRequest {
  password: string;
  method: 'app' | 'sms' | 'email';
}

export interface VerifyTwoFactorRequest {
  code: string;
  backup_code?: boolean;
}

// Social auth
export interface SocialAuthProvider {
  name: string;
  display_name: string;
  icon: string;
  is_enabled: boolean;
  auth_url: string;
}

export interface SocialAuthCallback {
  provider: string;
  code: string;
  state?: string;
}

// Account security
export interface SecurityLog {
  id: string;
  event_type: 'login' | 'logout' | 'password_change' | 'profile_update' | 'security_alert';
  description: string;
  ip_address: string;
  user_agent: string;
  location?: string;
  success: boolean;
  created_at: string;
}

export interface AccountSecurity {
  two_factor_enabled: boolean;
  last_password_change: string;
  active_sessions_count: number;
  recent_login_attempts: number;
  security_score: number;
  recommendations: string[];
}

// User activity
export interface UserActivity {
  id: string;
  action: string;
  description: string;
  entity_type?: string;
  entity_id?: string;
  metadata?: Record<string, any>;
  ip_address: string;
  user_agent: string;
  created_at: string;
}

// Notification preferences
export interface NotificationPreferences {
  email_notifications: {
    workflow_updates: boolean;
    assessment_reminders: boolean;
    interview_schedules: boolean;
    system_alerts: boolean;
    marketing: boolean;
  };
  push_notifications: {
    workflow_updates: boolean;
    assessment_reminders: boolean;
    interview_schedules: boolean;
    system_alerts: boolean;
  };
  sms_notifications: {
    urgent_alerts: boolean;
    interview_reminders: boolean;
  };
  frequency: 'immediate' | 'hourly' | 'daily' | 'weekly';
  quiet_hours: {
    enabled: boolean;
    start_time: string;
    end_time: string;
    timezone: string;
  };
}

// API key management
export interface ApiKey {
  id: string;
  name: string;
  key_preview: string; // Only shows first/last few characters
  permissions: string[];
  last_used?: string;
  expires_at?: string;
  is_active: boolean;
  created_at: string;
}

export interface CreateApiKeyRequest {
  name: string;
  permissions: string[];
  expires_at?: string;
}

export interface ApiKeyResponse {
  id: string;
  name: string;
  key: string; // Full key only shown once during creation
  permissions: string[];
  expires_at?: string;
  created_at: string;
}