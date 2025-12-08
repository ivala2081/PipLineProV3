"""
Apply Migrations Script
=======================

WHAT IS THIS?
-------------
This script applies migration files to your database.
Think of it like following a recipe to build your house.

WHEN TO USE IT:
--------------
- After pulling new code from git (if there are new migrations)
- When setting up the database on a new computer
- After someone else added new database tables or columns

WHAT IT DOES:
------------
1. Reads migration files from migrations/versions/
2. Applies them to your database in order
3. Creates or updates tables as needed
4. Keeps track of which migrations have been applied

HOW TO USE:
----------
python scripts/apply_migrations.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

from app import create_app

def apply_migrations():
    """Apply all pending migrations to the database"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("APPLYING MIGRATIONS")
        print("=" * 60)
        print("")
        print("This will update your database structure using migration files.")
        print("")
        
        try:
            from flask_migrate import upgrade, current, history
            
            # Show current migration status
            print("Checking current migration status...")
            try:
                current_rev = current()
                print(f"  Current database version: {current_rev}")
            except:
                print("  No migrations applied yet (fresh database)")
            
            # Show available migrations
            print("")
            print("Available migrations:")
            migrations = history()
            for migration in migrations:
                print(f"  - {migration.revision}: {migration.doc}")
            
            print("")
            print("Applying migrations...")
            
            # Apply all pending migrations
            upgrade()
            
            print("")
            print("=" * 60)
            print("✓ MIGRATIONS APPLIED SUCCESSFULLY!")
            print("=" * 60)
            print("")
            print("Your database is now up to date!")
            print("")
            print("NEXT STEP:")
            print("Run 'python scripts/seed_database.py' to add starting data")
            print("")
            return True
            
        except Exception as e:
            print("")
            print("=" * 60)
            print(f"✗ ERROR: {e}")
            print("=" * 60)
            print("")
            print("TROUBLESHOOTING:")
            print("1. Make sure migration files exist in migrations/versions/")
            print("2. Make sure your database file is not locked by another program")
            print("3. Check that all your models are properly defined")
            print("")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = apply_migrations()
    sys.exit(0 if success else 1)

