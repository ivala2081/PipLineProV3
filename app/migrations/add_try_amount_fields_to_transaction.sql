-- Migration script to add TRY amount fields to transaction table
-- This migration adds amount_try, commission_try, net_amount_try, and exchange_rate fields
-- Run this script to ensure all transactions have proper TRY conversion fields

-- Add amount_try column if it doesn't exist
ALTER TABLE transaction ADD COLUMN IF NOT EXISTS amount_try NUMERIC(15, 2);

-- Add commission_try column if it doesn't exist
ALTER TABLE transaction ADD COLUMN IF NOT EXISTS commission_try NUMERIC(15, 2);

-- Add net_amount_try column if it doesn't exist
ALTER TABLE transaction ADD COLUMN IF NOT EXISTS net_amount_try NUMERIC(15, 2);

-- Add exchange_rate column if it doesn't exist
ALTER TABLE transaction ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(10, 4);

-- Update existing transactions to populate TRY fields
-- For TL transactions, TRY amounts are the same as original amounts
UPDATE transaction 
SET amount_try = amount,
    commission_try = commission,
    net_amount_try = net_amount,
    exchange_rate = 1.0
WHERE currency = 'TL' 
  AND (amount_try IS NULL OR commission_try IS NULL OR net_amount_try IS NULL);

-- For USD transactions, calculate TRY amounts using current exchange rate
-- Note: This uses a default rate of 48.0 if no exchange rate is available
-- You should update these with actual historical rates if available
UPDATE transaction 
SET exchange_rate = (
    SELECT usd_to_tl 
    FROM exchange_rate 
    ORDER BY date DESC 
    LIMIT 1
),
amount_try = ABS(amount) * COALESCE((
    SELECT usd_to_tl 
    FROM exchange_rate 
    ORDER BY date DESC 
    LIMIT 1
), 48.0),
commission_try = ABS(commission) * COALESCE((
    SELECT usd_to_tl 
    FROM exchange_rate 
    ORDER BY date DESC 
    LIMIT 1
), 48.0),
net_amount_try = ABS(net_amount) * COALESCE((
    SELECT usd_to_tl 
    FROM exchange_rate 
    ORDER BY date DESC 
    LIMIT 1
), 48.0)
WHERE currency = 'USD' 
  AND (amount_try IS NULL OR commission_try IS NULL OR net_amount_try IS NULL);

-- Handle negative amounts for WD (withdrawal) transactions
UPDATE transaction 
SET amount_try = -amount_try,
    net_amount_try = -net_amount_try
WHERE category = 'WD' 
  AND amount_try > 0;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_transaction_amount_try ON transaction(amount_try);
CREATE INDEX IF NOT EXISTS idx_transaction_net_amount_try ON transaction(net_amount_try);
CREATE INDEX IF NOT EXISTS idx_transaction_exchange_rate ON transaction(exchange_rate);

