import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts';
import { 
  Users, 
  TrendingUp, 
  Briefcase, 
  DollarSign,
  Target,
  Clock,
  CheckCircle,
  AlertCircle,
  Eye,
  MousePointer,
  Send,
  UserCheck
} from 'lucide-react';

// Types
interface DashboardMetrics {
  totalEmployees: number;
  activeJobs: number;
  monthlyRevenue: number;
  clientSatisfaction: number;
  proposalsSent: number;
  proposalsAccepted: number;
  conversionRate: number;
  avgResponseTime: number;
}

interface ChartData {
  name: string;
  value: number;
  growth?: number;
}

interface VirtuousCircleMetrics {
  cycleId: string;
  totalJobs: number;
  opportunities: number;
  proposals: number;
  clients: number;
  revenue: number;
  efficiency: number;
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#ff0000'];

const MainDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');
  const [revenueData, setRevenueData] = useState<ChartData[]>([]);
  const [jobsData, setJobsData] = useState<ChartData[]>([]);
  const [proposalsData, setProposalsData] = useState<ChartData[]>([]);
  const [virtuousCircleData, setVirtuousCircleData] = useState<VirtuousCircleMetrics | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, [selectedTimeRange]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Simular carga de datos del API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Datos simulados
      setMetrics({
        totalEmployees: 2547,
        activeJobs: 156,
        monthlyRevenue: 2847500,
        clientSatisfaction: 4.8,
        proposalsSent: 89,
        proposalsAccepted: 34,
        conversionRate: 38.2,
        avgResponseTime: 2.4
      });

      setRevenueData([
        { name: 'Ene', value: 2100000 },
        { name: 'Feb', value: 2350000 },
        { name: 'Mar', value: 2680000 },
        { name: 'Abr', value: 2450000 },
        { name: 'May', value: 2847500 },
        { name: 'Jun', value: 3120000 },
      ]);

      setJobsData([
        { name: 'Publicados', value: 156 },
        { name: 'En proceso', value: 89 },
        { name: 'Completados', value: 234 },
        { name: 'Cancelados', value: 12 }
      ]);

      setProposalsData([
        { name: 'Lun', value: 12 },
        { name: 'Mar', value: 18 },
        { name: 'Mié', value: 15 },
        { name: 'Jue', value: 22 },
        { name: 'Vie', value: 28 },
        { name: 'Sáb', value: 8 },
        { name: 'Dom', value: 5 }
      ]);

