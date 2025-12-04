"""
Add missing commission rates for PSPs
Run this script to fix commission rate warnings
"""
from app import create_app, db
from app.models.psp_commission_rate import PSPCommissionRate
from datetime import date
from decimal import Decimal

app = create_app()

with app.app_context():
    print("=" * 80)
    print("ADDING MISSING PSP COMMISSION RATES")
    print("=" * 80)
    
    # PSPs that need commission rates
    missing_rates = [
        {'psp_name': '#71 CRYPPAY', 'rate': Decimal('0.09'), 'percent': '9%'},
        {'psp_name': '#70 CRYPPAY 9', 'rate': Decimal('0.09'), 'percent': '9%'},
        {'psp_name': '#72 CRYPPAY', 'rate': Decimal('0.09'), 'percent': '9%'},
    ]
    
    effective_from = date(2025, 1, 1)  # Set to start of year or appropriate date
    
    for psp_data in missing_rates:
        psp_name = psp_data['psp_name']
        rate = psp_data['rate']
        percent = psp_data['percent']
        
        # Check if rate already exists
        existing_rate = PSPCommissionRate.query.filter_by(
            psp_name=psp_name,
            is_active=True
        ).first()
        
        if existing_rate:
            print(f"✓ {psp_name}: Rate already exists ({float(existing_rate.commission_rate * 100):.1f}%)")
        else:
            # Create new commission rate
            new_rate = PSPCommissionRate(
                psp_name=psp_name,
                commission_rate=rate,
                effective_from=effective_from,
                effective_until=None,  # Current rate (no end date)
                is_active=True
            )
            db.session.add(new_rate)
            print(f"+ {psp_name}: Adding {percent} commission rate (effective from {effective_from})")
    
    try:
        db.session.commit()
        print("\n" + "=" * 80)
        print("✅ SUCCESS: All missing commission rates have been added")
        print("=" * 80)
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ ERROR: Failed to add commission rates: {e}")
        print("=" * 80)

