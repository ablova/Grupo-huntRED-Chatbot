import React from 'react';
import { 
  ArrowUpIcon, 
  ArrowDownIcon, 
  UserGroupIcon, 
  ChartBarIcon, 
  ClockIcon, 
  CurrencyDollarIcon,
  DocumentTextIcon
} from '@heroicons/react/outline';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

// Datos de ejemplo - reemplazar con datos reales de la API
const metrics = [
  {
    name: 'Usuarios Activos',
    value: '2,345',
    change: 12.5,
    changeType: 'increase',
    icon: UserGroupIcon,
  },
  {
    name: 'Tiempo Promedio',
    value: '2.5h',
    change: 3.2,
    changeType: 'decrease',
    icon: ClockIcon,
  },
  {
    name: 'Ingresos',
    value: '$34,543',
    change: 8.1,
    changeType: 'increase',
    icon: CurrencyDollarIcon,
  },
  {
    name: 'Tareas Completadas',
    value: '1,234',
    change: 5.7,
    changeType: 'increase',
    icon: DocumentTextIcon,
  },
];

const activityData = [
  { name: 'Ene', usuarios: 4000, tareas: 2400 },
  { name: 'Feb', usuarios: 3000, tareas: 1398 },
  { name: 'Mar', usuarios: 2000, tareas: 9800 },
  { name: 'Abr', usuarios: 2780, tareas: 3908 },
  { name: 'May', usuarios: 1890, tareas: 4800 },
  { name: 'Jun', usuarios: 2390, tareas: 3800 },
  { name: 'Jul', usuarios: 3490, tareas: 4300 },
];

const recentActivity = [
  { id: 1, user: 'Juan Pérez', action: 'creó un nuevo proyecto', time: 'Hace 5 minutos', icon: 'add' },
  { id: 2, user: 'María García', action: 'completó la tarea: Diseño UI', time: 'Hace 1 hora', icon: 'check' },
  { id: 3, user: 'Carlos López', action: 'subió un archivo', time: 'Hace 2 horas', icon: 'upload' },
  { id: 4, user: 'Ana Martínez', action: 'comentó en: Reunión de equipo', time: 'Hace 3 horas', icon: 'comment' },
  { id: 5, user: 'Luis Rodríguez', action: 'actualizó el perfil', time: 'Ayer', icon: 'user' },
];

const DashboardPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Panel de Control</h1>
        <div className="flex space-x-3">
          <select
            className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            defaultValue="this-week"
          >
            <option value="this-week">Esta semana</option>
            <option value="last-week">La semana pasada</option>
            <option value="this-month">Este mes</option>
            <option value="last-month">El mes pasado</option>
          </select>
          <button
            type="button"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Exportar
          </button>
        </div>
      </div>

      {/* Métricas */}
      <div className="grid grid-cols-1 gap-5 mt-6 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <div
            key={metric.name}
            className="px-4 py-5 overflow-hidden bg-white rounded-lg shadow sm:p-6 hover:shadow-md transition-shadow duration-200"
          >
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-md bg-blue-50">
                <metric.icon className="w-6 h-6 text-blue-600" aria-hidden="true" />
              </div>
              <div className="flex-1 w-0 ml-5">
                <dt className="text-sm font-medium text-gray-500 truncate">
                  {metric.name}
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {metric.value}
                  </div>
                  <div
                    className={classNames(
                      metric.changeType === 'increase' ? 'text-green-600' : 'text-red-600',
                      'ml-2 flex items-baseline text-sm font-semibold'
                    )}
                  >
                    {metric.changeType === 'increase' ? (
                      <ArrowUpIcon className="self-center flex-shrink-0 w-5 h-5 text-green-500" />
                    ) : (
                      <ArrowDownIcon className="self-center flex-shrink-0 w-5 h-5 text-red-500" />
                    )}
                    <span className="sr-only">
                      {metric.changeType === 'increase' ? 'Aumentó' : 'Disminuyó'} por
                    </span>
                    {metric.change}%
                  </div>
                </dd>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 gap-6 mt-8 lg:grid-cols-2">
        <div className="p-6 bg-white rounded-lg shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Actividad Mensual</h3>
            <div className="flex space-x-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Usuarios
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Tareas
              </span>
            </div>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={activityData}
                margin={{
                  top: 5,
                  right: 30,
                  left: 20,
                  bottom: 5,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="usuarios" stroke="#3B82F6" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="tareas" stroke="#10B981" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-6 bg-white rounded-lg shadow">
          <h3 className="mb-4 text-lg font-medium text-gray-900">Distribución por Categoría</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={activityData}
                margin={{
                  top: 5,
                  right: 30,
                  left: 20,
                  bottom: 5,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="usuarios" fill="#3B82F6" name="Usuarios" />
                <Bar dataKey="tareas" fill="#10B981" name="Tareas" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Actividad Reciente */}
      <div className="mt-8">
        <div className="px-6 py-5 bg-white border-b border-gray-200 rounded-t-lg">
          <h3 className="text-lg font-medium text-gray-900">Actividad Reciente</h3>
        </div>
        <div className="overflow-hidden bg-white shadow rounded-b-lg">
          <ul className="divide-y divide-gray-200">
            {recentActivity.map((activity) => (
              <li key={activity.id} className="px-6 py-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="text-blue-600">
                      {activity.icon === 'add' && '+'} 
                      {activity.icon === 'check' && '✓'}
                      {activity.icon === 'upload' && '↑'}
                      {activity.icon === 'comment' && '💬'}
                      {activity.icon === 'user' && '👤'}
                    </span>
                  </div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-900">
                      {activity.user} <span className="font-normal text-gray-500">{activity.action}</span>
                    </div>
                    <div className="text-sm text-gray-500">{activity.time}</div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
          <div className="px-6 py-3 text-sm text-center border-t border-gray-200 bg-gray-50">
            <a href="#" className="font-medium text-blue-600 hover:text-blue-500">
              Ver toda la actividad
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

// Función auxiliar para combinar clases
export function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

export default DashboardPage;
