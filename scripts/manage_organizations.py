"""
Organization & User Management Script
Allows super admins to manage organizations and assign users

Usage:
    python scripts/manage_organizations.py
"""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Organization, User
from werkzeug.security import generate_password_hash


def list_organizations():
    """List all organizations"""
    print("\n" + "=" * 80)
    print("ALL ORGANIZATIONS")
    print("=" * 80)
    
    orgs = Organization.query.all()
    
    if not orgs:
        print("No organizations found.")
        return
    
    for org in orgs:
        print(f"\nID: {org.id}")
        print(f"Name: {org.name}")
        print(f"Slug: {org.slug}")
        print(f"Tier: {org.subscription_tier}")
        print(f"Max Users: {org.max_users}")
        print(f"Active: {org.is_active}")
        
        # Count users in this org
        user_count = User.query.filter_by(organization_id=org.id).count()
        print(f"Users: {user_count}")
        print("-" * 80)


def list_users_by_org(org_id=None):
    """List users, optionally filtered by organization"""
    print("\n" + "=" * 80)
    if org_id:
        org = Organization.query.get(org_id)
        if not org:
            print(f"Organization with ID {org_id} not found.")
            return
        print(f"USERS IN ORGANIZATION: {org.name}")
        users = User.query.filter_by(organization_id=org_id).all()
    else:
        print("ALL USERS")
        users = User.query.all()
    print("=" * 80)
    
    if not users:
        print("No users found.")
        return
    
    for user in users:
        org_name = user.organization.name if user.organization else "No Organization"
        admin_type = "SUPER ADMIN" if user.admin_level <= 1 else f"ORG ADMIN (Level {user.admin_level})"
        
        print(f"\nID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Organization: {org_name} (ID: {user.organization_id})")
        print(f"Admin Level: {user.admin_level} ({admin_type})")
        print(f"Active: {user.is_active}")
        print("-" * 80)


def create_organization():
    """Create a new organization"""
    print("\n" + "=" * 80)
    print("CREATE NEW ORGANIZATION")
    print("=" * 80)
    
    name = input("Organization Name: ").strip()
    if not name:
        print("Error: Organization name is required.")
        return
    
    slug = input("Slug (URL-friendly, e.g., 'company-abc'): ").strip().lower()
    if not slug:
        slug = name.lower().replace(' ', '-')
    
    # Check if slug exists
    existing = Organization.query.filter_by(slug=slug).first()
    if existing:
        print(f"Error: Organization with slug '{slug}' already exists.")
        return
    
    print("\nSubscription Tiers:")
    print("1. free")
    print("2. starter")
    print("3. pro")
    print("4. enterprise")
    tier_choice = input("Choose tier (1-4): ").strip()
    
    tier_map = {'1': 'free', '2': 'starter', '3': 'pro', '4': 'enterprise'}
    tier = tier_map.get(tier_choice, 'free')
    
    # Set defaults based on tier
    tier_limits = {
        'free': {'users': 1, 'transactions': 100, 'psps': 1},
        'starter': {'users': 3, 'transactions': 1000, 'psps': 2},
        'pro': {'users': 10, 'transactions': 10000, 'psps': 5},
        'enterprise': {'users': 999, 'transactions': 999999, 'psps': 999}
    }
    
    limits = tier_limits[tier]
    
    max_users = input(f"Max Users [{limits['users']}]: ").strip()
    max_users = int(max_users) if max_users else limits['users']
    
    max_transactions = input(f"Max Transactions/Month [{limits['transactions']}]: ").strip()
    max_transactions = int(max_transactions) if max_transactions else limits['transactions']
    
    max_psps = input(f"Max PSP Connections [{limits['psps']}]: ").strip()
    max_psps = int(max_psps) if max_psps else limits['psps']
    
    contact_email = input("Contact Email (optional): ").strip() or None
    
    # Create organization
    org = Organization(
        name=name,
        slug=slug,
        subscription_tier=tier,
        max_users=max_users,
        max_transactions_per_month=max_transactions,
        max_psp_connections=max_psps,
        contact_email=contact_email,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    
    db.session.add(org)
    db.session.commit()
    
    print(f"\n✅ Organization created successfully!")
    print(f"   ID: {org.id}")
    print(f"   Name: {org.name}")
    print(f"   Slug: {org.slug}")
    print(f"   Tier: {org.subscription_tier}")
    
    # Ask if they want to create admin user
    create_admin = input("\nCreate admin user for this organization? (y/n): ").strip().lower()
    if create_admin == 'y':
        create_user_for_org(org.id)


def create_user_for_org(org_id):
    """Create a new user for an organization"""
    print("\n" + "=" * 80)
    print("CREATE NEW USER")
    print("=" * 80)
    
    org = Organization.query.get(org_id)
    if not org:
        print(f"Error: Organization with ID {org_id} not found.")
        return
    
    print(f"Organization: {org.name}\n")
    
    username = input("Username: ").strip()
    if not username:
        print("Error: Username is required.")
        return
    
    # Check if username exists
    existing = User.query.filter_by(username=username).first()
    if existing:
        print(f"Error: User '{username}' already exists.")
        return
    
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    
    if not password:
        print("Error: Password is required.")
        return
    
    print("\nAdmin Levels:")
    print("0. Super Admin (can see ALL organizations)")
    print("1. Main Admin (can see ALL organizations)")
    print("2. Organization Admin (can see ONLY this organization)")
    print("3. Sub Admin / User (can see ONLY this organization, limited access)")
    
    admin_level = input("Choose admin level (0-3) [2]: ").strip()
    admin_level = int(admin_level) if admin_level else 2
    
    # Create user
    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        organization_id=org_id,
        admin_level=admin_level,
        is_active=True
    )
    
    db.session.add(user)
    db.session.commit()
    
    print(f"\n✅ User created successfully!")
    print(f"   ID: {user.id}")
    print(f"   Username: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Organization: {org.name}")
    print(f"   Admin Level: {user.admin_level}")
    
    print(f"\n📧 Login Credentials:")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print(f"   (Send these to the user)")


