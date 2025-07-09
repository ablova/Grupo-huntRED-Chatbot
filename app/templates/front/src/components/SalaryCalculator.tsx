// app/templates/front/src/components/SalaryCalculator.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Grid,
  Divider,
  Tooltip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Snackbar,
  Alert,
} from '@mui/material';
import { Info as InfoIcon, Download as DownloadIcon } from '@mui/icons-material';

// Constantes fiscales (México 2025)
const SALARIO_MINIMO_DIARIO = 248.93;
const UMA_DIARIA = 108.57;
const DIAS_MES = 30;

// Tabla ISR completa (tarifa mensual, artículo 96 LISR 2025)
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

const SalaryCalculator: React.FC = () => {
  // Estados
  const [calculationType, setCalculationType] = useState<'brutoToNeto' | 'netoToBruto'>('brutoToNeto');
  const [grossSalary, setGrossSalary] = useState<number | string>(30000);
  const [netSalary, setNetSalary] = useState<number>(0);
  const [targetNetSalary, setTargetNetSalary] = useState<number | string>(25000);
  const [calculatedGrossSalary, setCalculatedGrossSalary] = useState<number>(0);
  const [deductions, setDeductions] = useState<{ isr: number; imss: number; afore: number; total: number }>({
    isr: 0,
    imss: 0,
    afore: 0,
    total: 0,
  });
  const [historyItems, setHistoryItems] = useState<
    Array<{ gross: number; net: number; deductions: { isr: number; imss: number; afore: number; total: number }; timestamp: Date }>
  >([]);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  // Cálculo de IMSS (cuota obrera)
  const calculateIMSS = useCallback((monthlySalary: number): number => {
    if (monthlySalary <= 0) return 0;
    const dailySalary = monthlySalary / DIAS_MES;
    const sbc = Math.min(dailySalary, 25 * UMA_DIARIA);
    const obreraExcedente = sbc > 3 * UMA_DIARIA ? (sbc - 3 * UMA_DIARIA) * 0.004 * DIAS_MES : 0;
    const obreraPrestaciones = sbc * 0.0025 * DIAS_MES;
    const obreraInvalidez = sbc * 0.00625 * DIAS_MES;
    const obreraEnfermedades = sbc * 0.00375 * DIAS_MES;
    return obreraExcedente + obreraPrestaciones + obreraInvalidez + obreraEnfermedades;
  }, []);

  // Cálculo de AFORE (obrera)
  const calculateAFORE = useCallback((monthlySalary: number): number => {
    if (monthlySalary <= 0) return 0;
    const sbc = Math.min(monthlySalary, 25 * UMA_DIARIA * DIAS_MES);
    return sbc * 0.01125; // 1.125% obrera
  }, []);

  // Cálculo de ISR
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

  // Cálculo de salario neto
  const calculateNetSalary = useCallback(
    (gross: number) => {
      if (gross <= 0) {
        setSnackbar({ open: true, message: 'El salario bruto debe ser positivo', severity: 'error' });
        return 0;
      }
      const imss = calculateIMSS(gross);
      const isr = calculateISR(gross);
      const afore = calculateAFORE(gross);
      const totalDeductions = imss + isr + afore;
      const net = gross - totalDeductions;
      setNetSalary(net);
      setDeductions({ imss, isr, afore, total: totalDeductions });
      return net;
    },
    [calculateIMSS, calculateISR, calculateAFORE]
  );

  // Cálculo de salario bruto a partir del neto (método iterativo)
  const calculateGrossSalary = useCallback(
    (targetNet: number) => {
      if (targetNet <= 0) {
        setSnackbar({ open: true, message: 'El salario neto debe ser positivo', severity: 'error' });
        return 0;
      }
      let low = targetNet;
      let high = targetNet * 2;
      let mid = 0;
      let calculatedNet = 0;
      const epsilon = 1;
      for (let i = 0; i < 20; i++) {
        mid = (low + high) / 2;
        calculatedNet = mid - calculateIMSS(mid) - calculateISR(mid) - calculateAFORE(mid);
        if (Math.abs(calculatedNet - targetNet) < epsilon) break;
        if (calculatedNet > targetNet) high = mid;
        else low = mid;
      }
      const imss = calculateIMSS(mid);
      const isr = calculateISR(mid);
      const afore = calculateAFORE(mid);
      setCalculatedGrossSalary(mid);
      setDeductions({ imss, isr, afore, total: imss + isr + afore });
      return mid;
    },
    [calculateIMSS, calculateISR, calculateAFORE]
  );

  // Handler para calcular
  const handleCalculate = useCallback(() => {
    const newHistoryItem = {
      gross: calculationType === 'brutoToNeto' ? Number(grossSalary) : calculatedGrossSalary,
      net: calculationType === 'brutoToNeto' ? netSalary : Number(targetNetSalary),
      deductions: { ...deductions },
      timestamp: new Date(),
    };
    setHistoryItems((prev) => [newHistoryItem, ...prev.slice(0, 49)]); // Límite de 50 entradas
    setSnackbar({ open: true, message: 'Cálculo realizado con éxito', severity: 'success' });
  }, [calculationType, grossSalary, netSalary, targetNetSalary, calculatedGrossSalary, deductions]);

  // Exportar historial a CSV
  const exportHistoryToCSV = useCallback(() => {
    const rows = ['Fecha,Tipo,Salario Bruto,Salario Neto,ISR,IMSS,AFORE'];
    historyItems.forEach((item) => {
      const row = [
        item.timestamp.toLocaleString('es-MX'),
        item.gross > item.net ? 'Bruto → Neto' : 'Neto → Bruto',
        item.gross.toFixed(2),
        item.net.toFixed(2),
        item.deductions.isr.toFixed(2),
        item.deductions.imss.toFixed(2),
        item.deductions.afore.toFixed(2),
      ].join(',');
      rows.push(row);
    });
    const csvContent = rows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'salary_calculator_history.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setSnackbar({ open: true, message: 'Historial exportado a CSV', severity: 'success' });
  }, [historyItems]);

  // Efecto inicial
  useEffect(() => {
    if (calculationType === 'brutoToNeto') {
      calculateNetSalary(Number(grossSalary));
    } else {
      calculateGrossSalary(Number(targetNetSalary));
    }
  }, [calculationType, grossSalary, targetNetSalary, calculateNetSalary, calculateGrossSalary]);

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom align="center">
        Calculadora de Salario Bruto-Neto
      </Typography>

      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Tipo de Cálculo</InputLabel>
              <Select
                value={calculationType}
                onChange={(e) => setCalculationType(e.target.value as 'brutoToNeto' | 'netoToBruto')}
                label="Tipo de Cálculo"
              >
                <MenuItem value="brutoToNeto">De Bruto a Neto</MenuItem>
                <MenuItem value="netoToBruto">De Neto a Bruto</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {calculationType === 'brutoToNeto' ? (
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Salario Bruto Mensual"
                type="number"
                InputProps={{ startAdornment: '$' }}
                value={grossSalary}
                onChange={(e) => setGrossSalary(e.target.value)}
                inputProps={{ min: SALARIO_MINIMO_DIARIO * DIAS_MES }}
              />
            </Grid>
          ) : (
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Salario Neto Deseado"
                type="number"
                InputProps={{ startAdornment: '$' }}
                value={targetNetSalary}
                onChange={(e) => setTargetNetSalary(e.target.value)}
                inputProps={{ min: 0 }}
              />
            </Grid>
          )}

          <Grid item xs={12}>
            <Button variant="contained" color="primary" fullWidth size="large" onClick={handleCalculate}>
              Calcular
            </Button>
          </Grid>
        </Grid>
      </Paper>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Resultados
              <Tooltip title="Cálculos basados en UMA, ISR y cuotas IMSS/AFORE 2025">
                <IconButton size="small" sx={{ ml: 1 }}>
                  <InfoIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {calculationType === 'brutoToNeto' ? (
              <Box>
                <Typography variant="subtitle1">Salario Bruto: ${Number(grossSalary).toFixed(2)}</Typography>
                <Typography variant="subtitle1" sx={{ mt: 1 }}>
                  <span style={{ color: 'red' }}>- ISR: ${deductions.isr.toFixed(2)}</span>
                </Typography>
                <Typography variant="subtitle1" sx={{ mt: 1 }}>
                  <span style={{ color: 'red' }}>- IMSS: ${deductions.imss.toFixed(2)}</span>
                </Typography>
                <Typography variant="subtitle1" sx={{ mt: 1 }}>
                  <span style={{ color: 'red' }}>- AFORE: ${deductions.afore.toFixed(2)}</span>
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Typography variant="h6" sx={{ mt: 1, fontWeight: 'bold' }}>
                  Salario Neto: ${netSalary.toFixed(2)}
                </Typography>
              </Box>
            ) : (
              <Box>
                <Typography variant="subtitle1">Salario Neto Deseado: ${Number(targetNetSalary).toFixed(2)}</Typography>
                <Typography variant="subtitle1" sx={{ mt: 1 }}>
                  <span style={{ color: 'red' }}>+ ISR: ${deductions.isr.toFixed(2)}</span>
                </Typography>
                <Typography variant="subtitle1" sx={{ mt: 1 }}>
                  <span style={{ color: 'red' }}>+ IMSS: ${deductions.imss.toFixed(2)}</span>
                </Typography>
                <Typography variant="subtitle1" sx={{ mt: 1 }}>
                  <span style={{ color: 'red' }}>+ AFORE: ${deductions.afore.toFixed(2)}</span>
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Typography variant="h6" sx={{ mt: 1, fontWeight: 'bold' }}>
                  Salario Bruto Necesario: ${calculatedGrossSalary.toFixed(2)}
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Desglose
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Concepto</TableCell>
                    <TableCell align="right">Monto</TableCell>
                    <TableCell align="right">Porcentaje</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {calculationType === 'brutoToNeto' ? (
                    <>
                      <TableRow>
                        <TableCell>Salario Bruto</TableCell>
                        <TableCell align="right">${Number(grossSalary).toFixed(2)}</TableCell>
                        <TableCell align="right">100%</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>ISR</TableCell>
                        <TableCell align="right">${deductions.isr.toFixed(2)}</TableCell>
                        <TableCell align="right">
                          {Number(grossSalary) > 0 ? ((deductions.isr / Number(grossSalary)) * 100).toFixed(2) : 0}%
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>IMSS</TableCell>
                        <TableCell align="right">${deductions.imss.toFixed(2)}</TableCell>
                        <TableCell align="right">
                          {Number(grossSalary) > 0 ? ((deductions.imss / Number(grossSalary)) * 100).toFixed(2) : 0}%
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>AFORE</TableCell>
                        <TableCell align="right">${deductions.afore.toFixed(2)}</TableCell>
                        <TableCell align="right">
                          {Number(grossSalary) > 0 ? ((deductions.afore / Number(grossSalary)) * 100).toFixed(2) : 0}%
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>
                          <strong>Salario Neto</strong>
                        </TableCell>
                        <TableCell align="right">
                          <strong>${netSalary.toFixed(2)}</strong>
                        </TableCell>
                        <TableCell align="right">
                          <strong>{Number(grossSalary) > 0 ? ((netSalary / Number(grossSalary)) * 100).toFixed(2) : 0}%</strong>
                        </TableCell>
                      </TableRow>
                    </>
                  ) : (
                    <>
                      <TableRow>
                        <TableCell>Salario Neto Deseado</TableCell>
                        <TableCell align="right">${Number(targetNetSalary).toFixed(2)}</TableCell>
                        <TableCell align="right">
                          {calculatedGrossSalary > 0 ? ((Number(targetNetSalary) / calculatedGrossSalary) * 100).toFixed(2) : 0}%
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>ISR</TableCell>
                        <TableCell align="right">${deductions.isr.toFixed(2)}</TableCell>
                        <TableCell align="right">
                          {calculatedGrossSalary > 0 ? ((deductions.isr / calculatedGrossSalary) * 100).toFixed(2) : 0}%
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>IMSS</TableCell>
                        <TableCell align="right">${deductions.imss.toFixed(2)}</TableCell>
                        <TableCell align="right">
                          {calculatedGrossSalary > 0 ? ((deductions.imss / calculatedGrossSalary) * 100).toFixed(2) : 0}%
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>AFORE</TableCell>
                        <TableCell align="right">${deductions.afore.toFixed(2)}</TableCell>
                        <TableCell align="right">
                          {calculatedGrossSalary > 0 ? ((deductions.afore / calculatedGrossSalary) * 100).toFixed(2) : 0}%
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>
                          <strong>Salario Bruto Necesario</strong>
                        </TableCell>
                        <TableCell align="right">
                          <strong>${calculatedGrossSalary.toFixed(2)}</strong>
                        </TableCell>
                        <TableCell align="right">
                          <strong>100%</strong>
                        </TableCell>
                      </TableRow>
                    </>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>

      <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Historial de Cálculos
          </Typography>
          <Tooltip title="Exportar historial a CSV">
            <IconButton onClick={exportHistoryToCSV} color="primary">
              <DownloadIcon />
            </IconButton>
          </Tooltip>
        </Box>
        <Divider sx={{ mb: 2 }} />
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Fecha</TableCell>
                <TableCell>Tipo</TableCell>
                <TableCell align="right">Bruto</TableCell>
                <TableCell align="right">Neto</TableCell>
                <TableCell align="right">ISR</TableCell>
                <TableCell align="right">IMSS</TableCell>
                <TableCell align="right">AFORE</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {historyItems.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    No hay cálculos en el historial
                  </TableCell>
                </TableRow>
              ) : (
                historyItems.map((item, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      {item.timestamp.toLocaleString('es-MX', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </TableCell>
                    <TableCell>{item.gross > item.net ? 'Bruto → Neto' : 'Neto → Bruto'}</TableCell>
                    <TableCell align="right">${item.gross.toFixed(2)}</TableCell>
                    <TableCell align="right">${item.net.toFixed(2)}</TableCell>
                    <TableCell align="right">${item.deductions.isr.toFixed(2)}</TableCell>
                    <TableCell align="right">${item.deductions.imss.toFixed(2)}</TableCell>
                    <TableCell align="right">${item.deductions.afore.toFixed(2)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

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

export default SalaryCalculator;