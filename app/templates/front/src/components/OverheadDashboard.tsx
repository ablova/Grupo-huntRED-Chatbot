import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import {
  TrendingUp, TrendingDown, DollarSign, Users, Brain, Heart, Leaf, 
  Lightbulb, Target, Award, AlertTriangle, CheckCircle, Info,
  Calendar, Download, Filter, Refresh, ArrowUpDown, BarChart3,
  PieChart as PieChartIcon, Activity, Zap, Star, Shield
} from 'lucide-react';

// Types
interface DashboardProps {
  companyId: string;
  hasAura?: boolean;
  hasMl?: boolean;
  timeRange?: '7d' | '30d' | '90d' | '1y' | 'all';
}

interface MetricCard {
  title: string;
  value: string;
  change: number;
  trend: 'up' | 'down' | 'stable';
  icon: React.ComponentType<any>;
  color: string;
}

interface HistoricalData {
  period: string;
  date: string;
  totalOverhead: number;
  traditionalOverhead: number;
  auraOverhead: number;
  employees: number;
  efficiency: number;
  ethicsScore: number;
  sustainabilityScore: number;
  mlAccuracy: number;
}

interface TeamPerformance {
  teamName: string;
  department: string;
  efficiency: number;
  overhead: number;
  ethicsScore: number;
  size: number;
  trend: number;
}

interface CategoryBreakdown {
  name: string;
  value: number;
  percentage: number;
  benchmark: number;
  color: string;
  trend: number;
}

