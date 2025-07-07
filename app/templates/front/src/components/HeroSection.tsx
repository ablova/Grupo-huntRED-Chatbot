import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ArrowRight, Calendar, Brain, Target, Sparkles, TrendingUp, Users, Globe, Briefcase, Clock, Landmark, Receipt } from 'lucide-react';

const HeroSection = () => {
  const [currentSlide, setCurrentSlide] = useState(0);

  const slides = [
    {
      title: "IA Aplicada para contratar más rápido",
      subtitle: "700+ marcas confían en huntRED® para transformar la eficiencia con automatización e inteligencia artificial",
      description: "La única plataforma diseñada específicamente para Latinoamérica. Conecte su gente, datos e interacciones para entregar experiencias increíbles durante todo el viaje usando inteligencia y automatización.",
      cta: "Ver Demo",
      ctaSecondary: "Agendar Demo",
      image: "https://images.unsplash.com/photo-1518770660439-4636190af475?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      icon: Brain,
      color: "from-red-600 to-red-800",
      stats: [
        { value: "25%", label: "Reducción tiempo contratación" },
        { value: "30%", label: "Aumento contrataciones internas" },
        { value: "50%", label: "Más eficiente en gastos" },
        { value: "11h", label: "Ahorradas por reclutador/semana" }
      ]
    },
    {
      title: "Administración de Nómina Inteligente",
      subtitle: "Optimice recursos y elimine errores con nuestra plataforma integral de nómina automatizada",
      description: "Nuestra solución de Administración de Nómina integra canales de mensajería, cálculos precisos según normativas regionales, dispersión automática y gestión de ausencias para una operación sin fricciones.",
      cta: "Explorar Solución",
      ctaSecondary: "Calcular Ahorro",
      image: "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      icon: Landmark,
      color: "from-blue-600 to-blue-800",
      stats: [
        { value: "40%", label: "Reducción en errores" },
        { value: "85%", label: "Automatización procesos" },
        { value: "5h", label: "Ahorro semanal por colaborador" },
        { value: "99.9%", label: "Precisión en cálculos" }
      ]
    },
    {
      title: "AURA AI™ - IA Personalizada",
      subtitle: "95% de precisión en matching de candidatos con aprendizaje continuo",
      description: "Nuestra IA propietaria AURA™ está entrenada con datos latinoamericanos y entiende las particularidades del mercado local. Análisis predictivo, matching inteligente y evaluación de soft skills.",
      cta: "Explorar AURA AI",
      ctaSecondary: "Ver Casos de Éxito",
      image: "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      icon: Sparkles,
      color: "from-purple-600 to-purple-800",
      stats: [
        { value: "95%", label: "Precisión en matching" },
        { value: "60%", label: "Mejora calidad contrataciones" },
        { value: "700+", label: "Marcas confían en huntRED®" },
        { value: "15", label: "Países con presencia" }
      ]
    },
    {
      title: "Precio Dinámico - Mejor Valor",
      subtitle: "El único modelo que se adapta a su presupuesto. huntRED® es 95% más económico que la competencia",
      description: "Precio basado en el valor real del servicio, sin costos ocultos. Escalabilidad automática y ROI predecible. La mejor opción para empresas latinoamericanas.",
      cta: "Calcular Precio",
      ctaSecondary: "Comparar con Competencia",
      image: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      icon: Target,
      color: "from-green-600 to-green-800",
      stats: [
        { value: "$95K", label: "huntRED® Solo IA" },
        { value: "$1.7M", label: "Mya (competencia)" },
        { value: "95%", label: "Más económico" },
        { value: "3 meses", label: "Tiempo recuperación" }
      ]
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 8000); // Increased to 8 seconds for better reading
    return () => clearInterval(timer);
  }, []);

  const IconComponent = slides[currentSlide].icon;

  return (
    <section id="hero" className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br from-gray-950 via-gray-900 to-red-950">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-[url('/img/grid-pattern.svg')] bg-center opacity-5" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-gray-950" />
      
      {/* Animated Gradient Orbs */}
      <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-red-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '10s' }} />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '15s', animationDelay: '2s' }} />
      <div className="absolute top-1/2 right-1/3 w-40 h-40 bg-purple-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '12s', animationDelay: '1s' }} />
      
      {/* Floating Elements */}
      <div className="absolute top-20 left-10 w-24 h-24 bg-gradient-to-br from-red-500/30 to-orange-500/30 rounded-full animate-float backdrop-blur-sm border border-white/10" />
      <div className="absolute top-40 right-20 w-20 h-20 bg-gradient-to-br from-indigo-500/30 to-purple-500/30 rounded-full animate-float backdrop-blur-sm border border-white/10" style={{ animationDelay: '2s' }} />
      <div className="absolute bottom-40 left-20 w-16 h-16 bg-gradient-to-br from-blue-500/30 to-cyan-500/30 rounded-full animate-float backdrop-blur-sm border border-white/10" style={{ animationDelay: '4s' }} />

      <div className="container mx-auto px-6 py-12 relative z-10">
        <div className="grid md:grid-cols-2 gap-16 items-center">
          
          {/* Content */}
          <div className="animate-slide-in-left">
            {/* Current Business Unit Badge */}
            <div className="inline-flex items-center gap-2 mb-6 py-2 px-4 bg-white/10 backdrop-blur-sm rounded-full border border-white/20 shadow-lg shadow-red-500/5">
              <div className="w-6 h-6 rounded-full bg-gradient-to-r from-red-500 to-red-600 flex items-center justify-center">
                <IconComponent className="w-3 h-3 text-white" />
              </div>
              <span className="text-sm font-medium text-white">Grupo huntRED</span>
            </div>
            
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-300 mb-4 leading-tight tracking-tight">
              {slides[currentSlide].title}
            </h1>
            
            <p className="text-xl text-gray-300 mb-6 leading-relaxed font-medium">
              {slides[currentSlide].subtitle}
            </p>
            
            <p className="text-gray-400 mb-8 max-w-2xl leading-relaxed">
              {slides[currentSlide].description}
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button size="lg" className={`bg-gradient-to-r ${slides[currentSlide].color} hover:opacity-90 transition-all duration-300 text-white border-0 shadow-lg`}>
                <Calendar className="mr-2 h-5 w-5" />
                {slides[currentSlide].cta}
              </Button>
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-gray-900 transition-all duration-300">
                {slides[currentSlide].ctaSecondary}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </div>

            {/* Slide Indicators */}
            <div className="flex space-x-3">
              {slides.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentSlide(index)}
                  className={`w-4 h-4 rounded-full transition-all duration-300 ${
                    index === currentSlide 
                      ? `bg-gradient-to-r ${slides[index].color} scale-125 shadow-lg` 
                      : 'bg-gray-400/50 hover:bg-gray-300/60'
                  }`}
                />
              ))}
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-10">
              {slides[currentSlide].stats.map((stat, index) => (
                <div key={index} className="text-center p-5 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 shadow-lg hover:shadow-xl hover:bg-white/10 transition-all duration-300 group">
                  <div className={`text-2xl md:text-3xl font-bold bg-gradient-to-r ${slides[currentSlide].color} bg-clip-text text-transparent mb-2 group-hover:scale-105 transition-transform duration-300`}>
                    {stat.value}
                  </div>
                  <div className="text-sm text-gray-300 leading-tight">
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Visual */}
          <div className="relative animate-slide-in-right">
            <div className="relative w-full h-[600px] rounded-3xl overflow-hidden border border-white/20 shadow-2xl shadow-red-500/10 transition-all duration-300 hover:shadow-red-500/20">
              <img
                src={slides[currentSlide].image}
                alt="huntRED® AI Technology"
                className="w-full h-full object-cover transition-transform duration-1000 hover:scale-105"
              />
              <div className={`absolute inset-0 bg-gradient-to-r ${slides[currentSlide].color} opacity-30`} />
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
              
              {/* Tech Overlay */}
              <div className="absolute top-6 left-6 glass rounded-xl p-4 border border-white/20 shadow-lg backdrop-blur-md">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-sm font-medium text-white">{currentSlide === 1 ? 'Nómina Automatizada' : 'AURA AI Active'}</span>
                </div>
              </div>
              
              <div className="absolute bottom-6 right-6 glass rounded-xl p-4 border border-white/20">
                <div className="text-white">
                  <div className="font-bold text-lg">95%</div>
                  <div className="text-sm text-gray-200">Precisión</div>
                </div>
              </div>
            </div>

            {/* Floating Stats */}
            <div className="absolute -top-8 -right-8 glass rounded-2xl p-6 border border-white/20 animate-float">
              <div className="text-center text-white">
                <div className="text-3xl font-bold bg-gradient-to-r from-red-500 to-red-600 bg-clip-text text-transparent">700+</div>
                <div className="text-sm text-gray-200">Empresas Confían</div>
              </div>
            </div>

            <div className="absolute -bottom-8 -left-8 glass rounded-2xl p-6 border border-white/20 animate-float" style={{ animationDelay: '3s' }}>
              <div className="text-center text-white">
                <div className="text-3xl font-bold bg-gradient-to-r from-green-500 to-green-600 bg-clip-text text-transparent">15</div>
                <div className="text-sm text-gray-200">Países</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Gradient */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-gray-900 to-transparent" />
    </section>
  );
};

export default HeroSection;
