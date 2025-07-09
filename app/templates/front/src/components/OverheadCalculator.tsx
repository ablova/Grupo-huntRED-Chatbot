// app/templates/front/src/components/OverheadCalculator.tsx
import React, { useState, useMemo, useCallback } from 'react';
import { 
  Box, Typography, Button, Paper, FormControl, 
  Step, StepLabel, Stepper, Tooltip, IconButton, InputAdornment, TextField,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Select, MenuItem, 
  useMediaQuery
} from '@mui/material';
import { 
  ArrowBack as ArrowBackIcon, ArrowForward as ArrowForwardIcon, 
  GetApp as DownloadIcon, Link as LinkIcon, Save as SaveIcon, Info as InfoIcon 
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';

// Constantes para cálculos
const SALARIO_MINIMO_DIARIO = 248.93; // Valor 2024
const UMA = 108.57; // Valor 2024
const UMA_DIARIA = UMA; // Para compatibilidad con código existente
const DIAS_MES = 30.4; // Promedio de días por mes

// Tipos de cambio por defecto - Valores fijos para homologación en todo el sitio
const DEFAULT_EXCHANGE_RATES = {
  MXN: 1,      // Base: Peso Mexicano
  USD: 20,     // 1 USD = 20 MXN
  COL: 0.0059, // 1 COL = 0.0059 MXN (170 COL = 1 MXN)
  CAD: 15,     // 1 CAD = 15 MXN
  EUR: 22      // 1 EUR = 22 MXN
};

// Configuración de assessments
const ASSESSMENTS = [
  { id: 'talent', name: 'Talent Assessment', priceYear: 36000, category: 'recruiting' },
  { id: 'psych', name: 'Evaluación Psicométrica', priceYear: 24000, category: 'recruiting' },
  { id: 'tech', name: 'Evaluación Técnica', priceYear: 18000, category: 'recruiting' },
  { id: 'hogan', name: 'Perfil de Liderazgo', priceYear: 48000, category: 'development' },
  { id: 'nom35', name: 'Evaluación NOM-35', priceYear: 12000, category: 'compliance' },
  { id: 'sales', name: 'Evaluación de Ventas', priceYear: 30000, category: 'sales' },
];

// Estándar de dispersiones
const BASE_DISPERSIONS = 1; // Dispersiones incluidas en precio base
const DISPERSION_FEE = 0.05; // 5% adicional por dispersión extra

// Opciones de meses para seguro de vida
const MESES_SEGURO_VIDA = [12, 24, 36, 48, 72];

// Tabla ISR completa (tarifa mensual, artículo 96 LISR 2024)
const ISR_TABLE = [
  { limiteInferior: 0.01, limiteSuperior: 746.04, cuotaFija: 0, tasa: 1.92 },
  { limiteInferior: 746.05, limiteSuperior: 6332.05, cuotaFija: 14.32, tasa: 6.40 },
  { limiteInferior: 6332.06, limiteSuperior: 11128.01, cuotaFija: 371.83, tasa: 10.88 },
  { limiteInferior: 11128.02, limiteSuperior: 12935.82, cuotaFija: 893.63, tasa: 16.00 },
  { limiteInferior: 12935.83, limiteSuperior: 16495.40, cuotaFija: 1188.90, tasa: 17.92 },
  { limiteInferior: 16495.41, limiteSuperior: 32736.83, cuotaFija: 2196.37, tasa: 21.36 },
  { limiteInferior: 32736.84, limiteSuperior: 51011.02, cuotaFija: 7186.57, tasa: 23.52 },
  { limiteInferior: 51011.03, limiteSuperior: 97409.29, cuotaFija: 11481.09, tasa: 30.00 },
  { limiteInferior: 97409.30, limiteSuperior: 129879.03, cuotaFija: 25479.09, tasa: 32.00 },
  { limiteInferior: 129879.04, limiteSuperior: 389637.10, cuotaFija: 36617.92, tasa: 34.00 },
  { limiteInferior: 389637.11, limiteSuperior: Infinity, cuotaFija: 124823.38, tasa: 35.00 },
];

// Interfaces para tipado estricto
interface OverheadItem {
  id: string;
  name: string;
  type: 'fixed' | 'percentage' | 'days';
  value: number;
  category: 'benefits' | 'bonuses' | 'retentions_patronal' | 'retentions_obrera';
}

interface Employee {
  id: string;
  name: string;
  monthlySalary: number;
  overheadItems: OverheadItem[];
}

interface GroupOverhead {
  id: string;
  name: string;
  marketValue: number;
}

interface CurrencyOption {
  code: string;
  name: string;
  symbol: string;
}

interface Assessment {
  id: string;
  name: string;
  selected: boolean;
  priceMonth: number;
}

interface DispersionConfig {
  baseCount: number;
  additionalCount: number;
  feePercentage: number;
}

// Configuración inicial de ítems de overhead individuales
const defaultOverheadItems: OverheadItem[] = [
  { id: 'gmm', name: 'Seguro GMM', type: 'fixed', value: 5000, category: 'benefits' },
  { id: 'life', name: 'Seguro de Vida (meses asegurados)', type: 'fixed', value: 24, category: 'benefits' },
  { id: 'phone', name: 'Celular', type: 'fixed', value: 1000, category: 'benefits' },
  { id: 'vehicle', name: 'Vehículo', type: 'fixed', value: 3000, category: 'benefits' },
  { id: 'savings', name: 'Fondo de Ahorro', type: 'percentage', value: 5, category: 'benefits' },
  { id: 'vacation', name: 'Prima Vacacional (días)', type: 'days', value: 6, category: 'benefits' },
  { id: 'computer', name: 'Computadora', type: 'fixed', value: 2000, category: 'benefits' },
  { id: 'vouchers', name: 'Vales de Despensa', type: 'fixed', value: 1500, category: 'benefits' },
  { id: 'uniform', name: 'Uniformes', type: 'fixed', value: 500, category: 'benefits' },
  { id: 'training', name: 'Capacitación', type: 'fixed', value: 1000, category: 'benefits' },
  { id: 'afore_patronal', name: 'AFORE (Patronal)', type: 'percentage', value: 5.15, category: 'retentions_patronal' }, // 2% SAR + 3.15% cesantía/vejez
  { id: 'afore_obrera', name: 'AFORE (Obrera)', type: 'percentage', value: 1.125, category: 'retentions_obrera' },
  { id: 'bonus', name: 'Bono Anual', type: 'percentage', value: 20, category: 'bonuses' },
  { id: 'aguinaldo', name: 'Aguinaldo', type: 'days', value: 15, category: 'bonuses' },
  { id: 'imss_patronal', name: 'IMSS (Cuota Patronal)', type: 'percentage', value: 0, category: 'retentions_patronal' },
  { id: 'imss_obrera', name: 'IMSS (Cuota Obrera)', type: 'percentage', value: 0, category: 'retentions_obrera' },
  { id: 'infonavit', name: 'Infonavit (Aportación)', type: 'percentage', value: 5, category: 'retentions_patronal' },
  { id: 'isr', name: 'ISR (Retención)', type: 'percentage', value: 0, category: 'retentions_obrera' },
];

// Configuración inicial de ítems grupales
const defaultGroupOverhead: GroupOverhead[] = [
  { id: 'office', name: 'Renta de Oficina', marketValue: 50000 },
  { id: 'utilities', name: 'Servicios (Luz, Agua, etc.)', marketValue: 10000 },
  { id: 'software', name: 'Licencias de Software', marketValue: 20000 },
  { id: 'equipment', name: 'Equipo de Oficina', marketValue: 15000 },
  { id: 'maintenance', name: 'Mantenimiento', marketValue: 5000 },
  { id: 'subscriptions', name: 'Suscripciones Corporativas', marketValue: 10000 },
];

// Plantillas por industria
const industryTemplates = [
  { id: 'tech', name: 'Tecnología', baseSalary: 45000, benefits: ['gmm', 'computer', 'training', 'bonus', 'savings', 'afore_patronal', 'afore_obrera'] },
  { id: 'manufacturing', name: 'Manufactura', baseSalary: 25000, benefits: ['uniform', 'vouchers', 'aguinaldo', 'imss_patronal', 'imss_obrera'] },
  { id: 'services', name: 'Servicios', baseSalary: 30000, benefits: ['bonus', 'computer', 'vouchers', 'infonavit', 'isr'] },
];

// Componente principal
const OverheadCalculator: React.FC = () => {
  // Estado para el flujo secuencial (wizard)
  // Definir un tipo específico para los pasos del wizard para evitar errores de tipado
  type WizardStep = 0 | 1 | 2;
  const [activeStep, setActiveStep] = useState<WizardStep>(0);

  // Estado para divisas
  const [currency, setCurrency] = useState<string>('MXN');
  const [exchangeRates] = useState<Record<string, number>>(DEFAULT_EXCHANGE_RATES);
  
  // Estado para dispersiones
  const [dispersionConfig, setDispersionConfig] = useState<DispersionConfig>({
    baseCount: BASE_DISPERSIONS, // Por defecto 1 dispersión incluida
    additionalCount: 0,
    feePercentage: DISPERSION_FEE * 100 // 5%
  });
  
  // Estado para assessments
  const assessments = useMemo<Assessment[]>(() => ASSESSMENTS.map(item => ({
    id: item.id,
    name: item.name,
    selected: false,
    priceMonth: item.priceYear / 12 // Mensualizar el precio anual
  })), []);
  
  // Opciones de divisa
  const currencyOptions: CurrencyOption[] = [
    { code: 'MXN', name: 'Peso Mexicano', symbol: '$' },
    { code: 'USD', name: 'Dólar Estadounidense', symbol: 'US$' },
    { code: 'COL', name: 'Peso Colombiano', symbol: 'COP$' },
    { code: 'CAD', name: 'Dólar Canadiense', symbol: 'C$' },
    { code: 'EUR', name: 'Euro', symbol: '€' }
  ];

  const [employees, setEmployees] = useState<Employee[]>([
    {
      id: '1',
      name: 'Empleado 1',
      monthlySalary: 25000,
      overheadItems: [...defaultOverheadItems],
    },
  ]);
  const [groupOverhead, setGroupOverhead] = useState<GroupOverhead[]>(defaultGroupOverhead);
  // const [tabValue, setTabValue] = useState<number>(0);
  const [grossSalaryInput, setGrossSalaryInput] = useState<number | string>('');
  const [netSalaryInput, setNetSalaryInput] = useState<number | string>('');
  const [grossToNetResult, setGrossToNetResult] = useState<number | null>(null);
  const [netToGrossResult, setNetToGrossResult] = useState<number | null>(null);

  // Función para mostrar información sobre categorías
  const showInfo = (category: string) => {
    let message = '';
    switch(category) {
      case 'benefits':
        message = 'Los beneficios incluyen prestaciones no monetarias como seguros, vales, etc.';
        break;
      case 'bonuses':
        message = 'Los bonos son pagos variables adicionales al salario base.';
        break;
      case 'retentions':
        message = 'Las retenciones incluyen impuestos, cuotas y aportaciones obligatorias.';
        break;
      default:
        message = 'Selecciona una categoría para ver más información.';
    }
    setSnackbar({
      open: true,
      message,
      severity: 'success'
    });
  };

  // Manejo de mensajes de feedback
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Cálculo de IMSS (cuota patronal y obrera)
  const calculateIMSS = useCallback((monthlySalary: number): { patronal: number; obrera: number } => {
    if (monthlySalary <= 0) return { patronal: 0, obrera: 0 };
    const dailySalary = monthlySalary / DIAS_MES;
    const sbc = Math.min(dailySalary, 25 * UMA_DIARIA);

    // Cuota patronal
    const cuotaFija = 20.4 * DIAS_MES;
    const excedente = sbc > 3 * UMA_DIARIA ? (sbc - 3 * UMA_DIARIA) * 0.011 * DIAS_MES : 0;
    const prestacionesDinero = sbc * 0.007 * DIAS_MES;
    const riesgosTrabajo = sbc * 0.025 * DIAS_MES;
    const guarderias = sbc * 0.01 * DIAS_MES;
    const invalidezVida = sbc * 0.0175 * DIAS_MES;
    const enfermedadesMaternidad = sbc * 0.0104 * DIAS_MES;
    const patronal =
      cuotaFija +
      excedente +
      prestacionesDinero +
      riesgosTrabajo +
      guarderias +
      invalidezVida +
      enfermedadesMaternidad;

    // Cuota obrera
    const obreraExcedente = sbc > 3 * UMA_DIARIA ? (sbc - 3 * UMA_DIARIA) * 0.004 * DIAS_MES : 0;
    const obreraPrestaciones = sbc * 0.0025 * DIAS_MES;
    const obreraInvalidez = sbc * 0.00625 * DIAS_MES;
    const obreraEnfermedades = sbc * 0.00375 * DIAS_MES;
    const obrera = obreraExcedente + obreraPrestaciones + obreraInvalidez + obreraEnfermedades;

    return { patronal, obrera };
  }, []);

  // Cálculo de ISR (retención mensual)
  const calculateISR = useCallback((monthlySalary: number): number => {
    if (monthlySalary <= 0) return 0;
    const taxableIncome = monthlySalary;
    const bracket = ISR_TABLE.find(
      (b) => taxableIncome >= b.limiteInferior && taxableIncome <= b.limiteSuperior
    ) || ISR_TABLE[ISR_TABLE.length - 1];

    const base = taxableIncome - bracket.limiteInferior;
    const isr = bracket.cuotaFija + base * (bracket.tasa / 100);
    const subsidio = taxableIncome <= 1768.96 ? 407.06 : taxableIncome <= 7460.28 ? 406.83 : 0;

    return Math.max(isr - subsidio, 0);
  }, []);

  // Cálculo de AFORE (patronal y obrera)
  const calculateAFORE = useCallback((monthlySalary: number): { patronal: number; obrera: number } => {
    if (monthlySalary <= 0) return { patronal: 0, obrera: 0 };
    const sbc = Math.min(monthlySalary, 25 * UMA_DIARIA * DIAS_MES);
    const patronal = sbc * 0.0515; // 2% SAR + 3.15% cesantía/vejez
    const obrera = sbc * 0.01125; // 1.125% obrera
    return { patronal, obrera };
  }, []);

  // Cálculo de sueldo neto desde bruto
  const calculateNetSalary = useCallback((monthlySalary: number): number => {
    const isr = calculateISR(monthlySalary);
    const imssObrera = calculateIMSS(monthlySalary).obrera;
    const aforeObrera = calculateAFORE(monthlySalary).obrera;
    return monthlySalary - isr - imssObrera - aforeObrera;
  }, [calculateISR, calculateIMSS, calculateAFORE]);

  // Cálculo de sueldo bruto desde neto (método iterativo)
  const calculateGrossFromNet = useCallback((netSalary: number): number => {
    if (netSalary <= 0) return 0;
    let gross = netSalary;
    const maxIterations = 100;
    const tolerance = 0.01;

    for (let i = 0; i < maxIterations; i++) {
      const calculatedNet = calculateNetSalary(gross);
      if (Math.abs(calculatedNet - netSalary) < tolerance) {
        return gross;
      }
      const diff = netSalary - calculatedNet;
      gross += diff * 1.2;
      if (gross < 0) gross = netSalary;
    }
    return gross;
  }, [calculateNetSalary]);

  // Cálculo de overhead individual por empleado
  const calculateIndividualOverhead = useCallback((employee: Employee): number => {
    if (employee.monthlySalary <= 0) return 0;
    const annualSalary = employee.monthlySalary * 12;
    const dailySalary = employee.monthlySalary / DIAS_MES;

    return employee.overheadItems.reduce((total, item) => {
      let cost = 0;
      if (item.id === 'imss_patronal') {
        cost = calculateIMSS(employee.monthlySalary).patronal;
      } else if (item.id === 'imss_obrera') {
        cost = calculateIMSS(employee.monthlySalary).obrera;
      } else if (item.id === 'isr') {
        cost = calculateISR(employee.monthlySalary);
      } else if (item.id === 'afore_patronal') {
        cost = calculateAFORE(employee.monthlySalary).patronal;
      } else if (item.id === 'afore_obrera') {
        cost = calculateAFORE(employee.monthlySalary).obrera;
      } else if (item.type === 'fixed') {
        cost = item.value;
      } else if (item.type === 'percentage') {
        if (item.id === 'bonus') {
          cost = (annualSalary * item.value) / 100 / 12;
        } else if (item.id === 'infonavit') {
          cost = (Math.min(employee.monthlySalary, 25 * UMA_DIARIA * DIAS_MES) * item.value) / 100;
        } else {
          cost = (employee.monthlySalary * item.value) / 100;
        }
      } else if (item.type === 'days') {
        cost = dailySalary * item.value;
      }
      return total + cost;
    }, employee.monthlySalary);
  }, [calculateIMSS, calculateISR, calculateAFORE]);

  // Cálculo de overhead por categoría para el gráfico
  const chartData = useMemo(() => {
    if (!employees.length) return [];
    return employees.map((employee) => {
      const annualSalary = employee.monthlySalary * 12;
      const dailySalary = employee.monthlySalary / DIAS_MES;
      const netSalary = calculateNetSalary(employee.monthlySalary);

      const categories = {
        salary: employee.monthlySalary,
        benefits: 0,
        bonuses: 0,
        retentions_patronal: 0,
        retentions_obrera: 0,
      };

      employee.overheadItems.forEach((item) => {
        let cost = 0;
        if (item.id === 'imss_patronal') {
          cost = calculateIMSS(employee.monthlySalary).patronal;
        } else if (item.id === 'imss_obrera') {
          cost = calculateIMSS(employee.monthlySalary).obrera;
        } else if (item.id === 'isr') {
          cost = calculateISR(employee.monthlySalary);
        } else if (item.id === 'afore_patronal') {
          cost = calculateAFORE(employee.monthlySalary).patronal;
        } else if (item.id === 'afore_obrera') {
          cost = calculateAFORE(employee.monthlySalary).obrera;
        } else if (item.type === 'fixed') {
          cost = item.value;
        } else if (item.type === 'percentage') {
          if (item.id === 'bonus') {
            cost = (annualSalary * item.value) / 100 / 12;
          } else if (item.id === 'infonavit') {
            cost = (Math.min(employee.monthlySalary, 25 * UMA_DIARIA * DIAS_MES) * item.value) / 100;
          } else {
            cost = (employee.monthlySalary * item.value) / 100;
          }
        } else if (item.type === 'days') {
          cost = dailySalary * item.value;
        }
        categories[item.category] += cost;
      });

      return {
        name: employee.name,
        salary: categories.salary,
        benefits: categories.benefits,
        bonuses: categories.bonuses,
        retentions_patronal: categories.retentions_patronal,
        retentions_obrera: categories.retentions_obrera,
        netSalary,
      };
    });
  }, [employees, calculateNetSalary, calculateIMSS, calculateISR, calculateAFORE]);

  // Cálculo de overhead total individual
  const totalIndividualOverhead = useMemo(() => {
    return employees.reduce((total, emp) => total + calculateIndividualOverhead(emp), 0);
  }, [employees, calculateIndividualOverhead]);

  // Cálculo de overhead grupal
  const totalGroupOverhead = useMemo(() => {
    return groupOverhead.reduce((total, item) => total + Math.max(item.marketValue, 0), 0);
  }, [groupOverhead]);

  // Cálculo de overhead total
  // Calcular el costo adicional por dispersiones extras
  const dispersionsOverhead = useMemo(() => {
    if (dispersionConfig.additionalCount <= 0) return 0;
    
    const baseOverhead = totalIndividualOverhead + totalGroupOverhead;
    const dispersionsCost = baseOverhead * (dispersionConfig.feePercentage / 100) * dispersionConfig.additionalCount;
    
    return dispersionsCost;
  }, [totalIndividualOverhead, totalGroupOverhead, dispersionConfig]);

  // Calcular el overhead total incluyendo dispersiones adicionales
  const totalOverhead = useMemo(() => {
    const baseOverhead = totalIndividualOverhead + totalGroupOverhead;
    return baseOverhead + dispersionsOverhead;
  }, [totalIndividualOverhead, totalGroupOverhead, dispersionsOverhead]);

  // Manejo de cambio de pestañas (comentado por no usarse)
  // const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
  //   setTabValue(newValue);
  // }, []);

  // Agregar nuevo empleado
  const addEmployee = useCallback(() => {
    const newEmployee: Employee = {
      id: `emp${employees.length + 1}`,
      name: `Empleado ${employees.length + 1}`,
      monthlySalary: 30000,
      overheadItems: defaultOverheadItems,
    };
    setEmployees((prev) => [...prev, newEmployee]);
  }, [employees]);

  // Actualizar datos del empleado
  // Función especial para manejar actualización de salarios (evita problemas de formato)
  const handleSalaryChange = useCallback((id: string, value: string) => {
    // Convertir a número entero para evitar problemas con decimales
    const numericValue = value === '' ? SALARIO_MINIMO_DIARIO * DIAS_MES : parseFloat(value);
    const validValue = Math.max(numericValue, SALARIO_MINIMO_DIARIO * DIAS_MES);
    
    setEmployees((prev) =>
      prev.map((emp) =>
        emp.id === id ? { ...emp, monthlySalary: validValue } : emp
      )
    );
  }, []);
  
  const updateEmployee = useCallback((id: string, field: keyof Employee, value: any) => {
    // Si es salario, usar la función especializada
    if (field === 'monthlySalary') {
      handleSalaryChange(id, value);
      return;
    }
    
    setEmployees((prev) =>
      prev.map((emp) =>
        emp.id === id ? { ...emp, [field]: value } : emp
      )
    );
  }, [handleSalaryChange]);

  // Actualizar ítem de overhead individual
  const updateOverheadItem = useCallback((empId: string, itemId: string, field: keyof OverheadItem, value: any) => {
    setEmployees((prev) =>
      prev.map((emp) =>
        emp.id === empId
          ? {
              ...emp,
              overheadItems: emp.overheadItems.map((item) =>
                item.id === itemId
                  ? { ...item, [field]: field === 'value' ? Math.max(Number(value), 0) : value }
                  : item
              ),
            }
          : emp
      )
    );
  }, []);

  // Actualizar el valor de overhead grupal
  const updateGroupOverhead = useCallback((id: string, value: number) => {
    setGroupOverhead((prevItems: GroupOverhead[]) =>
      prevItems.map((item: GroupOverhead) =>
        item.id === id ? { ...item, marketValue: value } : item
      )
    );
  }, []);

  // Actualizar el valor de overhead individual para un empleado específico
  const handleOverheadItemChange = (employeeId: string, itemId: string, value: string | number) => {
    setEmployees(prevEmployees =>
      prevEmployees.map(employee =>
        employee.id === employeeId ? {
          ...employee,
          overheadItems: employee.overheadItems.map(item =>
            item.id === itemId ? { ...item, value: typeof value === 'string' ? parseFloat(value) || 0 : value } : item
          )
        } : employee
      )
    );
  };

  // Exportar a CSV
  const exportToCSV = useCallback(() => {
    const rows = ['Empleado,Salario Bruto,Beneficios,Bonos,Retenciones Patronales,Retenciones Obreras,Sueldo Neto,Costo Total'];
    chartData.forEach((employee) => {
      const emp = employees.find((e) => e.name === employee.name)!;
      const row = [
        employee.name,
        employee.salary.toFixed(2),
        employee.benefits.toFixed(2),
        employee.bonuses.toFixed(2),
        employee.retentions_patronal.toFixed(2),
        employee.retentions_obrera.toFixed(2),
        employee.netSalary.toFixed(2),
        calculateIndividualOverhead(emp).toFixed(2),
      ].join(',');
      rows.push(row);
    });
    const csvContent = rows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'overhead_calculadora.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setSnackbar({ open: true, message: 'Exportado a CSV con éxito', severity: 'success' });
  }, [chartData, employees, calculateIndividualOverhead]);

  // Guardar configuración
  const saveConfiguration = useCallback(() => {
    try {
      localStorage.setItem('overheadConfig', JSON.stringify({ employees, groupOverhead }));
      setSnackbar({ open: true, message: 'Configuración guardada con éxito', severity: 'success' });
    } catch (error) {
      setSnackbar({ open: true, message: 'Error al guardar configuración', severity: 'error' });
    }
  }, [employees, groupOverhead]);

  // Aplicar plantilla por industria
  const applyTemplate = useCallback((templateId: string) => {
    const template = industryTemplates.find((t) => t.id === templateId);
    if (!template) {
      setSnackbar({ open: true, message: 'Plantilla no encontrada', severity: 'error' });
      return;
    }
    setEmployees((prevEmployees) =>
      prevEmployees.map((emp, index) => ({
        ...emp,
        monthlySalary: template.baseSalary,
        overheadItems: defaultOverheadItems.map((item) => ({
          ...item,
          value: template.benefits.includes(item.id) ? item.value : item.type === 'percentage' ? 0 : 0,
        })),
      }))
    );
    setSnackbar({ open: true, message: `Plantilla ${template.name} aplicada`, severity: 'success' });
  }, []);

  // Manejo del convertidor bruto a neto
  const handleGrossToNet = useCallback(() => {
    const gross = Number(grossSalaryInput);
    if (gross >= SALARIO_MINIMO_DIARIO * DIAS_MES) {
      setGrossToNetResult(calculateNetSalary(gross));
      setSnackbar({ open: true, message: 'Cálculo bruto a neto exitoso', severity: 'success' });
    } else {
      setGrossToNetResult(null);
      setSnackbar({ open: true, message: 'El salario debe ser mayor al mínimo', severity: 'error' });
    }
  }, [grossSalaryInput, calculateNetSalary]);

  // Manejo del convertidor neto a bruto
  const handleNetToGross = useCallback(() => {
    const net = Number(netSalaryInput);
    if (net > 0) {
      setNetToGrossResult(calculateGrossFromNet(net));
      setSnackbar({ open: true, message: 'Cálculo neto a bruto exitoso', severity: 'success' });
    } else {
      setNetToGrossResult(null);
      setSnackbar({ open: true, message: 'El salario neto debe ser positivo', severity: 'error' });
    }
  }, [netSalaryInput, calculateGrossFromNet]);

  // Pasos del wizard (reordenados según feedback)
  const steps = [
    { label: 'Definir Gastos Grupales', description: 'Configure los gastos grupales para el cálculo' },
    { label: 'Definir Empleados', description: 'Añada y configure los empleados para el cálculo' },
    { label: 'Resultados', description: 'Visualice los resultados del cálculo de overhead' },
  ];

  // Funciones para navegar entre pasos
  const handleNext = () => {
    setActiveStep((prevStep) => {
      const nextStep = prevStep + 1;
      return nextStep <= 2 ? nextStep as WizardStep : prevStep;
    });
  };

  const handleBack = () => {
    setActiveStep((prevStep) => {
      const prevStepValue = prevStep - 1;
      return prevStepValue >= 0 ? prevStepValue as WizardStep : prevStep;
    });
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4">Calculadora de Overhead</Typography>
        <Box>
          <Tooltip title="Exportar a CSV">
            <IconButton onClick={exportToCSV} color="primary">
              <DownloadIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title={<span>Info sobre beneficios</span>} placement="top">
            <IconButton size="small" onClick={() => showInfo('benefits')}>
              <InfoIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Guardar configuración">
            <IconButton onClick={saveConfiguration} color="primary">
              <SaveIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Selector de divisa */}
      <Box sx={{ width: '100%', mb: 2, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
        <Typography variant="body2" sx={{ mr: 1 }}>Divisa:</Typography>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <Select
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            displayEmpty
            variant="outlined"
          >
            {currencyOptions.map((option) => (
              <MenuItem key={option.code} value={option.code}>
                {option.symbol} - {option.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Pasos del wizard */}
      <Box sx={{ width: '100%', mb: 4 }}>
        <Stepper activeStep={activeStep} alternativeLabel>
          {steps.map((step, index) => (
            <Step key={step.label} completed={activeStep > index}>
              <StepLabel>{step.label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        <Box sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
          <Typography variant="subtitle1">{steps[activeStep].description}</Typography>
        </Box>
      </Box>

      {/* Sección de plantillas por industria movida a botón auxiliar */}

      {/* Paso 1: Definir Empleados */}
      {Number(activeStep) === 1 && (
        <Box>
          <Typography variant="h6" gutterBottom>Ingrese los datos de sus empleados</Typography>
          <Typography variant="body2" sx={{ mb: 3 }}>
            Añada todos los empleados que desea incluir en el cálculo de overhead. Para cada empleado, 
            ingrese su nombre y salario bruto mensual.
          </Typography>

          <Button 
            variant="contained" 
            onClick={addEmployee} 
            sx={{ mb: 2 }}
            startIcon={<i className="fas fa-user-plus" />}
          >
            Agregar Empleado
          </Button>
          {employees.map((employee) => (
            <Box key={employee.id} sx={{ mb: 4, p: 2, border: '1px solid #ccc', borderRadius: 2 }}>
              <TextField
                label="Nombre del Empleado"
                value={employee.name}
                onChange={(e) => updateEmployee(employee.id, 'name', e.target.value)}
                sx={{ mb: 2, mr: 2, width: isMobile ? '100%' : 'auto' }}
              />
              <TextField
                label="Sueldo Bruto Mensual"
                type="text"
                value={employee.monthlySalary}
                onChange={(e) => {
                  // Solo permitir números
                  const value = e.target.value.replace(/[^0-9]/g, '');
                  if (value) {
                    const numValue = parseInt(value);
                    // Aplicar validación de salario mínimo
                    const validValue = Math.max(numValue, SALARIO_MINIMO_DIARIO * DIAS_MES);
                    updateEmployee(employee.id, 'monthlySalary', validValue);
                  }
                }}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <IconButton 
                          size="small"
                          onClick={() => {
                            // Incrementar en 100
                            const newValue = employee.monthlySalary + 100;
                            updateEmployee(employee.id, 'monthlySalary', newValue);
                          }}
                          sx={{ height: '20px', width: '20px', p: 0 }}
                        >
                          <span>▲</span>
                        </IconButton>
                        <IconButton 
                          size="small"
                          onClick={() => {
                            // Decrementar en 100 pero respetando el mínimo
                            const newValue = Math.max(employee.monthlySalary - 100, SALARIO_MINIMO_DIARIO * DIAS_MES);
                            updateEmployee(employee.id, 'monthlySalary', newValue);
                          }}
                          sx={{ height: '20px', width: '20px', p: 0 }}
                        >
                          ▼
                        </IconButton>
                      </Box>
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 2, width: isMobile ? '100%' : 'auto' }}
              />
              {/* Estos campos solo se muestran en el paso 1 */}
              {Number(activeStep) === 1 && (
                <Typography variant="h6">Información Básica del Empleado</Typography>
              )}
              {/* Esta tabla solo se muestra en el paso 2 */}
              {Number(activeStep) === 2 && (
                <>
                  <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>Beneficios y Gastos</Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    Configure los beneficios y gastos asociados a este empleado.
                  </Typography>
                <Table size={isMobile ? 'small' : 'medium'}>
                  <TableHead>
                    <TableRow>
                      <TableCell width="50%">Ítem</TableCell>
                      <TableCell width="25%">Tipo</TableCell>
                      <TableCell width="25%">Valor</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                  {employee.overheadItems.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <Tooltip title={<span>Categoría: {item.category}</span>}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Box 
                              sx={{ 
                                width: 10, 
                                height: 10, 
                                borderRadius: '50%', 
                                bgcolor: item.category === 'benefits' ? '#4caf50' : 
                                        item.category === 'bonuses' ? '#ff9800' : 
                                        item.category === 'retentions_patronal' ? '#f44336' : '#ab47bc',
                                mr: 1
                              }} 
                            />
                            {item.name}
                          </Box>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        {item.id.includes('imss') || item.id === 'isr' || item.id.includes('afore') ? (
                          'Calculado'
                        ) : (
                          <Select
                            fullWidth
                            size="small"
                            value={item.type}
                            onChange={(e) => updateOverheadItem(employee.id, item.id, 'type', e.target.value)}
                          >
                            <MenuItem value="fixed">Fijo</MenuItem>
                            <MenuItem value="percentage">Porcentaje</MenuItem>
                            <MenuItem value="days">Días</MenuItem>
                          </Select>
                        )}
                      </TableCell>
                      <TableCell>
                        {item.type === 'fixed' ? (
                          item.id === 'life' ? (
                            <FormControl fullWidth size="small">
                              <Select
                                value={item.value}
                                onChange={(e) => handleOverheadItemChange(employee.id, item.id, e.target.value)}
                              >
                                {MESES_SEGURO_VIDA.map((meses: number) => (
                                  <MenuItem key={meses} value={meses}>
                                    {meses} meses
                                  </MenuItem>
                                ))}
                              </Select>
                            </FormControl>
                          ) : (
                            <TextField
                              size="small"
                              type="number"
                              fullWidth
                              value={item.value}
                              onChange={(e) => handleOverheadItemChange(employee.id, item.id, e.target.value)}
                            />
                          )
                        ) : (
                          <TextField
                            size="small"
                            type="number"
                            fullWidth
                            value={item.value}
                            InputProps={{ endAdornment: '%' }}
                            onChange={(e) => handleOverheadItemChange(employee.id, item.id, e.target.value)}
                          />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {employee.overheadItems.find(item => item.id === 'life') && (
                <Box sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
                  <Tooltip title={<span>La cantidad de meses asegurados no significa el costo del seguro, solo el monto de la cobertura en función del salario.</span>}>
                    <InfoIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                  </Tooltip>
                  <Typography variant="caption" color="text.secondary">
                    Los meses asegurados indican la cobertura, no el costo mensual del seguro.
                    <Button
                      component="a"
                      href="https://www.interproteccion.com/" 
                      target="_blank"
                      startIcon={<LinkIcon fontSize="small" />}
                      size="small"
                      sx={{ ml: 1, textTransform: 'none' }}
                    >
                      Cotizar con Interprotección
                    </Button>
                  </Typography>
                </Box>
              )}
              </>
              )}
              {/* Esta información solo se muestra en el paso 3 (resultados) */}
              {Number(activeStep) === 2 && (
                <>
                <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>Resumen de Costos</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 1 }}>
                  <Box sx={{ flex: '1 1 calc(33.333% - 16px)', minWidth: '250px' }}>
                    <Paper elevation={2} sx={{ p: 2, height: '100%', bgcolor: 'background.paper', borderLeft: '4px solid #2196f3' }}>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>Salario Bruto Mensual</Typography>
                      <Typography variant="h5">${employee.monthlySalary.toFixed(2)}</Typography>
                    </Paper>
                  </Box>
                  <Box sx={{ flex: '1 1 calc(33.333% - 16px)', minWidth: '250px' }}>
                    <Paper elevation={2} sx={{ p: 2, height: '100%', bgcolor: 'background.paper', borderLeft: '4px solid #4caf50' }}>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>Sueldo Neto Mensual</Typography>
                      <Typography variant="h5">${calculateNetSalary(employee.monthlySalary).toFixed(2)}</Typography>
                    </Paper>
                  </Box>
                  <Box sx={{ flex: '1 1 calc(33.333% - 16px)', minWidth: '250px' }}>
                    <Paper elevation={2} sx={{ p: 2, height: '100%', bgcolor: 'background.paper', borderLeft: '4px solid #f44336' }}>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>Costo Total (Overhead)</Typography>
                      <Typography variant="h5">${calculateIndividualOverhead(employee).toFixed(2)}</Typography>
                    </Paper>
                  </Box>
                </Box>
                </>
              )}
            </Box>
          ))}
          <Typography variant="h6">
            Total Overhead Individual Mensual: ${totalIndividualOverhead.toFixed(2)}
          </Typography>
          
          {/* Botones de navegación wizard */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
            <Button
              disabled={activeStep === 0}
              onClick={handleBack}
              startIcon={<ArrowBackIcon />}
            >
              Anterior
            </Button>
            <Button
              variant="contained"
              onClick={handleNext}
              endIcon={<ArrowForwardIcon />}
              disabled={employees.length === 0}
            >
              {activeStep === steps.length - 1 ? 'Finalizar' : 'Siguiente'}
            </Button>
          </Box>
        </Box>
      )}

      {/* Paso 1: Gastos y Beneficios */}
      {Number(activeStep) === 0 && (
        <Box>
          <Typography variant="h6">Overhead Grupal (Valores de Mercado)</Typography>
          <Table size={isMobile ? 'small' : 'medium'}>
            <TableHead>
              <TableRow>
                <TableCell>Ítem</TableCell>
                <TableCell>Valor de Mercado</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {groupOverhead.map((item: GroupOverhead) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <Tooltip title={<span>{`Descripción: ${item.name}`}</span>}>
                      <span>{item.name}</span>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    <TextField
                      type="number"
                      value={item.marketValue}
                      onChange={(e) => updateGroupOverhead(item.id, parseFloat(e.target.value))}
                      inputProps={{ min: 0 }}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          
          {/* Configuración de dispersiones adicionales */}
          <Box sx={{ mt: 3, p: 2, border: '1px solid #e0e0e0', borderRadius: 1, bgcolor: 'background.paper' }}>
            <Typography variant="h6" gutterBottom>Configuración de Dispersiones</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Se incluye {dispersionConfig.baseCount} dispersión por defecto. Cada dispersión adicional tiene un costo del {dispersionConfig.feePercentage}% sobre el overhead total.
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Typography variant="body2" sx={{ mr: 2, minWidth: '180px' }}>Dispersiones adicionales:</Typography>
              <TextField
                type="number"
                size="small"
                value={dispersionConfig.additionalCount}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 0;
                  const validValue = Math.max(value, 0); // No permitir valores negativos
                  setDispersionConfig(prev => ({
                    ...prev,
                    additionalCount: validValue
                  }));
                }}
                InputProps={{
                  inputProps: { min: 0 }
                }}
                sx={{ width: '100px' }}
              />
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Typography variant="body2" sx={{ mr: 2, minWidth: '180px' }}>Costo por dispersión adicional:</Typography>
              <Typography variant="body2" color="primary">
                {dispersionConfig.feePercentage}% del overhead total
              </Typography>
            </Box>
            
            {dispersionConfig.additionalCount > 0 && (
              <Box sx={{ mt: 2, p: 1, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                <Typography variant="body2">
                  Costo estimado por dispersiones adicionales: 
                  <Typography component="span" fontWeight="bold" color="primary">
                    ${(totalGroupOverhead * dispersionConfig.additionalCount * (dispersionConfig.feePercentage / 100)).toFixed(2)}
                  </Typography>
                </Typography>
              </Box>
            )}
          </Box>
          
          <Typography variant="h6" sx={{ mt: 2 }}>
            Total Overhead Grupal Mensual: ${totalGroupOverhead.toFixed(2)}
          </Typography>
          
          {/* Botones de navegación para el paso 2 */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
            <Button
              variant="outlined"
              startIcon={<ArrowBackIcon />}
              onClick={handleBack}
            >
              Atrás
            </Button>
            <Button
              variant="contained"
              endIcon={<ArrowForwardIcon />}
              onClick={handleNext}
            >
              Siguiente
            </Button>
          </Box>
        </Box>
      )}

      {/* Paso 3: Resultados */}
      {Number(activeStep) === 2 && (
        <Box>
          <Typography variant="h5">Resumen de Overhead</Typography>
          <Typography variant="subtitle1">
            Total Overhead Individual Mensual: ${totalIndividualOverhead.toFixed(2)}
          </Typography>
          <Typography variant="subtitle1">
            Total Overhead Grupal Mensual: ${totalGroupOverhead.toFixed(2)}
          </Typography>
          <Typography variant="h6" sx={{ mt: 2 }}>
            Total Overhead Empresa Mensual: ${totalOverhead.toFixed(2)}
          </Typography>

          <Typography variant="h6" sx={{ mt: 4, mb: 2 }}>
            Desglose por Empleado
          </Typography>
          <Table size={isMobile ? 'small' : 'medium'}>
            <TableHead>
              <TableRow>
                <TableCell>Empleado</TableCell>
                <TableCell align="right">Salario Bruto</TableCell>
                <TableCell align="right">Beneficios</TableCell>
                <TableCell align="right">Bonos</TableCell>
                <TableCell align="right">Ret. Patronales</TableCell>
                <TableCell align="right">Ret. Obreras</TableCell>
                <TableCell align="right">Sueldo Neto</TableCell>
                <TableCell align="right">Costo Total</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {chartData.map((employee) => (
                <TableRow key={employee.name} hover>
                  <TableCell>{employee.name}</TableCell>
                  <TableCell align="right">${employee.salary.toFixed(2)}</TableCell>
                  <TableCell align="right">${employee.benefits.toFixed(2)}</TableCell>
                  <TableCell align="right">${employee.bonuses.toFixed(2)}</TableCell>
                  <TableCell align="right">${employee.retentions_patronal.toFixed(2)}</TableCell>
                  <TableCell align="right">${employee.retentions_obrera.toFixed(2)}</TableCell>
                  <TableCell align="right">${employee.netSalary.toFixed(2)}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold' }}>${calculateIndividualOverhead(employees.find((e) => e.name === employee.name)!).toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <Typography variant="h6" sx={{ mt: 4, mb: 2 }}>
            Distribución de Costos por Empleado
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: 2 }}>
            {chartData.map((employee, index) => (
              <Box key={index}>
                <Typography variant="subtitle1" align="center">
                  {employee.name}
                </Typography>
                <Box sx={{ height: 300, width: '100%', border: '1px solid rgba(0,0,0,0.1)', borderRadius: 2, overflow: 'hidden' }}>
                  <Box sx={{ 
                    height: '100%', 
                    display: 'flex', 
                    flexDirection: 'column',
                    position: 'relative'
                  }}>
                    {/* Gráfico de pie implementado con CSS */}
                    <Box sx={{ 
                      flex: 1, 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      position: 'relative',
                      padding: 2
                    }}>
                      <Box sx={{ 
                        width: 180, 
                        height: 180, 
                        position: 'relative', 
                        borderRadius: '50%', 
                        overflow: 'hidden',
                        boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
                      }}>
                        {/* Segmentos del gráfico circular */}
                        {/* Calculamos los ángulos según proporciones */}
                        {(() => {
                          const values = [
                            employee.salary,
                            employee.benefits,
                            employee.bonuses,
                            employee.retentions_patronal,
                            employee.retentions_obrera
                          ];
                          const total = values.reduce((a, b) => a + b, 0);
                          const colors = ["#1976d2", "#4caf50", "#ff9800", "#f44336", "#ab47bc"];
                          // Definimos explícitamente el tipo para evitar el error any[]
                          const segments: React.ReactNode[] = [];
                          
                          let cumulativePercentage = 0;
                          
                          values.forEach((value, index) => {
                            const percentage = value / total * 100;
                            if (percentage > 0) {
                              segments.push(
                                <Box 
                                  key={index}
                                  sx={{
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                    width: '100%',
                                    height: '100%',
                                    background: `conic-gradient(
                                      transparent ${cumulativePercentage}%,
                                      ${colors[index]} ${cumulativePercentage}%,
                                      ${colors[index]} ${cumulativePercentage + percentage}%,
                                      transparent ${cumulativePercentage + percentage}%
                                    )`
                                  }}
                                />
                              );
                              cumulativePercentage += percentage;
                            }
                          });
                          
                          return segments;
                        })()} 
                      </Box>
                      <Box sx={{ position: 'absolute', left: 0, right: 0, bottom: 16, textAlign: 'center' }}>
                        <Typography variant="caption" sx={{ fontWeight: 'medium' }}>
                          Total: ${calculateIndividualOverhead(employees.find(e => e.name === employee.name)!).toFixed(2)}
                        </Typography>
                      </Box>
                    </Box>
                    
                    {/* Leyenda */}
                    <Box sx={{ 
                      p: 2,
                      bgcolor: 'rgba(0,0,0,0.03)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 0.5
                    }}>
                      <Typography variant="subtitle2" align="center" gutterBottom>
                        {employee.name} - Distribución de Costos
                      </Typography>
                      <Box sx={{ 
                        display: 'grid', 
                        gridTemplateColumns: 'repeat(2, 1fr)', 
                        gap: 1
                      }}>
                        {[
                          {label: "Salario Bruto", value: employee.salary, color: "#1976d2"},
                          {label: "Beneficios", value: employee.benefits, color: "#4caf50"},
                          {label: "Bonos", value: employee.bonuses, color: "#ff9800"},
                          {label: "Ret. Patronales", value: employee.retentions_patronal, color: "#f44336"},
                          {label: "Ret. Obreras", value: employee.retentions_obrera, color: "#ab47bc"}
                        ].filter(item => item.value > 0).map((item, i) => (
                          <Box key={i} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <Box 
                                sx={{ 
                                  width: 10, 
                                  height: 10, 
                                  borderRadius: '50%', 
                                  bgcolor: item.color,
                                  mr: 0.5 
                                }} 
                              />
                              <Typography variant="caption">{item.label}</Typography>
                            </Box>
                            <Typography variant="caption" sx={{ fontWeight: 'medium' }}>
                              ${item.value.toFixed(2)}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                      <Typography variant="caption" sx={{ alignSelf: 'flex-end', mt: 1 }}>
                        Sueldo Neto: ${employee.netSalary.toFixed(2)}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </Box>
            ))}
          </Box>
        </Box>
      )}

      {/* Convertidor (permanece siempre visible en el paso 3) */}
      {Number(activeStep) === 2 && (
        <Box>
          <Typography variant="h5" gutterBottom>
            Convertidor de Salario
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: '250px' }}>
              <Typography variant="h6">Bruto a Neto</Typography>
              <FormControl fullWidth sx={{ mt: 2, mb: 2 }}>
                <TextField
                  label="Sueldo Bruto Mensual"
                  type="number"
                  value={grossSalaryInput}
                  onChange={(e) => {
                    // Permitimos entrada manual directa
                    const numVal = Number(e.target.value);
                    setGrossSalaryInput(numVal || 0);
                  }}
                  inputProps={{
                    min: 0,
                    step: 100, // Establecemos incremento de 100 MXN
                  }}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">MXN</InputAdornment>
                    ),
                  }}
                  sx={{ mb: 2, width: isMobile ? '100%' : 'auto' }}
                />
              </FormControl>
              <Button variant="contained" onClick={handleGrossToNet} sx={{ mb: 2 }}>
                Calcular Neto
              </Button>
              {grossToNetResult !== null && (
                <Typography variant="subtitle1">
                  Sueldo Neto Mensual: ${grossToNetResult.toFixed(2)}
                </Typography>
              )}
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: '250px' }}>
              <Typography variant="h6">Neto a Bruto</Typography>
              <FormControl fullWidth sx={{ mt: 2, mb: 2 }}>
                <TextField
                  label="Salario Neto Mensual"
                  type="number"
                  value={netSalaryInput}
                  onChange={(e) => setNetSalaryInput(Number(e.target.value))}
                  inputProps={{ min: 0 }}
                />
              </FormControl>
              <Button variant="contained" onClick={handleNetToGross} sx={{ mb: 2 }}>
                Calcular Bruto
              </Button>
              {netToGrossResult !== null && (
                <Typography variant="subtitle1">
                  Sueldo Bruto Mensual: ${netToGrossResult.toFixed(2)}
                </Typography>
              )}
            </Box>
          </Box>
        </Box>
      )}

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default OverheadCalculator;
