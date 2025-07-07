import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Plus, CreditCard, GraduationCap, BookOpen, Scale, HeartPulse, BadgeDollarSign } from 'lucide-react';
import { usePayrollCalculator } from './PayrollCalculatorContext';

const AddonsCard = () => {
  const { availableAddons, selectedAddons, toggleAddon } = usePayrollCalculator();

  // Iconos para los addons
  const addonIcons: Record<string, React.ElementType> = {
    'nomina_basica': FileText,
    'dispersion_automatica': Coins,
    'creditos_empleados': CreditCard,
    'aura_learning': GraduationCap,
    'aura_ai': BookOpen,
    'nom_35': HeartPulse,
    'advanced_analytics': BadgeDollarSign,
    'compliance': Scale
  };

  return (
    <Card className="glass border-primary/20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Plus className="h-5 w-5" />
          Addons y Servicios Complementarios
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {availableAddons.map((addon) => {
            const AddonIcon = addonIcons[addon.id] || Plus;
            
            return (
              <div
                key={addon.id}
                className={`flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedAddons.includes(addon.id) 
                    ? 'bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800' 
                    : 'hover:bg-muted/50'
                }`}
                onClick={() => toggleAddon(addon.id)}
              >
                <div className="flex-shrink-0 mt-0.5">
                  <Checkbox 
                    checked={selectedAddons.includes(addon.id)} 
                    onCheckedChange={() => toggleAddon(addon.id)}
                    className="data-[state=checked]:bg-blue-600"
                    disabled={addon.id === 'nomina_basica'} // La nómina básica siempre está incluida
                  />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-1">
                    <AddonIcon className="h-4 w-4 text-blue-600" />
                    <span className="font-medium text-sm">
                      {addon.name}
                      {addon.isPremium && (
                        <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300">
                          Premium
                        </span>
                      )}
                      {addon.id === 'nomina_basica' && (
                        <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
                          Incluido
                        </span>
                      )}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {addon.description}
                  </p>
                  {addon.id !== 'nomina_basica' && addon.id !== 'dispersion_automatica' && (
                    <div className="mt-1 text-xs font-medium text-blue-600">
                      +${addon.price} USD/usuario/mes
                    </div>
                  )}
                  {addon.id === 'dispersion_automatica' && (
                    <div className="mt-1 text-xs font-medium text-blue-600">
                      +5% por dispersión adicional (después de 2)
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          
          {/* Nota sobre los créditos */}
          <div className="p-3 bg-muted/50 rounded-lg mt-4">
            <p className="text-xs text-muted-foreground">
              <strong>Nota importante:</strong> No ofrecemos créditos a empresas sobre nómina para garantizar la precisión y cumplimiento fiscal. 
              Los créditos para empleados se ofrecen exclusivamente a través de nuestras alianzas con terceros financieros verificados.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Importamos el componente FileText que faltaba
import { FileText, Coins } from 'lucide-react';

export default AddonsCard;
