import React from 'react';
import { Users, Heart, TrendingUp, Award, Sparkles, Brain, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

const TalentJourneyOverview = () => {
  const journeyPhases = [
    {
      phase: "Descubrimiento",
      icon: Users,
      title: "Identificamos su Potencial",
      description: "Cada persona es única. Sus motivadores, aspiraciones y contexto personal evolucionan constantemente.",
      color: "from-tech-blue to-tech-cyan",
      modules: ["CVParser", "AURA Analytics", "SocialLink"]
    },
    {
      phase: "Desarrollo",
      icon: TrendingUp,
      title: "Cultivamos su Crecimiento",
      description: "Acompañamos su evolución profesional con rutas personalizadas que se adaptan a sus cambios de vida.",
      color: "from-tech-purple to-huntred-primary",
      modules: ["GenIA", "Assessments", "Gamification"]
    },
    {
      phase: "Conexión",
      icon: Heart,
      title: "Creamos Vínculos Auténticos",
      description: "Construimos relaciones genuinas que trascienden lo laboral, entendiendo su momento personal actual.",
      color: "from-huntred-primary to-tech-red",
      modules: ["Chatbot", "Workflows", "Notifications"]
    },
    {
      phase: "Realización",
      icon: Award,
      title: "Maximizamos su Impacto",
      description: "Facilitamos su contribución significativa mientras respetamos sus prioridades y valores cambiantes.",
      color: "from-tech-red to-tech-purple",
      modules: ["TruthSense", "Payments", "Analytics"]
    }
  ];

  return (
    <section className="py-24 bg-gradient-to-b from-background to-muted/20 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5" />
      
      <div className="container mx-auto px-4 lg:px-8 relative">
        {/* Header */}
        <div className="text-center max-w-4xl mx-auto mb-16">
          <div className="inline-flex items-center space-x-2 glass rounded-full px-6 py-3 mb-6">
            <Brain className="h-5 w-5 text-primary" />
            <span className="text-sm font-semibold">GESTIÓN HOLÍSTICA DEL TALENTO</span>
          </div>
          
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="bg-gradient-to-r from-huntred-primary via-tech-purple to-tech-blue bg-clip-text text-transparent">
              Acompañamos toda la Vida del Talento
            </span>
          </h2>
          
          <p className="text-xl text-muted-foreground mb-4">
            Entendemos que las personas no son estáticas. Sus motivadores cambian, sus momentos personales evolucionan, 
            sus prioridades se transforman.
          </p>
          
          <p className="text-lg text-muted-foreground">
            <strong className="text-foreground">Grupo huntRED®</strong> gestiona de manera integral cada etapa de su viaje profesional, 
            adaptándose constantemente a su evolución personal y profesional.
          </p>
        </div>

        {/* Journey Visualization */}
        <div className="relative">
          {/* Connection Line */}
          <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-tech-blue via-tech-purple to-tech-red opacity-30 transform -translate-y-1/2 hidden lg:block" />
          
          {/* Journey Phases */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {journeyPhases.map((phase, index) => {
              const IconComponent = phase.icon;
              return (
                <div key={index} className="relative group">
                  {/* Phase Card */}
                  <div className="glass rounded-2xl p-6 border border-border/50 hover:border-primary/30 transition-all duration-300 hover:scale-105 h-full">
                    {/* Phase Number */}
                    <div className="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-gradient-to-r from-primary to-primary/80 flex items-center justify-center text-sm font-bold text-primary-foreground">
                      {index + 1}
                    </div>
                    
                    {/* Icon */}
                    <div className={`w-16 h-16 rounded-xl bg-gradient-to-r ${phase.color} p-0.5 mb-6`}>
                      <div className="w-full h-full rounded-xl bg-background flex items-center justify-center">
                        <IconComponent className="h-8 w-8 text-primary" />
                      </div>
                    </div>
                    
                    {/* Content */}
                    <div className="space-y-4">
                      <div>
                        <div className="text-sm font-medium text-primary mb-1">{phase.phase}</div>
                        <h3 className="text-xl font-bold mb-2">{phase.title}</h3>
                        <p className="text-muted-foreground text-sm leading-relaxed">{phase.description}</p>
                      </div>
                      
                      {/* Modules */}
                      <div className="space-y-2">
                        <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Módulos Clave:</div>
                        <div className="flex flex-wrap gap-1">
                          {phase.modules.map((module) => (
                            <span 
                              key={module}
                              className="inline-flex items-center px-2 py-1 rounded-md bg-primary/10 text-primary text-xs font-medium"
                            >
                              {module}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Connection Arrow */}
                  {index < journeyPhases.length - 1 && (
                    <div className="hidden lg:flex absolute top-1/2 -right-4 transform -translate-y-1/2 z-10">
                      <div className="w-8 h-8 rounded-full bg-background border border-primary/30 flex items-center justify-center">
                        <ArrowRight className="h-4 w-4 text-primary" />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Value Proposition */}
        <div className="mt-16 text-center">
          <div className="glass rounded-2xl p-8 max-w-4xl mx-auto">
            <div className="flex items-center justify-center space-x-2 mb-6">
              <Sparkles className="h-6 w-6 text-primary" />
              <h3 className="text-2xl font-bold">El Valor de la Gestión Holística</h3>
              <Sparkles className="h-6 w-6 text-primary" />
            </div>
            
            <p className="text-lg text-muted-foreground mb-6">
              No tratamos a las personas como recursos estáticos. Entendemos que son seres humanos complejos, 
              con motivaciones que evolucionan, contextos que cambian y aspiraciones que se transforman.
            </p>
            
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="space-y-2">
                <div className="text-2xl font-bold text-primary">360°</div>
                <div className="text-sm text-muted-foreground">Visión Integral</div>
              </div>
              <div className="space-y-2">
                <div className="text-2xl font-bold text-primary">∞</div>
                <div className="text-sm text-muted-foreground">Adaptación Continua</div>
              </div>
              <div className="space-y-2">
                <div className="text-2xl font-bold text-primary">❤️</div>
                <div className="text-sm text-muted-foreground">Enfoque Humano</div>
              </div>
            </div>
            
            <Button size="lg" className="bg-gradient-to-r from-huntred-primary to-tech-purple hover:opacity-90">
              <Brain className="mr-2 h-5 w-5" />
              Conocer Nuestra Metodología
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default TalentJourneyOverview;