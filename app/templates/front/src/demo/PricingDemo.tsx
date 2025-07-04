import React from 'react';
import PricingAdvantagesSection from '../components/PricingAdvantagesSection';

const PricingDemo: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Demo: Comparativa de Precios Dinámica
          </h1>
          <p className="text-xl text-gray-600">
            Componente interactivo para comparar precios huntRED vs competencia
          </p>
        </div>
        
        <PricingAdvantagesSection />
      </div>
    </div>
  );
};

export default PricingDemo; 