
import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowRight, Brain, MessageSquare, Target, Users, Zap, Database, User } from 'lucide-react';

const AIFlowsSection = () => {
  const conversationalFlow = {
    title: "IA Conversacional",
    description: "Interacción natural con candidatos y clientes",
    color: "tech-blue",
    icon: MessageSquare,
    steps: [
      {
        name: "Chatbot Inicial",
        description: "Primera interacción con el candidato",
        details: ["Recolección de datos básicos", "Evaluación de interés", "Programación automática"]
      },
      {
        name: "Entrevista Virtual",
        description: "Conversación estructurada con IA",
        details: ["Análisis de respuestas en tiempo real", "Evaluación de soft skills", "Feedback inmediato"]
      },
      {
        name: "Seguimiento",
        description: "Comunicación continua personalizada",
        details: ["Updates automáticos", "Recordatorios inteligentes", "Respuesta 24/7"]
      }
    ]
  };

  const mlFlow = {
    title: "ML/NLP Processing",
    description: "Análisis predictivo y comprensión profunda",
    color: "tech-purple",
    icon: Brain,
    steps: [
      {
        name: "Análisis de CV",
        description: "Extracción inteligente de información",
        details: ["Parsing avanzado de documentos", "Identificación de skills", "Experiencia relevante"]
      },
      {
        name: "Scoring Predictivo",
        description: "Evaluación de compatibilidad",
        details: ["Algoritmos de matching", "Predicción de éxito", "Análisis de personalidad"]
      },
      {
        name: "Recomendaciones",
        description: "Insights accionables para el cliente",
        details: ["Ranking de candidatos", "Áreas de mejora", "Predicción de retención"]
      }
    ]
  };

  const layers = [
    {
      name: "Capa de Interacción",
      description: "Interfaces conversacionales y experiencia de usuario",
      technologies: ["React Dashboard", "WhatsApp API", "Voice Assistant", "Mobile App"],
      gradient: "from-blue-500 to-cyan-500"
    },
    {
      name: "Capa de Procesamiento IA",
      description: "Motores de IA conversacional y análisis de ML/NLP",
      technologies: ["GPT-4", "BERT", "Custom NLP Models", "Speech Recognition"],
      gradient: "from-purple-500 to-pink-500"
    },
    {
      name: "Capa de Datos y ML",
      description: "Almacenamiento, procesamiento y modelos predictivos",
      technologies: ["PostgreSQL", "Redis", "TensorFlow", "Scikit-learn"],
      gradient: "from-green-500 to-emerald-500"
    },
    {
      name: "Capa de Integración",
      description: "APIs y conectores con sistemas empresariales",
      technologies: ["REST API", "GraphQL", "SAP Connector", "Workday API"],
      gradient: "from-orange-500 to-red-500"
    }
  ];

  return (
    <section className="py-20 bg-background">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-16">
          <h2 className="text-3xl md:text-4xl font-bold">
            Flujos de <span className="bg-tech-gradient bg-clip-text text-transparent">Inteligencia Artificial</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Dos corrientes tecnológicas que trabajan en paralelo para ofrecer la mejor experiencia de reclutamiento - GenIA & AURA
          </p>
        </div>

        {/* Flujos Paralelos con figura humana en el centro */}
        <div className="relative mb-16">
          <div className="grid lg:grid-cols-2 gap-8">
            {[conversationalFlow, mlFlow].map((flow, flowIndex) => (
              <Card key={flowIndex} className="glass border-primary/20 relative overflow-hidden">
                <div className={`absolute top-0 left-0 w-full h-1 bg-${flow.color}`} />
                <CardContent className="p-8 space-y-6">
                  <div className="flex items-center space-x-4">
                    <div className={`w-12 h-12 bg-${flow.color}/20 rounded-full flex items-center justify-center`}>
                      <flow.icon className={`w-6 h-6 text-${flow.color}`} />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold">{flow.title}</h3>
                      <p className="text-muted-foreground">{flow.description}</p>
                    </div>
                  </div>

                  <div className="space-y-6">
                    {flow.steps.map((step, stepIndex) => (
                      <div key={stepIndex} className="relative">
                        <div className="flex items-start space-x-4">
                          <div className={`w-8 h-8 bg-${flow.color}/20 rounded-full flex items-center justify-center flex-shrink-0 mt-1`}>
                            <span className={`text-sm font-bold text-${flow.color}`}>{stepIndex + 1}</span>
                          </div>
                          <div className="space-y-2 flex-1">
                            <h4 className="font-semibold">{step.name}</h4>
                            <p className="text-sm text-muted-foreground">{step.description}</p>
                            <div className="grid gap-1">
                              {step.details.map((detail, detailIndex) => (
                                <div key={detailIndex} className="flex items-center space-x-2">
                                  <div className={`w-1 h-1 rounded-full bg-${flow.color}`} />
                                  <span className="text-xs text-muted-foreground">{detail}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                        {stepIndex < flow.steps.length - 1 && (
                          <div className="ml-4 mt-2 h-4 w-0.5 bg-muted" />
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Figura humana en el centro */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="glass rounded-full p-8 border-4 border-primary/30 bg-background/80 backdrop-blur-md">
              <div className="text-center space-y-2">
                <User className="w-12 h-12 text-primary mx-auto" />
                <div className="text-sm font-bold text-primary">CANDIDATO</div>
                <div className="text-xs text-muted-foreground">Al centro del proceso</div>
              </div>
            </div>
          </div>

          {/* Flechas que apuntan al centro */}
          <div className="absolute left-1/4 top-1/2 transform -translate-y-1/2 pointer-events-none">
            <ArrowRight className="w-8 h-8 text-blue-500 animate-pulse" />
          </div>
          <div className="absolute right-1/4 top-1/2 transform -translate-y-1/2 rotate-180 pointer-events-none">
            <ArrowRight className="w-8 h-8 text-purple-500 animate-pulse" />
          </div>
        </div>

        {/* Arquitectura en Capas */}
        <div className="space-y-8">
          <div className="text-center space-y-2">
            <h3 className="text-2xl font-bold">Arquitectura en Capas</h3>
            <p className="text-muted-foreground">Infraestructura robusta que soporta ambos flujos de IA</p>
          </div>

          <div className="relative space-y-4">
            {layers.map((layer, index) => (
              <Card
                key={index}
                className="glass border-primary/20 relative overflow-hidden transform transition-all duration-300 hover:scale-105"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r ${layer.gradient}`} />
                <CardContent className="p-6">
                  <div className="grid md:grid-cols-3 gap-6 items-center">
                    <div className="space-y-2">
                      <h4 className="text-lg font-bold">{layer.name}</h4>
                      <p className="text-muted-foreground text-sm">{layer.description}</p>
                    </div>
                    
                    <div className="md:col-span-2">
                      <div className="flex flex-wrap gap-2">
                        {layer.technologies.map((tech, techIndex) => (
                          <span
                            key={techIndex}
                            className="glass rounded-full px-3 py-1 text-sm font-medium border border-primary/20"
                          >
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Indicadores de Conexión */}
          <div className="flex justify-center space-x-8 pt-8">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-tech-blue rounded-full animate-pulse" />
              <span className="text-sm text-muted-foreground">IA Conversacional</span>
            </div>
            <ArrowRight className="w-5 h-5 text-muted-foreground" />
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-tech-purple rounded-full animate-pulse" />
              <span className="text-sm text-muted-foreground">ML/NLP Processing</span>
            </div>
            <ArrowRight className="w-5 h-5 text-muted-foreground" />
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm text-muted-foreground">Insights Cliente</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AIFlowsSection;
