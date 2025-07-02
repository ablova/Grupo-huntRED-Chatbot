import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, X, Clock, User, Mail, Phone, Video, ArrowRight, Check } from 'lucide-react';

interface SchedulingWidgetProps {
  variant?: 'default' | 'compact' | 'floating';
  title?: string;
  description?: string;
  buttonText?: string;
  features?: string[];
  calendarLink?: string;
}

const SchedulingWidget: React.FC<SchedulingWidgetProps> = ({
  variant = 'default',
  title = "Agenda una Demo con nuestro CEO",
  description = "Conecta directamente con nuestra dirección ejecutiva para discutir cómo podemos transformar tu negocio con IA",
  buttonText = "Agendar con CEO",
  features = [
    "Contacto Directo",
    "C-Level",
    "Atención ejecutiva",
    "Demo Live",
    "Productos reales",
    "ROI",
    "Análisis incluido"
  ],
  calendarLink = "https://calendly.com/grupohuntred/30min"
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    message: ''
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      // Here you would typically make an API call to your backend
      await new Promise(resolve => setTimeout(resolve, 1500));
      setIsSuccess(true);
      
      // Redirect to Calendly after a short delay
      setTimeout(() => {
        window.open(calendarLink, '_blank');
      }, 1000);
      
    } catch (error) {
      console.error('Error submitting form:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Variants for different widget styles
  const variants = {
    default: {
      container: "max-w-4xl mx-auto p-6 md:p-8 bg-white rounded-xl shadow-lg",
      title: "text-2xl md:text-3xl font-bold text-gray-900 mb-3",
      description: "text-gray-600 mb-6",
      features: "grid grid-cols-2 md:grid-cols-3 gap-3 mb-8",
      feature: "flex items-center text-sm text-gray-700",
      button: "px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
    },
    compact: {
      container: "p-4 bg-white rounded-lg shadow",
      title: "text-lg font-semibold text-gray-900",
      description: "text-sm text-gray-600",
      features: "hidden",
      feature: "",
      button: "px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition-colors"
    },
    floating: {
      container: "fixed bottom-6 right-6 max-w-sm bg-white rounded-xl shadow-xl overflow-hidden z-50",
      title: "text-lg font-semibold text-gray-900 px-6 pt-6",
      description: "text-sm text-gray-600 px-6",
      features: "hidden",
      feature: "",
      button: "w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors"
    }
  };

  const currentVariant = variants[variant] || variants.default;

  return (
    <>
      {variant === 'floating' ? (
        <div className={currentVariant.container}>
          <div className="relative">
            <button 
              onClick={() => setIsOpen(!isOpen)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
            >
              <X size={20} />
            </button>
            
            <h3 className={currentVariant.title}>{title}</h3>
            <p className={currentVariant.description}>{description}</p>
            
            <button 
              onClick={() => setIsOpen(!isOpen)}
              className={currentVariant.button}
            >
              {buttonText}
            </button>
          </div>

          <AnimatePresence>
            {isOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <div className="p-6 border-t border-gray-100">
                  {isSuccess ? (
                    <div className="text-center py-8">
                      <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Check className="w-6 h-6 text-green-600" />
                      </div>
                      <h4 className="text-lg font-medium text-gray-900 mb-2">¡Listo!</h4>
                      <p className="text-gray-600 mb-6">Serás redirigido a Calendly para seleccionar un horario.</p>
                      <button
                        onClick={() => window.open(calendarLink, '_blank')}
                        className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800"
                      >
                        Abrir Calendly
                      </button>
                    </div>
                  ) : (
                    <form onSubmit={handleSubmit} className="space-y-4">
                      <div>
                        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                          Nombre completo
                        </label>
                        <div className="relative">
                          <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                          <input
                            type="text"
                            id="name"
                            name="name"
                            required
                            value={formData.name}
                            onChange={handleInputChange}
                            className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Tu nombre"
                          />
                        </div>
                      </div>

                      <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                          Correo electrónico
                        </label>
                        <div className="relative">
                          <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                          <input
                            type="email"
                            id="email"
                            name="email"
                            required
                            value={formData.email}
                            onChange={handleInputChange}
                            className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="tucorreo@ejemplo.com"
                          />
                        </div>
                      </div>

                      <div>
                        <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                          Teléfono
                        </label>
                        <div className="relative">
                          <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                          <input
                            type="tel"
                            id="phone"
                            name="phone"
                            value={formData.phone}
                            onChange={handleInputChange}
                            className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="+52 55 1234 5678"
                          />
                        </div>
                      </div>

                      <div>
                        <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-1">
                          Empresa
                        </label>
                        <input
                          type="text"
                          id="company"
                          name="company"
                          value={formData.company}
                          onChange={handleInputChange}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Nombre de tu empresa"
                        />
                      </div>

                      <div>
                        <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1">
                          ¿En qué podemos ayudarte?
                        </label>
                        <textarea
                          id="message"
                          name="message"
                          rows={3}
                          value={formData.message}
                          onChange={handleInputChange}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Cuéntanos sobre tus necesidades"
                        ></textarea>
                      </div>

                      <button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                      >
                        {isSubmitting ? (
                          <>
                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Procesando...
                          </>
                        ) : (
                          <>
                            <Calendar className="w-4 h-4 mr-2" />
                            {buttonText}
                          </>
                        )}
                      </button>
                    </form>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ) : (
        <div className={currentVariant.container}>
          <div className="md:flex md:items-center md:justify-between">
            <div className="md:w-2/3">
              <h3 className={currentVariant.title}>{title}</h3>
              <p className={currentVariant.description}>{description}</p>
              
              <div className={currentVariant.features}>
                {features.map((feature, index) => (
                  <div key={index} className={currentVariant.feature}>
                    <Check className="w-4 h-4 text-green-500 mr-2" />
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
              
              <button 
                onClick={() => window.open(calendarLink, '_blank')}
                className={`${currentVariant.button} flex items-center justify-center`}
              >
                <Calendar className="w-4 h-4 mr-2" />
                {buttonText}
              </button>
            </div>
            
            <div className="hidden md:block md:w-1/3">
              <div className="relative">
                <div className="absolute -top-4 -left-4 w-32 h-32 bg-blue-100 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
                <div className="absolute -bottom-4 -right-4 w-32 h-32 bg-purple-100 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
                <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-32 h-32 bg-pink-100 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>
                
                <div className="relative p-6 bg-white rounded-xl shadow-inner border border-gray-100">
                  <div className="flex items-center justify-center w-16 h-16 mx-auto mb-4 rounded-full bg-blue-50">
                    <Video className="w-8 h-8 text-blue-600" />
                  </div>
                  <h4 className="text-center font-medium text-gray-900 mb-2">Reunión por Google Meet</h4>
                  <p className="text-center text-sm text-gray-500">30 minutos • Sin costo</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SchedulingWidget;
