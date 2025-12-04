"""
Unit tests for database transaction helper
"""
import pytest
from app.utils.db_transaction import db_transaction
from app import db
from app.models.transaction import Transaction
from decimal import Decimal
from datetime import date


@pytest.mark.unit
@pytest.mark.database
class TestDBTransaction:
    """Test db_transaction context manager"""
    
    def test_db_transaction_commit(self, app, session):
        """Test successful transaction commit"""
        with app.app_context():
            # Clean up any existing test data
            db.session.query(Transaction).filter_by(client_name="Test Client").delete()
            db.session.commit()
            
            with db_transaction() as sess:
                transaction = Transaction(
                    client_name="Test Client",
                    amount=Decimal("1000.00"),
                    currency="TL",
                    date=date.today(),
                    category="DEP"
                )
                sess.add(transaction)
            
            # Transaction should be committed
            found = db.session.query(Transaction).filter_by(
                client_name="Test Client"
            ).first()
            assert found is not None
            assert found.amount == Decimal("1000.00")
    
    def test_db_transaction_rollback_on_error(self, app, session):
        """Test transaction rollback on error"""
        with app.app_context():
            # Clean up any existing test data
            db.session.query(Transaction).filter_by(client_name="Test Client Error").delete()
            db.session.commit()
            
            try:
                with db_transaction() as sess:
                    transaction = Transaction(
                        client_name="Test Client Error",
                        amount=Decimal("1000.00"),
                        currency="TL",
                        date=date.today(),
                        category="DEP"
                    )
                    sess.add(transaction)
                    # Force an error
                    raise ValueError("Test error")
            except ValueError:
                pass
            
            # Transaction should be rolled back
            found = db.session.query(Transaction).filter_by(
                client_name="Test Client Error"
            ).first()
            assert found is None
    
    def test_db_transaction_multiple_operations(self, app, session):
        """Test multiple operations in one transaction"""
        with app.app_context():
            # Clean up any existing test data
            db.session.query(Transaction).filter(
                Transaction.client_name.like("Client %")
            ).delete()
            db.session.commit()
            
            with db_transaction() as sess:
                for i in range(3):
                    transaction = Transaction(
                        client_name=f"Client {i}",
                        amount=Decimal(f"{(i+1)*100}.00"),
                        currency="TL",
                        date=date.today(),
                        category="DEP"
                    )
                    sess.add(transaction)
            
            # All transactions should be committed
            count = db.session.query(Transaction).filter(
                Transaction.client_name.like("Client %")
            ).count()
            assert count == 3

