
import React, { useState } from 'react';
import { ChevronRight, Users, Clock, CheckCircle, AlertCircle, FileText, Video, Target } from 'lucide-react';

const KanbanDashboardSection = () => {
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
      color: 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950',
      headerColor: 'bg-blue-500'
    },
    {
      id: 'assessment',
      title: 'Assessment',
      icon: FileText,
      color: 'border-purple-200 bg-purple-50 dark:border-purple-800 dark:bg-purple-950',
      headerColor: 'bg-purple-500'
    },
    {
      id: 'interviews',
      title: 'Entrevistas',
      icon: Video,
      color: 'border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-950',
      headerColor: 'bg-orange-500'
    },
    {
      id: 'evaluation',
      title: 'Evaluación',
      icon: Clock,
      color: 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950',
      headerColor: 'bg-yellow-500'
    },
    {
      id: 'completed',
      title: 'Completados',
      icon: CheckCircle,
      color: 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950',
      headerColor: 'bg-green-500'
    }
  ];

  const candidateCards = {
    sourcing: [
      { id: 1, name: 'Ana García', position: 'Senior Developer', score: null, status: 'En búsqueda' },
      { id: 2, name: 'Carlos López', position: 'Product Manager', score: null, status: 'Contactado' }
    ],
    assessment: [
      { id: 3, name: 'María Rodríguez', position: 'UX Designer', score: 85, status: 'Assessment en curso' },
      { id: 4, name: 'Juan Pérez', position: 'Data Scientist', score: 92, status: 'Assessment completado' }
    ],
    interviews: [
      { id: 5, name: 'Laura Martín', position: 'Tech Lead', score: 88, status: 'Primera entrevista' },
      { id: 6, name: 'Diego Torres', position: 'DevOps Engineer', score: 90, status: 'Segunda entrevista' }
    ],
    evaluation: [
      { id: 7, name: 'Sofia Chen', position: 'Frontend Developer', score: 95, status: 'Evaluación final' }
    ],
    completed: [
      { id: 8, name: 'Roberto Silva', position: 'Backend Developer', score: 89, status: 'Oferta enviada' },
      { id: 9, name: 'Elena Vega', position: 'QA Engineer', score: 87, status: 'Contratado' }
    ]
  };

  const getScoreColor = (score: number | null) => {
    if (!score) return 'text-gray-500';
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-blue-600';
    if (score >= 70) return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <section id="kanban-dashboard" className="py-20 bg-gradient-to-br from-slate-50 to-gray-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-slate-600 to-gray-800 bg-clip-text text-transparent">
            Dashboard de Selección
          </h2>
          <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
            Seguimiento en tiempo real del proceso de selección por unidad de negocio
          </p>
        </div>

        {/* Business Unit Selector */}
        <div className="mb-12 flex justify-center">
          <div className="glass p-2 rounded-xl">
            <div className="flex space-x-2">
              {businessUnits.map((unit) => (
                <button
                  key={unit.value}
                  onClick={() => setSelectedUnit(unit.value)}
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                    selectedUnit === unit.value
                      ? `bg-gradient-to-r ${unit.color} text-white shadow-lg`
                      : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                  }`}
                >
                  {unit.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Kanban Board */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6">
          {kanbanColumns.map((column) => {
            const ColumnIcon = column.icon;
            const cards = candidateCards[column.id as keyof typeof candidateCards] || [];
            
            return (
              <div key={column.id} className={`rounded-xl border-2 ${column.color} min-h-[500px]`}>
                {/* Column Header */}
                <div className={`${column.headerColor} text-white p-4 rounded-t-lg flex items-center justify-between`}>
                  <div className="flex items-center space-x-2">
                    <ColumnIcon className="w-5 h-5" />
                    <h3 className="font-semibold">{column.title}</h3>
                  </div>
                  <span className="bg-white/20 px-2 py-1 rounded-full text-sm font-medium">
                    {cards.length}
                  </span>
                </div>

                {/* Cards */}
                <div className="p-4 space-y-3">
                  {cards.map((card) => (
                    <div key={card.id} className="glass p-4 rounded-lg hover:scale-105 transition-all duration-300 cursor-pointer">
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-semibold text-slate-800 dark:text-slate-200">
                          {card.name}
                        </h4>
                        {card.score && (
                          <span className={`text-sm font-bold ${getScoreColor(card.score)}`}>
                            {card.score}%
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                        {card.position}
                      </p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs px-2 py-1 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                          {card.status}
                        </span>
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Statistics */}
        <div className="mt-16 grid md:grid-cols-4 gap-6">
          <div className="glass p-6 rounded-xl text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
              <Users className="w-6 h-6 text-white" />
            </div>
            <h4 className="font-semibold mb-1">Total Candidatos</h4>
            <p className="text-2xl font-bold text-blue-600">32</p>
          </div>

          <div className="glass p-6 rounded-xl text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full flex items-center justify-center">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <h4 className="font-semibold mb-1">Assessments</h4>
            <p className="text-2xl font-bold text-purple-600">18</p>
          </div>

          <div className="glass p-6 rounded-xl text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-gradient-to-r from-orange-500 to-orange-600 rounded-full flex items-center justify-center">
              <Video className="w-6 h-6 text-white" />
            </div>
            <h4 className="font-semibold mb-1">Entrevistas</h4>
            <p className="text-2xl font-bold text-orange-600">12</p>
          </div>

          <div className="glass p-6 rounded-xl text-center">
            <div className="w-12 h-12 mx-auto mb-3 bg-gradient-to-r from-green-500 to-green-600 rounded-full flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-white" />
            </div>
            <h4 className="font-semibold mb-1">Completados</h4>
            <p className="text-2xl font-bold text-green-600">8</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default KanbanDashboardSection;
