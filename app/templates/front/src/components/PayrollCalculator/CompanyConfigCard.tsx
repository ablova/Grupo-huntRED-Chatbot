import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Building, Users } from 'lucide-react';
import { usePayrollCalculator } from './PayrollCalculatorContext';

const CompanyConfigCard = () => {
  const {
    employees,
    setEmployees,
    companySize,
    dispersionsPerMonth,
    setDispersionsPerMonth
  } = usePayrollCalculator();
  
  const companySizeLabel = {
    small: 'Pequeña',
    medium: 'Mediana',
    large: 'Grande'
  }[companySize];

  return (
    <Card className="glass border-primary/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Building className="h-5 w-5" />
          Configura tu Empresa
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Número de Empleados */}
        <div>
          <div className="flex justify-between mb-2">
            <label className="text-sm font-medium">Número de Empleados</label>
            <span className="bg-blue-100 dark:bg-blue-900/30 px-2 py-0.5 rounded text-sm">
              {employees} <span className="text-xs text-muted-foreground">({companySizeLabel})</span>
            </span>
          </div>
          <Slider
            min={10}
            max={500}
            step={5}
            value={[employees]}
            onValueChange={(value) => setEmployees(value[0])}
            className="my-4"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>10</span>
            <span>100</span>
            <span>250</span>
            <span>500</span>
          </div>
        </div>
        
        {/* Dispersiones por mes */}
        <div>
          <div className="flex justify-between mb-2">
            <label className="text-sm font-medium">Dispersiones por Mes</label>
            <span className="bg-blue-100 dark:bg-blue-900/30 px-2 py-0.5 rounded text-sm">
              {dispersionsPerMonth}
            </span>
          </div>
          <Slider
            min={1}
            max={4}
            step={1}
            value={[dispersionsPerMonth]}
            onValueChange={(value) => setDispersionsPerMonth(value[0])}
            className="my-4"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>1</span>
            <span>2</span>
            <span>3</span>
            <span>4</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Nota: A partir de 3 dispersiones mensuales, se aplica un factor adicional de 5% por dispersión extra.
          </p>
        </div>
        
        {/* Información sobre sistema interno de mensajería */}
        <div className="p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
          <div className="flex items-start gap-2">
            <Users className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium">Sistema Interno de Mensajería</h4>
              <p className="text-xs text-muted-foreground mt-1">
                Los empleados pueden registrar entradas/salidas, solicitar vacaciones y más a través
                de nuestro sistema interno de mensajería segura (WhatsApp, Telegram, etc.).
                <br/>La plataforma utiliza únicamente nuestros sistemas propios, sin depender de proveedores
                externos para garantizar máxima seguridad y privacidad de datos.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default CompanyConfigCard;
