import React, { useState, useEffect } from 'react';
import { Brain, Target, Users, TrendingUp, Award, Lightbulb, Search, Heart, GraduationCap } from 'lucide-react';
import { Button } from '@/components/ui/button';

const TalentEcosystemSection = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  const ecosystemSteps = [
    {
      id: 'identify',
      title: 'Identifica',
      icon: Search,
      color: 'from-tech-blue to-tech-cyan',
      description: 'Descubre talento oculto y potencial no explorado',
      details: 'Utiliza IA avanzada para identificar candidatos perfectos basándose en skills, potencial y fit cultural.',
      assistant: 'GenIA',
      metrics: '95% precisión'
    },
    {
      id: 'know',
      title: 'Conoce',
      icon: Brain,
      color: 'from-tech-cyan to-tech-purple',
      description: 'Comprende profundamente a cada persona',
      details: 'Análisis 360° de competencias, motivaciones, aspiraciones y estilo de trabajo único.',
      assistant: 'AURA',
      metrics: '360° análisis'
    },
    {
      id: 'motivate',
      title: 'Motiva',
      icon: Heart,
      color: 'from-tech-purple to-tech-red',
      description: 'Impulsa el engagement y la pasión',
      details: 'Estrategias personalizadas de motivación basadas en perfiles psicológicos y objetivos individuales.',
      assistant: 'GenIA + AURA',
      metrics: '87% engagement'
    },
    {
      id: 'train',
      title: 'Capacita',
      icon: GraduationCap,
      color: 'from-tech-red to-huntred-primary',
      description: 'Desarrolla habilidades específicas',
      details: 'Rutas de aprendizaje personalizadas con contenido adaptativo y evaluación continua.',
      assistant: 'AURA',
      metrics: '92% completion'
    },
    {
      id: 'recruit',
      title: 'Recluta',
      icon: Users,
      color: 'from-huntred-primary to-tech-blue',
      description: 'Conecta talento con oportunidades',
      details: 'Matchmaking inteligente que considera skills, cultura, potencial de crecimiento y aspiraciones.',
      assistant: 'GenIA',
      metrics: '89% match success'
    },
    {
      id: 'grow',
      title: 'Desarrolla',
      icon: TrendingUp,
      color: 'from-tech-blue to-tech-cyan',
      description: 'Acelera el crecimiento profesional',
      details: 'Planes de carrera dinámicos con mentoría IA y oportunidades de crecimiento personalizadas.',
      assistant: 'AURA',
      metrics: '3x faster growth'
    }
  ];

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.1 }
    );

    const section = document.getElementById('talent-ecosystem');
    if (section) observer.observe(section);

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (isVisible) {
      const timer = setInterval(() => {
        setActiveStep((prev) => (prev + 1) % ecosystemSteps.length);
      }, 4000);
      return () => clearInterval(timer);
    }
  }, [isVisible, ecosystemSteps.length]);

  return (
    <section id="talent-ecosystem" className="py-20 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background/50 to-background" />
      <div className="absolute inset-0 bg-hero-pattern opacity-30" />
      
      {/* Floating particles */}
      <div className="absolute top-20 left-20 w-2 h-2 bg-tech-blue rounded-full animate-ping" />
      <div className="absolute top-40 right-40 w-1 h-1 bg-tech-purple rounded-full animate-pulse" />
      <div className="absolute bottom-60 left-60 w-3 h-3 bg-tech-cyan rounded-full animate-bounce" />

      <div className="container mx-auto px-4 lg:px-8 relative z-10">
        {/* Header */}
        <div className="text-center mb-16 animate-fade-in">
          <div className="inline-flex items-center space-x-2 glass rounded-full px-6 py-3 mb-6 border border-primary/20">
            <Award className="h-5 w-5 text-primary" />
            <span className="text-sm font-medium">ECOSISTEMA COMPLETO DE TALENTO</span>
          </div>
          
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            <span className="bg-gradient-to-r from-huntred-primary to-tech-blue bg-clip-text text-transparent">
              Ciclo Virtuoso
            </span>
            <br />
            de Talento Humano
          </h2>
          
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-8">
            Tu <strong>one-stop shop</strong> para revolucionar la gestión de talento. 
            Desde la identificación hasta el desarrollo continuo, todo en una plataforma inteligente.
          </p>
          
          <div className="flex flex-wrap justify-center gap-4 mb-12">
            <div className="glass rounded-lg px-4 py-2 border border-tech-blue/20">
              <span className="text-sm font-medium text-tech-blue">Powered by GenIA</span>
            </div>
            <div className="glass rounded-lg px-4 py-2 border border-tech-purple/20">
              <span className="text-sm font-medium text-tech-purple">Enhanced by AURA</span>
            </div>
          </div>
        </div>

        {/* Ecosystem Visualization */}
        <div className="relative max-w-6xl mx-auto">
          {/* Central Hub */}
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20">
            <div className="w-32 h-32 rounded-full bg-gradient-to-r from-huntred-primary to-tech-blue glass border-4 border-white/20 flex items-center justify-center animate-pulse-slow">
              <div className="text-center">
                <Brain className="h-8 w-8 text-white mx-auto mb-1" />
                <span className="text-xs font-bold text-white">huntRED®</span>
              </div>
            </div>
          </div>

          {/* Ecosystem Steps in Circle */}
          <div className="relative w-full h-[600px] mx-auto">
            {ecosystemSteps.map((step, index) => {
              const angle = (index * 360) / ecosystemSteps.length;
              const radius = 200;
              const x = Math.cos((angle - 90) * (Math.PI / 180)) * radius;
              const y = Math.sin((angle - 90) * (Math.PI / 180)) * radius;
              
              const IconComponent = step.icon;
              const isActive = activeStep === index;
              
              return (
                <div
                  key={step.id}
                  className={`absolute transform -translate-x-1/2 -translate-y-1/2 transition-all duration-1000 cursor-pointer ${
                    isActive ? 'scale-110 z-10' : 'scale-90 hover:scale-100'
                  }`}
                  style={{
                    left: `calc(50% + ${x}px)`,
                    top: `calc(50% + ${y}px)`,
                  }}
                  onClick={() => setActiveStep(index)}
                >
                  {/* Connection Line to Center */}
                  <div 
                    className={`absolute w-0.5 bg-gradient-to-r ${step.color} opacity-30 transition-opacity duration-500 ${
                      isActive ? 'opacity-100' : ''
                    }`}
                    style={{
                      height: `${radius - 64}px`,
                      left: '50%',
                      top: '100%',
                      transformOrigin: 'top center',
                      transform: `rotate(${angle + 90}deg)`,
                    }}
                  />
                  
                  {/* Step Card */}
                  <div className={`glass rounded-xl p-6 border-2 transition-all duration-500 w-48 ${
                    isActive 
                      ? `border-primary shadow-xl bg-gradient-to-r ${step.color} text-white` 
                      : 'border-border/20 hover:border-primary/50'
                  }`}>
                    <div className="text-center space-y-3">
                      <div className={`w-12 h-12 rounded-full mx-auto flex items-center justify-center ${
                        isActive ? 'bg-white/20' : 'bg-primary/10'
                      }`}>
                        <IconComponent className={`h-6 w-6 ${isActive ? 'text-white' : 'text-primary'}`} />
                      </div>
                      
                      <h3 className={`font-bold text-lg ${isActive ? 'text-white' : ''}`}>
                        {step.title}
                      </h3>
                      
                      <p className={`text-sm ${isActive ? 'text-white/90' : 'text-muted-foreground'}`}>
                        {step.description}
                      </p>
                      
                      <div className={`text-xs font-medium ${isActive ? 'text-white/80' : 'text-primary'}`}>
                        {step.assistant} • {step.metrics}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Active Step Details */}
        <div className="mt-16 max-w-4xl mx-auto animate-fade-in">
          <div className="glass rounded-2xl p-8 border border-primary/20">
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div>
                <h3 className={`text-3xl font-bold mb-4 bg-gradient-to-r ${ecosystemSteps[activeStep].color} bg-clip-text text-transparent`}>
                  {ecosystemSteps[activeStep].title}
                </h3>
                <p className="text-lg text-muted-foreground mb-6">
                  {ecosystemSteps[activeStep].details}
                </p>
                <div className="flex items-center space-x-4 mb-6">
                  <div className="flex items-center space-x-2">
                    <Lightbulb className="h-4 w-4 text-primary" />
                    <span className="text-sm font-medium">Asistido por {ecosystemSteps[activeStep].assistant}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Target className="h-4 w-4 text-green-500" />
                    <span className="text-sm font-medium">{ecosystemSteps[activeStep].metrics}</span>
                  </div>
                </div>
                <Button className={`bg-gradient-to-r ${ecosystemSteps[activeStep].color} hover:opacity-90`}>
                  Explorar {ecosystemSteps[activeStep].title}
                </Button>
              </div>
              
              <div className="relative">
                <div className={`w-64 h-64 rounded-2xl mx-auto bg-gradient-to-r ${ecosystemSteps[activeStep].color} p-0.5`}>
                  <div className="w-full h-full rounded-2xl bg-background/90 flex items-center justify-center">
                    {React.createElement(ecosystemSteps[activeStep].icon, {
                      className: `h-24 w-24 bg-gradient-to-r ${ecosystemSteps[activeStep].color} bg-clip-text text-transparent`
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center mt-16">
          <Button size="lg" className="bg-gradient-to-r from-huntred-primary to-tech-blue hover:opacity-90 text-white px-8 py-4">
            <Brain className="mr-2 h-5 w-5" />
            Comenzar Transformación
          </Button>
          <p className="text-sm text-muted-foreground mt-4">
            Únete a las empresas líderes que ya transformaron su gestión de talento
          </p>
        </div>
      </div>
    </section>
  );
};

export default TalentEcosystemSection;