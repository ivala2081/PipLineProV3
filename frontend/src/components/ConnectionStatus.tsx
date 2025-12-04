import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface ConnectionStatusProps {
  className?: string;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ className = '' }) => {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const checkConnection = async () => {
    try {
      setStatus('connecting');
      const response = await axios.get('/api/v1/health/', { timeout: 5000 });
      if (response.status === 200) {
        setStatus('connected');
        setLastChecked(new Date());
      } else {
        setStatus('disconnected');
      }
    } catch (error) {
      console.error('Connection check failed:', error);
      setStatus('disconnected');
      setLastChecked(new Date());
    }
  };

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const getStatusStyles = () => {
    switch (status) {
      case 'connected': 
        return {
          bg: 'bg-gradient-to-r from-emerald-50 to-green-50',
          border: 'border-emerald-200',
          text: 'text-emerald-700',
          dot: 'bg-emerald-500',
          shadow: 'shadow-emerald-100'
        };
      case 'disconnected': 
        return {
          bg: 'bg-gradient-to-r from-red-50 to-rose-50',
          border: 'border-red-200',
          text: 'text-red-700',
          dot: 'bg-red-500',
          shadow: 'shadow-red-100'
        };
      case 'connecting': 
        return {
          bg: 'bg-gradient-to-r from-amber-50 to-yellow-50',
          border: 'border-amber-200',
          text: 'text-amber-700',
          dot: 'bg-amber-500',
          shadow: 'shadow-amber-100'
        };
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'connected': 
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'disconnected': 
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'connecting': 
        return (
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        );
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected': return 'Connected';
      case 'disconnected': return 'Disconnected';
      case 'connecting': return 'Connecting';
    }
  };

  const styles = getStatusStyles();

  return (
    <div 
      className={`relative transition-all duration-300 ease-in-out ${className}`}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      {/* Main Status Indicator */}
      <div className={`
        flex items-center gap-2 px-3 py-2 rounded-xl border backdrop-blur-sm
        ${styles.bg} ${styles.border} ${styles.text} ${styles.shadow}
        shadow-lg transition-all duration-300 ease-in-out cursor-pointer
        hover:scale-105 hover:shadow-xl
      `}>
        {/* Status Dot with Pulse Animation */}
        <div className="relative">
          <div className={`w-2 h-2 rounded-full ${styles.dot}`}></div>
          {status === 'connected' && (
            <div className={`absolute inset-0 w-2 h-2 rounded-full ${styles.dot} animate-ping opacity-75`}></div>
          )}
        </div>
        
        {/* Status Icon */}
        <div className="flex items-center">
          {getStatusIcon()}
        </div>
        
        {/* Status Text */}
        <span className="text-sm font-medium tracking-wide">
          {getStatusText()}
        </span>

        {/* Expand Indicator */}
        <svg 
          className={`w-3 h-3 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {/* Expanded Details */}
      <div className={`
        absolute top-full right-0 mt-2 w-64 rounded-xl border backdrop-blur-sm
        ${styles.bg} ${styles.border} ${styles.shadow}
        shadow-xl transition-all duration-300 ease-in-out origin-top-right
        ${isExpanded ? 'opacity-100 scale-100' : 'opacity-0 scale-95 pointer-events-none'}
      `}>
        <div className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">Backend Status</span>
            <div className={`px-2 py-1 rounded-full text-xs font-medium ${styles.bg} ${styles.text} border ${styles.border}`}>
              {status.toUpperCase()}
            </div>
          </div>
          
          {lastChecked && (
            <div className="text-xs opacity-75">
              <span className="font-medium">Last checked:</span>
              <br />
              {lastChecked.toLocaleString()}
            </div>
          )}
          
          <div className="flex gap-2">
            <button
              onClick={checkConnection}
              disabled={status === 'connecting'}
              className={`
                flex-1 px-3 py-2 text-xs font-medium rounded-lg
                bg-white bg-opacity-60 hover:bg-opacity-80
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-all duration-200
                ${styles.text} border ${styles.border}
              `}
            >
              {status === 'connecting' ? 'Checking...' : 'Check Now'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
