import React from 'react';
import { 
  Brain, 
  Shield, 
  Users, 
  Zap, 
  Globe, 
  Lock, 
  FileText,
  MessageSquare,
  BarChart3,
  Settings,
  Award,
  Target,
  Cpu,
  Database,
  Workflow,
  Bot
} from 'lucide-react';

interface ModuleCardProps {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  description: string;
  features: string[];
  color: string;
  delay: number;
  isPremium?: boolean;
}

const ModuleCard: React.FC<ModuleCardProps> = ({ 
  icon, 
  title, 
  subtitle,
  description, 
  features, 
  color, 
  delay,
  isPremium = false
}) => (
  <div
    className={`relative overflow-hidden rounded-2xl p-8 shadow-xl border border-gray-200 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 bg-gradient-to-br ${color} group`}
  >
    {isPremium && (
      <div className="absolute top-4 right-4 bg-yellow-400 text-yellow-900 px-3 py-1 rounded-full text-xs font-bold">
        PREMIUM
      </div>
    )}
    
    <div className="absolute top-0 right-0 w-32 h-32 opacity-10">
      <div className="w-full h-full bg-white rounded-full transform translate-x-16 -translate-y-16"></div>
    </div>
    
    <div className="relative z-10">
      <div className="flex items-center mb-6">
        <div className="p-3 rounded-xl bg-white/20 backdrop-blur-sm mr-4 group-hover:scale-110 transition-transform">
          {icon}
        </div>
        <div>
          <h3 className="text-2xl font-bold text-white">{title}</h3>
          <p className="text-white/80 text-sm">{subtitle}</p>
        </div>
      </div>
      
      <p className="text-white/90 mb-6 text-lg leading-relaxed">
        {description}
      </p>
      
      <div className="space-y-3">
        {features.map((feature, index) => (
          <div key={index} className="flex items-center text-white/80">
            <div className="w-2 h-2 bg-white/60 rounded-full mr-3 flex-shrink-0"></div>
            <span className="text-sm">{feature}</span>
          </div>
        ))}
      </div>
    </div>
  </div>
);

