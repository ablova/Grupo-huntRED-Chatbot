
import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Brain, Zap, Eye, MessageCircle, Code, Sparkles } from 'lucide-react';

const LLMCapabilitiesSection = () => {
  const [activeCapability, setActiveCapability] = useState(0);
  const [neuralPulse, setNeuralPulse] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setNeuralPulse(prev => (prev + 1) % 100);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  const capabilities = [
    {
      icon: Brain,
      title: "Neural Language Understanding",
      description: "Comprensión profunda del lenguaje humano con contexto semántico avanzado",
      metrics: ["99.8% Precisión", "150+ Idiomas", "Tiempo Real"],
      color: "from-blue-500 to-purple-600",
      glow: "shadow-blue-500/50"
    },
    {
      icon: MessageCircle,
      title: "Conversational AI",
      description: "Diálogos naturales con memoria contextual y personalidad adaptable",
      metrics: ["Memoria 128K", "Contexto Infinito", "Multimodal"],
      color: "from-purple-500 to-pink-600",
      glow: "shadow-purple-500/50"
    },
    {
      icon: Code,
      title: "Skill Taxonomy & Gap Analysis",
      description: "Indexación de habilidades e identificacion de brechas con sistema de aprendizaje automático",
      metrics: ["43000+ Habilidades", "Auto-Indexación", "Plan de Carrera"],
      color: "from-green-500 to-blue-600",
      glow: "shadow-green-500/50"
    },
    {
      icon: Eye,
      title: "Vision & Analysis",
      description: "Análisis visual avanzado con comprensión de contexto y objetivos de carrera",
      metrics: ["4K Resolution", "OCR Avanzado", "Análisis Scene"],
      color: "from-orange-500 to-red-600",
      glow: "shadow-orange-500/50"
    },
    {
      icon: Zap,
      title: "Real-time Processing",
      description: "Procesamiento en tiempo real con latencia ultra-baja",
      metrics: ["<10ms Latencia", "Escalable", "Edge Computing"],
      color: "from-cyan-500 to-blue-600",
      glow: "shadow-cyan-500/50"
    },
    {
      icon: Sparkles,
      title: "Recomendaciones de Carrera",
      description: "Recomendaciones de carrera basadas en habilidades y objetivos de carrera",
      metrics: ["Arte Digital", "Música", "Video"],
      color: "from-pink-500 to-purple-600",
      glow: "shadow-pink-500/50"
    }
  ];

  return (
    <section className="py-20 bg-gradient-to-b from-background to-muted/30 relative overflow-hidden">
      {/* Neural Background Animation */}
      <div className="absolute inset-0 opacity-10">
        <div className="neural-network-bg"></div>
      </div>
      
      {/* Floating Neural Particles */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-primary rounded-full animate-neural-spark"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${3 + Math.random() * 2}s`
            }}
          />
        ))}
      </div>

      <div className="container mx-auto px-4 lg:px-8 relative z-10">
        <div className="text-center space-y-4 mb-16">
          <h2 className="text-4xl md:text-5xl font-bold">
            <span className="bg-tech-gradient bg-clip-text text-transparent">Artificial Understanding & Recruitment Assistant</span> AURA
          </h2>
          <p className="text-xl text-muted-foreground max-w-4xl mx-auto">
            Capacidades de IA de próxima generación que redefinen los límites de lo posible
          </p>
        </div>

        {/* Neural Grid */}
        <div className="grid md:grid-cols-3 lg:grid-cols-6 gap-6 mb-16">
          {capabilities.map((capability, index) => {
            const Icon = capability.icon;
            const isActive = activeCapability === index;
            
            return (
              <Card
                key={index}
                className={`group cursor-pointer transition-all duration-500 hover:scale-105 border-0 ${
                  isActive ? `shadow-2xl ${capability.glow}` : 'hover:shadow-xl'
                } neural-connection`}
                onClick={() => setActiveCapability(index)}
              >
                <CardContent className="p-6 text-center">
                  <div className={`relative mx-auto w-16 h-16 mb-4 rounded-xl bg-gradient-to-r ${capability.color} flex items-center justify-center ${
                    isActive ? 'animate-quantum-pulse' : ''
                  }`}>
                    <Icon className="w-8 h-8 text-white" />
                    {isActive && (
                      <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-white/20 to-transparent animate-pulse" />
                    )}
                  </div>
                  <h3 className="font-bold text-sm mb-2">{capability.title}</h3>
                  <div className="space-y-1">
                    {capability.metrics.map((metric, i) => (
                      <div key={i} className="text-xs text-muted-foreground">{metric}</div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Active Capability Detail */}
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6 animate-fade-in-up">
            <div className="space-y-4">
              <div className={`inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-gradient-to-r ${capabilities[activeCapability].color} text-white`}>
                {React.createElement(capabilities[activeCapability].icon, { className: "w-4 h-4" })}
                <span className="text-sm font-medium">Neural Network</span>
              </div>
              <h3 className="text-3xl md:text-4xl font-bold">
                {capabilities[activeCapability].title}
              </h3>
              <p className="text-lg text-muted-foreground">
                {capabilities[activeCapability].description}
              </p>
            </div>

            {/* Neural Processing Simulation */}
            <div className="glass rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Neural Processing</span>
                <span className="text-xs text-muted-foreground">Real-time</span>
              </div>
              
              <div className="space-y-3">
                {['Input Layer', 'Hidden Layers', 'Output Layer'].map((layer, i) => (
                  <div key={i} className="flex items-center space-x-3">
                    <div className="w-3 h-3 rounded-full bg-primary animate-pulse" />
                    <div className="flex-1 bg-muted rounded-full h-2 overflow-hidden">
                      <div 
                        className={`h-full bg-gradient-to-r ${capabilities[activeCapability].color} transition-all duration-1000`}
                        style={{ width: `${70 + (neuralPulse / 100) * 30}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">{layer}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="grid grid-cols-3 gap-4">
              {capabilities[activeCapability].metrics.map((metric, i) => (
                <div key={i} className="text-center p-4 glass rounded-lg">
                  <div className={`text-xl font-bold bg-gradient-to-r ${capabilities[activeCapability].color} bg-clip-text text-transparent`}>
                    {metric.split(' ')[0]}
                  </div>
                  <div className="text-xs text-muted-foreground">{metric.split(' ').slice(1).join(' ')}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Neural Visualization */}
          <div className="relative">
            <div className="glass rounded-2xl p-8 relative overflow-hidden">
              {/* Neural Network Visualization */}
              <div className="relative h-80 flex items-center justify-center">
                <div className="absolute inset-0 neural-network opacity-30"></div>
                
                {/* Central Processing Unit */}
                <div className={`relative w-24 h-24 rounded-full bg-gradient-to-r ${capabilities[activeCapability].color} flex items-center justify-center animate-quantum-pulse`}>
                  {React.createElement(capabilities[activeCapability].icon, { className: "w-12 h-12 text-white" })}
                  
                  {/* Neural Connections */}
                  {[...Array(8)].map((_, i) => (
                    <div
                      key={i}
                      className="absolute w-px h-16 bg-gradient-to-t from-primary to-transparent origin-bottom"
                      style={{
                        transform: `rotate(${i * 45}deg)`,
                        transformOrigin: 'center bottom'
                      }}
                    />
                  ))}
                </div>

                {/* Orbiting Nodes */}
                {[...Array(6)].map((_, i) => (
                  <div
                    key={i}
                    className="absolute w-4 h-4 bg-primary rounded-full animate-spin-slow"
                    style={{
                      left: `${50 + 35 * Math.cos((i * 60) * Math.PI / 180)}%`,
                      top: `${50 + 35 * Math.sin((i * 60) * Math.PI / 180)}%`,
                      animationDelay: `${i * 0.5}s`,
                      animationDuration: '10s'
                    }}
                  />
                ))}
              </div>

              {/* Real-time Metrics */}
              <div className="absolute top-4 right-4 glass rounded-lg p-3">
                <div className="text-xs text-muted-foreground mb-1">Neural Activity</div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-sm font-medium">Active</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Live Demo Section */}
        <div className="mt-16 glass rounded-2xl p-8">
          <div className="text-center mb-8">
            <h3 className="text-2xl font-bold mb-4">Demostración en Vivo</h3>
            <p className="text-muted-foreground">Experimenta nuestras capacidades de IA en tus procesos de reclutamiento de manera real</p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <MessageCircle className="w-5 h-5 text-primary" />
                <span className="font-medium">Chat con Conversación AI</span>
              </div>
              
              <div className="bg-muted/50 rounded-lg p-4 h-48 overflow-hidden relative">
                <div className="space-y-3">
                  <div className="bg-primary/10 rounded-lg p-3 ml-8">
                    <p className="text-sm">¿Cómo puede la IA transformar mi negocio?</p>
                  </div>
                  <div className="bg-primary rounded-lg p-3 mr-8 text-primary-foreground">
                    <p className="text-sm">Analizando tu industria y datos, puedo identificar oportunidades de automatización que incrementarían tu eficiencia en un 40-60%...</p>
                  </div>
                </div>
                
                <div className="absolute bottom-2 left-2 flex items-center space-x-2 text-xs text-muted-foreground">
                  <div className="w-1 h-1 bg-green-400 rounded-full animate-pulse" />
                  <span>IA escribiendo...</span>
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <Brain className="w-5 h-5 text-primary" />
                <span className="font-medium">Análisis Neural Constante</span>
              </div>
              
              <div className="space-y-2">
                {['Sentiment Analysis', 'Entity Recognition', 'Intent Classification'].map((analysis, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <span className="text-sm">{analysis}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-12 h-1 bg-muted rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-primary transition-all duration-2000"
                          style={{ width: `${85 + Math.sin(Date.now() / 1000 + i) * 15}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {Math.floor(85 + Math.sin(Date.now() / 1000 + i) * 15)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default LLMCapabilitiesSection;
