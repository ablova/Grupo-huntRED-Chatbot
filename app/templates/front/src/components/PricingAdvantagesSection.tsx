import React, { useState, useEffect } from 'react';
import { 
  DollarSign, 
  TrendingUp, 
  Shield, 
  Zap, 
  CheckCircle,
  Star,
  Target,
  Users,
  Clock,
  Award,
  Calculator,
  BarChart3,
  Settings,
  Info
} from 'lucide-react';

interface PricingCardProps {
  plan: string;
  price: string;
  originalPrice?: string;
  features: string[];
  color: string;
  isPopular?: boolean;
  savings?: string;
}

const PricingCard: React.FC<PricingCardProps> = ({ 
  plan, 
  price, 
  originalPrice,
  features, 
  color, 
  isPopular = false,
  savings
}) => (
  <div className={`relative overflow-hidden rounded-2xl p-8 shadow-xl border-2 ${isPopular ? 'border-red-500' : 'border-gray-200'} hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 bg-gradient-to-br ${color}`}>
    {isPopular && (
      <div className="absolute top-0 right-0 bg-red-500 text-white px-4 py-2 text-sm font-bold transform rotate-45 translate-x-8 -translate-y-2">
        MEJOR VALOR
      </div>
    )}
    
    <div className="text-center mb-8">
      <h3 className="text-2xl font-bold text-white mb-2">{plan}</h3>
      <div className="flex items-center justify-center mb-2">
        <span className="text-4xl font-bold text-white">{price}</span>
        {originalPrice && (
          <span className="text-white/60 line-through ml-2">{originalPrice}</span>
        )}
      </div>
      {savings && (
        <div className="text-green-300 text-sm font-semibold">
          Ahorro: {savings}
        </div>
      )}
    </div>
    
    <div className="space-y-4">
      {features.map((feature, index) => (
        <div key={index} className="flex items-center text-white/90">
          <CheckCircle className="w-5 h-5 mr-3 text-green-300 flex-shrink-0" />
          <span className="text-sm">{feature}</span>
        </div>
      ))}
    </div>
  </div>
);

