#!/usr/bin/env python3
"""
Test Supabase PostgreSQL Connection
Quick script to verify your Supabase connection is working
"""

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("❌ Error: psycopg2 is required")
    print("   Install it with: pip install psycopg2-binary")
    sys.exit(1)

from dotenv import load_dotenv


def test_connection():
    """Test Supabase PostgreSQL connection"""
    print("="*70)
    print("Testing Supabase Connection")
    print("="*70)
    
    # Load environment variables
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
        print(f"[OK] Loaded environment from {env_file}")
    else:
        print("[WARNING] No .env file found, using system environment variables")
    
    # Get connection details
    host = os.getenv('SUPABASE_DB_HOST') or os.getenv('POSTGRES_HOST')
    port = os.getenv('SUPABASE_DB_PORT') or os.getenv('POSTGRES_PORT', '5432')
    db = os.getenv('SUPABASE_DB_NAME') or os.getenv('POSTGRES_DB')
    user = os.getenv('SUPABASE_DB_USER') or os.getenv('POSTGRES_USER')
    password = os.getenv('SUPABASE_DB_PASSWORD') or os.getenv('POSTGRES_PASSWORD')
    
    if not all([host, db, user, password]):
        print("\n[ERROR] Missing connection details!")
        print("\nRequired environment variables:")
        print("  SUPABASE_DB_HOST (or POSTGRES_HOST)")
        print("  SUPABASE_DB_NAME (or POSTGRES_DB)")
        print("  SUPABASE_DB_USER (or POSTGRES_USER)")
        print("  SUPABASE_DB_PASSWORD (or POSTGRES_PASSWORD)")
        print("\nRun: python scripts/setup_supabase_env.py")
        return False
    
    print(f"\nConnection Details:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Database: {db}")
    print(f"  User: {user}")
    print(f"  Password: {'*' * len(password)}")
    
    # Build connection string
    password_encoded = quote_plus(password)
    user_encoded = quote_plus(user)
    conn_string = f"postgresql://{user_encoded}:{password_encoded}@{host}:{port}/{db}"
    
    try:
        print("\n[INFO] Connecting to Supabase...")
        conn = psycopg2.connect(conn_string)
        print("[OK] Connection successful!")
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"\nPostgreSQL Version: {version}")
        
        # List tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print(f"\nFound {len(tables)} tables in public schema:")
        for table in tables[:10]:  # Show first 10
            print(f"  - {table[0]}")
        if len(tables) > 10:
            print(f"  ... and {len(tables) - 10} more")
        
        # Check for key tables
        table_names = [t[0] for t in tables]
        key_tables = ['organizations', 'users', 'transactions', 'exchange_rates']
        print(f"\nChecking key tables:")
        for table in key_tables:
            if table in table_names:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"  [OK] {table}: {count} rows")
            else:
                print(f"  [WARNING] {table}: Not found")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("[OK] Connection test passed!")
        print("="*70)
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify your Supabase credentials")
        print("  2. Check if your IP is allowed in Supabase dashboard")
        print("  3. Ensure SSL mode is set correctly")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)

