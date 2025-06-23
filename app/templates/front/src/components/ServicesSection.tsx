import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Calendar, Users, Brain, Target, Star, Check } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

const fetchPlans = async () => {
  const res = await fetch('/api/pricing/plans/');
  return res.json();
};

const fetchAddons = async () => {
  const res = await fetch('/api/pricing/addons/');
  return res.json();
};

const ServicesSection = () => {
  const [selectedTab, setSelectedTab] = useState('business-units');

  const { data: plansData, isLoading: loadingPlans } = useQuery('pricingPlans', fetchPlans, {
    staleTime: 1000 * 60 * 60 * 24 * 30, // 30 días
  });
  const { data: addonsData, isLoading: loadingAddons } = useQuery('pricingAddons', fetchAddons, {
    staleTime: 1000 * 60 * 60 * 24 * 30,
  });

  if (loadingPlans || loadingAddons) return <div>Cargando servicios...</div>;

  // Data with dynamic identifiers for ATS system integration
  const businessUnits = [
    {
      id: "huntred-executive", // Dynamic ID for ATS pricing module
      name: "huntRED® Executive",
      price: "$95,000", // This will be dynamically updated from app/ats/pricing
      description: "Búsquedas ejecutivas de alto nivel para posiciones C-Level y directivas estratégicas.",
      features: ["Executive Search", "Leadership Assessment", "Succession Planning", "Board Advisory"],
      popular: false,
      color: "from-purple-600 to-indigo-600",
      dataSource: "ats.pricing.huntred_executive" // Reference for dynamic updates
    },
    {
      id: "huntred-standard", // Dynamic ID for ATS pricing module
      name: "huntRED®",
      price: "$95,000", // This will be dynamically updated from app/ats/pricing
      description: "Reclutamiento especializado para posiciones gerenciales y de alta especialización técnica.",
      features: ["Specialized Search", "Technical Assessment", "Cultural Fit Analysis", "Onboarding Support"],
      popular: true, // Most demanded as requested
      color: "from-blue-600 to-cyan-600",
      dataSource: "ats.pricing.huntred_standard"
    },
    {
      id: "huntu", // Dynamic ID for ATS pricing module
      name: "huntU®",
      price: "$55,000", // This will be dynamically updated from app/ats/pricing
      description: "Talento universitario y profesionales junior con alto potencial de crecimiento.",
      features: ["University Recruiting", "Graduate Programs", "Talent Pipeline", "Career Development"],
      popular: false,
      color: "from-green-600 to-emerald-600",
      dataSource: "ats.pricing.huntu"
    },
    {
      id: "amigro", // Dynamic ID for ATS pricing module
      name: "amigro®",
      price: "$20,000", // This will be dynamically updated from app/ats/pricing
      description: "Soluciones de reclutamiento masivo y posiciones operativas especializadas.",
      features: ["Volume Recruiting", "Operational Roles", "Quick Placement", "Process Optimization"],
      popular: false,
      color: "from-orange-600 to-red-600",
      dataSource: "ats.pricing.amigro"
    }
  ];

  const addons = {
    freemium: [
      {
        id: "basic-analytics",
        name: "Basic Analytics",
        description: "Reportes básicos de proceso y métricas fundamentales",
        price: "Incluido",
        icon: <Target className="h-5 w-5" />,
        dataSource: "ats.pricing.addons.freemium.basic_analytics"
      },
      {
        id: "standard-dashboard",
        name: "Standard Dashboard",
        description: "Dashboard estándar con visualización de pipeline",
        price: "Incluido",
        icon: <Users className="h-5 w-5" />,
        dataSource: "ats.pricing.addons.freemium.standard_dashboard"
      }
    ],
    premium: [
      {
        id: "aura-integration",
        name: "AURA Integration",
        description: "Integración completa con GNN y motores analíticos",
        price: "$15,000",
        icon: <Brain className="h-5 w-5" />,
        dataSource: "ats.pricing.addons.premium.aura_integration"
      },
      {
        id: "predictive-analytics",
        name: "Predictive Analytics",
        description: "IA predictiva para success rate y time-to-hire",
        price: "$12,000",
        icon: <Star className="h-5 w-5" />,
        dataSource: "ats.pricing.addons.premium.predictive_analytics"
      },
      {
        id: "custom-dashboards",
        name: "Custom Dashboards",
        description: "Dashboards personalizados para ejecutivos",
        price: "$8,000",
        icon: <Target className="h-5 w-5" />,
        dataSource: "ats.pricing.addons.premium.custom_dashboards"
      },
      {
        id: "api-access",
        name: "API Access",
        description: "Acceso completo a APIs y integraciones",
        price: "$10,000",
        icon: <Users className="h-5 w-5" />,
        dataSource: "ats.pricing.addons.premium.api_access"
      }
    ]
  };

  const assessments = [
    {
      id: "leadership-assessment",
      name: "Leadership Assessment Suite",
      description: "Evaluación completa de liderazgo y competencias ejecutivas",
      price: "$500/usuario",
      duration: "Licencia anual",
      dataSource: "ats.pricing.assessments.leadership"
    },
    {
      id: "technical-skills",
      name: "Technical Skills Profiler",
      description: "Assessment técnico especializado por industria",
      price: "$300/usuario",
      duration: "Licencia anual",
      dataSource: "ats.pricing.assessments.technical"
    },
    {
      id: "cultural-fit",
      name: "Cultural Fit Analyzer",
      description: "Análisis de compatibilidad cultural y valores",
      price: "$200/usuario",
      duration: "Licencia anual",
      dataSource: "ats.pricing.assessments.cultural"
    },
    {
      id: "cognitive-assessment",
      name: "Cognitive Assessment",
      description: "Evaluación de capacidades cognitivas y resolución de problemas",
      price: "$250/usuario",
      duration: "Licencia anual",
      dataSource: "ats.pricing.assessments.cognitive"
    }
  ];

  const auraPackages = [
    {
      id: "aura-starter",
      name: "AURA Starter",
      price: "$299/mes",
      description: "Para profesionales que inician su carrera",
      features: [
        "Análisis básico de red profesional",
        "Skill Gap Analysis",
        "3 simulaciones de carrera/mes",
        "Market Alerts básicos",
        "CV Generator"
      ],
      popular: false,
      dataSource: "ats.pricing.aura.starter"
    },
    {
      id: "aura-professional",
      name: "AURA Professional",
      price: "$599/mes",
      description: "Para profesionales en crecimiento",
      features: [
        "GNN completa y análisis avanzado",
        "Career Simulator ilimitado",
        "Network Matchmaker",
        "Executive Dashboard",
        "Interview Simulator",
        "Priority Support"
      ],
      popular: true,
      dataSource: "ats.pricing.aura.professional"
    },
    {
      id: "aura-executive",
      name: "AURA Executive",
      price: "$1,299/mes",
      description: "Para líderes y ejecutivos",
      features: [
        "Todo lo de Professional",
        "Organizational Analytics",
        "Personal Brand Monitor",
        "Executive Coaching AI",
        "Custom Integrations",
        "White-glove Support"
      ],
      popular: false,
      dataSource: "ats.pricing.aura.executive"
    }
  ];

  // Enterprise packages - custom solutions
  const enterprisePackages = [
    {
      id: "enterprise-unlimited",
      name: "Enterprise Unlimited",
      price: "$500,000/mes",
      description: "Paquete ilimitado de todas las posiciones y servicios",
      features: ["Búsquedas ilimitadas", "Todos los add-ons premium", "AURA completo", "Soporte dedicado"],
      dataSource: "ats.pricing.enterprise.unlimited"
    },
    {
      id: "enterprise-custom-5",
      name: "Enterprise Package (5 posiciones)",
      price: "$300,000/mes",
      description: "Paquete personalizado para 5 posiciones mensuales",
      features: ["5 búsquedas/mes", "Add-ons seleccionados", "AURA incluido", "Account Manager"],
      dataSource: "ats.pricing.enterprise.custom_5"
    }
  ];

  const tabs = [
    { id: 'business-units', label: 'Unidades de Negocio', icon: <Users className="h-4 w-4" /> },
    { id: 'addons', label: 'Add-ons', icon: <Star className="h-4 w-4" /> },
    { id: 'assessments', label: 'Assessments', icon: <Target className="h-4 w-4" /> },
    { id: 'aura', label: 'AURA para Candidatos', icon: <Brain className="h-4 w-4" /> },
    { id: 'enterprise', label: 'Paquetes Empresariales', icon: <Calendar className="h-4 w-4" /> }
  ];

  return (
    <section id="services" className="py-20 bg-background" data-section="pricing-services">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-16">
          <h2 className="text-3xl md:text-4xl font-bold">
            Nuestros <span className="bg-tech-gradient bg-clip-text text-transparent">Servicios</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Soluciones especializadas por unidad de negocio con tecnología AURA integrada
          </p>
          <Badge variant="outline" className="text-xs bg-yellow-50 border-yellow-200 text-yellow-800">
            💡 Precios dinámicos gestionados desde app/ats/pricing
          </Badge>
        </div>

        {/* Tab Navigation */}
        <div className="flex flex-wrap justify-center gap-2 mb-12">
          {tabs.map((tab) => (
            <Button
              key={tab.id}
              variant={selectedTab === tab.id ? "default" : "outline"}
              onClick={() => setSelectedTab(tab.id)}
              className={`flex items-center gap-2 ${
                selectedTab === tab.id ? 'bg-tech-gradient' : ''
              }`}
            >
              {tab.icon}
              {tab.label}
            </Button>
          ))}
        </div>

        {/* Business Units */}
        {selectedTab === 'business-units' && (
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {businessUnits.map((unit, index) => (
              <Card 
                key={index} 
                className={`relative overflow-hidden transition-all duration-300 hover:-translate-y-2 ${
                  unit.popular ? 'border-primary/50 shadow-xl scale-105' : 'hover:shadow-lg'
                }`}
                data-pricing-id={unit.id}
                data-source={unit.dataSource}
              >
                {unit.popular && (
                  <div className="absolute top-0 left-0 right-0 bg-tech-gradient text-white text-center py-2 text-sm font-medium">
                    Más Demandado
                  </div>
                )}
                
                <CardHeader className={unit.popular ? 'pt-12' : ''}>
                  <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${unit.color} flex items-center justify-center mb-4`}>
                    <Users className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-lg">{unit.name}</CardTitle>
                  <p className="text-sm text-muted-foreground">{unit.description}</p>
                </CardHeader>
                
                <CardContent className="space-y-4">
                  <div className="text-2xl font-bold bg-tech-gradient bg-clip-text text-transparent" data-price-field={unit.id}>
                    {unit.price}
                  </div>
                  
                  <ul className="space-y-2">
                    {unit.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-center space-x-2 text-sm">
                        <Check className="w-4 h-4 text-green-500" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                  
                  <Button className="w-full mt-4">
                    Solicitar Información
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Add-ons */}
        {selectedTab === 'addons' && (
          <div className="space-y-12">
            <div>
              <h3 className="text-2xl font-bold mb-6 text-center">Freemium Add-ons</h3>
              <div className="grid md:grid-cols-2 gap-6">
                {addons.freemium.map((addon, index) => (
                  <Card key={index} className="hover:shadow-lg transition-all duration-300" data-addon-id={addon.id} data-source={addon.dataSource}>
                    <CardContent className="p-6">
                      <div className="flex items-start space-x-4">
                        <div className="p-2 bg-green-100 rounded-lg">
                          {addon.icon}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold mb-2">{addon.name}</h4>
                          <p className="text-sm text-muted-foreground mb-3">{addon.description}</p>
                          <Badge variant="secondary" className="bg-green-100 text-green-800" data-price-field={addon.id}>
                            {addon.price}
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-2xl font-bold mb-6 text-center">Premium Add-ons</h3>
              <div className="grid md:grid-cols-2 gap-6">
                {addons.premium.map((addon, index) => (
                  <Card key={index} className="hover:shadow-lg transition-all duration-300 border-primary/20" data-addon-id={addon.id} data-source={addon.dataSource}>
                    <CardContent className="p-6">
                      <div className="flex items-start space-x-4">
                        <div className="p-2 bg-primary/10 rounded-lg">
                          {addon.icon}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold mb-2">{addon.name}</h4>
                          <p className="text-sm text-muted-foreground mb-3">{addon.description}</p>
                          <div className="text-lg font-bold text-primary" data-price-field={addon.id}>{addon.price}</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Assessments */}
        {selectedTab === 'assessments' && (
          <div className="grid md:grid-cols-2 gap-6">
            {assessments.map((assessment, index) => (
              <Card key={index} className="hover:shadow-lg transition-all duration-300" data-assessment-id={assessment.id} data-source={assessment.dataSource}>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <Target className="h-5 w-5 text-primary" />
                      <h4 className="font-semibold">{assessment.name}</h4>
                    </div>
                    <p className="text-sm text-muted-foreground">{assessment.description}</p>
                    <div className="flex justify-between items-center pt-2 border-t">
                      <div>
                        <div className="text-lg font-bold text-primary" data-price-field={assessment.id}>{assessment.price}</div>
                        <div className="text-xs text-muted-foreground">{assessment.duration}</div>
                      </div>
                      <Button size="sm" variant="outline">
                        Más Info
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* AURA Packages */}
        {selectedTab === 'aura' && (
          <div className="grid md:grid-cols-3 gap-8">
            {auraPackages.map((pkg, index) => (
              <Card key={index} className={`relative overflow-hidden transition-all duration-300 hover:-translate-y-2 ${
                pkg.popular ? 'border-primary/50 shadow-xl scale-105' : 'hover:shadow-lg'
              }`} data-aura-id={pkg.id} data-source={pkg.dataSource}>
                {pkg.popular && (
                  <div className="absolute top-0 left-0 right-0 bg-tech-gradient text-white text-center py-2 text-sm font-medium">
                    Más Popular
                  </div>
                )}
                
                <CardHeader className={pkg.popular ? 'pt-12' : ''}>
                  <div className="text-center space-y-2">
                    <CardTitle className="text-xl">{pkg.name}</CardTitle>
                    <div className="text-3xl font-bold bg-tech-gradient bg-clip-text text-transparent" data-price-field={pkg.id}>
                      {pkg.price}
                    </div>
                    <p className="text-sm text-muted-foreground">{pkg.description}</p>
                  </div>
                </CardHeader>
                
                <CardContent className="space-y-4">
                  <ul className="space-y-3">
                    {pkg.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-start space-x-2 text-sm">
                        <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                  
                  <Button 
                    className={`w-full ${pkg.popular ? 'bg-tech-gradient hover:opacity-90' : ''}`}
                    variant={pkg.popular ? 'default' : 'outline'}
                  >
                    Comenzar Ahora
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Enterprise Packages */}
        {selectedTab === 'enterprise' && (
          <div className="space-y-8">
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold mb-4">Paquetes Empresariales</h3>
              <p className="text-muted-foreground">Soluciones a medida para empresas con necesidades específicas</p>
            </div>
            
            <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              {enterprisePackages.map((pkg, index) => (
                <Card key={index} className="border-2 border-primary/20 hover:border-primary/40 transition-all duration-300" data-enterprise-id={pkg.id} data-source={pkg.dataSource}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xl">{pkg.name}</CardTitle>
                      <Badge className="bg-primary/10 text-primary">Personalizado</Badge>
                    </div>
                    <div className="text-3xl font-bold text-primary" data-price-field={pkg.id}>{pkg.price}</div>
                    <p className="text-muted-foreground">{pkg.description}</p>
                  </CardHeader>
                  
                  <CardContent className="space-y-4">
                    <ul className="space-y-2">
                      {pkg.features.map((feature, featureIndex) => (
                        <li key={featureIndex} className="flex items-center space-x-2 text-sm">
                          <Check className="w-4 h-4 text-green-500" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                    
                    <Button className="w-full bg-primary/10 text-primary hover:bg-primary/20">
                      Solicitar Cotización Personalizada
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
            
            <Card className="glass border-primary/20 max-w-2xl mx-auto">
              <CardContent className="p-6 text-center">
                <h4 className="text-xl font-semibold mb-3">¿Necesitas algo diferente?</h4>
                <p className="text-muted-foreground mb-4">
                  Creamos paquetes empresariales completamente personalizados según tus necesidades específicas
                </p>
                <Button className="bg-tech-gradient hover:opacity-90">
                  Hablar con un Especialista
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        {/* CTA Section */}
        <div className="mt-16 text-center">
          <Card className="glass border-primary/20 max-w-4xl mx-auto">
            <CardContent className="p-8 space-y-6">
              <h3 className="text-3xl font-bold">¿Listo para transformar tu proceso de reclutamiento?</h3>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Descubre cómo nuestras soluciones especializadas pueden potenciar tu estrategia de talento
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="lg" className="bg-tech-gradient hover:opacity-90 transition-opacity">
                  <Calendar className="mr-2 h-5 w-5" />
                  Agendar Demo Personalizada
                </Button>
                <Button size="lg" variant="outline" className="border-primary/30 hover:bg-primary/10">
                  Solicitar Cotización
                </Button>
              </div>
              
              <div className="grid md:grid-cols-3 gap-6 pt-6 border-t">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">45min</div>
                  <div className="text-sm text-muted-foreground">Demo personalizada</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">100%</div>
                  <div className="text-sm text-muted-foreground">Adaptado a tu BU</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">24h</div>
                  <div className="text-sm text-muted-foreground">Propuesta comercial</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default ServicesSection;
