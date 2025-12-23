"""
Add organization_id to User table and assign existing users to default organization
"""
import os
import sys
import sqlite3
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_migration():
    """Add organization_id column to user table"""
    
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
        
        # Check if organization_id column already exists in user table
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'organization_id' in columns:
            print("[WARN] organization_id column already exists in user table!")
            cursor.execute("SELECT id, username, organization_id FROM user")
            rows = cursor.fetchall()
            print(f"   Found {len(rows)} user(s)")
            for row in rows:
                print(f"   - ID: {row[0]}, Username: {row[1]}, Org ID: {row[2]}")
            conn.close()
            return True
        
        print("[INFO] Adding organization_id column to user table...")
        
        # Add organization_id column (nullable for backwards compatibility)
        cursor.execute("""
            ALTER TABLE user ADD COLUMN organization_id INTEGER REFERENCES organization(id)
        """)
        print("[OK] organization_id column added")
        
        # Create index for organization_id
        print("[INFO] Creating index for organization_id...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_organization ON user(organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_org_active ON user(organization_id, is_active)")
        print("[OK] Indexes created")
        
        # Assign all existing users to the default organization (ID: 1)
        print("[INFO] Assigning existing users to default organization...")
        cursor.execute("UPDATE user SET organization_id = 1 WHERE organization_id IS NULL")
        affected_rows = cursor.rowcount
        print(f"[OK] Assigned {affected_rows} user(s) to default organization")
        
        # Commit changes
        conn.commit()
        
        # Verify
        print("-" * 50)
        print("[INFO] Verification:")
        cursor.execute("SELECT id, username, organization_id FROM user")
        rows = cursor.fetchall()
        print(f"   Users in database: {len(rows)}")
        for row in rows:
            print(f"   - ID: {row[0]}, Username: {row[1]}, Org ID: {row[2]}")
        
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

