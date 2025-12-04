import logging
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import text, func
from app import db
from app.models.transaction import Transaction
from app.models.financial import PspTrack, DailyBalance
# Use enhanced exchange rate service (legacy service deprecated)
from app.services.enhanced_exchange_rate_service import EnhancedExchangeRateService as ExchangeRateService
from app.utils.db_compat import extract_compat

logger = logging.getLogger(__name__)

class AIAnalysisService:
    """
    AI-powered analysis service for revenue optimization and risk mitigation
    """
    
    def __init__(self):
        self.api_key = None  # Will be set via environment variable
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4"
        
    def _get_ai_response(self, prompt: str, context: Dict[str, Any]) -> Optional[str]:
        """Get AI response from OpenAI API"""
        try:
            if not self.api_key:
                logger.warning("OpenAI API key not configured")
                return None
                
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert financial analyst specializing in treasury management, PSP optimization, and revenue maximization. Provide actionable insights based on real-time data."
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nContext: {json.dumps(context, indent=2)}"
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            logger.error(f"AI API request failed: {e}")
            return None
    
    def analyze_revenue_patterns(self) -> Dict[str, Any]:
        """Analyze revenue patterns and identify optimization opportunities"""
        try:
            # Get comprehensive transaction data
            transactions = self._get_transaction_analytics()
            psp_performance = self._get_psp_performance()
            market_trends = self._get_market_trends()
            
            context = {
                "transactions": transactions,
                "psp_performance": psp_performance,
                "market_trends": market_trends,
                "analysis_date": datetime.now().isoformat()
            }
            
            prompt = """
            Analyze the following treasury data and provide insights on:
            1. Revenue optimization opportunities
            2. PSP performance patterns
            3. Market trend impacts
            4. Risk factors to monitor
            5. Specific actionable recommendations
            
            Focus on data-driven insights that can directly impact revenue and reduce risks.
            """
            
            ai_insights = self._get_ai_response(prompt, context)
            
            return {
                "status": "success",
                "analysis_type": "revenue_patterns",
                "timestamp": datetime.now().isoformat(),
                "data": context,
                "ai_insights": ai_insights,
                "recommendations": self._extract_recommendations(ai_insights) if ai_insights else []
            }
            
        except Exception as e:
            logger.error(f"Revenue pattern analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def predict_risk_factors(self) -> Dict[str, Any]:
        """Predict potential risk factors and mitigation strategies"""
        try:
            # Get risk-related data
            risk_data = self._get_risk_indicators()
            market_volatility = self._get_market_volatility()
            psp_reliability = self._get_psp_reliability()
            
            context = {
                "risk_indicators": risk_data,
                "market_volatility": market_volatility,
                "psp_reliability": psp_reliability,
                "analysis_date": datetime.now().isoformat()
            }
            
            prompt = """
            Analyze the following risk data and provide:
            1. Identified risk factors and their probability
            2. Potential impact on revenue and operations
            3. Mitigation strategies for each risk
            4. Early warning indicators to monitor
            5. Contingency plans for high-probability risks
            
            Prioritize risks by impact and probability.
            """
            
            ai_insights = self._get_ai_response(prompt, context)
            
            return {
                "status": "success",
                "analysis_type": "risk_prediction",
                "timestamp": datetime.now().isoformat(),
                "data": context,
                "ai_insights": ai_insights,
                "risk_factors": self._extract_risk_factors(ai_insights) if ai_insights else []
            }
            
        except Exception as e:
            logger.error(f"Risk prediction analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def optimize_psp_allocation(self) -> Dict[str, Any]:
        """Optimize PSP allocation for maximum revenue and minimum risk"""
        try:
            # Get PSP performance data
            psp_data = self._get_detailed_psp_analysis()
            transaction_patterns = self._get_transaction_patterns()
            cost_analysis = self._get_cost_analysis()
            
            context = {
                "psp_data": psp_data,
                "transaction_patterns": transaction_patterns,
                "cost_analysis": cost_analysis,
                "analysis_date": datetime.now().isoformat()
            }
            
            prompt = """
            Analyze PSP performance and provide optimization recommendations:
            1. Best PSP for different transaction types/amounts
            2. Optimal allocation percentages for each PSP
            3. Cost-benefit analysis for each PSP
            4. Risk-adjusted return recommendations
            5. Dynamic allocation strategies based on market conditions
            
            Provide specific percentages and reasoning for each recommendation.
            """
            
            ai_insights = self._get_ai_response(prompt, context)
            
            return {
                "status": "success",
                "analysis_type": "psp_optimization",
                "timestamp": datetime.now().isoformat(),
                "data": context,
                "ai_insights": ai_insights,
                "optimization_plan": self._extract_optimization_plan(ai_insights) if ai_insights else []
            }
            
        except Exception as e:
            logger.error(f"PSP optimization analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def generate_strategic_insights(self) -> Dict[str, Any]:
        """Generate high-level strategic insights for business growth"""
        try:
            # Get comprehensive business data
            business_metrics = self._get_business_metrics()
            market_analysis = self._get_market_analysis()
            competitive_position = self._get_competitive_position()
            
            context = {
                "business_metrics": business_metrics,
                "market_analysis": market_analysis,
                "competitive_position": competitive_position,
                "analysis_date": datetime.now().isoformat()
            }
            
            prompt = """
            Provide strategic business insights based on the data:
            1. Growth opportunities and market expansion strategies
            2. Competitive advantages to leverage
            3. Technology and process improvements
            4. Revenue diversification opportunities
            5. Long-term strategic recommendations
            
            Focus on actionable strategies that can drive significant growth.
            """
            
            ai_insights = self._get_ai_response(prompt, context)
            
            return {
                "status": "success",
                "analysis_type": "strategic_insights",
                "timestamp": datetime.now().isoformat(),
                "data": context,
                "ai_insights": ai_insights,
                "strategic_recommendations": self._extract_strategic_recommendations(ai_insights) if ai_insights else []
            }
            
        except Exception as e:
            logger.error(f"Strategic insights generation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _get_transaction_analytics(self) -> Dict[str, Any]:
        """Get comprehensive transaction analytics"""
        try:
            # Get transaction summary
            total_transactions = Transaction.query.count()
            total_amount = db.session.query(func.sum(Transaction.amount)).scalar() or 0
            
            # Get daily revenue trends
            daily_revenue = db.session.query(
                func.date(Transaction.date).label('date'),
                func.sum(Transaction.amount).label('amount')
            ).group_by(func.date(Transaction.date)).order_by(func.date(Transaction.date)).all()
            
            # Get PSP distribution
            psp_distribution = db.session.query(
                Transaction.psp,
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('amount')
            ).group_by(Transaction.psp).all()
            
            return {
                "total_transactions": total_transactions,
                "total_amount": float(total_amount),
                "daily_revenue": [{"date": str(row.date), "amount": float(row.amount)} for row in daily_revenue],
                "psp_distribution": [{"psp": row.psp, "count": row.count, "amount": float(row.amount)} for row in psp_distribution]
            }
        except Exception as e:
            logger.error(f"Failed to get transaction analytics: {e}")
            return {}
    
    def _get_psp_performance(self) -> Dict[str, Any]:
        """Get PSP performance metrics"""
        try:
            psp_data = db.session.query(
                PspTrack.psp_name,
                func.count(PspTrack.id).label('transactions'),
                func.sum(PspTrack.amount).label('total_amount'),
                func.avg(PspTrack.amount).label('avg_amount'),
                func.max(PspTrack.date).label('last_transaction')
            ).group_by(PspTrack.psp_name).all()
            
            return {
                "psp_metrics": [
                    {
                        "psp_name": row.psp_name,
                        "transactions": row.transactions,
                        "total_amount": float(row.total_amount or 0),
                        "avg_amount": float(row.avg_amount or 0),
                        "last_transaction": str(row.last_transaction) if row.last_transaction else None
                    }
                    for row in psp_data
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get PSP performance: {e}")
            return {}
    
    def _get_market_trends(self) -> Dict[str, Any]:
        """Get market trend data"""
        try:
            # Get exchange rate trends
            exchange_rates = ExchangeRateService.get_rates()
            
            return {
                "exchange_rates": exchange_rates,
                "market_volatility": self._calculate_market_volatility(),
                "trend_direction": self._analyze_trend_direction()
            }
        except Exception as e:
            logger.error(f"Failed to get market trends: {e}")
            return {}
    
    def _get_risk_indicators(self) -> Dict[str, Any]:
        """Get risk indicators from data"""
        try:
            # Calculate various risk metrics
            recent_transactions = Transaction.query.filter(
                Transaction.date >= datetime.now() - timedelta(days=30)
            ).all()
            
            if not recent_transactions:
                return {}
            
            amounts = [float(t.amount) for t in recent_transactions]
            avg_amount = sum(amounts) / len(amounts)
            max_amount = max(amounts)
            min_amount = min(amounts)
            
            # Calculate volatility
            variance = sum((x - avg_amount) ** 2 for x in amounts) / len(amounts)
            volatility = variance ** 0.5
            
            return {
                "transaction_volatility": volatility,
                "max_transaction": max_amount,
                "min_transaction": min_amount,
                "avg_transaction": avg_amount,
                "transaction_count": len(recent_transactions)
            }
        except Exception as e:
            logger.error(f"Failed to get risk indicators: {e}")
            return {}
    
    def _get_market_volatility(self) -> Dict[str, Any]:
        """Calculate market volatility metrics"""
        try:
            # This would typically involve more sophisticated market data
            # For now, we'll use exchange rate volatility as a proxy
            exchange_rates = ExchangeRateService.get_rates()
            
            if 'USD/TRY' in exchange_rates:
                usd_try_rate = exchange_rates['USD/TRY']
                # Simple volatility calculation (in real implementation, use historical data)
                volatility = abs(usd_try_rate - 40.0) / 40.0 * 100  # Percentage change from baseline
                
                return {
                    "usd_try_volatility": volatility,
                    "volatility_level": "high" if volatility > 10 else "medium" if volatility > 5 else "low"
                }
            
            return {"volatility_level": "unknown"}
        except Exception as e:
            logger.error(f"Failed to calculate market volatility: {e}")
            return {}
    
    def _get_psp_reliability(self) -> Dict[str, Any]:
        """Calculate PSP reliability metrics"""
        try:
            psp_data = db.session.query(
                PspTrack.psp_name,
                func.count(PspTrack.id).label('total_transactions'),
                func.count(func.distinct(func.date(PspTrack.date))).label('active_days')
            ).group_by(PspTrack.psp_name).all()
            
            reliability_metrics = []
            for row in psp_data:
                if row.total_transactions > 0:
                    reliability = (row.active_days / 30) * 100  # Assuming 30-day period
                    reliability_metrics.append({
                        "psp_name": row.psp_name,
                        "reliability_score": min(reliability, 100),
                        "total_transactions": row.total_transactions,
                        "active_days": row.active_days
                    })
            
            return {"psp_reliability": reliability_metrics}
        except Exception as e:
            logger.error(f"Failed to get PSP reliability: {e}")
            return {}
    
    def _get_detailed_psp_analysis(self) -> Dict[str, Any]:
        """Get detailed PSP analysis for optimization"""
        try:
            psp_data = db.session.query(
                PspTrack.psp_name,
                func.count(PspTrack.id).label('transactions'),
                func.sum(PspTrack.amount).label('total_amount'),
                func.avg(PspTrack.amount).label('avg_amount'),
                func.min(PspTrack.amount).label('min_amount'),
                func.max(PspTrack.amount).label('max_amount')
            ).group_by(PspTrack.psp_name).all()
            
            return {
                "psp_analysis": [
                    {
                        "psp_name": row.psp_name,
                        "transactions": row.transactions,
                        "total_amount": float(row.total_amount or 0),
                        "avg_amount": float(row.avg_amount or 0),
                        "min_amount": float(row.min_amount or 0),
                        "max_amount": float(row.max_amount or 0),
                        "efficiency_score": self._calculate_psp_efficiency(row)
                    }
                    for row in psp_data
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get detailed PSP analysis: {e}")
            return {}
    
    def _get_transaction_patterns(self) -> Dict[str, Any]:
        """Analyze transaction patterns"""
        try:
            # Get transaction patterns by hour, day, amount ranges
            hourly_patterns = db.session.query(
                extract_compat(Transaction.date, 'hour').label('hour'),
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('amount')
            ).group_by(extract_compat(Transaction.date, 'hour')).all()
            
            amount_ranges = db.session.query(
                func.case(
                    (Transaction.amount < 1000, 'small'),
                    (Transaction.amount < 10000, 'medium'),
                    (Transaction.amount < 100000, 'large'),
                    else_='xlarge'
                ).label('range'),
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('amount')
            ).group_by('range').all()
            
            return {
                "hourly_patterns": [{"hour": int(row.hour), "count": row.count, "amount": float(row.amount)} for row in hourly_patterns],
                "amount_ranges": [{"range": row.range, "count": row.count, "amount": float(row.amount)} for row in amount_ranges]
            }
        except Exception as e:
            logger.error(f"Failed to get transaction patterns: {e}")
            return {}
    
    def _get_cost_analysis(self) -> Dict[str, Any]:
        """Analyze costs and fees"""
        try:
            # This would typically involve fee calculations
            # For now, we'll provide a basic structure
            return {
                "estimated_fees": "To be calculated based on PSP fee structures",
                "cost_optimization_opportunities": "Analysis pending"
            }
        except Exception as e:
            logger.error(f"Failed to get cost analysis: {e}")
            return {}
    
    def _get_business_metrics(self) -> Dict[str, Any]:
        """Get comprehensive business metrics"""
        try:
            total_transactions = Transaction.query.count()
            total_amount = db.session.query(func.sum(Transaction.amount)).scalar() or 0
            unique_clients = db.session.query(func.count(func.distinct(Transaction.client_name))).scalar() or 0
            
            return {
                "total_transactions": total_transactions,
                "total_amount": float(total_amount),
                "unique_clients": unique_clients,
                "avg_transaction_value": float(total_amount / total_transactions) if total_transactions > 0 else 0
            }
        except Exception as e:
            logger.error(f"Failed to get business metrics: {e}")
            return {}
    
    def _get_market_analysis(self) -> Dict[str, Any]:
        """Get market analysis data"""
        try:
            # This would typically involve external market data
            return {
                "market_size": "To be determined",
                "growth_rate": "To be calculated",
                "competitive_landscape": "Analysis pending"
            }
        except Exception as e:
            logger.error(f"Failed to get market analysis: {e}")
            return {}
    
    def _get_competitive_position(self) -> Dict[str, Any]:
        """Analyze competitive position"""
        try:
            # This would typically involve competitive analysis
            return {
                "market_share": "To be calculated",
                "competitive_advantages": "To be identified",
                "improvement_areas": "To be determined"
            }
        except Exception as e:
            logger.error(f"Failed to get competitive position: {e}")
            return {}
    
    def _calculate_market_volatility(self) -> float:
        """Calculate market volatility"""
        try:
            # Simple volatility calculation
            return 5.2  # Placeholder
        except Exception as e:
            logger.error(f"Failed to calculate market volatility: {e}")
            return 0.0
    
    def _analyze_trend_direction(self) -> str:
        """Analyze trend direction"""
        try:
            # Simple trend analysis
            return "upward"  # Placeholder
        except Exception as e:
            logger.error(f"Failed to analyze trend direction: {e}")
            return "unknown"
    
    def _calculate_psp_efficiency(self, psp_row) -> float:
        """Calculate PSP efficiency score"""
        try:
            if psp_row.total_amount and psp_row.transactions:
                efficiency = (psp_row.total_amount / psp_row.transactions) / 1000  # Normalize
                return min(efficiency, 100.0)
            return 0.0
        except Exception as e:
            logger.error(f"Failed to calculate PSP efficiency: {e}")
            return 0.0
    
    def _extract_recommendations(self, ai_insights: str) -> List[Dict[str, Any]]:
        """Extract actionable recommendations from AI insights"""
        try:
            # Simple extraction logic - in production, use more sophisticated NLP
            recommendations = []
            if "increase" in ai_insights.lower():
                recommendations.append({"type": "revenue", "action": "Increase transaction volume", "priority": "high"})
            if "optimize" in ai_insights.lower():
                recommendations.append({"type": "efficiency", "action": "Optimize PSP allocation", "priority": "medium"})
            if "risk" in ai_insights.lower():
                recommendations.append({"type": "risk", "action": "Implement risk mitigation", "priority": "high"})
            
            return recommendations
        except Exception as e:
            logger.error(f"Failed to extract recommendations: {e}")
            return []
    
    def _extract_risk_factors(self, ai_insights: str) -> List[Dict[str, Any]]:
        """Extract risk factors from AI insights"""
        try:
            risk_factors = []
            if "volatility" in ai_insights.lower():
                risk_factors.append({"factor": "Market Volatility", "probability": "medium", "impact": "high"})
            if "concentration" in ai_insights.lower():
                risk_factors.append({"factor": "PSP Concentration", "probability": "low", "impact": "medium"})
            
            return risk_factors
        except Exception as e:
            logger.error(f"Failed to extract risk factors: {e}")
            return []
    
    def _extract_optimization_plan(self, ai_insights: str) -> List[Dict[str, Any]]:
        """Extract optimization plan from AI insights"""
        try:
            optimization_plan = []
            if "allocation" in ai_insights.lower():
                optimization_plan.append({"action": "Reallocate PSP distribution", "expected_impact": "15% revenue increase"})
            if "timing" in ai_insights.lower():
                optimization_plan.append({"action": "Optimize transaction timing", "expected_impact": "10% efficiency gain"})
            
            return optimization_plan
        except Exception as e:
            logger.error(f"Failed to extract optimization plan: {e}")
            return []
    
    def _extract_strategic_recommendations(self, ai_insights: str) -> List[Dict[str, Any]]:
        """Extract strategic recommendations from AI insights"""
        try:
            strategic_recommendations = []
            if "expand" in ai_insights.lower():
                strategic_recommendations.append({"strategy": "Market Expansion", "timeline": "6 months", "investment": "medium"})
            if "technology" in ai_insights.lower():
                strategic_recommendations.append({"strategy": "Technology Upgrade", "timeline": "3 months", "investment": "high"})
            
            return strategic_recommendations
        except Exception as e:
            logger.error(f"Failed to extract strategic recommendations: {e}")
            return []
