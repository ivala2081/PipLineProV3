-- Migration: Add new fields to daily_net table for enhanced Net calculation
-- Date: 2025-11-03
-- Description: Adds ÖNCEKİ KAPANIŞ, ANLIK KASA, BEKLEYEN TAHSİLAT, FARK, and FARK_BOTTOM fields

-- Add new columns to daily_net table
ALTER TABLE daily_net ADD COLUMN IF NOT EXISTS onceki_kapanis_usd NUMERIC(15, 2) DEFAULT 0.0 NOT NULL;
ALTER TABLE daily_net ADD COLUMN IF NOT EXISTS anlik_kasa_usd NUMERIC(15, 2) DEFAULT 0.0 NOT NULL;
ALTER TABLE daily_net ADD COLUMN IF NOT EXISTS bekleyen_tahsilat_usd NUMERIC(15, 2) DEFAULT 0.0 NOT NULL;
ALTER TABLE daily_net ADD COLUMN IF NOT EXISTS fark_usd NUMERIC(15, 2) DEFAULT 0.0 NOT NULL;
ALTER TABLE daily_net ADD COLUMN IF NOT EXISTS fark_bottom_usd NUMERIC(15, 2) DEFAULT 0.0 NOT NULL;

-- Update existing rows to have 0.0 as default values (if they don't already have values)
UPDATE daily_net 
SET onceki_kapanis_usd = 0.0 
WHERE onceki_kapanis_usd IS NULL;

UPDATE daily_net 
SET anlik_kasa_usd = 0.0 
WHERE anlik_kasa_usd IS NULL;

UPDATE daily_net 
SET bekleyen_tahsilat_usd = 0.0 
WHERE bekleyen_tahsilat_usd IS NULL;

UPDATE daily_net 
SET fark_usd = 0.0 
WHERE fark_usd IS NULL;

UPDATE daily_net 
SET fark_bottom_usd = 0.0 
WHERE fark_bottom_usd IS NULL;

-- Note: If using SQLite, you may need to recreate the table instead
-- SQLite doesn't support ALTER TABLE ADD COLUMN with NOT NULL and DEFAULT in all versions