const PricingAdvantagesSection: React.FC = () => {
  const [calculatorInputs, setCalculatorInputs] = useState({
    serviceType: 'executive',
    salary: 800000,
    positionCount: 1,
    companySize: 'medium'
  });

  const [comparisonResults, setComparisonResults] = useState({
    huntred: {
      ai: 95000,
      hybrid: 0,
      human: 0,
      total: 95000
    },
    smartrecruiters: 0,
    bullhorn: 0,
    mya: 0,
    savings: 0
  });

  // Configuración de precios por servicio
  const serviceConfig = {
    executive: {
      name: "huntRED Executive",
      ai: 95000,
      hybridRate: 0.14,
      humanRate: 0.20,
      hybridRateMulti: 0.13,
      humanRateMulti: 0.18,
      features: [
        "GenIA™ + AURA™ completos",
        "TruthSense™ + SocialLink™",
        "OffLimits™ protección",
        "Firma electrónica integrada",
        "Soporte prioritario 24/7"
      ]
    },
    standard: {
      name: "huntRED Standard", 
      ai: 95000,
      hybridRate: 0.14,
      humanRate: 0.20,
      hybridRateMulti: 0.13,
      humanRateMulti: 0.18,
      features: [
        "GenIA™ completo",
        "TruthSense™ básico",
        "Protección OffLimits™",
        "Soporte prioritario"
      ]
    },
    huntu: {
      name: "huntU",
      ai: 55000,
      hybridRate: 0.12,
      humanRate: 0.16,
      hybridRateMulti: 0.11,
      humanRateMulti: 0.15,
      features: [
        "Talento universitario",
        "Programas de graduados",
        "Pipeline de talento",
        "Desarrollo de carrera"
      ]
    },
    amigro: {
      name: "amigro",
      ai: 20000,
      hybridRate: 0.10,
      humanRate: 0.14,
      hybridRateMulti: 0.09,
      humanRateMulti: 0.13,
      features: [
        "Reclutamiento masivo",
        "Posiciones operativas",
        "Colocación rápida",
        "Optimización de procesos"
      ]
    }
  };

  // Calcular precios de competencia
  const calculateCompetitorPrices = (salary: number, positionCount: number) => {
    const annualSalary = salary * 12;
    
    // SmartRecruiters: $199/empleado/mes * 12 meses
    const smartrecruiters = 199 * 12 * positionCount;
    
    // Bullhorn: $199/empleado/mes * 12 meses + setup
    const bullhorn = (199 * 12 * positionCount) + (5000 * positionCount);
    
    // Mya: $100,000/año base + $10,000 por posición adicional
    const mya = 100000 + (positionCount - 1) * 10000;
    
    return { smartrecruiters, bullhorn, mya };
  };

  // Calcular precios huntRED
  const calculateHuntREDPrices = (serviceType: string, salary: number, positionCount: number) => {
    const config = serviceConfig[serviceType as keyof typeof serviceConfig];
    const annualSalary = salary * 12;
    
    // Precio AI fijo
    const ai = config.ai;
    
    // Precios híbrido y humano con descuento por volumen
    const hybridRate = positionCount >= 2 ? config.hybridRateMulti : config.hybridRate;
    const humanRate = positionCount >= 2 ? config.humanRateMulti : config.humanRate;
    
    const hybrid = annualSalary * hybridRate;
    const human = annualSalary * humanRate;
    
    return { ai, hybrid, human, total: ai + hybrid + human };
  };

  useEffect(() => {
    const huntred = calculateHuntREDPrices(
      calculatorInputs.serviceType,
      calculatorInputs.salary,
      calculatorInputs.positionCount
    );
    
    const competitors = calculateCompetitorPrices(
      calculatorInputs.salary,
      calculatorInputs.positionCount
    );
    
    const maxCompetitorPrice = Math.max(competitors.smartrecruiters, competitors.bullhorn, competitors.mya);
    const savings = maxCompetitorPrice - huntred.total;
    
    setComparisonResults({
      huntred,
      ...competitors,
      savings: Math.max(0, savings)
    });
  }, [calculatorInputs]);

  const handleInputChange = (field: string, value: string | number) => {
    setCalculatorInputs(prev => ({
      ...prev,
      [field]: typeof value === 'string' ? value : Math.max(0, value)
    }));
  };

  const renderStars = (score: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`w-4 h-4 ${i < score ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
      />
    ));
  };

  const currentService = serviceConfig[calculatorInputs.serviceType as keyof typeof serviceConfig];

  return (
    <section className="py-20 bg-gradient-to-br from-gray-50 to-white">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Comparativa de
            <span className="text-red-600"> Precios Dinámica</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Compare precios reales basados en su servicio específico y salario. 
            Nuestro modelo transparente le permite ver exactamente cuánto puede ahorrar.
          </p>
        </div>

        {/* Calculadora Dinámica */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 md:p-12 mb-16">
          <div className="text-center mb-8">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Calculadora de Precios
            </h3>
            <p className="text-gray-600">
              Configure su servicio y vea la comparativa en tiempo real
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Tipo de Servicio */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo de Servicio
              </label>
              <select
                value={calculatorInputs.serviceType}
                onChange={(e) => handleInputChange('serviceType', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              >
                <option value="executive">huntRED Executive</option>
                <option value="standard">huntRED Standard</option>
                <option value="huntu">huntU</option>
                <option value="amigro">amigro</option>
              </select>
            </div>

            {/* Salario Mensual */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Salario Mensual (MXN)
              </label>
              <input
                type="number"
                value={calculatorInputs.salary}
                onChange={(e) => handleInputChange('salary', parseInt(e.target.value) || 0)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder="800,000"
              />
            </div>

            {/* Número de Posiciones */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Número de Posiciones
              </label>
              <input
                type="number"
                value={calculatorInputs.positionCount}
                onChange={(e) => handleInputChange('positionCount', parseInt(e.target.value) || 1)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                min="1"
                max="10"
              />
            </div>

            {/* Tamaño de Empresa */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tamaño de Empresa
              </label>
              <select
                value={calculatorInputs.companySize}
                onChange={(e) => handleInputChange('companySize', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              >
                <option value="small">Pequeña (1-50)</option>
                <option value="medium">Mediana (51-200)</option>
                <option value="large">Grande (201-1000)</option>
                <option value="enterprise">Enterprise (1000+)</option>
              </select>
            </div>
          </div>

          {/* Resultados de Comparación */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="text-center p-6 bg-red-50 rounded-xl border-2 border-red-200">
              <h4 className="text-lg font-bold text-red-600 mb-2">{currentService.name}</h4>
              <div className="text-3xl font-bold text-red-600 mb-2">
                ${comparisonResults.huntred.total.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">
                <div>AI: ${comparisonResults.huntred.ai.toLocaleString()}</div>
                <div>Híbrido: ${comparisonResults.huntred.hybrid.toLocaleString()}</div>
                <div>Humano: ${comparisonResults.huntred.human.toLocaleString()}</div>
              </div>
            </div>

            <div className="text-center p-6 bg-gray-50 rounded-xl">
              <h4 className="text-lg font-bold text-gray-600 mb-2">SmartRecruiters</h4>
              <div className="text-3xl font-bold text-gray-600 mb-2">
                ${comparisonResults.smartrecruiters.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500">Precio fijo mensual</div>
            </div>

            <div className="text-center p-6 bg-gray-50 rounded-xl">
              <h4 className="text-lg font-bold text-gray-600 mb-2">Bullhorn</h4>
              <div className="text-3xl font-bold text-gray-600 mb-2">
                ${comparisonResults.bullhorn.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500">Precio fijo + setup</div>
            </div>

            <div className="text-center p-6 bg-gray-50 rounded-xl">
              <h4 className="text-lg font-bold text-gray-600 mb-2">Mya</h4>
              <div className="text-3xl font-bold text-gray-600 mb-2">
                ${comparisonResults.mya.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500">Precio anual base</div>
            </div>
          </div>

          {/* Ahorro */}
          {comparisonResults.savings > 0 && (
            <div className="text-center p-6 bg-green-50 rounded-xl border-2 border-green-200">
              <h4 className="text-2xl font-bold text-green-600 mb-2">
                ¡Ahorro con huntRED!
              </h4>
              <div className="text-4xl font-bold text-green-600">
                ${comparisonResults.savings.toLocaleString()}
              </div>
              <p className="text-green-700 mt-2">
                vs la opción más cara de la competencia
              </p>
            </div>
          )}
        </div>

        {/* Características del Servicio Seleccionado */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 md:p-12 mb-16">
          <div className="text-center mb-8">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Características de {currentService.name}
            </h3>
            <p className="text-gray-600">
              Todo incluido en el precio calculado
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {currentService.features.map((feature, index) => (
              <div key={index} className="flex items-center p-4 bg-gray-50 rounded-lg">
                <CheckCircle className="w-6 h-6 text-green-500 mr-3 flex-shrink-0" />
                <span className="text-gray-700">{feature}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Comparativa de Valor */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 md:p-12 mb-16">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              Valor vs. Competencia
            </h3>
            <p className="text-gray-600 text-lg">
              Nuestras tecnologías únicas incluidas sin costo adicional
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="text-left py-4 px-6 font-bold text-gray-900">Característica</th>
                  <th className="text-center py-4 px-6 font-bold text-red-600">huntRED</th>
                  <th className="text-center py-4 px-6 font-bold text-gray-600">SmartRecruiters</th>
                  <th className="text-center py-4 px-6 font-bold text-gray-600">Bullhorn</th>
                  <th className="text-center py-4 px-6 font-bold text-gray-600">Mya</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-100">
                  <td className="py-4 px-6 font-medium text-gray-900">IA Conversacional</td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(5)}</div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(2)}</div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(1)}</div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(3)}</div>
                  </td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-4 px-6 font-medium text-gray-900">Verificación Automática</td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(5)}</div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(1)}</div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(1)}</div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(2)}</div>
                  </td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-4 px-6 font-medium text-gray-900">Protección OffLimits</td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(5)}</div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(0)}</div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(0)}</div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(0)}</div>
                  </td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-4 px-6 font-medium text-gray-900">Firma Electrónica</td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(5)}</div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(2)}</div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(2)}</div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <div className="flex justify-center">{renderStars(0)}</div>
                  </td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-4 px-6 font-medium text-gray-900">ROI Promedio</td>
                  <td className="py-4 px-6 text-center text-red-600 font-bold">450%</td>
                  <td className="py-4 px-6 text-center text-gray-600">120%</td>
                  <td className="py-4 px-6 text-center text-gray-600">150%</td>
                  <td className="py-4 px-6 text-center text-gray-600">200%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 mb-16">
          <div className="flex items-start">
            <Info className="w-6 h-6 text-yellow-600 mr-3 mt-1 flex-shrink-0" />
            <div>
              <h4 className="text-lg font-bold text-yellow-800 mb-2">Información Importante</h4>
              <p className="text-yellow-700 mb-2">
                <strong>Precios de competencia:</strong> Los precios mostrados son estimaciones basadas en información pública disponible. 
                Los precios reales pueden variar según el contrato específico, volumen y características adicionales. 
                <span className="font-semibold">Estos precios NO incluyen costos de implementación, capacitación, integraciones adicionales o servicios premium.</span>
              </p>
              <p className="text-yellow-700">
                <strong>Precios huntRED:</strong> Nuestros precios son transparentes y se calculan en tiempo real según su configuración específica. 
                Todos los precios incluyen IVA, implementación, capacitación y soporte completo. 
                <span className="font-semibold">No hay costos ocultos ni cargos adicionales.</span>
              </p>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center">
          <div className="bg-gradient-to-r from-red-600 to-red-700 rounded-2xl p-8 md:p-12 text-white">
            <h3 className="text-3xl font-bold mb-4">
              ¿Listo para obtener la mejor relación precio-valor?
            </h3>
            <p className="text-xl mb-8 text-red-100">
              Nuestros precios transparentes y tecnologías únicas le dan la ventaja competitiva
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-white text-red-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
                Solicitar Propuesta Personalizada
              </button>
              <button className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-red-600 transition-colors">
                Agendar Demo
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PricingAdvantagesSection; 