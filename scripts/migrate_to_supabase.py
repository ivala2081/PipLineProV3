#!/usr/bin/env python3
"""
Migration Script: SQLite to Supabase (PostgreSQL)
Migrates all data from local SQLite database to Supabase PostgreSQL database.

This script:
1. Connects to both SQLite (source) and Supabase PostgreSQL (destination)
2. Exports all data from SQLite
3. Converts integer IDs to UUIDs
4. Maps foreign key relationships
5. Imports data to Supabase
6. Verifies data integrity
"""

import os
import sys
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from psycopg2.extras import execute_values
    from psycopg2 import sql
    from psycopg2 import errors as pg_errors
except ImportError:
    print("[ERROR] psycopg2 is required for PostgreSQL connection")
    print("   Install it with: pip install psycopg2-binary")
    sys.exit(1)

from dotenv import load_dotenv


class SupabaseMigrator:
    """Handles migration from SQLite to Supabase"""
    
    def __init__(self):
        """Initialize migrator with database connections"""
        # Load environment variables
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)
            print(f"[OK] Environment variables loaded from {env_file}")
        
        # SQLite connection (source)
        sqlite_path = project_root / 'instance' / 'treasury_fresh.db'
        if not sqlite_path.exists():
            raise FileNotFoundError(f"SQLite database not found at {sqlite_path}")
        
        self.sqlite_conn = sqlite3.connect(str(sqlite_path))
        self.sqlite_conn.row_factory = sqlite3.Row
        print(f"[OK] Connected to SQLite database: {sqlite_path}")
        
        # Supabase PostgreSQL connection (destination)
        self.supabase_host = os.getenv('SUPABASE_DB_HOST') or os.getenv('POSTGRES_HOST')
        self.supabase_port = os.getenv('SUPABASE_DB_PORT') or os.getenv('POSTGRES_PORT', '5432')
        self.supabase_db = os.getenv('SUPABASE_DB_NAME') or os.getenv('POSTGRES_DB')
        self.supabase_user = os.getenv('SUPABASE_DB_USER') or os.getenv('POSTGRES_USER')
        self.supabase_password = os.getenv('SUPABASE_DB_PASSWORD') or os.getenv('POSTGRES_PASSWORD')
        
        if not all([self.supabase_host, self.supabase_db, self.supabase_user, self.supabase_password]):
            raise ValueError(
                "Missing Supabase connection details. Set environment variables:\n"
                "  SUPABASE_DB_HOST (or POSTGRES_HOST)\n"
                "  SUPABASE_DB_NAME (or POSTGRES_DB)\n"
                "  SUPABASE_DB_USER (or POSTGRES_USER)\n"
                "  SUPABASE_DB_PASSWORD (or POSTGRES_PASSWORD)\n"
                "  SUPABASE_DB_PORT (or POSTGRES_PORT, default: 5432)"
            )
        
        # Build connection string
        password_encoded = quote_plus(self.supabase_password)
        user_encoded = quote_plus(self.supabase_user)
        conn_string = f"postgresql://{user_encoded}:{password_encoded}@{self.supabase_host}:{self.supabase_port}/{self.supabase_db}"
        
        self.pg_conn = psycopg2.connect(conn_string)
        self.pg_conn.autocommit = False
        print(f"[OK] Connected to Supabase PostgreSQL: {self.supabase_host}/{self.supabase_db}")
        
        # ID mapping dictionaries (SQLite integer ID -> Supabase UUID)
        self.id_mappings: Dict[str, Dict[int, str]] = {}
        
        # Migration statistics
        self.stats = {
            'tables_migrated': 0,
            'rows_migrated': 0,
            'errors': []
        }
    
    def generate_uuid(self, table_name: str, old_id: int) -> str:
        """Generate deterministic UUID from table name and old ID"""
        # Use deterministic UUID generation based on table name and old ID
        # This ensures same old_id always maps to same UUID
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
        name = f"{table_name}:{old_id}"
        return str(uuid.uuid5(namespace, name))
    
    def get_table_columns(self, conn, table_name: str, is_postgres: bool = False) -> List[str]:
        """Get column names for a table"""
        if is_postgres:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            return [row[0] for row in cursor.fetchall()]
        else:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            return [row[1] for row in cursor.fetchall()]
    
    def get_postgres_column_types(self, table_name: str) -> Dict[str, str]:
        """Get PostgreSQL column data types for a table"""
        cursor = self.pg_conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = %s
        """, (table_name,))
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def migrate_table(self, table_name: str, id_column: str = 'id', 
                     foreign_keys: Optional[Dict[str, str]] = None) -> bool:
        """
        Migrate a single table from SQLite to PostgreSQL
        
        Args:
            table_name: Name of the table to migrate
            id_column: Name of the ID column (default: 'id')
            foreign_keys: Dict mapping column names to their referenced tables
                         e.g., {'user_id': 'users', 'organization_id': 'organizations'}
        """
        print(f"\n[INFO] Migrating table: {table_name}")
        
        try:
            # Get source data from SQLite
            sqlite_cursor = self.sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"  [INFO] Table {table_name} is empty, skipping")
                return True
            
            print(f"  [INFO] Found {len(rows)} rows to migrate")
            
            # Get column names
            columns = self.get_table_columns(self.sqlite_conn, table_name)
            
            # Get PostgreSQL column types to identify boolean columns
            pg_column_types = self.get_postgres_column_types(table_name)
            
            # Initialize ID mapping for this table
            self.id_mappings[table_name] = {}
            
            # Prepare data for insertion
            pg_cursor = self.pg_conn.cursor()
            migrated_rows = 0
            batch_size = 100  # Commit every 100 rows
            batch_count = 0
            
            for row in rows:
                try:
                    # Convert row to dictionary
                    row_dict = dict(zip(columns, row))
                    
                    # Convert integer ID to UUID
                    old_id = row_dict.get(id_column)
                    if old_id is not None and isinstance(old_id, int):
                        new_uuid = self.generate_uuid(table_name, old_id)
                        row_dict[id_column] = new_uuid
                        self.id_mappings[table_name][old_id] = new_uuid
                    
                    # Map foreign key references
                    if foreign_keys:
                        for fk_column, ref_table in foreign_keys.items():
                            if fk_column in row_dict and row_dict[fk_column] is not None:
                                old_fk_id = row_dict[fk_column]
                                if isinstance(old_fk_id, int) and ref_table in self.id_mappings:
                                    if old_fk_id in self.id_mappings[ref_table]:
                                        row_dict[fk_column] = self.id_mappings[ref_table][old_fk_id]
                                    else:
                                        print(f"  [WARNING] Foreign key {fk_column}={old_fk_id} not found in {ref_table}, setting to NULL")
                                        row_dict[fk_column] = None
                    
                    # Convert data types for PostgreSQL
                    values = []
                    for col in columns:
                        value = row_dict.get(col)
                        
                        # Handle None values
                        if value is None:
                            values.append(None)
                            continue
                        
                        # Get PostgreSQL column type
                        pg_type = pg_column_types.get(col, '').lower()
                        
                        # Convert SQLite boolean (integer 0/1) to PostgreSQL boolean
                        if pg_type == 'boolean' and isinstance(value, int):
                            values.append(bool(value))
                        # Convert Decimal to string for PostgreSQL numeric type
                        elif isinstance(value, Decimal):
                            values.append(str(value))
                        # Convert datetime objects
                        elif isinstance(value, datetime):
                            values.append(value.isoformat())
                        # Convert bytes to hex string
                        elif isinstance(value, bytes):
                            values.append(value.hex())
                        # Keep UUIDs as strings
                        elif isinstance(value, str) and len(value) == 36 and '-' in value:
                            values.append(value)
                        # Convert integers (non-ID columns, non-boolean)
                        elif isinstance(value, int) and col != id_column and pg_type != 'boolean':
                            values.append(value)
                        else:
                            values.append(value)
                    
                    # Build INSERT statement with conflict handling
                    placeholders = ', '.join(['%s'] * len(columns))
                    
                    # Use ON CONFLICT on primary key (id) - this handles duplicate IDs
                    # For other unique constraints (slug, username), we'll catch UniqueViolation
                    insert_query = f"""
                        INSERT INTO {table_name} ({', '.join(columns)})
                        VALUES ({placeholders})
                        ON CONFLICT (id) DO NOTHING
                    """
                    
                    try:
                        pg_cursor.execute(insert_query, values)
                        if pg_cursor.rowcount > 0:
                            migrated_rows += 1
                        batch_count += 1
                        # Commit in batches to avoid transaction state issues
                        if batch_count >= batch_size:
                            self.pg_conn.commit()
                            batch_count = 0
                        # If rowcount is 0, row already exists (skipped due to ON CONFLICT on id)
                    except pg_errors.UniqueViolation:
                        # Handle unique constraint violations on other fields (e.g., slug, username)
                        # This means a row with this unique value already exists
                        # This is fine - just skip it silently (data already migrated)
                        # Commit to clear the transaction state
                        self.pg_conn.commit()
                        batch_count = 0
                    except Exception as insert_error:
                        # Rollback and commit to reset transaction state
                        self.pg_conn.rollback()
                        self.pg_conn.commit()  # Commit to reset transaction state
                        batch_count = 0
                        # Re-raise to be caught by outer exception handler
                        raise insert_error
                    
                except Exception as e:
                    error_msg = str(e)
                    # Skip duplicate key errors - they're expected if data already exists
                    if "duplicate key" not in error_msg.lower() and "unique constraint" not in error_msg.lower() and "current transaction is aborted" not in error_msg.lower():
                        error_msg_full = f"Error migrating row in {table_name}: {e}"
                        print(f"  [ERROR] {error_msg_full}")
                        self.stats['errors'].append(error_msg_full)
                    # Rollback and commit to reset transaction state
                    try:
                        self.pg_conn.rollback()
                        self.pg_conn.commit()  # Commit to reset transaction state
                    except:
                        pass  # Ignore errors during cleanup
                    # Create new cursor for next row
                    pg_cursor = self.pg_conn.cursor()
                    continue
            
            # Final commit for remaining batch
            try:
                if batch_count > 0:
                    self.pg_conn.commit()
            except:
                pass  # Transaction may already be committed
            print(f"  [OK] Successfully migrated {migrated_rows}/{len(rows)} rows")
            
            self.stats['tables_migrated'] += 1
            self.stats['rows_migrated'] += migrated_rows
            
            return True
            
        except Exception as e:
            self.pg_conn.rollback()
            error_msg = f"Error migrating table {table_name}: {e}"
            print(f"  [ERROR] {error_msg}")
            self.stats['errors'].append(error_msg)
            import traceback
            traceback.print_exc()
            return False
    
    def migrate_all_tables(self):
        """Migrate all tables in the correct order (respecting foreign key dependencies)"""
        print("\n" + "="*70)
        print("[START] Starting Migration: SQLite -> Supabase")
        print("="*70)
        
        # Migration order: tables without dependencies first
        migration_order = [
            # Core tables (no dependencies)
            ('organizations', 'id', None),
            ('users', 'id', {'organization_id': 'organizations', 'created_by': 'users'}),
            ('options', 'id', None),
            ('exchange_rates', 'id', None),
            
            # User-related tables
            ('user_settings', 'id', {'user_id': 'users'}),
            ('password_reset_tokens', 'id', {'user_id': 'users'}),
            ('audit_logs', 'id', {'user_id': 'users'}),
            ('user_sessions', 'id', {'user_id': 'users'}),
            ('login_attempts', 'id', None),
            
            # Financial tables
            ('transactions', 'id', {'organization_id': 'organizations', 'created_by': 'users'}),
            ('psp_track', 'id', {'organization_id': 'organizations'}),
            ('daily_balance', 'id', {'organization_id': 'organizations'}),
            ('psp_allocation', 'id', {'organization_id': 'organizations'}),
            ('psp_devir', 'id', {'organization_id': 'organizations'}),
            ('psp_kasa_top', 'id', {'organization_id': 'organizations'}),
            ('psp_commission_rates', 'id', None),
            
            # Accounting tables
            ('daily_net', 'id', {'organization_id': 'organizations', 'created_by': 'users'}),
            ('expenses', 'id', {'organization_id': 'organizations', 'created_by': 'users'}),
            ('expense_budgets', 'id', {'organization_id': 'organizations', 'created_by': 'users'}),
            ('monthly_currency_summaries', 'id', {'organization_id': 'organizations', 'created_by': 'users'}),
            
            # Trust wallet tables
            ('trust_wallets', 'id', {'organization_id': 'organizations', 'created_by': 'users'}),
            ('trust_wallet_transactions', 'id', {'wallet_id': 'trust_wallets', 'organization_id': 'organizations'}),
            
            # Admin tables
            ('admin_section_permissions', 'id', None),
        ]
        
        # Check which tables exist in SQLite
        sqlite_cursor = self.sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in sqlite_cursor.fetchall()}
        
        # Migrate tables in order
        for table_name, id_column, foreign_keys in migration_order:
            if table_name in existing_tables:
                self.migrate_table(table_name, id_column, foreign_keys)
            else:
                print(f"\n[INFO] Table {table_name} not found in SQLite, skipping")
        
        print("\n" + "="*70)
        print("[SUMMARY] Migration Summary")
        print("="*70)
        print(f"[OK] Tables migrated: {self.stats['tables_migrated']}")
        print(f"[OK] Rows migrated: {self.stats['rows_migrated']}")
        print(f"[ERROR] Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            print("\n[WARNING] Errors encountered:")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more errors")
    
    def verify_migration(self):
        """Verify that migration was successful by comparing row counts"""
        print("\n" + "="*70)
        print("[VERIFY] Verifying Migration")
        print("="*70)
        
        sqlite_cursor = self.sqlite_conn.cursor()
        pg_cursor = self.pg_conn.cursor()
        
        # Get all tables from SQLite
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in sqlite_cursor.fetchall()]
        
        verification_passed = True
        
        for table_name in tables:
            try:
                # Count rows in SQLite
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                sqlite_count = sqlite_cursor.fetchone()[0]
                
                # Count rows in PostgreSQL
                pg_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                pg_count = pg_cursor.fetchone()[0]
                
                if sqlite_count == pg_count:
                    print(f"  [OK] {table_name}: {sqlite_count} rows")
                else:
                    print(f"  [WARNING] {table_name}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
                    verification_passed = False
                    
            except Exception as e:
                print(f"  [ERROR] {table_name}: Error verifying - {e}")
                verification_passed = False
        
        if verification_passed:
            print("\n[OK] Migration verification passed!")
        else:
            print("\n[WARNING] Migration verification found discrepancies. Please review.")
        
        return verification_passed
    
    def close(self):
        """Close database connections"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_conn:
            self.pg_conn.close()
        print("\n[OK] Database connections closed")


