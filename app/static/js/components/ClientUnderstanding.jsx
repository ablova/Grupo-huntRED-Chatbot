import React, { useState, useEffect } from 'react';
import { Bar, Line } from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { Info, BarChart2, TrendingUp, Users, Zap, Award } from 'lucide-react';

const ClientUnderstanding = ({ clientData }) => {
  const [activeTab, setActiveTab] = useState('benchmark');
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Datos de ejemplo para el benchmark
  const benchmarkData = [
    { 
      metric: 'Tiempo de contratación (días)', 
      client: 45, 
      industry: 32,
      top25: 25
    },
    { 
      metric: 'Costo por contratación', 
      client: 12000, 
      industry: 8500,
      top25: 7000
    },
    { 
      metric: 'Retención 1er año', 
      client: 68, 
      industry: 75,
      top25: 85
    },
    { 
      metric: 'Satisfacción del gerente', 
      client: 72, 
      industry: 78,
      top25: 88
    },
  ];

  // Datos para la tendencia de contratación
  const hiringTrendData = [
    { name: 'Ene', value: 12 },
    { name: 'Feb', value: 15 },
    { name: 'Mar', value: 18 },
    { name: 'Abr', value: 22 },
    { name: 'May', value: 25 },
    { name: 'Jun', value: 28 },
  ];

  // Métricas clave
  const keyMetrics = [
    {
      title: 'Posiciones Críticas',
      value: '8',
      change: '+2',
      icon: <Users className="w-6 h-6" />,
      color: 'blue'
    },
    {
      title: 'Tiempo Promedio',
      value: '45 días',
      change: '-5',
      icon: <Clock className="w-6 h-6" />,
      color: 'green'
    },
    {
      title: 'Costo Promedio',
      value: '$12,000',
      change: '-8%',
      icon: <DollarSign className="w-6 h-6" />,
      color: 'purple'
    },
    {
      title: 'Retención',
      value: '68%',
      change: '+5%',
      icon: <Award className="w-6 h-6" />,
      color: 'orange'
    }
  ];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 shadow-lg rounded-lg border border-gray-200">
          <p className="font-semibold">{label}</p>
          {payload.map((item, index) => (
            <p key={index} style={{ color: item.color }}>
              {item.name}: {item.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (!isClient) return null;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold mb-2">Nuestra Comprensión de {clientData.name}</h2>
        <div className="h-1 w-16 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full mb-6"></div>
        <p className="text-gray-600 mb-6">
          Basado en nuestro análisis de la industria y datos internos, hemos identificado oportunidades clave 
          para optimizar su estrategia de adquisición de talento.
        </p>
      </div>

      {/* Métricas clave */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {keyMetrics.map((metric, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-all`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">{metric.title}</p>
                <p className="text-2xl font-bold mt-1">{metric.value}</p>
                <span className={`inline-flex items-center text-sm mt-1 ${
                  metric.change.startsWith('+') ? 'text-green-600' : 
                  metric.change.startsWith('-') ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {metric.change} vs. último trimestre
                </span>
              </div>
              <div className={`p-3 rounded-lg bg-${metric.color}-100 text-${metric.color}-600`}>
                {metric.icon}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Pestañas */}
      <div className="mt-8">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8">
            {[
              { id: 'benchmark', label: 'Benchmark de la Industria' },
              { id: 'trends', label: 'Tendencias' },
              { id: 'recommendations', label: 'Recomendaciones' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="mt-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ duration: 0.3 }}
            >
              {activeTab === 'benchmark' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold flex items-center">
                    <BarChart2 className="w-5 h-5 mr-2 text-blue-600" />
                    Comparativa con la industria
                  </h3>
                  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead>
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Métrica</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Su Empresa</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Promedio Industria</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Top 25%</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {benchmarkData.map((item, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {item.metric}
                              </td>
                              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-700 font-semibold">
                                {typeof item.client === 'number' && item.metric.includes('$') 
                                  ? `$${item.client.toLocaleString()}` 
                                  : item.client}
                              </td>
                              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-700">
                                {typeof item.industry === 'number' && item.metric.includes('$') 
                                  ? `$${item.industry.toLocaleString()}` 
                                  : item.industry}
                              </td>
                              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-700">
                                {typeof item.top25 === 'number' && item.metric.includes('$') 
                                  ? `$${item.top25.toLocaleString()}` 
                                  : item.top25}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div className="mt-4 text-sm text-gray-500 flex items-center">
                      <Info className="w-4 h-4 mr-1" />
                      Datos basados en análisis de la industria y benchmarks del sector.
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'trends' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
                    Tendencias de Contratación
                  </h3>
                  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={hiringTrendData}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip content={<CustomTooltip />} />
                          <Line 
                            type="monotone" 
                            dataKey="value" 
                            stroke="#3b82f6" 
                            strokeWidth={2}
                            dot={{ r: 4 }}
                            activeDot={{ r: 6, stroke: '#2563eb', strokeWidth: 2 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                    <p className="mt-4 text-sm text-gray-600">
                      Tendencias mensuales en el volumen de contrataciones. Se observa un crecimiento constante 
                      en la demanda de talento especializado en su sector.
                    </p>
                  </div>
                </div>
              )}

              {activeTab === 'recommendations' && (
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold flex items-center">
                    <Zap className="w-5 h-5 mr-2 text-blue-600" />
                    Recomendaciones Estratégicas
                  </h3>
                  <div className="space-y-4">
                    {[
                      {
                        title: 'Optimización del Proceso de Contratación',
                        description: 'Reducir el tiempo de contratación mediante la implementación de evaluaciones técnicas automatizadas en etapas tempranas.',
                        impact: 'Alto',
                        effort: 'Medio'
                      },
                      {
                        title: 'Programa de Referidos Mejorado',
                        description: 'Implementar un sistema de referidos con incentivos para empleados que generen contrataciones exitosas.',
                        impact: 'Medio',
                        effort: 'Bajo'
                      },
                      {
                        title: 'Estrategia de Employer Branding',
                        description: 'Desarrollar una estrategia integral de marca empleadora para atraer mejor talento pasivo en el mercado.',
                        impact: 'Alto',
                        effort: 'Alto'
                      }
                    ].map((rec, index) => (
                      <div key={index} className="bg-white p-4 rounded-lg border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                        <h4 className="font-semibold text-gray-900">{rec.title}</h4>
                        <p className="text-gray-600 text-sm mt-1">{rec.description}</p>
                        <div className="mt-2 flex space-x-4 text-xs">
                          <span className="inline-flex items-center">
                            <span className="text-gray-500 mr-1">Impacto:</span>
                            <span className="font-medium">{rec.impact}</span>
                          </span>
                          <span className="inline-flex items-center">
                            <span className="text-gray-500 mr-1">Esfuerzo:</span>
                            <span className="font-medium">{rec.effort}</span>
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default ClientUnderstanding;
