#!/usr/bin/env python3
"""
Database Backup Script
Supports both SQLite and PostgreSQL
Can be run as a cron job for automated backups
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.backup_service import BackupService
from dotenv import load_dotenv


def main():
    """Main backup function"""
    print("="*70)
    print("PipLinePro Database Backup")
    print("="*70)
    
    # Load environment variables
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Environment variables loaded from {env_file}")
    else:
        print("⚠️  No .env file found, using system environment variables")
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Try to build from components
        if all([os.getenv('POSTGRES_HOST'), os.getenv('POSTGRES_DB')]):
            user = os.getenv('POSTGRES_USER', 'postgres')
            password = os.getenv('POSTGRES_PASSWORD', '')
            host = os.getenv('POSTGRES_HOST')
            port = os.getenv('POSTGRES_PORT', '5432')
            db = os.getenv('POSTGRES_DB')
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    # Initialize backup service
    config = {
        'BACKUP_ENABLED': True,
        'BACKUP_RETENTION_DAYS': int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
    }
    
    backup_service = BackupService(config)
    
    # Create backup
    print("\n🔄 Creating backup...")
    success, message, backup_path = backup_service.create_backup(database_url)
    
    if success:
        print(f"✅ {message}")
        if backup_path:
            print(f"📁 Backup location: {backup_path}")
            
            # Verify backup
            print("\n🔍 Verifying backup...")
            is_valid, verify_msg, details = backup_service.verify_backup(backup_path)
            if is_valid:
                print(f"✅ {verify_msg}")
                if 'tables' in details:
                    print(f"📊 Tables: {details['tables']}")
            else:
                print(f"❌ {verify_msg}")
    else:
        print(f"❌ {message}")
        sys.exit(1)
    
    # List recent backups
    print("\n📋 Recent backups:")
    backups = backup_service.list_backups()
    if backups:
        for backup in backups[:5]:  # Show last 5
            print(f"  - {backup['filename']} ({backup['size_mb']} MB, {backup['age_days']} days old)")
    else:
        print("  No backups found")
    
    print("\n" + "="*70)
    print("✅ Backup completed successfully")
    print("="*70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Backup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Backup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

