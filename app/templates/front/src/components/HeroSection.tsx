import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, Calendar, Brain, Target, Sparkles, TrendingUp, Users, Globe } from 'lucide-react';

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
    <section id="hero" className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br from-gray-900 via-gray-800 to-red-900">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-hero-pattern opacity-10" />
      
      {/* Floating Elements */}
      <div className="absolute top-20 left-10 w-20 h-20 bg-red-500/20 rounded-full animate-float" />
      <div className="absolute top-40 right-20 w-16 h-16 bg-purple-500/20 rounded-full animate-float" style={{ animationDelay: '2s' }} />
      <div className="absolute bottom-40 left-20 w-12 h-12 bg-green-500/20 rounded-full animate-float" style={{ animationDelay: '4s' }} />

      <div className="container mx-auto px-4 lg:px-8 pt-16 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Content */}
          <div className="space-y-8 animate-fade-in-up text-white">
            <div className="space-y-6">
              {/* Badge */}
              <Badge variant="secondary" className="bg-red-100 text-red-700 hover:bg-red-200 border-0">
                <IconComponent className="h-4 w-4 mr-2" />
                GRUPO HUNTRED® - LÍDER EN LATINOAMÉRICA
              </Badge>
              
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold leading-tight">
                {slides[currentSlide].title.split(' ').map((word, index) => (
                  <span 
                    key={index} 
                    className={index >= 2 ? `bg-gradient-to-r ${slides[currentSlide].color} bg-clip-text text-transparent` : 'text-white'}
                  >
                    {word}{' '}
                  </span>
                ))}
              </h1>
              
              <p className="text-xl md:text-2xl text-gray-200 leading-relaxed">
                {slides[currentSlide].subtitle}
              </p>
              
              <p className="text-lg text-gray-300 max-w-2xl leading-relaxed">
                {slides[currentSlide].description}
              </p>
            </div>

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
                    index === currentSlide ? 'bg-red-500 scale-125' : 'bg-gray-400/50 hover:bg-gray-400'
                  }`}
                />
              ))}
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-8">
              {slides[currentSlide].stats.map((stat, index) => (
                <div key={index} className="text-center p-4 bg-white/10 backdrop-blur-sm rounded-xl border border-white/20">
                  <div className={`text-2xl md:text-3xl font-bold bg-gradient-to-r ${slides[currentSlide].color} bg-clip-text text-transparent mb-1`}>
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
            <div className="relative w-full h-[600px] rounded-2xl overflow-hidden glass border border-white/20">
              <img
                src={slides[currentSlide].image}
                alt="huntRED® AI Technology"
                className="w-full h-full object-cover transition-transform duration-1000 hover:scale-105"
              />
              <div className={`absolute inset-0 bg-gradient-to-r ${slides[currentSlide].color} opacity-30`} />
              
              {/* Tech Overlay */}
              <div className="absolute top-6 left-6 glass rounded-xl p-4 border border-white/20">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-sm font-medium text-white">AURA AI Active</span>
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
