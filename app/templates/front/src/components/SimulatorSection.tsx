
import React, { useState } from 'react';
import { Play, MessageCircle, CheckCircle, ArrowRight, Zap, Brain, Users } from 'lucide-react';

const SimulatorSection = () => {
  const [activeSimulator, setActiveSimulator] = useState('assessment');
  const [isSimulating, setIsSimulating] = useState(false);

  const simulators = [
    {
      id: 'assessment',
      title: 'Assessment Simulator',
      icon: CheckCircle,
      description: 'Experimenta nuestro sistema de evaluación inteligente',
      color: 'from-blue-500 to-blue-600',
      features: ['Evaluación técnica', 'Análisis comportamental', 'Scoring automático']
    },
    {
      id: 'chatbot',
      title: 'Chatbot Interactivo',
      icon: MessageCircle,
      description: 'Conversa con nuestra IA especializada en reclutamiento',
      color: 'from-purple-500 to-purple-600',
      features: ['NLP avanzado', 'Respuestas contextuales', 'Aprendizaje continuo']
    },
    {
      id: 'process',
      title: 'Process Simulator',
      icon: Users,
      description: 'Visualiza el flujo completo de selección',
      color: 'from-green-500 to-green-600',
      features: ['Flujo personalizable', 'Métricas en tiempo real', 'Optimización automática']
    }
  ];

  const assessmentQuestions = [
    "¿Cuál es tu experiencia con React y TypeScript?",
    "Describe un proyecto desafiante que hayas liderado",
    "¿Cómo manejas los conflictos en equipos multidisciplinarios?",
    "Explica tu enfoque para la resolución de problemas complejos"
  ];

  const chatbotResponses = [
    "¡Hola! Soy tu asistente de huntRED® AI. ¿En qué puedo ayudarte hoy?",
    "Entiendo que buscas información sobre nuestros servicios. ¿Te interesa alguna unidad específica?",
    "Basándome en tu perfil, creo que huntRED® Executive sería ideal para ti. ¿Quieres que te cuente más?",
    "Perfecto. Voy a conectarte con uno de nuestros especialistas para una consulta personalizada."
  ];

  const processSteps = [
    { step: 1, title: 'Sourcing Inteligente', status: 'completed', time: '2 días' },
    { step: 2, title: 'Screening Automático', status: 'completed', time: '1 día' },
    { step: 3, title: 'Assessment AI', status: 'active', time: '3 días' },
    { step: 4, title: 'Entrevistas Virtuales', status: 'pending', time: '5 días' },
    { step: 5, title: 'Decisión Final', status: 'pending', time: '2 días' }
  ];

  const handleSimulate = () => {
    setIsSimulating(true);
    setTimeout(() => setIsSimulating(false), 3000);
  };

  const renderSimulatorContent = () => {
    switch (activeSimulator) {
      case 'assessment':
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <Brain className="w-16 h-16 mx-auto mb-4 text-blue-500" />
              <h3 className="text-2xl font-bold mb-2">Assessment Inteligente</h3>
              <p className="text-slate-600 dark:text-slate-400">Evaluación adaptativa basada en IA</p>
            </div>
            
            {!isSimulating ? (
              <div className="space-y-4">
                <h4 className="font-semibold mb-4">Preguntas de Ejemplo:</h4>
                {assessmentQuestions.map((question, index) => (
                  <div key={index} className="glass p-4 rounded-lg animate-fade-in-up" style={{ animationDelay: `${index * 0.1}s` }}>
                    <div className="flex items-start space-x-3">
                      <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                        {index + 1}
                      </span>
                      <p className="text-slate-700 dark:text-slate-300">{question}</p>
                    </div>
                  </div>
                ))}
                <button
                  onClick={handleSimulate}
                  className="w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white py-3 rounded-lg font-semibold hover:scale-105 transition-all duration-300 flex items-center justify-center space-x-2"
                >
                  <Play className="w-5 h-5" />
                  <span>Iniciar Assessment</span>
                </button>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center animate-pulse">
                  <Zap className="w-8 h-8 text-white" />
                </div>
                <h4 className="text-xl font-semibold mb-4">Procesando respuestas...</h4>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 mb-4">
                  <div className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full animate-pulse" style={{ width: '75%' }}></div>
                </div>
                <p className="text-slate-600 dark:text-slate-400">Analizando competencias y generando score...</p>
              </div>
            )}
          </div>
        );

      case 'chatbot':
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <MessageCircle className="w-16 h-16 mx-auto mb-4 text-purple-500" />
              <h3 className="text-2xl font-bold mb-2">Chatbot Inteligente</h3>
              <p className="text-slate-600 dark:text-slate-400">Conversación natural con IA especializada</p>
            </div>
            
            <div className="bg-white dark:bg-slate-800 rounded-lg p-4 max-h-80 overflow-y-auto space-y-4">
              {chatbotResponses.map((response, index) => (
                <div key={index} className={`flex ${index % 2 === 0 ? 'justify-start' : 'justify-end'} animate-fade-in-up`} style={{ animationDelay: `${index * 0.5}s` }}>
                  <div className={`max-w-xs p-3 rounded-lg ${
                    index % 2 === 0 
                      ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white' 
                      : 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200'
                  }`}>
                    {response}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="flex space-x-2">
              <input
                type="text"
                placeholder="Escribe tu mensaje..."
                className="flex-1 p-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800"
              />
              <button className="bg-gradient-to-r from-purple-500 to-purple-600 text-white px-6 py-3 rounded-lg hover:scale-105 transition-all duration-300">
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        );

      case 'process':
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <Users className="w-16 h-16 mx-auto mb-4 text-green-500" />
              <h3 className="text-2xl font-bold mb-2">Process Flow</h3>
              <p className="text-slate-600 dark:text-slate-400">Visualización del proceso completo</p>
            </div>
            
            <div className="space-y-4">
              {processSteps.map((step, index) => (
                <div key={index} className={`flex items-center space-x-4 p-4 rounded-lg transition-all duration-300 ${
                  step.status === 'completed' ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800' :
                  step.status === 'active' ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 animate-pulse' :
                  'bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700'
                }`}>
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                    step.status === 'completed' ? 'bg-green-500 text-white' :
                    step.status === 'active' ? 'bg-blue-500 text-white' :
                    'bg-slate-300 dark:bg-slate-600 text-slate-600 dark:text-slate-400'
                  }`}>
                    {step.status === 'completed' ? <CheckCircle className="w-5 h-5" /> : step.step}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold">{step.title}</h4>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Tiempo estimado: {step.time}</p>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                    step.status === 'completed' ? 'bg-green-100 text-green-700' :
                    step.status === 'active' ? 'bg-blue-100 text-blue-700' :
                    'bg-slate-100 text-slate-600'
                  }`}>
                    {step.status === 'completed' ? 'Completado' :
                     step.status === 'active' ? 'En Proceso' : 'Pendiente'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <section className="py-20 bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 dark:from-purple-900/20 dark:via-pink-900/20 dark:to-orange-900/20">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            Simuladores Interactivos
          </h2>
          <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
            Experimenta nuestras tecnologías de vanguardia antes de implementarlas
          </p>
        </div>

        {/* Simulator Selector */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {simulators.map((simulator) => {
            const SimulatorIcon = simulator.icon;
            return (
              <button
                key={simulator.id}
                onClick={() => setActiveSimulator(simulator.id)}
                className={`p-6 rounded-xl transition-all duration-300 text-left hover:scale-105 ${
                  activeSimulator === simulator.id
                    ? `bg-gradient-to-r ${simulator.color} text-white shadow-xl`
                    : 'glass hover:shadow-lg'
                }`}
              >
                <SimulatorIcon className={`w-12 h-12 mb-4 ${activeSimulator === simulator.id ? 'text-white' : 'text-slate-600 dark:text-slate-400'}`} />
                <h3 className="text-xl font-semibold mb-2">{simulator.title}</h3>
                <p className={`text-sm mb-4 ${activeSimulator === simulator.id ? 'text-white/90' : 'text-slate-600 dark:text-slate-400'}`}>
                  {simulator.description}
                </p>
                <ul className="space-y-1">
                  {simulator.features.map((feature, index) => (
                    <li key={index} className={`text-xs flex items-center ${activeSimulator === simulator.id ? 'text-white/80' : 'text-slate-500 dark:text-slate-500'}`}>
                      <CheckCircle className="w-3 h-3 mr-2" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </button>
            );
          })}
        </div>

        {/* Simulator Content */}
        <div className="glass p-8 rounded-xl max-w-4xl mx-auto">
          {renderSimulatorContent()}
        </div>
      </div>
    </section>
  );
};

export default SimulatorSection;