      setVirtuousCircleData({
        cycleId: 'VC_20241125_143022',
        totalJobs: 2847,
        opportunities: 156,
        proposals: 34,
        clients: 12,
        revenue: 450000,
        efficiency: 87.5
      });

    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard HuntRED® v2</h1>
          <p className="text-gray-600">Sistema integral de gestión de RRHH</p>
        </div>
        <div className="flex gap-2">
          <select 
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
          >
            <option value="7d">Últimos 7 días</option>
            <option value="30d">Últimos 30 días</option>
            <option value="90d">Últimos 3 meses</option>
            <option value="1y">Último año</option>
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Empleados</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.totalEmployees.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+12.5%</span> vs mes anterior
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Trabajos Activos</CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.activeJobs}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+8.2%</span> vs mes anterior
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ingresos Mensuales</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(metrics?.monthlyRevenue || 0)}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+16.3%</span> vs mes anterior
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tasa de Conversión</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatPercentage(metrics?.conversionRate || 0)}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+3.1%</span> vs mes anterior
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Círculo Virtuoso Section */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse"></div>
            Círculo Virtuoso - Último Ciclo
          </CardTitle>
        </CardHeader>
        <CardContent>
          {virtuousCircleData && (
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{virtuousCircleData.totalJobs.toLocaleString()}</div>
                <div className="text-sm text-gray-600">Jobs Scraped</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{virtuousCircleData.opportunities}</div>
                <div className="text-sm text-gray-600">Oportunidades</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{virtuousCircleData.proposals}</div>
                <div className="text-sm text-gray-600">Propuestas</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{virtuousCircleData.clients}</div>
                <div className="text-sm text-gray-600">Nuevos Clientes</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{formatCurrency(virtuousCircleData.revenue)}</div>
                <div className="text-sm text-gray-600">Revenue</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{virtuousCircleData.efficiency}%</div>
                <div className="text-sm text-gray-600">Eficiencia</div>
              </div>
            </div>
          )}
          <div className="mt-4 p-3 bg-blue-100 rounded-lg">
            <p className="text-sm text-blue-800">
              ✅ Último ciclo completado exitosamente. Próximo ciclo programado en 18 horas.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Ingresos por Mes</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`} />
                <Tooltip 
                  formatter={(value: number) => [formatCurrency(value), 'Ingresos']}
                />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#8884d8" 
                  fill="#8884d8" 
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Jobs Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Distribución de Trabajos</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={jobsData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {jobsData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Proposals Timeline */}
        <Card>
          <CardHeader>
            <CardTitle>Propuestas por Día</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={proposalsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#82ca9d" 
                  strokeWidth={3}
                  dot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Performance Metrics */}
        <Card>
          <CardHeader>
            <CardTitle>Métricas de Performance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4 text-blue-600" />
                <span className="text-sm">Visualizaciones</span>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold">12,547</div>
                <div className="text-xs text-green-600">+15.2%</div>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MousePointer className="h-4 w-4 text-orange-600" />
                <span className="text-sm">Clicks</span>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold">3,289</div>
                <div className="text-xs text-green-600">+8.7%</div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Send className="h-4 w-4 text-purple-600" />
                <span className="text-sm">Aplicaciones</span>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold">867</div>
                <div className="text-xs text-green-600">+12.3%</div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <UserCheck className="h-4 w-4 text-green-600" />
                <span className="text-sm">Contrataciones</span>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold">143</div>
                <div className="text-xs text-green-600">+18.9%</div>
              </div>
            </div>

            <div className="pt-4 border-t">
              <div className="flex items-center justify-between">
                <span className="font-medium">Conversion Rate</span>
                <span className="text-lg font-bold text-green-600">16.5%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div className="bg-green-600 h-2 rounded-full" style={{ width: '16.5%' }}></div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Actividad Reciente</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-4 p-3 bg-green-50 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div className="flex-1">
                <div className="font-medium">Nueva propuesta aceptada</div>
                <div className="text-sm text-gray-600">TechCorp México - Valor: $125,000 MXN</div>
              </div>
              <div className="text-sm text-gray-500">hace 15 min</div>
            </div>

            <div className="flex items-center gap-4 p-3 bg-blue-50 rounded-lg">
              <Clock className="h-5 w-5 text-blue-600" />
              <div className="flex-1">
                <div className="font-medium">Círculo virtuoso completado</div>
                <div className="text-sm text-gray-600">2,847 jobs procesados, 156 oportunidades detectadas</div>
              </div>
              <div className="text-sm text-gray-500">hace 2 horas</div>
            </div>

            <div className="flex items-center gap-4 p-3 bg-orange-50 rounded-lg">
              <AlertCircle className="h-5 w-5 text-orange-600" />
              <div className="flex-1">
                <div className="font-medium">Atención requerida</div>
                <div className="text-sm text-gray-600">5 publicaciones requieren optimización</div>
              </div>
              <div className="text-sm text-gray-500">hace 4 horas</div>
            </div>

            <div className="flex items-center gap-4 p-3 bg-purple-50 rounded-lg">
              <TrendingUp className="h-5 w-5 text-purple-600" />
              <div className="flex-1">
                <div className="font-medium">Mejora en ML detectada</div>
                <div className="text-sm text-gray-600">Accuracy aumentó de 82% a 89%</div>
              </div>
              <div className="text-sm text-gray-500">hace 6 horas</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Acciones Rápidas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button className="p-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              <Briefcase className="h-6 w-6 mx-auto mb-2" />
              <div className="text-sm font-medium">Publicar Trabajo</div>
            </button>
            
            <button className="p-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
              <Send className="h-6 w-6 mx-auto mb-2" />
              <div className="text-sm font-medium">Enviar Propuesta</div>
            </button>
            
            <button className="p-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
              <TrendingUp className="h-6 w-6 mx-auto mb-2" />
              <div className="text-sm font-medium">Ver Analytics</div>
            </button>
            
            <button className="p-4 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors">
              <Users className="h-6 w-6 mx-auto mb-2" />
              <div className="text-sm font-medium">Gestión Empleados</div>
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MainDashboard;