const HuntREDModulesSection: React.FC = () => {
  const modules = [
    {
      icon: <Brain className="w-8 h-8 text-blue-600" />,
      title: "GenIA™",
      subtitle: "Motor de IA Conversacional",
      description: "Sistema de inteligencia artificial conversacional que automatiza el proceso de reclutamiento con comprensión contextual avanzada.",
      features: [
        "Chatbot multicanal con NLP avanzado",
        "Workflows dinámicos y personalizables",
        "Integración con assessments automáticos",
        "Análisis de sentimiento en tiempo real",
        "Soporte multi-idioma (15 idiomas)"
      ],
      color: "from-blue-600 to-blue-800",
      isPremium: true
    },
    {
      icon: <Cpu className="w-8 h-8 text-purple-600" />,
      title: "AURA™",
      subtitle: "IA Contextual Avanzada",
      description: "Inteligencia artificial que comprende el contexto histórico y las relaciones profesionales, proporcionando insights únicos.",
      features: [
        "Análisis de trayectoria profesional completa",
        "Detección de patrones de éxito",
        "Predicción de fit cultural",
        "Contexto histórico de la industria",
        "Análisis de relaciones profesionales"
      ],
      color: "from-purple-600 to-purple-800",
      isPremium: true
    },
    {
      icon: <Shield className="w-8 h-8 text-green-600" />,
      title: "TruthSense™",
      subtitle: "Verificación Automática",
      description: "Sistema de verificación de credenciales y autenticidad que garantiza la integridad de cada candidato.",
      features: [
        "Verificación automática de credenciales",
        "Detección de inconsistencias en CVs",
        "Validación de referencias laborales",
        "Análisis de huella digital",
        "Sistema anti-fraude 98% precisión"
      ],
      color: "from-green-600 to-green-800"
    },
    {
      icon: <Users className="w-8 h-8 text-orange-600" />,
      title: "SocialLink™",
      subtitle: "Análisis de Redes Sociales",
      description: "Análisis profundo de redes sociales y conexiones profesionales que va más allá del CV tradicional.",
      features: [
        "Análisis de LinkedIn, Twitter y redes",
        "Detección de influencia y autoridad",
        "Mapeo de conexiones estratégicas",
        "Evaluación de engagement digital",
        "Análisis de patrones de comportamiento"
      ],
      color: "from-orange-600 to-orange-800"
    },
    {
      icon: <Lock className="w-8 h-8 text-red-600" />,
      title: "OffLimits™",
      subtitle: "Protección de Exclusividad",
      description: "Sistema de protección de exclusividad que garantiza la confidencialidad y respeta las restricciones.",
      features: [
        "Protección automática de exclusividad",
        "Detección de conflictos de interés",
        "Auditoría completa de restricciones",
        "Cumplimiento de acuerdos",
        "Sistema de alertas automáticas"
      ],
      color: "from-red-600 to-red-800"
    },
    {
      icon: <FileText className="w-8 h-8 text-teal-600" />,
      title: "CV Generator AI",
      subtitle: "Generación Inteligente",
      description: "Generador de CVs asistido por IA que crea documentos profesionales optimizados para cada posición.",
      features: [
        "Generación automática de CVs",
        "Optimización para ATS",
        "Plantillas personalizables",
        "Análisis de keywords",
        "Integración con LinkedIn"
      ],
      color: "from-teal-600 to-teal-800"
    },
    {
      icon: <MessageSquare className="w-8 h-8 text-indigo-600" />,
      title: "Chatbot Conversacional",
      subtitle: "Atención 24/7",
      description: "Sistema de chatbot conversacional que automatiza la atención al candidato y mejora la experiencia.",
      features: [
        "Atención automática 24/7",
        "Respuestas contextuales",
        "Integración con calendario",
        "Seguimiento de candidatos",
        "Métricas de engagement"
      ],
      color: "from-indigo-600 to-indigo-800"
    },
    {
      icon: <BarChart3 className="w-8 h-8 text-pink-600" />,
      title: "Analytics Predictivo",
      subtitle: "Insights Avanzados",
      description: "Sistema de analytics predictivo que proporciona insights sobre tendencias y comportamientos del mercado.",
      features: [
        "Análisis predictivo de tendencias",
        "Benchmarks de mercado",
        "Métricas de performance",
        "Reportes personalizados",
        "Dashboards interactivos"
      ],
      color: "from-pink-600 to-pink-800"
    },
    {
      icon: <Settings className="w-8 h-8 text-gray-600" />,
      title: "ATS Integrado",
      subtitle: "Gestión Completa",
      description: "Sistema ATS nativo con integración completa de todos los módulos y funcionalidades avanzadas.",
      features: [
        "Gestión completa de vacantes",
        "Pipeline de candidatos",
        "Integración con job boards",
        "Workflows personalizables",
        "Reportes avanzados"
      ],
      color: "from-gray-600 to-gray-800"
    },
    {
      icon: <Workflow className="w-8 h-8 text-cyan-600" />,
      title: "Firma Electrónica",
      subtitle: "Procesos Digitales",
      description: "Sistema de firma electrónica integrado que agiliza los procesos de contratación y documentación.",
      features: [
        "Firma electrónica legal",
        "Templates de contratos",
        "Flujos de aprobación",
        "Auditoría completa",
        "Integración con ATS"
      ],
      color: "from-cyan-600 to-cyan-800"
    },
    {
      icon: <Globe className="w-8 h-8 text-emerald-600" />,
      title: "Multi-Jurisdicción",
      subtitle: "Soporte Global",
      description: "Soporte completo para diferentes jurisdicciones legales y regulaciones laborales globales.",
      features: [
        "Cumplimiento legal por país",
        "Adaptación a regulaciones",
        "Soporte multi-idioma",
        "Conocimiento de mercados",
        "Integración local"
      ],
      color: "from-emerald-600 to-emerald-800"
    },
    {
      icon: <Award className="w-8 h-8 text-yellow-600" />,
      title: "Gamificación",
      subtitle: "Engagement Avanzado",
      description: "Sistema de gamificación que motiva a candidatos y mejora la experiencia del proceso de reclutamiento.",
      features: [
        "Sistema de puntos y badges",
        "Challenges personalizados",
        "Leaderboards",
        "Recompensas automáticas",
        "Métricas de engagement"
      ],
      color: "from-yellow-600 to-yellow-800"
    }
  ];

  return (
    <section className="py-20 bg-gradient-to-br from-gray-50 to-white">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Módulos huntRED®
            <span className="text-red-600"> Únicos</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Nuestra plataforma integra módulos especializados que trabajan en sinergia para 
            revolucionar el reclutamiento con inteligencia artificial y automatización avanzada.
          </p>
        </div>

        {/* Módulos Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          {modules.map((module, index) => (
            <ModuleCard
              key={index}
              {...module}
              delay={index * 0.1}
            />
          ))}
        </div>

        {/* Call to Action */}
        <div className="text-center">
          <div className="bg-gradient-to-r from-red-600 to-red-700 rounded-2xl p-8 md:p-12 text-white">
            <h3 className="text-3xl font-bold mb-4">
              ¿Listo para experimentar todos nuestros módulos?
            </h3>
            <p className="text-xl mb-8 text-red-100">
              Descubra cómo nuestros módulos trabajan juntos para transformar su proceso de reclutamiento
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-white text-red-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
                Solicitar Demo Completa
              </button>
              <button className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-red-600 transition-colors">
                Ver Documentación Técnica
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HuntREDModulesSection; 