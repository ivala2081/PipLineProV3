#!/usr/bin/env python3
"""
Helper script to set up environment variables for Supabase connection
This script helps you configure your .env file with Supabase credentials
"""

import os
from pathlib import Path

def parse_connection_string(conn_str):
    """Parse a PostgreSQL connection string or hostname"""
    from urllib.parse import urlparse, unquote
    
    # Check if it's just a hostname (no protocol)
    if not conn_str.startswith(('postgresql://', 'postgres://', 'http://', 'https://')):
        # It's likely just a hostname
        if 'supabase.co' in conn_str or 'localhost' in conn_str or '.' in conn_str:
            return {
                'host': conn_str.strip(),
                'port': '5432',
                'db': 'postgres',
                'user': 'postgres',
                'password': ''  # Will prompt for password
            }
    
    # Try to parse as full connection string
    try:
        parsed = urlparse(conn_str)
        if parsed.hostname:
            return {
                'host': parsed.hostname,
                'port': str(parsed.port) if parsed.port else '5432',
                'db': parsed.path.lstrip('/') if parsed.path else 'postgres',
                'user': unquote(parsed.username) if parsed.username else 'postgres',
                'password': unquote(parsed.password) if parsed.password else ''
            }
    except Exception:
        pass
    
    return None

def get_supabase_connection_info():
    """Interactive script to get Supabase connection details"""
    print("="*70)
    print("Supabase Connection Setup")
    print("="*70)
    print("\n📋 STEP-BY-STEP GUIDE TO FIND YOUR CONNECTION DETAILS:")
    print("\nMethod 1: Using Connection String (EASIEST)")
    print("  1. Go to: https://supabase.com/dashboard")
    print("  2. Select your project")
    print("  3. Click the 'Connect' button at the top of the page")
    print("  4. Under 'Connection string' → 'URI', copy the entire string")
    print("     It looks like: postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres")
    print("\nMethod 2: Individual Details")
    print("  1. Go to: https://supabase.com/dashboard")
    print("  2. Select your project")
    print("  3. Go to: Settings → Database")
    print("  4. Find 'Connection string' section")
    print("  5. Copy the details from there")
    print("\n" + "-"*70)
    
    # Try to get connection string first
    print("\n💡 TIP: You can paste the full connection string, or enter details individually")
    print("\nOption 1: Paste full connection string (recommended)")
    conn_string = input("Connection String (or press Enter to enter details manually): ").strip()
    
    if conn_string:
        parsed = parse_connection_string(conn_string)
        if parsed and parsed.get('host'):
            print(f"\n✅ Parsed connection details:")
            print(f"   Host: {parsed['host']}")
            print(f"   Port: {parsed['port']}")
            print(f"   Database: {parsed['db']}")
            print(f"   User: {parsed['user']}")
            if not parsed['password']:
                parsed['password'] = input("Password (not in connection string): ").strip()
            
            # Build connection string for return
            from urllib.parse import quote_plus
            password_encoded = quote_plus(parsed['password'])
            user_encoded = quote_plus(parsed['user'])
            full_conn_string = f"postgresql://{user_encoded}:{password_encoded}@{parsed['host']}:{parsed['port']}/{parsed['db']}"
            
            return {
                'host': parsed['host'],
                'port': parsed['port'],
                'db': parsed['db'],
                'user': parsed['user'],
                'password': parsed['password'],
                'connection_string': full_conn_string
            }
        else:
            print("⚠️  Could not parse connection string, please enter details manually")
    
    # Get connection details individually
    print("\nOption 2: Enter details individually")
    print("\nYour project URL appears to be: sihlxucjplorgptrosed.supabase.co")
    print("So your database host should be: db.sihlxucjplorgptrosed.supabase.co")
    print("\nEnter your Supabase connection details:")
    
    host = input("Database Host (default: db.sihlxucjplorgptrosed.supabase.co): ").strip()
    if not host:
        host = "db.sihlxucjplorgptrosed.supabase.co"
        print(f"   Using default: {host}")
    
    port = input("Database Port (default: 5432): ").strip() or "5432"
    db_name = input("Database Name (default: postgres): ").strip() or "postgres"
    user = input("Database User (default: postgres): ").strip() or "postgres"
    
    print("\n⚠️  IMPORTANT: You need your database password!")
    print("   If you don't know it:")
    print("   1. Go to: https://supabase.com/dashboard/project/sihlxucjplorgptrosed/settings/database")
    print("   2. Click 'Reset database password'")
    print("   3. Copy the new password")
    password = input("Database Password: ").strip()
    
    if not all([host, db_name, user, password]):
        print("\n❌ Error: All fields are required")
        return None
    
    # Build connection string
    from urllib.parse import quote_plus
    password_encoded = quote_plus(password)
    user_encoded = quote_plus(user)
    connection_string = f"postgresql://{user_encoded}:{password_encoded}@{host}:{port}/{db_name}"
    
    return {
        'host': host,
        'port': port,
        'db': db_name,
        'user': user,
        'password': password,
        'connection_string': connection_string
    }

