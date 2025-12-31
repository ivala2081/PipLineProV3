#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick script to fix .env file with correct Supabase connection details
"""

from pathlib import Path
import sys

def fix_env_file():
    """Fix the .env file with correct Supabase connection details"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("ERROR: .env file not found")
        return False
    
    # Read current .env
    lines = []
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"ERROR reading .env file: {e}")
        return False
    
    # Fix the connection details
    fixed_lines = []
    changes_made = False
    
    for line in lines:
        original_line = line
        line_stripped = line.strip()
        
        # Fix POSTGRES_HOST
        if line_stripped.startswith('POSTGRES_HOST='):
            if 'None' in line or not line_stripped.split('=', 1)[1].strip() or 'db.sihlxucjplorgptrosed' not in line:
                fixed_lines.append('POSTGRES_HOST=db.sihlxucjplorgptrosed.supabase.co\n')
                changes_made = True
                continue
        
        # Fix SUPABASE_DB_HOST
        if line_stripped.startswith('SUPABASE_DB_HOST='):
            if 'None' in line or not line_stripped.split('=', 1)[1].strip() or 'db.sihlxucjplorgptrosed' not in line:
                fixed_lines.append('SUPABASE_DB_HOST=db.sihlxucjplorgptrosed.supabase.co\n')
                changes_made = True
                continue
        
        # Fix POSTGRES_DB if it has the hostname instead
        if line_stripped.startswith('POSTGRES_DB='):
            value = line_stripped.split('=', 1)[1].strip()
            if 'db.sihlxucjplorgptrosed.supabase.co' in value:
                fixed_lines.append('POSTGRES_DB=postgres\n')
                changes_made = True
                continue
        
        # Fix SUPABASE_DB_NAME if it has the hostname instead
        if line_stripped.startswith('SUPABASE_DB_NAME='):
            value = line_stripped.split('=', 1)[1].strip()
            if 'db.sihlxucjplorgptrosed.supabase.co' in value:
                fixed_lines.append('SUPABASE_DB_NAME=postgres\n')
                changes_made = True
                continue
        
        # Keep original line if no changes needed
        fixed_lines.append(line)
    
    # Write back
    if changes_made:
        try:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            print("SUCCESS: Fixed .env file!")
            print("\nUpdated connection details:")
            print("  POSTGRES_HOST=db.sihlxucjplorgptrosed.supabase.co")
            print("  POSTGRES_DB=postgres")
            print("  POSTGRES_PORT=5432")
            print("  POSTGRES_USER=postgres")
            print("  POSTGRES_PASSWORD=*****")
            return True
        except Exception as e:
            print(f"ERROR writing .env file: {e}")
            return False
    else:
        print("INFO: No changes needed in .env file")
        return True

if __name__ == '__main__':
    fix_env_file()

