import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Search, 
  UserCheck, 
  GraduationCap, 
  TrendingUp, 
  Heart, 
  LogOut, 
  Calculator,
  Brain,
  Target,
  ArrowRight,
  CheckCircle,
  BarChart3,
  Zap,
  Shield
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const TalentLifecycleSection = () => {
  const [activeStage, setActiveStage] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  const lifecycleStages = [
    {
      id: 'attraction',
      title: 'Atracción',
      subtitle: 'Employer Branding',
      icon: Users,
      color: 'from-tech-blue to-tech-cyan',
      description: 'Construcción de una marca empleadora atractiva',
      objective: 'Posicionar a la empresa cliente como un empleador de elección mediante estrategias de employer branding impulsadas por IA.',
      actions: [
        'Análisis predictivo de IA para identificar perfiles de candidatos ideales',
        'Campañas de marketing de reclutamiento personalizadas',
        'Contenido dinámico (videos, testimonios, historias)',
        'Monitoreo de percepción de marca empleadora en tiempo real'
      ],
      tools: [
        'Algoritmos de IA para segmentar audiencias',
        'Análisis de sentimiento en redes sociales'
      ],
      result: 'Incremento en la atracción de candidatos de alto potencial',
      metrics: '+40% candidatos calificados'
    },
    {
      id: 'selection',
      title: 'Selección',
      subtitle: 'Contratación',
      icon: Search,
      color: 'from-tech-cyan to-tech-purple',
      description: 'Identificación del talento ideal',
      objective: 'Implementar un proceso de selección eficiente y basado en datos para garantizar la contratación de los mejores candidatos.',
      actions: [
        'Herramientas de IA para filtrar currículums y evaluar competencias',
        'Entrevistas estructuradas con evaluaciones basadas en competencias',
        'Assessments gamificados para evaluar habilidades',
        'Reportes detallados del proceso de selección'
      ],
      tools: [
        'Plataformas de evaluación con IA para reducir sesgos',
        'Dashboards personalizados para seguimiento en tiempo real'
      ],
      result: 'Contrataciones más rápidas y precisas',
      metrics: '60% reducción tiempo de selección'
    },
    {
      id: 'onboarding',
      title: 'Onboarding',
      subtitle: 'Integración',
      icon: UserCheck,
      color: 'from-tech-purple to-tech-red',
      description: 'Integración eficiente y personalizada',
      objective: 'Facilitar una integración rápida y efectiva de los nuevos empleados para maximizar su compromiso desde el inicio.',
      actions: [
        'Programas de onboarding personalizados basados en el perfil',
        'Plataformas digitales con IA para guiar la incorporación',
        'Asignación de mentores o buddies',
        'Feedback continuo durante el onboarding'
      ],
      tools: [
        'Chatbots de IA para resolver dudas en tiempo real',
        'Análisis de datos para medir efectividad del onboarding'
      ],
      result: 'Nuevos empleados integrados rápidamente',
      metrics: '85% satisfacción inicial'
    },
    {
      id: 'development',
      title: 'Desarrollo',
      subtitle: 'Formación',
      icon: GraduationCap,
      color: 'from-tech-red to-huntred-primary',
      description: 'Crecimiento continuo del talento',
      objective: 'Fomentar el desarrollo profesional continuo para alinear las habilidades del equipo con los objetivos estratégicos.',
      actions: [
        'Planes de formación personalizados con análisis de brechas',
        'Programas de aprendizaje continuo (e-learning, talleres)',
        'Planes de carrera claros con metas alcanzables',
        'Evaluación de impacto mediante métricas de desempeño'
      ],
      tools: [
        'Plataformas de e-learning con recomendaciones de IA',
        'Reportes analíticos para medir ROI de formación'
      ],
      result: 'Equipos más capacitados y motivados',
      metrics: '3.2x ROI en formación'
    },
    {
      id: 'performance',
      title: 'Desempeño',
      subtitle: 'Reconocimiento',
      icon: TrendingUp,
      color: 'from-huntred-primary to-tech-blue',
      description: 'Motivación y productividad',
      objective: 'Monitorear el desempeño y recompensar los logros para mantener un equipo comprometido y productivo.',
      actions: [
        'Sistemas de evaluación basados en objetivos (OKRs/KPIs)',
        'IA para retroalimentación continua y personalizada',
        'Programas de reconocimiento con incentivos diversos',
        'Análisis de datos para identificar tendencias'
      ],
      tools: [
        'Dashboards de desempeño con visualización en tiempo real',
        'Algoritmos de IA para detectar patrones de alto rendimiento'
      ],
      result: 'Mayor productividad y compromiso',
      metrics: '+25% productividad'
    },
    {
      id: 'retention',
      title: 'Fidelización',
      subtitle: 'Retención',
      icon: Heart,
      color: 'from-tech-blue to-tech-cyan',
      description: 'Retención del talento',
      objective: 'Crear un entorno que promueva la satisfacción y el bienestar para reducir la rotación.',
      actions: [
        'Programas de bienestar con flexibilidad laboral',
        'Encuestas de clima laboral analizadas con IA',
        'Cultura de inclusión y diversidad',
        'Beneficios personalizados adaptados a necesidades'
      ],
      tools: [
        'Análisis predictivo para identificar riesgos de rotación',
        'Plataformas de engagement para medir satisfacción'
      ],
      result: 'Mayor retención y cultura empresarial sólida',
      metrics: '70% reducción rotación'
    },
    {
      id: 'offboarding',
      title: 'Desvinculación',
      subtitle: 'Outplacement',
      icon: LogOut,
      color: 'from-tech-cyan to-tech-purple',
      description: 'Salidas positivas',
      objective: 'Gestionar las desvinculaciones de manera profesional y ética, preservando la reputación de la empresa.',
      actions: [
        'Entrevistas de salida estructuradas para feedback',
        'Servicios de outplacement para transición',
        'Comunicación transparente y respetuosa',
        'Análisis de datos de desvinculaciones'
      ],
      tools: [
        'IA para analizar feedback y generar reportes accionables',
        'Programas de outplacement personalizados'
      ],
      result: 'Experiencias de salida positivas',
      metrics: '90% satisfacción en salida'
    },
    {
      id: 'payroll',
      title: 'Administración',
      subtitle: 'Nómina',
      icon: Calculator,
      color: 'from-tech-purple to-tech-red',
      description: 'Eficiencia y cumplimiento',
      objective: 'Garantizar una gestión de nómina precisa, eficiente y alineada con las regulaciones locales.',
      actions: [
        'Sistemas automatizados de nómina integrados con IA',
        'Gestión de cumplimiento normativo laboral y fiscal',
        'Portales de autoservicio para empleados',
        'Reportes financieros y analíticos'
      ],
      tools: [
        'Software de nómina con IA para detectar errores',
        'Dashboards financieros con métricas clave'
      ],
      result: 'Procesos eficientes y cumplimiento garantizado',
      metrics: '99.8% precisión nómina'
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

    const section = document.getElementById('talent-lifecycle');
    if (section) observer.observe(section);

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (isVisible) {
      const timer = setInterval(() => {
        setActiveStage((prev) => (prev + 1) % lifecycleStages.length);
      }, 5000);
      return () => clearInterval(timer);
    }
  }, [isVisible, lifecycleStages.length]);

  const currentStage = lifecycleStages[activeStage];
  const IconComponent = currentStage.icon;

  return (
    <section id="talent-lifecycle" className="py-20 relative overflow-hidden bg-gradient-to-br from-background to-background/80">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-hero-pattern opacity-20" />
      <div className="absolute top-40 left-40 w-96 h-96 bg-gradient-to-r from-tech-blue/10 to-tech-purple/10 rounded-full blur-3xl" />
      <div className="absolute bottom-40 right-40 w-80 h-80 bg-gradient-to-r from-huntred-primary/10 to-tech-cyan/10 rounded-full blur-3xl" />

      <div className="container mx-auto px-4 lg:px-8 relative z-10">
        {/* Header */}
        <div className="text-center mb-16 animate-fade-in">
          <div className="inline-flex items-center space-x-2 glass rounded-full px-6 py-3 mb-6 border border-primary/20">
            <Brain className="h-5 w-5 text-primary" />
            <span className="text-sm font-medium">CICLO VIRTUOSO COMPLETO</span>
          </div>
          
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            <span className="bg-gradient-to-r from-huntred-primary to-tech-blue bg-clip-text text-transparent">
              Gestión Integral
            </span>
            <br />
            del Talento Humano
          </h2>
          
          <p className="text-xl text-muted-foreground max-w-4xl mx-auto mb-8">
            Un ciclo virtuoso que combina <strong>inteligencia artificial</strong>, análisis de mercado y experiencia en recursos humanos 
            para optimizar el ciclo de vida del empleado y la administración de nómina.
          </p>
          
          <div className="flex flex-wrap justify-center gap-2 mb-8">
            <Badge variant="outline" className="border-tech-blue/50 text-tech-blue">
              IA Predictiva
            </Badge>
            <Badge variant="outline" className="border-tech-purple/50 text-tech-purple">
              Análisis de Datos
            </Badge>
            <Badge variant="outline" className="border-huntred-primary/50 text-huntred-primary">
              Mejora Continua
            </Badge>
            <Badge variant="outline" className="border-tech-cyan/50 text-tech-cyan">
              Experiencia Empleado
            </Badge>
          </div>
        </div>

        {/* Lifecycle Visualization */}
        <div className="max-w-7xl mx-auto mb-16">
          <div className="relative">
            {/* Central Hub */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20">
              <div className="w-40 h-40 rounded-full bg-gradient-to-r from-huntred-primary to-tech-blue glass border-4 border-white/20 flex items-center justify-center animate-pulse-slow">
                <div className="text-center text-white">
                  <Target className="h-10 w-10 mx-auto mb-2" />
                  <span className="text-sm font-bold">huntRED®</span>
                  <div className="text-xs opacity-80">Ciclo Virtuoso</div>
                </div>
              </div>
            </div>

            {/* Lifecycle Stages */}
            <div className="relative w-full h-[700px] mx-auto">
              {lifecycleStages.map((stage, index) => {
                const angle = (index * 360) / lifecycleStages.length;
                const radius = 250;
                const x = Math.cos((angle - 90) * (Math.PI / 180)) * radius;
                const y = Math.sin((angle - 90) * (Math.PI / 180)) * radius;
                
                const StageIcon = stage.icon;
                const isActive = activeStage === index;
                
                return (
                  <div
                    key={stage.id}
                    className={`absolute transform -translate-x-1/2 -translate-y-1/2 transition-all duration-1000 cursor-pointer ${
                      isActive ? 'scale-110 z-10' : 'scale-90 hover:scale-100'
                    }`}
                    style={{
                      left: `calc(50% + ${x}px)`,
                      top: `calc(50% + ${y}px)`,
                    }}
                    onClick={() => setActiveStage(index)}
                  >
                    {/* Connection Line */}
                    <div 
                      className={`absolute w-0.5 bg-gradient-to-r ${stage.color} transition-opacity duration-500 ${
                        isActive ? 'opacity-100' : 'opacity-30'
                      }`}
                      style={{
                        height: `${radius - 80}px`,
                        left: '50%',
                        top: '100%',
                        transformOrigin: 'top center',
                        transform: `rotate(${angle + 90}deg)`,
                      }}
                    />
                    
                    {/* Stage Card */}
                    <div className={`glass rounded-xl p-4 border-2 transition-all duration-500 w-56 ${
                      isActive 
                        ? `border-primary shadow-2xl bg-gradient-to-r ${stage.color} text-white` 
                        : 'border-border/20 hover:border-primary/50'
                    }`}>
                      <div className="text-center space-y-2">
                        <div className={`w-12 h-12 rounded-full mx-auto flex items-center justify-center ${
                          isActive ? 'bg-white/20' : 'bg-primary/10'
                        }`}>
                          <StageIcon className={`h-6 w-6 ${isActive ? 'text-white' : 'text-primary'}`} />
                        </div>
                        
                        <h3 className={`font-bold text-lg ${isActive ? 'text-white' : ''}`}>
                          {stage.title}
                        </h3>
                        
                        <p className={`text-sm ${isActive ? 'text-white/90' : 'text-muted-foreground'}`}>
                          {stage.subtitle}
                        </p>
                        
                        <div className={`text-xs font-medium ${isActive ? 'text-white/80' : 'text-primary'}`}>
                          {stage.metrics}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Stage Details */}
        <div className="max-w-6xl mx-auto animate-fade-in">
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Left Column - Details */}
            <div className="space-y-6">
              <div className="glass rounded-2xl p-8 border border-primary/20">
                <div className="flex items-center space-x-4 mb-6">
                  <div className={`w-16 h-16 rounded-full bg-gradient-to-r ${currentStage.color} flex items-center justify-center`}>
                    <IconComponent className="h-8 w-8 text-white" />
                  </div>
                  <div>
                    <h3 className={`text-3xl font-bold bg-gradient-to-r ${currentStage.color} bg-clip-text text-transparent`}>
                      {currentStage.title}
                    </h3>
                    <p className="text-lg text-muted-foreground">{currentStage.subtitle}</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-lg mb-2 flex items-center">
                      <Target className="h-4 w-4 mr-2 text-primary" />
                      Objetivo
                    </h4>
                    <p className="text-muted-foreground">{currentStage.objective}</p>
                  </div>

                  <div>
                    <h4 className="font-semibold text-lg mb-3 flex items-center">
                      <CheckCircle className="h-4 w-4 mr-2 text-green-500" />
                      Acciones Clave
                    </h4>
                    <ul className="space-y-2">
                      {currentStage.actions.map((action, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <ArrowRight className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                          <span className="text-sm text-muted-foreground">{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column - Tools & Results */}
            <div className="space-y-6">
              <div className="glass rounded-2xl p-8 border border-primary/20">
                <h4 className="font-semibold text-lg mb-4 flex items-center">
                  <Zap className="h-4 w-4 mr-2 text-tech-blue" />
                  Herramientas huntRED®
                </h4>
                <ul className="space-y-3 mb-6">
                  {currentStage.tools.map((tool, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <Brain className="h-4 w-4 text-tech-purple mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-muted-foreground">{tool}</span>
                    </li>
                  ))}
                </ul>

                <div className="border-t border-border/20 pt-4">
                  <h4 className="font-semibold text-lg mb-2 flex items-center">
                    <BarChart3 className="h-4 w-4 mr-2 text-green-500" />
                    Resultado Esperado
                  </h4>
                  <p className="text-muted-foreground mb-3">{currentStage.result}</p>
                  <div className={`inline-flex items-center px-3 py-1 rounded-full bg-gradient-to-r ${currentStage.color} text-white text-sm font-medium`}>
                    <TrendingUp className="h-4 w-4 mr-1" />
                    {currentStage.metrics}
                  </div>
                </div>
              </div>

              {/* Continuous Improvement */}
              <div className="glass rounded-2xl p-6 border border-huntred-primary/20 bg-gradient-to-r from-huntred-primary/5 to-tech-blue/5">
                <h4 className="font-semibold text-lg mb-3 flex items-center">
                  <Shield className="h-4 w-4 mr-2 text-huntred-primary" />
                  Mejora Continua
                </h4>
                <p className="text-sm text-muted-foreground mb-4">
                  Cada etapa retroalimenta el ciclo mediante análisis de IA, optimización en tiempo real y reportes estratégicos 
                  para maximizar la eficiencia y mejorar la experiencia del empleado.
                </p>
                <div className="flex items-center space-x-2 text-xs">
                  <div className="w-2 h-2 bg-huntred-primary rounded-full animate-pulse" />
                  <span className="text-muted-foreground">Análisis predictivo activo</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex justify-center mt-12 space-x-2">
          {lifecycleStages.map((_, index) => (
            <button
              key={index}
              onClick={() => setActiveStage(index)}
              className={`w-3 h-3 rounded-full transition-all ${
                index === activeStage ? 'bg-primary scale-110' : 'bg-muted-foreground/30 hover:bg-muted-foreground/50'
              }`}
            />
          ))}
        </div>

        {/* CTA */}
        <div className="text-center mt-16">
          <Button size="lg" className="bg-gradient-to-r from-huntred-primary to-tech-blue hover:opacity-90 text-white px-8 py-4">
            <Brain className="mr-2 h-5 w-5" />
            Implementar Ciclo Virtuoso
          </Button>
          <p className="text-sm text-muted-foreground mt-4">
            Transforma la gestión de talento de tu organización con IA avanzada
          </p>
        </div>
      </div>
    </section>
  );
};

export default TalentLifecycleSection;