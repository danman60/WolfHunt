import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiService } from '../services/api';

interface PriceData {
  price: number;
  change24h: number;
}

interface PriceContextType {
  prices: { [symbol: string]: PriceData };
  lastUpdate: Date | null;
  isLoading: boolean;
  error: string | null;
  isStale: boolean;
}

const PriceContext = createContext<PriceContextType>({
  prices: {},
  lastUpdate: null,
  isLoading: false,
  error: null,
  isStale: false
});

interface PriceProviderProps {
  children: ReactNode;
}

export function PriceProvider({ children }: PriceProviderProps) {
  const [prices, setPrices] = useState<{ [symbol: string]: PriceData }>({});
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isStale, setIsStale] = useState(false);

  const fetchPrices = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const newPrices = await apiService.getGMXPrices();
      
      if (newPrices && typeof newPrices === 'object') {
        setPrices(newPrices);
        setLastUpdate(new Date());
        setIsStale(false);
        console.log('Real CoinGecko prices loaded:', newPrices);
      } else {
        throw new Error('Invalid price data received');
      }
    } catch (fetchError) {
      console.warn('Failed to fetch prices, keeping previous prices if available:', fetchError);
      setError(fetchError instanceof Error ? fetchError.message : 'Price fetch failed');
      
      // Only set fallback prices if we have NO prices currently (first load failure)
      // Otherwise, preserve the last known good prices
      if (Object.keys(prices).length === 0) {
        console.log('No previous prices available, using fallback prices');
        const fallbackPrices = {
          'BTC-USD': { price: 95000, change24h: 1.67 },
          'ETH-USD': { price: 4200, change24h: 1.58 },
          'LINK-USD': { price: 23.50, change24h: 3.61 }
        };
        
        setPrices(fallbackPrices);
        setLastUpdate(new Date());
        setIsStale(false);
      } else {
        console.log(`Preserving ${Object.keys(prices).length} previous prices - API temporarily unavailable`);
        // Keep existing prices, don't update lastUpdate time to show data is stale
        setIsStale(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchPrices();

    // Set up interval for regular updates
    const interval = setInterval(fetchPrices, 30000); // 30 seconds

    // Cleanup function
    return () => {
      clearInterval(interval);
    };
  }, []); // Empty dependency array - only run once

  const contextValue: PriceContextType = {
    prices,
    lastUpdate,
    isLoading,
    error,
    isStale
  };

  return (
    <PriceContext.Provider value={contextValue}>
      {children}
    </PriceContext.Provider>
  );
}

export function usePrices(): PriceContextType {
  const context = useContext(PriceContext);
  if (!context) {
    throw new Error('usePrices must be used within a PriceProvider');
  }
  return context;
}