
import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, Globe, Headphones, Gamepad2, Users, Zap, Cpu, Eye, Sparkles } from 'lucide-react';

const MetaverseSection = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [activeWorld, setActiveWorld] = useState(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    const nodes: Array<{
      x: number;
      y: number;
      z: number;
      vx: number;
      vy: number;
      vz: number;
      color: string;
      size: number;
      connections: number[];
    }> = [];

    // Create 3D metaverse nodes
    for (let i = 0; i < 30; i++) {
      nodes.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        z: Math.random() * 200 - 100,
        vx: (Math.random() - 0.5) * 2,
        vy: (Math.random() - 0.5) * 2,
        vz: (Math.random() - 0.5) * 2,
        color: ['#3b82f6', '#8b5cf6', '#06b6d4', '#ec4899', '#f59e0b'][Math.floor(Math.random() * 5)],
        size: Math.random() * 8 + 4,
        connections: []
      });
    }

    // Create connections between nearby nodes
    nodes.forEach((node, i) => {
      nodes.forEach((otherNode, j) => {
        if (i !== j) {
          const distance = Math.sqrt(
            Math.pow(node.x - otherNode.x, 2) + 
            Math.pow(node.y - otherNode.y, 2) + 
            Math.pow(node.z - otherNode.z, 2)
          );
          if (distance < 120 && node.connections.length < 3) {
            node.connections.push(j);
          }
        }
      });
    });

    function animate() {
      if (!ctx || !canvas) return;
      
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Update node positions
      nodes.forEach(node => {
        node.x += node.vx;
        node.y += node.vy;
        node.z += node.vz;

        // Bounce off edges
        if (node.x < 0 || node.x > canvas.width) node.vx *= -1;
        if (node.y < 0 || node.y > canvas.height) node.vy *= -1;
        if (node.z < -100 || node.z > 100) node.vz *= -1;
      });

      // Draw connections
      nodes.forEach((node, i) => {
        node.connections.forEach(connectionIndex => {
          const connectedNode = nodes[connectionIndex];
          
          ctx.beginPath();
          ctx.moveTo(node.x, node.y);
          ctx.lineTo(connectedNode.x, connectedNode.y);
          
          const distance = Math.sqrt(
            Math.pow(node.x - connectedNode.x, 2) + 
            Math.pow(node.y - connectedNode.y, 2)
          );
          
          ctx.strokeStyle = node.color;
          ctx.globalAlpha = Math.max(0.1, 1 - distance / 120);
          ctx.lineWidth = 2;
          ctx.stroke();
        });
      });

      // Draw nodes with 3D effect
      nodes.forEach(node => {
        const perspective = 200 / (200 + node.z);
        const size = node.size * perspective;
        
        ctx.beginPath();
        ctx.arc(node.x, node.y, size, 0, Math.PI * 2);
        ctx.fillStyle = node.color;
        ctx.globalAlpha = 0.8 * perspective;
        ctx.fill();
        
        // Add glow effect
        ctx.beginPath();
        ctx.arc(node.x, node.y, size * 1.5, 0, Math.PI * 2);
        ctx.fillStyle = node.color;
        ctx.globalAlpha = 0.2 * perspective;
        ctx.fill();
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

  const metaverseWorlds = [
    {
      title: "Neural Academy",
      description: "Campus virtual donde la IA enseña a través de experiencias inmersivas",
      participants: "15.2K",
      icon: Users,
      gradient: "from-blue-400 to-cyan-600",
      features: ["Tutores Holográficos", "Laboratorios Virtuales", "Simulaciones Cuánticas", "Evaluación Neural"]
    },
    {
      title: "Quantum Workspace",
      description: "Oficinas virtuales con colaboración aumentada por inteligencia artificial",
      participants: "8.7K",
      icon: Cpu,
      gradient: "from-purple-400 to-pink-600",
      features: ["Meetings Holográficos", "IA Asistente", "Datos 3D", "Productividad Neural"]
    },
    {
      title: "Digital Twin City",
      description: "Réplica digital de ciudades reales para simulación y planificación urbana",
      participants: "32.1K",
      icon: Globe,
      gradient: "from-green-400 to-emerald-600",
      features: ["Gemelos Digitales", "Simulación Urbana", "IoT Virtual", "Predicción Climática"]
    },
    {
      title: "Creative Nexus",
      description: "Estudio de arte colaborativo donde humanos e IA crean juntos",
      participants: "11.8K",
      icon: Sparkles,
      gradient: "from-orange-400 to-red-600",
      features: ["Arte Generativo", "Colaboración IA", "Galería Virtual", "NFT Inteligentes"]
    }
  ];

  const technologies = [
    { name: "Realidad Virtual", icon: Headphones, progress: 95 },
    { name: "Realidad Aumentada", icon: Eye, progress: 88 },
    { name: "Inteligencia Artificial", icon: Cpu, progress: 92 },
    { name: "Blockchain", icon: Zap, progress: 76 },
    { name: "Computación Cuántica", icon: Sparkles, progress: 68 },
    { name: "Haptic Feedback", icon: Gamepad2, progress: 84 }
  ];

  return (
    <section id="metaverse" className="py-20 bg-muted/30 relative overflow-hidden">
      {/* 3D Network Background */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full opacity-20"
        style={{ background: 'transparent' }}
      />
      
      {/* Ambient Effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-purple-500/5 to-cyan-500/5" />
      <div className="absolute top-10 left-10 w-72 h-72 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-full blur-3xl animate-float" />
      <div className="absolute bottom-10 right-10 w-96 h-96 bg-gradient-to-r from-cyan-500/10 to-pink-500/10 rounded-full blur-3xl animate-float-delay" />
      
      <div className="container mx-auto px-4 lg:px-8 relative z-10">
        <div className="text-center space-y-4 mb-16">
          <div className="inline-flex items-center space-x-2 glass rounded-full px-6 py-2 border border-primary/20">
            <Globe className="h-5 w-5 text-primary animate-spin-slow" />
            <span className="text-sm font-medium">METAVERSO IA</span>
          </div>
          
          <h2 className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-blue-400 via-purple-500 to-cyan-400 bg-clip-text text-transparent">
            Mundos Virtuales
            <br />
            <span className="animate-pulse">Inteligentes</span>
          </h2>
          
          <p className="text-xl text-muted-foreground max-w-4xl mx-auto">
            Espacios digitales donde la inteligencia artificial amplifica la creatividad y colaboración humana
          </p>
        </div>

        {/* Technology Progress */}
        <Card className="glass border-primary/20 mb-16">
          <CardHeader>
            <CardTitle className="text-center">Stack Tecnológico del Metaverso</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {technologies.map((tech, index) => (
                <div key={index} className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <tech.icon className="h-5 w-5 text-primary" />
                    <span className="font-medium">{tech.name}</span>
                    <span className="text-sm text-muted-foreground">{tech.progress}%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div 
                      className="h-2 rounded-full bg-tech-gradient transition-all duration-1000"
                      style={{ width: `${tech.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Metaverse Worlds */}
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          {metaverseWorlds.map((world, index) => (
            <Card 
              key={index}
              className={`glass border-2 transition-all duration-500 hover:scale-105 cursor-pointer neural-connection ${
                activeWorld === index 
                  ? 'border-primary/50 shadow-2xl' 
                  : 'border-primary/20 hover:border-primary/40'
              }`}
              onClick={() => setActiveWorld(index)}
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-12 h-12 bg-gradient-to-r ${world.gradient} rounded-xl flex items-center justify-center`}>
                      <world.icon className="h-6 w-6 text-white animate-pulse" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{world.title}</CardTitle>
                      <Badge variant="secondary" className="mt-1">
                        {world.participants} usuarios
                      </Badge>
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="w-4 h-4 bg-green-400 rounded-full animate-pulse mb-1" />
                    <span className="text-xs text-muted-foreground">En Vivo</span>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">{world.description}</p>
                
                <div className="grid grid-cols-2 gap-2">
                  {world.features.map((feature, featureIndex) => (
                    <div key={featureIndex} className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${world.gradient}`} />
                      <span className="text-xs">{feature}</span>
                    </div>
                  ))}
                </div>
                
                <Button size="sm" className={`w-full bg-gradient-to-r ${world.gradient} hover:opacity-90`}>
                  Acceder al Mundo
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Developer Portal */}
        <Card className="glass border-primary/20 hyperdimensional-border">
          <CardContent className="p-8 text-center space-y-6">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <Gamepad2 className="h-8 w-8 text-primary animate-bounce" />
              <h3 className="text-2xl font-bold">Portal de Desarrolladores</h3>
            </div>
            
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Crea tus propios mundos virtuales con nuestras herramientas de desarrollo 
              potenciadas por inteligencia artificial.
            </p>
            
            <div className="grid md:grid-cols-4 gap-6">
              <div className="space-y-2">
                <Cpu className="h-12 w-12 mx-auto text-blue-400 animate-pulse" />
                <h4 className="font-semibold">SDK Neural</h4>
                <p className="text-sm text-muted-foreground">Herramientas de desarrollo avanzadas</p>
              </div>
              <div className="space-y-2">
                <Users className="h-12 w-12 mx-auto text-purple-400 animate-bounce" />
                <h4 className="font-semibold">Comunidad</h4>
                <p className="text-sm text-muted-foreground">Red de desarrolladores activa</p>
              </div>
              <div className="space-y-2">
                <Zap className="h-12 w-12 mx-auto text-cyan-400 animate-spin-slow" />
                <h4 className="font-semibold">IA Asistente</h4>
                <p className="text-sm text-muted-foreground">Copiloto para el desarrollo</p>
              </div>
              <div className="space-y-2">
                <Globe className="h-12 w-12 mx-auto text-green-400 animate-float" />
                <h4 className="font-semibold">Marketplace</h4>
                <p className="text-sm text-muted-foreground">Monetiza tus creaciones</p>
              </div>
            </div>
            
            <Button size="lg" className="btn-gradient mt-6">
              Empezar a Desarrollar
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </CardContent>
        </Card>
      </div>
    </section>
  );
};

export default MetaverseSection;
