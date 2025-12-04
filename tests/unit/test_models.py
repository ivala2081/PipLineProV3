# Test User and Transaction Models
"""
Unit tests for database models.
"""
import pytest
from datetime import datetime
from decimal import Decimal

from app.models.user import User
from app.models.transaction import Transaction


@pytest.mark.unit
class TestUserModel:
    """Tests for User model."""
    
    def test_create_user(self, session):
        """Test creating a new user."""
        user = User(
            username='testuser',
            email='test@example.com',
            role='user',
            is_active=True
        )
        user.set_password('password123')
        
        session.add(user)
        session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.role == 'user'
        assert user.is_active is True
    
    def test_password_hashing(self, session):
        """Test password hashing and verification."""
        user = User(username='testuser', email='test@example.com', role='user', admin_level=0)
        password = 'SecurePassword123!'
        
        user.set_password(password)
        session.add(user)
        session.commit()
        
        # Password should be hashed (not stored as plain text)
        assert user.password != password
        
        # Correct password should verify
        assert user.check_password(password) is True
        
        # Wrong password should not verify
        assert user.check_password('WrongPassword') is False
    
    def test_user_repr(self, admin_user):
        """Test user string representation."""
        repr_str = repr(admin_user)
        assert 'User' in repr_str
        assert 'admin' in repr_str
    
    def test_unique_username(self, session, admin_user):
        """Test that usernames must be unique."""
        duplicate_user = User(
            username='admin',  # Same as admin_user
            email='different@example.com'
        )
        duplicate_user.set_password('password')
        
        session.add(duplicate_user)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            session.commit()


@pytest.mark.unit
class TestTransactionModel:
    """Tests for Transaction model."""
    
    def test_create_transaction(self, session):
        """Test creating a new transaction."""
        from datetime import date
        transaction = Transaction(
            date=date.today(),
            category='DEP',  # Not 'type', use 'category'
            amount=Decimal('1500.50'),
            commission=Decimal('75.00'),
            net_amount=Decimal('1425.50'),
            currency='TL',  # Not 'TRY', use 'TL'
            notes='Test deposit',  # Not 'description', use 'notes'
            psp='Test PSP',
            company='Test Company',
            client_name='Test Client'  # Not 'client', use 'client_name'
        )
        
        session.add(transaction)
        session.commit()
        
        assert transaction.id is not None
        assert transaction.category == 'DEP'
        assert transaction.amount == Decimal('1500.50')
        assert transaction.currency == 'TL'
    
    def test_transaction_amount_precision(self, session):
        """Test that transaction amounts maintain decimal precision."""
        from datetime import date
        transaction = Transaction(
            date=date.today(),
            category='WD',  # Use category not type
            amount=Decimal('-1234.57'),  # WD requires negative, 2 decimals
            commission=Decimal('60.00'),
            net_amount=Decimal('-1174.57'),
            currency='USD',
            notes='Test',  # Use notes not description
            psp='Test PSP',
            company='Test Company',
            client_name='Test Client'  # Use client_name not client
        )
        
        session.add(transaction)
        session.commit()
        
        # Retrieve from database
        retrieved = session.query(Transaction).filter_by(id=transaction.id).first()
        assert retrieved.amount == Decimal('-1234.57')
    
    def test_transaction_types(self, session):
        """Test different transaction types."""
        from datetime import date
        # Only DEP and WD are valid categories
        categories = [
            ('DEP', Decimal('100.00'), Decimal('95.00')),  # Positive for deposits
            ('WD', Decimal('-100.00'), Decimal('-95.00'))  # Negative for withdrawals
        ]
        
        for category, amount, net_amount in categories:
            transaction = Transaction(
                date=date.today(),
                category=category,  # Use category not type
                amount=amount,
                commission=Decimal('5.00'),
                net_amount=net_amount,
                currency='TL',  # Use TL not TRY
                notes=f'Test {category}',  # Use notes not description
                psp='Test PSP',
                company='Test Company',
                client_name='Test Client'  # Use client_name not client
            )
            session.add(transaction)
        
        session.commit()
        
        # Verify all categories were created
        for category, _, _ in categories:
            count = session.query(Transaction).filter_by(category=category).count()
            assert count == 1
    
    def test_transaction_currencies(self, session):
        """Test transactions with different currencies."""
        from datetime import date
        currencies = ['TL', 'USD', 'EUR']  # Use TL not TRY
        
        for currency in currencies:
            transaction = Transaction(
                date=date.today(),
                category='DEP',  # Use category not type
                amount=Decimal('100.00'),
                commission=Decimal('5.00'),
                net_amount=Decimal('95.00'),
                currency=currency,
                notes=f'Test {currency}',  # Use notes not description
                psp='Test PSP',
                company='Test Company',
                client_name='Test Client'  # Use client_name not client
            )
            session.add(transaction)
        
        session.commit()
        
        # Verify all currencies were created
        for currency in currencies:
            count = session.query(Transaction).filter_by(currency=currency).count()
            assert count == 1

