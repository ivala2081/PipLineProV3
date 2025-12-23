"""
Add organization_id to all main data models for multi-tenancy support
This script adds organization_id to:
- Transaction
- Expense
- DailyNet
- ExpenseBudget
- MonthlyCurrencySummary
- PspTrack
- DailyBalance
- PSPAllocation
- PSPDevir
- PSPKasaTop
- TrustWallet
- TrustWalletTransaction
"""
import os
import sys
import sqlite3
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Tables that need organization_id
TABLES_TO_UPDATE = [
    'transaction',
    'expense',
    'daily_net',
    'expense_budget',
    'monthly_currency_summary',
    'psp_track',
    'daily_balance',
    'psp_allocation',
    'psp_devir',
    'psp_kasa_top',
    'trust_wallet',
    'trust_wallet_transaction',
]

def run_migration():
    """Add organization_id column to all main data tables"""
    
    # Database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'instance', 'treasury_fresh.db')
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found at: {db_path}")
        return False
    
    print(f"[INFO] Database: {db_path}")
    print(f"[INFO] Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"[INFO] Found {len(existing_tables)} tables in database")
        
        updated_tables = []
        skipped_tables = []
        missing_tables = []
        
        for table_name in TABLES_TO_UPDATE:
            print(f"\n[INFO] Processing table: {table_name}")
            
            # Check if table exists
            if table_name not in existing_tables:
                print(f"  [SKIP] Table does not exist")
                missing_tables.append(table_name)
                continue
            
            # Check if organization_id column already exists
            # Use quotes for table names to handle reserved words like 'transaction'
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'organization_id' in columns:
                print(f"  [SKIP] organization_id already exists")
                skipped_tables.append(table_name)
                continue
            
            # Add organization_id column
            print(f"  [ADD] Adding organization_id column...")
            cursor.execute(f'''
                ALTER TABLE "{table_name}" ADD COLUMN organization_id INTEGER REFERENCES organization(id)
            ''')
            
            # Create index for organization_id
            index_name = f"idx_{table_name}_organization"
            cursor.execute(f'''
                CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table_name}"(organization_id)
            ''')
            
            # Assign existing records to default organization (ID: 1)
            cursor.execute(f'UPDATE "{table_name}" SET organization_id = 1 WHERE organization_id IS NULL')
            affected_rows = cursor.rowcount
            print(f"  [OK] Added column, created index, assigned {affected_rows} rows to default org")
            
            updated_tables.append(table_name)
        
        # Commit changes
        conn.commit()
        
        # Summary
        print("\n" + "=" * 60)
        print("[SUMMARY]")
        print(f"  Updated tables: {len(updated_tables)}")
        for t in updated_tables:
            print(f"    - {t}")
        
        print(f"  Skipped tables (already had organization_id): {len(skipped_tables)}")
        for t in skipped_tables:
            print(f"    - {t}")
        
        print(f"  Missing tables (not in database): {len(missing_tables)}")
        for t in missing_tables:
            print(f"    - {t}")
        
        # Verify by counting records per organization
        print("\n[VERIFICATION] Records per organization:")
        for table_name in TABLES_TO_UPDATE:
            if table_name in existing_tables:
                try:
                    cursor.execute(f'SELECT organization_id, COUNT(*) FROM "{table_name}" GROUP BY organization_id')
                    results = cursor.fetchall()
                    if results:
                        for org_id, count in results:
                            print(f"  {table_name}: Org {org_id} = {count} records")
                    else:
                        print(f"  {table_name}: 0 records")
                except:
                    print(f"  {table_name}: Could not query")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("[OK] Migration completed successfully!")
        print(f"[INFO] Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

