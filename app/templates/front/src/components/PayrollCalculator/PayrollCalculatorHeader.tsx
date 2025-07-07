import React from 'react';
import { Calculator } from 'lucide-react';

const PayrollCalculatorHeader = () => {
  return (
    <div className="text-center space-y-4 mb-12">
      <div className="inline-flex items-center justify-center p-2 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-2">
        <Calculator className="h-6 w-6 text-blue-600" />
      </div>
      <h2 className="text-3xl md:text-4xl font-bold">
        Calculadora de <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">Administración de Nómina</span>
      </h2>
      <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
        Configura tu solución personalizada con precios transparentes y precisos
      </p>
      <div className="max-w-2xl mx-auto p-3 bg-amber-50 dark:bg-amber-950/20 rounded-lg text-sm text-amber-800 dark:text-amber-200 mt-4">
        <p>
          <strong>Nota:</strong> Los precios mostrados son valores temporales aproximados (28-32 USD por usuario/mes según tamaño).
          El módulo de Pricing completo estará disponible próximamente con valores finales.
        </p>
      </div>
    </div>
  );
};

export default PayrollCalculatorHeader;
