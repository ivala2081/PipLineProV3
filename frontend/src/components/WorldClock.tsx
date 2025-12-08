import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';

interface ClockProps {
  timezone: string;
  city: string;
  flag: string;
}

const WorldClock: React.FC<ClockProps> = ({ timezone, city, flag }) => {
  const [time, setTime] = useState<string>('');
  const [date, setDate] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      
      // Format time for the specific timezone
      const timeOptions: Intl.DateTimeFormatOptions = {
        timeZone: timezone,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      };
      
      const dateOptions: Intl.DateTimeFormatOptions = {
        timeZone: timezone,
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        weekday: 'short'
      };

      setTime(now.toLocaleTimeString('en-US', timeOptions));
      setDate(now.toLocaleDateString('en-US', dateOptions));
    };

    // Update immediately
    updateTime();
    
    // Update every second
    const interval = setInterval(updateTime, 1000);
    
    return () => clearInterval(interval);
  }, [timezone]);

  return (
    <div className="relative flex items-center gap-4 px-5 py-3 bg-gradient-to-r from-white/95 to-gray-50/80 backdrop-blur-md rounded-xl border border-gray-200/60 shadow-lg hover:shadow-xl hover:shadow-gray-100/50 transition-all duration-500 group hover:scale-105 hover:-translate-y-1">
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-gray-500/5 to-purple-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
      
      {/* Flag with enhanced styling */}
      <div className="relative flex items-center gap-3">
        <div className="relative">
          <span className="text-3xl drop-shadow-sm group-hover:scale-110 transition-transform duration-300">{flag}</span>
          <div className="absolute -inset-1 bg-gradient-to-r from-gray-400/20 to-purple-400/20 rounded-full blur-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        </div>
        
        <div className="flex flex-col">
          <span className="text-sm font-bold text-gray-800 group-hover:text-gray-700 transition-colors duration-300 tracking-wide">
            {city}
          </span>
          <span className="text-xs text-gray-500 group-hover:text-gray-600 transition-colors duration-300 font-medium">
            {date}
          </span>
        </div>
      </div>
      
      {/* Time display with enhanced styling */}
      <div className="flex items-center gap-3 pl-4 border-l-2 border-gradient-to-b from-gray-200 to-purple-200 group-hover:border-gray-300 transition-colors duration-300">
        <div className="relative">
          <Clock className="h-5 w-5 text-gray-500 group-hover:text-gray-600 transition-colors duration-300 group-hover:rotate-12 transition-transform duration-300" />
          <div className="absolute inset-0 bg-gray-400/20 rounded-full blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        </div>
        
        <div className="flex flex-col items-end">
          <span className="text-xl font-mono font-bold text-gray-800 group-hover:text-gray-700 transition-colors duration-300 tracking-wider animate-pulse">
            {time}
          </span>
          <div className="w-full h-0.5 bg-gradient-to-r from-gray-400 to-purple-400 rounded-full transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-left"></div>
        </div>
      </div>
      
      {/* Subtle glow effect */}
      <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-gray-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
    </div>
  );
};

const WorldClocks: React.FC = () => {
  return (
    <div className="flex items-center gap-6 relative">
      {/* Background glow effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-gray-500/10 via-purple-500/10 to-gray-500/10 rounded-2xl blur-xl opacity-50 animate-pulse"></div>
      
      <div className="relative z-10">
        <WorldClock 
          timezone="Europe/Istanbul" 
          city="Istanbul" 
          flag="🇹🇷" 
        />
      </div>
      
      <div className="relative z-10">
        <WorldClock 
          timezone="America/New_York" 
          city="New York" 
          flag="🇺🇸" 
        />
      </div>
    </div>
  );
};

export default WorldClocks;
