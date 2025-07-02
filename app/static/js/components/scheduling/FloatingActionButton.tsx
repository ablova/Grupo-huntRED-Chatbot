import React, { useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Calendar, MessageSquare, X } from 'lucide-react';
import SchedulingWidget from './SchedulingWidget';

interface FloatingActionButtonProps {
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  buttonText?: string;
  buttonIcon?: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'accent';
}

const FloatingActionButton: React.FC<FloatingActionButtonProps> = ({
  position = 'bottom-right',
  buttonText = 'Agendar Demo',
  buttonIcon = <Calendar className="w-5 h-5" />,
  variant = 'primary'
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const positionClasses = {
    'bottom-right': 'bottom-6 right-6',
    'bottom-left': 'bottom-6 left-6',
    'top-right': 'top-6 right-6',
    'top-left': 'top-6 left-6',
  };

  const variantClasses = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-100 hover:bg-gray-200 text-gray-800',
    accent: 'bg-indigo-600 hover:bg-indigo-700 text-white',
  };

  return (
    <div className={`fixed z-50 ${positionClasses[position]}`}>
      <AnimatePresence>
        {isOpen && (
          <div className="absolute bottom-16 right-0 w-80">
            <SchedulingWidget 
              variant="floating"
              title="Agenda una Demo"
              description="Conecta con nuestro equipo para una demostración personalizada"
              buttonText="Agendar Ahora"
            />
          </div>
        )}
      </AnimatePresence>

      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center justify-center w-14 h-14 rounded-full shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200 ${variantClasses[variant]}`}
        aria-label={isOpen ? 'Cerrar formulario' : 'Abrir formulario de contacto'}
      >
        {isOpen ? (
          <X className="w-6 h-6" />
        ) : (
          buttonIcon || <Calendar className="w-6 h-6" />
        )}
      </button>
      
      {!isOpen && buttonText && (
        <span className="absolute top-1/2 right-16 transform -translate-y-1/2 bg-gray-900 text-white text-sm font-medium px-3 py-1.5 rounded-md shadow-lg whitespace-nowrap">
          {buttonText}
        </span>
      )}
    </div>
  );
};

export default FloatingActionButton;
