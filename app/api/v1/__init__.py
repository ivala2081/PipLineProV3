"""
API v1 Blueprint Registration
"""
from flask import Blueprint
from app.api.v1.endpoints import transactions, analytics, users, health, translations, exchange_rates, currency_management, database, performance, bulk_rates, docs, realtime_analytics, ai_analysis, financial_performance, ai_assistant, database_management, security, trust_wallet, accounting, config, monitoring, metrics, organizations

# Create the main API v1 blueprint
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Register endpoint blueprints
api_v1.register_blueprint(organizations.organizations_api, url_prefix='/organizations')  # Multi-tenancy
api_v1.register_blueprint(transactions.transactions_api, url_prefix='/transactions')
api_v1.register_blueprint(analytics.analytics_api, url_prefix='/analytics')
api_v1.register_blueprint(users.users_api, url_prefix='/users')
api_v1.register_blueprint(health.health_api, url_prefix='/health')
api_v1.register_blueprint(translations.translations_bp, url_prefix='/translations')
api_v1.register_blueprint(exchange_rates.exchange_rates_bp, url_prefix='/exchange-rates')
api_v1.register_blueprint(currency_management.currency_management_api, url_prefix='/currency')
api_v1.register_blueprint(database.database_api, url_prefix='/database')
api_v1.register_blueprint(database_management.database_management_bp, url_prefix='/database-management')
api_v1.register_blueprint(performance.performance_api, url_prefix='/performance')
api_v1.register_blueprint(docs.docs_api, url_prefix='/docs')
api_v1.register_blueprint(realtime_analytics.realtime_analytics_api, url_prefix='/realtime')
api_v1.register_blueprint(ai_analysis.ai_analysis_api, url_prefix='/ai')
api_v1.register_blueprint(ai_assistant.ai_assistant_bp, url_prefix='/ai-assistant')
api_v1.register_blueprint(financial_performance.financial_performance_bp)
api_v1.register_blueprint(bulk_rates.bulk_rates_bp)
api_v1.register_blueprint(security.security_bp, url_prefix='/security')
api_v1.register_blueprint(trust_wallet.trust_wallet_bp, url_prefix='/trust-wallet')
api_v1.register_blueprint(accounting.accounting_api, url_prefix='/accounting')
api_v1.register_blueprint(config.config_api, url_prefix='/config')
api_v1.register_blueprint(monitoring.monitoring_api, url_prefix='/monitoring')
api_v1.register_blueprint(metrics.metrics_bp, url_prefix='/metrics')

@api_v1.route("/")
def api_root():
    """API root endpoint"""
    return {
        "message": "PipLine Treasury System API v1",
        "version": "1.0.0",
        "status": "active"
    }