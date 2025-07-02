import React from 'react';
import { motion } from 'framer-motion';
import { Calendar, Clock, CheckCircle, Users, FileText, BarChart2 } from 'lucide-react';

const ProcessTimeline = () => {
  const phases = [
    {
      title: "Análisis de Necesidades",
      description: "Entendimiento profundo del perfil requerido y del contexto organizacional.",
      duration: "1-2 días",
      icon: <BarChart2 className="w-6 h-6" />,
      features: [
        "Reunión de alineación",
        "Definición de competencias clave",
        "Análisis de mercado"
      ]
    },
    {
      title: "Búsqueda y Atracción",
      description: "Búsqueda activa de candidatos mediante múltiples canales y tecnologías.",
      duration: "3-5 días",
      icon: <Users className="w-6 h-6" />,
      features: [
        "Búsqueda en base de datos propia",
        "Atracción activa en redes profesionales",
        "Uso de IA para matching"
      ]
    },
    {
      title: "Evaluación y Entrevistas",
      description: "Proceso de evaluación integral con herramientas tecnológicas avanzadas.",
      duration: "3-4 días",
      icon: <FileText className="w-6 h-6" />,
      features: [
        "Evaluación técnica",
        "Entrevistas por competencias",
        "Pruebas psicométricas"
      ]
    },
    {
      title: "Presentación y Selección",
      description: "Presentación de candidatos y soporte en el proceso de decisión.",
      duration: "2-3 días",
      icon: <CheckCircle className="w-6 h-6" />,
      features: [
        "Informes detallados",
        "Presentación de candidatos",
        "Soporte en negociación"
      ]
    },
    {
      title: "Incorporación y Seguimiento",
      description: "Acompañamiento durante la incorporación y seguimiento post-contratación.",
      duration: "30-90 días",
      icon: <Users className="w-6 h-6" />,
      features: [
        "Plan de onboarding",
        "Seguimiento mensual",
        "Garantía extendida"
      ]
    }
  ];

  return (
    <div className="relative">
      {/* Línea del tiempo */}
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-blue-200"></div>
      
      <div className="space-y-12">
        {phases.map((phase, index) => (
          <motion.div 
            key={index}
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className="relative pl-12"
          >
            {/* Punto en la línea del tiempo */}
            <div className="absolute left-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white -translate-x-1/2">
              {phase.icon}
            </div>
            
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <h3 className="text-xl font-semibold text-gray-800">{phase.title}</h3>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  <Clock className="w-4 h-4 mr-1" />
                  {phase.duration}
                </span>
              </div>
              
              <p className="mt-2 text-gray-600">{phase.description}</p>
              
              <div className="mt-4 pt-4 border-t border-gray-100">
                <h4 className="text-sm font-medium text-gray-500 mb-2">INCLUYE:</h4>
                <ul className="space-y-2">
                  {phase.features.map((feature, i) => (
                    <li key={i} className="flex items-start">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 mr-2 flex-shrink-0" />
                      <span className="text-sm text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              {index < phases.length - 1 && (
                <div className="absolute -bottom-6 left-12 right-0 h-6 flex justify-center">
                  <div className="h-full w-0.5 bg-blue-100"></div>
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>
      
      <div className="mt-8 bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-xl">
        <div className="flex items-start">
          <div className="bg-blue-100 p-3 rounded-lg mr-4">
            <Calendar className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-800">Tiempo total estimado</h3>
            <p className="text-gray-600">
              El proceso completo puede completarse en <span className="font-semibold text-blue-600">9-14 días hábiles</span>, 
              dependiendo de la disponibilidad para entrevistas y la complejidad del perfil.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessTimeline;
