import React, { useState } from 'react';
import { Calculator, BarChart2, TrendingUp, DollarSign, Zap, ArrowRight, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

const CalculadoraPage: React.FC = () => {
  const [employees, setEmployees] = useState(50);
  const [turnoverRate, setTurnoverRate] = useState(15);
  const [hiringCost, setHiringCost] = useState(25000);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activeTab, setActiveTab] = useState('roi');

  // Calculate annual turnover cost
  const calculateTurnoverCost = () => {
    const turnoverCount = Math.round(employees * (turnoverRate / 100));
    return {
      count: turnoverCount,
      cost: turnoverCount * hiringCost
    };
  };

  // Calculate potential savings
  const calculateSavings = () => {
    const { count, cost } = calculateTurnoverCost();
    // Assuming our solution can reduce turnover by 30%
    const reduction = 0.3;
    return {
      employeesRetained: Math.round(count * reduction),
      costSaved: Math.round(cost * reduction),
      newTurnoverRate: Math.round(turnoverRate * (1 - reduction) * 10) / 10
    };
  };

  const { count: annualTurnover, cost: annualCost } = calculateTurnoverCost();
  const { employeesRetained, costSaved, newTurnoverRate } = calculateSavings();

  const tabs = [
    { id: 'roi', label: 'ROI', icon: <TrendingUp className="w-4 h-4 mr-2" /> },
    { id: 'costs', label: 'Costos', icon: <DollarSign className="w-4 h-4 mr-2" /> },
    { id: 'efficiency', label: 'Eficiencia', icon: <Zap className="w-4 h-4 mr-2" /> }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-700 text-sm font-medium mb-6">
            <Calculator className="w-4 h-4 mr-2" />
            Herramientas de Análisis
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Calculadora de <span className="bg-gradient-to-r from-tech-blue to-tech-purple bg-clip-text text-transparent">ROI</span>
          </h1>
          
          <p className="text-xl text-gray-700 max-w-3xl mx-auto">
            Descubre cuánto podrías ahorrar optimizando tus procesos de reclutamiento y retención de talento con nuestras soluciones.
          </p>
        </div>

        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-8 mb-16">
          {/* Calculator Card */}
          <div className="md:col-span-2">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="text-2xl">Calculadora de Ahorros</CardTitle>
                <CardDescription>
                  Ajusta los parámetros según tu organización para ver el impacto potencial.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-8">
                  <div>
                    <div className="flex justify-between mb-2">
                      <Label htmlFor="employees">Número de empleados</Label>
                      <span className="font-medium">{employees}</span>
                    </div>
                    <Slider
                      id="employees"
                      min={10}
                      max={1000}
                      step={10}
                      value={[employees]}
                      onValueChange={([value]) => setEmployees(value)}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-500 mt-1">
                      <span>10</span>
                      <span>1000+</span>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-2">
                      <Label htmlFor="turnover">Tasa de rotación anual</Label>
                      <span className="font-medium">{turnoverRate}%</span>
                    </div>
                    <Slider
                      id="turnover"
                      min={5}
                      max={50}
                      step={1}
                      value={[turnoverRate]}
                      onValueChange={([value]) => setTurnoverRate(value)}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-500 mt-1">
                      <span>5%</span>
                      <span>50%</span>
                    </div>
                  </div>

                  {showAdvanced && (
                    <div>
                      <div className="flex justify-between mb-2">
                        <Label htmlFor="hiring-cost">Costo promedio por contratación (USD)</Label>
                        <span className="font-medium">${hiringCost.toLocaleString()}</span>
                      </div>
                      <Slider
                        id="hiring-cost"
                        min={5000}
                        max={100000}
                        step={1000}
                        value={[hiringCost]}
                        onValueChange={([value]) => setHiringCost(value)}
                        className="w-full"
                      />
                      <div className="flex justify-between text-sm text-gray-500 mt-1">
                        <span>$5K</span>
                        <span>$100K+</span>
                      </div>
                    </div>
                  )}

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="advanced-options"
                      checked={showAdvanced}
                      onCheckedChange={setShowAdvanced}
                    />
                    <Label htmlFor="advanced-options">Mostrar opciones avanzadas</Label>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Results Card */}
          <div>
            <Card className="bg-gradient-to-br from-tech-blue to-tech-purple text-white border-0 h-full">
              <CardHeader>
                <CardTitle className="text-2xl">Tus Resultados</CardTitle>
                <CardDescription className="text-blue-100">
                  Potencial de ahorro anual
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div>
                    <div className="text-sm text-blue-200 mb-1">Rotación actual</div>
                    <div className="text-3xl font-bold">{annualTurnover} empleados</div>
                    <div className="text-blue-200">${annualCost.toLocaleString()} en costos</div>
                  </div>

                  <div className="h-px bg-blue-400/30 my-4"></div>

                  <div>
                    <div className="text-sm text-blue-200 mb-1">Con nuestra solución</div>
                    <div className="text-3xl font-bold">{employeesRetained} empleados retenidos</div>
                    <div className="text-blue-200">Hasta ${costSaved.toLocaleString()} en ahorros</div>
                  </div>

                  <div className="mt-8">
                    <div className="flex items-center text-sm text-blue-200 mb-2">
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Nueva tasa de rotación: {newTurnoverRate}%
                    </div>
                    <Button className="w-full bg-white text-tech-blue hover:bg-gray-100 mt-4">
                      Solicitar Demostración
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Additional Tools */}
        <div className="max-w-5xl mx-auto mb-20">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">Más Herramientas</h2>
          
          <div className="grid md:grid-cols-3 gap-6">
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center text-tech-blue mb-4">
                  <BarChart2 className="w-6 h-6" />
                </div>
                <CardTitle>Benchmarking</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-gray-700">
                  Compara tus métricas con los estándares de la industria y descubre áreas de mejora.
                </CardDescription>
                <Button variant="link" className="p-0 mt-4 text-tech-blue">
                  Explorar
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center text-tech-purple mb-4">
                  <Zap className="w-6 h-6" />
                </div>
                <CardTitle>Simulador de Eficiencia</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-gray-700">
                  Calcula cuánto tiempo podrías ahorrar automatizando tus procesos de reclutamiento.
                </CardDescription>
                <Button variant="link" className="p-0 mt-4 text-tech-purple">
                  Probar Ahora
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="w-12 h-12 rounded-xl bg-cyan-100 flex items-center justify-center text-tech-cyan mb-4">
                  <DollarSign className="w-6 h-6" />
                </div>
                <CardTitle>Calculadora de Costos</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-gray-700">
                  Compara los costos de diferentes estrategias de adquisición de talento.
                </CardDescription>
                <Button variant="link" className="p-0 mt-4 text-tech-cyan">
                  Calcular
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-gradient-to-r from-tech-purple to-tech-blue rounded-2xl p-8 text-white text-center">
          <h2 className="text-3xl font-bold mb-4">¿Listo para optimizar tu estrategia de talento?</h2>
          <p className="text-xl mb-8 max-w-2xl mx-auto">
            Agenda una consulta personalizada con nuestros expertos para un análisis detallado de tus necesidades.
          </p>
          <Button className="bg-white text-tech-blue hover:bg-gray-100 px-8 py-3 text-lg font-semibold">
            Hablar con un Experto
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CalculadoraPage;
