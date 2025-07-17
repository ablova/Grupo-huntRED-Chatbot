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
  Shield,
  Sparkles
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
        'Análisis predictivo GenIA para identificar perfiles ideales según tendencias del mercado',
        'Campañas de huntRED® Publish multicanal (LinkedIn, WhatsApp, Telegram, Email)',
        'Contenido dinámico generado por GenIA (videos, testimonios, historias de empleados)',
        'Monitoreo TruthSense de percepción de marca empleadora en tiempo real'
      ],
      tools: [
        'GenIA: Algoritmos de segmentación de audiencias y optimización de anuncios',
        'AURA: Análisis de sentimiento en redes sociales y ajuste de estrategias',
        'SocialLink: Integración con LinkedIn, WhatsApp, Telegram para publicación',
        'huntRED® Publish: Motor de campañas multicanal inteligentes'
      ],
      businessUnits: ['huntRED® Executive', 'huntRED®', 'huntRED® Inspiration', 'huntU', 'amigro'],
      result: 'Incremento en la atracción de candidatos de alto potencial alineados con cultura y necesidades',
      metrics: '+40% candidatos calificados, 2.5x engagement'
    },
    {
      id: 'selection',
      title: 'Selección',
      subtitle: 'Contratación',
      icon: Search,
      color: 'from-tech-cyan to-tech-purple',
      description: 'Identificación del talento ideal con ML y NLP',
      objective: 'Implementar un proceso de selección eficiente basado en 29 analyzers especializados para garantizar matching perfecto.',
      actions: [
        'CVParser + NLP para filtrar currículums y evaluar competencias técnicas y blandas',
        'Entrevistas estructuradas con Assessments ML gamificados',
        'Matchmaking inteligente con scoring predictivo AURA',
        'Workflows automatizados de aprobación y reportes detallados'
      ],
      tools: [
        'CVParser: Extracción inteligente de datos de CV con NLP avanzado',
        'AURA: 29 analyzers especializados (TechnicalSkillAnalyzer, CulturalFitAnalyzer)',
        'Assessments: Evaluaciones gamificadas con IA para reducir sesgos',
        'Workflow Engine: Automatización de procesos de selección',
        'Matchmaking ML: Scoring y ranking de candidatos'
      ],
      businessUnits: ['huntRED® Executive', 'huntRED®', 'huntRED® Experience', 'huntU'],
      result: 'Contrataciones más rápidas, precisas y con menor riesgo de rotación temprana',
      metrics: '60% reducción tiempo, 85% precisión matching'
    },
    {
      id: 'onboarding',
      title: 'Onboarding',
      subtitle: 'Integración',
      icon: UserCheck,
      color: 'from-tech-purple to-tech-red',
      description: 'Integración conversacional con Chatbot multicanal',
      objective: 'Facilitar onboarding personalizado con Chatbot IA, gamificación y workflows automáticos para maximizar engagement inicial.',
      actions: [
        'Chatbot conversacional multicanal (WhatsApp, Telegram, Slack) para guía paso a paso',
        'Workflows automatizados con triggers y tareas programadas (Celery)',
        'Gamificación: puntos, insignias y niveles por completar etapas de onboarding',
        'Feedback continuo y análisis de engagement en tiempo real'
      ],
      tools: [
        'Chatbot: Sistema conversacional NLP con contexto persistente multicanal',
        'GenIA: Generación de contenido personalizado de bienvenida',
        'Workflow Engine: Automatización de procesos de integración',
        'Gamification: Sistema de puntos, logros y leaderboards',
        'Notifications: Recordatorios automáticos multicanal (Email, WhatsApp, Slack)'
      ],
      businessUnits: ['huntRED® Inspiration', 'huntU', 'amigro', 'huntRED® Experience'],
      result: 'Nuevos empleados integrados con mayor satisfacción y productividad inicial',
      metrics: '85% satisfacción, 40% faster onboarding'
    },
    {
      id: 'development',
      title: 'Desarrollo',
      subtitle: 'Formación',
      icon: GraduationCap,
      color: 'from-tech-red to-huntred-primary',
      description: 'Crecimiento con IA predictiva y análisis de brechas',
      objective: 'Desarrollo profesional continuo con AURA predictive analytics y GenIA para alinear skills con objetivos estratégicos.',
      actions: [
        'AURA Skill Gap Analysis: análisis predictivo de brechas de habilidades',
        'GenIA Learning Plans: planes personalizados de formación con IA',
        'Assessments continuos con feedback 360° automatizado',
        'Calendaring automático con Google Calendar para sesiones de mentoring'
      ],
      tools: [
        'AURA: Predictive analytics para identificar skill gaps y recomendaciones',
        'GenIA: Generación de contenido de formación personalizado',
        'Assessments: Evaluaciones técnicas y soft skills con ML',
        'Calendar Integration: Sincronización automática de eventos de formación',
        'Analytics: Dashboards de progreso y ROI de formación'
      ],
      businessUnits: ['huntRED® Solutions', 'huntRED® Experience', 'huntU'],
      result: 'Equipos más capacitados, motivados y alineados con objetivos estratégicos',
      metrics: '3.2x ROI formación, 90% skill alignment'
    },
    {
      id: 'performance',
      title: 'Desempeño',
      subtitle: 'Reconocimiento',
      icon: TrendingUp,
      color: 'from-huntred-primary to-tech-blue',
      description: 'Motivación con gamificación y analytics predictivos',
      objective: 'Monitorear desempeño con AURA analytics y recompensar con gamificación para mantener equipos de alto rendimiento.',
      actions: [
        'Performance Analytics: dashboards en tiempo real con métricas OKRs/KPIs',
        'Gamification: puntos, badges, leaderboards y recompensas por logros',
        'AURA Pattern Detection: identificación de high performers y riesgos',
        'Feedback 360° automatizado con assessments periódicos'
      ],
      tools: [
        'AURA: Algoritmos predictivos para detectar patrones de rendimiento',
        'Gamification Analytics: métricas de engagement y motivation tracking',
        'Performance Dashboard: visualización en tiempo real con alertas',
        'Assessments: Evaluaciones 360° automatizadas',
        'Notifications: Alertas automáticas de performance y reconocimientos'
      ],
      businessUnits: ['huntRED® Executive', 'huntRED®', 'huntRED® Solutions'],
      result: 'Mayor productividad, compromiso y retención de high performers',
      metrics: '+25% productividad, 90% engagement score'
    },
    {
      id: 'retention',
      title: 'Fidelización',
      subtitle: 'Retención',
      icon: Heart,
      color: 'from-tech-blue to-tech-cyan',
      description: 'Retención predictiva con AURA churn analysis',
      objective: 'Crear ecosistema de bienestar con AURA predictive analytics para identificar riesgos de rotación y acciones preventivas.',
      actions: [
        'AURA Churn Prediction: análisis predictivo de riesgos de rotación',
        'Engagement Surveys automatizadas con sentiment analysis',
        'Referral Programs con gamificación e incentivos',
        'Beneficios personalizados con IA según preferencias del empleado'
      ],
      tools: [
        'AURA: Predictive analytics para churn prevention y engagement scoring',
        'Sentiment Analysis: NLP para analizar clima laboral en tiempo real',
        'Referral System: Programa de referidos con tracking y recompensas',
        'Gamification: Loyalty points y recognition programs',
        'Notifications: Alertas proactivas de riesgo y acciones preventivas'
      ],
      businessUnits: ['huntRED® Inspiration', 'huntRED® Experience', 'amigro'],
      result: 'Mayor retención, cultura empresarial sólida y employee advocacy',
      metrics: '70% reducción rotación, 88% satisfaction score'
    },
    {
      id: 'offboarding',
      title: 'Desvinculación',
      subtitle: 'Outplacement',
      icon: LogOut,
      color: 'from-tech-cyan to-tech-purple',
      description: 'Outplacement inteligente con GenIA y network huntRED®',
      objective: 'Gestionar desvinculaciones profesionales con GenIA feedback analysis y servicios de outplacement personalizados.',
      actions: [
        'Exit Interviews estructuradas con GenIA sentiment analysis',
        'Outplacement Services: conexión con red huntRED® para nuevas oportunidades',
        'Knowledge Transfer automatizado con documentación GenIA',
        'Alumni Network: mantener relación con ex-empleados para futuras colaboraciones'
      ],
      tools: [
        'GenIA: Análisis de feedback de salida y generación de reportes accionables',
        'huntRED® Network: Acceso a oportunidades en red de empresas clientes',
        'CVParser: Actualización automática de CV para outplacement',
        'Workflow: Automatización de procesos de desvinculación',
        'TruthSense: Monitoreo de reputación employer brand post-salida'
      ],
      businessUnits: ['huntRED® Solutions', 'huntRED® Executive', 'huntRED®'],
      result: 'Experiencias de salida positivas que refuerzan employer brand y generan referrals',
      metrics: '90% satisfacción salida, 25% rehire rate'
    },
    {
      id: 'payroll',
      title: 'Administración',
      subtitle: 'Nómina',
      icon: Calculator,
      color: 'from-tech-purple to-tech-red',
      description: 'Nómina automatizada con Payments y compliance IA',
      objective: 'Garantizar gestión de nómina con Payments automation, compliance multi-región y analytics financieros predictivos.',
      actions: [
        'Payments Integration: procesamiento automático con Stripe/PayPal/bancos',
        'Compliance IA: cumplimiento normativo multi-región automatizado',
        'Employee Self-Service: portales con Chatbot para consultas de nómina',
        'Financial Analytics: reportes predictivos y optimización de costos laborales'
      ],
      tools: [
        'Payments: Sistema automatizado con IA para detectar errores y optimización',
        'Compliance Engine: Cumplimiento GDPR, SOC2, normativas laborales locales',
        'Chatbot: Asistente para consultas de nómina y beneficios',
        'Analytics Dashboard: Métricas financieras y optimización presupuestaria',
        'Audit Trail: Trazabilidad completa y logs de cambios'
      ],
      businessUnits: ['huntRED® Solutions', 'Todas las BUs como servicio'],
      result: 'Procesos de nómina eficientes, compliance garantizado y optimización de costos',
      metrics: '99.8% precisión, 80% reducción errores'
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
    <section id="talent-lifecycle" className="py-20 relative overflow-hidden bg-gradient-to-br from-background to-background">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-hero-pattern opacity-10" />
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
        <div className="w-full mx-auto mb-16">
          <div className="relative max-w-none">
            {/* Central Hub with GenIA & AURA */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20">
              <div className="w-56 h-56 rounded-full bg-gradient-to-r from-huntred-primary to-tech-blue glass border-4 border-white/20 flex flex-col items-center justify-center animate-pulse-slow">
                <div className="text-center text-white">
                  <Target className="h-12 w-12 mx-auto mb-2" />
                  <span className="text-lg font-bold">huntRED®</span>
                  <div className="text-sm opacity-90 mb-3">Ciclo Virtuoso</div>
                  <div className="flex space-x-4 text-xs">
                    <div className="flex items-center space-x-1">
                      <Sparkles className="h-3 w-3" />
                      <span>GenIA</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Brain className="h-3 w-3" />
                      <span>AURA</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Lifecycle Stages */}
            <div className="relative w-full h-[800px] mx-auto">
              {lifecycleStages.map((stage, index) => {
                const angle = (index * 360) / lifecycleStages.length;
                const radius = 320;
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
                        height: `${radius - 110}px`,
                        left: '50%',
                        top: '100%',
                        transformOrigin: 'top center',
                        transform: `rotate(${angle + 90}deg)`,
                      }}
                    />
                    
                    {/* Stage Card */}
                    <div className={`glass rounded-xl p-5 border-2 transition-all duration-500 w-64 ${
                      isActive 
                        ? `border-white shadow-2xl bg-background/95 backdrop-blur-xl` 
                        : 'border-border/20 hover:border-primary/50'
                    }`}>
                      <div className="text-center space-y-3">
                        <div className={`w-14 h-14 rounded-full mx-auto flex items-center justify-center ${
                          isActive ? `bg-gradient-to-r ${stage.color} shadow-lg` : 'bg-primary/10'
                        }`}>
                          <StageIcon className={`h-7 w-7 ${isActive ? 'text-white' : 'text-primary'}`} />
                        </div>
                        
                        <h3 className={`font-bold text-xl ${isActive ? `bg-gradient-to-r ${stage.color} bg-clip-text text-transparent` : ''}`}>
                          {stage.title}
                        </h3>
                        
                        <p className={`text-sm ${isActive ? `bg-gradient-to-r ${stage.color} bg-clip-text text-transparent opacity-80` : 'text-muted-foreground'}`}>
                          {stage.subtitle}
                        </p>
                        
                        {/* GenIA & AURA indicators */}
                        <div className="flex justify-center space-x-3 py-2">
                          {(index === 0 || index === 1 || index === 2 || index === 6) && (
                            <div className="flex items-center space-x-1">
                              <Sparkles className={`h-3 w-3 ${isActive ? 'text-tech-cyan' : 'text-tech-cyan'}`} />
                              <span className={`text-xs ${isActive ? 'text-tech-cyan font-medium' : 'text-tech-cyan'}`}>GenIA</span>
                            </div>
                          )}
                          {(index === 3 || index === 4 || index === 5 || index === 7) && (
                            <div className="flex items-center space-x-1">
                              <Brain className={`h-3 w-3 ${isActive ? 'text-tech-purple' : 'text-tech-purple'}`} />
                              <span className={`text-xs ${isActive ? 'text-tech-purple font-medium' : 'text-tech-purple'}`}>AURA</span>
                            </div>
                          )}
                        </div>
                        
                        <div className={`text-xs font-medium ${isActive ? `bg-gradient-to-r ${stage.color} bg-clip-text text-transparent` : 'text-primary'}`}>
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
        <div className="max-w-7xl mx-auto animate-fade-in">
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Left Column - Stage Header */}
            <div className="space-y-6">
              <div className="glass rounded-2xl p-8 border border-primary/20">
                <div className="flex items-center space-x-4 mb-6">
                  <div className={`w-20 h-20 rounded-full bg-gradient-to-r ${currentStage.color} flex items-center justify-center`}>
                    <IconComponent className="h-10 w-10 text-white" />
                  </div>
                  <div>
                    <h3 className={`text-4xl font-bold bg-gradient-to-r ${currentStage.color} bg-clip-text text-transparent`}>
                      {currentStage.title}
                    </h3>
                    <p className="text-xl text-muted-foreground">{currentStage.subtitle}</p>
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

                  {/* AI Assistants */}
                  <div className="flex space-x-4 pt-4">
                    {(activeStage === 0 || activeStage === 1 || activeStage === 2 || activeStage === 6) && (
                      <div className="flex items-center space-x-2 glass rounded-full px-4 py-2 border border-tech-cyan/30">
                        <Sparkles className="h-4 w-4 text-tech-cyan" />
                        <span className="text-sm font-medium text-tech-cyan">Asistido por GenIA</span>
                      </div>
                    )}
                    {(activeStage === 3 || activeStage === 4 || activeStage === 5 || activeStage === 7) && (
                      <div className="flex items-center space-x-2 glass rounded-full px-4 py-2 border border-tech-purple/30">
                        <Brain className="h-4 w-4 text-tech-purple" />
                        <span className="text-sm font-medium text-tech-purple">Asistido por AURA</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Center Column - Actions */}
            <div className="space-y-6">
              <div className="glass rounded-2xl p-8 border border-primary/20">
                <h4 className="font-semibold text-lg mb-3 flex items-center">
                  <CheckCircle className="h-4 w-4 mr-2 text-green-500" />
                  Acciones Clave
                </h4>
                <ul className="space-y-3">
                  {currentStage.actions.map((action, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <ArrowRight className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-muted-foreground">{action}</span>
                    </li>
                  ))}
                </ul>
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