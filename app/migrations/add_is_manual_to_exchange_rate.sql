-- Migration: Add is_manual column to exchange_rate table
-- Purpose: Track whether an exchange rate was manually edited to prevent auto-updates from overwriting it
-- Date: 2025-10-15

-- Add is_manual column with default value of False
ALTER TABLE exchange_rate ADD COLUMN is_manual BOOLEAN NOT NULL DEFAULT 0;

-- Create index for faster queries on manual rates
CREATE INDEX IF NOT EXISTS idx_exchange_rate_is_manual ON exchange_rate(is_manual);

-- Update comment for the table
-- COMMENT ON COLUMN exchange_rate.is_manual IS 'Flag indicating if the rate was manually edited by a user';

