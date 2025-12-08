"""
ChatGPT Integration Service

This service handles integration with OpenAI's ChatGPT API for:
- AI-powered insights
- Data analysis recommendations
- Anomaly detection
- Smart predictions
"""

import os
from typing import Optional, Dict, Any, List
from openai import OpenAI
from app.utils.unified_logger import get_logger

logger = get_logger(__name__)


class ChatGPTService:
    """Service for interacting with ChatGPT API"""
    
    def __init__(self):
        """Initialize ChatGPT service with API key from environment"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('CHATGPT_MODEL', 'gpt-4')
        self.max_tokens = int(os.getenv('CHATGPT_MAX_TOKENS', '2000'))
        self.temperature = float(os.getenv('CHATGPT_TEMPERATURE', '0.7'))
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"✅ ChatGPT service initialized with model: {self.model}")
        else:
            self.client = None
            logger.warning("⚠️ OpenAI API key not found in environment variables")
    
    def is_configured(self) -> bool:
        """Check if ChatGPT service is properly configured"""
        return self.api_key is not None and self.api_key != '' and self.client is not None
    
    async def chat(self, messages: List[Dict[str, str]], model: str = None) -> Optional[str]:
        """
        General chat functionality for AI Assistant
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Optional model to use (overrides default)
            
        Returns:
            AI response string or None if error
        """
        if not self.is_configured():
            logger.warning("ChatGPT service not configured, cannot process chat request")
            return None
        
        # Use provided model or default
        model_to_use = model or self.model
        
        try:
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"✅ Generated chat response successfully")
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ Error in chat request: {e}")
            return None
    
    async def generate_insights(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Generate AI-powered insights from financial data
        
        Args:
            data: Dictionary containing financial metrics
            
        Returns:
            String with AI-generated insights or None if error
        """
        if not self.is_configured():
            logger.warning("ChatGPT service not configured, skipping insights generation")
            return None
        
        try:
            prompt = self._build_insights_prompt(data)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst AI assistant. Provide concise, actionable insights based on financial data."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            insight = response.choices[0].message.content.strip()
            logger.info(f"✅ Generated AI insights successfully")
            return insight
            
        except Exception as e:
            logger.error(f"❌ Error generating ChatGPT insights: {e}")
            return None
    
    async def detect_anomalies(self, transactions: List[Dict[str, Any]]) -> Optional[List[str]]:
        """
        Detect anomalies in transaction patterns using AI
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of anomaly descriptions or None if error
        """
        if not self.is_configured():
            return None
        
        try:
            prompt = self._build_anomaly_detection_prompt(transactions)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a fraud detection and anomaly detection AI. Identify unusual patterns in financial transactions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.3  # Lower temperature for more focused analysis
            )
            
            anomalies_text = response.choices[0].message.content.strip()
            anomalies = [line.strip() for line in anomalies_text.split('\n') if line.strip()]
            
            logger.info(f"✅ Detected {len(anomalies)} potential anomalies")
            return anomalies
            
        except Exception as e:
            logger.error(f"❌ Error detecting anomalies: {e}")
            return None
    
    async def predict_trends(self, historical_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Predict future trends based on historical data
        
        Args:
            historical_data: List of historical data points
            
        Returns:
            Dictionary with predictions or None if error
        """
        if not self.is_configured():
            return None
        
        try:
            prompt = self._build_trend_prediction_prompt(historical_data)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial forecasting AI. Analyze trends and provide data-driven predictions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.5
            )
            
            predictions = response.choices[0].message.content.strip()
            logger.info(f"✅ Generated trend predictions successfully")
            
            return {
                "predictions": predictions,
                "confidence": "medium",
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"❌ Error predicting trends: {e}")
            return None
    
    def _build_insights_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for insights generation"""
        return f"""
Analyze the following financial metrics and provide 3-5 key insights:

Total Revenue: {data.get('total_revenue', 0)}
Total Expenses: {data.get('total_expenses', 0)}
Net Profit: {data.get('net_profit', 0)}
Active Clients: {data.get('active_clients', 0)}
Transaction Count: {data.get('transaction_count', 0)}

Provide concise, actionable insights in bullet points.
"""
    
    def _build_anomaly_detection_prompt(self, transactions: List[Dict[str, Any]]) -> str:
        """Build prompt for anomaly detection"""
        summary = f"Analyzing {len(transactions)} transactions.\n\n"
        summary += "Sample transactions:\n"
        for txn in transactions[:5]:  # First 5 as examples
            summary += f"- Amount: {txn.get('amount', 0)}, Category: {txn.get('category', 'Unknown')}, Date: {txn.get('date', 'Unknown')}\n"
        
        return f"""
{summary}

Identify any unusual patterns or anomalies such as:
- Unusually large transactions
- Suspicious timing patterns
- Unexpected category combinations
- Duplicate transactions

List each anomaly found in a single line.
"""
    
    def _build_trend_prediction_prompt(self, historical_data: List[Dict[str, Any]]) -> str:
        """Build prompt for trend prediction"""
        summary = f"Historical data points: {len(historical_data)}\n\n"
        if historical_data:
            latest = historical_data[-1]
            summary += f"Latest: Date={latest.get('date')}, Amount={latest.get('amount', 0)}\n"
        
        return f"""
{summary}

Based on this historical data, predict:
1. Next 30-day trend (up/down/stable)
2. Expected growth percentage
3. Key factors to watch

Provide brief, data-driven predictions.
"""


# Singleton instance - will be initialized when first accessed
chatgpt_service = None

def get_chatgpt_service():
    """Get the ChatGPT service instance, initializing it if needed"""
    global chatgpt_service
    if chatgpt_service is None:
        chatgpt_service = ChatGPTService()
    return chatgpt_service