export const OverheadDashboard: React.FC<DashboardProps> = ({
  companyId,
  hasAura = false,
  hasMl = false,
  timeRange = '30d'
}) => {
  // State
  const [activeMetric, setActiveMetric] = useState('overview');
  const [selectedPeriod, setSelectedPeriod] = useState(timeRange);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Mock Data Generation (en producción vendría de APIs)
  const generateHistoricalData = (periods: number): HistoricalData[] => {
    const data: HistoricalData[] = [];
    const baseDate = new Date();
    
    for (let i = periods; i >= 0; i--) {
      const date = new Date(baseDate);
      date.setDate(date.getDate() - i * 7); // Weekly data
      
      const trend = Math.sin(i * 0.1) * 0.1 + 0.95; // Slight improvement trend
      const randomFactor = 0.9 + Math.random() * 0.2;
      
      data.push({
        period: `S${periods - i + 1}`,
        date: date.toISOString().split('T')[0],
        totalOverhead: (45 + Math.random() * 10) * trend * randomFactor,
        traditionalOverhead: (38 + Math.random() * 6) * trend * randomFactor,
        auraOverhead: hasAura ? (7 + Math.random() * 4) * trend * randomFactor : 0,
        employees: Math.floor(50 + Math.random() * 20),
        efficiency: (75 + Math.random() * 20) * trend,
        ethicsScore: hasAura ? (80 + Math.random() * 15) * trend : 0,
        sustainabilityScore: hasAura ? (75 + Math.random() * 20) * trend : 0,
        mlAccuracy: hasMl ? (82 + Math.random() * 13) * trend : 0
      });
    }
    
    return data;
  };

  const generateTeamData = (): TeamPerformance[] => [
    { teamName: 'Equipo IT', department: 'Tecnología', efficiency: 92, overhead: 38.5, ethicsScore: 88, size: 12, trend: 8.5 },
    { teamName: 'Marketing Digital', department: 'Marketing', efficiency: 85, overhead: 42.1, ethicsScore: 91, size: 8, trend: 5.2 },
    { teamName: 'Finanzas', department: 'Finanzas', efficiency: 89, overhead: 40.8, ethicsScore: 86, size: 6, trend: 3.1 },
    { teamName: 'RRHH', department: 'Recursos Humanos', efficiency: 87, overhead: 45.2, ethicsScore: 94, size: 5, trend: 6.7 },
    { teamName: 'Operaciones', department: 'Operaciones', efficiency: 81, overhead: 48.3, ethicsScore: 82, size: 15, trend: -2.1 },
    { teamName: 'Ventas', department: 'Comercial', efficiency: 83, overhead: 46.7, ethicsScore: 85, size: 10, trend: 4.3 }
  ];

  const generateCategoryData = (): CategoryBreakdown[] => [
    { name: 'Infraestructura', value: 7250, percentage: 15.2, benchmark: 15.0, color: '#3B82F6', trend: -2.3 },
    { name: 'Administrativo', value: 3850, percentage: 8.1, benchmark: 8.5, color: '#10B981', trend: -5.9 },
    { name: 'Beneficios', value: 5720, percentage: 12.0, benchmark: 12.5, color: '#8B5CF6', trend: -4.0 },
    { name: 'Capacitación', value: 1430, percentage: 3.0, benchmark: 3.5, color: '#F59E0B', trend: -14.3 },
    { name: 'Tecnología', value: 2385, percentage: 5.0, benchmark: 5.2, color: '#6366F1', trend: -3.8 },
    ...(hasAura ? [
      { name: 'Impacto Social', value: 950, percentage: 2.0, benchmark: 1.8, color: '#EF4444', trend: 11.1 },
      { name: 'Sustentabilidad', value: 715, percentage: 1.5, benchmark: 1.3, color: '#22C55E', trend: 15.4 },
      { name: 'Bienestar', value: 1190, percentage: 2.5, benchmark: 2.2, color: '#EC4899', trend: 13.6 },
      { name: 'Innovación', value: 950, percentage: 2.0, benchmark: 1.9, color: '#F97316', trend: 5.3 }
    ] : [])
  ];

  // Computed values
  const periodsMap = {
    '7d': 4,   // 4 weeks
    '30d': 12, // 12 weeks
    '90d': 24, // 24 weeks
    '1y': 52,  // 52 weeks
    'all': 104 // 2 years
  };

  const historicalData = useMemo(() => 
    generateHistoricalData(periodsMap[selectedPeriod]), 
    [selectedPeriod]
  );

  const teamData = useMemo(() => generateTeamData(), []);
  const categoryData = useMemo(() => generateCategoryData(), [hasAura]);

  // Latest metrics
  const latestData = historicalData[historicalData.length - 1];
  const previousData = historicalData[historicalData.length - 2];

  const calculateChange = (current: number, previous: number) => 
    previous > 0 ? ((current - previous) / previous) * 100 : 0;

  const metricCards: MetricCard[] = [
    {
      title: 'Overhead Total',
      value: `${latestData?.totalOverhead.toFixed(1)}%`,
      change: calculateChange(latestData?.totalOverhead || 0, previousData?.totalOverhead || 0),
      trend: latestData?.totalOverhead < (previousData?.totalOverhead || 0) ? 'down' : 'up',
      icon: DollarSign,
      color: 'text-blue-600'
    },
    {
      title: 'Eficiencia Promedio',
      value: `${latestData?.efficiency.toFixed(0)}%`,
      change: calculateChange(latestData?.efficiency || 0, previousData?.efficiency || 0),
      trend: latestData?.efficiency > (previousData?.efficiency || 0) ? 'up' : 'down',
      icon: Target,
      color: 'text-green-600'
    },
    {
      title: 'Total Empleados',
      value: latestData?.employees.toString() || '0',
      change: calculateChange(latestData?.employees || 0, previousData?.employees || 0),
      trend: latestData?.employees > (previousData?.employees || 0) ? 'up' : 'down',
      icon: Users,
      color: 'text-purple-600'
    },
    ...(hasAura ? [{
      title: 'Score Ético AURA',
      value: `${latestData?.ethicsScore.toFixed(0)}`,
      change: calculateChange(latestData?.ethicsScore || 0, previousData?.ethicsScore || 0),
      trend: latestData?.ethicsScore > (previousData?.ethicsScore || 0) ? 'up' : 'down' as const,
      icon: Heart,
      color: 'text-red-600'
    }] : []),
    ...(hasMl ? [{
      title: 'Precisión ML',
      value: `${latestData?.mlAccuracy.toFixed(1)}%`,
      change: calculateChange(latestData?.mlAccuracy || 0, previousData?.mlAccuracy || 0),
      trend: latestData?.mlAccuracy > (previousData?.mlAccuracy || 0) ? 'up' : 'down' as const,
      icon: Brain,
      color: 'text-indigo-600'
    }] : [])
  ];

  // Refresh data
  const handleRefresh = async () => {
    setIsLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setLastUpdated(new Date());
    setIsLoading(false);
  };

  return (
    <div className="w-full space-y-6 p-6 bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-900 dark:to-blue-900 min-h-screen">
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div>
          <h1 className="text-3xl lg:text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Dashboard de Overhead
          </h1>
          <p className="text-muted-foreground mt-2 flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Análisis completo con {hasAura && 'AURA™'} {hasAura && hasMl && 'y'} {hasMl && 'Machine Learning'}
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">7 días</SelectItem>
              <SelectItem value="30d">30 días</SelectItem>
              <SelectItem value="90d">90 días</SelectItem>
              <SelectItem value="1y">1 año</SelectItem>
              <SelectItem value="all">Todo</SelectItem>
            </SelectContent>
          </Select>
          
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <Refresh className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
          
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Exportar
          </Button>
        </div>
      </div>

      {/* Last Updated */}
      <div className="text-sm text-muted-foreground flex items-center gap-2">
        <Calendar className="h-4 w-4" />
        Última actualización: {lastUpdated.toLocaleString()}
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metricCards.map((metric, index) => (
          <Card key={index} className="glass hover:shadow-lg transition-all duration-300">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">{metric.title}</p>
                  <p className="text-2xl font-bold mt-1">{metric.value}</p>
                  <div className="flex items-center mt-2">
                    {metric.trend === 'up' ? (
                      <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                    ) : metric.trend === 'down' ? (
                      <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
                    ) : (
                      <ArrowUpDown className="h-4 w-4 text-gray-500 mr-1" />
                    )}
                    <span className={`text-sm font-medium ${
                      metric.trend === 'up' ? 'text-green-600' : 
                      metric.trend === 'down' ? 'text-red-600' : 'text-gray-600'
                    }`}>
                      {Math.abs(metric.change).toFixed(1)}%
                    </span>
                  </div>
                </div>
                <div className={`p-3 rounded-full bg-gradient-to-br ${
                  index % 4 === 0 ? 'from-blue-100 to-blue-200' :
                  index % 4 === 1 ? 'from-green-100 to-green-200' :
                  index % 4 === 2 ? 'from-purple-100 to-purple-200' :
                  'from-red-100 to-red-200'
                }`}>
                  <metric.icon className={`h-6 w-6 ${metric.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Historical Trend */}
        <Card className="xl:col-span-2 glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <LineChart className="h-5 w-5" />
              Tendencia Histórica de Overhead
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={historicalData}>
                  <defs>
                    <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1}/>
                    </linearGradient>
                    <linearGradient id="colorTraditional" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0.1}/>
                    </linearGradient>
                    {hasAura && (
                      <linearGradient id="colorAura" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.1}/>
                      </linearGradient>
                    )}
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="period" />
                  <YAxis />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                      border: 'none', 
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }} 
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="totalOverhead"
                    stroke="#3B82F6"
                    fillOpacity={1}
                    fill="url(#colorTotal)"
                    name="Overhead Total"
                  />
                  <Area
                    type="monotone"
                    dataKey="traditionalOverhead"
                    stroke="#10B981"
                    fillOpacity={1}
                    fill="url(#colorTraditional)"
                    name="Overhead Tradicional"
                  />
                  {hasAura && (
                    <Area
                      type="monotone"
                      dataKey="auraOverhead"
                      stroke="#8B5CF6"
                      fillOpacity={1}
                      fill="url(#colorAura)"
                      name="AURA Enhanced"
                    />
                  )}
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Category Breakdown */}
        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChartIcon className="h-5 w-5" />
              Distribución por Categoría
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 mb-4">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number) => [`$${value.toLocaleString()}`, 'Valor']}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            <div className="space-y-2">
              {categoryData.slice(0, 6).map((category, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: category.color }}
                    />
                    <span className="font-medium">{category.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">{category.percentage}%</span>
                    <span className={`text-xs px-1 py-0.5 rounded ${
                      category.trend > 0 ? 'text-green-700 bg-green-100' : 'text-red-700 bg-red-100'
                    }`}>
                      {category.trend > 0 ? '+' : ''}{category.trend.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analysis */}
      <Tabs defaultValue="teams" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="teams">Equipos</TabsTrigger>
          <TabsTrigger value="efficiency">Eficiencia</TabsTrigger>
          {hasAura && <TabsTrigger value="aura">AURA</TabsTrigger>}
          {hasMl && <TabsTrigger value="ml">Machine Learning</TabsTrigger>}
        </TabsList>

        {/* Team Performance */}
        <TabsContent value="teams">
          <Card className="glass">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Rendimiento por Equipos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80 mb-6">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart data={teamData}>
                    <CartesianGrid />
                    <XAxis 
                      type="number" 
                      dataKey="overhead" 
                      name="Overhead %" 
                      domain={['dataMin - 2', 'dataMax + 2']}
                    />
                    <YAxis 
                      type="number" 
                      dataKey="efficiency" 
                      name="Eficiencia %" 
                      domain={['dataMin - 5', 'dataMax + 5']}
                    />
                    <Tooltip 
                      cursor={{ strokeDasharray: '3 3' }}
                      content={({ payload }) => {
                        if (payload && payload[0]) {
                          const data = payload[0].payload;
                          return (
                            <div className="bg-white p-3 border rounded-lg shadow-lg">
                              <p className="font-semibold">{data.teamName}</p>
                              <p className="text-sm">Departamento: {data.department}</p>
                              <p className="text-sm">Overhead: {data.overhead.toFixed(1)}%</p>
                              <p className="text-sm">Eficiencia: {data.efficiency.toFixed(0)}%</p>
                              <p className="text-sm">Tamaño: {data.size} personas</p>
                              {hasAura && <p className="text-sm">Score Ético: {data.ethicsScore}</p>}
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Scatter 
                      name="Equipos" 
                      dataKey="efficiency" 
                      fill="#3B82F6"
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {teamData.map((team, index) => (
                  <Card key={index} className="border-l-4 border-l-blue-500">
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold">{team.teamName}</h4>
                        <Badge variant={team.trend > 0 ? 'default' : 'destructive'}>
                          {team.trend > 0 ? '+' : ''}{team.trend.toFixed(1)}%
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">{team.department}</p>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Eficiencia</span>
                          <span className="font-medium">{team.efficiency}%</span>
                        </div>
                        <Progress value={team.efficiency} className="h-2" />
                        
                        <div className="flex justify-between text-sm">
                          <span>Overhead</span>
                          <span className="font-medium">{team.overhead}%</span>
                        </div>
                        
                        {hasAura && (
                          <div className="flex justify-between text-sm">
                            <span>Score Ético</span>
                            <span className="font-medium">{team.ethicsScore}</span>
                          </div>
                        )}
                        
                        <div className="flex justify-between text-sm">
                          <span>Tamaño</span>
                          <span className="font-medium">{team.size} personas</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Efficiency Analysis */}
        <TabsContent value="efficiency">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Análisis de Eficiencia
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={historicalData.slice(-8)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="period" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="efficiency" fill="#10B981" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Comparativa Benchmarks
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {categoryData.slice(0, 5).map((category, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium">{category.name}</span>
                        <div className="flex items-center gap-2 text-sm">
                          <span>{category.percentage.toFixed(1)}%</span>
                          <span className="text-muted-foreground">vs</span>
                          <span className="text-muted-foreground">{category.benchmark.toFixed(1)}%</span>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <div className="flex-1">
                          <Progress 
                            value={(category.percentage / category.benchmark) * 50} 
                            className="h-2" 
                          />
                        </div>
                        <div className="w-16 text-right">
                          {category.percentage < category.benchmark ? (
                            <Badge variant="default" className="text-xs">
                              -{(category.benchmark - category.percentage).toFixed(1)}%
                            </Badge>
                          ) : (
                            <Badge variant="destructive" className="text-xs">
                              +{(category.percentage - category.benchmark).toFixed(1)}%
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* AURA Analysis */}
        {hasAura && (
          <TabsContent value="aura">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Heart className="h-5 w-5 text-red-500" />
                    Análisis Ético AURA
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={[
                        { subject: 'Ética', A: latestData?.ethicsScore || 0, fullMark: 100 },
                        { subject: 'Equidad', A: 87, fullMark: 100 },
                        { subject: 'Sustentabilidad', A: latestData?.sustainabilityScore || 0, fullMark: 100 },
                        { subject: 'Transparencia', A: 92, fullMark: 100 },
                        { subject: 'Responsabilidad', A: 89, fullMark: 100 },
                        { subject: 'Innovación', A: 85, fullMark: 100 }
                      ]}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="subject" />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} />
                        <Radar
                          name="Score AURA"
                          dataKey="A"
                          stroke="#EF4444"
                          fill="#EF4444"
                          fillOpacity={0.3}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              <Card className="glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Leaf className="h-5 w-5 text-green-500" />
                    Impacto de Sustentabilidad
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-600 mb-2">
                        {latestData?.sustainabilityScore.toFixed(0)}
                      </div>
                      <p className="text-sm text-muted-foreground">Score de Sustentabilidad</p>
                    </div>
                    
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Reducción CO₂</span>
                        <Badge variant="default">-15%</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Eficiencia Energética</span>
                        <Badge variant="default">+22%</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Waste Reduction</span>
                        <Badge variant="default">-30%</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Bienestar Empleados</span>
                        <Badge variant="default">+18%</Badge>
                      </div>
                    </div>

                    <div className="border-t pt-4">
                      <h4 className="font-medium mb-2">Recomendaciones AURA</h4>
                      <ul className="space-y-2 text-sm text-muted-foreground">
                        <li className="flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          Implementar programa de home office híbrido
                        </li>
                        <li className="flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          Optimizar infraestructura tecnológica
                        </li>
                        <li className="flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                          Revisar políticas de bienestar mental
                        </li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        )}

        {/* ML Analysis */}
        {hasMl && (
          <TabsContent value="ml">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5 text-indigo-500" />
                    Rendimiento de Modelos ML
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                      <span className="font-medium">Random Forest</span>
                      <div className="text-right">
                        <div className="text-lg font-bold text-indigo-600">87.3%</div>
                        <div className="text-xs text-muted-foreground">Accuracy</div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                      <span className="font-medium">AURA Enhanced</span>
                      <div className="text-right">
                        <div className="text-lg font-bold text-purple-600">91.7%</div>
                        <div className="text-xs text-muted-foreground">Accuracy</div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <span className="font-medium">Hybrid ML+AURA</span>
                      <div className="text-right">
                        <div className="text-lg font-bold text-green-600">94.1%</div>
                        <div className="text-xs text-muted-foreground">Accuracy</div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-6 pt-4 border-t">
                    <h4 className="font-medium mb-3">Predicciones Recientes</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Ahorro Potencial</span>
                        <span className="font-medium text-green-600">$12,450/mes</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Confianza Promedio</span>
                        <span className="font-medium">89.3%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Optimizaciones Aplicadas</span>
                        <span className="font-medium">23 de 31</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="h-5 w-5 text-yellow-500" />
                    Optimizaciones Automatizadas
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="border-l-4 border-l-green-500 pl-4">
                      <h4 className="font-medium text-green-700">Infraestructura</h4>
                      <p className="text-sm text-muted-foreground">
                        Consolidación de servidores detectada. Ahorro estimado: $2,100/mes
                      </p>
                      <Badge variant="default" className="mt-1">Aplicado</Badge>
                    </div>
                    
                    <div className="border-l-4 border-l-blue-500 pl-4">
                      <h4 className="font-medium text-blue-700">Procesos Admin</h4>
                      <p className="text-sm text-muted-foreground">
                        Automatización de reportes. Reducción 35% tiempo manual
                      </p>
                      <Badge variant="secondary" className="mt-1">En proceso</Badge>
                    </div>
                    
                    <div className="border-l-4 border-l-orange-500 pl-4">
                      <h4 className="font-medium text-orange-700">Capacitación</h4>
                      <p className="text-sm text-muted-foreground">
                        Optimización calendario training. Eficiencia +28%
                      </p>
                      <Badge variant="outline" className="mt-1">Pendiente</Badge>
                    </div>
                  </div>
                  
                  <div className="mt-6 pt-4 border-t">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">ROI de Optimizaciones</span>
                      <span className="text-lg font-bold text-green-600">347%</span>
                    </div>
                    <Progress value={87} className="h-2" />
                    <p className="text-xs text-muted-foreground mt-1">
                      Target: 300% | Actual: 347%
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        )}
      </Tabs>

      {/* Action Items */}
      <Card className="glass border-orange-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Star className="h-5 w-5 text-yellow-500" />
            Acciones Recomendadas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 border rounded-lg bg-red-50 dark:bg-red-900/10 border-red-200">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-red-500" />
                <Badge variant="destructive">Alta Prioridad</Badge>
              </div>
              <h4 className="font-medium">Revisar Equipo Operaciones</h4>
              <p className="text-sm text-muted-foreground mt-1">
                Overhead 48.3% por encima del benchmark. Posible optimización de $3,200/mes.
              </p>
            </div>
            
            <div className="p-4 border rounded-lg bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200">
              <div className="flex items-center gap-2 mb-2">
                <Info className="h-4 w-4 text-yellow-500" />
                <Badge variant="secondary">Media Prioridad</Badge>
              </div>
              <h4 className="font-medium">Actualizar Modelo ML</h4>
              <p className="text-sm text-muted-foreground mt-1">
                Nuevos datos disponibles. Reentrenamiento podría mejorar accuracy +2.3%.
              </p>
            </div>
            
            <div className="p-4 border rounded-lg bg-green-50 dark:bg-green-900/10 border-green-200">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <Badge variant="default">Oportunidad</Badge>
              </div>
              <h4 className="font-medium">Expandir AURA Enhanced</h4>
              <p className="text-sm text-muted-foreground mt-1">
                Equipos con AURA muestran 15% mayor eficiencia. Considerar expansión.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};