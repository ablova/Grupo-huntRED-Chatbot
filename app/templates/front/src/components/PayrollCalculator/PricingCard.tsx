import { FC } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Calculator, CheckCircle2 } from 'lucide-react';
import { usePayrollCalculator } from './PayrollCalculatorContext';

const PricingCard = () => {
  const { 
    employees, 
    getBasePrice, 
    getDispersionFactor, 
    calculateTotalCost, 
    calculateCostPerEmployee, 
    selectedAddons, 
    availableAddons 
  } = usePayrollCalculator();

  // Formato a USD
  const formatUSD = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  // Obtener los addons seleccionados
  const selectedAddonItems = availableAddons.filter(addon => 
    selectedAddons.includes(addon.id)
  );

  return (
    <Card className="glass border-primary/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calculator className="h-5 w-5" />
          Precio Estimado
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Precio total */}
        <div className="text-center">
          <p className="text-sm text-muted-foreground">Precio mensual estimado</p>
          <div className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            {formatUSD(calculateTotalCost())}
          </div>
          <p className="text-sm mt-1">
            {formatUSD(calculateCostPerEmployee())} por usuario/mes
          </p>
        </div>

        {/* Detalles de precio */}
        <div className="space-y-3">
          <div className="flex justify-between items-center pb-2 border-b">
            <span className="text-sm">Precio base ({employees} usuarios)</span>
            <span className="font-medium">
              {formatUSD(getBasePrice())} × {employees} = {formatUSD(getBasePrice() * employees)}
            </span>
          </div>

          {/* Addons seleccionados */}
          {selectedAddonItems.map(addon => {
            if (addon.id === 'nomina_basica') return null;
            if (addon.id === 'dispersion_automatica') {
              // Para dispersión automática mostramos el factor de dispersión
              const factor = getDispersionFactor();
              if (factor <= 1) return null;
              
              return (
                <div key={addon.id} className="flex justify-between items-center pb-2 border-b">
                  <span className="text-sm">Factor de dispersión</span>
                  <span className="font-medium text-blue-600">
                    +{((factor - 1) * 100).toFixed(0)}%
                  </span>
                </div>
              );
            }
            
            // Para otros addons mostramos su precio
            return (
              <div key={addon.id} className="flex justify-between items-center pb-2 border-b">
                <span className="text-sm">{addon.name}</span>
                <span className="font-medium">
                  {formatUSD(addon.price)} × {employees} = {formatUSD(addon.price * employees)}
                </span>
              </div>
            );
          })}
        </div>

        {/* Notas de precio */}
        <div className="pt-4 space-y-2">
          <h4 className="text-sm font-medium">Incluye:</h4>
          <ul className="space-y-2">
            {[
              "Cálculos automáticos de nómina conforme a legislación",
              "Control de horas y asistencia vía sistema interno de mensajería",
              "Gestión de vacaciones y ausencias",
              "Soporte para integración con sistemas existentes",
              "Reportes y análisis básicos",
              "Cumplimiento normativo actualizado",
            ].map((item, i) => (
              <li key={i} className="flex gap-2 text-sm">
                <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0 mt-0.5" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};

export default PricingCard;
