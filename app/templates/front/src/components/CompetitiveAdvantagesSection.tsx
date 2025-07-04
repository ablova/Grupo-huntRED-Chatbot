import React, { useState } from 'react';
import { 
  Shield, 
  Brain, 
  Users, 
  Zap, 
  Globe, 
  Lock, 
  TrendingUp, 
  Award,
  CheckCircle,
  Star,
  Target,
  Cpu,
  Crown,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Calendar
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface AdvantageCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  features: string[];
  color: string;
  delay: number;
  isExpanded?: boolean;
  onToggle?: () => void;
}

const AdvantageCard: React.FC<AdvantageCardProps> = ({ 
  icon, 
  title, 
  description, 
  features, 
  color, 
  delay,
  isExpanded = false,
  onToggle
}) => (
  <div
    className={`relative overflow-hidden rounded-2xl shadow-xl border border-gray-200 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 bg-gradient-to-br ${color} cursor-pointer`}
    onClick={onToggle}
  >
    <div className="absolute top-0 right-0 w-32 h-32 opacity-10">
      <div className="w-full h-full bg-white rounded-full transform translate-x-16 -translate-y-16"></div>
    </div>
    
    <div className="relative z-10 p-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <div className="p-3 rounded-xl bg-white/20 backdrop-blur-sm mr-4">
            {icon}
          </div>
          <div>
            <h3 className="text-2xl font-bold text-white">{title}</h3>
            <Badge variant="secondary" className="bg-white/20 text-white border-0 mt-1">
              EXCLUSIVO huntRED®
            </Badge>
          </div>
        </div>
        {onToggle && (
          <div className="text-white">
            {isExpanded ? <ChevronUp className="w-6 h-6" /> : <ChevronDown className="w-6 h-6" />}
          </div>
        )}
      </div>
      
      <p className="text-white/90 mb-6 text-lg leading-relaxed">
        {description}
      </p>
      
      <div 
        className={`overflow-hidden transition-all duration-300 ${
          isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="space-y-3 pt-4 border-t border-white/20">
          {features.map((feature, index) => (
            <div key={index} className="flex items-center text-white/80">
              <CheckCircle className="w-5 h-5 mr-3 text-green-300 flex-shrink-0" />
              <span className="text-sm">{feature}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

const CompetitiveAdvantagesSection: React.FC = () => {
  const [expandedCard, setExpandedCard] = useState<number | null>(null);

  const advantages = [
    {
      icon: <Brain className="w-8 h-8 text-blue-600" />,
      title: "SocialLink™",
      description: "Módulo de análisis de redes sociales y conexiones profesionales que va más allá del CV tradicional, detectando el verdadero potencial y fit cultural.",
      features: [
        "Análisis de LinkedIn, Twitter y redes profesionales",
        "Detección de influencia y autoridad en el sector",
        "Mapeo de conexiones estratégicas",
        "Evaluación de engagement y reputación digital",
        "Predicción de éxito basada en red profesional"
      ],
      color: "from-blue-600 to-blue-800"
    },
    {
      icon: <Shield className="w-8 h-8 text-green-600" />,
      title: "TruthSense™",
      description: "Módulo de verificación de credenciales y autenticidad que garantiza la integridad de cada candidato, eliminando riesgos de fraude.",
      features: [
        "Verificación automática de credenciales académicas",
        "Detección de inconsistencias en CVs",
        "Validación de referencias laborales",
        "Análisis de huella digital profesional",
        "Reporte de confiabilidad en tiempo real"
      ],
      color: "from-green-600 to-green-800"
    },
    {
      icon: <Users className="w-8 h-8 text-purple-600" />,
      title: "SocialVerify™",
      description: "Módulo de verificación social que valida la presencia y reputación online de candidatos, asegurando transparencia total.",
      features: [
        "Verificación de presencia en redes sociales",
        "Análisis de reputación online",
        "Validación de proyectos y contribuciones",
        "Evaluación de consistencia de marca personal",
        "Score de credibilidad social"
      ],
      color: "from-purple-600 to-purple-800"
    },
    {
      icon: <Zap className="w-8 h-8 text-orange-600" />,
      title: "AURA™ - AI Contextual",
      description: "Inteligencia artificial que comprende el contexto histórico y las relaciones profesionales, proporcionando insights únicos sobre candidatos.",
      features: [
        "Análisis de trayectoria profesional completa",
        "Detección de patrones de éxito",
        "Predicción de fit cultural y organizacional",
        "Contexto histórico de la industria",
        "Aprendizaje continuo con datos latinoamericanos"
      ],
      color: "from-orange-600 to-orange-800"
    },
    {
      icon: <Globe className="w-8 h-8 text-teal-600" />,
      title: "Multi-Jurisdicción",
      description: "Soporte completo para diferentes jurisdicciones legales y regulaciones laborales, adaptándose a las necesidades globales.",
      features: [
        "Cumplimiento legal por jurisdicción",
        "Adaptación a regulaciones locales",
        "Soporte multi-idioma y cultural",
        "Conocimiento de mercados locales",
        "Expertise en 15 países latinoamericanos"
      ],
      color: "from-teal-600 to-teal-800"
    },
    {
      icon: <Lock className="w-8 h-8 text-red-600" />,
      title: "OffLimits™",
      description: "Coherencia ética y monitoreo de protección de exclusividad que garantiza la confidencialidad y respeta las restricciones de contratación.",
      features: [
        "Protección automática de exclusividad",
        "Detección de conflictos de interés",
        "Auditoría completa de restricciones",
        "Cumplimiento de acuerdos de confidencialidad",
        "Sistema de alertas preventivas"
      ],
      color: "from-red-600 to-red-800"
    }
  ];

  const comparisonData = [
    {
      feature: "Análisis de Redes Sociales",
      huntred: "SocialLink™ Avanzado",
      holly: "Básico",
      hiring: "Limitado",
      mya: "No disponible",
      smartrecruiters: "Básico",
      bullhorn: "Limitado",
      huntredScore: 5,
      hollyScore: 2,
      hiringScore: 1,
      myaScore: 0,
      smartrecruitersScore: 2,
      bullhornScore: 1
    },
    {
      feature: "Verificación de Credenciales",
      huntred: "TruthSense™ Automático",
      holly: "Manual",
      hiring: "Básico",
      mya: "Limitado",
      smartrecruiters: "Manual",
      bullhorn: "Básico",
      huntredScore: 5,
      hollyScore: 3,
      hiringScore: 2,
      myaScore: 2,
      smartrecruitersScore: 3,
      bullhornScore: 2
    },
    {
      feature: "IA Contextual",
      huntred: "GenIA™ & AURA™ Completo",
      holly: "ChatGPT",
      hiring: "Básico",
      mya: "Video AI",
      smartrecruiters: "Matching AI",
      bullhorn: "Analytics AI",
      huntredScore: 5,
      hollyScore: 3,
      hiringScore: 2,
      myaScore: 4,
      smartrecruitersScore: 3,
      bullhornScore: 3
    },
    {
      feature: "Protección OffLimits",
      huntred: "Sistema Completo",
      holly: "No disponible",
      hiring: "No disponible",
      mya: "No disponible",
      smartrecruiters: "Básico",
      bullhorn: "Limitado",
      huntredScore: 5,
      hollyScore: 0,
      hiringScore: 0,
      myaScore: 0,
      smartrecruitersScore: 2,
      bullhornScore: 1
    },
    {
      feature: "Mercado Latinoamericano",
      huntred: "Especialización Completa",
      holly: "Limitado",
      hiring: "No disponible",
      mya: "No disponible",
      smartrecruiters: "Básico",
      bullhorn: "Limitado",
      huntredScore: 5,
      hollyScore: 2,
      hiringScore: 0,
      myaScore: 0,
      smartrecruitersScore: 2,
      bullhornScore: 1
    },
    {
      feature: "Precio Dinámico",
      huntred: "Modelo Adaptativo",
      holly: "Precio Fijo Alto",
      hiring: "Precio Fijo",
      mya: "Precio Fijo Muy Alto",
      smartrecruiters: "Precio Fijo",
      bullhorn: "Precio Fijo",
      huntredScore: 5,
      hollyScore: 2,
      hiringScore: 3,
      myaScore: 1,
      smartrecruitersScore: 2,
      bullhornScore: 2
    }
  ];

  const renderStars = (score: number) => {
    return (
      <div className="flex items-center space-x-1">
        {[...Array(5)].map((_, i) => (
          <Star
            key={i}
            className={`w-4 h-4 ${
              i < score ? 'text-yellow-400 fill-current' : 'text-gray-300'
            }`}
          />
        ))}
      </div>
    );
  };

  const getScoreColor = (score: number) => {
    if (score >= 4) return 'text-green-600';
    if (score >= 2) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <section className="py-20 bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="container mx-auto px-4 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <Badge variant="secondary" className="bg-red-100 text-red-700 hover:bg-red-200 border-0 mb-4">
            <Crown className="w-4 h-4 mr-2" />
            LÍDER EN LATINOAMÉRICA
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            ¿Por qué huntRED® es{' '}
            <span className="bg-gradient-to-r from-red-600 to-red-800 bg-clip-text text-transparent">
              superior?
            </span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Módulos exclusivos y tecnología propietaria que nos posicionan como la mejor opción para empresas latinoamericanas
          </p>
        </div>

        {/* Advantages Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
          {advantages.map((advantage, index) => (
            <AdvantageCard
              key={index}
              {...advantage}
              delay={index * 0.1}
              isExpanded={expandedCard === index}
              onToggle={() => setExpandedCard(expandedCard === index ? null : index)}
            />
          ))}
        </div>

        {/* Comparison Table */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
          <div className="bg-gradient-to-r from-red-600 to-red-800 p-8 text-white">
            <h3 className="text-3xl font-bold mb-2">Comparativa con la Competencia</h3>
            <p className="text-red-100">huntRED® vs principales plataformas del mercado</p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Característica</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-red-600">huntRED®</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-600">Holly AI</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-600">Hiring Agents</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-600">Mya</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-600">SmartRecruiters</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-600">Bullhorn</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {comparisonData.map((row, index) => (
                  <tr key={index} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{row.feature}</td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex flex-col items-center">
                        <span className="text-sm font-semibold text-red-600 mb-1">{row.huntred}</span>
                        {renderStars(row.huntredScore)}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex flex-col items-center">
                        <span className="text-sm text-gray-600 mb-1">{row.holly}</span>
                        {renderStars(row.hollyScore)}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex flex-col items-center">
                        <span className="text-sm text-gray-600 mb-1">{row.hiring}</span>
                        {renderStars(row.hiringScore)}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex flex-col items-center">
                        <span className="text-sm text-gray-600 mb-1">{row.mya}</span>
                        {renderStars(row.myaScore)}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex flex-col items-center">
                        <span className="text-sm text-gray-600 mb-1">{row.smartrecruiters}</span>
                        {renderStars(row.smartrecruitersScore)}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex flex-col items-center">
                        <span className="text-sm text-gray-600 mb-1">{row.bullhorn}</span>
                        {renderStars(row.bullhornScore)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center mt-16">
          <div className="bg-gradient-to-r from-red-600 to-red-800 rounded-2xl p-8 text-white">
            <h3 className="text-3xl font-bold mb-4">¿Listo para experimentar la diferencia?</h3>
            <p className="text-xl text-red-100 mb-8 max-w-2xl mx-auto">
              Únase a las 700+ empresas que ya confían en huntRED® para transformar su proceso de reclutamiento
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" className="bg-white text-red-600 hover:bg-gray-100 border-0">
                <Calendar className="mr-2 h-5 w-5" />
                Agendar Demo Gratis
              </Button>
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-red-600">
                Ver Casos de Éxito
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CompetitiveAdvantagesSection; 