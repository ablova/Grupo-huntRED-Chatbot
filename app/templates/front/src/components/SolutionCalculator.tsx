// /app/templates/front/src/components/SolutionCalculator.tsx
import React, { useState, useMemo, useRef, lazy } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useForm, FormProvider } from 'react-hook-form';
import { motion, AnimatePresence } from 'framer-motion';
import { useReactToPrint } from 'react-to-print';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tooltip as UITooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Loader2, Info, Calendar, Mail, Copy, Share2, Download } from 'lucide-react';
import axios from 'axios';
import { toast } from '@/components/ui/use-toast';
import { ErrorBoundary } from 'react-error-boundary';

// Interfaces
interface BusinessUnit {
  id: number;
  name: string;
  pricing_config: { plans: Array<{ name: string; type: string; base_price: string; description: string }> };
}

interface Addon {
  id: number;
  addon: string;
  metadata: { price: string; description: string };
}

interface Assessment {
  id: string;
  name: string;
  base_price: string;
  discount_tiers: Array<{ min_users: number; discount: number }>;
}

interface BillingMilestone {
  label: string;
  amount: number;
  detail: string;
}

interface PricingProposal {
  total_amount: string;
  currency: string;
  modalities: Array<{ type: string; count: number; cost: number; billing_milestones: BillingMilestone[] }>;
}

interface FormValues {
  businessUnit: string;
  services: { [key: string]: { ai: number; hybrid: number; human: number; baseSalary: number } };
  addons: string[];
  assessments: { id: string; users: number }[];
  retainerScheme: 'single' | 'double' | null;
  compareModes: string[];
  email: string;
}

// Logo Mapping
const LOGO_MAP: { [key: string]: string } = {
  'huntRED Executive': '/static/images/huntRED_Executive.png',
  'huntRED Standard': '/static/images/huntRED.png',
  huntU: '/static/images/huntU.png',
  amigro: '/static/images/amigro.png',
};
const DEFAULT_LOGO = '/static/images/g_huntred.png';
const LARGE_LOGO = '/static/images/Grupo_huntred.png';

// API Client
const apiClient = axios.create({ baseURL: '/api/pricing' });
const fetchBusinessUnits = () => apiClient.get('/business-units').then(res => res.data.business_units);
const fetchAddons = () => apiClient.get('/addons').then(res => res.data.addons);
const fetchAssessments = () => apiClient.get('/assessments').then(res => res.data.assessments);
const calculatePricing = (data: FormValues) =>
  apiClient
    .post('/calculate', {
      opportunity_id: null,
      include_addons: data.addons,
      include_assessments: data.assessments.map(a => ({ id: a.id, users: a.users })),
      include_bundles: Object.entries(data.services).map(([bu, svc]) => ({
        business_unit: bu,
        ai: svc.ai,
        hybrid: svc.hybrid,
        human: svc.human,
        base_salary: svc.baseSalary,
        retainer_scheme: ['huntRED Executive', 'huntRED Standard'].includes(bu) ? data.retainerScheme : null,
      })),
    })
    .then(res => res.data.proposal);
const sendProposal = (data: FormValues, proposal: PricingProposal) =>
  apiClient
    .post('/send-proposal', { email: data.email, proposal })
    .then(() => ({ status: 'success', message: 'Cotización enviada correctamente.' }))
    .catch(err => ({ status: 'error', message: err.response?.data?.error || 'Error enviando la cotización.' }));
const trackShare = (data: FormValues, proposal: PricingProposal, platform: string) =>
  apiClient.post('/track-share', {
    email: data.email || 'Anónimo',
    proposal,
    platform,
    business_unit: data.businessUnit,
    timestamp: new Date().toISOString(),
  });

// Modalidades
const MODALIDADES = [
  { key: 'ai', label: 'Solo IA', tooltip: 'Automatización total con IA, facturación 100% al inicio.', recommendation: 'Ideal para procesos rápidos y volumen alto.' },
  { key: 'hybrid', label: 'Híbrido', tooltip: 'Combinación de IA y consultores humanos, retainer + éxito.', recommendation: 'Equilibrio entre tecnología y trato humano.' },
  { key: 'human', label: 'Solo Humano', tooltip: 'Gestión 100% humana, retainer + éxito.', recommendation: 'Máxima personalización y acompañamiento.' },
];

