import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
const TechnologySection = () => {
  const [activeTab, setActiveTab] = useState(0);
  const technologies = [{
    title: "Natural Language Processing",
    description: "Procesamiento avanzado de lenguaje natural con modelos transformer de última generación",
    features: ["Análisis de sentimientos", "Generación de texto", "Traducción automática", "Chatbots conversacionales"],
    image: "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80",
    color: "tech-blue"
  }, {
    title: "Matchmaking Inteligente",
    description: "Comprensión profunda de capacidades, skills, soft skills, idiomas, experiencia, sentimiento y ubicación",
    features: ["Skills Técnicos", "Soft Skills", "Idiomas", "Experiencia", "Sentimiento", "Ubicación", "Cultura", "Personalidad", "Mercado"],
    image: "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80",
    color: "tech-purple"
  }, {
    title: "Predictive Analytics",
    description: "Algoritmos de machine learning para predicción y optimización de procesos empresariales",
    features: ["Forecasting", "Detección de anomalías", "Optimización", "Business Intelligence"],
    image: "https://images.unsplash.com/photo-1498050108023-c5249f4df085?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80",
    color: "tech-cyan"
  }];
  return <section id="technology" className="py-20 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-16">
          <h2 className="text-3xl md:text-4xl font-bold">
            Tecnologías de <span className="bg-tech-gradient bg-clip-text text-transparent">Vanguardia</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">GenIA es la capa de comprensión y ejecución del proceso de reclutamiento, donde sucede la magia del Conversational AI, la asignación de oportunidades y la ejecución de los flujos de trabajo para lograr la colocación.</p>
        </div>

        {/* Technology Tabs */}
        <div className="flex flex-wrap justify-center gap-4 mb-12">
          {technologies.map((tech, index) => <button key={index} onClick={() => setActiveTab(index)} className={`px-6 py-3 rounded-full font-medium transition-all ${activeTab === index ? 'bg-tech-gradient text-white shadow-lg' : 'bg-card hover:bg-muted text-muted-foreground hover:text-foreground'}`}>
              {tech.title}
            </button>)}
        </div>

        {/* Active Technology Display */}
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6 animate-fade-in-up">
            <div className="space-y-4">
              <h3 className="text-2xl md:text-3xl font-bold">
                {technologies[activeTab].title}
              </h3>
              <p className="text-lg text-muted-foreground">
                {technologies[activeTab].description}
              </p>
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              {technologies[activeTab].features.map((feature, index) => <div key={index} className="flex items-center space-x-3">
                  <div className={`w-2 h-2 bg-${technologies[activeTab].color} rounded-full`} />
                  <span className="text-sm font-medium">{feature}</span>
                </div>)}
            </div>

            {/* Performance Metrics */}
            <div className="grid grid-cols-3 gap-6 pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold bg-tech-gradient bg-clip-text text-transparent">99.9%</div>
                <div className="text-sm text-muted-foreground">Precisión</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold bg-tech-gradient bg-clip-text text-transparent">&lt;100ms</div>
                <div className="text-sm text-muted-foreground">Latencia</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold bg-tech-gradient bg-clip-text text-transparent">24/7</div>
                <div className="text-sm text-muted-foreground">Disponibilidad</div>
              </div>
            </div>
          </div>

          <div className="relative animate-slide-in-right">
            <Card className="overflow-hidden border-0 shadow-2xl">
              <CardContent className="p-0">
                <div className="relative h-[400px]">
                  <img src={technologies[activeTab].image} alt={technologies[activeTab].title} className="w-full h-full object-cover transition-transform duration-500 hover:scale-105" />
                  <div className="absolute inset-0 bg-tech-gradient/30" />
                  
                  {/* Tech Overlay */}
                  <div className="absolute top-4 left-4 glass rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                      <span className="text-sm font-medium">{technologies[activeTab].title}</span>
                    </div>
                  </div>

                  {/* Floating Elements */}
                  <div className="absolute bottom-4 right-4 space-y-2">
                    {technologies[activeTab].features.slice(0, 2).map((feature, index) => <div key={index} className="glass rounded-lg px-3 py-1">
                        <span className="text-sm">{feature}</span>
                      </div>)}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Floating Stats */}
            <div className="absolute -top-6 -right-6 glass rounded-xl p-4 animate-float">
              <div className="text-center">
                <div className="text-xl font-bold text-primary">AI</div>
                <div className="text-xs text-muted-foreground">Powered</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>;
};
export default TechnologySection;