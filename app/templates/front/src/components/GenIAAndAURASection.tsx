import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Brain, 
  Sparkles, 
  Zap, 
  Shield, 
  Cpu, 
  Database, 
  Activity, 
  CheckCircle, 
  ArrowRight,
  Users,
  Target,
  TrendingUp,
  Lock,
  Globe,
  Code,
  BarChart3,
  MessageSquare,
  Lightbulb,
  Network,
  Award
} from 'lucide-react';

const GenIAAndAURASection = () => {
  const [activeTab, setActiveTab] = useState('genia');
  const [currentFeature, setCurrentFeature] = useState(0);

  const geniaFeatures = [
    {
      icon: Brain,
      title: "Inteligencia Artificial Generativa",
      description: "Modelos de lenguaje avanzados para creación de contenido, análisis y automatización",
      capabilities: ["Generación de Texto", "Análisis de Sentimientos", "Traducción Automática", "Resúmenes Inteligentes"]
    },
    {
      icon: MessageSquare,
      title: "Chatbots Conversacionales",
      description: "Asistentes virtuales inteligentes con capacidad de aprendizaje continuo",
      capabilities: ["Atención al Cliente", "Ventas Automatizadas", "Soporte Técnico", "Reservas y Citas"]
    },
    {
      icon: Code,
      title: "Generación de Código",
      description: "Asistencia en programación con sugerencias inteligentes y debugging automático",
      capabilities: ["Code Review", "Refactoring", "Documentación", "Testing Automatizado"]
    },
    {
      icon: Lightbulb,
      title: "Análisis Creativo",
      description: "Generación de ideas innovadoras y soluciones creativas para problemas complejos",
      capabilities: ["Brainstorming", "Diseño de Productos", "Estrategias de Marketing", "Innovación"]
    }
  ];

  const auraFeatures = [
    {
      icon: Target,
      title: "Análisis de Brechas de Habilidades",
      description: "Identificación precisa de competencias faltantes y oportunidades de desarrollo",
      capabilities: ["Assessment Automatizado", "Mapeo de Competencias", "Análisis de Mercado", "Recomendaciones Personalizadas"]
    },
    {
      icon: TrendingUp,
      title: "Desarrollo Profesional",
      description: "Rutas de aprendizaje personalizadas basadas en objetivos de carrera y mercado",
      capabilities: ["Planes de Desarrollo", "Certificaciones", "Mentoría Virtual", "Progreso Tracking"]
    },
    {
      icon: Network,
      title: "Networking Inteligente",
      description: "Conecta profesionales con oportunidades y mentores relevantes",
      capabilities: ["Matching Inteligente", "Eventos Virtuales", "Comunidades", "Colaboración"]
    },
    {
      icon: BarChart3,
      title: "Analítica Avanzada",
      description: "Métricas detalladas sobre desarrollo profesional y mercado laboral",
      capabilities: ["KPIs Personalizados", "Tendencias de Mercado", "Benchmarking", "Reportes Automatizados"]
    }
  ];

  const ecosystemFeatures = [
    {
      icon: Shield,
      title: "Seguridad de Datos",
      description: "Protección avanzada con encriptación end-to-end y cumplimiento GDPR",
      features: ["Encriptación AES-256", "GDPR Compliance", "Audit Trails", "Access Control"]
    },
    {
      icon: Globe,
      title: "Integración Multiplataforma",
      description: "Conectividad con sistemas existentes y APIs de terceros",
      features: ["REST APIs", "Webhooks", "SSO Integration", "Data Sync"]
    },
    {
      icon: Zap,
      title: "Escalabilidad Automática",
      description: "Infraestructura cloud que se adapta automáticamente a la demanda",
      features: ["Auto-scaling", "Load Balancing", "CDN Global", "99.9% Uptime"]
    },
    {
      icon: Award,
      title: "Certificaciones y Compliance",
      description: "Cumplimiento con estándares internacionales de calidad y seguridad",
      features: ["ISO 27001", "SOC 2 Type II", "HIPAA Ready", "PCI DSS"]
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentFeature((prev) => (prev + 1) % 4);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  return (
    <section id="genia-aura" className="py-20 bg-gradient-to-br from-background via-background to-muted/20 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 quantum-grid opacity-5" />
      <div className="absolute top-10 left-10 w-72 h-72 bg-gradient-to-r from-blue-500/10 to-emerald-500/10 rounded-full blur-3xl animate-float" />
      <div className="absolute bottom-10 right-10 w-64 h-64 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-full blur-2xl animate-float" style={{ animationDelay: '3s' }} />
      
      <div className="container mx-auto px-4 lg:px-8 relative z-10">
        {/* Header */}
        <div className="text-center space-y-6 mb-16">
          <div className="inline-flex items-center space-x-2 glass rounded-full px-6 py-3 border border-primary/20">
            <Sparkles className="h-5 w-5 text-primary" />
            <span className="text-sm font-medium">ECOSISTEMA AI AVANZADO</span>
          </div>
          
          <h2 className="text-4xl md:text-5xl font-bold tech-title">
            GenIA & AURA
          </h2>
          <p className="text-xl text-muted-foreground max-w-4xl mx-auto">
            El corazón de nuestro ecosistema de Inteligencia Artificial. GenIA para la generación y creatividad, 
            AURA para el desarrollo profesional y análisis de habilidades.
          </p>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-16">
          <TabsList className="grid w-full grid-cols-3 glass">
            <TabsTrigger value="ecosystem" className="flex items-center space-x-2">
              <Globe className="h-4 w-4" />
              <span>Ecosistema</span>
            </TabsTrigger>
            <TabsTrigger value="genia" className="flex items-center space-x-2">
              <Brain className="h-4 w-4" />
              <span>GenIA</span>
            </TabsTrigger>
            <TabsTrigger value="aura" className="flex items-center space-x-2">
              <Target className="h-4 w-4" />
              <span>AURA</span>
            </TabsTrigger>
            
          </TabsList>

          {/* GenIA Content */}
          <TabsContent value="genia" className="space-y-8">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div className="space-y-6">
                <h3 className="text-3xl font-bold tech-title">
                  Inteligencia Artificial Generativa
                </h3>
                <p className="text-lg text-muted-foreground">
                  Potencia tu creatividad y automatización con nuestros modelos de IA generativa de última generación. 
                  Desde chatbots conversacionales hasta generación de código, GenIA transforma la forma en que trabajas.
                </p>
                
                <div className="grid grid-cols-2 gap-4">
                  {geniaFeatures.map((feature, index) => (
                    <div key={index} className="glass rounded-lg p-4 border border-primary/10">
                      <feature.icon className="h-8 w-8 text-primary mb-2" />
                      <h4 className="font-semibold mb-1">{feature.title}</h4>
                      <p className="text-sm text-muted-foreground">{feature.description}</p>
                    </div>
                  ))}
                </div>

                <Button size="lg" className="modern-gradient-bg hover:opacity-90 text-white">
                  Explorar GenIA
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </div>

              <div className="relative">
                <div className="glass rounded-2xl p-8 border border-primary/20">
                  <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-3 h-3 bg-emerald-400 rounded-full animate-pulse" />
                      <span className="font-medium">GenIA System Active</span>
                    </div>
                    
                    <div className="space-y-3">
                      {geniaFeatures[currentFeature].capabilities.map((capability, index) => (
                        <div key={index} className="flex items-center space-x-2">
                          <CheckCircle className="h-4 w-4 text-emerald-500" />
                          <span className="text-sm">{capability}</span>
                        </div>
                      ))}
                    </div>

                    <div className="mt-6 p-4 bg-gradient-to-r from-primary/10 to-emerald-500/10 rounded-lg">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">99.8%</div>
                        <div className="text-sm text-muted-foreground">Precisión en Generación</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* AURA Content */}
          <TabsContent value="aura" className="space-y-8">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div className="relative">
                <div className="glass rounded-2xl p-8 border border-primary/20">
                  <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-3 h-3 bg-purple-400 rounded-full animate-pulse" />
                      <span className="font-medium">AURA Analytics Engine</span>
                    </div>
                    
                    <div className="space-y-3">
                      {auraFeatures[currentFeature].capabilities.map((capability, index) => (
                        <div key={index} className="flex items-center space-x-2">
                          <CheckCircle className="h-4 w-4 text-purple-500" />
                          <span className="text-sm">{capability}</span>
                        </div>
                      ))}
                    </div>

                    <div className="mt-6 p-4 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-lg">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-600">500K+</div>
                        <div className="text-sm text-muted-foreground">Perfiles Analizados</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-6">
                <h3 className="text-3xl font-bold accent-title">
                  Motor de Desarrollo Profesional
                </h3>
                <p className="text-lg text-muted-foreground">
                  AURA revoluciona el desarrollo profesional con análisis inteligente de brechas de habilidades, 
                  networking automatizado y rutas de aprendizaje personalizadas basadas en datos del mercado.
                </p>
                
                <div className="grid grid-cols-2 gap-4">
                  {auraFeatures.map((feature, index) => (
                    <div key={index} className="glass rounded-lg p-4 border border-primary/10">
                      <feature.icon className="h-8 w-8 text-purple-500 mb-2" />
                      <h4 className="font-semibold mb-1">{feature.title}</h4>
                      <p className="text-sm text-muted-foreground">{feature.description}</p>
                    </div>
                  ))}
                </div>

                <Button size="lg" className="bg-gradient-to-r from-purple-600 to-pink-600 hover:opacity-90 text-white">
                  Descubrir AURA
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </div>
            </div>
          </TabsContent>

          {/* Ecosystem Content */}
          <TabsContent value="ecosystem" className="space-y-8">
            <div className="text-center mb-12">
              <h3 className="text-3xl font-bold mb-4">
                Ecosistema <span className="emerald-title">Integrado</span>
              </h3>
              <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
                Una plataforma unificada que combina la potencia de GenIA y AURA con infraestructura empresarial 
                de clase mundial, seguridad avanzada y escalabilidad automática.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {ecosystemFeatures.map((feature, index) => (
                <Card key={index} className="glass border-primary/20 hover:border-primary/40 transition-all hover:scale-105">
                  <CardHeader className="text-center pb-4">
                    <div className="mx-auto w-12 h-12 bg-gradient-to-r from-primary/20 to-emerald-500/20 rounded-lg flex items-center justify-center mb-3">
                      <feature.icon className="h-6 w-6 text-primary" />
                    </div>
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm text-muted-foreground text-center">
                      {feature.description}
                    </p>
                    <div className="space-y-2">
                      {feature.features.map((feat, featIndex) => (
                        <div key={featIndex} className="flex items-center space-x-2">
                          <CheckCircle className="h-3 w-3 text-emerald-500 flex-shrink-0" />
                          <span className="text-xs">{feat}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="text-center">
              <Button size="lg" className="modern-gradient-bg hover:opacity-90 text-white">
                Solicitar Demo
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </div>
          </TabsContent>
        </Tabs>

        {/* Stats Section */}
        <div className="grid md:grid-cols-4 gap-6 mt-16">
          <div className="glass rounded-xl p-6 text-center border border-primary/20">
            <div className="text-3xl font-bold tech-title mb-2">
              1M+
            </div>
            <div className="text-sm text-muted-foreground">Interacciones IA</div>
          </div>
          <div className="glass rounded-xl p-6 text-center border border-primary/20">
            <div className="text-3xl font-bold tech-title mb-2">
              50K+
            </div>
            <div className="text-sm text-muted-foreground">Usuarios Activos</div>
          </div>
          <div className="glass rounded-xl p-6 text-center border border-primary/20">
            <div className="text-3xl font-bold tech-title mb-2">
              99.9%
            </div>
            <div className="text-sm text-muted-foreground">Uptime</div>
          </div>
          <div className="glass rounded-xl p-6 text-center border border-primary/20">
            <div className="text-3xl font-bold tech-title mb-2">
              24/7
            </div>
            <div className="text-sm text-muted-foreground">Soporte</div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default GenIAAndAURASection;
