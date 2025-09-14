import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

interface ConnectionStatusProps {
  className?: string;
}

export function ConnectionStatus({ className = '' }: ConnectionStatusProps) {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [isDemoMode, setIsDemoMode] = useState(false);

  useEffect(() => {
    let mounted = true;

    const checkConnection = async () => {
      try {
        const connected = await apiService.checkConnection();
        if (mounted) {
          setIsConnected(connected);
          setIsDemoMode(!connected);
        }
      } catch (error) {
        if (mounted) {
          setIsConnected(false);
          setIsDemoMode(true);
        }
      }
    };

    // Initial check
    checkConnection();

    // Check every 30 seconds
    const interval = setInterval(checkConnection, 30000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (isConnected === null) {
    return (
      <div className={`flex items-center text-sm ${className}`}>
        <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2 animate-pulse"></div>
        <span className="text-gray-400">Connecting...</span>
      </div>
    );
  }

  return (
    <div className={`flex items-center text-sm ${className}`}>
      <div
        className={`w-2 h-2 rounded-full mr-2 ${
          isConnected ? 'bg-green-500' : 'bg-orange-500'
        }`}
      ></div>
      <span className={isConnected ? 'text-green-400' : 'text-orange-400'}>
        {isConnected ? 'Live Data' : 'Demo Mode'}
      </span>
      {isDemoMode && (
        <span className="text-xs text-gray-500 ml-2">
          (Using mock data)
        </span>
      )}
    </div>
  );
}