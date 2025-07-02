import React, { useState } from 'react';
import { ChevronRight, Users, Clock, CheckCircle, FileText, Video, Target } from 'lucide-react';
import { motion } from 'framer-motion';

const RecruitmentDashboard = ({ clientName }) => {
  const [selectedUnit, setSelectedUnit] = useState('huntred-executive');

  const businessUnits = [
    { value: 'huntred-executive', label: 'huntRED® Executive', color: 'from-slate-600 to-slate-700' },
    { value: 'huntred-m', label: 'huntRED® ', color: 'from-blue-500 to-blue-600' },
    { value: 'huntu', label: 'huntU®', color: 'from-green-500 to-green-600' },
    { value: 'amigro', label: 'Amigro®', color: 'from-orange-500 to-red-500' }
  ];

  const kanbanColumns = [
    {
      id: 'sourcing',
      title: 'Sourcing',
      icon: Target,
      color: 'border-blue-200 bg-blue-50',
      headerColor: 'bg-blue-500'
    },
    {
      id: 'assessment',
      title: 'Assessment',
      icon: FileText,
      color: 'border-purple-200 bg-purple-50',
      headerColor: 'bg-purple-500'
    },
    {
      id: 'interviews',
      title: 'Entrevistas',
      icon: Video,
      color: 'border-orange-200 bg-orange-50',
      headerColor: 'bg-orange-500'
    },
    {
      id: 'evaluation',
      title: 'Evaluación',
      icon: Clock,
      color: 'border-yellow-200 bg-yellow-50',
      headerColor: 'bg-yellow-500'
    },
    {
      id: 'completed',
      title: 'Completados',
      icon: CheckCircle,
      color: 'border-green-200 bg-green-50',
      headerColor: 'bg-green-500'
    }
  ];

  // Sample data - in a real app, this would come from an API
  const candidateCards = {
    sourcing: [
      { id: 1, name: 'Ana García', position: 'Senior Developer', score: null, status: 'En búsqueda' },
      { id: 2, name: 'Carlos López', position: 'Product Manager', score: null, status: 'Contactado' }
    ],
    assessment: [
      { id: 3, name: 'María Rodríguez', position: 'UX Designer', score: 85, status: 'Assessment' },
      { id: 4, name: 'Juan Pérez', position: 'Data Scientist', score: 92, status: 'Assessment' }
    ],
    interviews: [
      { id: 5, name: 'Laura Martín', position: 'Tech Lead', score: 88, status: 'Entrevista' },
      { id: 6, name: 'Diego Torres', position: 'DevOps', score: 90, status: 'Entrevista' }
    ],
    evaluation: [
      { id: 7, name: 'Sofia Chen', position: 'Frontend', score: 95, status: 'Evaluación' }
    ],
    completed: [
      { id: 8, name: 'Roberto Silva', position: 'Backend', score: 89, status: 'Oferta' },
      { id: 9, name: 'Elena Vega', position: 'QA', score: 87, status: 'Contratado' }
    ]
  };

  const getScoreColor = (score) => {
    if (!score) return 'text-gray-500';
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-blue-600';
    if (score >= 70) return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <div className="mt-12 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="p-6">
        <div className="mb-8">
          <h3 className="text-2xl font-bold text-gray-800 mb-2">Seguimiento del Proceso de Selección</h3>
          <p className="text-gray-600">Visualización en tiempo real del progreso de los candidatos para {clientName}</p>
        </div>

        {/* Business Unit Selector */}
        <div className="mb-8">
          <div className="inline-flex p-1 bg-gray-100 rounded-lg">
            {businessUnits.map((unit) => (
              <button
                key={unit.value}
                onClick={() => setSelectedUnit(unit.value)}
                className={`px-4 py-2 rounded-md font-medium text-sm transition-colors ${
                  selectedUnit === unit.value
                    ? `bg-gradient-to-r ${unit.color} text-white shadow`
                    : 'text-gray-600 hover:bg-gray-200'
                }`}
              >
                {unit.label}
              </button>
            ))}
          </div>
        </div>

        {/* Kanban Board */}
        <div className="overflow-x-auto pb-4 -mx-2">
          <div className="flex space-x-4 min-w-max px-2">
            {kanbanColumns.map((column) => {
              const ColumnIcon = column.icon;
              const cards = candidateCards[column.id] || [];
              
              return (
                <motion.div 
                  key={column.id} 
                  className={`w-64 flex-shrink-0 rounded-lg border ${column.color} min-h-[400px]`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  {/* Column Header */}
                  <div className={`${column.headerColor} text-white p-3 rounded-t-lg flex items-center justify-between`}>
                    <div className="flex items-center space-x-2">
                      <ColumnIcon className="w-4 h-4" />
                      <span className="text-sm font-medium">{column.title}</span>
                    </div>
                    <span className="bg-white/20 px-2 py-0.5 rounded-full text-xs font-medium">
                      {cards.length}
                    </span>
                  </div>

                  {/* Cards */}
                  <div className="p-3 space-y-3">
                    {cards.map((card) => (
                      <motion.div 
                        key={card.id} 
                        className="bg-white p-3 rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-all duration-200 cursor-move"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <div className="flex items-start justify-between mb-1">
                          <h4 className="font-medium text-sm text-gray-800">
                            {card.name}
                          </h4>
                          {card.score && (
                            <span className={`text-xs font-bold ${getScoreColor(card.score)}`}>
                              {card.score}%
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-600 mb-2">
                          {card.position}
                        </p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
                            {card.status}
                          </span>
                          <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
                        </div>
                      </motion.div>
                    ))}
                    {cards.length === 0 && (
                      <div className="text-center py-6 text-gray-400 text-sm">
                        Sin candidatos
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="bg-gray-50 border-t border-gray-100 p-4">
        <div className="grid grid-cols 2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Candidatos', value: '9', icon: Users, color: 'text-blue-500' },
            { label: 'En Proceso', value: '7', icon: Clock, color: 'text-yellow-500' },
            { label: 'Entrevistas', value: '2', icon: Video, color: 'text-orange-500' },
            { label: 'Contratados', value: '2', icon: CheckCircle, color: 'text-green-500' },
          ].map((stat, index) => {
            const Icon = stat.icon;
            return (
              <div key={index} className="bg-white p-3 rounded-lg border border-gray-100 shadow-xs">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg ${stat.color} bg-opacity-10 mr-3`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">{stat.label}</p>
                    <p className="text-lg font-semibold text-gray-800">{stat.value}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default RecruitmentDashboard;
