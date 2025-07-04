import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Check, 
  X, 
  Star, 
  Zap, 
  Shield, 
  Globe, 
  DollarSign,
  Users,
  Clock,
  Target,
  Award,
  TrendingUp
} from 'lucide-react';

interface Competitor {
  name: string;
  logo: string;
  pricing: {
    monthly: string;
    annual: string;
    currency: string;
  };
  features: {
    [key: string]: boolean | string;
  };
  pros: string[];
  cons: string[];
  rating: number;
  color: string;
}

const CompetitiveComparisonSection: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState('pricing');

  const competitors: Competitor[] = [
    {
      name: 'huntRED®',
      logo: 'H',
      pricing: {
        monthly: '95,000',
        annual: '1,140,000',
        currency: 'MXN'
      },
      features: {
        'IA Personalizada': true,
        'Soporte en Español': true,
        'Integración HR': true,
        'OffLimits™': true,
        'AURA AI™': true,
        'SocialLink™': true,
        'Mercado Latino': true,
        'Precio Dinámico': true,
        'Configuración Rápida': true,
        'Soporte 24/7': true,
        'API Nativa': true,
        'Web Scraping': true
      },
      pros: [
        'Precio más competitivo del mercado',
        'IA personalizada para Latinoamérica',
        'Módulos exclusivos (AURA AI, OffLimits)',
        'Soporte completo en español',
        'Integración nativa con sistemas HR'
      ],
      cons: [],
      rating: 5,
      color: 'from-red-500 to-red-700'
    },
    {
      name: 'SmartRecruiters',
      logo: 'S',
      pricing: {
        monthly: '2,388',
        annual: '28,656',
        currency: 'USD'
      },
      features: {
        'IA Personalizada': false,
        'Soporte en Español': false,
        'Integración HR': true,
        'OffLimits™': false,
        'AURA AI™': false,
        'SocialLink™': false,
        'Mercado Latino': false,
        'Precio Dinámico': false,
        'Configuración Rápida': false,
        'Soporte 24/7': false,
        'API Nativa': true,
        'Web Scraping': false
      },
      pros: [
        'Plataforma establecida',
        'API bien documentada'
      ],
      cons: [
        'Sin personalización para Latinoamérica',
        'Precio fijo alto',
        'Soporte limitado en español',
        'Sin módulos avanzados de IA'
      ],
      rating: 3,
      color: 'from-blue-500 to-blue-700'
    },
    {
      name: 'Bullhorn',
      logo: 'B',
      pricing: {
        monthly: '7,388',
        annual: '88,656',
        currency: 'USD'
      },
      features: {
        'IA Personalizada': false,
        'Soporte en Español': false,
        'Integración HR': true,
        'OffLimits™': false,
        'AURA AI™': false,
        'SocialLink™': false,
        'Mercado Latino': false,
        'Precio Dinámico': false,
        'Configuración Rápida': false,
        'Soporte 24/7': false,
        'API Nativa': true,
        'Web Scraping': false
      },
      pros: [
        'Funcionalidades avanzadas',
        'Integración con múltiples sistemas'
      ],
      cons: [
        'Precio extremadamente alto',
        'Configuración compleja',
        'Curva de aprendizaje pronunciada',
        'Sin enfoque en mercado latino'
      ],
      rating: 2,
      color: 'from-purple-500 to-purple-700'
    },
    {
      name: 'Mya',
      logo: 'M',
      pricing: {
        monthly: '8,333',
        annual: '100,000',
        currency: 'USD'
      },
      features: {
        'IA Personalizada': false,
        'Soporte en Español': false,
        'Integración HR': false,
        'OffLimits™': false,
        'AURA AI™': false,
        'SocialLink™': false,
        'Mercado Latino': false,
        'Precio Dinámico': false,
        'Configuración Rápida': false,
        'Soporte 24/7': false,
        'API Nativa': false,
        'Web Scraping': false
      },
      pros: [
        'IA conversacional básica'
      ],
      cons: [
        'Precio anual muy alto',
        'Solo en inglés',
        'Sin personalización',
        'Sin integración HR',
        'Soporte remoto únicamente'
      ],
      rating: 1,
      color: 'from-gray-500 to-gray-700'
    }
  ];

  const featureCategories = [
    {
      title: 'Inteligencia Artificial',
      features: ['IA Personalizada', 'AURA AI™']
    },
    {
      title: 'Integración & Soporte',
      features: ['Integración HR', 'API Nativa', 'Web Scraping', 'Soporte en Español', 'Soporte 24/7']
    },
    {
      title: 'Funcionalidades Únicas',
      features: ['OffLimits™', 'SocialLink™', 'Mercado Latino', 'Precio Dinámico', 'Configuración Rápida']
    }
  ];

  const renderFeatureIcon = (value: boolean | string) => {
    if (value === true) {
      return <Check className="w-5 h-5 text-green-500" />;
    } else if (value === false) {
      return <X className="w-5 h-5 text-red-500" />;
    } else {
      return <span className="text-sm text-gray-500">{value}</span>;
    }
  };

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star 
        key={i} 
        className={`w-4 h-4 ${i < rating ? 'text-yellow-400 fill-current' : 'text-gray-300'}`} 
      />
    ));
  };

  return (
    <section className="py-24 bg-gradient-to-br from-gray-50 to-white">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <Badge variant="secondary" className="mb-4 bg-red-100 text-red-700 hover:bg-red-200">
            <Award className="w-4 h-4 mr-2" />
            Comparativa Competitiva
          </Badge>
          <h2 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            ¿Por qué elegir
            <span className="bg-gradient-to-r from-red-600 to-red-800 bg-clip-text text-transparent">
              {' '}huntRED®?
            </span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Vea cómo huntRED® se compara con las principales soluciones del mercado 
            y por qué somos la mejor opción para empresas latinoamericanas.
          </p>
        </div>

        {/* Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8">
            <TabsTrigger value="pricing" className="text-lg">Precios</TabsTrigger>
            <TabsTrigger value="features" className="text-lg">Características</TabsTrigger>
            <TabsTrigger value="analysis" className="text-lg">Análisis</TabsTrigger>
          </TabsList>

          {/* Pricing Tab */}
          <TabsContent value="pricing" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {competitors.map((competitor, index) => (
                <Card 
                  key={index}
                  className={`relative group hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2 ${
                    competitor.name === 'huntRED®' 
                      ? 'border-2 border-red-500 shadow-lg' 
                      : 'border border-gray-200'
                  }`}
                >
                  {competitor.name === 'huntRED®' && (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <Badge className="bg-red-600 text-white px-4 py-1">
                        <Star className="w-4 h-4 mr-1" />
                        MEJOR VALOR
                      </Badge>
                    </div>
                  )}
                  
                  <CardHeader className="text-center pb-4">
                    <div className={`w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br ${competitor.color} flex items-center justify-center text-white text-2xl font-bold`}>
                      {competitor.logo}
                    </div>
                    <CardTitle className="text-2xl font-bold">{competitor.name}</CardTitle>
                    <div className="flex justify-center mb-2">
                      {renderStars(competitor.rating)}
                    </div>
                  </CardHeader>
                  
                  <CardContent className="text-center">
                    <div className="mb-6">
                      <div className="text-3xl font-bold text-gray-900">
                        ${competitor.pricing.monthly}
                      </div>
                      <div className="text-sm text-gray-600">
                        {competitor.pricing.currency} / mes
                      </div>
                      <div className="text-lg font-semibold text-gray-700 mt-2">
                        ${competitor.pricing.annual} {competitor.pricing.currency} / año
                      </div>
                    </div>

                    <div className="space-y-3 mb-6">
                      {competitor.pros.map((pro, i) => (
                        <div key={i} className="flex items-start space-x-2 text-sm">
                          <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-gray-700">{pro}</span>
                        </div>
                      ))}
                      {competitor.cons.map((con, i) => (
                        <div key={i} className="flex items-start space-x-2 text-sm">
                          <X className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                          <span className="text-gray-600">{con}</span>
                        </div>
                      ))}
                    </div>

                    <Button 
                      className={`w-full ${
                        competitor.name === 'huntRED®' 
                          ? 'bg-red-600 hover:bg-red-700' 
                          : 'bg-gray-600 hover:bg-gray-700'
                      }`}
                    >
                      {competitor.name === 'huntRED®' ? 'Solicitar Demo' : 'Ver Detalles'}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Features Tab */}
          <TabsContent value="features" className="space-y-8">
            {featureCategories.map((category, categoryIndex) => (
              <div key={categoryIndex} className="space-y-4">
                <h3 className="text-2xl font-bold text-gray-900 mb-6">{category.title}</h3>
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="border-b-2 border-gray-200">
                        <th className="text-left py-4 px-4 font-semibold text-gray-900">Característica</th>
                        {competitors.map((competitor, index) => (
                          <th key={index} className="text-center py-4 px-4 font-semibold text-gray-900">
                            {competitor.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {category.features.map((feature, featureIndex) => (
                        <tr key={featureIndex} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-4 px-4 font-medium text-gray-700">{feature}</td>
                          {competitors.map((competitor, compIndex) => (
                            <td key={compIndex} className="text-center py-4 px-4">
                              {renderFeatureIcon(competitor.features[feature])}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </TabsContent>

          {/* Analysis Tab */}
          <TabsContent value="analysis" className="space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* ROI Comparison */}
              <Card className="border-2 border-red-200">
                <CardHeader>
                  <CardTitle className="flex items-center text-red-600">
                    <DollarSign className="w-6 h-6 mr-2" />
                    Análisis de ROI
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    {competitors.map((competitor, index) => (
                      <div key={index} className="flex justify-between items-center p-3 rounded-lg bg-gray-50">
                        <span className="font-medium">{competitor.name}</span>
                        <div className="text-right">
                          <div className="font-bold text-gray-900">
                            ${competitor.pricing.annual} {competitor.pricing.currency}
                          </div>
                          <div className="text-sm text-gray-600">por año</div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <div className="text-lg font-bold text-green-700 mb-2">
                      <TrendingUp className="w-5 h-5 inline mr-2" />
                      Ahorro con huntRED®
                    </div>
                    <div className="text-2xl font-bold text-green-600">
                      $1,750,000 MXN
                    </div>
                    <div className="text-sm text-green-600">
                      vs Mya (competidor más caro)
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Market Position */}
              <Card className="border-2 border-blue-200">
                <CardHeader>
                  <CardTitle className="flex items-center text-blue-600">
                    <Target className="w-6 h-6 mr-2" />
                    Posicionamiento de Mercado
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Precio</span>
                      <div className="flex space-x-1">
                        {competitors.map((_, index) => (
                          <div 
                            key={index}
                            className={`w-4 h-4 rounded ${
                              index === 0 ? 'bg-green-500' : 'bg-gray-300'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Funcionalidades</span>
                      <div className="flex space-x-1">
                        {competitors.map((_, index) => (
                          <div 
                            key={index}
                            className={`w-4 h-4 rounded ${
                              index === 0 ? 'bg-green-500' : 'bg-gray-300'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Soporte Local</span>
                      <div className="flex space-x-1">
                        {competitors.map((_, index) => (
                          <div 
                            key={index}
                            className={`w-4 h-4 rounded ${
                              index === 0 ? 'bg-green-500' : 'bg-gray-300'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Personalización</span>
                      <div className="flex space-x-1">
                        {competitors.map((_, index) => (
                          <div 
                            key={index}
                            className={`w-4 h-4 rounded ${
                              index === 0 ? 'bg-green-500' : 'bg-gray-300'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        {/* Bottom CTA */}
        <div className="text-center mt-16">
          <div className="bg-gradient-to-r from-red-600 to-red-700 rounded-2xl p-8 text-white max-w-4xl mx-auto">
            <h3 className="text-2xl md:text-3xl font-bold mb-4">
              ¿Convencido de que huntRED® es la mejor opción?
            </h3>
            <p className="text-red-100 mb-6 text-lg">
              Únase a las empresas que ya eligieron la solución más inteligente y económica
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button className="bg-white text-red-600 hover:bg-gray-100 px-8 py-3 text-lg font-semibold">
                <Zap className="w-5 h-5 mr-2" />
                Solicitar Demo Gratuita
              </Button>
              <Button variant="outline" className="border-white text-white hover:bg-white hover:text-red-600 px-8 py-3 text-lg font-semibold">
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

export default CompetitiveComparisonSection; 