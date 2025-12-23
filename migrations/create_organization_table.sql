-- Migration: Create organization table for multi-tenancy
-- This creates the foundation for B2B SaaS support
-- 
-- Run this migration with: python scripts/apply_migrations.py
-- Or manually in SQLite: sqlite3 instance/treasury_fresh.db < migrations/create_organization_table.sql
--
-- Date: 2025-12-22
-- Author: PipLinePro Multi-Tenancy Implementation

-- Create organization table
CREATE TABLE IF NOT EXISTS organization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Basic Info
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) NOT NULL UNIQUE,
    
    -- Subscription & Billing
    subscription_tier VARCHAR(20) DEFAULT 'free',
    subscription_status VARCHAR(20) DEFAULT 'active',
    subscription_expires_at DATETIME,
    
    -- Limits based on subscription
    max_users INTEGER DEFAULT 1,
    max_transactions_per_month INTEGER DEFAULT 100,
    max_psp_connections INTEGER DEFAULT 1,
    
    -- Organization Settings (JSON for flexibility)
    settings JSON,
    
    -- Branding (for white-label)
    logo_url VARCHAR(255),
    primary_color VARCHAR(7),
    
    -- Contact Info
    contact_email VARCHAR(120),
    contact_phone VARCHAR(20),
    address TEXT,
    country VARCHAR(50),
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Status
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_organization_slug ON organization(slug);
CREATE INDEX IF NOT EXISTS idx_organization_is_active ON organization(is_active);
CREATE INDEX IF NOT EXISTS idx_organization_subscription ON organization(subscription_tier, subscription_status);

-- Insert default organization for existing data
-- This ensures all existing users/transactions can be assigned to this organization
-- Using enterprise tier with high limits so existing functionality is not affected
INSERT OR IGNORE INTO organization (
    id, 
    name, 
    slug, 
    subscription_tier, 
    subscription_status,
    max_users, 
    max_transactions_per_month, 
    max_psp_connections,
    is_active
)
VALUES (
    1, 
    'Default Organization', 
    'default', 
    'enterprise',
    'active',
    999, 
    999999, 
    999,
    1
);

-- Verify the migration
SELECT 'Organization table created successfully!' AS status;
SELECT * FROM organization;

