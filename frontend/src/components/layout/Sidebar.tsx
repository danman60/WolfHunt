import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '../../utils/cn';
import {
  ChartBarIcon,
  CogIcon,
  HomeIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  Bars3Icon,
  XMarkIcon,
  ShieldCheckIcon,
  BoltIcon
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Intelligence Brief', href: '/intelligence', icon: BoltIcon },
  { name: 'Wolf Configuration', href: '/configuration', icon: CogIcon },
  { name: 'History', href: '/history', icon: ClockIcon },
  { name: 'Risk Management', href: '/risk', icon: ShieldCheckIcon },
  { name: 'Alerts', href: '/alerts', icon: ExclamationTriangleIcon },
];

interface SidebarProps {
  isCollapsed?: boolean;
  onToggle?: () => void;
}

export function Sidebar({ isCollapsed = false, onToggle }: SidebarProps) {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <>
      {/* Mobile menu button */}
      <div className="lg:hidden">
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 text-gray-400 hover:text-white"
        >
          {mobileMenuOpen ? (
            <XMarkIcon className="w-6 h-6" />
          ) : (
            <Bars3Icon className="w-6 h-6" />
          )}
        </button>
      </div>

      {/* Desktop sidebar */}
      <div className={cn(
        'hidden lg:flex lg:flex-col lg:fixed lg:inset-y-0 lg:z-50',
        'bg-gray-900 border-r border-gray-700 transition-all duration-300',
        isCollapsed ? 'lg:w-16' : 'lg:w-64'
      )}>
        <div className="flex flex-col flex-1 min-h-0">
          {/* Logo */}
          <div className="flex items-center h-16 px-4 bg-gray-800">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">W</span>
              </div>
              {!isCollapsed && (
                <div className="ml-3">
                  <div className="text-white font-semibold text-lg">WolfHunt</div>
                  <div className="text-gray-400 text-xs">Trading Bot</div>
                </div>
              )}
            </div>
            
            {/* Collapse toggle */}
            <button
              onClick={onToggle}
              className={cn(
                'ml-auto p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-gray-700 transition-colors',
                isCollapsed && 'ml-0'
              )}
            >
              <ArrowPathIcon className={cn('w-4 h-4 transition-transform', isCollapsed && 'rotate-180')} />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-2 py-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href || 
                               (item.name === 'Wolf Configuration' && 
                                (location.pathname === '/trading' || location.pathname === '/strategy'));
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors',
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-700'
                  )}
                  title={isCollapsed ? item.name : undefined}
                >
                  <item.icon
                    className={cn(
                      'flex-shrink-0 w-5 h-5',
                      isActive ? 'text-white' : 'text-gray-400 group-hover:text-white',
                      !isCollapsed && 'mr-3'
                    )}
                  />
                  {!isCollapsed && item.name}
                </Link>
              );
            })}
          </nav>

          {/* Status indicator */}
          <div className="flex-shrink-0 px-4 py-4 border-t border-gray-700">
            <SystemStatus isCollapsed={isCollapsed} />
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden">
          <div className="fixed inset-0 z-50 flex">
            <div
              className="fixed inset-0 bg-black/25"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="relative flex flex-col w-full max-w-xs bg-gray-900">
              <div className="flex items-center justify-between h-16 px-4 bg-gray-800">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-sm">W</span>
                  </div>
                  <div className="ml-3">
                    <div className="text-white font-semibold text-lg">WolfHunt</div>
                    <div className="text-gray-400 text-xs">Trading Bot</div>
                  </div>
                </div>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-2 text-gray-400 hover:text-white"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>
              
              <nav className="flex-1 px-2 py-4 space-y-1">
                {navigation.map((item) => {
                  const isActive = location.pathname === item.href;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={cn(
                        'group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors',
                        isActive
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-400 hover:text-white hover:bg-gray-700'
                      )}
                    >
                      <item.icon className="flex-shrink-0 w-5 h-5 mr-3" />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>
              
              <div className="flex-shrink-0 px-4 py-4 border-t border-gray-700">
                <SystemStatus />
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function SystemStatus({ isCollapsed = false }: { isCollapsed?: boolean }) {
  const status = 'healthy'; // This would come from your app state
  const statusConfig = {
    healthy: { color: 'bg-green-400', text: 'System Healthy' },
    warning: { color: 'bg-yellow-400', text: 'System Warning' },
    error: { color: 'bg-red-400', text: 'System Error' }
  };

  return (
    <div className={cn('flex items-center', isCollapsed ? 'justify-center' : 'justify-start')}>
      <div className={cn('w-2 h-2 rounded-full animate-pulse', statusConfig[status].color)} />
      {!isCollapsed && (
        <span className="ml-2 text-sm text-gray-400">{statusConfig[status].text}</span>
      )}
    </div>
  );
}