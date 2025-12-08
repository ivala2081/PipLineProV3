-- Migration script for Trust Wallet tables
-- Run this script to create the necessary tables for Trust wallet functionality

-- Create trust_wallet table
CREATE TABLE IF NOT EXISTS trust_wallet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_address VARCHAR(100) NOT NULL UNIQUE,
    wallet_name VARCHAR(100) NOT NULL,
    network VARCHAR(20) NOT NULL CHECK (network IN ('ETH', 'BSC', 'TRC')),
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    last_sync_block INTEGER DEFAULT 0,
    last_sync_time DATETIME,
    FOREIGN KEY (created_by) REFERENCES user(id)
);

-- Create trust_wallet_transaction table
CREATE TABLE IF NOT EXISTS trust_wallet_transaction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_id INTEGER NOT NULL,
    transaction_hash VARCHAR(100) NOT NULL UNIQUE,
    block_number INTEGER NOT NULL,
    block_timestamp DATETIME NOT NULL,
    from_address VARCHAR(100) NOT NULL,
    to_address VARCHAR(100) NOT NULL,
    token_symbol VARCHAR(20) NOT NULL,
    token_address VARCHAR(100),
    token_amount DECIMAL(36, 18) NOT NULL,
    token_decimals INTEGER DEFAULT 18,
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('IN', 'OUT', 'INTERNAL')),
    gas_fee DECIMAL(36, 18) DEFAULT 0,
    gas_fee_token VARCHAR(20) DEFAULT 'ETH',
    status VARCHAR(20) DEFAULT 'CONFIRMED' CHECK (status IN ('CONFIRMED', 'PENDING', 'FAILED')),
    confirmations INTEGER DEFAULT 0,
    network VARCHAR(20) NOT NULL CHECK (network IN ('ETH', 'BSC', 'TRC')),
    exchange_rate DECIMAL(15, 4),
    amount_try DECIMAL(15, 2),
    gas_fee_try DECIMAL(15, 2),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wallet_id) REFERENCES trust_wallet(id) ON DELETE CASCADE
);

-- Create indexes for trust_wallet table
CREATE INDEX IF NOT EXISTS idx_trust_wallet_address ON trust_wallet(wallet_address);
CREATE INDEX IF NOT EXISTS idx_trust_wallet_network ON trust_wallet(network);
CREATE INDEX IF NOT EXISTS idx_trust_wallet_active ON trust_wallet(is_active);
CREATE INDEX IF NOT EXISTS idx_trust_wallet_created_by ON trust_wallet(created_by);

-- Create indexes for trust_wallet_transaction table
CREATE INDEX IF NOT EXISTS idx_trust_tx_hash ON trust_wallet_transaction(transaction_hash);
CREATE INDEX IF NOT EXISTS idx_trust_tx_wallet ON trust_wallet_transaction(wallet_id);
CREATE INDEX IF NOT EXISTS idx_trust_tx_block ON trust_wallet_transaction(block_number);
CREATE INDEX IF NOT EXISTS idx_trust_tx_timestamp ON trust_wallet_transaction(block_timestamp);
CREATE INDEX IF NOT EXISTS idx_trust_tx_from ON trust_wallet_transaction(from_address);
CREATE INDEX IF NOT EXISTS idx_trust_tx_to ON trust_wallet_transaction(to_address);
CREATE INDEX IF NOT EXISTS idx_trust_tx_token ON trust_wallet_transaction(token_symbol);
CREATE INDEX IF NOT EXISTS idx_trust_tx_type ON trust_wallet_transaction(transaction_type);
CREATE INDEX IF NOT EXISTS idx_trust_tx_status ON trust_wallet_transaction(status);
CREATE INDEX IF NOT EXISTS idx_trust_tx_network ON trust_wallet_transaction(network);
CREATE INDEX IF NOT EXISTS idx_trust_tx_wallet_timestamp ON trust_wallet_transaction(wallet_id, block_timestamp);
CREATE INDEX IF NOT EXISTS idx_trust_tx_wallet_token ON trust_wallet_transaction(wallet_id, token_symbol);

-- Insert some sample data (optional)
-- You can uncomment these lines to add sample wallets for testing

/*
INSERT INTO trust_wallet (wallet_address, wallet_name, network, created_by) VALUES 
('0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6', 'Main Company Wallet', 'ETH', 1),
('0x8ba1f109551bD432803012645Hac136c', 'BSC Operations', 'BSC', 1),
('TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE', 'TRON Treasury', 'TRC', 1);
*/

-- Update the database version or add a note about this migration
-- You might want to add this to your migration tracking system
INSERT OR IGNORE INTO option (field_name, value) VALUES 
('trust_wallet_migration', '1.0'),
('trust_wallet_enabled', 'true');
