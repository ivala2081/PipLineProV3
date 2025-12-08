-- Migration: Add PSP Commission Rate table for time-based commission rates
-- This allows PSPs to have different commission rates at different times

CREATE TABLE psp_commission_rate (
    id INTEGER NOT NULL, 
    psp_name VARCHAR(100) NOT NULL, 
    commission_rate NUMERIC(5, 4) NOT NULL, 
    effective_from DATE NOT NULL, 
    effective_until DATE, 
    is_active BOOLEAN DEFAULT 1, 
    created_at DATETIME, 
    updated_at DATETIME, 
    PRIMARY KEY (id)
);

-- Create indexes for performance
CREATE INDEX idx_psp_commission_rate_psp ON psp_commission_rate (psp_name);
CREATE INDEX idx_psp_commission_rate_effective_from ON psp_commission_rate (effective_from);
CREATE INDEX idx_psp_commission_rate_effective_until ON psp_commission_rate (effective_until);
CREATE INDEX idx_psp_commission_rate_psp_effective ON psp_commission_rate (psp_name, effective_from);
CREATE INDEX idx_psp_commission_rate_active ON psp_commission_rate (is_active);

-- Note: SQLite doesn't support CHECK constraints in ALTER TABLE
-- Constraints are enforced at the application level
