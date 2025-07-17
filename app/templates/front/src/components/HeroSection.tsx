
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { ArrowRight, Calendar, Brain, Target, Sparkles, Layers, Users, TrendingUp, BarChart3, Activity, PieChart, Zap } from 'lucide-react';

const HeroSection = () => {
  const [currentSlide, setCurrentSlide] = useState(0);

  const slides = [
    {
      title: "Gestión Integral del Talento Humano",
      subtitle: "Acompañamos toda la vida profesional de cada persona",
      description: "Desde el descubrimiento hasta la realización. Entendemos que las personas evolucionan, sus motivadores cambian y sus contextos se transforman. Nuestra plataforma se adapta a cada momento de su viaje.",
      cta: "Ver Metodología Integral",
      image: "https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      icon: Layers,
      color: "bg-gradient-to-r from-blue-600 to-blue-400",
      particles: true,
      type: "default"
    },
    {
      title: "Dashboard Inteligente de Talento",
      subtitle: "Visualización en tiempo real de métricas clave",
      description: "Monitorea, analiza y optimiza tu ecosistema de talento con dashboards interactivos, métricas predictivas y análisis profundos de rendimiento.",
      cta: "Ver Dashboard",
      image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      icon: BarChart3,
      color: "bg-gradient-blue-dark-light",
      particles: true,
      type: "dashboard"
    },
    {
      title: "huntRED®: Tu One-Stop Shop de Talento",
      subtitle: "La plataforma integral que conecta todo tu ecosistema de RH",
      description: "Ecosistema completo → Ciclo virtuoso detallado → GenIA & AURA → Casos de éxito → Soluciones tecnológicas → Partners globales. Todo conectado en una experiencia única.",
      cta: "Ver Plataforma Completa",
      image: "https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      icon: Target,
      color: "bg-gradient-cyan-blue",
      particles: true,
      type: "cards"
    },
    {
      title: "Grupo huntRED®: Tu Ecosistema Completo de Talento",
      subtitle: "La plataforma integral que revoluciona la gestión de talento humano",
      description: "Desde la identificación hasta la retención. Un ciclo virtuoso completo: identifica, conoce, motiva, capacita, recluta y desarrolla todo el potencial de tu organización en una sola plataforma.",
      cta: "Descubrir Ecosistema",
      image: "https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      icon: Brain,
      color: "from-huntred-primary to-tech-blue",
      particles: true,
      type: "default"
    },
    {
      title: "GenIA: Inteligencia Artificial Generativa",
      subtitle: "Creatividad sin límites impulsada por IA avanzada",
      description: "Potencia tu creatividad con modelos de IA de última generación. Chatbots conversacionales, generación de código, análisis creativo y automatización inteligente.",
      cta: "Explorar GenIA",
      image: "https://images.unsplash.com/photo-1677442136019-21780ecad995?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      icon: Sparkles,
      color: "from-tech-blue to-tech-cyan",
      particles: false,
      type: "default"
    },
    {
      title: "AURA: Motor de Desarrollo Profesional",
      subtitle: "Inteligencia predictiva para el crecimiento del talento",
      description: "Revoluciona el desarrollo profesional con análisis inteligente, detección de brechas de habilidades, rutas de aprendizaje personalizadas y networking estratégico.",
      cta: "Conocer AURA",
      image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      icon: Target,
      color: "from-tech-purple to-tech-red",
      particles: false,
      type: "default"
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  const IconComponent = slides[currentSlide].icon;

  const renderVisualContent = () => {
    const currentType = slides[currentSlide].type;
    
    if (currentType === 'dashboard') {
      return (
        <div className="relative animate-slide-in-right">
          <div className="relative w-full h-[500px] rounded-2xl overflow-hidden glass p-6">
            <div className="grid grid-cols-2 gap-4 h-full">
              {/* Dashboard Cards */}
              <Card className="glass border-primary/20">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Users className="h-4 w-4 text-primary" />
                    Talento Activo
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-primary">125,847</div>
                  <p className="text-xs text-muted-foreground">+12% vs mes anterior</p>
                  <Progress value={85} className="mt-2" />
                </CardContent>
              </Card>
              
              <Card className="glass border-primary/20">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-tech-blue" />
                    Match Rate
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-tech-blue">94.2%</div>
                  <p className="text-xs text-muted-foreground">Precisión de IA</p>
                  <Progress value={94} className="mt-2" />
                </CardContent>
              </Card>
              
              <Card className="glass border-primary/20">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Activity className="h-4 w-4 text-tech-purple" />
                    Procesamiento
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-tech-purple">Real-time</div>
                  <p className="text-xs text-muted-foreground">1.2M proc/día</p>
                  <Progress value={100} className="mt-2" />
                </CardContent>
              </Card>
              
              <Card className="glass border-primary/20">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Zap className="h-4 w-4 text-tech-cyan" />
                    Automatización
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-tech-cyan">87%</div>
                  <p className="text-xs text-muted-foreground">Tareas automáticas</p>
                  <Progress value={87} className="mt-2" />
                </CardContent>
              </Card>
            </div>
            
            <div className="absolute top-4 right-4 glass rounded-lg p-2">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span className="text-xs font-medium">Dashboard Live</span>
              </div>
            </div>
          </div>
        </div>
      );
    }
    
    if (currentType === 'cards') {
      return (
        <div className="relative animate-slide-in-right">
          <div className="relative w-full h-[500px] rounded-2xl overflow-hidden glass p-4">
            <div className="grid grid-cols-2 gap-3 h-full">
              <div className="space-y-3">
                <Card className="glass border-primary/20 p-3">
                  <div className="flex items-center gap-2">
                    <Brain className="h-8 w-8 text-primary" />
                    <div>
                      <div className="font-semibold text-sm">GenIA</div>
                      <div className="text-xs text-muted-foreground">IA Generativa</div>
                    </div>
                  </div>
                </Card>
                
                <Card className="glass border-primary/20 p-3">
                  <div className="flex items-center gap-2">
                    <Target className="h-8 w-8 text-tech-blue" />
                    <div>
                      <div className="font-semibold text-sm">AURA</div>
                      <div className="text-xs text-muted-foreground">Analítica Predictiva</div>
                    </div>
                  </div>
                </Card>
                
                <Card className="glass border-primary/20 p-3">
                  <div className="flex items-center gap-2">
                    <Users className="h-8 w-8 text-tech-purple" />
                    <div>
                      <div className="font-semibold text-sm">ATS</div>
                      <div className="text-xs text-muted-foreground">Gestión Completa</div>
                    </div>
                  </div>
                </Card>
              </div>
              
              <div className="space-y-3">
                <Card className="glass border-primary/20 p-3">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-8 w-8 text-tech-cyan" />
                    <div>
                      <div className="font-semibold text-sm">Analytics</div>
                      <div className="text-xs text-muted-foreground">Insights Profundos</div>
                    </div>
                  </div>
                </Card>
                
                <Card className="glass border-primary/20 p-3">
                  <div className="flex items-center gap-2">
                    <PieChart className="h-8 w-8 text-tech-red" />
                    <div>
                      <div className="font-semibold text-sm">Reporting</div>
                      <div className="text-xs text-muted-foreground">Dashboards</div>
                    </div>
                  </div>
                </Card>
                
                <Card className="glass border-primary/20 p-3">
                  <div className="flex items-center gap-2">
                    <Zap className="h-8 w-8 text-huntred-primary" />
                    <div>
                      <div className="font-semibold text-sm">Automation</div>
                      <div className="text-xs text-muted-foreground">Workflows</div>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
            
            <div className="absolute top-4 right-4 glass rounded-lg p-2">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                <span className="text-xs font-medium">Módulos Activos</span>
              </div>
            </div>
          </div>
        </div>
      );
    }
    
    // Default visual content
    return (
      <div className="relative animate-slide-in-right">
        <div className="relative w-full h-[500px] rounded-2xl overflow-hidden glass">
          <img
            src={slides[currentSlide].image}
            alt="AI Technology"
            className="w-full h-full object-cover transition-transform duration-1000 hover:scale-105"
          />
          <div className={`absolute inset-0 bg-gradient-to-r ${slides[currentSlide].color} opacity-20`} />
          
          {/* Tech Overlay */}
          <div className="absolute top-4 left-4 glass rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span className="text-sm font-medium">AI System Active</span>
            </div>
          </div>
          
          <div className="absolute bottom-4 right-4 glass rounded-lg p-3">
            <div className="text-sm">
              <div className="font-semibold">99.7%</div>
              <div className="text-muted-foreground">Accuracy</div>
            </div>
          </div>
        </div>

        {/* Floating Stats */}
        <div className="absolute -top-6 -right-6 glass rounded-xl p-4 animate-float">
          <div className="text-center">
            <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">500+</div>
            <div className="text-sm text-muted-foreground">Proyectos</div>
          </div>
        </div>

        <div className="absolute -bottom-6 -left-6 glass rounded-xl p-4 animate-float" style={{ animationDelay: '3s' }}>
          <div className="text-center">
            <div className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">24/7</div>
            <div className="text-sm text-muted-foreground">Soporte</div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <section id="hero" className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Dynamic Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background/80 to-background" />
      <div className="absolute inset-0 bg-hero-pattern opacity-60" />
      
      {/* Animated Particles */}
      {slides[currentSlide].particles && (
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className={`absolute w-1 h-1 bg-primary rounded-full animate-float`}
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 6}s`,
                animationDuration: `${3 + Math.random() * 4}s`
              }}
            />
          ))}
        </div>
      )}
      
      {/* Floating Elements */}
      <div className="absolute top-20 left-10 w-20 h-20 bg-tech-blue/30 rounded-full animate-float blur-sm" />
      <div className="absolute top-40 right-20 w-16 h-16 bg-tech-purple/30 rounded-full animate-float blur-sm" style={{ animationDelay: '2s' }} />
      <div className="absolute bottom-40 left-20 w-12 h-12 bg-tech-cyan/30 rounded-full animate-float blur-sm" style={{ animationDelay: '4s' }} />
      <div className="absolute top-60 right-60 w-8 h-8 bg-huntred-primary/30 rounded-full animate-float blur-sm" style={{ animationDelay: '1s' }} />
      <div className="absolute bottom-60 right-40 w-14 h-14 bg-tech-red/30 rounded-full animate-float blur-sm" style={{ animationDelay: '3s' }} />

      <div className="container mx-auto px-4 lg:px-8 pt-16 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Content */}
          <div className="space-y-8 animate-fade-in-up">
            <div className="space-y-4">
              {/* Badge */}
              <div className="inline-flex items-center space-x-2 glass rounded-full px-4 py-2 border border-primary/20">
                <IconComponent className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium">GRUPO HUNTRED® AI</span>
              </div>
              
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight">
                {slides[currentSlide].title.split(' ').map((word, index) => (
                  <span 
                    key={index} 
                    className={index >= 2 ? `bg-gradient-to-r ${slides[currentSlide].color} bg-clip-text text-transparent` : ''}
                  >
                    {word}{' '}
                  </span>
                ))}
              </h1>
              <p className="text-xl md:text-2xl text-muted-foreground">
                {slides[currentSlide].subtitle}
              </p>
              <p className="text-lg text-muted-foreground max-w-2xl">
                {slides[currentSlide].description}
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button size="lg" className={`bg-gradient-to-r ${slides[currentSlide].color} hover:opacity-90 transition-opacity`}>
                <Calendar className="mr-2 h-5 w-5" />
                Agendar Demo
              </Button>
              <Button size="lg" variant="outline" className="border-primary/30 hover:bg-primary/10">
                {slides[currentSlide].cta}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </div>

            {/* Slide Indicators */}
            <div className="flex space-x-2">
              {slides.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentSlide(index)}
                  className={`w-3 h-3 rounded-full transition-all ${
                    index === currentSlide ? 'bg-primary scale-110' : 'bg-muted-foreground/30'
                  }`}
                />
              ))}
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-4 pt-4">
              <div className="text-center">
                <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">1M+</div>
                <div className="text-sm text-muted-foreground">Interacciones</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">50K+</div>
                <div className="text-sm text-muted-foreground">Usuarios</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">99.9%</div>
                <div className="text-sm text-muted-foreground">Uptime</div>
              </div>
            </div>
          </div>

          {/* Dynamic Visual Content */}
          {renderVisualContent()}
        </div>
      </div>
    </section>
  );
};

export default HeroSection;