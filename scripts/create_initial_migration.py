"""
Create Initial Migration Script
================================

WHAT IS THIS?
-------------
This script creates the FIRST migration file that describes your database structure.
Think of it like taking a photo of your house before you start remodeling.

WHEN TO USE IT:
--------------
- When you want to start tracking database changes
- When setting up a new project
- BEFORE making any changes to your database structure

WHAT IT DOES:
------------
1. Creates a migration file that describes ALL your current database tables
2. This file can be used to recreate your database structure anywhere
3. You can commit this file to git (it's just text, not the actual database)

HOW TO USE:
----------
python scripts/create_initial_migration.py
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

def create_initial_migration():
    """Create the first migration file"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("CREATING INITIAL MIGRATION")
        print("=" * 60)
        print("")
        print("This will create a migration file that describes your database.")
        print("")
        
        try:
            # Use Flask-Migrate to create migration
            from flask_migrate import init, migrate, upgrade
            
            # Check if migrations folder exists
            migrations_dir = Path('migrations')
            if not migrations_dir.exists() or not (migrations_dir / 'versions').exists():
                print("Initializing migrations folder...")
                init()
                print("✓ Migrations folder initialized")
                print("")
            
            # Create the initial migration
            print("Creating initial migration file...")
            print("(This captures your current database structure)")
            print("")
            
            # Create migration with auto-detection
            migrate(message="Initial migration: Create all database tables")
            
            print("")
            print("=" * 60)
            print("✓ INITIAL MIGRATION CREATED!")
            print("=" * 60)
            print("")
            print("The migration file is in: migrations/versions/")
            print("")
            print("WHAT TO DO NEXT:")
            print("1. Review the migration file to make sure it's correct")
            print("2. Commit the migration file to git (it's safe - just text)")
            print("3. Use 'python scripts/apply_migrations.py' to apply it to other databases")
            print("")
            return True
            
        except Exception as e:
            print("")
            print("=" * 60)
            print(f"✗ ERROR: {e}")
            print("=" * 60)
            print("")
            print("TROUBLESHOOTING:")
            print("1. Make sure Flask-Migrate is installed: pip install flask-migrate")
            print("2. Make sure your database file exists")
            print("3. Check that all your models are properly defined")
            print("")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = create_initial_migration()
    sys.exit(0 if success else 1)