def assign_user_to_org():
    """Assign existing user to different organization"""
    print("\n" + "=" * 80)
    print("ASSIGN USER TO ORGANIZATION")
    print("=" * 80)
    
    user_id = input("User ID: ").strip()
    if not user_id:
        print("Error: User ID is required.")
        return
    
    user = User.query.get(int(user_id))
    if not user:
        print(f"Error: User with ID {user_id} not found.")
        return
    
    print(f"\nCurrent User: {user.username}")
    print(f"Current Organization: {user.organization.name if user.organization else 'None'} (ID: {user.organization_id})")
    
    list_organizations()
    
    org_id = input("\nNew Organization ID: ").strip()
    if not org_id:
        print("Error: Organization ID is required.")
        return
    
    org = Organization.query.get(int(org_id))
    if not org:
        print(f"Error: Organization with ID {org_id} not found.")
        return
    
    confirm = input(f"\nMove user '{user.username}' to organization '{org.name}'? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    user.organization_id = org.id
    db.session.commit()
    
    print(f"\n✅ User assigned successfully!")
    print(f"   User: {user.username}")
    print(f"   New Organization: {org.name}")


def main():
    """Main menu"""
    app = create_app(config_name='development')
    
    with app.app_context():
        while True:
            print("\n" + "=" * 80)
            print("ORGANIZATION & USER MANAGEMENT")
            print("=" * 80)
            print("\nOrganizations:")
            print("  1. List all organizations")
            print("  2. Create new organization")
            print("\nUsers:")
            print("  3. List all users")
            print("  4. List users by organization")
            print("  5. Create user for organization")
            print("  6. Assign user to organization")
            print("\n  0. Exit")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '1':
                list_organizations()
            elif choice == '2':
                create_organization()
            elif choice == '3':
                list_users_by_org()
            elif choice == '4':
                org_id = input("Organization ID: ").strip()
                if org_id:
                    list_users_by_org(int(org_id))
            elif choice == '5':
                org_id = input("Organization ID: ").strip()
                if org_id:
                    create_user_for_org(int(org_id))
            elif choice == '6':
                assign_user_to_org()
            elif choice == '0':
                print("\nGoodbye!")
                break
            else:
                print("\nInvalid choice. Please try again.")


if __name__ == '__main__':
    main()

