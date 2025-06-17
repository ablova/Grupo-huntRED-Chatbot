
import React, { useState } from 'react';
import { Users, Target, TrendingUp, Building2, Briefcase, Award } from 'lucide-react';

const MatchmakingSection = () => {
  const [selectedDivision, setSelectedDivision] = useState('tech');
  const [selectedUnit, setSelectedUnit] = useState('huntred-executive');

  const categories = [
    { id: 'skills', name: 'Habilidades Técnicas', icon: '⚡', weight: 25 },
    { id: 'experience', name: 'Experiencia', icon: '📊', weight: 20 },
    { id: 'education', name: 'Educación', icon: '🎓', weight: 15 },
    { id: 'culture', name: 'Fit Cultural', icon: '🤝', weight: 15 },
    { id: 'leadership', name: 'Liderazgo', icon: '👑', weight: 10 },
    { id: 'innovation', name: 'Innovación', icon: '💡', weight: 5 },
    { id: 'communication', name: 'Comunicación', icon: '💬', weight: 5 },
    { id: 'adaptability', name: 'Adaptabilidad', icon: '🔄', weight: 3 },
    { id: 'growth', name: 'Potencial', icon: '🚀', weight: 2 }
  ];

  const divisions = [
    { value: 'financial-services', label: 'Servicios Financieros' },
    { value: 'legal', label: 'Legal' },
    { value: 'energy', label: 'Energía' },
    { value: 'healthcare', label: 'Healthcare' },
    { value: 'sales-marketing', label: 'Ventas y Mercadotecnia' },
    { value: 'finance-accounting', label: 'Finanzas y Contabilidad' },
    { value: 'manufacturing', label: 'Manufactura e Industria' },
    { value: 'tech', label: 'Tecnologías de la Información' },
    { value: 'sustainability', label: 'Sustentabilidad' }
  ];

  const businessUnits = [
    { value: 'huntred-executive', label: 'huntRED® Executive' },
    { value: 'huntred-m', label: 'huntRED® m' },
    { value: 'huntu', label: 'huntU' },
    { value: 'amigro', label: 'Amigro' }
  ];

  return (
    <section className="py-20 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Análisis de Matchmaking Inteligente
          </h2>
          <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
            Sistema avanzado de análisis con 9 categorías personalizables por división sectorial/funcional y unidad de negocio
          </p>
        </div>

        {/* Division & Unit Selectors */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          <div className="glass p-6 rounded-xl">
            <label className="block text-sm font-semibold mb-3">División</label>
            <select 
              value={selectedDivision}
              onChange={(e) => setSelectedDivision(e.target.value)}
              className="w-full p-3 rounded-lg bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700"
            >
              {divisions.map(division => (
                <option key={division.value} value={division.value}>{division.label}</option>
              ))}
            </select>
          </div>
          <div className="glass p-6 rounded-xl">
            <label className="block text-sm font-semibold mb-3">Unidad de Negocio</label>
            <select 
              value={selectedUnit}
              onChange={(e) => setSelectedUnit(e.target.value)}
              className="w-full p-3 rounded-lg bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700"
            >
              {businessUnits.map(unit => (
                <option key={unit.value} value={unit.value}>{unit.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Categories Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {categories.map((category) => (
            <div key={category.id} className="glass p-6 rounded-xl hover:scale-105 transition-all duration-300">
              <div className="flex items-center justify-between mb-4">
                <span className="text-3xl">{category.icon}</span>
                <span className="text-sm font-semibold text-blue-600">{category.weight}%</span>
              </div>
              <h3 className="font-semibold mb-2">{category.name}</h3>
              <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-1000"
                  style={{ width: `${category.weight * 4}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>

        {/* Match Results */}
        <div className="glass p-8 rounded-xl">
          <h3 className="text-2xl font-bold mb-6 text-center">Resultados del Análisis</h3>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-r from-green-400 to-green-600 rounded-full flex items-center justify-center">
                <Target className="w-8 h-8 text-white" />
              </div>
              <h4 className="font-semibold mb-2">Match Score</h4>
              <p className="text-3xl font-bold text-green-600">87%</p>
            </div>
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-r from-blue-400 to-blue-600 rounded-full flex items-center justify-center">
                <TrendingUp className="w-8 h-8 text-white" />
              </div>
              <h4 className="font-semibold mb-2">Potencial</h4>
              <p className="text-3xl font-bold text-blue-600">Alto</p>
            </div>
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-r from-purple-400 to-purple-600 rounded-full flex items-center justify-center">
                <Award className="w-8 h-8 text-white" />
              </div>
              <h4 className="font-semibold mb-2">Recomendación</h4>
              <p className="text-3xl font-bold text-purple-600">★★★★★</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default MatchmakingSection;
