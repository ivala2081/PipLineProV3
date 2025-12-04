from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.services.ai_analysis_service import AIAnalysisService
import logging

logger = logging.getLogger(__name__)

ai_analysis_api = Blueprint('ai_analysis_api', __name__)

@ai_analysis_api.route('/revenue-analysis', methods=['GET'])
@login_required
def get_revenue_analysis():
    """Get AI-powered revenue analysis and optimization insights"""
    try:
        ai_service = AIAnalysisService()
        result = ai_service.analyze_revenue_patterns()
        
        logger.info(f"Revenue analysis requested by user {current_user.id}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Revenue analysis failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@ai_analysis_api.route('/risk-prediction', methods=['GET'])
@login_required
def get_risk_prediction():
    """Get AI-powered risk prediction and mitigation strategies"""
    try:
        ai_service = AIAnalysisService()
        result = ai_service.predict_risk_factors()
        
        logger.info(f"Risk prediction requested by user {current_user.id}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Risk prediction failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@ai_analysis_api.route('/psp-optimization', methods=['GET'])
@login_required
def get_psp_optimization():
    """Get AI-powered PSP allocation optimization recommendations"""
    try:
        ai_service = AIAnalysisService()
        result = ai_service.optimize_psp_allocation()
        
        logger.info(f"PSP optimization requested by user {current_user.id}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"PSP optimization failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@ai_analysis_api.route('/strategic-insights', methods=['GET'])
@login_required
def get_strategic_insights():
    """Get AI-powered strategic business insights"""
    try:
        ai_service = AIAnalysisService()
        result = ai_service.generate_strategic_insights()
        
        logger.info(f"Strategic insights requested by user {current_user.id}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Strategic insights failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@ai_analysis_api.route('/comprehensive-analysis', methods=['GET'])
@login_required
def get_comprehensive_analysis():
    """Get comprehensive AI analysis including all insights"""
    try:
        ai_service = AIAnalysisService()
        
        # Get all analysis types
        revenue_analysis = ai_service.analyze_revenue_patterns()
        risk_prediction = ai_service.predict_risk_factors()
        psp_optimization = ai_service.optimize_psp_allocation()
        strategic_insights = ai_service.generate_strategic_insights()
        
        comprehensive_result = {
            "status": "success",
            "analysis_type": "comprehensive",
            "timestamp": revenue_analysis.get('timestamp'),
            "revenue_analysis": revenue_analysis,
            "risk_prediction": risk_prediction,
            "psp_optimization": psp_optimization,
            "strategic_insights": strategic_insights,
            "summary": {
                "total_insights": len(revenue_analysis.get('recommendations', [])) + 
                                len(risk_prediction.get('risk_factors', [])) + 
                                len(psp_optimization.get('optimization_plan', [])) + 
                                len(strategic_insights.get('strategic_recommendations', [])),
                "analysis_quality": "high" if all(r.get('status') == 'success' for r in [revenue_analysis, risk_prediction, psp_optimization, strategic_insights]) else "partial"
            }
        }
        
        logger.info(f"Comprehensive analysis requested by user {current_user.id}")
        return jsonify(comprehensive_result)
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@ai_analysis_api.route('/ai-status', methods=['GET'])
@login_required
def get_ai_status():
    """Get AI service status and configuration"""
    try:
        ai_service = AIAnalysisService()
        
        status = {
            "ai_service_available": True,
            "api_configured": ai_service.api_key is not None,
            "model": ai_service.model,
            "features": [
                "Revenue Pattern Analysis",
                "Risk Prediction",
                "PSP Optimization",
                "Strategic Insights",
                "Comprehensive Analysis"
            ],
            "last_updated": "2025-09-23T16:30:00Z"
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"AI status check failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
