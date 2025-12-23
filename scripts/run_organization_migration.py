"""
Run Organization Table Migration
Creates the organization table for multi-tenancy support
"""
import os
import sys
import sqlite3
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_migration():
    """Run the organization table migration"""
    
    # Database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'instance', 'treasury_fresh.db')
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found at: {db_path}")
        return False
    
    print(f"[INFO] Database: {db_path}")
    print(f"[INFO] Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if organization table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='organization'")
        if cursor.fetchone():
            print("[WARN] Organization table already exists!")
            cursor.execute("SELECT * FROM organization")
            rows = cursor.fetchall()
            print(f"   Found {len(rows)} organization(s)")
            for row in rows:
                print(f"   - ID: {row[0]}, Name: {row[1]}, Slug: {row[2]}")
            conn.close()
            return True
        
        print("[INFO] Creating organization table...")
        
        # Create organization table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organization (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                slug VARCHAR(50) NOT NULL UNIQUE,
                subscription_tier VARCHAR(20) DEFAULT 'free',
                subscription_status VARCHAR(20) DEFAULT 'active',
                subscription_expires_at DATETIME,
                max_users INTEGER DEFAULT 1,
                max_transactions_per_month INTEGER DEFAULT 100,
                max_psp_connections INTEGER DEFAULT 1,
                settings JSON,
                logo_url VARCHAR(255),
                primary_color VARCHAR(7),
                contact_email VARCHAR(120),
                contact_phone VARCHAR(20),
                address TEXT,
                country VARCHAR(50),
                timezone VARCHAR(50) DEFAULT 'UTC',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Organization table created")
        
        # Create indexes
        print("[INFO] Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_organization_slug ON organization(slug)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_organization_is_active ON organization(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_organization_subscription ON organization(subscription_tier, subscription_status)")
        print("[OK] Indexes created")
        
        # Insert default organization
        print("[INFO] Inserting default organization...")
        cursor.execute("""
            INSERT OR IGNORE INTO organization (
                id, name, slug, subscription_tier, subscription_status,
                max_users, max_transactions_per_month, max_psp_connections, is_active
            ) VALUES (
                1, 'Default Organization', 'default', 'enterprise', 'active',
                999, 999999, 999, 1
            )
        """)
        print("[OK] Default organization created (ID: 1)")
        
        # Commit changes
        conn.commit()
        
        # Verify
        print("-" * 50)
        print("[INFO] Verification:")
        cursor.execute("SELECT * FROM organization")
        rows = cursor.fetchall()
        print(f"   Organizations in database: {len(rows)}")
        for row in rows:
            print(f"   - ID: {row[0]}, Name: {row[1]}, Slug: {row[2]}, Tier: {row[3]}")
        
        conn.close()
        
        print("-" * 50)
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

