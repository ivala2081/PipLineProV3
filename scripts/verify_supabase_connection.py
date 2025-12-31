#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify Supabase connection with Session Pooler
"""

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 is required")
    print("Install it with: pip install psycopg2-binary")
    sys.exit(1)

from dotenv import load_dotenv

def test_connection():
    """Test Supabase Session Pooler connection"""
    print("="*70)
    print("Testing Supabase Session Pooler Connection")
    print("="*70)
    
    # Load environment
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
        print(f"[OK] Loaded environment from {env_file}")
    
    # Get connection details
    host = os.getenv('POSTGRES_HOST') or os.getenv('SUPABASE_DB_HOST')
    port = os.getenv('POSTGRES_PORT', '5432')
    db = os.getenv('POSTGRES_DB', 'postgres')
    user = os.getenv('POSTGRES_USER') or os.getenv('SUPABASE_DB_USER')
    password = os.getenv('POSTGRES_PASSWORD') or os.getenv('SUPABASE_DB_PASSWORD')
    
    print(f"\nConnection Details:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Database: {db}")
    print(f"  User: {user}")
    print(f"  Password: {'*' * len(password) if password else 'NOT SET'}")
    
    if not all([host, db, user, password]):
        print("\n[ERROR] Missing connection details!")
        return False
    
    # Build connection string
    password_encoded = quote_plus(password)
    user_encoded = quote_plus(user)
    conn_string = f"postgresql://{user_encoded}:{password_encoded}@{host}:{port}/{db}"
    
    print(f"\n[INFO] Connection string format:")
    print(f"  postgresql://{user_encoded}:***@{host}:{port}/{db}")
    
    try:
        print("\n[INFO] Attempting connection...")
        conn = psycopg2.connect(conn_string)
        print("[OK] Connection successful!")
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"\nPostgreSQL Version: {version[:50]}...")
        
        # List tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"\nFound {len(tables)} tables in public schema")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("[OK] Connection test PASSED!")
        print("="*70)
        return True
        
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        print(f"\n[ERROR] Connection failed!")
        print(f"Error: {error_msg}")
        
        if "password authentication failed" in error_msg.lower():
            print("\n[INFO] Password authentication failed. Possible issues:")
            print("  1. Password might be incorrect")
            print("  2. Username format might be wrong for Session Pooler")
            print("\nFor Session Pooler, username should be: postgres.[PROJECT-REF]")
            print(f"  Your username: {user}")
            print("\nTo fix:")
            print("  1. Verify password in Supabase dashboard")
            print("  2. Reset password if needed: https://supabase.com/dashboard/project/sihlxucjplorgptrosed/settings/database")
            print("  3. Make sure username is: postgres.sihlxucjplorgptrosed")
        
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)

