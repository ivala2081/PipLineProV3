-- Performance Optimization Indexes for Monthly PSP Report
-- Created: 2025-11-19
-- Purpose: Dramatically improve monthly stats query performance

-- Critical index for monthly PSP stats query
-- This index covers the main query pattern: WHERE psp IN (...) AND date BETWEEN ... AND ... AND category IN (...)
CREATE INDEX IF NOT EXISTS idx_transaction_psp_date_category 
ON transaction(psp, date, category);

-- Note: Other indexes already exist in the Transaction model
-- - idx_transaction_date_psp_category (date, psp, category)
-- - idx_transaction_psp (psp)
-- - idx_transaction_date (date)
-- - idx_transaction_category (category)

-- PSPAllocation already has composite indexes:
-- - idx_psp_allocation_date_psp (date, psp_name)
-- - idx_psp_allocation_date (date)
-- - idx_psp_allocation_psp (psp_name)

-- PSPDevir already has composite indexes:
-- - idx_psp_devir_date_psp (date, psp_name)
-- - idx_psp_devir_date (date)
-- - idx_psp_devir_psp (psp_name)

-- Verify indexes were created
SELECT 
    name as index_name,
    tbl_name as table_name,
    sql as definition
FROM sqlite_master
WHERE type = 'index' 
AND (
    name LIKE 'idx_transaction_%' 
    OR name LIKE 'idx_psp_allocation_%'
    OR name LIKE 'idx_psp_devir_%'
)
ORDER BY tbl_name, name;

