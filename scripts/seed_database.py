"""
Seed Database Script
===================

WHAT IS THIS?
-------------
This script puts starting data into your database. 
Think of it like filling an empty house with furniture.

WHEN TO USE IT:
--------------
- When you create a NEW database
- When you want to reset your database to starting state
- After running migrations on a fresh database

WHAT IT DOES:
------------
1. Creates default admin user (admin@test.com / admin123)
2. Creates test users (manager, user, demo)
3. Creates default PSP options (like #72 CRYPPAY, TETHER, etc.)
4. Creates default payment methods (BANKA, Tether, etc.)
5. Creates default categories (WD, DEP)
6. Creates default exchange rates

HOW TO USE:
----------
python scripts/seed_database.py
"""

import os
import sys
from pathlib import Path
from decimal import Decimal
from datetime import date

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

from app import create_app, db
from app.models.user import User
from app.models.config import Option
from app.models.exchange_rate import ExchangeRate
from werkzeug.security import generate_password_hash

def seed_database():
    """Put starting data into the database"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("SEEDING DATABASE")
        print("=" * 60)
        print("")
        print("This will add starting data to your database.")
        print("")
        
        # Create tables if they don't exist
        print("Creating database tables...")
        db.create_all()
        print("✓ Tables created")
        print("")
        
        # 1. Create default users
        print("Creating default users...")
        users_created = 0
        
        # Admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@test.com',
                password=generate_password_hash('admin123'),
                role='admin',
                admin_level=1,  # Main admin
                is_active=True
            )
            db.session.add(admin)
            users_created += 1
            print("  ✓ Created admin user (admin@test.com / admin123)")
        else:
            print("  ℹ Admin user already exists")
        
        # Manager user
        manager = User.query.filter_by(username='manager').first()
        if not manager:
            manager = User(
                username='manager',
                email='manager@test.com',
                password=generate_password_hash('manager123'),
                role='admin',
                admin_level=2,  # Secondary admin
                is_active=True
            )
            db.session.add(manager)
            users_created += 1
            print("  ✓ Created manager user (manager@test.com / manager123)")
        else:
            print("  ℹ Manager user already exists")
        
        # Regular user
        user = User.query.filter_by(username='user').first()
        if not user:
            user = User(
                username='user',
                email='user@test.com',
                password=generate_password_hash('user123'),
                role='user',
                admin_level=0,
                is_active=True
            )
            db.session.add(user)
            users_created += 1
            print("  ✓ Created regular user (user@test.com / user123)")
        else:
            print("  ℹ Regular user already exists")
        
        # Demo user
        demo = User.query.filter_by(username='demo').first()
        if not demo:
            demo = User(
                username='demo',
                email='demo@test.com',
                password=generate_password_hash('demo123'),
                role='user',
                admin_level=0,
                is_active=True
            )
            db.session.add(demo)
            users_created += 1
            print("  ✓ Created demo user (demo@test.com / demo123)")
        else:
            print("  ℹ Demo user already exists")
        
        print(f"  Total users created: {users_created}")
        print("")
        
        # 2. Create default PSP options
        print("Creating PSP options...")
        psp_options = [
            ('#60 CASHPAY', Decimal('0.08')),   # 8%
            ('#61 CRYPPAY', Decimal('0.075')),  # 7.5%
            ('#62 CRYPPAY', Decimal('0.075')),  # 7.5%
            ('#70 CRYPPAY', Decimal('0.08')),   # 8%
            ('#70 CRYPPAY 9', Decimal('0.09')), # 9%
            ('#71 CRYPPAY', Decimal('0.075')),  # 7.5%
            ('#72 CRYPPAY', Decimal('0.08')),   # 8%
            ('TETHER', Decimal('0.0')),         # 0% (internal KASA)
            ('KUYUMCU', Decimal('0.12')),       # 12%
            ('SİPAY', Decimal('0.0015')),       # 0.15%
        ]
        
        psp_created = 0
        for psp_name, commission_rate in psp_options:
            existing = Option.query.filter_by(
                field_name='psp',
                value=psp_name,
                is_active=True
            ).first()
            
            if not existing:
                option = Option(
                    field_name='psp',
                    value=psp_name,
                    commission_rate=commission_rate,
                    is_active=True
                )
                db.session.add(option)
                psp_created += 1
                print(f"  ✓ Created PSP: {psp_name} (rate: {commission_rate * 100}%)")
            else:
                print(f"  ℹ PSP already exists: {psp_name}")
        
        print(f"  Total PSPs created: {psp_created}")
        print("")
        
        # 3. Create default payment methods
        print("Creating payment methods...")
        payment_methods = ['BANKA', 'Tether', 'KK', 'H', 'EFT']
        
        pm_created = 0
        for pm in payment_methods:
            existing = Option.query.filter_by(
                field_name='payment_method',
                value=pm,
                is_active=True
            ).first()
            
            if not existing:
                option = Option(
                    field_name='payment_method',
                    value=pm,
                    is_active=True
                )
                db.session.add(option)
                pm_created += 1
                print(f"  ✓ Created payment method: {pm}")
            else:
                print(f"  ℹ Payment method already exists: {pm}")
        
        print(f"  Total payment methods created: {pm_created}")
        print("")
        
        # 4. Create default categories
        print("Creating categories...")
        categories = ['WD', 'DEP']
        
        cat_created = 0
        for cat in categories:
            existing = Option.query.filter_by(
                field_name='category',
                value=cat,
                is_active=True
            ).first()
            
            if not existing:
                option = Option(
                    field_name='category',
                    value=cat,
                    is_active=True
                )
                db.session.add(option)
                cat_created += 1
                print(f"  ✓ Created category: {cat}")
            else:
                print(f"  ℹ Category already exists: {cat}")
        
        print(f"  Total categories created: {cat_created}")
        print("")
        
        # 5. Create default exchange rate (today's date)
        print("Creating default exchange rate...")
        today = date.today()
        existing_rate = ExchangeRate.query.filter_by(date=today).first()
        
        if not existing_rate:
            # Default rate: 42.20 (as per user requirement)
            rate = ExchangeRate(
                date=today,
                usd_to_tl=Decimal('42.20'),
                is_manual=False
            )
            db.session.add(rate)
            print(f"  ✓ Created exchange rate for {today}: 42.20 TL/USD")
        else:
            print(f"  ℹ Exchange rate for {today} already exists")
        
        print("")
        
        # Commit all changes
        try:
            db.session.commit()
            print("=" * 60)
            print("✓ DATABASE SEEDED SUCCESSFULLY!")
            print("=" * 60)
            print("")
            print("You can now login with:")
            print("  - Admin: admin@test.com / admin123")
            print("  - Manager: manager@test.com / manager123")
            print("  - User: user@test.com / user123")
            print("  - Demo: demo@test.com / demo123")
            print("")
            return True
        except Exception as e:
            db.session.rollback()
            print("=" * 60)
            print(f"✗ ERROR: Failed to seed database: {e}")
            print("=" * 60)
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = seed_database()
    sys.exit(0 if success else 1)

