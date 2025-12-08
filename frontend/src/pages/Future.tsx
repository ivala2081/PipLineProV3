import React, { useState, useEffect } from 'react';
import ChatGPTInterface from '../components/modern/ChatGPTInterface';
import { CHATGPT_CONFIG } from '../config/chatgpt';
import { 
  Bot, 
  Play,
  Pause,
  RotateCcw
} from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { UnifiedCard, UnifiedButton, UnifiedBadge } from '../design-system';
import { useLanguage } from '../contexts/LanguageContext';

/**
 * Future Component - AI Assistant Page
 * Redesigned for minimal, modern aesthetic
 */
const Future: React.FC = () => {
  const { t } = useLanguage();
  const [isPaused, setIsPaused] = useState(false);

  // Scroll to top on component mount to prevent auto-scroll down
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, []);

  // Handler functions
  const handlePauseToggle = () => {
    setIsPaused(!isPaused);
  };

  const handleReset = () => {
    setIsPaused(false);
  };

  return (
    <div className="p-6 animate-in fade-in duration-300">
      {/* Minimal Modern Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Bot className="h-8 w-8 text-gray-600" />
              AI Assistant
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Ask questions and get intelligent insights about your business
            </p>
                  </div>
                  <div className="flex items-center gap-2">
            {/* Minimal Status Indicator */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold ${
              isPaused 
                ? 'bg-yellow-100 text-yellow-700' 
                : 'bg-green-100 text-green-700'
            }`}>
              <div className={`w-1.5 h-1.5 rounded-full ${
                isPaused ? 'bg-yellow-500' : 'bg-green-500 animate-pulse'
              }`}></div>
              {isPaused ? 'Paused' : 'Active'}
            </div>
            
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={handlePauseToggle}
              className="h-8 w-8 p-0"
              title={isPaused ? 'Resume' : 'Pause'}
                    >
                      {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                    </Button>
            
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleReset}
              className="h-8 w-8 p-0"
              title="Reset"
            >
                      <RotateCcw className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
      </div>

      {/* Ultra-Minimal Chat Interface */}
      <div className="rounded-lg overflow-hidden min-h-[calc(100vh-200px)]">
                  <ChatGPTInterface 
                    apiKey={CHATGPT_CONFIG.API_KEY}
          className="future-chat-interface h-full"
        />
      </div>
    </div>
  );
};

export default Future;
