-- Migration: Create expense_budget table for budget tracking
-- Date: 2025-12-19
-- Description: Adds budget management functionality for expenses

CREATE TABLE IF NOT EXISTS expense_budget (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    budget_period VARCHAR(50) NOT NULL,
    budget_type VARCHAR(20) NOT NULL DEFAULT 'monthly',
    category VARCHAR(20),
    budget_try NUMERIC(15, 2) NOT NULL DEFAULT 0.0,
    budget_usd NUMERIC(15, 2) NOT NULL DEFAULT 0.0,
    budget_usdt NUMERIC(15, 2) NOT NULL DEFAULT 0.0,
    warning_threshold INTEGER NOT NULL DEFAULT 80,
    alert_threshold INTEGER NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    FOREIGN KEY (created_by) REFERENCES user(id),
    CONSTRAINT uix_budget_period_category UNIQUE (budget_period, category)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_budget_period ON expense_budget(budget_period);
CREATE INDEX IF NOT EXISTS idx_budget_type ON expense_budget(budget_type);
CREATE INDEX IF NOT EXISTS idx_budget_category ON expense_budget(category);
CREATE INDEX IF NOT EXISTS idx_budget_is_active ON expense_budget(is_active);

-- Insert sample budgets for current month (optional - can be removed in production)
INSERT OR IGNORE INTO expense_budget (budget_period, budget_type, category, budget_usd, warning_threshold, alert_threshold, is_active)
VALUES 
    (strftime('%Y-%m', 'now'), 'monthly', NULL, 50000.00, 80, 100, 1),
    (strftime('%Y-%m', 'now'), 'monthly', 'outflow', 30000.00, 80, 100, 1),
    (strftime('%Y-%m', 'now'), 'monthly', 'inflow', 60000.00, 80, 100, 1);

