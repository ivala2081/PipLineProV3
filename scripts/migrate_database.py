"""
Database Migration Script
Flask-Migrate ile database migration islemlerini yonetir
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from flask_migrate import upgrade, downgrade, current, history, migrate, init, revision
from app import create_app, db


def init_migrations():
    """Initialize Flask-Migrate migration repository"""
    app = create_app()
    with app.app_context():
        try:
            init()
            print("✓ Migration repository initialized successfully")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ Migration repository already exists")
                return True
            print(f"✗ Error initializing migrations: {e}")
            return False


def create_migration(message: str = None):
    """Create a new migration"""
    app = create_app()
    with app.app_context():
        try:
            if message:
                migrate(message=message)
            else:
                migrate()
            print("✓ Migration created successfully")
            return True
        except Exception as e:
            print(f"✗ Error creating migration: {e}")
            return False


def apply_migrations(revision: str = "head"):
    """Apply migrations to database"""
    app = create_app()
    with app.app_context():
        try:
            upgrade(revision=revision)
            print(f"✓ Migrations applied successfully to {revision}")
            return True
        except Exception as e:
            print(f"✗ Error applying migrations: {e}")
            return False


def rollback_migration(revision: str = "-1"):
    """Rollback last migration"""
    app = create_app()
    with app.app_context():
        try:
            downgrade(revision=revision)
            print(f"✓ Migration rolled back successfully to {revision}")
            return True
        except Exception as e:
            print(f"✗ Error rolling back migration: {e}")
            return False


def show_current():
    """Show current migration version"""
    app = create_app()
    with app.app_context():
        try:
            current_rev = current()
            print(f"Current migration: {current_rev}")
            return current_rev
        except Exception as e:
            print(f"✗ Error getting current migration: {e}")
            return None


def show_history():
    """Show migration history"""
    app = create_app()
    with app.app_context():
        try:
            hist = history()
            print("Migration history:")
            for rev in hist:
                print(f"  {rev.revision}: {rev.doc}")
            return hist
        except Exception as e:
            print(f"✗ Error getting migration history: {e}")
            return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration management")
    parser.add_argument("command", choices=["init", "create", "upgrade", "downgrade", "current", "history"],
                       help="Migration command to execute")
    parser.add_argument("-m", "--message", help="Migration message (for create command)")
    parser.add_argument("-r", "--revision", help="Revision to upgrade/downgrade to")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_migrations()
    elif args.command == "create":
        create_migration(args.message)
    elif args.command == "upgrade":
        apply_migrations(args.revision or "head")
    elif args.command == "downgrade":
        rollback_migration(args.revision or "-1")
    elif args.command == "current":
        show_current()
    elif args.command == "history":
        show_history()

