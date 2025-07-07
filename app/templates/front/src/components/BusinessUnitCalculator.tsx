import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Calculator, Plus, Minus, Calendar, Mail, Info, Building2, User, Users, Briefcase, LineChart, BrainCircuit } from 'lucide-react';

type BusinessUnitType = 'executive' | 'standard' | 'huntu' | 'amigro';

interface BusinessUnitConfig {
  name: string;
  description: string;
  icon: React.ElementType;
  color: string;
  baseValues: {
    baseSalary: number;
    ai: number;
    hybrid: number;
    human: number;
  };
  defaultServices: string[];
  specializations: string[];
  metricMultipliers: {
    costSavings: number;
    timeReduction: number;
    retentionImprovement: number;
    roiMultiplier: number;
  };
}

const businessUnits: Record<BusinessUnitType, BusinessUnitConfig> = {
  executive: {
    name: "huntRED® Executive",
    description: "Posiciones ejecutivas y directivas de alta especialización",
    icon: Briefcase,
    color: "bg-indigo-600",
    baseValues: {
      baseSalary: 150000,
      ai: 1,
      hybrid: 2,
      human: 1
    },
    defaultServices: ["Headhunting", "Assessment de Competencias", "Onboarding Ejecutivo"],
    specializations: ["C-Suite", "Directores", "Gerentes Senior"],
    metricMultipliers: {
      costSavings: 1.4,
      timeReduction: 0.65,
      retentionImprovement: 1.5,
      roiMultiplier: 2.0
    }
  },
  standard: {
    name: "huntRED®",
    description: "Especialistas y gerencias medias con experiencia comprobada",
    icon: User,
    color: "bg-blue-600",
    baseValues: {
      baseSalary: 80000,
      ai: 2,
      hybrid: 3,
      human: 1
    },
    defaultServices: ["Reclutamiento Especializado", "Assessment Técnico", "Referenciación"],
    specializations: ["Gerencias", "Coordinadores", "Especialistas"],
    metricMultipliers: {
      costSavings: 1.2,
      timeReduction: 0.6,
      retentionImprovement: 1.3,
      roiMultiplier: 1.7
    }
  },
  huntu: {
    name: "huntU",
    description: "Talento universitario y puestos de entrada con alto potencial",
    icon: Users,
    color: "bg-teal-600",
    baseValues: {
      baseSalary: 25000,
      ai: 5,
      hybrid: 2,
      human: 0
    },
    defaultServices: ["Reclutamiento en Campus", "Programas de Trainee", "Evaluación Grupal"],
    specializations: ["Recién Egresados", "Practicantes", "Analistas Junior"],
    metricMultipliers: {
      costSavings: 1.0,
      timeReduction: 0.7,
      retentionImprovement: 1.0,
      roiMultiplier: 1.3
    }
  },
  amigro: {
    name: "Amigro",
    description: "Talento para puestos operativos y de alta rotación",
    icon: Building2,
    color: "bg-amber-600",
    baseValues: {
      baseSalary: 18000,
      ai: 10,
      hybrid: 0,
      human: 0
    },
    defaultServices: ["Reclutamiento Masivo", "Validación Básica", "Onboarding Rápido"],
    specializations: ["Operativos", "Call Center", "Ventas", "Servicio al Cliente"],
    metricMultipliers: {
      costSavings: 0.8,
      timeReduction: 0.8,
      retentionImprovement: 0.7,
      roiMultiplier: 1.1
    }
  }
};

