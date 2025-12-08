"""
Rate Limiting Configuration
Centralized rate limit definitions for different endpoint categories
"""

# Rate limit categories based on endpoint usage patterns

# Lightweight endpoints (session checks, health checks)
# These are called very frequently and are lightweight
LIGHTWEIGHT_ENDPOINTS = {
    "/api/v1/auth/check": "120 per minute, 5000 per hour",  # Increased from 30/min - session checks are frequent and lightweight
    "/api/v1/health/": "60 per minute, 1000 per hour",  # Health checks need frequent monitoring
}

# Dashboard endpoints (frequently called on page load)
DASHBOARD_ENDPOINTS = {
    "/api/v1/analytics/dashboard/stats": "20 per minute, 200 per hour",
    "/api/v1/dashboard/consolidated": "15 per minute, 300 per hour",  # More generous than analytics consolidated-dashboard
    "/api/v1/financial-performance": "20 per minute, 200 per hour",
    "/api/v1/transactions/psp_summary_stats": "20 per minute, 200 per hour",
}

# User settings (frequently accessed but less critical)
USER_ENDPOINTS = {
    "/api/v1/users/settings": "30 per minute, 500 per hour",
}

# Analytics endpoints (heavy computation, should be more restricted)
ANALYTICS_ENDPOINTS = {
    "/api/v1/analytics/consolidated-dashboard": "10 per minute, 100 per hour",  # Already set in code, keep
    "/api/v1/analytics/revenue-detailed": "10 per minute, 100 per hour",
    "/api/v1/analytics/psp-rollover-summary": "10 per minute, 100 per hour",
    "/api/v1/analytics/ledger-data": "15 per minute, 150 per hour",
}

# Trust wallet endpoints (moderate frequency)
TRUST_WALLET_ENDPOINTS = {
    "/api/v1/trust-wallet/wallets": "30 per minute, 500 per hour",
    "/api/v1/trust-wallet/summary": "30 per minute, 500 per hour",
    "/api/v1/trust-wallet/transactions": "30 per minute, 500 per hour",
    "/api/v1/trust-wallet/wallets/*/balance": "30 per minute, 500 per hour",
}

# Authentication endpoints (need protection against brute force)
AUTH_ENDPOINTS = {
    "/api/v1/auth/login": "10 per minute, 20 per hour",  # Stricter for security
    "/api/v1/auth/logout": "30 per minute",  # Re-enable and set reasonable limit
}

# Exchange rate endpoints (external API calls - need throttling)
EXCHANGE_RATE_ENDPOINTS = {
    "/api/v1/exchange-rates/rates": "60 per minute, 1000 per hour",  # Already set, keep
    "/api/v1/exchange-rates/current": "120 per minute, 2000 per hour",  # More generous - lightweight cache check
    "/api/v1/exchange-rates/update": "5 per minute, 30 per hour",  # Strict - triggers external API calls
}

# Performance/Monitoring endpoints (moderate frequency)
PERFORMANCE_ENDPOINTS = {
    "/api/v1/performance/status": "30 per minute, 500 per hour",
    "/api/v1/performance/system-status": "30 per minute, 500 per hour",
    "/api/v1/performance/alerts": "30 per minute, 500 per hour",
    "/api/v1/performance/metrics": "20 per minute, 300 per hour",
}

# Transaction endpoints (moderate to high frequency)
TRANSACTION_ENDPOINTS = {
    "/api/v1/transactions/": "50 per minute, 1000 per hour",  # List endpoint - frequently paginated
}

# Default fallback (when no specific limit is set)
DEFAULT_LIMITS = "5000 per day, 1000 per hour, 200 per minute"

# Rate limit key function mapping
# Some endpoints should use user ID instead of IP for logged-in users
USER_BASED_LIMITS = [
    "/api/v1/analytics",
    "/api/v1/dashboard",
    "/api/v1/users",
    "/api/v1/transactions",
]

