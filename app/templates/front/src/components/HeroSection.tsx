import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { ArrowRight, Calendar, Brain, Target, Sparkles, TrendingUp, Users, Globe, Briefcase, Clock, Landmark, Receipt } from 'lucide-react';
import { motion } from 'framer-motion';

const HeroSection = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const heroRef = useRef<HTMLDivElement>(null);
  
  // Función para manejar el efecto parallax con el movimiento del mouse
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (heroRef.current) {
      const rect = heroRef.current.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;
      setMousePosition({ x, y });
    }
  };

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
    <section 
      id="hero" 
      className="hero-3d-container relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br from-gray-950 via-gray-900 to-red-950"
      ref={heroRef}
      onMouseMove={handleMouseMove}
    >
      {/* Background Elements */}
      <div className="absolute inset-0 bg-[url('/img/grid-pattern.svg')] bg-center opacity-5 enhanced-grid"></div>
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-gray-950"></div>
      
      {/* Main Content Container */}
      <div className="container mx-auto px-4 py-12 relative z-10">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-12">
          <motion.div 
            className="w-full lg:w-1/2 content-3d-wrapper"
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, ease: [0.25, 0.1, 0.25, 1] }}
            style={{
              transform: `perspective(2000px) rotateY(${(mousePosition.x - 0.5) * 5}deg) translateZ(${(mousePosition.y - 0.5) * 10}px)`,
              transition: 'transform 0.8s cubic-bezier(0.23, 1, 0.32, 1)'
            }}
          >
            <motion.h1 
              key={`title-${currentSlide}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.4 }}
              className="text-4xl md:text-6xl font-extrabold mb-6 text-white tracking-tight leading-tight"
            >
              {slides[currentSlide].title}
            </motion.h1>
            
            <motion.p 
              key={`subtitle-${currentSlide}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.5 }}
              className="text-lg md:text-xl text-gray-300 mb-8"
            >
              {slides[currentSlide].subtitle}
            </motion.p>
            
            <motion.div 
              key={`desc-${currentSlide}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.6 }}
              className="text-gray-300 mb-12 max-w-xl"
            >
              {slides[currentSlide].description}
            </motion.div>
            
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.7 }}
              className="flex flex-col sm:flex-row gap-4 mb-8"
            >
              <Button size="lg" className="bg-gradient-to-r from-red-600 to-red-800 hover:opacity-90 transition-opacity">
                {slides[currentSlide].cta} <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              
              <Button size="lg" variant="outline" className="border-red-500/30 text-white hover:bg-red-500/10">
                <Calendar className="mr-2 h-5 w-5" />
                {slides[currentSlide].ctaSecondary}
              </Button>
            </motion.div>
            
            {/* Controles de navegación */}
            <div className="flex items-center justify-center gap-3 mt-8 md:mt-10 nav-controls-3d">
              {slides.map((_, index) => (
                <motion.button
                  key={`nav-${index}`}
                  onClick={() => setCurrentSlide(index)}
                  whileHover={{ scale: 1.2 }}
                  whileTap={{ scale: 0.95 }}
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{ opacity: 1, scale: index === currentSlide ? 1.25 : 1 }}
                  transition={{ duration: 0.3, delay: 0.5 + (index * 0.1) }}
                  className={`w-3 h-3 rounded-full transition-all duration-300 shadow-md ${index === currentSlide 
                    ? `bg-gradient-to-r ${slides[index].color} scale-125 shadow-lg glow-control` 
                    : 'bg-gray-400/50 hover:bg-gray-300/60'
                  }`}
                />
              ))}
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-10">
              {slides[currentSlide].stats.map((stat, index) => (
                <div key={index} className="text-center p-5 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 shadow-lg hover:shadow-xl hover:bg-white/10 transition-all duration-300 group stat-card glass-effect card-3d">
                  <div className={`text-2xl md:text-3xl font-bold bg-gradient-to-r ${slides[currentSlide].color} bg-clip-text text-transparent mb-2 group-hover:scale-105 transition-transform duration-300`}>
                    {stat.value}
                  </div>
                  <div className="text-sm text-gray-300 leading-tight">
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Visual con efecto 3D y parallax */}
          <motion.div 
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 1, ease: [0.22, 1, 0.36, 1], delay: 0.3 }}
            className="relative"
          >
            <div 
              className="relative w-full h-[600px] rounded-3xl overflow-hidden border border-white/20 shadow-2xl shadow-red-500/10 transition-all duration-300 hover:shadow-red-500/20 hero-3d-element depth-layer-3 glow-red"
              style={{
                transform: `perspective(2000px) rotateY(${(mousePosition.x - 0.5) * -8}deg) rotateX(${(mousePosition.y - 0.5) * 8}deg)`,
                transition: 'transform 0.3s cubic-bezier(0.23, 1, 0.32, 1)'
              }}
            >
              <div 
                className="w-full h-full relative image-frame"
                style={{
                  transform: `scale(1.1) translate(${(mousePosition.x - 0.5) * -25}px, ${(mousePosition.y - 0.5) * -25}px)`,
                  transition: 'transform 0.3s cubic-bezier(0.23, 1, 0.32, 1)'
                }}
              >
                <img
                  src={slides[currentSlide].image}
                  alt="huntRED® AI Technology"
                  className="w-full h-full object-cover"
                />
              </div>
              
              <div 
                className={`absolute inset-0 bg-gradient-to-r ${slides[currentSlide].color} opacity-30 parallax-medium`} 
                style={{
                  transform: `translate(${(mousePosition.x - 0.5) * -15}px, ${(mousePosition.y - 0.5) * -15}px)`,
                  transition: 'transform 0.4s cubic-bezier(0.23, 1, 0.32, 1)'
                }}
              />
              
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent"></div>
              
              {/* Elementos 3D internos */}
              <div 
                className="absolute inset-0 parallax-deep" 
                style={{
                  backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(255,255,255,0.1) 1px, transparent 1px)',
                  backgroundSize: '30px 30px',
                  opacity: 0.4,
                  transform: `translate(${(mousePosition.x - 0.5) * -35}px, ${(mousePosition.y - 0.5) * -35}px)`,
                  transition: 'transform 0.6s cubic-bezier(0.23, 1, 0.32, 1)'
                }}
              />
              
              {/* Tech Overlay con desplazamiento parallax */}
              <motion.div 
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.8 }}
                className="absolute top-6 left-6 backdrop-blur-md rounded-xl p-4 border border-white/20 shadow-lg glass-effect float-element"
                style={{
                  transform: `translate(${(mousePosition.x - 0.5) * -20}px, ${(mousePosition.y - 0.5) * -20}px)`,
                  transition: 'transform 0.4s cubic-bezier(0.23, 1, 0.32, 1)',
                  background: 'rgba(255,255,255,0.1)'
                }}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-white">{currentSlide === 1 ? 'Nómina Automatizada' : 'AURA AI Active'}</span>
                </div>
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.9 }}
                className="absolute bottom-6 right-6 backdrop-blur-md rounded-xl p-4 border border-white/20 glass-effect float-element-reverse"
                style={{
                  transform: `translate(${(mousePosition.x - 0.5) * 20}px, ${(mousePosition.y - 0.5) * 20}px)`,
                  transition: 'transform 0.4s cubic-bezier(0.23, 1, 0.32, 1)',
                  background: 'rgba(255,255,255,0.1)'
                }}
              >
                <div className="text-white">
                  <div className="font-bold text-lg">95%</div>
                  <div className="text-sm text-gray-200">Precisión</div>
                </div>
              </motion.div>
              
              {/* Elementos decorativos tecnológicos */}
              {[...Array(3)].map((_, i) => (
                <motion.div 
                  key={`tech-element-${i}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.6 }}
                  transition={{ duration: 1, delay: 1 + (i * 0.2) }}
                  className="absolute bg-white/10 backdrop-blur-sm rounded-full glass-effect tech-particle"
                  style={{
                    width: 40 + (i * 20),
                    height: 40 + (i * 20),
                    left: `${20 + (i * 15)}%`,
                    top: `${70 - (i * 10)}%`,
                    transform: `translate(${(mousePosition.x - 0.5) * (30 + i * 15)}px, ${(mousePosition.y - 0.5) * (30 + i * 15)}px)`,
                    transition: 'transform 0.6s cubic-bezier(0.23, 1, 0.32, 1)',
                    animationDelay: `${i * 0.5}s`
                  }}
                />
              ))}
            </div>

            {/* Floating Stats con efecto 3D */}
            <motion.div 
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 1 }}
              className="absolute -top-8 -right-8 backdrop-blur-xl rounded-2xl p-6 border border-white/20"
              style={{
                transform: `perspective(1000px) rotateX(${(mousePosition.y - 0.5) * -10}deg) rotateY(${(mousePosition.x - 0.5) * 10}deg)`,
                transition: 'transform 0.3s cubic-bezier(0.33, 1, 0.68, 1)',
                background: 'rgba(255,255,255,0.05)'
              }}
            >
              <div className="text-center text-white">
                <div className="text-3xl font-bold bg-gradient-to-r from-red-500 to-red-600 bg-clip-text text-transparent">700+</div>
                <div className="text-sm text-gray-200">Empresas Confían</div>
              </div>
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 1.2 }}
              className="absolute -bottom-8 -left-8 backdrop-blur-xl rounded-2xl p-6 border border-white/20"
              style={{
                transform: `perspective(1000px) rotateX(${(mousePosition.y - 0.5) * 10}deg) rotateY(${(mousePosition.x - 0.5) * -10}deg)`,
                transition: 'transform 0.3s cubic-bezier(0.33, 1, 0.68, 1)',
                background: 'rgba(255,255,255,0.05)'
              }}
            >
              <div className="text-center text-white">
                <div className="text-3xl font-bold bg-gradient-to-r from-green-500 to-green-600 bg-clip-text text-transparent">15</div>
                <div className="text-sm text-gray-200">Países</div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </div>

      {/* Bottom Gradient */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-gray-900 to-transparent"></div>
      
      {/* SVG 3D decorativo */}
      <svg className="absolute bottom-0 left-0 w-full h-40 opacity-30" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320" preserveAspectRatio="none">
        <path 
          fill="rgba(239, 68, 68, 0.1)" 
          fillOpacity="1" 
          d="M0,288L48,272C96,256,192,224,288,197.3C384,171,480,149,576,165.3C672,181,768,235,864,250.7C960,267,1056,245,1152,224C1248,203,1344,181,1392,170.7L1440,160L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"
          style={{
            transform: `translate(${mousePosition.x * -30}px, ${mousePosition.y * 30}px)`,
            transition: 'transform 0.4s cubic-bezier(0.33, 1, 0.68, 1)'
          }}
        ></path>
      </svg>
      <svg className="absolute bottom-0 left-0 w-full h-60 opacity-20" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320" preserveAspectRatio="none">
        <path 
          fill="rgba(220, 38, 38, 0.2)" 
          fillOpacity="1" 
          d="M0,160L40,181.3C80,203,160,245,240,261.3C320,277,400,267,480,234.7C560,203,640,149,720,133.3C800,117,880,139,960,176C1040,213,1120,267,1200,277.3C1280,288,1360,256,1400,240L1440,224L1440,320L1400,320C1360,320,1280,320,1200,320C1120,320,1040,320,960,320C880,320,800,320,720,320C640,320,560,320,480,320C400,320,320,320,240,320C160,320,80,320,40,320L0,320Z"
          style={{
            transform: `translate(${mousePosition.x * 30}px, ${mousePosition.y * 20}px)`,
            transition: 'transform 0.5s cubic-bezier(0.33, 1, 0.68, 1)'
          }}
        ></path>
      </svg>
    </section>
  );
};

export default HeroSection;
