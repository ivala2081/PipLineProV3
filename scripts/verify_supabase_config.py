#!/usr/bin/env python3
"""
Verify Supabase Configuration
Checks if the application is configured to use Supabase PostgreSQL.
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
else:
    print("[ERROR] .env file not found!")
    sys.exit(1)

print("=" * 70)
print("Verifying Supabase Configuration")
print("=" * 70)

# Check database type
db_type = os.environ.get('DATABASE_TYPE', '').strip().lower()
print(f"\n[1] DATABASE_TYPE: {db_type if db_type else '(not set - defaults to sqlite)'}")

if db_type not in ['postgresql', 'postgres']:
    print("[WARNING] DATABASE_TYPE is not set to 'postgresql' or 'postgres'")
    print("          The application will use SQLite instead of Supabase!")
    print("\nTo fix this, run:")
    print("  python scripts/setup_supabase_env.py")
    sys.exit(1)

# Check PostgreSQL connection details
required_vars = {
    'POSTGRES_HOST': os.environ.get('POSTGRES_HOST'),
    'POSTGRES_PORT': os.environ.get('POSTGRES_PORT', '5432'),
    'POSTGRES_DB': os.environ.get('POSTGRES_DB'),
    'POSTGRES_USER': os.environ.get('POSTGRES_USER'),
    'POSTGRES_PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
}

print("\n[2] PostgreSQL Connection Details:")
missing_vars = []
for var_name, var_value in required_vars.items():
    if var_value:
        if 'PASSWORD' in var_name:
            display_value = '*' * len(var_value)
        else:
            display_value = var_value
        print(f"  {var_name}: {display_value}")
    else:
        print(f"  {var_name}: (NOT SET)")
        if var_name != 'POSTGRES_PORT':  # Port has a default
            missing_vars.append(var_name)

if missing_vars:
    print(f"\n[ERROR] Missing required environment variables: {', '.join(missing_vars)}")
    print("To fix this, run:")
    print("  python scripts/setup_supabase_env.py")
    sys.exit(1)

# Check SSL mode
ssl_mode = os.environ.get('POSTGRES_SSL_MODE', 'prefer')
print(f"\n[3] SSL Mode: {ssl_mode}")

# Test connection
print("\n[4] Testing database connection...")
try:
    import psycopg2
    from urllib.parse import quote_plus
    
    host = required_vars['POSTGRES_HOST']
    port = required_vars['POSTGRES_PORT']
    db = required_vars['POSTGRES_DB']
    user = required_vars['POSTGRES_USER']
    password = required_vars['POSTGRES_PASSWORD']
    
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=db,
        user=user,
        password=password,
        sslmode=ssl_mode
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    print(f"[OK] Connection successful!")
    print(f"     PostgreSQL Version: {version.split(',')[0]}")
    
except ImportError:
    print("[ERROR] psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
    sys.exit(1)

# Check if Flask app can connect
print("\n[5] Testing Flask application configuration...")
try:
    from config import DevelopmentConfig
    
    db_uri = DevelopmentConfig.get_database_uri()
    if 'postgresql' in db_uri.lower():
        print(f"[OK] Flask is configured to use PostgreSQL")
        print(f"     Connection string: postgresql://{user}:***@{host}:{port}/{db}")
    else:
        print(f"[WARNING] Flask is not configured to use PostgreSQL")
        print(f"     Current URI: {db_uri[:80]}...")
        sys.exit(1)
        
except Exception as e:
    print(f"[ERROR] Failed to test Flask configuration: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("[OK] All checks passed! Application is configured for Supabase.")
print("=" * 70)
print("\nNext steps:")
print("  1. Restart your Flask application")
print("  2. Run database migrations if needed: flask db upgrade")
print("  3. Verify the application connects to Supabase successfully")

