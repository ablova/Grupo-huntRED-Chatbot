import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Star, 
  TrendingUp, 
  Users, 
  Clock, 
  DollarSign, 
  Target,
  Award,
  Quote,
  MapPin,
  Building,
  CheckCircle,
  ArrowRight
} from 'lucide-react';

interface SuccessStory {
  id: string;
  company: string;
  industry: string;
  location: string;
  logo: string;
  testimonial: string;
  author: {
    name: string;
    position: string;
    avatar: string;
  };
  metrics: {
    timeReduction: string;
    costSavings: string;
    qualityImprovement: string;
    positionsFilled: string;
  };
  challenges: string[];
  solutions: string[];
  results: string[];
  rating: number;
  featured: boolean;
}

const CustomerSuccessStories: React.FC = () => {
  const [selectedStory, setSelectedStory] = useState<string>('techcorp');

  const successStories: SuccessStory[] = [
    {
      id: 'techcorp',
      company: 'TechCorp México',
      industry: 'Tecnología',
      location: 'México',
      logo: 'TC',
      testimonial: "huntRED® transformó completamente nuestro proceso de reclutamiento. La IA personalizada y el soporte local hicieron toda la diferencia. Reducimos nuestro tiempo de contratación en un 60% y mejoramos la calidad de nuestros candidatos significativamente.",
      author: {
        name: 'María González',
        position: 'Directora de Recursos Humanos',
        avatar: 'MG'
      },
      metrics: {
        timeReduction: '60%',
        costSavings: '45%',
        qualityImprovement: '75%',
        positionsFilled: '150+'
      },
      challenges: [
        'Tiempo de contratación de 45 días',
        'Alto costo por contratación',
        'Baja calidad de candidatos',
        'Proceso manual ineficiente'
      ],
      solutions: [
        'Implementación de AURA AI™',
        'Integración con Workday',
        'Sistema OffLimits™',
        'Precio dinámico personalizado'
      ],
      results: [
        'Tiempo de contratación reducido a 18 días',
        'Ahorro de $2.5M MXN anuales',
        '95% de satisfacción con candidatos',
        'Escalabilidad para 500+ posiciones'
      ],
      rating: 5,
      featured: true
    },
    {
      id: 'innovatelatam',
      company: 'InnovateLatam',
      industry: 'Fintech',
      location: 'Colombia',
      logo: 'IL',
      testimonial: "El precio dinámico y la integración nativa con nuestros sistemas HR nos permitieron ahorrar 40% en costos de reclutamiento. huntRED® entendió nuestras necesidades específicas del mercado latino.",
      author: {
        name: 'Carlos Rodríguez',
        position: 'CEO',
        avatar: 'CR'
      },
      metrics: {
        timeReduction: '50%',
        costSavings: '40%',
        qualityImprovement: '80%',
        positionsFilled: '80+'
      },
      challenges: [
        'Crecimiento rápido de 200 a 500 empleados',
        'Necesidad de talento especializado',
        'Presupuesto limitado',
        'Competencia por talento'
      ],
      solutions: [
        'Precio dinámico basado en salarios',
        'SocialLink™ para talento pasivo',
        'Integración con Oracle HCM',
        'Soporte local en español'
      ],
      results: [
        'Escalabilidad sin límites',
        'Ahorro de $1.8M MXN anuales',
        'Mejor retención de empleados',
        'Expansión a 3 países'
      ],
      rating: 5,
      featured: true
    },
    {
      id: 'retailpro',
      company: 'RetailPro',
      industry: 'Retail',
      location: 'Argentina',
      logo: 'RP',
      testimonial: "Como empresa de retail con 200+ tiendas, necesitábamos una solución que pudiera manejar contrataciones masivas. huntRED® nos dio exactamente lo que necesitábamos con un ROI increíble.",
      author: {
        name: 'Ana Martínez',
        position: 'VP de Talento',
        avatar: 'AM'
      },
      metrics: {
        timeReduction: '70%',
        costSavings: '55%',
        qualityImprovement: '65%',
        positionsFilled: '300+'
      },
      challenges: [
        'Contratación masiva estacional',
        'Múltiples ubicaciones',
        'Necesidad de estandarización',
        'Alto volumen de candidatos'
      ],
      solutions: [
        'Automatización con AURA AI™',
        'Integración multi-ubicación',
        'Sistema de evaluación estandarizado',
        'Precio por volumen'
      ],
      results: [
        'Proceso estandarizado en todas las tiendas',
        'Ahorro de $3.2M MXN anuales',
        'Mejor experiencia del candidato',
        'Reducción de rotación en 30%'
      ],
      rating: 5,
      featured: false
    },
    {
      id: 'healthcaremx',
      company: 'HealthcareMX',
      industry: 'Salud',
      location: 'México',
      logo: 'HM',
      testimonial: "En el sector salud, la calidad del candidato es crítica. huntRED® nos ayudó a encontrar profesionales altamente calificados mientras reducimos nuestros costos de reclutamiento.",
      author: {
        name: 'Dr. Roberto Silva',
        position: 'Director Médico',
        avatar: 'RS'
      },
      metrics: {
        timeReduction: '40%',
        costSavings: '35%',
        qualityImprovement: '90%',
        positionsFilled: '120+'
      },
      challenges: [
        'Necesidad de profesionales especializados',
        'Cumplimiento normativo estricto',
        'Verificación de credenciales',
        'Competencia por talento médico'
      ],
      solutions: [
        'Verificación automática con OffLimits™',
        'Matching especializado por especialidad',
        'Cumplimiento normativo automático',
        'Integración con sistemas médicos'
      ],
      results: [
        'Verificación 100% automatizada',
        'Cumplimiento normativo garantizado',
        'Mejor calidad de profesionales',
        'Reducción de errores de contratación'
      ],
      rating: 5,
      featured: false
    }
  ];

  const currentStory = successStories.find(story => story.id === selectedStory);

  return (
    <section className="py-24 bg-gradient-to-br from-white to-gray-50">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <Badge variant="secondary" className="mb-4 bg-red-100 text-red-700 hover:bg-red-200">
            <Award className="w-4 h-4 mr-2" />
            Casos de Éxito
          </Badge>
          <h2 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Historias de
            <span className="bg-gradient-to-r from-red-600 to-red-800 bg-clip-text text-transparent">
              {' '}éxito real
            </span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Descubra cómo empresas líderes en Latinoamérica transformaron su reclutamiento 
            con huntRED® y obtuvieron resultados extraordinarios.
          </p>
        </div>

        {/* Featured Stories Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
          {successStories.filter(story => story.featured).map((story) => (
            <Card 
              key={story.id}
              className={`group hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2 cursor-pointer ${
                selectedStory === story.id ? 'border-2 border-red-500' : 'border border-gray-200'
              }`}
              onClick={() => setSelectedStory(story.id)}
            >
              <CardHeader>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-red-600 rounded-xl flex items-center justify-center text-white font-bold text-lg">
                      {story.logo}
                    </div>
                    <div>
                      <CardTitle className="text-xl">{story.company}</CardTitle>
                      <div className="flex items-center space-x-2 text-sm text-gray-600">
                        <Building className="w-4 h-4" />
                        <span>{story.industry}</span>
                        <MapPin className="w-4 h-4" />
                        <span>{story.location}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex text-yellow-400">
                    {Array.from({ length: story.rating }).map((_, i) => (
                      <Star key={i} className="w-5 h-5 fill-current" />
                    ))}
                  </div>
                </div>
              </CardHeader>
              
              <CardContent>
                <p className="text-gray-600 mb-4 italic line-clamp-3">
                  "{story.testimonial}"
                </p>
                
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="text-center p-3 bg-red-50 rounded-lg">
                    <div className="text-lg font-bold text-red-600">{story.metrics.timeReduction}</div>
                    <div className="text-xs text-gray-600">Reducción Tiempo</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <div className="text-lg font-bold text-green-600">{story.metrics.costSavings}</div>
                    <div className="text-xs text-gray-600">Ahorro Costos</div>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-bold text-sm">
                      {story.author.avatar}
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">{story.author.name}</div>
                      <div className="text-sm text-gray-600">{story.author.position}</div>
                    </div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-red-600 transition-colors" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Detailed Story View */}
        {currentStory && (
          <div className="mb-16">
            <Tabs defaultValue="overview" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview">Resumen</TabsTrigger>
                <TabsTrigger value="challenges">Desafíos</TabsTrigger>
                <TabsTrigger value="solutions">Soluciones</TabsTrigger>
                <TabsTrigger value="results">Resultados</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="mt-6">
                <Card>
                  <CardContent className="p-6">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                      <div>
                        <h3 className="text-2xl font-bold text-gray-900 mb-4">
                          {currentStory.company}
                        </h3>
                        <p className="text-gray-600 mb-6 leading-relaxed">
                          {currentStory.testimonial}
                        </p>
                        <div className="flex items-center space-x-4">
                          <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-bold">
                            {currentStory.author.avatar}
                          </div>
                          <div>
                            <div className="font-semibold text-gray-900">{currentStory.author.name}</div>
                            <div className="text-sm text-gray-600">{currentStory.author.position}</div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-4 bg-red-50 rounded-lg">
                          <Clock className="w-8 h-8 mx-auto mb-2 text-red-600" />
                          <div className="text-2xl font-bold text-red-600">{currentStory.metrics.timeReduction}</div>
                          <div className="text-sm text-gray-600">Reducción Tiempo</div>
                        </div>
                        <div className="text-center p-4 bg-green-50 rounded-lg">
                          <DollarSign className="w-8 h-8 mx-auto mb-2 text-green-600" />
                          <div className="text-2xl font-bold text-green-600">{currentStory.metrics.costSavings}</div>
                          <div className="text-sm text-gray-600">Ahorro Costos</div>
                        </div>
                        <div className="text-center p-4 bg-blue-50 rounded-lg">
                          <Target className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                          <div className="text-2xl font-bold text-blue-600">{currentStory.metrics.qualityImprovement}</div>
                          <div className="text-sm text-gray-600">Mejora Calidad</div>
                        </div>
                        <div className="text-center p-4 bg-purple-50 rounded-lg">
                          <Users className="w-8 h-8 mx-auto mb-2 text-purple-600" />
                          <div className="text-2xl font-bold text-purple-600">{currentStory.metrics.positionsFilled}</div>
                          <div className="text-sm text-gray-600">Posiciones</div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="challenges" className="mt-6">
                <Card>
                  <CardContent className="p-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Desafíos Iniciales</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {currentStory.challenges.map((challenge, index) => (
                        <div key={index} className="flex items-start space-x-3 p-3 bg-red-50 rounded-lg">
                          <div className="w-6 h-6 bg-red-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                            <span className="text-white text-sm font-bold">{index + 1}</span>
                          </div>
                          <span className="text-gray-700">{challenge}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="solutions" className="mt-6">
                <Card>
                  <CardContent className="p-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Soluciones huntRED®</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {currentStory.solutions.map((solution, index) => (
                        <div key={index} className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
                          <div className="w-6 h-6 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                            <CheckCircle className="w-4 h-4 text-white" />
                          </div>
                          <span className="text-gray-700">{solution}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="results" className="mt-6">
                <Card>
                  <CardContent className="p-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Resultados Obtenidos</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {currentStory.results.map((result, index) => (
                        <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                          <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                            <TrendingUp className="w-4 h-4 text-white" />
                          </div>
                          <span className="text-gray-700">{result}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        )}

        {/* All Stories List */}
        <div className="mb-16">
          <h3 className="text-2xl font-bold text-center text-gray-900 mb-8">
            Más Casos de Éxito
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {successStories.map((story) => (
              <Card 
                key={story.id}
                className={`text-center hover:shadow-lg transition-shadow duration-300 cursor-pointer ${
                  selectedStory === story.id ? 'border-2 border-red-500' : 'border border-gray-200'
                }`}
                onClick={() => setSelectedStory(story.id)}
              >
                <CardContent className="p-4">
                  <div className="w-10 h-10 mx-auto mb-3 bg-red-600 rounded-lg flex items-center justify-center text-white font-bold">
                    {story.logo}
                  </div>
                  <h4 className="font-semibold text-gray-900 mb-1">{story.company}</h4>
                  <p className="text-sm text-gray-600 mb-2">{story.industry}</p>
                  <div className="flex justify-center text-yellow-400 mb-2">
                    {Array.from({ length: story.rating }).map((_, i) => (
                      <Star key={i} className="w-4 h-4 fill-current" />
                    ))}
                  </div>
                  <div className="text-sm font-semibold text-red-600">
                    {story.metrics.costSavings} ahorro
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="text-center">
          <div className="bg-gradient-to-r from-red-600 to-red-700 rounded-2xl p-8 text-white max-w-4xl mx-auto">
            <h3 className="text-2xl md:text-3xl font-bold mb-4">
              ¿Quiere ser el próximo caso de éxito?
            </h3>
            <p className="text-red-100 mb-6 text-lg">
              Únase a las empresas que ya transformaron su reclutamiento con huntRED®
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button className="bg-white text-red-600 hover:bg-gray-100 px-8 py-3 text-lg font-semibold">
                <Quote className="w-5 h-5 mr-2" />
                Solicitar Demo Personalizada
              </Button>
              <Button variant="outline" className="border-white text-white hover:bg-white hover:text-red-600 px-8 py-3 text-lg font-semibold">
                <ArrowRight className="w-5 h-5 mr-2" />
                Ver Más Casos
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CustomerSuccessStories; 