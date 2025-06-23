
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Users, TrendingUp, Clock, CheckCircle, AlertCircle, User, Building, Briefcase, Network, Zap, Brain, Target } from 'lucide-react';

const RecruitmentDashboard = () => {
  const [activeView, setActiveView] = useState('kanban');

  const kanbanColumns = [
    {
      title: "Nuevos Candidatos",
      count: 12,
      color: "bg-blue-500",
      candidates: [
        { name: "María González", role: "Senior Developer", score: 92, tags: ["React", "TypeScript"], auraInsight: "Red extensa en FinTech" },
        { name: "Carlos Ruiz", role: "Product Manager", score: 88, tags: ["Agile", "Leadership"], auraInsight: "Influencer en comunidad PM" },
        { name: "Ana López", role: "UX Designer", score: 95, tags: ["Figma", "Research"], auraInsight: "Mentor activo en diseño" }
      ]
    },
    {
      title: "En Evaluación",
      count: 8,
      color: "bg-yellow-500",
      candidates: [
        { name: "David Chen", role: "Data Scientist", score: 89, tags: ["Python", "ML"], auraInsight: "Publicaciones académicas relevantes" },
        { name: "Sofia Martín", role: "DevOps Engineer", score: 91, tags: ["AWS", "Docker"], auraInsight: "Red sólida en cloud computing" }
      ]
    },
    {
      title: "Entrevistas",
      count: 5,
      color: "bg-purple-500",
      candidates: [
        { name: "Roberto Silva", role: "Full Stack", score: 87, tags: ["Node.js", "React"], auraInsight: "Trayectoria ascendente proyectada" },
        { name: "Elena Vega", role: "Scrum Master", score: 93, tags: ["Agile", "Teams"], auraInsight: "Alta centralidad en equipos ágiles" }
      ]
    },
    {
      title: "Finalizados",
      count: 3,
      color: "bg-green-500",
      candidates: [
        { name: "Miguel Torres", role: "Tech Lead", score: 96, tags: ["Architecture", "Leadership"], auraInsight: "Potencial mentor organizacional" }
      ]
    }
  ];

  const auraMetrics = [
    { label: "Predicciones AURA", value: "94% precisión", change: "+8%", icon: Brain, color: "text-purple-600" },
    { label: "Red de Conexiones", value: "2.3M nodos", change: "+15%", icon: Network, color: "text-blue-600" },
    { label: "Insights Generados", value: "1,247", change: "+34%", icon: Zap, color: "text-yellow-600" },
    { label: "Match Quality Score", value: "89.2%", change: "+12%", icon: Target, color: "text-green-600" }
  ];

  const traditionalMetrics = [
    { label: "Tiempo Promedio", value: "8 días", change: "-45%", icon: Clock },
    { label: "Tasa de Éxito", value: "94%", change: "+18%", icon: CheckCircle },
    { label: "Candidatos Activos", value: "28", change: "+45%", icon: Users },
    { label: "ROI del Proceso", value: "340%", change: "+89%", icon: TrendingUp }
  ];

  return (
    <section className="py-20 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-16">
          <div className="inline-flex items-center gap-2 bg-tech-gradient/10 rounded-full px-4 py-2 text-sm font-medium">
            <Brain className="w-4 h-4 text-purple-600" />
            Potenciado por AURA
          </div>
          <h2 className="text-3xl md:text-4xl font-bold">
            Dashboard Inteligente de <span className="bg-tech-gradient bg-clip-text text-transparent">Reclutamiento</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Visualiza todo tu proceso con inteligencia de red neuronal gráfica y análisis predictivo en tiempo real
          </p>
        </div>

        {/* AURA Metrics */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-600" />
            Métricas AURA (Graph Neural Network)
          </h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {auraMetrics.map((metric, index) => (
              <Card key={index} className="glass border-purple-200/50 bg-gradient-to-br from-purple-50/50 to-blue-50/50 dark:from-purple-900/20 dark:to-blue-900/20">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{metric.label}</p>
                      <p className="text-2xl font-bold">{metric.value}</p>
                      <p className={`text-sm ${metric.change.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
                        {metric.change} vs mes anterior
                      </p>
                    </div>
                    <div className="w-12 h-12 bg-tech-gradient/20 rounded-full flex items-center justify-center">
                      <metric.icon className={`w-6 h-6 ${metric.color}`} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Traditional Metrics */}
        <div className="mb-12">
          <h3 className="text-lg font-semibold mb-4">Métricas de Rendimiento</h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {traditionalMetrics.map((metric, index) => (
              <Card key={index} className="glass border-primary/20">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{metric.label}</p>
                      <p className="text-2xl font-bold">{metric.value}</p>
                      <p className={`text-sm ${metric.change.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
                        {metric.change} vs mes anterior
                      </p>
                    </div>
                    <div className="w-12 h-12 bg-tech-gradient/20 rounded-full flex items-center justify-center">
                      <metric.icon className="w-6 h-6 text-primary" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Enhanced Kanban Board with AURA */}
        <Card className="glass border-primary/20">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl flex items-center justify-center gap-2">
              <Network className="w-6 h-6 text-purple-600" />
              Pipeline Inteligente de Candidatos
            </CardTitle>
            <p className="text-muted-foreground">Gestión visual potenciada por análisis de red y predicción de carrera</p>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid lg:grid-cols-4 gap-6">
              {kanbanColumns.map((column, index) => (
                <div key={index} className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-lg">{column.title}</h3>
                    <Badge variant="secondary" className={`${column.color} text-white`}>
                      {column.count}
                    </Badge>
                  </div>
                  
                  <div className="space-y-3">
                    {column.candidates.map((candidate, candidateIndex) => (
                      <Card key={candidateIndex} className="hover:shadow-md transition-all cursor-pointer border-l-4 border-l-purple-400">
                        <CardContent className="p-4 space-y-3">
                          <div className="flex items-start justify-between">
                            <div>
                              <h4 className="font-medium">{candidate.name}</h4>
                              <p className="text-sm text-muted-foreground">{candidate.role}</p>
                            </div>
                            <Badge variant="outline" className="text-xs bg-purple-50 text-purple-700">
                              {candidate.score}%
                            </Badge>
                          </div>
                          
                          <div className="flex flex-wrap gap-1">
                            {candidate.tags.map((tag, tagIndex) => (
                              <Badge key={tagIndex} variant="secondary" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                          
                          {/* AURA Insight */}
                          <div className="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-md">
                            <div className="flex items-center gap-2 text-xs">
                              <Brain className="w-3 h-3 text-purple-600" />
                              <span className="text-purple-700 dark:text-purple-300 font-medium">AURA:</span>
                            </div>
                            <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">{candidate.auraInsight}</p>
                          </div>
                          
                          <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                            <User className="w-3 h-3" />
                            <span>Actualizado hace 2h</span>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Enhanced AI Insights with AURA */}
        <div className="mt-12 grid md:grid-cols-2 gap-8">
          <Card className="glass border-purple-200/50 bg-gradient-to-br from-purple-50/30 to-blue-50/30 dark:from-purple-900/10 dark:to-blue-900/10">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Brain className="w-5 h-5 text-purple-500" />
                <span>AURA Graph Intelligence</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border-l-4 border-purple-400">
                <p className="text-sm"><strong>Red Neural:</strong> María González tiene conexiones estratégicas en 3 fintechs objetivo. Su red personal aumentaría el valor organizacional en un 23%.</p>
              </div>
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border-l-4 border-blue-400">
                <p className="text-sm"><strong>Predicción de Carrera:</strong> David Chen muestra trayectoria ascendente hacia roles de ML Engineering. Probabilidad de retención: 89%.</p>
              </div>
              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border-l-4 border-green-400">
                <p className="text-sm"><strong>Análisis de Influencia:</strong> Ana López es mentora activa con 94% de satisfacción. Potencial para liderazgo de equipos creativos.</p>
              </div>
            </CardContent>
          </Card>

          <Card className="glass border-primary/20">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-green-500" />
                <span>Análisis Predictivo Avanzado</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Probabilidad de contratación exitosa</span>
                  <span className="font-semibold">94%</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{ width: '94%' }} />
                </div>
                <p className="text-xs text-muted-foreground">Basado en análisis de personalidad y patrones históricos</p>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Tiempo estimado con GenIA & AURA</span>
                  <span className="font-semibold">5 días</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="bg-purple-500 h-2 rounded-full" style={{ width: '75%' }} />
                </div>
                <p className="text-xs text-muted-foreground">40% más rápido que métodos tradicionales</p>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Índice de Compatibilidad Cultural</span>
                  <span className="font-semibold">91%</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: '91%' }} />
                </div>
                <p className="text-xs text-muted-foreground">Análisis de personalidad y valores organizacionales</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* AURA Capabilities Preview */}
        <div className="mt-12">
          <Card className="glass border-tech-gradient bg-gradient-to-r from-purple-50/50 to-blue-50/50 dark:from-purple-900/10 dark:to-blue-900/10">
            <CardContent className="p-8 text-center space-y-6">
              <div className="flex items-center justify-center gap-2 mb-4">
                <Brain className="w-8 h-8 text-purple-600" />
                <h3 className="text-2xl font-bold">Capacidades AURA en Acción</h3>
              </div>
              <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
                Esta es solo una vista previa. AURA incluye análisis organizacional, simulador de carreras, 
                motor de gamificación, IA generativa y mucho más.
              </p>
              <div className="grid md:grid-cols-4 gap-4 mt-8">
                <div className="text-center space-y-2">
                  <Network className="w-8 h-8 text-purple-600 mx-auto" />
                  <div className="font-semibold text-sm">Graph Neural Network</div>
                  <div className="text-xs text-muted-foreground">Análisis de red y relaciones</div>
                </div>
                <div className="text-center space-y-2">
                  <Target className="w-8 h-8 text-blue-600 mx-auto" />
                  <div className="font-semibold text-sm">Skill Gap Analyzer</div>
                  <div className="text-xs text-muted-foreground">Identificación de brechas</div>
                </div>
                <div className="text-center space-y-2">
                  <Zap className="w-8 h-8 text-yellow-600 mx-auto" />
                  <div className="font-semibold text-sm">Career Simulator</div>
                  <div className="text-xs text-muted-foreground">Predicción de trayectorias</div>
                </div>
                <div className="text-center space-y-2">
                  <Brain className="w-8 h-8 text-green-600 mx-auto" />
                  <div className="font-semibold text-sm">Generative AI</div>
                  <div className="text-xs text-muted-foreground">Contenido automatizado</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default RecruitmentDashboard;
