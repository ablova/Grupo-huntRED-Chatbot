import { FC } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Clock, CheckCircle2, Repeat } from 'lucide-react';
import { usePayrollCalculator } from './PayrollCalculatorContext';

const ROICard = () => {
  const { calculateTotalCost, calculateAnnualSavings } = usePayrollCalculator();
  
  // Formato a USD
  const formatUSD = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(amount);
  };
  
  const totalCostMonthly = calculateTotalCost();
  const totalCostAnnual = totalCostMonthly * 12;
  const annualSavings = calculateAnnualSavings();
  
  // Calcular ROI
  const roi = Math.round((annualSavings / totalCostAnnual) * 100);
  
  // Calcular tiempo de recuperación en meses
  const paybackMonths = Math.ceil(totalCostAnnual / annualSavings * 12);
  
  // Beneficios para mostrar
  const benefits = [
    {
      title: "Ahorro de Tiempo",
      description: "Reducción de hasta 85% en tiempo dedicado a procesos de nómina",
      icon: Clock,
      color: "text-blue-600"
    },
    {
      title: "Precisión",
      description: "Reducción de errores en cálculos y pagos de hasta 95%",
      icon: CheckCircle2,
      color: "text-green-600"
    },
    {
      title: "Cumplimiento",
      description: "Actualización automática con normativa vigente",
      icon: Scale,
      color: "text-purple-600"
    },
    {
      title: "Rotación",
      description: "Mejora en satisfacción y retención de empleados",
      icon: Repeat,
      color: "text-amber-600"
    }
  ];

  return (
    <Card className="glass border-primary/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <LineChart className="h-5 w-5" />
          ROI Proyectado
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Métricas de ROI */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <p className="text-sm text-muted-foreground">Ahorro Anual Est.</p>
            <p className="text-2xl font-bold text-green-600">{formatUSD(annualSavings)}</p>
          </div>
          <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-sm text-muted-foreground">ROI Anual</p>
            <p className="text-2xl font-bold text-blue-600">{roi}%</p>
          </div>
        </div>
        
        {/* Tiempo de recuperación */}
        <div className="text-center p-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg">
          <p className="text-sm mb-1">Tiempo de recuperación estimado</p>
          <p className="text-xl font-bold">{paybackMonths} meses</p>
        </div>
        
        {/* Beneficios */}
        <div className="space-y-3 pt-2">
          <h4 className="text-sm font-medium">Beneficios principales:</h4>
          <div className="grid grid-cols-2 gap-3">
            {benefits.map((benefit, index) => {
              const Icon = benefit.icon;
              return (
                <div key={index} className="flex items-start gap-2">
                  <div className={`mt-0.5 ${benefit.color}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <h5 className="text-sm font-medium">{benefit.title}</h5>
                    <p className="text-xs text-muted-foreground">{benefit.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        
        {/* Nota sobre valor a largo plazo */}
        <div className="pt-4">
          <p className="text-xs text-muted-foreground">
            El sistema de Administración de Nómina ofrece beneficios adicionales a largo plazo
            como mayor seguridad, adaptabilidad a cambios normativos y mejora en la
            toma de decisiones gracias a datos precisos y actualizados.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

// Importamos el Scale que faltaba
import { Scale } from 'lucide-react';

export default ROICard;
