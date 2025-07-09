import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  CheckCircle, 
  Calendar, 
  Users, 
  CreditCard, 
  MessageSquare, 
  FileText, 
  Briefcase,
  UserRound,
  HomeIcon,
  UserCheck,
  Brain,
  Calculator,
  PieChart,
  ArrowRight
} from 'lucide-react';
import SalaryCalculator from '@/components/SalaryCalculator';
import OverheadCalculator from '@/components/OverheadCalculator';

const PayrollManagementSection = () => {
  const payrollFeatures = [
    {
      name: "Control por Mensajería",
      description: "Registro de entrada/salida vía WhatsApp y Telegram personalizados",
      icon: MessageSquare,
      color: "bg-green-500"
    },
    {
      name: "Gestión de Ausencias",
      description: "Solicitud y aprobación de vacaciones y permisos",
      icon: Calendar,
      color: "bg-blue-500"
    },
    {
      name: "Dispersión Automática",
      description: "Pagos automatizados con múltiples bancos (Premium)",
      icon: CreditCard,
      color: "bg-purple-500"
    },
    {
      name: "Cálculos Precisos",
      description: "Automatización con cumplimiento de normativas vigentes",
      icon: FileText,
      color: "bg-emerald-500"
    },
    {
      name: "Análisis Predictivo",
      description: "Previsión de nómina con IA y machine learning",
      icon: Brain,
      color: "bg-violet-500"
    },
    {
      name: "Control Normativo",
      description: "Actualizado a UMA, IMSS, Infonavit, ISR",
      icon: CheckCircle,
      color: "bg-amber-500"
    }
  ];

  const userRoles = [
    {
      role: "Empleado",
      description: "Control de asistencia y solicitudes desde aplicaciones de mensajería",
      features: ["Registro entrada/salida", "Solicitud vacaciones", "Consulta recibos", "Estado de solicitudes"],
      icon: UserRound,
      color: "bg-blue-500"
    },
    {
      role: "Supervisor",
      description: "Gestión de equipos y autorización de solicitudes de personal",
      features: ["Autorización ausencias", "Reportes de asistencia", "Evaluación desempeño", "Validación horas extra"],
      icon: UserCheck,
      color: "bg-emerald-500"
    },
    {
      role: "Recursos Humanos",
      description: "Administración completa y análisis predictivo de nómina",
      features: ["Análisis predictivo", "Ajuste automático UMA", "Cumplimiento IMSS/Infonavit", "Cálculos fiscales precisos"],
      icon: Users,
      color: "bg-primary"
    }
  ];

  const employeeTypes = [
    {
      type: "Presencial",
      description: "Control mediante registro biométrico y mensajería",
      features: ["Registro por ubicación", "Verificación facial", "Control de horas extra", "Cumplimiento normativo"],
      icon: Briefcase,
      color: "bg-blue-500"
    },
    {
      type: "Home Office",
      description: "Seguimiento por indicadores de productividad y conexión",
      features: ["Control de conexión", "Revisión de entregables", "Métricas de productividad", "Horas laborables"],
      icon: HomeIcon,
      color: "bg-emerald-500"
    },
    {
      type: "Confianza",
      description: "Evaluación por resultados y cumplimiento de objetivos",
      features: ["KPIs personalizados", "Evaluación por objetivos", "Reporte de actividades", "Autoevaluación"],
      icon: CheckCircle,
      color: "bg-amber-500"
    }
  ];

  const systemComponents = [
    "TimeTracker - Registro inteligente por mensajería",
    "LeaveManager - Gestión de vacaciones y ausencias", 
    "PayrollEngine - Cálculo automático de nómina",
    "PredictiveAnalytics - Análisis y previsión con IA",
    "AttendanceReports - Reportes detallados de asistencia",
    "EmployeeLoader - Carga simplificada de empleados",
    "OvertimeController - Control automático de horas extra",
    "BankConnector - Conexión con múltiples bancos",
    "RegulationUpdater - Actualización automática UMA/IMSS",
    "ComplianceManager - Cumplimiento normativo actualizado",
    "OutplacementModule - Transición laboral eficiente",
    "SettlementCalculator - Cálculo de finiquito por país"
  ];

  return (
    <section id="payroll-management" className="py-16 px-4 md:py-24 bg-background">      
      {/* Calculadoras integradas */}
      <div className="container mx-auto mb-16">
        <div className="text-center space-y-6 mb-10">
          <h2 className="text-3xl font-bold tracking-tight">Herramientas de Cálculo</h2>
          <p className="text-muted-foreground max-w-3xl mx-auto">
            Utilice nuestras calculadoras especializadas para planificación financiera, 
            estimación de costos y optimización de recursos humanos
          </p>
        </div>
        
        <Tabs defaultValue="overview" className="max-w-5xl mx-auto">
          <TabsList className="grid grid-cols-3 w-full mb-8">
            <TabsTrigger value="overview" className="text-base">
              <div className="flex items-center gap-2">
                <PieChart className="h-4 w-4" />
                <span>Vista General</span>
              </div>
            </TabsTrigger>
            <TabsTrigger value="salary" className="text-base">
              <div className="flex items-center gap-2">
                <Calculator className="h-4 w-4" />
                <span>Calculadora de Salario</span>
              </div>
            </TabsTrigger>
            <TabsTrigger value="overhead" className="text-base">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                <span>Calculadora de Overhead</span>
              </div>
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="space-y-8">
            <div className="grid md:grid-cols-2 gap-6">
              <Card className="border-primary/20 hover:shadow-lg transition-all duration-300">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white">
                      <Calculator className="h-5 w-5" />
                    </div>
                    <CardTitle className="text-lg">Calculadora de Salario</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    Convierta entre salarios brutos y netos con precisión utilizando
                    los cálculos oficiales de ISR, IMSS, Infonavit y más.
                  </p>
                  <ul className="text-sm space-y-2 mb-4">
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                      <span>Cálculos actualizados a la última legislación fiscal</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                      <span>Desglose detallado de impuestos y deducciones</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                      <span>Historial exportable de cálculos realizados</span>
                    </li>
                  </ul>
                  <Button 
                    variant="outline" 
                    className="w-full flex items-center justify-between group" 
                    onClick={() => {
                      const tabsList = document.querySelector('[role="tablist"]');
                      if (tabsList) {
                        const salaryTab = tabsList.querySelector('[value="salary"]');
                        if (salaryTab) {
                          (salaryTab as HTMLElement).click();
                        }
                      }
                    }}
                  >
                    <span>Acceder a la calculadora</span>
                    <ArrowRight className="h-4 w-4 opacity-70 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </CardContent>
              </Card>
              
              <Card className="border-primary/20 hover:shadow-lg transition-all duration-300">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center text-white">
                      <PieChart className="h-5 w-5" />
                    </div>
                    <CardTitle className="text-lg">Calculadora de Overhead</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    Calcule todos los costos asociados a sus empleados y obtenga
                    información detallada sobre distribución de gastos.
                  </p>
                  <ul className="text-sm space-y-2 mb-4">
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                      <span>Análisis visual con gráficos detallados</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                      <span>Configuración personalizada de beneficios y bonos</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                      <span>Gestión de múltiples empleados y comparativas</span>
                    </li>
                  </ul>
                  <Button 
                    variant="outline" 
                    className="w-full flex items-center justify-between group"
                    onClick={() => {
                      const tabsList = document.querySelector('[role="tablist"]');
                      if (tabsList) {
                        const overheadTab = tabsList.querySelector('[value="overhead"]');
                        if (overheadTab) {
                          (overheadTab as HTMLElement).click();
                        }
                      }
                    }}
                  >
                    <span>Acceder a la calculadora</span>
                    <ArrowRight className="h-4 w-4 opacity-70 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          
          <TabsContent value="salary">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <SalaryCalculator />
            </div>
          </TabsContent>
          
          <TabsContent value="overhead">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <OverheadCalculator />
            </div>
          </TabsContent>
        </Tabs>
      </div>
      
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-3xl md:text-4xl font-bold">
            Administración de <span className="text-primary">Nómina</span> Inteligente
          </h2>
          <p className="text-muted-foreground max-w-3xl mx-auto">
            Gestión completa de nómina mediante mensajería para registro de asistencia y solicitudes, con análisis predictivo y cumplimiento normativo
          </p>
        </div>
        
        {/* Features */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-16">
          {payrollFeatures.map((feature, index) => (
            <Card key={index} className="glass border-primary/20 hover:shadow-lg transition-shadow">
              <CardContent className="p-4 text-center">
                <div className={`w-12 h-12 mx-auto ${feature.color} rounded-full flex items-center justify-center text-white mb-3`}>
                  {feature.name === "Control por Mensajería" && <MessageSquare className="h-6 w-6" />}
                  {feature.name === "Gestión de Ausencias" && <Calendar className="h-6 w-6" />}
                  {feature.name === "Dispersión Automática" && <CreditCard className="h-6 w-6" />}
                  {feature.name === "Cálculos Precisos" && <FileText className="h-6 w-6" />}
                  {feature.name === "Análisis Predictivo" && <Brain className="h-6 w-6" />}
                  {feature.name === "Control Normativo" && <CheckCircle className="h-6 w-6" />}
                </div>
                <h3 className="font-medium text-sm">{feature.name}</h3>
                <p className="text-sm text-muted-foreground text-center">
                  {feature.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* User Roles */}
        <div className="space-y-8 mb-16">
          <div className="text-center space-y-4">
            <h3 className="text-2xl font-bold">Roles de Usuario Personalizados</h3>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Cada rol cuenta con funcionalidades específicas diseñadas para optimizar su experiencia
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {userRoles.map((role, index) => (
              <Card key={index} className="glass border-primary/20 hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 ${role.color} rounded-full flex items-center justify-center text-white`}>
                      {role.role === "Empleado" && <UserRound className="h-5 w-5" />}
                      {role.role === "Supervisor" && <UserCheck className="h-5 w-5" />}
                      {role.role === "Recursos Humanos" && <Users className="h-5 w-5" />}
                    </div>
                    <div>
                      <CardTitle className="text-lg">{role.role}</CardTitle>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground">{role.description}</p>
                  <div className="space-y-2">
                    {role.features.map((feature, featureIndex) => (
                      <div key={featureIndex} className="flex items-center space-x-2">
                        <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                        <span className="text-xs">{feature}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Employee Types */}
        <div className="space-y-8 mb-16">
          <div className="text-center space-y-4">
            <h3 className="text-2xl font-bold">Tipos de Empleados</h3>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Soluciones adaptadas a cada modalidad de trabajo para garantizar eficiencia y control
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {employeeTypes.map((type, index) => (
              <Card key={index} className="glass border-primary/20 hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 ${type.color} rounded-full flex items-center justify-center text-white`}>
                      {type.type === "Presencial" && <Briefcase className="h-5 w-5" />}
                      {type.type === "Home Office" && <HomeIcon className="h-5 w-5" />}
                      {type.type === "Confianza" && <CheckCircle className="h-5 w-5" />}
                    </div>
                    <div>
                      <CardTitle className="text-lg">{type.type}</CardTitle>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-muted-foreground">{type.description}</p>
                  <div className="space-y-2">
                    {type.features.map((feature, featureIndex) => (
                      <div key={featureIndex} className="flex items-center space-x-2">
                        <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                        <span className="text-xs">{feature}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
        
        {/* System Architecture */}
        <div className="space-y-8">
          <div className="text-center space-y-4">
            <h3 className="text-2xl font-bold">Arquitectura del Sistema</h3>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Componentes integrados que funcionan a través de canales de mensajería personalizados por cliente
            </p>
          </div>
          
          {/* Lista de componentes del sistema - podría convertirse en tarjetas visuales en el futuro */}
          <div className="max-w-3xl mx-auto bg-muted/30 rounded-lg p-6">
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {systemComponents.map((component, index) => (
                <li key={index} className="text-sm flex items-start gap-2">
                  <div className="w-1.5 h-1.5 bg-primary rounded-full mt-1.5" />
                  <span>{component}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
        
        {/* Ya no necesitamos estas anclas porque usamos JavaScript para navegar */}
      </div>
    </section>
  );
};

export default PayrollManagementSection;
