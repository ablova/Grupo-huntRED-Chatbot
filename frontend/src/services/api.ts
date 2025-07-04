import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { AuthTokens, ApiError, ApiResponse } from '../types/auth';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
const API_TIMEOUT = 30000; // 30 seconds

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Token management
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token!);
    }
  });
  
  failedQueue = [];
};

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add request timestamp for debugging
    config.metadata = { startTime: new Date() };
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Add response time for debugging
    if (response.config.metadata) {
      const endTime = new Date();
      const duration = endTime.getTime() - response.config.metadata.startTime.getTime();
      console.log(`API Request to ${response.config.url} took ${duration}ms`);
    }
    
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };
    
    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return apiClient(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
          refresh: refreshToken
        });

        const { access } = response.data;
        localStorage.setItem('access_token', access);
        
        processQueue(null, access);
        
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access}`;
        }
        
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Emit event for auth context to handle
        window.dispatchEvent(new CustomEvent('auth:logout'));
        
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Handle other errors
    if (error.response) {
      // Server responded with error status
      const apiError: ApiError = {
        detail: error.response.data?.detail || error.message,
        code: error.response.data?.code,
        field_errors: error.response.data?.field_errors,
        non_field_errors: error.response.data?.non_field_errors,
      };
      
      error.apiError = apiError;
    } else if (error.request) {
      // Request was made but no response received
      error.apiError = {
        detail: 'No se pudo conectar con el servidor. Verifica tu conexión a internet.',
        code: 'NETWORK_ERROR'
      };
    } else {
      // Something else happened
      error.apiError = {
        detail: error.message || 'Error desconocido',
        code: 'UNKNOWN_ERROR'
      };
    }

    return Promise.reject(error);
  }
);

// Generic API methods
export const api = {
  // GET request
  get: async <T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    try {
      const response = await apiClient.get(url, config);
      return {
        data: response.data,
        status: response.status,
        message: response.data?.message,
      };
    } catch (error: any) {
      throw error;
    }
  },

  // POST request
  post: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    try {
      const response = await apiClient.post(url, data, config);
      return {
        data: response.data,
        status: response.status,
        message: response.data?.message,
      };
    } catch (error: any) {
      throw error;
    }
  },

  // PUT request
  put: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    try {
      const response = await apiClient.put(url, data, config);
      return {
        data: response.data,
        status: response.status,
        message: response.data?.message,
      };
    } catch (error: any) {
      throw error;
    }
  },

  // PATCH request
  patch: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    try {
      const response = await apiClient.patch(url, data, config);
      return {
        data: response.data,
        status: response.status,
        message: response.data?.message,
      };
    } catch (error: any) {
      throw error;
    }
  },

  // DELETE request
  delete: async <T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    try {
      const response = await apiClient.delete(url, config);
      return {
        data: response.data,
        status: response.status,
        message: response.data?.message,
      };
    } catch (error: any) {
      throw error;
    }
  },

  // File upload
  upload: async <T = any>(url: string, file: File, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post(url, formData, {
        ...config,
        headers: {
          ...config?.headers,
          'Content-Type': 'multipart/form-data',
        },
      });
      return {
        data: response.data,
        status: response.status,
        message: response.data?.message,
      };
    } catch (error: any) {
      throw error;
    }
  },

  // Download file
  download: async (url: string, filename?: string, config?: AxiosRequestConfig): Promise<void> => {
    try {
      const response = await apiClient.get(url, {
        ...config,
        responseType: 'blob',
      });

      // Create blob link to download
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename || 'download';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error: any) {
      throw error;
    }
  },
};

// Specialized API endpoints
export const authAPI = {
  login: (credentials: { username: string; password: string }) =>
    api.post('/auth/login/', credentials),
  
  logout: () =>
    api.post('/auth/logout/'),
  
  refresh: (refreshToken: string) =>
    api.post('/auth/refresh/', { refresh: refreshToken }),
  
  me: () =>
    api.get('/auth/me/'),
  
  updateProfile: (data: any) =>
    api.patch('/auth/profile/', data),
  
  changePassword: (data: { old_password: string; new_password: string }) =>
    api.post('/auth/change-password/', data),
  
  resetPassword: (email: string) =>
    api.post('/auth/reset-password/', { email }),
  
  confirmResetPassword: (data: { token: string; new_password: string }) =>
    api.post('/auth/reset-password-confirm/', data),
};

export const candidatesAPI = {
  list: (params?: any) =>
    api.get('/candidates/', { params }),
  
  get: (id: string) =>
    api.get(`/candidates/${id}/`),
  
  create: (data: any) =>
    api.post('/candidates/', data),
  
  update: (id: string, data: any) =>
    api.patch(`/candidates/${id}/`, data),
  
  delete: (id: string) =>
    api.delete(`/candidates/${id}/`),
  
  // ML Analysis
  analyzeSkills: (id: string, jobId?: string) =>
    api.post(`/candidates/${id}/analyze-skills/`, { job_id: jobId }),
  
  analyzePersonality: (id: string) =>
    api.post(`/candidates/${id}/analyze-personality/`),
  
  getAnalysisResults: (id: string) =>
    api.get(`/candidates/${id}/analysis-results/`),
  
  // AURA Analysis
  getAuraProfile: (id: string) =>
    api.get(`/candidates/${id}/aura-profile/`),
  
  getCompatibilityAnalysis: (id: string, companyId: string) =>
    api.get(`/candidates/${id}/compatibility/${companyId}/`),
};

export const jobsAPI = {
  list: (params?: any) =>
    api.get('/jobs/', { params }),
  
  get: (id: string) =>
    api.get(`/jobs/${id}/`),
  
  create: (data: any) =>
    api.post('/jobs/', data),
  
  update: (id: string, data: any) =>
    api.patch(`/jobs/${id}/`, data),
  
  delete: (id: string) =>
    api.delete(`/jobs/${id}/`),
  
  // Matching
  findCandidates: (id: string, params?: any) =>
    api.get(`/jobs/${id}/find-candidates/`, { params }),
  
  matchCandidate: (jobId: string, candidateId: string) =>
    api.post(`/jobs/${jobId}/match-candidate/`, { candidate_id: candidateId }),
};

export const workflowsAPI = {
  list: (params?: any) =>
    api.get('/workflows/', { params }),
  
  get: (id: string) =>
    api.get(`/workflows/${id}/`),
  
  create: (data: any) =>
    api.post('/workflows/', data),
  
  update: (id: string, data: any) =>
    api.patch(`/workflows/${id}/`, data),
  
  delete: (id: string) =>
    api.delete(`/workflows/${id}/`),
  
  // Workflow actions
  start: (id: string) =>
    api.post(`/workflows/${id}/start/`),
  
  advance: (id: string, stageId: string) =>
    api.post(`/workflows/${id}/advance/`, { stage_id: stageId }),
  
  pause: (id: string, reason?: string) =>
    api.post(`/workflows/${id}/pause/`, { reason }),
  
  resume: (id: string) =>
    api.post(`/workflows/${id}/resume/`),
  
  cancel: (id: string, reason?: string) =>
    api.post(`/workflows/${id}/cancel/`, { reason }),
};

export const assessmentsAPI = {
  list: (params?: any) =>
    api.get('/assessments/', { params }),
  
  get: (id: string) =>
    api.get(`/assessments/${id}/`),
  
  create: (data: any) =>
    api.post('/assessments/', data),
  
  update: (id: string, data: any) =>
    api.patch(`/assessments/${id}/`, data),
  
  delete: (id: string) =>
    api.delete(`/assessments/${id}/`),
  
  // Assessment actions
  start: (id: string) =>
    api.post(`/assessments/${id}/start/`),
  
  submitResponse: (id: string, questionId: string, answer: any) =>
    api.post(`/assessments/${id}/submit-response/`, { 
      question_id: questionId, 
      answer 
    }),
  
  complete: (id: string) =>
    api.post(`/assessments/${id}/complete/`),
  
  getResults: (id: string) =>
    api.get(`/assessments/${id}/results/`),
  
  generateReport: (id: string, type: string = 'full') =>
    api.get(`/assessments/${id}/report/`, { params: { type } }),
};

export const notificationsAPI = {
  list: (params?: any) =>
    api.get('/notifications/', { params }),
  
  get: (id: string) =>
    api.get(`/notifications/${id}/`),
  
  markAsRead: (id: string) =>
    api.patch(`/notifications/${id}/mark-read/`),
  
  markAllAsRead: () =>
    api.post('/notifications/mark-all-read/'),
  
  getUnreadCount: () =>
    api.get('/notifications/unread-count/'),
  
  // Preferences
  getPreferences: () =>
    api.get('/notifications/preferences/'),
  
  updatePreferences: (data: any) =>
    api.patch('/notifications/preferences/', data),
};

export const analyticsAPI = {
  dashboard: () =>
    api.get('/analytics/dashboard/'),
  
  candidates: (params?: any) =>
    api.get('/analytics/candidates/', { params }),
  
  jobs: (params?: any) =>
    api.get('/analytics/jobs/', { params }),
  
  workflows: (params?: any) =>
    api.get('/analytics/workflows/', { params }),
  
  assessments: (params?: any) =>
    api.get('/analytics/assessments/', { params }),
  
  ml: (params?: any) =>
    api.get('/analytics/ml/', { params }),
  
  aura: (params?: any) =>
    api.get('/analytics/aura/', { params }),
};

// Error handling utility
export const handleApiError = (error: any): string => {
  if (error.apiError) {
    const apiError: ApiError = error.apiError;
    
    if (apiError.detail) {
      return apiError.detail;
    }
    
    if (apiError.non_field_errors && apiError.non_field_errors.length > 0) {
      return apiError.non_field_errors.join(', ');
    }
    
    if (apiError.field_errors) {
      const fieldErrors = Object.values(apiError.field_errors).flat();
      return fieldErrors.join(', ');
    }
  }
  
  return error.message || 'Error desconocido';
};

// Request cancellation utility
export const createCancelToken = () => {
  const cancelTokenSource = axios.CancelToken.source();
  return cancelTokenSource;
};

export default api;