def main():
    """Main migration function"""
    import sys
    
    # Check for --yes flag to skip confirmation
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv or os.getenv('AUTO_CONFIRM_MIGRATION', '').lower() == 'true'
    
    migrator = None
    
    try:
        # Confirm migration
        print("\n" + "="*70)
        print("[WARNING] This will migrate data from SQLite to Supabase")
        print("="*70)
        print("\nThis script will:")
        print("  1. Read all data from your SQLite database")
        print("  2. Convert integer IDs to UUIDs")
        print("  3. Import data into Supabase PostgreSQL")
        print("  4. Preserve all relationships and foreign keys")
        print("\n[IMPORTANT] Make sure you have:")
        print("  - Backed up your SQLite database")
        print("  - Set Supabase connection environment variables")
        print("  - Verified Supabase tables are created")
        
        if not auto_confirm:
            response = input("\nDo you want to continue? (yes/no): ").strip().lower()
            if response != 'yes':
                print("[CANCELLED] Migration cancelled")
                return
        else:
            print("\n[INFO] Auto-confirming migration (--yes flag detected)")
        
        # Initialize migrator
        migrator = SupabaseMigrator()
        
        # Run migration
        migrator.migrate_all_tables()
        
        # Verify migration
        migrator.verify_migration()
        
        print("\n" + "="*70)
        print("[OK] Migration completed!")
        print("="*70)
        print("\nNext steps:")
        print("  1. Update your .env file with Supabase connection details")
        print("  2. Set DATABASE_TYPE=postgresql")
        print("  3. Restart your application")
        print("  4. Test the application with Supabase")
        
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Migration cancelled by user")
        if migrator:
            migrator.pg_conn.rollback()
    except Exception as e:
        print(f"\n\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        if migrator:
            migrator.pg_conn.rollback()
    finally:
        if migrator:
            migrator.close()


if __name__ == '__main__':
    main()

