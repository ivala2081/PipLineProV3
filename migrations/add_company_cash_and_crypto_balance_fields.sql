-- Migration: Add company_cash_usd and crypto_balance_usd fields to daily_net table
-- Date: 2025-11-05
-- Description: Adds new fields to support Company Cash and Crypto Balance tracking in Net tab

-- Add new columns to daily_net table
ALTER TABLE daily_net ADD COLUMN company_cash_usd DECIMAL(15, 2) DEFAULT 0.0 NOT NULL;
ALTER TABLE daily_net ADD COLUMN crypto_balance_usd DECIMAL(15, 2) DEFAULT 0.0 NOT NULL;

-- Add comments for documentation (SQLite doesn't support COMMENT, but we document here)
-- company_cash_usd: Physical cash and bank balance in USD (manual input)
-- crypto_balance_usd: Total balance from all active Trust wallets in USD (auto-fetched)
-- anlik_kasa_usd: Auto-calculated as company_cash_usd + crypto_balance_usd

-- Verify the changes
SELECT 
    name,
    type
FROM 
    pragma_table_info('daily_net')
WHERE 
    name IN ('company_cash_usd', 'crypto_balance_usd');

