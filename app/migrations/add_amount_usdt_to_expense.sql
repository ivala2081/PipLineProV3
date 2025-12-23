-- Migration: Add amount_usdt field to expense table
-- Created: 2025-01-XX
-- Description: Adds amount_usdt column to support USDT currency in expenses

-- Add amount_usdt column
ALTER TABLE expense ADD COLUMN amount_usdt NUMERIC(15, 2) NOT NULL DEFAULT 0.0;

-- Update mount_currency validation (handled in model validation)
-- No SQL changes needed for mount_currency as it's already VARCHAR(10)

-- Create index for performance (optional)
CREATE INDEX IF NOT EXISTS idx_expense_amount_usdt ON expense(amount_usdt);

