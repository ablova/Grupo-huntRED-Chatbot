
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ArrowRight, Calendar, Brain, Target, Sparkles } from 'lucide-react';

const HeroSection = () => {
  const [currentSlide, setCurrentSlide] = useState(0);

  const slides = [
    {
      title: "Grupo huntRED® y su Ecosistema de Inteligencia Artificial ",
      subtitle: "Procesos de reclutamiento y desarollo organizacional mejorados",
      description: "Potencia tu estructura mediante atracción de talento más preciso, acorde e integrado.",
      cta: "Descubrir GenIA",
      image: "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      icon: Sparkles,
      color: "from-blue-600 to-cyan-600"
    },
    {
      title: "GenIA: Inteligencia Artificial Generativa",
      subtitle: "Chatbots conversacionales, matchmaking y workflows asistidos por AI",
      description: "Ya sea en modo híbrido, o totalmente automatizado, mejoramos la atracción de talento y el conocimiento de las áreas.",
      cta: "Descubrir GenIA",
      image: "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      icon: Sparkles,
      color: "from-blue-600 to-cyan-600"
    },
    {
      title: "AURA: Motor de Desarrollo Profesional",
      subtitle: "Análisis de brechas de habilidades y networking inteligente",
      description: "Revoluciona el desarrollo profesional con análisis inteligente, rutas de aprendizaje personalizadas y conexiones estratégicas.",
      cta: "Conocer AURA",
      image: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      icon: Target,
      color: "from-purple-600 to-pink-600"
    },
    {
      title: "GenIA & AURA: El Futuro de la IA",
      subtitle: "Ecosistema completo de Inteligencia Artificial para transformar tu talento",
      description: "GenIA para la atracción y creación de cultura, AURA para el desarrollo profesional. Una plataforma unificada que revoluciona la forma en que gestionamos RH.",
      cta: "Explorar Ecosistema",
      image: "https://images.unsplash.com/photo-1518770660439-4636190af475?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      icon: Brain,
      color: "from-blue-600 to-purple-600"
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  const IconComponent = slides[currentSlide].icon;

  return (
    <section id="hero" className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Pattern - removed overlay that was causing transparency issue */}
      <div className="absolute inset-0 bg-hero-pattern" />
      
      {/* Floating Elements */}
      <div className="absolute top-20 left-10 w-20 h-20 bg-tech-blue/20 rounded-full animate-float" />
      <div className="absolute top-40 right-20 w-16 h-16 bg-tech-purple/20 rounded-full animate-float" style={{ animationDelay: '2s' }} />
      <div className="absolute bottom-40 left-20 w-12 h-12 bg-tech-cyan/20 rounded-full animate-float" style={{ animationDelay: '4s' }} />

      <div className="container mx-auto px-4 lg:px-8 pt-16 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Content */}
          <div className="space-y-8 animate-fade-in-up">
            <div className="space-y-4">
              {/* Badge */}
              <div className="inline-flex items-center space-x-2 glass rounded-full px-4 py-2 border border-primary/20">
                <IconComponent className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium">GRUPO HUNTRED® AI</span>
              </div>
              
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight">
                {slides[currentSlide].title.split(' ').map((word, index) => (
                  <span 
                    key={index} 
                    className={index >= 2 ? `bg-gradient-to-r ${slides[currentSlide].color} bg-clip-text text-transparent` : ''}
                  >
                    {word}{' '}
                  </span>
                ))}
              </h1>
              <p className="text-xl md:text-2xl text-muted-foreground">
                {slides[currentSlide].subtitle}
              </p>
              <p className="text-lg text-muted-foreground max-w-2xl">
                {slides[currentSlide].description}
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button size="lg" className={`bg-gradient-to-r ${slides[currentSlide].color} hover:opacity-90 transition-opacity`}>
                <Calendar className="mr-2 h-5 w-5" />
                Agendar Demo
              </Button>
              <Button size="lg" variant="outline" className="border-primary/30 hover:bg-primary/10">
                {slides[currentSlide].cta}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </div>

            {/* Slide Indicators */}
            <div className="flex space-x-2">
              {slides.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentSlide(index)}
                  className={`w-3 h-3 rounded-full transition-all ${
                    index === currentSlide ? 'bg-primary scale-110' : 'bg-muted-foreground/30'
                  }`}
                />
              ))}
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-4 pt-4">
              <div className="text-center">
                <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">1M+</div>
                <div className="text-sm text-muted-foreground">Interacciones</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">50K+</div>
                <div className="text-sm text-muted-foreground">Usuarios</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">99.9%</div>
                <div className="text-sm text-muted-foreground">Uptime</div>
              </div>
            </div>
          </div>

          {/* Visual */}
          <div className="relative animate-slide-in-right">
            <div className="relative w-full h-[500px] rounded-2xl overflow-hidden glass">
              <img
                src={slides[currentSlide].image}
                alt="AI Technology"
                className="w-full h-full object-cover transition-transform duration-1000 hover:scale-105"
              />
              <div className={`absolute inset-0 bg-gradient-to-r ${slides[currentSlide].color} opacity-20`} />
              
              {/* Tech Overlay */}
              <div className="absolute top-4 left-4 glass rounded-lg p-3">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-sm font-medium">AI System Active</span>
                </div>
              </div>
              
              <div className="absolute bottom-4 right-4 glass rounded-lg p-3">
                <div className="text-sm">
                  <div className="font-semibold">99.7%</div>
                  <div className="text-muted-foreground">Accuracy</div>
                </div>
              </div>
            </div>

            {/* Floating Stats */}
            <div className="absolute -top-6 -right-6 glass rounded-xl p-4 animate-float">
              <div className="text-center">
                <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">500+</div>
                <div className="text-sm text-muted-foreground">Proyectos</div>
              </div>
            </div>

            <div className="absolute -bottom-6 -left-6 glass rounded-xl p-4 animate-float" style={{ animationDelay: '3s' }}>
              <div className="text-center">
                <div className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">24/7</div>
                <div className="text-sm text-muted-foreground">Soporte</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