// Componente Wizard
const WizardStep: React.FC<{ title: string; children: React.ReactNode; isActive: boolean }> = ({ title, children, isActive }) => (
  <AnimatePresence>
    {isActive && (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3 }}
        className="space-y-4"
      >
        <h3 className="text-xl font-semibold">{title}</h3>
        {children}
      </motion.div>
    )}
  </AnimatePresence>
);

// Componente para Imprimir PDF
const PrintableSummary: React.FC<{ formValues: FormValues; proposal: PricingProposal; addons: Addon[]; assessments: Assessment[] }> = ({
  formValues,
  proposal,
  addons,
  assessments,
}) => (
  <div className="p-8 bg-white text-black">
    <div className="bg-gray-900 p-4 mb-4">
      <img src={LARGE_LOGO} alt="Grupo huntRED®" className="h-16 mx-auto" />
    </div>
    <h1 className="text-2xl font-bold mb-4">Cotización Personalizada</h1>
    <p className="text-sm mb-4">Generado por huntRED® | {new Date().toLocaleDateString()}</p>
    <h2 className="text-lg font-semibold">Resumen</h2>
    <p><strong>Unidad de Negocio:</strong> {formValues.businessUnit}</p>
    <img src={LOGO_MAP[formValues.businessUnit] || DEFAULT_LOGO} alt={`${formValues.businessUnit} Logo`} className="h-12 my-2" />
    <h3 className="font-medium">Servicios de Reclutamiento</h3>
    <ul className="list-disc pl-5">
      {Object.entries(formValues.services[formValues.businessUnit])
        .filter(([_, count]) => count > 0)
        .map(([type, count]) => (
          <li key={type}>{type.charAt(0).toUpperCase() + type.slice(1)}: {count}</li>
        ))}
    </ul>
    <h3 className="font-medium">Addons</h3>
    <ul className="list-disc pl-5">
      {formValues.addons.map(id => (
        <li key={id}>{addons.find(a => a.id.toString() === id)?.addon}</li>
      ))}
    </ul>
    <h3 className="font-medium">Assessments</h3>
    <ul className="list-disc pl-5">
      {formValues.assessments.map(a => (
        <li key={a.id}>{assessments.find(ass => ass.id === a.id)?.name} - {a.users} usuarios</li>
      ))}
    </ul>
    {['huntRED Executive', 'huntRED Standard'].includes(formValues.businessUnit) && formValues.retainerScheme && (
      <div>
        <h3 className="font-medium">Esquema de Facturación</h3>
        <p>{formValues.retainerScheme === 'single' ? '1 Pago Retainer (25%)' : '2 Pagos Retainer (17.5% cada uno)'}</p>
      </div>
    )}
    <p className="text-lg font-bold mt-4">Total Estimado: ${Number(proposal?.total_amount || 0).toLocaleString()}</p>
    <p className="text-sm mt-4">Contacto: hola@huntred.com | www.huntred.com</p>
    <img src={DEFAULT_LOGO} alt="huntRED® Logo" className="h-8 mt-4" />
  </div>
);