def update_env_file(conn_info):
    """Update .env file with Supabase connection details"""
    env_file = Path('.env')
    
    # Read existing .env if it exists
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Update with Supabase connection details
    env_vars['DATABASE_TYPE'] = 'postgresql'
    env_vars['POSTGRES_HOST'] = conn_info['host']
    env_vars['POSTGRES_PORT'] = conn_info['port']
    env_vars['POSTGRES_DB'] = conn_info['db']
    env_vars['POSTGRES_USER'] = conn_info['user']
    env_vars['POSTGRES_PASSWORD'] = conn_info['password']
    env_vars['POSTGRES_SSL_MODE'] = 'require'
    
    # Also set Supabase-specific variables
    env_vars['SUPABASE_DB_HOST'] = conn_info['host']
    env_vars['SUPABASE_DB_PORT'] = conn_info['port']
    env_vars['SUPABASE_DB_NAME'] = conn_info['db']
    env_vars['SUPABASE_DB_USER'] = conn_info['user']
    env_vars['SUPABASE_DB_PASSWORD'] = conn_info['password']
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.write("# Database Configuration - Supabase PostgreSQL\n")
        f.write(f"DATABASE_TYPE=postgresql\n")
        f.write(f"POSTGRES_HOST={conn_info['host']}\n")
        f.write(f"POSTGRES_PORT={conn_info['port']}\n")
        f.write(f"POSTGRES_DB={conn_info['db']}\n")
        f.write(f"POSTGRES_USER={conn_info['user']}\n")
        f.write(f"POSTGRES_PASSWORD={conn_info['password']}\n")
        f.write(f"POSTGRES_SSL_MODE=require\n\n")
        
        f.write("# Supabase-specific variables (for migration script)\n")
        f.write(f"SUPABASE_DB_HOST={conn_info['host']}\n")
        f.write(f"SUPABASE_DB_PORT={conn_info['port']}\n")
        f.write(f"SUPABASE_DB_NAME={conn_info['db']}\n")
        f.write(f"SUPABASE_DB_USER={conn_info['user']}\n")
        f.write(f"SUPABASE_DB_PASSWORD={conn_info['password']}\n\n")
        
        # Write other existing variables
        f.write("# Other configuration\n")
        for key, value in env_vars.items():
            if key not in ['DATABASE_TYPE', 'POSTGRES_HOST', 'POSTGRES_PORT', 
                          'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 
                          'POSTGRES_SSL_MODE', 'SUPABASE_DB_HOST', 'SUPABASE_DB_PORT',
                          'SUPABASE_DB_NAME', 'SUPABASE_DB_USER', 'SUPABASE_DB_PASSWORD']:
                f.write(f"{key}={value}\n")
    
    print(f"\n✅ Updated {env_file} with Supabase connection details")
    print(f"\nConnection string: {conn_info['connection_string'][:50]}...")

def main():
    """Main function"""
    conn_info = get_supabase_connection_info()
    
    if conn_info:
        print("\n" + "="*70)
        print("Connection Details Summary")
        print("="*70)
        print(f"Host: {conn_info['host']}")
        print(f"Port: {conn_info['port']}")
        print(f"Database: {conn_info['db']}")
        print(f"User: {conn_info['user']}")
        print(f"Password: {'*' * len(conn_info['password'])}")
        
        confirm = input("\nSave these details to .env file? (yes/no): ").strip().lower()
        if confirm == 'yes':
            update_env_file(conn_info)
            print("\n✅ Configuration saved!")
            print("\nNext steps:")
            print("  1. Run: python scripts/migrate_to_supabase.py")
            print("  2. Verify migration was successful")
            print("  3. Restart your application")
        else:
            print("\n❌ Configuration not saved")

if __name__ == '__main__':
    main()

