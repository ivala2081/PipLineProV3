import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { 
  Send, 
  Bot, 
  User, 
  Loader2, 
  MessageSquare, 
  Sparkles,
  Trash2,
  Settings,
  Shield
} from 'lucide-react';
import { CHATGPT_CONFIG as AI_CONFIG, SYSTEM_PROMPT, validateApiKey, AVAILABLE_MODELS } from '../../config/chatgpt';
import { AILogo } from '../AILogo';
import { useLanguage } from '../../contexts/LanguageContext';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  model?: string; // Track which model was used for assistant responses
  enhanced?: boolean; // Track if enhanced mode was used
}

interface ChatGPTInterfaceProps {
  apiKey: string;
  className?: string;
}

const ChatGPTInterface: React.FC<ChatGPTInterfaceProps> = ({ apiKey, className = '' }) => {
  const { t } = useLanguage();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState('gpt-4o-mini');
  const [useEnhancedMode, setUseEnhancedMode] = useState(false);
  const [availableSections, setAvailableSections] = useState<{[key: string]: any}>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check if AI is properly configured (always enabled now, backend handles configuration)
  const isConfigured = AI_CONFIG.ENABLED;

  // Fetch available sections for enhanced mode
  useEffect(() => {
    const fetchAvailableSections = async () => {
      try {
        const response = await fetch('/api/v1/ai-assistant/sections');
        if (response.ok) {
          const data = await response.json();
          setAvailableSections(data.sections || {});
        }
      } catch (error) {
        console.error('Failed to fetch available sections:', error);
      }
    };

    if (isConfigured) {
      fetchAvailableSections();
    }
  }, [isConfigured]);

  // Clear any existing errors and messages if not configured
  useEffect(() => {
    if (!isConfigured) {
      if (error) {
        setError(null);
      }
      if (messages.length > 0) {
        setMessages([]);
      }
    }
  }, [isConfigured, error, messages.length]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    // Check if AI is properly configured
    if (!isConfigured) {
      setError('AI Assistant is not configured. Please contact your administrator to enable this feature.');
      return;
    }

    // API key validation is now handled by the backend

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      console.log('Sending AI request:', {
        model: selectedModel,
        use_enhanced: useEnhancedMode,
        message_count: messages.length + 1
      });
      
      const response = await fetch(AI_CONFIG.API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: selectedModel,
          use_enhanced: useEnhancedMode,
          messages: [
            {
              role: 'system',
              content: SYSTEM_PROMPT
            },
            ...messages.map(msg => ({
              role: msg.role,
              content: msg.content
            })),
            {
              role: 'user',
              content: userMessage.content
            }
          ]
        }),
      });
      
      console.log('AI response status:', response.status, response.statusText);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `API Error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('AI response data:', {
        status: data.status,
        hasResponse: !!data.response,
        enhanced: data.enhanced,
        model: data.model
      });
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || 'Sorry, I could not generate a response.',
        timestamp: new Date(),
        model: data.model || selectedModel,
        enhanced: data.enhanced || false,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      console.error('AI Assistant Error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  // Show a notification when model changes
  const handleModelChange = (newModel: string) => {
    if (newModel !== selectedModel && messages.length > 0) {
      // Add a system message indicating model change
      const modelChangeMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Switched to ${AVAILABLE_MODELS.find(m => m.id === newModel)?.name || newModel} model.`,
        timestamp: new Date(),
        model: newModel,
      };
      setMessages(prev => [...prev, modelChangeMessage]);
    }
    setSelectedModel(newModel);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gray-800 rounded-lg flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <CardTitle className="text-lg font-semibold text-slate-900">
                AI Assistant
              </CardTitle>
              <p className="text-sm text-slate-600">
                Intelligent Analysis & Insights
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Enhanced Mode Toggle */}
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1 text-xs text-slate-600">
                <input
                  type="checkbox"
                  checked={useEnhancedMode}
                  onChange={(e) => setUseEnhancedMode(e.target.checked)}
                  className="rounded border-slate-300 text-purple-600 focus:ring-purple-500"
                  disabled={isLoading}
                />
                <Sparkles className="w-3 h-3" />
                Enhanced
              </label>
            </div>

            {/* Model Selection Dropdown */}
            <div className="relative">
              <select
                value={selectedModel}
                onChange={(e) => handleModelChange(e.target.value)}
                className="text-xs border border-slate-300 rounded px-2 py-1 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent cursor-pointer"
                disabled={isLoading}
                title="Select AI model - cheaper models are faster, expensive models are more capable"
              >
                {AVAILABLE_MODELS.map((model) => (
                  <option 
                    key={model.id} 
                    value={model.id}
                    title={`${model.description} - Cost: ${model.cost}`}
                  >
                    {model.name} ({model.cost})
                  </option>
                ))}
              </select>
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={clearChat}
              className="text-slate-600 hover:text-red-600"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="text-slate-600"
            >
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[400px] max-h-[500px]">
          {!isConfigured ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                <Settings className="w-8 h-8 text-amber-600" />
              </div>
              <h3 className="text-lg font-medium text-slate-900 mb-2">
                AI Assistant Not Configured
              </h3>
              <p className="text-slate-600 max-w-sm mb-4">
                The AI Assistant feature requires proper configuration to function. Please contact your administrator to enable this feature.
              </p>
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 max-w-sm">
                <p className="text-sm text-amber-800">
                  <strong>Note:</strong> This is a premium feature that requires additional setup and API access.
                </p>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full">
              {/* Premium 3D AI Logo with Complex Animations */}
              <div className="relative scale-50 origin-center">
                <AILogo />
              </div>
              
              {/* Enhanced Mode Info */}
              {useEnhancedMode && Object.keys(availableSections).length > 0 && (
                <div className="mt-6 max-w-md">
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="w-4 h-4 text-purple-600" />
                      <h4 className="text-sm font-medium text-purple-900">Enhanced Mode Active</h4>
                    </div>
                    <p className="text-xs text-purple-700 mb-3">
                      I have read-only access to your PipLinePro data including:
                    </p>
                    <div className="grid grid-cols-2 gap-1 text-xs text-purple-600">
                      {Object.entries(availableSections).slice(0, 8).map(([key, section]) => (
                        <div key={key} className="flex items-center gap-1">
                          <div className="w-1 h-1 bg-purple-400 rounded-full"></div>
                          {section.name}
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-purple-600 mt-2">
                      Ask me about transactions, analytics, reports, or any business data!
                    </p>
                    <div className="mt-3 pt-3 border-t border-purple-200">
                      <p className="text-xs text-purple-500 flex items-center gap-1">
                        <Shield className="w-3 h-3" />
                        Read-only access: I can view and analyze data but cannot modify anything.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                )}
                
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 text-slate-900'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  <div className={`text-xs mt-2 ${
                    message.role === 'user' ? 'text-blue-100' : 'text-slate-500'
                  }`}>
                    <p>{message.timestamp.toLocaleTimeString()}</p>
                    {message.role === 'assistant' && (
                      <div className="flex items-center gap-2 mt-1">
                        {message.model && (
                          <p className="text-slate-400">
                            {AVAILABLE_MODELS.find(m => m.id === message.model)?.name || message.model}
                          </p>
                        )}
                        {message.enhanced && (
                          <div className="flex items-center gap-1 text-purple-600">
                            <Sparkles className="w-3 h-3" />
                            <span>Enhanced</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {message.role === 'user' && (
                  <div className="w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
            ))
          )}

          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-slate-100 rounded-lg px-4 py-3">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                  <span className="text-sm text-slate-600">AI is thinking...</span>
                </div>
              </div>
            </div>
          )}

          {error && isConfigured && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-600">
                <strong>Error:</strong> {error}
              </p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-slate-200 p-4">
          <div className="flex gap-2">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isConfigured ? "Ask me anything about your business or data..." : "AI Assistant is not configured"}
              className={`flex-1 resize-none border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:border-transparent ${
                isConfigured 
                  ? "border-slate-300 focus:ring-purple-500" 
                  : "border-amber-300 bg-amber-50 focus:ring-amber-500"
              }`}
              rows={2}
              disabled={isLoading || !isConfigured}
            />
            <Button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading || !isConfigured}
              className={`px-4 py-2 rounded-lg transition-all duration-200 ${
                isConfigured
                  ? "bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white"
                  : "bg-amber-100 text-amber-600 cursor-not-allowed"
              }`}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
          <p className={`text-xs mt-2 ${
            isConfigured ? "text-slate-500" : "text-amber-600"
          }`}>
            {isConfigured 
              ? "Press Enter to send, Shift+Enter for new line"
              : "Contact administrator to enable AI Assistant"
            }
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default ChatGPTInterface;
