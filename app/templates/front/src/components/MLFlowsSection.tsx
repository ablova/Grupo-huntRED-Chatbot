
import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowRight, ArrowLeft, Cpu, Database, Zap, Brain, Activity, Sparkles } from 'lucide-react';

const MLFlowsSection = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [activeFlow, setActiveFlow] = useState(0);

  // Particle system for background animation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    const particles: Array<{
      x: number;
      y: number;
      dx: number;
      dy: number;
      size: number;
      color: string;
      opacity: number;
    }> = [];

    // Create particles
    for (let i = 0; i < 50; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        dx: (Math.random() - 0.5) * 0.5,
        dy: (Math.random() - 0.5) * 0.5,
        size: Math.random() * 3 + 1,
        color: Math.random() > 0.5 ? '#3b82f6' : '#8b5cf6',
        opacity: Math.random() * 0.5 + 0.3
      });
    }

    function animate() {
      if (!ctx || !canvas) return;
      
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw connections between nearby particles
      particles.forEach((particle, i) => {
        particles.slice(i + 1).forEach(otherParticle => {
          const dx = particle.x - otherParticle.x;
          const dy = particle.y - otherParticle.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < 100) {
            ctx.beginPath();
            ctx.moveTo(particle.x, particle.y);
            ctx.lineTo(otherParticle.x, otherParticle.y);
            ctx.strokeStyle = `rgba(59, 130, 246, ${0.1 * (1 - distance / 100)})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        });
      });

      // Update and draw particles
      particles.forEach(particle => {
        particle.x += particle.dx;
        particle.y += particle.dy;

        if (particle.x < 0 || particle.x > canvas.width) particle.dx *= -1;
        if (particle.y < 0 || particle.y > canvas.height) particle.dy *= -1;

        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = particle.color;
        ctx.globalAlpha = particle.opacity;
        ctx.fill();
        ctx.globalAlpha = 1;
      });

      requestAnimationFrame(animate);
    }

    animate();

    const handleResize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const flows = [
    {
      id: 'input',
      title: "Flujo de Entrada Neural",
      description: "Ingesta ultrarrápida con IA cuántica",
      steps: [
        { name: "Captura Sensorial", icon: Activity, color: "text-cyan-400" },
        { name: "Validación Cuántica", icon: Zap, color: "text-blue-400" },
        { name: "Normalización 5D", icon: Database, color: "text-purple-400" },
        { name: "Enriquecimiento", icon: Sparkles, color: "text-pink-400" }
      ],
      direction: "right",
      gradient: "from-cyan-500 via-blue-500 to-purple-500"
    },
    {
      id: 'processing',
      title: "Flujo de Procesamiento Cuántico",
      description: "Análisis hiperdimensional con neuronas sintéticas",
      steps: [
        { name: "Feature Synthesis", icon: Brain, color: "text-purple-400" },
        { name: "Neural Training", icon: Cpu, color: "text-pink-400" },
        { name: "Quantum Validation", icon: Zap, color: "text-cyan-400" },
        { name: "Hyperstatic Optimization", icon: Sparkles, color: "text-blue-400" }
      ],
      direction: "left",
      gradient: "from-purple-500 via-pink-500 to-cyan-500"
    }
  ];

  const architectureLayers = [
    {
      name: "Capa de Experiencia Cuántica",
      description: "Interfaces neuromórficas y APIs hiperdimensionales",
      technologies: ["React Quantum", "Neural REST", "GraphQL 5D", "Holographic Apps"],
      position: "top",
      icon: Activity,
      gradient: "from-cyan-400 to-blue-500"
    },
    {
      name: "Capa de Inteligencia Sintética",
      description: "Modelos de consciencia artificial y procesamiento hiperespacial",
      technologies: ["TensorFlow Quantum", "PyTorch Neural", "Scikit-Hyper", "Custom Consciousness"],
      position: "middle",
      icon: Brain,
      gradient: "from-purple-500 to-pink-500"
    },
    {
      name: "Núcleo Hiperdimensional",
      description: "Infraestructura cuántica y gestión de datos multiversal",
      technologies: ["Kubernetes 5D", "Docker Quantum", "PostgreSQL Neural", "Redis Hyperspatial"],
      position: "bottom",
      icon: Database,
      gradient: "from-pink-500 to-cyan-400"
    }
  ];

  return (
    <section id="ml-flows" className="py-20 bg-background relative overflow-hidden">
      {/* Animated Background Canvas */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full opacity-30"
        style={{ background: 'transparent' }}
      />
      
      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-blue-500/5 to-purple-500/10" />
      
      <div className="container mx-auto px-4 lg:px-8 relative z-10">
        <div className="text-center space-y-4 mb-16">
          <div className="inline-flex items-center space-x-2 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 backdrop-blur-sm rounded-full px-6 py-2 border border-cyan-500/30">
            <Sparkles className="h-5 w-5 text-cyan-400" />
            <span className="text-sm font-medium text-cyan-300">ARQUITECTURA HIPERDIMENSIONAL</span>
          </div>
          
          <h2 className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent">
            Flujos Cuánticos de
            <br />
            <span className="animate-pulse">Inteligencia Neural</span>
          </h2>
          
          <p className="text-xl text-muted-foreground max-w-4xl mx-auto">
            Arquitectura hiperdimensional con flujos bidireccionales que procesan datos en múltiples realidades paralelas
          </p>
        </div>

        {/* Ultra Radical Flows */}
        <div className="space-y-20 mb-32">
          {flows.map((flow, index) => (
            <div 
              key={flow.id} 
              className={`relative ${flow.direction === 'left' ? 'flex-row-reverse' : ''} flex items-center`}
              onMouseEnter={() => setActiveFlow(index)}
            >
              {/* Flow Container */}
              <div className="flex-1 relative">
                <Card className={`glass border-2 transition-all duration-500 hover:scale-105 ${
                  activeFlow === index 
                    ? 'border-cyan-400/50 shadow-2xl shadow-cyan-500/25' 
                    : 'border-primary/20'
                }`}>
                  <CardContent className="p-8">
                    <div className="space-y-6">
                      {/* Flow Header */}
                      <div className="flex items-center space-x-4">
                        <div className={`w-4 h-4 bg-gradient-to-r ${flow.gradient} rounded-full animate-pulse`} />
                        <h3 className={`text-2xl font-bold bg-gradient-to-r ${flow.gradient} bg-clip-text text-transparent`}>
                          {flow.title}
                        </h3>
                      </div>
                      
                      <p className="text-muted-foreground text-lg">{flow.description}</p>
                      
                      {/* Interactive Steps */}
                      <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 ${flow.direction === 'left' ? 'order-reverse' : ''}`}>
                        {flow.steps.map((step, stepIndex) => (
                          <div 
                            key={stepIndex}
                            className="relative group"
                          >
                            <div className="glass rounded-xl p-4 text-center transition-all duration-300 hover:scale-110 hover:bg-gradient-to-br hover:from-cyan-500/10 hover:to-purple-500/10 border border-white/10 hover:border-cyan-400/30">
                              <step.icon className={`h-8 w-8 mx-auto mb-2 ${step.color} group-hover:animate-pulse`} />
                              <span className="text-sm font-medium">{step.name}</span>
                            </div>
                            
                            {/* Connection Lines */}
                            {stepIndex < flow.steps.length - 1 && (
                              <div className={`absolute top-1/2 ${flow.direction === 'right' ? 'right-0 translate-x-2' : 'left-0 -translate-x-2'} hidden md:block`}>
                                <div className={`w-4 h-0.5 bg-gradient-to-r ${flow.gradient} animate-pulse`} />
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
              
              {/* Ultra Radical Central Hub */}
              <div className="px-12 relative">
                <div className={`w-20 h-20 bg-gradient-to-r ${flow.gradient} rounded-full flex items-center justify-center animate-spin-slow relative`}>
                  <div className="w-16 h-16 bg-background rounded-full flex items-center justify-center">
                    {flow.direction === 'right' ? 
                      <ArrowRight className="h-8 w-8 text-cyan-400 animate-bounce" /> :
                      <ArrowLeft className="h-8 w-8 text-purple-400 animate-bounce" />
                    }
                  </div>
                  
                  {/* Orbital Particles */}
                  <div className="absolute inset-0 animate-spin">
                    <div className="absolute top-0 left-1/2 w-2 h-2 bg-cyan-400 rounded-full -translate-x-1/2 -translate-y-1" />
                    <div className="absolute bottom-0 left-1/2 w-2 h-2 bg-purple-400 rounded-full -translate-x-1/2 translate-y-1" />
                  </div>
                </div>
                
                {/* Energy Rings */}
                <div className="absolute inset-0 animate-ping">
                  <div className={`w-full h-full rounded-full border-2 border-gradient-to-r ${flow.gradient} opacity-20`} />
                </div>
              </div>
              
              <div className="flex-1" />
            </div>
          ))}
        </div>

        {/* Hyperdimensional Architecture */}
        <div className="space-y-8">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-600 bg-clip-text text-transparent mb-4">
              Arquitectura Hiperdimensional
            </h3>
            <p className="text-muted-foreground">Capas interconectadas que operan en múltiples dimensiones simultáneamente</p>
          </div>
          
          <div className="relative">
            {architectureLayers.map((layer, index) => (
              <Card 
                key={index} 
                className={`glass border-2 border-white/10 mb-6 transform transition-all duration-500 hover:scale-105 hover:border-cyan-400/30 group ${
                  layer.position === 'top' ? 'animate-slide-in-right' :
                  layer.position === 'middle' ? 'animate-fade-in-up' :
                  'animate-slide-in-left'
                }`} 
                style={{ animationDelay: `${index * 0.3}s` }}
              >
                <CardContent className="p-8">
                  <div className="grid md:grid-cols-4 gap-6 items-center">
                    <div className="flex items-center space-x-4">
                      <div className={`w-16 h-16 bg-gradient-to-r ${layer.gradient} rounded-xl flex items-center justify-center group-hover:animate-pulse`}>
                        <layer.icon className="h-8 w-8 text-white" />
                      </div>
                      <div>
                        <h4 className={`text-lg font-bold bg-gradient-to-r ${layer.gradient} bg-clip-text text-transparent`}>
                          {layer.name}
                        </h4>
                        <p className="text-muted-foreground text-sm">{layer.description}</p>
                      </div>
                    </div>
                    
                    <div className="md:col-span-3">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {layer.technologies.map((tech, techIndex) => (
                          <div 
                            key={techIndex} 
                            className="glass rounded-full px-4 py-2 text-center text-sm font-medium transition-all duration-300 hover:scale-110 hover:bg-gradient-to-r hover:from-cyan-500/20 hover:to-purple-500/20 border border-white/10 hover:border-cyan-400/30"
                          >
                            {tech}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            
            {/* Quantum Connection Grid */}
            <div className="absolute left-8 top-0 bottom-0 w-1 bg-gradient-to-b from-cyan-400 via-purple-500 to-pink-400 opacity-30" />
            
            {/* Quantum Nodes */}
            {architectureLayers.map((_, index) => (
              <div 
                key={index} 
                className="absolute left-6 w-5 h-5 bg-gradient-to-r from-cyan-400 to-purple-500 rounded-full animate-pulse border-2 border-background" 
                style={{ top: `${(index + 0.5) * 33.33}%`, transform: 'translateY(-50%)' }} 
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default MLFlowsSection;
