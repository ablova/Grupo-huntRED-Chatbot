import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Calculator, 
  TrendingUp, 
  DollarSign, 
  Clock, 
  Users, 
  Target,
  Award,
  CheckCircle,
  ArrowRight,
  Zap,
  BarChart3,
  PieChart
} from 'lucide-react';

interface ROICalculation {
  annualSalary: number;
  positions: number;
  companySize: string;
  currentCost: number;
  huntredCost: number;
  annualSavings: number;
  roiPercentage: number;
  paybackMonths: number;
}

const ROIDemonstrationSection: React.FC = () => {
  const [calculation, setCalculation] = useState<ROICalculation>({
    annualSalary: 800000,
    positions: 1,
    companySize: 'medium',
    currentCost: 0,
    huntredCost: 0,
    annualSavings: 0,
    roiPercentage: 0,
    paybackMonths: 0
  });

  const [isCalculating, setIsCalculating] = useState(false);

  const companySizes = [
    { value: 'small', label: 'Pequeña (1-50)', multiplier: 1.0 },
    { value: 'medium', label: 'Mediana (51-200)', multiplier: 1.2 },
    { value: 'large', label: 'Grande (201-1000)', multiplier: 1.5 },
    { value: 'enterprise', label: 'Enterprise (1000+)', multiplier: 2.0 }
  ];

  const competitorCosts = {
    smartrecruiters: 28656, // USD anual
    bullhorn: 88656, // USD anual
    mya: 100000, // USD anual
    workday: 50000, // USD anual
    phenom: 75000 // USD anual
  };

  const calculateROI = () => {
    setIsCalculating(true);
    
    setTimeout(() => {
      const usdToMxn = 17.5;
      const selectedSize = companySizes.find(size => size.value === calculation.companySize);
      const multiplier = selectedSize?.multiplier || 1.0;
      
      // huntRED® pricing
      const huntredAI = 95000; // Solo IA
      const huntredHybrid = calculation.annualSalary * 0.15 * multiplier; // 15% del salario
      const huntredHuman = calculation.annualSalary * 0.20 * multiplier; // 20% del salario
      
      // Usar el precio más bajo de huntRED® (Solo IA)
      const huntredCost = huntredAI * calculation.positions;
      
      // Costo promedio de competencia (convertido a MXN)
      const avgCompetitorCost = Object.values(competitorCosts).reduce((sum, cost) => sum + cost, 0) / Object.keys(competitorCosts).length;
      const currentCost = avgCompetitorCost * usdToMxn * calculation.positions;
      
      const annualSavings = currentCost - huntredCost;
      const roiPercentage = (annualSavings / huntredCost) * 100;
      const paybackMonths = (huntredCost / annualSavings) * 12;
      
      setCalculation(prev => ({
        ...prev,
        currentCost: Math.round(currentCost),
        huntredCost: Math.round(huntredCost),
        annualSavings: Math.round(annualSavings),
        roiPercentage: Math.round(roiPercentage),
        paybackMonths: Math.round(paybackMonths)
      }));
      
      setIsCalculating(false);
    }, 1000);
  };

  useEffect(() => {
    calculateROI();
  }, [calculation.annualSalary, calculation.positions, calculation.companySize]);

  const savingsBreakdown = [
    {
      title: "Ahorro vs SmartRecruiters",
      amount: Math.round((competitorCosts.smartrecruiters * 17.5) - calculation.huntredCost),
      icon: <DollarSign className="w-5 h-5" />
    },
    {
      title: "Ahorro vs Bullhorn",
      amount: Math.round((competitorCosts.bullhorn * 17.5) - calculation.huntredCost),
      icon: <TrendingUp className="w-5 h-5" />
    },
    {
      title: "Ahorro vs Mya",
      amount: Math.round((competitorCosts.mya * 17.5) - calculation.huntredCost),
      icon: <Zap className="w-5 h-5" />
    }
  ];

  return (
    <section className="py-24 bg-gradient-to-br from-gray-50 to-white">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-16">
          <Badge variant="secondary" className="mb-4 bg-green-100 text-green-700 hover:bg-green-200">
            <Calculator className="w-4 h-4 mr-2" />
            Calculadora de ROI
          </Badge>
          <h2 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Vea el
            <span className="bg-gradient-to-r from-green-600 to-green-800 bg-clip-text text-transparent">
              {' '}retorno real
            </span>
            {' '}de su inversión
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Calcule cuánto puede ahorrar su empresa con huntRED® vs la competencia. 
            Los números hablan por sí solos.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Calculator */}
          <div className="space-y-6">
            <Card className="border-2 border-green-200">
              <CardHeader>
                <CardTitle className="flex items-center text-green-600">
                  <Calculator className="w-6 h-6 mr-2" />
                  Configurar Cálculo
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <Label htmlFor="salary">Salario Anual del Puesto (MXN)</Label>
                  <Input
                    id="salary"
                    type="number"
                    value={calculation.annualSalary}
                    onChange={(e) => setCalculation(prev => ({ ...prev, annualSalary: Number(e.target.value) }))}
                    className="mt-2"
                    placeholder="800,000"
                  />
                </div>
                
                <div>
                  <Label htmlFor="positions">Número de Posiciones</Label>
                  <Input
                    id="positions"
                    type="number"
                    value={calculation.positions}
                    onChange={(e) => setCalculation(prev => ({ ...prev, positions: Number(e.target.value) }))}
                    className="mt-2"
                    placeholder="1"
                  />
                </div>
                
                <div>
                  <Label htmlFor="company-size">Tamaño de la Empresa</Label>
                  <Select 
                    value={calculation.companySize} 
                    onValueChange={(value) => setCalculation(prev => ({ ...prev, companySize: value }))}
                  >
                    <SelectTrigger className="mt-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {companySizes.map((size) => (
                        <SelectItem key={size.value} value={size.value}>
                          {size.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  onClick={calculateROI}
                  disabled={isCalculating}
                  className="w-full bg-green-600 hover:bg-green-700"
                >
                  {isCalculating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Calculando...
                    </>
                  ) : (
                    <>
                      <Calculator className="w-4 h-4 mr-2" />
                      Calcular ROI
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Savings Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center text-gray-700">
                  <BarChart3 className="w-6 h-6 mr-2" />
                  Desglose de Ahorros
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {savingsBreakdown.map((saving, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center text-green-600">
                          {saving.icon}
                        </div>
                        <span className="font-medium text-gray-700">{saving.title}</span>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-green-600">
                          ${saving.amount.toLocaleString()} MXN
                        </div>
                        <div className="text-sm text-gray-500">por año</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Results */}
          <div className="space-y-6">
            {/* Main ROI Card */}
            <Card className="border-2 border-green-500 bg-gradient-to-br from-green-50 to-white">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl text-green-700">
                  <Award className="w-8 h-8 inline mr-2" />
                  Resultados del ROI
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-4 bg-white rounded-lg border border-green-200">
                    <div className="text-3xl font-bold text-green-600 mb-1">
                      ${calculation.annualSavings.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">Ahorro Anual</div>
                  </div>
                  <div className="text-center p-4 bg-white rounded-lg border border-green-200">
                    <div className="text-3xl font-bold text-green-600 mb-1">
                      {calculation.roiPercentage}%
                    </div>
                    <div className="text-sm text-gray-600">ROI</div>
                  </div>
                </div>
                
                <div className="text-center p-4 bg-green-100 rounded-lg">
                  <div className="text-2xl font-bold text-green-700 mb-1">
                    {calculation.paybackMonths} meses
                  </div>
                  <div className="text-sm text-green-600">Tiempo de Recuperación</div>
                </div>
              </CardContent>
            </Card>

            {/* Cost Comparison */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center text-gray-700">
                  <PieChart className="w-6 h-6 mr-2" />
                  Comparación de Costos
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center text-red-600">
                        <DollarSign className="w-5 h-5" />
                      </div>
                      <span className="font-medium text-gray-700">Costo Promedio Competencia</span>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-red-600">
                        ${calculation.currentCost.toLocaleString()} MXN
                      </div>
                      <div className="text-sm text-gray-500">por año</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center text-green-600">
                        <CheckCircle className="w-5 h-5" />
                      </div>
                      <span className="font-medium text-gray-700">Costo huntRED®</span>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-green-600">
                        ${calculation.huntredCost.toLocaleString()} MXN
                      </div>
                      <div className="text-sm text-gray-500">por año</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Additional Benefits */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center text-gray-700">
                  <Target className="w-6 h-6 mr-2" />
                  Beneficios Adicionales
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    <span className="text-gray-700">Configuración en 24 horas</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    <span className="text-gray-700">Soporte local en español</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    <span className="text-gray-700">IA personalizada AURA™</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    <span className="text-gray-700">Integración nativa con HR</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    <span className="text-gray-700">Sin costos ocultos</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-16">
          <div className="bg-gradient-to-r from-green-600 to-green-700 rounded-2xl p-8 text-white max-w-4xl mx-auto">
            <h3 className="text-2xl md:text-3xl font-bold mb-4">
              ¿Listo para empezar a ahorrar?
            </h3>
            <p className="text-green-100 mb-6 text-lg">
              Únase a las empresas que ya están viendo un ROI promedio del {calculation.roiPercentage}% con huntRED®
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button className="bg-white text-green-600 hover:bg-gray-100 px-8 py-3 text-lg font-semibold">
                <Calculator className="w-5 h-5 mr-2" />
                Solicitar Análisis Personalizado
              </Button>
              <Button variant="outline" className="border-white text-white hover:bg-white hover:text-green-600 px-8 py-3 text-lg font-semibold">
                <ArrowRight className="w-5 h-5 mr-2" />
                Ver Casos de Éxito
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ROIDemonstrationSection; 