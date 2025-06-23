// Servicio para conectar con las APIs de AURA
const API_BASE_URL = '/api/aura';

export interface SkillGapAnalysis {
  id: string;
  user_id: string;
  business_unit: string;
  skills_analyzed: number;
  gaps_identified: number;
  recommendations_count: number;
  created_at: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  results?: {
    skills: Array<{
      name: string;
      current_level: number;
      required_level: number;
      gap: number;
      priority: 'low' | 'medium' | 'high' | 'critical';
    }>;
    recommendations: Array<{
      type: 'course' | 'certification' | 'project' | 'mentorship';
      title: string;
      description: string;
      estimated_duration: string;
      difficulty: 'beginner' | 'intermediate' | 'advanced';
      url?: string;
    }>;
  };
}

export interface NetworkingConnection {
  id: string;
  user_id: string;
  target_user_id: string;
  connection_strength: number;
  common_skills: string[];
  recommended_interaction: string;
  status: 'pending' | 'connected' | 'rejected';
  created_at: string;
}

export interface AuraMetrics {
  total_analyses: number;
  active_users: number;
  recommendations_generated: number;
  networking_connections: number;
  average_satisfaction: number;
  system_health: number;
  uptime_percentage: number;
}

export interface SystemAlert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  acknowledged: boolean;
}

class AuraAPI {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('AuraAPI request failed:', error);
      throw error;
    }
  }

  // Skill Gap Analysis
  async getSkillGapAnalyses(businessUnit?: string): Promise<SkillGapAnalysis[]> {
    const params = businessUnit ? `?business_unit=${businessUnit}` : '';
    return this.request<SkillGapAnalysis[]>(`/skill-gap-analyses${params}`);
  }

  async getSkillGapAnalysis(id: string): Promise<SkillGapAnalysis> {
    return this.request<SkillGapAnalysis>(`/skill-gap-analyses/${id}`);
  }

  async createSkillGapAnalysis(userId: string, businessUnit: string): Promise<SkillGapAnalysis> {
    return this.request<SkillGapAnalysis>('/skill-gap-analyses', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, business_unit: businessUnit }),
    });
  }

  // Networking
  async getNetworkingConnections(userId?: string): Promise<NetworkingConnection[]> {
    const params = userId ? `?user_id=${userId}` : '';
    return this.request<NetworkingConnection[]>(`/networking-connections${params}`);
  }

  async createNetworkingConnection(userId: string, targetUserId: string): Promise<NetworkingConnection> {
    return this.request<NetworkingConnection>('/networking-connections', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, target_user_id: targetUserId }),
    });
  }

  // Analytics Dashboard
  async getAnalyticsDashboard(businessUnit?: string): Promise<any> {
    const params = businessUnit ? `?business_unit=${businessUnit}` : '';
    return this.request<any>(`/analytics-dashboard${params}`);
  }

  // Recommendations
  async getRecommendations(userId: string, businessUnit: string): Promise<any[]> {
    return this.request<any[]>(`/recommendations?user_id=${userId}&business_unit=${businessUnit}`);
  }

  async generateRecommendations(userId: string, businessUnit: string): Promise<any[]> {
    return this.request<any[]>('/recommendations/generate', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, business_unit: businessUnit }),
    });
  }

  // System Metrics
  async getSystemMetrics(): Promise<AuraMetrics> {
    return this.request<AuraMetrics>('/system-metrics');
  }

  async getSystemHealth(): Promise<{ status: string; details: any }> {
    return this.request<{ status: string; details: any }>('/system-health');
  }

  // Alerts
  async getAlerts(): Promise<SystemAlert[]> {
    return this.request<SystemAlert[]>('/alerts');
  }

  async acknowledgeAlert(alertId: string): Promise<void> {
    return this.request<void>(`/alerts/${alertId}/acknowledge`, {
      method: 'POST',
    });
  }

  // Organizational Analytics
  async getOrganizationalAnalytics(businessUnit: string): Promise<any> {
    return this.request<any>(`/organizational-analytics?business_unit=${businessUnit}`);
  }

  // Public API
  async getPublicAPIStatus(): Promise<{ status: string; endpoints: string[] }> {
    return this.request<{ status: string; endpoints: string[] }>('/public-api/status');
  }

  // Mock data for development
  getMockSkillGapData(): SkillGapAnalysis[] {
    return [
      {
        id: '1',
        user_id: 'user123',
        business_unit: 'huntRED Executive',
        skills_analyzed: 15,
        gaps_identified: 8,
        recommendations_count: 12,
        created_at: '2024-01-15T14:30:00Z',
        status: 'completed',
        results: {
          skills: [
            { name: 'Python', current_level: 3, required_level: 5, gap: 2, priority: 'high' },
            { name: 'React', current_level: 4, required_level: 4, gap: 0, priority: 'low' },
            { name: 'Data Science', current_level: 2, required_level: 5, gap: 3, priority: 'critical' },
          ],
          recommendations: [
            {
              type: 'course',
              title: 'Advanced Python for Data Science',
              description: 'Curso avanzado de Python para análisis de datos',
              estimated_duration: '6 weeks',
              difficulty: 'intermediate',
            },
          ],
        },
      },
    ];
  }

  getMockMetrics(): AuraMetrics {
    return {
      total_analyses: 156,
      active_users: 89,
      recommendations_generated: 1247,
      networking_connections: 234,
      average_satisfaction: 4.6,
      system_health: 98,
      uptime_percentage: 99.8,
    };
  }

  getMockAlerts(): SystemAlert[] {
    return [
      {
        id: '1',
        type: 'warning',
        title: 'Alto uso de CPU en Servidor IA',
        message: 'El servidor de IA está utilizando 78% de CPU. Considerar optimización.',
        priority: 'medium',
        timestamp: '2024-01-15T14:25:00Z',
        acknowledged: false,
      },
      {
        id: '2',
        type: 'info',
        title: 'Actualización de seguridad disponible',
        message: 'Nueva versión de seguridad disponible para el sistema.',
        priority: 'low',
        timestamp: '2024-01-15T14:20:00Z',
        acknowledged: true,
      },
    ];
  }
}

export const auraAPI = new AuraAPI();
export default auraAPI; 