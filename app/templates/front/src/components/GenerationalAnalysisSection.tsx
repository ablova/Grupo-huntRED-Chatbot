import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Users, 
  TrendingUp, 
  Brain, 
  Target, 
  Heart, 
  Zap,
  BarChart3,
  PieChart,
  Activity,
  Sparkles,
  UserCheck,
  Award,
  ChevronRight
} from 'lucide-react';

const GenerationalAnalysisSection = () => {
  const [selectedGeneration, setSelectedGeneration] = useState('millennial');

  const generations = [
    {
      id: 'gen-z',
      name: 'Gen Z',
      range: '1997-2012',
      color: 'from-tech-purple to-tech-cyan',
      icon: Sparkles,
      population: '32%',
      traits: ['Digital Native', 'Entrepreneurial', 'Socially Conscious', 'Flexible']
    },
    {
      id: 'millennial',
      name: 'Millennial',
      range: '1981-1996',
      color: 'from-tech-blue to-tech-purple',
      icon: Users,
      population: '38%',
      traits: ['Tech-Savvy', 'Purpose-Driven', 'Collaborative', 'Growth-Oriented']
    },
    {
      id: 'gen-x',
      name: 'Gen X',
      range: '1965-1980',
      color: 'from-tech-cyan to-tech-purple',
      icon: Target,
      population: '24%',
      traits: ['Independent', 'Pragmatic', 'Balanced', 'Results-Focused']
    },
    {
      id: 'boomer',
      name: 'Baby Boomer',
      range: '1946-1964',
      color: 'from-tech-purple to-tech-blue',
      icon: Award,
      population: '6%',
      traits: ['Experienced', 'Loyal', 'Hierarchical', 'Stable']
    }
  ];

  const analysisData = {
    'millennial': {
      motivators: [
        { name: 'Crecimiento Profesional', value: 92, color: 'tech-blue' },
        { name: 'Propósito y Significado', value: 88, color: 'tech-purple' },
        { name: 'Work-Life Balance', value: 85, color: 'tech-cyan' },
        { name: 'Flexibilidad', value: 81, color: 'tech-blue' }
      ],
      interests: [
        { name: 'Tecnología', percentage: 76 },
        { name: 'Sostenibilidad', percentage: 68 },
        { name: 'Innovación', percentage: 72 },
        { name: 'Diversidad', percentage: 64 }
      ],
      skills: [
        { name: 'Habilidades Digitales', level: 'Avanzado', progress: 85 },
        { name: 'Colaboración', level: 'Experto', progress: 92 },
        { name: 'Adaptabilidad', level: 'Avanzado', progress: 78 },
        { name: 'Liderazgo', level: 'Intermedio', progress: 68 }
      ],
      predictions: [
        { metric: 'Retención', value: '89%', trend: 'up' },
        { metric: 'Productividad', value: '94%', trend: 'up' },
        { metric: 'Compromiso', value: '87%', trend: 'stable' },
        { metric: 'Rotación', value: '12%', trend: 'down' }
      ]
    },
    'gen-z': {
      motivators: [
        { name: 'Impacto Social', value: 94, color: 'tech-purple' },
        { name: 'Flexibilidad Total', value: 91, color: 'tech-cyan' },
        { name: 'Aprendizaje Continuo', value: 87, color: 'tech-blue' },
        { name: 'Autenticidad', value: 84, color: 'tech-purple' }
      ],
      interests: [
        { name: 'Emprendimiento', percentage: 82 },
        { name: 'Cambio Social', percentage: 78 },
        { name: 'Creatividad', percentage: 75 },
        { name: 'Gig Economy', percentage: 69 }
      ],
      skills: [
        { name: 'Innovación Digital', level: 'Experto', progress: 95 },
        { name: 'Multitasking', level: 'Avanzado', progress: 88 },
        { name: 'Creatividad', level: 'Avanzado', progress: 82 },
        { name: 'Comunicación Digital', level: 'Experto', progress: 91 }
      ],
      predictions: [
        { metric: 'Retención', value: '76%', trend: 'up' },
        { metric: 'Productividad', value: '91%', trend: 'up' },
        { metric: 'Compromiso', value: '83%', trend: 'up' },
        { metric: 'Rotación', value: '24%', trend: 'down' }
      ]
    },
    'gen-x': {
      motivators: [
        { name: 'Estabilidad', value: 90, color: 'huntred-primary' },
        { name: 'Autonomía', value: 88, color: 'tech-blue' },
        { name: 'Reconocimiento', value: 82, color: 'tech-red' },
        { name: 'Desarrollo', value: 78, color: 'tech-purple' }
      ],
      interests: [
        { name: 'Liderazgo', percentage: 84 },
        { name: 'Mentoría', percentage: 77 },
        { name: 'Estrategia', percentage: 81 },
        { name: 'Eficiencia', percentage: 88 }
      ],
      skills: [
        { name: 'Gestión', level: 'Experto', progress: 92 },
        { name: 'Resolución de Problemas', level: 'Experto', progress: 89 },
        { name: 'Comunicación', level: 'Avanzado', progress: 85 },
        { name: 'Toma de Decisiones', level: 'Experto', progress: 94 }
      ],
      predictions: [
        { metric: 'Retención', value: '95%', trend: 'stable' },
        { metric: 'Productividad', value: '96%', trend: 'up' },
        { metric: 'Compromiso', value: '91%', trend: 'stable' },
        { metric: 'Rotación', value: '5%', trend: 'stable' }
      ]
    },
    'boomer': {
      motivators: [
        { name: 'Respeto y Reconocimiento', value: 95, color: 'tech-red' },
        { name: 'Estabilidad', value: 93, color: 'huntred-primary' },
        { name: 'Mentoría', value: 87, color: 'tech-blue' },
        { name: 'Legado', value: 84, color: 'tech-purple' }
      ],
      interests: [
        { name: 'Transmisión de Conocimiento', percentage: 91 },
        { name: 'Estabilidad Organizacional', percentage: 89 },
        { name: 'Calidad sobre Cantidad', percentage: 85 },
        { name: 'Estructura', percentage: 82 }
      ],
      skills: [
        { name: 'Experiencia', level: 'Maestro', progress: 98 },
        { name: 'Sabiduría', level: 'Maestro', progress: 96 },
        { name: 'Mentoría', level: 'Experto', progress: 94 },
        { name: 'Perspectiva', level: 'Experto', progress: 92 }
      ],
      predictions: [
        { metric: 'Retención', value: '98%', trend: 'stable' },
        { metric: 'Productividad', value: '93%', trend: 'stable' },
        { metric: 'Compromiso', value: '96%', trend: 'up' },
        { metric: 'Rotación', value: '2%', trend: 'stable' }
      ]
    }
  };

  const currentData = analysisData[selectedGeneration];
  const currentGeneration = generations.find(g => g.id === selectedGeneration);

  return (
    <section className="py-20 bg-gradient-to-br from-background via-background/80 to-background/60">
      <div className="container mx-auto px-4 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center space-x-2 glass rounded-full px-4 py-2 border border-primary/20 mb-6">
            <Brain className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">ANÁLISIS GENERACIONAL</span>
          </div>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-6">
            Comprende a <span className="bg-gradient-to-r from-huntred-primary to-tech-blue bg-clip-text text-transparent">Cada Generación</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Nuestra IA analiza patrones generacionales para predecir comportamientos, identificar motivadores únicos y personalizar estrategias de talento granulares para cada perfil demográfico.
          </p>
        </div>

        {/* Generation Selector */}
        <div className="grid md:grid-cols-4 gap-4 mb-12">
          {generations.map((gen) => {
            const IconComponent = gen.icon;
            return (
              <Card 
                key={gen.id}
                className={`cursor-pointer transition-all duration-300 hover:scale-105 ${
                  selectedGeneration === gen.id 
                    ? 'ring-2 ring-primary glass border-primary/30' 
                    : 'glass border-primary/10 hover:border-primary/20'
                }`}
                onClick={() => setSelectedGeneration(gen.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <IconComponent className="h-6 w-6 text-primary" />
                    <Badge variant="outline">{gen.population}</Badge>
                  </div>
                  <h3 className="font-semibold text-lg mb-1">{gen.name}</h3>
                  <p className="text-sm text-muted-foreground mb-3">{gen.range}</p>
                  <div className="flex flex-wrap gap-1">
                    {gen.traits.slice(0, 2).map((trait, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">{trait}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Analysis Dashboard */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Motivadores */}
          <Card className="glass border-primary/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Heart className="h-5 w-5 text-primary" />
                Motivadores Clave
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {currentData.motivators.map((motivator, idx) => (
                  <div key={idx} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">{motivator.name}</span>
                      <span className="text-sm text-muted-foreground">{motivator.value}%</span>
                    </div>
                    <Progress value={motivator.value} className="h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Intereses */}
          <Card className="glass border-primary/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-tech-blue" />
                Intereses Principales
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {currentData.interests.map((interest, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-sm font-medium">{interest.name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-muted-foreground">{interest.percentage}%</span>
                      <PieChart className="h-4 w-4 text-tech-blue" />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Predicciones */}
          <Card className="glass border-primary/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-tech-purple" />
                Predicciones IA
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {currentData.predictions.map((prediction, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-sm font-medium">{prediction.metric}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold">{prediction.value}</span>
                      <Activity className={`h-4 w-4 ${
                        prediction.trend === 'up' ? 'text-green-500' : 
                        prediction.trend === 'down' ? 'text-red-500' : 'text-yellow-500'
                      }`} />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Skills Deep Dive */}
        <Card className="glass border-primary/20 mt-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-huntred-primary" />
              Análisis Granular de Habilidades - {currentGeneration?.name}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              {currentData.skills.map((skill, idx) => (
                <div key={idx} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{skill.name}</span>
                    <Badge variant="outline">{skill.level}</Badge>
                  </div>
                  <Progress value={skill.progress} className="h-3" />
                  <p className="text-sm text-muted-foreground">Competencia: {skill.progress}%</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* CTA */}
        <div className="text-center mt-16">
          <Card className="glass border-primary/20 max-w-2xl mx-auto">
            <CardContent className="p-8">
              <h3 className="text-2xl font-bold mb-4">
                ¿Listo para optimizar tu estrategia generacional?
              </h3>
              <p className="text-muted-foreground mb-6">
                Descubre cómo AURA puede ayudarte a crear estrategias personalizadas para cada generación en tu organización.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="lg" className="bg-gradient-to-r from-huntred-primary to-tech-blue hover:opacity-90">
                  <UserCheck className="mr-2 h-5 w-5" />
                  Analizar Mi Organización
                </Button>
                <Button size="lg" variant="outline" className="border-primary/30">
                  Ver Demo Interactiva
                  <ChevronRight className="ml-2 h-5 w-5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default GenerationalAnalysisSection;