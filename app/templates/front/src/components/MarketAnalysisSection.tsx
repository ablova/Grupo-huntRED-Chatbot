
import React, { useState } from 'react';
import { TrendingUp, DollarSign, BarChart, MapPin } from 'lucide-react';

const MarketAnalysisSection = () => {
  const [selectedRole, setSelectedRole] = useState('tech-lead');
  const [selectedLocation, setSelectedLocation] = useState('mx-cdmx');

  const salaryData = {
    'tech-lead': {
      base: 85000,
      range: { min: 70000, max: 120000 },
      percentile25: 75000,
      percentile75: 100000,
      equity: '0.1-0.3%',
      bonus: '10-20%'
    }
  };

  const benefits = [
    { name: 'Seguro Médico', coverage: '100%', value: 12000 },
    { name: 'Vacaciones', days: '25 días', value: 8000 },
    { name: 'Home Office', type: 'Híbrido', value: 15000 },
    { name: 'Capacitación', budget: '$5,000', value: 5000 },
  ];

  const marketTrends = [
    { skill: 'React/Next.js', demand: 95, growth: '+15%' },
    { skill: 'Python/Django', demand: 88, growth: '+12%' },
    { skill: 'AWS/Cloud', demand: 92, growth: '+18%' },
    { skill: 'AI/ML', demand: 85, growth: '+25%' },
  ];

  return (
    <section className="py-20 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            Marketing Analysis
          </h2>
          <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
            Análisis completo de mercado: salarios, compensación y tendencias laborales
          </p>
        </div>

        {/* Role & Location Selectors */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          <div className="glass p-6 rounded-xl">
            <label className="block text-sm font-semibold mb-3">Posición</label>
            <select 
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="w-full p-3 rounded-lg bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700"
            >
              <option value="tech-lead">Tech Lead</option>
              <option value="senior-dev">Senior Developer</option>
              <option value="eng-manager">Engineering Manager</option>
              <option value="director">Director of Engineering</option>
            </select>
          </div>
          <div className="glass p-6 rounded-xl">
            <label className="block text-sm font-semibold mb-3">Ubicación</label>
            <select 
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="w-full p-3 rounded-lg bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700"
            >
              <option value="mx-cdmx">Ciudad de México</option>
              <option value="mx-gdl">Guadalajara</option>
              <option value="mx-mty">Monterrey</option>
              <option value="remote">Remoto</option>
            </select>
          </div>
        </div>

        {/* Salary Analysis */}
        <div className="grid lg:grid-cols-2 gap-12 mb-16">
          <div className="glass p-8 rounded-xl">
            <h3 className="text-2xl font-bold mb-6 flex items-center">
              <DollarSign className="w-6 h-6 mr-3 text-green-500" />
              Análisis Salarial
            </h3>
            
            <div className="text-center mb-6">
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Salario Base Promedio</p>
              <p className="text-4xl font-bold text-green-600">${salaryData[selectedRole].base.toLocaleString()}</p>
              <p className="text-sm text-slate-500">USD anuales</p>
            </div>

            <div className="space-y-4 mb-6">
              <div className="flex justify-between">
                <span>Mínimo (P25)</span>
                <span className="font-semibold">${salaryData[selectedRole].percentile25.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span>Máximo (P75)</span>
                <span className="font-semibold">${salaryData[selectedRole].percentile75.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span>Equity</span>
                <span className="font-semibold">{salaryData[selectedRole].equity}</span>
              </div>
              <div className="flex justify-between">
                <span>Bonus</span>
                <span className="font-semibold">{salaryData[selectedRole].bonus}</span>
              </div>
            </div>

            <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-4 mb-2">
              <div className="relative h-4 rounded-full">
                <div className="bg-gradient-to-r from-green-400 to-green-600 h-4 rounded-full w-3/5"></div>
                <div className="absolute top-1 left-1/4 w-2 h-2 bg-white rounded-full"></div>
                <div className="absolute top-1 right-1/4 w-2 h-2 bg-white rounded-full"></div>
              </div>
            </div>
            <div className="flex justify-between text-xs text-slate-500">
              <span>P25</span>
              <span>Tu posición</span>
              <span>P75</span>
            </div>
          </div>

          <div className="glass p-8 rounded-xl">
            <h3 className="text-2xl font-bold mb-6 flex items-center">
              <BarChart className="w-6 h-6 mr-3 text-blue-500" />
              Beneficios Valorados
            </h3>
            
            <div className="space-y-4 mb-6">
              {benefits.map((benefit, index) => (
                <div key={index} className="flex justify-between items-center p-4 bg-white/50 dark:bg-slate-800/50 rounded-lg">
                  <div>
                    <p className="font-semibold">{benefit.name}</p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {benefit.coverage || benefit.days || benefit.type || benefit.budget}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-green-600">${benefit.value.toLocaleString()}</p>
                    <p className="text-xs text-slate-500">valor anual</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t pt-4">
              <div className="flex justify-between items-center">
                <span className="font-semibold">Valor Total Compensación</span>
                <span className="text-2xl font-bold text-purple-600">
                  ${(salaryData[selectedRole].base + benefits.reduce((sum, b) => sum + b.value, 0)).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Market Trends */}
        <div className="glass p-8 rounded-xl mb-12">
          <h3 className="text-2xl font-bold mb-6 flex items-center">
            <TrendingUp className="w-6 h-6 mr-3 text-purple-500" />
            Tendencias del Mercado
          </h3>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {marketTrends.map((trend, index) => (
              <div key={index} className="text-center p-4 bg-white/50 dark:bg-slate-800/50 rounded-lg">
                <h4 className="font-semibold mb-2">{trend.skill}</h4>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 mb-2">
                  <div 
                    className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                    style={{ width: `${trend.demand}%` }}
                  ></div>
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Demanda: {trend.demand}%</p>
                <p className="text-sm font-semibold text-green-600">{trend.growth}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendation */}
        <div className="glass p-8 rounded-xl text-center">
          <h3 className="text-2xl font-bold mb-4">Recomendación Personalizada</h3>
          <p className="text-lg text-slate-600 dark:text-slate-300 mb-6">
            Basado en tu perfil y el análisis de mercado, tu salario actual está en el percentil 65. 
            Considera negociar un incremento del 15% o explorar oportunidades con mejor compensación total.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-3 rounded-lg hover:opacity-90 transition-opacity">
              Ver Oportunidades
            </button>
            <button className="glass px-6 py-3 rounded-lg hover:scale-105 transition-transform">
              Descargar Reporte
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default MarketAnalysisSection;
