import React, { useState, useEffect, useRef } from 'react';
import { motion, useAnimation, AnimatePresence } from 'framer-motion';
import { 
  Brain, Sparkles, Users, Globe, Briefcase, Landmark, 
  ChevronDown, ArrowRight, BarChart3, Workflow, Filter
} from 'lucide-react';
// Usando botones HTML nativos con Tailwind
import TechEcosystem from './TechEcosystem';
import BusinessUnits from './BusinessUnits';
import HeroAnimation from './HeroAnimation';
import CallToAction from './CallToAction';

// Tipado para las secciones del Hero
type SectionType = 'overview' | 'ecosystem' | 'units' | 'contact';

const NewHeroSection: React.FC = () => {
  // Estados para animaciones y controles
  const [activeSection, setActiveSection] = useState<SectionType>('overview');
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const heroRef = useRef<HTMLDivElement>(null);
  const controls = useAnimation();

  // Efecto parallax con movimiento del mouse
  const handleMouseMove = (e: React.MouseEvent) => {
    const { clientX, clientY } = e;
    const { innerWidth, innerHeight } = window;
    
    // Movimiento más suave con interpolación
    setMousePosition(prev => ({
      x: prev.x + (clientX / innerWidth - prev.x) * 0.1,
      y: prev.y + (clientY / innerHeight - prev.y) * 0.1
    }));
  };

  // Cambiar a la siguiente sección
  const goToNextSection = () => {
    const sections: SectionType[] = ['overview', 'ecosystem', 'units', 'contact'];
    const currentIndex = sections.indexOf(activeSection);
    const nextIndex = (currentIndex + 1) % sections.length;
    setActiveSection(sections[nextIndex]);
  };

  // Efecto para las animaciones iniciales
  useEffect(() => {
    controls.start({
      opacity: 1,
      y: 0,
      transition: { duration: 0.8, ease: "easeOut" }
    });
  }, [controls]);

  // Variantes para las animaciones de las secciones
  const sectionVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.8,
        ease: "easeOut",
        staggerChildren: 0.2
      }
    },
    exit: { 
      opacity: 0, 
      y: -50,
      transition: {
        duration: 0.4,
        ease: "easeIn"
      }
    }
  };

  // Contenido basado en la sección activa
  const renderContent = () => {
    switch (activeSection) {
      case 'overview':
        return (
          <motion.div 
            key="overview"
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="flex flex-col lg:flex-row w-full h-full items-center"
          >
            <div className="lg:w-1/2 p-8 lg:pr-0 z-10">
              <div className="flex items-center mb-6">
                <motion.img 
                  src="/static/images/Grupo_huntred.png" 
                  alt="Grupo huntRED®" 
                  className="w-32 h-auto mr-4" 
                  variants={{ hidden: { opacity: 0, scale: 0.8 }, visible: { opacity: 1, scale: 1, transition: { delay: 0.05, type: 'spring', stiffness: 200 } } }}
                />
              </div>
              <motion.h1 
                className="text-4xl lg:text-6xl font-bold bg-gradient-to-br from-white to-gray-400 bg-clip-text text-transparent mb-6"
                variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { delay: 0.1 } } }}
              >
                Ecosistema Integral de <span className="text-red-600">Talento</span>
              </motion.h1>
              
              <motion.p 
                className="text-lg text-gray-300 mb-6"
                variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { delay: 0.2 } } }}
              >
                Grupo huntRED® ofrece un ecosistema completo para optimizar la gestión de talento, impulsado por IA propietaria
                y soluciones que conectan cada aspecto del ciclo de vida laboral.
              </motion.p>
              
              <motion.div 
                className="grid grid-cols-2 gap-4 mb-8"
                variants={{ hidden: { opacity: 0 }, visible: { opacity: 1, transition: { delay: 0.3 } } }}
              >
                <div className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-red-500" />
                  <span className="text-sm text-gray-300">GenIA & AURA™</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-red-500" />
                  <span className="text-sm text-gray-300">Reclutamiento IA</span>
                </div>
                <div className="flex items-center gap-2">
                  <Landmark className="w-5 h-5 text-red-500" />
                  <span className="text-sm text-gray-300">Nómina Inteligente</span>
                </div>
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-red-500" />
                  <span className="text-sm text-gray-300">Desarrollo Organizacional</span>
                </div>
              </motion.div>
              
              <motion.div 
                className="flex flex-col sm:flex-row gap-4"
                variants={{ hidden: { opacity: 0 }, visible: { opacity: 1, transition: { delay: 0.4 } } }}
              >
                <button 
                  onClick={goToNextSection}
                  className="px-4 py-2 rounded-md bg-gradient-to-r from-red-700 to-red-500 hover:from-red-600 hover:to-red-400 text-white flex items-center justify-center"
                >
                  Explorar Ecosistema <ArrowRight className="ml-2 w-4 h-4" />
                </button>
                <button 
                  className="px-4 py-2 rounded-md border border-gray-700 hover:bg-gray-800 text-white"
                >
                  Agendar Demo
                </button>
              </motion.div>
            </div>
            
            <div className="lg:w-1/2 h-full relative overflow-hidden">
              <HeroAnimation mousePosition={mousePosition} />
              
              {/* Estadísticas flotantes con efecto glassmorphism */}
              <motion.div 
                className="absolute top-[20%] right-[10%] bg-gray-900/40 backdrop-blur-lg rounded-xl p-4 border border-white/10 shadow-xl"
                style={{
                  transform: `perspective(1000px) rotateX(${(mousePosition.y - 0.5) * -5}deg) rotateY(${(mousePosition.x - 0.5) * 5}deg)`,
                  transition: 'transform 0.2s ease-out',
                }}
                variants={{ hidden: { opacity: 0, scale: 0.8 }, visible: { opacity: 1, scale: 1, transition: { delay: 0.5 } } }}
              >
                <div className="text-center">
                  <div className="text-2xl font-bold bg-gradient-to-r from-red-500 to-red-600 bg-clip-text text-transparent">250+</div>
                  <div className="text-xs text-gray-400">Empresas confían en nosotros</div>
                </div>
              </motion.div>
              
              <motion.div 
                className="absolute bottom-[20%] left-[15%] bg-gray-900/40 backdrop-blur-lg rounded-xl p-4 border border-white/10 shadow-xl"
                style={{
                  transform: `perspective(1000px) rotateX(${(mousePosition.y - 0.5) * 5}deg) rotateY(${(mousePosition.x - 0.5) * -5}deg)`,
                  transition: 'transform 0.2s ease-out',
                }}
                variants={{ hidden: { opacity: 0, scale: 0.8 }, visible: { opacity: 1, scale: 1, transition: { delay: 0.6 } } }}
              >
                <div className="text-center">
                  <div className="text-2xl font-bold bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">15+</div>
                  <div className="text-xs text-gray-400">Años de experiencia</div>
                </div>
              </motion.div>
            </div>
          </motion.div>
        );

      case 'ecosystem':
        return (
          <motion.div 
            key="ecosystem"
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="w-full h-full"
          >
            <TechEcosystem mousePosition={mousePosition} />
          </motion.div>
        );

      case 'units':
        return (
          <motion.div 
            key="units"
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="w-full h-full"
          >
            <BusinessUnits mousePosition={mousePosition} />
          </motion.div>
        );

      case 'contact':
        return (
          <motion.div 
            key="contact"
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="w-full h-full"
          >
            <CallToAction />
          </motion.div>
        );

      default:
        return null;
    }
  };

  // Indicadores de navegación
  const renderNavIndicators = () => {
    const sections: SectionType[] = ['overview', 'ecosystem', 'units', 'contact'];
    const labels = ['Inicio', 'Ecosistema', 'Unidades', 'Contacto'];
    
    return (
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex space-x-2 z-20">
        {sections.map((section, index) => (
          <button
            key={section}
            onClick={() => setActiveSection(section)}
            className="group flex flex-col items-center"
          >
            <span className={`text-xs mb-2 ${activeSection === section ? 'text-red-500' : 'text-gray-500'} transition-colors duration-300`}>
              {labels[index]}
            </span>
            <div 
              className={`h-1 w-6 rounded-full transition-all duration-300 ${
                activeSection === section ? 'bg-red-500' : 'bg-gray-700 group-hover:bg-gray-500'
              }`}
            />
          </button>
        ))}
      </div>
    );
  };

  return (
    <section 
      ref={heroRef}
      onMouseMove={handleMouseMove}
      className="relative h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black overflow-hidden"
    >
      {/* Decorative elements */}
      <div className="absolute inset-0">
        <div 
          className="absolute top-0 right-0 w-1/3 h-1/3 bg-gradient-to-b from-red-600/20 to-transparent rounded-full filter blur-[80px]"
          style={{
            transform: `translate(${mousePosition.x * -30}px, ${mousePosition.y * 30}px)`,
            transition: 'transform 0.4s ease-out'
          }}
        />
        <div 
          className="absolute bottom-0 left-0 w-1/3 h-1/3 bg-gradient-to-t from-blue-600/10 to-transparent rounded-full filter blur-[80px]"
          style={{
            transform: `translate(${mousePosition.x * 30}px, ${mousePosition.y * -30}px)`,
            transition: 'transform 0.4s ease-out'
          }}
        />
      </div>
      
      {/* Content container */}
      <div className="container mx-auto h-full px-4 py-16 relative z-10">
        <AnimatePresence mode="wait">
          {renderContent()}
        </AnimatePresence>
      </div>
      
      {/* Navigation indicators */}
      {renderNavIndicators()}
      
      {/* Scroll indicator */}
      <motion.div 
        className="absolute bottom-24 left-1/2 transform -translate-x-1/2"
        animate={{
          y: [0, 10, 0],
          opacity: [0.6, 1, 0.6],
        }}
        transition={{
          repeat: Infinity,
          duration: 2,
        }}
      >
        <ChevronDown className="w-6 h-6 text-white/70" />
      </motion.div>
    </section>
  );
};

export default NewHeroSection;
