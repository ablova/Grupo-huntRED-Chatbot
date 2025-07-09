import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface HeroAnimationProps {
  mousePosition: { x: number; y: number };
}

const HeroAnimation: React.FC<HeroAnimationProps> = ({ mousePosition }) => {
  const [particles, setParticles] = useState<Array<{
    id: number;
    x: number;
    y: number;
    size: number;
    color: string;
    speed: number;
  }>>([]);

  // Crear partículas al inicializar
  useEffect(() => {
    const colors = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'];
    const newParticles = Array(25).fill(0).map((_, index) => ({
      id: index,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      color: colors[Math.floor(Math.random() * colors.length)],
      speed: Math.random() * 0.5 + 0.2
    }));
    
    setParticles(newParticles);
  }, []);

  return (
    <div className="relative w-full h-full overflow-hidden">
      {/* Red gradient overlay */}
      <div 
        className="absolute inset-0 bg-gradient-to-br from-red-600/10 to-transparent rounded-full filter blur-3xl"
        style={{
          transform: `translate(${mousePosition.x * 20}px, ${mousePosition.y * -20}px)`,
          transition: 'transform 0.3s ease-out'
        }}
      />
      
      {/* Blue gradient overlay */}
      <div 
        className="absolute inset-0 bg-gradient-to-tl from-blue-600/10 to-transparent rounded-full filter blur-3xl"
        style={{
          transform: `translate(${mousePosition.x * -20}px, ${mousePosition.y * 20}px)`,
          transition: 'transform 0.3s ease-out'
        }}
      />
      
      {/* 3D Grid effect */}
      <div className="absolute inset-0 grid grid-cols-6 grid-rows-6">
        {Array(36).fill(0).map((_, index) => (
          <div key={index} className="border-[0.5px] border-white/5"></div>
        ))}
      </div>
      
      {/* Floating particles */}
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className="absolute rounded-full opacity-40"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            width: `${particle.size}px`,
            height: `${particle.size}px`,
            backgroundColor: particle.color,
          }}
          animate={{
            y: [0, -20, 0],
            opacity: [0.4, 0.8, 0.4],
            scale: [1, 1.2, 1],
          }}
          transition={{
            repeat: Infinity,
            duration: 4 / particle.speed,
            ease: "easeInOut",
            delay: Math.random() * 2,
          }}
        />
      ))}
      
      {/* Central 3D element */}
      <motion.div
        className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64"
        style={{
          perspective: "1000px",
          transformStyle: "preserve-3d",
        }}
      >
        {/* Abstract 3D shape */}
        <motion.div
          className="absolute inset-0"
          style={{
            transformStyle: "preserve-3d",
            transform: `
              rotateX(${mousePosition.y * 30}deg) 
              rotateY(${-mousePosition.x * 30}deg)
            `,
          }}
        >
          {/* Front face - Red Box */}
          <motion.div
            className="absolute inset-0 border-2 border-red-500/30 rounded-xl"
            style={{
              transform: "translateZ(40px)",
              background: "linear-gradient(135deg, rgba(239,68,68,0.1) 0%, rgba(0,0,0,0) 100%)",
              boxShadow: "0 0 20px rgba(239,68,68,0.3)",
            }}
            animate={{
              boxShadow: [
                "0 0 20px rgba(239,68,68,0.3)",
                "0 0 40px rgba(239,68,68,0.5)",
                "0 0 20px rgba(239,68,68,0.3)",
              ],
            }}
            transition={{
              repeat: Infinity,
              duration: 4,
              ease: "easeInOut",
            }}
          />
          
          {/* Back face - Blue Box */}
          <motion.div
            className="absolute inset-0 border-2 border-blue-500/30 rounded-xl"
            style={{
              transform: "translateZ(-40px)",
              background: "linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(0,0,0,0) 100%)",
              boxShadow: "0 0 20px rgba(59,130,246,0.3)",
            }}
            animate={{
              boxShadow: [
                "0 0 20px rgba(59,130,246,0.3)",
                "0 0 40px rgba(59,130,246,0.5)",
                "0 0 20px rgba(59,130,246,0.3)",
              ],
            }}
            transition={{
              repeat: Infinity,
              duration: 4,
              ease: "easeInOut",
              delay: 0.5,
            }}
          />
          
          {/* Middle face - Logo Placeholder */}
          <motion.div
            className="absolute inset-0 flex items-center justify-center"
            style={{
              transform: "translateZ(0px)",
            }}
          >
            {/* huntRED logo */}
            <motion.div
              className="text-4xl font-bold text-white flex items-center"
              animate={{ scale: [0.98, 1.02, 0.98] }}
              transition={{
                repeat: Infinity,
                duration: 6,
                ease: "easeInOut",
              }}
            >
              <span>Grupo</span>
              <span className="text-red-500">hunt</span>
              <span className="text-red-500 font-bold">RED</span>
              <span className="text-xs align-top">®</span>
            </motion.div>
          </motion.div>
          
          {/* Side faces - connecting lines */}
          <div className="absolute inset-0 border-2 border-white/10 rounded-xl" style={{ transform: "rotateX(90deg) translateZ(40px)" }} />
          <div className="absolute inset-0 border-2 border-white/10 rounded-xl" style={{ transform: "rotateX(90deg) translateZ(-40px)" }} />
          <div className="absolute inset-0 border-2 border-white/10 rounded-xl" style={{ transform: "rotateY(90deg) translateZ(40px)" }} />
          <div className="absolute inset-0 border-2 border-white/10 rounded-xl" style={{ transform: "rotateY(90deg) translateZ(-40px)" }} />
        </motion.div>
      </motion.div>
      
      {/* Tech words floating */}
      <motion.div
        className="absolute top-[15%] left-[20%] text-xs text-blue-400/60"
        animate={{ y: [0, -10, 0], opacity: [0.6, 1, 0.6] }}
        transition={{ repeat: Infinity, duration: 5 }}
      >
        GenIA™
      </motion.div>
      
      <motion.div
        className="absolute top-[30%] right-[25%] text-xs text-red-400/60"
        animate={{ y: [0, -8, 0], opacity: [0.6, 1, 0.6] }}
        transition={{ repeat: Infinity, duration: 4.5, delay: 1 }}
      >
        AURA™
      </motion.div>
      
      <motion.div
        className="absolute bottom-[20%] left-[30%] text-xs text-green-400/60"
        animate={{ y: [0, -12, 0], opacity: [0.6, 1, 0.6] }}
        transition={{ repeat: Infinity, duration: 5.5, delay: 0.5 }}
      >
        SocialLink™
      </motion.div>
      
      <motion.div
        className="absolute bottom-[35%] right-[20%] text-xs text-purple-400/60"
        animate={{ y: [0, -8, 0], opacity: [0.6, 1, 0.6] }}
        transition={{ repeat: Infinity, duration: 4.8, delay: 1.5 }}
      >
        TruthSense™
      </motion.div>
      
      <motion.div
        className="absolute bottom-[15%] right-[35%] text-xs text-yellow-400/60"
        animate={{ y: [0, -10, 0], opacity: [0.6, 1, 0.6] }}
        transition={{ repeat: Infinity, duration: 5.2, delay: 0.8 }}
      >
        OffLimits™
      </motion.div>
    </div>
  );
};

export default HeroAnimation;
