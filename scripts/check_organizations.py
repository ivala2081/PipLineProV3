"""
Diagnostic script to check organizations in the database
"""
import os
import sys
from datetime import datetime

# Add the app directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.organization import Organization
from app.models.user import User

def check_organizations():
    """Check all organizations in the database"""
    app = create_app(config_name='development')
    
    with app.app_context():
        print("=" * 60)
        print("ORGANIZATIONS DIAGNOSTIC CHECK")
        print("=" * 60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Get all organizations (no filter)
        all_orgs = Organization.query.all()
        print(f"Total organizations in database: {len(all_orgs)}")
        print()
        
        if len(all_orgs) == 0:
            print("[ERROR] No organizations found in database!")
            return
        
        # Check each organization
        for org in all_orgs:
            print(f"Organization ID: {org.id}")
            print(f"  Name: {org.name}")
            print(f"  Slug: {org.slug}")
            print(f"  is_active: {org.is_active} {'[ACTIVE]' if org.is_active else '[INACTIVE]'}")
            print(f"  subscription_status: {org.subscription_status}")
            print(f"  subscription_tier: {org.subscription_tier}")
            print(f"  Created: {org.created_at}")
            print(f"  Updated: {org.updated_at}")
            
            # Count users in this org
            user_count = User.query.filter_by(organization_id=org.id).count()
            print(f"  Users: {user_count}")
            print()
        
        # Check active organizations
        active_orgs = Organization.query.filter_by(is_active=True).all()
        print(f"Active organizations (is_active=True): {len(active_orgs)}")
        print()
        
        # Check inactive organizations
        inactive_orgs = Organization.query.filter_by(is_active=False).all()
        if inactive_orgs:
            print(f"[WARNING] Inactive organizations (is_active=False): {len(inactive_orgs)}")
            for org in inactive_orgs:
                print(f"  - {org.name} (ID: {org.id})")
            print()
        
        # Check current user
        print("Current User Check:")
        print("  (Run this from the Flask app context with current_user)")
        print()
        
        print("=" * 60)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 60)

if __name__ == '__main__':
    check_organizations()

