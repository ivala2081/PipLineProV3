-- Migration: Add strategy implementation tables
-- Created: 2025-09-25

-- Strategy implementations table
CREATE TABLE IF NOT EXISTS strategy_implementations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    config_data TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE(strategy_id, user_id, status)
);

-- System settings table (if not exists)
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Strategy performance tracking
CREATE TABLE IF NOT EXISTS strategy_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,2) NOT NULL,
    recorded_at DATETIME NOT NULL,
    notes TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_strategy_implementations_user_status 
ON strategy_implementations(user_id, status);

CREATE INDEX IF NOT EXISTS idx_strategy_implementations_strategy 
ON strategy_implementations(strategy_id);

CREATE INDEX IF NOT EXISTS idx_strategy_performance_strategy_date 
ON strategy_performance(strategy_id, recorded_at);

CREATE INDEX IF NOT EXISTS idx_system_settings_key 
ON system_settings(setting_key);

-- Insert default system settings
INSERT OR IGNORE INTO system_settings (setting_key, setting_value) VALUES 
('monday_campaign_active', 'false'),
('peak_hours_optimization', 'false'),
('weekend_optimization', 'false'),
('psp_optimization', 'false'),
('monday_discount_percentage', '0'),
('peak_hours_config', '{}'),
('psp_routing_config', '{}');
