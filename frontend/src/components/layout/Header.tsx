import { Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import {
  BellIcon,
  UserIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  ChevronDownIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import { cn } from '../../utils/cn';
import { ConnectionStatus } from '../ConnectionStatus';

interface HeaderProps {
  user?: {
    name: string;
    email: string;
    avatar?: string;
  };
  notifications?: number;
  onLogout?: () => void;
  onSettings?: () => void;
  tradingMode?: 'paper' | 'live';
}

export function Header({ 
  user = { name: 'Trading User', email: 'user@example.com' },
  notifications = 0,
  onLogout,
  onSettings,
  tradingMode = 'paper'
}: HeaderProps) {
  return (
    <header className="bg-gray-900 border-b border-gray-700 px-4 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between h-16">
        {/* Left side - Trading mode indicator and connection status */}
        <div className="flex items-center space-x-4">
          <div className={cn(
            'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium',
            tradingMode === 'live'
              ? 'bg-red-100 text-red-800 border border-red-200'
              : 'bg-blue-100 text-blue-800 border border-blue-200'
          )}>
            <div className={cn(
              'w-2 h-2 rounded-full mr-2',
              tradingMode === 'live' ? 'bg-red-400' : 'bg-blue-400'
            )} />
            {tradingMode === 'live' ? 'LIVE TRADING' : 'PAPER TRADING'}
            {tradingMode === 'live' && (
              <ExclamationCircleIcon className="w-4 h-4 ml-1" />
            )}
          </div>
          <ConnectionStatus />
        </div>

        {/* Right side - Notifications and user menu */}
        <div className="flex items-center space-x-4">
          {/* Notifications */}
          <button
            type="button"
            className="relative p-1 text-gray-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-white/20 focus:ring-offset-2 focus:ring-offset-gray-800 rounded-lg"
          >
            <span className="sr-only">View notifications</span>
            <BellIcon className="w-6 h-6" />
            {notifications > 0 && (
              <span className="absolute top-0 right-0 -mt-1 -mr-1 px-2 py-1 text-xs font-medium text-white bg-red-600 rounded-full min-w-[20px] flex items-center justify-center">
                {notifications > 99 ? '99+' : notifications}
              </span>
            )}
          </button>

          {/* User menu dropdown */}
          <Menu as="div" className="relative">
            <div>
              <Menu.Button className="flex items-center max-w-xs text-sm text-white focus:outline-none focus:ring-2 focus:ring-white/20 focus:ring-offset-2 focus:ring-offset-gray-800 rounded-lg p-2">
                <span className="sr-only">Open user menu</span>
                <div className="flex items-center space-x-3">
                  {user.avatar ? (
                    <img
                      className="w-8 h-8 rounded-full"
                      src={user.avatar}
                      alt={user.name}
                    />
                  ) : (
                    <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                      <UserIcon className="w-5 h-5 text-gray-300" />
                    </div>
                  )}
                  <div className="hidden sm:block text-left">
                    <div className="text-sm font-medium text-white">{user.name}</div>
                    <div className="text-xs text-gray-400">{user.email}</div>
                  </div>
                  <ChevronDownIcon className="w-4 h-4 text-gray-400" />
                </div>
              </Menu.Button>
            </div>
            
            <Transition
              as={Fragment}
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
              <Menu.Items className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-gray-800 py-1 shadow-lg ring-1 ring-black/5 focus:outline-none border border-gray-700">
                <div className="px-4 py-2 border-b border-gray-700">
                  <div className="text-sm font-medium text-white">{user.name}</div>
                  <div className="text-xs text-gray-400">{user.email}</div>
                </div>
                
                <Menu.Item>
                  {({ active }) => (
                    <button
                      onClick={onSettings}
                      className={cn(
                        'flex items-center w-full px-4 py-2 text-sm text-gray-300',
                        active && 'bg-gray-700 text-white'
                      )}
                    >
                      <Cog6ToothIcon className="w-4 h-4 mr-3" />
                      Settings
                    </button>
                  )}
                </Menu.Item>
                
                <Menu.Item>
                  {({ active }) => (
                    <button
                      onClick={onLogout}
                      className={cn(
                        'flex items-center w-full px-4 py-2 text-sm text-gray-300',
                        active && 'bg-gray-700 text-white'
                      )}
                    >
                      <ArrowRightOnRectangleIcon className="w-4 h-4 mr-3" />
                      Sign out
                    </button>
                  )}
                </Menu.Item>
              </Menu.Items>
            </Transition>
          </Menu>
        </div>
      </div>
    </header>
  );
}