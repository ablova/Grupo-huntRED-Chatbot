import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowRight, Brain, Database, Zap, Target, Users, FileText, MessageSquare, TrendingUp, Shield } from 'lucide-react';

const MLCapabilitiesSection = () => {
  const mlModules = [
    {
      name: "CVParser",
      description: "Procesamiento estructurado de currículums con IA",
      icon: FileText,
      capabilities: ["Extracción de datos", "Clasificación automática", "Validación de información", "Análisis de skills"],
      color: "bg-blue-500"
    },
    {
      name: "SkillClassifier", 
      description: "Clasificación automática de habilidades técnicas",
      icon: Target,
      capabilities: ["Matching inteligente", "Scoring de aptitudes", "Predicción de éxito", "Recomendaciones"],
      color: "bg-emerald-500"
    },
    {
      name: "MLScraper",
      description: "Extracción robusta de ofertas de empleo",
      icon: Database,
      capabilities: ["Web scraping", "Análisis de mercado", "Trending jobs", "Salary insights"],
      color: "bg-violet-500"
    },
    {
      name: "NLPProcessor",
      description: "Procesamiento de lenguaje natural optimizado",
      icon: MessageSquare,
      capabilities: ["Análisis de sentimiento", "Intent detection", "Contexto conversacional", "Multiidioma"],
      color: "bg-orange-500"
    }
  ];

  const businessModels = [
    {
      bu: "AmigrosModel",
      description: "Optimizado para perfiles técnicos migrantes",
      specialization: "Migración laboral y adaptación cultural",
      icon: Users,
      color: "bg-orange-500"
    },
    {
      bu: "HuntUModel", 
      description: "Especializado en perfiles universitarios",
      specialization: "Talento joven y graduados recientes",
      icon: Brain,
      color: "bg-emerald-500"
    },
    {
      bu: "HuntREDModel",
      description: "Enfocado en mandos medios y altos",
      specialization: "Posiciones gerenciales y especializadas",
      icon: TrendingUp,
      color: "bg-blue-500"
    },
    {
      bu: "ExecutiveModel",
      description: "Para posiciones de dirección y C-level",
      specialization: "Liderazgo ejecutivo y transformación",
      icon: Shield,
      color: "bg-primary"
    }
  ];

  return (
    <section className="py-20 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-16">
          <h2 className="text-3xl md:text-4xl font-bold">
            Capacidades de <span className="text-primary">Machine Learning</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Tecnología de vanguardia que potencia cada proceso de reclutamiento con inteligencia artificial especializada por unidad de negocio
          </p>
        </div>

        {/* ML Core Modules */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {mlModules.map((module, index) => (
            <Card key={index} className="glass border-primary/20 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
              <CardHeader className="text-center">
                <div className={`w-12 h-12 ${module.color} rounded-full flex items-center justify-center text-white mx-auto mb-4`}>
                  <module.icon className="h-6 w-6" />
                </div>
                <CardTitle className="text-lg">{module.name}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground text-center">
                  {module.description}
                </p>
                <div className="space-y-2">
                  {module.capabilities.map((capability, capIndex) => (
                    <div key={capIndex} className="flex items-center space-x-2">
                      <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                      <span className="text-xs">{capability}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Business Unit Models */}
        <div className="space-y-8">
          <div className="text-center space-y-4">
            <h3 className="text-2xl font-bold">Modelos Especializados por Unidad de Negocio</h3>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Cada modelo de ML está entrenado específicamente para las necesidades y características únicas de cada unidad de negocio
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {businessModels.map((model, index) => (
              <Card key={index} className="glass border-primary/20 hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className={`w-12 h-12 ${model.color} rounded-full flex items-center justify-center text-white flex-shrink-0`}>
                      <model.icon className="h-6 w-6" />
                    </div>
                    <div className="flex-1 space-y-2">
                      <h4 className="text-lg font-semibold">{model.bu}</h4>
                      <p className="text-sm text-muted-foreground">{model.description}</p>
                      <div className="flex items-center space-x-2">
                        <Zap className="h-4 w-4 text-primary" />
                        <span className="text-xs font-medium">{model.specialization}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center mt-16">
          <Card className="glass border-primary/20 max-w-3xl mx-auto">
            <CardContent className="p-8 space-y-6">
              <h3 className="text-2xl font-bold">Potencia tu Reclutamiento con IA</h3>
              <p className="text-muted-foreground">
                Descubre cómo nuestros modelos de machine learning pueden transformar tu proceso de selección y encontrar el talento perfecto para tu organización.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="lg" className="bg-primary hover:bg-primary/90">
                  Demo de Capacidades ML
                  <Brain className="ml-2 h-5 w-5" />
                </Button>
                <Button variant="outline" size="lg">
                  Documentación Técnica
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default MLCapabilitiesSection;