const SolutionCalculator: React.FC = () => {
  const [step, setStep] = useState(1);
  const printRef = useRef<HTMLDivElement>(null);
  const methods = useForm<FormValues>({
    defaultValues: {
      businessUnit: '',
      services: {
        'huntRED Executive': { ai: 0, hybrid: 0, human: 0, baseSalary: 150000 },
        'huntRED Standard': { ai: 0, hybrid: 0, human: 0, baseSalary: 80000 },
        huntU: { ai: 0, hybrid: 0, human: 0, baseSalary: 0 },
        amigro: { ai: 0, hybrid: 0, human: 0, baseSalary: 0 },
      },
      addons: [],
      assessments: [],
      retainerScheme: null,
      compareModes: [],
      email: '',
    },
  });
  const { register, watch, setValue, handleSubmit, formState: { errors } } = methods;
  const formValues = watch();

  // Queries
  const { data: businessUnits, isLoading: loadingUnits } = useQuery(['businessUnits'], fetchBusinessUnits, { staleTime: 24 * 60 * 60 * 1000 });
  const { data: addons, isLoading: loadingAddons } = useQuery(['addons'], fetchAddons, { staleTime: 24 * 60 * 60 * 1000 });
  const { data: assessments, isLoading: loadingAssessments } = useQuery(['assessments'], fetchAssessments, { staleTime: 24 * 60 * 60 * 1000 });
  const { data: pricingProposal, isLoading: loadingPricing, refetch: calculateTotal } = useQuery<PricingProposal>(
    ['pricing', formValues],
    () => calculatePricing(formValues),
    { enabled: false }
  );
  const { data: pricingPlans } = useQuery(['plans'], () => apiClient.get('/plans').then(res => res.data.plans), { staleTime: 24 * 60 * 60 * 1000 });

  // Progreso
  const progress = useMemo(() => (step / 5) * 100, [step]);

  // Subtotal
  const subtotal = useMemo(() => Number(pricingProposal?.total_amount || 0), [pricingProposal]);

  // Handlers
  const nextStep = () => setStep(prev => Math.min(prev + 1, 5));
  const prevStep = () => setStep(prev => Math.max(prev - 1, 1));
  const toggleCompareMode = (mode: string) => {
    setValue('compareModes', formValues.compareModes.includes(mode) ? formValues.compareModes.filter(m => m !== mode) : [...formValues.compareModes, mode]);
  };
  const onSubmit = async (data: FormValues) => {
    await calculateTotal();
    nextStep();
  };
  const handlePrint = useReactToPrint({
    content: () => printRef.current,
    documentTitle: `Cotización_huntRED_${new Date().toISOString().split('T')[0]}`,
    onAfterPrint: () => {
      toast({ title: 'PDF generado', description: 'La cotización ha sido descargada.' });
      apiClient.post('/track', { event: 'pdf_export', email: formValues.email || 'Anónimo', proposal: pricingProposal });
    },
  });
  const handleCopy = () => {
    const summary = `
Unidad de Negocio: ${formValues.businessUnit}
Servicios: ${Object.entries(formValues.services[formValues.businessUnit])
  .filter(([_, count]) => count > 0)
  .map(([type, count]) => `${type.charAt(0).toUpperCase() + type.slice(1)}: ${count}`)
  .join(', ')}
Addons: ${formValues.addons.map(id => addons.find(a => a.id.toString() === id)?.addon).join(', ')}
Assessments: ${formValues.assessments.map(a => `${assessments.find(ass => ass.id === a.id)?.name} - ${a.users} usuarios`).join(', ')}
Total Estimado: $${subtotal.toLocaleString()}
    `;
    navigator.clipboard.writeText(summary);
    toast({ title: 'Copiado', description: 'El resumen ha sido copiado al portapapeles.' });
  };
  const handleShare = async (platform: 'whatsapp' | 'linkedin') => {
    const summary = encodeURIComponent(`
Cotización huntRED®
Unidad: ${formValues.businessUnit}
Servicios: ${Object.entries(formValues.services[formValues.businessUnit])
  .filter(([_, count]) => count > 0)
  .map(([type, count]) => `${type.charAt(0).toUpperCase() + type.slice(1)}: ${count}`)
  .join(', ')}
Total: $${subtotal.toLocaleString()}
Más info: www.huntred.com
    `);
    const url = platform === 'whatsapp' ? `https://wa.me/?text=${summary}` : `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent('www.huntred.com')}&summary=${summary}`;
    window.open(url, '_blank');
    if (platform === 'whatsapp') {
      await trackShare(formValues, pricingProposal, 'whatsapp');
      toast({ title: 'Compartido', description: 'El resumen se ha compartido y nuestro equipo ha sido notificado.' });
    }
  };
  const handleSendEmail = async () => {
    if (!formValues.email) return;
    const response = await sendProposal(formValues, pricingProposal);
    toast({
      title: response.status === 'success' ? 'Correo enviado' : 'Error',
      description: response.message,
      variant: response.status === 'success' ? 'default' : 'destructive',
    });
  };

  // Gráfico de costos
  const chartData = useMemo(
    () =>
      formValues.compareModes.map(mode => {
        const modality = pricingProposal?.modalities.find(m => m.type === mode);
        return { name: MODALIDADES.find(m => m.key === mode)?.label, Costo: modality?.cost || 0 };
      }),
    [formValues.compareModes, pricingProposal]
  );

  // [MEJORA] Input para subir logo del cliente
  const [clientLogo, setClientLogo] = useState<File | null>(null);
  const handleLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.size > 2 * 1024 * 1024) { // 2MB limit
        toast({ title: 'Error', description: 'El logo no debe exceder 2MB.', variant: 'destructive' });
        return;
      }
      if (!['image/png', 'image/jpeg'].includes(file.type)) {
        toast({ title: 'Error', description: 'Solo se permiten imágenes PNG o JPEG.', variant: 'destructive' });
        return;
      }
      setClientLogo(file);
    }
  };

  if (loadingUnits || loadingAddons || loadingAssessments) {
    return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin" /></div>;
  }

  return (
    <section className="py-20 bg-muted/20">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-16">
          <img src={DEFAULT_LOGO} alt="huntRED® Logo" className="h-12 mx-auto" />
          <h2 className="text-3xl md:text-4xl font-bold">
            Calculadora de <span className="bg-tech-gradient bg-clip-text text-transparent">Solución</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Configura tu solución personalizada y obtén una cotización interactiva
          </p>
          <Progress value={progress} className="w-1/2 mx-auto" />
        </div>

        <FormProvider {...methods}>
          <ErrorBoundary fallback={<div>Error en la calculadora. Por favor, intenta de nuevo.</div>}>
            <form onSubmit={handleSubmit(onSubmit)} className="max-w-4xl mx-auto space-y-8">
              {/* Paso 1: Selección de Unidad de Negocio */}
              <WizardStep title="Selecciona tu Unidad de Negocio" isActive={step === 1}>
                <div className="grid md:grid-cols-2 gap-4">
                  {businessUnits?.map((bu: BusinessUnit) => (
                    <Card
                      key={bu.id}
                      className={`cursor-pointer ${formValues.businessUnit === bu.name ? 'border-primary' : ''}`}
                      role="radio"
                      aria-checked={formValues.businessUnit === bu.name}
                      tabIndex={0}
                      onKeyDown={e => e.key === 'Enter' && setValue('businessUnit', bu.name)}
                      onClick={() => setValue('businessUnit', bu.name)}
                    >
                      <CardHeader className="flex items-center gap-2">
                        <img src={LOGO_MAP[bu.name] || DEFAULT_LOGO} alt={`${bu.name} Logo`} className="h-8" />
                        <CardTitle>{bu.name}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground">{bu.pricing_config.plans[0]?.description}</p>
                        <input
                          type="radio"
                          value={bu.name}
                          {...register('businessUnit', { required: 'Selecciona una unidad de negocio' })}
                          className="hidden"
                        />
                      </CardContent>
                    </Card>
                  ))}
                </div>
                {errors.businessUnit && <p className="text-red-500 text-sm">{errors.businessUnit.message}</p>}
                <div className="flex justify-end gap-4">
                  <Button type="button" onClick={nextStep} disabled={!formValues.businessUnit}>Siguiente</Button>
                </div>
              </WizardStep>

              {/* Paso extra: Subir logo del cliente */}
              {step === 1 && (
                <div className="my-4 flex flex-col items-center">
                  <label className="text-sm font-medium mb-2">¿Quieres personalizar la cotización con tu logo?</label>
                  <input type="file" accept="image/*" onChange={handleLogoUpload} />
                  {clientLogo && <img src={URL.createObjectURL(clientLogo)} alt="Logo cliente" className="h-16 mt-2" />}
                </div>
              )}

              {/* Paso 2: Servicios de Reclutamiento */}
              <WizardStep title="Configura tus Servicios de Reclutamiento" isActive={step === 2}>
                {formValues.businessUnit && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <img src={LOGO_MAP[formValues.businessUnit] || DEFAULT_LOGO} alt={`${formValues.businessUnit} Logo`} className="h-8" />
                        {formValues.businessUnit}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {['huntRED Executive', 'huntRED Standard'].includes(formValues.businessUnit) && (
                        <>
                          <div className="grid md:grid-cols-2 gap-4">
                            <div>
                              <label className="text-sm font-medium">Salario Base Mensual</label>
                              <Input
                                type="number"
                                {...register(`services.${formValues.businessUnit}.baseSalary`, { min: { value: 0, message: 'El salario debe ser positivo' } })}
                                placeholder="Ej. 150000"
                                aria-invalid={!!errors.services?.[formValues.businessUnit]?.baseSalary}
                              />
                              {errors.services?.[formValues.businessUnit]?.baseSalary && (
                                <p className="text-red-500 text-sm">{errors.services[formValues.businessUnit].baseSalary.message}</p>
                              )}
                            </div>
                            <div className="text-sm text-muted-foreground pt-6">
                              Base de cálculo: ${(formValues.services[formValues.businessUnit].baseSalary * 13).toLocaleString()}
                            </div>
                          </div>
                          <div className="grid md:grid-cols-3 gap-4">
                            {MODALIDADES.map(({ key, label, tooltip }) => (
                              <div key={key} className="border rounded-lg p-4">
                                <UITooltipProvider>
                                  <UITooltip>
                                    <TooltipTrigger asChild>
                                      <div className="font-medium mb-2">{label}</div>
                                    </TooltipTrigger>
                                    <TooltipContent>{tooltip}</TooltipContent>
                                  </UITooltip>
                                </UITooltipProvider>
                                <div className="text-sm text-muted-foreground mb-3">
                                  {key === 'ai' && '$95,000 por búsqueda'}
                                  {key === 'hybrid' && `${formValues.services[formValues.businessUnit].ai + formValues.services[formValues.businessUnit].hybrid + formValues.services[formValues.businessUnit].human >= 2 ? '13' : '14'}% de la base`}
                                  {key === 'human' && `${formValues.services[formValues.businessUnit].ai + formValues.services[formValues.businessUnit].hybrid + formValues.services[formValues.businessUnit].human >= 2 ? '18' : '20'}% de la base`}
                                </div>
                                <div className="flex items-center gap-2">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => setValue(`services.${formValues.businessUnit}.${key}`, Math.max(0, formValues.services[formValues.businessUnit][key] - 1))}
                                    aria-label={`Reducir ${label}`}
                                  >
                                    <Minus className="h-3 w-3" />
                                  </Button>
                                  <span className="w-8 text-center">{formValues.services[formValues.businessUnit][key]}</span>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => setValue(`services.${formValues.businessUnit}.${key}`, formValues.services[formValues.businessUnit][key] + 1)}
                                    aria-label={`Aumentar ${label}`}
                                  >
                                    <Plus className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                            ))}
                          </div>
                          <div className="space-y-2">
                            <label className="text-sm font-medium">Esquema de Retainer (Hybrid/Human)</label>
                            <RadioGroup
                              {...register('retainerScheme', {
                                required: formValues.services[formValues.businessUnit].hybrid > 0 || formValues.services[formValues.businessUnit].human > 0 ? 'Selecciona un esquema de retainer' : false,
                              })}
                              defaultValue={formValues.retainerScheme || 'single'}
                              className="flex gap-4"
                              aria-invalid={!!errors.retainerScheme}
                            >
                              <div className="flex items-center space-x-2">
                                <RadioGroupItem value="single" id="single" />
                                <Label htmlFor="single">1 Pago Retainer (25%)</Label>
                              </div>
                              <div className="flex items-center space-x-2">
                                <RadioGroupItem value="double" id="double" />
                                <Label htmlFor="double">2 Pagos Retainer (17.5% cada uno)</Label>
                              </div>
                            </RadioGroup>
                            {errors.retainerScheme && <p className="text-red-500 text-sm">{errors.retainerScheme.message}</p>}
                          </div>
                        </>
                      )}
                      {['huntU', 'amigro'].includes(formValues.businessUnit) && (
                        <div className="grid md:grid-cols-2 gap-4">
                          {['ai', 'hybrid'].map(type => (
                            <div key={type} className="border rounded-lg p-4">
                              <div className="font-medium mb-2">Búsquedas {type.charAt(0).toUpperCase() + type.slice(1)}</div>
                              <div className="text-sm text-muted-foreground mb-3">
                                {formValues.businessUnit === 'huntU' ? (type === 'ai' ? '$45,000' : '$70,000') : type === 'ai' ? '$25,000' : '$40,000'}
                              </div>
                              <div className="flex items-center gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => setValue(`services.${formValues.businessUnit}.${type}`, Math.max(0, formValues.services[formValues.businessUnit][type] - 1))}
                                  aria-label={`Reducir ${type}`}
                                >
                                  <Minus className="h-3 w-3" />
                                </Button>
                                <span className="w-8 text-center">{formValues.services[formValues.businessUnit][type]}</span>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => setValue(`services.${formValues.businessUnit}.${type}`, formValues.services[formValues.businessUnit][type] + 1)}
                                  aria-label={`Aumentar ${type}`}
                                >
                                  <Plus className="h-3 w-3" />
                                </Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}
                <div className="flex justify-between gap-4">
                  <Button type="button" onClick={prevStep}>Anterior</Button>
                  <Button type="button" onClick={nextStep}>Siguiente</Button>
                </div>
              </WizardStep>

              {/* Paso 3: Addons */}
              <WizardStep title="Selecciona Addons" isActive={step === 3}>
                <Card>
                  <CardHeader>
                    <CardTitle>Complementa tu Solución</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {addons?.map((addon: Addon) => (
                      <div key={addon.id} className="flex items-center gap-4">
                        <Checkbox
                          checked={formValues.addons.includes(addon.id.toString())}
                          onCheckedChange={(checked) => {
                            setValue('addons', checked ? [...formValues.addons, addon.id.toString()] : formValues.addons.filter(id => id !== addon.id.toString()));
                          }}
                          id={`addon-${addon.id}`}
                          aria-label={addon.addon}
                        />
                        <div>
                          <Label htmlFor={`addon-${addon.id}`} className="font-medium">{addon.addon}</Label>
                          <div className="text-sm text-muted-foreground">{addon.metadata.description} - ${addon.metadata.price}</div>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
                <div className="flex justify-between gap-4">
                  <Button type="button" onClick={prevStep}>Anterior</Button>
                  <Button type="button" onClick={nextStep}>Siguiente</Button>
                </div>
              </WizardStep>

              {/* Paso 4: Assessments */}
              <WizardStep title="Selecciona Assessments" isActive={step === 4}>
                <Card>
                  <CardHeader>
                    <CardTitle>Desarrollo Organizacional</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {assessments?.map((assessment: Assessment) => (
                      <div key={assessment.id} className="space-y-2">
                        <div className="flex items-center gap-4">
                          <Checkbox
                            checked={formValues.assessments.some(a => a.id === assessment.id)}
                            onCheckedChange={(checked) => {
                              setValue('assessments', checked ? [...formValues.assessments, { id: assessment.id, users: 1 }] : formValues.assessments.filter(a => a.id !== assessment.id));
                            }}
                            id={`assessment-${assessment.id}`}
                            aria-label={assessment.name}
                          />
                          <div>
                            <Label htmlFor={`assessment-${assessment.id}`} className="font-medium">{assessment.name}</Label>
                            <div className="text-sm text-muted-foreground">${assessment.base_price}/usuario</div>
                          </div>
                        </div>
                        {formValues.assessments.some(a => a.id === assessment.id) && (
                          <div className="ml-8">
                            <label className="text-sm font-medium">Número de Usuarios</label>
                            <Input
                              type="number"
                              {...register(`assessments.${formValues.assessments.findIndex(a => a.id === assessment.id)}.users`, { min: { value: 1, message: 'Mínimo 1 usuario' } })}
                              defaultValue={1}
                              aria-invalid={!!errors.assessments?.[formValues.assessments.findIndex(a => a.id === assessment.id)]?.users}
                            />
                            {errors.assessments?.[formValues.assessments.findIndex(a => a.id === assessment.id)]?.users && (
                              <p className="text-red-500 text-sm">{errors.assessments[formValues.assessments.findIndex(a => a.id === assessment.id)].users.message}</p>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>
                <div className="flex justify-between gap-4">
                  <Button type="button" onClick={prevStep}>Anterior</Button>
                  <Button type="submit" disabled={loadingPricing}>
                    {loadingPricing ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Calcular Total'}
                  </Button>
                </div>
              </WizardStep>

              {/* Paso 5: Resumen */}
              <WizardStep title="Resumen de tu Cotización" isActive={step === 5}>
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <img src={LOGO_MAP[formValues.businessUnit] || DEFAULT_LOGO} alt={`${formValues.businessUnit} Logo`} className="h-8" />
                      Resumen
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h4 className="font-medium">Unidad de Negocio</h4>
                      <p>{formValues.businessUnit}</p>
                    </div>
                    <div>
                      <h4 className="font-medium">Servicios de Reclutamiento</h4>
                      <ul className="list-disc pl-5">
                        {Object.entries(formValues.services[formValues.businessUnit])
                          .filter(([_, count]) => count > 0)
                          .map(([type, count]) => (
                            <li key={type}>{type.charAt(0).toUpperCase() + type.slice(1)}: {count}</li>
                          ))}
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium">Addons</h4>
                      <ul className="list-disc pl-5">
                        {formValues.addons.map(id => (
                          <li key={id}>{addons?.find((a: Addon) => a.id.toString() === id)?.addon}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium">Assessments</h4>
                      <ul className="list-disc pl-5">
                        {formValues.assessments.map(a => (
                          <li key={a.id}>
                            {assessments?.find((ass: Assessment) => ass.id === a.id)?.name} - {a.users} usuarios
                          </li>
                        ))}
                      </ul>
                    </div>
                    {['huntRED Executive', 'huntRED Standard'].includes(formValues.businessUnit) && formValues.retainerScheme && (
                      <div>
                        <h4 className="font-medium">Esquema de Facturación</h4>
                        <p>{formValues.retainerScheme === 'single' ? '1 Pago Retainer (25%)' : '2 Pagos Retainer (17.5% cada uno)'}</p>
                      </div>
                    )}
                    <div className="text-right text-2xl font-bold">Total Estimado: ${subtotal.toLocaleString()}</div>

                    {/* Visualización Gráfica */}
                    {formValues.compareModes.length > 0 && (
                      <div className="space-y-4">
                        <h4 className="font-medium">Comparación de Costos</h4>
                        <div style={{ height: 200 }}>
                          <ResponsiveContainer>
                            <BarChart data={chartData}>
                              <XAxis dataKey="name" />
                              <YAxis />
                              <UITooltip />
                              <Bar dataKey="Costo" fill="#8884d8" />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    )}

                    {/* Comparativa de Modalidades */}
                    <div className="space-y-4">
                      <h4 className="font-medium">Comparar Modalidades</h4>
                      <div className="flex flex-wrap gap-4">
                        {MODALIDADES.map(({ key, label, tooltip }) => (
                          <UITooltipProvider key={key}>
                            <UITooltip>
                              <TooltipTrigger asChild>
                                <div className="flex items-center gap-2">
                                  <Checkbox
                                    checked={formValues.compareModes.includes(key)}
                                    onCheckedChange={() => toggleCompareMode(key)}
                                    disabled={['huntU', 'amigro'].includes(formValues.businessUnit) && key === 'human'}
                                    id={`compare-${key}`}
                                    aria-label={`Comparar ${label}`}
                                  />
                                  <Label htmlFor={`compare-${key}`}>{label}</Label>
                                </div>
                              </TooltipTrigger>
                              <TooltipContent>{tooltip}</TooltipContent>
                            </UITooltip>
                          </UITooltipProvider>
                        ))}
                      </div>
                      {formValues.compareModes.length > 0 && (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Modalidad</TableHead>
                              <TableHead>Cantidad</TableHead>
                              <TableHead>Costo Total</TableHead>
                              <TableHead>Momentos de Facturación</TableHead>
                              <TableHead>Recomendación</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {formValues.compareModes.map(mode => {
                              const modality = pricingProposal?.modalities.find(m => m.type === mode);
                              const count = modality?.count || 0;
                              const cost = modality?.cost || 0;
                              const milestones = modality?.billing_milestones || [];
                              const { label, recommendation } = MODALIDADES.find(m => m.key === mode)!;
                              return (
                                <TableRow key={mode}>
                                  <TableCell>{label}</TableCell>
                                  <TableCell>{count}</TableCell>
                                  <TableCell>${cost.toLocaleString()}</TableCell>
                                  <TableCell>
                                    <ul className="list-disc pl-5">
                                      {milestones.map((m, idx) => (
                                        <li key={idx}>
                                          {m.label}: ${m.amount.toLocaleString()} ({m.detail})
                                        </li>
                                      ))}
                                    </ul>
                                  </TableCell>
                                  <TableCell className="text-sm">{recommendation}</TableCell>
                                </TableRow>
                              );
                            })}
                          </TableBody>
                        </Table>
                      )}
                    </div>

                    {/* Email Form */}
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Enviar Cotización por Correo</label>
                      <div className="flex gap-2">
                        <Input
                          type="email"
                          {...register('email', { required: 'El correo es requerido', pattern: { value: /^\S+@\S+$/i, message: 'Correo inválido' } })}
                          placeholder="tu@correo.com"
                          aria-invalid={!!errors.email}
                        />
                        <Button type="button" onClick={handleSendEmail} disabled={!formValues.email || loadingPricing}>
                          Enviar
                        </Button>
                      </div>
                      {errors.email && <p className="text-red-500 text-sm">{errors.email.message}</p>}
                    </div>

                    {/* Checkbox de consentimiento */}
                    <div className="flex items-center gap-2">
                      <Checkbox
                        {...register('consent', { required: 'Debes aceptar el uso de tus datos.' })}
                        id="consent"
                        aria-label="Aceptar uso de datos"
                      />
                      <label htmlFor="consent" className="text-sm">Acepto el uso de mis datos para fines comerciales.</label>
                    </div>
                    {errors.consent && <p className="text-red-500 text-sm">{errors.consent.message}</p>}
                  </CardContent>
                </Card>
                <div className="flex justify-between gap-4 mt-4">
                  <Button type="button" onClick={prevStep}>Anterior</Button>
                  <div className="flex gap-4">
                    <Button onClick={handlePrint} aria-label="Descargar PDF">
                      <Download className="mr-2 h-4 w-4" />
                      Descargar PDF
                    </Button>
                    <Button onClick={handleCopy} aria-label="Copiar Resumen">
                      <Copy className="mr-2 h-4 w-4" />
                      Copiar
                    </Button>
                    <Button onClick={() => handleShare('whatsapp')} aria-label="Compartir por WhatsApp">
                      <Share2 className="mr-2 h-4 w-4" />
                      WhatsApp
                    </Button>
                    <Button onClick={() => handleShare('linkedin')} aria-label="Compartir por LinkedIn">
                      <Share2 className="mr-2 h-4 w-4" />
                      LinkedIn
                    </Button>
                    <Button className="bg-tech-gradient hover:opacity-90">
                      <Calendar className="mr-2 h-4 w-4" />
                      Solicitar Propuesta Formal
                    </Button>
                  </div>
                </div>
              </WizardStep>

              {/* Hidden Printable Component */}
              <div style={{ display: 'none' }}>
                <PrintableSummary ref={printRef} formValues={formValues} proposal={pricingProposal} addons={addons} assessments={assessments} />
              </div>
            </form>
          </ErrorBoundary>
        </FormProvider>
      </div>
    </section>
  );
};

export default SolutionCalculator;