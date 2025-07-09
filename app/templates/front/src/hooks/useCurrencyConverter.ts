import { useState, useEffect } from 'react';

// Tipo para opciones de moneda
export interface CurrencyOption {
  code: string;
  name: string;
  symbol: string;
}

// Valores fijos de respaldo (fallback)
const FIXED_EXCHANGE_RATES: Record<string, number> = {
  MXN: 1.0,      // Base: Peso Mexicano
  USD: 20.0,     // 1 USD = 20 MXN
  COL: 0.006,    // Redondeado a 1 decimal
  CAD: 15.0,     // 1 CAD = 15 MXN
  EUR: 22.0      // 1 EUR = 22 MXN
};

// Opciones de moneda disponibles
export const CURRENCY_OPTIONS: CurrencyOption[] = [
  { code: 'MXN', name: 'Peso Mexicano', symbol: '$' },
  { code: 'USD', name: 'Dólar Estadounidense', symbol: 'US$' },
  { code: 'COL', name: 'Peso Colombiano', symbol: 'COP$' },
  { code: 'CAD', name: 'Dólar Canadiense', symbol: 'C$' },
  { code: 'EUR', name: 'Euro', symbol: '€' }
];

/**
 * Hook personalizado para conversión de divisas
 * @param initialCurrency - Código de moneda inicial (default: 'MXN')
 * @returns - Objeto con estado y funciones de conversión
 */
export const useCurrencyConverter = (initialCurrency: string = 'MXN') => {
  const [currency, setCurrency] = useState<string>(initialCurrency);
  const [exchangeRates, setExchangeRates] = useState<Record<string, number>>(FIXED_EXCHANGE_RATES);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Función para convertir montos entre divisas
  const convertAmount = (amount: number, fromCurrency: string = 'MXN', toCurrency: string = currency): number => {
    if (!amount || isNaN(amount)) return 0;
    
    // Convertir primero a MXN (moneda base)
    const amountInMXN = fromCurrency === 'MXN' 
      ? amount 
      : amount * (1 / exchangeRates[fromCurrency]);
    
    // Luego convertir de MXN a la divisa destino
    return toCurrency === 'MXN' 
      ? amountInMXN 
      : amountInMXN * exchangeRates[toCurrency];
  };

  // Obtener tipos de cambio dinámicos (con API)
  useEffect(() => {
    const fetchExchangeRates = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Intentar obtener tipos de cambio de API
        // NOTA: En producción, aquí se conectaría con una API real de tipos de cambio
        // Ejemplo: const response = await fetch('https://api.exchangerate-api.com/v4/latest/MXN');
        
        // Por ahora usamos los valores fijos como fallback
        setExchangeRates(FIXED_EXCHANGE_RATES);
      } catch (err) {
        console.error('Error al obtener tipos de cambio:', err);
        setError('No se pudieron cargar los tipos de cambio. Usando valores predeterminados.');
        // Usar valores fijos como fallback
        setExchangeRates(FIXED_EXCHANGE_RATES);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchExchangeRates();
    
    // Actualizar cada 24 horas (opcional, para producción)
    const interval = setInterval(fetchExchangeRates, 24 * 60 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Formatear para mostrar
  const formatCurrency = (amount: number, currencyCode: string = currency): string => {
    if (!amount && amount !== 0) return '';
    
    const symbol = CURRENCY_OPTIONS.find(opt => opt.code === currencyCode)?.symbol || '';
    return `${symbol}${amount.toLocaleString('es-MX', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`;
  };

  return {
    currency,
    setCurrency,
    exchangeRates,
    convertAmount,
    formatCurrency,
    currencyOptions: CURRENCY_OPTIONS,
    isLoading,
    error
  };
};

export default useCurrencyConverter;
