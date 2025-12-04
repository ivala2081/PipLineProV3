"""
AI Assistant API Endpoints
Handles ChatGPT integration for the AI Assistant feature with enhanced project data access

SECURITY NOTE: The Enhanced AI Assistant has READ-ONLY access to the database.
- All database queries are SELECT operations only
- No INSERT, UPDATE, or DELETE operations are permitted
- Sensitive data (passwords, tokens, auth data) is excluded from all queries
- All data access is logged for security auditing
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.utils.unified_logger import get_logger
from app.services.chatgpt_service import get_chatgpt_service
from app.services.enhanced_ai_assistant_service import get_enhanced_ai_assistant
import asyncio
import json

logger = get_logger(__name__)

# Create blueprint
ai_assistant_bp = Blueprint('ai_assistant', __name__)


@ai_assistant_bp.route('/status', methods=['GET'])
def get_ai_assistant_status():
    """Get AI Assistant configuration status"""
    try:
        chatgpt_service = get_chatgpt_service()
        is_configured = chatgpt_service.is_configured()
        
        return jsonify({
            'status': 'success',
            'configured': is_configured,
            'message': 'AI Assistant is properly configured' if is_configured else 'AI Assistant is not configured'
        })
    
    except Exception as e:
        logger.error(f"Error checking AI Assistant status: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to check AI Assistant status'
        }), 500


@ai_assistant_bp.route('/chat', methods=['POST'])
@login_required
def chat_with_ai():
    """
    Chat with Enhanced AI Assistant with comprehensive READ-ONLY project data access
    
    Enhanced mode provides the AI with read-only access to:
    - Transaction data and analytics
    - Financial performance metrics
    - Business insights and reports
    - System monitoring data
    
    SECURITY: All database access is READ-ONLY. No data modifications are possible.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        messages = data.get('messages', [])
        model = data.get('model', 'gpt-4o-mini')  # Default model
        use_enhanced = data.get('use_enhanced', False)  # Default to standard mode
        
        # Validate model selection
        valid_models = ['gpt-3.5-turbo', 'gpt-4o-mini', 'gpt-4', 'gpt-4o', 'gpt-4-turbo']
        if model not in valid_models:
            return jsonify({
                'status': 'error',
                'message': f'Invalid model: {model}. Valid models are: {", ".join(valid_models)}'
            }), 400
        
        if not messages:
            return jsonify({
                'status': 'error',
                'message': 'No messages provided'
            }), 400
        
        # Get the last user message for enhanced processing
        user_message = None
        if messages and messages[-1].get('role') == 'user':
            user_message = messages[-1].get('content', '')
        
        # Use enhanced AI assistant if requested and user message is available
        if use_enhanced and user_message:
            enhanced_service = get_enhanced_ai_assistant()
            logger.info(f"Enhanced mode requested: {use_enhanced}, Service configured: {enhanced_service.is_configured()}")
            if enhanced_service.is_configured():
                # Test database connection before processing
                if not enhanced_service.test_database_connection():
                    logger.error("Database connection test failed, falling back to standard service")
                    return jsonify({
                        'status': 'error',
                        'message': 'Database connection issue. Please try again in a moment.'
                    }), 503
                
                logger.info(f"Processing enhanced query: {user_message[:100]}...")
                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    ai_response = loop.run_until_complete(
                        enhanced_service.process_query(user_message, {'model': model})
                    )
                    logger.info(f"Enhanced response generated: {bool(ai_response)}")
                finally:
                    loop.close()
                
                if ai_response:
                    return jsonify({
                        'status': 'success',
                        'response': ai_response,
                        'model': model,
                        'enhanced': True
                    })
                else:
                    logger.warning("Enhanced service returned no response, falling back to standard service")
            else:
                logger.warning("Enhanced service not configured, falling back to standard service")
        
        # Fallback to standard ChatGPT service
        # Validate message format
        for message in messages:
            if not isinstance(message, dict) or 'role' not in message or 'content' not in message:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid message format'
                }), 400
        
        # Add system message if not present
        has_system_message = any(msg.get('role') == 'system' for msg in messages)
        if not has_system_message:
            system_message = {
                "role": "system",
                "content": "You are a helpful AI assistant integrated into PipLinePro, a comprehensive financial management system. Help users understand their financial data, provide business insights, and answer questions about the system. Be professional, accurate, and helpful."
            }
            messages.insert(0, system_message)
        
        # Process chat request
        chatgpt_service = get_chatgpt_service()
        if not chatgpt_service.is_configured():
            return jsonify({
                'status': 'error',
                'message': 'AI Assistant is not configured. Please contact your administrator.'
            }), 503
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            ai_response = loop.run_until_complete(chatgpt_service.chat(messages, model))
        finally:
            loop.close()
        
        if ai_response is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate AI response'
            }), 500
        
        return jsonify({
            'status': 'success',
            'response': ai_response,
            'model': model,
            'enhanced': False
        })
    
    except Exception as e:
        logger.error(f"Error in AI Assistant chat: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while processing your request'
        }), 500


