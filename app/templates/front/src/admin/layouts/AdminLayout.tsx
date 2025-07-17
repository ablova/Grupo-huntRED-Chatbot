import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { 
  HomeIcon, 
  UsersIcon, 
  CogIcon, 
  ChartBarIcon, 
  DocumentTextIcon,
  MenuAlt2Icon,
  XIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/outline';
import { adminConfig } from '../config';

const navigation = [
  { name: 'Dashboard', href: adminConfig.routes.dashboard, icon: HomeIcon, current: true },
  { name: 'Usuarios', href: adminConfig.routes.users, icon: UsersIcon, current: false },
  { name: 'Reportes', href: '#', icon: ChartBarIcon, current: false },
  { name: 'Documentación', href: '#', icon: DocumentTextIcon, current: false },
  { name: 'Configuración', href: adminConfig.routes.settings, icon: CogIcon, current: false },
];

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

export const AdminLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  // Actualizar el estado activo según la ruta actual
  const updatedNavigation = navigation.map(item => ({
    ...item,
    current: location.pathname === item.href,
  }));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile menu */}
      <div className="lg:hidden">
        <div className="fixed inset-0 z-40 flex">
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)}></div>
          <div className="relative flex flex-col flex-1 w-full max-w-xs bg-white">
            <div className="absolute top-0 right-0 p-1 -mr-14">
              <button
                type="button"
                className="flex items-center justify-center w-12 h-12 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                onClick={() => setSidebarOpen(false)}
              >
                <XIcon className="w-6 h-6 text-white" aria-hidden="true" />
                <span className="sr-only">Cerrar menú</span>
              </button>
            </div>
            <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
              <div className="flex items-center flex-shrink-0 px-4">
                <img
                  className="w-auto h-8"
                  src="/logo.svg"
                  alt="huntRED"
                />
                <span className="ml-2 text-xl font-bold text-gray-900">Admin</span>
              </div>
              <nav className="px-2 mt-5 space-y-1">
                {updatedNavigation.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={classNames(
                      item.current
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                      'group flex items-center px-2 py-2 text-base font-medium rounded-md'
                    )}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <item.icon
                      className={classNames(
                        item.current ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500',
                        'mr-4 flex-shrink-0 h-6 w-6'
                      )}
                      aria-hidden="true"
                    />
                    {item.name}
                  </Link>
                ))}
              </nav>
            </div>
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:flex lg:flex-shrink-0">
        <div
          className={`flex flex-col transition-all duration-300 ease-in-out ${
            collapsed ? 'w-20' : 'w-64'
          }`}
        >
          <div className="flex flex-col flex-1 min-h-0 border-r border-gray-200 bg-white">
            <div className="flex flex-col flex-1 pt-5 pb-4 overflow-y-auto">
              <div className="flex items-center flex-shrink-0 px-4">
                <img
                  className="w-auto h-8"
                  src="/logo.svg"
                  alt="huntRED"
                />
                {!collapsed && (
                  <span className="ml-2 text-xl font-bold text-gray-900">Admin</span>
                )}
              </div>
              <nav className="flex-1 px-2 mt-5 space-y-1 bg-white">
                {updatedNavigation.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={classNames(
                      item.current
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                      'group flex items-center px-2 py-2 text-sm font-medium rounded-md',
                      collapsed ? 'justify-center' : ''
                    )}
                  >
                    <item.icon
                      className={classNames(
                        item.current ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500',
                        'flex-shrink-0 h-6 w-6',
                        !collapsed ? 'mr-3' : 'mx-auto'
                      )}
                      aria-hidden="true"
                    />
                    {!collapsed && item.name}
                  </Link>
                ))}
              </nav>
            </div>
            <div className="flex flex-shrink-0 p-4 border-t border-gray-200">
              <button
                onClick={() => setCollapsed(!collapsed)}
                className="flex items-center justify-center w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {collapsed ? (
                  <ChevronRightIcon className="w-5 h-5 text-gray-500" />
                ) : (
                  <>
                    <ChevronLeftIcon className="w-5 h-5 mr-2 text-gray-500" />
                    Contraer menú
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="flex flex-col flex-1 overflow-hidden">
          <div className="relative z-10 flex items-center justify-between flex-shrink-0 h-16 bg-white border-b border-gray-200 lg:hidden">
            <button
              type="button"
              className="px-4 text-gray-500 border-r border-gray-200 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 lg:hidden"
              onClick={() => setSidebarOpen(true)}
            >
              <span className="sr-only">Abrir menú</span>
              <MenuAlt2Icon className="w-6 h-6" aria-hidden="true" />
            </button>
            <div className="flex items-center px-4">
              <div className="flex-shrink-0">
                <img
                  className="w-auto h-8"
                  src="/logo.svg"
                  alt="huntRED"
                />
              </div>
              <span className="ml-2 text-lg font-bold text-gray-900">Admin</span>
            </div>
            <div className="w-12"></div> {/* Spacer for alignment */}
          </div>

          <main className="flex-1 overflow-y-auto focus:outline-none">
            <div className="relative z-0 flex flex-1 overflow-hidden">
              <div className="relative flex-1 overflow-y-auto">
                <div className="p-6">
                  <Outlet />
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default AdminLayout;
