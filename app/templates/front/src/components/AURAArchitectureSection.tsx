
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Brain, Network, Zap, Target, Shield, Users, Cog, BarChart3, Gamepad2, MessageSquare, Monitor, ArrowRight, ArrowDown, Layers } from 'lucide-react';

const AURAArchitectureSection = () => {
  const [activeLayer, setActiveLayer] = useState('genia');

  const architectureLayers = [
    {
      id: 'aura',
      name: 'AURA - Capa Superior de Relaciones',
      icon: Network,
      color: 'purple',
      description: 'Sistema de análisis de relaciones y contexto histórico con GNN propia',
      capabilities: [
        'Graph Neural Network especializada en relaciones profesionales',
        'Análisis de momentos históricos y trayectorias',
        'Predicción de capacidades de integración organizacional',
        'Evaluación sofisticada de experiencia y tiempo'
      ]
    },
    {
      id: 'genia',
      name: 'GenIA - Ecosistema de Reclutamiento',
      icon: Brain,
      color: 'blue',
      description: 'ML/NLP/Chatbot/Workflows para procesos de reclutamiento completos',
      capabilities: [
        'Análisis predictivo avanzado con múltiples algoritmos',
        'Redes neuronales para matchmaking inteligente',
        'Analizadores de comportamiento, mercado y personalidad',
        'Workflows automatizados y chatbots conversacionales'
      ]
    },
    {
      id: 'engines',
      name: 'Motores Analíticos Especializados',
      icon: Cog,
      color: 'green',
      description: 'Engines especializados que operan bajo la supervisión de AURA y GenIA',
      capabilities: [
        'Skill Gap Analyzer - Análisis de brechas técnicas y soft skills',
        'Career Simulator - Predicción de trayectorias profesionales',
        'Cultural Fit Analyzer - Compatibilidad organizacional',
        'Market Intelligence - Tendencias y alertas del mercado'
      ]
    },
    {
      id: 'interfaces',
      name: 'Interfaces y Orquestación',
      icon: Monitor,
      color: 'orange',
      description: 'Capa de presentación y coordinación de servicios',
      capabilities: [
        'Dashboards adaptativos por rol y contexto',
        'APIs y integraciones con sistemas externos',
        'Control granular de privacidad y explicabilidad',
        'Interfaces especializadas por unidad de negocio'
      ]
    }
  ];

  const coreModules = [
    {
      name: 'Personalización Dinámica',
      icon: Users,
      description: 'Adapta la experiencia según perfil y contexto',
      features: ['Dashboards adaptativos', 'Widgets personalizados', 'Mensajes contextuales']
    },
    {
      name: 'Upskilling Predictivo',
      icon: Target,
      description: 'Análisis de brechas y simulación de carrera',
      features: ['Gap analysis', 'Simulador de trayectorias', 'Alertas de mercado']
    },
    {
      name: 'Networking Inteligente',
      icon: Network,
      description: 'Conexiones estratégicas automatizadas',
      features: ['Auto-introducciones', 'Event recommender', 'Red expansion analysis']
    },
    {
      name: 'Analytics Ejecutivo',
      icon: BarChart3,
      description: 'KPIs y comparativas sectoriales',
      features: ['Dashboards ejecutivos', 'Sector benchmarking', 'Smart alerts']
    },
    {
      name: 'Gamificación Social',
      icon: Gamepad2,
      description: 'Logros y ranking de impacto profesional',
      features: ['Achievement system', 'Impact ranking', 'Social challenges']
    },
    {
      name: 'IA Generativa',
      icon: MessageSquare,
      description: 'Generación automática de contenido profesional',
      features: ['CV generator', 'Interview simulator', 'Auto summarizer']
    }
  ];

  const getColorClasses = (color: string) => {
    const colors = {
      purple: 'bg-purple-500 text-purple-500 border-purple-200',
      blue: 'bg-blue-500 text-blue-500 border-blue-200',
      green: 'bg-green-500 text-green-500 border-green-200',
      orange: 'bg-orange-500 text-orange-500 border-orange-200'
    };
    return colors[color as keyof typeof colors] || colors.purple;
  };

  return (
    <section className="py-20 bg-background">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-6 mb-16">
          <div className="inline-flex items-center gap-2 bg-tech-gradient/10 rounded-full px-4 py-2 text-sm font-medium">
            <Brain className="w-4 h-4 text-purple-600" />
            Arquitectura en Capas del Sistema
          </div>
          
          <h2 className="text-3xl md:text-4xl font-bold">
            <span className="bg-tech-gradient bg-clip-text text-transparent">Arquitectura en Capas</span>: AURA + GenIA
          </h2>
          
          <p className="text-xl text-muted-foreground max-w-4xl mx-auto">
            Sistema de inteligencia artificial en dos niveles: <strong>GenIA</strong> para el ecosistema completo de reclutamiento 
            y <strong>AURA</strong> como capa superior que analiza relaciones, contexto histórico y capacidades de integración
          </p>
        </div>

        {/* Architecture Overview */}
        <div className="mb-16">
          <h3 className="text-2xl font-bold text-center mb-8">Capas de la Arquitectura</h3>
          <div className="relative">
            {/* Connection Lines */}
            <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-tech-gradient opacity-30 transform -translate-x-1/2 hidden lg:block" />
            
            <div className="space-y-8">
              {architectureLayers.map((layer, index) => (
                <div key={layer.id} className={`flex items-center gap-8 ${index % 2 === 1 ? 'lg:flex-row-reverse' : ''}`}>
                  <div className="flex-1">
                    <Card 
                      className={`glass border-2 cursor-pointer transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${
                        activeLayer === layer.id 
                          ? `border-${layer.color}-400 bg-${layer.color}-50/30 dark:bg-${layer.color}-900/20` 
                          : 'border-border/40'
                      }`}
                      onClick={() => setActiveLayer(layer.id)}
                    >
                      <CardContent className="p-8 space-y-4">
                        <div className="flex items-start gap-4">
                          <div className={`w-12 h-12 rounded-full bg-${layer.color}-500/20 flex items-center justify-center`}>
                            <layer.icon className={`w-6 h-6 text-${layer.color}-600`} />
                          </div>
                          <div className="flex-1">
                            <h3 className="text-xl font-bold mb-2">{layer.name}</h3>
                            <p className="text-muted-foreground mb-4">{layer.description}</p>
                          </div>
                        </div>
                        
                        {activeLayer === layer.id && (
                          <div className="space-y-2 animate-fade-in">
                            {layer.capabilities.map((capability, capIndex) => (
                              <div key={capIndex} className="flex items-start gap-2">
                                <ArrowRight className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                                <span className="text-sm text-muted-foreground">{capability}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>

                  {/* Layer Indicator */}
                  <div className="hidden lg:flex w-16 h-16 rounded-full bg-tech-gradient items-center justify-center text-white font-bold text-xl shadow-lg">
                    {index + 1}
                  </div>

                  <div className="flex-1 hidden lg:block" />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Core Modules Grid */}
        <div className="mb-16">
          <h3 className="text-2xl font-bold text-center mb-8">Módulos Especializados</h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {coreModules.map((module, index) => (
              <Card key={index} className="glass border-primary/20 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-tech-gradient/20 rounded-lg flex items-center justify-center">
                      <module.icon className="w-5 h-5 text-primary" />
                    </div>
                    <span className="text-lg">{module.name}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">{module.description}</p>
                  <div className="space-y-2">
                    {module.features.map((feature, featureIndex) => (
                      <div key={featureIndex} className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                        <span className="text-sm">{feature}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Data Flow Visualization */}
        <Card className="glass border-primary/20 mb-16">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl flex items-center justify-center gap-2">
              <Layers className="w-6 h-6" />
              Flujo de Datos AURA
            </CardTitle>
            <p className="text-muted-foreground">Cómo la información fluye a través de las capas de AURA</p>
          </CardHeader>
          <CardContent className="p-8">
            <div className="flex flex-col lg:flex-row items-center justify-between space-y-8 lg:space-y-0 lg:space-x-8">
              <div className="text-center space-y-4">
                <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto">
                  <Users className="w-8 h-8 text-blue-600" />
                </div>
                <h4 className="font-semibold">Datos de Usuario</h4>
                <p className="text-sm text-muted-foreground">Perfiles, skills, trayectorias</p>
              </div>
              
              <ArrowRight className="w-6 h-6 text-primary hidden lg:block" />
              <ArrowDown className="w-6 h-6 text-primary lg:hidden" />
              
              <div className="text-center space-y-4">
                <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto">
                  <Network className="w-8 h-8 text-purple-600" />
                </div>
                <h4 className="font-semibold">Graph Neural Network</h4>
                <p className="text-sm text-muted-foreground">Análisis de relaciones y contexto</p>
              </div>
              
              <ArrowRight className="w-6 h-6 text-primary hidden lg:block" />
              <ArrowDown className="w-6 h-6 text-primary lg:hidden" />
              
              <div className="text-center space-y-4">
                <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto">
                  <Brain className="w-8 h-8 text-green-600" />
                </div>
                <h4 className="font-semibold">Motores de IA</h4>
                <p className="text-sm text-muted-foreground">Análisis y predicciones</p>
              </div>
              
              <ArrowRight className="w-6 h-6 text-primary hidden lg:block" />
              <ArrowDown className="w-6 h-6 text-primary lg:hidden" />
              
              <div className="text-center space-y-4">
                <div className="w-16 h-16 bg-orange-500/20 rounded-full flex items-center justify-center mx-auto">
                  <Monitor className="w-8 h-8 text-orange-600" />
                </div>
                <h4 className="font-semibold">Interfaces</h4>
                <p className="text-sm text-muted-foreground">Dashboards personalizados</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Value Proposition */}
        <Card className="glass border-tech-gradient bg-gradient-to-r from-purple-50/50 to-blue-50/50 dark:from-purple-900/10 dark:to-blue-900/10">
          <CardContent className="p-8 text-center space-y-6">
            <h3 className="text-3xl font-bold">El Poder de AURA en Números</h3>
            <div className="grid md:grid-cols-4 gap-6 mt-8">
              <div className="space-y-2">
                <div className="text-3xl font-bold text-purple-600">94%</div>
                <div className="text-sm font-medium">Precisión Predictiva</div>
                <div className="text-xs text-muted-foreground">vs 67% métodos tradicionales</div>
              </div>
              <div className="space-y-2">
                <div className="text-3xl font-bold text-blue-600">45%</div>
                <div className="text-sm font-medium">Reducción de Tiempo</div>
                <div className="text-xs text-muted-foreground">En procesos de selección</div>
              </div>
              <div className="space-y-2">
                <div className="text-3xl font-bold text-green-600">340%</div>
                <div className="text-sm font-medium">ROI Mejorado</div>
                <div className="text-xs text-muted-foreground">Retorno de inversión</div>
              </div>
              <div className="space-y-2">
                <div className="text-3xl font-bold text-orange-600">2.3M</div>
                <div className="text-sm font-medium">Nodos en Red</div>
                <div className="text-xs text-muted-foreground">Conexiones analizadas</div>
              </div>
            </div>
            <div className="pt-6 border-t">
              <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
                AURA no solo optimiza procesos, sino que <strong>reinventa completamente</strong> cómo entendemos, 
                conectamos y desarrollamos el talento en el ecosistema profesional.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
};

export default AURAArchitectureSection;
