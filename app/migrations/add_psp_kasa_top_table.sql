-- Migration: Add psp_kasa_top table for storing manual KASA TOP overrides
-- This table stores manual overrides for KASA TOP (Revenue) amounts by PSP and date

CREATE TABLE psp_kasa_top (
    id INTEGER NOT NULL, 
    date DATE NOT NULL, 
    psp_name VARCHAR(100) NOT NULL, 
    kasa_top_amount NUMERIC(15, 2) DEFAULT 0.0, 
    created_at DATETIME, 
    updated_at DATETIME, 
    PRIMARY KEY (id), 
    UNIQUE (date, psp_name), 
    CHECK (kasa_top_amount >= -999999999.99 AND kasa_top_amount <= 999999999.99)
);

-- Create indexes for better query performance
CREATE INDEX idx_psp_kasa_top_date ON psp_kasa_top (date);
CREATE INDEX idx_psp_kasa_top_psp ON psp_kasa_top (psp_name);
CREATE INDEX idx_psp_kasa_top_date_psp ON psp_kasa_top (date, psp_name);
