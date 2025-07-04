import React, { useState } from 'react';
import { 
  Database, 
  Zap, 
  Shield, 
  CheckCircle,
  ArrowRight,
  Settings,
  Users,
  Clock,
  Globe,
  Lock,
  RefreshCw,
  AlertTriangle,
  Play,
  Pause,
  Activity,
  BarChart3,
  TrendingUp,
  Cpu,
  Wifi,
  Server
} from 'lucide-react';

interface IntegrationCardProps {
  platform: string;
  status: 'connected' | 'connecting' | 'disconnected' | 'error';
  features: string[];
  icon: React.ReactNode;
  color: string;
  description: string;
  connectionType: string;
  lastSync?: string;
  jobCount?: number;
}

const IntegrationCard: React.FC<IntegrationCardProps> = ({ 
  platform, 
  status, 
  features, 
  icon, 
  color, 
  description,
  connectionType,
  lastSync,
  jobCount
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-100';
      case 'connecting': return 'text-yellow-600 bg-yellow-100';
      case 'disconnected': return 'text-gray-600 bg-gray-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircle className="w-4 h-4" />;
      case 'connecting': return <RefreshCw className="w-4 h-4 animate-spin" />;
      case 'disconnected': return <Pause className="w-4 h-4" />;
      case 'error': return <AlertTriangle className="w-4 h-4" />;
      default: return <Pause className="w-4 h-4" />;
    }
  };

  return (
    <div className={`bg-white rounded-2xl shadow-lg border-2 border-gray-100 hover:shadow-xl transition-all duration-300 p-6 ${color}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-white rounded-lg shadow-sm">
            {icon}
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">{platform}</h3>
            <p className="text-sm text-gray-600">{connectionType}</p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${getStatusColor(status)}`}>
          {getStatusIcon(status)}
          <span className="capitalize">{status}</span>
        </div>
      </div>

      <p className="text-gray-700 mb-4">{description}</p>

      <div className="space-y-3 mb-4">
        {features.map((feature, index) => (
          <div key={index} className="flex items-center text-sm text-gray-600">
            <CheckCircle className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
            <span>{feature}</span>
          </div>
        ))}
      </div>

      <div className="border-t border-gray-200 pt-4">
        <div className="flex justify-between items-center text-sm">
          <div className="text-gray-600">
            {lastSync && (
              <div className="flex items-center">
                <Clock className="w-4 h-4 mr-1" />
                Última sincronización: {lastSync}
              </div>
            )}
          </div>
          {jobCount !== undefined && (
            <div className="text-gray-600">
              <div className="flex items-center">
                <Users className="w-4 h-4 mr-1" />
                {jobCount} posiciones
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 flex space-x-2">
        <button className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          status === 'connected' 
            ? 'bg-red-100 text-red-600 hover:bg-red-200' 
            : 'bg-green-100 text-green-600 hover:bg-green-200'
        }`}>
          {status === 'connected' ? 'Desconectar' : 'Conectar'}
        </button>
        <button className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors">
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

const HRSystemIntegrationSection: React.FC = () => {
  const [activeTab, setActiveTab] = useState('integrations');
  const [isConnecting, setIsConnecting] = useState(false);

  const integrations = [
    {
      platform: "Workday",
      status: 'connected' as const,
      features: [
        "Sincronización automática de vacantes",
        "Extracción de perfiles de candidatos",
        "Actualización en tiempo real",
        "Mapeo de campos personalizado"
      ],
      icon: <Database className="w-6 h-6 text-blue-600" />,
      color: "border-blue-200",
      description: "Integración nativa con Workday HCM para sincronización bidireccional de datos de reclutamiento.",
      connectionType: "API REST + Web Scraping",
      lastSync: "Hace 5 minutos",
      jobCount: 47
    },
    {
      platform: "Phenom People",
      status: 'connecting' as const,
      features: [
        "Conexión con Phenom CRM",
        "Sincronización de candidatos",
        "Análisis de engagement",
        "Automatización de workflows"
      ],
      icon: <Users className="w-6 h-6 text-purple-600" />,
      color: "border-purple-200",
      description: "Integración con Phenom People para gestión avanzada de candidatos y experiencia del candidato.",
      connectionType: "API GraphQL",
      lastSync: "Conectando...",
      jobCount: 23
    },
    {
      platform: "Oracle HCM",
      status: 'connected' as const,
      features: [
        "Conexión con Oracle Cloud HCM",
        "Sincronización de empleados",
        "Gestión de perfiles",
        "Reportes integrados"
      ],
      icon: <Server className="w-6 h-6 text-orange-600" />,
      color: "border-orange-200",
      description: "Integración completa con Oracle Human Capital Management Cloud para gestión integral de talento.",
      connectionType: "Oracle Cloud API",
      lastSync: "Hace 2 minutos",
      jobCount: 89
    },
    {
      platform: "BambooHR",
      status: 'disconnected' as const,
      features: [
        "Sincronización de empleados",
        "Gestión de vacaciones",
        "Onboarding automatizado",
        "Reportes de HR"
      ],
      icon: <Globe className="w-6 h-6 text-green-600" />,
      color: "border-green-200",
      description: "Integración con BambooHR para gestión completa del ciclo de vida del empleado.",
      connectionType: "REST API",
      lastSync: "Desconectado",
      jobCount: 0
    },
    {
      platform: "Greenhouse",
      status: 'connected' as const,
      features: [
        "Sincronización de candidatos",
        "Gestión de pipelines",
        "Evaluaciones integradas",
        "Métricas de reclutamiento"
      ],
      icon: <BarChart3 className="w-6 h-6 text-emerald-600" />,
      color: "border-emerald-200",
      description: "Integración con Greenhouse para optimización del proceso de reclutamiento y selección.",
      connectionType: "REST API",
      lastSync: "Hace 1 minuto",
      jobCount: 156
    },
    {
      platform: "Lever",
      status: 'error' as const,
      features: [
        "Conexión con Lever ATS",
        "Sincronización de candidatos",
        "Gestión de entrevistas",
        "Automatización de emails"
      ],
      icon: <Activity className="w-6 h-6 text-indigo-600" />,
      color: "border-indigo-200",
      description: "Integración con Lever para gestión avanzada del proceso de reclutamiento.",
      connectionType: "REST API",
      lastSync: "Error de conexión",
      jobCount: 0
    }
  ];

  const scrapingCapabilities = [
    {
      platform: "LinkedIn",
      status: 'connected' as const,
      features: [
        "Extracción de perfiles profesionales",
        "Búsqueda avanzada de candidatos",
        "Análisis de redes profesionales",
        "Detección de cambios en perfiles"
      ],
      icon: <Cpu className="w-6 h-6 text-blue-600" />,
      color: "border-blue-200",
      description: "Sistema de scraping robusto para LinkedIn con anti-detección avanzada.",
      connectionType: "Web Scraping Avanzado",
      lastSync: "Hace 3 minutos",
      jobCount: 234
    },
    {
      platform: "Indeed",
      status: 'connected' as const,
      features: [
        "Extracción de ofertas de trabajo",
        "Análisis de mercado salarial",
        "Detección de tendencias",
        "Monitoreo de competencia"
      ],
      icon: <TrendingUp className="w-6 h-6 text-yellow-600" />,
      color: "border-yellow-200",
      description: "Scraping inteligente de Indeed para análisis de mercado y competencia.",
      connectionType: "Web Scraping Inteligente",
      lastSync: "Hace 10 minutos",
      jobCount: 567
    },
    {
      platform: "Glassdoor",
      status: 'connected' as const,
      features: [
        "Extracción de reviews de empresas",
        "Análisis de cultura organizacional",
        "Datos de compensación",
        "Insights de empleados"
      ],
      icon: <Shield className="w-6 h-6 text-green-600" />,
      color: "border-green-200",
      description: "Scraping de Glassdoor para análisis de reputación y cultura empresarial.",
      connectionType: "Web Scraping Robusto",
      lastSync: "Hace 15 minutos",
      jobCount: 89
    }
  ];

  const handleConnectAll = async () => {
    setIsConnecting(true);
    // Simular proceso de conexión
    await new Promise(resolve => setTimeout(resolve, 3000));
    setIsConnecting(false);
  };

  return (
    <section className="py-20 bg-gradient-to-br from-gray-50 to-white">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Integración con
            <span className="text-red-600"> Sistemas HR</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Conecte huntRED con sus sistemas HR existentes. Nuestro sistema de scraping robusto 
            y APIs nativas le permiten sincronizar datos sin interrumpir sus procesos actuales.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex justify-center mb-12">
          <div className="bg-white rounded-xl p-2 shadow-lg">
            <div className="flex space-x-2">
              <button
                onClick={() => setActiveTab('integrations')}
                className={`px-6 py-3 rounded-lg font-medium transition-all ${
                  activeTab === 'integrations'
                    ? 'bg-red-600 text-white shadow-lg'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Database className="w-5 h-5" />
                  <span>APIs Nativas</span>
                </div>
              </button>
              <button
                onClick={() => setActiveTab('scraping')}
                className={`px-6 py-3 rounded-lg font-medium transition-all ${
                  activeTab === 'scraping'
                    ? 'bg-red-600 text-white shadow-lg'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Zap className="w-5 h-5" />
                  <span>Web Scraping</span>
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <div className="bg-white rounded-xl p-6 shadow-lg text-center">
            <div className="text-3xl font-bold text-red-600 mb-2">6</div>
            <div className="text-gray-600">Sistemas Conectados</div>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-lg text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">890</div>
            <div className="text-gray-600">Posiciones Sincronizadas</div>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-lg text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">99.8%</div>
            <div className="text-gray-600">Tiempo Activo</div>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-lg text-center">
            <div className="text-3xl font-bold text-purple-600 mb-2">2.3s</div>
            <div className="text-gray-600">Latencia Promedio</div>
          </div>
        </div>

        {/* Integration Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
          {(activeTab === 'integrations' ? integrations : scrapingCapabilities).map((integration, index) => (
            <IntegrationCard key={index} {...integration} />
          ))}
        </div>

        {/* Connection Actions */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 md:p-12 mb-16">
          <div className="text-center mb-8">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Gestión de Conexiones
            </h3>
            <p className="text-gray-600">
              Configure y gestione todas sus conexiones desde un solo lugar
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-6 bg-gray-50 rounded-xl">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Play className="w-8 h-8 text-red-600" />
              </div>
              <h4 className="text-lg font-bold text-gray-900 mb-2">Conectar Todo</h4>
              <p className="text-gray-600 mb-4">Establezca conexiones con todos sus sistemas HR</p>
              <button 
                onClick={handleConnectAll}
                disabled={isConnecting}
                className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                {isConnecting ? 'Conectando...' : 'Conectar Todo'}
              </button>
            </div>

            <div className="text-center p-6 bg-gray-50 rounded-xl">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <RefreshCw className="w-8 h-8 text-blue-600" />
              </div>
              <h4 className="text-lg font-bold text-gray-900 mb-2">Sincronizar</h4>
              <p className="text-gray-600 mb-4">Sincronice datos con todos los sistemas conectados</p>
              <button className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                Sincronizar Ahora
              </button>
            </div>

            <div className="text-center p-6 bg-gray-50 rounded-xl">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Settings className="w-8 h-8 text-green-600" />
              </div>
              <h4 className="text-lg font-bold text-gray-900 mb-2">Configurar</h4>
              <p className="text-gray-600 mb-4">Configure parámetros de sincronización y mapeo</p>
              <button className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors">
                Configurar
              </button>
            </div>
          </div>
        </div>

        {/* Technical Features */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 md:p-12 mb-16">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Características Técnicas
            </h3>
            <p className="text-gray-600 text-lg">
              Tecnologías avanzadas para integración segura y confiable
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="w-8 h-8 text-red-600" />
              </div>
              <h4 className="text-lg font-bold text-gray-900 mb-2">Anti-Detección</h4>
              <p className="text-gray-600">
                Sistema avanzado de evasión de detección con rotación de IPs y user agents
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Zap className="w-8 h-8 text-blue-600" />
              </div>
              <h4 className="text-lg font-bold text-gray-900 mb-2">Tiempo Real</h4>
              <p className="text-gray-600">
                Sincronización en tiempo real con latencia mínima y alta disponibilidad
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Lock className="w-8 h-8 text-green-600" />
              </div>
              <h4 className="text-lg font-bold text-gray-900 mb-2">Encriptación</h4>
              <p className="text-gray-600">
                Todos los datos se transmiten con encriptación AES-256 y SSL/TLS
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Activity className="w-8 h-8 text-purple-600" />
              </div>
              <h4 className="text-lg font-bold text-gray-900 mb-2">Monitoreo</h4>
              <p className="text-gray-600">
                Monitoreo 24/7 con alertas automáticas y métricas en tiempo real
              </p>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center">
          <div className="bg-gradient-to-r from-red-600 to-red-700 rounded-2xl p-8 md:p-12 text-white">
            <h3 className="text-3xl font-bold mb-4">
              ¿Listo para integrar huntRED con sus sistemas?
            </h3>
            <p className="text-xl mb-8 text-red-100">
              Nuestro equipo de integración le ayudará a conectar todos sus sistemas HR en menos de 24 horas
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-white text-red-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
                Solicitar Integración
              </button>
              <button className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-red-600 transition-colors">
                Ver Documentación
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HRSystemIntegrationSection; 