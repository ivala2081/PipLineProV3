-- Migration: Add expense table for Accounting → Expenses tab
-- Created: 2025-01-XX
-- Description: Creates the expense table to store company expenses

CREATE TABLE IF NOT EXISTS expense (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description VARCHAR(200) NOT NULL,
    detail TEXT,
    amount_try NUMERIC(15, 2) NOT NULL DEFAULT 0.0,
    amount_usd NUMERIC(15, 2) NOT NULL DEFAULT 0.0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    cost_period VARCHAR(50),
    payment_date DATE,
    payment_period VARCHAR(50),
    source VARCHAR(100),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    FOREIGN KEY (created_by) REFERENCES user(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_expense_status ON expense(status);
CREATE INDEX IF NOT EXISTS idx_expense_payment_date ON expense(payment_date);
CREATE INDEX IF NOT EXISTS idx_expense_cost_period ON expense(cost_period);
CREATE INDEX IF NOT EXISTS idx_expense_created_by ON expense(created_by);
CREATE INDEX IF NOT EXISTS idx_expense_created_at ON expense(created_at);

