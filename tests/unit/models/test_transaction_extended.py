"""
Extended unit tests for Transaction model
"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from app.models.transaction import Transaction


@pytest.mark.unit
@pytest.mark.database
class TestTransactionModelExtended:
    """Extended tests for Transaction model"""
    
    def test_transaction_currency_validation(self, session):
        """Test transaction currency validation"""
        transaction = Transaction(
            client_name="Test Client",
            amount=Decimal("1000.00"),
            currency="TL",
            date=date.today(),
            category="DEP",
            commission=Decimal("25.00"),
            net_amount=Decimal("975.00")
        )
        session.add(transaction)
        session.commit()
        
        assert transaction.currency == "TL"
    
    def test_transaction_psp_assignment(self, session):
        """Test PSP assignment"""
        transaction = Transaction(
            client_name="Test Client",
            amount=Decimal("1000.00"),
            currency="TL",
            date=date.today(),
            category="DEP",
            psp="SIPAY",
            commission=Decimal("25.00"),
            net_amount=Decimal("975.00")
        )
        session.add(transaction)
        session.commit()
        
        assert transaction.psp == "SIPAY"
    
    def test_transaction_payment_method(self, session):
        """Test payment method assignment"""
        transaction = Transaction(
            client_name="Test Client",
            amount=Decimal("1000.00"),
            currency="TL",
            date=date.today(),
            category="DEP",
            payment_method="KK",
            commission=Decimal("25.00"),
            net_amount=Decimal("975.00")
        )
        session.add(transaction)
        session.commit()
        
        assert transaction.payment_method == "KK"
    
    def test_transaction_notes(self, session):
        """Test notes field"""
        transaction = Transaction(
            client_name="Test Client",
            amount=Decimal("1000.00"),
            currency="TL",
            date=date.today(),
            category="DEP",
            notes="Test notes",
            commission=Decimal("25.00"),
            net_amount=Decimal("975.00")
        )
        session.add(transaction)
        session.commit()
        
        assert transaction.notes == "Test notes"
    
    def test_transaction_commission_calculation(self, session):
        """Test commission field"""
        transaction = Transaction(
            client_name="Test Client",
            amount=Decimal("1000.00"),
            currency="TL",
            date=date.today(),
            category="DEP",
            commission=Decimal("25.00"),
            net_amount=Decimal("975.00")
        )
        session.add(transaction)
        session.commit()
        
        assert transaction.commission == Decimal("25.00")
        assert transaction.net_amount == Decimal("975.00")
    
    def test_transaction_created_at_timestamp(self, session):
        """Test created_at timestamp"""
        from datetime import timezone
        
        transaction = Transaction(
            client_name="Test Client",
            amount=Decimal("1000.00"),
            currency="TL",
            date=date.today(),
            category="DEP",
            commission=Decimal("25.00"),
            net_amount=Decimal("975.00")
        )
        session.add(transaction)
        session.commit()
        
        # Check that created_at is set and is a datetime
        assert transaction.created_at is not None
        assert isinstance(transaction.created_at, datetime)
        
        # If timezone aware, check it's UTC
        if transaction.created_at.tzinfo is not None:
            assert transaction.created_at.tzinfo == timezone.utc
    
    def test_transaction_updated_at_timestamp(self, session):
        """Test updated_at timestamp"""
        transaction = Transaction(
            client_name="Test Client",
            amount=Decimal("1000.00"),
            currency="TL",
            date=date.today(),
            category="DEP",
            commission=Decimal("25.00"),
            net_amount=Decimal("975.00")
        )
        session.add(transaction)
        session.commit()
        
        original_updated = transaction.updated_at
        
        # Update transaction
        transaction.amount = Decimal("2000.00")
        transaction.net_amount = Decimal("1975.00")
        session.commit()
        
        assert transaction.updated_at >= original_updated
    
    def test_transaction_string_representation(self, session):
        """Test transaction string representation"""
        transaction = Transaction(
            client_name="Test Client",
            amount=Decimal("1000.00"),
            currency="TL",
            date=date.today(),
            category="DEP",
            commission=Decimal("25.00"),
            net_amount=Decimal("975.00")
        )
        session.add(transaction)
        session.commit()
        
        # Check if __repr__ or __str__ exists
        str_repr = str(transaction)
        assert "Test Client" in str_repr or "Transaction" in str_repr

