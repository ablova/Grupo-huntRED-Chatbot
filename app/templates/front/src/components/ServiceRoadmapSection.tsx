
import React, { useState } from 'react';
import { CheckCircle, Clock, Zap, Star, ArrowRight, Calendar } from 'lucide-react';

const ServiceRoadmapSection = () => {
  const [selectedQuarter, setSelectedQuarter] = useState('Q1');

  const roadmapData = {
    Q1: {
      title: 'Q1 2024 - Fundación Inteligente',
      features: [
        { name: 'NLP Engine v2.0', status: 'completed', impact: 'high' },
        { name: 'Assessment Analyzer', status: 'completed', impact: 'high' },
        { name: 'Matchmaking Básico', status: 'completed', impact: 'medium' },
        { name: 'Dashboard Kanban', status: 'in-progress', impact: 'high' }
      ]
    },
    Q2: {
      title: 'Q2 2024 - Expansión de Capacidades',
      features: [
        { name: 'Predictions Analyzer', status: 'planned', impact: 'high' },
        { name: 'Conversational AI', status: 'planned', impact: 'medium' },
        { name: 'Integración WhatsApp', status: 'planned', impact: 'medium' },
        { name: 'API RESTful Completa', status: 'planned', impact: 'high' }
      ]
    },
    Q3: {
      title: 'Q3 2024 - IA Avanzada',
      features: [
        { name: 'Career Path Analyzer', status: 'planned', impact: 'high' },
        { name: 'Video Assessment AI', status: 'planned', impact: 'high' },
        { name: 'Quantum Lab Beta', status: 'planned', impact: 'medium' },
        { name: 'Blockchain Verification', status: 'research', impact: 'low' }
      ]
    },
    Q4: {
      title: 'Q4 2024 - Ecosistema Completo',
      features: [
        { name: 'Metaverse Integration', status: 'research', impact: 'medium' },
        { name: 'AI Ethics Module', status: 'planned', impact: 'high' },
        { name: 'Global Talent Pool', status: 'planned', impact: 'high' },
        { name: 'Predictive Analytics 3.0', status: 'research', impact: 'high' }
      ]
    }
  };

  const quarters = ['Q1', 'Q2', 'Q3', 'Q4'];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'in-progress':
        return <Zap className="w-5 h-5 text-blue-500 animate-pulse" />;
      case 'planned':
        return <Clock className="w-5 h-5 text-orange-500" />;
      case 'research':
        return <Star className="w-5 h-5 text-purple-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completado';
      case 'in-progress':
        return 'En Desarrollo';
      case 'planned':
        return 'Planificado';
      case 'research':
        return 'Investigación';
      default:
        return 'Pendiente';
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high':
        return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'low':
        return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400';
    }
  };

  const milestones = [
    { date: 'Mar 2024', title: 'Lanzamiento MVP', description: 'Primera versión funcional' },
    { date: 'Jun 2024', title: 'IA Conversacional', description: 'Chatbot inteligente integrado' },
    { date: 'Sep 2024', title: 'Análisis Predictivo', description: 'Predicciones avanzadas' },
    { date: 'Dic 2024', title: 'Ecosistema Completo', description: 'Plataforma integral' }
  ];

  return (
    <section className="py-20 bg-gradient-to-br from-indigo-50 via-white to-cyan-50 dark:from-indigo-900/20 dark:via-slate-900 dark:to-cyan-900/20">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-indigo-600 to-cyan-600 bg-clip-text text-transparent">
            Roadmap de Servicios
          </h2>
          <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
            Nuestra visión para revolucionar el reclutamiento con IA de vanguardia
          </p>
        </div>

        {/* Timeline Overview */}
        <div className="mb-12">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0 md:space-x-4">
            {milestones.map((milestone, index) => (
              <div key={index} className="flex-1 text-center animate-fade-in-up" style={{ animationDelay: `${index * 0.2}s` }}>
                <div className="relative">
                  <div className="w-4 h-4 bg-gradient-to-r from-indigo-500 to-cyan-500 rounded-full mx-auto mb-3"></div>
                  {index < milestones.length - 1 && (
                    <div className="hidden md:block absolute top-2 left-1/2 w-full h-0.5 bg-gradient-to-r from-indigo-200 to-cyan-200"></div>
                  )}
                </div>
                <div className="glass p-4 rounded-lg">
                  <div className="flex items-center justify-center mb-2">
                    <Calendar className="w-4 h-4 mr-2 text-indigo-500" />
                    <span className="text-sm font-semibold text-indigo-600 dark:text-indigo-400">{milestone.date}</span>
                  </div>
                  <h3 className="font-semibold mb-1">{milestone.title}</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400">{milestone.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quarter Selector */}
        <div className="mb-8 flex justify-center">
          <div className="glass p-2 rounded-xl">
            <div className="flex space-x-2">
              {quarters.map((quarter) => (
                <button
                  key={quarter}
                  onClick={() => setSelectedQuarter(quarter)}
                  className={`px-6 py-3 rounded-lg font-semibold transition-all duration-300 ${
                    selectedQuarter === quarter
                      ? 'bg-gradient-to-r from-indigo-500 to-cyan-600 text-white shadow-lg'
                      : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                  }`}
                >
                  {quarter} 2024
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Quarter Details */}
        <div className="glass p-8 rounded-xl max-w-4xl mx-auto">
          <h3 className="text-2xl font-bold mb-6 text-center bg-gradient-to-r from-indigo-600 to-cyan-600 bg-clip-text text-transparent">
            {roadmapData[selectedQuarter as keyof typeof roadmapData].title}
          </h3>
          
          <div className="grid md:grid-cols-2 gap-6">
            {roadmapData[selectedQuarter as keyof typeof roadmapData].features.map((feature, index) => (
              <div key={index} className="flex items-center space-x-4 p-4 rounded-lg bg-white dark:bg-slate-800 hover:scale-105 transition-all duration-300 animate-fade-in-up" style={{ animationDelay: `${index * 0.1}s` }}>
                <div className="flex-shrink-0">
                  {getStatusIcon(feature.status)}
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold mb-1">{feature.name}</h4>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-slate-600 dark:text-slate-400">
                      {getStatusText(feature.status)}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded-full font-medium ${getImpactColor(feature.impact)}`}>
                      {feature.impact === 'high' ? 'Alto Impacto' : 
                       feature.impact === 'medium' ? 'Impacto Medio' : 'Bajo Impacto'}
                    </span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400" />
              </div>
            ))}
          </div>
        </div>

        {/* Progress Stats */}
        <div className="mt-12 grid md:grid-cols-4 gap-6">
          <div className="glass p-6 rounded-xl text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-gradient-to-r from-green-500 to-green-600 rounded-full flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-white" />
            </div>
            <h4 className="font-semibold mb-1">Completados</h4>
            <p className="text-2xl font-bold text-green-600">8</p>
            <p className="text-sm text-slate-600 dark:text-slate-400">Features lanzados</p>
          </div>

          <div className="glass p-6 rounded-xl text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <h4 className="font-semibold mb-1">En Desarrollo</h4>
            <p className="text-2xl font-bold text-blue-600">4</p>
            <p className="text-sm text-slate-600 dark:text-slate-400">Features activos</p>
          </div>

          <div className="glass p-6 rounded-xl text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-gradient-to-r from-orange-500 to-orange-600 rounded-full flex items-center justify-center">
              <Clock className="w-6 h-6 text-white" />
            </div>
            <h4 className="font-semibold mb-1">Planificados</h4>
            <p className="text-2xl font-bold text-orange-600">12</p>
            <p className="text-sm text-slate-600 dark:text-slate-400">Features pendientes</p>
          </div>

          <div className="glass p-6 rounded-xl text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full flex items-center justify-center">
              <Star className="w-6 h-6 text-white" />
            </div>
            <h4 className="font-semibold mb-1">Investigación</h4>
            <p className="text-2xl font-bold text-purple-600">6</p>
            <p className="text-sm text-slate-600 dark:text-slate-400">Features en R&D</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ServiceRoadmapSection;
