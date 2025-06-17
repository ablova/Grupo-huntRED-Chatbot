
import React, { useState } from 'react';
import { BookUser, GraduationCap, TrendingUp, ArrowUp } from 'lucide-react';

const LearningSection = () => {
  const [selectedLevel, setSelectedLevel] = useState('senior');

  const skillGaps = [
    { skill: 'Cloud Architecture', current: 60, required: 85, priority: 'Alta' },
    { skill: 'Team Leadership', current: 70, required: 90, priority: 'Media' },
    { skill: 'Strategic Planning', current: 45, required: 80, priority: 'Alta' },
    { skill: 'Data Analytics', current: 55, required: 75, priority: 'Media' },
  ];

  const recommendations = [
    { 
      title: 'AWS Solutions Architect', 
      provider: 'Amazon Web Services',
      duration: '3 meses',
      type: 'Certificación',
      impact: '+25% Cloud Skills'
    },
    { 
      title: 'Executive Leadership Program', 
      provider: 'MIT Sloan',
      duration: '6 semanas',
      type: 'Programa',
      impact: '+20% Leadership'
    },
    { 
      title: 'Data Science Fundamentals', 
      provider: 'Stanford Online',
      duration: '8 semanas',
      type: 'Curso',
      impact: '+20% Analytics'
    }
  ];

  return (
    <section className="py-20 bg-white dark:bg-slate-900">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
            Módulo de Learning
          </h2>
          <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
            Cierra las brechas de habilidades para alcanzar el siguiente nivel en tu carrera profesional
          </p>
        </div>

        {/* Career Level Selector */}
        <div className="max-w-md mx-auto mb-12">
          <label className="block text-sm font-semibold mb-3 text-center">Objetivo de Carrera</label>
          <select 
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
            className="w-full p-3 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-center"
          >
            <option value="senior">Senior Developer → Tech Lead</option>
            <option value="lead">Tech Lead → Engineering Manager</option>
            <option value="manager">Engineering Manager → Director</option>
            <option value="director">Director → VP Engineering</option>
          </select>
        </div>

        {/* Skill Gaps Analysis */}
        <div className="grid lg:grid-cols-2 gap-12 mb-16">
          <div>
            <h3 className="text-2xl font-bold mb-6 flex items-center">
              <TrendingUp className="w-6 h-6 mr-3 text-red-500" />
              Análisis de Brechas
            </h3>
            <div className="space-y-4">
              {skillGaps.map((gap, index) => (
                <div key={index} className="glass p-6 rounded-xl">
                  <div className="flex justify-between items-start mb-3">
                    <h4 className="font-semibold">{gap.skill}</h4>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      gap.priority === 'Alta' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {gap.priority}
                    </span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Actual: {gap.current}%</span>
                      <span>Requerido: {gap.required}%</span>
                    </div>
                    <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3">
                      <div className="relative h-3 rounded-full">
                        <div 
                          className="bg-blue-500 h-3 rounded-full"
                          style={{ width: `${gap.current}%` }}
                        ></div>
                        <div 
                          className="absolute top-0 bg-green-500 h-1 rounded-full"
                          style={{ left: `${gap.required}%`, width: '2px' }}
                        ></div>
                      </div>
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">
                      Brecha: {gap.required - gap.current} puntos
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-2xl font-bold mb-6 flex items-center">
              <GraduationCap className="w-6 h-6 mr-3 text-green-500" />
              Recomendaciones de Aprendizaje
            </h3>
            <div className="space-y-4">
              {recommendations.map((rec, index) => (
                <div key={index} className="glass p-6 rounded-xl hover:scale-105 transition-all duration-300">
                  <div className="flex justify-between items-start mb-3">
                    <h4 className="font-semibold text-blue-600">{rec.title}</h4>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                      {rec.type}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">{rec.provider}</p>
                  <div className="flex justify-between text-sm mb-3">
                    <span>⏱️ {rec.duration}</span>
                    <span className="text-green-600 font-medium">{rec.impact}</span>
                  </div>
                  <button className="w-full bg-gradient-to-r from-blue-500 to-green-500 text-white py-2 rounded-lg hover:opacity-90 transition-opacity">
                    Comenzar Aprendizaje
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Progress Timeline */}
        <div className="glass p-8 rounded-xl">
          <h3 className="text-2xl font-bold mb-6 text-center">Timeline de Desarrollo</h3>
          <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold mb-2">1</div>
              <p className="text-sm">Actual</p>
              <p className="font-semibold">Senior Dev</p>
            </div>
            <ArrowUp className="w-6 h-6 text-slate-400 rotate-90 md:rotate-0" />
            <div className="text-center">
              <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center text-white font-bold mb-2">2</div>
              <p className="text-sm">3-6 meses</p>
              <p className="font-semibold">Tech Lead</p>
            </div>
            <ArrowUp className="w-6 h-6 text-slate-400 rotate-90 md:rotate-0" />
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-500 rounded-full flex items-center justify-center text-white font-bold mb-2">3</div>
              <p className="text-sm">12-18 meses</p>
              <p className="font-semibold">Eng. Manager</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default LearningSection;