@ai_assistant_bp.route('/insights', methods=['POST'])
@login_required
def generate_insights():
    """Generate AI-powered insights from financial data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        chatgpt_service = get_chatgpt_service()
        if not chatgpt_service.is_configured():
            return jsonify({
                'status': 'error',
                'message': 'AI Assistant is not configured. Please contact your administrator.'
            }), 503
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            insights = loop.run_until_complete(chatgpt_service.generate_insights(data))
        finally:
            loop.close()
        
        if insights is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate insights'
            }), 500
        
        return jsonify({
            'status': 'success',
            'insights': insights,
            'model': chatgpt_service.model
        })
    
    except Exception as e:
        logger.error(f"Error generating AI insights: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while generating insights'
        }), 500


@ai_assistant_bp.route('/anomalies', methods=['POST'])
@login_required
def detect_anomalies():
    """Detect anomalies in transaction data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        transactions = data.get('transactions', [])
        
        if not transactions:
            return jsonify({
                'status': 'error',
                'message': 'No transaction data provided'
            }), 400
        
        chatgpt_service = get_chatgpt_service()
        if not chatgpt_service.is_configured():
            return jsonify({
                'status': 'error',
                'message': 'AI Assistant is not configured. Please contact your administrator.'
            }), 503
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            anomalies = loop.run_until_complete(chatgpt_service.detect_anomalies(transactions))
        finally:
            loop.close()
        
        if anomalies is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to detect anomalies'
            }), 500
        
        return jsonify({
            'status': 'success',
            'anomalies': anomalies,
            'model': chatgpt_service.model
        })
    
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while detecting anomalies'
        }), 500


@ai_assistant_bp.route('/predictions', methods=['POST'])
@login_required
def predict_trends():
    """Predict trends based on historical data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        historical_data = data.get('historical_data', [])
        
        if not historical_data:
            return jsonify({
                'status': 'error',
                'message': 'No historical data provided'
            }), 400
        
        chatgpt_service = get_chatgpt_service()
        if not chatgpt_service.is_configured():
            return jsonify({
                'status': 'error',
                'message': 'AI Assistant is not configured. Please contact your administrator.'
            }), 503
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            predictions = loop.run_until_complete(chatgpt_service.predict_trends(historical_data))
        finally:
            loop.close()
        
        if predictions is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate predictions'
            }), 500
        
        return jsonify({
            'status': 'success',
            'predictions': predictions,
            'model': chatgpt_service.model
        })
    
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while generating predictions'
        }), 500


@ai_assistant_bp.route('/data/<section>', methods=['GET'])
@login_required
def get_section_data(section):
    """Get specific section data for AI assistant"""
    try:
        enhanced_service = get_enhanced_ai_assistant()
        
        if not enhanced_service.is_configured():
            return jsonify({
                'status': 'error',
                'message': 'AI Assistant is not configured'
            }), 503
        
        # Validate section
        if section not in enhanced_service.accessible_sections:
            return jsonify({
                'status': 'error',
                'message': f'Invalid section: {section}. Available sections: {list(enhanced_service.accessible_sections.keys())}'
            }), 400
        
        # Get section data
        data_function = enhanced_service.accessible_sections[section]
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            section_data = loop.run_until_complete(data_function())
        finally:
            loop.close()
        
        return jsonify({
            'status': 'success',
            'section': section,
            'data': section_data
        })
    
    except Exception as e:
        logger.error(f"Error getting section data: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get {section} data'
        }), 500


@ai_assistant_bp.route('/sections', methods=['GET'])
@login_required
def get_available_sections():
    """Get list of available data sections for AI assistant"""
    try:
        enhanced_service = get_enhanced_ai_assistant()
        
        sections_info = {}
        for section in enhanced_service.accessible_sections.keys():
            sections_info[section] = {
                'name': section.replace('_', ' ').title(),
                'description': f'{section.replace("_", " ")} data and analytics'
            }
        
        return jsonify({
            'status': 'success',
            'sections': sections_info
        })
    
    except Exception as e:
        logger.error(f"Error getting available sections: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get available sections'
        }), 500


@ai_assistant_bp.route('/test-database', methods=['GET'])
@login_required
def test_database_access():
    """Test database access for enhanced AI assistant"""
    try:
        enhanced_service = get_enhanced_ai_assistant()
        if not enhanced_service.is_configured():
            return jsonify({
                'status': 'error',
                'message': 'Enhanced AI Assistant is not configured'
            }), 503
        
        # Test database connection
        db_accessible = enhanced_service.test_database_connection()
        
        return jsonify({
            'status': 'success',
            'database_accessible': db_accessible,
            'message': 'Database connection test completed'
        })
    except Exception as e:
        logger.error(f"Error testing database access: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Database test failed: {str(e)}'
        }), 500


@ai_assistant_bp.route('/comprehensive-analysis', methods=['POST'])
@login_required
def comprehensive_analysis():
    """Perform comprehensive analysis across all accessible sections"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        analysis_query = data.get('query', 'Provide a comprehensive business overview')
        sections = data.get('sections', [])  # Optional: specify which sections to include
        
        enhanced_service = get_enhanced_ai_assistant()
        
        if not enhanced_service.is_configured():
            return jsonify({
                'status': 'error',
                'message': 'AI Assistant is not configured'
            }), 503
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            analysis_response = loop.run_until_complete(
                enhanced_service.process_query(analysis_query, {'sections': sections})
            )
        finally:
            loop.close()
        
        return jsonify({
            'status': 'success',
            'analysis': analysis_response,
            'query': analysis_query,
            'sections_analyzed': sections if sections else 'all available sections'
        })
    
    except Exception as e:
        logger.error(f"Error performing comprehensive analysis: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to perform comprehensive analysis'
        }), 500
