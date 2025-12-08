/**
 * ChatGPT Configuration
 * Handles API key management and configuration
 */

export const validateApiKey = (apiKey: string): boolean => {
  return Boolean(apiKey) && apiKey.startsWith('sk-') && apiKey.length > 20;
};

// Check for environment variable first, then fallback to a placeholder
const getApiKey = () => {
  const envKey = import.meta.env.VITE_CHATGPT_API_KEY;
  if (envKey && validateApiKey(envKey)) {
    return envKey;
  }
  return null; // Return null instead of a hardcoded key
};

// Available AI models sorted by cost (cheapest to most expensive)
export const AVAILABLE_MODELS = [
  {
    id: 'gpt-3.5-turbo',
    name: 'AI Standard',
    description: 'Fast and efficient for most tasks',
    cost: 'Budget',
    maxTokens: 4096,
    pricePer1kTokens: 0.0015
  },
  {
    id: 'gpt-4o-mini',
    name: 'AI Balanced',
    description: 'Balanced performance and cost',
    cost: 'Economy',
    maxTokens: 128000,
    pricePer1kTokens: 0.00015
  },
  {
    id: 'gpt-4',
    name: 'AI Professional',
    description: 'High-quality reasoning and analysis',
    cost: 'Premium',
    maxTokens: 8192,
    pricePer1kTokens: 0.03
  },
  {
    id: 'gpt-4o',
    name: 'AI Advanced',
    description: 'Latest model with enhanced capabilities',
    cost: 'Premium+',
    maxTokens: 128000,
    pricePer1kTokens: 0.005
  },
  {
    id: 'gpt-4-turbo',
    name: 'AI Enterprise',
    description: 'Enhanced model with larger context',
    cost: 'Enterprise',
    maxTokens: 128000,
    pricePer1kTokens: 0.01
  }
];

export const CHATGPT_CONFIG = {
  API_KEY: getApiKey(),
  MODEL: 'gpt-4o-mini', // Default to a balanced option
  MAX_TOKENS: 2000,
  TEMPERATURE: 0.7,
  API_URL: '/api/v1/ai-assistant/chat', // Use backend API endpoint
  ENABLED: true, // Always enabled, backend will handle configuration
};

export const SYSTEM_PROMPT = `You are an intelligent AI assistant integrated into PipLinePro, a comprehensive financial management system. 

Your role is to:
- Provide clear, concise, and accurate responses
- Help users understand their financial data and business insights
- Assist with data analysis and interpretation
- Answer general business and technical questions
- Maintain a professional and helpful tone

Focus areas:
- Financial data analysis and insights
- Business intelligence and reporting
- Transaction processing and PSP management
- Client relationship management
- System usage and troubleshooting

Always be helpful, accurate, and maintain user privacy and data security.`;

export default CHATGPT_CONFIG;
