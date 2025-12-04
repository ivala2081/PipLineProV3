-- Migration: Add PSPDevir table for storing manual Devir overrides
-- Date: 2025-09-29
-- Description: Creates psp_devir table to store manual Devir (Transfer/Carryover) overrides

CREATE TABLE IF NOT EXISTS psp_devir (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    psp_name VARCHAR(100) NOT NULL,
    devir_amount DECIMAL(15, 2) DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_psp_devir_date ON psp_devir(date);
CREATE INDEX IF NOT EXISTS idx_psp_devir_psp ON psp_devir(psp_name);
CREATE INDEX IF NOT EXISTS idx_psp_devir_date_psp ON psp_devir(date, psp_name);

-- Create unique constraint to ensure one Devir override per PSP per date
CREATE UNIQUE INDEX IF NOT EXISTS uq_psp_devir_date_psp ON psp_devir(date, psp_name);

-- Add trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_psp_devir_updated_at 
    AFTER UPDATE ON psp_devir
    FOR EACH ROW
    BEGIN
        UPDATE psp_devir SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