const BusinessUnitCalculator = () => {
  const [selectedUnit, setSelectedUnit] = useState<BusinessUnitType>('executive');
  const [values, setValues] = useState({
    executive: { ...businessUnits.executive.baseValues },
    standard: { ...businessUnits.standard.baseValues },
    huntu: { ...businessUnits.huntu.baseValues },
    amigro: { ...businessUnits.amigro.baseValues }
  });
  
  const [metrics, setMetrics] = useState({
    currentHires: 15,
    timeToHire: 45,
    turnoverRate: 20,
    recruitmentCost: 5000
  });

  // Helper function to calculate total positions
  const getTotalPositions = (service: {ai: number, hybrid: number, human: number}) => {
    return service.ai + service.hybrid + service.human;
  };

  // Calculate base for salary calculation
  const calculateBase = (monthlySalary: number) => {
    return monthlySalary * 13; // 12 months + 1 month aguinaldo
  };

  // Calculate pricing for the business unit
  const calculatePricing = () => {
    const service = values[selectedUnit];
    const baseSalary = service.baseSalary;
    const baseCalculation = calculateBase(baseSalary);
    const totalPositions = getTotalPositions(service);
    
    let total = 0;
    
    // AI pricing (fixed rate)
    total += service.ai * (selectedUnit === 'executive' ? 95000 : 
                          selectedUnit === 'standard' ? 75000 : 
                          selectedUnit === 'huntu' ? 45000 : 25000);
    
    // Hybrid pricing (% varies by business unit)
    const hybridRates = {
      executive: totalPositions >= 2 ? 0.13 : 0.14,
      standard: totalPositions >= 2 ? 0.12 : 0.13,
      huntu: totalPositions >= 2 ? 0.10 : 0.11,
      amigro: totalPositions >= 2 ? 0.08 : 0.09
    };
    
    total += service.hybrid * (baseCalculation * hybridRates[selectedUnit]);
    
    // Human pricing (% varies by business unit)
    const humanRates = {
      executive: totalPositions >= 2 ? 0.18 : 0.20,
      standard: totalPositions >= 2 ? 0.16 : 0.18,
      huntu: totalPositions >= 2 ? 0.14 : 0.15,
      amigro: totalPositions >= 2 ? 0.12 : 0.13
    };
    
    total += service.human * (baseCalculation * humanRates[selectedUnit]);
    
    return total;
  };

  // Calculate ROI metrics
  const calculateROI = () => {
    const unitConfig = businessUnits[selectedUnit];
    const multipliers = unitConfig.metricMultipliers;
    
    // Time reduction in days
    const timeReduction = Math.round(metrics.timeToHire * multipliers.timeReduction);
    
    // Cost savings
    const costPerHire = metrics.recruitmentCost;
    const annualRecruitmentCost = metrics.currentHires * costPerHire;
    const timeSavings = metrics.currentHires * timeReduction * 100; // $100 per day saved
    const automationSavings = annualRecruitmentCost * multipliers.costSavings * 0.4;
    
    // Quality improvement
    const improvedRetention = metrics.turnoverRate * (1 - multipliers.retentionImprovement * 0.2);
    const qualityImprovement = Math.round(((metrics.turnoverRate - improvedRetention) / metrics.turnoverRate) * 100);
    
    // ROI calculation
    const totalSavings = timeSavings + automationSavings;
    const investment = calculatePricing();
    const roi = Math.round((totalSavings - investment) / investment * 100 * multipliers.roiMultiplier);
    
    return {
      timeReduction,
      costSavings: Math.round(totalSavings),
      qualityImprovement,
      roi: Math.max(30, roi), // Minimum 30% ROI
      paybackMonths: Math.ceil(12 / multipliers.roiMultiplier)
    };
  };

  const updateUnitValues = (field: string, value: number) => {
    setValues(prev => ({
      ...prev,
      [selectedUnit]: {
        ...prev[selectedUnit],
        [field]: Math.max(0, value)
      }
    }));
  };

  const updateMetric = (field: string, value: number) => {
    setMetrics(prev => ({
      ...prev,
      [field]: Math.max(0, value)
    }));
  };

  const currentUnit = businessUnits[selectedUnit];
  const roiMetrics = calculateROI();
  const Icon = currentUnit.icon;

  return (
    <section className="py-16 bg-muted/10">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-12">
          <h2 className="text-3xl md:text-4xl font-bold">
            Calculadora por <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">Unidad de Negocio</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
            Configura y calcula el retorno de inversión para cada unidad de negocio especializada
          </p>
        </div>

        <div className="max-w-6xl mx-auto">
          {/* Business Unit Selector Tabs */}
          <Tabs value={selectedUnit} onValueChange={(value) => setSelectedUnit(value as BusinessUnitType)} className="mb-8">
            <TabsList className="grid w-full grid-cols-4">
              {Object.entries(businessUnits).map(([key, unit]) => (
                <TabsTrigger key={key} value={key} className="text-sm">
                  {unit.name}
                </TabsTrigger>
              ))}
            </TabsList>

            {Object.entries(businessUnits).map(([key, unit]) => (
              <TabsContent key={key} value={key} className="space-y-6">
                {/* Business Unit Info Card */}
                <Card className="glass border-primary/20">
                  <CardHeader className="pb-2">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 ${unit.color} rounded-full flex items-center justify-center text-white`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          {unit.name}
                        </CardTitle>
                        <p className="text-sm text-muted-foreground">{unit.description}</p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <h4 className="text-sm font-medium mb-2">Especializaciones</h4>
                        <div className="flex flex-wrap gap-1">
                          {unit.specializations.map((spec, i) => (
                            <span key={i} className={`px-2 py-1 ${unit.color.replace('bg-', 'bg-').replace('600', '100')} dark:bg-opacity-20 rounded-full text-xs`}>
                              {spec}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium mb-2">Servicios Incluidos</h4>
                        <div className="flex flex-col gap-1">
                          {unit.defaultServices.map((service, i) => (
                            <div key={i} className="flex items-center gap-1 text-xs">
                              <div className="w-1 h-1 rounded-full bg-primary"></div>
                              <span>{service}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Salary and Configuration */}
                    <div className="space-y-4 mb-6">
                      <div className="flex justify-between items-center">
                        <label className="text-sm font-medium">Salario Base Mensual (MXN)</label>
                        <div className="flex items-center gap-2 w-32">
                          <input 
                            type="number"
                            value={values[selectedUnit].baseSalary}
                            onChange={(e) => updateUnitValues('baseSalary', parseInt(e.target.value) || 0)}
                            className="w-full p-1 rounded border text-center"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <div className="flex justify-between items-center">
                            <label className="text-sm font-medium">Búsquedas AI</label>
                            <div className="flex items-center gap-2">
                              <Button size="sm" variant="outline" onClick={() => updateUnitValues('ai', values[selectedUnit].ai - 1)}>
                                <Minus className="h-3 w-3" />
                              </Button>
                              <span className="w-8 text-center">{values[selectedUnit].ai}</span>
                              <Button size="sm" variant="outline" onClick={() => updateUnitValues('ai', values[selectedUnit].ai + 1)}>
                                <Plus className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between items-center">
                            <label className="text-sm font-medium">Híbridas</label>
                            <div className="flex items-center gap-2">
                              <Button size="sm" variant="outline" onClick={() => updateUnitValues('hybrid', values[selectedUnit].hybrid - 1)}>
                                <Minus className="h-3 w-3" />
                              </Button>
                              <span className="w-8 text-center">{values[selectedUnit].hybrid}</span>
                              <Button size="sm" variant="outline" onClick={() => updateUnitValues('hybrid', values[selectedUnit].hybrid + 1)}>
                                <Plus className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between items-center">
                            <label className="text-sm font-medium">Humanas</label>
                            <div className="flex items-center gap-2">
                              <Button size="sm" variant="outline" onClick={() => updateUnitValues('human', values[selectedUnit].human - 1)}>
                                <Minus className="h-3 w-3" />
                              </Button>
                              <span className="w-8 text-center">{values[selectedUnit].human}</span>
                              <Button size="sm" variant="outline" onClick={() => updateUnitValues('human', values[selectedUnit].human + 1)}>
                                <Plus className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Company Metrics for ROI Calculation */}
                    <div className="border-t pt-4">
                      <h4 className="text-sm font-medium mb-3 flex items-center">
                        <LineChart className="h-4 w-4 mr-1" />
                        Métricas de tu Empresa para Cálculo de ROI
                      </h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex justify-between items-center">
                          <label className="text-sm">Contrataciones anuales</label>
                          <input 
                            type="number"
                            value={metrics.currentHires}
                            onChange={(e) => updateMetric('currentHires', parseInt(e.target.value) || 0)}
                            className="w-20 p-1 rounded border text-center"
                          />
                        </div>
                        <div className="flex justify-between items-center">
                          <label className="text-sm">Tiempo actual de contratación (días)</label>
                          <input 
                            type="number"
                            value={metrics.timeToHire}
                            onChange={(e) => updateMetric('timeToHire', parseInt(e.target.value) || 0)}
                            className="w-20 p-1 rounded border text-center"
                          />
                        </div>
                        <div className="flex justify-between items-center">
                          <label className="text-sm">Rotación actual (%)</label>
                          <input 
                            type="number"
                            value={metrics.turnoverRate}
                            onChange={(e) => updateMetric('turnoverRate', parseInt(e.target.value) || 0)}
                            className="w-20 p-1 rounded border text-center"
                          />
                        </div>
                        <div className="flex justify-between items-center">
                          <label className="text-sm">Costo por contratación (MXN)</label>
                          <input 
                            type="number"
                            value={metrics.recruitmentCost}
                            onChange={(e) => updateMetric('recruitmentCost', parseInt(e.target.value) || 0)}
                            className="w-20 p-1 rounded border text-center"
                          />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Results Card */}
                <div className="grid md:grid-cols-2 gap-6">
                  <Card className="glass border-primary/20">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <Calculator className="h-5 w-5" />
                        Inversión Estimada
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-center mb-4">
                        <div className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                          ${calculatePricing().toLocaleString()} MXN
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Inversión total estimada
                        </p>
                      </div>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between items-center p-2 border-b">
                          <span>Búsquedas AI:</span>
                          <span className="font-medium">{values[selectedUnit].ai}</span>
                        </div>
                        <div className="flex justify-between items-center p-2 border-b">
                          <span>Búsquedas Híbridas:</span>
                          <span className="font-medium">{values[selectedUnit].hybrid}</span>
                        </div>
                        <div className="flex justify-between items-center p-2 border-b">
                          <span>Búsquedas Humanas:</span>
                          <span className="font-medium">{values[selectedUnit].human}</span>
                        </div>
                        <div className="flex justify-between items-center p-2 border-b">
                          <span>Total de posiciones:</span>
                          <span className="font-medium">{getTotalPositions(values[selectedUnit])}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="glass border-primary/20">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <LineChart className="h-5 w-5" />
                        ROI Proyectado
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4 mb-6">
                        <div className="text-center p-3 bg-blue-50 dark:bg-blue-950/30 rounded-lg">
                          <p className="text-sm text-muted-foreground">Reducción de Tiempo</p>
                          <p className="text-2xl font-bold text-blue-600">{roiMetrics.timeReduction} días</p>
                        </div>
                        <div className="text-center p-3 bg-green-50 dark:bg-green-950/30 rounded-lg">
                          <p className="text-sm text-muted-foreground">Ahorro Total</p>
                          <p className="text-2xl font-bold text-green-600">${roiMetrics.costSavings.toLocaleString()}</p>
                        </div>
                        <div className="text-center p-3 bg-purple-50 dark:bg-purple-950/30 rounded-lg">
                          <p className="text-sm text-muted-foreground">Mejora en Retención</p>
                          <p className="text-2xl font-bold text-purple-600">{roiMetrics.qualityImprovement}%</p>
                        </div>
                        <div className="text-center p-3 bg-amber-50 dark:bg-amber-950/30 rounded-lg">
                          <p className="text-sm text-muted-foreground">ROI Anual</p>
                          <p className="text-2xl font-bold text-amber-600">{roiMetrics.roi}%</p>
                        </div>
                      </div>
                      
                      <div className="text-center p-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg">
                        <p className="font-medium">Tiempo de recuperación: {roiMetrics.paybackMonths} meses</p>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* AI Specialization */}
                <div className="border-t pt-6">
                  <div className="flex items-center gap-2 mb-4">
                    <BrainCircuit className="h-5 w-5 text-indigo-600" />
                    <h3 className="text-lg font-medium">Especialización con IA</h3>
                  </div>
                  <p className="text-sm text-muted-foreground mb-4">
                    Cada Business Unit cuenta con algoritmos y modelos de IA/ML optimizados para su segmento específico:
                  </p>
                  
                  <div className="p-4 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950/30 dark:to-blue-950/30 rounded-lg">
                    <p className="font-medium mb-2">Especialización para {currentUnit.name}:</p>
                    <ul className="list-disc pl-5 space-y-1 text-sm">
                      {selectedUnit === 'executive' && (
                        <>
                          <li>Modelos predictivos enfocados en liderazgo y visión estratégica</li>
                          <li>Análisis de trayectoria para validación de logros significativos</li>
                          <li>Detección de potencial para roles de alta complejidad</li>
                        </>
                      )}
                      {selectedUnit === 'standard' && (
                        <>
                          <li>Algoritmos de matchmaking especializados por sector y disciplina</li>
                          <li>Evaluación técnica y de habilidades blandas equilibrada</li>
                          <li>Análisis predictivo de permanencia y desarrollo</li>
                        </>
                      )}
                      {selectedUnit === 'huntu' && (
                        <>
                          <li>Modelos centrados en potencial y capacidad de aprendizaje</li>
                          <li>Evaluación de adaptabilidad y crecimiento acelerado</li>
                          <li>Identificación de talentos con mayor proyección futura</li>
                        </>
                      )}
                      {selectedUnit === 'amigro' && (
                        <>
                          <li>Algoritmos optimizados para alto volumen de candidatos</li>
                          <li>Validación rápida de habilidades operativas esenciales</li>
                          <li>Modelos predictivos de rotación y permanencia</li>
                        </>
                      )}
                    </ul>
                  </div>
                </div>
              </TabsContent>
            ))}
          </Tabs>
          
          {/* CTA */}
          <div className="text-center mt-10">
            <Button size="lg" className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-90">
              <Mail className="mr-2 h-4 w-4" />
              Solicitar Propuesta Personalizada
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default BusinessUnitCalculator;
