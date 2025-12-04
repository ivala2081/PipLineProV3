#!/usr/bin/env python3
"""
Database Restore Script
Restores database from backup file (SQLite or PostgreSQL)
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.backup_service import BackupService
from dotenv import load_dotenv


def restore_sqlite(backup_path: Path, target_path: Path = None):
    """Restore SQLite database from backup"""
    import shutil
    
    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_path}")
        return False
    
    if target_path is None:
        target_path = Path("instance/treasury_improved.db")
    
    # Create backup of current database before restore
    if target_path.exists():
        current_backup = target_path.parent / f"{target_path.stem}_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(target_path, current_backup)
        print(f"✅ Current database backed up to: {current_backup}")
    
    # Restore from backup
    try:
        shutil.copy2(backup_path, target_path)
        print(f"✅ Database restored from: {backup_path}")
        print(f"📁 Target: {target_path}")
        return True
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False


def restore_postgresql(backup_path: Path, database_url: str):
    """Restore PostgreSQL database from backup"""
    import subprocess
    from urllib.parse import urlparse
    
    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_path}")
        return False
    
    try:
        parsed = urlparse(database_url)
        
        # Set environment variables
        env = os.environ.copy()
        if parsed.password:
            env['PGPASSWORD'] = parsed.password
        
        # Build pg_restore command
        cmd = [
            'pg_restore',
            '-h', parsed.hostname or 'localhost',
            '-p', str(parsed.port or 5432),
            '-U', parsed.username or 'postgres',
            '-d', parsed.path.lstrip('/') if parsed.path else 'postgres',
            '--clean',  # Drop existing objects
            '--if-exists',  # Don't error if objects don't exist
            '--verbose',
            str(backup_path)
        ]
        
        print(f"🔄 Restoring PostgreSQL database...")
        print(f"   Host: {parsed.hostname or 'localhost'}")
        print(f"   Database: {parsed.path.lstrip('/')}")
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            print(f"❌ Restore failed:")
            print(result.stderr)
            return False
        
        print(f"✅ PostgreSQL database restored successfully")
        return True
        
    except FileNotFoundError:
        print("❌ pg_restore not found. Please install PostgreSQL client tools.")
        return False
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False


def main():
    """Main restore function"""
    parser = argparse.ArgumentParser(description='Restore database from backup')
    parser.add_argument('backup_path', help='Path to backup file')
    parser.add_argument('--target', help='Target database path (SQLite only)')
    parser.add_argument('--database-url', help='PostgreSQL database URL')
    parser.add_argument('--dry-run', action='store_true', help='Validate backup without restoring')
    
    args = parser.parse_args()
    
    print("="*70)
    print("PipLinePro Database Restore")
    print("="*70)
    
    backup_path = Path(args.backup_path)
    
    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_path}")
        sys.exit(1)
    
    # Load environment variables
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Environment variables loaded from {env_file}")
    
    # Verify backup
    print(f"\n🔍 Verifying backup: {backup_path}")
    backup_service = BackupService()
    is_valid, verify_msg, details = backup_service.verify_backup(backup_path)
    
    if not is_valid:
        print(f"❌ Backup verification failed: {verify_msg}")
        sys.exit(1)
    
    print(f"✅ {verify_msg}")
    if details and 'tables' in details:
        print(f"📊 Tables in backup: {details['tables']}")
    
    if args.dry_run:
        print("\n✅ Dry run completed - backup is valid")
        sys.exit(0)
    
    # Confirm restore
    print("\n⚠️  WARNING: This will overwrite the current database!")
    response = input("Type 'RESTORE' to confirm: ")
    if response != 'RESTORE':
        print("❌ Restore cancelled")
        sys.exit(1)
    
    # Determine database type and restore
    if backup_path.suffix == '.db' or 'sqlite' in backup_path.name.lower():
        # SQLite restore
        target = Path(args.target) if args.target else None
        success = restore_sqlite(backup_path, target)
    elif backup_path.suffix == '.sql' or 'postgres' in backup_path.name.lower():
        # PostgreSQL restore
        database_url = args.database_url or os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ PostgreSQL database URL required. Use --database-url or set DATABASE_URL")
            sys.exit(1)
        success = restore_postgresql(backup_path, database_url)
    else:
        print("❌ Unknown backup format. Use .db for SQLite or .sql for PostgreSQL")
        sys.exit(1)
    
    if success:
        print("\n" + "="*70)
        print("✅ Database restore completed successfully")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ Database restore failed")
        print("="*70)
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Restore cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Restore failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
