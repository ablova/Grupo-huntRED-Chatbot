import React from 'react';
import { motion } from 'framer-motion';
import { 
  Users, Briefcase, GraduationCap, 
  Building, Calculator, Database, Award
} from 'lucide-react';
// Usando elementos HTML básicos con Tailwind

interface BusinessUnitsProps {
  mousePosition: { x: number; y: number };
}

// Definición de las unidades de negocio
const businessUnits = [
  {
    id: 'executive',
    name: 'huntRED® Executive',
    description: 'Reclutamiento de alta dirección con herramientas de IA propietarias.',
    icon: <Briefcase className="w-8 h-8 text-yellow-400" />,
    color: 'from-yellow-600 to-yellow-400',
    features: ['Headhunting ejecutivo', 'Assessment C-Suite', 'Evaluación 360°']
  },
  {
    id: 'huntred',
    name: 'huntRED®',
    description: 'Reclutamiento especializado para posiciones de gerencia media a nivel directivo.',
    icon: <Users className="w-8 h-8 text-red-400" />,
    color: 'from-red-600 to-red-400',
    features: ['Búsqueda especializada', 'Pruebas técnicas', 'Onboarding']
  },
  {
    id: 'huntuinterns',
    name: 'huntU®',
    description: 'Desarrollo de talento universitario y programas de pasantías.',
    icon: <GraduationCap className="w-8 h-8 text-blue-400" />,
    color: 'from-blue-600 to-blue-400',
    features: ['Talento joven', 'Programas educativos', 'Career coaching']
  },
  {
    id: 'amigro',
    name: 'amigroRH®',
    description: 'Servicios de administración de personal y reclutamiento masivo.',
    icon: <Building className="w-8 h-8 text-green-400" />,
    color: 'from-green-600 to-green-400',
    features: ['Reclutamiento masivo', 'Administración de personal', 'BPO']
  },
  {
    id: 'payroll',
    name: 'Nómina IA',
    description: 'Gestión inteligente de nómina con herramientas de cumplimiento.',
    icon: <Calculator className="w-8 h-8 text-purple-400" />,
    color: 'from-purple-600 to-purple-400',
    features: ['Procesamiento multipáis', 'Cumplimiento fiscal', 'Analítica avanzada']
  },
  {
    id: 'orgdev',
    name: 'Desarrollo Organizacional',
    description: 'Evaluación y desarrollo de equipos de alto desempeño.',
    icon: <Award className="w-8 h-8 text-orange-400" />,
    color: 'from-orange-600 to-orange-400',
    features: ['Assessments especializados', 'Clima laboral', 'Talent analytics']
  }
];

const BusinessUnits: React.FC<BusinessUnitsProps> = ({ mousePosition }) => {
  return (
    <div className="w-full h-full flex flex-col items-center justify-center py-12 px-4">
      <motion.div 
        className="text-center mb-12"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <h2 className="text-4xl font-bold mb-3 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
          Unidades de <span className="text-red-500">Negocio</span>
        </h2>
        <p className="text-gray-400 max-w-2xl mx-auto">
          Grupo huntRED® ofrece soluciones especializadas para cada etapa del ciclo de vida
          del talento a través de sus unidades de negocio estratégicamente diseñadas.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
        {businessUnits.map((unit, index) => (
          <motion.div
            key={unit.id}
            className="bg-gray-900/80 backdrop-blur-sm border border-gray-800 rounded-xl overflow-hidden"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + index * 0.1 }}
            style={{
              transform: `perspective(1000px) rotateX(${(mousePosition.y - 0.5) * 5}deg) rotateY(${(mousePosition.x - 0.5) * 5}deg)`,
              transition: 'transform 0.2s ease-out',
            }}
          >
            {/* Header */}
            <div className={`bg-gradient-to-r ${unit.color} p-4 flex items-center gap-3`}>
              <div className="bg-white/20 rounded-full p-2">
                {unit.icon}
              </div>
              <h3 className="text-white text-xl font-semibold">{unit.name}</h3>
            </div>

            {/* Content */}
            <div className="p-5">
              <p className="text-gray-300 text-sm mb-4">
                {unit.description}
              </p>

              <ul className="space-y-2 mb-4">
                {unit.features.map((feature, idx) => (
                  <li key={idx} className="text-gray-400 text-xs flex items-center gap-2">
                    <span className={`w-1 h-1 rounded-full bg-${unit.color.split(' ')[0].replace('from-', '')}`}></span>
                    {feature}
                  </li>
                ))}
              </ul>
              
              <button 
                className="w-full mt-2 px-3 py-1.5 text-sm rounded-md border border-gray-700 text-white hover:bg-gray-800"
              >
                Conocer más
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default BusinessUnits;
