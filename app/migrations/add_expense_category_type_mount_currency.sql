-- Migration: Add category, type, and mount_currency fields to expense table
-- Created: 2025-01-XX
-- Description: Adds category (inflow/outflow), type (payment/transfer), and mount_currency fields to expense table

-- Add new columns
ALTER TABLE expense ADD COLUMN category VARCHAR(20) NOT NULL DEFAULT 'inflow';
ALTER TABLE expense ADD COLUMN type VARCHAR(20) NOT NULL DEFAULT 'payment';
ALTER TABLE expense ADD COLUMN mount_currency VARCHAR(10);

-- Migrate existing data:
-- 1. Set category based on amount sign (positive = inflow, negative = outflow)
--    Since amounts are stored as positive, we'll check if amount_try or amount_usd > 0
--    For existing records, if both amounts are 0, default to 'inflow'
UPDATE expense 
SET category = CASE 
    WHEN (amount_try > 0 OR amount_usd > 0) THEN 'inflow'
    ELSE 'inflow'
END
WHERE category = 'inflow';

-- 2. Set type to 'payment' for all existing records (already default)
-- No update needed as default is already 'payment'

-- 3. Set mount_currency based on which amount was entered
--    If amount_try > 0, set to 'TRY', otherwise if amount_usd > 0, set to 'USD'
UPDATE expense 
SET mount_currency = CASE 
    WHEN amount_try > 0 THEN 'TRY'
    WHEN amount_usd > 0 THEN 'USD'
    ELSE 'TRY'  -- Default to TRY if both are 0
END
WHERE mount_currency IS NULL;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_expense_category ON expense(category);
CREATE INDEX IF NOT EXISTS idx_expense_type ON expense(type);

