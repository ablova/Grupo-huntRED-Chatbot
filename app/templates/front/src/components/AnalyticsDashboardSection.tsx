import React, { useState } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { TrendingUp, Users, Target, Clock, CheckCircle, Eye } from 'lucide-react';

const AnalyticsDashboardSection = () => {
  const [selectedMetric, setSelectedMetric] = useState('hiring');

  const hiringData = [
    { month: 'Ene', huntRED_Executive: 12, huntRED_m: 45, huntU: 78, Amigro: 23 },
    { month: 'Feb', huntRED_Executive: 15, huntRED_m: 52, huntU: 85, Amigro: 28 },
    { month: 'Mar', huntRED_Executive: 18, huntRED_m: 48, huntU: 92, Amigro: 31 },
    { month: 'Abr', huntRED_Executive: 22, huntRED_m: 58, huntU: 88, Amigro: 35 },
    { month: 'May', huntRED_Executive: 19, huntRED_m: 61, huntU: 95, Amigro: 29 },
    { month: 'Jun', huntRED_Executive: 25, huntRED_m: 55, huntU: 102, Amigro: 38 }
  ];

  const performanceData = [
    { name: 'Assessment Score', value: 89, color: '#3b82f6' },
    { name: 'Cultural Fit', value: 92, color: '#8b5cf6' },
    { name: 'Technical Skills', value: 87, color: '#06b6d4' },
    { name: 'Communication', value: 94, color: '#10b981' }
  ];

  const timeToHireData = [
    { week: 'S1', Executive: 28, Middle: 16, Junior: 12, Network: 8 },
    { week: 'S2', Executive: 25, Middle: 16, Junior: 10, Network: 7 },
    { week: 'S3', Executive: 22, Middle: 14, Junior: 9, Network: 6 },
    { week: 'S4', Executive: 20, Middle: 13, Junior: 8, Network: 5 }
  ];

  const conversionData = [
    { stage: 'Sourcing', candidates: 100, percentage: 100 },
    { stage: 'Screening', candidates: 75, percentage: 75 },
    { stage: 'Assessment', candidates: 45, percentage: 45 },
    { stage: 'Entrevistas', candidates: 25, percentage: 25 },
    { stage: 'Oferta', candidates: 8, percentage: 8 },
    { stage: 'Contratado', candidates: 6, percentage: 6 }
  ];

  const metrics = [
    { id: 'hiring', label: 'Contrataciones', icon: Users, data: hiringData },
    { id: 'performance', label: 'Performance', icon: Target, data: performanceData },
    { id: 'time', label: 'Tiempo de Contratación', icon: Clock, data: timeToHireData },
    { id: 'conversion', label: 'Conversión', icon: TrendingUp, data: conversionData }
  ];

  const kpiCards = [
    { title: 'Total Candidatos', value: '2,847', change: '+12%', color: 'from-blue-500 to-blue-600', icon: Users },
    { title: 'Tasa de Éxito', value: '89.2%', change: '+5.3%', color: 'from-green-500 to-green-600', icon: CheckCircle },
    { title: 'Tiempo Promedio', value: '18 días', change: '-2.1%', color: 'from-purple-500 to-purple-600', icon: Clock },
    { title: 'Satisfacción Cliente', value: '4.8/5', change: '+0.3%', color: 'from-orange-500 to-red-500', icon: Target }
  ];

  const COLORS = ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981'];

  const renderChart = () => {
    switch (selectedMetric) {
      case 'hiring':
        return (
          <AreaChart data={hiringData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Area type="monotone" dataKey="huntRED_Executive" stackId="1" stroke="#1e293b" fill="#1e293b" />
            <Area type="monotone" dataKey="huntRED_m" stackId="1" stroke="#3b82f6" fill="#3b82f6" />
            <Area type="monotone" dataKey="huntU" stackId="1" stroke="#10b981" fill="#10b981" />
            <Area type="monotone" dataKey="Amigro" stackId="1" stroke="#f59e0b" fill="#f59e0b" />
          </AreaChart>
        );
      case 'time':
        return (
          <LineChart data={timeToHireData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="week" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="Executive" stroke="#1e293b" strokeWidth={3} />
            <Line type="monotone" dataKey="Middle" stroke="#3b82f6" strokeWidth={3} />
            <Line type="monotone" dataKey="Junior" stroke="#10b981" strokeWidth={3} />
            <Line type="monotone" dataKey="Network" stroke="#f59e0b" strokeWidth={3} />
          </LineChart>
        );
      case 'conversion':
        return (
          <BarChart data={conversionData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="stage" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="candidates" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        );
      case 'performance':
        return (
          <PieChart>
            <Pie
              data={performanceData}
              cx="50%"
              cy="50%"
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
              label={({ name, value }) => `${name}: ${value}%`}
            >
              {performanceData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        );
      default:
        return null;
    }
  };

  return (
    <section id="analytics" className="py-20 bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-700">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-800 bg-clip-text text-transparent">
            Analytics Dashboard
          </h2>
          <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
            Insights en tiempo real para optimizar tu proceso de selección
          </p>
        </div>

        {/* KPI Cards */}
        <div className="grid md:grid-cols-4 gap-6 mb-12">
          {kpiCards.map((kpi, index) => {
            const KpiIcon = kpi.icon;
            return (
              <div key={index} className="glass p-6 rounded-xl hover:scale-105 transition-all duration-300 animate-fade-in-up" style={{ animationDelay: `${index * 0.1}s` }}>
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-12 h-12 bg-gradient-to-r ${kpi.color} rounded-lg flex items-center justify-center`}>
                    <KpiIcon className="w-6 h-6 text-white" />
                  </div>
                  <span className={`text-sm font-semibold px-2 py-1 rounded-full ${
                    kpi.change.startsWith('+') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {kpi.change}
                  </span>
                </div>
                <h3 className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">{kpi.title}</h3>
                <p className="text-2xl font-bold text-slate-800 dark:text-slate-200">{kpi.value}</p>
              </div>
            );
          })}
        </div>

        {/* Metric Selector */}
        <div className="mb-8 flex justify-center">
          <div className="glass p-2 rounded-xl">
            <div className="flex space-x-2">
              {metrics.map((metric) => {
                const MetricIcon = metric.icon;
                return (
                  <button
                    key={metric.id}
                    onClick={() => setSelectedMetric(metric.id)}
                    className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                      selectedMetric === metric.id
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                        : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                    }`}
                  >
                    <MetricIcon className="w-4 h-4" />
                    <span>{metric.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Main Chart */}
          <div className="lg:col-span-2 glass p-8 rounded-xl">
            <h3 className="text-xl font-semibold mb-6 text-center">
              {metrics.find(m => m.id === selectedMetric)?.label} por Unidad de Negocio
            </h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                {renderChart()}
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Real-time indicators */}
        <div className="mt-12 grid md:grid-cols-3 gap-6">
          <div className="glass p-6 rounded-xl text-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mx-auto mb-3 animate-pulse"></div>
            <h4 className="font-semibold mb-2">Sistema Activo</h4>
            <p className="text-sm text-slate-600 dark:text-slate-400">Procesando en tiempo real</p>
          </div>
          
          <div className="glass p-6 rounded-xl text-center">
            <div className="flex items-center justify-center mb-3">
              <Eye className="w-5 h-5 text-blue-500 mr-2" />
              <span className="text-xl font-bold text-blue-600">247</span>
            </div>
            <h4 className="font-semibold mb-2">Candidatos Activos</h4>
            <p className="text-sm text-slate-600 dark:text-slate-400">En proceso ahora</p>
          </div>

          <div className="glass p-6 rounded-xl text-center">
            <div className="flex items-center justify-center mb-3">
              <TrendingUp className="w-5 h-5 text-green-500 mr-2" />
              <span className="text-xl font-bold text-green-600">+15%</span>
            </div>
            <h4 className="font-semibold mb-2">Crecimiento Mensual</h4>
            <p className="text-sm text-slate-600 dark:text-slate-400">Comparado al mes anterior</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AnalyticsDashboardSection;
