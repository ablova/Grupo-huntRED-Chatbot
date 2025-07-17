import React from 'react';
import { Link } from 'react-router-dom';
import { FlaskConical, Rocket, Lightbulb, Code2, BrainCircuit, TestTube2, GitBranch, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const LaboratorioPage: React.FC = () => {
  const currentProjects = [
    {
      icon: <BrainCircuit className="w-6 h-6 text-tech-purple" />,
      title: "AURA Next Gen",
      description: "Próxima generación de nuestro motor de IA con capacidades mejoradas de procesamiento de lenguaje natural.",
      status: "En desarrollo",
      progress: 65
    },
    {
      icon: <Zap className="w-6 h-6 text-tech-blue" />,
      title: "Automatización de Flujos",
      description: "Nuevas herramientas de automatización para optimizar los procesos de reclutamiento.",
      status: "Beta cerrada",
      progress: 85
    },
    {
      icon: <TestTube2 className="w-6 h-6 text-tech-cyan" />,
      title: "Análisis Predictivo",
      description: "Modelos avanzados para predecir el éxito de candidatos y la retención de empleados.",
      status: "En pruebas",
      progress: 45
    }
  ];

  const futureProjects = [
    {
      icon: <FlaskConical className="w-6 h-6 text-tech-green" />,
      title: "Realidad Aumentada",
      description: "Entrevistas inmersivas con tecnología de realidad aumentada.",
      eta: "Q2 2024"
    },
    {
      icon: <Code2 className="w-6 h-6 text-tech-purple" />,
      title: "API Pública",
      description: "Acceso abierto a nuestra plataforma para desarrolladores externos.",
      eta: "Q3 2024"
    },
    {
      icon: <GitBranch className="w-6 h-6 text-tech-blue" />,
      title: "Integración Continua",
      description: "Herramientas para integración con más plataformas de RRHH.",
      eta: "Q4 2024"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20 text-center">
        <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-700 text-sm font-medium mb-6">
          <FlaskConical className="w-4 h-4 mr-2" />
          Laboratorio de Innovación
        </div>
        
        <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
          Explorando el <span className="bg-gradient-to-r from-tech-purple to-tech-blue bg-clip-text text-transparent">futuro</span> del talento
        </h1>
        
        <p className="text-xl text-gray-700 max-w-3xl mx-auto mb-12">
          En nuestro laboratorio, experimentamos con tecnologías emergentes para crear las soluciones de reclutamiento del mañana.
        </p>
        
        <div className="flex flex-wrap justify-center gap-4 mb-20">
          <Button className="bg-tech-blue hover:bg-blue-700 px-6 py-3">
            Ver Demostraciones
          </Button>
          <Button variant="outline" className="border-tech-blue text-tech-blue hover:bg-blue-50 px-6 py-3">
            Unirse al Programa Beta
          </Button>
        </div>

        {/* Current Projects */}
        <div className="max-w-6xl mx-auto mb-20">
          <h2 className="text-3xl font-bold text-gray-900 mb-12 text-left">Proyectos en Desarrollo</h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            {currentProjects.map((project, index) => (
              <Card key={index} className="overflow-hidden hover:shadow-lg transition-shadow">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="p-2 rounded-lg bg-blue-50 text-tech-blue">
                      {project.icon}
                    </div>
                    <span className="text-sm font-medium px-3 py-1 rounded-full bg-blue-100 text-blue-700">
                      {project.status}
                    </span>
                  </div>
                  <CardTitle className="mt-4 text-xl">{project.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700 mb-4">{project.description}</p>
                  <div className="mt-4">
                    <div className="flex justify-between text-sm text-gray-600 mb-1">
                      <span>Progreso</span>
                      <span>{project.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-tech-blue to-tech-purple h-2 rounded-full" 
                        style={{ width: `${project.progress}%` }}
                      ></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Future Projects */}
        <div className="max-w-6xl mx-auto mb-20">
          <h2 className="text-3xl font-bold text-gray-900 mb-12 text-left">Próximamente</h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            {futureProjects.map((project, index) => (
              <Card key={index} className="group relative overflow-hidden border-2 border-dashed border-gray-200 hover:border-tech-blue transition-colors">
                <div className="absolute top-4 right-4 px-2 py-1 rounded-full text-xs font-medium bg-blue-50 text-tech-blue">
                  {project.eta}
                </div>
                <CardHeader>
                  <div className="p-3 rounded-lg bg-blue-50 text-tech-blue w-12 h-12 flex items-center justify-center mb-4">
                    {project.icon}
                  </div>
                  <CardTitle className="text-xl">{project.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-gray-700">
                    {project.description}
                  </CardDescription>
                  <Button variant="ghost" size="sm" className="mt-4 text-tech-blue hover:bg-blue-50">
                    Más información
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-1">
                      <line x1="5" y1="12" x2="19" y2="12"></line>
                      <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-gradient-to-r from-tech-purple to-tech-blue rounded-2xl p-8 text-white text-left">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold mb-4">¿Tienes una idea innovadora?</h2>
            <p className="text-xl mb-8 text-blue-100">
              En huntRED® estamos siempre buscando nuevas ideas y colaboraciones. Si tienes un proyecto en mente o quieres unirte a nuestro equipo de innovación, nos encantaría escucharte.
            </p>
            <Button variant="outline" className="bg-transparent border-white text-white hover:bg-white/10">
              <Lightbulb className="w-4 h-4 mr-2" />
              Enviar Propuesta
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LaboratorioPage;
