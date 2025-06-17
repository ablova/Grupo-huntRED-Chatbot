
import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, Atom, Zap, Brain, Sparkles, Activity, Database, Cpu } from 'lucide-react';

const QuantumLabSection = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [activeExperiment, setActiveExperiment] = useState(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    const atoms: Array<{
      x: number;
      y: number;
      radius: number;
      angle: number;
      speed: number;
      color: string;
      electrons: Array<{ angle: number; distance: number; speed: number }>;
    }> = [];

    // Create quantum atoms
    for (let i = 0; i < 8; i++) {
      atoms.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        radius: Math.random() * 30 + 20,
        angle: Math.random() * Math.PI * 2,
        speed: (Math.random() - 0.5) * 0.02,
        color: ['#3b82f6', '#8b5cf6', '#06b6d4', '#ec4899'][Math.floor(Math.random() * 4)],
        electrons: Array.from({ length: Math.floor(Math.random() * 3) + 2 }, () => ({
          angle: Math.random() * Math.PI * 2,
          distance: Math.random() * 20 + 15,
          speed: Math.random() * 0.1 + 0.05
        }))
      });
    }

    function animate() {
      if (!ctx || !canvas) return;
      
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      atoms.forEach(atom => {
        atom.angle += atom.speed;
        
        // Draw atom nucleus
        ctx.beginPath();
        ctx.arc(atom.x, atom.y, 8, 0, Math.PI * 2);
        ctx.fillStyle = atom.color;
        ctx.globalAlpha = 0.8;
        ctx.fill();
        
        // Draw electron orbits and electrons
        atom.electrons.forEach(electron => {
          electron.angle += electron.speed;
          
          // Orbit
          ctx.beginPath();
          ctx.arc(atom.x, atom.y, electron.distance, 0, Math.PI * 2);
          ctx.strokeStyle = atom.color;
          ctx.globalAlpha = 0.2;
          ctx.lineWidth = 1;
          ctx.stroke();
          
          // Electron
          const electronX = atom.x + Math.cos(electron.angle) * electron.distance;
          const electronY = atom.y + Math.sin(electron.angle) * electron.distance;
          
          ctx.beginPath();
          ctx.arc(electronX, electronY, 3, 0, Math.PI * 2);
          ctx.fillStyle = atom.color;
          ctx.globalAlpha = 1;
          ctx.fill();
        });
        
        // Quantum entanglement lines
        atoms.forEach(otherAtom => {
          if (otherAtom !== atom) {
            const dx = atom.x - otherAtom.x;
            const dy = atom.y - otherAtom.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < 150) {
              ctx.beginPath();
              ctx.moveTo(atom.x, atom.y);
              ctx.lineTo(otherAtom.x, otherAtom.y);
              ctx.strokeStyle = atom.color;
              ctx.globalAlpha = 0.1 * (1 - distance / 150);
              ctx.lineWidth = 2;
              ctx.stroke();
            }
          }
        });
      });

      ctx.globalAlpha = 1;
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

  const experiments = [
    {
      title: "Computación Cuántica Neural",
      description: "Algoritmos híbridos que combinan qubits con redes neuronales para procesamiento hiperdimensional",
      status: "En Progreso",
      progress: 78,
      icon: Atom,
      gradient: "from-blue-400 to-cyan-600",
      features: ["Q-Learning", "Quantum Gates", "Neural Superposition", "Entangled Networks"]
    },
    {
      title: "Consciencia Artificial Emergente",
      description: "Investigación en la creación de sistemas con auto-conciencia y razonamiento abstracto",
      status: "Experimental",
      progress: 34,
      icon: Brain,
      gradient: "from-purple-400 to-pink-600",
      features: ["Self-Reflection", "Abstract Reasoning", "Emotional AI", "Creative Thinking"]
    },
    {
      title: "Realidad Aumentada Neural",
      description: "Interfaces cerebro-computadora para interacción directa con sistemas de IA",
      status: "Prototipo",
      progress: 62,
      icon: Zap,
      gradient: "from-cyan-400 to-blue-600",
      features: ["Brain-Computer Interface", "Neural Feedback", "AR Overlay", "Thought Control"]
    },
    {
      title: "Singularidad Tecnológica",
      description: "Desarrollo de IA recursiva capaz de mejorarse a sí misma exponencialmente",
      status: "Teórico",
      progress: 12,
      icon: Sparkles,
      gradient: "from-pink-400 to-red-600",
      features: ["Self-Improvement", "Recursive Enhancement", "Exponential Growth", "Transcendence"]
    }
  ];

  const metrics = [
    { label: "Experimentos Activos", value: "47", icon: Activity, color: "text-blue-400" },
    { label: "Modelos Evolutivos", value: "23", icon: Brain, color: "text-purple-400" },
    { label: "Qubits Simulados", value: "1,024", icon: Atom, color: "text-cyan-400" },
    { label: "Dimensiones Paralelas", value: "∞", icon: Database, color: "text-pink-400" }
  ];

  return (
    <section id="quantum-lab" className="py-20 bg-background relative overflow-hidden">
      {/* Quantum Animation Background */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full opacity-20"
        style={{ background: 'transparent' }}
      />
      
      {/* Quantum Energy Fields */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-purple-500/5 to-cyan-500/5" />
      <div className="absolute top-20 left-20 w-96 h-96 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-full blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-20 right-20 w-64 h-64 bg-gradient-to-r from-cyan-500/10 to-pink-500/10 rounded-full blur-2xl animate-float" />
      
      <div className="container mx-auto px-4 lg:px-8 relative z-10">
        <div className="text-center space-y-4 mb-16">
          <div className="inline-flex items-center space-x-2 glass rounded-full px-6 py-2 border border-primary/20">
            <Atom className="h-5 w-5 text-primary animate-spin-slow" />
            <span className="text-sm font-medium">LABORATORIO CUÁNTICO</span>
          </div>
          
          <h2 className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-blue-400 via-purple-500 to-cyan-400 bg-clip-text text-transparent">
            Investigación de
            <br />
            <span className="animate-pulse">Vanguardia</span>
          </h2>
          
          <p className="text-xl text-muted-foreground max-w-4xl mx-auto">
            Explorando los límites de la inteligencia artificial y la computación cuántica
          </p>
        </div>

        {/* Quantum Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-16">
          {metrics.map((metric, index) => (
            <Card key={index} className="glass border-primary/20 text-center hover:scale-105 transition-all duration-300">
              <CardContent className="p-6">
                <metric.icon className={`h-8 w-8 mx-auto mb-2 ${metric.color} animate-pulse`} />
                <div className="text-2xl font-bold text-gradient">{metric.value}</div>
                <div className="text-sm text-muted-foreground">{metric.label}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Quantum Experiments */}
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          {experiments.map((experiment, index) => (
            <Card 
              key={index} 
              className={`glass border-2 transition-all duration-500 hover:scale-105 cursor-pointer ${
                activeExperiment === index 
                  ? 'border-primary/50 shadow-2xl' 
                  : 'border-primary/20 hover:border-primary/40'
              }`}
              onClick={() => setActiveExperiment(index)}
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-12 h-12 bg-gradient-to-r ${experiment.gradient} rounded-xl flex items-center justify-center`}>
                      <experiment.icon className="h-6 w-6 text-white animate-pulse" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{experiment.title}</CardTitle>
                      <Badge variant={experiment.status === 'En Progreso' ? 'default' : 'secondary'}>
                        {experiment.status}
                      </Badge>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-muted-foreground">Progreso</div>
                    <div className="text-xl font-bold text-gradient">{experiment.progress}%</div>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">{experiment.description}</p>
                
                {/* Progress Bar */}
                <div className="w-full bg-muted rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full bg-gradient-to-r ${experiment.gradient} transition-all duration-1000`}
                    style={{ width: `${experiment.progress}%` }}
                  />
                </div>
                
                {/* Features */}
                <div className="grid grid-cols-2 gap-2">
                  {experiment.features.map((feature, featureIndex) => (
                    <div key={featureIndex} className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${experiment.gradient}`} />
                      <span className="text-xs">{feature}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Research Collaboration */}
        <Card className="glass border-primary/20 hyperdimensional-border">
          <CardContent className="p-8 text-center space-y-6">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <Cpu className="h-8 w-8 text-primary animate-quantum-pulse" />
              <h3 className="text-2xl font-bold">Colaboración en Investigación</h3>
            </div>
            
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Únete a nuestro laboratorio cuántico y contribuye al desarrollo de las próximas 
              generaciones de inteligencia artificial.
            </p>
            
            <div className="grid md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <Brain className="h-12 w-12 mx-auto text-blue-400 animate-pulse" />
                <h4 className="font-semibold">Investigación Colaborativa</h4>
                <p className="text-sm text-muted-foreground">Acceso a experimentos de vanguardia</p>
              </div>
              <div className="space-y-2">
                <Atom className="h-12 w-12 mx-auto text-purple-400 animate-spin-slow" />
                <h4 className="font-semibold">Recursos Cuánticos</h4>
                <p className="text-sm text-muted-foreground">Simuladores y hardware especializado</p>
              </div>
              <div className="space-y-2">
                <Sparkles className="h-12 w-12 mx-auto text-cyan-400 animate-bounce" />
                <h4 className="font-semibold">Publicaciones</h4>
                <p className="text-sm text-muted-foreground">Co-autoría en papers científicos</p>
              </div>
            </div>
            
            <Button size="lg" className="btn-gradient mt-6">
              Solicitar Acceso al Laboratorio
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </CardContent>
        </Card>
      </div>
    </section>
  );
};

export default QuantumLabSection;
