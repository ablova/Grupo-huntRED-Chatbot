
import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowRight, ArrowLeft } from 'lucide-react';

const MLFlowsSection = () => {
  const flows = [
    {
      title: "Flujo de Entrada",
      description: "Ingesta y procesamiento de datos en tiempo real",
      steps: ["Captura de Datos", "Validación", "Normalización", "Enriquecimiento"],
      direction: "right",
      color: "tech-blue"
    },
    {
      title: "Flujo de Procesamiento",
      description: "Análisis y transformación mediante algoritmos de ML",
      steps: ["Feature Engineering", "Model Training", "Validación", "Optimización"],
      direction: "left",
      color: "tech-purple"
    }
  ];

  const layers = [
    {
      name: "Capa de Presentación",
      description: "Interfaces de usuario y APIs",
      technologies: ["React", "REST API", "GraphQL", "Mobile Apps"],
      position: "top"
    },
    {
      name: "Capa de Machine Learning",
      description: "Modelos de IA y procesamiento inteligente",
      technologies: ["TensorFlow", "PyTorch", "Scikit-learn", "Custom Models"],
      position: "middle"
    },
    {
      name: "Sistemas Centrales",
      description: "Infraestructura y gestión de datos",
      technologies: ["Kubernetes", "Docker", "PostgreSQL", "Redis"],
      position: "bottom"
    }
  ];

  return (
    <section id="ml-flows" className="py-20 bg-background">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-16">
          <h2 className="text-3xl md:text-4xl font-bold">
            Arquitectura de <span className="bg-tech-gradient bg-clip-text text-transparent">Machine Learning</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Flujos bidireccionales y recurrentes que optimizan el procesamiento de datos en tiempo real
          </p>
        </div>

        {/* Parallel Flows */}
        <div className="space-y-12 mb-20">
          {flows.map((flow, index) => (
            <div key={index} className={`flex items-center ${flow.direction === 'left' ? 'flex-row-reverse' : ''}`}>
              <div className="flex-1">
                <Card className="glass border-primary/20">
                  <CardContent className="p-6">
                    <div className="space-y-4">
                      <div className="flex items-center space-x-3">
                        <div className={`w-3 h-3 bg-${flow.color} rounded-full`} />
                        <h3 className="text-xl font-bold">{flow.title}</h3>
                      </div>
                      <p className="text-muted-foreground">{flow.description}</p>
                      
                      <div className={`flex items-center space-x-4 ${flow.direction === 'left' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                        {flow.steps.map((step, stepIndex) => (
                          <React.Fragment key={stepIndex}>
                            <div className="glass rounded-lg px-3 py-2 text-sm font-medium">
                              {step}
                            </div>
                            {stepIndex < flow.steps.length - 1 && (
                              flow.direction === 'right' ? 
                                <ArrowRight className="h-4 w-4 text-primary" /> :
                                <ArrowLeft className="h-4 w-4 text-primary" />
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
              
              <div className="px-8">
                <div className={`w-12 h-12 bg-${flow.color}/20 rounded-full flex items-center justify-center animate-pulse-slow`}>
                  {flow.direction === 'right' ? 
                    <ArrowRight className={`h-6 w-6 text-${flow.color}`} /> :
                    <ArrowLeft className={`h-6 w-6 text-${flow.color}`} />
                  }
                </div>
              </div>
              
              <div className="flex-1" />
            </div>
          ))}
        </div>

        {/* Architecture Layers */}
        <div className="space-y-6">
          <h3 className="text-2xl font-bold text-center mb-8">Arquitectura en Capas</h3>
          
          <div className="relative space-y-4">
            {layers.map((layer, index) => (
              <Card key={index} className={`glass border-primary/20 transform transition-all duration-300 hover:scale-105 ${
                layer.position === 'top' ? 'animate-slide-in-right' :
                layer.position === 'middle' ? 'animate-fade-in-up' :
                'animate-slide-in-left'
              }`} style={{ animationDelay: `${index * 0.2}s` }}>
                <CardContent className="p-6">
                  <div className="grid md:grid-cols-3 gap-6 items-center">
                    <div className="space-y-2">
                      <h4 className="text-lg font-bold">{layer.name}</h4>
                      <p className="text-muted-foreground text-sm">{layer.description}</p>
                    </div>
                    
                    <div className="md:col-span-2">
                      <div className="flex flex-wrap gap-2">
                        {layer.technologies.map((tech, techIndex) => (
                          <span key={techIndex} className="glass rounded-full px-3 py-1 text-sm font-medium">
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            
            {/* Connection Lines */}
            <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-tech-gradient opacity-30 transform -translate-x-1/2" />
            
            {/* Layer Connectors */}
            {layers.map((_, index) => (
              index < layers.length - 1 && (
                <div key={index} className="absolute left-1/2 w-3 h-3 bg-primary rounded-full transform -translate-x-1/2 animate-pulse" 
                     style={{ top: `${(index + 1) * 33.33}%` }} />
              )
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default MLFlowsSection;
