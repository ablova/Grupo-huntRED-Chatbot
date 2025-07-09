import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ChevronRight, Send, CheckCircle2, CalendarClock, Briefcase, Zap, MessageSquare } from 'lucide-react';
// Usando elementos HTML básicos con Tailwind en lugar de componentes UI personalizados

const CallToAction: React.FC = () => {
  const [formState, setFormState] = useState({
    name: '',
    email: '',
    company: '',
    interest: '',
    message: ''
  });
  
  const [formSubmitted, setFormSubmitted] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormState(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Aquí iría la lógica de envío del formulario
    console.log("Form submitted:", formState);
    setFormSubmitted(true);
    
    // Resetear el estado después de un tiempo
    setTimeout(() => {
      setFormSubmitted(false);
      setFormState({
        name: '',
        email: '',
        company: '',
        interest: '',
        message: ''
      });
    }, 3000);
  };

  // Opciones para el select de interés
  const interestOptions = [
    { value: "", label: "Selecciona tu interés" },
    { value: "recruitment", label: "Reclutamiento Especializado" },
    { value: "executive", label: "Búsqueda Ejecutiva" },
    { value: "payroll", label: "Administración de Nómina" },
    { value: "assessments", label: "Assessments y D.O." },
    { value: "tech", label: "Tecnologías de IA" },
    { value: "other", label: "Otro" },
  ];

  return (
    <div className="w-full h-full flex flex-col lg:flex-row py-12 px-4">
      {/* Left side - value proposition */}
      <motion.div 
        className="lg:w-1/2 lg:pr-10 mb-10 lg:mb-0"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.1 }}
      >
        <h2 className="text-4xl font-bold mb-6 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
          Transforma tu <span className="text-red-500">Gestión de Talento</span>
        </h2>
        
        <p className="text-gray-300 mb-8">
          Descubre cómo nuestro ecosistema integral puede optimizar todos tus procesos de talento,
          desde el reclutamiento y selección hasta la administración de nómina, con tecnologías
          propietarias que maximizan la eficiencia y reducen costos.
        </p>
        
        <div className="space-y-6">
          <div className="flex gap-4">
            <div className="bg-gradient-to-br from-red-600 to-red-400 rounded-full p-3 h-min">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-white text-lg font-medium mb-1">Decisiones más inteligentes</h3>
              <p className="text-gray-400 text-sm">
                Nuestras tecnologías de IA te ayudan a tomar mejores decisiones de contratación
                basadas en datos y análisis predictivos.
              </p>
            </div>
          </div>
          
          <div className="flex gap-4">
            <div className="bg-gradient-to-br from-blue-600 to-blue-400 rounded-full p-3 h-min">
              <CalendarClock className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-white text-lg font-medium mb-1">Ciclos más rápidos</h3>
              <p className="text-gray-400 text-sm">
                Reduce hasta un 40% el tiempo de tus procesos de selección y onboarding
                con nuestros sistemas automatizados.
              </p>
            </div>
          </div>
          
          <div className="flex gap-4">
            <div className="bg-gradient-to-br from-green-600 to-green-400 rounded-full p-3 h-min">
              <Briefcase className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-white text-lg font-medium mb-1">Resultados superiores</h3>
              <p className="text-gray-400 text-sm">
                Incrementa la retención y el desempeño de tu personal con nuestras
                soluciones de evaluación y desarrollo organizacional.
              </p>
            </div>
          </div>
        </div>
      </motion.div>
      
      {/* Right side - contact form */}
      <motion.div 
        className="lg:w-1/2 lg:pl-10"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.3 }}
      >
        <div className="bg-gray-900/50 backdrop-blur-md p-8 rounded-2xl border border-white/10 shadow-xl">
          {formSubmitted ? (
            <motion.div 
              className="text-center py-16 h-full flex flex-col items-center justify-center"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ type: "spring", stiffness: 100, damping: 10 }}
            >
              <CheckCircle2 className="w-16 h-16 text-green-500 mb-4" />
              <h3 className="text-2xl font-bold text-white mb-2">¡Mensaje enviado!</h3>
              <p className="text-gray-400">
                Gracias por tu interés. Nuestro equipo se pondrá en contacto contigo pronto.
              </p>
            </motion.div>
          ) : (
            <>
              <h3 className="text-2xl font-bold text-white mb-6">
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-red-500 to-red-300">
                  Contáctanos
                </span>
              </h3>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <input
                    type="text"
                    name="name"
                    placeholder="Nombre completo"
                    value={formState.name}
                    onChange={handleChange}
                    required
                    className="w-full p-2 rounded-md bg-gray-800/50 border border-gray-700 text-white placeholder:text-gray-500 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-all"
                  />
                </div>
                
                <div>
                  <input
                    type="email"
                    name="email"
                    placeholder="Correo electrónico"
                    value={formState.email}
                    onChange={handleChange}
                    required
                    className="w-full p-2 rounded-md bg-gray-800/50 border border-gray-700 text-white placeholder:text-gray-500 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-all"
                  />
                </div>
                
                <div>
                  <input
                    type="text"
                    name="company"
                    placeholder="Empresa"
                    value={formState.company}
                    onChange={handleChange}
                    required
                    className="w-full p-2 rounded-md bg-gray-800/50 border border-gray-700 text-white placeholder:text-gray-500 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-all"
                  />
                </div>
                
                <div>
                  <select
                    name="interest"
                    value={formState.interest}
                    onChange={handleChange}
                    required
                    className="w-full p-2 rounded-md bg-gray-800/50 border border-gray-700 text-white placeholder:text-gray-500 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-all"
                  >
                    {interestOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <textarea
                    name="message"
                    placeholder="Mensaje (opcional)"
                    value={formState.message}
                    onChange={handleChange}
                    className="w-full p-2 rounded-md bg-gray-800/50 border border-gray-700 text-white placeholder:text-gray-500 min-h-[100px] resize-none focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-all"
                  />
                </div>
                
                <div className="pt-2">
                  <button 
                    type="submit"
                    className="w-full flex items-center justify-center bg-gradient-to-r from-red-700 to-red-500 hover:from-red-600 hover:to-red-400 text-white py-3 rounded-md transition-all hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50"
                  >
                    <span>Enviar mensaje</span>
                    <Send className="ml-2 w-4 h-4" />
                  </button>
                </div>
                
                <p className="text-xs text-gray-500 text-center mt-4">
                  Al enviar este formulario, aceptas nuestra política de privacidad y términos de uso.
                </p>
              </form>
            </>
          )}
        </div>
        
        <div className="mt-6 flex justify-center">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-500">También puedes contactarnos directamente por WhatsApp o llamada</span>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default CallToAction;
