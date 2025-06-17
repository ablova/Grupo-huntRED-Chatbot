
import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Play, Pause, RefreshCw, Database, Cpu, Target, TrendingUp } from 'lucide-react';

const MLPipelineSection = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [metrics, setMetrics] = useState({
    accuracy: 0,
    loss: 1.0,
    epoch: 0,
    throughput: 0
  });

  const pipelineSteps = [
    {
      id: 'data-ingestion',
      title: 'Data Ingestion',
      icon: Database,
      description: 'Ingesta masiva de datos multimodales',
      color: 'from-blue-500 to-cyan-500',
      status: 'completed'
    },
    {
      id: 'preprocessing',
      title: 'Preprocessing',
      icon: RefreshCw,
      description: 'Limpieza y transformación inteligente',
      color: 'from-cyan-500 to-green-500',
      status: 'processing'
    },
    {
      id: 'training',
      title: 'Neural Training',
      icon: Cpu,
      description: 'Entrenamiento de redes neuronales profundas',
      color: 'from-green-500 to-yellow-500',
      status: 'pending'
    },
    {
      id: 'evaluation',
      title: 'Model Evaluation',
      icon: Target,
      description: 'Validación y optimización automática',
      color: 'from-yellow-500 to-orange-500',
      status: 'pending'
    },
    {
      id: 'deployment',
      title: 'Deployment',
      icon: TrendingUp,
      description: 'Despliegue escalable en la nube',
      color: 'from-orange-500 to-red-500',
      status: 'pending'
    }
  ];

  useEffect(() => {
    if (isRunning) {
      const interval = setInterval(() => {
        setCurrentStep(prev => (prev + 1) % pipelineSteps.length);
        setMetrics(prev => ({
          accuracy: Math.min(0.99, prev.accuracy + Math.random() * 0.05),
          loss: Math.max(0.001, prev.loss - Math.random() * 0.1),
          epoch: prev.epoch + 1,
          throughput: 1000 + Math.random() * 500
        }));
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [isRunning]);

  return (
    <section className="py-20 bg-gradient-to-br from-muted/30 to-background relative overflow-hidden">
      {/* Background Grid */}
      <div className="absolute inset-0 quantum-grid opacity-20"></div>
      
      <div className="container mx-auto px-4 lg:px-8 relative z-10">
        <div className="text-center space-y-4 mb-16">
          <h2 className="text-4xl md:text-5xl font-bold">
            ML Pipeline <span className="bg-tech-gradient bg-clip-text text-transparent">Automatizado</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-4xl mx-auto">
            Flujo de trabajo de machine learning completamente automatizado con monitoreo en tiempo real
          </p>
        </div>

        {/* Pipeline Controls */}
        <div className="flex justify-center mb-12">
          <div className="glass rounded-full p-2 flex items-center space-x-2">
            <button
              onClick={() => setIsRunning(!isRunning)}
              className={`flex items-center space-x-2 px-6 py-3 rounded-full font-medium transition-all ${
                isRunning 
                  ? 'bg-red-500 hover:bg-red-600 text-white' 
                  : 'bg-green-500 hover:bg-green-600 text-white'
              }`}
            >
              {isRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              <span>{isRunning ? 'Pausar Pipeline' : 'Iniciar Pipeline'}</span>
            </button>
            <button
              onClick={() => {
                setCurrentStep(0);
                setMetrics({ accuracy: 0, loss: 1.0, epoch: 0, throughput: 0 });
              }}
              className="p-3 rounded-full bg-muted hover:bg-muted/80 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Pipeline Visualization */}
        <div className="grid lg:grid-cols-5 gap-6 mb-16">
          {pipelineSteps.map((step, index) => {
            const Icon = step.icon;
            const isActive = currentStep === index && isRunning;
            const isCompleted = index < currentStep || !isRunning;
            
            return (
              <div key={step.id} className="relative">
                <Card className={`transition-all duration-500 hover:scale-105 border-0 ${
                  isActive ? 'shadow-2xl shadow-primary/50 animate-quantum-pulse' : 
                  isCompleted ? 'shadow-lg shadow-green-500/30' : 'shadow-md'
                }`}>
                  <CardContent className="p-6 text-center">
                    <div className={`relative mx-auto w-16 h-16 mb-4 rounded-xl bg-gradient-to-r ${step.color} flex items-center justify-center ${
                      isActive ? 'animate-pulse' : ''
                    }`}>
                      <Icon className="w-8 h-8 text-white" />
                      {isActive && (
                        <div className="absolute inset-0 rounded-xl bg-white/20 animate-ping" />
                      )}
                      {isCompleted && (
                        <div className="absolute -top-1 -right-1 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-xs">✓</span>
                        </div>
                      )}
                    </div>
                    
                    <h3 className="font-bold text-sm mb-2">{step.title}</h3>
                    <p className="text-xs text-muted-foreground">{step.description}</p>
                    
                    {isActive && (
                      <div className="mt-3 flex justify-center">
                        <div className="w-12 h-1 bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-primary animate-pulse" style={{ width: '100%' }} />
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
                
                {/* Connection Line */}
                {index < pipelineSteps.length - 1 && (
                  <div className="hidden lg:block absolute top-1/2 -right-3 w-6 h-px bg-gradient-to-r from-primary to-muted z-10">
                    {isRunning && index <= currentStep && (
                      <div className="w-2 h-2 bg-primary rounded-full absolute -top-0.5 right-0 animate-pulse" />
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Real-time Metrics */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <Card className="glass border-0">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-muted-foreground">Accuracy</span>
                <TrendingUp className="w-4 h-4 text-green-500" />
              </div>
              <div className="text-2xl font-bold bg-tech-gradient bg-clip-text text-transparent mb-2">
                {(metrics.accuracy * 100).toFixed(1)}%
              </div>
              <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-green-500 to-green-600 transition-all duration-500"
                  style={{ width: `${metrics.accuracy * 100}%` }}
                />
              </div>
            </CardContent>
          </Card>

          <Card className="glass border-0">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-muted-foreground">Loss</span>
                <Target className="w-4 h-4 text-red-500" />
              </div>
              <div className="text-2xl font-bold bg-tech-gradient bg-clip-text text-transparent mb-2">
                {metrics.loss.toFixed(3)}
              </div>
              <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-red-500 to-orange-500 transition-all duration-500"
                  style={{ width: `${(1 - metrics.loss) * 100}%` }}
                />
              </div>
            </CardContent>
          </Card>

          <Card className="glass border-0">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-muted-foreground">Epoch</span>
                <RefreshCw className="w-4 h-4 text-blue-500" />
              </div>
              <div className="text-2xl font-bold bg-tech-gradient bg-clip-text text-transparent mb-2">
                {metrics.epoch}
              </div>
              <div className="text-xs text-muted-foreground">Iteraciones completadas</div>
            </CardContent>
          </Card>

          <Card className="glass border-0">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-muted-foreground">Throughput</span>
                <Cpu className="w-4 h-4 text-purple-500" />
              </div>
              <div className="text-2xl font-bold bg-tech-gradient bg-clip-text text-transparent mb-2">
                {Math.floor(metrics.throughput)}
              </div>
              <div className="text-xs text-muted-foreground">samples/sec</div>
            </CardContent>
          </Card>
        </div>

        {/* Model Architecture Visualization */}
        <div className="glass rounded-2xl p-8">
          <h3 className="text-2xl font-bold text-center mb-8">Arquitectura Neural en Tiempo Real</h3>
          
          <div className="grid md:grid-cols-3 gap-8 items-center">
            {/* Input Layer */}
            <div className="text-center">
              <h4 className="font-bold mb-4">Input Layer</h4>
              <div className="space-y-2">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className={`w-8 h-8 mx-auto rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 ${
                    isRunning ? 'animate-pulse' : ''
                  }`} style={{ animationDelay: `${i * 0.1}s` }} />
                ))}
              </div>
            </div>

            {/* Hidden Layers */}
            <div className="text-center">
              <h4 className="font-bold mb-4">Hidden Layers</h4>
              <div className="grid grid-cols-3 gap-2">
                {[...Array(9)].map((_, i) => (
                  <div key={i} className={`w-6 h-6 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 ${
                    isRunning ? 'animate-quantum-pulse' : ''
                  }`} style={{ animationDelay: `${i * 0.05}s` }} />
                ))}
              </div>
            </div>

            {/* Output Layer */}
            <div className="text-center">
              <h4 className="font-bold mb-4">Output Layer</h4>
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className={`w-8 h-8 mx-auto rounded-full bg-gradient-to-r from-green-500 to-emerald-500 ${
                    isRunning ? 'animate-bounce' : ''
                  }`} style={{ animationDelay: `${i * 0.2}s` }} />
                ))}
              </div>
            </div>
          </div>

          {/* Neural Connections Visualization */}
          <div className="mt-8 h-32 relative overflow-hidden rounded-lg bg-gradient-to-r from-muted/50 to-transparent">
            {isRunning && [...Array(20)].map((_, i) => (
              <div
                key={i}
                className="absolute w-px h-px bg-primary rounded-full animate-neural-spark opacity-60"
                style={{
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  animationDelay: `${Math.random() * 2}s`,
                  animationDuration: `${1 + Math.random()}s`
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default MLPipelineSection;
