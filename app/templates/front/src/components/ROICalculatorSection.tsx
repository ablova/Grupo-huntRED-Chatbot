
import React, { useState, useEffect } from 'react';
import { Calculator, TrendingUp, DollarSign, Clock, Users, Target } from 'lucide-react';

const ROICalculatorSection = () => {
  const [inputs, setInputs] = useState({
    currentHires: 50,
    averageSalary: 80000,
    timeToHire: 45,
    recruitmentCost: 5000,
    turnoverRate: 15,
    hrTeamSize: 3
  });

  const [results, setResults] = useState({
    timeReduction: 0,
    costSavings: 0,
    qualityImprovement: 0,
    roiPercentage: 0,
    monthlyBenefit: 0,
    annualBenefit: 0
  });

  const [animationKey, setAnimationKey] = useState(0);

  useEffect(() => {
    calculateROI();
    setAnimationKey(prev => prev + 1);
  }, [inputs]);

  const calculateROI = () => {
    // Cálculos basados en métricas reales de IA en reclutamiento
    const timeReduction = Math.round(inputs.timeToHire * 0.6); // 60% reducción en tiempo
    const costPerHire = inputs.recruitmentCost;
    const annualRecruitmentCost = inputs.currentHires * costPerHire;
    
    // Ahorro por reducción de tiempo
    const hrHourlyCost = 35; // USD por hora de RRHH
    const hoursPerHiring = inputs.timeToHire * 2; // 2 horas por día de proceso
    const timeBasedSavings = inputs.currentHires * (timeReduction * 2 * hrHourlyCost);
    
    // Ahorro por mejor calidad (reducción de turnover)
    const turnoverCost = inputs.averageSalary * 0.2; // 20% del salario anual
    const currentTurnoverCost = (inputs.currentHires * inputs.turnoverRate / 100) * turnoverCost;
    const improvedTurnoverRate = inputs.turnoverRate * 0.4; // 60% mejora en retención
    const newTurnoverCost = (inputs.currentHires * improvedTurnoverRate / 100) * turnoverCost;
    const qualitySavings = currentTurnoverCost - newTurnoverCost;
    
    // Ahorro en costos de reclutamiento (automatización)
    const automationSavings = annualRecruitmentCost * 0.4; // 40% reducción en costos
    
    const totalAnnualSavings = timeBasedSavings + qualitySavings + automationSavings;
    const huntredInvestment = 24000; // Costo anual promedio de la plataforma
    const netBenefit = totalAnnualSavings - huntredInvestment;
    const roiPercentage = (netBenefit / huntredInvestment) * 100;

    setResults({
      timeReduction,
      costSavings: Math.round(totalAnnualSavings),
      qualityImprovement: Math.round(((inputs.turnoverRate - improvedTurnoverRate) / inputs.turnoverRate) * 100),
      roiPercentage: Math.round(roiPercentage),
      monthlyBenefit: Math.round(netBenefit / 12),
      annualBenefit: Math.round(netBenefit)
    });
  };

  const handleInputChange = (field: string, value: number) => {
    setInputs(prev => ({ ...prev, [field]: value }));
  };

  const inputFields = [
    { key: 'currentHires', label: 'Contrataciones Anuales', icon: Users, unit: 'personas', min: 1, max: 500 },
    { key: 'averageSalary', label: 'Salario Promedio', icon: DollarSign, unit: 'USD', min: 30000, max: 200000 },
    { key: 'timeToHire', label: 'Tiempo de Contratación', icon: Clock, unit: 'días', min: 10, max: 120 },
    { key: 'recruitmentCost', label: 'Costo por Contratación', icon: Calculator, unit: 'USD', min: 1000, max: 20000 },
    { key: 'turnoverRate', label: 'Tasa de Rotación', icon: TrendingUp, unit: '%', min: 5, max: 50 },
    { key: 'hrTeamSize', label: 'Equipo de RRHH', icon: Target, unit: 'personas', min: 1, max: 20 }
  ];

  const resultCards = [
    {
      title: 'Reducción de Tiempo',
      value: results.timeReduction,
      unit: 'días',
      color: 'from-blue-500 to-blue-600',
      icon: Clock,
      description: 'Menos tiempo por contratación'
    },
    {
      title: 'Ahorro Anual',
      value: results.costSavings.toLocaleString(),
      unit: 'USD',
      color: 'from-green-500 to-green-600',
      icon: DollarSign,
      description: 'Reducción de costos totales'
    },
    {
      title: 'Mejora de Calidad',
      value: results.qualityImprovement,
      unit: '%',
      color: 'from-purple-500 to-purple-600',
      icon: Target,
      description: 'Reducción en rotación'
    },
    {
      title: 'ROI',
      value: results.roiPercentage,
      unit: '%',
      color: 'from-orange-500 to-red-500',
      icon: TrendingUp,
      description: 'Retorno de inversión anual'
    }
  ];

  return (
    <section className="py-20 bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 dark:from-emerald-900/20 dark:via-teal-900/20 dark:to-cyan-900/20">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
            Calculadora de ROI
          </h2>
          <p className="text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto">
            Descubre el impacto financiero de implementar huntRED® AI en tu organización
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12">
          {/* Input Section */}
          <div className="space-y-6">
            <h3 className="text-2xl font-bold mb-6 flex items-center">
              <Calculator className="w-7 h-7 mr-3 text-emerald-600" />
              Configuración Actual
            </h3>
            
            {inputFields.map((field) => {
              const FieldIcon = field.icon;
              return (
                <div key={field.key} className="glass p-6 rounded-xl hover:scale-105 transition-all duration-300">
                  <div className="flex items-center mb-3">
                    <FieldIcon className="w-5 h-5 mr-3 text-emerald-600" />
                    <label className="font-semibold text-slate-700 dark:text-slate-300">
                      {field.label}
                    </label>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <input
                      type="range"
                      min={field.min}
                      max={field.max}
                      value={inputs[field.key as keyof typeof inputs]}
                      onChange={(e) => handleInputChange(field.key, parseInt(e.target.value))}
                      className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="bg-emerald-100 dark:bg-emerald-900/30 px-3 py-2 rounded-lg min-w-[100px] text-center">
                      <span className="font-bold text-emerald-700 dark:text-emerald-400">
                        {inputs[field.key as keyof typeof inputs].toLocaleString()} {field.unit}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Results Section */}
          <div className="space-y-6">
            <h3 className="text-2xl font-bold mb-6 flex items-center">
              <TrendingUp className="w-7 h-7 mr-3 text-emerald-600" />
              Beneficios Proyectados
            </h3>

            <div className="grid grid-cols-2 gap-4 mb-8">
              {resultCards.map((card, index) => {
                const CardIcon = card.icon;
                return (
                  <div
                    key={`${card.title}-${animationKey}`}
                    className="glass p-6 rounded-xl text-center hover:scale-105 transition-all duration-300 animate-fade-in-up"
                    style={{ animationDelay: `${index * 0.1}s` }}
                  >
                    <div className={`w-12 h-12 mx-auto mb-3 bg-gradient-to-r ${card.color} rounded-full flex items-center justify-center`}>
                      <CardIcon className="w-6 h-6 text-white" />
                    </div>
                    <h4 className="font-semibold mb-2 text-sm">{card.title}</h4>
                    <p className="text-2xl font-bold mb-1">
                      {card.value} <span className="text-sm font-normal">{card.unit}</span>
                    </p>
                    <p className="text-xs text-slate-600 dark:text-slate-400">{card.description}</p>
                  </div>
                );
              })}
            </div>

            {/* Financial Summary */}
            <div className="glass p-8 rounded-xl">
              <h4 className="text-xl font-bold mb-6 text-center">Resumen Financiero</h4>
              
              <div className="space-y-4">
                <div className="flex justify-between items-center p-4 bg-white dark:bg-slate-800 rounded-lg">
                  <span className="font-semibold">Beneficio Mensual:</span>
                  <span className="text-xl font-bold text-green-600">
                    ${results.monthlyBenefit.toLocaleString()}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-4 bg-white dark:bg-slate-800 rounded-lg">
                  <span className="font-semibold">Beneficio Anual:</span>
                  <span className="text-2xl font-bold text-green-600">
                    ${results.annualBenefit.toLocaleString()}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-4 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-lg">
                  <span className="font-semibold">ROI Total:</span>
                  <span className="text-2xl font-bold">
                    {results.roiPercentage}%
                  </span>
                </div>
              </div>

              <div className="mt-6 p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
                <p className="text-sm text-emerald-700 dark:text-emerald-400 text-center">
                  <strong>Tiempo de recuperación:</strong> {Math.ceil(24000 / (results.annualBenefit / 12))} meses
                </p>
              </div>
            </div>

            {/* CTA */}
            <div className="text-center">
              <button className="bg-gradient-to-r from-emerald-500 to-teal-600 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:scale-105 transition-all duration-300 shadow-lg">
                Solicitar Análisis Detallado
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ROICalculatorSection;
