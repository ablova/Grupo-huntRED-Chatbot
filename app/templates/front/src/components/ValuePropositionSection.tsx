import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Globe, 
  Brain, 
  Shield, 
  Zap, 
  Users, 
  Target,
  Award,
  TrendingUp,
  CheckCircle,
  Star,
  MapPin,
  MessageSquare
} from 'lucide-react';

interface ValueProposition {
  icon: React.ReactNode;
  title: string;
  description: string;
  benefits: string[];
  color: string;
  gradient: string;
}

const ValuePropositionSection: React.FC = () => {
  const valuePropositions: ValueProposition[] = [
    {
      icon: <Globe className="w-8 h-8" />,
      title: "Hecho para Latinoamérica",
      description: "La única plataforma diseñada específicamente para el mercado latinoamericano, con comprensión profunda de las necesidades locales.",
      benefits: [
        "Soporte completo en español",
        "Cumplimiento normativo local",
        "Integración con sistemas HR latinos",
        "Administración de nómina adaptada",
        "Equipo local de soporte"
      ],
      color: "text-tech-blue",
      gradient: "from-tech-blue to-tech-cyan"
    },
    {
      icon: <Brain className="w-8 h-8" />,
      title: "IA Personalizada AURA™",
      description: "Nuestra IA propietaria AURA™ está entrenada con datos latinoamericanos y entiende las particularidades del mercado local.",
      benefits: [
        "95% de precisión en matching",
        "Aprendizaje continuo",
        "Análisis cultural local",
        "Predicción de retención",
        "Evaluación de soft skills"
      ],
      color: "text-tech-purple",
      gradient: "from-tech-purple to-tech-blue"
    },
    {
      icon: <Shield className="w-8 h-8" />,
      title: "OffLimits™ - Protección Total",
      description: "Sistema único de protección que previene conflictos de interés y garantiza la confidencialidad de sus procesos de reclutamiento.",
      benefits: [
        "Protección automática de exclusividad",
        "Cumplimiento legal automático",
        "Auditoría completa de procesos",
        "Prevención de conflictos",
        "Reportes de compliance"
      ],
      color: "text-tech-green",
      gradient: "from-tech-green to-tech-cyan"
    },
    {
      icon: <Zap className="w-8 h-8" />,
      title: "Precio Dinámico Inteligente",
      description: "El único modelo de precios que se adapta a su presupuesto y necesidades, basado en el valor real del servicio.",
      benefits: [
        "Precio basado en salario del puesto",
        "Administración de nómina optimizada",
        "Escalabilidad automática",
        "ROI predecible",
        "Mejor valor del mercado"
      ],
      color: "text-tech-cyan",
      gradient: "from-tech-cyan to-tech-blue"
    }
  ];

  const competitiveAdvantages = [
    {
      title: "vs SmartRecruiters",
      advantage: "Precio 95% menor + IA personalizada",
      icon: <TrendingUp className="w-5 h-5" />
    },
    {
      title: "vs Bullhorn", 
      advantage: "Configuración 10x más rápida",
      icon: <Zap className="w-5 h-5" />
    },
    {
      title: "vs Mya",
      advantage: "Soporte local vs remoto",
      icon: <MapPin className="w-5 h-5" />
    }
  ];

  return (
    <section className="py-24 bg-gradient-to-br from-white via-gray-50 to-blue-50" aria-label="Propuesta de Valor">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <Badge variant="secondary" className="mb-4 bg-blue-100 text-blue-700 hover:bg-blue-200">
            <Star className="w-4 h-4 mr-2" />
            Propuesta de Valor Única
          </Badge>
          <h2 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            ¿Por qué la Plataforma de Talento de Grupo hunt<span className="bg-gradient-to-r from-tech-blue to-tech-purple bg-clip-text text-transparent">
              {' '}RED® es superior?
            </span>
          </h2>
          <p className="text-xl text-gray-700 max-w-3xl mx-auto">
            Módulos exclusivos y tecnología propietaria que posicionan nuestra plataforma como la mejor opción para empresas latinoamericanas.
            diseñada específicamente para transformar el talento en Latinoamérica, con procesos personalizados y tecnología de vanguardia.
          </p>
        </div>

        {/* Value Propositions Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-16">
          {valuePropositions.map((proposition, index) => (
            <Card 
              key={index}
              className="group hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2 border-0 bg-white/90 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-tech-blue focus:ring-offset-2 rounded-xl"
              tabIndex={0}
            >
              <CardHeader className="pb-4">
                <div className="flex items-center space-x-4">
                  <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${proposition.gradient} flex items-center justify-center text-white group-hover:scale-110 transition-transform duration-300`}>
                    {proposition.icon}
                  </div>
                  <div>
                    <CardTitle className={`text-2xl font-bold ${proposition.color}`}>
                      {proposition.title}
                    </CardTitle>
                    <Badge variant="outline" className="mt-2">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Exclusivo huntRED®
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent>
                <p className="text-gray-700 mb-6 leading-relaxed">
                  {proposition.description}
                </p>
                
                <div className="space-y-3">
                  {proposition.benefits.map((benefit, benefitIndex) => (
                    <div key={benefitIndex} className="flex items-center space-x-3">
                      <div className={`w-6 h-6 rounded-full bg-gradient-to-br ${proposition.gradient} flex items-center justify-center`}>
                        <CheckCircle className="w-4 h-4 text-white" />
                      </div>
                      <span className="text-gray-800 font-medium">{benefit}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Competitive Advantages */}
        <div className="mb-16">
          <h3 className="text-3xl font-bold text-center text-gray-900 mb-8">
            Ventajas Competitivas Clave
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {competitiveAdvantages.map((advantage, index) => (
              <Card 
                key={index} 
                className="text-center hover:shadow-lg transition-shadow duration-300 focus:outline-none focus:ring-2 focus:ring-tech-blue focus:ring-offset-2 rounded-lg"
                tabIndex={0}
              >
                <CardContent className="p-6">
                  <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-blue-100 flex items-center justify-center text-tech-blue">
                    {advantage.icon}
                  </div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">
                    {advantage.title}
                  </h4>
                  <p className="text-tech-blue font-medium">
                    {advantage.advantage}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Market Position */}
        <div className="bg-gradient-to-r from-tech-blue to-tech-purple rounded-2xl p-8 text-white mb-16">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
            <div>
              <h3 className="text-2xl font-bold mb-4">
                Módulos Exclusivos del Ecosistema
              </h3>
              <p className="text-lg text-gray-600 mb-8">
                Nuestra plataforma integra módulos especializados que trabajan en sinergia para revolucionar la gestión del talento con inteligencia artificial y automatización avanzada en todas nuestras unidades de negocio.
              </p>
            </div>
            
            <div className="text-center">
              <div className="text-4xl font-bold mb-2">700+</div>
              <div className="text-white font-medium">Empresas Confían</div>
            </div>
            
            <div className="text-center">
              <div className="text-4xl font-bold mb-2">15</div>
              <div className="text-white font-medium">Países Cubiertos</div>
            </div>
          </div>
        </div>

        {/* Testimonials Preview */}
        <div className="mb-16">
          <h3 className="text-3xl font-bold text-center text-gray-900 mb-8">
            Lo que dicen nuestros clientes
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="border-l-4 border-red-500">
              <CardContent className="p-6">
                <div className="flex items-center mb-4">
                  <div className="flex text-yellow-400">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star key={i} className="w-5 h-5 fill-current" />
                    ))}
                  </div>
                </div>
                <p className="text-gray-700 mb-4 italic">
                  "huntRED® transformó completamente nuestro proceso de reclutamiento. 
                  La IA personalizada y el soporte local hicieron toda la diferencia."
                </p>
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-red-600 rounded-full flex items-center justify-center text-white font-bold mr-3">
                    M
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900">María González</div>
                    <div className="text-sm text-gray-600">Directora de RH, TechCorp México</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="border-l-4 border-red-500">
              <CardContent className="p-6">
                <div className="flex items-center mb-4">
                  <div className="flex text-yellow-400">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star key={i} className="w-5 h-5 fill-current" />
                    ))}
                  </div>
                </div>
                <p className="text-gray-700 mb-4 italic">
                  "El precio dinámico y la integración nativa con nuestros sistemas 
                  HR y nómina nos permitieron ahorrar 40% en costos operativos."
                </p>
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-red-600 rounded-full flex items-center justify-center text-white font-bold mr-3">
                    C
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900">Carlos Rodríguez</div>
                    <div className="text-sm text-gray-600">CEO, InnovateLatam</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="text-center">
          <div className="bg-white rounded-2xl p-8 shadow-2xl border border-gray-100 max-w-4xl mx-auto">
            <h3 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
              ¿Listo para experimentar la diferencia de la Plataforma de Talento de Grupo huntRED®?
            </h3>
            <p className="text-gray-600 mb-6 text-lg">
              Descubra por qué más de 350 empresas confían en nuestra plataforma completa de soluciones de talento y administración de nómina
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                className="bg-tech-blue hover:bg-blue-700 px-8 py-3 text-lg font-semibold focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                aria-label="Solicitar una demostración personalizada"
              >
                <MessageSquare className="w-5 h-5 mr-2" />
                Solicitar Demo Personalizada
              </Button>
              <Button 
                variant="outline" 
                className="border-tech-blue text-tech-blue hover:bg-tech-blue hover:text-white px-8 py-3 text-lg font-semibold focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                aria-label="Hablar con un experto en soluciones de talento"
              >
                <Users className="w-5 h-5 mr-2" />
                Hablar con Experto
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ValuePropositionSection; 