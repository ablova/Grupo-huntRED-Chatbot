import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Brain, Shield, Link, Database, Search, FileCheck } from 'lucide-react';

interface TechEcosystemProps {
  mousePosition: { x: number; y: number };
}

// Definición de las tecnologías propietarias
const technologies = [
  { 
    id: 'genia', 
    name: 'GenIA™', 
    description: 'Motor de IA especializado en reclutamiento y selección de personal',
    icon: <Brain className="w-8 h-8 text-red-400" />,
    color: 'from-red-600 to-red-400',
    position: { top: '2.5%', left: '32.5%' }
  },
  { 
    id: 'aura', 
    name: 'AURA™', 
    description: 'ML Graphos para identificar Relaciones Humanas y sus potenciales',
    icon: <Sparkles className="w-8 h-8 text-blue-400" />,
    color: 'from-blue-600 to-blue-400',
    position: { top: '35%', left: '10%' }
  },
  { 
    id: 'sociallink', 
    name: 'SocialLink™', 
    description: 'Verificación avanzada de conexiones profesionales y sociales',
    icon: <Link className="w-8 h-8 text-green-400" />,
    color: 'from-green-600 to-green-400',
    position: { top: '35%', right: '10%' }
  },
  { 
    id: 'truthsense', 
    name: 'TruthSense™', 
    description: 'Validación de integridad y verificación de antecedentes',
    icon: <Shield className="w-8 h-8 text-purple-400" />,
    color: 'from-purple-600 to-purple-400',
    position: { top: '60%', left: '25%' }
  },
  { 
    id: 'offlimits', 
    name: 'OffLimits™', 
    description: 'Control de acceso y limitaciones por rol y sensibilidad',
    icon: <FileCheck className="w-8 h-8 text-yellow-400" />,
    color: 'from-yellow-600 to-yellow-400',
    position: { top: '10%', right: '25%' }
  },
  { 
    id: 'socialverify', 
    name: 'SocialVerify™', 
    description: 'Validación de presencia digital y reputación online',
    icon: <Search className="w-8 h-8 text-cyan-400" />,
    color: 'from-cyan-600 to-cyan-400',
    position: { bottom: '-25%', left: '50%' }
  }
];

// Conexiones entre tecnologías para visualizar
const connections = [
  { from: 'genia', to: 'aura' },
  { from: 'genia', to: 'sociallink' },
  { from: 'aura', to: 'truthsense' },
  { from: 'aura', to: 'offlimits' },
  { from: 'sociallink', to: 'socialverify' },
  { from: 'truthsense', to: 'socialverify' },
  { from: 'offlimits', to: 'socialverify' }
];

const TechEcosystem: React.FC<TechEcosystemProps> = ({ mousePosition }) => {
  return (
    <div className="w-full h-full flex flex-col items-center justify-center py-12 px-4">
      <motion.div 
        className="text-center mb-12"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <h2 className="text-4xl font-bold mb-3 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
          Ecosistema de Tecnologías <span className="text-red-500">Propietarias</span>
        </h2>
        <p className="text-gray-400 max-w-2xl mx-auto">
          Nuestras tecnologías trabajan en conjunto para ofrecer una experiencia integral
          en la gestión del talento, desde el reclutamiento hasta la nómina.
        </p>
      </motion.div>

      <div className="relative w-full max-w-5xl h-[500px] mx-auto">
        {/* Central hub */}
        <motion.div 
          className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10
                     w-24 h-24 rounded-full bg-gradient-to-r from-red-700 to-red-500 flex items-center justify-center
                     shadow-[0_0_30px_rgba(220,38,38,0.5)]"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.4, type: 'spring', stiffness: 200, damping: 10 }}
          style={{
            transform: `translate(-50%, -50%) perspective(1000px) rotateX(${(mousePosition.y - 0.5) * 10}deg) rotateY(${(mousePosition.x - 0.5) * -10}deg)`,
          }}
        >
          <img 
            src="/static/images/Grupo_huntred.png" 
            alt="Grupo huntRED®" 
            className="w-16 h-16 object-contain" 
          />
        </motion.div>

        {/* Connection lines */}
        <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 1 }}>
          <g>
            {connections.map((connection, index) => {
              const fromTech = technologies.find(tech => tech.id === connection.from);
              const toTech = technologies.find(tech => tech.id === connection.to);
              
              if (!fromTech || !toTech) return null;
              
              // Extract positions from the tech objects
              const fromPosition = fromTech.position;
              const toPosition = toTech.position;
              
              // Convert positions to coordinates
              const fromCoord = {
                x: fromPosition.left ? parseInt(fromPosition.left as string) : 50,
                y: fromPosition.top ? parseInt(fromPosition.top as string) : (fromPosition.bottom ? 100 - parseInt(fromPosition.bottom as string) : 50)
              };
              
              const toCoord = {
                x: toPosition.left ? parseInt(toPosition.left as string) : 50,
                y: toPosition.top ? parseInt(toPosition.top as string) : (toPosition.bottom ? 100 - parseInt(toPosition.bottom as string) : 50)
              };
              
              return (
                <motion.path
                  key={`${connection.from}-${connection.to}`}
                  d={`M${fromCoord.x}% ${fromCoord.y}% L${toCoord.x}% ${toCoord.y}%`}
                  stroke="url(#lineGradient)"
                  strokeWidth="2"
                  strokeDasharray="6,4"
                  fill="none"
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ pathLength: 1, opacity: 0.7 }}
                  transition={{ delay: 0.5 + index * 0.1, duration: 1.5 }}
                />
              );
            })}
          </g>
          <defs>
            <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="rgba(255,255,255,0.7)" />
              <stop offset="100%" stopColor="rgba(239,68,68,0.7)" />
            </linearGradient>
          </defs>
        </svg>

        {/* Technology nodes */}
        {technologies.map((tech, index) => {
          // Convert position to style object
          const positionStyle: React.CSSProperties = {};
          if (tech.position.top) positionStyle.top = tech.position.top;
          if (tech.position.left) positionStyle.left = tech.position.left;
          if (tech.position.right) positionStyle.right = tech.position.right;
          if (tech.position.bottom) positionStyle.bottom = tech.position.bottom;
          
          return (
            <motion.div
              key={tech.id}
              className={`absolute z-20 w-48 transform -translate-x-1/2 -translate-y-1/2`}
              style={{
                ...positionStyle,
                transform: `translate(-50%, -50%) perspective(1000px) rotateX(${(mousePosition.y - 0.5) * 5}deg) rotateY(${(mousePosition.x - 0.5) * 5}deg)`,
              }}
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 + index * 0.1, type: 'spring', stiffness: 100, damping: 10 }}
            >
              <div className={`bg-gray-900/80 backdrop-blur-sm p-4 rounded-xl border border-gray-800 
                              shadow-lg hover:shadow-xl transition-all duration-300
                              hover:border-${tech.color.split(' ')[0].replace('from-', '')}/30`}>
                <div className={`bg-gradient-to-br ${tech.color} rounded-full w-16 h-16 
                                flex items-center justify-center mx-auto mb-3
                                shadow-[0_0_15px_rgba(255,255,255,0.2)]`}>
                  {tech.icon}
                </div>
                <h3 className="text-lg font-semibold text-white text-center mb-1">{tech.name}</h3>
                <p className="text-xs text-gray-400 text-center">{tech.description}</p>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default TechEcosystem;
