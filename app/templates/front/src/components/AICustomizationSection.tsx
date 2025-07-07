import React from 'react';
import { Brain } from 'lucide-react';

// Componente simplificado para diagnóstico
const AICustomizationSection = () => {
  return (
    <section className="py-20 bg-muted/20" data-section="ai-customization">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center p-2 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">
            <Brain className="h-5 w-5 text-blue-600" />
          </div>
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Personalización de <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">IA y ML</span>
          </h2>
          <p className="text-lg text-muted-foreground">
            Componente simplificado para diagnóstico
          </p>
        </div>
      </div>
    </section>
  );
};

export default AICustomizationSection;
