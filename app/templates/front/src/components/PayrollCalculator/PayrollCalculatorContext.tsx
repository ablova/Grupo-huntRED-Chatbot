import React, { createContext, useState, useContext, ReactNode } from 'react';

// Tipos
interface PayrollAddon {
  id: string;
  name: string;
  description: string;
  price: number; // USD por usuario/mes
  isPremium: boolean;
}

interface PayrollContextType {
  // Datos de la empresa
  employees: number;
  setEmployees: (value: number) => void;
  companySize: 'small' | 'medium' | 'large';
  dispersionsPerMonth: number;
  setDispersionsPerMonth: (value: number) => void;
  
  // Addons y configuración
  selectedAddons: string[];
  toggleAddon: (addonId: string) => void;
  
  // Cálculos
  getBasePrice: () => number;
  getDispersionFactor: () => number;
  calculateTotalCost: () => number;
  calculateCostPerEmployee: () => number;
  calculateAnnualSavings: () => number;
  
  // Lista de addons disponibles
  availableAddons: PayrollAddon[];
}

// Crear el contexto
const PayrollCalculatorContext = createContext<PayrollContextType | undefined>(undefined);

// Hook para usar el contexto
export const usePayrollCalculator = () => {
  const context = useContext(PayrollCalculatorContext);
  if (context === undefined) {
    throw new Error('usePayrollCalculator debe usarse dentro de PayrollCalculatorProvider');
  }
  return context;
};

// Provider component
export const PayrollCalculatorProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Estados
  const [employees, setEmployees] = useState<number>(50);
  const [dispersionsPerMonth, setDispersionsPerMonth] = useState<number>(2);
  const [selectedAddons, setSelectedAddons] = useState<string[]>(['nomina_basica']);
  
  // Lista de addons disponibles
  const availableAddons: PayrollAddon[] = [
    { 
      id: 'nomina_basica', 
      name: 'Nómina Básica', 
      description: 'Cálculos precisos y validados de nómina según legislación vigente',
      price: 0, // Incluido en el precio base
      isPremium: false
    },
    { 
      id: 'dispersion_automatica', 
      name: 'Dispersión Automática', 
      description: 'Pago automático integrado con los principales bancos',
      price: 0, // Se calcula como porcentaje del total
      isPremium: true
    },
    { 
      id: 'creditos_empleados', 
      name: 'Créditos para Empleados', 
      description: 'Opciones de crédito para empleados a través de alianzas con terceros',
      price: 3, // USD por usuario/mes
      isPremium: false
    },
    { 
      id: 'aura_learning', 
      name: 'AURA Learning & Career Path', 
      description: 'Plataforma de upskilling y desarrollo profesional personalizado',
      price: 5, // USD por usuario/mes
      isPremium: true
    },
    { 
      id: 'aura_ai', 
      name: 'AURA AI Coach', 
      description: 'Asistente de IA para desarrollo personal y profesional',
      price: 7, // USD por usuario/mes
      isPremium: true
    },
    { 
      id: 'nom_35', 
      name: 'NOM-35 Compliance', 
      description: 'Herramientas para cumplimiento y gestión de la NOM-35',
      price: 4, // USD por usuario/mes
      isPremium: false
    }
  ];
  
  // Determinar tamaño de empresa basado en número de empleados
  const companySize = employees < 50 ? 'small' : employees <= 200 ? 'medium' : 'large';
  
  // Precio base por empleado según tamaño de empresa (USD)
  const getBasePrice = () => {
    switch(companySize) {
      case 'small': return 32;
      case 'medium': return 30;
      case 'large': return 28;
      default: return 30;
    }
  };
  
  // Factor de dispersión - aumenta 5% por cada dispersión adicional después de 2
  const getDispersionFactor = () => {
    if (dispersionsPerMonth <= 2) return 1;
    return 1 + ((dispersionsPerMonth - 2) * 0.05);
  };
  
  // Toggle addon
  const toggleAddon = (addonId: string) => {
    if (addonId === 'nomina_basica') return; // Siempre incluido
    
    setSelectedAddons(prev => {
      if (prev.includes(addonId)) {
        return prev.filter(id => id !== addonId);
      } else {
        return [...prev, addonId];
      }
    });
  };
  
  // Calcular costo total
  const calculateTotalCost = () => {
    // Costo base (precio por empleado)
    let baseCost = employees * getBasePrice();
    
    // Costo de addons
    let addonCost = 0;
    selectedAddons.forEach(addonId => {
      const addon = availableAddons.find(a => a.id === addonId);
      if (!addon || addon.id === 'nomina_basica') return;
      
      // Si no es la dispersión automática, sumamos el costo por empleado
      if (addon.id !== 'dispersion_automatica') {
        addonCost += employees * addon.price;
      }
    });
    
    let total = baseCost + addonCost;
    
    // Si tiene dispersión automática, aplicamos el factor
    if (selectedAddons.includes('dispersion_automatica')) {
      total = total * getDispersionFactor();
    }
    
    return total;
  };
  
  // Costo por empleado al mes
  const calculateCostPerEmployee = () => {
    return calculateTotalCost() / employees;
  };
  
  // Estimación de ahorro anual
  const calculateAnnualSavings = () => {
    // Variables para el cálculo
    const hoursPerMonth = 15; // Horas dedicadas a nómina manualmente por mes
    const costPerHour = 400; // MXN
    const errorRate = 0.08; // 8% de errores en nómina manual
    const costPerError = 1500; // MXN
    
    // Ahorro en tiempo
    const timeSavings = hoursPerMonth * costPerHour * 12;
    
    // Ahorro en errores
    const errorSavings = employees * errorRate * costPerError * 12;
    
    // Factor de reducción basado en tamaño
    const savingsFactor = {
      small: 0.85,
      medium: 0.9,
      large: 0.95
    }[companySize];
    
    return (timeSavings + errorSavings) * savingsFactor / 20; // Convertir a USD (aprox)
  };
  
  const value = {
    // Estados y setters
    employees,
    setEmployees,
    companySize,
    dispersionsPerMonth,
    setDispersionsPerMonth,
    selectedAddons,
    toggleAddon,
    
    // Cálculos
    getBasePrice,
    getDispersionFactor,
    calculateTotalCost,
    calculateCostPerEmployee,
    calculateAnnualSavings,
    
    // Datos
    availableAddons
  };
  
  return (
    <PayrollCalculatorContext.Provider value={value}>
      {children}
    </PayrollCalculatorContext.Provider>
  );
};

export default PayrollCalculatorContext;
