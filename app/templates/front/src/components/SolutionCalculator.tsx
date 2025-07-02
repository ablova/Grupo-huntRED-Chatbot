
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Calculator, Plus, Minus, Calendar, Mail, Info } from 'lucide-react';

const SolutionCalculator = () => {
  const [calculatorValues, setCalculatorValues] = useState({
    huntRedExecutive: { ai: 0, hybrid: 0, human: 0, baseSalary: 150000 },
    huntRedStandard: { ai: 0, hybrid: 0, human: 0, baseSalary: 80000 },
    huntU: 0,
    amigro: 0,
    assessments: 0,
    premiumAddons: []
  });

  // Helper function to calculate total positions for a service
  const getTotalPositions = (service) => {
    return service.ai + service.hybrid + service.human;
  };

  // Helper function to calculate base calculation
  const calculateBase = (monthlySalary, months = 12, aguinaldo = 1, bonus = 0) => {
    return monthlySalary * (months + aguinaldo + bonus);
  };

  // Calculate pricing for huntRED Executive and Standard
  const calculatePremiumPricing = (service, baseSalary) => {
    const baseCalculation = calculateBase(baseSalary);
    const totalPositions = getTotalPositions(service);
    
    let total = 0;
    
    // AI pricing (fixed rate from ATS)
    total += service.ai * 95000;
    
    // Hybrid pricing (14% or 13% if 2+)
    const hybridRate = totalPositions >= 2 ? 0.13 : 0.14;
    total += service.hybrid * (baseCalculation * hybridRate);
    
    // Human pricing (20% or 18% if 2+)
    const humanRate = totalPositions >= 2 ? 0.18 : 0.20;
    total += service.human * (baseCalculation * humanRate);
    
    return total;
  };

  const calculateTotal = () => {
    let total = 0;
    
    // huntRED Executive
    total += calculatePremiumPricing(calculatorValues.huntRedExecutive, calculatorValues.huntRedExecutive.baseSalary);
    
    // huntRED Standard
    total += calculatePremiumPricing(calculatorValues.huntRedStandard, calculatorValues.huntRedStandard.baseSalary);
    
    // huntU and amigro (fixed pricing)
    total += calculatorValues.huntU * 55000;
    total += calculatorValues.amigro * 20000;
    total += calculatorValues.assessments * 300;
    
    return total;
  };

  const updateService = (serviceName, field, value) => {
    setCalculatorValues(prev => ({
      ...prev,
      [serviceName]: {
        ...prev[serviceName],
        [field]: Math.max(0, value)
      }
    }));
  };

  const updateSimpleService = (service, value) => {
    setCalculatorValues(prev => ({
      ...prev,
      [service]: Math.max(0, value)
    }));
  };

  return (
    <section className="py-20 bg-muted/20" data-section="solution-calculator">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-16">
          <h2 className="text-3xl md:text-4xl font-bold">
            Calculadora de <span className="bg-tech-gradient bg-clip-text text-transparent">Solución</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Configura tu solución personalizada y obtén una estimación inmediata
          </p>
        </div>

        <div className="max-w-6xl mx-auto">
          <Tabs defaultValue="premium" className="mb-8">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="premium">huntRED® Premium</TabsTrigger>
              <TabsTrigger value="standard">Servicios Standard</TabsTrigger>
              <TabsTrigger value="assessments">Assessments</TabsTrigger>
            </TabsList>

            {/* Premium Services */}
            <TabsContent value="premium" className="space-y-6">
              {/* huntRED Executive */}
              <Card className="glass border-primary/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calculator className="h-5 w-5" />
                    huntRED® Executive
                    <span className="text-sm bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">Más Demandado</span>
                  </CardTitle>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Info className="h-4 w-4" />
                    Base de cálculo: Salario Mensual × (12 meses + Aguinaldo + Bono Potencial)
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium">Salario Base Mensual</label>
                      <div className="flex items-center mt-1">
                        <span className="text-sm mr-2">$</span>
                        <input
                          type="number"
                          value={calculatorValues.huntRedExecutive.baseSalary}
                          onChange={(e) => updateService('huntRedExecutive', 'baseSalary', parseInt(e.target.value) || 0)}
                          className="flex-1 px-3 py-2 border rounded-md"
                          data-source="ats.pricing.huntred_executive.base_salary"
                        />
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground pt-6">
                      Base de cálculo: ${calculateBase(calculatorValues.huntRedExecutive.baseSalary).toLocaleString()}
                    </div>
                  </div>
                  
                  <div className="grid md:grid-cols-3 gap-4">
                    {/* AI Searches */}
                    <div className="border rounded-lg p-4" data-pricing-id="huntred-executive-ai" data-source="ats.pricing.huntred_executive.ai">
                      <div className="font-medium mb-2">Búsquedas por IA</div>
                      <div className="text-sm text-muted-foreground mb-3" data-price-field="ai">$95,000 por búsqueda</div>
                      <div className="flex items-center gap-2">
                        <Button size="sm" variant="outline" onClick={() => updateService('huntRedExecutive', 'ai', calculatorValues.huntRedExecutive.ai - 1)}>
                          <Minus className="h-3 w-3" />
                        </Button>
                        <span className="w-8 text-center">{calculatorValues.huntRedExecutive.ai}</span>
                        <Button size="sm" variant="outline" onClick={() => updateService('huntRedExecutive', 'ai', calculatorValues.huntRedExecutive.ai + 1)}>
                          <Plus className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>

                    {/* Hybrid Searches */}
                    <div className="border rounded-lg p-4" data-pricing-id="huntred-executive-hybrid" data-source="ats.pricing.huntred_executive.hybrid">
                      <div className="font-medium mb-2">Búsquedas Híbridas</div>
                      <div className="text-sm text-muted-foreground mb-3" data-price-field="hybrid">
                        {getTotalPositions(calculatorValues.huntRedExecutive) >= 2 ? '13%' : '14%'} de la base
                      </div>
                      <div className="flex items-center gap-2">
                        <Button size="sm" variant="outline" onClick={() => updateService('huntRedExecutive', 'hybrid', calculatorValues.huntRedExecutive.hybrid - 1)}>
                          <Minus className="h-3 w-3" />
                        </Button>
                        <span className="w-8 text-center">{calculatorValues.huntRedExecutive.hybrid}</span>
                        <Button size="sm" variant="outline" onClick={() => updateService('huntRedExecutive', 'hybrid', calculatorValues.huntRedExecutive.hybrid + 1)}>
                          <Plus className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>

                    {/* Human Searches */}
                    <div className="border rounded-lg p-4" data-pricing-id="huntred-executive-human" data-source="ats.pricing.huntred_executive.human">
                      <div className="font-medium mb-2">Búsquedas Humanas</div>
                      <div className="text-sm text-muted-foreground mb-3" data-price-field="human">
                        {getTotalPositions(calculatorValues.huntRedExecutive) >= 2 ? '18%' : '20%'} de la base
                      </div>
                      <div className="flex items-center gap-2">
                        <Button size="sm" variant="outline" onClick={() => updateService('huntRedExecutive', 'human', calculatorValues.huntRedExecutive.human - 1)}>
                          <Minus className="h-3 w-3" />
                        </Button>
                        <span className="w-8 text-center">{calculatorValues.huntRedExecutive.human}</span>
                        <Button size="sm" variant="outline" onClick={() => updateService('huntRedExecutive', 'human', calculatorValues.huntRedExecutive.human + 1)}>
                          <Plus className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right text-lg font-semibold">
                    Subtotal: ${calculatePremiumPricing(calculatorValues.huntRedExecutive, calculatorValues.huntRedExecutive.baseSalary).toLocaleString()}
                  </div>
                </CardContent>
              </Card>

              {/* huntRED Standard */}
              <Card className="glass border-primary/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calculator className="h-5 w-5" />
                    huntRED® Standard
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium">Salario Base Mensual</label>
                      <div className="flex items-center mt-1">
                        <span className="text-sm mr-2">$</span>
                        <input
                          type="number"
                          value={calculatorValues.huntRedStandard.baseSalary}
                          onChange={(e) => updateService('huntRedStandard', 'baseSalary', parseInt(e.target.value) || 0)}
                          className="flex-1 px-3 py-2 border rounded-md"
                          data-source="ats.pricing.huntred_standard.base_salary"
                        />
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground pt-6">
                      Base de cálculo: ${calculateBase(calculatorValues.huntRedStandard.baseSalary).toLocaleString()}
                    </div>
                  </div>
                  
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="border rounded-lg p-4" data-pricing-id="huntred-standard-ai" data-source="ats.pricing.huntred_standard.ai">
                      <div className="font-medium mb-2">Búsquedas por IA</div>
                      <div className="text-sm text-muted-foreground mb-3" data-price-field="ai">$95,000 por búsqueda</div>
                      <div className="flex items-center gap-2">
                        <Button size="sm" variant="outline" onClick={() => updateService('huntRedStandard', 'ai', calculatorValues.huntRedStandard.ai - 1)}>
                          <Minus className="h-3 w-3" />
                        </Button>
                        <span className="w-8 text-center">{calculatorValues.huntRedStandard.ai}</span>
                        <Button size="sm" variant="outline" onClick={() => updateService('huntRedStandard', 'ai', calculatorValues.huntRedStandard.ai + 1)}>
                          <Plus className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>

                    <div className="border rounded-lg p-4" data-pricing-id="huntred-standard-hybrid" data-source="ats.pricing.huntred_standard.hybrid">
                      <div className="font-medium mb-2">Búsquedas Híbridas</div>
                      <div className="text-sm text-muted-foreground mb-3" data-price-field="hybrid">
                        {getTotalPositions(calculatorValues.huntRedStandard) >= 2 ? '13%' : '14%'} de la base
                      </div>
                      <div className="flex items-center gap-2">
                        <Button size="sm" variant="outline" onClick={() => updateService('huntRedStandard', 'hybrid', calculatorValues.huntRedStandard.hybrid - 1)}>
                          <Minus className="h-3 w-3" />
                        </Button>
                        <span className="w-8 text-center">{calculatorValues.huntRedStandard.hybrid}</span>
                        <Button size="sm" variant="outline" onClick={() => updateService('huntRedStandard', 'hybrid', calculatorValues.huntRedStandard.hybrid + 1)}>
                          <Plus className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>

                    <div className="border rounded-lg p-4" data-pricing-id="huntred-standard-human" data-source="ats.pricing.huntred_standard.human">
                      <div className="font-medium mb-2">Búsquedas Humanas</div>
                      <div className="text-sm text-muted-foreground mb-3" data-price-field="human">
                        {getTotalPositions(calculatorValues.huntRedStandard) >= 2 ? '18%' : '20%'} de la base
                      </div>
                      <div className="flex items-center gap-2">
                        <Button size="sm" variant="outline" onClick={() => updateService('huntRedStandard', 'human', calculatorValues.huntRedStandard.human - 1)}>
                          <Minus className="h-3 w-3" />
                        </Button>
                        <span className="w-8 text-center">{calculatorValues.huntRedStandard.human}</span>
                        <Button size="sm" variant="outline" onClick={() => updateService('huntRedStandard', 'human', calculatorValues.huntRedStandard.human + 1)}>
                          <Plus className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right text-lg font-semibold">
                    Subtotal: ${calculatePremiumPricing(calculatorValues.huntRedStandard, calculatorValues.huntRedStandard.baseSalary).toLocaleString()}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Standard Services */}
            <TabsContent value="standard" className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between p-4 border rounded-lg" data-pricing-id="huntu" data-source="ats.pricing.huntu">
                  <div>
                    <div className="font-medium">huntU</div>
                    <div className="text-sm text-muted-foreground" data-price-field="huntu">$55,000 por búsqueda</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" onClick={() => updateSimpleService('huntU', calculatorValues.huntU - 1)}>
                      <Minus className="h-3 w-3" />
                    </Button>
                    <span className="w-8 text-center">{calculatorValues.huntU}</span>
                    <Button size="sm" variant="outline" onClick={() => updateSimpleService('huntU', calculatorValues.huntU + 1)}>
                      <Plus className="h-3 w-3" />
                    </Button>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg" data-pricing-id="amigro" data-source="ats.pricing.amigro">
                  <div>
                    <div className="font-medium">amigro</div>
                    <div className="text-sm text-muted-foreground" data-price-field="amigro">$20,000 por búsqueda</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" onClick={() => updateSimpleService('amigro', calculatorValues.amigro - 1)}>
                      <Minus className="h-3 w-3" />
                    </Button>
                    <span className="w-8 text-center">{calculatorValues.amigro}</span>
                    <Button size="sm" variant="outline" onClick={() => updateSimpleService('amigro', calculatorValues.amigro + 1)}>
                      <Plus className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Assessments */}
            <TabsContent value="assessments">
              <div className="flex items-center justify-between p-4 border rounded-lg" data-assessment-id="assessment-licenses" data-source="ats.pricing.assessments.bulk">
                <div>
                  <div className="font-medium">Licencias de Assessment</div>
                  <div className="text-sm text-muted-foreground" data-price-field="assessment-licenses">Promedio $300/usuario/año</div>
                </div>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" onClick={() => updateSimpleService('assessments', calculatorValues.assessments - 1)}>
                    <Minus className="h-3 w-3" />
                  </Button>
                  <span className="w-8 text-center">{calculatorValues.assessments}</span>
                  <Button size="sm" variant="outline" onClick={() => updateSimpleService('assessments', calculatorValues.assessments + 1)}>
                    <Plus className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </TabsContent>
          </Tabs>
          
          {/* Total Calculation */}
          <Card className="glass border-primary/20">
            <CardContent className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-xl font-semibold">Total Estimado</h4>
                <div className="text-3xl font-bold bg-tech-gradient bg-clip-text text-transparent" data-total-calculator="solution-total">
                  ${calculateTotal().toLocaleString()}
                </div>
              </div>
              
              <div className="space-y-2 text-sm text-muted-foreground mb-6">
                <p>• Base de cálculo: Salario Mensual × (12 meses + Aguinaldo + Bono Potencial)</p>
                <p>• Búsquedas híbridas: 14% de la base (13% si son 2 o más)</p>
                <p>• Búsquedas humanas: 20% de la base (18% si son 2 o más)</p>
                <p>• Búsquedas por IA: Precio fijo de $95,000</p>
                <p>• Paquetes empresariales personalizados disponibles</p>
              </div>
              
              <div className="flex gap-4">
                <Button className="flex-1 bg-tech-gradient hover:opacity-90">
                  <Calendar className="mr-2 h-4 w-4" />
                  Solicitar Propuesta Formal
                </Button>
                <Button variant="outline" className="flex-1">
                  <Mail className="mr-2 h-4 w-4" />
                  Agendar Demo
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default SolutionCalculator;
