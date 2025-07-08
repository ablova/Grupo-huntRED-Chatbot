import React, { useState } from 'react';
import { BookUser, GraduationCap, TrendingUp, ArrowUp, Sparkles, Brain, BadgeCheck, LineChart, Users, Star } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const LearningSection = () => {
  const [selectedLevel, setSelectedLevel] = useState('senior');
  const [showAuraModal, setShowAuraModal] = useState(false);

  const skillGaps = [
    { skill: 'Cloud Architecture', current: 60, required: 85, priority: 'Alta', auraImpact: 25 },
    { skill: 'Team Leadership', current: 70, required: 90, priority: 'Media', auraImpact: 18 },
    { skill: 'Strategic Planning', current: 45, required: 80, priority: 'Alta', auraImpact: 30 },
    { skill: 'Data Analytics', current: 55, required: 75, priority: 'Media', auraImpact: 22 },
  ];

  const recommendations = [
    { 
      title: 'AWS Solutions Architect', 
      provider: 'Amazon Web Services',
      duration: '3 meses',
      type: 'Certificación',
      impact: '+25% Cloud Skills',
      aura: true,
      auraBoost: '+40% efectividad',
      icon: <BadgeCheck className="h-5 w-5 text-blue-500" />
    },
    { 
      title: 'Executive Leadership Program', 
      provider: 'MIT Sloan',
      duration: '6 semanas',
      type: 'Programa',
      impact: '+20% Leadership',
      aura: true,
      auraBoost: '+35% efectividad',
      icon: <Users className="h-5 w-5 text-purple-500" />
    },
    { 
      title: 'Data Science Fundamentals', 
      provider: 'Stanford Online',
      duration: '8 semanas',
      type: 'Curso',
      impact: '+20% Analytics',
      aura: true,
      auraBoost: '+30% efectividad',
      icon: <LineChart className="h-5 w-5 text-green-500" />
    }
  ];
  
  // Características de AURA para Learning
  const auraFeatures = [
    {
      icon: <Brain className="h-6 w-6" />,
      title: "Inteligencia Adaptativa",
      description: "AURA aprende de tus hábitos de estudio y adapta los materiales a tu estilo de aprendizaje único."
    },
    {
      icon: <Star className="h-6 w-6" />,
      title: "Enfoque Personalizado",
      description: "Identifica tus fortalezas y áreas de mejora para crear un plan de upskilling completamente a tu medida."
    },
    {
      icon: <TrendingUp className="h-6 w-6" />,
      title: "Predictive Career Path",
      description: "Analiza tendencias del mercado para guiar tu desarrollo hacia las habilidades con mayor demanda futura."
    },
    {
      icon: <Sparkles className="h-6 w-6" />,
      title: "Aprendizaje Potenciado",
      description: "Incrementa la retención y aplicación práctica del conocimiento mediante técnicas de microlearning optimizadas."
    }
  ];

  return (
    <section className="py-20 bg-white dark:bg-slate-900">
      <div className="container mx-auto px-4">
        {/* AURA Feature Alert */}
        <motion.div 
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="flex items-center justify-between mb-10 p-4 md:p-6 bg-gradient-to-r from-purple-600/10 to-blue-600/10 border border-blue-200 dark:border-blue-900 rounded-xl"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-gradient-to-br from-blue-500 to-purple-600 p-3 rounded-lg mr-4">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-lg text-blue-700 dark:text-blue-400">Potenciado por AURA™</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">Este módulo requiere la activación de AURA™ para funcionar con todas sus capacidades</p>
            </div>
          </div>
          <Button onClick={() => setShowAuraModal(true)} variant="ghost" className="bg-blue-100 dark:bg-blue-900/40 hover:bg-blue-200 text-blue-700 dark:text-blue-400 dark:hover:bg-blue-800/60">
            <span className="flex items-center">
              <Sparkles className="w-4 h-4 mr-2" /> Ver Beneficios
            </span>
          </Button>
        </motion.div>

        <div className="text-center mb-16">
          <motion.h2 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent flex items-center justify-center gap-3"
          >
            <GraduationCap className="inline-block h-10 w-10" /> Módulo de Learning
          </motion.h2>
          <motion.p 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto"
          >
            Cierra las brechas de habilidades para alcanzar el siguiente nivel en tu carrera profesional
          </motion.p>
        </div>

        {/* AURA Modal */}
        {showAuraModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="bg-white dark:bg-slate-800 rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent flex items-center">
                  <Sparkles className="h-6 w-6 mr-2 text-purple-500" /> AURA™ para Learning
                </h3>
                <button 
                  onClick={() => setShowAuraModal(false)}
                  className="p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700"
                >
                  <span className="sr-only">Cerrar</span>
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="grid sm:grid-cols-2 gap-6 mb-8">
                {auraFeatures.map((feature, index) => (
                  <div key={index} className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
                    <div className="flex items-center mb-3">
                      <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg mr-3">
                        {feature.icon}
                      </div>
                      <h4 className="font-semibold text-lg">{feature.title}</h4>
                    </div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">{feature.description}</p>
                  </div>
                ))}
              </div>
              
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg mb-6">
                <h4 className="font-semibold mb-2 flex items-center">
                  <BadgeCheck className="w-5 h-5 mr-2 text-blue-500" /> Beneficios Exclusivos
                </h4>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start">
                    <span className="text-green-500 mr-2">✓</span>
                    Incrementa la efectividad del aprendizaje hasta un 40%
                  </li>
                  <li className="flex items-start">
                    <span className="text-green-500 mr-2">✓</span>
                    Identifica automáticamente oportunidades de crecimiento alineadas al perfil
                  </li>
                  <li className="flex items-start">
                    <span className="text-green-500 mr-2">✓</span>
                    Aprendizaje continuo que evoluciona con las tendencias del mercado
                  </li>
                </ul>
              </div>
              
              <div className="flex justify-end space-x-3">
                <Button onClick={() => setShowAuraModal(false)} variant="outline">
                  Cerrar
                </Button>
                <Button className="bg-gradient-to-r from-purple-600 to-blue-600 text-white">
                  <Sparkles className="w-4 h-4 mr-2" /> Activar AURA
                </Button>
              </div>
            </motion.div>
          </div>
        )}
        
        {/* Career Level Selector */}
        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="max-w-md mx-auto mb-12"
        >
          <div className="flex items-center justify-center gap-2 mb-3">
            <label className="block text-sm font-semibold text-center">Objetivo de Carrera</label>
            <Badge variant="outline" className="bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 border-purple-200 dark:border-purple-800">
              Potenciado por AURA
            </Badge>
          </div>
          <select 
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
            className="w-full p-3 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-center focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="senior">Senior Developer → Tech Lead</option>
            <option value="lead">Tech Lead → Engineering Manager</option>
            <option value="manager">Engineering Manager → Director</option>
            <option value="director">Director → VP Engineering</option>
          </select>
        </motion.div>

        {/* Skill Gaps Analysis */}
        <div className="grid lg:grid-cols-2 gap-12 mb-16">
          <motion.div 
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <h3 className="text-2xl font-bold mb-6 flex items-center">
              <TrendingUp className="w-6 h-6 mr-3 text-purple-500" />
              Análisis de Brechas
            </h3>
            <div className="space-y-4">
              {skillGaps.map((gap, index) => (
                <motion.div 
                  key={index} 
                  className="glass p-6 rounded-xl border border-slate-200 dark:border-slate-700 hover:shadow-md transition-all duration-300"
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.5 + (index * 0.1) }}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center">
                      <h4 className="font-semibold">{gap.skill}</h4>
                      <Badge className="ml-2 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 border-purple-200">
                        <Sparkles className="w-3 h-3 mr-1" /> AURA
                      </Badge>
                    </div>
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
                          className="absolute top-0 h-3 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 opacity-40"
                          style={{ width: `${gap.auraImpact}%`, left: `${gap.current}%` }}
                        ></div>
                        <div 
                          className="absolute top-0 bg-green-500 h-1 rounded-full"
                          style={{ left: `${gap.required}%`, width: '2px' }}
                        ></div>
                      </div>
                    </div>
                    <div className="flex justify-between text-sm">
                      <div className="text-slate-600 dark:text-slate-400">
                        Brecha: {gap.required - gap.current} puntos
                      </div>
                      <div className="text-purple-600 dark:text-purple-400 font-medium flex items-center">
                        <Sparkles className="w-3 h-3 mr-1" /> +{gap.auraImpact}% con AURA
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <h3 className="text-2xl font-bold mb-6 flex items-center">
              <GraduationCap className="w-6 h-6 mr-3 text-blue-500" />
              Recomendaciones de Aprendizaje
            </h3>
            <div className="space-y-4">
              {recommendations.map((rec, index) => (
                <motion.div 
                  key={index} 
                  className="glass p-6 rounded-xl border border-slate-200 dark:border-slate-700 hover:scale-102 hover:shadow-lg transition-all duration-300"
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.5 + (index * 0.1) }}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center gap-2">
                      {rec.icon}
                      <h4 className="font-semibold text-blue-600">{rec.title}</h4>
                    </div>
                    <div className="flex items-center gap-2">
                      {rec.aura && (
                        <Badge className="bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300">
                          <Sparkles className="w-3 h-3 mr-1" /> AURA
                        </Badge>
                      )}
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                        {rec.type}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">{rec.provider}</p>
                  <div className="flex justify-between text-sm mb-3">
                    <span>⏰ {rec.duration}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-green-600 font-medium">{rec.impact}</span>
                      {rec.auraBoost && (
                        <span className="text-purple-600 font-medium flex items-center">
                          <Sparkles className="w-3 h-3 mr-1" />
                          {rec.auraBoost}
                        </span>
                      )}
                    </div>
                  </div>
                  <Button className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:opacity-90 transition-opacity">
                    Comenzar Aprendizaje
                  </Button>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Progress Timeline */}
        <motion.div 
          className="glass p-8 rounded-xl border border-slate-200 dark:border-slate-700"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.8 }}
        >
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-2xl font-bold flex items-center">
              <TrendingUp className="w-6 h-6 mr-3 text-green-500" /> Career Roadmap
            </h3>
            <Badge className="bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300">
              <Sparkles className="w-3 h-3 mr-1" /> AURA Predictive
            </Badge>
          </div>
          
          <div className="flex flex-col md:flex-row items-center justify-between space-y-8 md:space-y-0">
            <div className="text-center relative">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white font-bold mb-3 shadow-lg">
                <BookUser className="w-8 h-8" />
              </div>
              <p className="text-sm text-blue-600 dark:text-blue-400 font-medium">Actual</p>
              <p className="font-semibold text-lg">Senior Dev</p>
              <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">0 meses</div>
            </div>
            
            <div className="hidden md:block w-full max-w-[100px] h-1 bg-gradient-to-r from-blue-500 to-green-500 relative">
              <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 text-xs text-slate-500 dark:text-slate-400">+Skills</div>
            </div>
            
            <div className="text-center relative">
              <div className="w-20 h-20 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center text-white font-bold mb-3 shadow-lg">
                <Users className="w-8 h-8" />
              </div>
              <p className="text-sm text-green-600 dark:text-green-400 font-medium">Siguiente</p>
              <p className="font-semibold text-lg">Tech Lead</p>
              <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">3-6 meses</div>
              
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 px-2 py-1 rounded-md text-xs flex items-center">
                <Sparkles className="w-3 h-3 mr-1" /> -30% tiempo con AURA
              </div>
            </div>
            
            <div className="hidden md:block w-full max-w-[100px] h-1 bg-gradient-to-r from-green-500 to-purple-500 relative">
              <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 text-xs text-slate-500 dark:text-slate-400">+Liderazgo</div>
            </div>
            
            <div className="text-center relative">
              <div className="w-20 h-20 bg-gradient-to-br from-purple-400 to-purple-600 rounded-full flex items-center justify-center text-white font-bold mb-3 shadow-lg opacity-90">
                <Star className="w-8 h-8" />
              </div>
              <p className="text-sm text-purple-600 dark:text-purple-400 font-medium">Objetivo</p>
              <p className="font-semibold text-lg">Eng. Manager</p>
              <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">12-18 meses</div>
            </div>
          </div>
          
          <div className="mt-8 bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
            <h4 className="font-medium mb-2 flex items-center text-blue-800 dark:text-blue-300">
              <BadgeCheck className="w-5 h-5 mr-2" /> Beneficio AURA
            </h4>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Con AURA, tu desarrollo profesional es potenciado a través de un análisis predictivo constante 
              que identifica las habilidades emergentes más demandadas en el mercado y adapta tu plan de carrera 
              para maximizar tu progresión y relevancia profesional.
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default LearningSection;
