import React from 'react';
import { Link } from 'react-router-dom';
import { Brain, Cpu, GitBranch, Zap, Shield, BarChart, Code, Database } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const PlataformaPage: React.FC = () => {
  const features = [
    {
      icon: <Brain className="w-8 h-8 text-tech-purple" />,
      title: "AURA - Núcleo de IA",
      description: "Nuestra tecnología de IA avanzada que potencia todas las soluciones de la plataforma.",
      link: "/ai-services/aura"
    },
    {
      icon: <Cpu className="w-8 h-8 text-tech-blue" />,
      title: "GenIA - Generación Inteligente",
      description: "Herramientas de generación de contenido y análisis predictivo.",
      link: "/ai-services/genia"
    },
    {
      icon: <GitBranch className="w-8 h-8 text-tech-cyan" />,
      title: "Flujos de Trabajo",
      description: "Automatización de procesos y flujos de trabajo personalizables.",
      link: "#"
    },
    {
      icon: <Database className="w-8 h-8 text-tech-green" />,
      title: "Integración de Datos",
      description: "Conecta con tus sistemas existentes sin problemas.",
      link: "#"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20 text-center">
        <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
          Plataforma de <span className="bg-gradient-to-r from-tech-blue to-tech-purple bg-clip-text text-transparent">Tecnología Avanzada</span>
        </h1>
        <p className="text-xl text-gray-700 max-w-3xl mx-auto mb-12">
          Descubre el poder de nuestra plataforma integral con AURA, GenIA y Flujos de Trabajo Inteligentes.
        </p>
        
        <div className="flex flex-wrap justify-center gap-6 mb-20">
          {features.map((feature, index) => (
            <Link to={feature.link} key={index} className="w-full sm:w-1/2 lg:w-1/4 p-2">
              <Card className="h-full hover:shadow-lg transition-all duration-300 hover:-translate-y-1 border-0 bg-white/90 backdrop-blur-sm">
                <CardHeader>
                  <div className="w-16 h-16 mx-auto rounded-xl bg-blue-50 flex items-center justify-center mb-4">
                    {feature.icon}
                  </div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-gray-700">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>

        <div className="mt-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">Características Principales</h2>
          
          <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center mr-4">
                  <Zap className="w-5 h-5 text-tech-blue" />
                </div>
                <h3 className="text-xl font-semibold">Rendimiento Óptimo</h3>
              </div>
              <p className="text-gray-700">Arquitectura escalable diseñada para manejar grandes volúmenes de datos con tiempos de respuesta mínimos.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center mr-4">
                  <Shield className="w-5 h-5 text-tech-purple" />
                </div>
                <h3 className="text-xl font-semibold">Seguridad Integral</h3>
              </div>
              <p className="text-gray-700">Protección de datos de nivel empresarial con cifrado de extremo a extremo y cumplimiento normativo.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 rounded-full bg-cyan-100 flex items-center justify-center mr-4">
                  <BarChart className="w-5 h-5 text-tech-cyan" />
                </div>
                <h3 className="text-xl font-semibold">Análisis en Tiempo Real</h3>
              </div>
              <p className="text-gray-700">Panel de control con métricas en tiempo real para la toma de decisiones informadas.</p>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center mr-4">
                  <Code className="w-5 h-5 text-tech-green" />
                </div>
                <h3 className="text-xl font-semibold">API Abierta</h3>
              </div>
              <p className="text-gray-700">Documentación completa y herramientas para desarrolladores para integraciones personalizadas.</p>
            </div>
          </div>
        </div>

        <div className="mt-20 bg-gradient-to-r from-tech-blue to-tech-purple rounded-2xl p-8 text-white">
          <h2 className="text-3xl font-bold mb-6">¿Listo para comenzar?</h2>
          <p className="text-xl mb-8 max-w-2xl mx-auto">
            Descubre cómo nuestra plataforma puede transformar tus procesos de negocio con tecnología de vanguardia.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button className="bg-white text-tech-blue hover:bg-gray-100 px-8 py-3 text-lg font-semibold">
              Solicitar Demo
            </Button>
            <Button variant="outline" className="bg-transparent border-white text-white hover:bg-white/10 px-8 py-3 text-lg font-semibold">
              Contactar Ventas
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlataformaPage;
