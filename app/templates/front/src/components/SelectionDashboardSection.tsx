import React from 'react';
import DragDropDashboard from './DragDropDashboard';

const SelectionDashboardSection = () => {
  return (
    <section className="py-16 bg-gray-50 dark:bg-gray-900" id="selection-dashboard">
      <div className="container mx-auto px-4">
        <div className="max-w-3xl mx-auto text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4 text-gray-900 dark:text-white">
            Dashboard de Selección Inteligente
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Experimente la interfaz de selección con acciones automáticas en tiempo real
          </p>
        </div>
        
        {/* Descripción del sistema */}
        <div className="max-w-4xl mx-auto bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-10">
          <h3 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Potencia tu proceso de selección con automatización inteligente
          </h3>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900 dark:text-gray-100">Características principales:</h4>
              <ul className="space-y-2 text-gray-600 dark:text-gray-300">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  Flujos de trabajo personalizables para cada cliente
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  Automatización de acciones repetitivas (emails, agendamiento, etc.)
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  Integración con sistemas de mensajería internos
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  Análisis predictivo de éxito en cada etapa
                </li>
              </ul>
            </div>
            
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900 dark:text-gray-100">Beneficios:</h4>
              <ul className="space-y-2 text-gray-600 dark:text-gray-300">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  Reduce tiempo de contratación hasta en un 35%
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  Mejora experiencia del candidato con comunicación fluida
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  Dashboard visual en tiempo real para toda la organización
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  Análisis avanzado de métricas de selección
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Demo interactivo */}
        <DragDropDashboard />

        {/* Llamada a la acción */}
        <div className="mt-12 text-center">
          <p className="text-lg mb-4 text-gray-600 dark:text-gray-300">
            Personaliza este dashboard para tu organización
          </p>
          <button className="bg-gradient-to-r from-red-600 to-red-800 hover:opacity-90 text-white px-6 py-3 rounded-lg font-medium shadow-md inline-flex items-center">
            Solicitar Demo Personalizada
          </button>
        </div>
      </div>
    </section>
  );
};

export default SelectionDashboardSection;
