#!/usr/bin/env python3
"""
Check which database the Flask application is actually using
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_file = Path('.env')
if env_file.exists():
    load_dotenv(env_file)

print("=" * 70)
print("Checking Active Database Configuration")
print("=" * 70)

# Check environment variables
db_type = os.environ.get('DATABASE_TYPE', '').strip().lower()
flask_env = os.environ.get('FLASK_ENV', '').strip().lower()

print(f"\n[1] Environment Variables:")
print(f"  DATABASE_TYPE: {db_type if db_type else '(not set)'}")
print(f"  FLASK_ENV: {flask_env if flask_env else '(not set)'}")

# Check Flask app configuration
print(f"\n[2] Flask Application Configuration:")
try:
    from app import create_app
    
    app = create_app()
    with app.app_context():
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        print(f"  SQLALCHEMY_DATABASE_URI: {db_uri[:80]}...")
        
        # Determine database type from URI
        if 'postgresql' in db_uri.lower() or 'postgres' in db_uri.lower():
            print(f"  [OK] Application is configured to use PostgreSQL (Supabase)")
            db_type_detected = 'postgresql'
        elif 'sqlite' in db_uri.lower():
            print(f"  [WARNING] Application is configured to use SQLite")
            db_type_detected = 'sqlite'
        elif 'mssql' in db_uri.lower():
            print(f"  [INFO] Application is configured to use MSSQL")
            db_type_detected = 'mssql'
        else:
            print(f"  [UNKNOWN] Database type could not be determined")
            db_type_detected = 'unknown'
        
        # Check actual database connection
        print(f"\n[3] Testing Database Connection:")
        try:
            from app import db
            from sqlalchemy import text
            
            # Get connection info
            with db.engine.connect() as conn:
                if db_type_detected == 'postgresql':
                    result = conn.execute(text("SELECT version();"))
                    version = result.fetchone()[0]
                    print(f"  [OK] Connected to PostgreSQL")
                    print(f"       Version: {version.split(',')[0]}")
                    
                    # Check transaction count
                    result = conn.execute(text("SELECT COUNT(*) FROM transactions;"))
                    count = result.fetchone()[0]
                    print(f"       Transaction count: {count}")
                    
                elif db_type_detected == 'sqlite':
                    result = conn.execute(text("SELECT sqlite_version();"))
                    version = result.fetchone()[0]
                    print(f"  [WARNING] Connected to SQLite")
                    print(f"            Version: {version}")
                    
                    # Check transaction count
                    result = conn.execute(text("SELECT COUNT(*) FROM transactions;"))
                    count = result.fetchone()[0]
                    print(f"            Transaction count: {count}")
                    
        except Exception as e:
            print(f"  [ERROR] Failed to connect: {e}")
            
except Exception as e:
    print(f"  [ERROR] Failed to create Flask app: {e}")
    import traceback
    traceback.print_exc()

# Check SQLite database directly
print(f"\n[4] Checking SQLite Database (if exists):")
sqlite_path = Path('instance/treasury_fresh.db')
if sqlite_path.exists():
    try:
        import sqlite3
        conn = sqlite3.connect(str(sqlite_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions;")
        count = cursor.fetchone()[0]
        print(f"  [INFO] SQLite database exists")
        print(f"         Transaction count: {count}")
        
        # Get latest transaction
        cursor.execute("SELECT id, date, amount, currency FROM transactions ORDER BY id DESC LIMIT 1;")
        latest = cursor.fetchone()
        if latest:
            print(f"         Latest transaction ID: {latest[0]}, Date: {latest[1]}, Amount: {latest[2]} {latest[3]}")
        conn.close()
    except Exception as e:
        print(f"  [ERROR] Failed to read SQLite: {e}")
else:
    print(f"  [INFO] SQLite database not found")

# Check Supabase directly
print(f"\n[5] Checking Supabase Database:")
try:
    import psycopg2
    from urllib.parse import quote_plus
    
    host = os.environ.get('POSTGRES_HOST')
    port = os.environ.get('POSTGRES_PORT', '5432')
    db = os.environ.get('POSTGRES_DB')
    user = os.environ.get('POSTGRES_USER')
    password = os.environ.get('POSTGRES_PASSWORD')
    
    if all([host, db, user, password]):
        password_encoded = quote_plus(password)
        user_encoded = quote_plus(user)
        conn_string = f"postgresql://{user_encoded}:{password_encoded}@{host}:{port}/{db}"
        
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM transactions;")
        count = cursor.fetchone()[0]
        print(f"  [INFO] Supabase connection successful")
        print(f"         Transaction count: {count}")
        
        # Get latest transaction
        cursor.execute("SELECT id, date, amount, currency FROM transactions ORDER BY id DESC LIMIT 1;")
        latest = cursor.fetchone()
        if latest:
            print(f"         Latest transaction ID: {latest[0]}, Date: {latest[1]}, Amount: {latest[2]} {latest[3]}")
        
        cursor.close()
        conn.close()
    else:
        print(f"  [WARNING] Supabase credentials not found")
except Exception as e:
    print(f"  [ERROR] Failed to connect to Supabase: {e}")

print("\n" + "=" * 70)
print("Summary:")
print("=" * 70)
print("If the Flask app is using SQLite but you want it to use Supabase:")
print("  1. Make sure DATABASE_TYPE=postgresql in .env")
print("  2. Restart your Flask application")
print("  3. Verify with: python scripts/verify_supabase_config.py")

